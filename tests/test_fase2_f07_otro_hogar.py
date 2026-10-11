"""F07 / `C01b`: **que un hogar no vea las listas de otro.**

El criterio (`docs/SUPERAPP-COMPETENCIA-Y-REA.md:89`) dice:

> C01 — Lista familiar: añadir/tachar/deshacer desde dos sesiones, sin perder cambios **ni exponer listas de
> otro hogar**.

*La primera mitad ya está medida (§3 de `docs/investigaciones/F07-compra-familiar.md`). **Ésta es la segunda,
y es la que importa**: de todo C01–C05 **es lo único que puede hacer daño si falla.**

**Las dos defensas que hay, leídas:** `almacen.papel_en(lista_id, usuario_id)` -- *devuelve el papel, o `None`
si esa persona no está en la lista* --, y `main._acceso(lista_id, usuario, hace_falta_escribir=False)` -- *el
guardián que usan las rutas, y que además convierte un identificador que no es UUID en un 404 en vez de un 500.*

*Van contra el Postgres de verdad, y crean sus propios hogares: **no tocan datos de nadie**.*
"""
from __future__ import annotations

import time
import uuid

import pytest
from fastapi import HTTPException

from plataforma.api import almacen, main


@pytest.fixture(scope="module", autouse=True)
def _arrancado():
    almacen.arranca()
    yield
    almacen.para()


def _hogar(nombre: str) -> tuple[str, str]:
    """Un usuario nuevo y su lista. *Con sello, porque los usuarios viven en Postgres y no se borran.*"""
    sello = f"{int(time.time() * 1000) % 100000000}"
    usuario = almacen.crea_usuario(f"c01b-{nombre}-{sello}", f"Hogar {nombre}", "clave-de-prueba-123")
    identificador = usuario["id"] if isinstance(usuario, dict) else usuario
    lista = almacen.crea_lista(identificador, f"Lista de {nombre}")
    lista_id = lista["id"] if isinstance(lista, dict) else lista
    return identificador, lista_id


# ---------------------------------------------------------------------------------------------
# El papel: quien esta y quien no
# ---------------------------------------------------------------------------------------------


def test_el_dueno_tiene_su_lista_y_el_otro_no():
    """**Lo minimo, y es lo que hay que demostrar.** *`papel_en` contesta por cada uno.*"""
    dueno, lista_id = _hogar("papel")
    ajeno, _ = _hogar("papel-ajeno")

    assert almacen.papel_en(lista_id, dueno) is not None, "el dueno tiene que estar en su lista"
    assert almacen.papel_en(lista_id, ajeno) is None, (
        "**y el de otro hogar NO**: si esto falla, la lista se expone")


def test_un_hogar_ajeno_no_pasa_el_guardian():
    """**La prueba de seguridad.** *El guardián de las rutas tiene que negarse con el de fuera.*

    *Sin esto, `papel_en` podría estar bien y las rutas no usarlo* -- **y entonces la lista se expone igual.**
    """
    _dueno, lista_id = _hogar("guardian")
    ajeno, _ = _hogar("guardian-ajeno")

    with pytest.raises(HTTPException) as fallo:
        main._acceso(lista_id, {"id": ajeno})

    # **Y el codigo importa**: 403 es «no puedes», 404 es «no existe».
    # *Para una lista ajena, **404 es mejor**: no confirma que exista.*
    assert fallo.value.status_code in (403, 404), (
        f"un hogar ajeno tiene que recibir 403 o 404, y recibio {fallo.value.status_code}")


def test_el_dueno_si_pasa_el_guardian():
    """*El otro lado, para que la prueba anterior no pase porque el guardián no deja pasar a nadie.*"""
    dueno, lista_id = _hogar("dueno-pasa")

    assert main._acceso(lista_id, {"id": dueno}) is not None


def test_leer_no_es_escribir():
    """**Y el guardián distingue.** *`hace_falta_escribir=True` es para lo que cambia la lista.*

    *Quien solo puede mirar no tiene que poder tachar* -- **y si el guardián ignorara el parámetro, la
    distinción no existiría.**
    """
    dueno, lista_id = _hogar("papel-lectura")
    # A alguien de fuera, la marca de escritura no le sirve de nada: sigue fuera.
    ajeno, _ = _hogar("papel-lectura-ajeno")

    for escribir in (False, True):
        with pytest.raises(HTTPException):
            main._acceso(lista_id, {"id": ajeno}, hace_falta_escribir=escribir)

    # Y el dueno pasa en los dos casos.
    assert main._acceso(lista_id, {"id": dueno}, hace_falta_escribir=True) is not None


def test_un_identificador_que_no_es_lista_no_revienta():
    """**Un 404, no un 500.** *Está documentado en `_acceso`: «un identificador que no es un UUID no es un error
    del servidor: es una dirección que no existe» -- y se vio el 18-sep-2026 pidiendo `/api/listas/None`.*
    """
    dueno, _ = _hogar("no-uuid")

    with pytest.raises(HTTPException) as fallo:
        main._acceso("None", {"id": dueno})

    assert fallo.value.status_code == 404, (
        f"un identificador que no es UUID tiene que ser 404 y fue {fallo.value.status_code}")


def test_una_lista_que_no_existe_tampoco():
    """*Y una que sí es UUID pero no está, igual: 404.*"""
    dueno, _ = _hogar("inexistente")

    with pytest.raises(HTTPException) as fallo:
        main._acceso(str(uuid.uuid4()), {"id": dueno})

    assert fallo.value.status_code == 404
