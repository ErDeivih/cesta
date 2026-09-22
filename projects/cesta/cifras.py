"""Reescribe `docs/CIFRAS.md` con los numeros de la ultima ejecucion.

El agujero que tapa
-------------------
`docs/CIFRAS.md` dice de si mismo, desde el 19 de septiembre de 2026:

    Este documento tiene un solo trabajo: llevar los numeros de **hoy**.
    Se reescribe entero despues de cada pasada.

**No lo reescribia nadie.** Se escribio a mano aquel dia y ahi se quedo. La
consecuencia se vio al revisar la ejecucion del 20: `verificar_docs` cerro otra
vez con "8 cifra(s) posiblemente caducada(s)", y las ocho eran las del 19
esperando en un fichero que se suponia automatico.

Eso es peor que no tener el control. Un aviso que sale todos los dias y que
todos los dias hay que descartar a mano deja de leerse a la semana, y el dia que
avise de algo de verdad tampoco se leera. La regla 21 decia que un control que
aprueba sin nada con que comparar es peor que no tenerlo; esta es su otra mitad.

Por que comparte tabla con el verificador
-----------------------------------------
Las consultas salen de `verificar_docs.COMPROBACIONES`, no de una copia. Si el
escritor y el comprobador tuvieran cada uno su SQL, acabarian midiendo cosas
ligeramente distintas y el aviso volveria sin que nada estuviera mal. Una regla
escrita en dos sitios acaba siendo dos reglas.

    uv run python -m projects.cesta.cifras
"""
from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

import duckdb

from core import config
from projects.cesta.verificar_docs import COMPROBACIONES, DOCS, _miles

DESTINO = Path(DOCS[0]).parent / "CIFRAS.md"

MESES = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre")

# Como se agrupan las cifras en el documento. Lo que no este aqui sale al final,
# que es mejor que desaparecer sin que nadie lo note.
APARTADOS = (
    ("Catalogo", ("productos del catalogo", "grupos comparables",
                  "productos comparables por kg/l/m",
                  "productos con codigo de barras")),
    ("Etiquetado y composicion",
     ("productos con algun sello", "productos con certificado",
      "productos con Nutri-Score", "productos con tabla nutricional",
      "productos con envase")),
)


def _en_castellano(d: date) -> str:
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}"


def _historico(con: duckdb.DuckDBPyConnection) -> tuple[int, int]:
    ruta = str(config.GOLD / "precio_diario.parquet").replace("\\", "/")
    if not Path(ruta).exists():
        return 0, 0
    filas, dias = con.execute(
        f"SELECT count(*), count(DISTINCT fecha) FROM '{ruta}'").fetchone()
    return filas, dias


def _ultima_de_cada_cadena() -> list[dict]:
    """La ultima fila de runs.csv por cadena, en orden de tamano."""
    log = config.DATA / "runs.csv"
    if not log.exists():
        return []
    ultimas: dict[str, dict] = {}
    with log.open(encoding="utf-8") as fh:
        for fila in csv.DictReader(fh):
            ultimas[fila["fuente"]] = fila
    return sorted(ultimas.values(), key=lambda f: -int(f["filas"]))


def _promociones(con: duckdb.DuckDBPyConnection) -> dict[str, int] | None:
    """Con texto de promocion, de tarjeta, y las que de verdad bajan el ticket."""
    columnas = {f[0] for f in con.execute("DESCRIBE g").fetchall()}
    if "promo_txt" not in columnas:
        return None
    club = ("coalesce(promo_club, false)" if "promo_club" in columnas else "false")
    online = ("coalesce(promo_solo_online, false)"
              if "promo_solo_online" in columnas else "false")
    con_texto, de_tarjeta, solo_online = con.execute(f"""
        SELECT count(promo_txt),
               count(*) FILTER (WHERE promo_txt IS NOT NULL AND {club}),
               count(*) FILTER (WHERE promo_txt IS NOT NULL AND {online}
                                  AND NOT {club})
          FROM g
    """).fetchone()
    return {"con_texto": con_texto, "de_tarjeta": de_tarjeta,
            "solo_online": solo_online,
            "utiles": con_texto - de_tarjeta - solo_online}


