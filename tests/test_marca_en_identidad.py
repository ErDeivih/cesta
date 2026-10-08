"""Mismo codigo con marcas distintas no es el mismo producto; sin codigo, son dos productos.

Es el caso A de las pruebas de aceptacion: un grupo antiguo puede juntar dos marcas incompatibles. Con el
mismo GTIN eso es una de las dos fichas mintiendo -- cuarentena --; sin GTIN son simplemente dos
productos, y como mucho alternativas.
"""
from __future__ import annotations

from core import identidad

GTIN_A = "4056489574392"


def ficha(fuente, nombre, gtin=None, marca=None):
    return identidad.Producto(fuente=fuente, id_fuente=nombre[:12], nombre=nombre,
                              marca=marca, gtin=gtin)


def test_mismo_gtin_con_marcas_distintas_va_a_cuarentena():
    a = ficha("carrefour", "Leche entera 1 l", GTIN_A, "Marca blanca")
    b = ficha("dia", "Leche entera 1 l", GTIN_A, "Otra marca")
    veredicto = identidad.decide(a, b)
    assert veredicto["estado"] == identidad.CUARENTENA
    assert "marcas distintas" in " ".join(veredicto["motivos"])
    assert veredicto["evidencia"]["marcas_incompatibles"] is True


def test_la_misma_marca_con_ruido_no_es_un_conflicto():
    """Hacendado y hacendado con espacios de mas son la misma marca: eso es ruido, no conflicto."""
    a = ficha("dia", "Leche entera 1 l", GTIN_A, "Hacendado")
    b = ficha("aldi", "Leche entera 1 l", GTIN_A, "  hacendado ")
    assert identidad.decide(a, b)["estado"] == identidad.EXACTO


def test_sin_gtin_dos_marcas_son_dos_productos():
    a = ficha("dia", "Leche entera 1 l", None, "Hacendado")
    b = ficha("aldi", "Leche entera 1 l", None, "Milsani")
    assert identidad.decide(a, b)["estado"] == identidad.ALTERNATIVA


def test_si_una_de_las_dos_no_trae_marca_no_se_inventa_un_conflicto():
    a = ficha("dia", "Leche entera 1 l", GTIN_A, None)
    b = ficha("aldi", "Leche entera 1 l", GTIN_A, "Milsani")
    assert identidad.decide(a, b)["estado"] == identidad.EXACTO


def test_la_marca_no_rompe_lo_que_ya_funcionaba():
    a = ficha("dia", "Leche entera 1 l", GTIN_A, "Hacendado")
    b = ficha("aldi", "Leche entera 1 l", GTIN_A, "Hacendado")
    assert identidad.decide(a, b)["estado"] == identidad.EXACTO
    grande = ficha("aldi", "Leche entera 2 l", GTIN_A, "Hacendado")
    assert identidad.decide(a, grande)["estado"] == identidad.CUARENTENA
    otro = ficha("aldi", "Leche entera 1 l", "8412345678905", "Hacendado")
    assert identidad.decide(a, otro)["estado"] == identidad.ALTERNATIVA
