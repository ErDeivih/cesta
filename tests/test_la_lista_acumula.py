"""*** La lista ACUMULA, *y la operacion de la que viene cada linea esta guardada. *** *

*El 14/10/2026 el propietario decidio que **la lista acumula**: *dos operaciones distintas sobre el
mismo producto **se suman**, *y **la misma operacion repetida no duplica.** *

*Y esto **no se podia** con el `id` solo, *aunque ya llevara la operacion: *`uuid5` es **un hash**, *
*asi que de `id_de_linea(lista_id, "tomate|2026-11-02|2026-11-08")` **no se puede recuperar la
operacion.** *Y **por eso** el traspaso la tiene **en columnas** *(-- `receta_id`, `version`,
`semana` --)*: *un id sirve para que **dos cosas iguales den el mismo** *y **dos distintas den
otro**, *y nada mas.* *

*Y estos ensayos prueban **las dos mitades** donde se pueden probar: *la columna, *y que **dos
operaciones coexisten.** *
"""
from __future__ import annotations

import uuid

import pytest

from plataforma.api import almacen


@pytest.fixture
def con_lista():
    """*Un usuario y su lista de casa, **nuevos en cada ensayo.***"""
    almacen.arranca()
    sello = uuid.uuid4().hex[:10]
    yo = almacen.crea_usuario(f"acumula-{sello}", "Acumula", "clave-de-prueba-123")
    lista = almacen.crea_lista(str(yo["id"]), f"casa-{sello}", es_de_casa=True)
    return str(yo["id"]), str(lista["id"])


def test_la_operacion_se_guarda_y_se_lee(con_lista):
    """*** La columna, *de punta a punta: *se escribe, *y `lineas_de` la devuelve. *** *

    *Y **`None` es un valor legitimo** *-- *«no viene de una operacion» --, *no un hueco: *
    *una linea **puesta a mano** no viene de ninguna.* *
    """
    usuario, lista = con_lista
    con_op = almacen.anade_linea(lista, usuario, str(uuid.uuid4()), "Tomate",
                                 grupo_id=7, cantidad=1, operacion="2026-11-02|2026-11-08")
    sin_op = almacen.anade_linea(lista, usuario, str(uuid.uuid4()), "Pan",
                                 grupo_id=8, cantidad=1)

    por_id = {x["id"]: x for x in almacen.lineas_de(lista)}
    assert por_id[con_op["id"]]["operacion"] == "2026-11-02|2026-11-08", por_id[con_op["id"]]
    assert por_id[sin_op["id"]]["operacion"] is None, por_id[sin_op["id"]]


def test_dos_operaciones_distintas_sobre_lo_mismo_COEXISTEN(con_lista):
    """*** La acumulacion, *que es lo que el propietario pidio. *** *

    *Mismo producto, *mismo grupo, ***dos operaciones** -> **dos lineas**, *y **las dos vivas.** *
    *Y **antes esto era una sola**: *el id salia de `lista_id|clave` sin la operacion, *
    *asi que la segunda **actualizaba la primera** *-- *y **la compra menguaba sin decirlo.*** *
    """
    usuario, lista = con_lista
    # *** Y los ids se sacan con `id_de_linea`, *que es lo que hace el puente. *** *
    #
    # *La columna `id` es *** `uuid` ***, *asi que un literal como `"id-de-la-semana-1"` **revienta
    # en Postgres** -- *y eso me paso a mi escribiendo esto: *lo dice el error, que es lo que tiene
    # que pasar.* *Y ademas, **sacarlos con la funcion de verdad** es lo que hace que el ensayo
    # pruebe **la idempotencia real** y no una imitacion.* *
    from core import traspaso

    semana_1 = "2026-11-02|2026-11-08"
    semana_2 = "2026-11-09|2026-11-15"
    almacen.anade_linea(lista, usuario, traspaso.id_de_linea(lista, f"7|{semana_1}"),
                        "Tomate", grupo_id=7, cantidad=2, operacion=semana_1)
    almacen.anade_linea(lista, usuario, traspaso.id_de_linea(lista, f"7|{semana_2}"),
                        "Tomate", grupo_id=7, cantidad=3, operacion=semana_2)

    vivas = [x for x in almacen.lineas_de(lista) if x["nombre_visto"] == "Tomate"]
    assert len(vivas) == 2, vivas
    assert {x["operacion"] for x in vivas} == {"2026-11-02|2026-11-08", "2026-11-09|2026-11-15"}
    assert {x["cantidad"] for x in vivas} == {2, 3}, vivas


