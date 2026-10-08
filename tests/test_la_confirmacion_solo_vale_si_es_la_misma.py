"""La confirmacion solo vale si sigue siendo la misma sustitucion, en producto y cadena.

La regla es pura: se prueba sin base y sin catalogo. Lo que fija es lo que pidio el dueno -- que el motor pueda
cambiar de producto sin que la autorizacion vieja lo ampare.
"""
from __future__ import annotations

from plataforma.api import cesta


def _peticion(autorizado=False, producto=None, cadena=None):
    return cesta.Peticion(grupo_id=7, producto_id=None, cantidad=1, nombre="MANZANAS",
                          autorizado=autorizado, autorizado_producto=producto,
                          autorizado_cadena=cadena)


def _alternativa(producto="p1", cadena="DIA"):
    return {"producto_id": producto, "cadena": cadena, "nombre": "PERAS"}


def test_sin_si_no_cuenta():
    assert cesta._es_la_confirmada(_peticion(), _alternativa()) is False


def test_un_si_sin_producto_no_se_puede_honrar():
    """Es lo que la base rechaza desde la 012, y aqui se rechaza antes de llegar a ella."""
    assert cesta._es_la_confirmada(_peticion(True, None, "DIA"), _alternativa()) is False


def test_la_misma_sustitucion_cuenta():
    assert cesta._es_la_confirmada(_peticion(True, "p1", "DIA"), _alternativa()) is True


def test_otro_producto_no_cuenta_y_pide_confirmacion_nueva():
    """El caso que denuncio el dueno: el motor cambia de producto y el si viejo lo amparaba."""
    assert cesta._es_la_confirmada(_peticion(True, "p1", "DIA"), _alternativa(producto="p2")) is False


def test_el_mismo_producto_en_otra_cadena_tampoco_cuenta():
    """Es otra sustitucion: otro sitio y otro precio."""
    assert cesta._es_la_confirmada(_peticion(True, "p1", "DIA"), _alternativa(cadena="MERCADONA")) is False


def test_sin_alternativa_propuesta_no_hay_nada_que_confirmar():
    assert cesta._es_la_confirmada(_peticion(True, "p1", "DIA"), None) is False


def test_la_alternativa_tambien_se_lee_si_llega_como_objeto():
    """No se supone como llega: diccionario u objeto, las dos formas."""
    class Alternativa:
        producto_id = "p1"
        cadena = "DIA"

    assert cesta._es_la_confirmada(_peticion(True, "p1", "DIA"), Alternativa()) is True