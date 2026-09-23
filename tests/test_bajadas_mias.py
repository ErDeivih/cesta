"""«Solo lo mio»: la cuarta pregunta, la unica que no tenia por donde contestarse.

Las cuatro preguntas con las que se abre la aplicacion (encargo de Claude, y la prueba
de aceptacion de la barra) son: que me falta y donde lo compro, esto que tengo en la mano
esta caro, voy tachando bien, y **ha bajado algo de lo mio**. Las tres primeras tenian
pantalla; la cuarta no: `/api/bajadas` contestaba *"que ha bajado en el catalogo"*, que no
es la pregunta. Una lista de sesenta bajadas del catalogo entero no dice si **lo tuyo** se
ha movido.

Lo que se fija aqui, y por que:

  - **El filtro se hace en SQL, no recortando la respuesta.** La consulta viene con un
    `LIMIT` de 60: filtrar en Python lo que ya viene recortado dejaria fuera bajadas mias
    que no estan entre las sesenta mayores del catalogo. Es la diferencia entre contestar
    la pregunta y contestar otra.
  - **Una lista vacia de grupos no es "sin filtro".** Son dos cosas distintas y se
    distinguen: `None` es "no me filtres", `[]` es "esta persona no tiene nada apuntado",
    y eso se contesta vacio sin consultar el catalogo.
  - **Sin sesion no se inventa un "tuyo".** `solo_mios` sin sesion no puede saber que es
    "lo mio", asi que se contesta lo del catalogo y se dice en la respuesta que no se
    filtro: un "tuyo" que no existe seria peor que no filtrar.

No hace falta PostgreSQL ni el catalogo del dia: la consulta a la base y la de precios se
sustituyen, y la fecha se fija. Una prueba que dependa del catalogo de hoy mide el
calendario, no el codigo.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from plataforma.api import almacen, catalogo, main, movimientos


@pytest.fixture
def casi(monkeypatch):
    """El cliente con la base y los precios sustituidos, y lo que llega al SQL."""
    visto: dict = {}

    def falsa(dias=7, cadenas=None, limite=60, subidas=False, grupos=None):
        visto["grupos"] = grupos
        visto["llamada"] = True
        return [{"grupo_id": 10, "nombre": "Leche entera", "cadena": "aldi",
                 "unidad": "l", "precio_unidad_cent": 96.0,
                 "precio_unidad_antes_cent": 120.0, "desde": "2026-09-16",
                 "variacion_pct": -20.0, "solo_con_tarjeta": False}]

    monkeypatch.setattr(movimientos, "bajadas", falsa)
    monkeypatch.setattr(catalogo, "fecha_de_gold", lambda: "2026-09-23")
    monkeypatch.setattr(almacen, "preferencias_de", lambda usuario_id: {})
    visto["llamada"] = False

    def con_sesion(mios=None):
        if mios is not None:
            monkeypatch.setattr(almacen, "mis_grupos", lambda usuario_id: list(mios))
        main.app.dependency_overrides[main.usuario_opcional] = lambda: {
            "id": "u1", "usuario": "ana", "nombre": "Ana"}
        return TestClient(main.app)

    yield con_sesion, visto
    main.app.dependency_overrides.clear()


def test_sin_solo_mios_no_se_filtra(casi):
    """El comportamiento de siempre: el catalogo, y `grupos=None` en el SQL."""
    con_sesion, visto = casi
    cliente = con_sesion()
    cuerpo = cliente.get("/api/bajadas").json()
    assert visto["grupos"] is None, "sin `solo_mios` no se filtra por nada"
    assert cuerpo["solo_mios"] is False
    assert cuerpo["resultados"][0]["grupo_id"] == 10


def test_solo_mios_pasa_mis_grupos_al_sql(casi):
    """Los grupos salen de mis listas y mis favoritos, y llegan a la consulta."""
    con_sesion, visto = casi
    cliente = con_sesion(mios=[10, 20, 30])
    cuerpo = cliente.get("/api/bajadas", params={"solo_mios": "true"}).json()
    assert visto["grupos"] == [10, 20, 30], (
        "el filtro no ha llegado al SQL: recortar la respuesta ya recortada dejaria "
        "fuera bajadas mias que no estan entre las sesenta mayores del catalogo")
    assert cuerpo["solo_mios"] is True
    assert cuerpo["resultados"][0]["grupo_id"] == 10


def test_sin_nada_apuntado_se_contesta_vacio_sin_mirar_el_catalogo(casi):
    """`[]` no es `None`: no hay "lo mio", asi que no hay bajadas mias."""
    con_sesion, visto = casi
    cliente = con_sesion(mios=[])
    cuerpo = cliente.get("/api/bajadas", params={"solo_mios": "true"}).json()
    assert cuerpo["resultados"] == []
    assert cuerpo["solo_mios"] is True
    assert visto["llamada"] is False, (
        "se ha consultado el catalogo entero para acabar devolviendo vacio")


def test_sin_sesion_no_se_inventa_un_tuyo(casi):
    """`solo_mios` sin sesion: lo del catalogo, y dicho en la respuesta."""
    con_sesion, visto = casi
    cliente = con_sesion()          # con sesion, pero el filtro no puede saber de quien
    main.app.dependency_overrides.clear()
    cuerpo = cliente.get("/api/bajadas", params={"solo_mios": "true"}).json()
    assert cuerpo["resultados"], "sin sesion se contesta el catalogo, no vacio"
    assert visto["grupos"] is None, "sin sesion no hay grupos que pasar"


def test_la_consulta_lleva_el_filtro_y_no_se_filtra_despues():
    """Lo que hace que el filtro sirva: esta **dentro** de la consulta.

    Si alguien lo moviera a una lista por comprension sobre el resultado, la prueba de
    arriba seguiria pasando (los grupos llegan igual) y el filtro dejaria de servir
    para nada. Por eso se mira el SQL.
    """
    import inspect

    fuente = inspect.getsource(movimientos.bajadas)
    assert "filtro_grupo" in fuente and "b.grupo_id IN (" in fuente, \
        "el filtro por grupo tiene que ir en el SQL, antes del LIMIT"
    # Y el LIMIT tiene que quedar despues del filtro en el texto de la consulta.
    assert fuente.index("b.grupo_id IN (") < fuente.index("LIMIT ?"), \
        "el filtro tiene que aplicarse antes de recortar a `limite` filas"
