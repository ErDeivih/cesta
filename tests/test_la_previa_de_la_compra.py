"""La previa de consumir dice que se podria anotar y que no, y no escribe nada.

El diario rechaza el tipo `compra` a proposito, asi que este puente **propone**. Lo que se comprueba aqui es que
dice la verdad sobre la cobertura: las lineas sin nutricion en el catalogo salen aparte, con su nombre.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from plataforma.api import main

CON_NUTRICION = {"producto_id": "dia:1", "nombre": "Lentejas", "nutricion": "energia 350 kcal"}
SIN_NUTRICION = {"producto_id": "dia:2", "nombre": "Pan", "nutricion": None}


def _monta(monkeypatch, lineas, fichas):
    monkeypatch.setattr(main.almacen, "compras_de",
                        lambda lista_id, limite=12: [{"compra_id": "c1", "lineas": len(lineas)}])
    monkeypatch.setattr(main.almacen, "lineas_de_compra", lambda compra_id: list(lineas))
    monkeypatch.setattr(main.catalogo, "producto", lambda pid: fichas.get(pid))
    monkeypatch.setattr(main, "_acceso", lambda *a, **k: "dueno")
    main.app.dependency_overrides[main.usuario_actual] = lambda: {
        "id": "ana", "usuario": "ana", "nombre": "Ana"}
    return TestClient(main.app)


def _linea(linea_id, producto_id, nombre):
    return {"id": linea_id, "linea_id": linea_id, "grupo_id": None,
            "producto_id": producto_id, "nombre": nombre, "precio_cent": 100, "cadena": "dia"}


def test_dice_que_se_anotaria_y_que_no(monkeypatch):
    lineas = [_linea("l1", "dia:1", "Lentejas"), _linea("l2", "dia:2", "Pan")]
    cliente = _monta(monkeypatch, lineas, {"dia:1": CON_NUTRICION, "dia:2": SIN_NUTRICION})
    r = cliente.get("/api/listas/lo-que-sea/desde-la-compra")
    main.app.dependency_overrides.clear()
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert [x["nombre"] for x in cuerpo["anotarian"]] == ["Lentejas"], cuerpo
    assert cuerpo["sin_dato"] == ["Pan"], "lo que no se puede anotar tiene que decirse, no callarse"
    assert cuerpo["cobertura"] == {"con_dato": 1, "total": 2}, cuerpo


def test_una_linea_sin_producto_no_se_puede_anotar(monkeypatch):
    """Es el caso de la linea que apunta a otro producto: no hay ficha que consultar."""
    lineas = [_linea("l1", None, "Pan que no me llevo")]
    cliente = _monta(monkeypatch, lineas, {})
    r = cliente.get("/api/listas/lo-que-sea/desde-la-compra")
    main.app.dependency_overrides.clear()
    cuerpo = r.json()
    assert cuerpo["anotarian"] == [] and cuerpo["sin_dato"] == ["Pan que no me llevo"], cuerpo
    assert cuerpo["cobertura"] == {"con_dato": 0, "total": 1}, cuerpo


def test_sin_compras_lo_dice_sin_inventarse_nada(monkeypatch):
    monkeypatch.setattr(main.almacen, "compras_de", lambda lista_id, limite=12: [])
    monkeypatch.setattr(main, "_acceso", lambda *a, **k: "dueno")
    main.app.dependency_overrides[main.usuario_actual] = lambda: {
        "id": "ana", "usuario": "ana", "nombre": "Ana"}
    cliente = TestClient(main.app)
    r = cliente.get("/api/listas/lo-que-sea/desde-la-compra")
    main.app.dependency_overrides.clear()
    cuerpo = r.json()
    assert cuerpo["compra_id"] is None and cuerpo["cobertura"] == {"con_dato": 0, "total": 0}, cuerpo


def test_la_previa_no_escribe_en_el_diario(monkeypatch):
    """Es un GET, y el diario no acepta el tipo `compra`: la previa propone, no anota."""
    lineas = [_linea("l1", "dia:1", "Lentejas")]
    monkeypatch.setattr(main.almacen, "compras_de",
                        lambda lista_id, limite=12: [{"compra_id": "c1", "lineas": 1}])
    monkeypatch.setattr(main.almacen, "lineas_de_compra", lambda compra_id: list(lineas))
    monkeypatch.setattr(main.catalogo, "producto", lambda pid: CON_NUTRICION)
    monkeypatch.setattr(main, "_acceso", lambda *a, **k: "dueno")
    anotadas = []
    monkeypatch.setattr(main, "apuntar", lambda *a, **k: anotadas.append(a), raising=False)
    main.app.dependency_overrides[main.usuario_actual] = lambda: {
        "id": "ana", "usuario": "ana", "nombre": "Ana"}
    cliente = TestClient(main.app)
    cliente.get("/api/listas/lo-que-sea/desde-la-compra")
    main.app.dependency_overrides.clear()
    assert anotadas == [], anotadas
