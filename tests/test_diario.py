"""El diario: subtotales conocidos separados de nutricion completa, y compras que no son consumo.

Lo que se fija: que una entrada sin dato **no** aporte cero, que el dia sepa decir cuantas entradas le
faltan, que una receta se anote con su version, y que una compra **no se pueda** registrar como consumo.
"""
from __future__ import annotations

import pytest

from core import diario


@pytest.fixture
def con(tmp_path):
    return diario.conecta(tmp_path / "diario.sqlite")


def test_una_entrada_con_etiqueta_se_suma_al_conocido(con):
    diario.apunta(con, "2026-10-07", "desayuno", referencia="dia:1", kcal=250, proteinas_g=8,
                  fuente_dato=diario.ETIQUETA)
    resumen = diario.dia(con, "2026-10-07")
    assert resumen["conocido"]["kcal"] == 250
    assert resumen["conocido"]["proteinas_g"] == 8
    assert resumen["sin_dato"] == []
    assert resumen["completo"] is True


def test_una_entrada_sin_dato_no_aporta_cero(con):
    """Ausencia no es cero: es que no se sabe, y el dia lo dice."""
    diario.apunta(con, "2026-10-07", "comida", referencia="dia:1", kcal=600,
                  fuente_dato=diario.ETIQUETA)
    diario.apunta(con, "2026-10-07", "cena", referencia="receta:3", version="2",
                  tipo=diario.RECETA, fuente_dato=diario.DESCONOCIDO)
    resumen = diario.dia(con, "2026-10-07")
    assert resumen["conocido"]["kcal"] == 600, "lo desconocido no suma cero"
    assert resumen["conocido"]["entradas"] == 1
    assert len(resumen["sin_dato"]) == 1, "y el dia sabe cuantas le faltan"
    assert resumen["completo"] is False


def test_un_dia_sin_nada_no_esta_completo_ni_tiene_total(con):
    resumen = diario.dia(con, "2026-10-07")
    assert resumen["entradas"] == [] and resumen["completo"] is False
    assert resumen["conocido"]["kcal"] is None, "sin entradas no hay cero: no hay nada"


def test_las_compras_no_se_registran_como_consumo(con):
    """La regla del encargo, en el codigo y no en un comentario."""
    with pytest.raises(ValueError) as fallo:
        diario.apunta(con, "2026-10-07", "comida", tipo="compra", kcal=1000)
    assert "no es consumo" in str(fallo.value)
    assert diario.dia(con, "2026-10-07")["entradas"] == []


def test_otras_reglas_que_no_se_pueden_romper(con):
    with pytest.raises(ValueError):
        diario.apunta(con, "2026-10-07", "siesta")                    # comida que no existe
    with pytest.raises(ValueError):
        diario.apunta(con, "el martes", "comida")                     # fecha que no es fecha
    with pytest.raises(ValueError):
        diario.apunta(con, "2026-10-07", "comida", kcal=-5)           # energia negativa
    with pytest.raises(ValueError):
        diario.apunta(con, "2026-10-07", "comida", fuente_dato="creo")  # fuente que no existe
    with pytest.raises(ValueError):
        diario.apunta(con, "2026-10-07", "comida", tipo=diario.RECETA)  # receta sin version


def test_una_receta_se_anota_con_su_version_y_se_puede_releer(con):
    """Sin la version, releer el diario de la semana pasada no seria posible."""
    diario.apunta(con, "2026-10-05", "cena", tipo=diario.RECETA, referencia="7", version="1",
                  kcal=480, fuente_dato=diario.FICHA)
    entrada = diario.dia(con, "2026-10-05")["entradas"][0]
    assert entrada["tipo"] == diario.RECETA
    assert entrada["version"] == "1" and entrada["referencia"] == "7"


def test_las_entradas_se_agrupan_por_comida_y_en_orden(con):
    diario.apunta(con, "2026-10-07", "cena", kcal=500, fuente_dato=diario.ESTIMADO)
    diario.apunta(con, "2026-10-07", "desayuno", kcal=200, fuente_dato=diario.ESTIMADO)
    resumen = diario.dia(con, "2026-10-07")
    assert list(resumen["comidas"]) == ["desayuno", "cena"], "solo las comidas con algo, en su orden"
    assert resumen["conocido"]["kcal"] == 700


def test_anotar_de_mas_se_puede_deshacer(con):
    entrada = diario.apunta(con, "2026-10-07", "comida", kcal=300, fuente_dato=diario.ESTIMADO)
    assert diario.borrar(con, entrada) is True
    assert diario.dia(con, "2026-10-07")["entradas"] == []
    assert diario.borrar(con, entrada) is False, "borrar dos veces no es un error, es que ya no esta"


def test_los_macronutrientes_se_suman_solo_si_alguno_los_trae(con):
    """Un dia con energia pero sin proteinas no puede inventarse un cero de proteinas."""
    diario.apunta(con, "2026-10-07", "comida", kcal=600, fuente_dato=diario.ETIQUETA)
    resumen = diario.dia(con, "2026-10-07")
    assert resumen["conocido"]["kcal"] == 600
    assert resumen["conocido"]["proteinas_g"] is None
    diario.apunta(con, "2026-10-07", "cena", kcal=400, proteinas_g=20, fuente_dato=diario.ETIQUETA)
    assert diario.dia(con, "2026-10-07")["conocido"]["proteinas_g"] == 20


def test_el_rango_dice_que_dias_estan_completos(con):
    diario.apunta(con, "2026-10-01", "comida", kcal=500, fuente_dato=diario.ETIQUETA)
    diario.apunta(con, "2026-10-02", "comida", kcal=500, fuente_dato=diario.ETIQUETA)
    diario.apunta(con, "2026-10-02", "cena", fuente_dato=diario.DESCONOCIDO)
    dias = {d["fecha"]: d for d in diario.rango(con, "2026-10-01", "2026-10-07")}
    assert dias["2026-10-01"]["completo"] is True
    assert dias["2026-10-02"]["completo"] is False
    assert dias["2026-10-02"]["kcal_conocida"] == 500


def test_macronutrientes_sin_calorias_conservan_su_cobertura(con):
    diario.apunta(con, "2026-10-08", "comida", proteinas_g=12, grasas_g=0)
    diario.apunta(con, "2026-10-08", "cena", kcal=300, proteinas_g=8)
    resumen = diario.dia(con, "2026-10-08")
    assert resumen["conocido"]["proteinas_g"] == 20
    assert resumen["conocido"]["grasas_g"] == 0
    assert resumen["conocido"]["hidratos_g"] is None
    assert resumen["cobertura"]["proteinas_g"] == {
        "con_dato": 2, "total": 2, "completa": True}
    assert resumen["cobertura"]["kcal"]["completa"] is False
    assert resumen["cobertura"]["grasas_g"]["con_dato"] == 1


def test_rango_sin_energia_no_inventa_cero(con):
    diario.apunta(con, "2026-10-08", "comida")
    assert diario.rango(con, "2026-10-08", "2026-10-08")[0]["kcal_conocida"] is None


@pytest.mark.parametrize("campo", ["kcal", "cantidad_g", "proteinas_g", "grasas_g", "hidratos_g"])
@pytest.mark.parametrize("valor", [float("nan"), float("inf"), float("-inf")])
def test_no_se_guardan_numeros_no_finitos(con, campo, valor):
    with pytest.raises(ValueError, match="finitas"):
        diario.apunta(con, "2026-10-08", "comida", **{campo: valor})
    assert diario.dia(con, "2026-10-08")["entradas"] == []
