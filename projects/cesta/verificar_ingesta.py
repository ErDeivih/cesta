"""¿La cosecha de hoy llego entera? Lo que la cadena nos dio, contra lo que guardamos.

Por que existe
--------------
Cuando alguien pregunta *"¿la ingesta de hoy esta bien?"*, los controles que hay contestan
cosas distintas y ninguna contesta esa:

    core/runlog.check_drift     avisa si el total se sale de lo normal. No decide, y un
                                total puede bajar un 13 % sin que falte nada raro
    core/cobertura.revisa       compara RAMAS contra el ultimo bronze bueno. Ve
                                desaparecer media tienda, no ve perder 400 productos
    auditar_recorrido.py        ¿pedimos las categorias que la cadena declara en su menu?
    verificar_precios.py        sale a la calle: ¿el precio que publicamos esta en su
                                pagina? ¿el enlace lleva a algun sitio?
    auditar_crudo.py            de lo que bajamos, ¿que campos no leemos?

Lo que faltaba es lo mas tonto de todo y lo que mas duele: **de los productos que la cadena
nos entrego hoy en las respuestas que guardamos, cuantos estan en bronze**, y **de las
paginas que la propia cadena dice que tiene una categoria, cuantas pedimos**. Eso no se
sabia. Un `unique(subset=["fuente","id_fuente"])`, un `join` que pierde filas o un parseo
que se traga un 3 % de las fichas no dan error, no cambian el orden de magnitud del total y
no los ve nadie.

Asi que esto se mide contra el crudo del dia, que es lo unico que no miente: la respuesta
tal cual la dio la cadena.

Las cuatro preguntas, y por que cada una
----------------------------------------
1. **Productos declarados / guardados.** Los ids que aparecen en el crudo de hoy contra los
   ids que hay en bronze. Lo que falta aqui es una perdida entre el crudo y el bronze, que
   es donde el codigo propio puede equivocarse en silencio.
   *Ojo con leerlo al reves*: que un id este en el crudo y no en bronze es un fallo **nuestro**;
   que un id de bronze no este en el crudo significa que ese bronze no salio de este crudo
   (una cache de otro dia, por ejemplo), y tambien cuenta.

2. **Paginas declaradas / pedidas.** Carrefour y DIA dicen, en la respuesta de la primera
   pagina, cuantas paginas tiene la categoria. Si pedimos menos, faltan productos, y lo
   sabemos sin salir a la calle.

3. **Enlaces.** Cada fila tiene que traer su enlace, y el enlace tiene que llevar **su propio
   id** dentro. Esta es la comprobacion que faltaba el 21 de septiembre de 2026: los 23.776
   enlaces de Alcampo estaban roto**s** porque la URL publica lleva el `retailerProductId` y
   guardabamos el `productId`. El precio estaba bien, el catalogo parecia bien, y los 23.776
   enlaces daban 404. Un enlace roto solo se nota cuando una persona lo pulsa.

4. **Categorias al tope.** Cuando la API de una cadena devuelve como maximo N productos por
   respuesta, una categoria que devuelve **exactamente N** puede estar cortada. No es una
   prueba de que falte nada: es la lista de sitios donde hay que mirar.

Como se usa
-----------
    uv run python -m projects.cesta.verificar_ingesta
    uv run python -m projects.cesta.verificar_ingesta --fecha 2026-09-23
    uv run python -m projects.cesta.verificar_ingesta --fuente dia

Sale 0 si todo cuadra y, si no, **cuantos problemas hay**. No arregla nada: dice donde mirar.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import math
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import polars as pl

from core import config

FUENTES = ("alcampo", "aldi", "carrefour", "dia", "mercadona")

# Cuantos productos por respuesta sirve cada cadena, cuando lo sirve con tope.
TOPE_DE_API = {"alcampo": 300}

# El host que tiene que aparecer en el enlace de cada cadena. Un enlace a otro sitio es un
# enlace mal construido, aunque el id este bien.
HOST = {
    "alcampo": "compraonline.alcampo.es",
    "aldi": "aldi.es",
    "carrefour": "carrefour.es",
    "dia": "dia.es",
    "mercadona": "tienda.mercadona.es",
}

# Donde **construimos nosotros** el enlace a partir del id: ahi un enlace que no lleve su id es
# un fallo, y es el fallo que dejo 23.776 enlaces de Alcampo en 404 durante quince dias. Donde
# el enlace lo da la cadena en su propia respuesta (Carrefour publica `R-<referencia>` y su
# `product_id` no aparece en la URL; DIA y Mercadona dan la suya), el id de dentro puede ser
# otro a proposito, y eso se comprueba en vivo con `verificar_precios.py`, no aqui.
URL_PROPIA = frozenset({"alcampo", "aldi"})

# Los ids de producto, tal y como aparecen en el crudo de cada cadena. Son expresiones sobre
# el TEXTO de la respuesta, no sobre el objeto ya parseado: si se usara el lector del colector,
# este control no podria discrepar de el, y un control que no puede discrepar no es un control
# (es la misma razon que explica `verificar_precios.py`).
#
# El id que se busca es **el que acaba en `id_fuente`**, que no siempre es el mas obvio:
#   mercadona    `"id":"12049.1"` -- los pesados llevan decimal, y en bronce va tal cual
#   dia          `"sku_id":"10065P4"` -- hay sku con letra; cortarlo en el primer digito
#                hacia que 114 productos del dia salieran como «sobran» sin serlo
#   alcampo      `retailerProductId`, y si no lo trae, `productId` (la regla del colector)
IDS = {
    "alcampo": (r'"retailerProductId"\s*:\s*"?([A-Za-z0-9_\-]+)"?',),
    "aldi": (r'"objectID"\s*:\s*"(\d+)"', r'-(\d+)\.html</loc>'),
    "carrefour": (r'"product_id"\s*:\s*"([A-Za-z0-9_\-]+)"',),
    "dia": (r'"sku_id"\s*:\s*"([A-Za-z0-9._\-]+)"',),
    "mercadona": (r'"share_url"\s*:\s*"[^"]*/product/([A-Za-z0-9._\-]+)/',),
}

# Cuantas paginas declara una respuesta, y de cuanto es cada pagina.
DECLARA_PAGINAS = {
    "carrefour": (r'"total_results"\s*:\s*(\d+)', 24),
}
# DIA dice el numero de paginas directamente.
DIA_PAGINAS = re.compile(r'"total_pages"\s*:\s*"?(\d+)"?')
DIA_CATEGORIA = re.compile(r"<loc>([^<]*?/c/L\d+)</loc>")
CARREFOUR_CATEGORIA = re.compile(r"/supermercado/([a-z0-9\-/]+)/(cat\d+)/c")
# La categoria que Carrefour dice haber servido: si no es la que se pidio, esa direccion ya
# no existe y la respuesta es la de su padre.
_SERVIDA = re.compile(r'"navigation_id":"(cat\d+)"')

# Alcampo declara su arbol en JSON; su menu trae 2.600 categorias y una categoria suya
# entre 0 y 20, que es el mismo corte que usa `auditar_recorrido.py`.
MENU_MINIMO = 200


@dataclass
class Informe:
    """Lo que se ha medido de una cadena, con los problemas ya en frases."""

    fuente: str
    fecha: str
    declarados: set[str] = field(default_factory=set)
    guardados: set[str] = field(default_factory=set)
    categorias: int = 0
    respuestas: int = 0
    paginas_esperadas: int = 0
    paginas_pedidas: int = 0
    categorias_cortas: list[str] = field(default_factory=list)
    servidas_por_su_padre: list[str] = field(default_factory=list)
    sin_pedir: list[str] = field(default_factory=list)
    sin_url: int = 0
    url_sin_id: list[str] = field(default_factory=list)
    url_fuera_de_su_host: list[str] = field(default_factory=list)
    enlaces_repetidos: int = 0
    al_tope: int = 0
    # Los que faltan, separados por si hay explicacion o no. La diferencia es toda la gracia
    # del informe: 13 productos sin explicacion son un fallo, y 13 con explicacion son el
    # comportamiento documentado del colector. Se guardan los ids y no solo el recuento,
    # porque el problema es justo lo que NO esta aqui.
    explicados: dict[str, list[str]] = field(default_factory=dict)

    @property
    def faltan(self) -> set[str]:
        return self.declarados - self.guardados

    @property
    def ids_explicados(self) -> set[str]:
        return {i for ids in self.explicados.values() for i in ids}

    @property
    def faltan_sin_explicar(self) -> set[str]:
        return self.faltan - self.ids_explicados

    @property
    def sobran(self) -> set[str]:
        return self.guardados - self.declarados

    def problemas(self) -> list[str]:
        dichos = []
        if self.faltan_sin_explicar:
            dichos.append(f"{len(self.faltan_sin_explicar)} producto(s) que la cadena dio y no "
                          f"estan en bronze, sin explicacion: "
                          f"{sorted(self.faltan_sin_explicar)[:5]}")
        if self.sobran:
            dichos.append(f"{len(self.sobran)} producto(s) en bronze que no salen del crudo de "
                          f"hoy, p.ej. {sorted(self.sobran)[:5]} (¿bronce de otro dia?)")
        if self.categorias_cortas:
            dichos.append(f"{len(self.categorias_cortas)} categoria(s) con menos paginas de las "
                          f"que declaran: {self.categorias_cortas[:5]}")
        if self.sin_url:
            dichos.append(f"{self.sin_url} fila(s) sin enlace")
        # El enlace tiene que llevar su id **donde lo construimos nosotros**. Cuando lo da la
        # cadena en su propia respuesta (Carrefour, DIA, Mercadona) el id de dentro puede ser
        # otro a proposito -- Carrefour publica `R-<referencia>` y su `product_id` no aparece --
        # y eso no se comprueba aqui: se comprueba en vivo, con `verificar_precios.py`.
        if self.url_sin_id and self.fuente in URL_PROPIA:
            dichos.append(f"{len(self.url_sin_id)} enlace(s) que no llevan su propio id: "
                          f"{self.url_sin_id[:3]}")
        if self.url_fuera_de_su_host:
            dichos.append(f"{len(self.url_fuera_de_su_host)} enlace(s) fuera del dominio de la "
                          f"cadena: {self.url_fuera_de_su_host[:3]}")
        if self.enlaces_repetidos:
            dichos.append(f"{self.enlaces_repetidos} enlace(s) repetidos")
        return dichos


def _raiz(fuente: str, fecha: str) -> Path:
    return config.RAW / f"fuente={fuente}" / f"fecha={fecha}"


def _cuerpos(fuente: str, fecha: str) -> list[tuple[str, bytes]]:
    """Todas las respuestas guardadas de ese dia, como texto."""
    raiz = _raiz(fuente, fecha)
    if not raiz.exists():
        return []
    salida = []
    for p in sorted(raiz.glob("*.json.gz")):
        try:
            salida.append((p.name, gzip.decompress(p.read_bytes())))
        except Exception:  # noqa: BLE001
            continue
    return salida


def _texto(cuerpos) -> str:
    return "\n".join(c.decode("utf-8", "replace") for _n, c in cuerpos)


def _hay(fuente: str, fecha: str, clave: str) -> bool:
    """¿Se guardo esta respuesta ese dia? Se mira por el hash de la clave."""
    raiz = _raiz(fuente, fecha)
    if not raiz.exists():
        return False
    prefijo = hashlib.sha1(clave.encode()).hexdigest()[:12]
    return any(raiz.glob(f"{prefijo}-*.json.gz"))


def _lee(fuente: str, fecha: str, clave: str) -> bytes | None:
    raiz = _raiz(fuente, fecha)
    if not raiz.exists():
        return None
    prefijo = hashlib.sha1(clave.encode()).hexdigest()[:12]
    candidatos = sorted(raiz.glob(f"{prefijo}-*.json.gz"),
                        key=lambda p: (p.stat().st_mtime_ns, p.name))
    if not candidatos:
        return None
    return gzip.decompress(candidatos[-1].read_bytes())


def _declarados(fuente: str, cuerpos) -> set[str]:
    """Los ids de producto que la cadena dio hoy, leidos del texto de sus respuestas.

    Con una excepcion, y esta razonada: el id de Alcampo no esta en un campo fijo. Su API
    publica `retailerProductId` en unos sitios y solo `productId` en otros, y el colector usa
    `retailerProductId or productId`. Para poder comparar hay que usar **la misma regla**, o se
    estarian comparando dos identificadores distintos: ahi se camina el JSON. Lo que no se
    reutiliza nunca es la lectura de los VALORES (precio, nombre, cantidad).
    """
    if fuente == "alcampo":
        ids = _ids_alcampo(cuerpos)
        if ids:
            return ids
    texto = _texto(cuerpos)
    ids: set[str] = set()
    for patron in IDS[fuente]:
        ids.update(re.findall(patron, texto))
    return ids


def _ids_alcampo(cuerpos) -> set[str]:
    """Camina el JSON y aplica la regla del colector: `retailerProductId or productId`."""
    import json

    salida: set[str] = set()

    def anda(nodo):
        if isinstance(nodo, dict):
            if "retailerProductId" in nodo or "productId" in nodo:
                ident = nodo.get("retailerProductId") or nodo.get("productId")
                if ident and (nodo.get("name") or nodo.get("priceInstructions")):
                    salida.add(str(ident))
            for v in nodo.values():
                anda(v)
        elif isinstance(nodo, list):
            for v in nodo:
                anda(v)

    for _n, cuerpo in cuerpos:
        try:
            anda(json.loads(cuerpo))
        except Exception:  # noqa: BLE001
            continue
    return salida


def _guardados(fuente: str, fecha: str) -> pl.DataFrame | None:
    parte = config.DATA / "bronze" / f"fuente={fuente}" / f"fecha={fecha}" / "part.parquet"
    if not parte.exists():
        return None
    return pl.read_parquet(parte)


def _enlaces(df: pl.DataFrame, fuente: str, informe: Informe) -> None:
    """Las tres preguntas del enlace: ¿esta?, ¿es suyo?, ¿es de su casa?"""
    if "url" not in df.columns:
        informe.sin_url = df.height
        return
    filas = df.select(["id_fuente", "url"]).iter_rows()
    vistos: set[str] = set()
    for ident, url in filas:
        if not url:
            informe.sin_url += 1
            continue
        if url in vistos:
            informe.enlaces_repetidos += 1
        vistos.add(url)
        # El id tiene que estar en el enlace, y **entero**. La primera version partia el enlace
        # por todo lo que no fuera letra o digito, y con eso `73902-RODAJAS` (Alcampo) o
        # `VC4AECOMM-438819` (Carrefour) salian como enlaces rotos sin serlo: el id lleva guion.
        # Se mira el texto del enlace, y si el id es numerico se exige que no este pegado a otro
        # digito, que es la unica forma de confundir `/p/40976` con `/p/140976`.
        if not _enlace_lleva(url, str(ident)):
            informe.url_sin_id.append(f"{ident} -> {url}")
        if HOST[fuente] not in url:
            informe.url_fuera_de_su_host.append(f"{ident} -> {url}")


def _enlace_lleva(url: str, ident: str) -> bool:
    """¿El enlace lleva su propio id dentro, como pieza entera?"""
    if not ident:
        return False
    if not ident.isdigit():
        return ident in url
    return re.search(rf"(?<!\d){re.escape(ident)}(?!\d)", url) is not None


def _paginas(informe: Informe, fuente: str, fecha: str, cuerpos) -> None:
    """Lo que la cadena declara de paginacion, contra lo que se pidio.

    Solo Carrefour y DIA lo declaran; Aldi no pagina (su sitemap es la lista entera),
    Mercadona devuelve la categoria completa y Alcampo corta por tope (que se cuenta aparte,
    porque con tope no se sabe si falta: solo se sabe donde mirar).
    """
    if fuente == "carrefour":
        patron, por_pagina = DECLARA_PAGINAS["carrefour"]
        # Las categorias salen del propio crudo del dia (sitemaps y listados).
        vistas = {m.group(2) for m in CARREFOUR_CATEGORIA.finditer(_texto(cuerpos))}
        for cat_id in sorted(vistas):
            cuerpo = _lee(fuente, fecha, f"{cat_id}-0")
            if cuerpo is None:
                continue
            texto = cuerpo.decode("utf-8", "replace")
            # **Carrefour contesta con el padre cuando la direccion ya no existe**, y entonces
            # el `total_results` que trae no es el de esta categoria sino el de su rama. Sin
            # mirarlo, 22 categorias del dia salian como «cortadas» (cat20010: 1 de 42) sin
            # faltarles nada: su padre si se recorre entero, por su cuenta.
            servida = _SERVIDA.search(texto)
            if servida and servida.group(1) != cat_id:
                informe.servidas_por_su_padre.append(f"{cat_id} -> {servida.group(1)}")
                continue
            m = re.search(patron, texto)
            if not m:
                continue
            total = int(m.group(1))
            if total <= 0:
                continue
            esperadas = math.ceil(total / por_pagina)
            pedidas = sum(1 for i in range(esperadas) if _hay(fuente, fecha, f"{cat_id}-{i * por_pagina}"))
            informe.paginas_esperadas += esperadas
            informe.paginas_pedidas += pedidas
            if pedidas < esperadas:
                informe.categorias_cortas.append(f"{cat_id}: {pedidas} de {esperadas}")
    elif fuente == "dia":
        sitemap = _lee(fuente, fecha, "sitemap")
        if sitemap is None:
            return
        urls = DIA_CATEGORIA.findall(sitemap.decode("utf-8", "replace"))
        informe.categorias = len(urls)
        for url in urls:
            cuerpo = _lee(fuente, fecha, f"{url}-1")
            if cuerpo is None:
                # No se pidio, o se pidio y la cadena devolvio un 404 (su propio sitemap lista
                # categorias que ya no sirve: hoy, 3, y el registro del dia lo dice con esas
                # palabras). Desde fuera no se pueden distinguir, asi que se cuentan aparte.
                informe.sin_pedir.append(url)
                continue
            m = DIA_PAGINAS.search(cuerpo.decode("utf-8", "replace"))
            if not m:
                continue
            esperadas = int(m.group(1))
            pedidas = sum(1 for p in range(1, esperadas + 1) if _hay(fuente, fecha, f"{url}-{p}"))
            informe.paginas_esperadas += esperadas
            informe.paginas_pedidas += pedidas
            if pedidas < esperadas:
                informe.categorias_cortas.append(f"{url}: {pedidas} de {esperadas}")


def _al_tope(fuente: str, cuerpos) -> int:
    """Respuestas que devolvieron justo el tope de la API: pueden estar cortadas."""
    tope = TOPE_DE_API.get(fuente)
    if not tope:
        return 0
    cuantas = 0
    for _n, cuerpo in cuerpos:
        ids = set(re.findall(IDS[fuente][0], cuerpo.decode("utf-8", "replace")))
        if len(ids) >= tope:
            cuantas += 1
    return cuantas


def _categorias_declaradas(fuente: str, cuerpos) -> int:
    """Cuantas categorias distintas declara la cadena en el crudo de hoy."""
    texto = _texto(cuerpos)
    nombres: set[str] = set()
    if fuente == "alcampo":
        nombres = set(re.findall(r'"retailerCategoryId"\s*:\s*"?([A-Za-z0-9_\-]+)"?', texto))
    elif fuente == "mercadona":
        nombres = set(re.findall(r'"category_id"\s*:\s*(\d+)', texto)) | \
            set(re.findall(r'"id"\s*:\s*(\d+)\s*,\s*"name"', texto))
    elif fuente == "carrefour":
        nombres = {m.group(2) for m in CARREFOUR_CATEGORIA.finditer(texto)}
    elif fuente == "dia":
        nombres = set(DIA_CATEGORIA.findall(texto))
    return len(nombres)


def _rejilla_de_carrefour(fecha: str, cuerpos) -> set[str]:
    """Los ids que estan **en la rejilla** de alguna pagina de Carrefour, no en su texto.

    Y esto hay que hacerlo asi, aunque parezca que se esta usando el lector del colector: una
    pagina de listado de Carrefour trae, ademas de su rejilla, bloques de recomendaciones con
    ids de productos de otras categorias. Leidos del texto, esos ids salen como «declarados y
    no guardados» y son **7 falsas alarmas al dia**: el colector guarda los items de la rejilla
    y hace bien en no guardar el resto. Aqui se separa una cosa de la otra para poder decir cual
    es cual, y la comprobacion de verdad (que el lector no se deje items dentro de la rejilla)
    la sigue haciendo `auditar_crudo.py`, que mira las respuestas crudo a crudo.
    """
    from projects.cesta.collectors import carrefour

    raiz = _raiz("carrefour", fecha)
    if not raiz.exists():
        return set()
    texto = _texto(cuerpos)
    vistas = {m.group(2) for m in CARREFOUR_CATEGORIA.finditer(texto)}
    claves = {}
    for cat_id in vistas:
        for offset in range(0, 1008 + 24, 24):
            claves[hashlib.sha1(f"{cat_id}-{offset}".encode()).hexdigest()[:12]] = (cat_id, offset)
    ids: set[str] = set()
    for nombre, cuerpo in cuerpos:
        clave = claves.get(nombre.split("-")[0])
        if clave is None:
            continue                      # sitemaps y demas respuestas que no son listados
        try:
            pagina = carrefour._lee_listado(cuerpo, clave[0], clave[1])
        except Exception:  # noqa: BLE001
            continue                      # sin rejilla, sin catalogo o parseo que no traga
        ids.update(str(p.get("product_id")) for p in pagina["items"] if p.get("product_id"))
    return ids


def _por_que_no_esta(fuente: str, ident: str, cuerpos, rejilla: set[str] | None = None) -> str | None:
    """Si el producto no esta en bronze, ¿hay una razon escrita? Devuelve la razon o None.

    Un producto declarado y no guardado es un fallo **solo si nadie puede explicarlo**. Estas
    tres razones son comportamiento documentado del colector, y las tres estan medidas hoy:

      aldi       el id sale del sitemap de productos y **no** de una respuesta de precios: la
                 cadena publica la ficha pero su API no le da precio (agotado, sin precio
                 publicado). Un producto sin precio no es un dato de precio.
      carrefour  el id sale de una pagina que Carrefour sirve **sin rejilla** (`"plpData":{}`:
                 paginas de marca o de campana). El colector las cuenta en `sin_catalogo` y lo
                 imprime en el registro del dia.
      carrefour  el id aparece en el **texto** de una pagina con rejilla pero no dentro de la
                 rejilla: son los bloques de recomendaciones, que traen productos de otras
                 categorias. Se guardan los de la rejilla, y eso es lo correcto.
    """
    declarantes = []
    for nombre, cuerpo in cuerpos:
        texto = cuerpo.decode("utf-8", "replace")
        if f'"{ident}"' in texto or f"-{ident}.html" in texto:
            declarantes.append((nombre, texto))
    if not declarantes:
        return None                      # declarado, pero no se sabe donde: no se explica
    if fuente == "aldi":
        # El sitemap de productos escribe cada ficha como `...-<id>.html</loc>`; la respuesta
        # de precios, como `"objectID":"<id>"`. Si solo sale en el primero, la cadena publica
        # la ficha pero su API no le da precio.
        if all(f"-{ident}.html" in t and '"objectID"' not in t for _n, t in declarantes):
            return "en el sitemap y sin precio en su API"
        return None
    if fuente == "carrefour":
        # Una pagina con rejilla trae `"plpData":{"breadcrumb":…`; una de marca o campana trae
        # `"plpData":{}` vacio y sus productos sueltos en otro bloque (`homeFoodDataProducts`).
        vacia = re.compile(r'"plpData"\s*:\s*\{\s*\}')
        if all(vacia.search(t) for _n, t in declarantes):
            return "solo en paginas sin rejilla (marca o campana)"
        if rejilla is not None and ident not in rejilla:
            return "en el texto de la pagina fuera de la rejilla (recomendaciones)"
        return None
    return None


def revisa(fuente: str, fecha: str) -> Informe:
    """El informe de una cadena para un dia. Sin red: todo sale del crudo y de bronze."""
    inf = Informe(fuente=fuente, fecha=fecha)
    cuerpos = _cuerpos(fuente, fecha)
    inf.respuestas = len(cuerpos)
    df = _guardados(fuente, fecha)
    if df is None:
        return inf
    inf.guardados = {str(i) for i in df["id_fuente"].to_list()}
    if not cuerpos:
        return inf
    inf.declarados = _declarados(fuente, cuerpos)
    inf.categorias = _categorias_declaradas(fuente, cuerpos)
    inf.al_tope = _al_tope(fuente, cuerpos)
    rejilla = _rejilla_de_carrefour(fecha, cuerpos) if fuente == "carrefour" else None
    for ident in sorted(inf.faltan):
        razon = _por_que_no_esta(fuente, ident, cuerpos, rejilla)
        if razon is not None:
            inf.explicados.setdefault(razon, []).append(ident)
    _enlaces(df, fuente, inf)
    _paginas(inf, fuente, fecha, cuerpos)
    return inf


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--fecha", default=str(config.hoy_local()))
    ap.add_argument("--fuente", choices=FUENTES)
    args = ap.parse_args(argv)

    fuentes = [args.fuente] if args.fuente else FUENTES
    problemas = 0
    print(f"=== la ingesta del {args.fecha}, contra lo que declaran las cadenas\n")
    for fuente in fuentes:
        inf = revisa(fuente, args.fecha)
        if inf.respuestas == 0 and not inf.guardados:
            print(f"{fuente.upper():11} sin crudo ni bronze de ese dia")
            continue
        print(f"{fuente.upper():11} respuestas {inf.respuestas:>5}  "
              f"categorias declaradas {inf.categorias:>5}")
        print(f"{'':11} productos declarados {len(inf.declarados):>7,}  "
              f"en bronze {len(inf.guardados):>7,}  "
              f"faltan {len(inf.faltan):>5,}  sobran {len(inf.sobran):>5,}")
        for razon, ids in sorted(inf.explicados.items()):
            print(f"{'':11}   de los que faltan, {len(ids)} con explicacion: {razon}")
        if inf.paginas_esperadas:
            print(f"{'':11} paginas declaradas {inf.paginas_esperadas:>7,}  "
                  f"pedidas {inf.paginas_pedidas:>7,}")
        if inf.servidas_por_su_padre:
            print(f"{'':11} categorias que la cadena sirve desde su padre: "
                  f"{len(inf.servidas_por_su_padre)}  (su listado es el de la rama, y la rama "
                  f"si se recorre)")
        if inf.sin_pedir:
            print(f"{'':11} categorias del sitemap sin pedir: {len(inf.sin_pedir)}  "
                  f"{inf.sin_pedir[:3]}   (el registro del dia dice por que: 404 de la cadena "
                  f"o un alias del mismo codigo)")
        enlaces = (f"sin url {inf.sin_url}  sin su id {len(inf.url_sin_id)}  "
                   f"fuera de su dominio {len(inf.url_fuera_de_su_host)}  "
                   f"repetidos {inf.enlaces_repetidos}")
        if inf.url_sin_id and fuente not in URL_PROPIA:
            enlaces += "   (el enlace lo da la cadena: se comprueba en vivo)"
        print(f"{'':11} enlaces: {enlaces}")
        if inf.al_tope:
            print(f"{'':11} respuestas al tope de la API ({TOPE_DE_API[fuente]}): {inf.al_tope}"
                  f"   <- puede estar cortada, se mira con las busquedas")
        dichos = inf.problemas()
        if not dichos:
            print(f"{'':11} sin problemas\n")
            continue
        problemas += len(dichos)
        for dicho in dichos:
            print(f"{'':11} PROBLEMA: {dicho}")
        print()
    print(f"problemas: {problemas}")
    return problemas


if __name__ == "__main__":
    sys.exit(main())
