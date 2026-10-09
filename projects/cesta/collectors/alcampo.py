"""Alcampo: arbol de categorias y catalogo mediante su API interna.

Verificado el 6 sep 2026:
  - `/api/webproductpagews/v1/categories` trae el arbol.
  - `/api/webproductpagews/v6/product-pages` devuelve hasta 300 productos ya
    decorados, con formato, precio unitario y promociones.
  - Si una categoria es demasiado ancha, `additionalPageInfo.categories` permite
    bajar recursivamente a sus hijas. Asi no se pierde lo que el SSR cortaba a 50.
"""
from __future__ import annotations

import json
import time
import unicodedata
from collections import deque
from datetime import datetime, timezone
from urllib.parse import quote, urlencode

import polars as pl

from core import alcance, cobertura, config, peticiones, waf
from core.fetch import Fetcher, HTTPStatusError
from core.promos import fechas
from core.runlog import check_drift, log_run
from core.schemas import ESQUEMA_BRONZE, vacio
from core.sellos import conservacion_de, de_etiquetas
from core.state import js_object
from core.storage import load_raw_bytes, save_raw, write_parquet

BASE = "https://www.compraonline.alcampo.es"
DOMINIO = "compraonline.alcampo.es"
FUENTE = "alcampo"
# pagina protegida con la que se comprueba que la sesion sirve de verdad
URL_PRUEBA = f"{BASE}/categories/frescos/pasteler%C3%ADa/OC1282"
RAIZ = "/categories/alimentaci%C3%B3n/OCC10"
REGION = "ac90d761-9d58-4918-a37d-dd14e1ce384a"   # peninsula
TOPE_API = 300
# Terminos del buscador que se recorren cada dia. Solo se usan para rellenar las
# categorias que aun asi se truncan; los 5.153 rotan a lo largo de ~9 dias.
TERMINOS_POR_DIA = 600
# Son escaparates que repiten productos de las ramas reales. Recorrerlos aumenta
# mucho las peticiones y puede alcanzar el limite de 300 sin aportar SKUs nuevos.
RAMAS_REPETIDAS = {"folletos y promociones", "campanas"}

# la etiqueta de su precio unitario -> nuestra unidad
_UNIDAD = {
    "fop.price.per.kg": ("kg", 1), "fop.price.per.litre": ("l", 1),
    "fop.price.per.l": ("l", 1), "fop.price.per.100gram": ("kg", 10),
    "fop.price.per.100g": ("kg", 10), "fop.price.per.100ml": ("l", 10),
    "fop.price.per.gram": ("kg", 1000), "fop.price.per.ml": ("l", 1000),
    "fop.price.per.meter": ("m", 1), "fop.price.per.unit": ("ud", 1),
    "fop.price.per.piece": ("ud", 1), "fop.price.per.each": ("ud", 1),
    "fop.price.per.dozen": ("ud", 1 / 12),
    "per_kilo": ("kg", 1), "per_litre": ("l", 1), "per_unit": ("ud", 1),
    # **Los nombres de `unitName`.** Su API manda dos formas para lo mismo y el mapa solo tenia la de
    # `unit`; `unitName` llega en mayusculas ("PER_100ML") y se busca en minusculas. Sin estas, la
    # etiqueta no se reconocia, el factor se quedaba en 1 y el valor pasaba sin escalar: medido el
    # 9 de octubre de 2026, **190.732 filas de Alcampo (29,8 %) sin unidad de referencia**.
    #
    # Cada una se mapea igual que su gemela `fop.*`: son sinonimos, no reglas nuevas.
    "per_100ml": ("l", 10), "per_100g": ("kg", 10), "per_100gram": ("kg", 10),
    "per_kg": ("kg", 1), "per_l": ("l", 1), "per_liter": ("l", 1),
    "per_g": ("kg", 1000), "per_gram": ("kg", 1000), "per_ml": ("l", 1000),
    "per_m": ("m", 1), "per_meter": ("m", 1), "per_metro": ("m", 1),
    "per_piece": ("ud", 1), "per_each": ("ud", 1), "per_dozen": ("ud", 1 / 12),
    "per_ud": ("ud", 1), "per_unidad": ("ud", 1),
}


def _unidad_referencia(p: dict, etiqueta_html: str) -> tuple[str | None, float]:
    """La unidad de su precio de referencia y por cuanto hay que multiplicarlo.

    Su API manda dos nombres para lo mismo: `unit` ("fop.price.per.100ml") y
    `unitName` ("PER_100ML"). Solo el primero esta en el mapa, asi que se mira
    antes. Y publica precios por 100 g o por 100 ml, que hay que llevar a kg o l
    para poder comparar con las demas cadenas.
    """
    for clave in (etiqueta_html, (p.get("unitPrice") or {}).get("unit"),
                  (p.get("unitPrice") or {}).get("unitName")):
        hallado = _UNIDAD.get(str(clave or "").lower())
        if hallado:
            return hallado
    return None, 1.0


def _estado(f: Fetcher, ruta: str) -> dict:
    r = f.get(BASE + ruta)
    _guardar(ruta, r.body)
    html = r.body.decode("utf-8", "replace")
    try:
        return js_object(html, "__INITIAL_STATE__")
    except ValueError:
        if waf.es_reto(html):
            raise RetoWAF(ruta) from None
        destino = config.DEBUG / f"alcampo_sin_estado_{abs(hash(ruta)) % 10**8}.html"
        destino.write_text(html[:200_000], encoding="utf-8", errors="replace")
        raise


class RetoWAF(Exception):
    """La pagina llego con el reto de AWS WAF en vez de con datos."""


# Cuantas veces se renueva la cookie en una misma pasada. Empezo siendo una sola:
# al segundo corte se abandonaba el recorrido entero. Con tres se paso de 6.623
# productos a 21.199; con ocho, a 36.935, y aun asi corto antes de terminar.
MAX_RENOVACIONES = 20

# Cuantos reintentos con la MISMA sesion antes de tocar el navegador. Existe porque
# el 25 de septiembre de 2026 el dueno dijo *"a veces salta el navegador"*: el WAF
# corta entre 8 y 13 veces al dia (13 el dia 24, 10 el 23) y cada corte abria Chrome
# **a la vista**. Muchos de esos cortes son del momento -- una racha de peticiones --,
# y con la espera de `ESPERA_TRAS_CORTE` la misma cookie vuelve a valer: abrir una
# ventana que le roba el foco al ordenador de casa es lo ultimo que hay que probar,
# no lo primero. Dos reintentos, y si con eso no pasa, sesion nueva.
REINTENTOS_SIN_NAVEGADOR = 2

