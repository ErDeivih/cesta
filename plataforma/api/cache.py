"""**La cache de lo caro, atada a la version de gold.**

Por que existe
--------------
La auditoria de la app del 5 de noviembre de 2026 (P1-1 y P1-2) midio lo que ya se
sabia en el panel pero no en la calle: `/api/producto` tardaba 1,5-5,9 s,
`/api/grupo` 1,5-6,0 s, `/api/ofertas-dudosas` **15,5 s** y las pestanas del panel
15-18 s. *No era la base de datos: era que **cada peticion reconstruia el CTE
`veredicto` entero sobre el gold**, y gold cambia una vez al dia.*

Asi que lo que hace falta no es una cache con fecha de caducidad: es **no repetir el
calculo mientras se sirve la misma publicacion**. *La version publicada esta en
`data/gold/actual.json` (`version`, p. ej. `20261104-144138`), y leerla es leer 864
bytes.*

Que se cachea, y que no
-----------------------
**Solo lo que depende de gold y cuesta**: la ficha de grupo, su explicacion, el
verificador de ofertas y las consultas del panel. *Lo que depende de la persona
-- favoritos, listas, diario, avisos -- no entra aqui y no puede entrar*: no es
caro por gold, y una cache compartida entre cuentas seria la forma mas tonta de
ensenarle a alguien el dato de otra persona.

**No se cachea lo que ya es barato** (una consulta por indice de 30 ms, como
`catalogo.producto`): *con 64 huecos, llenarlos de fichas de producto desalojaria
las fichas de grupo, que son las que cuestan medio segundo.* El limite no es un
numero al azar: esta puesto para que la cache no crezca con el trafico.

Como se invalida
----------------
Cada entrada lleva en la clave **la version de gold**, el nombre de la funcion y
los argumentos normalizados. *La version se comprueba en CADA llamada* (leer el
puntero y mirar el `mtime` de `grupos.parquet` son dos llamadas al sistema), y en
cuanto cambia **se tira la cache entera**: no hay entradas viejas conviviendo con
nuevas.

Se miran tres cosas y las tres son baratas:

    el puntero `actual.json`        la version publicada
    `mtime` de `grupos.parquet`     el fallback sin puntero, y una reescritura en
                                    el sitio: es la misma senal que usa
                                    `catalogo.conexion()` para rehacerse
    `mtime` de `matching/`          la explicacion del grupo sale de ahi y una
                                    pasada nueva del emparejador no toca `grupos`

*Se lee de `catalogo.AJUSTES` y no del objeto de `ajustes.py` a proposito*: las
pruebas sustituyen el de `catalogo`, y la cache tiene que mirar el mismo gold que
la conexion.

Hilos y tamano
--------------
FastAPI atiende en un pool de hilos, asi que el diccionario va detras de un
`threading.Lock`. *El calculo se hace **fuera** del candado*: dos peticiones
distintas pueden tardar a la vez, que es justo lo que no puede pasar si se
serializa todo. Con dos peticiones iguales a la vez se calcula dos veces la
primera vez; a partir de ahi, una.

El desalojo es **LRU** sobre `MAXIMO` entradas: se va la que menos se ha usado,
no la que llego antes. *Una cache sin tope es una fuga de memoria con buen
aspecto.*

Los valores se comparten, no se copian
--------------------------------------
Devolver el mismo objeto evita copiar 36 KB de ficha en cada peticion, y es
seguro **mientras nadie lo modifique**. Quien llame tiene que tratarlo como de
solo lectura: en las rutas se construye una respuesta nueva (`g | {...}`), no se
toca la cache. *Si algun dia hace falta mutar, se copia al salir, no aqui.*
"""
from __future__ import annotations

import functools
import threading
from collections import OrderedDict
from collections.abc import Callable
from typing import Any

from core import version_vigente

# Huecos. Con 64 caben de sobra las fichas que se repiten en una sesion (las
# pantallas de producto y de grupo son las mismas para media docena de productos
# por visita) y las consultas del panel, sin crecer con el trafico.
MAXIMO = 64

_candado = threading.Lock()
_entradas: OrderedDict[Any, Any] = OrderedDict()
_epoca: tuple | None = None
_aciertos = 0
_fallos = 0


