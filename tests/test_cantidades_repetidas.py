"""Dos lineas del mismo producto suman su cantidad al elegir candidato.

La segunda prueba es la que vale: **el candidato elegido no puede depender de como se repartan las lineas**.
Pedir 2 y 3 es pedir 5, y la oferta que conviene se decide con las unidades que se compran.
"""
from __future__ import annotations

import pytest

from plataforma.api import cesta


def _peticion(referencia, cantidad, nombre="producto de prueba"):
    return cesta.Peticion(grupo_id=referencia, producto_id=None, cantidad=cantidad, nombre=nombre)


def test_dos_lineas_del_mismo_producto_suman_su_cantidad():
    """Puro, sin base: la cantidad de una referencia es la suma de sus lineas."""
    cantidades = cesta._cantidades_por_referencia([_peticion(7, 2), _peticion(7, 3)])
    assert cantidades == {7: 5}, cantidades


def test_referencias_distintas_no_se_mezclan():
    cantidades = cesta._cantidades_por_referencia([_peticion(7, 2), _peticion(9, 3)])
    assert cantidades == {7: 2, 9: 3}, cantidades


def test_al_menos_una_unidad():
    """Una linea con cantidad cero o negativa no puede quitar el producto de la compra."""
    assert cesta._cantidades_por_referencia([_peticion(7, 0)]) == {7: 1}


def _una_referencia_con_promocion():
    """Una referencia real del catalogo que tenga promocion: sin promocion, la cantidad no cambia el coste."""
    con = cesta.conexion()
    fila = con.execute("""
        SELECT grupo_id FROM grupos
         WHERE grupo_id IS NOT NULL AND precio_cent > 0 AND promo_txt IS NOT NULL
         LIMIT 1
    """).fetchone()
    return fila[0] if fila else None


def test_el_candidato_elegido_no_depende_de_como_se_repartan_las_lineas():
    """**La prueba que manda.** Pedir 2 y 3 en dos lineas tiene que dar lo mismo que pedir 5 en una."""
    referencia = _una_referencia_con_promocion()
    if referencia is None:
        pytest.skip("esta copia no tiene catalogo con promociones: no se puede distinguir")
    fecha = cesta._fecha_de_hoy()
    repartido = cesta._candidatos([_peticion(referencia, 2), _peticion(referencia, 3)], fecha)
    junto = cesta._candidatos([_peticion(referencia, 5)], fecha)
    # Se comparan los candidatos elegidos, no los diccionarios enteros: lo que importa es QUE se elige.
    elegido_repartido = {k: v[:2] for k, v in repartido.items() if isinstance(k, tuple) and len(k) == 2}
    elegido_junto = {k: v[:2] for k, v in junto.items() if isinstance(k, tuple) and len(k) == 2}
    assert elegido_repartido == elegido_junto, (
        "elegir con la cantidad de la ultima linea da otro candidato que elegir con las unidades de verdad")
