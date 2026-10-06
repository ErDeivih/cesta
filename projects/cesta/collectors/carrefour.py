"""Carrefour: sitemap oficial + catalogo SSR con window.__INITIAL_STATE__.

Listado:  /supermercado/<slug>/<catId>/c?offset=N   (avanza de 24 en 24)
Datos en: criteo.plpData.results.items
El Crawl-delay 60 de robots.txt pertenece solo a TwengaBot, no a User-agent *.
Ver docs/RECON.md.
"""
from __future__ import annotations

import re
import time
from datetime import datetime, timezone

import polars as pl

from core import alcance, cobertura, config, peticiones
from core.fetch import Fetcher, HTTPStatusError
from core.runlog import check_drift, log_run
from core.schemas import ESQUEMA_BRONZE, vacio
from core.sellos import conservacion_de, de_etiquetas
from core.state import js_object, to_cents
from core.storage import load_raw_bytes, load_raw_reciente, save_raw, write_parquet

BASE = "https://www.carrefour.es"
FUENTE = "carrefour"
# Cuantas veces se vuelve a por las categorias que fallaron, y cuanto se espera
# antes de cada vuelta. Tres vueltas cubren de sobra un bloqueo de Cloudflare,
# que el 18 de septiembre duro unos veinte minutos.
# El rescate espera **una vez por tanda**, y cada vuelta el doble que la anterior:
# 2, 4, 8 y 16 minutos, o sea media hora de margen en total.
#
# Antes eran tres vueltas creciendo en linea (2, 4 y 6 minutos: doce en total) y
# eso **no daba**. Medido en los dos dias que Cloudflare ha bloqueado de verdad:
#
#     18 sep   bloqueo de ~20 min, empezo pasada la categoria 300
#     19 sep   bloqueo de ~15 min, empezo en la peticion numero 1
#
# Con doce minutos de margen, las dos veces se habria acabado el rescate con el
# muro todavia puesto. Lo que salvo el dia 19 fue, por casualidad, que recorrer
# 653 categorias a una por segundo son once minutos: **andar hacia el muro estaba
# haciendo de espera**. Esa casualidad deja de existir en cuanto se corta el
# recorrido al detectar el bloqueo (ver `UMBRAL_BLOQUEO_TOTAL`), asi que la
# espera tiene que ser de verdad y no un efecto secundario.
#
# Esperar no cuesta nada cuando no hay bloqueo: el bucle sale en cuanto no quedan
# categorias fallidas.
VUELTAS_DE_RESCATE = 4
ESPERA_ENTRE_VUELTAS = 120

# ...pero esperar SI cuesta cuando lo que falla no es un bloqueo.
#
# El 20 de septiembre de 2026 no hubo ni un solo 403 en toda la ejecucion, y aun
# asi quedaron fallidas tres categorias:
#
#     papeleria/colorear           HTTP 500
#     papeleria/pequeno-accesorio  HTTP 500
#     papeleria/archivadores       HTTP 500
#
# Tres ramas de papeleria que el servidor de Carrefour sirve rotas. No es un
# muro que se levante solo: manana daran 500 otra vez. Con la regla anterior,
# esas tres categorias se llevaban las cuatro vueltas enteras -- media hora de
# `sleep` -- para volver a fallar igual las cuatro veces.
#
# Asi que la espera larga se reserva para lo que la necesita. Si entre las
# fallidas no hay ningun bloqueo, se da una segunda oportunidad corta (por si
# fue un 5xx pasajero, que los hay: ese mismo dia un 520 de Cloudflare se
# recupero al primer reintento) y se para. Lo que falla por su cuenta se cuenta
# como error de catalogo, que es lo que es.
ESTADOS_DE_BLOQUEO = (403, 429)
ESPERA_SIN_BLOQUEO = 30
VUELTAS_SIN_BLOQUEO = 1

# Cuantos 403 SEGUIDOS bastan para dar por hecho que el bloqueo es total y dejar
# de recorrer.
#
# El 19 de septiembre de 2026 Cloudflare bloqueo **desde la peticion numero 1**:
# a los catorce minutos llevaba 383 respuestas 403 y 2.563 productos de los
# 16.416 de un dia normal. Una de esas 403 fue a `https://www.carrefour.es/` a
# secas, la portada, que es la prueba de que no era una categoria concreta sino
# nosotros.
#
# Recorrer las 653 categorias en ese estado es coleccionar 653 fallos identicos:
# no se recoge nada, se tarda media hora y ademas cada peticion de mas alarga el
# bloqueo. Con esto, a los 25 seguidos se para, las que quedan se apuntan como
# fallidas y pasan al bucle de rescate, que es quien sabe esperar.
#
# Es la otra mitad de la leccion del dia anterior. Entonces se aprendio que no
# hay que esperar en cada peticion; ahora, que tampoco hay que enterarse 653
# veces de lo mismo.
UMBRAL_BLOQUEO_TOTAL = 25

