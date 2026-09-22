"""¿Nos dejamos categorias sin pedir? El gemelo de `auditar_crudo.py`.

La diferencia entre los dos, que es toda la gracia:

    auditar_crudo.py       de las respuestas que SI bajamos, que campos no leemos
    auditar_recorrido.py   que respuestas NO bajamos aunque la cadena nos diga
                           que existen

El fallo que obliga a escribir esto
-----------------------------------
El 18 de septiembre de 2026 Alcampo entrego un catalogo sin la rama Frescos
entera, con cero errores. La causa resulto ser una linea del recorrido:

    if len(productos) >= TOPE_API and hijas:
        pendientes.extend(hijas)      # bajar
    else:
        filas.extend(productos)       # quedarse

Su API devuelve los productos de todo el subarbol con un tope de 300, asi que un
nodo con **0 productos y con hijas** es un nodo de navegacion puro: los productos
estan abajo. Caia en el `else`, no anadia nada y no encolaba nada. El subarbol
entero desaparecia sin un solo error.

Medido con esta herramienta sobre el crudo del 17: **289 nodos asi, con 1.245
hijas nunca pedidas**. De ellas 1.192 llegaban igual por otro camino, y 53 no
llegaban nunca. El 18 le toco a Frescos, que son 2.646 productos.

Lo importante no es el numero: es que **nadie lo habria visto**. No hay error, no
hay excepcion, no hay hueco en el log. Solo faltan cosas.

Como se usa
-----------
    uv run python -m projects.cesta.auditar_recorrido
    uv run python -m projects.cesta.auditar_recorrido --fuente alcampo --fecha 2026-09-17

Que cuenta como "perdida"
-------------------------
Una categoria que la cadena declara y que cumple las tres:

  1. no se pidio (su clave no esta en el crudo del dia),
  2. no trae sus productos dentro de la respuesta del padre, y
  3. su nombre no aparece en ninguna categoria del bronze de ese dia.

Las tres juntas. Sin la tercera, Mercadona saldria con 469 falsas perdidas: su
API devuelve la categoria de nivel 2 con las hojas y sus productos dentro, asi
que no hace falta pedirlas.
"""
from __future__ import annotations

import argparse
import glob
import gzip
import hashlib
import json
import os

import polars as pl

from core import config

FUENTES = ("alcampo", "mercadona", "dia", "carrefour", "aldi")

# A partir de cuantas categorias nuevas, una respuesta es "el menu entero" y no
# una categoria concreta. El menu de Alcampo declara 2.600 y una categoria suya
# declara entre 0 y 20.
MENU_MINIMO = 200

# Como se construye la clave de cache de una categoria en cada colector. Si un
# colector cambia su clave, aqui hay que cambiarla tambien o la auditoria dira
# que no se pidio nada.
CLAVES = {
    "alcampo": ("api-category-{id}",),
    "mercadona": ("category-{id}",),
    "dia": ("{id}", "{id}-1"),
    "carrefour": ("{id}-0",),
}


def _pedidas(fuente: str, fecha: str) -> set[str]:
    return {os.path.basename(f).split("-")[0]
            for f in glob.glob(str(config.RAW / f"fuente={fuente}" / f"fecha={fecha}" / "*.json.gz"))}


def _se_pidio(fuente: str, cat_id: str, pedidas: set[str]) -> bool:
    for plantilla in CLAVES.get(fuente, ("{id}",)):
        clave = plantilla.format(id=cat_id)
        if hashlib.sha1(clave.encode()).hexdigest()[:12] in pedidas:
            return True
    return False


def _categorias_del_bronze(fuente: str, fecha: str) -> set[str]:
    camino = config.DATA / "bronze" / f"fuente={fuente}" / f"fecha={fecha}" / "part.parquet"
    if not camino.exists():
        return set()
    try:
        df = pl.read_parquet(camino, columns=["categoria"])
    except Exception:  # noqa: BLE001
        return set()
    nombres = set()
    for c in df["categoria"].drop_nulls().to_list():
        for trozo in str(c).replace("/", " > ").split(" > "):
            t = trozo.strip().lower()
            if t:
                nombres.add(t)
    return nombres


