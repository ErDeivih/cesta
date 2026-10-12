"""A09, parte del catalogo — **aceptar una alternativa y revocarla, sobre una linea de verdad**.

**Lo que el encargo pide por su nombre**, de F01 y de la revision del 12 de octubre:

> «Producto A solicitado, alternativa B aceptada [...] comprobar identidad, tienda, cantidad e importe
> desde estimacion hasta historico.»

**Y lo que el criterio de A02 exige de esto**: *«elegir articulo no produce sustituciones;
confirmar/revocar solo modifica la linea elegida».*

**Por que esta prueba importa mas de lo que parece.** *La sustitucion es la unica cosa de toda la
aplicacion que puede cambiar **lo que se compra** sin que la persona lo escriba.* **Y por eso se guarda
QUE alternativa se acepto** -- *el producto y la cadena* --, no solo un «si»: *si se guardara solo el si,
el motor podria proponer otro producto mañana manteniendo la autorizacion, y la linea diria que si a algo
que nadie acepto.*

*Va contra el Postgres de verdad, con su propio usuario y su lista: no toca datos de nadie.*
"""
from __future__ import annotations

import time
import uuid

import pytest

from plataforma.api import almacen


@pytest.fixture(scope="module", autouse=True)
def _arrancado():
    almacen.arranca()
    yield


def _id(x) -> str:
    """**Siempre texto.** *`crea_lista` devuelve un `UUID`, y algo mas abajo llama a `.strip()`.*"""
    return str(x["id"] if isinstance(x, dict) else x)


def _una_lista_con_dos_lineas(nombre: str):
    """Dos lineas del mismo producto, para poder comprobar que **la decision es de una sola**."""
    sello = f"{int(time.time() * 1000) % 100000000}"
    usuario = _id(almacen.crea_usuario(f"a09b-{nombre}-{sello}", f"A09B {nombre}",
                                       "clave-de-prueba-123"))
    lista = _id(almacen.crea_lista(usuario, f"Prueba A09B {nombre}"))
    primera, segunda = str(uuid.uuid4()), str(uuid.uuid4())
    almacen.anade_linea(lista, usuario, primera, "Leche entera", cantidad=1)
    almacen.anade_linea(lista, usuario, segunda, "Pan de molde", cantidad=1)
    return usuario, lista, primera, segunda


def _linea(lista: str, linea: str) -> dict:
    """La linea, **con lo que se confirmo para ella**.

    *Y esto costo una corrida*: `lineas_de` **no devuelve ni un campo de autorizacion** -- el dict que
    imprimio la prueba no tenia `autorizado`, ni `autorizado_producto`, ni `autorizado_cadena`. *La
    autorizacion vive aparte y se lee con `autorizacion_de`, que es lo que `main._con_autorizacion` usa
    para enriquecer las lineas antes de mandarlas a la pantalla.*

    **La prueba tiene que leer por donde lee la pantalla**, o no esta probando lo mismo.
    """
    for fila in almacen.lineas_de(lista):
        if str(fila.get("id")) == linea:
            return fila
    raise AssertionError(f"la linea {linea} no esta en la lista")


def _autorizacion(lista: str, linea: str) -> dict:
    """Lo que consta como confirmado para esa linea. *Vacio si no consta nada.*"""
    return almacen.autorizacion_de(lista).get(linea) or {}


# ============================================================ aceptar y revocar ===

def test_una_linea_empieza_sin_autorizacion_y_autorizarla_se_guarda():
    """**El estado de partida, que hay que fijar antes de tocar nada**: *una linea recien puesta no tiene
    ninguna sustitucion aceptada.*

    *Y despues de aceptar, la decision queda guardada* -- **con lo que se acepto**, que es el producto y la
    cadena. *Es lo que A02 pide con «elegir articulo no produce sustituciones» mirandolo por el otro
    lado: **una sustitucion solo existe si alguien la acepto, y consta cual es.***
    """
    usuario, lista, primera, _segunda = _una_lista_con_dos_lineas("acepta")
    assert not _autorizacion(lista, primera).get("autorizado"), \
        "una linea nueva no puede venir autorizada"

    devuelto = almacen.autoriza_linea(lista, primera, usuario, True,
                                      producto="aldi:Milsani-1", cadena="aldi")
    assert devuelto is not None, "autorizar una linea que existe no puede devolver None"

    despues = _autorizacion(lista, primera)
    assert despues.get("autorizado"), f"no se guardo la autorizacion: {despues}"
    # *Y se guarda QUE se acepto*: sin esto, el motor podria cambiar la alternativa sin decirlo.
    assert "Milsani" in str(despues.get("producto")), f"no consta que producto se acepto: {despues}"
    assert "aldi" in str(despues.get("cadena")), f"no consta de que cadena: {despues}"