def documento(hoy: date | None = None) -> str:
    """El contenido entero del fichero, para poder probarlo sin escribir nada."""
    ruta = str(config.GOLD / "grupos.parquet").replace("\\", "/")
    con = duckdb.connect()
    con.execute(f"CREATE VIEW g AS SELECT * FROM '{ruta}'")
    medidas = {nombre: con.execute(consulta).fetchone()[0]
               for nombre, consulta, _fmt, _tol in COMPROBACIONES}
    filas_hist, dias_hist = _historico(con)
    promos = _promociones(con)
    con.close()

    fecha = _en_castellano(hoy or config.hoy_local())
    partes = [
        "# Las cifras de la ultima ejecucion",
        "",
        f"**Ejecucion del {fecha}.** Este documento tiene un solo trabajo:",
        "llevar los numeros de **hoy**. Lo reescribe entero",
        "`projects/cesta/cifras.py` al final de cada pasada.",
        "",
        "Existe porque los demas documentos guardan sus cifras **con la fecha",
        "en que se midieron**, y eso no es una cifra caducada sino un registro:",
        "cambiarla no la actualiza, la falsifica. Asi los numeros de hoy viven",
        "aqui, la historia se queda quieta, y `verificar_docs` encuentra aqui lo",
        "de hoy y deja de avisar sin que nadie tenga que reescribir nada.",
        "",
        "    uv run python -m projects.cesta.verificar_docs",
        "",
        "---",
        "",
    ]
    vistos: set[str] = set()
    for titulo, nombres in APARTADOS:
        partes += [f"## {titulo}", "", "| | |", "|---|---:|"]
        for nombre in nombres:
            if nombre not in medidas:
                continue
            vistos.add(nombre)
            partes.append(f"| {nombre} | **{_miles(medidas[nombre])}** |")
        partes.append("")
    sueltas = [n for n in medidas if n not in vistos]
    if sueltas:
        partes += ["## Otras", "", "| | |", "|---|---:|"]
        partes += [f"| {n} | **{_miles(medidas[n])}** |" for n in sueltas]
        partes.append("")

    partes += ["## Historico", "",
               f"    {_miles(filas_hist)} filas, {dias_hist} dias acumulados", ""]

    cadenas = _ultima_de_cada_cadena()
    if cadenas:
        partes += ["## Por cadena, la ultima captura de cada una", "",
                   "| cadena | productos | errores | tiempo | fecha |",
                   "|---|---:|---:|---:|---|"]
        for f in cadenas:
            partes.append(
                f"| {f['fuente']} | {_miles(int(f['filas']))} | {f['errores']} "
                f"| {_miles(int(float(f['segundos'])))} s | {f['ts'][:10]} |")
        partes.append("")

    if promos:
        partes += [
            "## Promociones", "", "| | |", "|---|---:|",
            f"| productos con texto de promocion | {_miles(promos['con_texto'])} |",
            f"| **de tarjeta** (no bajan lo que pagas en caja) "
            f"| **{_miles(promos['de_tarjeta'])}** |",
            f"| **solo por internet** (no bajan el ticket de la tienda) "
            f"| **{_miles(promos['solo_online'])}** |",
            f"| ofertas que cuentan de verdad | {_miles(promos['utiles'])} |",
            "",
        ]
    return "\n".join(partes).rstrip() + "\n"


def main() -> int:
    ruta = config.GOLD / "grupos.parquet"
    if not ruta.exists():
        print("  cifras: no hay gold todavia, no se reescribe CIFRAS.md")
        return 0
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(documento(), encoding="utf-8")
    print(f"  cifras: {DESTINO.name} reescrito con los numeros de hoy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
