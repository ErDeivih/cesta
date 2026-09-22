"""Los certificados que Aldi cuelga de cada producto.

Durante once dias `assets` se leia solo para sacar la foto y se tiraba el resto.
Uno de los tipos que se tiraba, `certificate`, aparece en 1.106 de los 2.065
productos de Aldi y trae 32 logotipos distintos con nombre estable. De ahi salen
sellos de dieta, el pais de origen (que Aldi no publica en ningun campo de
texto), la marca propia y las certificaciones de tercero.
"""
from core.certificados import _CATALOGO, _clave, lee, sin_traducir


def test_un_sello_de_dieta():
    assert lee(["https://s7g10.scene7.com/is/image/aldinord/07_Sin_gluten"]) == {
        "sellos": "sin-gluten", "certificados": "feacab"}


def test_el_origen_sale_de_un_logotipo():
    # El 5 de septiembre se midio que el origen tenia un techo del 3,7 % del
    # catalogo y se dio por imposible el filtro "producto espanol". Aldi lo
    # publica, pero en una imagen.
    r = lee(["https://x/01_A_Origen_nacional"])
    assert r["origen"] == "España"


def test_el_logotipo_de_la_casa_es_marca_propia():
    assert lee(["https://x/12_ALDI_Nord_Logo_2021"]) == {"es_marca_propia": True}


def test_varios_certificados_salen_ordenados_y_sin_repetir():
    r = lee(["https://x/51_A_Rainforest_Alliance_Cacao_2021",
             "https://x/51_A_Rainforest_Alliance_Cafe_2021",
             "https://x/52_Fairtrade_Cocoa"])
    assert r["certificados"] == "comercio-justo,rainforest-alliance"


def test_una_certificacion_que_no_es_de_comida_no_pone_sello_ecologico():
    # Natrue certifica cosmetica natural y Oeko-Tex tejidos. Si pusieran el sello
    # "ecologico", el filtro devolveria camisetas de algodon organico entre los
    # alimentos: el error que la OCU le reprocha a la competencia.
    for logo in ("63_Natrue", "Standard_Oekotex", "OrganicCotton_Oekotex", "62_PEFC"):
        assert "sellos" not in lee([f"https://x/{logo}"]), logo


def test_la_version_y_el_tamano_del_logotipo_no_crean_certificados_nuevos():
    # "MSC_0626" y "42_ASC_16_mm_de_alto" son el mismo sello con el ano y los
    # milimetros pegados al nombre del fichero.
    assert lee(["https://x/MSC_0626"])["certificados"] == "msc"
    assert lee(["https://x/42_ASC_16_mm_de_alto"])["certificados"] == "asc"


def test_las_claves_del_catalogo_sobreviven_a_la_limpieza():
    # Si alguien anade una clave copiandola de la URL, con su "_Color" o su ano,
    # no casara nunca y no se notaria hasta contar los productos.
    assert [k for k in _CATALOGO if _clave(k) != k] == []


def test_lo_que_no_sabemos_leer_se_cuenta_en_vez_de_inventarse():
    # Cuatro logotipos de Aldi llevan el nombre por defecto de Illustrator
    # ("Mesa de trabajo 1"). No se adivinan: se cuentan para la auditoria.
    assert lee(["https://x/Mesa de trabajo 1"]) == {}
    assert sin_traducir(["https://x/Mesa de trabajo 1"]) == ["mesa de trabajo 1"]
    assert sin_traducir(["https://x/07_Sin_gluten"]) == []


def test_sin_logotipos_no_pasa_nada():
    assert lee([]) == {}
    assert lee(None) == {}
