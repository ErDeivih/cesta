"""Recetas guardadas y versionadas: una version, una vez escrita, no se mueve.

La prueba central es la del versionado, porque de ella depende el diario: si editar una receta cambiara
lo que dice una version antigua, el diario de la semana pasada dejaria de ser cierto.
"""
from __future__ import annotations

from datetime import datetime

import pytest

from core import recetas


@pytest.fixture
def con(tmp_path):
    return recetas.conecta(tmp_path / "recetas.sqlite")


def test_una_receta_nueva_se_lee_entera(con):
    rid = recetas.crear(con, "Tortilla de patatas", raciones=4,
                        preparacion="Pochar la cebolla y cuajar.",
                        ingredientes=[{"texto": "patatas", "cantidad": 600, "unidad": "g"},
                                      {"texto": "huevos", "cantidad": 5, "unidad": "ud"}],
                        minutos=40, etiquetas="cena")
    leida = recetas.leer(con, rid)
    assert leida["nombre"] == "Tortilla de patatas"
    assert leida["raciones"] == 4 and leida["version"] == 1
    assert [i["texto"] for i in leida["ingredientes"]] == ["patatas", "huevos"]
    assert leida["ingredientes"][0]["cantidad"] == 600


def test_editar_crea_version_nueva_y_no_toca_la_anterior(con):
    """La promesa que sostiene el diario: la version 1 sigue diciendo lo que decia."""
    rid = recetas.crear(con, "Bizcocho", raciones=8,
                        ingredientes=[{"texto": "azucar", "cantidad": 200, "unidad": "g"}])
    numero = recetas.actualizar(con, rid, ingredientes=[{"texto": "azucar", "cantidad": 120,
                                                        "unidad": "g"}], minutos=45)
    assert numero == 2
    assert recetas.leer(con, rid, version=1)["ingredientes"][0]["cantidad"] == 200
    assert recetas.leer(con, rid)["ingredientes"][0]["cantidad"] == 120
    assert recetas.versiones(con, rid) == [1, 2]


def test_lo_que_no_se_cambia_se_hereda_copiado(con):
    """La version nueva queda completa por si misma, sin depender de la anterior."""
    rid = recetas.crear(con, "Gazpacho", raciones=4, preparacion="Batir todo.",
                        ingredientes=[{"texto": "tomate"}])
    recetas.actualizar(con, rid, raciones=6)
    v2 = recetas.leer(con, rid, version=2)
    assert v2["raciones"] == 6
    assert v2["preparacion"] == "Batir todo."
    assert [i["texto"] for i in v2["ingredientes"]] == ["tomate"]


def test_cambiar_el_nombre_no_crea_version_de_contenido_pero_si_actualiza(con):
    rid = recetas.crear(con, "Tarta", ingredientes=[{"texto": "harina"}])
    recetas.actualizar(con, rid, nombre="Tarta de manzana")
    assert recetas.leer(con, rid)["nombre"] == "Tarta de manzana"
    assert recetas.leer(con, rid, version=1)["nombre"] == "Tarta de manzana", (
        "el nombre es de la receta, no de la version")


def test_una_version_que_no_existe_devuelve_nada_en_vez_de_inventar(con):
    rid = recetas.crear(con, "Sopa")
    assert recetas.leer(con, rid, version=99) is None
    assert recetas.leer(con, 4242) is None


def test_una_receta_sin_nombre_o_sin_raciones_no_se_guarda(con):
    with pytest.raises(ValueError):
        recetas.crear(con, "   ")
    with pytest.raises(ValueError):
        recetas.crear(con, "Sopa", raciones=0)
    with pytest.raises(ValueError):
        recetas.crear(con, "Sopa", ingredientes=[{"cantidad": 3}]), "un ingrediente sin texto no vale"


def test_archivar_no_borra_y_el_recetario_separa(con):
    """Una receta que se comio sigue existiendo para el diario que la cita."""
    rid = recetas.crear(con, "Potaje")
    recetas.archivar(con, rid)
    assert recetas.listar(con) == []
    assert [r["id"] for r in recetas.listar(con, incluir_archivadas=True)] == [rid]
    assert recetas.leer(con, rid) is not None, "archivar no puede borrar el contenido"


def test_el_recetario_ensena_la_ultima_version(con):
    a = recetas.crear(con, "Arroz", raciones=2)
    recetas.actualizar(con, a, raciones=5)
    recetas.crear(con, "Ensalada", raciones=1)
    filas = {f["nombre"]: f for f in recetas.listar(con)}
    assert filas["Arroz"]["version"] == 2 and filas["Arroz"]["raciones"] == 5
    assert filas["Ensalada"]["raciones"] == 1


def test_el_plan_fija_la_version_y_sobrevive_a_los_cambios(con):
    """El plan de la semana pasada se relee tal cual, aunque la receta haya cambiado."""
    rid = recetas.crear(con, "Lentejas", raciones=4)
    recetas.planificar(con, "2026-10-05", rid, comensales=3)
    recetas.actualizar(con, rid, raciones=8)
    planificado = recetas.plan(con, "2026-10-01", "2026-10-07")
    assert len(planificado) == 1
    assert planificado[0]["version"] == 1 and planificado[0]["comensales"] == 3
    assert recetas.leer(con, rid, version=planificado[0]["version"])["raciones"] == 4


def test_el_plan_no_admite_fechas_que_no_son_fechas_ni_comensales_cero(con):
    rid = recetas.crear(con, "Pure")
    with pytest.raises(ValueError):
        recetas.planificar(con, "el martes", rid)
    with pytest.raises(ValueError):
        recetas.planificar(con, "2026-10-05", rid, comensales=0)
    with pytest.raises(ValueError):
        recetas.planificar(con, "2026-10-05", 999)


def test_las_fechas_se_guardan_para_poder_ordenar(con):
    rid = recetas.crear(con, "Cena", ahora=datetime(2026, 10, 7, 21, 30))
    assert recetas.leer(con, rid)["creada"].startswith("2026-10-07T21:30")
