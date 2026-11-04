"""Auditoria reproducible de la cobertura diaria: presencia, volumen y NOVEDAD.

**Que mide, y que NO mide.** Esta auditoria no dicta la vara de cobertura: esa vive en
`projects/cesta/cobertura_diaria.py` (maximo de 30 dias, 90 %) y aqui no se reimplementa. Lo que
mide es otra cosa, la que hace falta para responder "¿salen datos nuevos cada dia?":

  - por cadena de catalogo y por dia de la ventana: si hay particion de bronce, cuantas filas
    trae el bronce y cuantas trae el gold (`data/gold/precio_diario.parquet`);
  - NOVEDAD frente a la captura anterior de esa misma cadena: ids nuevos, precios cambiados e
    ids que desaparecen. **Se mide sobre BRONCE**, que es la captura del dia (id_fuente +
    precio_cent de `data/bronze/fuente=X/fecha=Y`). La misma cuenta se hace tambien sobre gold y
    se publica al lado: gold es bronce filtrado por alcance, no la captura, y sus cifras pueden
    diferir (el 2026-11-04, Alcabpo da 943/4/303 sobre bronce y 942/1/303 sobre gold);
  - si la particion de bronce se escribio el mismo dia de la captura (mtime, hora local) y si
    hay pasada registrada en `data/runs.csv`, cuantas hubo y si alguna termino bien.

**Solo lee local.** `data/bronze/fuente=*/fecha=*`, `data/gold/precio_diario.parquet` y
`data/runs.csv`. Nada de red, nada de base de datos.

**Puerta de salida.** Por defecto es un **instrumento de medida**: mide, dice los huecos de cada
cadena y sale **0** si pudo medir (2 si no hay datos que mirar). Con `--exigir-dias N` se
convierte en **puerta estricta**: sale 1 si alguna cadena de catalogo no llega a N de los 30 dias
de la ventana con captura, y dice cual. `--exigir-dias` sin numero usa 28/30, que hoy **no
cumplen las cinco** (2/5: el resultado medido esta en `docs/COBERTURA-DIARIA-2026-11-04.md` §9).
El umbral no se rebaja nunca para que pase; lo que no se hace es gritar todos los dias por un
hueco ya conocido: un aviso que salta siempre deja de leerse. Que la guarda de cobertura real
(la de `projects/`) dispare o no es otra pregunta y se responde alli.

**Evidencia.** Ademas de imprimir las tablas, deja dos CSV para pasarlos por data_profile y
data_verify:

  - `data/debug/auditoria-cobertura/cobertura_diaria.csv`  una fila por (cadena, dia) de la
    ventana, incluidos los dias SIN captura (estado `sin_captura`), que son la evidencia del hueco;
  - `data/debug/auditoria-cobertura/mercadona-<fecha>.csv`  muestra sistematica del bronce del
    dia de referencia de Mercadona (1 de cada N productos, ordenado por id_fuente).

Uso:

    uv run python -m scripts.auditar_cobertura_diaria
    uv run python -m scripts.auditar_cobertura_diaria --dias 30 --hasta 2026-11-04
    uv run python -m scripts.auditar_cobertura_diaria --muestra-filas 500

En Windows, consola UTF-8:  $env:PYTHONIOENCODING='utf-8'
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import statistics
import sys
from itertools import pairwise
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import duckdb

FUENTES = ("alcampo", "aldi", "carrefour", "dia", "mercadona")
DIAS_DEFECTO = 30
UMBRAL_DIAS = 28           # de los 30 de la ventana: umbral de aceptacion, no se rebaja
MUESTRA_FILAS = 500

TZ = ZoneInfo("Europe/Madrid")
BRONCE = Path("data/bronze")
ORO = "data/gold/precio_diario.parquet"
RUNS = Path("data/runs.csv")
DIR_SALIDA = Path("data/debug/auditoria-cobertura")
SALIDA_CSV = DIR_SALIDA / "cobertura_diaria.csv"

# Estados posibles de una (cadena, dia). Es el enum que verifica data_verify.
ESTADOS = (
    "ok",                          # particion escrita + alguna pasada del dia termino bien
    "captura_sin_run",             # particion escrita, ninguna pasada registrada
    "captura_run_fallido",         # particion escrita, pasadas registradas pero ninguna bien
    "run_sin_captura",             # pasada bien pero NO se escribio la particion
    "sin_captura_run_fallido",     # sin particion y con pasadas fallidas: no trajo nada
    "sin_captura",                 # ni particion ni pasada: no se intento (o no se sabe)
)

COLUMNAS_CSV = [
    "fuente", "fecha", "estado", "tiene_captura", "ficheros_bronce",
    "filas_bronce", "bronce_con_precio", "bronce_sin_precio",
    "filas_gold", "ids_gold_con_precio", "ids_gold_sin_precio",
    "captura_previa",
    "novedad_bronce_medida", "nuevos_ids_bronce", "precios_cambiados_bronce",
    "ids_desaparecen_bronce",
    "novedad_gold_medida", "nuevos_ids_gold", "precios_cambiados_gold",
    "ids_desaparecen_gold",
    "mtime_particion", "escrito_el_mismo_dia",
    "runs_del_dia", "runs_ok_del_dia", "run_filas", "run_ts",
]

# En el CSV los booleanos van como 1/0 y "sin dato" va como celda vacia. En las tablas por
# consola se escriben "si"/"no": la evidencia tiene que ser legible por una persona y por
# data_profile, y "si"/"no" hace que el perfilador vea tipos mixtos donde solo hay un binario.
COLUMNAS_BOOLEANAS = (
    "tiene_captura", "novedad_bronce_medida", "novedad_gold_medida", "escrito_el_mismo_dia",
)


# --------------------------------------------------------------------------------------
# lectura del disco
# --------------------------------------------------------------------------------------

def calendario(hasta: dt.date, dias: int) -> list[str]:
    """Los `dias` dias de calendario que acaban en `hasta`, ambos incluidos, de viejo a nuevo."""
    return [(hasta - dt.timedelta(days=i)).isoformat() for i in range(dias - 1, -1, -1)]


def _con() -> duckdb.DuckDBPyConnection:
    c = duckdb.connect()
    c.execute("SET enable_progress_bar=false")
    return c


def _fuente_parquet(tabla: str) -> str:
    """El `FROM` que toca segun se mida sobre bronce o sobre gold."""
    if tabla == "bronce":
        patron = (BRONCE / "**" / "*.parquet").as_posix()
        return f"read_parquet('{patron}', hive_partitioning=true)"
    if tabla == "gold":
        return f"read_parquet('{ORO}')"
    raise ValueError(tabla)


def filas_bronce(con: duckdb.DuckDBPyConnection) -> dict[tuple[str, str], dict[str, int]]:
    """{(fuente, fecha): {filas, con_precio, sin_precio}} de todo el bronze.

    La fecha sale de la particion, no de un campo del producto. Se cuentan tambien los precios
    nulos porque son parte de la captura: Aldi trae filas sin precio y eso no es un fallo de
    esta auditoria, es un dato que hay que ver.
    """
    patron = (BRONCE / "**" / "*.parquet").as_posix()
    consulta = f"""
        SELECT fuente, CAST(fecha AS VARCHAR) AS fecha,
               count(*) AS filas,
               count(precio_cent) AS con_precio,
               count(*) - count(precio_cent) AS sin_precio
        FROM read_parquet('{patron}', hive_partitioning=true)
        WHERE fecha IS NOT NULL
        GROUP BY 1, 2
    """
    return {(f, fe): {"filas": int(n), "con_precio": int(cp), "sin_precio": int(sp)}
            for f, fe, n, cp, sp in con.execute(consulta).fetchall()}


def filas_gold(con: duckdb.DuckDBPyConnection) -> dict[tuple[str, str], dict[str, int]]:
    """{(fuente, fecha): {filas, con_precio, sin_precio}} de todo el gold.

    Sin filtrar por cadena: Lidl no es cadena de catalogo, pero se imprime como contexto para
    poder corregir la premisa de "solo Lidl". Las filas del CSV si se limitan a FUENTES.
    """
    consulta = f"""
        SELECT fuente, CAST(fecha AS VARCHAR) AS fecha,
               count(*) AS filas,
               count(precio_cent) AS con_precio,
               count(*) - count(precio_cent) AS sin_precio
        FROM read_parquet('{ORO}')
        GROUP BY 1, 2
    """
    return {(f, fe): {"filas": int(n), "con_precio": int(cp), "sin_precio": int(sp)}
            for f, fe, n, cp, sp in con.execute(consulta).fetchall()}


def particiones() -> dict[tuple[str, str], list[Path]]:
    """{(fuente, fecha): ficheros parquet} de las cadenas de catalogo, mirando el disco."""
    salida: dict[tuple[str, str], list[Path]] = {}
    for fuente in FUENTES:
        carpeta = BRONCE / f"fuente={fuente}"
        if not carpeta.is_dir():
            continue
        for dia in sorted(carpeta.glob("fecha=*")):
            if not dia.is_dir():
                continue
            ficheros = sorted(dia.glob("*.parquet"))
            if ficheros:
                salida[(fuente, dia.name.removeprefix("fecha="))] = ficheros
    return salida


def pasadas() -> dict[tuple[str, str], dict[str, Any]]:
    """{(fuente, fecha local): pasadas del dia} leidas de data/runs.csv.

    `ts` esta en UTC; el dia se cuenta en Europe/Madrid, que es el dia de la particion. Si un dia
    tiene varias pasadas (reintentos), se guardan todas: `n`, cuantas terminaron bien, y las filas
    y el ts de la ULTIMA, que es la que dejo el fichero.
    """
    if not RUNS.is_file():
        return {}
    por_dia: dict[tuple[str, str], list[dict[str, Any]]] = {}
    with RUNS.open(encoding="utf-8", newline="") as f:
        for fila in csv.DictReader(f):
            try:
                ts = dt.datetime.fromisoformat(fila["ts"]).astimezone(TZ)
            except (KeyError, ValueError):
                continue
            clave = (fila["fuente"], ts.date().isoformat())
            por_dia.setdefault(clave, []).append({
                "ts": ts,
                "filas": int(fila.get("filas") or 0),
                "ok": str(fila.get("ok", "")).strip().lower() in ("true", "1", "si", "yes"),
            })
    salida: dict[tuple[str, str], dict[str, Any]] = {}
    for clave, lista in por_dia.items():
        lista.sort(key=lambda r: r["ts"])
        ultima = lista[-1]
        salida[clave] = {
            "n": len(lista),
            "ok": sum(1 for r in lista if r["ok"]),
            "filas": ultima["filas"],
            "ts": ultima["ts"],
        }
    return salida


def mtime_particion(ficheros: list[Path]) -> dt.datetime | None:
    """Cuando se escribio de verdad la particion: el mtime mas nuevo de sus parquet, en hora local."""
    if not ficheros:
        return None
    return max(dt.datetime.fromtimestamp(f.stat().st_mtime, TZ) for f in ficheros)


# --------------------------------------------------------------------------------------
# novedad: que ids aparecen, cuales cambian de precio y cuales desaparecen
# --------------------------------------------------------------------------------------

def series_por_fuente(dias: dict[tuple[str, str], Any]) -> dict[str, list[str]]:
    """{fuente: [fechas ordenadas]} a partir de un diccionario {(fuente, fecha): ...}."""
    series: dict[str, list[str]] = {}
    for (fuente, fecha) in dias:
        series.setdefault(fuente, []).append(fecha)
    for fuente in series:
        series[fuente].sort()
    return series


def pares_de_novedad(serie: dict[str, list[str]], ventana: list[str]) -> list[tuple[str, str, str]]:
    """[(fuente, fecha, captura_previa)] para cada dia de la ventana con captura y previa.

    La "captura anterior" es el ultimo dia CON captura de esa cadena, aunque quede antes de la
    ventana: tras un hueco, la novedad se mide contra lo ultimo que se trajo, no contra el
    calendario. Un dia sin captura no genera par (no hay nada que comparar).
    """
    pares: list[tuple[str, str, str]] = []
    for fuente in FUENTES:
        fechas = serie.get(fuente, [])
        previa_de = {actual: anterior for anterior, actual in pairwise(fechas)}
        for fecha in ventana:
            previa = previa_de.get(fecha)
            if previa is not None:
                pares.append((fuente, fecha, previa))
    return pares


def novedad(con: duckdb.DuckDBPyConnection, pares: list[tuple[str, str, str]], tabla: str) -> dict[tuple[str, str], dict[str, int]]:
    """{(fuente, fecha): nuevos, desaparecen, cambiados} contra la captura previa.

    Una sola consulta por tabla: se cruzan las dos capturas de cada par por id_fuente y se cuenta.
    Un precio solo cuenta como cambiado si los dos lados tienen precio: un null no es un cambio de
    precio, es un producto sin precio.
    """
    if not pares:
        return {}
    valores = ",\n            ".join(
        "('" + f + "', '" + fe + "', '" + pr + "')" for f, fe, pr in pares)
    origen = _fuente_parquet(tabla)
    consulta = f"""
        WITH pares(fuente, fecha, previa) AS (
            VALUES
            {valores}
        ),
        hoy AS (
            SELECT p.fuente, p.fecha, g.id_fuente, g.precio_cent
            FROM pares p
            JOIN {origen} g
              ON g.fuente = p.fuente AND CAST(g.fecha AS VARCHAR) = p.fecha
        ),
        antes AS (
            SELECT p.fuente, p.fecha, g.id_fuente, g.precio_cent
            FROM pares p
            JOIN {origen} g
              ON g.fuente = p.fuente AND CAST(g.fecha AS VARCHAR) = p.previa
        )
        SELECT COALESCE(h.fuente, a.fuente) AS fuente,
               COALESCE(h.fecha, a.fecha) AS fecha,
               count(*) FILTER (WHERE a.id_fuente IS NULL) AS nuevos,
               count(*) FILTER (WHERE h.id_fuente IS NULL) AS desaparecen,
               count(*) FILTER (
                   WHERE h.id_fuente IS NOT NULL AND a.id_fuente IS NOT NULL
                     AND h.precio_cent IS NOT NULL AND a.precio_cent IS NOT NULL
                     AND h.precio_cent <> a.precio_cent) AS cambiados
        FROM hoy h
        FULL OUTER JOIN antes a
          ON h.fuente = a.fuente AND h.fecha = a.fecha AND h.id_fuente = a.id_fuente
        GROUP BY 1, 2
    """
    return {(f, fe): {"nuevos": int(n), "desaparecen": int(d), "cambiados": int(c)}
            for f, fe, n, d, c in con.execute(consulta).fetchall()}


# --------------------------------------------------------------------------------------
# composicion de la tabla
# --------------------------------------------------------------------------------------

def construir_filas(con: duckdb.DuckDBPyConnection, ventana: list[str],
                    partes: dict[tuple[str, str], list[Path]],
                    bronze: dict[tuple[str, str], dict[str, int]],
                    gold: dict[tuple[str, str], dict[str, int]],
                    corredores: dict[tuple[str, str], dict[str, Any]]) -> list[dict[str, Any]]:
    """Una fila por (cadena, dia) de la ventana, con todo lo medido y el estado."""

    serie_bronce = series_por_fuente(bronze)
    serie_gold = series_por_fuente(gold)

    pares_bronce = pares_de_novedad(serie_bronce, ventana)
    previa_de = {(f, fe): pr for f, fe, pr in pares_bronce}
    # la misma novedad sobre gold solo tiene sentido donde gold tiene las dos capturas
    pares_gold = [(f, fe, pr) for f, fe, pr in pares_bronce
                  if pr in set(serie_gold.get(f, []))]
    novedades_bronce = novedad(con, pares_bronce, "bronce")
    novedades_gold = novedad(con, pares_gold, "gold")

    filas: list[dict[str, Any]] = []
    for fuente in FUENTES:
        for fecha in ventana:
            ficheros = partes.get((fuente, fecha), [])
            tiene_captura = bool(ficheros)
            corredor = corredores.get((fuente, fecha), {})
            runs_n = int(corredor.get("n", 0))
            runs_ok = int(corredor.get("ok", 0))
            b = bronze.get((fuente, fecha), {"filas": 0, "con_precio": 0, "sin_precio": 0})
            g = gold.get((fuente, fecha), {"filas": 0, "con_precio": 0, "sin_precio": 0})
            nov_b = novedades_bronce.get((fuente, fecha))
            nov_g = novedades_gold.get((fuente, fecha))
            mtime = mtime_particion(ficheros)
            escrito_hoy = (mtime is not None and mtime.date().isoformat() == fecha)
            filas.append({
                "fuente": fuente,
                "fecha": fecha,
                "estado": _estado(tiene_captura, runs_n, runs_ok),
                "tiene_captura": "si" if tiene_captura else "no",
                "ficheros_bronce": len(ficheros),
                "filas_bronce": int(b["filas"]),
                "bronce_con_precio": int(b["con_precio"]),
                "bronce_sin_precio": int(b["sin_precio"]),
                "filas_gold": int(g["filas"]),
                "ids_gold_con_precio": int(g["con_precio"]),
                "ids_gold_sin_precio": int(g["sin_precio"]),
                "captura_previa": previa_de.get((fuente, fecha), ""),
                "novedad_bronce_medida": "si" if nov_b is not None else "no",
                "nuevos_ids_bronce": int(nov_b["nuevos"]) if nov_b else 0,
                "precios_cambiados_bronce": int(nov_b["cambiados"]) if nov_b else 0,
                "ids_desaparecen_bronce": int(nov_b["desaparecen"]) if nov_b else 0,
                "novedad_gold_medida": "si" if nov_g is not None else "no",
                "nuevos_ids_gold": int(nov_g["nuevos"]) if nov_g else 0,
                "precios_cambiados_gold": int(nov_g["cambiados"]) if nov_g else 0,
                "ids_desaparecen_gold": int(nov_g["desaparecen"]) if nov_g else 0,
                "mtime_particion": (mtime.replace(tzinfo=None).isoformat(sep=" ", timespec="seconds")
                                    if mtime else ""),
                "escrito_el_mismo_dia": ("si" if escrito_hoy else "no") if mtime else "",
                "runs_del_dia": runs_n,
                "runs_ok_del_dia": runs_ok,
                "run_filas": corredor.get("filas", "") if runs_n else "",
                "run_ts": corredor["ts"].isoformat(timespec="seconds") if runs_n else "",
            })
    return filas


def _estado(tiene_captura: bool, runs: int, runs_ok: int) -> str:
    if tiene_captura:
        if runs_ok:
            return "ok"
        return "captura_run_fallido" if runs else "captura_sin_run"
    if runs_ok:
        return "run_sin_captura"
    return "sin_captura_run_fallido" if runs else "sin_captura"


# --------------------------------------------------------------------------------------
# escritura de evidencia
# --------------------------------------------------------------------------------------

def escribir_csv(filas: list[dict[str, Any]], destino: Path) -> None:
    """Escribe la evidencia canonica: booleanos 1/0, celda vacia = sin dato."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=COLUMNAS_CSV, lineterminator="\n")
        escritor.writeheader()
        for fila in filas:
            salida = dict(fila)
            for columna in COLUMNAS_BOOLEANAS:
                valor = salida[columna]
                salida[columna] = "" if valor == "" else (1 if valor == "si" else 0)
            escritor.writerow(salida)


