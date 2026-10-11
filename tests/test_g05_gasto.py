"""G05, el gasto pagado: **un importe que falta no es un cero**.

El caso que da sentido al modulo es el ultimo: un periodo **sin ninguna linea con importe** tiene que
dar `total_cent is None` -- *no 0* --, porque un cero se lee como «ese mes no gaste nada» y lo que pasa
es que **no se sabe**. Y `completo` tiene que ser `False` en cuanto falte una, aunque el total sea
grande y creible: *un numero que parece completo y no lo esta es peor que no dar numero.*
"""
from __future__ import annotations

import pytest

from core.gasto import SEMANA, gasto_por_periodo


def _linea(fecha: str, importe: int | None):
    return {"fecha_compra": fecha, "importe_cent": importe}


def test_suma_lo_conocido_y_declara_lo_que_falta():
    """Un total con cobertura: **el numero y cuantas lineas no entraron.**"""
    filas = gasto_por_periodo([
        _linea("2026-10-01", 1200),
        _linea("2026-10-03", 800),
        _linea("2026-10-05", None),
    ])
    assert len(filas) == 1
    f = filas[0]
    assert f["periodo"] == "2026-10"
    assert f["total_cent"] == 2000, "solo suma lo que tiene importe"
    assert f["lineas"] == 3
    assert f["con_importe"] == 2
    assert f["sin_importe"] == 1
    assert f["completo"] is False, "con una sin importe, el total NO esta completo"


def test_sin_ningun_importe_el_total_es_None_y_no_cero():
    """**El caso que da sentido a todo esto.** Cero se leeria como «no gaste nada»."""
    f = gasto_por_periodo([_linea("2026-10-01", None), _linea("2026-10-02", None)])[0]
    assert f["total_cent"] is None, "no es 0: es que no se sabe"
    assert f["con_importe"] == 0
    assert f["sin_importe"] == 2
    assert f["completo"] is False


def test_cero_explicito_SI_es_un_importe_conocido():
    """Algo que salio gratis es un cero **sabido**, y no cobertura que falta."""
    f = gasto_por_periodo([_linea("2026-10-01", 0)])[0]
    assert f["total_cent"] == 0
    assert f["con_importe"] == 1
    assert f["sin_importe"] == 0
    assert f["completo"] is True


def test_todo_con_importe_esta_completo():
    f = gasto_por_periodo([_linea("2026-10-01", 500), _linea("2026-10-20", 700)])[0]
    assert f["total_cent"] == 1200
    assert f["completo"] is True


def test_agrupa_por_mes_y_por_semana_ISO():
    lineas = [_linea("2026-10-01", 100), _linea("2026-10-31", 200), _linea("2026-11-02", 300)]
    meses = gasto_por_periodo(lineas, "mes")
    assert [m["periodo"] for m in meses] == ["2026-10", "2026-11"]
    assert [m["total_cent"] for m in meses] == [300, 300]
    semanas = gasto_por_periodo(lineas, SEMANA)
    assert all(s["periodo"].startswith("2026-W") for s in semanas)
    assert sum(s["total_cent"] for s in semanas) == 600, "por semana se reparte igual, no se pierde"


def test_la_fecha_que_agrupa_es_la_de_la_compra():
    """**G05: separar fechas de compra y de precios.** Se agrupa por cuando se compro."""
    filas = gasto_por_periodo([
        {"fecha_compra": "2026-10-01", "fecha_precio": "2026-12-31", "importe_cent": 100},
    ])
    assert filas[0]["periodo"] == "2026-10"


def test_una_linea_sin_fecha_no_se_coloca_en_el_periodo_de_hoy():
    """Inventaria una compra. Se cuenta aparte y se declara."""
    filas = gasto_por_periodo([_linea("2026-10-01", 100), {"importe_cent": 900}])
    conocido = next(f for f in filas if f["periodo"] == "2026-10")
    assert conocido["total_cent"] == 100, "el de la linea sin fecha no entra en octubre"
    suelta = next(f for f in filas if f["periodo"] is None)
    assert suelta["lineas"] == 1
    assert suelta["completo"] is False


def test_un_periodo_desconocido_es_un_error_y_no_un_silencio():
    with pytest.raises(ValueError):
        gasto_por_periodo([], periodo="dia")
