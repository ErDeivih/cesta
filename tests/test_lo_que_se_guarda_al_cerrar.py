"""Lo que se guarda al cerrar tiene que llevar precio, y el de la tienda decidida.

**La llave:** una linea con producto concreto salia con `precio_cent: None` -- y eso se escribe en la compra como
«sin precio», que no es una estimacion que se mira: es un registro.

**El suelo:** si la linea tiene tienda decidida (`cadena_elegida`), se guarda **esa** tienda y su precio, aunque
haya otra mas barata. Guardar la mas barata cuando alguien decidio comprarlo en DIA apuntaria un precio que no se
pago.
"""
from __future__ import annotations

from plataforma.api import cesta


def _linea(linea_id="l1", producto_id=None, cantidad=1, cadena_elegida=None, movido=False):
    """Con las claves que `coste_por_linea` lee de cada linea."""
    return {"id": linea_id, "grupo_id": 7, "producto_id": producto_id, "cantidad": cantidad,
            "nombre_visto": "Leche", "cadena_elegida": cadena_elegida, "producto_movido": movido}


def _monta(monkeypatch):
    """Dos cadenas, con precios distintos: dia 100 y aldi 90."""

    def candidatos(peticiones, fecha_tope):
        mejor = {}
        for p in peticiones:
            for cadena, precio in (("dia", 100), ("aldi", 90)):
                mejor[cesta._llave_candidato(p.grupo_id, p.producto_id, cadena)] = (
                    "dia:P1", precio, "Leche", "3x2", None, None, None, precio, True)
        return mejor

    monkeypatch.setattr(cesta, "_candidatos", candidatos)
    monkeypatch.setattr(cesta, "_promos_vigentes", lambda *a, **k: {})


def test_una_linea_con_producto_concreto_guarda_su_precio(monkeypatch):
    """La llave: antes salia None, y None se guarda como «sin precio»."""
    _monta(monkeypatch)
    salida = cesta.coste_por_linea([_linea(producto_id="dia:P1")])
    assert salida["l1"]["precio_cent"] is not None, (
        f"se guardaria sin precio una linea que si lo tiene: {salida}")
    assert salida["l1"]["cadena"] == "aldi", salida


def test_una_linea_de_grupo_tambien_guarda_su_precio(monkeypatch):
    _monta(monkeypatch)
    salida = cesta.coste_por_linea([_linea()])
    assert salida["l1"]["precio_cent"] == 90 and salida["l1"]["cadena"] == "aldi", salida


def test_la_tienda_decidida_manda_sobre_la_mas_barata(monkeypatch):
    """El suelo: decidio DIA, se guarda DIA (100), no la mas barata (90)."""
    _monta(monkeypatch)
    salida = cesta.coste_por_linea([_linea(cadena_elegida="dia")])
    assert salida["l1"]["cadena"] == "dia" and salida["l1"]["precio_cent"] == 100, salida


def test_una_linea_que_apunta_a_otro_producto_no_se_inventa_precio(monkeypatch):
    _monta(monkeypatch)
    salida = cesta.coste_por_linea([_linea(movido=True)])
    assert salida["l1"]["precio_cent"] is None, salida
