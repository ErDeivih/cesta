"""**El lector de la ficha de Carrefour: la tabla esta en atributos `data-*`.**

Medido en la ronda 77, pidiendo **una** ficha con `robots.txt` comprobado: la pagina de producto de Carrefour
**si trae nutricion**, y **los listados no** -- *por eso el crudo, que son 2.004 paginas de categoria, no
tenia ni una cifra.*

**Y no es una tabla HTML** (el `<table` sale 0): viene en atributos de un `div` de grafico.

    <h3 class="nutrition__info-title">Información nutricional</h3>
    <p class="nutrition-graph__info-text">Valores medios por 100 g.</p>
    <div data-cal="900 Kcal" data-fi="" data-fa="100 g" data-h="0 g"
         data-kj="3700 KJ" data-p="0 g" data-s="0 g" class="nutrition-graph__graphic-svg">

*Comprobado con aceite de oliva: **900 kcal y 100 g de grasa por 100 g**, que es lo que tiene el aceite.*
**Los numeros son reales, y la base es la comparable** -- *«por 100 g»*, que es lo que el proyecto exige para
poder ensenar una tabla sin mentir (`dia.py:_nutricion` rechaza las que no se pueden comparar).*

Lo que hace, y lo que no
------------------------
**Lee los `data-*` y devuelve los nutrientes con su unidad y la base.** *No baja nada de la red* -- *recibe el
HTML* --, y **no rellena lo que la fuente no trae**: *`data-fi=""` es fibra **vacia**, no cero, y la diferencia
importa* -- *un cero dice «no tiene», un vacio dice «no lo dice».*

*Es la misma regla que `ficha_dia` y `ficha_mercadona`: lo que falta se dice, no se rellena.*
"""
from __future__ import annotations

import re

# **Los campos de Carrefour, medidos.** *La clave es el atributo; el valor, su nombre para dentro.*
NUTRIENTES = {
    "cal": "kcal",
    "kj": "energia_kj",
    "fa": "grasas",
    "hc": "hidratos",
    "h": "hidratos",
    "p": "proteinas",
    "s": "sal",
    "fi": "fibra",
    "ag": "grasas_saturadas",
}

# El bloque donde viven, y la base.
RE_GRAFICO = re.compile(r"class=\"nutrition-graph__graphic-svg\"[^>]*>", re.I)
# Los atributos pueden ir **antes o despues** de la clase, asi que se busca el `div` entero por su clase.
RE_DIV = re.compile(r"<div\b[^>]*nutrition-graph__graphic-svg[^>]*>", re.I)
RE_ATRIBUTO = re.compile(r'data-([a-z]+)="([^"]*)"', re.I)
RE_BASE = re.compile(r"Valores medios por\s*([^.<]+)\.", re.I)
RE_TITULO = re.compile(r"Informaci[oó]n nutricional", re.I)

# **Una cifra de verdad.** *`"900 Kcal"`, `"100 g"`, `"0 g"` -- y `""` no lo es.*
RE_CIFRA = re.compile(r"^\s*(-?\d+(?:[.,]\d+)?)\s*([A-Za-z%]*)\s*$")


def _cifra(texto: str) -> tuple[float | None, str | None]:
    """De `"900 Kcal"` saca `(900.0, "Kcal")`. *De `""` saca `(None, None)`: **vacio no es cero**.*"""
    m = RE_CIFRA.match(texto or "")
    if not m:
        return None, None
    try:
        return float(m.group(1).replace(",", ".")), (m.group(2) or None)
    except ValueError:
        return None, None


def base(html: str) -> str | None:
    """**Por cuanto esta la tabla** -- *«Valores medios por 100 g» -> `"100 g"`.*

    *Sin la base, una tabla no se puede comparar con otra, y el proyecto ya decidio que ensenar una que no se
    puede comparar **es peor que no tenerla** (`dia.py:_nutricion`).*
    """
    m = RE_BASE.search(html or "")
    return m.group(1).strip() if m else None


def lee(html: str) -> dict:
    """**Los nutrientes de una ficha de Carrefour**, del HTML de su pagina de producto.

    *Devuelve cada nutriente con su valor y su unidad, y la base aparte.* **Lo que venga vacio NO aparece**:
    *`data-fi=""` significa que la fuente no lo dice, y poner un cero seria inventar un dato* -- *justo lo que
    el encargo prohibe.*
    """
    if not isinstance(html, str) or not html:
        return {}
    # **El bloque**, y solo ese: *buscarlo por su clase, porque los atributos pueden ir antes o despues.*
    div = RE_DIV.search(html)
    if not div:
        return {}
    if not RE_TITULO.search(html):
        # Una pagina sin el titulo de nutricion no es una ficha con tabla.
        return {}

    salida: dict = {}
    for atributo, valor in RE_ATRIBUTO.findall(div.group(0)):
        destino = NUTRIENTES.get(atributo.lower())
        if destino is None:
            continue
        numero, unidad = _cifra(valor)
        # **Vacio no es cero.** *Se salta, y por eso `data-fi=""` no saca fibra.*
        if numero is None:
            continue
        salida[destino] = {"valor": numero, "uom": unidad} if unidad else {"valor": numero}

    por = base(html)
    if por:
        salida["por"] = por
    return salida


def la_tiene(html: str) -> bool:
    """**Si esta pagina trae tabla.** *Para poder contar cuantas la traen sin leerlas enteras.*"""
    return bool([k for k in lee(html) if k != "por"])
