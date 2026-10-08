"""Quitar una receta de un dia: se puede, y solo de tu plan y de ese dia.

Por HTTP sobre la aplicacion montada, con la sesion sustituida por el punto que el proyecto ya usa, que es
como se prueban los permisos: un anonimo no borra, B no borra lo de A, y un dia equivocado no borra el plan
de otro dia.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from core import recetas
from plataforma.api import main, sesion
from plataforma.api import recetas as api_recetas

ANA = {"id": "ana", "usuario": "ana", "nombre": "Ana"}
LUIS = {"id": "luis", "usuario": "luis", "nombre": "Luis"}


@pytest.fixture(autouse=True)
def base(tmp_path):
    api_recetas.ruta_base(tmp_path / "recetas.sqlite")
    yield
    main.app.dependency_overrides.clear()


def como(quien):
    main.app.dependency_overrides.clear()
    if quien is not None:
        main.app.dependency_overrides[sesion.usuario_actual] = lambda: quien
    return TestClient(main.app)


def test_quitar_una_receta_de_un_dia_la_deja_libre():
    con = recetas.conecta(api_recetas.ruta_base())
    rid = recetas.crear(con, "ana", "Lentejas", raciones=4)
    recetas.planificar(con, "ana", "2026-10-05", rid, comensales=3)
    assert len(recetas.plan(con, "ana", "2026-10-01", "2026-10-07")) == 1
    con.close()

    cliente = como(ANA)
    r = cliente.delete(f"/api/recetas/plan?fecha=2026-10-05&receta_id={rid}")
    assert r.status_code == 200, r.text
    assert como(ANA).get("/api/recetas/plan?desde=2026-10-01&hasta=2026-10-07").json()["plan"] == []


def test_quitar_dos_veces_da_404_y_no_dice_hecho_cuando_no_ha_hecho_nada():
    con = recetas.conecta(api_recetas.ruta_base())
    rid = recetas.crear(con, "ana", "Pure", raciones=2)
    recetas.planificar(con, "ana", "2026-10-05", rid)
    con.close()
    cliente = como(ANA)
    assert cliente.delete(f"/api/recetas/plan?fecha=2026-10-05&receta_id={rid}").status_code == 200
    assert cliente.delete(f"/api/recetas/plan?fecha=2026-10-05&receta_id={rid}").status_code == 404


def test_un_dia_equivocado_no_borra_el_plan_de_otro_dia():
    """Sin esta comprobacion, un error de tecleo en la fecha borraria otro dia y no se notaria."""
    con = recetas.conecta(api_recetas.ruta_base())
    rid = recetas.crear(con, "ana", "Sopa", raciones=2)
    recetas.planificar(con, "ana", "2026-10-05", rid)
    con.close()
    cliente = como(ANA)
    assert cliente.delete(f"/api/recetas/plan?fecha=2026-10-06&receta_id={rid}").status_code == 404
    plan = como(ANA).get("/api/recetas/plan?desde=2026-10-01&hasta=2026-10-07").json()["plan"]
    assert len(plan) == 1, "el plan del dia 5 sigue donde estaba"


def test_un_anonimo_no_quita_nada():
    assert como(None).delete("/api/recetas/plan?fecha=2026-10-05&receta_id=1").status_code == 401


def test_b_no_puede_quitar_la_receta_planificada_de_a():
    con = recetas.conecta(api_recetas.ruta_base())
    rid = recetas.crear(con, "ana", "Cocido", raciones=6)
    recetas.planificar(con, "ana", "2026-10-05", rid)
    con.close()
    assert como(LUIS).delete(f"/api/recetas/plan?fecha=2026-10-05&receta_id={rid}").status_code == 404
    plan = como(ANA).get("/api/recetas/plan?desde=2026-10-01&hasta=2026-10-07").json()["plan"]
    assert len(plan) == 1, "lo de A sigue planificado"
