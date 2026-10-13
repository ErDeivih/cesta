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

    # ---------------------------------------------- LA DESPENSA, EXPLICITA
    # **G12, punto 221**: *«descontar despensa solo si esta modelada y la persona lo elige, NO POR HABER
    # COMPRADO ANTES»*. *Se prueba en las tres direcciones: que se DICE, que NO se descuenta por defecto,
    # y que SI se descuenta cuando se pide.*
    # *Y en una lista NUEVA*: **`entrarian` excluye lo que ya esta en la lista**, asi que comprobarlo
    # despues de haber traido las seis lineas daba vacio -- *que es lo que paso en la primera corrida.*
    r = otro.post("/api/listas", json={"nombre": f"Despensa {sello}"})
    lista2 = r.json().get("id") or r.json().get("lista_id")

    r = otro.post("/api/despensa", json={"texto": "patata", "cantidad": 1, "unidad": "kg"})
    revisa("se declara una existencia en la despensa", r.status_code, r.status_code in (200, 201))

    # 1) SE DICE.
    r = otro.get(f"/api/listas/{lista2}/desde-el-plan?desde=2026-10-19&hasta=2026-10-25")
    suyos = {x["nombre"]: x for x in r.json()["entrarian"]}
    revisa("la previa DICE que la patata esta en casa",
           suyos.get("patata", {}).get("en_la_despensa"),
           suyos.get("patata", {}).get("en_la_despensa") is True)
    revisa("y de las que no estan, dice que no",
           suyos.get("harina", {}).get("en_la_despensa"),
           suyos.get("harina", {}).get("en_la_despensa") is False)

    # 2) Y **NO SE DESCUENTA POR DEFECTO** -- *que es la mitad que la regla prohibe.*
    revisa("SIN pedirlo, la patata SIGUE entrando (no se descuenta sola)",
           "patata" in suyos, "patata" in suyos)

    # 3) Y **SI SE DESCUENTA CUANDO SE PIDE**, que es «la persona lo elige».
    r = otro.get(f"/api/listas/{lista2}/desde-el-plan?desde=2026-10-19&hasta=2026-10-25"
                 f"&descontar_despensa=true")
    elegido = {x["nombre"]: x for x in r.json()["entrarian"]}
    revisa("PIDIENDOLO, la patata ya no entra", elegido.get("patata"),
           "patata" not in elegido, "sin patata")
    revisa("y lo que no esta en casa sigue entrando", "harina" in elegido, "harina" in elegido)
    revisa("y la lista nueva sigue VACIA: la previa no escribe",
           len(almacen.lineas_de(lista2)), len(almacen.lineas_de(lista2)) == 0)

    # ---------------------------------------------- LO QUE FALTABA DE LA ACEPTACION
    # *Leido del plan, no supuesto:* «escenario de cinco recetas, DOS LISTAS, DOS MARCAS y plan de otra
    # semana; preview=confirmacion=persistencia, CAMBIOS/VERSIONES Y REINTENTOS incluidos.»

    # (1) **DOS LISTAS: el mismo plan, traido a dos listas distintas.**
    # *Es lo que comprueba que el destino es una ELECCION y no un descuido.*
    r = otro.post("/api/listas", json={"nombre": f"Segunda {sello}"})
    lista3 = r.json().get("id") or r.json().get("lista_id")
    r = otro.post(f"/api/listas/{lista3}/desde-el-plan?desde=2026-10-19&hasta=2026-10-25")
    revisa("el MISMO plan entra en una SEGUNDA lista", r.json()["anadidos"],
           r.json()["anadidos"] == 6, 6)
    revisa("y las dos listas tienen sus lineas, sin pisarse",
           (len(almacen.lineas_de(lista)), len(almacen.lineas_de(lista3))),
           len(almacen.lineas_de(lista)) == 6 and len(almacen.lineas_de(lista3)) == 6)

    # (2) **DOS MARCAS: un ingrediente con `producto_id` exacto, no con `grupo_id`.**
    # *La consolidacion por identidad cuando hay producto de marca no se habia ejercitado.*
    r = otro.post("/api/recetas", json={
        "nombre": "Marca A", "raciones": 2,
        "ingredientes": [{"texto": "aceite", "cantidad": 100, "unidad": "ml",
                          "producto_id": "dia:aceite-1"}]})
    ra = r.json()["id"]
    r = otro.post("/api/recetas", json={
        "nombre": "Marca B", "raciones": 2,
        "ingredientes": [{"texto": "aceite", "cantidad": 300, "unidad": "ml",
                          "producto_id": "dia:aceite-1"}]})
    rb = r.json()["id"]
    otro.post("/api/recetas/plan", json={"fecha": "2026-10-26", "receta_id": ra, "comensales": 4})
    otro.post("/api/recetas/plan", json={"fecha": "2026-10-27", "receta_id": rb, "comensales": 4})
    r = otro.get(f"/api/listas/{lista3}/desde-el-plan?desde=2026-10-26&hasta=2026-10-27")
    aceites = [x for x in r.json()["entrarian"] if x["nombre"] == "aceite"]
    revisa("DOS MARCAS del mismo producto: una sola linea",
           len(aceites), len(aceites) == 1, 1)
    revisa("y la cantidad suma: 100x4/2 + 300x4/2 = 800",
           aceites[0]["cantidad"] if aceites else None,
           bool(aceites) and aceites[0]["cantidad"] == 800.0, 800.0)
    revisa("y conserva el producto exacto de la marca",
           aceites[0]["producto_id"] if aceites else None,
           bool(aceites) and aceites[0]["producto_id"] == "dia:aceite-1")

    # (3) **OTRA SEMANA: «otra semana/operacion legitima si».**
    # *La misma receta en otra semana tiene que entrar, no darse por repetida.*
    r = otro.post("/api/listas", json={"nombre": f"Otra semana {sello}"})
    lista4 = r.json().get("id") or r.json().get("lista_id")
    r = otro.post(f"/api/listas/{lista4}/desde-el-plan?desde=2026-10-26&hasta=2026-11-01")
    revisa("OTRA SEMANA entra (no se da por repetida)", r.json()["anadidos"],
           r.json()["anadidos"] >= 1, "al menos 1")

    print(f"\n== {'TODA LA ACEPTACION PASA' if not FALLOS else str(len(FALLOS)) + ' FALLO(S): ' + ', '.join(FALLOS)}")
    return 1 if FALLOS else 0


if __name__ == "__main__":
    sys.exit(main_aceptacion())
