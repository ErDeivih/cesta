"""F07 (fase 2): **dos sesiones del mismo hogar, la misma linea.**

El criterio (`docs/SUPERAPP-FASE2-EMPEZAR-AQUI.md:125`) dice:

> Dos usuarios concurrentes del mismo hogar **no pisan cantidades ni tachados**; conflictos claros, sin
> empujar[se].

*Y leer `almacen.cambia_linea` (§2 de `docs/investigaciones/F07-compra-familiar.md`) dejo una asimetria que
estas pruebas convierten en un dato:*

```
421  if tachado is True:
423      # COALESCE: si ya estaba tachado, se respeta el primero.
424      trozos.append("tachado_en = LEAST(COALESCE(tachado_en, %s), %s)")   <- gana el PRIMERO
430  if cantidad is not None:
431      trozos.append("cantidad = %s")      # gana el ultimo, a proposito   <- gana el ULTIMO
```

**El tachado cumple el criterio; la cantidad, segun como se lea, no.** *Y lo que decide no es la opinion: es
que pasa de verdad.*

*Van contra el Postgres de verdad, y crean su propio usuario y su propia lista: **no tocan datos de nadie**.*
"""
from __future__ import annotations

import time
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from plataforma.api import almacen

# **Dos horas de movil**, con la de `antes` anterior a la de `despues`.
AHORA = datetime(2026, 10, 26, 18, 30, tzinfo=timezone.utc)
ANTES = AHORA - timedelta(minutes=40)
DESPUES = AHORA


def _una_lista(nombre: str):
    """Una cuenta y una lista nuevas, con una linea. *De quien ejecuta las pruebas, y de nadie mas.*"""
    # **Un sufijo por ejecucion**: *los usuarios viven en Postgres y no se borran, asi que el segundo
    # pase chocaba con `UsuarioRepetido`. Es el mismo detalle que el ensayo de F03 resuelve con su hora.*
    sello = f"{int(time.time() * 1000) % 100000000}"
    usuario = almacen.crea_usuario(f"f07-{nombre}-{sello}", f"Prueba F07 {nombre}",
                                   "clave-de-prueba-123")
    # `crea_usuario` puede devolver el id o un diccionario: se admiten las dos formas.
    identificador = usuario["id"] if isinstance(usuario, dict) else usuario
    lista = almacen.crea_lista(identificador, f"Prueba F07 {nombre}")
    lista_id = lista["id"] if isinstance(lista, dict) else lista
    # **El id de una linea es un UUID**: *lo dijo Postgres -- «invalid input syntax for type uuid:
    # "linea-1"» --, y es el mismo error de siempre: dar por hecho el tipo de un dato sin leerlo.*
    linea = str(uuid.uuid4())
    almacen.anade_linea(lista_id, identificador, linea, "Brick de leche", cantidad=1)
    return identificador, lista_id, linea


def _linea(lista_id: str, linea: str) -> dict:
    for fila in almacen.lineas_de(lista_id):
        if str(fila.get("id") if isinstance(fila, dict) else "") == linea:
            return fila
    raise AssertionError(f"la linea {linea} no esta en la lista: {almacen.lineas_de(lista_id)}")


@pytest.fixture(scope="module", autouse=True)
def _arrancado():
    almacen.arranca()
    yield
    almacen.para()


# ---------------------------------------------------------------------------------------------
# La cantidad
# ---------------------------------------------------------------------------------------------


def test_la_cantidad_vieja_no_gana_por_llegar_despues():
    """**La pregunta de F07, en el orden que importa.**

    *Dos personas cambian la cantidad de la misma linea sin cobertura:* **la primera a las 17:50 (pone 3), la
    segunda a las 18:30 (pone 5)** -- *y por lo que sea, **la de las 17:50 llega al servidor DESPUES**.*

    **Si gana la de las 18:30, `momento` sirve y el criterio se cumple.** *Si gana la que llego ultima -- la de
    las 17:50 -- entonces **el orden de los hechos se lo inventa el servidor**, que es justo lo que el
    comentario del tachado dice que no hay que permitir.*
    """
    usuario, lista_id, linea = _una_lista("cantidad-orden")
    # La de las 18:30 (mas nueva) llega PRIMERO.
    almacen.cambia_linea(lista_id, linea, usuario, cantidad=5, momento=DESPUES)
    # Y la de las 17:50 (mas vieja) llega DESPUES.
    almacen.cambia_linea(lista_id, linea, usuario, cantidad=3, momento=ANTES)

    cantidad = _linea(lista_id, linea)["cantidad"]

    # **ARREGLADO, y la regla esta escrita.** *Estuvo en `xfail(strict=True)` desde que se midio, con el
    # defecto nombrado -- «gana la ultima que LLEGA y no la mas nueva» --, y **al arreglarse la prueba fallo
    # por pasar, que es exactamente lo que se buscaba.***
    #
    # *Ahora la cantidad mira `momento` contra `cantidad_en`, que trae la migracion `019`*: **una cantidad
    # vieja que llega tarde no se escribe.** *Y usa `GREATEST`, al contrario que el `LEAST` del tachado*
    # -- porque tachar es «yo lo hice primero» y la cantidad es «este es el valor de ahora».
    assert cantidad == 5, (
        f"gana la que llego ultima (3), no la mas nueva (5): la cantidad NO mira `momento`. Medido: {cantidad}")


