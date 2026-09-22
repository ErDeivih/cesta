"""Los ejes contradictorios del catalogo, contados. Es el medidor del encargo.

La barra de aceptacion pide **cero grupos con eje contradictorio** y **menos de 30
grupos de 11+ productos**. Esto mide las dos cosas sobre el gold de hoy, y sirve de
trinquete: `projects/cesta/verificar_docs` no lo mira, pero las pruebas si.

    uv run python -m projects.cesta.ejes
    uv run python -m projects.cesta.ejes --peores 5
"""
from __future__ import annotations

import argparse
from collections import Counter

import duckdb

from core import config
from core.atributos import contradicciones


def _filas(limite: int | None = None) -> list[tuple]:
    con = duckdb.connect()
    sql = (f"SELECT grupo_id, nombre, precio_unidad_cent "
           f"FROM read_parquet('{(config.GOLD / 'grupos.parquet').as_posix()}') "
           f"WHERE grupo_id IS NOT NULL AND precio_unidad_cent > 0")
    return con.execute(sql).fetchall()


def resumen(peores: int = 0) -> dict:
    """Los grupos con eje contradictorio, y el reparto por tamaño."""
    por_grupo: dict[int, list[str]] = {}
    tamano: Counter = Counter()
    for grupo_id, nombre, _precio in _filas():
        por_grupo.setdefault(int(grupo_id), []).append(nombre or "")
        tamano[int(grupo_id)] += 1

    contradictorios = {}
    for grupo_id, nombres in por_grupo.items():
        ejes = contradicciones(nombres)
        if ejes:
            contradictorios[grupo_id] = ejes

    grandes = {g: n for g, n in tamano.items() if n >= 11}
    grandes_malos = {g: e for g, e in contradictorios.items() if tamano[g] >= 11}

    salida = {
        "grupos": len(por_grupo),
        "grupos_con_eje_contradictorio": len(contradictorios),
        "grupos_de_11_o_mas": len(grandes),
        "de_esos_con_eje_contradictorio": len(grandes_malos),
        "peores": sorted(
            ((tamano[g], g, e) for g, e in contradictorios.items()),
            reverse=True)[:peores] if peores else [],
    }
    return salida


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="ejes")
    ap.add_argument("--peores", type=int, default=0,
                    help="cuantos grupos contradictorios enseñar, por tamaño")
    a = ap.parse_args(argv)

    r = resumen(peores=a.peores)
    print(f"  grupos                                  {r['grupos']:>7,}")
    print(f"  con algun eje contradictorio            "
          f"{r['grupos_con_eje_contradictorio']:>7,}")
    print(f"  grupos de 11 o mas productos            {r['grupos_de_11_o_mas']:>7,}")
    print(f"  de esos, con eje contradictorio         "
          f"{r['de_esos_con_eje_contradictorio']:>7,}")
    for n, grupo_id, ejes in r["peores"]:
        print(f"    grupo {grupo_id} ({n} productos): {ejes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
