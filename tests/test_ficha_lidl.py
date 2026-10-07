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