# Categorias que el propio Carrefour sirve rotas, con su nombre y desde cuando.
#
# No es una tolerancia disfrazada: una tolerancia perdona "hasta N fallos,
# cualesquiera", y esto perdona **estas cuatro y ninguna mas**. Si manana falla
# una quinta, la captura sale incompleta aunque sigan siendo pocas.
#
# Cada una lleva la fecha en que empezo a fallar para que se vea cuanto lleva
# aqui, y el recorrido avisa cuando alguna vuelve a funcionar: una lista de
# excepciones donde las cosas entran y no salen nunca acaba siendo una excusa.
ROTAS_EN_ORIGEN = {
    # Anadida el 22 de septiembre de 2026. Ese dia la regla estricta tiro la
    # captura ENTERA de Carrefour -- 16.525 productos buenos y 47 minutos de
    # recorrido -- por culpa de esta sola categoria, que el servidor devuelve con
    # HTTP 500. Comprobado antes de anadirla, en `data/ejecuciones.log`: aparece
    # fallando en 10 ejecuciones distintas y la primera es del **8 de septiembre**,
    # dos semanas antes. Es hermana de dos de las de abajo: misma rama de
    # papeleria, misma averia.
    #
    # Ponerla aqui no es tapar el fallo: es que un dia entero de catalogo no puede
    # depender de que Carrefour arregle una pagina de cuadernos de colorear. El dia
    # que la arreglen, la entrada sobra y el propio recorrido lo dice (ver
    # `revividas` mas abajo), asi que se quita.
    "cat11729677": "papeleria/colorear, HTTP 500 desde el 8 sep 2026",
    "cat11729678": "papeleria/pequeno-accesorio, HTTP 500 desde el 20 sep 2026",
    "cat11729673": "papeleria/archivadores, HTTP 500 desde el 20 sep 2026",
    "cat32482101": "congelados/comidas-del-mundo/resto-del-mundo, "
                   "HTTP 520 desde el 20 sep 2026",
}

PAGE_SIZE = 24
SITEMAP_INDEX = f"{BASE}/crs/cdn-static/sitemap-food/index.xml"
_LOC = re.compile(r"<loc>([^<]+)</loc>")
_CATEGORIA = re.compile(r"/supermercado/(.+)/(cat\d+)/c/?$")

# El EAN sale gratis: el mismo HTML del listado lleva el datalayer de analitica
# (window["impressions"]), con el codigo de barras de cada producto. Los items de
# criteo.plpData NO traen ean13 aunque la palabra aparezca en la pagina (es de los
# banners de Criteo), asi que este es el unico sitio donde esta. Se empareja por el
# slug de la url, que es el mismo en los dos sitios; el product_id no lo es.
_EAN_DL = re.compile(
    r'"item_name":"([^"]+)","item_id":"\d+","item_ean":"(\d{8,14})"')
_SLUG_URL = re.compile(r"/supermercado/([^/]+)/R-")

# La mecanica de la oferta ("2a unidad -50%", "3x2", "-30% Dias Locos") solo esta
# en el HTML de la tarjeta, no en el JSON de `__INITIAL_STATE__` que leemos. Sin
# ella, Carrefour salia con cero promociones cuando en realidad tiene una en el
# 11,8 % de sus productos. Se ancla igual que el EAN: la tarjeta va desde el
# enlace del producto hasta el enlace del siguiente.
_TARJETA = re.compile(
    r'/supermercado/([^/"]+)/R-[^"]*?/p"(.*?)(?=/supermercado/[^/"]+/R-|$)', re.S)
_INSIGNIA = re.compile(r'class="badge badge-promotions"[^>]*>\s*<div title="([^"]{1,90})"')


def _promos_del_html(texto: str) -> dict[str, str]:
    """{slug del producto: la mecanica de su oferta}, para los que la tengan."""
    salida = {}
    for slug, tarjeta in _TARJETA.findall(texto):
        if m := _INSIGNIA.search(tarjeta):
            salida[slug] = m.group(1).strip()
    return salida