def test_la_misma_operacion_y_el_mismo_id_actualiza_y_no_anade(con_lista):
    """*** Y la otra mitad: *repetir la operacion **no duplica.** *** *

    *Es **el mismo id** *(-- *porque sale de la operacion y la clave --)*, *y `anade_linea` **es un
    upsert**: *asi que **actualiza**.* *Que es lo que hace que pulsar dos veces sea seguro.* *
    """
    usuario, lista = con_lista
    from core import traspaso

    la_operacion = "2026-11-02|2026-11-08"
    # *El MISMO id las dos veces, *y sacado como lo saca el puente.* *
    el_id = traspaso.id_de_linea(lista, f"7|{la_operacion}")
    almacen.anade_linea(lista, usuario, el_id, "Tomate", grupo_id=7, cantidad=2,
                        operacion=la_operacion)
    almacen.anade_linea(lista, usuario, el_id, "Tomate", grupo_id=7, cantidad=5,
                        operacion=la_operacion)

    vivas = [x for x in almacen.lineas_de(lista) if x["nombre_visto"] == "Tomate"]
    assert len(vivas) == 1, vivas
    assert vivas[0]["cantidad"] == 5, vivas


def test_una_linea_puesta_a_mano_no_viene_de_ninguna_operacion(con_lista):
    """*** Y **`None` es «no viene de una operacion»**, *y eso importa: *** *

    *una linea que alguien **apunto a mano** *-- *o que **ya estaba** antes de la migracion 020 --*
    *no se puede atribuir a una operacion, *y **no se le inventa una.** *
    *Y por eso **el puente la sigue contando como «ya esta»**: *saltarla la **duplicaria**, *
    *y eso no es acumular.* *
    """
    usuario, lista = con_lista
    almacen.anade_linea(lista, usuario, str(uuid.uuid4()), "Tomate", grupo_id=7, cantidad=1)
    suyas = almacen.lineas_de(lista)
    assert all(x["operacion"] is None for x in suyas), suyas
    # *Y **sigue viva y legible**, *que es lo que `014` garantiza: *la linea existe aunque no
    # tenga destino ni operacion.* *
    assert any(x["nombre_visto"] == "Tomate" for x in suyas), suyas


def test_el_id_determinista_de_la_operacion_es_el_mismo_y_no_se_puede_deshacer():
    """*** Y **por que la operacion va en una columna y no dentro del id.** *** *

    *`id_de_linea` **da el mismo id** para la misma operacion *-- *que es lo que hace la
    idempotencia --, *y **da otro** para otra. *Pero **es un `uuid5`**, *o sea **un hash**: *
    *** de los dos ids NO SE PUEDE RECUPERAR la operacion.** *
    *Y **por eso** `traspaso` guarda `receta_id`, `version` y `semana` **en columnas**, *
    *y **por eso** la linea tiene `operacion`. *
    """
    from core import traspaso

    a = traspaso.id_de_linea("lista", "tomate|2026-11-02|2026-11-08")
    b = traspaso.id_de_linea("lista", "tomate|2026-11-02|2026-11-08")
    c = traspaso.id_de_linea("lista", "tomate|2026-11-09|2026-11-15")

    assert a == b, "la misma operacion tiene que dar el mismo id"
    assert a != c, "otra operacion tiene que dar otro id"
    # *Y **no lleva el texto dentro**: *si lo llevara, leerlo seria trivial.* *
    assert "2026-11-02" not in a, a
    assert "tomate" not in a, a


def test_dos_lineas_a_mano_con_ids_distintos_son_dos():
    """*Y una ultima, que es de sentido comun y no estaba escrita: *dos lineas **a mano** con
    **ids distintos** son **dos**, *aunque sean el mismo producto.* *
    *Sin esto, «acumular» podria confundirse con «una linea por producto», *y no es eso: *
    *es **una por operacion**, *y las de a mano son **una por vez que se apuntan.** *
    """
    from plataforma.api import almacen as a

    sello = uuid.uuid4().hex[:10]
    a.arranca()
    yo = a.crea_usuario(f"mano-{sello}", "Mano", "clave-de-prueba-123")
    lista = a.crea_lista(str(yo["id"]), f"mano-{sello}", es_de_casa=True)
    a.anade_linea(str(lista["id"]), str(yo["id"]), str(uuid.uuid4()), "Tomate", grupo_id=7)
    a.anade_linea(str(lista["id"]), str(yo["id"]), str(uuid.uuid4()), "Tomate", grupo_id=7)
    assert len([x for x in a.lineas_de(str(lista["id"])) if x["nombre_visto"] == "Tomate"]) == 2