def test_la_cantidad_nueva_gana_si_llega_despues():
    """*El otro orden, para que la prueba anterior no pase por casualidad.*"""
    usuario, lista_id, linea = _una_lista("cantidad-normal")
    almacen.cambia_linea(lista_id, linea, usuario, cantidad=3, momento=ANTES)
    almacen.cambia_linea(lista_id, linea, usuario, cantidad=5, momento=DESPUES)

    assert _linea(lista_id, linea)["cantidad"] == 5


# ---------------------------------------------------------------------------------------------
# El tachado -- que es donde esta el diseno bueno
# ---------------------------------------------------------------------------------------------


def test_el_tachado_gana_el_primero_aunque_llegue_segundo():
    """**Lo que el criterio pide, y esta cumplido.** *«Si los dos tachais a la vez, gana quien lo hizo antes y
    el otro ve lo que queria ver.»*

    **La de las 18:30 llega primero y tacha; la de las 17:50 llega despues y tacha tambien.** *`LEAST` +
    `COALESCE` tienen que dejar la hora de las 17:50* -- *la del movil, no la de llegada.* **Y las dos ven la
    linea tachada: nadie recibe un error ni se deshace lo del otro.**
    """
    usuario, lista_id, linea = _una_lista("tachado")
    almacen.cambia_linea(lista_id, linea, usuario, tachado=True, momento=DESPUES)
    almacen.cambia_linea(lista_id, linea, usuario, tachado=True, momento=ANTES)

    fila = _linea(lista_id, linea)
    assert fila["tachado_en"] or fila.get("en_carrito"), (
        f"los dos tacharon y la linea no queda tachada: {fila}")
    # **La hora, la del movil mas antiguo.**
    tachado_en = fila.get("tachado_en")
    if tachado_en is not None:
        momento = tachado_en if isinstance(tachado_en, datetime) else datetime.fromisoformat(str(tachado_en))
        assert momento.replace(tzinfo=momento.tzinfo or timezone.utc) <= DESPUES, (
            f"la hora tiene que ser la del movil que lo hizo antes, y es {momento}")


def test_tachar_dos_veces_no_es_un_error():
    """*«Idempotente a proposito: tachar algo ya tachado no hace nada y no es un error.»*

    **Es lo que pasa cuando la red va y viene en el pasillo**: *el movil sube lo mismo dos veces.*
    """
    usuario, lista_id, linea = _una_lista("idempotente")
    primera = almacen.cambia_linea(lista_id, linea, usuario, tachado=True, momento=ANTES)
    segunda = almacen.cambia_linea(lista_id, linea, usuario, tachado=True, momento=DESPUES)

    assert primera is not None and segunda is not None, "la segunda vez no puede fallar"
    assert _linea(lista_id, linea)["en_carrito"], "y la linea sigue tachada"


def test_destachar_gana_siempre_sin_mirar_la_hora():
    """**La asimetria que §2 dejo escrita, ahora medida.** *`tachado is False` **borra la hora sin mirar
    `cuando`*** -- *asi que destachar gana sobre tachar sin importar el orden.*

    *Puede ser correcto* -- *destachar es una accion deliberada* --, **pero es una asimetria, y conviene que
    este dicha en vez de descubierta.**
    """
    usuario, lista_id, linea = _una_lista("destachar")
    almacen.cambia_linea(lista_id, linea, usuario, tachado=True, momento=DESPUES)
    # La de la hora VIEJA destacha, y llega despues.
    almacen.cambia_linea(lista_id, linea, usuario, tachado=False, momento=ANTES)

    fila = _linea(lista_id, linea)
    assert not fila["en_carrito"], (
        "destachar gana siempre: no mira la hora. Medido y anotado como asimetria deliberada")
