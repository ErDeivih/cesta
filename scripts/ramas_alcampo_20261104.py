"""Cuanto pesa cada rama de Alcampo en los ultimos bronce: la rama que hoy cayo, en serie.

Read-only. La pregunta: "Folletos y Promociones: 1472 -> 716" es un corte del WAF
o es una rama que rota (folletos semanales)? Se mira su serie, y la de las demas.

    uv run python -m scripts.ramas_alcampo_20261104
"""
from __future__ import annotations

from collections import Counter

import duckdb

from core import config


def main() -> int:
    patron = (config.DATA / "bronze" / "fuente=alcampo" / "**" / "*.parquet").as_posix()
    c = duckdb.connect()
    c.execute("SET enable_progress_bar=false")
    filas = c.execute(
        f"""select fecha, categoria, count(*) as n
            from read_parquet('{patron}', hive_partitioning=true)
            where fecha is not null
            group by 1, 2 order by 1""").fetchall()

    por_dia: dict[str, Counter] = {}
    for fecha, categoria, n in filas:
        rama = (categoria or "(sin categoria)").split(" > ")[0].strip()
        clave = fecha.isoformat() if hasattr(fecha, "isoformat") else str(fecha)
        por_dia.setdefault(clave, Counter())[rama] += n

    dias = sorted(por_dia)[-12:]
    print("dias:", " ".join(dias))
    ramas = sorted({r for d in dias for r in por_dia[d]},
                   key=lambda r: -sum(por_dia[d][r] for d in dias))
    ancho = max(len(r) for r in ramas)
    print(f"\n{'rama':<{ancho}} " + " ".join(f"{d[5:]:>6}" for d in dias))
    for rama in ramas:
        vals = [por_dia[d][rama] for d in dias]
        print(f"{rama:<{ancho}} " + " ".join(f"{v:>6}" for v in vals))

    print("\n=== solo las ramas que se movieron mas del 40% entre dias ===")
    for rama in ramas:
        vals = [por_dia[d][rama] for d in dias]
        for a, b, da, db in zip(vals, vals[1:], dias, dias[1:], strict=False):
            if a >= 100 and b < a * 0.6:
                print(f"  {rama:<{ancho}} {da[5:]}={a} -> {db[5:]}={b}  ({100*(1-b/a):.0f}% menos)")

    print("\n=== total por dia ===")
    for d in dias:
        print(f"  {d} {sum(por_dia[d].values()):>7}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
