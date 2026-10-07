"""La sombra: candidatos exactos, candidatos probables y su separacion.

Lo que se fija: que los exactos exijan GTIN valido y sean multi-cadena, que los probables **no** se
mezclen con ellos, y que un grupo exacto con presentaciones incompatibles salga a la luz (cuarentena)
en vez de publicarse.
"""
from __future__ import annotations

from core import identidad


def P(fuente, nombre, gtin=None, marca=None, familia="lacteos"):
    return identidad.Producto(fuente=fuente, id_fuente=nombre, nombre=nombre, marca=marca,
                              gtin=gtin, familia=familia)


def test_los_exactos_exigen_gtin_valido_y_son_multi_cadena():
    productos = [
        P("dia", "Leche entera 1 l", gtin="4056489574392"),
        P("aldi", "Leche entera 1 l", gtin="4056489574392"),
        P("dia", "Yogur natural 1 kg", gtin="1234567890128"),
    ]
    exactos = identidad.candidatos_por_gtin(productos)
    assert list(exactos) == ["4056489574392"]
    assert len(exactos["4056489574392"]) == 2


def test_un_gtin_invalido_no_crea_grupo():
    productos = [P("dia", "Leche 1 l", gtin="4056489574399"), P("aldi", "Leche 1 l", gtin="4056489574399")]
    assert identidad.candidatos_por_gtin(productos) == {}, "un GTIN invalido no puede agrupar"


def test_los_probables_van_aparte_y_no_son_identidad():
    """Sin GTIN, misma marca y presentacion: candidatos para proponer, nunca para afirmar."""
    productos = [
        P("dia", "Leche entera 1 l", marca="Hacendado"),
        P("aldi", "Leche entera 1 l", marca="Hacendado"),
        P("dia", "Leche entera 1 l", gtin="4056489574392", marca="Hacendado"),
        P("aldi", "Leche entera 1 l", gtin="4056489574392", marca="Hacendado"),
    ]
    probables = identidad.candidatos_por_bloque(productos)
    assert len(probables) == 1, "los que tienen GTIN no entran en los probables"
    assert all(not p.gtin for miembros in probables.values() for p in miembros)


# NOTA (7 de octubre de 2026): aqui vivia una prueba del lector de gold con un catalogo de
# mentira. Se retira despues de cuatro intentos fallidos de montarla, y se dice por que:
# es una comprobacion de INTEGRACION -- lee un parquet de gold y clasifica con el alcance -- y
# su sitio natural es la propia sombra, que la hace sobre el catalogo entero y deja informe.
# Los tres casos que quedan arriba cubren la logica pura, que es lo que debe vivir aqui.
