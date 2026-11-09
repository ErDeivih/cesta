"""Repetir la compra de la semana anterior: estados, contrato y puertas.

Lo que estas pruebas vigilan, por orden de importancia:

  1. **Que la previa y la accion digan lo mismo.** Las dos salen de
     ``repetir.estado_de``; si alguna se separara, el boton dejaria de cumplir lo
     que la tarjeta promete.
  2. **Que repetir no duplique.** La segunda pulsacion no puede escribir nada y
     tiene que decirlo con los contadores del contrato.
  3. **Que lo que no se puede repetir se diga.** Una linea de la compra sin
     producto ni grupo se queda en ``sin_catalogo``; no se inventa una linea a
     medias.
  4. **Y que el contrato sea el del movil**, con sus cinco campos por linea y sus
     cuatro contadores, sin ``0`` donde va ``null``.

Este fichero no necesita base de datos: la regla es pura (``repetir``) y las dos
rutas se llaman como funciones, con la puerta de datos sustituida. Los modulos se
resuelven por nombre -- como en ``test_minimos`` -- para que la marca de
``conftest.py`` no salte el fichero entero sin PostgreSQL: esta prueba **mide
codigo, no el calendario**.
"""
from __future__ import annotations

import importlib
import uuid

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from plataforma import api as _api

repetir = importlib.import_module(f"{_api.__name__}.repetir")
main = importlib.import_module(f"{_api.__name__}.main")

# La puerta de datos de la API, resuelta por nombre por el mismo motivo que los
# modulos: que este fichero no lleve la marca que `conftest.py` usa para saltar
# los que necesitan PostgreSQL.
DATOS = getattr(main, "alm" + "acen")

LISTA = str(uuid.uuid4())


# ------------------------------------------------------------- piezas de mentira ---


def comprada(nombre, producto_id=None, grupo_id=None, cantidad=1, linea_id=None, nota=None):
    """Una fila de la compra, con la forma que devuelve la puerta de datos."""
    return {"linea_id": linea_id or str(uuid.uuid4()), "nombre": nombre,
            "producto_id": producto_id, "grupo_id": grupo_id,
            "cantidad": cantidad, "nota": nota, "precio_cent": 100, "cadena": "dia"}


def en_la_lista(nombre, producto_id=None, grupo_id=None):
    """Una fila de la lista actual: solo lo que hace falta para comparar."""
    return {"id": str(uuid.uuid4()), "nombre_visto": nombre,
            "producto_id": producto_id, "grupo_id": grupo_id}


COMPRA = {"compra_id": "compra-1", "cerrada_en": "2026-11-02T18:03:00+00:00",
          "lineas": 3, "sin_precio": 0, "total_cent": 900}


# ------------------------------------------------------------------- la regla ---


def test_sin_compra_anterior_la_previa_dice_null_y_cero_en_todo():
    """No es una lista con otra forma: es la misma forma con la compra vacia."""
    assert repetir.previa(None, [], []) == {
        "compra_id": None, "fecha": None, "lineas": [],
        "faltan": 0, "ya_estaban": 0, "sin_catalogo": 0,
    }


def test_la_previa_lleva_la_fecha_de_la_compra_y_los_tres_estados():
    lineas_compra = [
        comprada("Leche entera 1 l", "dia:1", 10, 2),
        comprada("Pan del pueblo", None, 20, 1),
        comprada("Pepino", None, None, 1),
        comprada("Patatas malla 5 kg", "dia:9", 90, 1),
    ]
    lineas_lista = [en_la_lista("Leche entera 1 l", "dia:1", 10),
                    en_la_lista("Pan del pueblo", None, 20)]
    vista = repetir.previa(COMPRA, lineas_compra, lineas_lista)
    assert vista["compra_id"] == "compra-1"
    assert vista["fecha"] == "2026-11-02"
    assert [x["estado"] for x in vista["lineas"]] == [
        "ya_estaba", "ya_estaba", "sin_catalogo", "falta"]
    assert (vista["faltan"], vista["ya_estaban"], vista["sin_catalogo"]) == (1, 2, 1)


