"""Elegir raciones en la pantalla: el campo, las dos cifras y las reglas del contrato.

Se lee el codigo, como las demas pruebas de contrato del frontend, porque aqui nada da error al compilar si
el servidor escala y la pantalla no lo pide: el trabajo quedaria hecho y sin verse.
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


def test_el_gancho_de_datos_pide_las_raciones_y_las_lleva_en_la_clave():
    api = _leer("api/recetas.ts")
    assert "raciones?: number | null" in api
    assert "raciones: raciones ?? undefined" in api, "la peticion tiene que mandarlas"
    assert "raciones ?? 'receta'" in api, \
        "y la clave tiene que llevarlas, o dos escalas distintas compartirian entrada de cache"


def test_el_detalle_deja_elegir_para_cuantas_raciones():
    detalle = _leer("paginas/RecetaDetalle.tsx")
    assert "setRaciones" in detalle
    assert "useReceta(id, version, raciones)" in detalle


def test_el_campo_no_baja_de_16_px():
    """Por debajo de 16, el navegador del movil hace zoom al enfocar: lo vigila el contrato de movil."""
    detalle = _leer("paginas/RecetaDetalle.tsx")
    assert 'id="raciones"' in detalle and 'type="number"' in detalle
    assert "text-[16px]" in detalle, "el campo de raciones tiene que ir a 16 px o mas"


def test_se_dicen_las_dos_cifras_cuando_se_esta_escalando():
    """Ensenar solo las pedidas haria creer que la receta es de seis."""
    detalle = _leer("paginas/RecetaDetalle.tsx")
    assert "data.escalada" in detalle
    assert "data.raciones_receta" in detalle
