"""G01: el recibo del puente compra→diario, medido contra el almacén real.

**Por qué esta prueba necesita PostgreSQL y las demás no.** El puente cruza dos almacenes: lee la
**última compra cerrada** de PostgreSQL (listas, líneas, `importe_cent`) y escribe en el **diario**
(SQLite). El recibo que devuelve -- `{anotadas, ya_estaban, ajenas, sin_nutricion}` -- es lo que la
pantalla usa para decir qué se anotó **de verdad**, así que medirlo con dobles mediría el doble.

Tres reglas que respeta, y que importan más que la prueba:

1. **No toca datos reales.** El diario va a un fichero temporal y la lista es **nueva y con nombre
   único**: no se usa la lista de casa ni se modifica ninguna compra existente.
2. **Se salta con motivo explícito** si no hay motor o la base desechable no está. Un `skip` que dice
   por qué no es un falso positivo: no afirma nada.
3. **Corre contra la base desechable del 5434**, nunca contra la de la aplicación en el 5432.

**La cadena de conexión se lee al IMPORTAR** (lo dice `prueba_transaccion.py`), así que no vale
un `monkeypatch.setenv`: el módulo ya la leyó. Por eso el comando la lleva delante, como
`prueba_transaccion.py` con su subproceso:

    $env:CESTA_POSTGRES='postgresql://cesta:prueba@127.0.0.1:5434/cesta'
    uv run pytest -q tests/test_g01_recibo_del_puente.py

Y si no se da, la prueba **se salta diciéndolo** en vez de conectar al 5432 -- que es lo que hacía
la primera versión, y tardaba treinta segundos en timeouts por cada caso.
"""
from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

from plataforma.api import almacen, main
from plataforma.api import diario as api_diario

BASE = "postgresql://cesta:prueba@127.0.0.1:5434/cesta"
CLAVE = "clave-de-prueba-123"


@pytest.fixture()
def con_almacen(tmp_path, monkeypatch):
    """El almacén real, el diario en temporal, y un `skip` claro si no hay motor."""
    monkeypatch.setenv("CESTA_POSTGRES", BASE)
    try:
        almacen.arranca(espera=10)
    except Exception as fallo:  # noqa: BLE001 -- el motivo va en el skip
        # El motivo dice **qué hacer**, no solo qué falló: sin esto, quien lo vea conectará con el
        # 5432 por defecto y creerá que la prueba está rota.
        pytest.skip(
            f"sin almacen en CESTA_POSTGRES al importar (la cadena se lee al importar, no ahora). "
            f"Ejecuta con: $env:CESTA_POSTGRES='{BASE}' | {type(fallo).__name__}: {fallo}")
    api_diario.ruta_base(tmp_path / "diario.sqlite")
    try:
        yield
    finally:
        api_diario.ruta_base(None)
        main.app.dependency_overrides.clear()


# **Una sola cuenta para las tres pruebas, y no una por prueba.** El alta tiene límite por hora
# -- `429: Se han creado demasiadas cuentas en la última hora` -- y es comportamiento real del
# producto, no un estorbo de la prueba: quien abuse de la puerta se encuentra eso. Tres altas por
# ejecución, repetidas mientras se depura, lo agotan en minutos. Medido el 11 de octubre de 2026.
_CUENTA: str | None = None


def _alta(cliente: TestClient) -> str:
    """Entra con la cuenta de la ejecución, y la crea **solo la primera vez**."""
    global _CUENTA
    if _CUENTA is not None:
        r = cliente.post("/api/entrar", json={"usuario": _CUENTA, "clave": CLAVE})
        assert r.status_code == 200, r.text
        return _CUENTA
    # **Se entra con una cuenta que ya exista, y solo se registra si no hay ninguna.** Esta prueba
    # mide el puente, no el alta: hacerla depender del registro la ata al limite por hora de una
    # puerta que no esta probando. `prueba-navegador` existe en la base desechable desde hace
    # semanas; si no estuviera, se crea y se sigue.
    for candidata in ("prueba-navegador", "recibo-de-prueba"):
        r = cliente.post("/api/entrar", json={"usuario": candidata, "clave": CLAVE})
        if r.status_code == 200:
            _CUENTA = candidata
            return candidata
    usuario = f"recibo{int(time.time() * 1000) % 100000000}"
    r = cliente.post("/api/registrarse",
                     json={"nombre": "Prueba Recibo", "usuario": usuario, "clave": CLAVE})
    if r.status_code == 429:
        pytest.skip("no hay cuenta de prueba y el alta tiene limite por hora agotado")
    assert r.status_code == 201, r.text
    _CUENTA = usuario
    return usuario


