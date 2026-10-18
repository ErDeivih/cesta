"""G03: el cierre. Revocar cambia el precio que se **archiva**, no solo una columna.

**Por que esta puerta importa mas que las otras dos.** La estimacion y el reparto se recalculan cada
vez: si se equivocan, se ven y se corrigen. **El cierre no.** Lo que se guarda al cerrar una compra
queda en `compra_linea.importe_cent` -- la columna de la migracion 013 -- y *una compra de hace un mes
no se puede volver a explicar con los precios de hoy*. **Si una linea revocada se archiva con el
precio de la sustitucion que se dejo de aceptar, esa compra miente para siempre.**

**Y el caso lo eligio el catalogo, no yo.** Medido el 11 de octubre de 2026 sobre el grupo **6803**:

    exacto en alcampo 518   ·   exacto en aldi 299   ·   exacto en dia 260
    ALTERNATIVA en alcampo 518  («Tortilla de patata con cebolla caramelizada PA»)

**La alternativa cuesta lo mismo que el exacto de su cadena** -- es el producto de esa cadena, en el
mismo pasillo -- asi que **una prueba con el precio igual no demostraria nada**.

**Y hay que decirlo entero, porque la version anterior de este parrafo prometia una diferencia que
aqui no se puede ver**: decia que *«revocada, la linea no tiene nada aceptado y coge el mas barato de
hoy: dia, 260»*. **No.** Este fixture **decide la tienda** (`POST /lineas/{id}/tienda`), y con la
tienda decidida la eleccion no cae al mas barato: revocar tambien archiva `alcampo` a **518**.
*Medido el 13 de octubre de 2026.*

**Y en `alcampo` hay un solo candidato para el grupo 6803, que ocupa las dos casillas** -- la
principal y la de alternativa, las dos con `alcampo:202841` a 518 --: *en esa tienda no hay dos
productos que distinguir.* **Es un limite del fixture, no del motor.** La prueba que si discrimina la
sustitucion esta en `tests/test_fase2_f01_sustitucion.py`, con un catalogo controlado donde A y B
difieren en precio y en oferta.

    $env:CESTA_POSTGRES='postgresql://cesta:prueba@127.0.0.1:5434/cesta'
    uv run pytest -q tests/test_g03_cierre.py
"""
from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

from plataforma.api import almacen, main

BASE = "postgresql://cesta:prueba@127.0.0.1:5434/cesta"
CLAVE = "clave-de-prueba-123"
_CUENTA: str | None = None

# **El caso, del catalogo.** Grupo 6803 con la tienda decidida en alcampo, y la sustitucion que el
# motor propone ahi. Los numeros son los medidos: 518 en alcampo, 260 en dia.
GRUPO = 6803
TIENDA = "alcampo"
PRODUCTO_ALTERNATIVA = "alcampo:202841"
PRECIO_CON_ALTERNATIVA = 518
PRECIO_SIN_ALTERNATIVA = 260


@pytest.fixture(scope="module")
def con_almacen():
    global _CUENTA
    try:
        almacen.arranca(espera=10)
        # *** Y QUE EL CATALOGO DE REFERENCIA ESTE, *o se salta diciendolo*. ***
        # *Estas pruebas usan constantes MEDIDAS del catalogo real de casa:*
        # *GRUPO=6803, TIENDA=alcampo, 518 y 260.* *En una base sintetica ese grupo no existe, y antes
        # pasaba una de dos cosas: se saltaba sin decir por que, o fallaba en compania de otra prueba
        # que sembraba un catalogo distinto -- y parecia una dependencia de orden, que no lo era.*
        # *Ahora se comprueba el grupo y, si no esta, se salta con el motivo escrito.*
        try:
            with almacen.cursor() as _cur:
                _cur.execute("SELECT count(*) AS n FROM grupos WHERE grupo_id = %s", (GRUPO,))
                _hay = _cur.fetchone()["n"]
        except Exception:  # noqa: BLE001
            _hay = 0
        if not _hay:
            pytest.skip(
                f"estas pruebas necesitan el catalogo de casa (grupo {GRUPO}); en una base "
                f"sintetica no existe. Sembrarlo, o correrlas contra una copia del catalogo.")
    except Exception as fallo:  # noqa: BLE001
        pytest.skip(f"sin almacen en CESTA_POSTGRES al importar. Ejecuta con "
                    f"$env:CESTA_POSTGRES='{BASE}' | {type(fallo).__name__}: {fallo}")
    with TestClient(main.app) as preparacion:
        for candidata in ("prueba-navegador", "recibo-de-prueba"):
            if preparacion.post("/api/entrar",
                                json={"usuario": candidata, "clave": CLAVE}).status_code == 200:
                _CUENTA = candidata
                break
        else:
            usuario = f"cierre{int(time.time() * 1000) % 100000000}"
            r = preparacion.post("/api/registrarse",
                                 json={"nombre": "Prueba Cierre", "usuario": usuario, "clave": CLAVE})
            if r.status_code == 429:
                pytest.skip("no hay cuenta de prueba y el alta tiene limite por hora agotado")
            assert r.status_code == 201, r.text
            _CUENTA = usuario
    almacen.arranca(espera=10)
    yield
    main.app.dependency_overrides.clear()


