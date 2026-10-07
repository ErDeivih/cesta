"""Identidad exacta: que solo diga exacto cuando puede, y que se abstenga cuando no.

Lo que se fija, y es la regla central del encargo: **elegir un producto concreto no autoriza a
sustituirlo por otro mas barato**. Por eso ninguna prueba acepta un "exacto" sin GTIN valido, y las
fusiones por parecido de texto estan prohibidas por construccion.
"""
from __future__ import annotations

import pytest

from core import identidad as ident


def P(fuente: str, nombre: str, **extra) -> ident.Producto:
    datos = {"marca": None, "gtin": None, "familia": None}
    datos.update(extra)
    return ident.Producto(fuente=fuente, id_fuente=nombre[:12], nombre=nombre, **datos)


# --- El GTIN se valida, no se copia ------------------------------------------------------------

def test_el_gtin_se_valida_con_su_digito_de_control():
    assert ident.normaliza_gtin("4056489574392") == "4056489574392"
    assert ident.normaliza_gtin("4056489574393") is None          # digito de control mal
    assert ident.normaliza_gtin("12345") is None                  # longitud que no es GTIN
    assert ident.normaliza_gtin("04056489574392") == "4056489574392"  # el cero es relleno
    assert ident.normaliza_gtin(None) is None


def test_un_gtin_valido_solo_no_basta_para_identidad():
    """Lo dice el contrato: hay que comprobar ademas que la presentacion cuadra."""
    a = P("dia", "Leche entera 1 l", gtin="4056489574392", marca="Hacendado")
    b = P("aldi", "Leche entera 1 l", gtin="4056489574392", marca="Hacendado")
    grande = P("aldi", "Leche entera 2 l", gtin="4056489574392", marca="Hacendado")
    assert ident.decide(a, b)["estado"] == ident.EXACTO
    veredicto = ident.decide(a, grande)
    assert veredicto["estado"] == ident.CUARENTENA, "mismo GTIN con otra cantidad no es identidad"
    assert "presentacion incompatible" in " ".join(veredicto["motivos"])


def test_gtin_distinto_no_se_fusiona_por_texto():
    """Podran ser alternativas, nunca lo mismo. Y sin GTIN no se afirma identidad."""
    a = P("dia", "Leche entera 1 l", gtin="4056489574392", marca="Hacendado")
    b = P("mercadona", "Leche entera 1 l", gtin="8412345678905", marca="Hacendado")
    veredicto = ident.decide(a, b)
    assert veredicto["estado"] == ident.ALTERNATIVA
    assert "GTIN distinto" in veredicto["motivos"][0]


def test_sin_gtin_compatible_es_probable_y_nunca_exacto():
    a = P("dia", "Leche entera 1 l", marca="Hacendado")
    b = P("aldi", "Leche entera 1 l", marca="Hacendado")
    assert ident.decide(a, b)["estado"] == ident.PROBABLE


def test_el_pack_cambia_el_producto():
    """6x1 l y 1 l se escriben casi igual y no son lo mismo: es el error caro."""
    suelto = P("dia", "Agua mineral 1 l", marca="Bezoya")
    pack = P("dia", "Agua mineral 1 l pack 6", marca="Bezoya")
    assert ident.decide(suelto, pack)["estado"] == ident.ALTERNATIVA


def test_las_unidades_no_comparables_abstienen_en_vez_de_decidir():
    """Gramos contra mililitros no se comparan sin densidad documentada."""
    a = P("dia", "Crema de cacahuete 500 g", marca="Marca")
    b = P("aldi", "Crema de cacahuete 500 ml", marca="Marca")
    veredicto = ident.decide(a, b)
    assert veredicto["estado"] == ident.ABSTIENE
    assert any("no comparable" in m for m in veredicto["motivos"])


def test_marcas_distintas_son_alternativa_no_identidad():
    a = P("dia", "Leche entera 1 l", marca="Hacendado")
    b = P("aldi", "Leche entera 1 l", marca="Milsani")
    assert ident.decide(a, b)["estado"] in (ident.ALTERNATIVA, ident.PROBABLE)
    assert ident.decide(a, b)["estado"] != ident.EXACTO


def test_sin_nada_en_comun_se_abstiene():
    a = P("dia", "Pimientos rojos 500 g")
    b = P("aldi", "Detergente lavadora 30 lavados")
    assert ident.decide(a, b)["estado"] == ident.ABSTIENE


def test_los_atributos_leen_cantidad_unidad_y_envases():
    datos = ident.atributos("Aceite de oliva 1,5 l botella")
    assert datos["cantidad"] == 1500 and datos["unidad"] == "ml"
    assert ident.atributos("Refresco 33 cl")["cantidad"] == 330
    assert ident.atributos("Cerveza pack 24")["envases"] == 24
    assert ident.atributos("Agua 6x1,5 l")["envases"] == 6
    assert ident.atributos("Leche entera")["cantidad"] is None


# --- Sin cierre transitivo: la parte que evita el grupo envenenado ------------------------------

def test_un_grupo_solo_se_amplia_si_es_compatible_con_todos():
    """A parecido a B y B a C no hace que A y C sean lo mismo."""
    a = P("dia", "Leche entera 1 l", gtin="4056489574392")
    b = P("aldi", "Leche entera 1 l", gtin="4056489574392")
    c = P("mercadona", "Leche entera 2 l", gtin="4056489574392")
    grupo = ident.ampliar_grupo([a], b)
    assert len(grupo) == 2
    with pytest.raises(ident.Cuarentena) as fallo:
        ident.ampliar_grupo(grupo, c)
    assert "no es compatible" in str(fallo.value)


def test_ampliar_un_grupo_vacio_empieza_el_grupo():
    a = P("dia", "Leche entera 1 l")
    assert ident.ampliar_grupo([], a) == [a]
