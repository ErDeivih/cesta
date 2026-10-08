"""La cobertura por nutriente se enseña, y un nutriente sin dato se dice con la palabra.

Se lee el codigo, como las demas pruebas de contrato del frontend, porque aqui el fallo no da error: la
pantalla seguiria enseñando solo la energia y pareciendo completa.
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


def test_el_tipo_del_dia_declara_la_cobertura():
    api = _leer("api/diario.ts")
    assert "cobertura: Record<string," in api
    assert "con_dato: number" in api and "completa: boolean" in api


def test_la_pantalla_enseña_la_cobertura_nutriente_a_nutriente():
    diario = _leer("paginas/Diario.tsx")
    assert "data.cobertura" in diario
    assert "Object.entries(data.cobertura)" in diario
    assert "NOMBRE_NUTRIENTE" in diario, "los nutrientes se nombran en castellano, no con la clave"


def test_un_nutriente_que_no_trae_nadie_se_dice_con_la_palabra():
    """Un cero no es lo mismo que no saber, y aqui se nota: nadie anoto proteinas."""
    diario = _leer("paginas/Diario.tsx")
    assert "c.con_dato === 0" in diario
    assert "sin dato" in diario


def test_se_dice_de_cuantas_entradas_sale_cada_numero():
    diario = _leer("paginas/Diario.tsx")
    assert "c.con_dato} de {c.total" in diario
