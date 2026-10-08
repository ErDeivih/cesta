"""Se elige la oferta mas barata para las unidades que se piden, no para una unidad imaginaria.

Es el caso C de las pruebas de aceptacion, con los numeros que se midieron antes de tocar el codigo:
dos unidades a 1,00 EUR con "2a unidad -50%" cuestan 150 cent; dos a 0,90 EUR sin promocion, 180. Hoy se
elegia la segunda, porque se comparaba el precio unitario antes de mirar la promocion.
"""
from __future__ import annotations

from plataforma.api import cesta


def test_la_promocion_cambia_cual_es_la_oferta_mas_barata():
    """El caso C, con sus numeros: 150 frente a 180 para DOS unidades."""
    con_promo = cesta._coste_para(2, 100, "2a unidad -50%")
    sin_promo = cesta._coste_para(2, 90, None)
    assert con_promo == 150 and sin_promo == 180
    assert con_promo < sin_promo, \
        "el envase mas caro por unidad es el mas barato al pagar dos: hay que elegirlo"


def test_una_unidad_sola_sigue_eligiendo_el_precio_mas_bajo():
    """La regla no puede romper lo de siempre: para una unidad manda el precio unitario."""
    assert cesta._coste_para(1, 100, "2a unidad -50%") == 100
    assert cesta._coste_para(1, 90, None) == 90
    assert cesta._coste_para(1, 90, None) < cesta._coste_para(1, 100, "2a unidad -50%")


def test_la_cantidad_manda_en_el_calculo():
    """Tres unidades con "3x2" cuestan dos: el coste es de la cantidad pedida, no de una."""
    assert cesta._coste_para(3, 100, "3x2") == 200
    assert cesta._coste_para(2, 100, "3x2") == 200, "con dos no se completa la oferta"
    assert cesta._coste_para(6, 100, "3x2") == 400


def test_sin_promocion_el_coste_es_cantidad_por_precio():
    assert cesta._coste_para(4, 75, None) == 300
    assert cesta._coste_para(1, 0, None) == 0


def test_la_seleccion_usa_la_regla_y_no_el_precio_unitario():
    """Se lee el codigo: si alguien vuelve a comparar `precio < actual[1]`, la prueba lo dice."""
    from pathlib import Path

    fuente = Path(cesta.__file__).read_text(encoding="utf-8")
    assert "_coste_para(cantidades.get" in fuente, "la seleccion tiene que usar el coste final"
    assert "if actual is None or precio < actual[1]:" not in fuente, \
        "volvio la comparacion por precio unitario del envase"
