"""La API del diario: las tres reglas del encargo, comprobadas por HTTP.

Se llama a los manejadores directamente, apuntando la base a un fichero temporal.
"""
from __future__ import annotations

import pytest
from fastapi import HTTPException

from plataforma.api import diario


@pytest.fixture(autouse=True)
def base_temporal(tmp_path):
    diario.ruta_base(tmp_path / "diario.sqlite")


def test_el_dia_separa_lo_conocido_de_lo_que_no_se_sabe():
    diario.apuntar(diario.EntradaIn(fecha="2026-10-07", comida="comida", kcal=600,
                                    fuente_dato=diario.diario.ETIQUETA))
    diario.apuntar(diario.EntradaIn(fecha="2026-10-07", comida="cena", tipo="receta",
                                    referencia="3", version="1"))
    resumen = diario.dia("2026-10-07")
    assert resumen["conocido"]["kcal"] == 600, "lo que no se sabe no suma cero"
    assert len(resumen["sin_dato"]) == 1
    assert resumen["completo"] is False


def test_una_compra_no_se_registra_como_consumo_y_lo_dice():
    with pytest.raises(HTTPException) as fallo:
        diario.apuntar(diario.EntradaIn(fecha="2026-10-07", comida="comida", tipo="compra", kcal=900))
    assert fallo.value.status_code == 400
    assert "no es consumo" in fallo.value.detail
    assert diario.dia("2026-10-07")["entradas"] == []


def test_una_receta_sin_version_se_rechaza_porque_no_se_podria_releer():
    with pytest.raises(HTTPException) as fallo:
        diario.apuntar(diario.EntradaIn(fecha="2026-10-07", comida="cena", tipo="receta",
                                        referencia="3"))
    assert fallo.value.status_code == 400
    assert "version" in fallo.value.detail


def test_una_fecha_que_no_es_fecha_o_una_comida_que_no_existe_son_error_del_cliente():
    for malo in (diario.EntradaIn(fecha="el martes", comida="comida"),
                 diario.EntradaIn(fecha="2026-10-07", comida="siesta")):
        with pytest.raises(HTTPException) as fallo:
            diario.apuntar(malo)
        assert fallo.value.status_code == 400


def test_una_entrada_se_puede_deshacer_y_borrar_dos_veces_da_404():
    creada = diario.apuntar(diario.EntradaIn(fecha="2026-10-07", comida="comida", kcal=300,
                                             fuente_dato=diario.diario.ESTIMADO))
    assert diario.borrar(creada["id"])["borrada"] == creada["id"]
    with pytest.raises(HTTPException) as fallo:
        diario.borrar(creada["id"])
    assert fallo.value.status_code == 404


def test_las_rutas_estan_en_el_orden_que_evita_la_trampa():
    caminos = [r.path for r in diario.rutas.routes]
    assert caminos.index("/api/diario/rango") < caminos.index("/api/diario/{fecha}")
