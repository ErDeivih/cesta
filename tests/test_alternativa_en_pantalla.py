"""La alternativa se declara en el tipo y se enseña con las funciones del proyecto.

Se lee el codigo, como las demas pruebas de contrato del frontend, porque aqui nada da error al compilar si
el campo no existe: simplemente no se enseña. Y se comprueba lo que la suite me enseno a base de rojos:
que el precio va con `euros` y la cadena con `nombreCadena`, porque `toFixed` pone el punto decimal y el
identificador (`dia`) no es el nombre ("DIA").
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


def test_el_tipo_declara_lo_que_el_servidor_manda():
    tipos = _leer("tipos.ts")
    assert "autorizada?: boolean" in tipos
    assert "alternativa?:" in tipos and "coste_cent: number" in tipos


def test_el_aviso_usa_las_funciones_del_proyecto_para_lo_que_se_lee():
    aviso = _leer("componentes/AvisoIdentidad.tsx")
    assert "euros(alternativa.coste_cent)" in aviso, "el precio se formatea con `euros`, no a mano"
    assert "toFixed" not in aviso, "`toFixed` pone el punto decimal: el proyecto no lo usa"
    assert "nombreCadena(alternativa.fuente)" in aviso, "la cadena se pinta con su nombre, no con su id"
    assert "alternativa.nombre" in aviso, "y hay que decir QUE se puede pedir"


def test_el_aviso_sigue_sin_pintarse_cuando_no_hay_nada_que_decir():
    aviso = _leer("componentes/AvisoIdentidad.tsx")
    assert "if (CONFIRMADO.has(identidad)) return null" in aviso


def test_el_reparto_le_pasa_la_alternativa():
    reparto = _leer("componentes/RepartoEnTiendas.tsx")
    assert "alternativa={f.alternativa}" in reparto
