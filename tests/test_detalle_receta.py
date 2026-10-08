"""El detalle por receta lee la receta de la ruta y tiene 404 de verdad.

Se lee el codigo, como las demas pruebas de contrato del frontend, porque aqui nada da error al compilar si
la pantalla sigue sirviendo el modulo compartido: simplemente seguiria sin leer nada persistido.
"""
from __future__ import annotations

from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "plataforma" / "web" / "app" / "src"


def _leer(relativa: str) -> str:
    ruta = SRC / relativa
    if not ruta.exists():
        pytest.skip("esta copia no trae la interfaz nueva")
    return ruta.read_text(encoding="utf-8")


def test_la_ruta_del_detalle_ya_no_sirve_el_modulo_compartido():
    app = _leer("App.tsx")
    assert "RecetaDetalle" in app
    assert 'path="/recetas/:recetaId"' in app
    # Las tres secciones de recetas tienen ya su pantalla propia.
    assert '<Recetario />' in app and '<PlanSemanal />' in app, \
        "las otras dos rutas de recetas siguen donde estaban"


def test_el_detalle_lee_la_receta_de_la_ruta_y_no_un_estado_de_paso():
    detalle = _leer("paginas/RecetaDetalle.tsx")
    assert "useParams()" in detalle, "el identificador sale de la direccion"
    assert "useReceta(id, version)" in detalle, "y la receta se pide a la API con ese identificador"


def test_el_404_se_distingue_de_un_fallo():
    """Un 404 de una receta es una respuesta, no un error rojo."""
    detalle = _leer("paginas/RecetaDetalle.tsx")
    assert "error.estado === 404" in detalle
    assert "Esa receta no existe" in detalle


def test_se_puede_llegar_a_una_version_concreta():
    detalle = _leer("paginas/RecetaDetalle.tsx")
    assert "setVersion(Number(e.target.value))" in detalle
    assert "Estas viendo una version anterior" in detalle, \
        "mirar una version vieja tiene que decirse, no parecer la ultima"
