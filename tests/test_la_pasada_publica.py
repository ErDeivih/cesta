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


def test_el_ciclo_publica_despues_de_lo_que_escribe_gold():
    """**F03 (fase 2): el orden que faltaba.** *Antes publicaba `pipeline.main()` a mitad del ciclo, y
    por eso la version publicada **no llevaba** `grupos.parquet` ni `enlaces.parquet` -- los dos
    ficheros que escribe el emparejador.* Medido el 13 de octubre de 2026: la ultima version publicada
    tenia esos dos distintos del gold y los otros cuatro identicos, asi que **lo que el emparejador
    calculaba no lo veia nadie.**

    *Se lee la fuente del ciclo, que es lo unico comprobable sin correr la pasada entera.*

    **Y son tres cosas**: que el pipeline **no** publique cuando lo llama el ciclo, que el ciclo
    publique, y que lo haga **despues** del emparejador.
    """
    import pathlib

    fuente = (pathlib.Path(__file__).resolve().parents[1]
              / "projects" / "cesta" / "run.py").read_text(encoding="utf-8")

    assert 'main(publicar=False)' in fuente, (
        "el ciclo tiene que decirle al pipeline que **no** publique: publicar antes del emparejador "
        "deja fuera los grupos emparejados")
    assert 'importlib.import_module("core.publicacion").publicar()' in fuente, (
        "y tiene que publicar **el ciclo**, que es quien sabe cuando se ha acabado de escribir gold")

    pos_emparejar = fuente.index('"projects.cesta.emparejar"')
    pos_publicar = fuente.index('"core.publicacion"')
    assert pos_publicar > pos_emparejar, (
        "la publicacion tiene que ir DESPUES del emparejador: es lo ultimo que toca gold")
    # Y el fallo entra en el veredicto del dia, que es la otra mitad del arreglo.
    assert 'fallos.append("publicacion")' in fuente