# Renovar la cookie al instante no sirve cuando lo que ha saltado no es que el
# testigo caduque, sino que AWS WAF nos ha marcado por ritmo: el testigo nuevo
# nace ya vigilado. Esperar antes de pedirlo es lo que deja que el contador del
# otro lado se enfrie. La espera crece con cada corte y se topa, porque una
# espera de diez minutos cuesta mas que perder esa categoria.
ESPERA_TRAS_CORTE = 20      # segundos, x numero de corte
ESPERA_MAXIMA = 90

# Hay dos situaciones distintas que se ven igual desde dentro. Una: el testigo ha
# caducado a mitad de un recorrido largo, se renueva y se sigue -- asi se paso de
# 6.623 productos a 36.935. Otra: AWS WAF ya nos tiene fichados por haber tirado
# fuerte hace un rato, y entonces el testigo nuevo nace marcado y vuelve a cortar
# a las pocas categorias. En el segundo caso insistir es tirar media hora de
# esperas para acabar igual, y ademas empeora la reputacion de la IP para el dia
# siguiente. Si tras estos cortes seguimos sin haber recogido casi nada, se deja
# para manana con lo que haya en cache.
CORTES_PARA_RENDIRSE = 6
AVANCE_MINIMO = 0.25        # fraccion del ultimo catalogo bueno

# Cuanto puede encoger una captura y seguir siendo mejor que la de ayer. El 8 sep
# el recorrido duro casi diez horas, visito 650 categorias y trajo 35.311
# productos distintos, un 4 % menos que los 36.935 del dia anterior. Con la regla
# de "solo si iguala o supera", esas diez horas se tiraron enteras para conservar
# un catalogo VIEJO. Y esa es la trampa: lo que hace valioso al catalogo de hoy no
# es su tamano, son sus precios. Perder un 4 % de referencias a cambio de precios
# frescos sale a cuenta; perder la mitad no, porque eso ya no es un catalogo
# incompleto sino una captura rota.
MERMA_ACEPTABLE = 0.10

# Donde empezar el recorrido. Sin esto, el WAF corta SIEMPRE por el mismo sitio:
# como la cola se recorre en el mismo orden todos los dias, las categorias del
# final nunca llegan a visitarse. Medido el 8 sep: se corto con 65 categorias en
# cola, y anteayer con otras tantas -- probablemente las mismas. Guardando por
# donde se quedo y empezando ahi al dia siguiente, ninguna rama queda condenada:
# lo que hoy no se llega a mirar es lo primero que se mira manana.
MARCADOR = config.DATA / "alcampo_por_donde_iba.txt"

# Con que alcance se capturo el ultimo bronze bueno. Sin esto, el dia que se
# excluyen ramas el catalogo encoge a proposito -- de 37.019 a 25.004 al dejar
# fuera el bazar -- y la red de seguridad del tamano lo confunde con una captura
# rota y no guarda NUNCA MAS. Comparar tamanos solo tiene sentido entre capturas
# que buscaban lo mismo.
ALCANCE = config.DATA / "alcampo_alcance.txt"


def _alcance_actual() -> str:
    # El prefijo evita que "no se excluye ninguna rama" se escriba como un
    # fichero vacio, indistinguible de un fichero que no se pudo escribir.
    return "ramas:" + ",".join(sorted(config.RAMAS_EXCLUIDAS_ALCAMPO))


def _mismo_alcance() -> bool:
    """True si el ultimo bronze se capturo buscando lo mismo que hoy."""
    try:
        return ALCANCE.read_text(encoding="utf-8").strip() == _alcance_actual()
    except OSError:
        # No hay constancia: se asume que si, que es como se ha venido
        # comportando hasta ahora. La primera pasada tras este cambio deja el
        # fichero escrito y a partir de ahi la comparacion es fiable.
        return True


def _apuntar_alcance() -> None:
    try:
        ALCANCE.parent.mkdir(parents=True, exist_ok=True)
        ALCANCE.write_text(_alcance_actual(), encoding="utf-8")
    except OSError:
        pass


def _desde_donde(total: int) -> int:
    """Indice por el que empezar hoy. 0 si no hay marcador o ya no vale."""
    try:
        n = int(MARCADOR.read_text().strip())
    except (OSError, ValueError):
        return 0
    return n % total if total else 0


def _apuntar_donde_voy(indice: int) -> None:
    try:
        MARCADOR.parent.mkdir(parents=True, exist_ok=True)
        MARCADOR.write_text(str(indice))
    except OSError:
        pass          # perder el marcador solo cuesta empezar de nuevo por el principio


def _cache_limpia(clave: str) -> bytes | None:
    """Crudo cacheado, ignorando lo que en realidad sea un reto del WAF.

    El reto se guardaba como si fuera catalogo, y a partir de ahi la categoria
    quedaba envenenada: la ejecucion siguiente la leia del disco, veia el reto y
    se paraba sin llegar a pedir nada por la red. Renovar la cookie no arreglaba
    nada porque nunca se volvia a pedir. De ahi la pasada del 7 sep que "corto"
    tras 6.623 productos en ocho segundos sin una sola peticion.
    """
    body = load_raw_bytes(FUENTE, clave)
    if body is None or waf.es_reto(body.decode("utf-8", "replace")):
        return None
    return body


def _guardar(clave: str, body: bytes) -> None:
    """Guardar un reto es envenenar la cache de manana. No se guarda."""
    if not waf.es_reto(body.decode("utf-8", "replace")):
        save_raw(FUENTE, clave, body)


def _plano(s: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFD", s.lower())
                   if unicodedata.category(ch) != "Mn")


def categorias(f: Fetcher) -> list[dict]:
    """Categorias de segundo nivel; las mas anchas se subdividen al recorrerlas."""
    url = f"{BASE}/api/webproductpagews/v1/categories?decoration=false&categoryDepth=2"
    clave = "api-categories"
    body = _cache_limpia(clave)
    if body is None:
        try:
            r = f.get(url)
        except HTTPStatusError as exc:
            if waf.es_reto(exc.body.decode("utf-8", "replace")):
                raise RetoWAF(clave) from None
            raise
        body = r.body
        _guardar(clave, body)
    html = body.decode("utf-8", "replace")
    if waf.es_reto(html):
        raise RetoWAF("api-categories")
    raices = json.loads(body)
    salida, descartadas = [], 0
    for raiz in raices:
        rama = _plano(raiz.get("name") or "")
        if rama in RAMAS_REPETIDAS or rama in config.RAMAS_EXCLUIDAS_ALCAMPO:
            descartadas += 1
            continue
        hijas = raiz.get("childCategories") or [raiz]
        salida.extend({**c, "rama": raiz.get("name")} for c in hijas)
    if descartadas:
        print(f"  {descartadas} ramas descartadas por configuracion")
    return salida


def _productos_api(data: dict) -> list[dict]:
    salida = []
    vistos = set()
    for grupo in data.get("productGroups") or []:
        for producto in grupo.get("decoratedProducts") or []:
            producto_id = producto.get("productId") or producto.get("retailerProductId")
            if producto_id and producto_id not in vistos:
                vistos.add(producto_id)
                salida.append(producto)
    return salida


