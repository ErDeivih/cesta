"""Compartir una lista: quien entra, con que papel, y a quien NO se le toca el papel.

**Esto guarda un fallo que dejo a alguien sin su propia lista.** Medido el 28 de septiembre de
2026 con la puerta de las funciones, escribiendo **tu propio usuario** en «Compartir con quien ya
tiene cuenta»: `almacen.comparte` actualizaba tu fila de `lista_acceso` a `escribe`, y a partir de
ahi, con la cuenta de la prueba:

    GET  /api/listas          soy_dueno: true   papel: 'escribe'   (se contradicen)
    PATCH (renombrar)         200
    POST /invitacion          403 «solo quien la creo puede invitar»
    DELETE (borrarla)         403 «Solo quien la creo puede borrarla.»

Y la tarjeta de Compartir **desaparecia** de la pantalla, porque solo se pinta para el dueno: se
salia de ahi sin forma de volver, con una lista que ya no se podia borrar ni compartir.

**Por que esto se comprueba leyendo el codigo y no con una prueba de verdad.** El arreglo es una
condicion del SQL (`WHERE lista_acceso.papel <> 'dueno'` en el `DO UPDATE`), y **ninguna prueba de
`tests/` ejecuta SQL**: sustituyen PostgreSQL a proposito. Quien lo ejecuta de verdad es
`plataforma/prueba_e2e.py`, que siembra el caso entero contra una base desechable (y ahi esta la
comprobacion de comportamiento: papel `dueno`, 201 al invitar, 200 al borrar). Aqui se vigila lo
unico que el punta a punta no puede vigilar: que la condicion **siga escrita**, porque borrarla no
rompe ninguna prueba de este directorio y solo se notaria cuando alguien perdiera una lista.
"""
from __future__ import annotations

import pathlib

RAIZ = pathlib.Path(__file__).resolve().parents[1]
ALMACEN = RAIZ / "plataforma" / "api" / "almacen.py"
E2E = RAIZ / "plataforma" / "prueba_e2e.py"


def test_compartir_no_le_baja_el_papel_al_dueno():
    """La condicion del `DO UPDATE`, con el numero medido al lado."""
    fuente = ALMACEN.read_text(encoding="utf-8")
    assert "def comparte(" in fuente, "no encuentro la funcion que mete a alguien en la lista"
    assert "WHERE lista_acceso.papel <> 'dueno'" in fuente, (
        "falta la condicion que deja en paz la fila del dueno: sin ella, escribir tu propio "
        "usuario en «Compartir» te quita la lista (403 al invitar y al borrarla)")
    # El caso contado donde se lee. Se busca sobre el texto **sin los saltos de linea**, porque
    # en el docstring la fecha esta partida en dos lineas (y buscarla a pelo daba un FALLO que
    # era del instrumento, no del codigo).
    junto = " ".join(fuente.split())
    assert "dueno" in junto and "28 de septiembre de 2026" in junto, (
        "el caso que lo destapo tiene que estar contado donde se lee")


def test_compartir_devuelve_el_papel_que_queda_en_la_base():
    """No el que se pidio: si no, la pantalla no puede decir la verdad."""
    fuente = ALMACEN.read_text(encoding="utf-8")
    trozo = fuente.split("def comparte(", 1)[1].split("\ndef ", 1)[0]
    assert "SELECT papel FROM lista_acceso" in trozo, (
        "la funcion no vuelve a leer el papel: devolveria el que se pidio, y con el dueno eso "
        "es mentira")
    assert '"papel": fila["papel"] if fila else papel' in trozo, (
        "el papel que se devuelve no sale de la base")


def test_la_invitacion_no_le_toca_el_papel_a_quien_ya_esta_dentro():
    """El otro camino de entrada, que ya estaba bien y hay que dejar bien.

    Quien abre un enlace de invitacion estando ya dentro (el dueno, sin ir mas lejos) recibe un
    `ya_estabas` **antes** de insertar nada. Si esa salida temprana desapareciera, abrir tu propio
    enlace te bajaria a «escribe» igual que el otro camino.
    """
    fuente = ALMACEN.read_text(encoding="utf-8")
    trozo = fuente.split("def acepta_invitacion(", 1)[1].split("\ndef ", 1)[0]
    assert '"ya_estabas": True' in trozo, (
        "quien ya esta dentro tiene que salir por ahi, sin tocar su fila")
    posicion_salida = trozo.index('"ya_estabas": True')
    posicion_insert = trozo.index("INSERT INTO lista_acceso")
    assert posicion_salida < posicion_insert, (
        "la salida temprana esta despues del INSERT: abrir tu propio enlace te cambiaria el papel")


def test_el_punta_a_punta_mide_las_dos_consecuencias():
    """Y el comportamiento, donde se puede medir de verdad (contra PostgreSQL)."""
    e2e = E2E.read_text(encoding="utf-8")
    assert "compartir contigo mismo no te quita la lista" in e2e, (
        "el punta a punta no siembra el caso")
    for consecuencia in ("y sigo pudiendo invitar", "y sigo pudiendo borrarla"):
        assert consecuencia in e2e, f"el punta a punta no comprueba «{consecuencia}»"
