"""El techo del bloqueo: la medida que dice si el recall es una nota o un limite.

Esta prueba vigila **el instrumento**, no el dato: que separe bien los tres motivos por los que
el bloqueo pierde un par, porque el arreglo de cada uno es distinto (leer mejor el formato,
tratar los packs, o comparar unidades distintas) y contarlos todos juntos no dice qué hacer.

El dato de verdad lo mide `projects/cesta/bloqueo.py` sobre el gold de hoy; aqui se comprueba
que mira donde dice que mira.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from projects.cesta import bloqueo

GOLD = Path(__file__).resolve().parents[1] / "data" / "gold" / "grupos.parquet"


def _par(cantidad_a, unidad_a, cantidad_b, unidad_b) -> tuple:
    """Un par con la forma que devuelve la consulta: (fuente, nombre, cant, unidad) x2 + ean."""
    return ("alcampo", "Cafe molido X 1 kg", cantidad_a, unidad_a,
            "dia", "Cafe molido X 1 kg", cantidad_b, unidad_b, "8412345678905")


def test_el_mismo_formato_no_se_pierde():
    assert bloqueo._motivo(_par(1.0, "kg", 1.0, "kg")) is None


def test_sin_formato_leible_es_otro_motivo():
    """Una cantidad ausente no es «formato distinto»: es que no se pudo leer, y eso se arregla
    en silver (o no se arregla, pero se sabe donde mirar)."""
    assert bloqueo._motivo(_par(None, "kg", 1.0, "kg")) == "no se le pudo leer el formato"
    assert bloqueo._motivo(_par(1.0, "kg", None, None)) == "no se le pudo leer el formato"


def test_peso_contra_unidad_es_otro_motivo():
    """«6 x 44 g» frente a la pieza suelta: el mismo helado vendido de dos formas."""
    assert (bloqueo._motivo(_par(0.044, "kg", 1.0, "ud"))
            == "una cadena lo vende por unidad y la otra al peso")


def test_misma_unidad_y_cantidad_distinta_es_el_pack():
    """Y este es el unico de los tres que a veces NO es un error: es un pack."""
    assert (bloqueo._motivo(_par(1.5, "l", 9.0, "l"))
            == "misma unidad y cantidad distinta (pack frente a suelta)")


@pytest.mark.skipif(not GOLD.exists(), reason="esta copia no trae gold")
def test_la_medida_sale_y_sus_partes_suman():
    """Con gold delante: el resumen cuenta, y los vistos + los perdidos son el total."""
    r = bloqueo.resumen()
    assert r["pares_ciertos"] >= bloqueo.MINIMO_PARES, (
        f"solo {r['pares_ciertos']} pares ciertos: la medida no diria nada")
    assert r["los_ve_el_bloqueo"] + r["no_los_ve"] == r["pares_ciertos"]
    assert 0 < r["completeness_pct"] <= 100
    # Los motivos no tienen que sumar el total (un par puede fallar por mas de uno), pero
    # ninguno puede ser mayor que los perdidos.
    assert all(v <= r["no_los_ve"] for v in r["motivos"].values())
    assert set(r["motivos"]) <= {
        "no se le pudo leer el formato",
        "una cadena lo vende por unidad y la otra al peso",
        "misma unidad y cantidad distinta (pack frente a suelta)"}
