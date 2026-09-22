"""De la categoria de cada cadena a una seccion comun.

Por que un fichero y no un modelo
---------------------------------
Son 849 claves entre las cinco cadenas. Un fichero se lee de un vistazo, se
corrige en diez segundos y **no se equivoca en silencio**. Un clasificador de
texto acierta el 90 % y el 10 % restante no se sabe cual es hasta que alguien lo
ve en pantalla y le extrana.

El fichero esta en `core/datos/secciones.yml` y se genero automaticamente por
palabras clave: el 97 % de las claves salieron propuestas, y las 25 que no estan
marcadas para repasar a mano.

Para que sirve
--------------
Sin una seccion comun no hay lista ordenada por pasillos, ni "Explorar", ni
pantalla de secciones en el panel, ni analisis por linea de producto. Es lo que
mas desbloquea de todo el proyecto.

    >>> seccion_de("alcampo", "Bebidas > Cervezas > Rubias")
    'bebidas'
    >>> seccion_de("dia", "https://www.dia.es/zumos-y-smoothies/smoothies/c/L2291")
    'bebidas'
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

FICHERO = Path(__file__).resolve().parent / "datos" / "secciones.yml"

# El orden en que se recorre un supermercado, que es el orden en que se ordena
# la lista. No es alfabetico a proposito: es el recorrido.
ORDEN = (
    "frutas-verduras", "carniceria", "pescaderia", "lacteos-huevos",
    "panaderia", "despensa", "desayuno-dulces", "aperitivos", "congelados",
    "preparados", "bebidas", "droguería-limpieza", "higiene-belleza",
    "parafarmacia", "bebe", "mascotas", "ecologico", "hogar", "promociones",
)

_DIA_URL = re.compile(r"dia\.es/([^/]+)/([^/]+)/")


def clave_de(fuente: str, categoria: str | None) -> str | None:
    """La categoria de la cadena, recortada a lo que sirve como clave.

    Cada cadena escribe la suya de forma distinta y hay que recortarla igual que
    lo hizo el generador del fichero, o no casara nada:

        alcampo    los dos primeros niveles de su arbol, que tiene 3,6 de media
        dia        los dos primeros trozos de su URL (su `categoria` es una URL,
                   no un arbol; ver CADENAS.md punto 4)
        el resto   su categoria tal cual
    """
    if not categoria:
        return None
    if fuente == "alcampo":
        partes = [p.strip() for p in categoria.split(">")]
        return " > ".join(partes[:2]) if partes else None
    if fuente == "dia":
        m = _DIA_URL.search(categoria)
        return f"{m.group(1)}/{m.group(2)}" if m else categoria
    return categoria


@lru_cache(maxsize=1)
def _mapa() -> dict[tuple[str, str], str]:
    """Lee el fichero. Sin dependencias: su forma es fija y conocida.

    No se usa PyYAML porque anadir una dependencia para leer un fichero que
    escribimos nosotros, con una forma que controlamos, no sale a cuenta.
    """
    mapa: dict[tuple[str, str], str] = {}
    fuente = None
    dentro = False
    for linea in FICHERO.read_text(encoding="utf-8").splitlines():
        if linea.startswith("mapa:"):
            dentro = True
            continue
        if not dentro:
            continue
        sin_comentario = linea.split("#")[0].rstrip()
        if not sin_comentario.strip():
            continue
        # "  alcampo:" abre una cadena; '    "clave": valor' es una fila
        if re.fullmatch(r"  (\w+):", sin_comentario):
            fuente = sin_comentario.strip().rstrip(":")
            continue
        m = re.match(r'\s+"(.*)":\s*(\S+)\s*$', sin_comentario)
        if m and fuente:
            valor = m.group(2)
            if valor != "null":
                mapa[(fuente, m.group(1))] = valor
    return mapa


def seccion_de(fuente: str, categoria: str | None) -> str | None:
    """La seccion comun de un producto, o None si no se sabe.

    None es una respuesta valida y la interfaz la trata como "otros". **No se
    inventa una seccion** para que la lista no quede fea: un producto en el
    pasillo equivocado es peor que uno al final.
    """
    clave = clave_de(fuente, categoria)
    return _mapa().get((fuente, clave)) if clave else None


def orden_de(seccion: str | None) -> int:
    """Para ordenar la lista por el recorrido de la tienda. Lo desconocido, al final."""
    try:
        return ORDEN.index(seccion)
    except ValueError:
        return len(ORDEN)


def sin_asignar() -> list[tuple[str, str]]:
    """Las claves que siguen marcadas para repasar. Util para una prueba que
    avise si alguien anade una cadena y se olvida de mapearla."""
    fuera = []
    fuente = None
    dentro = False
    for linea in FICHERO.read_text(encoding="utf-8").splitlines():
        if linea.startswith("mapa:"):
            dentro = True
            continue
        if not dentro:
            continue
        sin_comentario = linea.split("#")[0].rstrip()
        if re.fullmatch(r"  (\w+):", sin_comentario):
            fuente = sin_comentario.strip().rstrip(":")
        elif (m := re.match(r'\s+"(.*)":\s*null\s*$', sin_comentario)) and fuente:
            fuera.append((fuente, m.group(1)))
    return fuera