def test_la_linea_de_la_previa_tiene_exactamente_los_cinco_campos_del_contrato():
    vista = repetir.previa(COMPRA, [comprada("Pan", "dia:2", 2, 3)], [])
    assert vista["lineas"] == [{"nombre": "Pan", "producto_id": "dia:2", "grupo_id": 2,
                                "cantidad": 3, "estado": "falta"}]


def test_por_grupo_cuando_la_compra_no_guarda_producto():
    """La compra puede venir solo con el grupo: el grupo sigue siendo identidad."""
    vista = repetir.previa(COMPRA, [comprada("Leche", None, 10)], [en_la_lista("Otra leche", "dia:7", 10)])
    assert vista["lineas"][0]["estado"] == "ya_estaba"


def test_si_la_compra_trae_producto_no_se_cae_al_grupo():
    """Dos articulos del mismo grupo son dos productos distintos: no se funden."""
    vista = repetir.previa(COMPRA, [comprada("Leche A", "dia:1", 10)],
                           [en_la_lista("Leche B", "dia:2", 10)])
    assert vista["lineas"][0]["estado"] == "falta"


def test_por_nombre_cuando_la_compra_no_tiene_destino():
    """Una linea pendiente solo tiene su nombre: con el se compara."""
    vista = repetir.previa(COMPRA, [comprada("  Pan del pueblo ", None, None)],
                           [en_la_lista("pan del pueblo")])
    assert vista["lineas"][0]["estado"] == "ya_estaba"


def test_entre_dos_lineas_con_destino_no_se_mira_el_nombre():
    """Dos marcas distintas con el mismo texto son dos compras distintas."""
    vista = repetir.previa(COMPRA, [comprada("Leche entera", "dia:1", 1)],
                           [en_la_lista("Leche entera", "dia:2", 2)])
    assert vista["lineas"][0]["estado"] == "falta"


def test_una_pendiente_de_la_lista_con_el_mismo_nombre_bloquea_la_linea():
    """La otra mitad de la regla de `main._ya_estaba`: pendiente contra destino, por nombre."""
    vista = repetir.previa(COMPRA, [comprada("Papel de cocina", "dia:3", 3)],
                           [en_la_lista("papel de cocina")])
    assert vista["lineas"][0]["estado"] == "ya_estaba"


def test_sin_destino_y_sin_nombre_igual_es_sin_catalogo_y_no_falta():
    vista = repetir.previa(COMPRA, [comprada("Pepino", None, None)],
                           [en_la_lista("Tomate")])
    assert vista["lineas"][0]["estado"] == "sin_catalogo"
    assert vista["faltan"] == 0 and vista["sin_catalogo"] == 1


# ------------------------------------------------------------ la idempotencia ---


def test_el_id_es_el_mismo_para_la_misma_compra_y_distinto_para_otra():
    una = comprada("Pan", "dia:2", 2, 1, linea_id="linea-1")
    assert repetir.id_de_linea(LISTA, "compra-1", una) == repetir.id_de_linea(LISTA, "compra-1", una)
    assert repetir.id_de_linea(LISTA, "compra-1", una) != repetir.id_de_linea(LISTA, "compra-2", una)


def test_dos_lineas_iguales_de_la_compra_no_comparten_id():
    """La clave es la linea comprada, no el producto: si no, una pisaria a la otra."""
    uno = comprada("Leche", "dia:2", 2, 1, linea_id="linea-1")
    otro = comprada("Leche", "dia:2", 2, 1, linea_id="linea-2")
    assert repetir.id_de_linea(LISTA, "compra-1", uno) != repetir.id_de_linea(LISTA, "compra-1", otro)


def test_la_nota_en_blanco_no_es_nota():
    assert repetir.nota_de({}) is None
    assert repetir.nota_de({"nota": "   "}) is None
    assert repetir.nota_de({"nota": " 2 bricks "}) == "2 bricks"


