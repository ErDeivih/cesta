"""Mide el estado REAL de la ingesta: sin interpretar documentos.

Read-only sobre gold parquet. No escribe nada.

    uv run python -m scripts.medir_estado_ingesta_20261104
"""
from __future__ import annotations

import duckdb

PRECIO = "data/gold/precio_diario.parquet"
GRUPOS = "data/gold/grupos.parquet"
HOY = "2026-11-04"


def main() -> int:
    c = duckdb.connect()
    c.execute("SET enable_progress_bar=false")

    print(f"=== dias de precio por cadena (desde 2026-10-01), hoy={HOY} ===")
    q = f"""
        select fuente,
               count(distinct fecha) as dias,
               min(fecha) as desde,
               max(fecha) as hasta,
               count(*) filter (where fecha = '{HOY}') as filas_hoy,
               count(distinct fecha) filter (where fecha > '{HOY}') as dias_futuros
        from '{PRECIO}'
        where fecha >= '2026-10-01'
        group by 1 order by 2 desc
    """
    for r in c.execute(q).fetchall():
        print(f"  {r[0]:<10} dias={r[1]:<3} desde={r[2]} hasta={r[3]} filas_hoy={r[4]:<6} futuros={r[5]}")

    print("\n=== dias que faltan desde 2026-10-06 (ventana 30d) ===")
    q = f"""
        select fuente, list(substr(fecha,6,5) order by fecha)
        from (select distinct fuente, fecha from '{PRECIO}' where fecha >= '2026-10-06')
        group by 1 order by 1
    """
    for fuente, fechas in c.execute(q).fetchall():
        print(f"  {fuente:10s} {len(fechas):2d} dias: {' '.join(fechas)}")

    print("\n=== comparabilidad real: grupos con precio en N cadenas != NULL ===")
    q = f"""
        select n_cadenas, count(*) as grupos
        from (
          select grupo_id, count(distinct fuente) as n_cadenas
          from '{GRUPOS}'
          where grupo_id is not null and precio_cent is not null
          group by 1)
        group by 1 order by 1
    """
    tot = 0
    filas = c.execute(q).fetchall()
    for n, g in filas:
        tot += g
        print(f"  {n} cadenas: {g:6d} grupos")
    print(f"  TOTAL grupos comparables: {tot}")
    dos_o_mas = sum(g for n, g in filas if n >= 2)
    print(f"  con 2+ cadenas: {dos_o_mas}  ({100.0*dos_o_mas/tot:.1f}%)")

    print("\n=== reparto por cadena de esos grupos con 2+ cadenas ===")
    q = f"""
        with multi as (
          select grupo_id from '{GRUPOS}'
          where grupo_id is not null and precio_cent is not null
          group by 1 having count(distinct fuente) >= 2)
        select g.fuente, count(distinct g.grupo_id) as grupos, count(*) as ofertas
        from '{GRUPOS}' g join multi m using (grupo_id)
        group by 1 order by 2 desc
    """
    for r in c.execute(q).fetchall():
        print(f"  {r[0]:<10} grupos={r[1]:<6} ofertas={r[2]}")

    print("\n=== productos por cadena en gold (ofertas con precio) ===")
    q = f"""
        select fuente, count(*) as ofertas, count(distinct grupo_id) as en_grupo,
               count(*) filter (where ean is not null and ean <> '') as con_ean
        from '{GRUPOS}' group by 1 order by 2 desc
    """
    for r in c.execute(q).fetchall():
        print(f"  {r[0]:<10} ofertas={r[1]:<6} en_grupo={r[2]:<6} con_ean={r[3]}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
