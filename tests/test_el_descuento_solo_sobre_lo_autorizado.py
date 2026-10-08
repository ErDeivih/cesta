"""En la lista, la oferta no se aplica a cantidades pendientes de autorizacion.

Dos lineas del mismo producto con un 3x2: una es el producto pedido (exacta) y la otra es una sustitucion **sin
confirmar**. La oferta puede agrupar las unidades de la exacta; **no** las de la que espera confirmacion, porque
nadie ha aceptado esa sustitucion todavia.
"""
from __future__ import annotations

from core import identidad
from plataforma.api import cesta

REFERENCIA = identidad.Producto(fuente="dia", id_fuente="ref", nombre="Leche", gtin="8410000000001")


def _linea(linea_id, cantidad, autorizado_producto=None, producto_id=None):
    return {"id": linea_id, "grupo_id": 7, "producto_id": producto_id, "cantidad": cantidad,
            "nombre_visto": "Leche", "cadena_elegida": None, "producto_movido": False,
            "autorizado": autorizado_producto is not None,
            "autorizado_producto": autorizado_producto,
            "autorizado_cadena": "dia" if autorizado_producto else None}


def _monta(monkeypatch):
    """El candidato es una **sustitucion** (GTIN distinto al pedido), con un 3x2."""

    def candidatos(peticiones, fecha_tope):
        mejor = {}
        for p in peticiones:
            clave = cesta._llave_candidato(p.grupo_id, p.producto_id, "dia")
            mejor[clave] = (("dia:S", 100, "Leche de otra marca", "3x2", "8410000000009",
                             REFERENCIA, None, 200, False))
        return mejor

    monkeypatch.setattr(cesta, "_candidatos", candidatos)
    monkeypatch.setattr(cesta, "_promos_vigentes", lambda *a, **k: {})


def test_la_oferta_no_agrupa_lo_que_espera_confirmacion(monkeypatch):
    _monta(monkeypatch)
    # Una linea sin confirmar: su cantidad no puede entrar en el grupo de la oferta.
    pendiente = cesta.estimacion([_linea("l1", 3)])
    assert pendiente["total_cent"] == 300, (
        f"una sustitucion sin confirmar no puede llevar la oferta aplicada: {pendiente}")
