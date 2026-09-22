r"""Sondea una cadena nueva: ¿se puede, se debe, y merece la pena?

Por que existe este fichero
---------------------------
Cada vez que aparece una cadena candidata -- Eroski, Consum, Ahorramas -- se
repite la misma conversacion a medias: alguien mira una URL, ve algo raro y se
decide por impresion. Este script contesta las cuatro preguntas con su respuesta
escrita, en un minuto y sin escribir una linea de colector:

    1. ¿lo permite su robots.txt?
    2. ¿hay un reto anti-bot delante?
    3. ¿viene el precio en lo que nos entregan?
    4. ¿trae codigo de barras, para poder emparejar con lo que ya tenemos?

    uv run python -m projects.cesta.sondear_cadena eroski
    uv run python -m projects.cesta.sondear_cadena ahorramas

Las candidatas conocidas se sondean por su nombre, sin escribir ni una direccion:
las rutas estan apuntadas mas abajo, en `CANDIDATAS`. Para una cadena que no este
en la lista, se le pasa la direccion y las rutas a mano:

    uv run python -m projects.cesta.sondear_cadena https://www.ejemplo.es --categoria /alimentacion/

**En PowerShell no se parte la linea con `\`.** Eso es de bash, y el error que
sale no lo dice: `unrecognized arguments: \`. En PowerShell el continuador es el
acento grave, pero lo sensato es escribir el comando entero en una linea, que es
justo para lo que existe la lista de candidatas de aqui abajo.

Sobre la pregunta 2, que es la unica que no es tecnica
------------------------------------------------------
Si delante hay un reto anti-bot -- reCAPTCHA, Turnstile, "Checking your
browser" -- este script lo dice y **se para**. No intenta pasarlo, y el proyecto
tampoco: no se resuelven ni se automatizan verificaciones anti-bot. Es una linea
distinta de "leer una pagina publica", que es lo que hacemos con las cinco
cadenas que ya estan.

Conviene no confundir dos cosas que se parecen:

    403 sin marcas de reto     casi siempre es la IP o el User-Agent: un centro
                               de datos pidiendo como si fuera un navegador. Desde
                               una linea de casa puede no pasar. **Vuelve a
                               probarlo desde el PC antes de dar nada por cerrado.**
    reto anti-bot de verdad    hay que resolver algo para entrar. Ahi se para.

Por eso este script se ejecuta **en el PC de casa**, no en un contenedor: la
respuesta desde un centro de datos no dice lo mismo.

Sobre la pregunta 4, que es la que de verdad decide
---------------------------------------------------
Una cadena que anade 8.000 productos y treinta grupos comparables no anade nada.
Lo dicho por la competencia lo demuestra: RadarSuper cubre siete cadenas y su
comparativa publica se sostiene sobre 177 referencias comparables; la nuestra,
con cinco, sobre 6.448. Las cadenas se suman; el emparejamiento se gana.

Asi que si la ficha trae EAN, el script cuenta **cuantos de los EAN que encuentra
ya estan en nuestro gold**. Ese numero, y no el tamano del catalogo, es el que
dice si merece la pena escribir el colector.
"""
from __future__ import annotations

import argparse
import re
import sys
import urllib.robotparser
from pathlib import Path
from urllib.parse import urljoin, urlparse

from core import config
from core.fetch import Fetcher, HTTPStatusError

# Marcas de que delante hay un reto que hay que resolver. Se buscan en el cuerpo
# y en las cabeceras. No pretende ser exhaustivo: pretende no dejar pasar por
# "pagina normal" algo que es un muro.
RETOS = (
    (b"g-recaptcha", "reCAPTCHA de Google"),
    (b"recaptcha/api.js", "reCAPTCHA de Google"),
    (b"hcaptcha", "hCaptcha"),
    (b"challenges.cloudflare.com", "Cloudflare Turnstile"),
    (b"cf-challenge", "reto de Cloudflare"),
    (b"Checking your browser", "interstitial de 'Checking your browser'"),
    (b"Just a moment", "interstitial de Cloudflare"),
    (b"_Incapsula_Resource", "Imperva/Incapsula"),
    (b"px-captcha", "PerimeterX"),
    (b"datadome", "DataDome"),
    (b"awswaf", "AWS WAF"),
    (b"aws-waf-token", "AWS WAF"),
)