class SinCatalogo(Exception):
    """La pagina responde 200 pero no trae rejilla de productos.

    Pasa con categorias vacias y con paginas de marca o "tienda dentro de la
    tienda", que usan otra plantilla. No es un fallo de extraccion: es una
    categoria del sitemap que no lista nada, igual que las que dan 404.
    """


# Reparto del tiempo de la ejecucion. Sin esto solo se puede especular sobre por
# que una pasada con todo cacheado tarda mucho mas que otra igual.
TIEMPOS = {"disco": 0.0, "red": 0.0, "parseo": 0.0, "cacheadas": 0, "pedidas": 0}


def _raw(f: Fetcher, url: str, clave: str, *, sin_cache: bool = False) -> bytes:
    """La respuesta, de la cache del dia o de la red.

    `sin_cache` existe por un fallo medido el 19 de septiembre de 2026. Una
    pagina de `cat20013` llego **cortada** -- 220.978 caracteres de los ~468.000
    que trae entera --, asi que el objeto de JavaScript no cerraba y el parseo
    fallo. Hasta ahi, normal: una de cada 2.648. Lo malo fue lo siguiente: el
    cuerpo cortado **se habia guardado en el crudo del dia**, asi que las tres
    vueltas de rescate volvieron a leerlo de disco y fallaron exactamente igual,
    sin tocar la red. La categoria entera se perdio por una descarga cortada que
    nadie volvio a pedir.

    Es otra vez la regla de siempre: la cache multiplica cualquier fallo. Cuando
    el parseo no traga, hay que volver a pedirlo de verdad.
    """
    if not sin_cache:
        t0 = time.perf_counter()
        body = load_raw_bytes(FUENTE, clave)
        TIEMPOS["disco"] += time.perf_counter() - t0
        if body is not None:
            TIEMPOS["cacheadas"] += 1
            return body

    t0 = time.perf_counter()
    r = f.get(url)
    TIEMPOS["red"] += time.perf_counter() - t0
    TIEMPOS["pedidas"] += 1
    body = r.body

    t0 = time.perf_counter()
    save_raw(FUENTE, clave, body)
    TIEMPOS["disco"] += time.perf_counter() - t0
    return body


def _sitemap(f: Fetcher, url: str, clave: str) -> str:
    """El sitemap de hoy; si hoy no se deja, el mas reciente que si se dejo.

    El 11 y el 12 de sep Carrefour devolvio 403 a estas peticiones dos dias
    seguidos, y como sin el indice de secciones no hay recorrido, se perdio el
    catalogo entero de ambos dias. El indice de secciones de un supermercado es
    de lo mas estable que hay: usar el de ayer es infinitamente mejor que no
    tener precios. Si falla y tampoco hay nada guardado, entonces si se rinde.
    """
    try:
        return _raw(f, url, clave).decode("utf-8", "replace")
    except Exception as exc:
        guardado = load_raw_reciente(FUENTE, clave)
        if guardado is None:
            raise
        cuerpo, dia = guardado
        print(f"  {type(exc).__name__} al pedir {clave}; se usa el guardado "
              f"del {dia}", flush=True)
        return cuerpo.decode("utf-8", "replace")


def categorias(f: Fetcher) -> list[tuple[str, str]]:
    """Devuelve (id, slug completo) desde el sitemap que publica Carrefour."""
    indice = _sitemap(f, SITEMAP_INDEX, "sitemap-index")
    mapas = [u for u in _LOC.findall(indice) if "categor" in u.lower()]
    if not mapas:
        raise ValueError("el indice de sitemaps no contiene categorias")
    salida = []
    saltadas = 0        # categorias de bazar no pedidas (T01)
    for numero, url in enumerate(mapas):
        xml = _sitemap(f, url, f"sitemap-categorias-{numero}")
        for categoria_url in _LOC.findall(xml):
            if m := _CATEGORIA.search(categoria_url):
                # **El bazar no se pide** (T01). Ver `_fuera_de_alcance`.
                if _fuera_de_alcance(m.group(1)):
                    saltadas += 1
                    peticiones.evita(FUENTE)   # categoria de bazar: no se pide
                    continue
                salida.append((m.group(2), m.group(1)))
    if saltadas:
        print(f"  {saltadas} categorias fuera de alcance: no se han pedido", flush=True)
    return list(dict.fromkeys(salida))


