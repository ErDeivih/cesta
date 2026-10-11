"""**Lo que Mercadona publica de verdad: ingredientes y alérgenos, en texto.**

Por que existe
--------------
F05 pedia *«medir situación actual por campo/cadena»* y *«no llamar toda ausencia "limitación de
fuente"»*. Medido, sobre el crudo que el colector **ya captura a diario**, el reparto es:

- **Las cifras** (kcal, grasas, hidratos, proteínas): **ninguna de las cinco cadenas medidas las publica.**
  *Eso sí es limitación de fuente, y no se arregla ejecutando la cola: no hay nada que pedir.*
- **Los ingredientes y los alérgenos**: **Mercadona y Día sí los publican, y ya están en disco.**
  *Eso se arregla extrayendo, y es lo que hace este módulo.*

**El nombre del campo engaña, y conviene decirlo aquí**: se llama `nutrition_information`, y **no contiene
información nutricional** -- contiene `allergens` e `ingredients`. *Leer el nombre y creerse lo que promete
fue un error real de esta fase, y está escrito en `docs/investigaciones/F05-cobertura-de-fichas.md` §9.*

Lo que llega, y lo que hay que limpiar
--------------------------------------
Los dos campos vienen **en texto con HTML dentro**, medido sobre ficheros reales:

    "allergens":   "Contiene <strong>soja y productos a base de soja</strong>. Contiene <strong>cereales..."
    "ingredients": "<strong>INGREDIENTES</strong>: Preparado de nata batida (<strong>leche</strong>..."

*Así que el trabajo no es sólo leer: es **quitar el marcado** y dejar texto que se pueda enseñar.* **Y las
etiquetas `<strong>` de Mercadona no son decorativas: marcan los alérgenos dentro de la lista de
ingredientes.** *Por eso se quitan sin perder el texto, y no se descarta nada.*

Lo que NO hace, y no se le atribuye
-----------------------------------
**No baja nada de la red**: lee el JSON que el colector ya guardó. **No escribe en la cola de fichas**:
devuelve lo que ha leído, y quien lo llame decide. *Y **no inventa** campos: si la fuente no trae
`allergens`, la clave no aparece, en vez de salir vacía -- que es la diferencia entre «no lo publica» y
«no lo hemos leído».*
"""
from __future__ import annotations

import re

# Mercadona mete el texto con marcado; y **el marcado marca los alérgenos**, así que se quita el tag y se
# conserva el texto. Se acepta cualquier etiqueta, no sólo `<strong>`: si mañana usan otra, sigue valiendo.
RE_ETIQUETA = re.compile(r"<[^>]+>")

# Los espacios que deja el marcado al desaparecer: `a </strong>.` no puede quedar como `a .`.
RE_ESPACIOS = re.compile(r"[ \t]{2,}")
RE_ANTES_DE_PUNTO = re.compile(r"\s+([.,;:)])")


def sin_marcado(texto: str) -> str:
    """Quita el HTML y deja el texto legible. *No descarta nada: el `<strong>` marca, no decora.*"""
    limpio = RE_ETIQUETA.sub("", texto)
    limpio = RE_ESPACIOS.sub(" ", limpio)
    limpio = RE_ANTES_DE_PUNTO.sub(r"\1", limpio)
    return limpio.strip()


def lee(cuerpo: dict) -> dict:
    """**Los campos de ficha que Mercadona publica**, leídos del JSON del colector.

    *Devuelve sólo lo que trae.* Un campo ausente **no aparece**, en vez de aparecer vacío: así quien lea
    el resultado puede distinguir **«la fuente no lo publica»** de **«lo publicamos en blanco»**, que es
    justo la distinción que F05 pide no perder.

    *Se acepta el cuerpo entero del producto, no sólo el bloque `nutrition_information`*: **los ficheros
    de Mercadona lo traen unas veces dentro y otras el `ingredients` de nivel 1 es `null`**, y leer de los
    dos sitios evita depender de cuál de las dos formas vino hoy.
    """
    if not isinstance(cuerpo, dict):
        return {}

    # El bloque donde viven, medido: `nutrition_information`. Y el de nivel 1 como respaldo.
    bloque = cuerpo.get("nutrition_information")
    if not isinstance(bloque, dict):
        bloque = {}

    salida: dict[str, str] = {}
    for clave, origen in (("ingredientes", "ingredients"), ("alergenos", "allergens")):
        texto = bloque.get(origen)
        if not isinstance(texto, str) or not texto.strip():
            texto = cuerpo.get(origen)          # el respaldo de nivel 1
        if isinstance(texto, str) and texto.strip():
            salida[clave] = sin_marcado(texto)

    # **Y la identidad, que hace falta para poder guardarlo en la cola.** *Sin esto, la ficha no se puede
    # casar con el producto al que pertenece.* Se aceptan los dos nombres que usa la fuente.
    for destino, nombres in (("id", ("id", "objectID")), ("ean", ("ean",)), ("nombre", ("display_name", "name"))):
        for nombre in nombres:
            valor = cuerpo.get(nombre)
            if valor not in (None, ""):
                salida[destino] = str(valor)
                break

    return salida


def la_tiene(cuerpo: dict) -> bool:
    """Si este cuerpo trae algo de ficha. *Para poder contar cuántos de los capturados la traen.*"""
    leido = lee(cuerpo)
    return "ingredientes" in leido or "alergenos" in leido
