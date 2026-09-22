"""Los sellos: sin gluten, sin lactosa, vegano, ecologico.

El hallazgo que justifica este fichero: creiamos que los sellos solo podian
venir de Open Food Facts, o sea solo para productos con codigo de barras. Es
falso. **Alcampo y Carrefour los publican ellos mismos**, y Alcampo no tiene ni
un EAN. Medido el 17 de septiembre de 2026, las dos cadenas juntas dan 9.398
sellos frente a los 8.055 de OFF, y los de Alcampo llegan a productos donde OFF
nunca podria llegar.
"""
import pytest

from core.sellos import SELLOS, conservacion_de, de_etiquetas, tiene

# --- cada cadena lo escribe a su manera ---------------------------------

@pytest.mark.parametrize("etiqueta,esperado", [
    ("Sin Gluten", "sin-gluten"),          # Alcampo
    ("Sin gluten", "sin-gluten"),          # Carrefour
    ("Sin Lactosa", "sin-lactosa"),
    ("Vegano", "vegano"),
    ("Alternativa Vegetal", "vegano"),     # como lo llama Carrefour
    ("Producto Ecológico", "ecologico"),
    ("Bio", "ecologico"),                  # como lo llama Carrefour
])
def test_cada_cadena_lo_escribe_distinto_y_acaba_igual(etiqueta, esperado):
    assert de_etiquetas([etiqueta]) == esperado


def test_varias_etiquetas_salen_ordenadas_y_sin_repetir():
    # Ordenado a proposito: dos productos con los mismos sellos tienen que
    # tener EXACTAMENTE el mismo texto, o el filtro por LIKE falla.
    assert de_etiquetas(["Vegano", "Sin Gluten", "Bio"]) == "ecologico,sin-gluten,vegano"
    assert de_etiquetas(["Bio", "Producto Ecológico"]) == "ecologico"


def test_las_etiquetas_que_no_son_sellos_se_ignoran():
    # "Producto Alcampo" es marca propia, "Refrigerado" es conservacion,
    # "Peso variable" es otra cosa. Ninguna es un sello.
    assert de_etiquetas(["Producto Alcampo", "Refrigerado", "Peso variable"]) is None


def test_sin_etiquetas_no_hay_sellos():
    assert de_etiquetas([]) is None
    assert de_etiquetas(None) is None
    assert de_etiquetas([""]) is None


def test_no_se_confunde_con_lo_contrario():
    # El fallo que acecha: que "sin gluten" salga de un texto que dice otra cosa.
    assert de_etiquetas(["Contiene gluten"]) is None
    assert de_etiquetas(["Gluten"]) is None


def test_todos_los_sellos_que_produce_estan_declarados():
    # Si alguien anade un patron nuevo y olvida el nombre en SELLOS, el filtro
    # de la app no sabria que existe.
    from core.sellos import _PATRONES, _PATRONES_PROSA
    assert set(_PATRONES) <= set(SELLOS)
    assert set(_PATRONES_PROSA) <= set(SELLOS)


def test_una_palabra_que_contiene_el_sello_no_es_el_sello():
    # El fallo real del 17 de septiembre: la busqueda era por subcadena, asi que
    # "eco" dentro de "Seco" o de "Marruecos" marcaba el producto como ecologico.
    for trampa in ("Seco", "Recambios", "Marruecos", "economico", "Ecopack",
                   "Bebida", "Aceite de palma"):
        assert de_etiquetas([trampa]) is None, trampa
    # Pero como palabra entera si valen, que es como las escriben las cadenas.
    assert de_etiquetas(["Bio"]) == "ecologico"
    assert de_etiquetas(["Eco"]) == "ecologico"
    assert de_etiquetas(["Ecológico"]) == "ecologico"


def test_la_prosa_es_mas_estricta_que_la_etiqueta():
    from core.sellos import de_prosa
    # Un ingrediente ecologico no hace ecologico al producto. Los 57 champus de
    # Aldi "con aloe vera ecologico" no son productos ecologicos.
    assert de_prosa("Con extracto de arroz ecológico") is None
    assert de_prosa("Origen: Marruecos,España") is None
    assert de_prosa("Hasta 12 horas seco") is None
    # Lo que si afirma algo del producto, se lee.
    assert de_prosa("Con 95% de aguacate. Sin azúcares añadidos. Sin gluten.") == \
        "sin-azucar,sin-gluten"
    assert de_prosa("Apto para veganos") == "vegano"


def test_la_conservacion_de_una_frase():
    from core.sellos import conservacion_de_prosa as leer
    assert leer("Conservar a -18 ºC. Una vez descongelado no volver a congelar") == "congelado"
    assert leer("Conservar refrigerado entre 0 y 4 ºC") == "refrigerado"
    assert leer("Conservar en lugar fresco y seco.") == "ambiente"
    # "Una vez abierto, conservar refrigerado" describe un brik de zumo que vive
    # en el armario, no un refrigerado.
    assert leer("Una vez abierto, conservar refrigerado") is None
    assert leer("Mantener en lugar fresco y seco. Una vez abierto, en nevera") == "ambiente"


# --- conservacion --------------------------------------------------------

def test_la_conservacion_sale_de_la_etiqueta():
    assert conservacion_de(["Refrigerado", "Sin Gluten"]) == "refrigerado"
    assert conservacion_de(["Congelado"]) == "congelado"


def test_sin_etiqueta_de_conservacion_no_se_supone():
    # No saber si algo va en la nevera es distinto de saber que va a temperatura
    # ambiente, y la ficha no debe decir lo segundo cuando pasa lo primero.
    assert conservacion_de(["Sin Gluten"]) is None
    assert conservacion_de([]) is None
    assert conservacion_de(None) is None


# --- filtrar -------------------------------------------------------------

def test_filtrar_por_un_sello():
    assert tiene("ecologico,sin-gluten", "sin-gluten")
    assert not tiene("ecologico", "sin-gluten")
    assert not tiene(None, "vegano")


def test_un_sello_no_casa_con_otro_que_lo_contenga():
    # "sin-gluten" no puede salir de buscar dentro de "sin-gluten-anadido".
    assert not tiene("sin-gluten-anadido", "sin-gluten")
