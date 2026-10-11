"""F09 / `R02`: **la fuente permitida** -- la primera mitad del importar recetas.

El criterio (`docs/SUPERAPP-COMPETENCIA-Y-REA.md:102`) dice, y **empieza por aqui**:

> **URL/archivo de fuente permitida**; previa, **fuente**, unidades y edicion antes de guardar.

**Y medido el 11 de octubre de 2026** (`docs/investigaciones/F09-recetario.md` §4), *importar recetas **no existe**:
ni ruta, ni pantalla, ni `fuente` de receta* -- *el campo `fuente` que hay es **del ingrediente**, no de la receta.*

## Y lo primero que hay que escribir no es el lector: es **a quien se le puede leer**

**«Fuente permitida» no es un detalle del lector: es la **primera** cosa que el criterio nombra**, y es la que
decide **si el lector se puede escribir**. *Bajarse una receta de un sitio que no lo permite no es un problema
tecnico: es el problema.*

**Y por eso este modulo no lleva la lista: lleva el **mecanismo**, y la lista `FUENTES` **empieza vacia**.**

> **Nada esta permitido hasta que se declare.** *Un importador que por defecto acepta cualquier URL no tiene una
> politica de fuentes: tiene la politica de que **todo vale**, escrita en ningun sitio.*

**Es la misma disciplina que `diario.FUENTES`** (*cuatro valores, y una quinta es un `raise`*) **y que
`_acceso`**: *la regla **no se deja al cuidado de quien escribe** -- *se pone en el camino, y en un solo sitio.*

**Y lo que falta, dicho para no confundirlo con un olvido**: *la lista de fuentes es **una decision**, y va con
las cuatro que esperan en el tablero.* **Lo que estas pruebas fijan es que el mecanismo **rechaza lo no
declarado**, que es la mitad que no se puede equivocar.**
"""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

# ---------------------------------------------------------------------------------------------
# La lista, que empieza VACIA a proposito. *Ver el docstring del modulo.*
# ---------------------------------------------------------------------------------------------

#: **De donde se puede importar una receta.** *Vacio hasta que se decida: ver el docstring.*
#: *La clave es el **host** en minusculas, y el valor es **por que** se permite* -- *que es lo que
#: hace que la lista se pueda revisar dentro de un ano.*
FUENTES: dict[str, str] = {}

#: *Los esquemas que existen.* **`file` esta porque el criterio dice «URL/**archivo**», y `http`/`https`
#: porque es lo que se usa.** *Cualquier otro -- `ftp`, `data`, `javascript` -- **no se acepta**, y no
#: hace falta enumerarlos: **se acepta lo que esta en la lista**, no se rechaza lo que no.*
ESQUEMAS = ("http", "https", "file")


@dataclass
class Permiso:
    """**Si se puede leer esa fuente, y por que.** *Nunca un booleano suelto: el motivo viaja con él.*

    *Es la forma que el proyecto usa en `sin_cantidad`, `sin_consolidar` y `faltantes`: **lo que no se puede
    hacer se dice, con su razon** -- para que la pantalla lo pueda enseñar en vez de dejar a alguien mirando
    una lista sin la receta y sin entender por que.*
    """

    permitida: bool
    motivo: str
    host: str | None = None
    razon_declarada: str | None = None


def fuentes_permitidas() -> dict[str, str]:
    """*La lista, para poder enseñarla.* **Una politica que no se puede leer no se puede revisar.**"""
    return dict(FUENTES)


def comprueba_fuente(url: str | None) -> Permiso:
    """**Si esa direccion se puede leer.** *Y si no, por que no.*

    **Los motivos estan separados a proposito**, porque son **problemas distintos** y se arreglan distinto:

    - **no es una direccion** -- *el texto esta vacio o no se puede leer*
    - **el esquema no vale** -- *`ftp` no es una pagina web, y `javascript:` menos*
    - **el host no esta declarado** -- *es una web, y **no se ha decidido** si se puede*
    - **no tiene host** -- *`file://` sin ruta, o una direccion a medias*
    """
    if not url or not str(url).strip():
        return Permiso(False, "no es una direccion")

    trozos = urlparse(str(url).strip())

    if trozos.scheme.lower() not in ESQUEMAS:
        return Permiso(False, f"el esquema no vale: {trozos.scheme or '(ninguno)'}")

    host = (trozos.hostname or "").lower()

    # **`file` no tiene host, y se permite por el criterio** -- *«URL/**archivo** de fuente permitida»* --,
    # pero **con ruta**: un `file://` pelado no es un archivo.
    if trozos.scheme.lower() == "file":
        if not trozos.path:
            return Permiso(False, "archivo sin ruta")
        return Permiso(True, "archivo local", host="", razon_declarada="el criterio admite archivo")

    if not host:
        return Permiso(False, "no tiene host")

    if host not in FUENTES:
        return Permiso(False, f"la fuente no esta declarada: {host}", host=host)

    return Permiso(True, "declarada", host=host, razon_declarada=FUENTES[host])
