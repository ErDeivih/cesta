"""La respuesta ofrece la alternativa, y no la inventa: lee la que ya se eligio.

Es la mitad que faltaba del caso B: decir que una linea no cuenta esta bien, pero sin ofrecer nada deja a
quien compra sin salida. La alternativa llega con su nombre, su coste y su motivo.
"""
from __future__ import annotations

from core import identidad
from plataforma.api import cesta

GTIN_A = "4056489574392"
GTIN_B = "8412345678905"


def peticion(autorizado=False):
    return cesta.Peticion(grupo_id=1, producto_id=None, cantidad=1,
                          nombre="Leche entera 1 l", id="l1", autorizado=autorizado)


def fila(pid, precio, nombre, ean, gtin_canonico):
    return (pid, precio, nombre, None, ean,
            identidad.Producto(fuente="dia", id_fuente="ref", nombre="Leche entera 1 l",
                               gtin=gtin_canonico), None, precio, ean == gtin_canonico)


def test_la_alternativa_llega_con_su_nombre_su_coste_y_su_motivo():
    """La exacta de 209 se elige para el total; la de 199 se ofrece."""
    mejor = {(1, "dia"): fila("p1", 209, "Leche entera 1 l", GTIN_A, GTIN_A)}
    mejor[(1, "dia", "alternativa")] = (("p2", 199, "Leche entera 1 l de otra marca", None, GTIN_B,
                                         None, None, 199, False))
    eleccion = cesta._resolver(peticion(), "dia", mejor)
    assert eleccion.identidad == identidad.EXACTO
    assert eleccion.autorizada is True
    assert eleccion.alternativa is not None, "sin alternativa no hay nada que ofrecer"
    assert eleccion.alternativa["coste_cent"] == 199
    assert eleccion.alternativa["nombre"] == "Leche entera 1 l de otra marca"


def test_sin_alternativa_guardada_el_campo_es_none_y_no_se_inventa():
    mejor = {(1, "dia"): fila("p1", 199, "Leche entera 1 l", GTIN_A, GTIN_A)}
    eleccion = cesta._resolver(peticion(), "dia", mejor)
    assert eleccion.alternativa is None


def test_una_linea_que_no_cuenta_ofrece_su_alternativa_y_avisa():
    """El caso util: no es el producto pedido, no suma, y se ofrece en su lugar."""
    mejor = {(1, "dia"): fila("p2", 149, "Leche entera 1 l", GTIN_B, GTIN_A)}
    mejor[(1, "dia", "alternativa")] = (("p3", 139, "Leche entera 1 l mas barata", None, GTIN_B,
                                         None, None, 139, False))
    eleccion = cesta._resolver(peticion(), "dia", mejor)
    assert eleccion.autorizada is False
    assert eleccion.identidad == identidad.ALTERNATIVA
    assert eleccion.alternativa["coste_cent"] == 139
