"""El orden de los pasillos cruza a gold, y en el orden del recorrido.

El cliente puede saber que pasillos hay, pero no en que orden se recorre la tienda. `ORDEN` vive en el modulo del
scraper y la plataforma no puede importarlo, asi que el numero viaja con el producto -- la misma regla que hizo
falta para la seccion.

Y es el **recorrido**, no el alfabeto: `frutas-verduras` va antes que `bebidas`, aunque alfabeticamente no toque.
"""
from __future__ import annotations

import polars as pl

from core.secciones import ORDEN
from projects.cesta.pipeline import _anota_seccion


def _tabla(filas):
    return pl.DataFrame({
        "fuente": [f for f, _c, _g in filas],
        "categoria": [c for _f, c, _g in filas],
        "grupo_id": [g for _f, _c, g in filas],
    })


def _una_categoria_con_seccion() -> tuple[str, str]:
    from plataforma.api import catalogo

    fila = catalogo.conexion().execute(
        "SELECT fuente, categoria FROM grupos WHERE seccion IS NOT NULL "
        "AND categoria IS NOT NULL AND categoria NOT LIKE 'http%' LIMIT 1").fetchall()
    assert fila, "no hay ninguna categoria con seccion: revisar antes de esta prueba"
    return str(fila[0][0]), str(fila[0][1])


def test_el_orden_es_el_del_recorrido_y_no_el_alfabetico():
    fuente, categoria = _una_categoria_con_seccion()
    salida = _anota_seccion(_tabla([(fuente, categoria, 1)]))
    seccion = salida["seccion"].to_list()[0]
    assert seccion in ORDEN, f"{seccion!r} deberia estar en el recorrido"
    assert salida["seccion_orden"].to_list() == [ORDEN.index(seccion)], salida
    # frutas-verduras (0) antes que bebidas (10): alfabeticamente seria al reves.
    assert ORDEN.index("frutas-verduras") < ORDEN.index("bebidas")


def test_el_que_hereda_tambien_hereda_su_sitio():
    fuente, categoria = _una_categoria_con_seccion()
    otra = "aldi" if fuente != "aldi" else "dia"
    salida = _anota_seccion(_tabla([(fuente, categoria, 7), (otra, None, 7)]))
    ordenes = dict(zip(salida["fuente"].to_list(), salida["seccion_orden"].to_list(), strict=True))
    assert ordenes[otra] == ordenes[fuente] is not None, ordenes


def test_sin_pasillo_no_hay_sitio():
    salida = _anota_seccion(_tabla([("aldi", None, None)]))
    assert salida["seccion_orden"].to_list() == [None], salida