@pytest.fixture()
def limpio():
    """El almacen se vuelve a arrancar: salir del `with TestClient` lo cierra."""
    yield
    main.app.dependency_overrides.clear()
    almacen.arranca(espera=10)


def _cliente() -> TestClient:
    cliente = TestClient(main.app)
    r = cliente.post("/api/entrar", json={"usuario": _CUENTA, "clave": CLAVE})
    assert r.status_code == 200, f"no se pudo entrar con {_CUENTA}: {r.status_code} {r.text}"
    return cliente


def _compra_cerrada(cliente: TestClient, *, con_alternativa: bool,
                    nombre_de_la_linea: str = "Tortilla de patata") -> dict:
    """Una lista con la linea, su tienda decidida, la sustitucion aceptada o no, y la compra cerrada.

    Devuelve lo que se **archivo**: la cadena y el precio de cada linea de la compra.
    """
    lista = cliente.post("/api/listas", json={"nombre": "Prueba G03 cierre", "es_de_casa": False})
    assert lista.status_code in (200, 201), lista.text
    lista_id = lista.json()["id"]

    linea = cliente.post(f"/api/listas/{lista_id}/lineas",
                         json={"nombre": nombre_de_la_linea, "grupo_id": GRUPO, "cantidad": 1})
    assert linea.status_code == 201, linea.text
    linea_id = linea.json()["id"]

    # La tienda, decidida: es lo que hace que se guarde **el precio de esa tienda** y no el mas barato.
    puesta = cliente.post(f"/api/listas/{lista_id}/tienda",
                          json={"linea_id": linea_id, "cadena": TIENDA})
    assert puesta.status_code < 300, f"poner la tienda: {puesta.status_code} {puesta.text}"

    if con_alternativa:
        # **Los parametros van en la direccion**, no en el cuerpo (`main.py:1217`).
        aut = cliente.post(f"/api/listas/{lista_id}/lineas/{linea_id}/autorizar",
                           params={"autorizado": "true", "producto": PRODUCTO_ALTERNATIVA,
                                   "cadena": TIENDA})
        assert aut.status_code < 300, f"autorizar: {aut.status_code} {aut.text}"

    # Al carro, que es lo que el cierre archiva.
    carro = cliente.patch(f"/api/listas/{lista_id}/lineas/{linea_id}", json={"en_carrito": True})
    assert carro.status_code < 300, carro.text
    cierre = cliente.post(f"/api/listas/{lista_id}/cerrar", json={})
    assert cierre.status_code < 300, f"cerrar: {cierre.status_code} {cierre.text}"

    compras = almacen.compras_de(lista_id, limite=1)
    assert compras, "el cierre no ha dejado compra"
    archivadas = almacen.lineas_de_compra(str(compras[0]["compra_id"]))
    assert len(archivadas) == 1, f"esperaba una linea archivada: {archivadas}"
    return archivadas[0]


def test_con_la_sustitucion_aceptada_se_archiva_el_precio_de_su_tienda(con_almacen, limpio):
    """**El caso de referencia.** Sin esto, la prueba de la revocacion no significaria nada."""
    with _cliente() as cliente:
        guardada = _compra_cerrada(cliente, con_alternativa=True)
        assert guardada.get("cadena") == TIENDA, guardada
        assert guardada.get("precio_cent") == PRECIO_CON_ALTERNATIVA, (
            f"con la sustitucion de {TIENDA} aceptada se archiva su precio: {guardada}")


