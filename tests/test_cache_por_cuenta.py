"""La cache no puede sobrevivir a un cambio de cuenta.

Se lee el codigo, como en las pruebas de contraste y de movil del proyecto, porque esto es de las cosas
que no dan error al compilar y solo se notan cuando ya se ha enseñado el dato de otra persona.

Lo que se vigila: que el vaciado exista y este montado **antes** de la aplicacion, que dispare con el
cambio de cuenta y no en el primer render, y que las pantallas nuevas lleven la cuenta en su clave.
"""
from __future__ import annotations

from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
SRC = RAIZ / "plataforma" / "web" / "app" / "src"


def _leer(relativa: str) -> str:
    ruta = SRC / relativa
    if not ruta.exists():
        pytest.skip("esta copia no trae la interfaz nueva")
    return ruta.read_text(encoding="utf-8")


def test_al_cambiar_de_cuenta_se_vacia_la_cache():
    cuenta = _leer("api/cuenta.ts")
    assert "cliente.clear()" in cuenta, "sin vaciado, la cache de la cuenta anterior se queda"
    assert "anterior.current !== null && anterior.current !== clave" in cuenta, \
        "el primer render no puede vaciar: todavia no hay nada que vaciar"
    assert "JSON.stringify(data)" in cuenta, \
        "la clave de cuenta sale del JSON, para no acertar con la forma del objeto"


def test_el_vigilante_va_antes_que_la_aplicacion():
    main = _leer("main.tsx")
    assert "<VigilaCuenta />" in main, "el vigilante tiene que estar montado"
    assert main.index("<VigilaCuenta />") < main.index("<App />"), \
        "si va despues, hay un render con datos de la sesion anterior"


def test_las_pantallas_nuevas_llevan_la_cuenta_en_la_clave():
    recetas = _leer("api/recetas.ts")
    diario = _leer("api/diario.ts")
    for clave in ("['recetas', cuenta", "['receta', cuenta", "['plan', cuenta"):
        assert clave in recetas, f"falta la cuenta en la clave {clave}"
    assert "['diario', cuenta" in diario, "falta la cuenta en la clave del diario"
    assert "useClaveDeCuenta()" in recetas and "useClaveDeCuenta()" in diario
