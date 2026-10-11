"""**El mapeo que faltaba: de los campos del maestro a los de la cola de fichas.**

Por que existe
--------------
F05 midio que **la cola cuenta como pendiente algo que ya esta hecho**: de los 6.292 pendientes de Dia,
**4.655 ya tienen ficha en el maestro**; de los 4.477 de Mercadona, **2.821**. *7.476 fichas de deuda falsa.*

*La causa no es un fallo de codigo: son **dos caminos** que no comparten estado.* El colector pide la ficha
de los productos que recorre y la guarda en el maestro; **la cola solo se entera si alguien llama a
`inventario.terminar`**, y solo lo llama el ejecutor de Lidl.

Para reconciliar hace falta marcar `correcto` con **el mismo hash** que usaria el ejecutor -- *porque el hash
es lo que detecta que el contenido cambio, y uno distinto haria que la proxima pasada creyera que todo
cambio* --. Y ese hash se calcula sobre `CAMPOS_DE_FICHA`:

    fichas_lidl.py:56   CAMPOS_DE_FICHA = ("nombre", "marca", "ean", "gtin_invalido",
                                           "descripcion", "url", "imagen")
    fichas_lidl.py:59   def _hash_util(datos): "|".join(... para k en CAMPOS_DE_FICHA ...)

**Esos nombres son normalizados. Los maestros usan los de su fuente** -- *Dia guarda `product_name`,
`brand_description`, `ean_code`; el `ingredients` de Mercadona es una cadena de texto con marcado* --. **Asi
que hay que traducir, y de eso va este modulo.**

Lo que hace, y lo que no
------------------------
**Traduce un registro de maestro a los campos de la ficha**, y **nada mas**: *no calcula el hash -- eso es de
quien reconcilia --, no toca la cola, y no baja nada de la red.*

*Y devuelve solo lo que encuentra*: **un campo que la fuente no trae no se inventa**, y **una cadena vacia no
es lo mismo que un campo ausente** a la hora de hashear -- *aqui si, porque `_hash_util` usa `or ""` para
todos* --, pero se respeta lo que hay para que el reconciliador pueda contarlo.
"""
from __future__ import annotations

import re

# **El marcado de los textos del maestro.** *Mercadona mete HTML en `ingredients`, y Dia en `ingredients`
# igual*: si el hash se calcula sobre el texto con `<p>`, dos lecturas del mismo contenido con distinto
# envoltorio darian hashes distintos.
RE_ETIQUETA = re.compile(r"<[^>]+>")


def sin_marcado(texto: str) -> str:
    """*El mismo criterio que `ficha_mercadona` y `ficha_dia`: las etiquetas se van, el texto se queda.*"""
    return RE_ETIQUETA.sub("", texto).replace("&nbsp;", " ").strip()


def _texto(valor) -> str:
    """Un campo del maestro, como texto. **Con marcado, se limpia.**"""
    if valor is None:
        return ""
    if isinstance(valor, dict):
        # La forma de Dia: `{"name": ..., "value": ...}`.
        valor = valor.get("value")
    if valor is None:
        return ""
    texto = str(valor)
    return sin_marcado(texto) if "<" in texto else texto


# **De donde sale cada campo de ficha, por cadena.** *Medido sobre los maestros reales:*
#   dia       -> `product_name`, `brand_description`, `ean_code` (medidos en la ronda 33)
#   mercadona -> el maestro no trae la forma de la ficha, trae lo suyo
#
# *Se deja explicito y por cadena a proposito*: **adivinar el nombre de un campo es como se escribe un
# mapeo que no casa**, y eso es peor que no reconciliar.
DE_MAESTRO = {
    "dia": {
        "nombre": ("product_name",),
        "marca": ("brand_description",),
        "ean": ("ean_code",),
        "descripcion": ("web_description", "advertising_description"),
    },
    "mercadona": {
        "nombre": ("display_name", "name"),
        "marca": ("brand",),
        "ean": ("ean",),
        "descripcion": ("description", "long_description"),
    },
}


def campos_de_ficha(fuente: str, registro: dict) -> dict:
    """**Traduce un registro del maestro a los campos que hashea la cola.**

    *Devuelve solo lo que encuentra.* Un campo del que la fuente no tenga nada **no aparece** -- *y
    `_hash_util` lo trata como cadena vacia, que es lo que hace con los suyos* --, asi que el hash sale igual
    se ponga o no.

    *Una cadena de fuente desconocida devuelve `{}`*: **mejor no reconciliar que reconciliar con un mapeo
    adivinado.**
    """
    if not isinstance(registro, dict):
        return {}
    mapa = DE_MAESTRO.get(fuente)
    if mapa is None:
        return {}

    salida: dict[str, str] = {}
    for campo, origenes in mapa.items():
        for origen in origenes:
            valor = registro.get(origen)
            if isinstance(valor, dict):
                valor = valor.get("value")
            if valor not in (None, ""):
                salida[campo] = _texto(valor)
                break
    return salida


def tiene_ficha(fuente: str, registro: dict) -> bool:
    """**Si el maestro ya tiene lo que la cola andaria a buscar.**

    *No basta con que el producto este*: **tiene que tener su dato**. Para Dia y Mercadona, el dato es el
    que trae la ficha -- *y un registro sin nada no puede contar como hecho, o el reconciliador marcaria
    `correcto` una ficha vacia.*
    """
    if not isinstance(registro, dict):
        return False
    # **El dato de la ficha**, con los nombres de cada maestro -- *los mismos que se midieron al escribir los
    # lectores*: `nutricion`/`nutricion_por` en Dia, `ingredients`/`allergens` en Mercadona.
    marcas = {
        "dia": ("nutricion", "ingredientes"),
        "mercadona": ("ingredients", "allergens", "ingredientes", "alergenos"),
    }.get(fuente, ())
    # **El dato de la ficha es lo que cuenta, y no hay respaldo.** *La primera version tenia uno -- «un
    # registro que ya trae campos de ficha traducibles tambien sirve» -- y **estaba mal**: un producto con
    # nombre y marca pero sin nutricion ni ingredientes **no tiene ficha**, y marcarlo `correcto` seria dar
    # por buena una ficha vacia.* **Lo cazo la prueba, no la lectura.**
    return any(registro.get(marca) for marca in marcas)
