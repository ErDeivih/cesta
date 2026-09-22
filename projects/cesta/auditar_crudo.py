"""Que campos guarda cada cadena en data/raw y cuales no lee nadie.

Por que existe este fichero
---------------------------
Siete veces seguidas, al mirar el crudo a mano, ha aparecido un dato que ya
estaba descargado y que ningun colector leia:

    el precio por kilo de Alcampo        17,2 % -> 100 %
    la marca de Aldi                          0 % -> 91 %   (229 marcas)
    los packs de DIA anunciados en el nombre           211 productos
    las ofertas de Carrefour, con fecha de fin       3.387 productos
    la tabla nutricional de DIA                      3.685 productos
    los 32 certificados de Aldi                      1.106 productos
    el envase y la conservacion de Mercadona         3.452 / 1.785

Siete de siete. Eso ya no es mala suerte: es que **nadie mira**. Y mirar a mano
depende de que a alguien se le ocurra, que es justo lo que no se puede
planificar. Asi que se automatiza:

    uv run python -m projects.cesta.auditar_crudo
    uv run python -m projects.cesta.auditar_crudo --fuente dia --minimo 5

Que hace exactamente
--------------------
1. Abre el crudo del ultimo dia de cada cadena y saca los productos con la misma
   funcion que usa el reprocesador, o sea con el parser de verdad.
2. Aplana cada producto a rutas con puntos (`currentPrice.validUntil`) y cuenta
   en que porcentaje de productos aparece con valor.
3. Lee el codigo fuente del colector y saca todas las claves que pide, esten
   como `.get("x")` o como `p["x"]`.
4. Enseña lo que pasa del umbral y **no** esta en el codigo.

Es una heuristica, no un demostrador: una clave leida por una variable no se ve.
Falla hacia el lado bueno -- avisa de mas, nunca de menos -- que es lo que
interesa en una herramienta de auditoria.
"""
from __future__ import annotations

import argparse
import glob
import gzip
import importlib
import json
import os
import re
from collections import Counter

from core import config

FUENTES = ("alcampo", "aldi", "carrefour", "dia", "mercadona")

# Claves que no son datos del producto: identificadores internos, marcas de
# tiempo del CDN, restos de maquetacion. Avisar de ellas solo hace ruido.
# Se comprueba contra la hoja de la ruta (lo que va detras del ultimo punto) y
# tambien contra la ruta entera, porque el ruido aparece de las dos formas:
# "objectID" es una hoja, "criteo.plpData.results" es una rama.
RUIDO = re.compile(
    r"(^_|\._|"
    r"\b(?:id|ids|uuid|hash|etag|version|revision|typename|slug|order|level|"
    r"priority|imageid|promoid|skuid|objectid|sku_id|object_id)$|"
    r"seo|meta[A-Z]|tracking|analytics|criteo|gtm|utm|srcset|resolution)",
    re.IGNORECASE)

MAX_PROFUNDIDAD = 3
MAX_FICHEROS = 400          # de sobra para medir un porcentaje


def _aplana(valor, prefijo: str = "", nivel: int = 0) -> dict:
    """{'currentPrice.priceValue': 3.99}. Las listas se miran por su primer item."""
    if nivel >= MAX_PROFUNDIDAD:
        return {prefijo: valor} if prefijo else {}
    if isinstance(valor, dict):
        salida = {}
        for k, v in valor.items():
            salida.update(_aplana(v, f"{prefijo}.{k}" if prefijo else str(k), nivel + 1))
        return salida
    if isinstance(valor, list):
        if not valor:
            return {}
        # Una lista de objetos: se describe por el primero, con [] en la ruta.
        if isinstance(valor[0], (dict, list)):
            return _aplana(valor[0], f"{prefijo}[]" if prefijo else "[]", nivel + 1)
        return {prefijo: valor}
    return {prefijo: valor} if prefijo else {}


def _lee_fuente(nombre: str) -> set[str]:
    """Las claves que el colector pide en su codigo."""
    camino = (config.RAIZ / "projects" / "cesta" / "collectors" / f"{nombre}.py")
    texto = camino.read_text(encoding="utf-8")
    claves = set(re.findall(r'\.get\(\s*["\']([\w\-]+)["\']', texto))
    claves |= set(re.findall(r'\[\s*["\']([\w\-]+)["\']\s*\]', texto))
    # Tambien lo que aparezca dentro de una expresion regular o de un literal
    # largo: los parsers de HTML buscan la clave por texto.
    claves |= set(re.findall(r'"([\w]{4,})"\s*:', texto))
    return claves


