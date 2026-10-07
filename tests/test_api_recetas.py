"""La API de recetas: las rutas que existen y el recorrido completo de una receta.

Se llama a los manejadores **directamente**, apuntando la base a un fichero temporal. Es la manera de
probar la API sin levantar nada, y la razon de que los manejadores no usen `Depends` para la conexion.
"""
from __future__ import annotations

import pytest

from plataforma.api import recetas


@pytest.fixture(autouse=True)
def base_temporal(tmp_path):
    recetas.ruta_base(tmp_path / "recetas.sqlite")
    yield
    recetas.ruta_base(tmp_path / "recetas.sqlite")


def test_el_recorrido_completo_de_una_receta():
    """Crear, leer, cambiar (version nueva), releer la vieja, archivar y que siga existiendo."""
    creada = recetas.crear(recetas.RecetaIn(
        nombre="Tortilla", raciones=4, preparacion="Pochar y cuajar.",
        ingredientes=[recetas.IngredienteIn(texto="patatas", cantidad=600, unidad="g")],
        minutos=40))
    rid = creada["id"]
    assert creada["receta"]["version"] == 1

    recetas.cambiar(rid, recetas.CambioIn(raciones=6))
    assert recetas.leer(rid)["raciones"] == 6, "la ultima version manda"
    assert recetas.leer(rid, version=1)["raciones"] == 4, "y la vieja no se mueve"

    assert [r["id"] for r in recetas.listar()["recetas"]] == [rid]
    recetas.archivar(rid)
    assert recetas.listar()["recetas"] == []
    assert len(recetas.listar(incluir_archivadas=True)["recetas"]) == 1
    assert recetas.leer(rid)["nombre"] == "Tortilla", "archivar no borra"


def test_una_receta_que_no_existe_da_404_y_no_inventa():
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as fallo:
        recetas.leer(999)
    assert fallo.value.status_code == 404
    with pytest.raises(HTTPException):
        recetas.leer(1, version=77)


def test_el_plan_se_pone_y_se_lee_y_fija_la_version():
    rid = recetas.crear(recetas.RecetaIn(nombre="Lentejas", raciones=4))["id"]
    recetas.planificar(recetas.PlanIn(fecha="2026-10-05", receta_id=rid, comensales=3))
    recetas.cambiar(rid, recetas.CambioIn(raciones=8))
    plan = recetas.plan(desde="2026-10-01", hasta="2026-10-07")["plan"]
    assert len(plan) == 1 and plan[0]["version"] == 1 and plan[0]["comensales"] == 3


def test_una_fecha_mala_en_el_plan_es_un_error_del_cliente_no_del_servidor():
    from fastapi import HTTPException
    rid = recetas.crear(recetas.RecetaIn(nombre="Pure"))["id"]
    with pytest.raises(HTTPException) as fallo:
        recetas.planificar(recetas.PlanIn(fecha="el martes", receta_id=rid))
    assert fallo.value.status_code == 400


def test_las_rutas_estan_declaradas_con_su_sitio():
    """`/plan` tiene que ir antes que `/{receta_id}`, o "plan" se leeria como un identificador."""
    caminos = [r.path for r in recetas.rutas.routes]
    assert "/api/recetas" in caminos and "/api/recetas/plan" in caminos
    assert "/api/recetas/{receta_id}" in caminos
    assert caminos.index("/api/recetas/plan") < caminos.index("/api/recetas/{receta_id}")
