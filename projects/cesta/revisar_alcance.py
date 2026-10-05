"""Ejecucion seca del alcance: que pediria y que excluiria, sobre el catalogo que ya hay.

**No toca la red.** Clasifica lo que ya esta en gold con la politica de `core/datos/alcance.yml`
y dice, por cadena, cuantos productos entran, cuantos salen y por que. Es la primera mitad de
T01: sirve para ver la lista real antes de cambiar nada, y para que la frontera del "consumible"
se fije con numeros delante en vez de a ojo.

    uv run python -m projects.cesta.revisar_alcance
    uv run python -m projects.cesta.revisar_alcance --fuente alcampo --ejemplos 12

Cuando la politica este aplicada dentro de los colectores, esto sigue valiendo para comprobar el
efecto de un cambio de reglas sin lanzar una pasada: es el mismo clasificador.
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict

import duckdb

from core import alcance, config


def _catalogo() -> list[tuple[str, str, str]]:
    """(fuente, nombre, categoria) de gold. Sin red: es lo que ya esta guardado."""
    ruta = (config.DATA / "gold" / "grupos.parquet").as_posix()
    con = duckdb.connect()
    con.execute("SET enable_progress_bar=false")
    filas = con.execute(
        f"""SELECT fuente, nombre, coalesce(categoria, '') AS categoria
            FROM read_parquet('{ruta}')""").fetchall()
    return [(f, n or "", c) for f, n, c in filas]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--fuente", help="mirar solo una cadena")
    ap.add_argument("--ejemplos", type=int, default=6, help="ejemplos por cadena y estado")
    a = ap.parse_args()

    try:
        filas = _catalogo()
    except Exception as exc:  # noqa: BLE001
        print(f"No hay catalogo que mirar ({type(exc).__name__}). Ejecuta el pipeline antes.")
        return 0
    if a.fuente:
        filas = [f for f in filas if f[0] == a.fuente]
    if not filas:
        print("No hay productos que clasificar con ese filtro.")
        return 0

    print(f"Politica version {alcance.version()}, {len(filas):,} productos clasificados "
          f"(sin tocar la red)\n".replace(",", "."))

    por_fuente: dict[str, Counter] = defaultdict(Counter)
    motivos: dict[str, Counter] = defaultdict(Counter)
    ejemplos: dict[tuple[str, str], list[str]] = defaultdict(list)
    for fuente, nombre, categoria in filas:
        d = alcance.clasificar_alcance(nombre, categoria)
        por_fuente[fuente][d.estado] += 1
        motivos[fuente][d.regla_id] += 1
        if len(ejemplos[(fuente, d.estado)]) < a.ejemplos:
            # **La regla y la palabra que decidieron**, no solo el resultado: sin esto, corregir
            # un falso positivo es adivinar. Se aprendio en la primera pasada, con seis productos
            # excluidos por una palabra del titulo que resultaba ser de comida.
            termino = d.evidencias.get("termino")
            ejemplos[(fuente, d.estado)].append(
                f"{nombre[:50]}  [{categoria[:38]}]  <- {d.regla_id}"
                + (f" por \"{termino}\"" if termino else ""))

    print(f"  {'cadena':<11}{'entran':>10}{'salen':>10}{'a revisar':>11}{'% fuera':>10}")
    total = Counter()
    for fuente in sorted(por_fuente):
        c = por_fuente[fuente]
        n = sum(c.values())
        fuera = c[alcance.EXCLUIDO]
        total.update(c)
        print(f"  {fuente:<11}{c[alcance.INCLUIDO]:>10,}{fuera:>10,}{c[alcance.REVISAR]:>11,}"
              f"{100 * fuera / n:>9.1f}%".replace(",", "."))
    n = sum(total.values())
    print(f"  {'TOTAL':<11}{total[alcance.INCLUIDO]:>10,}{total[alcance.EXCLUIDO]:>10,}"
          f"{total[alcance.REVISAR]:>11,}{100 * total[alcance.EXCLUIDO] / n:>9.1f}%"
          .replace(",", "."))

    print("\n  por que salen (las cinco reglas que mas):")
    todos = Counter()
    for fuente in por_fuente:
        todos.update(motivos[fuente])
    reglas = {r["id"]: r for r in (alcance.politica().get("excluye_producto", [])
                                   + alcance.politica().get("reglas_categoria", [])
                                   + alcance.politica().get("revisar_categoria", []))}
    for regla_id, cuantos in todos.most_common(5):
        motivo = reglas.get(regla_id, {}).get("motivo", "")
        print(f"    {cuantos:>7,}  {regla_id:<28} {motivo}".replace(",", "."))

    for fuente in sorted(por_fuente):
        for estado in (alcance.EXCLUIDO, alcance.REVISAR):
            lista = ejemplos.get((fuente, estado), [])
            if not lista:
                continue
            print(f"\n  {fuente} / {estado} (ejemplos):")
            for ejemplo in lista:
                print(f"    {ejemplo}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
