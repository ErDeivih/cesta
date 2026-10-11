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

from dataclasses import dataclass, field
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


# ---------------------------------------------------------------------------------------------
# El borrador: **la previa, que no escribe**
# ---------------------------------------------------------------------------------------------


@dataclass
class Borrador:
    """**Una receta importada, antes de guardarla.** *Y por eso **no es una receta**: no tiene `id`, no tiene
    version y **no esta en ninguna base** -- *se puede mirar, corregir y tirar sin dejar rastro.*

    Es la forma que el criterio pide con «**previa**, fuente, unidades y **edicion antes de guardar**»:
    *`core/recetas.crear` **escribe**, asi que **enseñar antes de decidir exige un objeto que no escriba*** --
    *la misma decision que `previa_compra` tomo en `F10`.*
    """

    nombre: str
    raciones: int
    ingredientes: list[dict] = field(default_factory=list)
    preparacion: str = ""
    minutos: int | None = None
    #: **De donde se importo.** *El criterio lo pide por su nombre -- «previa, **fuente**, unidades...» --, y
    #: es lo que hace que la receta se pueda **volver a comprobar** dentro de un ano.*
    fuente: str = ""
    #: *Lo que no se pudo leer, y **por que**.* *La misma forma que `sin_cantidad` y `sin_consolidar`: lo que
    #: falta **se dice**, y no se rellena con un cero.*
    faltantes: list[str] = field(default_factory=list)


def borrador(url: str | None, campos: dict | None = None) -> tuple[Permiso, Borrador | None]:
    """**La previa de una receta importada.** *Devuelve el permiso (para poder decir que no) y el borrador.*

    **No lee la red, no parsea HTML y no escribe**: *recibe los **campos ya extraidos** y los pone en la forma
    que `core.recetas.crear` espera.* *Lo que falta -- **el lector de cada sitio** -- no se puede escribir hasta
    que haya una fuente declarada, que es la decision del tablero.*

    **Tres cosas que hace, y las tres son del criterio:**

    1. **Comprueba la fuente primero**, y **si no esta permitida no construye nada** -- *no un borrador a
       medias: **`None`, y el motivo.***
    2. **Guarda la `fuente`**, que es lo que permite comprobarla despues.
    3. **Cuenta lo que falta en vez de inventarlo**: *sin nombre, o con un nombre vacio, **no hay borrador** --
       *una receta sin nombre no se puede leer en una lista.* *Sin raciones, se dice; y un ingrediente sin
       texto **no entra**, que es la misma regla de `core.recetas._ingredientes_para_guardar`.*
    """
    permiso = comprueba_fuente(url)
    if not permiso.permitida:
        return permiso, None

    campos = campos or {}
    faltantes: list[str] = []

    nombre = str(campos.get("nombre") or "").strip()
    if not nombre:
        # **Sin nombre no hay borrador.** *No se inventa «Receta importada»: una receta sin nombre en una lista
        # es una fila que nadie sabe que es.*
        return Permiso(False, "sin nombre no hay receta que previsualizar", host=permiso.host), None

    raciones = campos.get("raciones")
    if not isinstance(raciones, int) or raciones < 1:
        # *Y las raciones son al menos una, como en `core.recetas.crear`.* **Se dice y se pone una**, en vez de
        # dejar el campo en `None` y que reviente al guardar.
        faltantes.append("raciones (se asume 1)")
        raciones = 1

    ingredientes: list[dict] = []
    for uno in campos.get("ingredientes") or []:
        if not isinstance(uno, dict) or not str(uno.get("texto") or "").strip():
            # **Un ingrediente sin texto no entra**, y se dice: *es la regla de `recetas.crear`.*
            faltantes.append(f"ingrediente sin texto: {uno!r:.60}")
            continue
        ingredientes.append({
            "texto": str(uno["texto"]).strip(),
            "cantidad": uno.get("cantidad"),
            "unidad": uno.get("unidad"),
            # *Los enlaces al catalogo **se conservan si vienen**: son la trazabilidad de `R02`/`R07`.*
            "producto_id": uno.get("producto_id"),
            "grupo_id": uno.get("grupo_id"),
            "fuente": uno.get("fuente"),
        })

    if not ingredientes:
        faltantes.append("ningun ingrediente con texto")

    minutos = campos.get("minutos")
    return permiso, Borrador(
        nombre=nombre,
        raciones=raciones,
        ingredientes=ingredientes,
        preparacion=str(campos.get("preparacion") or ""),
        minutos=int(minutos) if isinstance(minutos, (int, float)) else None,
        fuente=str(url).strip(),
        faltantes=faltantes,
    )


# ---------------------------------------------------------------------------------------------
# El lector: **`application/ld+json` con `@type: Recipe`**
# ---------------------------------------------------------------------------------------------

#: **El formato que se lee, y por que ese.** *`schema.org/Recipe` en `application/ld+json` es **el estandar que
#: las webs de recetas publican para que las lean las maquinas** -- *no es un formato inventado aqui, y por eso es
#: el unico que se lee.* **Un sitio que no lo publique no se puede leer sin escribirlo a mano, y eso es scraping**:
#: *por eso «fuente permitida» y «formato» son la misma decision.*
TIPO = "Recipe"


