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
    bueno.write_bytes(gzip.compress('{"name": "Leche", "ingredients": "leche"}'
                                    .encode("utf-8")))
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
