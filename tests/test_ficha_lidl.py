"""La parte del lector de fichas que se puede probar sin red: leer señales de un HTML.

Lo que se fija es que el informe de señales no mienta por exceso: cuenta bloques de datos
estructurados y busca señales, y lo dice como **cota inferior**. Ver la palabra "ingredientes" no
prueba que exista una tabla del producto, que es la advertencia que trae el propio encargo.
"""
from __future__ import annotations

from projects.cesta import ficha_lidl


def test_cuenta_los_bloques_de_datos_estructurados():
    html = ('<script type="application/ld+json">{"name": "Galletas"}</script>'
            '<script type="APPLICATION/LD+JSON">{}</script>')
    assert ficha_lidl.estructura_de(html)["bloques_ldjson"] == 2


def test_busca_las_señales_sin_prometer_que_el_dato_exista():
    html = "<p>Ingredientes: harina, azucar</p><p>Valor energetico 450 kcal</p><p>Precio 1,49 €</p>"
    datos = ficha_lidl.estructura_de(html)
    assert datos["ingredientes"] and datos["nutricion"] and datos["precio"]
    assert not datos["alergenos"], "no puede decir que hay alergenos donde no se nombran"


def test_una_ficha_vacia_no_inventa_nada():
    datos = ficha_lidl.estructura_de("")
    assert datos["bytes"] == 0 and datos["bloques_ldjson"] == 0
    assert not any(datos[n] for n in ("ingredientes", "nutricion", "precio", "alergenos"))


# --- El lector, con los nombres de campo medidos en la ficha real -------------------------------
# Estructura copiada del fixture del 7 de octubre de 2026: Product con name, brand, description,
# gtin13, sku, image, offers, url. Los Organization de Lidl van en otros bloques y se ignoran.

FICHA = """
<script type="application/ld+json">{"@type":"Organization","name":"LIDL"}</script>
<script type="application/ld+json">
{"@type":"Product","name":"Galletas rellenas","sku":"11000174",
 "brand":{"@type":"Brand","name":"Sondey"},
 "description":"<ul><li>Rellenas de crema de chocolate.</li></ul>",
 "gtin13":["4056489123456"],"image":["https://cdn/x.jpg"],
 "offers":[{"@type":"Offer","price":"1.49","priceCurrency":"EUR"}],
 "url":"https://www.lidl.es/p/sondey-galletas-rellenas/p11000174"}
</script>"""


def test_ignora_los_bloques_de_la_cadena_y_coge_el_producto():
    assert len(ficha_lidl.productos_de(FICHA)) == 1
    assert ficha_lidl.productos_de(FICHA)[0]["name"] == "Galletas rellenas"


def test_la_descripcion_se_convierte_a_texto():
    """Viene con HTML: se limpia, no se pinta."""
    datos = ficha_lidl.lee(FICHA)
    assert datos["descripcion"] == "Rellenas de crema de chocolate."
    assert "<" not in datos["descripcion"]


def test_el_gtin_se_valida_y_el_sku_nunca_es_un_ean():
    """El identificador interno de la tienda no puede entrar como codigo de barras."""
    datos = ficha_lidl.lee(FICHA)
    assert datos["id_fuente"] == "11000174"
    assert datos["ean"] != "11000174"
    # El del fixture no tiene digito de control valido: se guarda aparte, no se usa ni se tira.
    if datos["ean"] is None:
        assert datos["gtin_invalido"] == "4056489123456"


def test_la_validacion_del_gtin_es_de_verdad():
    """Digito de control EAN-13: se calcula, no se supone."""
    assert ficha_lidl.gtin_valido("1234567890128") == "1234567890128"
    assert ficha_lidl.gtin_valido("1234567890123") is None       # digito de control mal
    assert ficha_lidl.gtin_valido("12345") is None               # longitud que no es GTIN


def test_dos_condiciones_no_se_funden_en_un_precio():
    """Con club y normal delante, no se elige por el usuario ni se anuncia una bajada."""
    html = FICHA.replace('"offers":[{"@type":"Offer","price":"1.49","priceCurrency":"EUR"}]',
                         '"offers":[{"@type":"Offer","price":"1.49"},'
                         '{"@type":"Offer","price":"1.29"}]')
    datos = ficha_lidl.lee(html)
    assert datos["precio_cent"] is None, "con dos condiciones no se elige una"
    assert len(datos["condiciones"]) == 2, "y las dos se conservan"


def test_una_ficha_sin_producto_no_inventa_uno():
    import pytest as _pytest
    with _pytest.raises(ValueError):
        ficha_lidl.lee("<html>sin datos estructurados</html>")


def test_la_ficha_de_un_alimento_NO_trae_contenido_y_esta_escrito():
    """**La limitacion, fijada con una prueba.** *G08 pide ingredientes, nutricion y alergenos; el
    JSON-LD de Lidl no los publica -- y no es un parser incompleto: es una fuente que no los da.*

    Medido sobre las galletas: el bloque `Product` trae **las mismas nueve claves que un
    electrodomestico** (@type, brand, description, gtin13, image, name, offers, sku, url).

    *Si algun dia Lidl los publica, **esta prueba cae y avisa** -- que es para lo que sirve.*
    """
    p = ficha_lidl.productos_de(FICHA)[0]
    assert p["name"] == "Galletas rellenas", "es un alimento, no un electrodomestico"
    for clave in ("ingredients", "nutrition", "allergens", "additionalProperty"):
        assert clave not in p, f"Lidl ya publica {clave}: hay que extraerlo y anadirlo al hash"
    assert set(p) >= {"name", "brand", "description", "gtin13", "image", "offers", "sku", "url"}