# La categoria que Carrefour dice haber servido. Cuando no coincide con la que
# pedimos, esa direccion ya no existe y nos han dado la de su padre.
_SERVIDA = re.compile(r'"navigation_id":"(cat\d+)"')


def _fuera_de_alcance(slug: str) -> bool:
    """¿Esta categoria es bazar? Entonces ni se pide su listado.

    La categoria viene en la URL (`supermercado/<slug>/<catId>/c`), asi que se sabe **antes** de
    pedir el listado, que es justo lo que hace falta para ahorrar peticiones. Y con esto no puede
    pasar lo de Alcampo el 5 de octubre de 2026: una rama de bazar hundida **no veta una captura
    incluida**, porque ni entra en la captura.

    **Solo se salta lo excluido, nunca lo que hay que revisar**, y si el clasificador falla se pide
    igual: una peticion de mas es barata; perder una rama de comida, no.
    """
    try:
        return alcance.clasificar_alcance(None, slug.replace("-", " ")).estado == alcance.EXCLUIDO
    except Exception:  # noqa: BLE001
        return False


def listado(f: Fetcher, cat_id: str, slug: str = "c", offset: int = 0) -> dict:
    url = f"{BASE}/supermercado/{slug}/{cat_id}/c?offset={offset}"
    clave = f"{cat_id}-{offset}"
    body = _raw(f, url, clave)
    try:
        return _lee_listado(body, cat_id, offset)
    except SinCatalogo:
        raise
    except ValueError:
        # El parseo no traga. Si el cuerpo venia de la cache puede estar cortado
        # de una descarga anterior, asi que se pide de verdad una vez mas antes
        # de dar la categoria por perdida.
        body = _raw(f, url, clave, sin_cache=True)
        return _lee_listado(body, cat_id, offset)


def _lee_listado(body: bytes, cat_id: str, offset: int) -> dict:
    t0 = time.perf_counter()
    texto = body.decode("utf-8", "replace")
    st = js_object(texto, "__INITIAL_STATE__")
    eans = dict(_EAN_DL.findall(texto))
    promos = _promos_del_html(texto)
    servida = _SERVIDA.search(texto)
    TIEMPOS["parseo"] += time.perf_counter() - t0
    resultados = (((st.get("criteo") or {}).get("plpData") or {}).get("results"))
    if not isinstance(resultados, dict) or "items" not in resultados:
        raise SinCatalogo(f"{cat_id}@{offset}")
    return {
        "items": resultados["items"],
        "total": (st.get("pagination") or {}).get("total_results") or 0,
        "eans": eans,
        "promos": promos,
        "servida": servida.group(1) if servida else None,
    }


def _ean_de(p: dict, eans: dict[str, str] | None) -> str | None:
    if not eans:
        return None
    m = _SLUG_URL.search(p.get("url") or "")
    return eans.get(m.group(1)) if m else None


def _promo_de(p: dict, promos: dict[str, str] | None) -> str | None:
    if not promos:
        return None
    m = _SLUG_URL.search(p.get("url") or "")
    return promos.get(m.group(1)) if m else None


def _fecha_fin(texto: str | None) -> datetime | None:
    """Su fecha viene como "21/09/2026". Si no se entiende, no se inventa."""
    if not texto:
        return None
    try:
        return datetime.strptime(texto.strip(), "%d/%m/%Y").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _promocion(p: dict, promos: dict[str, str] | None) -> tuple[str | None, str | None]:
    """La oferta y hasta cuando dura.

    El JSON del listado trae `badge_map.promotions`, con el nombre de la
    mecanica Y su fecha de fin. Es mejor que el `title` que sacabamos del HTML:
    medido el 17 de septiembre, 1.032 promociones y **las 1.032 con fecha**.
    El respaldo del HTML se queda para cuando el JSON no la traiga.
    """
    for promo in ((p.get("badge_map") or {}).get("promotions") or []):
        if nombre := promo.get("name"):
            return nombre.strip(), promo.get("end_date")
    # MEDIDO Y DESCARTADO el 17 de septiembre de 2026: `badge.description` trae
    # la mecanica explicada con palabras ("Compra 2 unidades de este producto y
    # te descontamos el 50% en la segunda") y parecia mejor que la insignia
    # corta. No lo es. Nunca aparece sin `badge_map.promotions` -- van siempre
    # juntas, en los 5.542 productos mirados -- y de las 102 insignias que
    # `promos.lee()` no entiende, el texto largo no rescata **ninguna**: son
    # "Envio Gratis", "XXL Ahorro", "Super Precio", que no son mecanicas.
    # Se deja anotado para que nadie lo vuelva a intentar.
    return _promo_de(p, promos), None


