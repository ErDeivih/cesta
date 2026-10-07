"""El medidor de nutricion: que cuente lo que dice contar, y que no llame tabla a una palabra.

Es la deuda que quedo dicha en la ronda anterior. Los umbrales -- tres campos para una tabla, dos
señales para ingredientes -- son lo que separa una medida de un titular, asi que se prueban.
"""
from __future__ import annotations

from projects.cesta import mide_nutricion as m


def test_una_tabla_de_verdad_se_cuenta_como_tabla():
    html = ("<p>Valor energetico 450 kcal</p><p>Grasas 12 g</p><p>Proteinas 6 g</p>"
            "<p>por 100 g</p><p>Ingredientes: harina, azucar, cacao</p>")
    datos = m.mide(html)
    assert datos["nutrientes"] >= 3 and datos["bases"] >= 1 and datos["ingredientes"] >= 2
    cobertura = m.cuenta_cobertura([datos])
    assert cobertura["con_tabla"] == 1 and cobertura["con_ingredientes"] == 1


def test_una_palabra_suelta_no_es_una_tabla():
    """`porcion` o `racion` aparecen en cualquier interfaz: no bastan para decir que hay tabla."""
    datos = m.mide("<p>Elige una racion y una porcion</p><p>Energia</p>")
    assert datos["nutrientes"] == 1, "una palabra no son tres campos"
    assert datos["bases"] == 0, "porcion y racion no son una base interpretable"
    assert m.cuenta_cobertura([datos])["con_tabla"] == 0


def test_una_ficha_vacia_no_inventa_nada():
    datos = m.mide("")
    assert datos == {"nutrientes": 0, "bases": 0, "ingredientes": 0, "ldjson_producto": False}
    cobertura = m.cuenta_cobertura([datos])
    assert cobertura["con_tabla"] == 0 and cobertura["fichas"] == 1


def test_detecta_los_datos_estructurados_de_producto():
    assert m.mide('<script type="application/ld+json">{"@type":"Product"}</script>')[
        "ldjson_producto"] is True
    assert m.mide('<script type="application/ld+json">{"@type":"Organization"}</script>')[
        "ldjson_producto"] is False


def test_la_cobertura_cuenta_fichas_y_no_una_tendencia():
    """Cada cuenta lleva su denominador: es lo que impide leer seis fichas como un catalogo."""
    medidas = [m.mide("<p>Energia, grasas, proteinas, por 100 g, ingredientes: harina, azucar</p>"),
               m.mide(""), m.mide("")]
    cobertura = m.cuenta_cobertura(medidas)
    assert cobertura["fichas"] == 3
    assert cobertura["con_tabla"] == 1