def _texto(v) -> str:
    """*Un campo de schema.org puede venir como texto, como `{"@value": ...}` o como lista.* **Se acepta lo que
    es, y lo que no, se deja vacio -- no se inventa.**"""
    if isinstance(v, str):
        return v.strip()
    if isinstance(v, dict):
        return _texto(v.get("name") or v.get("@value") or v.get("text") or "")
    if isinstance(v, list) and v:
        return _texto(v[0])
    return ""


def _raciones(v) -> int | None:
    """**El numero de raciones, si lo dice.** *Y `None` si no -- `borrador` ya sabe decir «se asume 1»*."""
    if isinstance(v, (int, float)) and v >= 1:
        return int(v)
    s = _texto(v)
    if not s:
        return None
    m = __import__("re").search(r"\d+", s)
    return int(m.group(0)) if m else None


def campos_de_json_ld(datos) -> dict | None:
    """**Los campos de una receta de `schema.org`, en la forma que `borrador` entiende.**

    *Devuelve `None` si el objeto **no es una receta** -- *que es distinto de «es una receta vacia»*. *Y acepta
    tanto un objeto como la lista que muchas webs publican (`@graph`), **buscando dentro al que es `Recipe`***.
    """
    if isinstance(datos, list):
        for uno in datos:
            hallado = campos_de_json_ld(uno)
            if hallado is not None:
                return hallado
        return None
    if not isinstance(datos, dict):
        return None

    # *Muchas webs envuelven todo en `@graph`.*
    if "@graph" in datos:
        return campos_de_json_ld(datos["@graph"])

    tipo = datos.get("@type")
    tipos = [tipo] if isinstance(tipo, str) else (tipo if isinstance(tipo, list) else [])
    if TIPO not in tipos:
        return None

    # **Los ingredientes, tal cual vienen.** *Se convierten en `{texto, cantidad, unidad}` **con lo que se pueda
    # sacar del texto**, y **lo que no se pueda se deja en `None`** -- *no se inventa «1 unidad».*
    ingredientes = []
    for linea in datos.get("recipeIngredient") or []:
        texto = _texto(linea)
        if not texto:
            continue
        cantidad, unidad = _parte_cantidad(texto)
        ingredientes.append({"texto": texto, "cantidad": cantidad, "unidad": unidad})

    # *La preparacion: las instrucciones pueden venir como texto, como lista, o como lista de objetos con `text`.*
    pasos = datos.get("recipeInstructions") or []
    if isinstance(pasos, str):
        preparacion = pasos
    else:
        preparacion = "\n".join(_texto(p) for p in pasos if _texto(p))

    return {
        "nombre": _texto(datos.get("name")),
        "raciones": _raciones(datos.get("recipeYield")),
        "ingredientes": ingredientes,
        "preparacion": preparacion,
        # *Y el tiempo, si lo dice: `PT1H30M` -- **o `None`, que es no decirlo.***
        "minutos": _minutos_iso(datos.get("totalTime") or datos.get("cookTime")),
    }


#: *«200 g de harina» -> (200, 'g').* **Y si no hay cantidad, `(None, None)`** -- *que es lo que hace que `borrador`
#: pueda contar lo que falta en vez de inventarlo.*
_CANTIDAD = __import__("re").compile(r"^\s*([\d]+(?:[.,]\d+)?)\s*([A-Za-zÁÉÍÓÚÜáéíóúüñ]+)?")


def _parte_cantidad(texto: str) -> tuple[float | None, str | None]:
    """*Lo que se pueda sacar del principio de la linea, y nada mas.*"""
    m = _CANTIDAD.match(texto)
    if not m:
        return None, None
    try:
        n = float(m.group(1).replace(",", "."))
    except ValueError:
        return None, None
    return n, (m.group(2) or "").lower() or None


#: *`PT1H30M` -> 90.* **`None` si no es un tiempo ISO o no viene.**
_ISO = __import__("re").compile(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?")


def _minutos_iso(v) -> int | None:
    s = _texto(v)
    if not s:
        return None
    m = _ISO.fullmatch(s)
    if not m:
        return None
    dias, horas, minutos = (int(x) if x else 0 for x in m.groups())
    total = dias * 24 * 60 + horas * 60 + minutos
    return total or None


def lee_json_ld(html: str) -> dict | None:
    """**Los campos de la receta que hay en un HTML, o `None` si no hay ninguna.**

    *Busca los bloques `<script type="application/ld+json">`, los parsea y se queda con el que es `Recipe`.*
    **No adivina: si no hay `Recipe`, devuelve `None`** -- *y quien llama decide, con `borrador`, si eso es «no
    hay receta» o «no se pudo leer».*
    """
    import json
    import re

    for m in re.finditer(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', html or "",
                         re.S | re.I):
        try:
            datos = json.loads(m.group(1).strip())
        except (ValueError, TypeError):
            # *Un bloque que no es JSON **no es un fallo**: hay webs con varios, y alguno puede ser basura.*
            continue
        campos = campos_de_json_ld(datos)
        if campos is not None:
            return campos
    return None
