"""Lidl: leer su sitemap y decidir que merece una ficha, **sin gastar una peticion de mas**.

**Lo que resuelve, y lo que no.** El encargo (SUPERAPP-02 §5) pide dos caminos: descubrir y detallar
por un lado, y las ofertas por otro. Esto es la **primera mitad del primero**: leer el sitemap de
productos, quedarse con las direcciones de ficha, clasificarlas por su *slug* con la politica de
alcance y decir cuantas merecen detalle. **No pide nada a la red**: se le da el XML ya descargado.

**Las tres reglas que mas importan aqui, porque son las que se pueden hacer mal con buena intencion:**

1. **6.622 URLs no son 6.622 alimentos.** El sitemap no clasifica: incluye bazar, y los prefijos de
   identificador observados (100, 110, 111) **no** son un clasificador de alimentacion. Se cuentan
   direcciones y se dice que son direcciones.
2. **Un alimento no se excluye por su slug.** Si la direccion no da una señal clara, va a **revision**,
   no a la basura: excluir comida por un nombre de URL es el error caro.
3. **Una URL no prueba que la pagina viva.** El propio encargo documenta un 404 en el sitemap. Aqui
   solo se decide **a quien pedirle**; que conteste es otra cosa, y el estado de esa ficha lo dirá la
   cola de S02.
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

from core import alcance

RE_LOC = re.compile(r"<loc>\s*([^<\s]+)\s*</loc>", re.IGNORECASE)
# Las fichas de producto de Lidl acaban en `/p<slug>/p<id>`; el resto son categorias y editoriales.
RE_FICHA = re.compile(r"/p/(?P<slug>[^/]+)/p(?P<id>\d+)", re.IGNORECASE)
CAMPOS = ("urls", "fichas", "identificadores", "incluidas", "excluidas", "revision")


def urls_de_sitemap(xml: bytes | str) -> list[str]:
    """Las direcciones `<loc>` del XML, en orden y sin repetir."""
    texto = xml.decode("utf-8", "replace") if isinstance(xml, bytes) else xml
    vistas, salida = set(), []
    for url in RE_LOC.findall(texto):
        if url not in vistas:
            vistas.add(url)
            salida.append(url)
    return salida


def desglosa(url: str) -> tuple[str, str] | None:
    """(slug, identificador) si es una ficha de producto; None si es categoria o editorial."""
    encontrado = RE_FICHA.search(urlsplit(url).path)
    if not encontrado:
        return None
    return encontrado.group("slug"), encontrado.group("id")


def clasifica(url: str) -> tuple[str, str]:
    """(estado, motivo) de una direccion de ficha, **por su slug y nada mas**.

    Se apoya en la politica de alcance, que ya sabe de bazar y de comida, para no inventar aqui un
    segundo vocabulario que se desviaria del primero. Lo que no da señal clara queda en `revisar`.
    """
    partes = desglosa(url)
    if partes is None:
        return "no_es_ficha", "no es una direccion de ficha de producto"
    slug = partes[0].replace("-", " ").replace("_", " ")
    # **El slug va como nombre Y como categoria.** Como nombre, para que se apliquen los lexicos de
    # producto (un "taladro" tiene que caer aqui y no gastar ficha); como categoria, para que valgan
    # los pasillos. Con la categoria sola no se rechazaba el bazar, que es la mitad del trabajo.
    decision = alcance.clasificar_alcance(slug, slug)
    return decision.estado, decision.regla_id


def informe(urls: list[str]) -> dict:
    """Cuantas direcciones hay, cuantas son ficha y que dice la politica de cada una."""
    cuenta: Counter = Counter()
    identificadores: set[str] = set()
    por_estado: dict[str, list[str]] = {"incluido": [], "excluido": [], "revisar": []}
    for url in urls:
        cuenta["urls"] += 1
        partes = desglosa(url)
        if partes is None:
            cuenta["no_es_ficha"] += 1
            continue
        cuenta["fichas"] += 1
        identificadores.add(partes[1])
        estado, _ = clasifica(url)
        if estado in por_estado:
            por_estado[estado].append(url)
            cuenta[{"incluido": "incluidas", "excluido": "excluidas",
                    "revisar": "revision"}[estado]] += 1
    cuenta["identificadores"] = len(identificadores)
    return {"cuenta": dict(cuenta), "por_estado": por_estado,
            "cobertura": "catalogo_publico_descubierto",
            "aviso": ("son direcciones, no alimentos ni surtido: el sitemap no clasifica, y un "
                      "prefijo de identificador no es un pasillo. Una direccion tampoco prueba que "
                      "la pagina viva.")}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--xml", type=Path, required=True, help="sitemap ya descargado (sin red)")
    ap.add_argument("--ejemplos", type=int, default=3, help="ejemplos por estado")
    a = ap.parse_args(argv)
    if not a.xml.exists():
        print(f"no esta {a.xml}: este instrumento lee un sitemap guardado, no lo descarga")
        return 1
    datos = informe(urls_de_sitemap(a.xml.read_bytes()))
    cuenta = datos["cuenta"]
    print(f"direcciones: {cuenta.get('urls', 0):,} · fichas de producto: {cuenta.get('fichas', 0):,}"
          f" · identificadores distintos: {cuenta.get('identificadores', 0):,}"
          .replace(",", "."))
    print(f"  incluidas {cuenta.get('incluidas', 0):,} · excluidas {cuenta.get('excluidas', 0):,} · "
          f"a revision {cuenta.get('revision', 0):,} · no son ficha {cuenta.get('no_es_ficha', 0):,}"
          .replace(",", "."))
    for estado in ("incluido", "excluido", "revisar"):
        ejemplos = datos["por_estado"][estado][:a.ejemplos]
        for url in ejemplos:
            print(f"    {estado:<9} {url[:96]}")
    print(f"  {datos['aviso']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