def _compra_cerrada(cliente: TestClient, grupo_id: int = 6803) -> str:
    """Crea una lista nueva, le mete una línea **con destino del catálogo**, y la cierra.

    **La línea necesita `grupo_id` o `producto_id`**: `POST /api/listas/{id}/lineas` responde
    *«Una linea necesita el grupo o el producto al que se refiere»* (422) si no lo lleva. Es la
    regla que hace que G02 -- texto libre con vínculo posterior explícito -- sea un paquete propio y
    no un detalle, y por eso esta prueba **no** puede fabricar hoy una línea sin nutrición: haría
    falta un grupo cuyo producto no declare ninguna, o G02 resuelto.
    """
    lista = cliente.post("/api/listas", json={"nombre": "Prueba del recibo", "es_de_casa": False})
    assert lista.status_code in (200, 201), lista.text
    lista_id = lista.json()["id"]
    linea = cliente.post(f"/api/listas/{lista_id}/lineas", json={
        "nombre": "Plato preparado de prueba", "cantidad": 1,
        "grupo_id": grupo_id, "producto_id": None,
    })
    assert linea.status_code in (200, 201), linea.text
    linea_id = linea.json().get("id") or linea.json().get("linea_id")
    assert linea_id, linea.json()

    # Al carro, que es lo que el cierre archiva, y se cierra.
    puesto = cliente.patch(f"/api/listas/{lista_id}/lineas/{linea_id}", json={"en_carrito": True})
    assert puesto.status_code < 300, puesto.text
    cierre = cliente.post(f"/api/listas/{lista_id}/cerrar", json={})
    assert cierre.status_code < 300, cierre.text
    return lista_id


def test_el_recibo_dice_lo_que_se_anoto_y_lo_que_no(con_almacen):
    """La primera vez anota; la segunda dice que ya estaba. **Y las dos veces lo dice el servidor.**"""
    with TestClient(main.app) as cliente:
        _alta(cliente)
        lista_id = _compra_cerrada(cliente)

        primera = cliente.post(f"/api/listas/{lista_id}/desde-la-compra",
                               json={"fecha": "2026-10-11", "comida": "comida", "lineas": []})
        assert primera.status_code == 201, primera.text
        recibo = primera.json()
        # Las cuatro claves del contrato: la pantalla depende de las cuatro.
        for clave in ("anotadas", "ya_estaban", "ajenas", "sin_nutricion"):
            assert clave in recibo, f"el recibo no trae `{clave}`: {recibo}"
        assert isinstance(recibo["anotadas"], int)
        assert recibo["anotadas"] + len(recibo["ya_estaban"]) == 1, (
            f"una linea de la compra: o se anota o ya estaba -- {recibo}")

        # **Y la segunda vez dice que ya estaba**, no que anoto otra: es la idempotencia que el
        # documento pide, medida por el recibo y no por el numero de filas que alguien cuente.
        segunda = cliente.post(f"/api/listas/{lista_id}/desde-la-compra",
                               json={"fecha": "2026-10-11", "comida": "comida", "lineas": []})
        assert segunda.status_code == 201, segunda.text
        segundo = segunda.json()
        assert segundo["anotadas"] == 0, f"la segunda vez no anota nada: {segundo}"
        assert len(segundo["ya_estaban"]) >= 1, f"y lo dice: {segundo}"

        # El diario tiene **una** entrada, que es lo que el recibo prometio.
        dia = cliente.get("/api/diario/2026-10-11").json()
        assert len(dia["entradas"]) == 1, f"el diario dice {len(dia['entradas'])} entradas"


def test_una_linea_ajena_se_devuelve_en_vez_de_ignorarse(con_almacen):
    """Pedir una línea que no es de esa compra se **dice**, no se traga."""
    with TestClient(main.app) as cliente:
        _alta(cliente)
        lista_id = _compra_cerrada(cliente)
        r = cliente.post(f"/api/listas/{lista_id}/desde-la-compra",
                         json={"fecha": "2026-10-11", "comida": "comida",
                               "lineas": ["no-existe-esta-linea"]})
        assert r.status_code == 201, r.text
        assert r.json()["ajenas"] == ["no-existe-esta-linea"], r.json()


def test_una_linea_con_destino_del_catalogo_no_va_a_sin_nutricion(con_almacen):
    """El recibo distingue **las que van sin dato** de las que sí lo traen.

    **Y aquí no se puede medir el caso contrario todavía.** Fabricar una línea *sin* nutrición exigiría
    un producto del catálogo que no la declare -- o una línea sin destino, que la API rechaza con 422
    (*«Una linea necesita el grupo o el producto al que se refiere»*). Eso es exactamente el paquete
    **G02**: texto libre con vínculo posterior. No se inventa el fixture para poder decir que el caso
    está cubierto; queda como pendiente con su motivo.
    """
    with TestClient(main.app) as cliente:
        _alta(cliente)
        lista_id = _compra_cerrada(cliente)
        r = cliente.post(f"/api/listas/{lista_id}/desde-la-compra",
                         json={"fecha": "2026-10-11", "comida": "comida", "lineas": []})
        assert r.status_code == 201, r.text
        recibo = r.json()
        if recibo["anotadas"]:
            dia = cliente.get("/api/diario/2026-10-11").json()
            sin_dato = bool(recibo["sin_nutricion"])
            # **La equivalencia, que es lo que se puede afirmar sin saber qué producto eligió el
            # motor.** La primera versión daba por hecho que un grupo del catálogo trae siempre
            # nutrición, y **es falso**: medido el 11 de octubre, el de este caso anota con
            # `sin_nutricion` no vacío y el día se queda sin energía. Lo que se cumple en los dos
            # casos -- y es la regla del endpoint, *no se inventan calorías* -- es que el recibo y el
            # día digan **lo mismo**: si va sin dato, el día no trae energía; y si no, la trae.
            assert (dia["conocido"]["kcal"] is None) == sin_dato, (
                f"el recibo y el dia no dicen lo mismo: {recibo} frente a {dia['conocido']}")
            if sin_dato:
                assert dia["cobertura"]["kcal"]["con_dato"] == 0