def exportar_muestra(con: duckdb.DuckDBPyConnection, fecha: str, filas_objetivo: int) -> dict[str, Any]:
    """Muestra sistematica del bronce de Mercadona del dia: 1 de cada N productos por id_fuente."""
    patron = (BRONCE / "fuente=mercadona" / f"fecha={fecha}" / "*.parquet").as_posix()
    total = int(con.execute(f"SELECT count(*) FROM read_parquet('{patron}')").fetchone()[0])
    paso = max(1, -(-total // max(1, filas_objetivo)))  # ceil
    destino = DIR_SALIDA / f"mercadona-{fecha}.csv"
    con.execute(f"""
        COPY (
            SELECT * EXCLUDE (_fila) FROM (
                SELECT *, row_number() OVER (ORDER BY id_fuente) AS _fila
                FROM read_parquet('{patron}')
            )
            WHERE _fila % {paso} = 1
            ORDER BY _fila
        ) TO '{destino.as_posix()}' (FORMAT CSV, HEADER)
    """)
    muestra = int(con.execute(
        f"SELECT count(*) FROM read_csv_auto('{destino.as_posix()}', header=true)").fetchone()[0])
    return {"fecha": fecha, "total": total, "paso": paso, "filas": muestra, "ruta": destino}


# --------------------------------------------------------------------------------------
# informes
# --------------------------------------------------------------------------------------

def _n(valor: int | float) -> str:
    """Numero legible en castellano: miles con punto."""
    if isinstance(valor, float):
        return f"{valor:,.0f}".replace(",", ".")
    return f"{valor:,}".replace(",", ".")


def _media_min_max(valores: list[int]) -> tuple[float, int, int] | None:
    if not valores:
        return None
    return statistics.mean(valores), min(valores), max(valores)


def imprimir_historico(bronze: dict, gold: dict, corredores: dict) -> None:
    print("== 1. Historico de capturas por cadena (todo el bronze en disco) ==")
    print(f"  {'cadena':<20}{'dias_captura':>13}{'primera':>12}{'ultima':>12}"
          f"{'dias_con_run':>14}{'filas_bronce':>14}{'filas_gold':>13}")
    for fuente in (*FUENTES, "lidl"):
        dias = sorted(f2 for (f, f2) in bronze if f == fuente)
        total_bronce = sum(v["filas"] for (f, _), v in bronze.items() if f == fuente)
        total_gold = sum(v["filas"] for (f, _), v in gold.items() if f == fuente)
        dias_run = len({f2 for (f, f2) in corredores if f == fuente})
        etiqueta = fuente if fuente in FUENTES else f"{fuente} (contexto)"
        rango = (dias[0], dias[-1]) if dias else ("-", "-")
        print(f"  {etiqueta:<20}{len(dias):>13}{rango[0]:>12}{rango[1]:>12}"
              f"{dias_run:>14}{_n(total_bronce):>14}{_n(total_gold):>13}")
    print("  ('contexto' = no es cadena de catalogo; se imprime para poder corregir la premisa"
          " de 'solo Lidl')\n")


def imprimir_ventana(filas: list[dict[str, Any]], ventana: list[str]) -> None:
    print(f"== 2. La ventana, por cadena ({ventana[0]} .. {ventana[-1]}, {len(ventana)} dias) ==")
    print(f"  {'cadena':<12}{'dias_captura':>13}{'dias_gold':>10}"
          f"{'media_bronce':>13}{'min':>8}{'max':>8}"
          f"{'media_gold':>11}{'min':>8}{'max':>8}")
    for fuente in FUENTES:
        suyas = [f for f in filas if f["fuente"] == fuente]
        con_captura = [f for f in suyas if f["tiene_captura"] == "si"]
        con_gold = [f for f in suyas if f["filas_gold"] > 0]
        b = _media_min_max([f["filas_bronce"] for f in con_captura])
        g = _media_min_max([f["filas_gold"] for f in con_gold])
        texto_b = f"{_n(b[0]):>7}{_n(b[1]):>8}{_n(b[2]):>8}" if b else f"{'-':>7}{'-':>8}{'-':>8}"
        texto_g = f"{_n(g[0]):>7}{_n(g[1]):>8}{_n(g[2]):>8}" if g else f"{'-':>7}{'-':>8}{'-':>8}"
        print(f"  {fuente:<12}{len(con_captura):>8}/{len(suyas):<4}{len(con_gold):>10}"
              f"{texto_b:>10}{texto_g:>10}")
    print()


def imprimir_novedad_hoy(filas: list[dict[str, Any]], hasta: str) -> None:
    print(f"== 3. Novedad del dia de referencia ({hasta}) ==")
    print("  medida sobre BRONCE (la captura del dia); entre parentesis, la misma cuenta sobre gold")
    print(f"  {'cadena':<12}{'filas_bronce':>13}{'filas_gold':>11}{'nuevos':>12}"
          f"{'cambiados':>14}{'desaparecen':>14}{'captura_previa':>15}"
          f"{'escrito_el_dia':>15}{'runs_ok':>9}")
    for fuente in FUENTES:
        fila = next((f for f in filas if f["fuente"] == fuente and f["fecha"] == hasta), None)
        if fila is None:
            continue
        escrito = (fila["mtime_particion"][11:16] if fila["escrito_el_mismo_dia"] == "si"
                   else (fila["escrito_el_mismo_dia"] or "-"))
        runs = (f"{fila['runs_ok_del_dia']}/{fila['runs_del_dia']}"
                if fila["runs_del_dia"] else "-")
        nuevos = f"{_n(fila['nuevos_ids_bronce'])} ({_n(fila['nuevos_ids_gold'])})"
        cambiados = f"{_n(fila['precios_cambiados_bronce'])} ({_n(fila['precios_cambiados_gold'])})"
        desaparecen = f"{_n(fila['ids_desaparecen_bronce'])} ({_n(fila['ids_desaparecen_gold'])})"
        print(f"  {fuente:<12}{_n(fila['filas_bronce']):>13}{_n(fila['filas_gold']):>11}"
              f"{nuevos:>12}{cambiados:>14}{desaparecen:>14}"
              f"{(fila['captura_previa'] or '-'):>15}{escrito:>15}{runs:>9}")
    print()


def imprimir_ultimos_dias(filas: list[dict[str, Any]], dias: int = 7) -> None:
    print(f"== 4. Novedad de los ultimos {dias} dias CON captura, por cadena ==")
    print("  sobre BRONCE, contra la captura anterior; 'desaparecen' es un id de la captura previa"
          " que hoy no esta")
    for fuente in FUENTES:
        suyas = [f for f in filas if f["fuente"] == fuente and f["tiene_captura"] == "si"]
        ultimas = suyas[-dias:]
        if not ultimas:
            print(f"  {fuente}: sin capturas en la ventana")
            continue
        print(f"  -- {fuente} --")
        print(f"    {'fecha':<12}{'bronce':>10}{'gold':>9}{'nuevos':>8}{'cambiados':>10}"
              f"{'desaparecen':>12}{'con_precio':>11}{'escrito':>9}{'run_ok':>8}")
        for fila in ultimas:
            escrito = "si" if fila["escrito_el_mismo_dia"] == "si" else "no"
            run_ok = "si" if fila["runs_ok_del_dia"] else ("no" if fila["runs_del_dia"] else "-")
            print(f"    {fila['fecha']:<12}{_n(fila['filas_bronce']):>10}"
                  f"{_n(fila['filas_gold']):>9}{_n(fila['nuevos_ids_bronce']):>8}"
                  f"{_n(fila['precios_cambiados_bronce']):>10}"
                  f"{_n(fila['ids_desaparecen_bronce']):>12}"
                  f"{_n(fila['bronce_con_precio']):>11}{escrito:>9}{run_ok:>8}")
    print()


def imprimir_huecos(filas: list[dict[str, Any]], ventana: list[str],
                    partes: dict[tuple[str, str], list[Path]],
                    corredores: dict[tuple[str, str], dict[str, Any]]) -> None:
    print("== 5. Huecos, escritura y coherencia bronce/gold ==")
    for fuente in FUENTES:
        suyas = [f for f in filas if f["fuente"] == fuente]
        huecos = [f["fecha"] for f in suyas if f["tiene_captura"] == "no"]
        detalle = ", ".join(h[5:] for h in huecos) if huecos else "ninguno"
        print(f"  {fuente:<12}{len(huecos):>3} dias sin captura de {len(ventana)}: {detalle}")
    con_captura = [f for f in filas if f["tiene_captura"] == "si"]
    mtime_ok = sum(1 for f in con_captura if f["escrito_el_mismo_dia"] == "si")
    con_run_ok = sum(1 for f in con_captura if f["runs_ok_del_dia"] > 0)
    sin_run = sum(1 for f in con_captura if f["runs_del_dia"] == 0)
    run_sin_captura_ok = [f for f in filas if f["tiene_captura"] == "no" and f["runs_ok_del_dia"] > 0]
    run_sin_captura_fallo = [f for f in filas if f["tiene_captura"] == "no" and f["runs_del_dia"] > 0
                             and f["runs_ok_del_dia"] == 0]
    print()
    print(f"  dias con captura: {len(con_captura)}; escritos el mismo dia (mtime): {mtime_ok};"
          f" con alguna pasada buena: {con_run_ok}; sin pasada registrada: {sin_run}")
    print(f"  dias con pasada buena y SIN particion (trajo y no escribio): {len(run_sin_captura_ok)}")
    for f in run_sin_captura_ok:
        print(f"    - {f['fuente']:<11}{f['fecha']}  run_filas={f['run_filas']}")
    print(f"  dias con pasadas y ninguna buena (fallaron) y sin particion: {len(run_sin_captura_fallo)}")
    for f in run_sin_captura_fallo:
        print(f"    - {f['fuente']:<11}{f['fecha']}  ultimo_run={f['run_filas']} filas")
    # el mismo patron, en todo el historico: dias con pasada pero sin particion escrita
    hist_ok = [(f, fe) for (f, fe), c in corredores.items()
               if f in FUENTES and c["ok"] > 0 and (f, fe) not in partes]
    hist_fallo = [(f, fe) for (f, fe), c in corredores.items()
                  if f in FUENTES and c["ok"] == 0 and (f, fe) not in partes]
    print(f"  historico completo: {len(hist_ok)} dias con pasada buena y sin particion"
          f" (trajo y no escribio) y {len(hist_fallo)} con pasadas fallidas y sin particion")
    print("    con pasada buena: "
          + (", ".join(f"{f} {fe[5:]}" for f, fe in sorted(hist_ok)) if hist_ok else "ninguno"))
    # coherencia bronce <-> gold
    total_bronce = sum(f["filas_bronce"] for f in filas)
    total_gold = sum(f["filas_gold"] for f in filas)
    merma = total_bronce - total_gold
    pct = (100.0 * merma / total_bronce) if total_bronce else 0.0
    print(f"  bronce frente a gold en la ventana: {_n(total_bronce)} filas -> {_n(total_gold)}"
          f" gold ({_n(merma)} menos, {pct:.1f} %): gold es bronce filtrado por alcance")
    incoherentes = [f for f in filas if f["tiene_captura"] == "no" and f["filas_gold"] > 0]
    if incoherentes:
        print(f"  AVISO: {len(incoherentes)} dias con filas en gold y sin particion de bronce:")
        for f in incoherentes:
            print(f"    - {f['fuente']:<11}{f['fecha']}  gold={_n(f['filas_gold'])}")
    vacias = [f for f in con_captura if f["filas_bronce"] == 0]
    if vacias:
        print(f"  AVISO: {len(vacias)} particiones con fichero y cero filas.")
    print()


def imprimir_veredicto(filas: list[dict[str, Any]], ventana: list[str],
                       umbral: int | None) -> int:
    print("== 7. Veredicto de la auditoria ==")
    dias_por_cadena = {
        fuente: sum(1 for f in filas if f["fuente"] == fuente and f["tiene_captura"] == "si")
        for fuente in FUENTES
    }
    sin_nada = [f for f, d in dias_por_cadena.items() if d == 0]
    if sin_nada:
        print(f"  NO SE PUEDE MEDIR: {', '.join(sin_nada)} no tienen ni una captura en la "
              f"ventana. Salida 1.")
        return 1

    if umbral is None:
        total = len(filas)
        con = sum(1 for f in filas if f["tiene_captura"] == "si")
        print(f"  Modo medida: {con}/{total} dias-cadena de la ventana tienen captura.")
        print("  Huecos por cadena (informativo, no hace fallar la medicion):")
        for fuente in FUENTES:
            print(f"    {fuente:<11}{dias_por_cadena[fuente]:>3}/{len(ventana)} dias con captura")
        print("  Para usar esto como puerta estricta: --exigir-dias N (p. ej. --exigir-dias 28).")
        print("  Salida 0: la medicion se ha hecho y los huecos estan dichos.")
        return 0

    print(f"  Umbral exigido: cada cadena de catalogo necesita >= {umbral} de {len(ventana)} "
          "dias con captura. No se rebaja.")
    cumplen = [(f, d) for f, d in dias_por_cadena.items() if d >= umbral]
    fallan = [(f, d) for f, d in dias_por_cadena.items() if d < umbral]
    print(f"  cadenas que cumplen: {len(cumplen)}/{len(FUENTES)}"
          + (" -> " + ", ".join(f"{f} {d}/{len(ventana)}" for f, d in cumplen) if cumplen else ""))
    if fallan:
        print("  cadenas que NO cumplen: "
              + ", ".join(f"{f} {d}/{len(ventana)}" for f, d in fallan))
        print()
        print("  La auditoria NO baja el umbral para que pase: sale 1 y dice el hueco.")
        return 1
    print("  Las cinco cadenas superan el umbral: salida 0.")
    return 0


# --------------------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dias", type=int, default=DIAS_DEFECTO,
                    help=f"tamano de la ventana en dias de calendario (por defecto {DIAS_DEFECTO})")
    ap.add_argument("--hasta", default=dt.date.today().isoformat(),
                    help="ultimo dia de la ventana (por defecto, hoy)")
    ap.add_argument("--muestra-filas", type=int, default=MUESTRA_FILAS,
                    help=f"filas de la muestra de bronce de Mercadona (por defecto {MUESTRA_FILAS})")
    ap.add_argument("--exigir-dias", type=int, nargs="?", const=UMBRAL_DIAS, default=None,
                    help=f"modo puerta estricta: sale 1 si alguna cadena no llega a N de "
                         f"{DIAS_DEFECTO} dias con captura (sin numero: {UMBRAL_DIAS}). Sin esta "
                         "bandera el script solo mide y sale 0 si pudo medir.")
    a = ap.parse_args(argv)

    if a.dias < 1:
        print("--dias tiene que ser >= 1")
        return 2
    if a.exigir_dias is not None and not 0 <= a.exigir_dias <= a.dias:
        print(f"--exigir-dias tiene que estar entre 0 y {a.dias}")
        return 2
    try:
        hasta = dt.date.fromisoformat(a.hasta)
    except ValueError:
        print(f"--hasta no es una fecha ISO: {a.hasta!r}")
        return 2
    if not Path(ORO).is_file():
        print(f"No existe {ORO}: no hay gold que medir.")
        return 2

    ventana = calendario(hasta, a.dias)
    con = _con()
    ahora = dt.datetime.now(TZ)

    bronze = filas_bronce(con)
    gold = filas_gold(con)
    corredores = pasadas()
    partes = particiones()
    filas = construir_filas(con, ventana, partes, bronze, gold, corredores)

    print("AUDITORIA DE COBERTURA DIARIA")
    print(f"medido: {ahora.isoformat(sep=' ', timespec='seconds')} (Europe/Madrid)")
    print(f"ventana: {ventana[0]} .. {ventana[-1]} ({len(ventana)} dias)")
    print(f"lee: {BRONCE}/fuente=*/fecha=*  {ORO}  {RUNS}  (nada de red)")
    print()

    imprimir_historico(bronze, gold, corredores)
    imprimir_ventana(filas, ventana)
    imprimir_novedad_hoy(filas, hasta.isoformat())
    imprimir_ultimos_dias(filas, dias=7)
    imprimir_huecos(filas, ventana, partes, corredores)

    escribir_csv(filas, SALIDA_CSV)
    print("== 6. Evidencia ==")
    print(f"  CSV de auditoria: {SALIDA_CSV} ({len(filas)} filas = {len(FUENTES)} cadenas x "
          f"{len(ventana)} dias)")
    print(f"  columnas: {', '.join(COLUMNAS_CSV)}")

    candidatas = sorted(f for f in series_por_fuente(bronze).get("mercadona", [])
                        if f <= hasta.isoformat())
    if candidatas:
        muestra = exportar_muestra(con, candidatas[-1], a.muestra_filas)
        print(f"  muestra de bronce Mercadona {muestra['fecha']}: {muestra['ruta']} "
              f"({muestra['filas']} de {muestra['total']} filas, 1 de cada {muestra['paso']})")
    else:
        print("  sin bronce de Mercadona hasta la fecha pedida: no hay muestra que exportar")
    print()

    return imprimir_veredicto(filas, ventana, a.exigir_dias)


if __name__ == "__main__":
    sys.exit(main())
