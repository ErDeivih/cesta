"""B00 · **El ensayo no destructivo que rechaza un DSN protegido.**

**Por que existe.** *El 13 de octubre de 2026 se perdieron **716 usuarios, 2529 listas y 2533 lineas** de la
base de pruebas* -- *y el error de entonces fue mio: pasarle a `plataforma/prueba_copia.py` un
`CESTA_POSTGRES` que apuntaba al `5434`, con lo que su e2e rehizo el esquema.*

**Y el fallo no fue del script: fue que nada impedia apuntarlo.**

*Asi que estos ensayos comprueban **el guardia**, no la base:* **no se conectan a nada, no escriben nada, y no
necesitan que Postgres este levantado.** *Se puede correr con Docker parado, que es justo cuando uno esta
tocando cosas y no deberia.*

*Y son la respuesta a la celda de B00 que pedia «ensayo no destructivo que rechaza DSN protegido».*
"""
from __future__ import annotations

import pytest

from plataforma.api.ajustes import PUERTOS_PROTEGIDOS, comprueba_que_es_una_prueba

# ================================================== lo que se rechaza ===


def test_rechaza_la_base_de_casa():
    """**El 5432 es la base de verdad.** *Un ensayo que rehace esquema no puede apuntarle, nunca.*"""
    with pytest.raises(ValueError) as fallo:
        comprueba_que_es_una_prueba("postgresql://cesta:cesta@localhost:5432/cesta")
    assert "5432" in str(fallo.value)
    assert "la base de casa" in str(fallo.value)


def test_rechaza_facylf():
    """**El 5433 es de otro proyecto**, y el encargo pide no tocarlo."""
    with pytest.raises(ValueError) as fallo:
        comprueba_que_es_una_prueba("postgresql://alguien:x@127.0.0.1:5433/facylf")
    assert "5433" in str(fallo.value)
    assert "facylf" in str(fallo.value)


def test_rechaza_un_dsn_sin_puerto():
    """**«No se sabe» no es «es de pruebas».** *Un DSN sin puerto no dice donde apunta.*"""
    with pytest.raises(ValueError) as fallo:
        comprueba_que_es_una_prueba("postgresql://cesta:cesta@localhost/cesta")
    assert "no dice su puerto" in str(fallo.value)


def test_rechaza_un_dsn_vacio():
    """*Y sin DSN, menos todavia:* **no hay nada que comprobar.**"""
    with pytest.raises(ValueError) as fallo:
        comprueba_que_es_una_prueba("")
    assert "sin DSN" in str(fallo.value)


# ================================================== lo que se acepta ===


def test_acepta_el_5434():
    """**La de pruebas.** *La unica que un ensayo puede rehacer.*"""
    comprueba_que_es_una_prueba("postgresql://cesta:prueba@127.0.0.1:5434/cesta")


def test_acepta_otro_puerto_que_no_este_en_la_lista():
    """*El guardia comprueba **los tres puertos conocidos**, no «solo el 5434».*

    **Y eso es a proposito**: *una base de pruebas distinta -- en un contenedor nuevo, o en otro puerto -- no
    tiene por que estar prohibida.* **Lo que se prohibe es lo que se sabe que es de verdad.**
    """
    comprueba_que_es_una_prueba("postgresql://cesta:prueba@127.0.0.1:5555/cesta")


# ================================================== y la lista, dicha ===


def test_la_lista_de_protegidos_es_la_que_es():
    """**Y se comprueba la lista, no solo su efecto.** *Si alguien anade un puerto o lo quita, esto lo dice.*

    *Porque el guardia vale lo que vale su lista*, y la lista es lo unico que hay que revisar cuando la casa
    cambie de puertos.
    """
    assert set(PUERTOS_PROTEGIDOS) == {"5432", "5433"}, (
        "los protegidos son la base de casa (5432) y facylf (5433); "
        f"si esto cambia, revisa por que: {sorted(PUERTOS_PROTEGIDOS)}")
    # *Y las dos llevan su motivo*, para que el error pueda decirlo en vez de dar un numero.
    for puerto, motivo in PUERTOS_PROTEGIDOS.items():
        assert motivo.strip(), f"el puerto {puerto} no dice por que esta protegido"