def epoca_de_gold() -> tuple:
    """**Lo que identifica al gold que se esta sirviendo.** Cambia al publicar.

    *Se lee en cada llamada, y es barato*: un JSON pequeno y dos `stat`. La version
    del puntero es lo que invalida al publicar; el `mtime` de `grupos.parquet` es el
    fallback sin puntero (y el que hace que reescribir gold en el sitio tambien
    invalide); el de `matching/` cubre una pasada nueva del emparejador.
    """
    from . import catalogo

    gold = catalogo.AJUSTES.gold
    version = version_vigente.version_actual(gold)
    return (
        str(gold),
        version or "",
        version_vigente.sello(gold, "grupos.parquet", version),
        _sello_de_carpeta(gold / catalogo.CARPETA_MATCHING),
    )


def _sello_de_carpeta(carpeta) -> float:
    """El `mtime` de una carpeta, o 0.0 si no esta. Una carpeta que no existe no es un fallo."""
    try:
        return carpeta.stat().st_mtime
    except OSError:
        return 0.0


def _congela(valor: Any) -> Any:
    """Argumentos -> algo hashable y estable.

    *Una lista y una tupla con los mismos valores son la misma llamada*, y un
    diccionario se ordena para que `{"a": 1, "b": 2}` y `{"b": 2, "a": 1}` no
    ocupen dos huecos. Lo que no sea hashable se reduce a su `repr`, que es peor
    clave pero nunca revienta.
    """
    if isinstance(valor, dict):
        return ("dict", tuple(sorted(((_congela(k), _congela(v))
                                     for k, v in valor.items()), key=repr)))
    if isinstance(valor, (list, tuple)):
        return ("secuencia", tuple(_congela(v) for v in valor))
    try:
        hash(valor)
    except TypeError:
        return ("repr", repr(valor))
    return valor


def _clave(nombre: str, argumentos: tuple, opciones: dict) -> tuple:
    return (epoca_de_gold(), nombre, _congela(argumentos), _congela(opciones))


def recuerda(nombre: str, argumentos: tuple, calcula: Callable[[], Any]) -> Any:
    """El valor guardado para `(version de gold, nombre, argumentos)`, o `calcula()`.

    Es la primitiva; `cacheada` es el decorador que se usa en los modulos.
    """
    global _epoca, _aciertos, _fallos
    clave = _clave(nombre, argumentos, {})
    epoca = clave[0]
    with _candado:
        if epoca != _epoca:
            _entradas.clear()          # otra publicacion: lo guardado ya no vale
            _epoca = epoca
        if clave in _entradas:
            _entradas.move_to_end(clave)
            _aciertos += 1
            return _entradas[clave]
    valor = calcula()                  # fuera del candado: dos peticiones no se esperan
    with _candado:
        _fallos += 1
        if epoca != _epoca:
            # *Se publico otro gold MIENTRAS se calculaba*: lo de esta version ya no
            # vale, y guardarlo dejaria una entrada vieja ocupando un hueco.
            return valor
        _entradas[clave] = valor
        _entradas.move_to_end(clave)
        while len(_entradas) > MAXIMO:
            _entradas.popitem(last=False)
    return valor


def cacheada(funcion: Callable) -> Callable:
    """Envuelve una funcion cara para que se calcule una vez por version de gold."""
    nombre = f"{funcion.__module__}.{funcion.__qualname__}"

    @functools.wraps(funcion)
    def envuelta(*args, **kwargs):
        return recuerda(nombre, (args, kwargs), lambda: funcion(*args, **kwargs))

    return envuelta


def estadisticas() -> dict:
    """Aciertos, fallos y huecos ocupados. *Lo usa la prueba, y sirve para mirar.*"""
    with _candado:
        return {"aciertos": _aciertos, "fallos": _fallos,
                "entradas": len(_entradas), "epoca": _epoca}


def olvida() -> None:
    """Tira todo. Para las pruebas y para forzar una recarga a mano."""
    global _epoca, _aciertos, _fallos
    with _candado:
        _entradas.clear()
        _epoca = None
        _aciertos = 0
        _fallos = 0
