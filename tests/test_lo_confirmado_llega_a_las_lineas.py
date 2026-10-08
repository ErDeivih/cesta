"""Lo confirmado llega a las lineas, con sus tres claves.

Se prueba el ayudante con el almacen sustituido: es lo que comprueba que el cruce no se deja ningun dato por el
camino, y que una linea sin confirmacion **no** queda autorizada por accidente.
"""
from __future__ import annotations

from plataforma.api import almacen, main


def _lineas():
    return [{"id": "l1", "nombre_visto": "MANZANAS"}, {"id": "l2", "nombre_visto": "PERAS"}]


def test_lo_confirmado_llega_con_su_producto_y_su_cadena(monkeypatch):
    monkeypatch.setattr(almacen, "autorizacion_de",
                        lambda lista_id: {"l1": {"autorizado": True, "producto": "p1", "cadena": "DIA"}})
    salida = main._con_autorizacion(_lineas(), "lista")
    assert salida[0]["autorizado"] is True
    assert salida[0]["autorizado_producto"] == "p1"
    assert salida[0]["autorizado_cadena"] == "DIA"


def test_una_linea_sin_confirmacion_no_queda_autorizada(monkeypatch):
    """El estado malo que hay que evitar: que un diccionario vacio cuente como un si."""
    monkeypatch.setattr(almacen, "autorizacion_de", lambda lista_id: {})
    salida = main._con_autorizacion(_lineas(), "lista")
    assert salida[0]["autorizado"] is False
    assert salida[0]["autorizado_producto"] is None
    assert salida[1]["autorizado"] is False


def test_las_lineas_conservan_lo_que_ya_tenian(monkeypatch):
    monkeypatch.setattr(almacen, "autorizacion_de", lambda lista_id: {})
    assert main._con_autorizacion(_lineas(), "lista")[0]["nombre_visto"] == "MANZANAS"


def test_un_si_sin_producto_no_se_da_por_autorizado(monkeypatch):
    """No se puede honrar, asi que no se marca: es la regla, aplicada ya en el cruce."""
    monkeypatch.setattr(almacen, "autorizacion_de",
                        lambda lista_id: {"l1": {"autorizado": True, "producto": None, "cadena": None}})
    salida = main._con_autorizacion(_lineas(), "lista")
    assert salida[0]["autorizado_producto"] is None
