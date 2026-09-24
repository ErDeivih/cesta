"""El techo del emparejador: cuantos pares ciertos puede ver el bloqueo, y por que no.

Por que existe
--------------
El emparejador no compara todos los pares: seria 57.000 x 57.000. Compara los que caen en el
**mismo bloque**, y el bloque es el formato (`core/matching.py:216`):

    bloque(cantidad, unidad) = (unidad_canon, round(cantidad, 3))

Eso es correcto -- un litro de leche no es un brik de 200 ml -- pero tiene una consecuencia que
hay que medir antes de tocar nada mas: **un par que no cae en el mismo bloque no se puede
encontrar nunca**, por muy bueno que sea el matcher. Ese es el techo del recall, y saber si el
65 % que se mide es una nota del matcher o un techo estructural es la primera pregunta de
cualquier trabajo de emparejamiento.

Se mide con la verdad de referencia que ya existe: **dos fichas con el mismo codigo de barras
son el mismo producto**, sin discusion. Si esas dos fichas caen en bloques distintos, el
bloqueo las ha perdido.

    uv run python -m projects.cesta.bloqueo
    uv run python -m projects.cesta.bloqueo --ejemplos 8

Lo que se hizo con esta medida la primera vez (8 de septiembre de 2026, sobre 1.767 pares
ciertos): 579 caian en bloques distintos, y la respuesta fue **una segunda pasada sin bloque y
con el liston mas alto** (`UMBRAL_SIN_FORMATO = 0.82`): si no se puede comprobar el tamano, se
exige que el nombre sea casi el mismo. Este medidor vuelve a contar lo mismo sobre el gold de
hoy, y separa los tres motivos, porque el arreglo de cada uno es distinto:

    no se le pudo leer el formato     no hay cantidad o no hay unidad -> se arregla en silver
    una cadena lo vende por unidad    ud frente a kg/l -> son dos formas de vender lo mismo
    y la otra al peso
    los numeros no coinciden           un pack frente a la pieza suelta -> el eje `pack`
"""
from __future__ import annotations

import argparse
from collections import Counter

import duckdb

from core import config
from core.matching import bloque

# Cuantos pares tiene que haber para que la medida signifique algo.
MINIMO_PARES = 200


def pares_ciertos() -> list[tuple]:
    """Los pares de fichas de **dos cadenas distintas** que comparten codigo de barras."""
    con = duckdb.connect()
    ruta = (config.GOLD / "grupos.parquet").as_posix()
    return con.execute(f"""
        SELECT a.fuente, a.nombre, a.cantidad, a.unidad_canon,
               b.fuente, b.nombre, b.cantidad, b.unidad_canon, a.ean
          FROM read_parquet('{ruta}') a
          JOIN read_parquet('{ruta}') b
            ON a.ean = b.ean AND a.ean IS NOT NULL AND a.fuente < b.fuente
    """).fetchall()


def _motivo(fila: tuple) -> str | None:
    """Por que este par no lo puede ver el bloqueo. `None` si si lo ve."""
    _fa, _na, ca, ua, _fb, _nb, cb, ub, _ean = fila
    if bloque(ca, ua) == bloque(cb, ub):
        return None
    if ca is None or not ua or cb is None or not ub:
        return "no se le pudo leer el formato"
    if ua != ub:
        return "una cadena lo vende por unidad y la otra al peso"
    return "misma unidad y cantidad distinta (pack frente a suelta)"


def resumen(ejemplos: int = 0) -> dict:
    """Los pares ciertos, los que ve el bloqueo y los que no, con su motivo."""
    filas = pares_ciertos()
    vistos = 0
    motivos: Counter = Counter()
    muestra: dict[str, list[str]] = {}
    for fila in filas:
        motivo = _motivo(fila)
        if motivo is None:
            vistos += 1
            continue
        motivos[motivo] += 1
        if ejemplos and len(muestra.get(motivo, [])) < ejemplos:
            muestra.setdefault(motivo, []).append(
                f"{fila[1][:44]} ({fila[0]}) <-> {fila[5][:44]} ({fila[4]})")
    total = len(filas)
    return {
        "pares_ciertos": total,
        "los_ve_el_bloqueo": vistos,
        "no_los_ve": total - vistos,
        "completeness_pct": 100.0 * vistos / total if total else 0.0,
        "cadenas": sorted({f[0] for f in filas} | {f[4] for f in filas}),
        "motivos": dict(motivos),
        "ejemplos": muestra,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="bloqueo", description=__doc__.split("\n")[0])
    ap.add_argument("--ejemplos", type=int, default=0,
                    help="cuantos pares enseñar de cada motivo")
    a = ap.parse_args(argv)

    r = resumen(ejemplos=a.ejemplos)
    if r["pares_ciertos"] < MINIMO_PARES:
        print(f"  Solo {r['pares_ciertos']} pares ciertos: con tan pocos, esta medida no dice "
              f"nada. Hace falta gold de verdad.")
        return 0

    print(f"  pares ciertos (mismo EAN, dos cadenas)     {r['pares_ciertos']:>7,}")
    print(f"  el bloqueo los puede ver                   {r['los_ve_el_bloqueo']:>7,}"
          f"   ({r['completeness_pct']:.1f} % -- es el TECHO del recall)")
    print(f"  el bloqueo los pierde                      {r['no_los_ve']:>7,}")
    print(f"  cadenas                                    {', '.join(r['cadenas'])}")
    print("\n  por que se pierden (un par puede tener mas de un motivo):")
    for motivo, cuantos in sorted(r["motivos"].items(), key=lambda x: -x[1]):
        print(f"    {motivo:<48} {cuantos:>6,}  "
              f"({100.0 * cuantos / r['pares_ciertos']:.1f} % de los pares ciertos)")
    for motivo, lineas in r["ejemplos"].items():
        print(f"\n  ejemplos de «{motivo}»:")
        for linea in lineas:
            print(f"    {linea}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
