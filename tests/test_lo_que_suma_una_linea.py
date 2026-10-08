"""Lo que suma una linea en la caja: la parte repartida, y sin inventar ceros.

Es la cuenta que decide el total de una compra guardada. Estaba dentro del cierre, sin prueba posible sin
PostgreSQL, y era donde vivia el fallo: unitario x cantidad por linea, sin ofertas.
"""
from __future__ import annotations

from plataforma.api.almacen import _lo_que_se_paga


def test_la_parte_repartida_manda_sobre_el_unitario():
    """Tres unidades con un 3x2: la parte repartida son 200, no 300."""
    assert _lo_que_se_paga(100, 200, 3) == 200


def test_sin_parte_se_calcula_unitario_por_cantidad():
    """Una llamada que no trae la parte: el mismo numero cuando la linea va sola."""
    assert _lo_que_se_paga(100, None, 3) == 300
    assert _lo_que_se_paga(120, None, 1) == 120


def test_sin_precio_no_se_inventa_un_cero():
    """Un cero afirmaria que salio gratis; el cierre lo cuenta aparte."""
    assert _lo_que_se_paga(None, None, 2) is None
    assert _lo_que_se_paga(None, 500, 2) is None


def test_las_partes_de_una_compra_suman_lo_que_se_enseño():
    """Dos lineas de una y dos unidades: 66+134 o 67+133, pero 200."""
    partes = [_lo_que_se_paga(100, 67, 1), _lo_que_se_paga(100, 133, 2)]
    assert sum(partes) == 200, partes
