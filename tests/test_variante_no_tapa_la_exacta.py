"""Una variante mas barata no puede tapar a la exacta del mismo grupo en la misma cadena.

Es la mitad que faltaba del caso E: el motor ya distingue las variantes, pero la **seleccion** se quedaba
con la mas barata sin mirar cual era, asi que la exacta se perdia. La regla se prueba con numeros.
"""
from __future__ import annotations

from plataforma.api import cesta


def test_la_exacta_gana_a_una_alternativa_mas_barata():
    """199 la variante, 209 la exacta: la eleccion tiene que ser la exacta."""
    assert cesta._prefiere(exacta_nueva=True, coste_nuevo=209,
                           exacta_actual=False, coste_actual=199) is True


def test_una_alternativa_no_desplaza_a_la_exacta_ni_siendo_mas_barata():
    assert cesta._prefiere(exacta_nueva=False, coste_nuevo=150,
                           exacta_actual=True, coste_actual=209) is False


def test_entre_dos_exactas_gana_la_mas_barata():
    assert cesta._prefiere(exacta_nueva=True, coste_nuevo=200,
                           exacta_actual=True, coste_actual=209) is True
    assert cesta._prefiere(exacta_nueva=True, coste_nuevo=220,
                           exacta_actual=True, coste_actual=209) is False


def test_entre_dos_alternativas_gana_la_mas_barata():
    assert cesta._prefiere(exacta_nueva=False, coste_nuevo=140,
                           exacta_actual=False, coste_actual=150) is True
    assert cesta._prefiere(exacta_nueva=False, coste_nuevo=160,
                           exacta_actual=False, coste_actual=150) is False


def test_la_seleccion_usa_la_regla_y_guarda_la_alternativa_aparte():
    """Se lee el codigo: la comparacion por coste a secas no puede volver, y la alternativa no se tira."""
    from pathlib import Path

    fuente = Path(cesta.__file__).read_text(encoding="utf-8")
    assert "_prefiere(exacta, coste" in fuente, "la eleccion tiene que usar la regla"
    assert 'mejor[(*clave, "alternativa")]' in fuente, \
        "sin guardar la alternativa aparte, no se puede ofrecer"
