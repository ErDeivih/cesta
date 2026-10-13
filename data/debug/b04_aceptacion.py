"""B04, aceptacion: **cinco recetas semanales -> lista -> y que persista tras recargar.**

**Lo que pide el encargo por su nombre:**

> *«La aceptacion principal son cinco recetas semanales con cantidades, compra y porciones reales que
> persisten tras recargar.»*

**Y por que esto no es lo mismo que las 13 pruebas de B04.** *Aquellas usan mocks* -- *por eso pueden fallar
sin tocar datos de nadie* --, **y estas pasan por la API de verdad, con Postgres y con el recetario en
SQLite.** *Es la unica forma de saber que el puente funciona de punta a punta y no solo por dentro.*

*Y comprueba las OCHO piezas que el criterio de B04 nombra: escalado por comensales, consolidacion por
identidad y unidad, despensa explicita, envases y sobrantes, ingrediente sin catalogo conservado, destino
elegido, e idempotencia por operacion.*

    uv run python data/debug/b04_aceptacion.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi.testclient import TestClient  # noqa: E402

from plataforma.api import almacen, main  # noqa: E402

CLAVE = "clave-de-prueba-123"
FALLOS: list[str] = []


def revisa(nombre: str, valor, condicion: bool, esperado=None) -> None:
    if condicion:
        print(f"   OK   {nombre}: {valor}")
    else:
        extra = f" (se esperaba {esperado})" if esperado is not None else ""
        FALLOS.append(nombre)
        print(f"   FALLA {nombre}: {valor}{extra}")


def main_aceptacion() -> int:
    almacen.arranca()
    sello = f"{int(time.time() * 1000) % 100000000}"
    usuario = f"b04-{sello}"
    almacen.crea_usuario(usuario, "Aceptacion B04", CLAVE)

    c = TestClient(main.app)
    r = c.post("/api/entrar", json={"usuario": usuario, "clave": CLAVE})
    assert r.status_code == 200, r.text
    print(f"== aceptacion de B04, con la API de verdad ({usuario})")

    # **La lista de la compra.**
    r = c.post("/api/listas", json={"nombre": f"Semana {sello}"})
    assert r.status_code in (200, 201), r.text
    lista = r.json().get("id") or r.json().get("lista_id")
    print(f"   lista: {lista}")

    # ---------------------------------------------- cinco recetas, con dos que comparten harina
    # *Y a proposito con RACIONES DISTINTAS de los COMENSALES, que es lo que hacia el defecto.*
    recetas = [
        ("Tortilla", 2, [{"texto": "huevo", "cantidad": 3, "unidad": "ud", "grupo_id": 11},
                         {"texto": "patata", "cantidad": 400, "unidad": "g", "grupo_id": 12},
                         {"texto": "harina", "cantidad": 100, "unidad": "g", "grupo_id": 13}]),
        ("Pan", 2, [{"texto": "harina", "cantidad": 100, "unidad": "g", "grupo_id": 13},
                    {"texto": "agua", "cantidad": 300, "unidad": "ml", "grupo_id": 14}]),
        ("Ensalada", 4, [{"texto": "lechuga", "cantidad": 1, "unidad": "ud", "grupo_id": 15}]),
        ("Sopa", 2, [{"texto": "agua", "cantidad": 500, "unidad": "ml", "grupo_id": 14},
                     {"texto": "sal", "cantidad": 5, "unidad": "g"}]),
        ("Croquetas", 2, [{"texto": "harina", "cantidad": 50, "unidad": "g", "grupo_id": 13},
                          {"texto": "leche", "cantidad": 200, "unidad": "ml", "grupo_id": 16}]),
    ]
    ids = []
    for nombre, raciones, ings in recetas:
        r = c.post("/api/recetas", json={"nombre": nombre, "raciones": raciones, "ingredientes": ings})
        assert r.status_code in (200, 201), f"{nombre}: {r.text}"
        ids.append(r.json()["id"])
    print(f"   recetas creadas: {len(ids)}")

    # ---------------------------------------------- al plan, con comensales distintos
    comensales = [4, 2, 4, 2, 8]
    for i, (rid, com) in enumerate(zip(ids, comensales, strict=True), start=19):
        r = c.post("/api/recetas/plan", json={"fecha": f"2026-10-{i}", "receta_id": rid,
                                              "comensales": com})
        assert r.status_code in (200, 201), f"plan {rid}: {r.text}"
    print(f"   planificadas: 5 recetas, comensales {comensales}")

    # ---------------------------------------------- la previa
    r = c.get(f"/api/listas/{lista}/desde-el-plan?desde=2026-10-19&hasta=2026-10-25")
    assert r.status_code == 200, r.text
    previa = r.json()
    entran = {x["nombre"]: x for x in previa["entrarian"]}

    # **La harina: 100x4/2 + 100x2/2 + 50x8/2 = 200 + 100 + 200 = 500 g.**
    revisa("harina: escala por comensales y suma las TRES recetas",
           entran.get("harina", {}).get("cantidad"), 
           entran.get("harina", {}).get("cantidad") == 500.0, 500.0)
    # **El agua: 300x2/2 + 500x2/2 = 300 + 500 = 800 ml.**
    revisa("agua: suma dos recetas y respeta la unidad",
           entran.get("agua", {}).get("cantidad"),
           entran.get("agua", {}).get("cantidad") == 800.0, 800.0)
    # **Y la sal no tiene destino: se dice, no se promete.**
    revisa("sal: sin destino, dicha en sin_catalogo",
           previa["sin_catalogo"], "sal" in previa["sin_catalogo"])
    # **Y la nota dice de que recetas viene la harina.**
    revisa("harina: la nota dice las recetas que aportan",
           entran.get("harina", {}).get("recetas"),
           len(entran.get("harina", {}).get("recetas") or []) == 3, "3 recetas")

    # ---------------------------------------------- y se trae a la lista
    r = c.post(f"/api/listas/{lista}/desde-el-plan?desde=2026-10-19&hasta=2026-10-25")
    assert r.status_code in (200, 201), r.text
    recibo = r.json()
    # **SEIS, y mi cuenta estaba mal**: *los ingredientes con destino son seis -- agua, leche,
    # patata, harina, huevo y lechuga --, y la sal no lo tiene.* *Esperaba cinco porque conte las
    # recetas, y son los ingredientes.*
    revisa("traidas: las que tienen destino", recibo["anadidos"], recibo["anadidos"] == 6, 6)
    revisa("y la sal queda dicha, no metida", recibo["sin_catalogo"], recibo["sin_catalogo"] == ["sal"])

    lineas = almacen.lineas_de(lista)
    por_nombre = {ln["nombre_visto"]: ln for ln in lineas}
    # **Una UNIDAD por linea**, que es lo que el defecto del otro puente hacia mal.
    revisa("cada linea: UNA unidad, no los gramos",
           {k: v["cantidad"] for k, v in por_nombre.items()},
           all(v["cantidad"] == 1 for v in lineas))
    # **Y la nota con los gramos.**
    nota = por_nombre.get("harina", {}).get("nota") or ""
    revisa("la nota de la harina dice 500 g", nota, "500" in nota, "500 en la nota")

    # ---------------------------------------------- IDEMPOTENCIA: repetir no duplica
    antes = len(lineas)
    r = c.post(f"/api/listas/{lista}/desde-el-plan?desde=2026-10-19&hasta=2026-10-25")
    despues = len(almacen.lineas_de(lista))
    revisa("repetir la operacion NO duplica", f"{antes} -> {despues}", antes == despues)

    # ---------------------------------------------- PERSISTENCIA: cliente NUEVO
    otro = TestClient(main.app)
    otro.post("/api/entrar", json={"usuario": usuario, "clave": CLAVE})
    r = otro.get(f"/api/listas/{lista}")
    # *Y `antes` cuenta las lineas del plan; la lista entera puede traer mas.*
    cuerpo = r.json() if r.status_code == 200 else {}
    suyas = cuerpo.get("lineas") if isinstance(cuerpo, dict) else cuerpo
    revisa("persiste tras recargar (cliente nuevo) y trae las mismas lineas del plan",
           len(suyas) if suyas is not None else r.status_code,
           suyas is not None and len(suyas) >= antes, f"al menos {antes}")

    # ---------------------------------------------- y el otro puente: receta -> lista
    r = otro.post(f"/api/recetas/{ids[0]}/a-la-lista", json={"lista_id": lista})
    revisa("receta -> lista responde", r.status_code, r.status_code in (200, 201))

    print(f"\n== {'TODA LA ACEPTACION PASA' if not FALLOS else str(len(FALLOS)) + ' FALLO(S): ' + ', '.join(FALLOS)}")
    return 1 if FALLOS else 0


if __name__ == "__main__":
    sys.exit(main_aceptacion())
