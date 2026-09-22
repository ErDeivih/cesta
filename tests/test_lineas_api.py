"""Una peticion mal formada tiene que contestar 422, no 500.

Esta prueba existe por un hallazgo de la auditoria del front: anadir una linea
**sin destino** (ni grupo ni producto) devolvia **500**. Lo rechazaba la base con
una restriccion (`linea_con_destino`), y el `CheckViolation` salia por la puerta
como "el servidor ha fallado".

Un 500 ahi es mentira y ademas hace perder el tiempo: manda a mirar los registros
de la API por algo que es una peticion mal formada. La interfaz siempre manda uno
de los dos -- se comprobo contra la API viva --, asi que esto no se ve desde la
pantalla: se ve desde `curl`, y `curl` es donde se prueba una API.

No hay PostgreSQL en las pruebas: el almacen se sustituye, como en
`test_registro.py`.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from plataforma.api import almacen, main


def _cliente(monkeypatch, llamado: list):
    """El cliente con la sesion y el acceso resueltos, y el almacen espiado."""
    monkeypatch.setattr(almacen, "anade_linea",
                        lambda *a, **k: (llamado.append(a), {"id": "l1"})[1])
    monkeypatch.setattr(main, "_acceso", lambda *a, **k: "dueno")
    main.app.dependency_overrides[main.usuario_actual] = lambda: {
        "id": "u1", "usuario": "ana", "nombre": "Ana"}
    return TestClient(main.app)


def test_una_linea_sin_destino_da_422(monkeypatch):
    llamado: list = []
    cliente = _cliente(monkeypatch, llamado)
    try:
        r = cliente.post("/api/listas/una-lista/lineas",
                         json={"nombre": "Leche", "cantidad": 1})
        assert r.status_code == 422, (
            f"una linea sin grupo ni producto ha contestado {r.status_code}; "
            f"la base la rechaza, pero eso es una peticion mal formada, no un "
            f"fallo del servidor")
        assert "grupo o el producto" in r.json()["detail"]
        assert not llamado, (
            "ha llegado al almacen una linea sin destino: la comprobacion tiene "
            "que ir antes de escribir nada")
    finally:
        main.app.dependency_overrides.clear()


def test_una_linea_con_grupo_si_entra(monkeypatch):
    """El otro lado, para que la prueba de arriba no pase por no dejar pasar nada."""
    llamado: list = []
    cliente = _cliente(monkeypatch, llamado)
    try:
        r = cliente.post("/api/listas/una-lista/lineas",
                         json={"nombre": "Leche", "grupo_id": 11580, "cantidad": 1})
        assert r.status_code == 201, r.text
        assert llamado, "no ha llegado nada al almacen con una linea bien formada"
    finally:
        main.app.dependency_overrides.clear()


def test_una_linea_con_producto_tambien_entra(monkeypatch):
    """El destino puede ser el producto en vez del grupo, y las dos vias valen."""
    llamado: list = []
    cliente = _cliente(monkeypatch, llamado)
    try:
        r = cliente.post("/api/listas/una-lista/lineas",
                         json={"nombre": "Leche", "producto_id": "dia:12345",
                               "cantidad": 1})
        assert r.status_code == 201, r.text
        assert llamado
    finally:
        main.app.dependency_overrides.clear()