# Las candidatas que ya se han mirado desde fuera, con la ruta de una categoria y
# la de una ficha de las suyas. Estan aqui para que sondearlas sea escribir un
# nombre y no una direccion larga: un comando que hay que componer a mano es un
# comando que no se ejecuta.
CANDIDATAS = {
    "eroski": {
        "base": "https://supermercado.eroski.es",
        # Una categoria HOJA, no una rama. El 19 de septiembre de 2026 se sondeo
        # `/2059806-alimentacion/`, que es un nodo de navegacion: devolvio un
        # megabyte de menu -- 1.535 categorias, el arbol entero -- y **ni un solo
        # producto**. Es el mismo patron del nodo vacio de Alcampo, y la leccion
        # es la misma: sondear una rama no dice nada de lo que hay en las hojas.
        "categoria": ("/es/supermercado/2059698-frescos/2059699-frutas/"
                      "2059700-naranjas-y-otros-citricos/"),
        "ficha": "/es/productdetail/23760622-naranja-eroski-malla-3-kg/",
        "nota": "RESUELTA el 19 de septiembre de 2026. Se lee entera y sin "
                "navegador: la categoria hoja trae los productos servidos por el "
                "servidor, con su precio dentro de un `data-metrics` de GA4, el "
                "precio por kilo en texto y hasta las valoraciones de clientes. "
                "El menu da 1.593 categorias de una sola peticion. Ver "
                "docs/EROSKI.md.",
    },
    "ahorramas": {
        "base": "https://www.ahorramas.com",
        "categoria": "/cuidado-personal/desodorantes/otros-desodorantes/",
        "ficha": "/miel-de-flores-mel-da-anta-800g-47.html",
        "nota": "robots.txt permisivo y sitemaps de productos y categorias. Es "
                "Salesforce Commerce Cloud: falta ver si el precio viene en el "
                "HTML o por una peticion aparte.",
    },
    "consum": {
        "base": "https://tienda.consum.es",
        "categoria": None,
        "ficha": "/es/p/suavizante-concentrado-original/7451334",
        "nota": "DESCARTADA: su robots.txt dice Disallow: /api/ y la ficha es "
                "una SPA que solo trae un spinner. El unico camino al dato es "
                "el que el sitio prohibe.",
    },
}


EAN = re.compile(rb"\b(\d{13})\b")
# El euro se escribe en bytes, y de cuatro formas distintas segun como venga
# codificada la pagina. Aqui no se decodifica nada a proposito: decodificar mal
# una pagina es la forma de no encontrar un precio que si esta.
#
#   UTF-8            \xe2\x82\xac      lo normal hoy
#   cp1252           \x80             Windows-1252, todavia comun en Espana
#   iso-8859-15      \xa4             el "latin-9", que anadio el euro
#   entidad HTML     &euro; / &#8364;
EURO = rb"(?:&euro;|&#8364;|\xe2\x82\xac|\x80|\xa4|EUR)"

# Entre el numero y el simbolo casi nunca hay un espacio normal: hay un espacio
# **duro**. Y eso costo dar por muerta a Eroski dos veces.
#
# El 19 de septiembre de 2026 el sondeo dijo "precios con simbolo de euro: 0" en
# una pagina de Eroski que a la vista pone "1 KILO A 1,95 €". En bytes era:
#
#     b'1 KILO A  1,95\xc2\xa0\xe2\x82\xac'
#                        ^^^^^^^^ espacio duro (U+00A0 en UTF-8)
#
# `\s` en un patron de **bytes** solo casa el espacio ASCII, asi que no lo veia.
# Un falso negativo de estos no dice "no lo he encontrado": dice "aqui no hay
# precios", que es un veredicto, y con el se cierra una cadena que si se podia
# leer.
ESPACIO = rb"(?:[\s]|\xc2\xa0|&nbsp;|&#160;|\xa0)*"

PRECIO = re.compile(rb"(\d{1,3}[.,]\d{2})" + ESPACIO + EURO, re.IGNORECASE)
POR_UNIDAD = re.compile(
    EURO + ESPACIO + rb"/" + ESPACIO + rb"(?:kg|l|litro|ud|unidad)|"
    rb"(?:\d{1,3}[.,]\d{2})" + ESPACIO + EURO + ESPACIO + rb"/" + ESPACIO + rb"(?:kg|l)|"
    # "1 KILO A 1,95 €" y "PRECIO POR LITRO": muchas cadenas lo escriben en
    # prosa, no como una fraccion.
    rb"\b(?:1\s*)?(?:kilo|litro|unidad)\s*a\b|\bprecio\s+por\s+(?:kilo|litro|unidad)\b",
    re.IGNORECASE)
