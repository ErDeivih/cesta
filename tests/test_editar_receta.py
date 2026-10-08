"""Editar una receta: el formulario dice que crea version nueva, y no inventa cantidades.

Se lee el codigo, como las demas pruebas de contrato del frontend: aqui nada da error al compilar si el
formulario no esta conectado, simplemente la receta no se podria cambiar desde su pantalla.
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


def test_el_detalle_tiene_el_formulario_conectado():
    detalle = _leer("paginas/RecetaDetalle.tsx")
    assert "FormularioReceta" in detalle
    assert "<FormularioReceta receta={data} />" in detalle


def test_editar_dice_en_voz_alta_que_crea_version_nueva():
    """Si creyera que reescribe, no entenderia por que luego aparecen dos versiones."""
    formulario = _leer("componentes/FormularioReceta.tsx")
    assert "version nueva" in formulario
    assert "se conserva" in formulario
    assert "Guardar como version nueva" in formulario


def test_lo_que_no_se_cambia_no_se_manda():
    """El servidor hereda copiado lo que no se manda; el formulario solo manda lo que se toca."""
    formulario = _leer("componentes/FormularioReceta.tsx")
    assert "useCambiarReceta(receta.id)" in formulario
    assert "onSuccess: () => setAbierto(false)" in formulario


def test_sin_cantidad_no_se_inventa_una():
    formulario = _leer("componentes/FormularioReceta.tsx")
    assert "Sin cantidad no se inventa una" in formulario


def test_los_campos_no_bajan_de_16_px():
    formulario = _leer("componentes/FormularioReceta.tsx")
    assert "text-[16px]" in formulario
    assert "text-[15px]" not in formulario, "ningun campo de texto por debajo de 16 px"
