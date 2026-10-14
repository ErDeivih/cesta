"""Anadir el mismo favorito dos veces no deja dos lineas, y la respuesta lo dice.

Un puente que se puede pulsar dos veces sin mirar es un puente en el que se puede confiar; uno que duplica obliga
a revisar la lista despues, que es justo lo que nadie hace de pie en la tienda.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from plataforma.api import main


def _monta(monkeypatch):
    """Almacen de mentira que **recuerda** lo anadido, para que la segunda llamada lo vea."""
    en_la_lista = []

    def anade(lista_id, usuario_id, linea_id, nombre, grupo_id=None, producto_id=None,
              cantidad=1, nota=None, cadena_elegida=None):
        fila = {"id": linea_id, "nombre_visto": nombre, "grupo_id": grupo_id, "producto_id": producto_id}
        en_la_lista.append(fila)
        return fila

    monkeypatch.setattr(main.almacen, "anade_linea", anade)
    monkeypatch.setattr(main.almacen, "lineas_de", lambda lista_id: list(en_la_lista))
    monkeypatch.setattr(main.catalogo, "grupo",
                        lambda grupo_id: {"grupo_id": grupo_id, "nombre": "Leche entera 1 l", "productos": []})
    monkeypatch.setattr(main, "_acceso", lambda *a, **k: "dueno")
    main.app.dependency_overrides[main.usuario_actual] = lambda: {
        "id": "u1", "usuario": "ana", "nombre": "Ana"}
    return en_la_lista, TestClient(main.app)


def test_la_segunda_vez_no_anade_nada_y_lo_dice(monkeypatch):
    en_la_lista, cliente = _monta(monkeypatch)
    primera = cliente.post("/api/listas/lo-que-sea/desde-favoritos", json={"grupo_ids": [1]}).json()
    segunda = cliente.post("/api/listas/lo-que-sea/desde-favoritos", json={"grupo_ids": [1]}).json()
    main.app.dependency_overrides.clear()
    assert len(en_la_lista) == 1, f"el puente ha dejado {len(en_la_lista)} lineas donde cabe una"
    assert primera.get("anadidos") == 1, primera
    assert segunda.get("anadidos") == 0, f"la segunda vez anadio {segunda.get('anadidos')}"
    assert segunda.get("ya_estaban") == 1, segunda


def test_lo_que_no_esta_se_sigue_anadiendo(monkeypatch):
    """Idempotente no es «no hacer nada»: lo nuevo entra."""
    en_la_lista, cliente = _monta(monkeypatch)
    cliente.post("/api/listas/lo-que-sea/desde-favoritos", json={"grupo_ids": [1]})
    segunda = cliente.post("/api/listas/lo-que-sea/desde-favoritos", json={"grupo_ids": [1, 2]}).json()
    main.app.dependency_overrides.clear()
    assert len(en_la_lista) == 2, en_la_lista
    assert segunda.get("anadidos") == 1 and segunda.get("ya_estaban") == 1, segunda


def test_la_segunda_vez_por_PRODUCTO_tampoco_duplica(monkeypatch):
    """**La rama de `producto_ids`, que no tenia NINGUN ensayo -- y por eso el fallo sobrevivio.**

    *Los dos ensayos de arriba usan `grupo_ids`, que era **la rama que estaba bien**. Y la de productos
    no tenia ninguno.*

    *`ya_en_la_lista` se construye con `(grupo_id, producto_id)`, asi que una linea **con producto y sin
    grupo** guarda `(None, producto_id)`. *Y la comprobacion de productos buscaba `(producto_id, None)`,
    **que no coincide con nada**: *asi que el mismo producto entraba **dos veces** -- *justo lo que el
    comentario de la ruta promete que no pasa: **«pulsar dos veces el mismo favorito no puede dejar dos
    lineas»**.*

    **Lo que se fija aqui**: *pulsar dos veces el mismo producto deja **una** linea, y la segunda vez lo
    dice.*
    """
    en_la_lista, cliente = _monta(monkeypatch)
    monkeypatch.setattr(main.catalogo, "producto",
                        lambda pid: {"producto_id": pid, "nombre": "Leche entera 1 l"})
    primera = cliente.post("/api/listas/lo-que-sea/desde-favoritos",
                           json={"producto_ids": ["dia:1"]}).json()
    segunda = cliente.post("/api/listas/lo-que-sea/desde-favoritos",
                           json={"producto_ids": ["dia:1"]}).json()
    main.app.dependency_overrides.clear()
    assert len(en_la_lista) == 1, f"el puente ha dejado {len(en_la_lista)} lineas donde cabe una"
    assert primera.get("anadidos") == 1, primera
    assert segunda.get("anadidos") == 0, f"la segunda vez anadio {segunda.get('anadidos')}"
    assert segunda.get("ya_estaban") == 1, segunda
    # *Y la linea es de PRODUCTO, sin grupo: es lo que hace que su tupla sea `(None, producto_id)`.*
    assert en_la_lista[0]["producto_id"] == "dia:1", en_la_lista[0]
    assert en_la_lista[0]["grupo_id"] is None, en_la_lista[0]
