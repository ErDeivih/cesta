"""La seccion se hereda dentro del grupo: el mismo producto, el mismo pasillo.

Un grupo son el mismo producto en varias cadenas. Si una lo trae con seccion y otra llega sin categoria -- o con
la categoria rota --, la que no la tiene **no se queda sin pasillo**: la hereda.

Es la parte que el backlog pedia y que recoge, medido el 9 de octubre, 149 productos de Aldi sin categoria y los
de DIA que la mandan como URL.
"""
from __future__ import annotations

import polars as pl

from projects.cesta.pipeline import _anota_seccion


def _tabla(filas):
    return pl.DataFrame({
        "fuente": [f for f, _c, _g in filas],
        "categoria": [c for _f, c, _g in filas],
        "grupo_id": [g for _f, _c, g in filas],
    })


def _una_categoria_con_seccion() -> tuple[str, str]:
    """Una categoria **real** que si tenga seccion, preguntada al catalogo.

    No se inventa: una clave que no exista devuelve None y la prueba mediria nada. Es la misma fuente que usa la
    pasada, asi que la prueba no puede desviarse de los datos.
    """
    from plataforma.api import catalogo

    fila = catalogo.conexion().execute(
        "SELECT fuente, categoria, seccion FROM grupos "
        "WHERE seccion IS NOT NULL AND categoria IS NOT NULL "
        "AND categoria NOT LIKE 'http%' LIMIT 1").fetchall()
    assert fila, "el catalogo no tiene ninguna categoria con seccion: algo va mal antes de esta prueba"
    return str(fila[0][0]), str(fila[0][1])


def test_el_que_no_tiene_seccion_la_hereda_del_grupo():
    fuente, categoria = _una_categoria_con_seccion()
    otra = "aldi" if fuente != "aldi" else "dia"
    tabla = _tabla([(fuente, categoria, 7), (otra, None, 7)])
    salida = _anota_seccion(tabla)
    secciones = dict(zip(salida["fuente"].to_list(), salida["seccion"].to_list(), strict=True))
    assert secciones[fuente] is not None, f"{fuente}/{categoria} deberia tener seccion: {secciones}"
    assert secciones[otra] == secciones[fuente], (
        f"el mismo producto tiene que ir al mismo pasillo: {secciones}")


def test_sin_grupo_no_se_inventa_nada():
    """Un producto suelto y sin categoria se queda sin seccion: no hay de quien heredar."""
    salida = _anota_seccion(_tabla([("aldi", None, None)]))
    assert salida["seccion"].to_list() == [None], salida


def test_sin_columna_categoria_la_seccion_es_nula():
    salida = _anota_seccion(pl.DataFrame({"fuente": ["dia"], "grupo_id": [1]}))
    assert salida["seccion"].to_list() == [None], salida
