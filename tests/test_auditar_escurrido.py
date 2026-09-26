"""La auditoria del peso escurrido: que su cuenta sea la del caso real que la disparo.

Los numeros de este fichero son los de la ventresca de atun claro del 26 de septiembre de 2026,
que es el caso que enseno el problema: Mercadona declara 111 g, dice que el escurrido son 78 g
y las otras cadenas venden la misma lata declarando 73 g.
"""
import pytest

from projects.cesta.auditar_escurrido import precio_por_kilo

VENTRESCA_CENT = 330.0        # 3,30 EUR
NETO_KG = 0.111
ESCURRIDO_G = 78.0
MEDIANA_OTRAS_CENT = 4233.0   # la mediana de Alcampo, Carrefour y DIA por kilo


def test_el_escurrido_cambia_el_precio_por_kilo_de_la_ventresca():
    """Dividiendo por lo declarado son 2.973 c/kg; por el escurrido, 4.230,8."""
    con_declarado, con_escurrido = precio_por_kilo(VENTRESCA_CENT, NETO_KG, ESCURRIDO_G)
    assert con_declarado == pytest.approx(2972.973, rel=1e-6)
    assert con_escurrido == pytest.approx(4230.769, rel=1e-6)


def test_con_el_escurrido_la_ventresca_cae_donde_estan_las_demas():
    """Antes se quedaba en el 70 % de la mediana de las otras; ahora, al 99,9 %."""
    con_declarado, con_escurrido = precio_por_kilo(VENTRESCA_CENT, NETO_KG, ESCURRIDO_G)
    assert con_declarado / MEDIANA_OTRAS_CENT == pytest.approx(0.702, abs=0.002)
    assert con_escurrido / MEDIANA_OTRAS_CENT == pytest.approx(0.999, abs=0.002)


def test_sin_escurrido_no_hay_dos_precios_distintos():
    """Si la cadena no publica escurrido, la regla nueva y la vieja son la misma cuenta."""
    con_declarado, con_escurrido = precio_por_kilo(1725.0, 5.0, None)
    assert con_declarado == con_escurrido == 345.0


def test_un_escurrido_absurdo_no_toca_el_precio():
    """Mas grande que lo declarado no es informacion: se ignora, no se usa para dividir."""
    con_declarado, con_escurrido = precio_por_kilo(1725.0, 5.0, 9000.0)
    assert con_declarado == con_escurrido == 345.0
