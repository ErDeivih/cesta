"""Un aviso no autoriza una sustitucion: el total suma solo lo que puede contar.

Es el caso B de las pruebas de aceptacion: producto exacto con una alternativa mas barata **no
autorizada**. Hoy esa alternativa se avisa y se suma; tiene que avisarse, ofrecerse aparte y **no**
sumarse.
"""
from __future__ import annotations

from core import identidad
from plataforma.api import cesta

ANA = {"id": "ana"}
GTIN_A = "4056489574392"
GTIN_B = "8412345678905"


def peticion(autorizado=False, cantidad=1):
    return cesta.Peticion(grupo_id=1, producto_id=None, cantidad=cantidad,
                          nombre="Leche entera 1 l", id="l1", autorizado=autorizado)


def fila(pid, precio, ean, gtin_canonico, marca=None):
    return (pid, precio, "Leche entera 1 l", None, ean,
            identidad.Producto(fuente="dia", id_fuente="ref", nombre="Leche entera 1 l",
                               gtin=gtin_canonico), marca, 0)


def test_una_alternativa_mas_barata_no_suma_si_nadie_la_autoriza():
    """El caso B: 149 es mas barato que 199, y aun asi el total no puede quedarse con 149."""
    mejor = {(1, "dia"): fila("p2", 149, GTIN_B, GTIN_A)}
    eleccion = cesta._resolver(peticion(), "dia", mejor)
    assert eleccion.identidad == identidad.ALTERNATIVA
    assert eleccion.coste_cent == 149, "el precio se sigue calculando: es lo que se ofrece"
    assert eleccion.autorizada is False, "pero no cuenta para el total"
    total = cesta._total_autorizado([eleccion])
    assert total["total_cent"] == 0 and total["completo"] is False
    assert total["pendientes"][0]["linea_id"] == "l1"
    assert "GTIN distinto" in total["pendientes"][0]["motivo"]


def test_la_misma_alternativa_si_suma_cuando_se_autoriza():
    mejor = {(1, "dia"): fila("p2", 149, GTIN_B, GTIN_A)}
    eleccion = cesta._resolver(peticion(autorizado=True), "dia", mejor)
    assert eleccion.autorizada is True
    total = cesta._total_autorizado([eleccion])
    assert total["total_cent"] == 149 and total["completo"] is True


def test_lo_exacto_suma_siempre():
    mejor = {(1, "dia"): fila("p1", 199, GTIN_A, GTIN_A)}
    eleccion = cesta._resolver(peticion(), "dia", mejor)
    assert eleccion.autorizada is True
    assert cesta._total_autorizado([eleccion])["total_cent"] == 199


def test_el_total_dice_lo_que_falta_y_no_solo_cuanto_suma():
    """Un total que esconde lo que no pudo contar miente; uno que lo dice se puede explicar."""
    exacta = cesta._resolver(peticion(), "dia", {(1, "dia"): fila("p1", 199, GTIN_A, GTIN_A)})
    alternativa = cesta._resolver(peticion(), "aldi", {(1, "aldi"): fila("p3", 149, GTIN_B, GTIN_A)})
    total = cesta._total_autorizado([exacta, alternativa])
    assert total["total_cent"] == 199, "solo cuenta la exacta"
    assert total["lineas_contadas"] == 1 and total["completo"] is False
    assert len(total["pendientes"]) == 1 and total["pendientes"][0]["fuente"] == "aldi"


def test_la_cuarentena_tampoco_suma_sin_autorizacion():
    """Mismo GTIN con presentacion incompatible: se ofrece, se explica y no cuenta."""
    mejor = {(1, "dia"): fila("p4", 599, GTIN_A, GTIN_A)}
    mejor[(1, "dia")] = (mejor[(1, "dia")][0], 599, "Leche entera 1 l pack 6", None, GTIN_A,
                         identidad.Producto(fuente="dia", id_fuente="ref",
                                            nombre="Leche entera 1 l", gtin=GTIN_A), None, 0)
    eleccion = cesta._resolver(peticion(), "dia", mejor)
    assert eleccion.identidad == identidad.CUARENTENA
    assert eleccion.autorizada is False
    assert cesta._total_autorizado([eleccion])["total_cent"] == 0
