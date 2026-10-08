"""Lo que el servidor decide tiene que salir en la respuesta, o no existe para la pantalla.

`_serializa` es pura: recibe una eleccion y devuelve el diccionario que viaja al navegador. Durante varias
rondas el veredicto de identidad, la autorizacion y la alternativa se quedaron dentro del servidor porque
la respuesta no los llevaba, y el frontend no tenia forma de saber nada de ellos.

Esta prueba existe porque el cambio que los anadio viajo **sin ella** -- se dijo en su propio mensaje de
commit -- y una regla que no se comprueba es una regla que se puede perder en el siguiente cambio.
"""
from __future__ import annotations

from plataforma.api import cesta


def eleccion(**extra):
    """Una eleccion completa: los ocho primeros campos son obligatorios, el resto tienen valor."""
    datos = {"producto_id": "p1", "nombre": "Leche entera 1 l", "fuente": "dia", "unidades": 1,
             "coste_cent": 209, "coste_sin_oferta_cent": 209, "promo_txt": None,
             "sugerencia": None, "linea_id": "l1"}
    datos.update(extra)
    return cesta.Eleccion(**datos)


def test_la_respuesta_lleva_el_veredicto_la_autorizacion_y_la_alternativa():
    serializada = cesta._serializa(eleccion(
        identidad="alternativa", motivo="GTIN distinto", autorizada=False,
        alternativa={"producto_id": "p2", "nombre": "Otra leche", "coste_cent": 199,
                     "fuente": "dia"}))
    assert serializada["identidad"] == "alternativa"
    assert serializada["motivo"] == "GTIN distinto"
    assert serializada["autorizada"] is False
    # La alternativa viaja entera: sin el coste no se puede enseñar el precio, y sin el nombre no se
    # puede decir que se puede pedir.
    assert serializada["alternativa"]["coste_cent"] == 199
    assert serializada["alternativa"]["nombre"] == "Otra leche"


def test_ninguno_de_los_campos_de_siempre_se_ha_perdido():
    """Anadir campos a una respuesta es facil; quitarlos sin querer, tambien. Esto lo vigila."""
    serializada = cesta._serializa(eleccion())
    for campo in ("producto_id", "nombre", "cadena", "unidades", "coste_cent",
                  "coste_sin_oferta_cent", "promo", "sugerencia", "linea_id"):
        assert campo in serializada, f"se perdio {campo} al anadir los campos nuevos"


def test_una_linea_exacta_viaja_autorizada_y_sin_nada_que_ofrecer():
    """El caso normal no puede quedar raro por el cambio: exacta, cuenta, y nada que ofrecer."""
    serializada = cesta._serializa(eleccion(identidad="exacto", motivo="mismo GTIN valido"))
    assert serializada["autorizada"] is True
    assert serializada["alternativa"] is None


def test_una_linea_sin_veredicto_tambien_viaja_y_cuenta():
    """Sin nada que afirmar se cuenta, y el motivo va vacio en vez de inventado."""
    serializada = cesta._serializa(eleccion())
    assert serializada["identidad"] is None
    assert serializada["motivo"] is None
    assert serializada["autorizada"] is True
