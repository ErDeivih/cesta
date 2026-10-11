"""G02: la linea sin destino, contra el almacen real.

**Dos nombres para lo mismo, y conviene saberlo antes de leer esto**: el contrato de entrada
(`NuevaLinea`) llama al campo `nombre`, y el almacen lo devuelve como **`nombre_visto`** -- «lo que se
vio escrito», que es mas exacto, porque no es un nombre de producto sino el texto que alguien tecleo.
El 11 de octubre de 2026 esta misma confusion me costo una migracion fallida y tres aserciones

**Por que necesita PostgreSQL.** La regla que cambia este paquete **vive en la base**: era una
restriccion (`linea_con_destino`) y la migracion 014 la sustituye por una que exige el nombre. Medir
esto con dobles mediria el doble: lo que hay que comprobar es que **la base acepta la linea sin
destino y sigue rechazando la que no tiene nombre**.

Se salta con motivo explicito si no hay motor, y la cadena se lee **al importar**, asi que va en el
comando:

    $env:CESTA_POSTGRES='postgresql://cesta:prueba@127.0.0.1:5434/cesta'
    uv run pytest -q tests/test_g02_texto_libre.py
"""
from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

from plataforma.api import almacen, main

BASE = "postgresql://cesta:prueba@127.0.0.1:5434/cesta"
CLAVE = "clave-de-prueba-123"
_CUENTA: str | None = None
_LISTA: str | None = None


@pytest.fixture(scope="module")
def con_almacen():
    """**Una cuenta y una lista para toda la sesion de pruebas**, resueltas una sola vez.

    Resolver la cuenta dentro de cada prueba hacia dos cosas malas: repetir el alta -- que tiene
    **limite por hora** y acababa saltando las pruebas -- y abrir conexiones de mas. La cuenta se
    busca entre las que ya existen y solo se crea si no hay ninguna.
    """
    global _CUENTA, _LISTA
    try:
        almacen.arranca(espera=10)
    except Exception as fallo:  # noqa: BLE001 -- el motivo va en el skip
        pytest.skip(f"sin almacen en CESTA_POSTGRES al importar. Ejecuta con "
                    f"$env:CESTA_POSTGRES='{BASE}' | {type(fallo).__name__}: {fallo}")
    with TestClient(main.app) as preparacion:
        if _CUENTA is None:
            for candidata in ("prueba-navegador", "recibo-de-prueba"):
                if preparacion.post("/api/entrar",
                                    json={"usuario": candidata, "clave": CLAVE}).status_code == 200:
                    _CUENTA = candidata
                    break
            else:
                usuario = f"texto{int(time.time() * 1000) % 100000000}"
                r = preparacion.post("/api/registrarse",
                                     json={"nombre": "Prueba Texto", "usuario": usuario, "clave": CLAVE})
                if r.status_code == 429:
                    pytest.skip("no hay cuenta de prueba y el alta tiene limite por hora agotado")
                assert r.status_code == 201, r.text
                _CUENTA = usuario
    yield
    main.app.dependency_overrides.clear()


@pytest.fixture()
def limpio():
    """El estado por prueba se limpia, pero **el almacen no se rearranca**: arrancarlo en cada una
    dejaba conexiones sin devolver y las siguientes fallaban con `psycopg`. Medido el 11 de octubre
    de 2026: con `arranca()` por prueba, la primera pasaba y las tres siguientes no."""
    yield
    main.app.dependency_overrides.clear()


def _entra(cliente: TestClient) -> None:
    """Entra con la cuenta de la sesion: esta prueba mide la linea, no el alta."""
    r = cliente.post("/api/entrar", json={"usuario": _CUENTA, "clave": CLAVE})
    assert r.status_code == 200, f"no se pudo entrar con {_CUENTA}: {r.status_code} {r.text}"


def _lista(cliente: TestClient) -> str:
    """**Una lista nueva por prueba**, para que lo que se afirme no dependa de lo anterior."""
    r = cliente.post("/api/listas", json={"nombre": "Prueba texto libre", "es_de_casa": False})
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def test_una_linea_solo_con_nombre_se_puede_apuntar(con_almacen, limpio):
    """**Lo que el paquete desbloquea**: apuntar lo que no está en el catálogo.

    Antes esto devolvía *«Una linea necesita el grupo o el producto al que se refiere»* (422), y por
    eso «papel de cocina» o «lo que sea del mercado» no se podían apuntar en la lista.
    """
    with TestClient(main.app) as cliente:
        _entra(cliente)
        lista_id = _lista(cliente)
        r = cliente.post(f"/api/listas/{lista_id}/lineas",
                         json={"nombre": "Papel de cocina", "cantidad": 2})
        assert r.status_code == 201, f"deberia aceptarse: {r.status_code} {r.text}"
        linea = r.json()
        assert linea.get("nombre_visto") == "Papel de cocina", linea
        # **Sin destino, y sin inventarle nada.**
        assert linea.get("grupo_id") is None and linea.get("producto_id") is None
        assert linea.get("precio_cent") is None, "no se le inventa precio"
        assert linea.get("importe_cent") is None, "ni importe"


def test_sigue_en_la_lista_y_se_lee(con_almacen, limpio):
    """La línea existe, se lee y se puede identificar después: el vínculo es posterior y explícito."""
    with TestClient(main.app) as cliente:
        _entra(cliente)
        lista_id = _lista(cliente)
        cliente.post(f"/api/listas/{lista_id}/lineas", json={"nombre": "Lo del mercado"})
        detalle = cliente.get(f"/api/listas/{lista_id}")
        assert detalle.status_code == 200, detalle.text
        nombres = [x.get("nombre_visto") for x in detalle.json().get("lineas", [])]
        assert "Lo del mercado" in nombres, detalle.json()


def test_una_linea_sin_nombre_se_sigue_rechazando(con_almacen, limpio):
    """**La red que se queda**: sin nombre no hay nada que leer ni que identificar después.

    La migración 014 quitó una restricción y puso otra. Ésta comprueba que la nueva existe y corta.
    """
    with TestClient(main.app) as cliente:
        _entra(cliente)
        lista_id = _lista(cliente)
        r = cliente.post(f"/api/listas/{lista_id}/lineas", json={"nombre": "   "})
        assert r.status_code >= 400, f"un nombre en blanco no deberia entrar: {r.status_code} {r.text}"


def test_una_linea_del_catalogo_sigue_funcionando(con_almacen, limpio):
    """**Y lo de antes no se ha roto**: con grupo del catálogo se apunta igual que siempre."""
    with TestClient(main.app) as cliente:
        _entra(cliente)
        lista_id = _lista(cliente)
        r = cliente.post(f"/api/listas/{lista_id}/lineas",
                         json={"nombre": "Con destino", "grupo_id": 6803})
        assert r.status_code == 201, r.text
        assert r.json().get("grupo_id") == 6803
