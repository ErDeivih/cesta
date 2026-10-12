"""F15: paginacion estable. Revision del 12/10: desempate corregido y datos controlados.

Las notas siguientes describen el hallazgo historico; las pruebas ya no son xfail.

El criterio (`docs/SUPERAPP-FASE2-EMPEZAR-AQUI.md:189`) pide: *«Medir busqueda/listas/fichas/graficas con
volumen real: **paginacion**, indices, cargas, tamanos JS y latencia.»*

**Y medido en la ronda 147, no habia paginacion**: *`buscar` tenia un `LIMIT` parametrizado y **ningun
`OFFSET`**, asi que **se veian los primeros 40 y los siguientes no se podian pedir**.* *Un tope corta; una
paginacion continua -- **no es lo mismo «se para» que «no hay mas»**.*

**El arreglo son tres lineas**, y estas pruebas fijan que **pagina de verdad** y que **quien no pase el
parametro no nota nada**.

## Y al escribirlas aparecio el defecto de verdad

**El `OFFSET` funciona. Lo que **no** funciona es el orden sobre el que se aplica.**

*`buscar` ordena por `comparable DESC, cadenas DESC, min_unidad` **sin desempate**, asi que los grupos con las
mismas tres claves salen **en orden arbitrario** -- y **la misma llamada devolvio `[20378, ...]` una vez y
`[10645, ...]` otra**.* **Sin orden total, paginar es peor que no paginar**: *un producto puede salir dos veces o
no salir, y ademas **parece** que funciona.*

**Y un detalle de instrumento que costo una suite en rojo**: *comparar **dos** llamadas **no basta** -- si
coinciden por azar, `xfail(strict=True)` da **XPASS** y la suite falla.* **Las de abajo comparan VEINTE.**
"""
from __future__ import annotations

import duckdb
import pytest

from plataforma.api import catalogo


@pytest.fixture(autouse=True)
def catalogo_controlado(monkeypatch):
    """Empates deliberados; no depende de los productos ni de las ofertas del dia."""
    con = duckdb.connect(":memory:")
    con.execute("""
        CREATE TABLE buscable AS SELECT
            i::INTEGER AS grupo_id, 'leche' AS texto, 'Leche' AS nombre,
            'Marca' AS marca, 'dia' AS fuente, 100 AS precio_cent,
            100 AS precio_unidad_cent, 'l' AS unidad_canon,
            true AS precio_comparable, true AS comparacion_fiable,
            NULL::VARCHAR AS nutriscore, NULL::VARCHAR AS nutricion,
            NULL::VARCHAR AS imagen, NULL::VARCHAR AS promo_txt,
            false AS promo_club, false AS promo_solo_online, false AS es_recall
        FROM range(30, 0, -1) t(i)
    """)
    monkeypatch.setattr(catalogo, "conexion", lambda: con)
    yield
    con.close()

#: *Cuanto se repite una llamada para saber si su orden es estable.* **Dos no basta; veinte si.**
VEINTE = 20


def _ids(filas: list[dict]) -> list[str]:
    return [str(f.get("grupo_id")) for f in filas]


# ----------------------------------------------------- la paginacion, que funciona ---


def test_dos_paginas_no_se_solapan():
    """**Lo que hace que sea paginacion y no un tope.** *Si las dos trajeran lo mismo, el `OFFSET` no haria nada.*"""
    primera = catalogo.buscar("leche", limite=5)
    segunda = catalogo.buscar("leche", limite=5, desplazamiento=5)

    assert primera and segunda, "las dos paginas tienen que traer algo"
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


def test_un_desplazamiento_negativo_no_revienta():
    """*Un numero que no tiene sentido no puede tumbar la busqueda.* **El `max(0, ...)` esta para eso**: *un
    `OFFSET -1` en SQL **no es un resultado raro, es un error**.*

    **Se mide lo que no depende del orden**: *que devuelve una pagina entera. Comparar los ids seria depender
    del defecto del `ORDER BY`, que es otra prueba.*
    """
    for raro in (-1, -10, -1_000_000_000):
        pagina = catalogo.buscar("leche", limite=5, desplazamiento=raro)
        assert len(pagina) == 5, f"con desplazamiento {raro} salieron {len(pagina)} filas, no 5"


def test_mas_alla_del_final_devuelve_vacio_y_no_falla():
    """**«No hay mas» se dice, y se dice vacio.** *Un desplazamiento mayor que el catalogo **no es un error**:
    es que no hay nada.* *Es la distincion de `comparacion: null` (`N02`): **vacio es una respuesta, no un
    fallo**.*
    """
    assert catalogo.buscar("leche", limite=5, desplazamiento=1_000_000) == []


# ------------------------- y EL DEFECTO QUE LA PAGINACION DESTAPO: el orden no es total ---


def test_el_orden_del_buscador_es_estable_entre_llamadas():
    """**Lo que la paginacion necesita para no mentir.** *Un `OFFSET` sobre un orden que cambia no pagina: baraja.*

    **Veinte intentos, y no dos**: *con dos, si coinciden por azar, `xfail(strict=True)` da XPASS y **falla la
    suite** -- que es exactamente lo que paso.*
    """
    vistas = {tuple(_ids(catalogo.buscar("leche", limite=5))) for _ in range(VEINTE)}

    assert len(vistas) == 1, (
        f"veinte llamadas iguales dieron {len(vistas)} ordenes distintos:\n"
        + "\n".join(f"  {v}" for v in list(vistas)[:3]))
    assert next(iter(vistas)) == ("1", "2", "3", "4", "5")


def test_el_desplazamiento_por_defecto_no_cambia_nada():
    """**La mitad que evita romper lo que ya funcionaba.** *`desplazamiento` vale `0` por defecto: quien no lo
    pasa recibe lo de antes.*
    """
    con_cero = {tuple(_ids(catalogo.buscar("leche", limite=5, desplazamiento=0))) for _ in range(VEINTE)}
    sin = tuple(_ids(catalogo.buscar("leche", limite=5)))

    assert len(con_cero) == 1 and con_cero.pop() == sin, (
        "`desplazamiento=0` tiene que dar lo mismo que no pasar nada, y de forma estable")
