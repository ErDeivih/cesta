"""G03: revocar mide **la linea que se pulso**, no un contador.

Lo que el documento pide, literal: *«Fixture con al menos tres lineas: dos alternativas autorizadas y
una exacta. Pulsar revocar en una. Identificar la linea por ID estable. Verificar respuesta,
almacenamiento y pantalla: solo ella pierde. Recargar y comparar los tres estados.»* Y la correccion
de la revision: ***«un contador global de alternativas no acredita esto»***.

**Por que hacen falta tres y no dos.** Con dos alternativas, «revocar una» y «revocar cualquiera» dan
el mismo resultado y la prueba pasaria sin medir nada. La tercera -- la exacta, la que no necesita
sustitucion -- es la que distingue *esta* de *alguna*.

**Y por que se mide con `autorizacion_de`, que es un mapa por id.** Es la unica forma de decir «esta
linea dejo de estar aceptada **y las otras dos siguen como estaban**». Un numero de aceptadas antes y
despues no lo dice: bajar de 2 a 1 es compatible con haber revocado la equivocada.

La revocacion **ya existia** (`almacen.autoriza_linea(..., autorizado=False)`), y el diagnostico del
documento ya lo decia: *funcion existente, falta una medicion*. Esto es la medicion.

    $env:CESTA_POSTGRES='postgresql://cesta:prueba@127.0.0.1:5434/cesta'
    uv run pytest -q tests/test_g03_revocacion.py
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
    """El almacen real, y **otra vez despues del `lifespan`**: salir de un `TestClient` lo cierra."""
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
            usuario = f"revoca{int(time.time() * 1000) % 100000000}"
            r = preparacion.post("/api/registrarse",
                                 json={"nombre": "Prueba Revoca", "usuario": usuario, "clave": CLAVE})
            if r.status_code == 429:
                pytest.skip("no hay cuenta de prueba y el alta tiene limite por hora agotado")
            assert r.status_code == 201, r.text
            _CUENTA = usuario
    almacen.arranca(espera=10)
    yield
    main.app.dependency_overrides.clear()


@pytest.fixture()
def limpio():
    """**El almacen se vuelve a arrancar despues de cada prueba, porque salir del `with TestClient`
    lo cierra.** Es el mismo motivo que en `test_lista_de_casa_unica.py` y `test_g02_texto_libre.py`
    -- y este fichero nacio sin el, asi que la primera prueba pasaba y la segunda moria con
    `RuntimeError: el almacen no esta arrancado`. Medido el 11 de octubre de 2026."""
    yield
    main.app.dependency_overrides.clear()
    almacen.arranca(espera=10)


def _cliente() -> TestClient:
    cliente = TestClient(main.app)
    r = cliente.post("/api/entrar", json={"usuario": _CUENTA, "clave": CLAVE})
    assert r.status_code == 200, f"no se pudo entrar con {_CUENTA}: {r.status_code} {r.text}"
    return cliente


def _tres_lineas(cliente: TestClient) -> tuple[str, dict]:
    """**Dos alternativas autorizadas y una exacta**, con sus ids guardados.

    La exacta es una linea normal del catalogo: no se le acepta ninguna sustitucion. Las otras dos
    llevan producto y cadena aceptados, que es lo que las hace alternativas confirmadas.
    """
    lista = cliente.post("/api/listas", json={"nombre": "Prueba G03", "es_de_casa": False})
    assert lista.status_code in (200, 201), lista.text
    lista_id = lista.json()["id"]

    ids = {}
    for clave, grupo in (("alternativa_1", 6803), ("alternativa_2", 6804), ("exacta", 6805)):
        r = cliente.post(f"/api/listas/{lista_id}/lineas",
                         json={"nombre": f"Linea {clave}", "grupo_id": grupo, "cantidad": 1})
        assert r.status_code == 201, f"{clave}: {r.status_code} {r.text}"
        ids[clave] = r.json()["id"]

    # Las dos alternativas, autorizadas **con su producto y su cadena**.
    for clave, producto, cadena in (("alternativa_1", "prod-a", "alcampo"),
                                    ("alternativa_2", "prod-b", "aldi")):
        # **Los parametros van en la direccion, no en el cuerpo**: el endpoint los declara
        # `Query(default=...)` (`main.py:1217`), asi que un JSON se ignora en silencio y el almacen
        # contesta *«para autorizar hay que decir QUE producto se acepta»*. Medido el 11 de octubre
        # de 2026: mi primera version mandaba un cuerpo y recibia un 400 que parecia del dato.
        r = cliente.post(f"/api/listas/{lista_id}/lineas/{ids[clave]}/autorizar",
                         params={"autorizado": "true", "producto": producto, "cadena": cadena})
        assert r.status_code < 300, f"autorizar {clave}: {r.status_code} {r.text}"
    return lista_id, ids


def test_revocar_una_alternativa_deja_intactas_las_otras_dos(con_almacen, limpio):
    """**El nucleo del paquete.** Se revoca `alternativa_1` y se comparan los tres estados por id."""
    with _cliente() as cliente:
        lista_id, ids = _tres_lineas(cliente)

        antes = almacen.autorizacion_de(lista_id)
        assert antes[ids["alternativa_1"]]["autorizado"] is True, antes
        assert antes[ids["alternativa_2"]]["autorizado"] is True, antes
        assert not antes[ids["exacta"]]["autorizado"], f"la exacta no esta autorizada: {antes}"

        r = cliente.post(f"/api/listas/{lista_id}/lineas/{ids['alternativa_1']}/autorizar",
                         params={"autorizado": "false"})
        assert r.status_code < 300, r.text
        # **La respuesta nombra la linea que se toco**, que es lo que la revision exigia.
        cuerpo = r.text
        assert ids["alternativa_1"] in cuerpo, (
            f"la respuesta no identifica la linea revocada: {cuerpo[:200]}")

        despues = almacen.autorizacion_de(lista_id)
        assert not despues[ids["alternativa_1"]]["autorizado"], (
            f"la revocada sigue autorizada: {despues}")
        # **Y las otras dos, exactamente igual que antes.** Esto es lo que un contador no dice.
        assert despues[ids["alternativa_2"]]["autorizado"] is True, (
            f"se ha revocado la que no era: {despues}")
        assert not despues[ids["exacta"]]["autorizado"], despues


def test_revocar_una_linea_que_no_es_no_toca_ninguna(con_almacen, limpio):
    """**Y no se puede revocar por aproximacion**: un identificador que no es de esa lista no cambia
    nada. Si esto fallara, la revocacion estaria tocando por posicion o por parecido."""
    with _cliente() as cliente:
        lista_id, _ = _tres_lineas(cliente)
        antes = almacen.autorizacion_de(lista_id)

        r = cliente.post(f"/api/listas/{lista_id}/lineas/00000000-0000-0000-0000-000000000000/autorizar",
                         params={"autorizado": "false"})
        # El endpoint contesta lo que el almacen diga; lo que **no** puede es cambiar el estado.
        assert r.status_code in (200, 201, 404), r.text
        despues = almacen.autorizacion_de(lista_id)
        assert despues == antes, f"un id inexistente ha cambiado el estado: {antes} -> {despues}"


def test_el_estado_se_lee_de_la_base_y_sobrevive_a_una_lectura_nueva(con_almacen, limpio):
    """**Recargar y comparar los tres estados**: la lista, leida de nuevo, dice lo mismo."""
    with _cliente() as cliente:
        lista_id, ids = _tres_lineas(cliente)
        cliente.post(f"/api/listas/{lista_id}/lineas/{ids['alternativa_1']}/autorizar",
                     params={"autorizado": "false"})

        detalle = cliente.get(f"/api/listas/{lista_id}")
        assert detalle.status_code == 200, detalle.text
        por_id = {x["id"]: x for x in detalle.json().get("lineas", [])}
        assert len(por_id) == 3, f"esperaba tres lineas: {list(por_id)}"
        assert not por_id[ids["alternativa_1"]].get("autorizado"), por_id[ids["alternativa_1"]]
        assert por_id[ids["alternativa_2"]].get("autorizado") is True, por_id[ids["alternativa_2"]]
        assert not por_id[ids["exacta"]].get("autorizado"), por_id[ids["exacta"]]