JSONLD = re.compile(rb'type=["\']application/ld\+json["\']', re.IGNORECASE)

# Una pagina moderna casi nunca escribe el precio en el HTML con su simbolo de
# euro al lado: lo trae dentro de un JSON incrustado que despues pinta el
# navegador. Buscar solo el "€" da un falso negativo que parece un veredicto.
#
# Paso con Eroski el 19 de septiembre de 2026: un megabyte de HTML, HTTP 200, sin
# reto delante... y cero euros. El dato estaba, pero no donde se estaba mirando.
ESTADOS = (
    (rb"__NEXT_DATA__", "Next.js (__NEXT_DATA__)"),
    (rb"__INITIAL_STATE__", "estado inicial (__INITIAL_STATE__)"),
    (rb"__NUXT__", "Nuxt (__NUXT__)"),
    (rb"__APOLLO_STATE__", "Apollo (__APOLLO_STATE__)"),
    (rb"window\.__", "algun window.__ con estado"),
    (rb"application/json", "un <script type=application/json>"),
    (rb"data-component-state", "estado en un atributo data-"),
)
# Claves con pinta de precio dentro de ese JSON, en varios idiomas y dialectos.
CLAVES_PRECIO = (b'"price"', b'"pvp"', b'"precio"', b'"unitPrice"', b'"amount"',
                 b'"priceValue"', b'"salePrice"', b'"currentPrice"')

# Un enlace con pinta de categoria. Que una pagina traiga el arbol entero es un
# hallazgo por si solo, aunque no traiga ni un precio: es el recorrido resuelto.
RUTA_CATEGORIA = re.compile(rb'href="[^"]*?(/[a-z]{2}/[a-z-]+/[0-9a-z/-]{6,90}/)"')


def reto_en(cuerpo: bytes, cabeceras: dict | None = None) -> str | None:
    """Nombre del reto anti-bot que hay delante, o None si no hay ninguno."""
    trozo = cuerpo[:200_000]
    for marca, nombre in RETOS:
        if marca.lower() in trozo.lower():
            return nombre
    for clave, valor in (cabeceras or {}).items():
        if clave.lower() in ("cf-mitigated", "x-datadome", "x-amzn-waf-action"):
            return f"cabecera {clave}: {valor}"
    return None


def _robots(base: str, f: Fetcher) -> tuple[urllib.robotparser.RobotFileParser | None, str]:
    url = urljoin(base, "/robots.txt")
    try:
        r = f.get(url, retries=1)
    except HTTPStatusError as exc:
        return None, f"robots.txt devuelve HTTP {exc.status}"
    except Exception as exc:  # noqa: BLE001
        return None, f"robots.txt no se pudo leer: {type(exc).__name__}"
    nombre = reto_en(r.body)
    if nombre:
        return None, f"robots.txt viene con un reto delante ({nombre})"
    rp = urllib.robotparser.RobotFileParser()
    rp.parse(r.body.decode("utf-8", "replace").splitlines())
    sitemaps = [ln.split(":", 1)[1].strip()
                for ln in r.body.decode("utf-8", "replace").splitlines()
                if ln.lower().startswith("sitemap:")]
    extra = f"; declara {len(sitemaps)} sitemap(s): {', '.join(sitemaps[:3])}" if sitemaps else ""
    return rp, f"robots.txt leido ({len(r.body)} bytes){extra}"


