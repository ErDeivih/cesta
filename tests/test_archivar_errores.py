"""Archivar ensena su error: una accion que falla en silencio hace creer que funciono.

Se lee el codigo, como las demas pruebas de contrato del frontend, porque aqui nada da error al compilar si
el error de la mutacion se ignora: simplemente no se ve.
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


def test_el_error_de_archivar_se_ensena():
    recetario = _leer("paginas/Recetario.tsx")
    assert "archivar.error" in recetario, "el error de la mutacion no puede quedarse sin usar"
    assert "textoDeError(archivar.error)" in recetario, "y con el motivo que da la API"


def test_el_error_solo_sale_cuando_toca():
    recetario = _leer("paginas/Recetario.tsx")
    assert "archivar.error && !r.archivada" in recetario