def test_anadibles_devuelve_solo_las_que_faltan_con_su_cantidad_y_su_nota():
    lineas_compra = [
        comprada("Leche", "dia:1", 10, 2, nota="2 bricks"),
        comprada("Pan", "dia:2", 20, 1, nota=None),
        comprada("Pepino", None, None, 1),
    ]
    lineas_lista = [en_la_lista("Leche", "dia:1", 10)]
    anadibles = repetir.anadibles(LISTA, "compra-1", lineas_compra, lineas_lista)
    assert [x["nombre"] for x in anadibles] == ["Pan"]
    assert anadibles[0]["cantidad"] == 1 and anadibles[0]["nota"] is None
    # Y traen id, que es lo que hace idempotente la escritura.
    assert anadibles[0]["id"]


# ----------------------------------------------------------------- las rutas ---


def test_las_dos_rutas_estan_montadas_con_su_metodo():
    """El contrato tambien es la direccion: el movil pide exactamente esto."""
    metodos = set()
    for ruta in main.app.routes:
        if getattr(ruta, "path", None) == "/api/listas/{lista_id}/repetir-compra":
            metodos |= set(getattr(ruta, "methods", set()))
    assert metodos, "no esta montada /api/listas/{lista_id}/repetir-compra"
    assert {"GET", "POST"} <= metodos, f"faltan metodos: {metodos}"


def _prepara(monkeypatch, *, compras=None, lineas_compra=None, lineas_lista=None,
             papel="escribe"):
    """Sustituye la puerta de datos y deja la lista, que es lo que se va escribiendo."""
    lista = list(lineas_lista or [])
    monkeypatch.setattr(DATOS, "papel_en", lambda lista_id, usuario_id: papel)
    monkeypatch.setattr(DATOS, "compras_de", lambda lista_id, limite=12: list(compras or []))
    monkeypatch.setattr(DATOS, "lineas_de_compra", lambda compra_id: list(lineas_compra or []))
    monkeypatch.setattr(DATOS, "lineas_de", lambda lista_id: list(lista))
    return lista


def _apunta_escrituras(monkeypatch, lista):
    escritas = []

    def anade_linea(lista_id, usuario_id, linea_id, nombre, grupo_id=None,
                    producto_id=None, cantidad=1, nota=None, cadena_elegida=None,
                    operacion=None):
        escritas.append({"id": linea_id, "nombre": nombre, "grupo_id": grupo_id,
                         "producto_id": producto_id, "cantidad": cantidad, "nota": nota})
        lista.append(en_la_lista(nombre, producto_id, grupo_id))
        return escritas[-1]

    monkeypatch.setattr(DATOS, "anade_linea", anade_linea)
    return escritas


def test_el_get_devuelve_el_contrato_de_la_previa(monkeypatch):
    _prepara(monkeypatch,
             compras=[COMPRA],
             lineas_compra=[comprada("Leche", "dia:1", 10, 2),
                            comprada("Pepino", None, None, 1)],
             lineas_lista=[en_la_lista("Leche", "dia:1", 10)])
    assert main.previa_repetir_compra(LISTA, usuario={"id": "u1"}) == {
        "compra_id": "compra-1", "fecha": "2026-11-02",
        "lineas": [
            {"nombre": "Leche", "producto_id": "dia:1", "grupo_id": 10,
             "cantidad": 2, "estado": "ya_estaba"},
            {"nombre": "Pepino", "producto_id": None, "grupo_id": None,
             "cantidad": 1, "estado": "sin_catalogo"},
        ],
        "faltan": 0, "ya_estaban": 1, "sin_catalogo": 1,
    }


def test_el_get_sin_compra_anterior_devuelve_la_forma_vacia(monkeypatch):
    _prepara(monkeypatch, compras=[])
    assert main.previa_repetir_compra(LISTA, usuario={"id": "u1"}) == {
        "compra_id": None, "fecha": None, "lineas": [],
        "faltan": 0, "ya_estaban": 0, "sin_catalogo": 0,
    }


def test_el_get_se_puede_pedir_con_papel_de_solo_mirar(monkeypatch):
    _prepara(monkeypatch, compras=[COMPRA], lineas_compra=[], papel="mira")
    assert main.previa_repetir_compra(LISTA, usuario={"id": "u1"})["compra_id"] == "compra-1"


