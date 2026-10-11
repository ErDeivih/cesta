"""**Lo que publica Día: la tabla de nutrición entera, con unidades.**

Por que existe, y que error corrige
-----------------------------------
En la ronda 31 escribi, y quedo commiteado, que *«ninguna cadena publica nutricion numerica»*. **Es
falso**, y lo era por un error de metodo que conviene dejar escrito: *generalice desde Mercadona,
Alcampo y Aldi -- tres cadenas que efectivamente no la publican -- **sin mirar las claves de Dia**, que
tenia cuatro ficheros JSON ya clasificados y sin inspeccionar.*

**Dia SI publica la tabla entera**, medida sobre el crudo de hoy:

    kilo_calories   {"name": "Kcal",                  "uom": "kcal", "value": 54}
    energy          {"name": "Valor Energetico (KJ)", "uom": "kJ",   "value": 257}
    fat             {"name": "Grasas",                "uom": "g",    "value": 3.5}
    carbohydrate    {"name": "Hidratos de carbono",   "uom": "g",    "value": 4.0}
    sugars          {"name": "Azucares",              "uom": "g",    "value": 4.0}
    protein         {"name": "Proteinas",             "uom": "g",    "value": 3.3}
    salt            {"name": "Sal",                   "uom": "g",    "value": 0.1}
    ingredients     {"name": "Ingredientes",          "value": "<p>...</p>"}

**La forma es la misma para todos**: un diccionario con `name`, `value` y -- en los nutrientes -- `uom`.
*Asi que leerlos es un solo patron, y anadir un nutriente que hoy no se lea es una linea.*

*Y los nombres vienen en espanol y con el `uom` al lado: no hay que traducir ni suponer unidades.*

Lo que NO hace
--------------
**No baja nada de la red**: lee el JSON que el colector ya guardo. **No convierte unidades** -- devuelve el
`uom` que la fuente declara, para no inventar una conversion --. *Y **no rellena** lo que la fuente no
trae: medido, los nutrientes estan en 3 de las 4 fichas, y en la cuarta no aparecen.*
"""
from __future__ import annotations

import re

RE_ETIQUETA = re.compile(r"<[^>]+>")
RE_ESPACIOS = re.compile(r"[ \t]{2,}")
RE_ANTES_DE_PUNTO = re.compile(r"\s+([.,;:)])")

# **Los nutrientes que se leen, y su nombre para dentro.** *La lista es la que publica Dia, medida; el
# diccionario se recorre entero, asi que anadir uno es anadir una linea aqui.*
NUTRIENTES = {
    "kilo_calories": "kcal",
    "energy": "energia_kj",
    "fat": "grasas",
    "saturated_fat": "grasas_saturadas",
    "carbohydrate": "hidratos",
    "sugars": "azucares",
    "protein": "proteinas",
    "salt": "sal",
    "fiber": "fibra",
}

# Y los de texto, que no son numeros.
TEXTOS = {
    "ingredients": "ingredientes",
    "storage_instructions": "conservacion",
}

# La identidad, para poder casar la ficha con el producto.
IDENTIDAD = {
    "sku_id": "id",
    "ean_code": "ean",
    "product_name": "nombre",
    "brand_description": "marca",
}


def sin_marcado(texto: str) -> str:
    """Quita el HTML y deja el texto legible. *Dia usa `<p>` y `<strong>`, y `&nbsp;` entre medias.*"""
    limpio = RE_ETIQUETA.sub("", texto).replace("&nbsp;", " ")
    limpio = RE_ESPACIOS.sub(" ", limpio)
    limpio = RE_ANTES_DE_PUNTO.sub(r"\1", limpio)
    return limpio.strip()


def _valor(campo) -> tuple[str | None, str | None]:
    """De un campo de Dia saca `(valor, unidad)`.

    **La fuente mezcla DOS formas, y medirlo costó un fallo de prueba.** Los nutrientes y los textos vienen
    como `{name, value, uom?}` -- pero **la identidad viene plana**: `"sku_id": "310847"`,
    `"ean_code": "8480017328212"`. *Aceptar sólo la forma con `value` dejaba fuera justo los campos que
    hacen falta para casar la ficha con el producto.*
    """
    if isinstance(campo, dict):
        if "value" not in campo:
            return None, None
        valor = campo.get("value")
        unidad = campo.get("uom")
    else:
        valor, unidad = campo, None      # la forma plana: la identidad
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        return None, None
    return str(valor), (str(unidad) if unidad else None)


def lee(cuerpo: dict) -> dict:
    """**Los campos de ficha que publica Dia**, leidos del JSON del colector.

    *Devuelve los nutrientes con su unidad al lado* -- `{"grasas": {"valor": 3.5, "uom": "g"}}` -- **para
    no inventar una conversion ni dar por hecho que todo viene en gramos.**

    *Y lo que la fuente no trae no aparece*: asi quien cuente cobertura no da por buena una ficha vacia.
    """
    if not isinstance(cuerpo, dict):
        return {}

    salida: dict = {}

    for clave, destino in IDENTIDAD.items():
        valor, _ = _valor(cuerpo.get(clave))
        if valor is not None:
            salida[destino] = sin_marcado(valor) if "<" in valor else valor

    for clave, destino in NUTRIENTES.items():
        valor, unidad = _valor(cuerpo.get(clave))
        if valor is None:
            continue
        # **El numero se devuelve como numero cuando lo es.** *Dia manda 3.3 como numero, pero podria
        # mandarlo como texto: se aceptan los dos y se decide por el contenido, no por el tipo.*
        try:
            numero = float(valor)
        except ValueError:
            numero = valor  # una etiqueta como "trazas" tambien es informacion
        salida[destino] = {"valor": numero, "uom": unidad} if unidad else {"valor": numero}

    for clave, destino in TEXTOS.items():
        valor, _ = _valor(cuerpo.get(clave))
        if valor is not None:
            salida[destino] = sin_marcado(valor)

    return salida


def los_nutrientes(leido: dict) -> dict:
    """Solo los numericos. *Para saber si una ficha sirve para enseñar una tabla.*"""
    return {k: v for k, v in leido.items() if k in set(NUTRIENTES.values())}


def la_tiene(cuerpo: dict) -> bool:
    """Si este cuerpo trae algo de ficha. *Para poder contar cuantos de los capturados la traen.*"""
    return bool(lee(cuerpo))
