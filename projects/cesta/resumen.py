"""Que hay hoy en la nevera de datos. Se imprime al final de cada ejecucion.

    uv run python -m projects.cesta.resumen

No calcula nada nuevo: lee lo que ya escribieron el pipeline y el emparejador y
lo cuenta en voz alta. La razon de existir es que una ejecucion diaria que solo
dice "hecho" no sirve para saber si el dia ha ido bien; lo que hace falta es ver
que cadenas han refrescado, cuanto historico hay y cuanto se ahorra hoy.
"""
from __future__ import annotations

import json

import polars as pl

from core import cobertura, comparacion, config, publicacion
from projects.cesta import avisos

# Por encima de esto no hay ninguna diferencia de precio real entre supermercados
# espanoles: lo que hay es un formato mal leido. Se mide, se avisa y no se mezcla.
# La frontera de "esto ya no es una oferta, es un fallo nuestro" vive en
# core/comparacion.py, compartida con la interfaz. Antes habia dos numeros
# distintos y los dos se llamaban "imposible".
TOPE_CREIBLE = (comparacion.FACTOR_INCREIBLE - 1) * 100      # 2.900 %
TOPE_LLAMATIVO = (comparacion.FACTOR_LLAMATIVO - 1) * 100    #   200 %


def _catalogo() -> pl.DataFrame | None:
    fichero = config.DATA / "gold" / "grupos.parquet"
    return pl.read_parquet(fichero) if fichero.exists() else None


def _historico() -> pl.DataFrame | None:
    fichero = config.DATA / "gold" / "precio_diario.parquet"
    return pl.read_parquet(fichero) if fichero.exists() else None


def dias_huerfanos() -> list[tuple[str, str, int, str]]:
    """Dias que estan en el historico y ya no tienen bronze en su sitio.

    El historico de gold se **acumula**: cada dia se le anade la instantanea de
    cada cadena y nada lo vuelve a comprobar. Si el bronze de un dia deja de estar
    donde estaba, sus filas se quedan en gold igual, y no hay forma de notarlo.

    Devuelve (cadena, fecha, filas, motivo), y el motivo importa mas que el aviso,
    porque hay dos situaciones que se parecen mucho y no son la misma:

    - **apartado**: alguien lo movio a `data/debug/descartados` a proposito,
      siguiendo `docs/OPERACION.md`, y el motivo va escrito en el nombre de la
      carpeta. El dato esta entero; el historico conserva lo que se capturo ese
      dia y `--rehacer-historico` lo dejaria fuera, que es justo lo que se quiso.
    - **sin rastro**: no esta ni en bronze ni entre los apartados. Eso si es un
      problema: esas filas no se pueden recalcular desde nada.

    El 18 de septiembre de 2026 se confundieron durante un dia entero. El
    historico tenia 20.559 filas de alcampo de ese dia y `bronze/fuente=alcampo/`
    se quedaba en el 17, asi que se dio el bronze por perdido y se estuvo
    conjeturando quien lo habia borrado. Estaba entero en
    `data/debug/descartados/alcampo-2026-09-18-sin-frescos`, apartado esa misma
    manana por venir sin la rama Frescos. Bronze no se borra nunca; si no esta,
    es que lo apartaron.
    """
    fichero = config.DATA / "gold" / "precio_diario.parquet"
    if not fichero.exists():
        return []
    hist = pl.read_parquet(fichero, columns=["fuente", "fecha"]).with_columns(
        pl.col("fecha").cast(pl.Utf8))
    en_bronze = cobertura.particiones_bronze()
    if not en_bronze:
        return []          # sin bronze no hay nada que contrastar, no se avisa
    fuera = cobertura.apartados()
    cuenta = hist.group_by(["fuente", "fecha"]).len()
    return sorted(
        (f["fuente"], f["fecha"], f["len"],
         fuera.get((f["fuente"], f["fecha"]), "SIN RASTRO"))
        for f in cuenta.iter_rows(named=True)
        if (f["fuente"], f["fecha"]) not in en_bronze
    )


