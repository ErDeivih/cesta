"""Lo que la linea dice que se confirmo llega a la peticion, que es quien decide.

Sin esto, la regla de la confirmacion recibe siempre `None` y no cuenta ninguna: el dato estaba guardado en la
base, cruzado a las lineas... y se quedaba ahi.
"""
from __future__ import annotations

from plataforma.api import cesta


def _linea(**extra):
    base = {"id": "l1", "grupo_id": 1, "producto_id": None, "nombre_visto": "Leche entera 1 l", "cantidad": 2}
    return {**base, **extra}


def _captura(monkeypatch):
    """Sustituye `_candidatos`, que es quien recibe las peticiones, y se queda con ellas."""
    capturadas = []

    def falso(peticiones, fecha):
        capturadas.extend(peticiones)
        return {}

    monkeypatch.setattr(cesta, "_candidatos", falso)
    return capturadas


def test_la_peticion_se_lleva_lo_confirmado_de_la_linea(monkeypatch):
    capturadas = _captura(monkeypatch)
    cesta.estimacion([_linea(autorizado=True, autorizado_producto="p2", autorizado_cadena="dia")])
    assert capturadas, "no se construyo ninguna peticion"
    assert capturadas[0].autorizado is True
    assert capturadas[0].autorizado_producto == "p2"
    assert capturadas[0].autorizado_cadena == "dia"


def test_una_linea_sin_confirmacion_no_autoriza(monkeypatch):
    capturadas = _captura(monkeypatch)
    cesta.estimacion([_linea()])
    assert capturadas[0].autorizado is False
    assert capturadas[0].autorizado_producto is None


def test_el_coste_por_linea_tambien_lo_lleva(monkeypatch):
    """Es el otro sitio que construye peticiones, y se le olvido igual."""
    capturadas = _captura(monkeypatch)
    cesta.coste_por_linea([_linea(autorizado=True, autorizado_producto="p2", autorizado_cadena="dia")])
    assert capturadas, "no se construyo ninguna peticion"
    assert capturadas[0].autorizado_producto == "p2"
    assert capturadas[0].autorizado_cadena == "dia"