def a_registro(p: dict, categoria: str | None = None,
               eans: dict[str, str] | None = None,
               promos: dict[str, str] | None = None) -> dict:
    # Al reprocesar desde el crudo no hay quien pase la categoria, los EAN ni
    # las promociones: son de la PAGINA, no del producto, y el reprocesador solo
    # ve productos sueltos. `productos_crudo` se los engancha a cada item en
    # "_ctx" antes de devolverlos, y aqui se recogen si no vinieron por argumento.
    ctx = p.get("_ctx") or {}
    categoria = categoria or ctx.get("categoria")
    eans = eans or ctx.get("eans")
    promos = promos or ctx.get("promos")
    promo_txt, promo_hasta_txt = _promocion(p, promos)
    # Carrefour marca sus productos con etiquetas de dieta y de conservacion,
    # y no las miraba nadie: 908 sin gluten, 267 sin lactosa, 218 bio.
    etiquetas = [t.get("message") for t in (p.get("info_tags") or []) if t.get("message")]
    r = vacio()
    r.update({
        "fuente": FUENTE,
        "id_fuente": p.get("product_id"),
        "ean": _ean_de(p, eans),
        "nombre": p.get("name"),
        "marca": p.get("brand"),
        "formato_txt": None,
        "precio_cent": to_cents(p.get("price")),
        "precio_ref_nativo_cent": to_cents(p.get("price_per_unit")),
        "unidad_ref_nativa": (p.get("measure_unit") or "").lower() or None,
        "promo": bool(promo_txt or p.get("promotion") or p.get("promotions")),
        "promo_txt": promo_txt,
        "promo_hasta": _fecha_fin(promo_hasta_txt),
        "sellos": de_etiquetas(etiquetas),
        "conservacion": conservacion_de(etiquetas),
        # Carrefour dice cuantas unidades lleva el pack. No hace falta leerlo
        # del nombre como en las otras cadenas.
        "es_pack": (p.get("sell_pack_unit") or 1) > 1 or None,
        "categoria": categoria,
        "disponible": (p.get("units_in_stock") or 0) > 0,
        "url": BASE + (p.get("url") or ""),
        "imagen": (p.get("images") or {}).get("desktop"),
        "capturado_en": datetime.now(timezone.utc),
    })
    return r


def plural_vueltas(n: int) -> str:
    """Las vueltas que se dieron, no las que caben.

    El mensaje decia siempre "despues de 4 vueltas" porque leia la constante en
    vez de contar. Desde que el rescate puede pararse pronto -- tres categorias
    de papeleria rotas no se arreglan esperando -- eso paso a ser mentira: el 21
    de septiembre de 2026 dio **una** vuelta y el log seguia diciendo cuatro.
    Una cifra inventada en un log de operacion envenena la siguiente lectura.
    """
    if n == 0:
        return "ninguna vuelta"
    return "1 vuelta" if n == 1 else f"{n} vueltas"


def _por_que_fallan(fallidas, ultimo_fallo) -> str:
    """"3 con HTTP 500, 1 sin respuesta": el reparto de motivos, en una linea."""
    cuenta: dict[int, int] = {}
    for cat_id, _ in fallidas:
        estado = ultimo_fallo.get(cat_id, 0)
        cuenta[estado] = cuenta.get(estado, 0) + 1
    trozos = [f"{n} {'con HTTP ' + str(e) if e else 'sin respuesta'}"
              for e, n in sorted(cuenta.items(), key=lambda par: -par[1])]
    return ", ".join(trozos)