def _fechas_por_cadena() -> list[tuple[str, str]]:
    raiz = config.DATA / "silver"
    ultimos: dict[str, str] = {}
    for parte in raiz.glob("fuente=*/fecha=*/part.parquet"):
        fuente = parte.parent.parent.name.split("=")[1]
        fecha = parte.parent.name.split("=")[1]
        if fecha > ultimos.get(fuente, ""):
            ultimos[fuente] = fecha
    return sorted(ultimos.items())


def ahorro(catalogo: pl.DataFrame) -> pl.DataFrame:
    """Por grupo comparable: cuanto separa a la cadena mas barata de la mas cara.

    Se compara por precio por unidad, no por precio total: dos formatos del mismo
    producto no se pueden restar. Y solo entran grupos con al menos dos cadenas,
    que son los unicos donde la palabra "mas barato" significa algo.
    """
    base = catalogo.filter(
        pl.col("precio_unidad_cent").is_not_null() & (pl.col("precio_unidad_cent") > 0))
    # Solo kg, litro y metro. En "ud" cada cadena cuenta una cosa distinta (un
    # paquete de seis rollos frente a un rollo suelto), y meter eso en la cifra
    # de ahorro la convierte en ruido: su diferencia mediana es del 24 % frente
    # al 12 % de las demas, y una de cada cuatro es directamente imposible.
    if "comparacion_fiable" in base.columns:
        base = base.filter(pl.col("comparacion_fiable"))
    # Y fuera las filas en disputa: son aquellas donde nuestro precio por unidad
    # y el de la cadena se contradicen por mas del doble y no se sabe cual de los
    # dos esta mal. Una fila asi no puede decidir donde sale mas barato nada.
    if "precio_comparable" in base.columns:
        base = base.filter(pl.col("precio_comparable").fill_null(True))
    # Y una sola unidad por grupo, la misma regla que usa la interfaz: dentro de
    # un grupo puede haber kg y litros a la vez, y restarlos no significa nada.
    base = comparacion.unidad_dominante(base)
    por_grupo = base.group_by("grupo_id").agg([
        pl.col("fuente").n_unique().alias("cadenas"),
        pl.col("precio_unidad_cent").min().alias("min_cent"),
        pl.col("precio_unidad_cent").max().alias("max_cent"),
        pl.col("nombre").first().alias("ejemplo"),
        pl.col("unidad_canon").first().alias("unidad"),
    ])
    return por_grupo.filter(pl.col("cadenas") > 1).with_columns(
        ((pl.col("max_cent") - pl.col("min_cent")) / pl.col("min_cent") * 100)
        .alias("dif_pct"))


def _crudo_de_hoy() -> list[tuple[str, int]]:
    """**De que cadenas hay captura de hoy, y cuantas.** *Para poder reanudar sin volver a pedirlo.*

    *`load_raw_bytes` sirve de la copia guardada **sin hacer la peticion**, pero solo si existe.*
    **Saber de que cadenas existe es lo que convierte «reanudar» en una decision y no en una
    esperanza** -- y es la mitad del criterio de F03 que el resumen no decia.

    *Se mira el disco, no la red: `data/raw/fuente=<cadena>/fecha=<hoy>/`.*
    """
    from core import storage

    hoy = str(config.hoy_local())
    salida = []
    for carpeta in sorted((storage.ROOT / "raw").glob(f"fuente=*/fecha={hoy}")):
        cuantas = sum(1 for _ in carpeta.glob("*.json.gz"))
        salida.append((carpeta.parent.name.removeprefix("fuente="), cuantas))
    return salida


