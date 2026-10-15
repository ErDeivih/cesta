"""Al anadir un grupo a la lista, se guarda el miembro que la ficha enseno.

Sin esto, la linea queda solo con el grupo y el motor tiene que **deducir** cual era el producto: lo hace por
identificador mas bajo, que no es lo que se vio -- la ficha enseña el mas barato por unidad --.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from plataforma.api import main


def _prepara(monkeypatch, grupo):
    anadidas = []

    def anade(lista_id, usuario_id, linea_id, nombre, grupo_id=None, producto_id=None,
              cantidad=1, nota=None, cadena_elegida=None, **kwargs):
        anadidas.append({"nombre": nombre, "grupo_id": grupo_id, "producto_id": producto_id})
        return {"id": linea_id}

    monkeypatch.setattr(main.almacen, "anade_linea", anade)
    # **Y las lineas que ya hay**, que el endpoint lee para no duplicar: sin sustituirla iria al
    # almacen de verdad, que aqui no esta arrancado. El doble va en paso con lo que se pide.
    monkeypatch.setattr(main.almacen, "lineas_de", lambda lista_id: [])
    monkeypatch.setattr(main.catalogo, "grupo", lambda grupo_id: grupo)
    monkeypatch.setattr(main, "_acceso", lambda *a, **k: "dueno")
    main.app.dependency_overrides[main.usuario_actual] = lambda: {
        "id": "u1", "usuario": "ana", "nombre": "Ana"}
    return anadidas, TestClient(main.app)


def _grupo_con_dos_miembros():
    """El que ensena la ficha es el primero: el mas barato por unidad."""
    return {
        "grupo_id": 1,
        "nombre": "Leche entera 1 l",
        "productos": [
            {"fuente": "dia", "id_fuente": "77", "nombre": "Leche entera 1 l", "precio_unidad_cent": 100},
            {"fuente": "mercadona", "id_fuente": "3", "nombre": "Leche entera 1 l", "precio_unidad_cent": 130},
        ],
    }


def test_se_guarda_el_miembro_que_ensena_la_ficha(monkeypatch):
    anadidas, cliente = _prepara(monkeypatch, _grupo_con_dos_miembros())
    r = cliente.post("/api/listas/lo-que-sea/desde-favoritos", json={"grupo_ids": [1]})
    assert r.status_code == 201, r.text
    main.app.dependency_overrides.clear()
    assert anadidas, "no se anadio nada"
    assert anadidas[0]["grupo_id"] == 1, anadidas
    assert anadidas[0]["producto_id"] == "dia:77", (
        f"se guardo {anadidas[0]['producto_id']}: sin el miembro mostrado, el motor tiene que deducirlo")


def test_sin_productos_en_la_ficha_no_se_inventa_uno(monkeypatch):
    """Si el catalogo no puede decir cual se enseno, se guarda el grupo y nada mas."""
    anadidas, cliente = _prepara(monkeypatch, {"grupo_id": 1, "nombre": "Algo", "productos": []})
    r = cliente.post("/api/listas/lo-que-sea/desde-favoritos", json={"grupo_ids": [1]})
    assert r.status_code == 201, r.text
    main.app.dependency_overrides.clear()
    assert anadidas[0]["producto_id"] is None, anadidas