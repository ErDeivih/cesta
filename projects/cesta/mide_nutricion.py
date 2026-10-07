"""Cobertura de nutricion en las fichas guardadas: cuantas, no una.

    uv run python -m projects.cesta.mide_nutricion

Lee `data/fichas-lidl/*.html` (copias por producto que deja el colector) y cuenta en cuantas
aparecen estructuras de tabla nutricional, bases interpretables e ingredientes. Busca **estructuras**
y no palabras sueltas, que es la advertencia del encargo: "porcion" o "racion" aparecen en cualquier
interfaz y no son una tabla.

**Lo que dice y lo que no:** informa de cobertura sobre la muestra disponible. Con pocas fichas eso
es una muestra, y no se convierte en una afirmacion sobre el surtido de Lidl.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
CARPETA = RAIZ / "data" / "fichas-lidl"

# Los campos de una tabla nutricional espanola, y las bases que la hacen interpretable.
NUTRIENTES = ("valor energetico", "energia", "grasas", "saturadas", "hidratos", "azucares",
              "proteinas", "fibra", "sal", "kilojulio", "kcal")
BASES = ("por 100", "100 g", "100 ml")
INGREDIENTES = ("ingredientes:", "harina", "azucar", "cacao", "grasa vegetal")


def mide(html: str) -> dict:
    plano = html.lower()
    return {
        "nutrientes": sum(1 for t in NUTRIENTES if t in plano),
        "bases": sum(1 for t in BASES if t in plano),
        "ingredientes": sum(1 for t in INGREDIENTES if t in plano),
        "ldjson_producto": bool(re.search(r'"@type"\s*:\s*"Product"', html)),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--carpeta", type=Path, default=CARPETA)
    a = ap.parse_args(argv)
    fichas = sorted(a.carpeta.glob("*.html")) if a.carpeta.exists() else []
    if not fichas:
        print(f"no hay fichas guardadas en {a.carpeta}: se miden cuando el colector las deje")
        return 0
    print(f"fichas guardadas: {len(fichas)}")
    con_tabla = con_base = con_ingredientes = con_producto = 0
    for ficha in fichas:
        datos = mide(ficha.read_text(encoding="utf-8", errors="replace"))
        con_tabla += datos["nutrientes"] >= 3          # tres campos ya son una tabla, no una palabra
        con_base += datos["bases"] >= 1
        con_ingredientes += datos["ingredientes"] >= 2
        con_producto += datos["ldjson_producto"]
    total = len(fichas)
    print(f"  con datos estructurados de producto: {con_producto}/{total}")
    print(f"  con tabla nutricional (3+ campos):   {con_tabla}/{total}")
    print(f"  con base interpretable (por 100 g):  {con_base}/{total}")
    print(f"  con ingredientes (2+ señales):       {con_ingredientes}/{total}")
    print("\n  Cobertura sobre ESTA muestra. Con pocas fichas no se afirma nada del surtido: se dice")
    print("  cuantas se midieron y cuantas traen el dato.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