def _mira(nombre: str, url: str, f: Fetcher,
          rp: urllib.robotparser.RobotFileParser | None,
          guardar: Path | None = None) -> tuple[bool, bytes]:
    """Pide una direccion y cuenta lo que trae. Devuelve False si hay reto."""
    print(f"\n--- {nombre}: {url}")
    if rp is not None and not rp.can_fetch("*", url):
        print("    su robots.txt NO permite esta ruta a User-agent *. No se pide.")
        return True, b""
    try:
        r = f.get(url, retries=1)
        cuerpo, estado = r.body, r.status
    except HTTPStatusError as exc:
        cuerpo, estado = exc.body, exc.status
    except Exception as exc:  # noqa: BLE001
        print(f"    no se pudo pedir: {type(exc).__name__}: {exc}")
        return True, b""

    marca = reto_en(cuerpo)
    print(f"    HTTP {estado}, {len(cuerpo)} bytes")
    if marca:
        print(f"    *** RETO ANTI-BOT DELANTE: {marca} ***")
        return False, cuerpo
    if estado == 403:
        print("    403 sin marcas de reto. Casi siempre es la IP o el User-Agent,")
        print("    no un muro: repite esta misma prueba desde el PC de casa antes")
        print("    de dar la cadena por cerrada.")
        return True, cuerpo
    if estado >= 400:
        return True, cuerpo

    precios = PRECIO.findall(cuerpo)
    eans = sorted(set(EAN.findall(cuerpo)))
    print(f"    precios con simbolo de euro: {len(precios)}"
          f"{'  ej. ' + precios[0].decode() if precios else ''}")
    print(f"    precio por unidad (EUR/kg, EUR/l): "
          f"{'SI' if POR_UNIDAD.search(cuerpo) else 'no se ve'}")
    print(f"    JSON-LD: {'SI' if JSONLD.search(cuerpo) else 'no'}")
    print(f"    candidatos a EAN de 13 digitos: {len(eans)}"
          f"{'  ej. ' + eans[0].decode() if eans else ''}")
    if eans:
        _cruce(eans)

    enlaces = len(set(RUTA_CATEGORIA.findall(cuerpo)))
    if enlaces > 20:
        print(f"    enlaces con pinta de categoria: {enlaces} distintos "
              f"(el arbol de navegacion viene en esta misma respuesta)")

    estados = [nombre for marca, nombre in ESTADOS if re.search(marca, cuerpo)]
    claves = [c.decode() for c in CLAVES_PRECIO if c in cuerpo]
    if estados:
        print(f"    JSON incrustado: {', '.join(estados)}")
    if claves:
        print(f"    claves con pinta de precio dentro: {', '.join(claves)}")

    if guardar is not None:
        guardar.mkdir(parents=True, exist_ok=True)
        destino = guardar / f"{nombre}.html"
        destino.write_bytes(cuerpo)
        print(f"    guardado en {destino}")

    if not precios and not claves:
        print("    ni euros ni claves de precio: el dato viene por otra peticion.")
        print("    Vuelve a lanzarlo con --guardar y se puede mirar el cuerpo entero.")
    elif not precios and claves:
        print("    NO hay euros pero SI claves de precio: el precio esta dentro")
        print("    del JSON incrustado. Eso es bueno: no hace falta navegador.")
    return True, cuerpo


# Un enlace que parece una ficha de producto. Cada cadena tiene su patron, asi
# que se prueban varios y gana el primero que aparezca.
FICHAS = (
    re.compile(rb'href="([^"]*/productdetail/[^"]{4,120})"'),   # eroski
    re.compile(rb'href="([^"]*/p/[^"]{4,120})"'),               # consum, mercadona
    re.compile(rb'href="([^"]*/producto[s]?/[^"]{4,120})"'),
    re.compile(rb'href="([^"]*/product/[^"]{4,120})"'),
    re.compile(rb'href="([^"]{4,120}-\d{1,10}\.html)"'),        # ahorramas (SFCC)
)

# Direcciones que parecen fichas y no lo son. La ultima costo una peticion
# perdida: el 19 de septiembre de 2026 el sondeo de Eroski "siguio una ficha" y
# lo que siguio fue **el selector de idioma**:
#
#   .../es/supermarket.menulayout.menumobile.languageswitcher:changelanguage/es
#       ?t:ac=2059698-frescos/2059699-frutas/2059700-naranjas-y-otros-citricos
#
# Es una direccion de evento de Apache Tapestry: lleva un `:` en la ruta y un
# `t:ac=` en la query. Devolvio la misma pagina de la categoria y el sondeo dijo
# de ella lo mismo, asi que parecia que habia funcionado. Un falso positivo
# silencioso es peor que un error.
NO_SON_FICHA = (b"/login", b"/cesta", b"/carro", b"/basket", b"javascript:",
                b"t:ac=", b"t:formdata", b"languageswitcher", b"comparator",
                b"/search", b"/buscador")


def _una_ficha(cuerpo: bytes, base: str) -> str | None:
    """La primera direccion del cuerpo que parece una ficha de producto."""
    # Se mira el cuerpo **entero**, no los primeros N bytes. En Eroski el menu de
    # navegacion ocupa los primeros 600 KB y la rejilla de productos empieza
    # despues: recortar por delante dejaba fuera justo lo que se venia a buscar.
    for patron in FICHAS:
        for m in patron.finditer(cuerpo):
            ruta = m.group(1)
            baja = ruta.lower()
            if any(x in baja for x in NO_SON_FICHA):
                continue
            # Una direccion de evento de un marco web lleva `:` **en la ruta**.
            # Una ficha de producto, nunca. Ojo: el esquema y el puerto tambien
            # llevan dos puntos (`https://supermercado.eroski.es:443/...`), asi
            # que hay que mirar solo la ruta, no la direccion entera. Esa
            # distincion costo otra vuelta.
            entera = urljoin(base, ruta.decode("utf-8", "replace"))
            if ":" in urlparse(entera).path:
                continue
            return entera
    return None


