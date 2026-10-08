"""La version del diario se verifica: no se anotan referencias inventadas.

Por HTTP sobre la aplicacion montada. Lo que se fija: que una receta sin version existente no se anota, que
la de otra persona tampoco, que la tuya si, y que la respuesta dice la procedencia de cada entrada.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from core import recetas
from plataforma.api import diario as api_diario
from plataforma.api import main, sesion
from plataforma.api import recetas as api_recetas

ANA = {"id": "ana", "usuario": "ana", "nombre": "Ana"}
LUIS = {"id": "luis", "usuario": "luis", "nombre": "Luis"}


@pytest.fixture(autouse=True)
def bases(tmp_path):
    api_diario.ruta_base(tmp_path / "diario.sqlite")
    api_recetas.ruta_base(tmp_path / "recetas.sqlite")
    yield
    main.app.dependency_overrides.clear()


def como(quien):
    main.app.dependency_overrides.clear()
    if quien is not None:
        main.app.dependency_overrides[sesion.usuario_actual] = lambda: quien
    return TestClient(main.app)


def una_receta(propietario="ana") -> int:
    con = recetas.conecta(api_recetas.ruta_base())
    try:
        return recetas.crear(con, propietario, "Lentejas", raciones=4)
    finally:
        con.close()


def test_una_receta_que_no_existe_no_se_anota():
    """El fallo que la revision manda cerrar: referencias inventadas."""
    r = como(ANA).post("/api/diario", json={
        "fecha": "2026-10-07", "comida": "cena", "tipo": "receta", "referencia": "4242",
        "version": "1"})
    assert r.status_code == 400, r.text
    assert "inventada" in r.json()["detail"]
    assert como(ANA).get("/api/diario/2026-10-07").json()["entradas"] == []


def test_una_version_que_no_existe_tampoco():
    rid = una_receta()
    r = como(ANA).post("/api/diario", json={
        "fecha": "2026-10-07", "comida": "cena", "tipo": "receta", "referencia": str(rid),
        "version": "99"})
    assert r.status_code == 400


def test_la_receta_de_otra_persona_tampoco_se_puede_anotar():
    """El aislamiento, aplicado tambien a la referencia: no basta con que exista."""
    rid = una_receta("ana")
    r = como(LUIS).post("/api/diario", json={
        "fecha": "2026-10-07", "comida": "cena", "tipo": "receta", "referencia": str(rid),
        "version": "1"})
    assert r.status_code == 400


def test_una_receta_sin_numero_se_rechaza_con_su_motivo():
    r = como(ANA).post("/api/diario", json={
        "fecha": "2026-10-07", "comida": "cena", "tipo": "receta", "referencia": "la de la abuela",
        "version": "1"})
    assert r.status_code == 400
    assert "numero de su receta" in r.json()["detail"]


def test_mi_receta_se_anota_y_queda_vinculada():
    rid = una_receta()
    r = como(ANA).post("/api/diario", json={
        "fecha": "2026-10-07", "comida": "cena", "tipo": "receta", "referencia": str(rid),
        "version": "1", "kcal": 480})
    assert r.status_code == 201, r.text
    entrada = como(ANA).get("/api/diario/2026-10-07").json()["entradas"][0]
    assert entrada["procedencia"] == "vinculada", "el enlace esta vivo y se dice"


def test_lo_anotado_a_mano_es_manual():
    como(ANA).post("/api/diario", json={
        "fecha": "2026-10-07", "comida": "comida", "kcal": 600, "fuente_dato": "etiqueta"})
    entrada = como(ANA).get("/api/diario/2026-10-07").json()["entradas"][0]
    assert entrada["procedencia"] == "manual", "no es una receta: es lo que alguien anoto"
