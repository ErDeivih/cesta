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


def cuenta_cobertura(medidas: list[dict]) -> dict:
    """Cuantas fichas traen cada cosa, con los umbrales declarados en un solo sitio.

    Los umbrales son lo que separa una medida de un titular: **tres campos** de tabla nutricional ya
    son una tabla (uno solo es una palabra que aparece en cualquier interfaz) y **dos señales** ya son
    ingredientes. Estan aqui, y no dentro del `print`, para poder probarlos.
    """
    return {
        "fichas": len(medidas),
        "con_producto": sum(1 for d in medidas if d["ldjson_producto"]),
        "con_tabla": sum(1 for d in medidas if d["nutrientes"] >= 3),
        "con_base": sum(1 for d in medidas if d["bases"] >= 1),
        "con_ingredientes": sum(1 for d in medidas if d["ingredientes"] >= 2),
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
    cobertura = cuenta_cobertura(
        [mide(ficha.read_text(encoding="utf-8", errors="replace")) for ficha in fichas])
    total = cobertura["fichas"]
    print(f"  con datos estructurados de producto: {cobertura['con_producto']}/{total}")
    print(f"  con tabla nutricional (3+ campos):   {cobertura['con_tabla']}/{total}")
    print(f"  con base interpretable (por 100 g):  {cobertura['con_base']}/{total}")
    print(f"  con ingredientes (2+ señales):       {cobertura['con_ingredientes']}/{total}")
    print("\n  Cobertura sobre ESTA muestra. Con pocas fichas no se afirma nada del surtido: se dice")
    print("  cuantas se midieron y cuantas traen el dato.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