def productos_de_categoria(f: Fetcher, cat: dict) -> tuple[list[dict], list[dict]]:
    """Productos y subcategorias directas de una categoria."""
    cat_id = cat.get("retailerCategoryId") or cat.get("retailerId")
    query = urlencode({
        "retailerCategoryId": cat_id,
        "tag": "web",
        "maxProductsToDecorate": TOPE_API,
        "maxPageSize": TOPE_API,
    })
    clave = f"api-category-{cat_id}"
    body = _cache_limpia(clave)
    if body is None:
        try:
            r = f.get(f"{BASE}/api/webproductpagews/v6/product-pages?{query}")
        except HTTPStatusError as exc:
            if waf.es_reto(exc.body.decode("utf-8", "replace")):
                raise RetoWAF(str(cat_id)) from None
            raise
        body = r.body
        _guardar(clave, body)
    texto = body.decode("utf-8", "replace")
    if waf.es_reto(texto):
        raise RetoWAF(str(cat_id))
    data = json.loads(body)
    hijas = (data.get("additionalPageInfo") or {}).get("categories") or []
    return _productos_api(data), hijas


def terminos_de_busqueda(f: Fetcher) -> list[str]:
    """Los 5.000 y pico terminos que sugiere su propio buscador.

    Sirven como segundo camino de descubrimiento: el listado de una categoria se
    corta en 50 productos (comprobado: la propia web tampoco enseña mas, ni con
    scroll ni con boton), asi que sin esto el catalogo queda a medias.
    """
    url = (f"{BASE}/api/search/v1/suggestions/primary"
           f"?searchTerm=&limit=20000&regionId={REGION}")
    try:
        r = f.get(url)
    except HTTPStatusError as exc:
        if waf.es_reto(exc.body.decode("utf-8", "replace")):
            raise RetoWAF("terminos") from None
        raise
    texto = r.body.decode("utf-8", "replace")
    if waf.es_reto(texto):
        raise RetoWAF("terminos")
    _guardar("terminos", r.body)
    datos = json.loads(r.body)
    if not isinstance(datos, list):
        raise TypeError("la respuesta de sugerencias no es una lista")
    terminos = [t for t in datos if isinstance(t, str) and t.strip()]
    if not terminos:
        raise ValueError("el buscador no devolvio terminos")
    return terminos


def productos_de_busqueda(f: Fetcher, termino: str) -> list[dict]:
    """Los productos que devuelve el buscador para un termino.

    **Con la forma comprobada a mano, porque una respuesta degradada no es una lista
    vacia.** El 26 de septiembre de 2026 esto era una cadena de `.get()` encadenados y el
    primer termino raro de los 600 tumbo el barrido entero con
    "'str' object has no attribute 'get'": la pagina habia llegado con `data` en texto, que
    es lo que devuelve el WAF cuando no da el reto de frente pero tampoco da la pagina.
    """
    ruta = f"/search?q={quote(termino)}"
    st = _estado(f, ruta)
    if not isinstance(st, dict):
        raise RetoWAF(ruta)          # una pagina sin estado no es una busqueda sin resultados
    datos = st.get("data")
    productos = datos.get("products") if isinstance(datos, dict) else None
    entidades = productos.get("productEntities") if isinstance(productos, dict) else None
    if not isinstance(entidades, dict):
        return []
    return [p for p in entidades.values() if isinstance(p, dict)]


# Cuando hay que recorrer los terminos del buscador, y cuando no.
#
# Esto era `if truncadas and not detener`, o sea: solo si alguna categoria HOJA habia
# tocado el tope de 300 productos. **Esa condicion no se ha cumplido nunca**, y se
# midio en tres dias seguidos sobre el crudo de Alcampo:
#
#     2026-09-23   respuestas 421   al tope  29   hojas al tope  0
#     2026-09-24   respuestas 543   al tope  44   hojas al tope  0
#     2026-09-25   respuestas 410   al tope  28   hojas al tope  0
#
# Y no se cumple porque una categoria con 300 productos **casi siempre tiene hijas** y
# entonces no cuenta como hoja: el tope lo tocan los nodos de arriba, que se subdividen.
# O sea que el segundo camino de descubrimiento llevaba dias existiendo en el codigo y
# sin ejecutarse ni una vez, y no se notaba porque el arbol de categorias bastaba.
#
# Hasta que no basto: el 25 de septiembre de 2026 la captura se quedo en **23.924
# productos contra 28.977** del dia anterior (un 17,5 % menos, con el aviso de deriva
# saltando) y el barrido, que es justo lo que tapa ese agujero, no llegó a correr.
#
# **Y ese 17,5 % hay que leerlo al revés, medido el 26 de septiembre de 2026.** Los dias
# de Alcampo, con sus respuestas de categoria y sus productos:
#
#     2026-09-17   407 respuestas   23.793      2026-09-23   422   23.842
#     2026-09-19   411 respuestas   23.794      2026-09-24   544   28.977  <- el raro
#     2026-09-20   422 respuestas   23.905      2026-09-25   411   23.924
#     2026-09-21   418 respuestas   23.776      2026-09-26   432   23.932
#
# O sea que **el normal es 23.900 y el raro es el 24** (91 minutos de recorrido contra ~70,
# 544 respuestas contra ~415). Los 5.161 productos que el 24 vio y el 26 no estan repartidos
# por todas las ramas (Perfumeria 1.186, Frescos 1.071, Alimentacion 539, Bebidas 495...),
# decenas por categoria: eso no es una rama que falte, es un recorrido que se queda antes de
# llegar a las hojas. El barrido del buscador **no es** lo que tapa ese agujero: devuelve 50
# productos por termino y, medido en los 8 primeros terminos del turno del 26, recupera 1
# producto nuevo (~75 extrapolando a los 600). La medicion entera y el siguiente
# experimento estan en `docs/BACKLOG.md`, N30.
#
# Ahora se recorre **cuando hace falta**, que son dos casos medibles:
#   - alguna hoja toco el tope (lo de antes, que sigue valiendo cuando pasa);
#   - o la captura se ha quedado por debajo de la ultima buena, que es la senal de que
#     el arbol no ha bastado hoy.
#
# Y con **presupuesto de tiempo**: a una peticion cada 6,7 s (ritmo del WAF), los 600
# terminos del turno son casi 67 minutos, mas que el recorrido entero. Se recorre lo que
# quepa y se dice cuanto quedo, que es mejor que doblar la tarea por si acaso.
MARGEN_BAJON = 0.05            # por debajo del 5 % ya se barre
PRESUPUESTO_BARRIDO_S = 1200   # 20 minutos


