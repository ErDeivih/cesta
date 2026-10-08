"""La respuesta dice de que version del catalogo salen los precios, no solo de que dia.

Se comprueba en dos niveles: que el dato existe y es el del puntero -- eso es comportamiento, y se prueba
leyendo el fichero de verdad -- y que el endpoint lo manda, que se lee en el codigo porque la llamada toca
la base.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from plataforma.api import main

PUNTERO = Path(__file__).resolve().parents[1] / "data" / "gold" / "actual.json"


def test_la_version_del_catalogo_se_sabe_leer():
    from core import publicacion

    if not PUNTERO.exists():
        pytest.skip("esta copia no tiene catalogo publicado")
    esperada = json.loads(PUNTERO.read_text(encoding="utf-8"))["version"]
    assert publicacion.version_actual() == esperada


def test_sin_puntero_no_se_inventa_una_version(tmp_path, monkeypatch):
    """Sin catalogo publicado, `None`. Una version inventada seria peor que no tener ninguna."""
    from core import publicacion

    monkeypatch.setattr(publicacion, "PUNTERO", tmp_path / "no-existe.json")
    assert publicacion.version_actual() is None


def test_el_estado_manda_la_version_y_no_solo_el_dia():
    fuente = Path(main.__file__).read_text(encoding="utf-8")
    assert '"version_catalogo": _version_del_catalogo()' in fuente, \
        "sin la version, un precio no se puede atar a su catalogo"
    assert "def _version_del_catalogo" in fuente
