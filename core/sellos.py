"""Los sellos de un producto: sin gluten, vegano, ecologico, sin lactosa.

Por que esta en core y no en cada colector
------------------------------------------
Cada cadena los escribe a su manera ("Sin Gluten", "sin gluten", "Bio",
"Producto Ecologico", "Alternativa Vegetal") y todas quieren decir lo mismo. Si
cada colector normaliza por su cuenta, el filtro de la app acaba encontrando
unos productos y otros no, segun de donde vengan.

El hallazgo que hace util este fichero
--------------------------------------
Creiamos que los sellos solo podian venir de Open Food Facts, es decir, solo para
productos con codigo de barras. Es falso: **Alcampo y Carrefour los publican
ellos mismos**, y Alcampo no tiene ni un EAN. Medido el 17 de septiembre de 2026:

    alcampo     sin gluten 3.337 · vegano 2.405 · sin lactosa 1.105 · eco 1.052
    carrefour   sin gluten   908 · sin lactosa 267 · eco 218 · vegetal 106
    -----------------------------------------------------------------------
    las dos                                                          9.398
    Open Food Facts, por EAN                                         8.055

Y los de Alcampo llegan a productos donde OFF **nunca** podria llegar.
"""
from __future__ import annotations

import re
import unicodedata

# Nuestros nombres. Son los que salen en la interfaz y en el filtro.
SELLOS = ("sin-gluten", "sin-lactosa", "vegano", "vegetariano", "ecologico",
          "sin-azucar", "sin-sal", "halal", "kosher", "sin-aceite-palma")

# Como lo escribe cada cadena -> como lo llamamos nosotros.
#
# Por que son expresiones regulares y no un diccionario de subcadenas
# ------------------------------------------------------------------
# Hasta el 17 de septiembre de 2026 esto era un `dict` y se buscaba con
# `como_lo_escriben in texto`. El comentario de al lado prometia que "se exige
# que la etiqueta SEA el sello o lo contenga como palabra, no que se parezca".
# El comentario mentia: `in` es subcadena, no palabra. Con "eco" y "bio" dentro
# del diccionario, esto devolvia el sello *ecologico* para:
#
#     "Seco"        "Recambios"    "Marruecos"    "economico"    "Ecopack"
#
# Con etiquetas cortas y controladas (Alcampo, Carrefour) nunca llego a fallar,
# porque ninguna de sus etiquetas contiene esas letras por casualidad. Salto al
# leer texto libre: en la descripcion de Aldi "Origen: Marruecos" marcaba el
# producto como ecologico. Un filtro de dieta que se equivoca no es un filtro
# incomodo, es uno en el que no se puede confiar, asi que ahora cada sello es un
# patron con limites de palabra y con las flexiones que de verdad se escriben.
_PATRONES = {
    "sin-gluten": (r"\bsin gluten\b", r"\bgluten free\b", r"\b0% gluten\b"),
    "sin-lactosa": (r"\bsin lactosa\b", r"\b0[,.]?\d*%\s*(?:de\s+)?lactosa\b",
                    r"\bdeslactosad\w*", r"\blactose free\b"),
    "vegano": (r"\bveganos?\b", r"\bvegan\b", r"\balternativa vegetal\b",
               r"\b100% vegetal\b"),
    "vegetariano": (r"\bvegetarian\w*",),
    # "ecologic\w*" y "biologic\w*" cubren ecologico/ecologica/ecologicos. "bio"
    # y "eco" sueltos solo valen como palabra entera, que es como los escriben
    # las cadenas en una etiqueta ("BIO", "Eco"), nunca dentro de otra.
    "ecologico": (r"\becologic\w*", r"\bbiologic\w*", r"\bbio\b", r"\beco\b",
                  r"\borganic\w*"),
    "sin-azucar": (r"\bsin azucar\w*", r"\bsin azucares anadidos\b",
                   r"\b0% azucares\b", r"\bsugar free\b"),
    "sin-sal": (r"\bsin sal\b", r"\bsin sal anadida\b"),
    "halal": (r"\bhalal\b",),
    "kosher": (r"\bkosher\b",),
    "sin-aceite-palma": (r"\bsin aceite de palma\b", r"\bsin palma\b"),
}

# Los mismos sellos, pero leidos de PROSA (la descripcion que escribe la cadena)
# en vez de una etiqueta. Aqui hay que ser mas estricto: en una etiqueta "Eco"
# describe el producto, pero en una frase "con extracto de arroz ecologico" o
# "con aloe vera biologico" describe un INGREDIENTE, y marcar por eso el champu
# entero como ecologico es mentir. Solo entran las formas en las que la frase
# habla del producto.
_PATRONES_PROSA = {
    "sin-gluten": (r"\bsin gluten\b", r"\bgluten free\b",
                   r"\bproducto sin gluten\b"),
    "sin-lactosa": (r"\bsin lactosa\b", r"\bdeslactosad\w*"),
    "vegano": (r"\b100% vegano\b", r"\bapto para veganos\b", r"\bproducto vegano\b",
               r"\bveganos?\b"),
    "vegetariano": (r"\bapto para vegetarianos\b", r"\bproducto vegetariano\b"),
    "sin-azucar": (r"\bsin azucares anadidos\b", r"\bsin azucar anadid\w*\b",
                   r"\b0% azucares anadidos\b"),
    "sin-sal": (r"\bsin sal anadida\b",),
    "sin-aceite-palma": (r"\bsin aceite de palma\b",),
    # Nada de "ecologico" aqui. En prosa casi siempre califica a un ingrediente
    # y no al producto; los 57 que daba el texto de Aldi eran champus con aloe
    # vera "ecologico". El sello ecologico de verdad llega por el certificado,
    # que es un logotipo con auditoria detras.
}

