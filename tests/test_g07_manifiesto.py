"""G07: el manifiesto mide la ficha y el precio **por separado**.

G07 lo pide con estas palabras: *«descubrimiento con sitemap antiguo no implica automaticamente precio
antiguo; **medir ambos por separado**»*. Hasta hoy el manifiesto declaraba **una sola** fecha de captura
-- la de ficha, que sale de `bronze` -- y los precios viven en `gold/precio_diario` con la suya. *Un
catalogo con las fichas de hoy y los precios de anteayer producia **cero avisos** y se leia como
fresco.*
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import polars as pl
import pytest

from core import manifiesto


@pytest.fixture()
def almacen(tmp_path, monkeypatch):
    """Un gold y un bronze de ensayo, sin tocar los de verdad."""
    oro = tmp_path / "gold"
    bronce = tmp_path / "bronze"
    oro.mkdir()
    bronce.mkdir()
    monkeypatch.setattr(manifiesto, "GOLD", oro)
    monkeypatch.setattr(manifiesto, "BRONZE", bronce)
    monkeypatch.setattr(manifiesto, "MANIFIESTO", oro / "manifiesto.json")
    monkeypatch.setattr(manifiesto, "COBERTURA", tmp_path / "cobertura")
    monkeypatch.setattr(manifiesto, "POLITICA", tmp_path / "alcance.yml")

    def ficha(fuente: str, dia: str) -> None:
        carpeta = bronce / f"fuente={fuente}" / f"fecha={dia}"
        carpeta.mkdir(parents=True)
        pl.DataFrame({"fuente": [fuente], "id_fuente": ["1"]}).write_parquet(carpeta / "part.parquet")

    def precio(fuente: str, dia: str) -> None:
        fila = {"fuente": fuente, "id_fuente": "1", "precio_cent": 100,
                "precio_unidad_cent": 1.0, "unidad_canon": "kg", "producto_id": "p", "fecha": dia}
        ruta = oro / "precio_diario.parquet"
        nuevo = pl.DataFrame([fila])
        if ruta.exists():
            nuevo = pl.concat([pl.read_parquet(ruta), nuevo])
        nuevo.write_parquet(ruta)

    return {"ficha": ficha, "precio": precio, "oro": oro}


def test_la_ficha_y_el_precio_van_cada_uno_con_su_fecha(almacen):
    """**Los dos relojes, dichos por separado.** Es la clausula que faltaba de G07."""
    hoy = date.today().isoformat()
    almacen["ficha"]("alcampo", hoy)
    almacen["precio"]("alcampo", "2026-01-01")

    d = manifiesto.construye()
    alcampo = d["fuentes"]["alcampo"]
    assert alcampo["captura"] == hoy, "la ficha es de hoy"
    assert alcampo["precio"] == "2026-01-01", "y el precio, de enero"


def test_con_la_ficha_de_hoy_y_el_precio_viejo_AVISA(almacen):
    """*El caso contra el que G07 escribe esa linea.*"""
    hoy = date.today().isoformat()
    almacen["ficha"]("alcampo", hoy)
    almacen["precio"]("alcampo", "2026-01-01")

    avisos = manifiesto.construye()["avisos"]
    assert any("el precio es de 2026-01-01" in a for a in avisos), (
        "una ficha de hoy con un precio de enero no es un catalogo de hoy, y hay que decirlo")


def test_si_las_dos_fechas_coinciden_no_hay_aviso(almacen):
    """**Y el filtro va por la frase entera, no por la palabra.** *«precio» a secas casa con el aviso
    de «falta publicar: … precio_diario.parquet …», que aqui sale y es correcto: el montaje no escribe
    los seis ficheros de gold.*"""
    hoy = date.today().isoformat()
    almacen["ficha"]("alcampo", hoy)
    almacen["precio"]("alcampo", hoy)
    avisos = manifiesto.construye()["avisos"]
    assert not [a for a in avisos if "el precio es de" in a], (
        "con las dos fechas iguales no hay nada que avisar")


def test_sin_fichero_de_precios_el_manifiesto_sale_igual(almacen):
    """**No lanza.** El dia se mide por el dato, no por el manifiesto."""
    almacen["ficha"]("aldi", date.today().isoformat())
    d = manifiesto.construye()
    assert d["fuentes"]["aldi"]["precio"] is None
    assert d["fuentes"]["aldi"]["captura"] == date.today().isoformat()


def test_una_cadena_con_precio_y_sin_ficha_entra_en_el_manifiesto(almacen):
    """*Un precio sin ficha tambien es un dato, y hasta hoy no aparecia.*"""
    almacen["precio"]("lidl", "2026-05-05")
    fuentes = manifiesto.construye()["fuentes"]
    assert fuentes["lidl"]["precio"] == "2026-05-05"
    assert fuentes["lidl"]["captura"] is None


def test_se_escribe_de_forma_atomica_y_no_deja_temporal(almacen):
    almacen["ficha"]("dia", date.today().isoformat())
    ruta = manifiesto.escribe()
    assert ruta is not None and ruta.exists()
    datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
    assert datos["version_manifiesto"] == manifiesto.VERSION_MANIFIESTO
    assert not list(Path(almacen["oro"]).glob("*.tmp")), "sin restos del temporal"
