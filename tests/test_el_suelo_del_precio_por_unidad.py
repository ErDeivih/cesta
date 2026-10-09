"""El suelo del precio por unidad depende de la unidad de referencia.

Un suelo unico de 10 centimos habria borrado datos buenos: una caja de 300 bastoncillos por 1,09 EUR son
0,363 centimos por pieza, y eso es correcto. Lo que no existe es un kilo de nada por dos centimos.

Medido el 9 de octubre de 2026: de las 287 filas por debajo de 10 centimos en drogueria, higiene y bebe,
la mayoria son bastoncillos, discos de algodon y toallitas con la aritmetica correcta.
"""
from __future__ import annotations

from core.normalize import SUELO_REFERENCIA_CENT, referencia_publicable


def test_por_kilo_o_litro_un_precio_imposible_no_se_publica():
    # Los valores medidos en gold por debajo del suelo, con unidad de peso o volumen.
    for imposible in (2, 3, 4, 9):
        assert not referencia_publicable(imposible, "kg"), imposible
        assert not referencia_publicable(imposible, "l"), imposible


def test_por_kilo_o_litro_un_precio_plausible_se_publica():
    for plausible in (60, 120, 6_875):
        assert referencia_publicable(plausible, "kg"), plausible
        assert referencia_publicable(plausible, "l"), plausible


def test_por_unidad_no_hay_suelo_porque_la_pieza_puede_costar_menos_de_un_centimo():
    """300 bastoncillos por 1,09 EUR: 0,363 centimos cada uno. Es un dato, no un error."""
    assert referencia_publicable(0.363, "ud")
    assert referencia_publicable(1, "ud")
    assert referencia_publicable(19, "ud")


def test_por_metro_ni_por_unidad_desconocida_tampoco_se_filtra():
    """Donde no hay medida que lo sostenga, no se inventa un umbral."""
    assert referencia_publicable(2, "m")
    assert referencia_publicable(2, None)


def test_lo_desconocido_sigue_desconocido():
    assert not referencia_publicable(None, "kg")
    assert not referencia_publicable(None, "ud")


def test_el_suelo_esta_declarado_y_es_bajo():
    """10 centimos por kilo o litro: filtra lo imposible, no lo barato."""
    assert SUELO_REFERENCIA_CENT == 10
