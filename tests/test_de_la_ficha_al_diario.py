"""De la ficha del producto al diario: la cuenta, y lo que NO se afirma.

La regla que gobierna esto es la del propio diario: **ausencia no es cero**. Un producto sin proteinas
publicadas no aporta 0 g de proteina: no aporta nada, y la entrada lo dice con `None`.
"""
from __future__ import annotations

import pytest

from core import diario


def test_la_cuenta_es_gramos_por_valor_de_100g():
    """150 g de un producto de 485 kcal/100 g son 727,5 kcal, y sus proteinas se calculan igual."""
    valores = diario.de_ficha({"kcal_100g": 485.0, "proteinas_100g": 6.0}, 150)
    assert valores["kcal"] == pytest.approx(727.5)
    assert valores["proteinas_g"] == pytest.approx(9.0)


def test_lo_que_el_producto_no_trae_se_queda_en_None_y_no_en_cero():
    """Un cero es una afirmacion -- "no lleva proteina" -- y no la tenemos."""
    valores = diario.de_ficha({"kcal_100g": 200.0}, 100)
    assert valores["kcal"] == pytest.approx(200.0)
    assert valores["proteinas_g"] is None
    assert valores["grasas_g"] is None
    assert valores["hidratos_g"] is None


def test_cada_nutriente_se_calcula_por_separado():
    """12 g de proteina son 12 g de proteina aunque la energia no se sepa."""
    valores = diario.de_ficha({"proteinas_100g": 12.0}, 100)
    assert valores["proteinas_g"] == pytest.approx(12.0)
    assert valores["kcal"] is None


def test_un_producto_sin_ningun_nutriente_no_se_anota():
    """Si no hay nada que decir, no se escribe una entrada vacia: se dice que no hay."""
    with pytest.raises(ValueError):
        diario.de_ficha({}, 100)


def test_los_gramos_tienen_que_ser_un_numero_utilizable():
    for malos in (-1, float("nan"), float("inf")):
        with pytest.raises(ValueError):
            diario.de_ficha({"kcal_100g": 100.0}, malos)


def test_se_anota_en_el_diario_con_fuente_de_ficha(tmp_path):
    """Y `apunta` recibe lo calculado, marcado como venido de la ficha, no tecleado."""
    con = diario.conecta(tmp_path / "diario.db")
    entrada = diario.apunta_de_ficha(con, "david", "2026-10-10", "comida",
                                     producto={"kcal_100g": 485.0, "proteinas_100g": 6.0},
                                     gramos=150, referencia="dia:12345")
    filas = con.execute("SELECT kcal, proteinas_g, fuente_dato, cantidad_g, referencia FROM entrada WHERE id = ?",
                        (entrada,)).fetchall()
    kcal, proteinas, fuente, cantidad, referencia = filas[0]
    assert kcal == pytest.approx(727.5)
    assert proteinas == pytest.approx(9.0)
    assert fuente == "ficha"
    assert cantidad == pytest.approx(150)
    assert referencia == "dia:12345"
