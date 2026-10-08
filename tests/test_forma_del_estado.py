"""La forma de la respuesta de /api/estado: un objeto con sus claves.

**Esta prueba existe por un fallo real.** `/api/estado` llego a devolver la cadena de la version, porque el
decorador de la ruta acabó envolviendo a una función auxiliar insertada entre el decorador y `def estado()`.
La funcion era correcta, el fichero era correcto, y el endpoint estaba roto: solo se ve **llamandolo**.

Por eso esta prueba **llama** y mira la **forma**, en vez de leer el codigo. Las que leian el codigo pasaban
mientras el endpoint devolvia una cadena.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from plataforma.api import main

ESPERADAS = {"fecha_datos", "version_catalogo", "vigencia_precio", "dias_precio_valido", "cadenas"}


@pytest.fixture()
def cliente():
    main.app.dependency_overrides.clear()
    yield TestClient(main.app)
    main.app.dependency_overrides.clear()


def test_el_estado_devuelve_un_objeto_y_no_una_cadena(cliente):
    """El fallo del decorador se ve aqui y en ningun otro sitio: la respuesta era un texto."""
    r = cliente.get("/api/estado")
    assert r.status_code == 200
    cuerpo = r.json()
    assert isinstance(cuerpo, dict), f"esperaba un objeto y vino {type(cuerpo).__name__}: {cuerpo!r}"


def test_el_estado_trae_sus_claves(cliente):
    cuerpo = cliente.get("/api/estado").json()
    faltan = ESPERADAS - set(cuerpo)
    assert not faltan, f"faltan claves en la respuesta: {sorted(faltan)}"


def test_la_ruta_esta_registrada_sobre_la_funcion_del_estado():
    """La comprobacion directa del fallo: a que funcion esta atada la ruta."""
    atadas = [getattr(r, "endpoint", None) for r in main.app.routes
              if getattr(r, "path", "") == "/api/estado"]
    assert atadas, "no hay ninguna ruta /api/estado registrada"
    nombres = [getattr(f, "__name__", None) for f in atadas]
    assert nombres == ["estado"], f"la ruta esta atada a {nombres}, no a `estado`"
