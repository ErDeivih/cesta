"""Calcular raciones: la regla de tres, y lo que NO se puede inventar.

Se prueba la funcion pura con numeros y, ademas, por el endpoint real, porque la escala tiene que llegar
por la respuesta y no quedarse dentro.
"""
from __future__ import annotations

import pytest

from core import recetas


def test_escalar_una_receta_es_una_regla_de_tres():
    tortilla = [{"texto": "patatas", "cantidad": 600, "unidad": "g"},
                {"texto": "huevos", "cantidad": 4, "unidad": "ud"}]
    para_seis = recetas.escala(tortilla, 4, 6)
    assert para_seis[0]["cantidad"] == 900
    assert para_seis[1]["cantidad"] == 6


def test_escalar_hacia_abajo_tambien():
    para_dos = recetas.escala([{"texto": "arroz", "cantidad": 400, "unidad": "g"}], 4, 2)
    assert para_dos[0]["cantidad"] == 200


def test_lo_que_no_tiene_cantidad_no_la_gana():
    """La sal sin cantidad sigue sin cantidad: no se puede aplicar la regla de tres a lo que no se sabe."""
    con_sal = recetas.escala([{"texto": "sal"}, {"texto": "harina", "cantidad": 250, "unidad": "g"}], 2, 4)
    assert "cantidad" not in con_sal[0] or con_sal[0]["cantidad"] is None
    assert con_sal[1]["cantidad"] == 500


def test_media_unidad_es_la_verdad_y_no_se_redondea_a_dos():
    """De 4 a 6, un huevo es 1,5. Redondear a 2 seria comodo y mentira."""
    assert recetas.escala([{"texto": "huevos", "cantidad": 1, "unidad": "ud"}], 4, 6)[0]["cantidad"] == 1.5


def test_no_se_escala_con_raciones_imposibles():
    with pytest.raises(ValueError):
        recetas.escala([{"texto": "pan"}], 0, 2)
    with pytest.raises(ValueError):
        recetas.escala([{"texto": "pan"}], 2, 0)


def test_la_receta_dice_las_dos_cifras_y_si_esta_escalada(tmp_path):
    """Ensenar solo las raciones pedidas obligaria a adivinar de donde sale la cantidad."""
    con = recetas.conecta(tmp_path / "recetas.sqlite")
    rid = recetas.crear(con, "ana", "Tortilla", raciones=4,
                        ingredientes=[{"texto": "patatas", "cantidad": 600, "unidad": "g"}])
    pedida = recetas.leer(con, "ana", rid, raciones=6)
    assert pedida["raciones"] == 6 and pedida["raciones_receta"] == 4
    assert pedida["escalada"] is True
    assert pedida["ingredientes"][0]["cantidad"] == 900
    # Y sin pedir nada, la receta tal cual.
    normal = recetas.leer(con, "ana", rid)
    assert normal["raciones"] == 4 and normal["escalada"] is False
    assert normal["ingredientes"][0]["cantidad"] == 600
    con.close()
