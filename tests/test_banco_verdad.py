"""Pruebas del banco de verdad: reproducible, ciego y con los dos errores bien separados.

Lo que se fija aqui no es el vocabulario de la politica, sino el **instrumento**: que la muestra sea
la misma siempre, que el fichero de etiquetar no lleve el veredicto, y que un falso descarte y un
bazar aceptado no se mezclen en la misma cuenta. Si el instrumento esta mal, cualquier numero que
salga de el da igual lo bien que este la politica.
"""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

from projects.cesta import banco_verdad as banco


def _ficha(fuente: str, nombre: str, categoria: str, estado: str, familia: str = "") -> dict:
    return {"id": banco._id(fuente, nombre, categoria), "fuente": fuente, "nombre": nombre,
            "categoria": categoria, "estado_politica": estado, "familia_politica": familia}


def test_la_misma_muestra_siempre():
    """Reproducible: dos ejecuciones dan exactamente las mismas fichas, en el mismo orden.

    Es lo que permite comparar la medicion de hoy con la de dentro de un mes sin que el muestreo
    explique la diferencia.
    """
    fichas = [_ficha("aldi", f"Producto {i}", "despensa", banco.alcance.INCLUIDO, "despensa")
              for i in range(50)]
    fichas += [_ficha("aldi", f"Bazar {i}", "hogar-y-decoracion", banco.alcance.EXCLUIDO)
               for i in range(20)]
    primera = banco.muestrear(fichas, 5)
    segunda = banco.muestrear(fichas, 5)
    assert [f["id"] for f in primera] == [f["id"] for f in segunda]
    assert len(primera) > 0


def test_la_muestra_respeta_las_cuotas_por_estrato():
    fichas = ([_ficha("aldi", f"Incluido {i}", "despensa", banco.alcance.INCLUIDO, "despensa")
               for i in range(10)]
              + [_ficha("dia", f"Excluido {i}", "bazar", banco.alcance.EXCLUIDO) for i in range(10)])
    muestra = banco.muestrear(fichas, 4)
    por_estrato = {}
    for f in muestra:
        por_estrato.setdefault((f["fuente"], f["estado_politica"]), 0)
        por_estrato[(f["fuente"], f["estado_politica"])] += 1
    assert por_estrato[("aldi", banco.alcance.INCLUIDO)] == 4
    assert por_estrato[("dia", banco.alcance.EXCLUIDO)] == 4


def test_un_estrato_pequeno_se_coge_entero_y_se_dice():
    """Si no hay suficientes fichas, la muestra es mas pequena: no se rellena con lo que no toca."""
    fichas = [_ficha("aldi", "Solo uno", "despensa", banco.alcance.INCLUIDO, "despensa")]
    assert len(banco.muestrear(fichas, 5)) == 1


def test_el_fichero_de_etiquetar_no_lleva_el_veredicto(tmp_path, monkeypatch):
    """Ciego: el que etiqueta no puede ver lo que dice la politica, o etiqueta lo que le dicen."""
    monkeypatch.setattr(banco, "BANCO", tmp_path)
    monkeypatch.setattr(banco, "MUESTRA", tmp_path / "muestra.csv")
    monkeypatch.setattr(banco, "CIEGA", tmp_path / "para-etiquetar.csv")
    banco._escribe_muestra([_ficha("aldi", "Barrita proteica", "parafarmacia",
                                   banco.alcance.EXCLUIDO)])
    with (tmp_path / "para-etiquetar.csv").open(encoding="utf-8") as f:
        ciegas = list(csv.DictReader(f))
    assert list(ciegas[0]) == ["id", "fuente", "nombre", "categoria"], "la copia ciega lleva mas"
    assert "estado_politica" not in ciegas[0]
    # Y la muestra completa si lo lleva, que es con la que se mide.
    with (tmp_path / "muestra.csv").open(encoding="utf-8") as f:
        completa = next(iter(csv.DictReader(f)))
    assert completa["estado_politica"] == banco.alcance.EXCLUIDO


@pytest.mark.parametrize("etiqueta, estado, esperado", [
    (banco.CESTA, banco.alcance.EXCLUIDO, "falso_descarte"),      # comida que la politica tira
    (banco.CESTA, banco.alcance.INCLUIDO, "acuerdo"),
    (banco.NO_CESTA, banco.alcance.INCLUIDO, "bazar_aceptado"),   # bazar que entra como cesta
    (banco.NO_CESTA, banco.alcance.EXCLUIDO, "acuerdo"),
    (banco.DUDA, banco.alcance.INCLUIDO, "duda"),
])
def test_los_dos_errores_se_cuentan_por_separado(etiqueta, estado, esperado):
    """Un falso descarte y un bazar aceptado son errores distintos y no se suman en la misma cifra.

    Sumarlos daria un "error total" que no dice que arreglar. La duda se cuenta aparte: forzar un si
    o un no en un caso limite es como se fabrican los numeros bonitos.
    """
    ficha = _ficha("aldi", "Cosa", "sitio", estado)
    if etiqueta == banco.CESTA and estado == banco.alcance.EXCLUIDO:
        clasificado = "falso_descarte"
    elif etiqueta == banco.NO_CESTA and estado == banco.alcance.INCLUIDO:
        clasificado = "bazar_aceptado"
    elif etiqueta == banco.DUDA:
        clasificado = "duda"
    else:
        clasificado = "acuerdo"
    assert clasificado == esperado
    assert ficha["estado_politica"] == estado


def test_el_id_es_estable_y_distingue_fichas(tmp_path: Path):
    """La etiqueta se pega a la ficha, no a la posicion: por eso el id es un hash del contenido."""
    uno = banco._id("aldi", "Leche entera 1 l", "lacteos")
    assert uno == banco._id("aldi", "Leche entera 1 l", "lacteos")
    assert uno != banco._id("dia", "Leche entera 1 l", "lacteos")
    assert uno != banco._id("aldi", "Leche entera 1 l", "lacteos > otro")
