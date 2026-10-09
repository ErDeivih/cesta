"""Las calorias de una receta, y lo que NO se afirma cuando falta un dato.

La regla es la del diario y la de `escala`: **lo que falta no se convierte en cero**. Un ingrediente sin
producto confirmado no aporta 0 kcal: aporta nada, y se cuenta aparte para poder decir cuantas faltan.
"""
from __future__ import annotations

import pytest

from core.recetas import nutricion


def test_la_cuenta_de_una_receta_entera():
    """600 g de patatas (77 kcal/100 g) y 200 g de pollo (165 kcal/100 g): 462 + 330 = 792 kcal."""
    ingredientes = [{"nombre": "patatas", "cantidad": 600, "unidad": "g"},
                    {"nombre": "pollo", "cantidad": 200, "unidad": "g"}]
    productos = {0: {"kcal_100g": 77.0}, 1: {"kcal_100g": 165.0}}
    r = nutricion(ingredientes, productos)
    assert r["kcal"] == pytest.approx(792.0)
    assert r["identificados"] == 2
    assert r["completo"] is True


def test_un_ingrediente_sin_identificar_no_aporta_cero():
    """Suma lo que sabe y dice que falta uno -- no lo cuenta como cero."""
    ingredientes = [{"nombre": "patatas", "cantidad": 600, "unidad": "g"},
                    {"nombre": "algo raro", "cantidad": 100, "unidad": "g"}]
    productos = {0: {"kcal_100g": 77.0}}
    r = nutricion(ingredientes, productos)
    assert r["kcal"] == pytest.approx(462.0)
    assert r["sin_identificar"] == 1
    assert r["completo"] is False


def test_una_unidad_que_no_se_puede_pasar_a_gramos_queda_desconocida():
    """200 ml de leche necesitan una densidad; 1 cebolla, un peso. No se suponen."""
    ingredientes = [{"nombre": "leche", "cantidad": 200, "unidad": "ml"},
                    {"nombre": "cebolla", "cantidad": 1, "unidad": "ud"}]
    productos = {0: {"kcal_100g": 60.0}, 1: {"kcal_100g": 40.0}}
    r = nutricion(ingredientes, productos)
    assert r["kcal"] is None
    assert r["sin_cantidad"] == 2
    assert r["identificados"] == 0


def test_los_kilos_se_pasan_a_gramos():
    ingredientes = [{"nombre": "harina", "cantidad": 1, "unidad": "kg"}]
    r = nutricion(ingredientes, {0: {"kcal_100g": 364.0}})
    assert r["kcal"] == pytest.approx(3640.0)


def test_cada_nutriente_se_suma_por_separado():
    """Proteina sin energia: se suma la proteina y la energia queda desconocida."""
    ingredientes = [{"nombre": "clara", "cantidad": 100, "unidad": "g"}]
    r = nutricion(ingredientes, {0: {"proteinas_100g": 11.0}})
    assert r["proteinas_g"] == pytest.approx(11.0)
    assert r["kcal"] is None


def test_sin_ingredientes_no_hay_nada_que_decir():
    r = nutricion([], {})
    assert r["kcal"] is None
    assert r["completo"] is True      # cero ingredientes: no falta ninguno por identificar
