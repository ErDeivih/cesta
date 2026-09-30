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


# --- La nota: `null` quiere decir "quitala" ----------------------------------
# Encontrado por la puerta de las funciones el 30 de septiembre de 2026: la pantalla
# vaciaba el campo, pulsaba Guardar, y la nota seguia escrita en la lista. El front
# mandaba `nota: null` y el servidor lo tomaba por un "no la toques", porque la
# comprobacion era `if nota is not None`. `cadena_elegida` ya usaba un centinela para
# distinguir "ausente" de "borralo"; la nota no. Esto lo fija en la ruta, que es donde
# se ve sin base de datos: que se le pasa al almacen cuando el movil manda cada cosa.


def _cliente_de_lineas(monkeypatch):
    """Cliente con el almacen espiado: devuelve (cliente, lo que le llega)."""
    visto: dict = {}

    def cambia(*a, **k):
        visto.clear()
        visto.update(k)
        return {"id": "l1"}

    monkeypatch.setattr(almacen, "cambia_linea", cambia)
    monkeypatch.setattr(main, "_acceso", lambda *a, **k: "dueno")
    monkeypatch.setitem(main.app.dependency_overrides, main.usuario_actual,
                        lambda: {"id": "u1", "usuario": "ana", "nombre": "Ana"})
    return TestClient(main.app), visto


def test_quitar_la_nota_se_le_dice_al_almacen(monkeypatch):
    """`nota: null` es "quitala", y tiene que llegar al almacen como tal."""
    cliente, visto = _cliente_de_lineas(monkeypatch)
    r = cliente.patch("/api/listas/una-lista/lineas/l1", json={"nota": None})
    assert r.status_code == 200, r.text
    assert visto["nota"] is None, (
        "con `nota: null` el almacen tiene que recibir None: si recibe el centinela, "
        "la nota se queda escrita y la pantalla miente")


def test_sin_mandar_la_nota_no_se_toca(monkeypatch):
    """El otro lado: no mandarla no es borrarla, o cambiar la cantidad la borraria."""
    cliente, visto = _cliente_de_lineas(monkeypatch)
    r = cliente.patch("/api/listas/una-lista/lineas/l1", json={"cantidad": 2})
    assert r.status_code == 200, r.text
    assert visto["nota"] is almacen.SIN_CAMBIAR, (
        "sin el campo `nota` el almacen no puede tocarla: cambiar la cantidad borraria "
        "la nota sin que nadie lo haya pedido")


def test_poner_la_nota_llega_entera(monkeypatch):
    cliente, visto = _cliente_de_lineas(monkeypatch)
    r = cliente.patch("/api/listas/una-lista/lineas/l1",
                      json={"nota": "2 bricks de los grandes"})
    assert r.status_code == 200, r.text
    assert visto["nota"] == "2 bricks de los grandes"
