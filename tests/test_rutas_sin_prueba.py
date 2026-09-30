"""Las rutas que la API servia sin que ninguna prueba las llamara.

Medido el 30 de septiembre de 2026: de las 46 rutas de `plataforma/api/main.py`, **siete no las
tocaba ninguna prueba** -- `/api/favoritos` (las tres), `/api/preferencias`, `/api/producto/{cadena}/{id_fuente}`,
`/api/invitacion/{codigo}` y `/api/salud`. Lo encontro `data/debug/rutas_sin_prueba.py`, que saca
las rutas del fichero y busca cada una en `tests/` por su ruta o por el nombre de su funcion.

Lo que ese instrumento mide es **que nadie las llama**, no que su comportamiento este sin
comprobar: `/api/favoritos` tiene `test_favoritos_orden.py`, que fija el orden, pero el orden vive
en `_orden_de_favoritos` y la ruta --la forma de lo que sale, la ventana de dias, el favorito que
ya no esta-- no la habia mirado nadie. Es la diferencia entre probar la cuenta y probar el
mostrador.

Estas pruebas van por HTTP, con el almacen sustituido: **en `tests/` no hay PostgreSQL** (esa
parte la ejecuta `plataforma/prueba_e2e.py` contra una base desechable). Lo que se comprueba aqui
es la parte que no necesita base: que la ruta exista, que conteste lo que promete, que la sesion
se pida donde hay que pedirla y que lo que llega al almacen sea lo que se pidio.

La sesion se sustituye con `monkeypatch.setitem`, que la deja como estaba al terminar la prueba.
`test_lineas_api.py` la escribe a mano en el diccionario global de dependencias y necesita
`try/finally` para no dejarla puesta; con `setitem` no hace falta.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from plataforma.api import almacen, catalogo, main, movimientos


def _cliente(monkeypatch, usuario: dict | None = None) -> TestClient:
    """El cliente con la sesion resuelta, salvo que se pida sin sesion."""
    if usuario is not None:
        monkeypatch.setitem(main.app.dependency_overrides, main.usuario_actual,
                            lambda: usuario)
    return TestClient(main.app)


ANA = {"id": "u1", "usuario": "ana", "nombre": "Ana"}


# --- /api/salud: la unica que no pide sesion --------------------------------

def test_salud_contesta_sin_sesion_y_dice_de_que_dia_son_los_datos(monkeypatch):
    """Es la que mira el vigilante de fuera: si pidiera sesion, no valdria para eso."""
    monkeypatch.setattr(catalogo, "fecha_de_gold", lambda: "2026-09-30")
    r = TestClient(main.app).get("/api/salud")
    assert r.status_code == 200, r.text
    assert r.json() == {"vivo": True, "fecha_datos": "2026-09-30"}


# --- /api/producto/{cadena}/{id_fuente}: la puerta de la extension ----------

def test_la_ficha_se_pide_con_el_id_de_la_cadena(monkeypatch):
    """Lo unico que se puede sacar de la URL de un supermercado es su propio id."""
    pedido: dict = {}

    def producto(pid):
        pedido["pid"] = pid
        return {"producto_id": pid, "nombre": "Leche entera 1 L", "grupo_id": 7,
                "fuente": "dia", "marca": "DIA", "unidad": "1 L",
                "precio_cent": 95, "precio_unidad_cent": 95, "imagen": None}

    monkeypatch.setattr(catalogo, "producto", producto)
    monkeypatch.setattr(catalogo, "grupo",
                        lambda gid: {"grupo_id": gid, "productos": [], "ahorro_pct": None})
    monkeypatch.setattr(catalogo, "fecha_de_gold", lambda: "2026-09-30")
    r = _cliente(monkeypatch, ANA).get("/api/producto/dia/12345")
    assert r.status_code == 200, r.text
    assert pedido["pid"] == "dia:12345", (
        "la cadena y el id tienen que juntarse como `fuente:id_fuente`, que es como "
        "se llaman los productos dentro de la casa")
    assert r.json()["grupo"]["grupo_id"] == 7, "falta el grupo: es la comparacion"


def test_un_producto_que_no_tengo_contesta_404(monkeypatch):
    monkeypatch.setattr(catalogo, "producto", lambda pid: None)
    r = _cliente(monkeypatch, ANA).get("/api/producto/aldi/999")
    assert r.status_code == 404
    assert "No tengo ese producto" in r.json()["detail"]


# --- /api/invitacion/{codigo} -----------------------------------------------

def test_aceptar_una_invitacion_devuelve_lo_que_contesta_el_almacen(monkeypatch):
    monkeypatch.setattr(almacen, "acepta_invitacion",
                        lambda codigo, uid: {"lista_id": "l1", "papel": "escribe",
                                             "codigo": codigo})
    r = _cliente(monkeypatch, ANA).post("/api/invitacion/ABC123")
    assert r.status_code == 200, r.text
    assert r.json() == {"lista_id": "l1", "papel": "escribe", "codigo": "ABC123"}


def test_una_invitacion_que_ya_no_vale_lo_dice_con_su_motivo(monkeypatch):
    """`None` del almacen es "caducada o usada", y la frase tiene que decirlo."""
    monkeypatch.setattr(almacen, "acepta_invitacion", lambda codigo, uid: None)
    r = _cliente(monkeypatch, ANA).post("/api/invitacion/VIEJA")
    assert r.status_code == 404
    detalle = r.json()["detail"]
    assert "siete dias" in detalle and "Pidele otro" in detalle


# --- /api/favoritos: lo que se sigue, y como sale ---------------------------

def _grupo(gid, nombre="Leche entera 1 L", cadena="dia", precio=95):
    return {"grupo_id": gid, "ahorro_pct": 12.0,
            "productos": [{"producto_id": f"{cadena}:{gid}", "nombre": nombre,
                           "marca": "DIA", "unidad": "1 L", "precio_cent": precio,
                           "precio_unidad_cent": precio, "fuente": cadena,
                           "imagen": None}]}


def test_los_favoritos_llegan_con_su_nombre_su_precio_y_su_cambio(monkeypatch):
    monkeypatch.setattr(almacen, "favoritos_de",
                        lambda uid: [{"grupo_id": 7, "producto_id": None,
                                      "anadido_en": "2026-09-20"}])
    monkeypatch.setattr(catalogo, "grupo", lambda gid: _grupo(gid))
    monkeypatch.setattr(catalogo, "fecha_de_gold", lambda: "2026-09-30")
    monkeypatch.setattr(movimientos, "cambios_de_grupos",
                        lambda grupos, dias: {("dia", "7"): {
                            "comparable": True, "motivo": None, "variacion_pct": -6.5,
                            "precio_unidad_antes_cent": 102, "dias_medidos": 3}})
    r = _cliente(monkeypatch, ANA).get("/api/favoritos")
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert cuerpo["dias"] == 7 and cuerpo["fecha_datos"] == "2026-09-30"
    (item,) = cuerpo["favoritos"]
    assert item["nombre"] == "Leche entera 1 L"
    assert item["precio_cent"] == 95
    assert item["variacion_pct"] == -6.5
    assert item["dias_medidos"] == 3, (
        "los dias que hay de verdad, no los de la ventana: un producto que lleva "
        "tres dias en el catalogo dice tres")
    assert item["cadena"] == "dia"


def test_un_favorito_que_ya_no_esta_se_dice_en_vez_de_desaparecer(monkeypatch):
    """La regla de la casa: lo que no se puede ensenar, se dice."""
    monkeypatch.setattr(almacen, "favoritos_de",
                        lambda uid: [{"grupo_id": 99, "producto_id": None,
                                      "anadido_en": "2026-09-01"}])
    monkeypatch.setattr(catalogo, "grupo", lambda gid: None)
    monkeypatch.setattr(catalogo, "fecha_de_gold", lambda: "2026-09-30")
    monkeypatch.setattr(movimientos, "cambios_de_grupos", lambda grupos, dias: {})
    r = _cliente(monkeypatch, ANA).get("/api/favoritos")
    (item,) = r.json()["favoritos"]
    assert item["desconocido"] is True
    assert item["motivo"] == "ya no esta en el catalogo"
    assert item["grupo_id"] == 99, "hay que poder quitarlo: sin el id no se puede"


def test_el_favorito_de_un_producto_suelto_sale_con_la_misma_forma(monkeypatch):
    """Grupo y producto se siguen de dos formas, pero se pintan con la misma tarjeta."""
    monkeypatch.setattr(almacen, "favoritos_de",
                        lambda uid: [{"grupo_id": None, "producto_id": "dia:12345",
                                      "anadido_en": "2026-09-20"}])
    monkeypatch.setattr(catalogo, "producto", lambda pid: {
        "producto_id": pid, "nombre": "Cafe molido", "marca": "DIA", "unidad": "250 g",
        "precio_cent": 210, "precio_unidad_cent": 84, "fuente": "dia", "grupo_id": 12})
    monkeypatch.setattr(catalogo, "fecha_de_gold", lambda: "2026-09-30")
    monkeypatch.setattr(movimientos, "cambios_de_grupos", lambda grupos, dias: {})
    r = _cliente(monkeypatch, ANA).get("/api/favoritos")
    (item,) = r.json()["favoritos"]
    assert item["nombre"] == "Cafe molido"
    assert item["n_cadenas"] == 1 and item["ahorro_pct"] is None
    de_grupo = {"grupo_id", "producto_id", "nombre", "marca", "unidad", "precio_cent",
                "precio_unidad_cent", "cadena", "imagen", "ahorro_pct", "n_cadenas"}
    assert de_grupo <= set(item), (
        "la tarjeta es la misma para las dos formas: si falta una clave, la pantalla "
        "pinta un hueco")


def test_la_ventana_de_dias_es_la_que_se_pide(monkeypatch):
    pedido: dict = {}
    monkeypatch.setattr(almacen, "favoritos_de", lambda uid: [])
    monkeypatch.setattr(catalogo, "fecha_de_gold", lambda: "2026-09-30")

    def cambios(grupos, dias):
        pedido["dias"] = dias
        return {}

    monkeypatch.setattr(movimientos, "cambios_de_grupos", cambios)
    r = _cliente(monkeypatch, ANA).get("/api/favoritos?dias=30")
    assert r.json()["dias"] == 30
    assert pedido["dias"] == 30, "la ventana no llega a la consulta de movimientos"


def test_seguir_algo_sin_decir_que_contesta_400(monkeypatch):
    llamado: list = []
    monkeypatch.setattr(almacen, "anade_favorito",
                        lambda *a: llamado.append(a))
    r = _cliente(monkeypatch, ANA).post("/api/favoritos", json={})
    assert r.status_code == 400
    assert "grupo o un producto" in r.json()["detail"]
    assert not llamado, "ha llegado al almacen un favorito sin destino"


def test_seguir_un_grupo_lo_guarda_con_el_usuario_de_la_sesion(monkeypatch):
    llamado: list = []
    monkeypatch.setattr(almacen, "anade_favorito", lambda *a: llamado.append(a))
    r = _cliente(monkeypatch, ANA).post("/api/favoritos", json={"grupo_id": 7})
    assert r.status_code == 201, r.text
    assert r.json() == {"hecho": True}
    assert llamado == [("u1", 7, None)], (
        "el usuario sale de la sesion, no del cuerpo: si no, cualquiera seguiria cosas "
        "en la cuenta de otro")


def test_dejar_de_seguirlo_lo_quita(monkeypatch):
    llamado: list = []
    monkeypatch.setattr(almacen, "quita_favorito", lambda *a: llamado.append(a))
    r = _cliente(monkeypatch, ANA).request(
        "DELETE", "/api/favoritos", json={"producto_id": "dia:12345"})
    assert r.status_code == 200, r.text
    assert llamado == [("u1", None, "dia:12345")]


# --- /api/preferencias ------------------------------------------------------

def test_una_preferencia_guarda_lo_que_le_manden(monkeypatch):
    """El valor es `object`: la pantalla guarda numeros, textos y listas."""
    guardado: list = []
    monkeypatch.setattr(almacen, "guarda_preferencia",
                        lambda uid, clave, valor: guardado.append((uid, clave, valor)))
    cliente = _cliente(monkeypatch, ANA)
    for clave, valor in (("tema", "oscuro"), ("columnas", ["nombre", "precio"]),
                         ("dias", 30)):
        r = cliente.put("/api/preferencias", json={"clave": clave, "valor": valor})
        assert r.status_code == 200, r.text
        assert r.json() == {"hecho": True}
    assert guardado == [("u1", "tema", "oscuro"),
                        ("u1", "columnas", ["nombre", "precio"]),
                        ("u1", "dias", 30)]
