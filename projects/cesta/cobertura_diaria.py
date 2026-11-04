"""Cuanto trajo cada cadena hoy, comparado con lo que esa cadena sabe traer.

**Por que existe, habiendo ya un control de cobertura.** En `core/cobertura.py` hay dos
controles, y los dos son buenos; lo que se les escapa es concreto:

  - `revisa()` compara **rama por rama contra el bronze anterior**. Eso caza "hoy falta Frescos
    entero", que es el caso del 18 de septiembre de 2026. Lo que no caza es una bajada lenta:
    desde el momento en que la captura de ayer ya viene corta, la de ayer es la vara y el
    hundimiento se mide contra si mismo. Alcampo paso de 37.019 filas de bronze a 24.120 a lo
    largo de dos dias y **ninguna rama se hundio de golpe**: todas bajaron un poco.
  - `sin_bronze()` mira las cadenas que **dijeron haber ido bien** y no dejaron fichero. Bien
    pensado (una cadena que se nego a escribir ya devuelve error), pero deja fuera justo el otro
    caso: la cadena que **falla y no escribe nada**. Alcampo no trajo una sola captura del 2 al 5
    de octubre y ningun control lo dijo: el verificador de la ingesta comprueba coherencia --lo
    que la cadena declaro, lo guardamos-- y una cadena que no llega a declarar nada es coherente
    consigo misma.

De ahi las dos decisiones de aqui:

  1. **La referencia es el maximo de una ventana larga**, no la captura de ayer ni la mediana de
     los ultimos dias. La pregunta no es "trajiste lo mismo que ayer" sino "trajiste lo que esta
     cadena es capaz de traer". Con la mediana, la captura corta se acaba dando por buena.
  2. **Se mira cada cadena, haya dicho lo que haya dicho.** Que una cadena falle y no traiga nada
     es exactamente lo que hay que ver, no una razon para no mirar.

    uv run python -m projects.cesta.cobertura_diaria                # hoy
    uv run python -m projects.cesta.cobertura_diaria --fecha 2026-10-02 --dias 30

Sale 0 si todas traen lo suyo y 1 si alguna se quedo corta o no trajo nada. **No arregla nada:
avisa**, y en la cadena diaria se llama sin hacer fallar el dia --como `verificar_docs`--, porque
una cadena corta no es motivo para no recoger las otras cuatro.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from contextlib import suppress
from pathlib import Path
from zoneinfo import ZoneInfo

import duckdb
import polars as pl

from core import config

FUENTES = ("alcampo", "aldi", "carrefour", "dia", "mercadona")

# --- la cobertura que se declara, no la que se supone ------------------------
#
# **Por que existe esto.** `data/cobertura/` lo leen el manifiesto de publicacion y
# `GET /api/estado`, y hasta el 4 de noviembre de 2026 **solo escribia ahi Lidl** -- porque
# solo Lidl tiene un alcance parcial que declarar. Las cinco cadenas de catalogo capturaban
# todos los dias y no declaraban nada, asi que el dato publicado decia «cobertura: una sola
# cadena, Lidl, 21 dias» y el panel no podia saber que Mercadona llevaba 57 dias.
#
# Ahora cada cadena de catalogo declara su dia **con lo medido sobre su bronce**: filas,
# referencia y de que dia es, huecos y veredicto (la misma `veredicto` que el aviso, no una
# copia) y, ademas, **que produjo el dia**: ids nuevos, precios cambiados y desaparecidos
# frente a su captura anterior. Eso es lo que convierte «trajo filas» en «produjo datos
# nuevos», que es lo que hay que demostrar.
COBERTURA = "catalogo_diario"
ETIQUETA = "catalogo diario medido"
METODO = "medido sobre data/bronze y data/gold; no autodeclarado por el colector"
# Con un hueco (un domingo sin captura, p. ej.) no se compara contra un dia de hace un mes:
# la novedad se mide contra la ultima captura de la semana anterior, y el fichero dice cual.
DIAS_PARA_NOVEDAD = 7

# Por debajo de esto, la captura se considera corta. Alcampo paso de 37.019 a 24.120 filas (el
# 65 %) sin que saltara nada, asi que el umbral tiene que estar muy por encima de ese 65 %: una
# cadena que pierde uno de cada tres productos esta rota, y una que pierde uno de cada diez
# tambien merece que alguien lo mire.
MINIMO_PCT = 90.0
DIAS_DE_VENTANA = 30


def filas_por_dia(dias: int = DIAS_DE_VENTANA) -> dict[str, dict[str, int]]:
    """{fuente: {fecha: filas}} leido del bronze. Sin ficheros, un diccionario vacio."""
    carpeta = config.DATA / "bronze"
    if not carpeta.exists():
        return {}
    patron = (carpeta / "**" / "*.parquet").as_posix()
    con = duckdb.connect()
    con.execute("SET enable_progress_bar=false")
    try:
        filas = con.execute(
            f"""SELECT CAST(fecha AS VARCHAR) AS fecha, fuente, count(*) AS n
                FROM read_parquet('{patron}', hive_partitioning=true)
                WHERE fecha IS NOT NULL
                GROUP BY 1, 2""").fetchall()
    except Exception:  # noqa: BLE001
        return {}
    salida: dict[str, dict[str, int]] = {}
    for fecha, fuente, n in filas:
        salida.setdefault(fuente, {})[fecha] = n
    return salida


def veredicto(serie: dict[str, int], hoy: str, dias: int = DIAS_DE_VENTANA,
              minimo_pct: float = MINIMO_PCT) -> dict:
    """Como de corta es la captura de `hoy` frente al maximo de la ventana.

    `serie` es {fecha: filas} de UNA cadena. Devuelve, con nombres que se puedan leer en un
    aviso: `hoy`, `filas`, `referencia` (el maximo de la ventana, sin contar hoy), `pct`,
    `dias_sin_datos` (huecos dentro de la ventana) y `veredicto` (`ok`, `corta` o `sin datos`).

    El maximo y no la mediana, a proposito: ver la cabecera. Sin contar hoy, para que una captura
    buena no suba su propia vara.

    **La ventana es el calendario, no las fechas que hay en la serie.** Un dia sin fichero no
    aparece en `serie` --no hay nada que leer--, y la primera version contaba los huecos mirando
    la serie, asi que una cadena que llevaba cuatro dias sin traer nada salia con **cero huecos**.
    Justo el caso que esto existe para cazar.
    """
    fin = dt.date.fromisoformat(hoy)
    calendario = [(fin - dt.timedelta(days=i)).isoformat() for i in range(1, dias + 1)]
    referencia = max((serie.get(f, 0) for f in calendario), default=0)
    # **De que dia es la vara.** Sin esto, «corta» no se puede interpretar: el 17 de
    # octubre de 2026 Alcampo trajo 28.022 cuando lo normal era 22.800-24.300, y desde
    # entonces una captura de 23.416 -- normal, y mejor que la de ayer -- sale «corta»
    # todos los dias. El veredicto se queda como esta (la vara no se baja sola), pero
    # ahora se puede leer contra que mide.
    dia_referencia = None
    if referencia:
        # En orden (ayer -> atras): si el maximo se repite varios dias, la referencia es el
        # **mas reciente** de ellos, que es el que se puede leer como «su mejor dia ultimo».
        for f in calendario:
            if serie.get(f, 0) == referencia:
                dia_referencia = f
                break
    filas_hoy = serie.get(hoy, 0)
    pct = (100.0 * filas_hoy / referencia) if referencia else 0.0
    dias_sin_datos = sum(1 for f in calendario if not serie.get(f))
    if filas_hoy == 0:
        estado = "sin datos"
    elif referencia and pct < minimo_pct:
        estado = "corta"
    else:
        estado = "ok"
    # **Y cuanto cambio respecto a la ULTIMA captura**, que es la otra mitad de la frase:
    # «corta contra el maximo» y «+2,8 % sobre ayer» pueden ser las dos verdad a la vez.
    #
    # **El orden importa y estaba mal.** `calendario` va de ayer hacia atras (indice 0 = ayer),
    # asi que recorrerlo con `reversed` empieza por **el dia mas antiguo de la ventana**: el
    # 4/11/2026 el informe decia «alcampo +1,7 % sobre la captura anterior» comparando con el
    # 5/10; contra el 3/11 era **+2,8 %**. Y en Aldi hasta cambiaba el signo (+6,8 % publicado
    # frente a -4,4 % real). Se recorre en orden: la primera captura que hay es la penultima.
    anterior = next((serie[f] for f in calendario if serie.get(f)), None)
    vs_anterior = (round(100.0 * (filas_hoy / anterior - 1), 1)
                   if anterior and filas_hoy else None)
    return {"hoy": hoy, "filas": filas_hoy, "referencia": referencia,
            "referencia_fecha": dia_referencia,
            "pct": round(pct, 1), "dias_en_la_ventana": len(calendario),
            "dias_sin_datos": dias_sin_datos, "vs_anterior_pct": vs_anterior,
            "veredicto": estado}


def veredictos(hoy: str | None = None, dias: int = DIAS_DE_VENTANA,
               minimo_pct: float = MINIMO_PCT) -> dict[str, dict]:
    """`{fuente: veredicto}` de las cadenas de catalogo, en una sola llamada.

    Lo usa el manifiesto de publicacion: la cobertura **medida** tiene que viajar con lo
    publicado, y hasta hoy el manifiesto solo llevaba lo que cada colector declaraba de su
    propio alcance -- que era solo Lidl, y de ahi salio el «solo Lidl tiene cobertura».
    Una regla, un sitio: esto no recalcula nada, llama a `veredicto`.
    """
    hoy = hoy or dt.date.today().isoformat()
    series = filas_por_dia()
    return {fuente: veredicto(series.get(fuente, {}), hoy, dias=dias, minimo_pct=minimo_pct)
            for fuente in FUENTES}


def _particiones(fuente: str) -> dict[str, Path]:
    """{fecha: carpeta} de las particiones de bronce que tienen algun parquet.

    Se listan los directorios y no se abre ningun fichero: el nombre es el dato. Una
    particion vacia (captura que se nego a escribir) no cuenta como dia.
    """
    carpeta = config.DATA / "bronze" / f"fuente={fuente}"
    if not carpeta.is_dir():
        return {}
    salida: dict[str, Path] = {}
    for sub in carpeta.iterdir():
        if not sub.is_dir() or not sub.name.startswith("fecha="):
            continue
        if any(sub.glob("*.parquet")):
            salida[sub.name.split("=", 1)[1]] = sub
    return salida


def _precios(carpeta: Path) -> pl.DataFrame:
    """(id_fuente, precio_cent) de una particion. Si falta una columna, devuelve vacio.

    No se inventa el precio que no esta: una particion sin `precio_cent` no puede decir
    cuantos precios cambiaron, y se declara desconocido en vez de cero.
    """
    marcos = []
    for fichero in sorted(carpeta.glob("*.parquet")):
        try:
            marcos.append(pl.read_parquet(fichero, columns=["id_fuente", "precio_cent"]))
        except Exception:  # noqa: BLE001  (una particion ilegible no invalida el dia)
            return pl.DataFrame()
    if not marcos:
        return pl.DataFrame()
    return (
        pl.concat(marcos)
        .with_columns(pl.col("id_fuente").cast(pl.Utf8))
        .unique(subset=["id_fuente"], keep="first")
    )


def novedad(fuente: str, fecha: str, dias: int = DIAS_PARA_NOVEDAD) -> dict:
    """Que produjo el dia frente a la ultima captura: nuevos, cambiados y desaparecidos.

    `vs` es la fecha con la que se compara. **Si no hay captura del dia no se devuelve un
    cero**: `nuevos`/`cambiados`/`desaparecen` van a `None` y `motivo` dice por que. Un cero
    es «no cambio nada»; `None` es «no lo se», y no son lo mismo.
    """
    desconocido = {"vs": None, "nuevos": None, "cambiados": None, "desaparecen": None}
    partes = _particiones(fuente)
    if fecha not in partes:
        return {**desconocido, "motivo": "no hay captura de ese dia"}
    fin = dt.date.fromisoformat(fecha)
    candidatas = [
        f for f in partes
        if f < fecha and 0 <= (fin - dt.date.fromisoformat(f)).days <= dias
    ]
    if not candidatas:
        return {**desconocido, "motivo": "no hay captura anterior con la que comparar"}
    vs = max(candidatas)
    hoy, anterior = _precios(partes[fecha]), _precios(partes[vs])
    if hoy.is_empty() or anterior.is_empty():
        return {**desconocido, "vs": vs, "motivo": "captura sin id/precio legible"}
    ids_hoy = set(hoy["id_fuente"].to_list())
    ids_anterior = set(anterior["id_fuente"].to_list())
    comun = hoy.join(anterior, on="id_fuente", how="inner", suffix="_anterior")
    cambiados = (
        comun.filter(
            pl.col("precio_cent").is_not_null()
            & pl.col("precio_cent_anterior").is_not_null()
            & (pl.col("precio_cent") != pl.col("precio_cent_anterior"))
        ).height
        if "precio_cent_anterior" in comun.columns
        else None
    )
    return {
        "vs": vs,
        "nuevos": len(ids_hoy - ids_anterior),
        "cambiados": cambiados,
        "desaparecen": len(ids_anterior - ids_hoy),
    }


def captura_del_dia(fuente: str, fecha: str) -> dict | None:
    """La particion de bronce del dia, con cuantas filas tiene y cuando se escribio.

    `escrita` es el mtime del fichero: es la prueba de que el dia se capturo **ese dia** y
    no se relleno despues desde otro crudo. Sin particion, `None`: no se inventa la captura.
    """
    carpeta = _particiones(fuente).get(fecha)
    if carpeta is None:
        return None
    filas = 0
    escrituras = []
    for fichero in sorted(carpeta.glob("*.parquet")):
        try:
            import pyarrow.parquet as pq

            filas += pq.ParquetFile(fichero).metadata.num_rows
        except Exception:  # noqa: BLE001
            filas += 0
        escrituras.append(fichero.stat().st_mtime)
    if not escrituras:
        return None
    return {
        "fecha": fecha,
        "escrita": dt.datetime.fromtimestamp(max(escrituras)).isoformat(timespec="seconds"),
        "filas": filas,
        "ficheros": len(escrituras),
    }


def run_del_dia(fuente: str, fecha: str) -> dict | None:
    """La fila de `data/runs.csv` de esa cadena y ese dia, si la hay.

    Es la otra mitad de la prueba: la particion dice que hay datos; el registro dice que la
    pasada se ejecuto y como termino. Sin fila, `None` -- no se supone que fue bien.
    """
    ruta = config.DATA / "runs.csv"
    if not ruta.is_file():
        return None
    try:
        # **La fecha del `ts` es UTC; el dia de la captura es local.** Una pasada a las 00:30 de
        # Madrid es el dia anterior en UTC, y comparar el prefijo UTC la daria por «sin run».
        # Se convierte a Europe/Madrid antes de comparar.
        local = ZoneInfo("Europe/Madrid")
        marco = pl.read_csv(ruta, infer_schema_length=0)
        marco = marco.filter(pl.col("fuente") == fuente)
        del_dia = marco.filter(
            pl.col("ts").map_elements(
                lambda ts: dt.datetime.fromisoformat(ts).astimezone(local).date().isoformat()
                if ts else None,
                return_dtype=pl.Utf8,
            ) == fecha
        )
        if del_dia.is_empty():
            return None
        fila = del_dia.row(-1, named=True)
        return {"ts": fila["ts"], "filas": int(fila["filas"]),
                "errores": int(fila["errores"]),
                "ok": str(fila["ok"]).strip().lower() in {"true", "1"}}
    except Exception:  # noqa: BLE001  (un CSV ilegible no invalida la declaracion)
        return None


def declaracion(fuente: str, fecha: str, serie: dict[str, int] | None = None) -> dict:
    """La cobertura declarada de una cadena y un dia: medida, con su novedad y su prueba.

    `serie` es {fecha: filas} de esa cadena; se pasa desde `declara` para no releer el bronce
    cinco veces. El veredicto es el de `veredicto`: no se recalcula aqui.
    """
    serie = filas_por_dia().get(fuente, {}) if serie is None else serie
    v = veredicto(serie, fecha)
    captura = captura_del_dia(fuente, fecha)
    # **Una particion que existe no es «sin datos», ni aunque no se pueda leer.** Hay tres casos
    # distintos y el fichero no los puede mezclar:
    #   - no hay particion: no hubo captura -> «sin datos», sin referencia ni porcentaje;
    #   - hay particion con filas pero el historico no se pudo leer: se declaran las filas y se
    #     deja la referencia a null -> «sin referencia»;
    #   - hay particion pero su parquet es ilegible (0 filas): tampoco es «sin datos»; es una
    #     particion que no se pudo leer -> «sin referencia» con aviso, no una ausencia inventada.
    if v["filas"] == 0 and captura is not None:
        v = {**v, "filas": captura["filas"], "referencia": None, "referencia_fecha": None,
             "pct": None, "veredicto": "sin referencia"}
        aviso_medida = True
    elif v["filas"] == 0:
        # Sin precio hoy no hay referencia que enseñar: un 0,0 % seria un numero inventado.
        v = {**v, "referencia": None, "referencia_fecha": None, "pct": None}
        aviso_medida = False
    else:
        aviso_medida = False
    datos = {
        "fuente": fuente,
        "cobertura": COBERTURA,
        "etiqueta": ETIQUETA,
        "fecha": fecha,
        # **Los huecos, con el nombre que pide el contrato** (`huecos`) y ademas los dos
        # numeros de los que sale (dias sin datos / dias de la ventana), que es lo que se lee
        # en el aviso. En la rama sin referencia no se sabe la ventana leida: van a null.
        "huecos": None if aviso_medida else v["dias_sin_datos"],
        "filas": v["filas"],
        "referencia": v["referencia"],
        "referencia_fecha": v["referencia_fecha"],
        "pct": v["pct"],
        "dias_en_la_ventana": None if aviso_medida else v["dias_en_la_ventana"],
        "dias_sin_datos": None if aviso_medida else v["dias_sin_datos"],
        "vs_anterior_pct": v["vs_anterior_pct"],
        "veredicto": v["veredicto"],
        "novedad": novedad(fuente, fecha),
        "captura": captura,
        "run": run_del_dia(fuente, fecha),
        "metodo": METODO,
    }
    if aviso_medida:
        datos["aviso"] = ("la particion del dia existe, pero no se pudo leer con fiabilidad: "
                          "ni la referencia ni los huecos se pueden acreditar")
    elif v["veredicto"] == "sin datos":
        datos["aviso"] = "no hubo captura este dia: la cobertura no se puede acreditar"
    elif v["dias_sin_datos"]:
        datos["aviso"] = (f"captura del dia contra una referencia del "
                          f"{v['referencia_fecha']}; en la ventana faltan "
                          f"{v['dias_sin_datos']} de {v['dias_en_la_ventana']} dias")
    return datos


def declara(fecha: str | None = None) -> list[Path]:
    """Escribe `data/cobertura/<fuente>-<fecha>.json` para las cinco cadenas de catalogo.

    Se escribe **lo medido**, no lo que la cadena dice de si misma: filas del bronce del dia,
    referencia de la ventana de 30 dias, veredicto y novedad frente a la captura anterior.
    Asi el manifiesto de publicacion y `GET /api/estado` dejan de tener una sola cadena con
    cobertura declarada.

    Idempotente: el mismo dia se reescribe igual, con temporal y renombrado atomico. Un
    fichero a medias se leeria como una publicacion valida.
    """
    fecha = fecha or dt.date.today().isoformat()
    series = filas_por_dia()
    destino = config.DATA / "cobertura"
    destino.mkdir(parents=True, exist_ok=True)
    # **Primero se preparan los cinco, despues se sustituyen.** Escribir de uno en uno y
    # sustituir sobre la marcha deja, si falla a mitad, un conjunto mezclado (dos del dia y tres
    # de ayer) que el manifiesto publicaria como si fuera de hoy. Aqui, o estan los cinco
    # temporales escritos, o no se sustituye ninguno.
    preparados: list[tuple[Path, Path]] = []
    try:
        for fuente in FUENTES:
            datos = declaracion(fuente, fecha, serie=series.get(fuente, {}))
            ruta = destino / f"{fuente}-{fecha}.json"
            temporal = ruta.with_suffix(".json.tmp")
            temporal.write_text(json.dumps(datos, ensure_ascii=False, indent=1),
                                encoding="utf-8")
            preparados.append((temporal, ruta))
    except Exception:
        for temporal, _ in preparados:
            temporal.unlink(missing_ok=True)
        raise
    escritos: list[Path] = []
    # **Y si falla la sustitucion a mitad, se deshace.** El renombrado de cada fichero es
    # atomico, pero el conjunto no: si el tercero falla (antivirus, bloqueo, disco), los dos
    # primeros ya son de hoy. Antes de sustituir se guarda lo que habia; si algo falla se
    # restaura y se borran los temporales, para que el manifiesto no publique una mezcla.
    #
    # **Leer lo anterior tambien puede fallar** (fichero bloqueado por el antivirus), y ese es
    # justo el escenario del comentario: si esa lectura va fuera del `try`, se quedan los cinco
    # `.tmp` en `data/cobertura/`. Va dentro, y el `anteriores` se rellena antes de tocar nada.
    anteriores: dict[Path, bytes | None] = {}
    try:
        anteriores = {ruta: (ruta.read_bytes() if ruta.exists() else None)
                      for _, ruta in preparados}
        for temporal, ruta in preparados:
            os.replace(temporal, ruta)
            escritos.append(ruta)
    except Exception:
        for ruta in escritos:
            previo = anteriores.get(ruta)
            try:
                if previo is None:
                    ruta.unlink(missing_ok=True)
                else:
                    ruta.write_bytes(previo)
            except OSError:
                # No se puede hacer mas: se propaga el fallo original, que es el que importa.
                pass
        # Los temporales se borran siempre, y un fallo al borrarlos no puede tapar el original.
        for temporal, _ in preparados:
            with suppress(OSError):
                temporal.unlink(missing_ok=True)
        raise
    return escritos


def main(argv: list[str] | None = None) -> int:
    """`argv` explicito para poder llamarlo desde la cadena diaria sin leer sus argumentos.

    **Esto no es adorno.** En `run.py` se llama asi: `...cobertura_diaria").main([])`. Con un
    `main()` a secas, `argparse` leeria el `sys.argv` de `run.py`, y un argumento que no conociera
    lanzaria `SystemExit` -- que **no** es una `Exception`, asi que el `except` de la cadena no lo
    cogería y se llevaria por delante la pasada entera. Un aviso que puede tumbar el dia deja de
    ser un aviso.
    """
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--fecha", help="el dia a mirar (por defecto, hoy)")
    ap.add_argument("--dias", type=int, default=DIAS_DE_VENTANA,
                    help="tamano de la ventana con la que se compara")
    ap.add_argument("--minimo-pct", type=float, default=MINIMO_PCT)
    ap.add_argument("--escribir", action="store_true",
                    help="dejar la cobertura medida de cada cadena en data/cobertura/")
    a = ap.parse_args(argv)

    hoy = a.fecha or dt.date.today().isoformat()
    series = filas_por_dia()
    if not series:
        print("No hay bronze que mirar todavia. Ejecuta el pipeline antes.")
        return 0

    print(f"la cobertura del {hoy}, contra el maximo de los {a.dias} dias anteriores\n")
    print(f"  {'cadena':<11}{'filas':>10}{'referencia':>12}{'%':>7}  {'huecos':>7}   veredicto")
    malas = []
    for fuente in FUENTES:
        v = veredicto(series.get(fuente, {}), hoy, dias=a.dias, minimo_pct=a.minimo_pct)
        huecos = f"{v['dias_sin_datos']}/{v['dias_en_la_ventana']}"
        print(f"  {fuente:<11}{v['filas']:>10,}{v['referencia']:>12,}{v['pct']:>6.1f}%  "
              f"{huecos:>7}   {v['veredicto']}".replace(",", "."))
        if v["veredicto"] != "ok":
            malas.append((fuente, v))

    # **Y la declaracion, si se pide.** Va antes del veredicto a proposito: el dia puede ir
    # mal --una cadena corta o sin datos-- y la declaracion sigue siendo cierta y necesaria,
    # porque «no trajo nada» tambien hay que declararlo, no callarlo.
    if a.escribir:
        escritas = declara(hoy)
        print(f"\ncobertura declarada en {len(escritas)} ficheros de data/cobertura/:")
        for ruta in escritas:
            datos = json.loads(ruta.read_text(encoding="utf-8"))
            nov = datos.get("novedad") or {}
            print(f"  {ruta.name}: {datos['filas']} filas, {datos['veredicto']}, "
                  f"novedad vs {nov.get('vs')}: {nov.get('nuevos')} nuevos, "
                  f"{nov.get('cambiados')} cambiados")
        print()

    print()
    if not malas:
        print("Todas las cadenas traen lo que suelen traer.")
        return 0
    print(f"{len(malas)} cadena(s) que no traen lo suyo:")
    for fuente, v in malas:
        if v["veredicto"] == "sin datos":
            print(f"  {fuente}: **no trajo nada** el {v['hoy']}. En la ventana faltan "
                  f"{v['dias_sin_datos']} de {v['dias_en_la_ventana']} dias.")
        else:
            # **Contra que se mide, y como va la tendencia.** Las dos cosas, porque
            # «corta» a secas se lee como «esta roto» y no siempre es eso.
            cuando = f" (la vara es del {v['referencia_fecha']})" if v.get("referencia_fecha") else ""
            cambio = (f"; {v['vs_anterior_pct']:+.1f}% sobre la captura anterior"
                      if v.get("vs_anterior_pct") is not None else "")
            print(f"  {fuente}: {v['filas']:,} filas contra {v['referencia']:,} de referencia "
                  f"({v['pct']}%){cuando}{cambio}.".replace(",", "."))
    print("\n**Ojo con la diferencia, que no es lo mismo:** sin bronze puede querer decir dos cosas"
          "\n  - que la cadena no trajo nada, o"
          "\n  - que **si trajo y el propio colector no lo guardo**, porque el control de cobertura"
          "\n    de dentro vio ramas enteras hundidas y prefirio conservar la captura anterior."
          "\nEl registro del dia lo distingue: `data/ejecuciones.log`.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