def test_el_cierre_archiva_el_producto_que_puso_el_precio(con_almacen, limpio):
    """**La identidad que faltaba**, y el limite medido de este fixture.

    Antes de F01 el cierre escribia `lista_linea.producto_id`. Con una linea que pide **solo grupo**
    -- que es este caso -- eso es **NULL**: *la compra no guardaba **que** producto le habia puesto el
    precio, y el historico quedaba sin identidad.* Ahora guarda el que de verdad lo puso.

    **Y aqui esta el limite de este fixture, medido y no supuesto** (13 de octubre de 2026, grupo 6803):
    en `alcampo` hay **un solo candidato**, y no es exacto, asi que ocupa **las dos casillas** de
    `_candidatos`:

        clave=(6803, 'alcampo')                 pid=alcampo:202841  precio=518  exacta=False
        clave=(6803, 'alcampo', 'alternativa')  pid=alcampo:202841  precio=518  exacta=False

    *Asi que aceptar la sustitucion y no aceptarla archivan **el mismo producto, la misma tienda y el
    mismo precio** -- no por una regla, sino porque en esa tienda no hay dos productos que distinguir.*
    **Por eso esta prueba no puede discriminar el defecto de F01**, y la que si lo hace es
    `tests/test_fase2_f01_sustitucion.py`, con un catalogo controlado donde A y B difieren en precio y
    en oferta. *Se deja escrito para que nadie vuelva a creer que esta puerta cubre la sustitucion.*

    *La prueba que estaba aqui se llamaba «el cierre archiva el producto del grupo no el sustituto»,
    **pasaba antes y despues del arreglo**, y de un caso que no puede distinguir sacaba la conclusion
    general de que «el cierre es de precios y guarda lo que se compro» -- que es justo lo que el
    escenario del encargo refuta. Se sustituye, no se borra.*
    """
    with _cliente() as cliente:
        con = _compra_cerrada(cliente, con_alternativa=True)
        sin = _compra_cerrada(cliente, con_alternativa=False)

    # **Lo que si se prueba aqui**: el cierre archiva el producto que puso el precio.
    assert con.get("producto_id") == PRODUCTO_ALTERNATIVA, con
    assert sin.get("producto_id"), (
        f"una linea de grupo tambien tiene que archivar QUE producto se precio: {sin}")

    # El precio y la tienda, los de la tienda decidida: la sustitucion no los mueve **aqui**.
    assert con.get("precio_cent") == sin.get("precio_cent") == PRECIO_CON_ALTERNATIVA, (con, sin)
    assert con.get("cadena") == sin.get("cadena") == TIENDA, (con, sin)

    # Y `producto_pedido_id` queda NULL: la linea pedia **grupo**, no un producto concreto, asi que no
    # hay dos cosas que distinguir. *Se guarda solo cuando lo pedido y lo comprado difieren.*
    assert con.get("producto_pedido_id") is None, con
    assert sin.get("producto_pedido_id") is None, sin


def test_una_linea_movida_se_archiva_sin_precio_y_no_con_el_de_otro(con_almacen, limpio):
    """**Donde el cierre SI tiene algo que demostrar.** Y lo demuestra.

    Una linea movida es la que dice un nombre que **ya no es** el de ningun producto de su grupo
    (`catalogo.lineas_movidas`): el sintoma de que `grupo_id` es un ordinal que se renumera. Medido el
    28 de septiembre de 2026 con datos de casa: *la leche entera salia en el pasillo de higiene y
    belleza, con el precio del pintalabios*.

    Lo que **no puede** pasar es que se archive con el precio de otro producto. Y lo que pasa es
    `precio_cent` en **NULL**, que va a `sin_precio`: *un cero ahi seria afirmar que salio gratis*.
    Se prueba con la autorizacion puesta y sin ella, porque **tampoco aqui hay sustituto que usar**.
    """
    with _cliente() as cliente:
        for con_alternativa in (True, False):
            guardada = _compra_cerrada(cliente, con_alternativa=con_alternativa,
                                       nombre_de_la_linea="Pintalabios REVLON")
            assert guardada.get("precio_cent") is None, (
                f"una linea movida no puede llevar el precio de otro producto "
                f"(autorizada={con_alternativa}): {guardada}")
            assert guardada.get("importe_cent") is None, guardada


