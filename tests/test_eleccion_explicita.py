"""Una linea resuelta con otro producto lo dice: no hay sustitucion silenciosa.

Se prueba `_resolver`, que es donde se cruzan la referencia del grupo y el producto propuesto, con el
diccionario que produce `_candidatos` **con su forma exacta**: identificador, precio, nombre, oferta,
GTIN de la fila elegida y ficha canonica del grupo. Los GTIN son validos de verdad, con su digito de
control, porque el motor los valida: si fueran inventados, la prueba mediria otra cosa.
"""
from __future__ import annotations

from core import identidad
from plataforma.api import cesta

GTIN_A = "4056489574392"   # valido
GTIN_B = "8412345678905"   # valido y distinto


def peticion(cantidad=1):
    return cesta.Peticion(grupo_id=1, producto_id=None, cantidad=cantidad,
                          nombre="Leche entera 1 l", id="l1")


def fila(pid, precio, nombre, ean, gtin_canonico, nombre_canonico=None):
    return (pid, precio, nombre, None, ean, identidad.Producto(
        fuente="dia", id_fuente="ref", nombre=nombre_canonico or nombre, gtin=gtin_canonico))


def test_mismo_gtin_y_misma_presentacion_es_exacto():
    mejor = {(1, "dia"): fila("p1", 199, "Leche entera 1 l", GTIN_A, GTIN_A)}
    eleccion = cesta._resolver(peticion(), "dia", mejor)
    assert eleccion.identidad == identidad.EXACTO
    assert eleccion.coste_cent == 199 and eleccion.linea_id == "l1"


def test_gtin_distinto_es_alternativa_con_su_motivo():
    """El caso que el encargo prohibe esconder: otro producto, y encima mas barato."""
    mejor = {(1, "dia"): fila("p2", 149, "Leche entera 1 l", GTIN_B, GTIN_A)}
    eleccion = cesta._resolver(peticion(), "dia", mejor)
    assert eleccion.identidad == identidad.ALTERNATIVA
    assert "GTIN distinto" in eleccion.motivo
    assert eleccion.coste_cent == 149, "el precio se calcula igual: lo que cambia es que se avisa"


def test_mismo_gtin_con_pack_distinto_va_a_cuarentena():
    """Mismo codigo y presentacion incompatible: una de las dos fichas miente."""
    mejor = {(1, "dia"): fila("p3", 599, "Leche entera 1 l pack 6", GTIN_A, GTIN_A,
                      "Leche entera 1 l")}
    eleccion = cesta._resolver(peticion(), "dia", mejor)
    assert eleccion.identidad == identidad.CUARENTENA
    assert "presentacion incompatible" in eleccion.motivo


def test_sin_el_gtin_de_la_fila_es_probable_y_lo_dice():
    mejor = {(1, "dia"): fila("p4", 199, "Leche entera 1 l", None, GTIN_A)}
    eleccion = cesta._resolver(peticion(), "dia", mejor)
    assert eleccion.identidad == identidad.PROBABLE
    assert "GTIN" in eleccion.motivo


def test_sin_referencia_no_se_afirma_nada():
    """Si el grupo no trae canonico, no se inventa un veredicto: queda sin afirmar."""
    mejor = {(1, "dia"): ("p5", 199, "Leche entera 1 l", None, None, None)}
    eleccion = cesta._resolver(peticion(), "dia", mejor)
    assert eleccion.identidad is None and eleccion.motivo is None


def test_la_cantidad_sigue_mandando_en_el_coste():
    """El veredicto es informacion añadida: no toca el precio ni la mecanica de la oferta."""
    mejor = {(1, "dia"): fila("p6", 200, "Leche entera 1 l", GTIN_A, GTIN_A)}
    eleccion = cesta._resolver(peticion(cantidad=3), "dia", mejor)
    assert eleccion.unidades == 3 and eleccion.coste_cent == 600
    assert eleccion.coste_sin_oferta_cent == 600
