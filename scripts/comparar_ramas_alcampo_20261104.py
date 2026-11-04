"""Alcampo: la rama que hoy cayo, contra las de al lado, y control de la particion de hoy.

Read-only sobre bronze.

    uv run python -m scripts.comparar_ramas_alcampo_20261104
"""
from __future__ import annotations

import duckdb

PATRON = "data/bronze/fuente=alcampo/**/*.parquet"


def main() -> int:
    c = duckdb.connect()
    c.execute("SET enable_progress_bar=false")
    filas = c.execute(
        f"""select strftime(fecha,'%Y-%m-%d') as fecha, categoria, id_fuente
            from read_parquet('{PATRON}', hive_partitioning=true)
            where fecha is not null""").fetchall()

    por_dia: dict[str, dict[str, set]] = {}
    for fecha, categoria, idf in filas:
        rama = (categoria or "(sin categoria)").split(" > ")[0].strip()
        por_dia.setdefault(fecha, {}).setdefault(rama, set()).add(idf)

    dias = sorted(por_dia)[-4:]
    print("=== productos unicos por rama (no filas) ===")
    ramas = sorted({r for d in dias for r in por_dia[d]},
                   key=lambda r: -len(por_dia[dias[-1]].get(r, ())))
    ancho = max(len(r) for r in ramas)
    print(f"{'rama':<{ancho}} " + " ".join(f"{d[5:]:>7}" for d in dias) + "   hoy vs ayer")
    for rama in ramas:
        vals = [len(por_dia[d].get(rama, ())) for d in dias]
        v = f"{100 * (vals[-1] / vals[-2] - 1):+.0f}%" if vals[-2] else "-"
        print(f"{rama:<{ancho}} " + " ".join(f"{x:>7}" for x in vals) + f"   {v}")

    print("\n=== hoy: total y comprobaciones ===")
    hoy = por_dia[dias[-1]]
    total = sum(len(s) for s in hoy.values())
    print(f"  productos unicos: {total}")
    todos = [i for s in hoy.values() for i in s]
    print(f"  ids unicos de verdad: {len(set(todos))}  (duplicados: {len(todos) - len(set(todos))})")
    nulos = c.execute(
        f"""select count(*) from read_parquet('{PATRON}', hive_partitioning=true)
            where strftime(fecha,'%Y-%m-%d') = '{dias[-1]}'
              and (precio_cent is null or precio_cent <= 0)""").fetchone()[0]
    print(f"  filas sin precio > 0: {nulos}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
