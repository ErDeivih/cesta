"""El suelo del precio por unidad: un valor imposible no se publica.

El respaldo por cadena del precio de referencia acierta casi siempre, pero cuando la cadena no publica
formato con el que comprobar deja pasar lecturas equivocadas. Medido: 1.524 filas (2,9 %) con precios
por unidad de 2 a 19 centimos, en las cinco cadenas.

Lo que se prueba aqui es la regla sola, sin motor: un valor imposible no se publica, uno plausible si,
y **uno vacio sigue vacio** -- "no lo se" no se convierte en "no vale".
"""
from __future__ import annotations

from projects.cesta.pipeline import SUELO_REFERENCIA_CENT, _referencia_publicable


def test_un_precio_imposible_no_se_publica():
    # Los valores medidos en gold por debajo del suelo: 2, 3, 4 y 9 centimos por unidad.
    for imposible in (2, 3, 4, 9):
        assert not _referencia_publicable(imposible), imposible


def test_un_precio_plausible_se_publica():
    # Un brick de leche a 0,60 EUR/l, un kilo de patatas a 1,20, un kilo de azafran a 6.875.
    for plausible in (60, 120, 6_875):
        assert _referencia_publicable(plausible), plausible


def test_el_suelo_no_es_un_umbral_de_barato():
    """19 centimos por unidad es posible -- un sobre, una bolsita, una pastilla -- y se publica.

    La medicion cortaba en 20 centimos porque era un umbral de *medida*; el suelo de correccion es 10 y
    filtra lo imposible, no lo barato. La distincion importa: si el suelo subiera, empezaria a borrar
    datos buenos.
    """
    assert _referencia_publicable(19)
    assert _referencia_publicable(SUELO_REFERENCIA_CENT)


def test_lo_desconocido_sigue_desconocido():
    """Sin dato no se inventa: vacio se queda vacio."""
    assert not _referencia_publicable(None)


def test_el_suelo_esta_declarado_y_es_bajo():
    """El suelo es bajo a proposito: no filtra barato, filtra imposible."""
    assert SUELO_REFERENCIA_CENT == 10