def main() -> int:
    t0, errores = time.monotonic(), 0
    # Deja el recuento del dia escrito al terminar el proceso:
    peticiones.registra_al_salir(FUENTE)
    f = Fetcher(rate_per_sec=config.RITMO[FUENTE])
    try:
        cats = categorias(f)
    except Exception as exc:  # noqa: BLE001
        log_run(FUENTE, 0, 1, time.monotonic() - t0)
        print(f"  no se pudieron leer las categorias: {exc}")
        return 1
    print(f"  {len(cats)} categorias del sitemap")

    productos: dict[str, dict] = {}
    contadores = {"paginas": 0, "obsoletas": 0, "sin_catalogo": 0, "redirigidas": 0}
    redirigidas: dict[str, str] = {}
    # Por que fallo cada categoria la ultima vez: el codigo HTTP, o 0 si no fue
    # una respuesta sino una excepcion. Lo lee el rescate para saber si lo que
    # tiene delante es un muro (que hay que esperar) o una pagina rota (que no).
    ultimo_fallo: dict[str, int] = {}

    def recorre(lista, etiqueta=""):
        """Recorre categorias y devuelve las que fallaron, para reintentarlas.

        Antes esta funcion no existia y el bucle vivia suelto en `main`: una
        categoria que fallaba se contaba como error y **se perdia para el dia**.
        El 18 de septiembre de 2026 Cloudflare devolvio 403 en 373 de las 653
        categorias; el bloqueo se levanto solo a mitad de ejecucion y las 373 ya
        estaban descartadas. Se perdio el 57 % del catalogo por no volver a
        intentarlo mas tarde.
        """
        fallidas = []
        seguidas = 0          # 403 consecutivos: si son muchos, el bloqueo es total
        for posicion, (cat_id, slug) in enumerate(lista, start=1):
            offset, total = 0, None
            try:
                while total is None or offset < total:
                    pagina = listado(f, cat_id, slug, offset)
                    contadores["paginas"] += 1
                    # Una categoria que ya no existe no da 404: Carrefour sirve
                    # **la de su padre**, con su navigation_id dentro y su
                    # paginacion entera. Sin mirarlo, se recorren las 42 paginas
                    # del padre otra vez, y otra por cada hija difunta.
                    #
                    # Medido sobre el crudo del 19 de septiembre de 2026: 531 de
                    # 2.634 paginas, **el 20 % de todo lo que se pidio ese dia**.
                    # El caso gordo, `cat20001`: 462 paginas servidas para 1.008
                    # productos, o sea 420 paginas repetidas.
                    servida = pagina.get("servida")
                    if servida and servida != cat_id:
                        redirigidas[cat_id] = servida
                        contadores["redirigidas"] += 1
                        break
                    total = int(pagina["total"] or 0)
                    items = pagina["items"]
                    for p in items:
                        producto_id = str(p.get("product_id") or "")
                        if producto_id:
                            productos[producto_id] = a_registro(
                                p, slug, pagina.get("eans"), pagina.get("promos"))
                    if not items:
                        break
                    offset += PAGE_SIZE
            except SinCatalogo:
                contadores["sin_catalogo"] += 1
                continue
            except HTTPStatusError as exc:
                if exc.status == 404:
                    contadores["obsoletas"] += 1
                    continue
                fallidas.append((cat_id, slug))
                ultimo_fallo[cat_id] = exc.status
                print(f"  error HTTP en {posicion}/{len(lista)}{etiqueta} "
                      f"{cat_id}: {exc}")
                seguidas = seguidas + 1 if exc.status == 403 else 0
                if seguidas >= UMBRAL_BLOQUEO_TOTAL:
                    restantes = list(lista)[posicion:]
                    fallidas.extend(restantes)
                    # No se han llegado a pedir, pero se dejan de pedir POR el
                    # bloqueo: cuentan como bloqueadas para el rescate.
                    for pendiente, _ in restantes:
                        ultimo_fallo[pendiente] = 403
                    print(f"  {seguidas} bloqueos seguidos{etiqueta}: el bloqueo "
                          f"es total, no una categoria. Se deja de recorrer y las "
                          f"{len(restantes)} que quedan pasan al rescate, que es "
                          f"quien sabe esperar.", flush=True)
                    return fallidas
            except Exception as exc:  # noqa: BLE001
                fallidas.append((cat_id, slug))
                ultimo_fallo[cat_id] = 0
                print(f"  error en {posicion}/{len(lista)}{etiqueta} {cat_id}: {exc}")
                seguidas = 0
            else:
                seguidas = 0
            if posicion % 25 == 0:
                print(f"  progreso{etiqueta}: {posicion}/{len(lista)} categorias, "
                      f"{len(productos)} productos unicos", flush=True)
        return fallidas

    fallidas = recorre(cats)
    vueltas_dadas = 0
    # Segunda y tercera oportunidad. Un bloqueo por sospecha de bot se levanta
    # solo, y lo que hace falta es estar ahi cuando se levante. Cada vuelta
    # espera mas y va mas despacio, porque insistir al mismo ritmo es lo que nos
    # tenia fichados.
    for vuelta in range(1, VUELTAS_DE_RESCATE + 1):
        if not fallidas:
            break
        bloqueadas = sum(1 for c, _ in fallidas
                         if ultimo_fallo.get(c) in ESTADOS_DE_BLOQUEO)
        if bloqueadas:
            espera = ESPERA_ENTRE_VUELTAS * 2 ** (vuelta - 1)
            print(f"  {len(fallidas)} categorias quedaron sin recoger "
                  f"({bloqueadas} por bloqueo); se espera {espera}s y se "
                  f"reintentan a ritmo mas lento (vuelta {vuelta})", flush=True)
        elif vuelta > VUELTAS_SIN_BLOQUEO:
            print(f"  quedan {len(fallidas)} categorias y ninguna esta "
                  f"bloqueada: {_por_que_fallan(fallidas, ultimo_fallo)}. Eso no "
                  f"se arregla esperando, asi que no se espera mas y se cuentan "
                  f"como errores de catalogo.", flush=True)
            break
        else:
            espera = ESPERA_SIN_BLOQUEO
            print(f"  {len(fallidas)} categorias quedaron sin recoger y ninguna "
                  f"por bloqueo ({_por_que_fallan(fallidas, ultimo_fallo)}); se "
                  f"espera {espera}s por si fue pasajero (vuelta {vuelta})",
                  flush=True)
        time.sleep(espera)
        vueltas_dadas = vuelta
        # Mas despacio, pero **el mismo** fetcher: ver `Fetcher.cambia_ritmo`.
        # Un fetcher nuevo tira las cookies que nos han costado media hora de
        # navegacion limpia y nos presenta como un desconocido.
        f.cambia_ritmo(config.RITMO[FUENTE] / (2 ** vuelta))
        antes = len(fallidas)
        fallidas = recorre(fallidas, etiqueta=f" (rescate {vuelta})")
        print(f"  rescatadas {antes - len(fallidas)} de {antes}", flush=True)

    errores = len(fallidas)
    paginas = contadores["paginas"]
    obsoletas = contadores["obsoletas"]
    sin_catalogo = contadores["sin_catalogo"]

    if contadores["redirigidas"]:
        # Si nos redirigen a una categoria que no recorremos por su cuenta, sus
        # productos se pierden y nadie lo nota. Eso si hay que decirlo.
        pedidas = {c for c, _ in cats}
        huerfanas = {d for d in redirigidas.values() if d not in pedidas}
        print(f"  {contadores['redirigidas']} categorias redirigen a la de su "
              f"padre; se dejan de paginar")
        if huerfanas:
            print(f"  OJO: {len(huerfanas)} de esos destinos no se recorren por "
                  f"su cuenta ({', '.join(sorted(huerfanas)[:5])}): sus productos "
                  f"no los coge nadie")
    if obsoletas:
        print(f"  {obsoletas} categorias del sitemap ya no existen")
    if sin_catalogo:
        print(f"  {sin_catalogo} categorias sin rejilla de productos (marca o vacias)")

    filas = list(productos.values())
    # Aqui habia una tolerancia: hasta el 2 % de las categorias podia fallar y
    # el dia se daba por bueno igual. Era comodo y era mentira. "3 errores
    # dentro de la tolerancia de 13" no dice si el catalogo esta entero: dice
    # que hemos decidido no mirar. Y una franquicia anonima acaba tapando
    # cualquier cosa que quepa dentro de ella.
    #
    # Ahora solo se perdona lo que este **declarado con su nombre** en
    # `ROTAS_EN_ORIGEN`, y cualquier otro fallo deja la captura incompleta. Sin
    # numero de por medio: o estan todas, o falta alguna y se dice cual.
    no_declaradas = [(c, s) for c, s in fallidas if c not in ROTAS_EN_ORIGEN]
    declaradas = [(c, s) for c, s in fallidas if c in ROTAS_EN_ORIGEN]
    completa = bool(filas) and not no_declaradas
    if declaradas:
        print(f"  {len(declaradas)} categorias rotas en el propio Carrefour, "
              f"declaradas y no contadas como fallo nuestro:")
        for cat_id, _ in declaradas:
            print(f"      {cat_id}  {ROTAS_EN_ORIGEN[cat_id]}")
    if no_declaradas:
        print(f"  {len(no_declaradas)} categorias de {len(cats)} no se pudieron "
              f"recoger y no estan declaradas, asi que la captura NO esta "
              f"completa (despues de {plural_vueltas(vueltas_dadas)} de rescate):")
        for cat_id, slug in no_declaradas:
            print(f"      {cat_id}  {slug}  ultimo fallo: "
                  f"{ultimo_fallo.get(cat_id) or 'sin respuesta'}")
    # Una rota que vuelve a funcionar tiene que salir de la lista, o la lista se
    # convierte en un sitio donde las cosas entran y no salen nunca.
    revividas = [c for c in ROTAS_EN_ORIGEN
                 if c in {x for x, _ in cats} and c not in dict(fallidas)]
    if revividas:
        print(f"  {len(revividas)} categorias declaradas rotas ya funcionan "
              f"({', '.join(sorted(revividas))}): quitalas de ROTAS_EN_ORIGEN")
    # Y aunque los errores entren en la tolerancia, puede faltar una rama entera:
    # una sola categoria de las gordas vale por cincuenta pequenas. Ver
    # core/cobertura.py y lo que le paso a Frescos en Alcampo.
    if filas:
        caidas = cobertura.revisa(
            pl.DataFrame(filas, schema_overrides=ESQUEMA_BRONZE), FUENTE)
        if caidas:
            completa = False
            print("  faltan ramas enteras respecto a la ultima captura buena:")
            for linea in caidas:
                print(f"      {linea}")
    if completa:
        df = pl.DataFrame(filas, schema_overrides=ESQUEMA_BRONZE)
        df = df.unique(subset=["fuente", "id_fuente"], keep="last")
        write_parquet(df, "bronze", FUENTE)
        filas = df.to_dicts()
    elif filas:
        print("  ejecucion parcial: se conserva el ultimo bronze completo")

    segundos = time.monotonic() - t0
    aviso = check_drift(FUENTE, len(filas))
    log_run(FUENTE, len(filas), errores, segundos, completa)
    if aviso:
        print(f"  {aviso}")
    print(f"  {paginas} paginas "
          f"({TIEMPOS['cacheadas']} de cache, {TIEMPOS['pedidas']} pedidas)")
    medido = TIEMPOS["red"] + TIEMPOS["disco"] + TIEMPOS["parseo"]
    print(f"  tiempo: red {TIEMPOS['red']:.0f}s | disco {TIEMPOS['disco']:.0f}s | "
          f"parseo {TIEMPOS['parseo']:.0f}s | resto {segundos - medido:.0f}s")
    print(f"{FUENTE}: {len(filas)} productos, {errores} errores, {segundos:.0f}s")
    return 0 if completa else 1


