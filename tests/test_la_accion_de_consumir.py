"""Anotar en el diario lo que se confirma, sin duplicar y sin inventar calorias.

El diario es **SQLite de verdad**, en un directorio temporal: es la unica forma de comprobar que la anotacion
queda guardada y que la segunda vez no se repite. El lado de la compra va sustituido.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from core import diario as nucleo
from plataforma.api import diario as api_diario
from plataforma.api import main


def _monta(tmp_path, monkeypatch, lineas):
    api_diario.ruta_base(tmp_path / "diario.sqlite")
    monkeypatch.setattr(main.almacen, "compras_de",
                        lambda lista_id, limite=12: [{"compra_id": "c1", "lineas": len(lineas)}])
    monkeypatch.setattr(main.almacen, "lineas_de_compra", lambda compra_id: list(lineas))
    monkeypatch.setattr(main, "_acceso", lambda *a, **k: "dueno")
    main.app.dependency_overrides[main.usuario_actual] = lambda: {
        "id": "ana", "usuario": "ana", "nombre": "Ana"}
    return TestClient(main.app)


def _linea(linea_id, nombre):
    return {"id": linea_id, "linea_id": linea_id, "grupo_id": None, "producto_id": "dia:1",
            "nombre": nombre, "precio_cent": 100, "cadena": "dia"}


def _anota(cliente, lineas=("l1",)):
    return cliente.post("/api/listas/lo-que-sea/desde-la-compra",
                        json={"fecha": "2026-10-07", "comida": "comida", "lineas": list(lineas)})


def test_anota_lo_confirmado_en_el_diario(tmp_path, monkeypatch):
    cliente = _monta(tmp_path, monkeypatch, [_linea("l1", "Lentejas")])
    r = _anota(cliente)
    main.app.dependency_overrides.clear()
    assert r.status_code == 201, r.text
    assert r.json()["anotadas"] == 1, r.json()
    con = nucleo.conecta(tmp_path / "diario.sqlite")
    entradas = nucleo.dia(con, "ana", "2026-10-07")["entradas"]
    con.close()
    assert len(entradas) == 1 and entradas[0]["referencia"] == "l1", entradas
    # **Sin calorias inventadas**: no hay dato, y el diario lo dice en su cobertura.
    assert entradas[0]["kcal"] is None, entradas[0]


def test_anotar_dos_veces_la_misma_linea_es_la_misma_anotacion(tmp_path, monkeypatch):
    cliente = _monta(tmp_path, monkeypatch, [_linea("l1", "Lentejas")])
    _anota(cliente)
    segunda = _anota(cliente)
    main.app.dependency_overrides.clear()
    assert segunda.json()["anotadas"] == 0 and segunda.json()["ya_estaban"] == ["Lentejas"], segunda.json()
    con = nucleo.conecta(tmp_path / "diario.sqlite")
    assert len(nucleo.dia(con, "ana", "2026-10-07")["entradas"]) == 1
    con.close()


def test_una_linea_que_no_es_de_esa_compra_no_se_anota(tmp_path, monkeypatch):
    """Sin este cruce, cualquiera podria anotar el identificador de una linea ajena."""
    cliente = _monta(tmp_path, monkeypatch, [_linea("l1", "Lentejas")])
    r = _anota(cliente, lineas=("l1", "de-otra-lista"))
    main.app.dependency_overrides.clear()
    assert r.json()["ajenas"] == ["de-otra-lista"], r.json()
    assert r.json()["anotadas"] == 1, r.json()
