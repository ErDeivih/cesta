"""La lista no puede mentir: ni «sin precio» donde lo hay, ni dos precios para la misma compra.

**Dos fallos, y los dos los destapa la revision del dueno:**

  1. una linea con **producto concreto** sale como «sin precio», porque la llave de `mejor` cambio a
     `(grupo, producto)` y `estimacion` seguia comparando contra el producto;
  2. el mismo 3x2 cuesta 200 en una linea de tres y 300 en dos de una y dos: cobra por linea y sin promociones.

El segundo es de antes; el primero es mio, y es silencioso. Por eso se prueban los dos.
"""
from __future__ import annotations

from plataforma.api import cesta


def _linea(cantidad, producto_id=None, linea_id="l1"):
    """Con las claves que `estimacion` lee de cada linea."""
    return {"id": linea_id, "grupo_id": 7, "producto_id": producto_id, "cantidad": cantidad,
            "nombre_visto": "Leche", "en_carrito": False, "tachado_en": None,
            "producto_movido": False}


def _monta(monkeypatch, promo="3x2", precio=100):
    """El mismo candidato para lo que pidan, por la llave del motor."""

    def candidatos(peticiones, fecha_tope):
        mejor = {}
        for p in peticiones:
            mejor[cesta._llave_candidato(p.grupo_id, p.producto_id, "dia")] = (
                "dia:P1", precio, "Leche", promo, None, None, None, 200, True)
        return mejor

    monkeypatch.setattr(cesta, "_candidatos", candidatos)
    monkeypatch.setattr(cesta, "_promos_vigentes", lambda *a, **k: {})


def test_una_linea_con_producto_concreto_encuentra_su_precio(monkeypatch):
    """La regresion: con producto concreto salia como «sin precio»."""
    _monta(monkeypatch)
    r = cesta.estimacion([_linea(1, producto_id="dia:P1")])
    assert r["sin_precio"] == 0, f"una linea que tiene precio cuenta como sin precio: {r}"
    assert r["total_cent"] == 100, r


def test_una_linea_de_grupo_tambien(monkeypatch):
    """El suelo: sin esto, el arreglo podria dejar de encontrar el caso de grupo."""
    _monta(monkeypatch)
    r = cesta.estimacion([_linea(1)])
    assert r["sin_precio"] == 0 and r["total_cent"] == 100, r


def test_dividir_la_compra_en_lineas_no_cambia_el_total(monkeypatch):
    """La regla del dueno, en la pantalla de la lista."""
    _monta(monkeypatch)
    de_tres = cesta.estimacion([_linea(3)])
    de_una_y_dos = cesta.estimacion([_linea(1, linea_id="l1"), _linea(2, linea_id="l2")])
    assert de_tres["total_cent"] == de_una_y_dos["total_cent"], (
        f"la misma compra cuesta {de_tres['total_cent']} en una linea y "
        f"{de_una_y_dos['total_cent']} en dos: dividir lineas no puede cambiar el precio")
    assert de_tres["total_cent"] == 200, f"un 3x2 sobre tres unidades de 100 son 200: {de_tres}"