if __name__ == "__main__":
    raise SystemExit(main())


# El slug de la categoria dentro de la URL canonica de la pagina guardada.
_CANONICA = re.compile(r'<link rel="canonical" href="[^"]*?/supermercado/([a-z0-9\-]+)/')


def productos_crudo(body: bytes) -> list[dict]:
    """Para reprocesar: saca los productos del HTML guardado.

    Carrefour guarda paginas HTML con extension .json.gz, asi que el extractor
    generico del reprocesador hacia `json.loads`, fallaba y devolvia lista vacia.
    Resultado: durante once dias los 16.416 productos de Carrefour NO se podian
    reprocesar, o sea que cualquier arreglo del parser exigia volver a scrapear
    una cadena protegida por Cloudflare. Esa es justo la situacion que guardar el
    crudo deberia evitar.

    La categoria no se puede recuperar de la clave del fichero (se guarda con la
    clave ya pasada por sha1), pero si de la URL canonica que trae el propio HTML,
    que ademas es mas fiable: es la que Carrefour dice que es.
    """
    try:
        texto = body.decode("utf-8", "replace")
        st = js_object(texto, "__INITIAL_STATE__")
    except Exception:  # noqa: BLE001
        return []
    resultados = ((st.get("criteo") or {}).get("plpData") or {}).get("results")
    if not isinstance(resultados, dict):
        return []
    items = resultados.get("items") or []
    m = _CANONICA.search(texto)
    ctx = {
        "categoria": m.group(1) if m else None,
        "eans": dict(_EAN_DL.findall(texto)),
        "promos": _promos_del_html(texto),
    }
    for item in items:
        if isinstance(item, dict):
            item["_ctx"] = ctx
    return [i for i in items if isinstance(i, dict)]