# --- F01 (fase 2): el producto efectivo comprado, por HTTP y contra PostgreSQL -------------------
#
# **El escenario del encargo, con el catalogo real.** La persona **pide un producto concreto** -- que
# es lo que hace que haya algo que sustituir -- y acepta la alternativa que el motor ofrece en una
# tienda. Medido el 13 de octubre de 2026 sobre el grupo 6803:
#
#     la linea pide            dia:262522          («el producto que quiero»)
#     en alcampo el grupo tiene alcampo:202841  518 c
#     y se acepta              alcampo:202841 en alcampo
#
# **Y hay que decir que esta prueba discrimina la IDENTIDAD, no el precio.** En el catalogo de hoy
# **no existe ni un solo par (grupo, tienda) con dos GTIN distintos** -- medido ese dia: **0** --, asi
# que el precio de la alternativa coincide con el del candidato principal de esa tienda. *Lo que si
# cambia, y es lo grave, es **que producto queda en el historico**: antes del arreglo se guardaba
# `producto_id = dia:262522`, el pedido; ahora se guarda el aceptado.*
PEDIDO_REAL = "dia:262522"
ACEPTADO_REAL = "alcampo:202841"
PRECIO_REAL = 518


def test_la_compra_archiva_el_producto_aceptado_cuando_la_linea_pide_otro(con_almacen, limpio):
    """**F01, por HTTP y contra la base de verdad.** *El nivel que el motor en memoria no alcanza.*

    Y el caso que el fixture de arriba **no puede** montar: alli la linea pedia **solo grupo**, asi que
    no habia pedido del que distinguir la sustitucion. **Aqui se pide un producto concreto.**
    """
    with _cliente() as cliente:
        lista = cliente.post("/api/listas", json={"nombre": "Prueba F01 sustitucion",
                                                  "es_de_casa": False})
        assert lista.status_code in (200, 201), lista.text
        lista_id = lista.json()["id"]

        # **Se pide un producto concreto**, no el grupo: sin eso no hay nada que sustituir.
        linea = cliente.post(f"/api/listas/{lista_id}/lineas",
                             json={"nombre": "Tortilla de patata", "grupo_id": GRUPO,
                                   "producto_id": PEDIDO_REAL, "cantidad": 3})
        assert linea.status_code == 201, linea.text
        linea_id = linea.json()["id"]

        puesta = cliente.post(f"/api/listas/{lista_id}/tienda",
                              json={"linea_id": linea_id, "cadena": TIENDA})
        assert puesta.status_code < 300, puesta.text

        aut = cliente.post(f"/api/listas/{lista_id}/lineas/{linea_id}/autorizar",
                           params={"autorizado": "true", "producto": ACEPTADO_REAL,
                                   "cadena": TIENDA})
        assert aut.status_code < 300, f"autorizar: {aut.status_code} {aut.text}"

        carro = cliente.patch(f"/api/listas/{lista_id}/lineas/{linea_id}",
                              json={"en_carrito": True})
        assert carro.status_code < 300, carro.text
        cierre = cliente.post(f"/api/listas/{lista_id}/cerrar", json={})
        assert cierre.status_code < 300, f"cerrar: {cierre.status_code} {cierre.text}"

        compras = almacen.compras_de(lista_id, limite=1)
        assert compras, "el cierre no ha dejado compra"
        guardada = almacen.lineas_de_compra(str(compras[0]["compra_id"]))[0]

    # **El producto que se compro**, no el que se pidio. Es la diferencia que F01 arregla.
    assert guardada.get("producto_id") == ACEPTADO_REAL, (
        f"se acepto {ACEPTADO_REAL} y el historico tiene que decir eso, no el pedido: {guardada}")
    # **Y el pedido no se pierde**: queda guardado aparte, para poder explicar la compra despues.
    assert guardada.get("producto_pedido_id") == PEDIDO_REAL, guardada
    # La tienda, la cantidad y el importe, los de la eleccion efectiva.
    assert guardada.get("cadena") == TIENDA, guardada
    assert guardada.get("cantidad") == 3, guardada
    assert guardada.get("precio_cent") == PRECIO_REAL, guardada
    assert guardada.get("importe_cent") == 3 * PRECIO_REAL, guardada
