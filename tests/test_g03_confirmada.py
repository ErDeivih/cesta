"""G03: la confirmacion de una sustitucion, y **la revocacion decidiendo**.

**Por que esta pieza.** `_es_la_confirmada(peticion, alternativa)` es donde la revocacion cambia el
resultado: dice si *la sustitucion que confirmo la persona* es *la que el motor propone ahora*. Si
devuelve `True`, la linea cuenta en el total autorizado; si `False`, se enseña con su precio **pero no
suma** -- *un aviso no es un permiso*. **Revocar es poner `autorizado` a `False`, y esta funcion tiene
que notarlo por el primer camino, no por casualidad.**

**Por que se puede medir sin nada.** No toca el catalogo, ni la base, ni el servidor: **dos
dataclasses y una comparacion**. `donde_comprar` -- que seria lo natural de medir -- **si** lee el
catalogo (`_candidatos` sobre `data/gold/`), asi que una prueba suya *mide el calendario*. Esta mide
la regla.

**Tres condiciones, y ninguna sobra** (lo dice su docstring): que haya un si; que conste **que** se
acepto; y que coincida **en producto y en cadena**. Se prueban las tres por separado, y tambien cada
una sola frente a las otras dos ciertas -- que es lo unico que demuestra que **hacen falta las tres**.
"""
from __future__ import annotations

from plataforma.api.cesta import Eleccion, Peticion, _es_la_confirmada, _total_autorizado


def _peticion(**cambios) -> Peticion:
    """Una linea con su sustitucion ya confirmada, salvo lo que diga la prueba."""
    base = dict(
        grupo_id=6803, producto_id=None, cantidad=1, nombre="Leche",
        id="linea-1", autorizado=True,
        autorizado_producto="prod-a", autorizado_cadena="alcampo",
    )
    base.update(cambios)
    return Peticion(**base)


def _alternativa(**cambios) -> Eleccion:
    # **`autorizada` es el campo que `_total_autorizado` mira** (`cesta.py:383`), y no estaba en mi
    # primera lectura del dataclass: hay al menos tres campos mas -- `autorizada`, `identidad` y
    # `motivo` --. Sin ponerlo, la eleccion contaba por defecto y mis dos pruebas del total median mi
    # suposicion, no el codigo. Medido el 11 de octubre de 2026.
    base = dict(producto_id="prod-a", nombre="Leche semidesnatada", fuente="alcampo",
                unidades=1, coste_cent=95, coste_sin_oferta_cent=95, promo_txt=None,
                sugerencia=None, linea_id="linea-1",
                autorizada=True, identidad="exacta", motivo=None)
    base.update(cambios)
    return Eleccion(**base)


# --- el si, y la revocacion -------------------------------------------------

def test_con_el_si_puesto_y_todo_coincidiendo_cuenta():
    """El caso bueno, primero: sin esto, las demas pruebas no significan nada."""
    assert _es_la_confirmada(_peticion(), _alternativa()) is True


def test_revocar_la_linea_la_saca_de_las_confirmadas():
    """**El nucleo de G03.** La misma linea, la misma alternativa, y el si retirado.

    Revocar no borra la linea ni cambia el producto: **cambia esta respuesta**. Y es por esto por lo
    que el total baja y la linea pasa a «lo que falta» -- no porque desaparezca.
    """
    assert _es_la_confirmada(_peticion(autorizado=False), _alternativa()) is False


def test_sin_alternativa_no_hay_nada_que_confirmar():
    assert _es_la_confirmada(_peticion(), None) is False


# --- las tres condiciones, cada una sola ------------------------------------

def test_un_si_sin_producto_no_se_puede_honrar():
    """La base lo rechaza desde la migracion 012: *un si sin producto no se puede cumplir*."""
    assert _es_la_confirmada(_peticion(autorizado_producto=None), _alternativa()) is False
    assert _es_la_confirmada(_peticion(autorizado_producto=""), _alternativa()) is False


def test_si_el_motor_propone_otro_producto_hay_que_volver_a_confirmar():
    """*Es una sustitucion distinta, aunque se parezca.*"""
    assert _es_la_confirmada(_peticion(), _alternativa(producto_id="prod-b")) is False


