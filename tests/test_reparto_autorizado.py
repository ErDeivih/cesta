"""El reparto no puede sumar lo que no esta autorizado, ni dejar ganar a un reparto que no autoriza nada.

`_mejor_reparto` recibe sus estructuras y no toca la base, asi que se prueba con dos cadenas armadas a
mano y se comprueba **la decision**: que la linea sin autorizar no suma y que un reparto exacto gana a
uno que resuelve mas barato pero sin autorizacion.
"""
from __future__ import annotations

from plataforma.api import cesta


def eleccion(pid, fuente, coste, autorizada=True, identidad=None):
    return cesta.Eleccion(pid, f"Producto {pid}", fuente, 1, coste, coste, None, None,
                          linea_id="l1", identidad=identidad,
                          motivo=None if autorizada else "GTIN distinto",
                          autorizada=autorizada)


def peticion(nombre="Leche"):
    return cesta.Peticion(grupo_id=1, producto_id=None, cantidad=1, nombre=nombre, id="l1")


def test_lo_no_autorizado_no_suma_en_el_reparto():
    """La exacta de dia cuesta 199; la alternativa de aldi, 149. El reparto no puede quedarse con 149."""
    peticiones = [peticion()]
    por_cadena = {
        "dia": [eleccion("p1", "dia", 199)],
        "aldi": [eleccion("p2", "aldi", 149, autorizada=False, identidad="alternativa")],
    }
    una_tienda = [{"cadena": "dia", "faltan": [], "sin_autorizar": 0, "total_cent": 199},
                  {"cadena": "aldi", "faltan": [], "sin_autorizar": 1, "total_cent": 0}]
    reparto = cesta._mejor_reparto(peticiones, por_cadena, 2, una_tienda)
    # Con dos cadenas y una linea, no hay reparto posible: cada combinacion usa una sola tienda.
    assert reparto is None, "una linea no se reparte entre dos tiendas"


def test_un_reparto_exacto_gana_a_uno_mas_barato_sin_autorizar():
    """Dos lineas: el reparto barato resuelve una con alternativa; el exacto cuesta mas y es el bueno."""
    peticiones = [peticion("Leche"), peticion("Pan")]
    por_cadena = {
        "dia": [eleccion("p1", "dia", 199), None],
        "aldi": [None, eleccion("p2", "aldi", 50)],
        "carrefour": [eleccion("p3", "carrefour", 199, autorizada=False, identidad="alternativa"),
                      eleccion("p4", "carrefour", 60)],
    }
    una_tienda = [
        {"cadena": "carrefour", "faltan": [], "sin_autorizar": 1, "total_cent": 60},
        {"cadena": "dia", "faltan": ["Pan"], "sin_autorizar": 0, "total_cent": 199},
    ]
    reparto = cesta._mejor_reparto(peticiones, por_cadena, 3, una_tienda)
    assert reparto is not None
    # El reparto elegido usa dia y aldi, los dos exactos, y no la alternativa de carrefour.
    assert reparto["cadenas"] == ["aldi", "dia"]
    assert reparto["total_cent"] == 249
    assert reparto["sin_autorizar"] == []


def test_el_reparto_dice_lo_que_no_pudo_contar():
    """Tres lineas: dos exactas en dos tiendas -- que es lo que hace que haya reparto -- y una tercera
    que solo tiene alternativa, que es la que no suma y aparece en `sin_autorizar`."""
    peticiones = [peticion("Leche"), peticion("Pan"), peticion("Vino")]
    por_cadena = {
        "dia": [eleccion("p1", "dia", 199), None, None],
        "aldi": [None, eleccion("p2", "aldi", 50), None],
        "carrefour": [None, None, eleccion("p3", "carrefour", 70, autorizada=False,
                                           identidad="alternativa")],
    }
    una_tienda = [
        {"cadena": "carrefour", "faltan": ["Leche", "Pan"], "sin_autorizar": 1, "total_cent": 0},
        {"cadena": "dia", "faltan": ["Pan", "Vino"], "sin_autorizar": 0, "total_cent": 199},
    ]
    reparto = cesta._mejor_reparto(peticiones, por_cadena, 3, una_tienda)
    assert reparto is not None
    assert reparto["total_cent"] == 249, "el vino no suma: solo esta como alternativa"
    assert len(reparto["sin_autorizar"]) == 1
    assert reparto["sin_autorizar"][0]["cadena"] == "carrefour"
    assert reparto["sin_autorizar"][0]["motivo"] == "GTIN distinto"