def hay_que_barrer(truncadas: int, filas: int, anterior: int | None, *,
                   margen: float = MARGEN_BAJON) -> bool:
    """¿Toca recorrer los terminos del buscador?

    `anterior` es el tamaño de la **última captura buena** —el mayor del último mes, no la
    de ayer: ver `_filas_ultimo_bronze`—; `None` o 0 si es la primera.
    """
    if truncadas:
        return True
    if not anterior:
        return False               # primera captura: no hay con que comparar
    return filas < anterior * (1 - margen)


def _turno_de_hoy(terminos: list[str], cuantos: int) -> list[str]:
    """Reparte los terminos por dias: hoy unos, manana los siguientes."""
    if len(terminos) <= cuantos:
        return terminos
    vueltas = (len(terminos) + cuantos - 1) // cuantos
    turno = config.hoy_local().toordinal() % vueltas
    return terminos[turno * cuantos:(turno + 1) * cuantos]


def _gramos(cantidad: dict | None) -> int | None:
    """{"value": "500", "uom": "G"} -> 500. Solo peso; el volumen no se mezcla."""
    if not isinstance(cantidad, dict):
        return None
    try:
        valor = float(str(cantidad.get("value")).replace(",", "."))
    except (TypeError, ValueError):
        return None
    uom = str(cantidad.get("uom") or "").upper()
    factor = {"G": 1, "GR": 1, "KG": 1000, "ML": 1, "L": 1000, "CL": 10}.get(uom)
    return round(valor * factor) if factor else None


def _rango_al_peso(p: dict) -> tuple[int | None, int | None]:
    """(peso tipico en gramos, variacion en %) de un producto al peso.

    Alcampo publica `catchweight` con minimo, tipico y maximo en 742 productos
    (3,1 %). Son justo los productos donde el precio total es una estimacion: un
    tomate "al peso" de 500 g puede venir entre 375 y 625. El precio por kilo si
    es bueno, y decir de cuanto es la horquilla es mas honesto que callarla.
    """
    cw = p.get("catchweight")
    if not isinstance(cw, dict):
        return None, None
    tipico = _gramos(cw.get("typicalQuantity"))
    minimo = _gramos(cw.get("minQuantity"))
    maximo = _gramos(cw.get("maxQuantity"))
    if not tipico:
        return None, None
    if minimo and maximo and maximo > minimo:
        return tipico, round(100 * (maximo - minimo) / (2 * tipico))
    return tipico, None


def _unidades_de_la_mecanica(promos: list[dict]) -> int | None:
    """Cuantas unidades hay que comprar para que la oferta valga, segun la cadena.

    `promotions[].requiredProductQuantity` viene en el 7,8 % del catalogo (1.900 productos de
    hoy) y vale 2, 3 o 4. Se guarda el mayor de la ficha, que es la condicion mas exigente; y
    `None` cuando ninguna oferta pide mas de una unidad, que es distinto de "pide una".
    """
    exigidas = []
    for pr in promos:
        if not isinstance(pr, dict):
            continue
        n = pr.get("requiredProductQuantity")
        if isinstance(n, (int, float)) and n > 1:
            exigidas.append(int(n))
    return max(exigidas) if exigidas else None


def _fin_de_promo(promos: list[dict]) -> datetime | None:
    """La fecha de fin que Alcampo escribe dentro del texto de la oferta.

    Se descartan las que ya pasaron. Alcampo deja textos viejos colgados -- hay
    ofertas que dicen acabar el 25 de febrero de 2026 -- y ensenar "hasta el 25
    de febrero" en septiembre es peor que no decir nada: hace dudar del resto.
    """
    hoy = datetime.now(timezone.utc).date()
    for pr in promos:
        _, hasta = fechas(pr.get("description"))
        if hasta and hasta >= hoy:
            # Fin del dia: una oferta que acaba el 23 vale todo el 23.
            return datetime(hasta.year, hasta.month, hasta.day, 23, 59,
                            tzinfo=timezone.utc)
    return None


def _iconos_de(p: dict, campo: str) -> list[dict]:
    """Los iconos de un producto, vengan como vengan.

    **Alcampo manda dos formas distintas del mismo campo, según por dónde se pida.**
    Medido el 26 de septiembre de 2026 comparando una respuesta de categoría con una del
    buscador:

        categoría   "icons": [ {"label": ...}, ... ]          <- lista de diccionarios
        buscador    "icons": {"certification": [...], "legal": [...]}   <- diccionario

    `a_registro` hacía `for ic in (p.get("icons") or [])` y `ic.get("label")`, así que con
    la forma del buscador recorría **las claves** ("certification", "legal") y reventaba con
    `'str' object has no attribute 'get'`. Eso es lo que mataba el barrido del buscador
    incluso después de arreglar cuándo se dispara: sacaba productos y no podía convertirlos
    a registro.
    """
    valor = p.get(campo)
    if isinstance(valor, dict):
        # las dos formas de dentro: listas de iconos, o un icono suelto
        fuera = []
        for dentro in valor.values():
            if isinstance(dentro, list):
                fuera.extend(dentro)
            elif isinstance(dentro, dict):
                fuera.append(dentro)
        valor = fuera
    if not isinstance(valor, list):
        return []
    return [ic for ic in valor if isinstance(ic, dict)]