# Como llama cada cadena a la conservacion.
_CONSERVACION = {
    "refrigerado": "refrigerado",
    "fresco": "refrigerado",
    "congelado": "congelado",
    "ultracongelado": "congelado",
    "ambiente": "ambiente",
    "temperatura ambiente": "ambiente",
}


def _plano(texto: str) -> str:
    sin = "".join(c for c in unicodedata.normalize("NFD", texto or "")
                  if unicodedata.category(c) != "Mn")
    return " ".join(sin.lower().split())


def _casan(texto: str, patrones: dict) -> set[str]:
    hallados = set()
    for nombre, exprs in patrones.items():
        if any(re.search(e, texto) for e in exprs):
            hallados.add(nombre)
    return hallados


def de_etiquetas(etiquetas) -> str | None:
    """Las etiquetas que publica una cadena -> nuestros sellos, separados por comas.

    Se devuelve ordenado y sin repetidos para que dos productos con los mismos
    sellos tengan exactamente el mismo texto, y un LIKE en la busqueda funcione
    sin sorpresas.
    """
    if not etiquetas:
        return None
    hallados: set[str] = set()
    for bruta in etiquetas:
        t = _plano(str(bruta))
        if t:
            hallados |= _casan(t, _PATRONES)
    return ",".join(sorted(hallados)) or None


def de_prosa(*textos) -> str | None:
    """Los sellos que se pueden leer de una descripcion escrita a mano.

    Aldi no publica etiquetas de dieta en ningun campo, pero su
    `shortDescription` dice cosas como "Sin gluten" o "Sin azucares anadidos" en
    1.295 productos. Se lee con el vocabulario restringido de `_PATRONES_PROSA`,
    frase a frase, para no juntar dos afirmaciones que estaban separadas por un
    punto.
    """
    hallados: set[str] = set()
    for texto in textos:
        for frase in re.split(r"[.;\n]", _plano(str(texto or ""))):
            if frase.strip():
                hallados |= _casan(frase, _PATRONES_PROSA)
    return ",".join(sorted(hallados)) or None


def conservacion_de(etiquetas) -> str | None:
    """Refrigerado, congelado o ambiente, si la cadena lo dice."""
    if not etiquetas:
        return None
    for bruta in etiquetas:
        t = _plano(str(bruta))
        for como_lo_escriben, el_nuestro in _CONSERVACION.items():
            if t == como_lo_escriben:
                return el_nuestro
    return None


# Frases con las que una cadena explica como se guarda algo, en orden: gana la
# primera que case, porque "conservar a -18 C; una vez descongelado, mantener
# refrigerado" es un congelado, no un refrigerado.
_CONSERVACION_PROSA = (
    ("congelado", (r"\bcongelad\w*", r"\bultracongelad\w*", r"-\s?18\s?[ºo°]?\s?c",
                   r"\bmantener en el congelador\b")),
    ("refrigerado", (r"\brefrigerad\w*", r"\ben (?:la )?nevera\b", r"\bentre 0",
                     r"\bde 0\s?[ºo°]?\s?c a 4", r"\bconservar en frio\b")),
    # "lugar fresco" a secas incluida a proposito: DIA escribe "Mantengase en
    # lugar fresco, seco y alejado de la luz" -- con coma -- y el patron de
    # "lugar fresco y seco" no la cazaba. En unas instrucciones de conservacion,
    # "lugar fresco" es siempre la despensa: la nevera se dice con "refrigerado",
    # "nevera" o "frio", y esos tres se comprueban antes que este bloque.
    ("ambiente", (r"\blugar fresco\b", r"\btemperatura ambiente\b",
                  r"\blugar seco\b", r"\bproteger de la luz\b",
                  r"\bsitio fresco\b", r"\blugar limpio y seco\b")),
)


def conservacion_de_prosa(texto) -> str | None:
    """Refrigerado, congelado o ambiente leido de una frase.

    Mercadona no tiene campo de conservacion, pero escribe
    `storage_instructions` en el 64 % de sus fichas: "Conservar a -18 ºC",
    "Una vez abierto, conservar refrigerado", "Conservar en lugar fresco y
    seco". Es la unica forma de saber si algo es congelado en Mercadona.

    El orden importa. Una frase de congelado suele mencionar tambien la nevera
    ("una vez descongelado, conservar refrigerado y consumir en 24 h"), asi que
    congelado se comprueba primero o la mitad de los congelados acabarian de
    refrigerados.
    """
    t = _plano(str(texto or ""))
    if not t:
        return None
    # "Una vez abierto, conservar refrigerado" describe un brik de zumo que vive
    # en el armario, no un refrigerado. Se quita la parte que habla de despues
    # de abrir antes de mirar nada; si el producto es congelado de verdad, lo
    # dice en la parte que queda ("conservar a -18 C").
    t = re.sub(r"\b(?:una vez|tras|despues de) (?:abierto|abrir|el envase abierto)\b[^.;]*",
               " ", t)
    for nombre, exprs in _CONSERVACION_PROSA:
        if any(re.search(e, t) for e in exprs):
            return nombre
    return None


def tiene(sellos: str | None, sello: str) -> bool:
    """Si un producto lleva un sello. Para filtrar sin montar otra tabla."""
    if not sellos:
        return False
    return sello in sellos.split(",")
