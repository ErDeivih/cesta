"""**Que version del catalogo se sirve, sin arrastrar polars.**

Por que existe
--------------
`core/publicacion.py` sabe donde vive una version publicada, pero **importa polars**: escribe marcos
(`datos: dict[str, pl.DataFrame]`) y parquet. *Meterlo en la API para leer una ruta seria meter polars
en el proceso que atiende a quien compra.*

Y eso no es una precaucion teorica: `docs/SUPERAPP-ESTADO.md` lo deja escrito --
*«importar `publicacion` en la API»* traeria polars, que **«causo reinicios de `cesta-api` el 21 de
septiembre»** -- y el camino que el propio documento apunta es este: **«sacar la lectura a un modulo
pequeno sin polars que usen los dos»**.

**Este modulo no importa nada del proyecto.** Ni polars, ni `core.config`, ni `duckdb`. *Solo la
biblioteca estandar.* Es lo que permite comprobarlo con una prueba en vez de confiar en la intencion:
`test_no_arrastra_polars` mira `sys.modules` despues de importarlo.

Que resuelve, y que no
----------------------
**Resuelve rutas**, que es todo lo que hace falta para leer la version vigente:

    version_actual(puntero)                 el nombre de la version, o None
    carpeta_de(gold, version)               donde vive esa version
    ruta(gold, nombre, version=None)        el fichero, de la version o del gold suelto
    sello(gold, nombre, version=None)       su `mtime`, para cachear por el

**No publica, no mueve el puntero y no sabe de marcos.** *Eso se queda en `publicacion.py`, que es quien
escribe.*

*El fallback es el conservador de siempre*: **sin puntero se lee el catalogo suelto**, para que esto
pueda entrar sin migrar nada de golpe.
"""
from __future__ import annotations

import json
from pathlib import Path

# El nombre del puntero, que vive **dentro** de `data/gold` y al lado de las carpetas de version.
PUNTERO = "actual.json"


def version_actual(gold: Path) -> str | None:
    """**La version que se sirve**, o `None` si no hay ninguna publicada.

    *Un puntero ilegible o a medias se trata como si no hubiera*: el fallback -- leer el catalogo suelto
    -- es mejor que reventar la peticion de alguien porque un JSON quedo cortado.
    """
    try:
        datos = json.loads((gold / PUNTERO).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    version = datos.get("version")
    return str(version) if version else None


def publicado_en(gold: Path) -> str | None:
    """Cuando se movio el puntero. *Es lo que compara `/api/estado` para decir si hay coherencia.*"""
    try:
        datos = json.loads((gold / PUNTERO).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    momento = datos.get("publicado_en")
    return str(momento) if momento else None


def carpeta_de(gold: Path, version: str) -> Path:
    """Donde vive una version. `v` delante, como las nombra `publicacion._sello`."""
    return gold / f"v{version}"


def ruta(gold: Path, nombre: str, version: str | None = None) -> Path:
    """**El fichero de una version, o el suelto si no hay ninguna.**

    `version` explicito es lo que permite que **una peticion fije la suya**: *quien resuelve el puntero
    dos veces puede acabar leyendo `grupos` de una publicacion y `enlaces` de la siguiente, que es la
    mezcla que S01 prohibe.* **Quien llame con dos ficheros debe resolver la version una vez y pasarla.**
    """
    elegida = version if version is not None else version_actual(gold)
    if elegida is None:
        return gold / nombre
    return carpeta_de(gold, elegida) / nombre


def sello(gold: Path, nombre: str, version: str | None = None) -> float:
    """El `mtime` de lo que se lee, **para cachear por lo que de verdad cambio**.

    *Cachear por el `mtime` del gold suelto mientras se sirve una version es cachear por un fichero que
    puede no ser el que se lee: el dia que la API lea la version, la cache no se invalidaria al publicar
    -- que es justo cuando tiene que invalidarse.*
    """
    try:
        return ruta(gold, nombre, version).stat().st_mtime
    except OSError:
        return 0.0