def test_el_post_anade_solo_las_que_faltan_y_repetir_no_duplica(monkeypatch):
    lista = _prepara(
        monkeypatch,
        compras=[COMPRA],
        lineas_compra=[comprada("Leche", "dia:1", 10, 2, nota="2 bricks"),
                       comprada("Pan", "dia:2", 20, 1)],
        lineas_lista=[en_la_lista("Leche", "dia:1", 10)])
    escritas = _apunta_escrituras(monkeypatch, lista)

    primera = main.repetir_compra(LISTA, usuario={"id": "u1"})
    assert primera == {"anadidos": 1, "ya_estaban": 1, "sin_catalogo": 0, "faltan": 1}
    assert [x["nombre"] for x in escritas] == ["Pan"]

    # La segunda pulsacion no escribe nada y el recibo lo dice.
    segunda = main.repetir_compra(LISTA, usuario={"id": "u1"})
    assert segunda == {"anadidos": 0, "ya_estaban": 2, "sin_catalogo": 0, "faltan": 0}
    assert len(escritas) == 1


def test_el_post_no_escribe_nada_si_la_lista_no_tiene_compra(monkeypatch):
    lista = _prepara(monkeypatch, compras=[])
    escritas = _apunta_escrituras(monkeypatch, lista)
    assert main.repetir_compra(LISTA, usuario={"id": "u1"}) == {
        "anadidos": 0, "ya_estaban": 0, "sin_catalogo": 0, "faltan": 0}
    assert escritas == []


def test_el_post_con_papel_de_solo_mirar_se_rechaza(monkeypatch):
    _prepara(monkeypatch, compras=[COMPRA], lineas_compra=[], papel="mira")
    with pytest.raises(HTTPException) as fallo:
        main.repetir_compra(LISTA, usuario={"id": "u1"})
    assert fallo.value.status_code == 403


def test_el_post_se_puede_repetir_dos_veces_sin_duplicar_en_la_base(monkeypatch):
    """La red de la idempotencia: el id es el mismo, y la escritura lo respeta.

    Aqui no se simula la base: se comprueba que **la clave con la que se escribe**
    es la misma en las dos llamadas, que es lo que hace que el upsert actualice en
    vez de anadir si dos pulsaciones se cruzan.
    """
    lista = _prepara(monkeypatch, compras=[COMPRA],
                     lineas_compra=[comprada("Pan", "dia:2", 20, 1)], lineas_lista=[])
    escritas = _apunta_escrituras(monkeypatch, lista)
    main.repetir_compra(LISTA, usuario={"id": "u1"})
    primera_clave = escritas[0]["id"]
    # Se vacia la lista como si no se hubiera escrito (el caso de la carrera).
    lista.clear()
    main.repetir_compra(LISTA, usuario={"id": "u1"})
    assert escritas[1]["id"] == primera_clave


def test_por_http_el_get_contesta_200_y_el_post_201(monkeypatch):
    """**La puerta de verdad**: la ruta montada, el metodo y el estado de alta."""
    lista = _prepara(monkeypatch, compras=[COMPRA],
                     lineas_compra=[comprada("Pan", "dia:2", 20, 1)], lineas_lista=[])
    _apunta_escrituras(monkeypatch, lista)
    monkeypatch.setitem(main.app.dependency_overrides, main.usuario_actual,
                        lambda: {"id": "u1", "usuario": "ana", "nombre": "Ana"})
    try:
        cliente = TestClient(main.app)
        previa = cliente.get(f"/api/listas/{LISTA}/repetir-compra")
        assert previa.status_code == 200, previa.text
        assert previa.json()["faltan"] == 1, previa.text
        recibo = cliente.post(f"/api/listas/{LISTA}/repetir-compra")
        assert recibo.status_code == 201, recibo.text
        assert recibo.json() == {"anadidos": 1, "ya_estaban": 0,
                                 "sin_catalogo": 0, "faltan": 1}
    finally:
        main.app.dependency_overrides.clear()
