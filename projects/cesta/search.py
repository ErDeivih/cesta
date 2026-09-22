"""Busqueda local del catalogo actual en DuckDB.

Ejemplos:
    uv run python -m projects.cesta.search "aceite oliva"
    uv run python -m projects.cesta.search iphone --fuente alcampo
    uv run python -m projects.cesta.search leche --marca hacendado
"""
from __future__ import annotations

import argparse

import duckdb

from core import config
from core.normalize import nombre_limpio


def buscar(consulta: str, *, fuente: str | None = None, marca: str | None = None,
           limite: int = 20, con=None) -> list[dict]:
    """Devuelve candidatos ordenados por cobertura de palabras y precio."""
    if limite < 1 or limite > 200:
        raise ValueError("limite debe estar entre 1 y 200")
    texto = nombre_limpio(consulta)
    tokens = list(dict.fromkeys(texto.split()))
    if not tokens and not marca:
        return []

    propia = con is None
    con = con or duckdb.connect(str(config.WAREHOUSE), read_only=True)
    condiciones, params = [], []
    if tokens:
        condiciones.append("(" + " OR ".join("nombre_limpio LIKE ?" for _ in tokens) + ")")
        params.extend(f"%{t}%" for t in tokens)
    if fuente:
        condiciones.append("fuente = ?")
        params.append(fuente.lower())
    if marca:
        condiciones.append("lower(coalesce(marca, '')) LIKE ?")
        params.append(f"%{marca.lower()}%")

    score = " + ".join("CASE WHEN nombre_limpio LIKE ? THEN 1 ELSE 0 END" for _ in tokens)
    score = score or "0"
    score_params = [f"%{t}%" for t in tokens]
    frase_score = "CASE WHEN nombre_limpio LIKE ? THEN 5 ELSE 0 END" if texto else "0"
    inicio_score = "CASE WHEN nombre_limpio LIKE ? THEN 4 ELSE 0 END" if texto else "0"
    frase_params = [f"%{texto}%", f"{texto}%"] if texto else []
    sql = f"""
        SELECT fuente, id_fuente, nombre, marca, precio_cent, precio_unidad_cent,
               unidad_canon, disponible, url, precio_comparable,
               ({frase_score} + {inicio_score} + {score}) AS relevancia
        FROM producto
        WHERE {' AND '.join(condiciones)}
        ORDER BY relevancia DESC, disponible DESC, precio_comparable DESC,
                 length(nombre_limpio) ASC, precio_unidad_cent ASC NULLS LAST, nombre
        LIMIT ?
    """
    cur = con.execute(sql, [*frase_params, *score_params, *params, limite])
    columnas = [x[0] for x in cur.description]
    salida = [dict(zip(columnas, fila, strict=True)) for fila in cur.fetchall()]
    if propia:
        con.close()
    return salida


def _precio(fila: dict) -> str:
    if fila["precio_cent"] is None:
        return "sin precio"
    total = f"{fila['precio_cent'] / 100:.2f} EUR"
    if fila["precio_unidad_cent"] is not None and fila["unidad_canon"]:
        return f"{total} ({fila['precio_unidad_cent'] / 100:.2f} EUR/{fila['unidad_canon']})"
    return total


def main() -> int:
    ap = argparse.ArgumentParser(description="Busca en el catalogo local actual")
    ap.add_argument("consulta")
    ap.add_argument("--fuente", choices=["mercadona", "aldi", "alcampo", "dia", "carrefour"])
    ap.add_argument("--marca")
    ap.add_argument("--limite", type=int, default=20)
    args = ap.parse_args()
    filas = buscar(args.consulta, fuente=args.fuente, marca=args.marca, limite=args.limite)
    if not filas:
        print("sin resultados")
        return 1
    for fila in filas:
        marca = f" | {fila['marca']}" if fila["marca"] else ""
        estado = "" if fila["disponible"] else " | no disponible"
        print(f"[{fila['fuente']}] {fila['nombre']}{marca} | {_precio(fila)}{estado}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