def _productos(fuente: str, mod, limite: int) -> list[dict]:
    dias = sorted(glob.glob(str(config.RAW / f"fuente={fuente}" / "fecha=*")))
    if not dias:
        return []
    ficheros = sorted(glob.glob(os.path.join(dias[-1], "*.json.gz")))[:limite]
    propio = getattr(mod, "productos_crudo", None)
    salida: list[dict] = []
    for f in ficheros:
        try:
            with open(f, "rb") as fh:
                crudo = gzip.decompress(fh.read())
        except Exception:  # noqa: BLE001
            continue
        if propio:
            salida.extend(propio(crudo))
            continue
        try:
            datos = json.loads(crudo)
        except Exception:  # noqa: BLE001
            continue
        if isinstance(datos, dict):
            if "products" in datos:
                salida.extend(datos["products"])
            elif "categories" in datos:
                salida.extend(p for sub in datos["categories"]
                              for p in sub.get("products", []))
            elif "id" in datos:
                salida.append(datos)
    return salida


def _hermanos_leidos(ruta: str, presentes: Counter, leidas: set[str]) -> list[str]:
    """Otras hojas del mismo sitio que el colector si pide.

    Existe porque la heuristica tiene un falso positivo muy caro de comprobar. El
    18 de septiembre de 2026 el auditor senalo `iconAttributes[].file` en el 52 %
    del catalogo de Alcampo, y se tardo media hora en descubrir que el colector ya
    lee esa misma lista entera -- por `iconAttributes[].label`, que dice lo mismo
    en cristiano. Media hora midiendo algo que ya estaba hecho.

    No se puede descartar automaticamente: que se lea un hermano no demuestra que
    este no aporte nada (`price.amount` y `price.currency` son hermanos y solo uno
    importa). Pero decirlo ahorra la media hora.
    """
    prefijo = ruta.rsplit(".", 1)[0] if "." in ruta else ""
    if not prefijo:
        return []
    vecinas = []
    for otra in presentes:
        if otra == ruta or not otra.startswith(prefijo + "."):
            continue
        hoja = otra.rstrip("[]").rsplit(".", 1)[-1].rstrip("[]")
        if hoja in leidas and hoja not in vecinas:
            vecinas.append(hoja)
    return sorted(vecinas)[:4]


def audita(fuente: str, minimo: float, limite: int = MAX_FICHEROS) -> int:
    mod = importlib.import_module(f"projects.cesta.collectors.{fuente}")
    productos = _productos(fuente, mod, limite)
    if not productos:
        print(f"{fuente}: no se pudo leer el crudo "
              f"(¿le falta `productos_crudo`?)")
        return 1

    presentes: Counter = Counter()
    ejemplos: dict[str, str] = {}
    for p in productos:
        if not isinstance(p, dict):
            continue
        for ruta, valor in _aplana(p).items():
            if valor in (None, "", [], {}):
                continue
            presentes[ruta] += 1
            if ruta not in ejemplos:
                ejemplos[ruta] = str(valor)[:56].replace("\n", " ")

    leidas = _lee_fuente(fuente)
    n = len(productos)
    sin_leer = []
    for ruta, veces in presentes.items():
        pct = 100 * veces / n
        if pct < minimo or RUIDO.search(ruta):
            continue
        hoja = ruta.rstrip("[]").rsplit(".", 1)[-1].rstrip("[]")
        if hoja in leidas:
            continue
        sin_leer.append((pct, ruta, ejemplos.get(ruta, ""),
                         _hermanos_leidos(ruta, presentes, leidas)))

    print(f"\n=== {fuente}: {n} productos del ultimo dia")
    if not sin_leer:
        print("    nada sin leer por encima del umbral. Bien.")
        return 0
    print(f"    {len(sin_leer)} campos con valor que el colector NO pide:")
    for pct, ruta, ej, hermanos in sorted(sin_leer, reverse=True):
        print(f"      {pct:5.1f}%  {ruta:46s} {ej}")
        if hermanos:
            print(f"               (de ese mismo sitio si se lee: "
                  f"{', '.join(hermanos)} -- probablemente ya cubierto)")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="auditar_crudo")
    ap.add_argument("--fuente", choices=FUENTES)
    ap.add_argument("--minimo", type=float, default=2.0,
                    help="porcentaje minimo de productos con el campo (2 por defecto)")
    ap.add_argument("--ficheros", type=int, default=MAX_FICHEROS)
    a = ap.parse_args(argv)
    fuentes = [a.fuente] if a.fuente else list(FUENTES)
    for f in fuentes:
        audita(f, a.minimo, a.ficheros)
    print("\nOjo: es una heuristica. Una clave leida a traves de una variable no")
    print("se ve, asi que puede avisar de algo que si se lee. Avisa de mas, nunca")
    print("de menos, que es lo que interesa en una auditoria.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