def test_si_cambia_la_cadena_tambien():
    """El docstring es explicito: coincidir **en producto y cadena**."""
    assert _es_la_confirmada(_peticion(), _alternativa(fuente="aldi")) is False


def test_sin_cadena_confirmada_no_vale():
    assert _es_la_confirmada(_peticion(autorizado_cadena=None), _alternativa()) is False


# --- y el defecto que ya hubo: los dos nombres de la cadena ------------------

def test_la_cadena_se_lee_por_sus_dos_nombres():
    """**El defecto que ya paso, fijado para que no vuelva.**

    La alternativa llama a la cadena `fuente` -- es la cadena de la que sale el precio --, y leer solo
    `cadena` hacia que la comparacion saliera **siempre falsa**: no contaba ninguna confirmacion, ni
    la buena. Se comprueban los dos nombres, porque los dos aparecen.
    """
    como_objeto = _alternativa(fuente="alcampo")
    assert _es_la_confirmada(_peticion(), como_objeto) is True
    # Y `cadena`, que es el otro nombre, tiene que valer igual.
    assert _es_la_confirmada(_peticion(), {"producto_id": "prod-a", "cadena": "alcampo"}) is True


def test_la_alternativa_puede_llegar_como_diccionario():
    """*Se lee sin suponer cual*: la alternativa llega de la base como diccionario y del motor como
    objeto, y la funcion tiene que servir para las dos."""
    assert _es_la_confirmada(_peticion(),
                             {"producto_id": "prod-a", "fuente": "alcampo"}) is True
    assert _es_la_confirmada(_peticion(),
                             {"producto_id": "prod-b", "fuente": "alcampo"}) is False


# --- y el total, que es lo que obedece --------------------------------------

def test_el_total_cuenta_lo_confirmado_y_dice_lo_que_falta():
    """**Los tres numeros.** `total_cent` suma; `lineas_contadas` cuenta; **y lo que no cuenta no se
    tira**: va en `pendientes`, que es de donde sale la propuesta de alternativa.

    Es lo que hace que revocar una linea **no sea una linea desaparecida**, sino una linea retirada
    del total que sigue enseñandose y sigue diciendo por que.
    """
    cuenta = _alternativa(coste_cent=95, coste_sin_oferta_cent=95)
    # La que no cuenta lleva `autorizada=False` **y su motivo**: es una linea retirada del total, no
    # una linea desaparecida, y el motivo es lo que la hace explicable.
    no_cuenta = _alternativa(producto_id="prod-b", coste_cent=120, coste_sin_oferta_cent=130,
                             autorizada=False, identidad="alternativa",
                             motivo="no autorizada: el motor propone otro producto")
    total = _total_autorizado([cuenta, no_cuenta])

    assert total["total_cent"] == 95, f"suma solo lo autorizado: {total}"
    assert total["lineas_contadas"] == 1, total
    assert len(total["pendientes"]) == 1, (
        f"lo que no cuenta tiene que salir en `pendientes`, con su motivo: {total}")
    assert total["completo"] is False, "con una pendiente, el total no esta completo"
    # **Y el motivo viaja**, que es lo que hace que la linea revocada sea explicable y no un hueco.
    assert total["pendientes"][0]["motivo"], f"la pendiente tiene que decir por que: {total}"
    assert total["pendientes"][0]["linea_id"] == "linea-1", total["pendientes"][0]


def test_sin_ninguna_confirmada_el_total_es_cero_y_dice_por_que():
    """El total mas bajo es el que se puede explicar. Y cero **con las lineas dentro**."""
    total = _total_autorizado([_alternativa(producto_id="otro", autorizada=False,
                                            identidad="alternativa", motivo="sin confirmar")])
    assert total["total_cent"] == 0, total
    assert total["lineas_contadas"] == 0, total
    assert len(total["pendientes"]) == 1, total


def test_una_lista_vacia_no_revienta():
    """Y una lista vacia devuelve ceros, no una excepcion: el caso de una lista sin nada."""
    total = _total_autorizado([])
    assert total["total_cent"] == 0 and total["lineas_contadas"] == 0, total
    assert total["pendientes"] == [], total