def a_registro(p: dict) -> dict:
    precio = p.get("price") or {}
    # dos formas conviven: la del HTML (price.current) y la de su API (price.amount)
    actual = precio.get("current") or precio
    unidad = precio.get("unit") or {}
    unidad_actual = unidad.get("current") or (p.get("unitPrice") or {}).get("price") or {}
    unidad_ref, factor = _unidad_referencia(p, unidad.get("label") or "")
    promos = p.get("promotions") or []
    # Alcampo es la cadena con menos datos: no publica codigo de barras, asi que
    # nunca podra cruzar con Open Food Facts. Pero SI publica las etiquetas que
    # la gente busca de verdad, y nadie las miraba: 3.337 sin gluten, 2.405
    # veganos, 1.105 sin lactosa, 1.052 ecologicos. Mas que todo lo que da OFF.
    etiquetas = [ic.get("label") for ic in _iconos_de(p, "iconAttributes")
                 if ic.get("label")]
    # Los pictogramas de peligro del Reglamento CLP: "Corrosivo para la piel",
    # "Peligro para el medio ambiente". Vienen en `icons`, que es otra lista
    # distinta de `iconAttributes` y que nadie leia: 531 productos de limpieza.
    # El tipo dice CERTIFICATION, pero no certifican nada: avisan.
    peligros = sorted({ic.get("label") for ic in _iconos_de(p, "icons")
                       if ic.get("label")})
    # El rango real de un producto al peso: 742 productos. Un tomate "al peso"
    # de 500 g que puede venir entre 375 y 625 g.
    tipico, variacion = _rango_al_peso(p)

    def cent(v, factor=1.0):
        return None if v in (None, "") else round(float(v) * 100 * factor)

    r = vacio()
    r.update({
        "fuente": FUENTE,
        "id_fuente": str(p.get("retailerProductId") or p.get("productId") or ""),
        "nombre": p.get("name"),
        "marca": p.get("brand"),
        "formato_txt": p.get("packSizeDescription"),
        "precio_cent": cent(actual.get("amount")),
        "precio_ref_nativo_cent": cent(unidad_actual.get("amount"), factor),
        "unidad_ref_nativa": unidad_ref,
        "promo": bool(promos),
        "promo_txt": promos[0].get("description") if promos else None,
        # **Cuantas unidades hay que comprar para que la oferta valga, en numero.** El texto
        # lo dice en palabras ("2ª UD AL 50% DTO.") y esto lo dice la propia web: 1.900
        # productos de hoy (7,8 %) traen `requiredProductQuantity` >= 2.
        #
        # Se guarda y **no se usa todavia**, y el motivo es el mismo por el que el precio de
        # tarjeta no cuenta: una oferta que exige comprar dos unidades no es el precio de una.
        # Decidir que hacer con eso (enseñar "2ª unidad al 50 %" en la ficha, o calcular el
        # precio efectivo de la pareja) es una decision de producto con su medicion, no un
        # campo que se lee y ya. Medido el 26 de septiembre de 2026 y escrito en
        # `docs/DATOS-QUE-NO-COGEMOS.md`.
        "promo_unidades_minimas": _unidades_de_la_mecanica(promos),
        # Alcampo tenia 3.125 textos de oferta y CERO fechas de fin, porque la
        # fecha va dentro del texto: "Producto en Folleto (10/09/26_23/09/26)".
        # El 61 % de sus ofertas la lleva.
        "promo_hasta": _fin_de_promo(promos),
        # Su etiqueta "Peso variable" es mas fiable que suponerlo, y ademas
        # publica `catchweight` con el rango.
        "peso_variable": any("peso variable" in (e or "").lower() for e in etiquetas)
                         or bool(p.get("catchweight")),
        "sellos": de_etiquetas(etiquetas),
        "conservacion": conservacion_de(etiquetas),
        # Separadas por barra y no por coma: una de las etiquetas de Alcampo es
        # "Corrosivo para la piel, ojos y/o metales", y con comas se partia en
        # dos advertencias que no significan nada.
        "advertencias": " | ".join(peligros) or None,
        "peso_neto_g": tipico,
        "peso_variacion_pct": variacion,
        # `alcohol` y `ageRestriction` van siempre juntos en los 1.589 que lo
        # llevan. Es el filtro que pide cualquiera que no beba, y no se puede
        # deducir del nombre: "cerveza 0,0" lleva la palabra cerveza.
        "es_alcohol": bool(p.get("alcohol")) or bool(p.get("ageRestriction")) or None,
        # Que la cadena lo diga es mas fiable que deducirlo del texto de la marca.
        "es_marca_propia": any("producto alcampo" in (e or "").lower()
                               for e in etiquetas) or None,
        "categoria": " > ".join(p.get("categoryPath") or []) or None,
        "disponible": bool(p.get("available", True)),
        # La URL publica lleva el `retailerProductId` (el mismo que `id_fuente`),
        # no el `productId`, que es un UUID interno.
        #
        # Con el UUID, los 23.776 enlaces de Alcampo daban **404**. Nadie se
        # entero en quince dias porque el precio estaba bien y el enlace no lo
        # mira ningun control: solo se nota al pulsarlo, y eso lo hace una
        # persona, no el scraper. Se vio el 21 de septiembre de 2026 abriendo
        # dos productos al azar en el navegador.
        #
        #     .../products/72bccb32-c2f9-4735-90c7-501a89eaed7a  -> 404
        #     .../products/181786                                -> el producto
        "url": (f"{BASE}/products/{p.get('retailerProductId') or p.get('productId')}"
                if (p.get("retailerProductId") or p.get("productId")) else None),
        "imagen": (p.get("image") or {}).get("src"),
        "capturado_en": datetime.now(timezone.utc),
    })
    return r


def _sin_repetidos(filas: list[dict]) -> tuple[list[dict], int]:
    """Quita los productos repetidos y dice cuántos eran.

    **La API de Alcampo devuelve el subárbol entero en cada categoría**, así que un producto
    sale en la rama y otra vez en la hoja: el 26 de septiembre de 2026, 28.783 filas crudas
    para **23.932 productos**, un 20 % de repetidos.

    Eso no era solo un desperdicio: la condición del barrido comparaba esas 28.783 filas
    contra la referencia de un bronze ya deduplicado (28.977), así que
    `28.783 < 28.977 × 0,95` salía **falso** y el barrido **no se ejecutaba** ni con la
    captura dos días corta. Contar peras contra manzanas, y el que salía perdiendo era el
    mecanismo que tapa el agujero.

    Se queda la última aparición, que es lo que hacía `unique(keep="last")` al guardar.
    """
    vistos: dict[str, dict] = {}
    for r in filas:
        if r.get("id_fuente"):
            vistos[str(r["id_fuente"])] = r
    return list(vistos.values()), len(filas) - len(vistos)


# Cuantos dias hacia atras se busca la captura buena con la que comparar.
#
# **Eran siete, y la semana era el ratchet.** Ver `_filas_ultimo_bronze`: con una semana de
# capturas cortas, el mayor de esos siete dias pasa a ser la referencia y el barrido que tapa el
# agujero se apaga solo. Medido el 5 de octubre de 2026: Alcampo bajo de 37.019 filas de bronze a
# 24.120 en dos dias, y despues a **cero durante cuatro**, y el barrido no se disparo ni una vez.
# Treinta dias es la capacidad real de la cadena, no su ultima semana mala, y equivocarse cuesta
# un barrido, que tiene presupuesto propio.
DIAS_DE_REFERENCIA = 30