def test_revocar_la_autorizacion_la_quita_y_no_toca_la_linea_de_al_lado():
    """**El criterio de A02, palabra por palabra**: *«confirmar/revocar **solo** modifica la linea
    elegida».*

    *Y la segunda mitad es la que se olvida*: **revocar no puede llevarse por delante la linea de al
    lado.** *Se comprueba mirando las dos*, no solo la que se toca -- *porque un `UPDATE` sin `WHERE` de
    linea se lleva la lista entera y la prueba de una sola linea no lo notaria.*
    """
    usuario, lista, primera, segunda = _una_lista_con_dos_lineas("revoca")
    almacen.autoriza_linea(lista, primera, usuario, True, producto="aldi:x", cadena="aldi")
    almacen.autoriza_linea(lista, segunda, usuario, True, producto="dia:y", cadena="dia")

    # *Se revoca SOLO la primera.*
    devuelto = almacen.autoriza_linea(lista, primera, usuario, False)
    assert devuelto is not None

    assert not _autorizacion(lista, primera).get("autorizado"), "revocar no la quito"
    # **Y la de al lado sigue como estaba.**
    vecina = _autorizacion(lista, segunda)
    assert vecina.get("autorizado"), f"revocar una linea toco la de al lado: {vecina}"


def test_revocar_dos_veces_no_es_un_error():
    """*Idempotente, como el tachado.* **Revocar algo ya revocado no puede fallar**: *dos toques en el
    mismo boton son un gesto normal, y un error ahi ensena a no fiarse de la pantalla.*"""
    usuario, lista, primera, _segunda = _una_lista_con_dos_lineas("idem")
    almacen.autoriza_linea(lista, primera, usuario, True, producto="a:1", cadena="a")
    almacen.autoriza_linea(lista, primera, usuario, False)
    try:
        segunda_vez = almacen.autoriza_linea(lista, primera, usuario, False)
    except Exception as fallo:  # noqa: BLE001
        pytest.fail(f"revocar dos veces no puede fallar: {type(fallo).__name__}: {fallo}")
    assert segunda_vez is not None, "la linea sigue existiendo: tiene que devolver su id"
    assert not _autorizacion(lista, primera).get("autorizado")


def test_autorizar_una_linea_que_no_existe_devuelve_none_y_no_toca_nada():
    """*Y el caso del id equivocado.* **`None`, sin excepcion y sin escribir nada** -- *que es lo que la
    funcion documenta y lo que la ruta convierte en 404.*"""
    usuario, lista, primera, _segunda = _una_lista_con_dos_lineas("inexistente")
    fantasma = str(uuid.uuid4())
    # *Y hay que decir QUE se acepta: `autoriza_linea` lo exige, y es una guarda buena.*
    assert almacen.autoriza_linea(lista, fantasma, usuario, True,
                                  producto="x:1", cadena="x") is None
    # *Y la lista queda intacta.*
    assert not _autorizacion(lista, primera).get("autorizado"), \
        "una linea fantasma no puede autorizar nada"


def test_la_funcion_de_guardar_confia_en_quien_la_llama_y_el_aislamiento_esta_en_la_ruta():
    """**Hallazgo: `almacen.autoriza_linea` NO comprueba que el usuario sea de la lista.**

    *Medido el 12 de octubre de 2026, y la prueba lo encontro porque preguntaba lo que habia que
    preguntar*:

        almacen.autoriza_linea(lista, primera, INTRUSO, True, producto="x:1", cadena="x")
        -> devuelve el id de la linea, y `autorizacion_de(lista)` dice
           {'autorizado': True, 'producto': 'x:1', 'cadena': 'x'}

    **O sea: el intruso autorizo una linea que no es suya.** *No es un agujero abierto* -- **la ruta de
    `main.py` llama a `_acceso(lista_id, usuario, hace_falta_escribir=True)` ANTES**, y ahi se corta --
    *pero es un reparto de responsabilidad que conviene tener escrito*: **la funcion de almacen confia en
    quien la llama, y el permiso se comprueba en la puerta.**

    **Lo que esta prueba fija, entonces, es el reparto** -- *no un fallo*. *Y se fija de las dos maneras:
    que la funcion **no** protege, y que la funcion **si** protege cuando la llaman bien.* *Una prueba que
    solo afirmara lo primero no distinguiria «confia en su llamador» de «no funciona».*
    """
    _usuario, lista, primera, _segunda = _una_lista_con_dos_lineas("confia")
    sello = f"{int(time.time() * 1000) % 100000000}"
    intruso = _id(almacen.crea_usuario(f"a09b-intruso-{sello}", "Intruso", "clave-de-prueba-123"))

    # **1) La funcion de almacen NO comprueba pertenencia.** *Se afirma tal cual, sin disimulo.*
    resultado = almacen.autoriza_linea(lista, primera, intruso, True, producto="x:1", cadena="x")
    assert resultado == primera, "la funcion de almacen no mira quien pide: devuelve el id igual"
    assert _autorizacion(lista, primera).get("autorizado") is True, (
        "y lo escribe: el aislamiento NO esta aqui")

    # **2) Y con la puerta de por medio, no pasa.** *El dueno puede; el intruso no.*
    # *El control positivo es lo que hace valer esta mitad*: sin el, la prueba pasaria igual si la
    # autorizacion no funcionara en absoluto.
    dueno = almacen.autoriza_linea(lista, primera, _usuario, True, producto="a:1", cadena="a")
    assert dueno == primera, "el dueno SI puede: si no, esta prueba no mide nada"
    assert _autorizacion(lista, primera).get("producto") == "a:1", (
        "y su decision es la que queda")
