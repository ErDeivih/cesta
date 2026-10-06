"""La matriz de fichas: que mide, y que no promete.

Es el instrumento que decide en que se trabaja T11, asi que se prueba como el codigo que mide: que
la muestra sea reproducible, que los tres estados no se confundan, y que no afirme como disponible
algo que solo ha visto mencionado.
"""
from __future__ import annotations

import gzip

from projects.cesta import matriz_fichas as matriz


def test_la_muestra_es_reproducible(tmp_path):
    """La misma muestra hoy y manana: si cambiara, dos mediciones no se podrian comparar."""
    ficheros = []
    for i in range(100):
        f = tmp_path / f"{i:03d}.json.gz"
        f.write_bytes(gzip.compress(b'{"name": "x"}'))
        ficheros.append(f)
    assert matriz._muestra(ficheros, 10) == matriz._muestra(ficheros, 10)
    assert len(matriz._muestra(ficheros, 10)) == 10


def test_una_muestra_pequena_se_coge_entera(tmp_path):
    ficheros = []
    for i in range(3):
        f = tmp_path / f"{i}.json.gz"
        f.write_bytes(gzip.compress(b"{}"))
        ficheros.append(f)
    assert len(matriz._muestra(ficheros, 40)) == 3


def test_normaliza_tildes_y_mayusculas():
    """Las cadenas escriben 'Ingredientes' y 'Alérgenos': hay que verlo sin tildes."""
    assert matriz._normaliza("Alérgenos: LECHE") == "alergenos: leche"
    assert "ingrediente" in matriz._normaliza("INGREDIENTES")


def test_lee_un_crudo_comprimido_y_no_revienta_con_uno_roto(tmp_path):
    bueno = tmp_path / "bueno.json.gz"
    bueno.write_bytes(gzip.compress(b'{"name": "Leche", "ingredients": "leche"}'
))
    assert "ingredients" in matriz._texto_de(bueno)
    roto = tmp_path / "roto.json.gz"
    roto.write_bytes(b"esto no es gzip")
    # No lanza: devuelve una marca de error, que el informe cuenta aparte.
    assert matriz._texto_de(roto).startswith("__error__")


def test_los_campos_de_la_ficha_estan_declarados():
    """La lista es el contrato de T11: sin ingredientes ni nutrientes no hay recetas ni calorias."""
    for campo in ("ingredientes", "alergenos", "traza", "nutrientes", "energia_kcal",
                  "base_nutricional", "peso_neto", "peso_escurrido", "piezas", "envase",
                  "origen", "conservacion", "preparacion", "certificaciones", "advertencias",
                  "gtin", "marca", "descripcion"):
        assert campo in matriz.CAMPOS, f"falta el campo {campo}"
        assert matriz.CAMPOS[campo], f"el campo {campo} no tiene ninguna señal que buscar"


# --- Contar productos y no respuestas: el denominador cambia la respuesta ----------------------

def test_encuentra_los_productos_dentro_de_un_listado():
    """Un listado de categoria trae muchos productos: contarlos a ellos, no a la respuesta."""
    listado = {"categories": [{"id": 1, "name": "Lacteos"}],
               "items": [{"id": "a1", "name": "Leche entera 1 l", "price": 1.09, "ean": "123"},
                         {"id": "a2", "name": "Yogur natural", "price": 0.85, "ean": "456"}]}
    encontrados = matriz.objetos_de_producto(listado)
    assert [o["name"] for o in encontrados] == ["Leche entera 1 l", "Yogur natural"]


def test_una_categoria_no_es_un_producto():
    """Una categoria tiene nombre, pero no precio, unidad ni codigo: no puede ser el denominador."""
    listado = {"categories": [{"id": 1, "name": "Lacteos", "categories": []}],
               "name": "Lacteos", "id": 1}
    assert matriz.objetos_de_producto(listado) == []


def test_recorre_estructuras_anidadas():
    anidado = {"data": {"products": [{"id": "x", "title": "Pan", "price": {"unit_price": 1}}]}}
    assert [o["title"] for o in matriz.objetos_de_producto(anidado)] == ["Pan"]


def test_el_limite_corta_para_no_recorrer_un_catalogo_entero():
    grande = {"items": [{"id": str(i), "name": f"P{i}", "price": 1} for i in range(100)]}
    assert len(matriz.objetos_de_producto(grande, limite=10)) == 10


def test_un_json_roto_no_revienta():
    assert matriz._json_de("esto no es json") is None
    assert matriz._json_de('{"a": 1}') == {"a": 1}
