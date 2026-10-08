"""Despues de publicar, el catalogo deja de declararse incoherente.

La regla de vigencia compara **el dia mas reciente de los precios** con **la publicacion del catalogo**. Si
gold se reescribe en su sitio y el puntero no se mueve, esos dos datos se separan y `/api/estado` lo dice -- con
razon. Esta prueba fija que publicar los vuelve a juntar.
"""
from __future__ import annotations

import polars as pl

from core import publicacion
from plataforma.api import main

DIA_PRECIO = "2026-10-08"


def test_antes_de_publicar_el_catalogo_se_declara_incoherente():
    """El estado que se sirve hoy: precios del 8 con publicacion del 7."""
    v = main._vigencia(DIA_PRECIO, "2026-10-07T16:15:18")
    assert v["comprobable"] is True
    assert v["coherente"] is False


def test_despues_de_publicar_los_dos_datos_concuerdan(tmp_path, monkeypatch):
    """Publicar adopta los ficheros sueltos y mueve el puntero: ahi se acaba la incoherencia."""
    gold = tmp_path / "gold"
    gold.mkdir()
    for nombre in publicacion.FICHEROS:
        pl.DataFrame({"x": [1]}).write_parquet(gold / nombre)
    monkeypatch.setattr(publicacion, "GOLD", gold)
    monkeypatch.setattr(publicacion, "PUNTERO", gold / "actual.json")

    version = publicacion.publicar()
    puntero = publicacion.version_actual()
    publicado_en = __import__("json").loads((gold / "actual.json").read_text(encoding="utf-8"))["publicado_en"]

    assert puntero == version
    # Y ahora la regla de vigencia, con los datos de verdad: el dia del precio no es posterior.
    v = main._vigencia(DIA_PRECIO, publicado_en)
    assert v["comprobable"] is True
    assert v["coherente"] is True, v


def test_la_pasada_publica_al_terminar():
    """El comportamiento que faltaba: el pipeline llama a publicar. Se lee su fuente, que es lo unico
    comprobable sin correr la pasada entera (que necesita red, disco y media hora)."""
    fuente = (__import__("pathlib").Path(__file__).resolve().parents[1]
              / "projects" / "cesta" / "pipeline.py").read_text(encoding="utf-8")
    assert "publicacion.publicar()" in fuente, (
        "la pasada escribe gold en su sitio y nadie mueve el puntero: eso es la incoherencia del 8 y el 7")
    # Y con su try, como el resto de la cola: un fallo al publicar no puede tumbar la pasada.
    assert "no se pudo publicar" in fuente