def _filas_ultimo_bronze(dias: int = DIAS_DE_REFERENCIA) -> int:
    """El catálogo **más grande de los últimos días**: la última captura BUENA.

    No el más reciente, y eso es un arreglo del 26 de septiembre de 2026 con su medición
    detrás. Ese día la captura de Alcampo llevaba dos días corta (23.932 contra 28.977) y
    el barrido del buscador —que es justo lo que tapa el agujero— **volvió a no
    ejecutarse**, aunque la condición ya estaba arreglada. El motivo: al comparar contra
    el bronze de más cerca, el bajón se comparaba **consigo mismo** (la pasada de las
    09:17 de esa misma mañana, ya degradada), así que `filas < anterior * 0,95` era falso
    por construcción. Un catálogo degradado se convertía en la referencia contra la que
    medirse, y a partir de ahí todo parecía normal.

    Aquel arreglo miró **una semana** hacia atrás, y la semana resultó ser el mismo ratchet
    con más paciencia: del 26 de septiembre al 1 de octubre todas las capturas estuvieron
    entre 23.635 y 24.120, así que el mayor de los siete días era una captura corta y el
    barrido tampoco se disparaba. Del 2 al 5 de octubre no hubo captura ninguna. Ahora se
    mira **un mes** (`DIAS_DE_REFERENCIA`), que es lo que la cadena sabe traer de verdad.

    Lo bueno se mide hacia atrás y con ventana larga. Si el catálogo encoje de verdad --una
    cadena que deja de vender algo--, esto lo notará, y el barrido correrá sin encontrar
    nada nuevo hasta que alguien lo mire: cuesta lo que dura el barrido, que tiene
    presupuesto propio y se corta solo. Lo que no puede costar es quedarse una semana con
    media tienda sin que nada lo diga.
    """
    carpeta = config.DATA / "bronze" / f"fuente={FUENTE}"
    partes = sorted(carpeta.glob("fecha=*/part.parquet"))[-dias:]
    tamano = 0
    for parte in partes:
        try:
            tamano = max(tamano, pl.read_parquet(parte, columns=["id_fuente"]).height)
        except Exception:  # noqa: BLE001
            continue
    return tamano


def _fetcher() -> Fetcher:
    """Fetcher con la sesion del WAF ya puesta; la renueva si hace falta.

    El User-Agent tiene que ser el mismo con el que se obtuvo el testigo: AWS WAF
    lo comprueba, y mandarlo con otro agente invalida la cookie.
    """
    s = waf.para(DOMINIO, URL_PRUEBA)
    cabeceras = {"User-Agent": s["user_agent"]} if s.get("user_agent") else None
    # Deja el recuento del dia escrito al terminar el proceso:
    peticiones.registra_al_salir(FUENTE)
    return Fetcher(rate_per_sec=config.RITMO[FUENTE],
                   cookies=s.get("cookies"), headers=cabeceras)


def _fuera_de_alcance(cat: dict) -> bool:
    """¿Esta rama es bazar? Entonces ni se pide.

    El 5 de octubre de 2026 este colector **rechazo una captura de 23.859 productos con 0
    errores** porque venia corta la rama "Hogar y Decoracion" (133 -> 31). Con la politica de
    `core/datos/alcance.yml` esa rama no tiene ni un producto de cesta: 133 excluidos, 0
    incluidos, medido con `revisar_alcance --ramas`.

    **Solo lo excluido se salta, nunca lo que hay que revisar**: media despensa de Alcampo sale en
    `revisar` y saltarsela seria perder comida. Y **si el clasificador falla, se pide igual**: una
    peticion de mas es barata; perder la captura cuesta el dia entero.
    """
    try:
        ruta = " > ".join(p for p in (cat.get("rama"), cat.get("name")) if p)
        return alcance.clasificar_alcance(None, ruta).estado == alcance.EXCLUIDO
    except Exception:  # noqa: BLE001
        return False


