"""Empareja el mismo producto entre cadenas y le pone calidad A/B/C.

    uv run python -m projects.cesta.emparejar            # construye los grupos
    uv run python -m projects.cesta.emparejar --medir    # mide contra los EAN

Escribe en data/gold:
    enlaces.parquet   pares (i, j) con parecido y nivel identico/equivalente
    grupos.parquet    una fila por producto con grupo_id, calidad y su origen
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import itertools
import json
import time

import polars as pl

from core import config
from core import equivalencias as eq
from core.calidad import letras, por_precio, puntua
from core.matching import (
    CAMPOS_PARA_EMPAREJAR,
    UNIDADES_FIABLES,
    _ean,
    agrupar_enlaces,
    enlaces,
)
from core.normalize import parse_formato

# Medido el 8 sep escondiendo el EAN a 65.155 productos, contra los 1.767 pares
# que ya sabemos ciertos. Bajar de 0,65 a 0,55 sube el acierto del 46 % al 54 % y
# la precision del nivel identico apenas se mueve (68 % frente a 66 %). Con 0,50
# se llega al 55 %, pero ya empieza a juntar cosas que solo se parecen de nombre.
UMBRAL = 0.55

# El canal de vectores **apagado en la pasada diaria**, y esta vez no por el coste
# -- que ya no lo es -- sino porque **rompe una garantia del encargo**.
#
# Lo que se gana, medido sobre el mismo catalogo (misma huella) el 23 de septiembre
# de 2026:
#
#     metrica                    sin vectores   con vectores   diferencia
#     enlaces                          22.705         26.703   +3.998 (+18 %)
#     grupos comparables                7.992          8.394     +402 (+5 %)
#     productos comparables            22.693         24.823   +2.130 (+9,4 %)
#     calidad asignada                 12.338         14.153   +1.815 (+14,7 %)
#     recall de --medir                 65 %           73 %
#
# Y lo que se rompe, medido igual:
#
#     conflictos de asignacion              0            861
#     peor caso (parejas de un producto
#       en la misma cadena)                 2              3
#
# El encargo pide **cero conflictos de asignacion**, y con el canal puesto hay 861
# productos emparejados con **tres** productos de la misma cadena. Contado sobre el
# `equivalencia.parquet` de las dos pasadas.
#
# La causa esta en como entra el canal: `enlaces()` le da su propio reparto hungaro
# y su propio juego de `ocupados` (`core/matching.py`, `for canal in ("marca",
# "equivalente", "vector")`), asi que el 1-a-1 se respeta **dentro del canal** y no
# entre canales. Los dos del nombre nunca produjeron un conflicto; el tercero si.
#
# **Lo que hay que hacer antes de encenderlo**: que los candidatos del canal de
# vectores pasen por el mismo reparto y el mismo `ocupados` que los otros dos. Se
# vuelve a medir esto entero -- recall **y** conflictos -- y entonces se enciende.
# Un canal que sube el recall rompiendo la asignacion no es una mejora: es otro
# emparejador.
#
# (El coste, que era el otro obstaculo, ya esta resuelto: `candidatos()` lee los
# vectores en SQL en vez de traerlos a Python, y el catalogo entero son 239,9 s y
# 270 MB, donde antes no terminaba en 62 minutos.)
USAR_VECTORES = False
COLUMNAS = ("fuente", "id_fuente", "nombre", "marca", "cantidad", "unidad_canon",
            "ean", "precio_cent", "precio_unidad_cent", "precio_ref_canon_cent",
            "unidad_ref_canon",
            # Si el tamano lo publica la cadena o lo confirma su propio precio de
            # referencia, o si es un "1 ud" de relleno. Sin esta columna el
            # emparejador trata igual un dato y una ausencia disfrazada: los dos
            # valen 1, pero uno sirve para bloquear y el otro no.
            # Ver docs/DIAGNOSTICO-MATCHING.md §6.
            "cantidad_fiable",
            # Lo que necesita la ficha del producto en el movil. Estaba en silver
            # y no llegaba a gold, asi que la app no podia ensenar una foto ni
            # decir si algo lleva gluten: dos cosas que se miran en el pasillo
            # mucho mas que el Nutri-Score.
            "imagen", "alergenos", "ingredientes", "origen", "promo_txt",
            "categoria", "url",
            # La seccion comun a las cinco cadenas: sin ella no hay pantalla de
            # pasillos ni lista ordenada por el recorrido de la tienda. Ver
            # `pipeline._anota_seccion`.
            "seccion",
            # Lo que se fue anadiendo al contrato entre el 15 y el 17 de
            # septiembre y se quedaba en silver. El contrato tenia 40 columnas y
            # esta tupla 17: nueve campos recien conquistados a las cadenas
            # (sellos, nutricion, conservacion...) no llegaban a gold, asi que
            # la app no podia ni ensenarlos ni filtrar por ellos. Un dato que no
            # cruza la frontera de gold es un dato que no existe.
            "sellos", "sellos_origen", "certificados", "conservacion", "es_marca_propia",
            "nutricion", "nutricion_por", "tipo_producto", "envase",
            "peso_escurrido_g", "peso_neto_g", "dias_caducidad", "descripcion",
            "grado_alcohol",
            "promo", "promo_hasta",
            # De la primera pasada de `auditar_crudo.py`, el 17 de septiembre.
            # `promo_club` es la mas importante de las seis: sin ella, las 200
            # ofertas de tarjeta de DIA se anunciarian como rebajas que no
            # existen en el ticket.
            "promo_club", "promo_solo_online", "es_recall", "es_alcohol", "peso_variacion_pct",
            "distintivo", "advertencias",
            # Si el precio por unidad de esta fila sirve para comparar. Lo decide
            # silver (ver docs/PRECIO-POR-UNIDAD.md) y hasta hoy se quedaba ahi:
            # gold no lo sabia, asi que las 72 filas "en disputa" -- donde
            # nuestro precio y el de la cadena se llevan mas del doble -- seguian
            # decidiendo donde estaba mas barato algo. El resumen del 18 de
            # septiembre las tenia como los peores casos del dia.
            "precio_comparable", "proc_precio_unidad", "unidades_pack")


def catalogo_actual() -> pl.DataFrame:
    """Ultima instantanea de cada cadena. Si una no capturo hoy, entra la suya."""
    raiz = config.DATA / "silver"
    ultimos = {}
    for parte in sorted(raiz.glob("fuente=*/fecha=*/part.parquet")):
        fuente = parte.parent.parent.name.split("=")[1]
        fecha = parte.parent.name.split("=")[1]
        if fuente not in ultimos or fecha > ultimos[fuente][0]:
            ultimos[fuente] = (fecha, parte)
    if not ultimos:
        raise FileNotFoundError("no hay silver; ejecuta antes el pipeline")
    marcos = []
    for _, parte in ultimos.values():
        df = pl.read_parquet(parte)
        # Un silver viejo puede no tener una columna nueva del contrato. Se
        # rellena a None en vez de reventar: asi un dia de historico anterior al
        # cambio sigue entrando, que es justo para lo que se guarda el historico.
        faltan = [c for c in COLUMNAS if c not in df.columns]
        if faltan:
            df = df.with_columns([pl.lit(None).alias(c) for c in faltan])
        marcos.append(df.select(COLUMNAS))
    return pl.concat(marcos, how="diagonal_relaxed")


def _completa_cantidad(filas: list[dict]) -> int:
    """Respaldo para las cadenas que no publican campo de formato.

    Duplica a proposito lo que ya hace el pipeline, para que medir el
    emparejador no dependa de que el silver este recien regenerado.
    """
    recuperadas = 0
    for r in filas:
        if r.get("cantidad") is not None:
            continue
        cant, uni, _ = parse_formato(r.get("nombre") or "")
        ref, ref_uni = r.get("precio_ref_canon_cent"), r.get("unidad_ref_canon")
        if (cant and uni and r.get("precio_cent") and ref and uni == ref_uni
                and abs(r["precio_cent"] / cant - ref) / ref < 0.05):
            r["cantidad"], r["unidad_canon"] = cant, uni
            recuperadas += 1
    return recuperadas


def ingredientes_por_producto() -> dict[tuple[str, str], str]:
    """Lo que publican las fichas maestras. Hoy: Mercadona y DIA."""
    salida = {}
    carpeta = config.DATA / "master"
    for fichero in sorted(carpeta.glob("*.json.gz")):
        fuente = fichero.name.split(".")[0]
        with gzip.open(fichero, "rt", encoding="utf-8") as fh:
            for id_fuente, ficha in json.load(fh).items():
                texto = ficha.get("ingredientes")
                if texto:
                    salida[(fuente, str(id_fuente))] = texto
    return salida


def _clave_ean(valor) -> str | None:
    return _ean(valor)


def externo_por_ean() -> dict[str, dict]:
    """Open Food Facts, por codigo de barras. {} si no se ha descargado.

    Es lo que iguala a las cadenas que no publican ingredientes: Carrefour no
    publica ninguno y aqui gana 4.751. Y es la unica fuente de Nutri-Score que
    hay, porque no lo da ningun supermercado.
    """
    fichero = config.DATA / "externo" / "off_es.parquet"
    if not fichero.exists():
        return {}
    import duckdb

    filas = duckdb.connect().execute(f"""
        SELECT ltrim(regexp_replace(code, '[^0-9]', '', 'g'), '0') AS k,
               ingredients_text, nutriscore_grade, nova_group
        FROM read_parquet('{fichero}')
        WHERE code IS NOT NULL
    """).fetchall()
    return {k: {"ingredientes": ing, "nutriscore": ns, "nova": nova}
            for k, ing, ns, nova in filas if k and len(k) >= 8}


def grupos_de(enlaces_: list[tuple[int, int, float, str]], filas: list[dict]) -> list[int]:
    """Id de grupo por producto. El freno contra el grupo monstruo vive en `core`.

    Aqui habia un union-find a pelo, y era el que juntaba "Cerveza Dia Ramblers"
    con "Guinness" en un grupo de 329 productos: un grupo es lo que queda
    conectado, y eso se propaga. Ver `core.matching.agrupar_enlaces`.

    Se le pasan los precios por unidad porque el freno necesita saber si un
    enlace flojo esta a punto de crear un grupo ANCHO, y ancho solo lo puede
    decir el precio.
    """
    return agrupar_enlaces(
        enlaces_, len(filas),
        precios=[(f.get("unidad_canon"), f.get("precio_unidad_cent"))
                 for f in filas])


def composicion(filas: list[dict], ingredientes: dict,
                externo: dict) -> tuple[list, list]:
    """Ingredientes de cada producto y de donde salen.

    Primero lo que publica la cadena, que es el dato de casa; si no lo publica,
    lo que dice Open Food Facts para ese codigo de barras. El origen viaja
    siempre al lado del dato: un ingrediente prestado de fuera no es lo mismo que
    uno leido en la ficha del producto, aunque los dos sirvan.
    """
    textos: list[str | None] = []
    procedencias: list[str | None] = []
    for fila in filas:
        propio = ingredientes.get((fila["fuente"], str(fila["id_fuente"])))
        if propio:
            textos.append(propio)
            procedencias.append("cadena")
            continue
        fuera = externo.get(_ean(fila.get("ean")) or "")
        if fuera and fuera.get("ingredientes"):
            textos.append(fuera["ingredientes"])
            procedencias.append("off")
        else:
            textos.append(None)
            procedencias.append(None)
    return textos, procedencias


def calidad_de_grupos(filas: list[dict], grupo: list[int],
                      textos: list, procedencias: list) -> tuple[list, list]:
    """Letra y origen de la letra, producto a producto."""
    por_grupo: dict[int, list[int]] = {}
    for i, g in enumerate(grupo):
        por_grupo.setdefault(g, []).append(i)

    letra: list[str | None] = [None] * len(filas)
    origen: list[str] = ["sin_datos"] * len(filas)
    for indices in por_grupo.values():
        notas = [puntua(textos[i]) for i in indices]
        asignadas = letras(notas)
        for pos, i in enumerate(indices):
            if asignadas[pos]:
                letra[i] = asignadas[pos]
                origen[i] = ("ingredientes" if procedencias[i] == "cadena"
                             else "ingredientes_off")

        # Los que quedan son de cadenas que no publican ingredientes. Dejarlos en
        # blanco seria justo el "dato no encontrado" que no queremos: dentro de un
        # grupo ya comparable, el precio por unidad es una senal debil pero real
        # de gama. Se rellena con ella y se marca como tal, nunca como etiqueta.
        faltan = [i for i in indices if letra[i] is None]
        if faltan:
            por_p = por_precio([filas[i].get("precio_unidad_cent") for i in faltan])
            for pos, i in enumerate(faltan):
                if por_p[pos]:
                    letra[i], origen[i] = por_p[pos], "precio"
    return letra, origen


def medir(filas: list[dict], umbral: float, comparar_vectores: bool = False) -> None:
    """Esconde el EAN, empareja por nombre y cuenta aciertos.

    Mide **la configuracion que se usa de verdad**, la que dice `USAR_VECTORES`.
    El numero que sale de aqui es el que se compara con el 65 % del encargo, y
    medir otra cosa seria contestar a otra pregunta.

    Con `comparar_vectores=True` mide ademas la pasada **con** el canal de
    vectores. Esa es la pregunta de la Fase 3 -- ¿sube el recall o no? --, y por
    eso `enlaces` tiene un interruptor aparte para los vectores en vez de ir
    pegado al del EAN. Va apagado por defecto porque hoy esa pasada **no
    termina** (mas de 62 minutos, ver el comentario de `USAR_VECTORES`): hay que
    pedirla a proposito y con el rato por delante.
    """
    por_ean: dict[str, list[int]] = {}
    for i, f in enumerate(filas):
        e = _ean(f.get("ean"))
        if e:
            por_ean.setdefault(e, []).append(i)
    verdad = {(min(a, b), max(a, b))
              for ids in por_ean.values()
              for a, b in itertools.combinations(ids, 2)
              if filas[a]["fuente"] != filas[b]["fuente"]}
    if not verdad:
        print("  no hay pares con el mismo EAN en cadenas distintas: nada que medir")
        return
    print(f"  verdad: {len(verdad)} pares entre cadenas con el mismo EAN", flush=True)
    pasadas = [("sin vectores", False), ("con vectores", True)]
    if not comparar_vectores:
        pasadas = [(("con vectores" if USAR_VECTORES else "sin vectores"),
                    USAR_VECTORES)]
        print(f"  (la configuracion de hoy es USAR_VECTORES={USAR_VECTORES}; para "
              f"medir las dos, --comparar-vectores)", flush=True)
    for etiqueta, vectores in pasadas:
        ls = enlaces(filas, umbral=umbral, usar_ean=False,
                     usar_vectores=vectores)
        pares = {(min(i, j), max(i, j)) for i, j, _s, _n in ls}
        acertados = len(pares & verdad)
        # Cuantos enlaces comprobables comparten codigo. Antes se imprimia "de los
        # marcados identico, cuantos comparten codigo", y desde el 22 de septiembre
        # eso es una tautologia: `nivel()` ya no llama identico a dos productos con
        # codigos distintos. Esta proporcion si informa.
        con_ean = iguales = 0
        for i, j, _s, _n in ls:
            ea, eb = _ean(filas[i].get("ean")), _ean(filas[j].get("ean"))
            if ea and eb:
                con_ean += 1
                iguales += ea == eb
        # `flush`: la pasada con vectores puede tardar mas de una hora (ver
        # `USAR_VECTORES`), y sin esto, con la salida redirigida a un fichero, la
        # linea de "sin vectores" -- que es la que contesta la pregunta y la que
        # tarda 90 segundos -- no se ve hasta que termina la otra.
        print(f"  {etiqueta:14s} {len(ls):6d} enlaces  "
              f"encuentra {acertados} ({100 * acertados / len(verdad):.0f}%)  "
              f"de los {con_ean} comprobables comparten codigo {iguales} "
              f"({100 * iguales / max(con_ean, 1):.0f}%)", flush=True)
    print("  ojo: un enlace 'equivalente' con EAN distinto NO es un fallo, es el")
    print("       objetivo. Comparar marcas blancas es imposible por codigo.")


def _huella(filas: list[dict]) -> str:
    """Una firma del catalogo: que productos hay y en que orden.

    Los enlaces son pares de **posiciones** en esta lista, no de identificadores.
    Reutilizarlos contra otro catalogo empareja productos al azar, y encima sin
    hacer ruido: saldrian grupos con cosas que no tienen nada que ver.

    La primera version solo comprobaba que el indice mas alto cupiera. No basta:
    un catalogo de otro dia con el mismo numero de filas, o con mas, pasa esa
    prueba y aun asi tiene los productos en otras posiciones. Esto firma la
    secuencia entera de (cadena, id), que es lo unico que de verdad garantiza que
    las posiciones significan lo mismo.
    """
    h = hashlib.sha1()
    for f in filas:
        h.update(f"{f.get('fuente')}\x00{f.get('id_fuente')}\n".encode())
    return h.hexdigest()


def _camino_huella():
    return config.DATA / "gold" / "enlaces_huella.json"


def _guardar_huella(filas: list[dict]) -> None:
    camino = _camino_huella()
    camino.parent.mkdir(parents=True, exist_ok=True)
    camino.write_text(json.dumps({"filas": len(filas), "huella": _huella(filas)}),
                      encoding="utf-8")


def _enlaces_guardados(filas: list[dict]) -> list[tuple[int, int, float, str]] | None:
    """Los enlaces del ultimo calculo, si son de ESTE mismo catalogo."""
    camino = config.DATA / "gold" / "enlaces.parquet"
    if not camino.exists() or not _camino_huella().exists():
        return None
    try:
        guardada = json.loads(_camino_huella().read_text(encoding="utf-8"))
        if guardada.get("huella") != _huella(filas):
            return None
        df = pl.read_parquet(camino)
    except Exception:  # noqa: BLE001
        return None
    if df.is_empty() or "i" not in df.columns:
        return None
    if int(df["i"].max()) >= len(filas) or int(df["j"].max()) >= len(filas):
        return None
    return list(zip(df["i"].to_list(), df["j"].to_list(),
                    df["parecido"].to_list(), df["nivel"].to_list(), strict=True))


def main(argv: list[str] | None = None) -> int:
    # argv explicito, no sys.argv: run.py llama a este main() dentro de su propio
    # proceso, y sin esto argparse leia los argumentos de run.py y reventaba con
    # "unrecognized arguments: --solo alcampo".
    ap = argparse.ArgumentParser(prog="emparejar")
    ap.add_argument("--umbral", type=float, default=UMBRAL)
    ap.add_argument("--medir", action="store_true",
                    help="mide contra los pares ya ciertos por EAN y no escribe")
    ap.add_argument("--comparar-vectores", action="store_true",
                    help="mide tambien con el canal de vectores. Hoy esa pasada "
                         "no termina (ver USAR_VECTORES), asi que va aparte")
    ap.add_argument("--reusar-enlaces", action="store_true",
                    help="no recalcula los enlaces: reutiliza data/gold/enlaces.parquet")
    a = ap.parse_args(argv)

    t0 = time.monotonic()
    df = catalogo_actual()
    # Solo las columnas que el emparejador mira, y ademas `cantidad` y
    # `unidad_canon`, que `_completa_cantidad` puede corregir. Construir 52.000
    # diccionarios con las 40 columnas de gold cuesta tiempo y memoria para
    # nada: el emparejador usa seis. Ver core/matching.adelgaza.
    columnas_util = list(dict.fromkeys(
        # `id_fuente` para cruzar con las fichas maestras y
        # `precio_unidad_cent` para la gama por precio: sin el, la letra se
        # quedaba solo en los 2.656 productos con ingredientes en vez de 11.463.
        [*CAMPOS_PARA_EMPAREJAR, "id_fuente", "cantidad", "unidad_canon",
         "precio_cent", "precio_unidad_cent", "precio_ref_canon_cent",
         "unidad_ref_canon", "ean"]))
    filas = df.select([c for c in columnas_util if c in df.columns]).to_dicts()
    recuperadas = _completa_cantidad(filas)
    cadenas = df["fuente"].n_unique()
    print(f"  {len(filas)} productos de {cadenas} cadenas"
          + (f" ({recuperadas} cantidades deducidas del nombre)" if recuperadas else ""))

    if a.medir:
        medir(filas, a.umbral, comparar_vectores=a.comparar_vectores)
        print(f"emparejar: medicion en {time.monotonic() - t0:.0f}s")
        return 0

    # Recalcular los enlaces cuesta un minuto y medio: son 16,7 millones de
    # pares candidatos. Cuando el cambio no toca **ninguna** de las seis
    # columnas que mira el emparejador (fuente, nombre, marca, cantidad,
    # unidad_canon, ean), los enlaces de ayer son exactamente los de hoy, y
    # reutilizarlos deja iterar en la calidad y en las columnas nuevas sin pagar
    # ese minuto y medio cada vez.
    #
    # Se comprueba que el fichero tenga el mismo numero de filas del que salio:
    # los enlaces son indices de posicion, asi que usarlos contra un catalogo de
    # otro tamano emparejaria productos al azar. Si no cuadra, se recalcula.
    ls = None
    if a.reusar_enlaces:
        ls = _enlaces_guardados(filas)
        if ls is None:
            print("  los enlaces guardados son de otro catalogo: se recalculan")
        else:
            print(f"  {len(ls)} enlaces reutilizados de data/gold/enlaces.parquet")
    if ls is None:
        ls = enlaces(filas, umbral=a.umbral, usar_vectores=USAR_VECTORES)
    grupo = grupos_de(ls, filas)
    ingredientes = ingredientes_por_producto()
    externo = externo_por_ean()
    if not externo:
        print("  aviso: falta data/externo/off_es.parquet, asi que no hay "
              "Nutri-Score ni ingredientes de fuera  (uv run python -m core.off)")
    textos, procedencias = composicion(filas, ingredientes, externo)
    letra, origen = calidad_de_grupos(filas, grupo, textos, procedencias)
    # La letra necesita al menos tres productos con datos en el grupo, asi que
    # muchos productos con ingredientes se quedan sin ella. La nota, en cambio,
    # se puede calcular siempre que haya lista de ingredientes, y es lo que
    # permite ordenar dentro de una busqueda aunque no haya con quien comparar.
    notas = [puntua(t) for t in textos]
    nutriscore = [(externo.get(_ean(f.get("ean")) or "") or {}).get("nutriscore")
                  for f in filas]
    nova = [(externo.get(_ean(f.get("ean")) or "") or {}).get("nova")
            for f in filas]

    salida = df.with_columns([
        pl.Series("grupo_id", grupo, dtype=pl.Int32),
        pl.Series("calidad", letra, dtype=pl.Utf8),
        pl.Series("calidad_origen", origen, dtype=pl.Utf8),
        pl.Series("calidad_nota", notas, dtype=pl.Float64),
        pl.Series("nutriscore", nutriscore, dtype=pl.Utf8),
        pl.col("unidad_canon").is_in(UNIDADES_FIABLES).fill_null(False)
          .alias("comparacion_fiable"),
        pl.Series("nova", nova, dtype=pl.Int32),
        pl.Series("cantidad", [f["cantidad"] for f in filas], dtype=pl.Float64),
        pl.Series("unidad_canon", [f["unidad_canon"] for f in filas], dtype=pl.Utf8),
    ])
    from core.storage import write_parquet_file
    write_parquet_file(salida, config.DATA / "gold" / "grupos.parquet")
    write_parquet_file(
        pl.DataFrame(
            {"i": [x[0] for x in ls], "j": [x[1] for x in ls],
             "parecido": [x[2] for x in ls], "nivel": [x[3] for x in ls]},
            schema={"i": pl.Int32, "j": pl.Int32, "parecido": pl.Float64,
                    "nivel": pl.Utf8}),
        config.DATA / "gold" / "enlaces.parquet")
    _guardar_huella(filas)

    multi = salida.group_by("grupo_id").agg(
        pl.col("fuente").n_unique().alias("cadenas")).filter(pl.col("cadenas") > 1)
    dudosos = salida.join(multi, on="grupo_id").filter(
        ~pl.col("comparacion_fiable"))["grupo_id"].n_unique()
    identicos = sum(1 for x in ls if x[3] == "identico")
    print(f"  {len(ls)} enlaces ({identicos} identicos, {len(ls) - identicos} equivalentes)")
    print(f"  {len(multi)} grupos comparables entre cadenas "
          f"({dudosos} de ellos en 'ud', donde cada cadena cuenta distinto)")
    con_letra = salida.filter(pl.col("calidad").is_not_null())
    de_etiqueta = con_letra.filter(
        pl.col("calidad_origen").is_in(["ingredientes", "ingredientes_off"]))
    con_nota = salida.filter(pl.col("calidad_nota").is_not_null())
    print(f"  calidad asignada a {len(con_letra)} productos "
          f"({len(de_etiqueta)} leyendo ingredientes, el resto por precio)")
    print(f"  nota de composicion en {len(con_nota)} productos "
          f"(la letra pide tres comparables en el grupo; la nota, no)")
    con_ns = salida.filter(pl.col("nutriscore").is_not_null())
    if len(con_ns):
        print(f"  Nutri-Score en {len(con_ns)} productos "
              f"({salida.filter(pl.col('nova').is_not_null()).height} con NOVA)")

    # La pasada entera, versionada. Los ficheros de arriba son "lo de hoy" y se
    # reescriben; esto es el registro de que paso cada dia, con clave estable y
    # con el motivo de cada par, y no se toca nunca mas.
    ejecucion_id = eq.id_de_ejecucion()
    equivalencias = eq.filas_de_equivalencia(filas, ls, ejecucion_id)
    # Si esta pasada uso los embeddings o no: lo que manda es `USAR_VECTORES`, no
    # lo que haya en disco. El fichero puede estar entero y la pasada no haberlo
    # mirado, y entonces el resumen diria "si" de una pasada que no los uso. Sin
    # esto, dos ejecuciones con numeros distintos pareceran iguales y no se sabra
    # por que.
    from core import embeddings as emb
    embed_cache = USAR_VECTORES and emb.camino().exists()
    metricas = {
        "enlaces": float(len(ls)),
        "identicos": float(sum(1 for x in ls if x[3] == "identico")),
        "grupos_comparables": float(len(multi)),
        "productos_comparables": float(
            salida.filter(pl.col("grupo_id").is_in(multi["grupo_id"])).height),
        "calidad_asignada": float(len(con_letra)),
        "grupos_dudosos_ud": float(dudosos),
    }
    carpeta = eq.escribe_ejecucion(
        ejecucion_id, equivalencias, metricas,
        {"productos": len(filas), "huella_catalogo": eq.huella_catalogo(filas),
         "umbral": a.umbral,
         # Si esta pasada uso los embeddings o no. Sin esto, dos ejecuciones con
         # numeros distintos pareceran iguales y no se sabra por que.
         "embeddings": bool(embed_cache)})
    print(f"  equivalencias versionadas en {carpeta.name} "
          f"({len(equivalencias)} pares con su motivo)")
    print(f"  embeddings: {'si, canal de vectores activo' if embed_cache else 'no'}"
          f"{'' if embed_cache else f' (USAR_VECTORES={USAR_VECTORES}: ver por que arriba)'}")
    print(f"emparejar: hecho en {time.monotonic() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
