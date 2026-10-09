"""Las unidades que Alcampo publica de verdad, no solo las del mapa antiguo.

Su API manda dos nombres para lo mismo: `unit` ("fop.price.per.100ml") y `unitName` ("PER_100ML"). El mapa
solo tenia la primera familia, asi que las etiquetas de `unitName` no se reconocian y el factor se quedaba
en 1: el valor de la cadena pasaba sin escalar.

Medido el 9 de octubre de 2026: **190.732 filas (29,8 %) sin unidad de referencia**. Estas son las
etiquetas que faltaban, y cada una tiene que dar lo mismo que su gemela `fop.*`.
"""
from __future__ import annotations

import pytest

from projects.cesta.collectors.alcampo import _unidad_referencia


def _por_unit_name(nombre: str):
    return _unidad_referencia({"unitPrice": {"unitName": nombre}}, "")


@pytest.mark.parametrize(("etiqueta", "esperado"), [
    ("PER_100ML", ("l", 10)),
    ("PER_100G", ("kg", 10)),
    ("PER_100GRAM", ("kg", 10)),
    ("PER_KG", ("kg", 1)),
    ("PER_L", ("l", 1)),
    ("PER_G", ("kg", 1000)),
    ("PER_ML", ("l", 1000)),
    ("PER_UNIT", ("ud", 1)),
    ("PER_PIECE", ("ud", 1)),
    ("PER_METER", ("m", 1)),
])
def test_las_etiquetas_de_unit_name_se_reconocen(etiqueta, esperado):
    """Antes del 10 de octubre de 2026 todas estas devolvian `(None, 1.0)`: sin unidad y sin escalar."""
    assert _por_unit_name(etiqueta) == esperado


def test_una_etiqueta_desconocida_sigue_sin_unidad():
    """Lo que no se sabe no se inventa: sin unidad y factor 1, que es la cara que ya existe."""
    assert _por_unit_name("PER_LO_QUE_SEA") == (None, 1.0)


def test_el_nombre_de_fop_sigue_valiendo():
    """La familia que ya estaba no se ha tocado."""
    assert _unidad_referencia({"unitPrice": {"unit": "fop.price.per.100ml"}}, "") == ("l", 10)