def main() -> int:
    t0, errores, filas, truncadas = time.monotonic(), 0, [], 0
    try:
        f = _fetcher()
    except RuntimeError as exc:
        log_run(FUENTE, 0, 1, time.monotonic() - t0)
        print(f"  {exc}")
        return 1

    try:
        cats = categorias(f)
    except RetoWAF:
        print("  el WAF sigue bloqueando tras renovar la cookie: se deja para manana")
        log_run(FUENTE, 0, 1, time.monotonic() - t0)
        return 1
    except Exception as exc:  # noqa: BLE001
        log_run(FUENTE, 0, 1, time.monotonic() - t0)
        print(f"  no se pudo leer el arbol de categorias: {exc}")
        return 1
    arranque = _desde_donde(len(cats))
    if arranque:
        cats = cats[arranque:] + cats[:arranque]
        print(f"  {len(cats)} categorias iniciales, empezando por la {arranque} "
              f"(donde se corto la ultima vez)")
    else:
        print(f"  {len(cats)} categorias iniciales")

    sin_estado, renovaciones, reintentos, detener = [], 0, 0, False
    ramas_saltadas = 0        # ramas de bazar que no se han pedido (T01)
    pendientes = deque(cats)
    categorias_vistas: set[str] = set()
    while pendientes:
        cat = pendientes.popleft()
        cat_id = str(cat.get("retailerCategoryId") or cat.get("retailerId") or "")
        if not cat_id or cat_id in categorias_vistas:
            continue
        categorias_vistas.add(cat_id)
        # **El bazar no se pide.** Ver `_fuera_de_alcance`: evita que una rama de decoracion
        # pueda tumbar el dia, y de paso se le ahorran peticiones al WAF.
        if _fuera_de_alcance(cat):
            ramas_saltadas += 1
            peticiones.evita(FUENTE)   # rama de bazar: no se pide
            continue
        while True:
            try:
                productos, hijas = productos_de_categoria(f, cat)
                # Cuando bajar a las hijas y cuando quedarse con lo que hay.
                #
                # La API de Alcampo devuelve los productos de TODO el subarbol de
                # una categoria, con un tope de 300. Asi que:
                #
                #   300 productos y con hijas  -> viene cortado: hay que bajar
                #   entre 1 y 299 productos    -> cabe entero: nos lo quedamos
                #   0 productos y con hijas    -> es un nodo de navegacion puro,
                #                                 los productos estan abajo
                #
                # Ese tercer caso caia en el `else` y no encolaba nada: ni
                # productos (no habia) ni hijas. El subarbol entero se perdia sin
                # un solo error. Medido sobre el crudo del 17 de septiembre de
                # 2026: 289 nodos asi, con 1.245 hijas nunca pedidas. De ellas,
                # 1.192 llegaban igual por otro camino y **53 no llegaban nunca**
                # ("Lacteos sin lactosa", "Verduras y Frutas CALIDAD EXTRA",
                # "Ron Premium"...).
                #
                # Y el 18, ese mismo agujero se trago la rama Frescos entera:
                # 2.646 productos el dia antes, 91 ese dia, con cero errores.
                if hijas and (len(productos) >= TOPE_API or not productos):
                    pendientes.extend({**hija, "rama": cat.get("rama")} for hija in hijas)
                else:
                    filas.extend(a_registro(p) for p in productos)
                if len(productos) >= TOPE_API and not hijas:
                    truncadas += 1
                reintentos = 0        # esta categoria ha salido: la racha se rompe
                break
            except RetoWAF:
                anterior = _filas_ultimo_bronze()
                if (renovaciones >= CORTES_PARA_RENDIRSE and anterior
                        and len(filas) < anterior * AVANCE_MINIMO):
                    errores += 1
                    print(f"  {renovaciones} cortes y solo {len(filas)} productos "
                          f"de los {anterior} de la ultima pasada buena: hoy el WAF "
                          f"nos tiene fichados. Se deja para manana; lo descargado "
                          f"queda en cache y no se volvera a pedir.")
                    detener = True
                    break
                if renovaciones >= MAX_RENOVACIONES:
                    errores += 1
                    print(f"  el WAF nos ha cortado tras {len(filas)} productos "
                          f"y {renovaciones} renovaciones. Se guarda lo conseguido "
                          f"y se para.")
                    detener = True
                    break
                espera = min(ESPERA_TRAS_CORTE * (renovaciones + 1), ESPERA_MAXIMA)
                # **Antes de abrir nada, se reintenta con la misma sesion.** El reto
                # de AWS WAF es muchas veces del momento -- ritmo, una racha de
                # peticiones --, y con la pausa de arriba la misma cookie suele valer.
                # Medido el 25 de septiembre de 2026: el dia anterior se abrio el
                # navegador 13 veces y esta pausa sola resuelve la mayoria. Abrir una
                # ventana que le roba el foco al ordenador de casa es lo ultimo que hay
                # que probar, no lo primero.
                if reintentos < REINTENTOS_SIN_NAVEGADOR:
                    reintentos += 1
                    print(f"  el WAF ha saltado en '{cat.get('name')}': {espera}s de "
                          f"espera y se reintenta con la misma sesion, sin navegador "
                          f"({reintentos}/{REINTENTOS_SIN_NAVEGADOR})", flush=True)
                    time.sleep(espera)
                    continue
                print(f"  el WAF ha saltado en '{cat.get('name')}' "
                      f"({renovaciones + 1}/{MAX_RENOVACIONES}): {espera}s de espera "
                      f"y cookie nueva...", flush=True)
                time.sleep(espera)
                try:
                    sesion = waf.renueva(DOMINIO, URL_PRUEBA)
                    print(f"      sesion renovada ({sesion.get('via')})", flush=True)
                    f = _fetcher()
                    renovaciones += 1
                    reintentos = 0
                    continue  # reintenta ESTA categoria; antes se perdia
                except RuntimeError as exc:
                    errores += 1
                    print(f"  {exc}")
                    detener = True
                    break
            except ValueError:
                sin_estado.append(cat.get("name"))
                errores += 1
                break
            except Exception as exc:  # noqa: BLE001
                errores += 1
                print(f"  error en {cat.get('name')}: {type(exc).__name__}: {exc}")
                break
        if detener:
            # Apuntar por donde se corto, en indices del recorrido ORIGINAL, para
            # que manana empiece justo aqui y las de la cola dejen de ser siempre
            # las mismas.
            _apuntar_donde_voy((arranque + len(categorias_vistas)) % max(len(cats), 1))
            break
        # Decir algo cada tanto. Es la tercera vez que un silencio de horas hace
        # pensar que el sistema esta colgado; aqui ademas el recorrido crece solo
        # (cada categoria ancha empuja a sus hijas), asi que sin esto no hay forma
        # de saber si quedan diez categorias o mil.
        # De 50 en 50 mientras queda mucho, y de 10 en 10 en la recta final: es
        # justo al final cuando el silencio parece que el proceso se ha colgado,
        # porque quedan pocas categorias y ya no se llega al siguiente multiplo.
        paso = 50 if len(pendientes) > 60 else 10
        if ramas_saltadas and len(categorias_vistas) % paso == 0:
            print(f"  (y {ramas_saltadas} ramas fuera de alcance: no se han "
                  f"pedido)", flush=True)
        if len(categorias_vistas) % paso == 0:
            print(f"  progreso: {len(categorias_vistas)} categorias vistas, "
                  f"{len(pendientes)} en cola, {len(filas)} productos", flush=True)

    if not detener:
        _apuntar_donde_voy(0)     # pasada entera: manana se empieza por el principio

    if sin_estado:
        print(f"  {len(sin_estado)} categorias llegaron sin datos "
              f"(ej.: {', '.join(sin_estado[:3])})")

    # **Las cuentas, con los repetidos fuera, y antes de decidir nada.** La API devuelve el
    # subarbol entero en cada categoria, asi que un producto sale en la rama y en la hoja:
    # 28.783 filas crudas para 23.932 productos el 26 de septiembre de 2026. Comparar esas
    # 28.783 contra la referencia de un bronze deduplicado (28.977) hacia que la condicion
    # del barrido saliera falsa con la captura dos dias corta, o sea que el mecanismo que
    # tapa el agujero se quedaba apagado justo cuando hacia falta. Medido, no supuesto.
    if filas:
        filas, repetidos = _sin_repetidos(filas)
        if repetidos > len(filas) // 10:
            print(f"  {repetidos} filas repetidas de {len(filas) + repetidos} "
                  f"(la API devuelve el subarbol en cada categoria): "
                  f"quedan {len(filas)} productos", flush=True)

    if not detener and hay_que_barrer(truncadas, len(filas), _filas_ultimo_bronze()):
        if truncadas:
            print(f"  {truncadas} categorias hoja tocaron el limite de {TOPE_API}: "
                  f"se completan por buscador", flush=True)
        else:
            print(f"  la captura ({len(filas)}) va por debajo de la ultima buena: se "
                  f"recorren los terminos del buscador", flush=True)
        vistos = {r["id_fuente"] for r in filas}
        nuevos = 0
        terminos = []
        sin_datos = 0
        t0_buscador = time.monotonic()
        agotado = False
        try:
            terminos = _turno_de_hoy(terminos_de_busqueda(f), TERMINOS_POR_DIA)
            for termino in terminos:
                if time.monotonic() - t0_buscador > PRESUPUESTO_BARRIDO_S:
                    agotado = True
                    break
                # Un termino que no devuelve datos **no puede tumbar el barrido**, y menos
                # aun la captura del dia. Medido el 26 de septiembre de 2026: el primer
                # termino de los 600 trajo una respuesta con forma rara
                # ("'str' object has no attribute 'get'"), el barrido entero se aborto en
                # cero minutos y el `errores += 1` de aqui abajo hizo que la pasada
                # terminara diciendo "es una captura rota" y no guardara nada. Una racha
                # de seiscientas peticiones tiene terminos raros; el barrido va de
                # completar lo que falta, no de ser perfecto.
                try:
                    encontrados = productos_de_busqueda(f, termino)
                except RetoWAF:
                    raise                     # el WAF sí corta el barrido entero
                except Exception as exc:  # noqa: BLE001
                    sin_datos += 1
                    if sin_datos <= 3:
                        print(f"    termino '{termino}' sin datos: "
                              f"{type(exc).__name__}: {exc}", flush=True)
                    continue
                for prod in encontrados:
                    r = a_registro(prod)
                    if r["id_fuente"] and r["id_fuente"] not in vistos:
                        vistos.add(r["id_fuente"])
                        filas.append(r)
                        nuevos += 1
        except RetoWAF:
            # El WAF corta el barrido, no la captura: el arbol ya esta recorrido y lo que
            # hay en `filas` es catalogo de hoy. Marcarlo como error dejaba la pasada sin
            # guardar por un corte en la fase extra.
            print("  el WAF corta la fase de buscador: se guarda lo que trajo el arbol")
        except Exception as exc:  # noqa: BLE001
            print(f"  no se pudo completar la fase de buscador: {exc}")
        minutos = (time.monotonic() - t0_buscador) / 60
        print(f"  buscador: {len(terminos)} terminos, {nuevos} productos nuevos, "
              f"{sin_datos} terminos sin datos ({minutos:.0f} min)", flush=True)
        if agotado:
            print(f"  aviso: se acabo el presupuesto del buscador "
                  f"({PRESUPUESTO_BARRIDO_S}s) con {len(filas)} productos: manana "
                  f"sigue por donde iba")
    elif truncadas:
        print(f"  aviso: {truncadas} categorias hoja alcanzaron el limite de {TOPE_API}")
    # La truncacion es una limitacion conocida y acotada, no una ejecucion rota:
    # descartar 7.500 productos buenos porque una categoria toco el tope seria
    # peor que guardarlos. Solo cortan el guardado un corte del WAF o los errores.
    completa = not detener and errores == 0

    # Que no haya habido errores no significa que este el catalogo entero. El 18
    # de septiembre de 2026 esta misma linea dio por buena una captura sin la
    # rama **Frescos** completa -- 2.646 productos el dia antes, 91 ese dia --, se
    # escribio el bronze y salio a la app. Cero errores: nadie fallo, es que esas
    # categorias no se llegaron a pedir. Un total puede bajar un 13 % por mil
    # razones normales; una rama que se queda en el 3 % de lo que tenia mientras
    # las demas siguen igual, no.
    caidas = []
    if filas:
        caidas = cobertura.revisa(
            pl.DataFrame(filas, schema_overrides=ESQUEMA_BRONZE), FUENTE)

    # Una captura cortada no es automaticamente peor que la anterior. El 7 sep el
    # WAF corto tras 21.199 productos y se descartaron todos para conservar un
    # bronze de 10.074: se tiraron 971 segundos de red y once mil productos buenos
    # por respetar una regla pensada para el caso contrario. Lo que decide es el
    # tamano, no la etiqueta: si la parcial iguala o supera a la ultima buena,
    # entra; si es mas pequena, se conserva la anterior.
    df = None
    if filas:
        df = pl.DataFrame(filas, schema_overrides=ESQUEMA_BRONZE)
        df = df.unique(subset=["fuente", "id_fuente"], keep="last")
    guardar = completa
    # Las ramas que faltan mandan sobre todo lo demas, incluido el tamano total.
    # Es la unica regla de aqui que dice "no" sin mirar cuantos productos hay, y
    # es a proposito: cuando falta una rama entera **sabemos** que se ha perdido,
    # no lo estimamos. Si Frescos hubiera tenido mil productos en vez de 2.646, el
    # total se habria quedado por encima del 90 % y la regla de la merma habria
    # dado el visto bueno a un catalogo sin pescaderia.
    if df is not None and caidas:
        print("  faltan ramas enteras respecto a la ultima captura buena:")
        for linea in caidas:
            print(f"      {linea}")
        print("  eso no es un catalogo mas pequeno, es un catalogo con agujeros. "
              "Se conserva el anterior y manana se vuelve a intentar.")
        guardar = False
    elif df is not None and not completa and not _mismo_alcance():
        guardar = True
        print(f"  ejecucion parcial con {df.height} productos, pero las ramas que "
              f"se recogen han cambiado: no tiene sentido compararla con la "
              f"anterior. Se guarda")
    elif df is not None and not completa:
        anterior = _filas_ultimo_bronze()
        minimo = anterior * (1 - MERMA_ACEPTABLE)
        if df.height >= minimo:
            guardar = True
            merma = 100 * (1 - df.height / anterior) if anterior else 0.0
            if df.height >= anterior:
                print(f"  ejecucion parcial, pero {df.height} productos igualan o "
                      f"superan los {anterior} del ultimo bronze: se guarda")
            else:
                print(f"  ejecucion parcial con {df.height} productos, un "
                      f"{merma:.0f}% menos que los {anterior} de la ultima pasada: "
                      f"se guarda igual, porque los precios son de hoy")
        else:
            print(f"  ejecucion parcial con {df.height} productos, muy por debajo "
                  f"de los {anterior} del ultimo bronze: eso no es un catalogo "
                  f"incompleto, es una captura rota. Se conserva el anterior")
    if df is not None and guardar:
        # **Otra vez la clasificacion, ahora sobre el producto** (T01). Una rama puede
        # estar bien y colar bazar dentro: esta es la ultima puerta antes del catalogo.
        # Se quita lo EXCLUIDO y se deja lo que hay que REVISAR (media despensa de
        # Alcampo sale en revisar, y quitarla seria perder comida). Es la misma funcion
        # que usa el control de cobertura, para que colector y control no discrepen.
        # Ver `docs/CESTA-DATOS-Y-COMPARACION.md` 1.
        en_alcance = cobertura.solo_cesta_familiar(df)
        if en_alcance.height != df.height:
            print(f"  {df.height - en_alcance.height} productos fuera de alcance: no se "
                  f"guardan", flush=True)
            df = en_alcance
        write_parquet(df, "bronze", FUENTE)
        _apuntar_alcance()
        filas = df.to_dicts()

    segundos = time.monotonic() - t0
    aviso = check_drift(FUENTE, len(filas))
    log_run(FUENTE, len(filas), errores, segundos, completa)
    if aviso:
        print(f"  {aviso}")
    print(f"{FUENTE}: {len(filas)} productos, {errores} errores, {segundos:.0f}s")
    # Guardar catalogo es el trabajo del dia. Si se ha guardado, el dia ha ido
    # bien aunque el WAF cortara por el camino: devolver 1 aqui hacia que la tarea
    # programada marcara fallo todos los dias con los datos ya en disco.
    return 0 if filas and guardar else 1


if __name__ == "__main__":
    raise SystemExit(main())


def productos_crudo(body: bytes) -> list[dict]:
    """Para reprocesar tanto el SSR historico como las respuestas nuevas de la API."""
    try:
        data = json.loads(body)
        if isinstance(data, dict) and "productGroups" in data:
            return _productos_api(data)
    except (json.JSONDecodeError, UnicodeDecodeError):
        pass
    try:
        st = js_object(body.decode("utf-8", "replace"), "__INITIAL_STATE__")
    except Exception:  # noqa: BLE001
        return []
    ents = (st.get("data", {}).get("products") or {}).get("productEntities") or {}
    return list(ents.values())