def _declaradas(fuente: str, fecha: str):
    """(id, nombre, cuantas hijas declara, cuantos productos trae dentro).

    Devuelve tambien el mapa padre -> hijas, que hace falta para saber que
    categorias cuelgan de una rama excluida a proposito. Sin eso, Alcampo sale
    con 901 "perdidas" que son juguetes, bricolaje y accesorios de coche, o sea
    justo lo que `RAMAS_EXCLUIDAS_ALCAMPO` dice que no queremos.
    """
    salida = {}
    hijas_de: dict[str, list[str]] = {}
    del_menu: set[str] = set()
    vistas_en_categoria: set[str] = set()

    def anda(nodo):
        if isinstance(nodo, dict):
            hijas = nodo.get("categories") or nodo.get("subcategories") or []
            ident = nodo.get("retailerCategoryId") or nodo.get("retailerId") or nodo.get("id")
            nombre = nodo.get("name")
            if ident is not None and nombre:
                dentro = nodo.get("products") or []
                salida[str(ident)] = (str(nombre), len(hijas) if isinstance(hijas, list) else 0,
                                      len(dentro) if isinstance(dentro, list) else 0)
                if isinstance(hijas, list):
                    crias = []
                    for h in hijas:
                        if isinstance(h, dict):
                            hid = (h.get("retailerCategoryId") or h.get("retailerId")
                                   or h.get("id"))
                            if hid is not None:
                                crias.append(str(hid))
                    if crias:
                        hijas_de[str(ident)] = crias
            for v in nodo.values():
                anda(v)
        elif isinstance(nodo, list):
            for v in nodo:
                anda(v)

    for f in glob.glob(str(config.RAW / f"fuente={fuente}" / f"fecha={fecha}" / "*.json.gz")):
        try:
            with open(f, "rb") as fh:
                datos = json.loads(gzip.decompress(fh.read()))
        except Exception:  # noqa: BLE001
            continue          # HTML, no JSON: esa cadena no declara su arbol asi
        antes = len(salida)
        anda(datos)
        # El menu completo declara el arbol ENTERO de la tienda, incluidas las
        # ramas que la configuracion excluye a proposito (juguetes, bricolaje,
        # accesorios de coche). Contarlas como "perdidas" es cantar 899 falsas
        # alarmas. Solo interesan las categorias que declara una respuesta de
        # CATEGORIA, o sea aquellas por las que ibamos andando cuando nos
        # dejamos el desvio.
        if len(salida) - antes > MENU_MINIMO:
            del_menu.update(k for k in salida if k not in vistas_en_categoria)
        else:
            vistas_en_categoria.update(salida)
    return salida, hijas_de, del_menu


def _excluidas(fuente, declaradas, hijas_de) -> set[str]:
    """Todo lo que cuelga de una rama que la configuracion dice que no queremos."""
    if fuente != "alcampo":
        return set()
    raices = {i for i, (nombre, _h, _p) in declaradas.items()
              if nombre.strip().lower() in config.RAMAS_EXCLUIDAS_ALCAMPO}
    fuera, pendientes = set(raices), list(raices)
    while pendientes:
        for hijo in hijas_de.get(pendientes.pop(), ()):
            if hijo not in fuera:
                fuera.add(hijo)
                pendientes.append(hijo)
    return fuera


def audita(fuente: str, fecha: str) -> int:
    pedidas = _pedidas(fuente, fecha)
    if not pedidas:
        print(f"{fuente}: no hay crudo de {fecha}")
        return 1
    declaradas, hijas_de, del_menu = _declaradas(fuente, fecha)
    fuera = _excluidas(fuente, declaradas, hijas_de) | del_menu
    if not declaradas:
        print(f"\n=== {fuente} ({fecha}): su crudo no declara el arbol en JSON, "
              f"no se puede auditar asi")
        return 0
    en_bronze = _categorias_del_bronze(fuente, fecha)

    perdidas = []
    llegan_por_otro_lado = 0
    for ident, (nombre, _hijas, dentro) in declaradas.items():
        if _se_pidio(fuente, ident, pedidas) or dentro or ident in fuera:
            continue
        if nombre.strip().lower() in en_bronze:
            llegan_por_otro_lado += 1
            continue
        perdidas.append((ident, nombre))

    print(f"\n=== {fuente} ({fecha}): {len(pedidas)} respuestas guardadas, "
          f"{len(declaradas)} categorias declaradas"
          + (f", {len(fuera)} solo del menu o excluidas" if fuera else ""))
    print(f"    sin pedir pero llegan por otro camino: {llegan_por_otro_lado}")
    if not perdidas:
        print("    categorias que no llegan de ninguna forma: 0. Bien.")
        return 0
    print(f"    **{len(perdidas)} categorias no llegan de ninguna forma**:")
    for ident, nombre in sorted(perdidas, key=lambda x: x[1])[:30]:
        print(f"      {ident:>12s}  {nombre}")
    if len(perdidas) > 30:
        print(f"      ... y {len(perdidas) - 30} mas")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="auditar_recorrido")
    ap.add_argument("--fuente", choices=FUENTES)
    ap.add_argument("--fecha", default=str(config.hoy_local()))
    a = ap.parse_args(argv)
    for f in ([a.fuente] if a.fuente else list(FUENTES)):
        audita(f, a.fecha)
    print("\nUna categoria cuenta como perdida solo si se cumplen las tres: no se")
    print("pidio, no trae sus productos dentro del padre, y su nombre no aparece")
    print("en ninguna categoria del bronze de ese dia.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