def main(argv: list[str] | None = None) -> int:
    hoy = str(config.hoy_local())
    print(f"=== resumen {hoy} ===")

    fechas = _fechas_por_cadena()
    if not fechas:
        print("  no hay silver todavia")
        return 1
    # **Y el crudo de hoy, que es lo que se puede reanudar sin red.** *La linea de arriba dice lo que
    # se ha **procesado** (silver); esta dice de donde hay **captura guardada** -- y las dos cosas no
    # son lo mismo: una cadena puede tener silver de hoy y no tener crudo, o al reves.*
    reanudables = _crudo_de_hoy()
    if reanudables:
        total = sum(n for _c, n in reanudables)
        detalle = ", ".join(f"{c} {n}" for c, n in reanudables)
        print(f"  reanudable sin red: {total} capturas de hoy en {len(reanudables)} cadenas ({detalle})")
    else:
        print("  reanudable sin red: ninguna captura de hoy")

    viejas = [f"{c} ({d})" for c, d in fechas if d != hoy]
    print(f"  cadenas: {len(fechas)}"
          + (f" | SIN REFRESCAR HOY: {', '.join(viejas)}" if viejas else " | todas de hoy"))

    catalogo = _catalogo()
    if catalogo is None:
        print("  no hay grupos: falta ejecutar el emparejador")
        return 1
    print(f"  catalogo: {len(catalogo)} productos")

    historico = _historico()
    if historico is not None and "fecha" in historico.columns:
        dias = historico["fecha"].n_unique()
        print(f"  historico: {len(historico)} filas, {dias} "
              f"dia{'s' if dias != 1 else ''} acumulado{'s' if dias != 1 else ''}")
        huerfanos = dias_huerfanos()
        perdidos = [h for h in huerfanos if h[3] == "SIN RASTRO"]
        if perdidos:
            filas = sum(n for _, _, n, _ in perdidos)
            print(f"  AVISO: {filas} filas del historico sin bronze y sin rastro "
                  f"en descartados. No se pueden recalcular desde nada:")
            for fuente, fecha, n, _ in perdidos[:8]:
                print(f"      {fuente:10} {fecha}  {n} filas")
            if len(perdidos) > 8:
                print(f"      ...y {len(perdidos) - 8} mas")
        for fuente, fecha, n, motivo in huerfanos:
            if motivo != "SIN RASTRO":
                print(f"  nota: {n} filas de {fuente} del {fecha} vienen de una "
                      f"captura apartada ({motivo}); el bronze esta en "
                      f"data/debug/descartados")

    # **Y lo publicado, que era la pata que faltaba.** *El resumen decia lo **capturado** -- las
    # cadenas de hoy -- y lo **procesado** -- catalogo e historico --, pero no **que se esta
    # sirviendo**. Sin esto, un dia que no publico se lee igual que uno que si: medido el 13 de
    # octubre de 2026, `/api/estado` declaraba incoherente el catalogo y el resumen no decia nada.*
    version = publicacion.version_actual()
    if version is None:
        print("  publicado: NO hay version publicada: se sirve el catalogo suelto de data/gold")
    else:
        try:
            puntero = json.loads(publicacion.PUNTERO.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            puntero = {}
        print(f"  publicado: v{version}, el {puntero.get('publicado_en')}")
        # **Y si hay catalogo procesado que no se sirve, se dice.** *Es lo que de verdad importa de
        # esta linea: no que haya version, sino que la version **no se quede atras**.*
        dia_publicado = str(puntero.get("publicado_en", ""))[:10]
        dia_silver = max(d for _c, d in fechas)
        if dia_publicado and dia_publicado < dia_silver:
            # **Cuidado con lo que se afirma aqui.** *La primera version de este aviso decia «hay
            # catalogo procesado que NO se esta sirviendo», y **es falso**: la aplicacion lee
            # `data/gold` directamente (`catalogo.buscar`, con la conexion cacheada por el `mtime` de
            # `grupos.parquet`), no la version publicada. Lo que se sirve es el gold, que si es lo mas
            # nuevo; **la que se ha quedado atras es la version publicada**.*
            #
            # *Y ese es el hallazgo de verdad: `publicacion.ruta()` y `rutas()` -- que existen para
            # fijar la version por peticion -- **no los usa nadie**. El versionado se publica, el
            # puntero se mueve y `/api/estado` lo mira, pero **la aplicacion nunca lee una version**.*
            print(f"  AVISO: la version publicada es del {dia_publicado} y el silver llega al "
                  f"{dia_silver}: se publico por detras de lo procesado")
            print("      (la aplicacion lee `data/gold`, no la version: lo servido es lo de gold; "
                  "la que quedo atras es la publicacion)")

    comparables = ahorro(catalogo)
    con_letra = catalogo.filter(pl.col("calidad").is_not_null())
    etiqueta = con_letra.filter(
        pl.col("calidad_origen").is_in(["ingredientes", "ingredientes_off"]))
    # El nombre importa: `emparejar` cuenta TODOS los grupos con dos cadenas, y
    # aqui solo entran los medidos en kg, litro o metro. Los dos numeros son
    # correctos y durante semanas parecieron contradecirse en el mismo resumen
    # porque se llamaban igual.
    print(f"  grupos comparables por kg/l/m: {len(comparables)}")
    print(f"  con calidad A/B/C: {len(con_letra)} productos "
          f"({len(etiqueta)} leidos de la etiqueta)")
    for columna, etiqueta_texto in (("calidad_nota", "nota de composicion"),
                                    ("nutriscore", "Nutri-Score"),
                                    ("nova", "NOVA")):
        if columna in catalogo.columns:
            n = catalogo.filter(pl.col(columna).is_not_null()).height
            print(f"  con {etiqueta_texto}: {n} productos")
    if "nutriscore" not in catalogo.columns:
        print("  sin Nutri-Score: falta Open Food Facts "
              "(uv run python -m core.off)")

    if len(comparables):
        # Una diferencia de 200.000% no es una ganga: es una unidad mal leida.
        # Se separan a proposito, porque mezcladas taparian las diferencias
        # reales y ademas son la mejor lista de errores que hay que arreglar.
        creibles = comparables.filter(pl.col("dif_pct") <= TOPE_LLAMATIVO)
        grandes = comparables.filter((pl.col("dif_pct") > TOPE_LLAMATIVO)
                                     & (pl.col("dif_pct") <= TOPE_CREIBLE))
        raras = comparables.filter(pl.col("dif_pct") > TOPE_CREIBLE)
        mediana = creibles["dif_pct"].median() if len(creibles) else 0
        print(f"  entre la cadena mas barata y la mas cara de un mismo producto "
              f"hay un {mediana:.0f}% de diferencia (mediana)")
        print("  donde mas se nota hoy:")
        for fila in creibles.sort("dif_pct", descending=True).head(5).iter_rows(named=True):
            unidad = fila["unidad"] or "ud"
            print(f"    {fila['dif_pct']:5.0f}%  {fila['ejemplo'][:44]:44} "
                  f"{fila['min_cent'] / 100:8.2f} -> {fila['max_cent'] / 100:8.2f} EUR/{unidad}")
        if len(grandes):
            print(f"  {len(grandes)} grupos con diferencias grandes pero creibles "
                  f"(entre {TOPE_LLAMATIVO:.0f}% y {TOPE_CREIBLE:.0f}%): marca "
                  f"blanca contra marca, casi siempre")
        if len(raras):
            print(f"  aviso: {len(raras)} grupos con diferencias imposibles "
                  f"(>{TOPE_CREIBLE:.0f}%, o sea mas de {comparacion.FACTOR_INCREIBLE:.0f} "
                  f"veces): formato mal leido o mal emparejado")
            peor = raras.sort("dif_pct", descending=True).head(1).to_dicts()[0]
            print(f"         el peor: {peor['ejemplo'][:44]} "
                  f"({peor['min_cent'] / 100:.2f} -> {peor['max_cent'] / 100:.2f} "
                  f"EUR/{peor['unidad'] or 'ud'})")

    # Y los avisos, que es lo ultimo que pedia el §6 del encargo: *"que el resumen
    # diario diga cuantas saltaron"*. Lo mide `projects/cesta/avisos.py`, que corre
    # justo antes que esto, y lo deja escrito en `data/avisos.json`; aqui solo se lee
    # y se traduce. **La base no se consulta desde aqui**: desde el PC no se llega a
    # PostgreSQL (no publica su puerto), y si el paso no ha podido mirarlos, esta
    # linea tiene que decir "no lo se" en vez de un cero, que se leeria como "no ha
    # saltado nada" cuando lo que pasa es que no se ha mirado.
    print("  " + avisos.frase(avisos.lee()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