def _cruce(eans: list[bytes]) -> None:
    """Cuantos de esos EAN ya estan en nuestro catalogo. Es la pregunta que decide."""
    fichero = config.GOLD / "grupos.parquet"
    if not fichero.exists():
        return
    try:
        import polars as pl
        nuestros = set(pl.read_parquet(fichero, columns=["ean"])["ean"]
                       .drop_nulls().cast(pl.Utf8).to_list())
    except Exception:  # noqa: BLE001
        return
    suyos = {e.decode() for e in eans}
    comunes = suyos & nuestros
    print(f"    de esos, YA los tenemos: {len(comunes)} de {len(suyos)}")
    if suyos:
        print("    (esta es la cifra que decide si merece la pena el colector:")
        print("     una cadena que no empareja no anade comparaciones)")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="sondear_cadena",
        description="Sondea una cadena nueva: si se puede, si se debe y si "
                    "compensa. Candidatas conocidas: " + ", ".join(CANDIDATAS))
    ap.add_argument("base", help="nombre de una candidata conocida "
                                 f"({', '.join(CANDIDATAS)}) o https://www.ejemplo.es")
    ap.add_argument("--categoria", help="ruta de una categoria con listado")
    ap.add_argument("--ficha", help="ruta de una ficha de producto")
    ap.add_argument("--ritmo", type=float, default=0.5,
                    help="peticiones por segundo (por defecto 0,5: despacio)")
    ap.add_argument("--guardar", action="store_true",
                    help="dejar cada respuesta en data/debug/sondeo/ para mirarla")
    a = ap.parse_args(argv)

    conocida = CANDIDATAS.get(a.base.strip().lower().rstrip("/"))
    if conocida:
        a.categoria = a.categoria or conocida["categoria"]
        a.ficha = a.ficha or conocida["ficha"]
        a.base = conocida["base"]
        print(f"lo que ya se sabia de esta: {conocida['nota']}\n")

    base = a.base if a.base.startswith("http") else f"https://{a.base}"
    dominio = urlparse(base).netloc
    print(f"=== sondeo de {dominio} (a {a.ritmo} pet/s) ===")
    f = Fetcher(rate_per_sec=a.ritmo)

    rp, dicho = _robots(base, f)
    print(f"\n--- robots.txt\n    {dicho}")

    carpeta = (config.DATA / "debug" / "sondeo" / dominio) if a.guardar else None
    seguir, cuerpos = True, {}
    for nombre, ruta in (("portada", "/"),
                         ("categoria", a.categoria),
                         ("ficha", a.ficha)):
        if not ruta or not seguir:
            continue
        seguir, cuerpos[nombre] = _mira(nombre, urljoin(base, ruta), f, rp, carpeta)

    # Si no sabiamos ninguna ficha, se busca una en la categoria y se sigue. Es
    # la unica forma de saber que publica una cadena por producto -- codigo de
    # barras, ingredientes, nutricion -- sin tener que adivinar su patron de URL.
    if seguir and not a.ficha and cuerpos.get("categoria"):
        enlace = _una_ficha(cuerpos["categoria"], base)
        if enlace:
            print("\n(no habia ficha apuntada; se sigue una de la categoria)")
            seguir, _ = _mira("ficha", enlace, f, rp, carpeta)
        else:
            print("\n(no se ha encontrado ningun enlace de producto en la "
                  "categoria: o no los hay, o la rejilla la pinta JavaScript)")

    print()
    if not seguir:
        print("VEREDICTO: hay un reto anti-bot delante. Aqui se para.")
        print("  No se resuelven ni se automatizan verificaciones anti-bot: es una")
        print("  linea distinta de leer una pagina publica. Si el reto solo salta")
        print("  desde fuera de casa, repite el sondeo desde el PC antes de cerrar.")
        return 1
    print("VEREDICTO: sin reto delante. Lo que decide ahora es el cruce de EAN")
    print("  y que el precio venga por una ruta que el robots.txt permita.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
