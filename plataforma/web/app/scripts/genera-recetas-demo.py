#!/usr/bin/env python3
"""Genera 10 recetas de la demo con ingredientes del catálogo y sus calorías reales.

Cada ingrediente guarda el grupo del catálogo, los gramos y las kcal/100 g **de gold**. La
caloría por ración no se escribe aquí: la calcula `src/demo/recetas.ts` sumando
`gramos × kcal_100g / 100` y dividiendo por las raciones. Así el número se puede comprobar y no
es una cifra pegada a mano.

Uso: python scripts/genera-recetas-demo.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[4]
CATALOGO = Path(__file__).resolve().parents[1] / "src" / "demo" / "catalogo.json"
GOLD = RAIZ / "data" / "gold" / "v20261115-184138" / "grupos.parquet"
SALIDA = Path(__file__).resolve().parents[1] / "src" / "demo" / "recetas.json"

# *Cada receta: nombre, raciones, minutos, etiquetas, preparación e ingredientes por grupo y
# gramos. Los grupos están en el catálogo embebido; las kcal salen de gold, no de una tabla
# inventada.*
RECETAS = [
    {
        "nombre": "Arroz con tomate y atún",
        "raciones": 2,
        "minutos": 25,
        "etiquetas": "arroz, pescado, rápido",
        "preparacion": "Cuece el arroz en agua con una pizca de sal. Aparte, calienta el tomate triturado con el aceite, añade el atún escurrido y deja que espese. Mezcla con el arroz y sirve.",
        "ingredientes": [(7077, 80), (24149, 150), (18112, 80), (78952, 10)],
    },
    {
        "nombre": "Pasta con tomate y atún",
        "raciones": 2,
        "minutos": 20,
        "etiquetas": "pasta, pescado, rápido",
        "preparacion": "Cuece la pasta según el paquete. Calienta el tomate frito con el atún y un chorrito de aceite, mezcla con la pasta escurrida y deja un minuto al fuego.",
        "ingredientes": [(12506, 100), (22561, 100), (18112, 80), (78952, 5)],
    },
    {
        "nombre": "Lentejas con verduras",
        "raciones": 2,
        "minutos": 30,
        "etiquetas": "legumbres, cuchara",
        "preparacion": "Pocha la cebolla con el aceite. Añade el tomate y las lentejas escurridas, cubre con un poco de agua y deja hervir diez minutos.",
        "ingredientes": [(9375, 200), (1698, 80), (24149, 100), (78952, 10)],
    },
    {
        "nombre": "Pollo con arroz y verduras",
        "raciones": 2,
        "minutos": 35,
        "etiquetas": "pollo, arroz, sartén",
        "preparacion": "Dora el pollo en el aceite. Añade las verduras y el arroz, cubre con agua y deja cocer hasta que el arroz esté tierno.",
        "ingredientes": [(21334, 200), (7077, 80), (13053, 150), (78952, 10)],
    },
    {
        "nombre": "Salmón ahumado con pan y queso",
        "raciones": 2,
        "minutos": 10,
        "etiquetas": "pescado, frío, rápido",
        "preparacion": "Tuesta el pan. Unta el queso, coloca el salmón ahumado encima y termina con un poco de aceite.",
        "ingredientes": [(42990, 100), (3094, 80), (7791, 50)],
    },
    {
        "nombre": "Garbanzos con tomate",
        "raciones": 2,
        "minutos": 25,
        "etiquetas": "legumbres, cuchara",
        "preparacion": "Calienta el tomate con el aceite, añade los garbanzos escurridos y deja que se junten los sabores durante diez minutos.",
        "ingredientes": [(70550, 250), (24149, 150), (78952, 10)],
    },
    {
        "nombre": "Sopa de pollo con fideos",
        "raciones": 2,
        "minutos": 20,
        "etiquetas": "sopa, pollo, cuchara",
        "preparacion": "Calienta el caldo, añade los fideos y el pollo troceado y deja cocer hasta que los fideos estén listos.",
        "ingredientes": [(20395, 500), (10611, 40), (21334, 100)],
    },
    {
        "nombre": "Tostadas de tomate y atún",
        "raciones": 2,
        "minutos": 10,
        "etiquetas": "pan, pescado, rápido",
        "preparacion": "Tuesta el pan, unta el tomate triturado, reparte el atún y termina con unas gotas de aceite.",
        "ingredientes": [(3094, 80), (24149, 100), (18112, 80), (78952, 5)],
    },
    {
        "nombre": "Yogur con avena y miel",
        "raciones": 2,
        "minutos": 5,
        "etiquetas": "desayuno, lácteo, rápido",
        "preparacion": "Reparte el yogur en dos cuencos, añade los copos de maíz y la miel y deja reposar cinco minutos.",
        "ingredientes": [(3093, 250), (29647, 40), (3849, 20)],
    },
    {
        "nombre": "Leche con maíz y miel",
        "raciones": 2,
        "minutos": 5,
        "etiquetas": "desayuno, lácteo, rápido",
        "preparacion": "Calienta la leche, añade los copos de maíz y la miel y sirve al momento.",
        "ingredientes": [(11627, 300), (29647, 50), (3849, 15)],
    },
]


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    catalogo = json.loads(CATALOGO.read_text(encoding="utf-8"))
    por_grupo = {p["grupo_id"]: p for p in catalogo["productos"]}
    gold = pd.read_parquet(GOLD)
    kcal = gold.groupby("grupo_id").kcal_100g.first()

    recetas = []
    for i, receta in enumerate(RECETAS, start=1):
        ingredientes = []
        total = 0.0
        for grupo_id, gramos in receta["ingredientes"]:
            producto = por_grupo.get(grupo_id)
            if producto is None:
                raise SystemExit(f"El grupo {grupo_id} no está en el catálogo")
            valor = kcal.get(grupo_id)
            if pd.isna(valor):
                raise SystemExit(f"El grupo {grupo_id} no tiene kcal en gold")
            valor = float(valor)
            total += valor * gramos / 100
            ingredientes.append({
                "texto": producto["nombre"],
                "cantidad": gramos,
                "unidad": "g",
                "grupo_id": grupo_id,
                "producto_id": None,
                "fuente": None,
                "kcal_100g": round(valor, 2),
            })
        recetas.append({
            "id": i,
            "nombre": receta["nombre"],
            "creada": "2026-11-15T10:00:00+00:00",
            "archivada": False,
            "version": 1,
            "raciones": receta["raciones"],
            "minutos": receta["minutos"],
            "etiquetas": receta["etiquetas"],
            "preparacion": receta["preparacion"],
            "ingredientes": ingredientes,
        })
        print(f"{receta['nombre']}: {total:.1f} kcal totales, {total / receta['raciones']:.1f} por ración")

    SALIDA.write_text(
        json.dumps({"recetas": recetas}, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )
    print(f"{len(recetas)} recetas → {SALIDA}")


if __name__ == "__main__":
    main()
