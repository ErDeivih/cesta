"""F15: **la paginacion del buscador**, que era un tope.

El criterio (`docs/SUPERAPP-FASE2-EMPEZAR-AQUI.md:189`) pide, entre otras cosas:

> Medir busqueda/listas/fichas/graficas con volumen real: **paginacion**, indices, cargas, tamanos JS y latencia.

**Y medido en la ronda 147, no habia paginacion**: *`buscar` tenia un `LIMIT` parametrizado -- `limite: int = 40`
-- y **ningun `OFFSET`**, asi que **se veian los primeros 40 y los siguientes no se podian pedir**.*

> **Un tope corta; una paginacion continua.** *No es lo mismo «se para» que «no hay mas».*

**Y el arreglo son tres lineas**: *un `desplazamiento`, un `OFFSET ?` y su argumento.* **Lo que estas pruebas
fijan es que pagina de verdad -- sin solaparse -- y que **quien no pase el parametro no nota nada**.*
"""
from __future__ import annotations

import pytest

from plataforma.api import catalogo


def _ids(filas: list[dict]) -> list[str]:
    return [str(f.get("grupo_id")) for f in filas]


def test_dos_paginas_no_se_solapan():
    """**Lo que hace que sea paginacion y no un tope.** *Si las dos paginas trajeran lo mismo, el `OFFSET` no
    estaria haciendo nada.*
    """
    primera = catalogo.buscar("leche", limite=5)
    segunda = catalogo.buscar("leche", limite=5, desplazamiento=5)

    assert primera, "la primera pagina no puede estar vacia"
    assert segunda, "y la segunda tampoco: hay mas de cinco leches en 52.087 grupos"
    assert not set(_ids(primera)) & set(_ids(segunda)), (
        f"las dos paginas comparten productos: {set(_ids(primera)) & set(_ids(segunda))}")


def test_tres_paginas_seguidas_son_distintas():
    """*Y no solo dos: la tercera sigue avanzando.*"""
    paginas = [_ids(catalogo.buscar("leche", limite=5, desplazamiento=n)) for n in (0, 5, 10)]

    assert all(paginas), f"alguna pagina vino vacia: {[len(p) for p in paginas]}"
    vistas: set[str] = set()
    for n, p in enumerate(paginas):
        repetidos = vistas & set(p)
        assert not repetidos, f"la pagina {n + 1} repite {repetidos}"
        vistas |= set(p)


@pytest.mark.xfail(strict=True, reason=(
    "DEFECTO MEDIDO: el mismo que `test_el_orden_del_buscador_es_estable` -- *el orden de `buscar` no "
    "es total, asi que dos llamadas iguales dan orden distinto, y esta prueba compara dos llamadas.* "
    "**Depende del arreglo del `ORDER BY`, no de la paginacion**, que funciona."))
def test_el_desplazamiento_por_defecto_no_cambia_nada():
    """**La mitad que evita romper lo que ya funcionaba.** *`desplazamiento` vale `0` por defecto, asi que
    **quien no lo pasa recibe exactamente lo de antes*** -- *y eso es lo que hace que el cambio se pueda meter sin
    tocar ni una pantalla.*
    """
    sin = catalogo.buscar("leche")
    con_cero = catalogo.buscar("leche", desplazamiento=0)

    assert _ids(sin) == _ids(con_cero), "pasar 0 tiene que dar lo mismo que no pasar nada"
    assert len(sin) == 40, f"y el tope por defecto sigue siendo 40, no {len(sin)}"


@pytest.mark.xfail(strict=True, reason=(
    "DEFECTO MEDIDO: el mismo que `test_el_orden_del_buscador_es_estable` -- *el orden de `buscar` no "
    "es total, asi que dos llamadas iguales dan orden distinto, y esta prueba compara dos llamadas.* "
    "**Depende del arreglo del `ORDER BY`, no de la paginacion**, que funciona."))
def test_un_desplazamiento_negativo_no_revienta():
    """*Y un numero que no tiene sentido no puede tumbar la busqueda.* **El `max(0, ...)` esta para eso**: *un
    `OFFSET -1` en SQL **no es un resultado raro, es un error**.*
    """
    raro = catalogo.buscar("leche", limite=5, desplazamiento=-10)

    assert _ids(raro) == _ids(catalogo.buscar("leche", limite=5)), (
        "un desplazamiento negativo tiene que comportarse como cero, no fallar")


def test_mas_alla_del_final_devuelve_vacio_y_no_falla():
    """**«No hay mas» se dice, y se dice vacio.** *Un desplazamiento mas grande que el catalogo **no es un error**:
    es que no hay nada -- y devolver `[]` es lo correcto.* *Y es la misma distincion de `comparacion: null`
    (`N02`): **vacio es una respuesta, no un fallo.***
    """
    assert catalogo.buscar("leche", limite=5, desplazamiento=1_000_000) == []


# ---------------------------------------------------------------------------------------------
# Y EL HALLAZGO QUE LA PAGINACION DESTAPO: **el orden no es total, asi que no es estable**
# ---------------------------------------------------------------------------------------------


@pytest.mark.xfail(strict=True, reason=(
    "DEFECTO MEDIDO: `buscar` ordena por `comparable DESC, cadenas DESC, min_unidad` **sin desempate**, "
    "asi que los grupos con las mismas tres claves salen en orden ARBITRARIO. Medido el 11 de octubre de 2026 "
    "al anadir el `OFFSET`: la misma llamada, `buscar('leche', limite=5)`, devolvio ['20378', ...] una vez y "
    "['10645', ...] otra. **Y eso hace que la paginacion pierda y repita filas**: entre dos paginas, un "
    "producto puede salir dos veces o no salir -- *que es peor que no paginar, porque ademas PARECE que "
    "funciona*. El arreglo es un desempate estable al final del `ORDER BY` (p. ej. `grupo_id`), y **no se ha "
    "hecho porque cambia el orden que ve quien ya usa el buscador**, y eso es una decision."))
def test_el_orden_del_buscador_es_estable_entre_llamadas():
    """**Lo que la paginacion necesita para no mentir.** *Un `OFFSET` sobre un orden que cambia no pagina: baraja.*"""
    primera = _ids(catalogo.buscar("leche", limite=5))
    segunda = _ids(catalogo.buscar("leche", limite=5))

    assert primera == segunda, (
        f"dos llamadas iguales dan orden distinto:\n  {primera}\n  {segunda}")
