"""F02 (fase 2): **la carrera del diario**, con dos conexiones a la vez.

Por que existe
--------------
La revision de fase 2 lo dejo escrito como hallazgo: *«clave de diario escrita tras el INSERT»*. Y es
exactamente eso. `core/diario.py:apunta` hacia:

    1. SELECT por (propietario, clave_operacion)  -> si estaba, se devuelve
    2. INSERT  ... **sin la clave**
    3. UPDATE  ... poniendo la clave            <- despues
    4. commit

**Con dos envios a la vez los dos pasos 1 no ven nada**, porque ninguno ha escrito todavia. Los dos
insertan su fila. Y al poner la clave, el indice unico parcial
`(propietario, clave_operacion) WHERE clave_operacion IS NOT NULL` **rechaza al segundo**: no se
deduplica, se falla. *Y la fila del que falla se queda sin clave, que es peor que fallar.*

Lo que se prueba aqui, y son dos cosas opuestas
-----------------------------------------------
- **la misma clave a la vez deja UNA entrada** y las dos respuestas dicen el mismo id;
- **claves distintas a la vez dejan DOS**, porque *dos meriendas iguales de verdad son dos* y una
  deduplicacion de mas seria tan grave como una de menos.

Es la carrera del almacen, con dos conexiones y una barrera. **No necesita PostgreSQL** y **no toca el
diario de casa**: cada prueba usa su fichero.
"""
from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

import pytest

from core import diario as motor

FECHA = "2026-10-11"


def _a_la_vez(ruta: Path, claves: list[str]) -> tuple[list[int], list[str]]:
    """Lanza un envio por clave **a la vez**, y devuelve los ids y los errores.

    *La barrera es lo que hace que sea una carrera y no una cola*: los hilos no empiezan de uno en uno,
    salen todos del mismo punto.
    """
    barrera = threading.Barrier(len(claves))
    salidas: list[int] = []
    errores: list[str] = []
    cerrojo = threading.Lock()

    def envia(clave: str) -> None:
        con = motor.conecta(ruta)
        try:
            barrera.wait(timeout=10)
            identificador = motor.apunta(con, "ana", FECHA, "comida", clave_operacion=clave,
                                         kcal=100)
            with cerrojo:
                salidas.append(identificador)
        except Exception as fallo:                      # noqa: BLE001 -- se quiere el texto, sea cual sea
            with cerrojo:
                errores.append(f"{type(fallo).__name__}: {fallo}")
        finally:
            con.close()

    hilos = [threading.Thread(target=envia, args=(c,)) for c in claves]
    for hilo in hilos:
        hilo.start()
    for hilo in hilos:
        hilo.join(timeout=20)
    return salidas, errores


def _cuantas(ruta: Path) -> int:
    con = sqlite3.connect(ruta)
    try:
        return int(con.execute(f"SELECT count(*) FROM {motor.TABLA}").fetchone()[0])
    finally:
        con.close()


def test_dos_envios_a_la_vez_con_la_misma_clave_dejan_una_entrada(tmp_path):
    """**El defecto, tal cual.** *Dos peticiones simultaneas con la misma clave son un reintento.*"""
    ruta = tmp_path / "carrera.sqlite"
    clave = "la-misma-para-los-dos"

    salidas, errores = _a_la_vez(ruta, [clave, clave])

    assert not errores, f"un reintento simultaneo no puede fallar: {errores}"
    assert len(salidas) == 2, f"los dos envios tienen que contestar: {salidas}"
    assert len(set(salidas)) == 1, f"y con el mismo id, porque es la misma entrada: {salidas}"
    assert _cuantas(ruta) == 1, "y en el diario hay UNA entrada, no dos"


def test_dos_envios_a_la_vez_con_claves_distintas_dejan_dos(tmp_path):
    """**El otro lado, y el que impide pasarse de listo.**

    *Dos meriendas iguales de verdad llevan claves distintas y son dos.* Si la carrera se arreglara
    deduplicando de mas, esto lo diria.
    """
    ruta = tmp_path / "distintas.sqlite"

    salidas, errores = _a_la_vez(ruta, ["una", "otra"])

    assert not errores, errores
    assert len(set(salidas)) == 2, f"dos claves distintas son dos entradas: {salidas}"
    assert _cuantas(ruta) == 2


def test_la_misma_clave_de_uno_en_uno_tampoco_duplica(tmp_path):
    """*Lo que ya funcionaba, para que el arreglo no lo rompa.*"""
    ruta = tmp_path / "seguidas.sqlite"
    con = motor.conecta(ruta)
    try:
        primera = motor.apunta(con, "ana", FECHA, "comida", clave_operacion="k", kcal=100)
        segunda = motor.apunta(con, "ana", FECHA, "comida", clave_operacion="k", kcal=100)
    finally:
        con.close()

    assert primera == segunda
    assert _cuantas(ruta) == 1


def test_la_misma_clave_con_otros_datos_no_devuelve_un_exito_falso(tmp_path):
    """**El tercer punto de F02**: *«misma clave con payload distinto produce conflicto o politica
    explicita, **no exito que parece guardar otro dato**»*.

    Devolver la entrada vieja en silencio seria lo peor de los dos mundos: *quien lo pidio creeria
    haber anotado lo suyo, y en el diario estaria lo de antes.* **El cliente no puede llegar aqui**
    --su regla es que un payload distinto lleva clave nueva, y esta probada-- pero **el servidor no
    puede depender de que el cliente sea correcto.**
    """
    ruta = tmp_path / "choque.sqlite"
    con = motor.conecta(ruta)
    try:
        primera = motor.apunta(con, "ana", FECHA, "comida", clave_operacion="k", kcal=100)
        with pytest.raises(ValueError, match="ya se uso con otros datos"):
            motor.apunta(con, "ana", FECHA, "comida", clave_operacion="k", kcal=999)
    finally:
        con.close()

    assert _cuantas(ruta) == 1, "el choque no puede dejar una segunda entrada"

    # **Y el reintento de verdad -- los mismos datos -- sigue devolviendo la misma entrada**, que es
    # lo que no se puede romper al arreglar esto.
    con = motor.conecta(ruta)
    try:
        assert motor.apunta(con, "ana", FECHA, "comida", clave_operacion="k", kcal=100) == primera
    finally:
        con.close()


def test_un_cero_no_es_lo_mismo_que_no_saberlo(tmp_path):
    """*La comparacion del reintento no puede confundir «no se sabe» con «cero».*

    Es la misma regla que el resto del diario: **dejar un campo en blanco no es anotar cero.** Si se
    compararan como iguales, un reintento que corrigiera un dato a `0` se tomaria por el mismo y no se
    guardaria la correccion.
    """
    ruta = tmp_path / "cero.sqlite"
    con = motor.conecta(ruta)
    try:
        motor.apunta(con, "ana", FECHA, "comida", clave_operacion="k", kcal=100)
        with pytest.raises(ValueError, match="ya se uso con otros datos"):
            motor.apunta(con, "ana", FECHA, "comida", clave_operacion="k", kcal=0)
    finally:
        con.close()
