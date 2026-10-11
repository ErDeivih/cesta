"""G02: una lista de casa por persona, y **la respuesta cuando ya hay una**.

**Por que esta prueba esta aqui y no en `test_lineas_api.py`.** Aquella sustituye el almacen por un
doble -- y esta bien que lo haga, porque mide el contrato de la ruta. Pero **la regla que se comprueba
aqui vive en la base**: la restriccion `lista_de_casa_por_dueno`. Con un doble nunca se dispara, y el
defecto original era exactamente eso: **la restriccion hacia su trabajo y el usuario leia «Internal
Server Error»**. Medido contra la API viva el 11 de octubre de 2026:

    psycopg.errors.UniqueViolation: duplicate key value violates unique constraint
    "lista_de_casa_por_dueno"  DETAIL: Key (dueno_id)=(9d82b14f-...) already exists.

**Por que importa mas de lo que parece.** La lista de casa es **el eje de la aplicacion**: alimenta el
contador del menu, el puente de la compra y las alertas. Que exista una sola es la regla correcta;
**que crear la segunda culpe al servidor no lo es**. Un 500 ahi manda a mirar los registros de la API
por algo que la persona puede entender y resolver en un segundo.

Se salta con motivo explicito si no hay motor:

    $env:CESTA_POSTGRES='postgresql://cesta:prueba@127.0.0.1:5434/cesta'
    uv run pytest -q tests/test_lista_de_casa_unica.py
"""
from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

from plataforma.api import almacen, main

BASE = "postgresql://cesta:prueba@127.0.0.1:5434/cesta"
CLAVE = "clave-de-prueba-123"
_CUENTA: str | None = None


@pytest.fixture(scope="module")
def con_almacen():
    """El almacen real, arrancado **una vez**: arrancarlo por prueba deja conexiones sin devolver."""
    global _CUENTA
    try:
        almacen.arranca(espera=10)
    except Exception as fallo:  # noqa: BLE001 -- el motivo va en el skip
        pytest.skip(f"sin almacen en CESTA_POSTGRES al importar. Ejecuta con "
                    f"$env:CESTA_POSTGRES='{BASE}' | {type(fallo).__name__}: {fallo}")
    with TestClient(main.app) as preparacion:
        for candidata in ("prueba-navegador", "recibo-de-prueba"):
            if preparacion.post("/api/entrar",
                                json={"usuario": candidata, "clave": CLAVE}).status_code == 200:
                _CUENTA = candidata
                break
        else:
            usuario = f"casa{int(time.time() * 1000) % 100000000}"
            r = preparacion.post("/api/registrarse",
                                 json={"nombre": "Prueba Casa", "usuario": usuario, "clave": CLAVE})
            if r.status_code == 429:
                pytest.skip("no hay cuenta de prueba y el alta tiene limite por hora agotado")
            assert r.status_code == 201, r.text
            _CUENTA = usuario
    # **Salir del `with TestClient(...)` APAGA el almacen**, porque el `lifespan` de la aplicacion lo
    # cierra al terminar. Es lo que hacia que la primera prueba de un modulo pasara y las siguientes
    # murieran con `RuntimeError: el almacen no esta arrancado`. Medido el 11 de octubre de 2026.
    almacen.arranca(espera=10)
    yield
    main.app.dependency_overrides.clear()


@pytest.fixture()
def limpio():
    """**Y aqui se vuelve a arrancar el almacen, que es lo que faltaba.**

    Cada prueba abre su cliente con `with TestClient(main.app) as cliente:`, y **salir de ese `with`
    ejecuta el `lifespan` de la aplicacion, que CIERRA el almacen**. Con el arranque solo al principio
    del modulo, la primera prueba pasaba y la segunda moria con `RuntimeError: el almacen no esta
    arrancado`. Medido el 11 de octubre de 2026: `test_una_lista_normal_sin_marca_de_casa...` **pasa
    sola y falla en el fichero**, que es la firma exacta de un problema de estado entre pruebas.
    """
    yield
    main.app.dependency_overrides.clear()
    almacen.arranca(espera=10)


def _cliente() -> TestClient:
    cliente = TestClient(main.app)
    r = cliente.post("/api/entrar", json={"usuario": _CUENTA, "clave": CLAVE})
    assert r.status_code == 200, f"no se pudo entrar con {_CUENTA}: {r.status_code} {r.text}"
    return cliente


def test_la_segunda_lista_de_casa_responde_409_y_no_500(con_almacen, limpio):
    """**La regla se mantiene y la respuesta dice la verdad.**

    No se le quita la restriccion a la base -- una lista de casa por persona es lo correcto --, pero
    la segunda peticion **no puede** salir como «el servidor ha fallado»: es una peticion que no se
    puede atender, y el mensaje tiene que decirlo.
    """
    with _cliente() as cliente:
        # La cuenta de prueba ya tiene su «Casa»; si no la tuviera, esta la crea y la segunda choca.
        primera = cliente.post("/api/listas", json={"nombre": "Casa", "es_de_casa": True})
        assert primera.status_code in (200, 201, 409), primera.text

        segunda = cliente.post("/api/listas",
                               json={"nombre": "Otra casa", "es_de_casa": True})
        assert segunda.status_code == 409, (
            f"la segunda lista de casa ha contestado {segunda.status_code}: {segunda.text}")
        detalle = segunda.json().get("detail", "")
        assert "lista de casa" in detalle.lower(), (
            f"el mensaje tiene que decir que pasa: {detalle!r}")
        assert "error" not in detalle.lower() or "ya tienes" in detalle.lower(), detalle


def test_una_lista_normal_sin_marca_de_casa_sigue_creandose(con_almacen, limpio):
    """**Y lo de antes no se ha roto**: las listas que no son de casa no tienen limite."""
    with _cliente() as cliente:
        for i in (1, 2):
            r = cliente.post("/api/listas",
                             json={"nombre": f"Lista suelta {i}", "es_de_casa": False})
            assert r.status_code in (200, 201), f"la {i}: {r.status_code} {r.text}"
