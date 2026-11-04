"""DIA: catalogo paginado + maestro incremental de fichas.

Listado: /<l1>/<l2>/c/<CODIGO>?page=N   (page_size 20)
Datos:   INITIAL_STATE.l2.plp_items
Ficha:   /api/v1/product/<sku_id>?lang=es  -> ean_code (clave para el matching)
Categorias: sitemap.xml -> URLs con /c/L####
Proteccion: Akamai. Ritmo lento y curl_cffi.
"""
from __future__ import annotations

import gzip
import json
import math
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

import polars as pl
from selectolax.parser import HTMLParser

from core import alcance, cobertura, config, envases, peticiones, sellos
from core.fetch import Fetcher, HTTPStatusError
from core.runlog import check_drift, log_run
from core.schemas import ESQUEMA_BRONZE, vacio
from core.sellos import de_etiquetas
from core.state import json_script
from core.storage import load_raw_bytes, save_raw, write_parquet

BASE = "https://www.dia.es"
FUENTE = "dia"
PASO_MAESTRO = 250   # cada cuantas fichas se guarda y se informa
MASTER = config.DATA / "master" / "dia.json.gz"


def _fuera_de_alcance(url: str) -> bool:
    """¿Esta categoria es bazar? Se sabe por la URL, antes de pedir el listado.

    DIA publica sus categorias en el sitemap como `/compra-online/<pasillo>/.../c/L123`, asi que el
    pasillo se lee de la propia direccion: es el sitio donde el ahorro de peticiones es real, porque
    se decide **antes** de pedir.

    **Solo se salta lo excluido, nunca lo que hay que revisar**, y si el clasificador falla se pide
    igual: una peticion de mas es barata.
    """
    try:
        texto = urlsplit(url).path.replace("/", " ").replace("-", " ")
        return alcance.clasificar_alcance(None, texto).estado == alcance.EXCLUIDO
    except Exception:  # noqa: BLE001
        return False


def categorias(f: Fetcher) -> list[str]:
    body = load_raw_bytes(FUENTE, "sitemap")
    if body is None:
        r = f.get(f"{BASE}/sitemap.xml")
        body = r.body
        save_raw(FUENTE, "sitemap", body)
    urls = re.findall(r"<loc>([^<]+)</loc>", body.decode("utf-8", "replace"))
    return [u for u in urls if "/c/L" in u]


def listado(f: Fetcher, cat_url: str, page: int = 1) -> dict:
    clave = f"{cat_url}-{page}"
    body = load_raw_bytes(FUENTE, clave)
    if body is None:
        r = f.get(f"{cat_url}?page={page}")
        body = r.body
        save_raw(FUENTE, clave, body)
    st = json_script(body.decode("utf-8", "replace"), "vike_pageContext")["INITIAL_STATE"]
    pag = st.get("pagination", {}).get("pagination", {})
    return {"items": st.get("l2", {}).get("plp_items", []),
            "total_pages": int(pag.get("total_pages") or 1)}


def ficha(f: Fetcher, sku_id: str) -> dict:
    """Datos maestros: EAN, ingredientes, alergenos, peso neto. Sin precio."""
    r = f.get(f"{BASE}/api/v1/product/{sku_id}?lang=es")
    save_raw(FUENTE, f"product-{sku_id}", r.body)
    return json.loads(r.body)


def _valor(campo):
    """Las fichas envuelven muchos valores como {name, value}."""
    return campo.get("value") if isinstance(campo, dict) else campo


def _texto_html(valor) -> str | None:
    valor = _valor(valor)
    if not valor:
        return None
    texto = HTMLParser(str(valor)).text(separator=" ").strip()
    return " ".join(texto.split()) or None


# La tabla nutricional viene campo a campo, cada uno como {"value": 3.1,
# "uom": "g"}. DIA la publica en el 66 % de sus fichas y durante doce dias no la
# miramos: son ~3.570 productos con dato de ETIQUETA, que es mejor que el de
# Open Food Facts porque no depende de que el codigo de barras cruce.
_NUTRIENTES = {
    "energy": "energia_kj",
    "energy_kcal": "energia_kcal",
    "fat": "grasas",
    "saturated_fat": "saturadas",
    "carbohydrate": "hidratos",
    "sugars": "azucares",
    "dietary_fiber": "fibra",
    "protein": "proteinas",
    "salt": "sal",
}


def _numero(valor):
    """El numero de un campo {"value": ..., "uom": ...}, o None."""
    if isinstance(valor, dict):
        valor = valor.get("value")
    if valor in (None, "", "No Aplica"):
        return None
    try:
        return float(str(valor).replace(",", "."))
    except (TypeError, ValueError):
        return None


# El valor con el que DIA rellena "no caduca".
CADUCIDAD_CENTINELA = 999

# Unidades declaradas -> gramos o mililitros, para comprobar que el peso neto
# que publica DIA es creible antes de creerselo.
_A_BASE = {"kg": 1000, "l": 1000, "g": 1, "gr": 1, "ml": 1, "cl": 10}


def _caducidad(p: dict) -> int | None:
    dias = _numero(p.get("days_to_expiration"))
    if not dias or dias >= CADUCIDAD_CENTINELA:
        return None
    return int(dias)


def _peso_neto(p: dict) -> int | None:
    """Los gramos que pesa el contenido, si el numero es creible.

    DIA publica aqui cosas como 8.000 para un refresco de 2 litros y 6.000 para
    un brik de leche de uno: son pesos de caja, no de unidad. Se exige que el
    valor este entre la mitad y el doble de la cantidad declarada, que es el
    rango en el que cabe cualquier densidad real de un alimento (el aceite pesa
    0,916 kg/l, la miel 1,42) y no cabe un palet.
    """
    gramos = _numero(p.get("drained_weight"))
    if not gramos:
        return None
    cantidad = _numero(p.get("quantity_per_unit"))
    unidad = str(_valor(p.get("measurement_unit_description"))
                 or p.get("measure_unit") or "").lower()
    factor = _A_BASE.get(unidad)
    if not cantidad or not factor:
        return None
    base = cantidad * factor
    if not (base * 0.5 <= gramos <= base * 2):
        return None
    return int(gramos)


def _nutricion(p: dict) -> tuple[str | None, str | None]:
    """La tabla nutricional en JSON, y por cuanto esta expresada.

    Se conserva una tabla parcial sin inventar los nutrientes ausentes. Quien
    la consulte debe distinguir desconocido de cero y comprobar la base.
    """
    tabla = {}
    for campo, nuestro in _NUTRIENTES.items():
        n = _numero(p.get(campo))
        if n is not None and math.isfinite(n) and n >= 0:
            tabla[nuestro] = n
    if not tabla:
        return None, None
    medida = _numero(p.get("nutri_size"))
    unidad = _valor(p.get("nutri_measurement_unit")) or ""
    por = None
    if medida and unidad:
        por = f"{medida:g}{str(unidad).lower().strip()}"
    # Ocho fichas dicen que su tabla esta por "1447g", "2.7g" o "97ml". No se
    # sabe comparar eso con un "por 100 g", y una tabla que no se puede comparar
    # ensenada como si se pudiera es peor que no tenerla.
    if por not in ("100g", "100ml", "porcion"):
        por = None
    return json.dumps(tabla, separators=(",", ":")), por


def _maestro_de_ficha(p: dict) -> dict:
    nutricion, nutricion_por = _nutricion(p)
    cantidad = p.get("quantity_per_unit")
    unidad = (_valor(p.get("measurement_unit_description"))
              or p.get("measure_unit"))
    formato = None
    if cantidad not in (None, "") and unidad:
        numero = float(cantidad)
        formato = f"{numero:g} {str(unidad).lower()}"
    return {
        "ean": str(p["ean_code"]) if p.get("ean_code") else None,
        "marca": _valor(p.get("brand_description")),
        "proveedores_txt": _valor(p.get("manufacturer_contact_name")),
        "nombre_legal": _valor(p.get("product")),
        "ingredientes": _texto_html(p.get("ingredients")),
        "alergenos": _texto_html(p.get("allergen_statement")),
        "formato_txt": formato,
        "cantidad_declarada": float(cantidad) if cantidad not in (None, "") else None,
        "unidad_declarada": str(unidad).lower() if unidad else None,
        "iva": str(p.get("iva_tax_value")) if p.get("iva_tax_value") is not None else None,
        "nutricion": nutricion,
        "nutricion_por": nutricion_por,
        # Ninguna otra cadena publica cuanto dura un producto. Alimenta la
        # despensa deducida: se compro hace 12 dias, dura 15, se acaba el viernes.
        # 999 es el centinela de "no caduca" y aparece en 1.272 fichas: si se
        # deja pasar, la despensa avisaria de que se acaba el arroz dentro de
        # dos anos y ocho meses.
        "dias_caducidad": _caducidad(p),
        # `drained_weight` NO es el peso escurrido, por mucho que se llame asi:
        # es el peso de lo que hay dentro. Ver core/schemas.py.
        "peso_escurrido_g": None,
        "peso_neto_g": _peso_neto(p),
        # Tal cual lo dice DIA. La ficha maestra guarda las palabras de la
        # cadena; normalizar es trabajo de `a_registro`, que es la frontera del
        # contrato. Asi, cambiar el vocabulario no obliga a volver a leer 5.410
        # fichas.
        "envase_txt": _valor(p.get("package_format_description")),
        # Un tipo fino ("Leche infantil", no "Lacteos"): etiqueta limpia y gratis
        # para bloquear emparejamientos entre productos que no son lo mismo.
        "tipo_producto": _valor(p.get("product_type")),
        # --- de la auditoria de FICHAS del 19 de septiembre de 2026 ---
        #
        # Hasta ese dia se habia auditado el crudo de los **listados** y nunca el
        # de las **fichas**, que es donde esta lo bueno. La de DIA tiene unas 200
        # claves. Medido sobre 460 fichas reales:
        #
        #   storage_instructions          44 %   y `conservacion` estaba al 0 %
        #   manufacturer_name             41 %   y `origen` estaba al 0 %
        #   manufacturer_contact_country  29 %
        #   secondary_eans                22 %   codigos de barras de mas
        #
        # Las dos primeras tapan huecos que llevaban semanas en el backlog (N2 y
        # el origen), y la tercera da munición al emparejador, que es donde
        # estamos por delante de la competencia.
        "conservacion_txt": _texto_html(p.get("storage_instructions")),
        "origen": _origen_de_ficha(p),
        # Codigos de barras secundarios: 187 en 460 fichas. Se guardan porque el
        # dato es gratis, pero **NO se usan todavia para emparejar**, y la razon
        # importa: entre ellos esta el codigo del **pack**. Emparejar por ahi
        # haria que un pack de seis y una unidad suelta fueran "el mismo
        # producto", que es justo el error que este proyecto se dedica a evitar.
        #
        # Para usarlos hay que saber antes cual es de unidad y cual de pack, y
        # eso la ficha no lo dice. Queda apuntado en el backlog con su numero.
        "eans_extra": [str(e) for e in (p.get("secondary_eans") or []) if e],
    }


def _origen_de_ficha(p: dict) -> str | None:
    """De donde viene, con lo que DIA publica y sin inventar nada.

    Se prefiere el pais cuando lo dice ("Union Europea", "Espana") y, si no, el
    fabricante, que al menos dice quien lo hace. No se mezcla con la direccion
    postal: un domicilio social no es un origen, y ponerlo ahi seria vender por
    procedencia lo que solo es una oficina.
    """
    pais = _valor(p.get("manufacturer_contact_country"))
    if pais and str(pais).strip():
        return str(pais).strip()
    fabricante = _valor(p.get("manufacturer_name"))
    if fabricante and str(fabricante).strip():
        return str(fabricante).strip()
    return None


def _cargar_maestro() -> dict[str, dict]:
    if not MASTER.exists():
        return {}
    try:
        return json.loads(gzip.decompress(MASTER.read_bytes()))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return {}


def _guardar_maestro(datos: dict[str, dict]) -> None:
    MASTER.parent.mkdir(parents=True, exist_ok=True)
    temporal = Path(str(MASTER) + ".tmp")
    cuerpo = json.dumps(datos, ensure_ascii=False, sort_keys=True).encode()
    temporal.write_bytes(gzip.compress(cuerpo))
    temporal.replace(MASTER)


# Los distintivos que DIA pone en su listado. "Mejor valorado" es la unica
# senal de popularidad de todo el proyecto: ninguna cadena publica ventas ni
# resenas que sirvan (Alcampo publica valoraciones, pero son 1.060 productos con
# 1.260 votos en total y mediana de UN voto: eso no es una valoracion, es ruido).
DISTINTIVOS = {
    "Mejor valorado": "mejor-valorado",
    "Novedad": "novedad",
    "Precio destacado": "precio-destacado",
    "Air Fryer": "air-fryer",
}


def _distintivo(p: dict) -> str | None:
    return DISTINTIVOS.get((p.get("stamp_description") or "").strip())


def _sellos_de_listado(p: dict) -> str | None:
    """Los sellos que DIA pone en el listado, en dos campos con nombre enganoso.

    `allergens` no son alergenos: son 1.177 productos etiquetados "Sin gluten",
    "Sin lactosa" o "BIO". Y `product_info` trae otros 336 con lo mismo. DIA
    tenia 3 % de sellos -- y esos venian de leerle el nombre al producto --
    teniendo esto guardado desde el primer dia.
    """
    etiquetas = [a.get("name") for a in (p.get("allergens") or [])
                 if isinstance(a, dict) and a.get("name")]
    # product_info llega como "Sin lactosa | BIO"
    etiquetas += [t.strip() for t in str(p.get("product_info") or "").split("|")]
    return de_etiquetas([e for e in etiquetas if e])


def _promocion(p: dict) -> tuple[str | None, bool]:
    """(texto de la oferta, si es solo con la tarjeta Club DIA).

    DIA publica el texto en `promotions[].description` -- "2ª UD AL 70% DTO." --
    y hasta hoy se tiraba, asi que DIA era la unica cadena con ofertas y sin
    texto de oferta: 221 productos.

    Lo importante es el segundo valor. **200 de esas 221 son solo con tarjeta**,
    y en este proyecto ya estaba decidido que un descuento de tarjeta no baja lo
    que pagas en caja: se acumula en un monedero. Sin distinguirlo, anadir el
    texto de DIA habria hecho que la app anunciara 200 rebajas que no estan en
    el ticket.
    """
    for pr in (p.get("promotions") or []):
        if pr.get("description"):
            return pr["description"], bool(pr.get("only_club_dia"))
    return None, False


def _peso_real(p: dict) -> int | None:
    """Los gramos que pesa de verdad, para lo que se vende al peso.

    DIA lo publica en 108 productos: "Cebolla dulce granel 1.1 Kg aprox." trae
    `weight_in_grams: 1100`. Son justo los productos donde nuestro precio por
    kilo sale de una cantidad inventada.
    """
    for campo in ("weight_in_grams", "average_weight"):
        n = _numero(p.get(campo))
        if n and n > 0:
            return int(n)
    return None


def a_registro(p: dict, maestro: dict | None = None,
               categoria: str | None = None) -> dict:
    # Al reprocesar desde el crudo la categoria no llega por argumento: es de la
    # pagina, no del producto. `productos_crudo` la engancha en "_ctx".
    categoria = categoria or (p.get("_ctx") or {}).get("categoria")
    pr = p.get("prices") or {}
    def cent(v):
        return None if v is None else round(float(v) * 100)

    maestro = maestro or {}
    promo_txt, promo_club = _promocion(p)
    r = vacio()
    r.update({
        "fuente": FUENTE,
        "id_fuente": str(p.get("sku_id")),
        "nombre": p.get("display_name"),
        "marca": p.get("brand") or maestro.get("marca"),
        "ean": maestro.get("ean"),
        "proveedores_txt": maestro.get("proveedores_txt"),
        "nombre_legal": maestro.get("nombre_legal"),
        "ingredientes": maestro.get("ingredientes"),
        "alergenos": maestro.get("alergenos"),
        "formato_txt": maestro.get("formato_txt"),
        "cantidad_declarada": maestro.get("cantidad_declarada"),
        "unidad_declarada": maestro.get("unidad_declarada"),
        "precio_cent": cent(pr.get("price")),
        "precio_ref_nativo_cent": cent(pr.get("price_per_unit")),
        "unidad_ref_nativa": (pr.get("measure_unit") or "").lower() or None,
        "promo": bool(pr.get("is_promo_price")) or bool(promo_txt),
        "promo_txt": promo_txt,
        "promo_club": promo_club or None,
        "precio_anterior_nativo_cent": cent(pr.get("strikethrough_price")),
        "iva": maestro.get("iva"),
        # Lo que la ficha maestra sabe y el listado no. Se enseno a leerlo el 16
        # de septiembre y se quedo ahi: `_maestro_de_ficha` los devolvia y esta
        # funcion no los copiaba, asi que durante un dia los seis campos
        # existieron en data/master y en ninguna otra parte.
        # Los sellos del listado se suman a lo que diga la ficha maestra.
        "sellos": _sellos_de_listado(p),
        "distintivo": _distintivo(p),
        "nutricion": maestro.get("nutricion"),
        "nutricion_por": maestro.get("nutricion_por"),
        "dias_caducidad": maestro.get("dias_caducidad"),
        "peso_neto_g": _peso_real(p) or maestro.get("peso_neto_g"),
        "peso_escurrido_g": maestro.get("peso_escurrido_g"),
        "envase": envases.lee(maestro.get("envase_txt") or maestro.get("envase"))[0],
        "tipo_producto": maestro.get("tipo_producto"),
        # DIA escribe `storage_instructions` en el 44 % de sus fichas, con las
        # mismas palabras que Mercadona -- "Mantengase en lugar fresco y seco",
        # "Conservar a -18 ºC" -- y `sellos.conservacion_de_prosa` lleva semanas
        # sabiendo leerlas. El dato estaba, el motor estaba, y nadie los habia
        # juntado: `conservacion` de DIA marcaba **0 %** en gold.
        "conservacion": sellos.conservacion_de_prosa(maestro.get("conservacion_txt")),
        # Lo mismo con el origen, que tambien estaba al 0 %.
        "origen": maestro.get("origen"),
        "peso_variable": bool(p.get("weight")),
        "categoria": categoria,
        "disponible": (p.get("units_in_stock") or 0) > 0,
        "url": BASE + (p.get("url") or ""),
        "imagen": BASE + p["image"] if p.get("image") else None,
        "capturado_en": datetime.now(timezone.utc),
    })
    return r


def main(detalles_max: int | None = None) -> int:
    """Recorre todo el precio catalogado; las fichas caras se completan por tandas."""
    t0 = time.monotonic()
    errores = 0
    try:
        # Deja el recuento del dia escrito al terminar el proceso:
        peticiones.registra_al_salir(FUENTE)
        f = Fetcher(rate_per_sec=config.RITMO[FUENTE])
        cats = categorias(f)
    except Exception as exc:  # noqa: BLE001
        print(f"  no se pudo leer el sitemap: {exc}")
        log_run(FUENTE, 0, 1, time.monotonic() - t0)
        return 1
    print(f"  {len(cats)} categorias hoja")

    productos: dict[str, tuple[dict, str]] = {}
    paginas = 0
    categorias_obsoletas = 0
    for posicion, cat_url in enumerate(cats, start=1):
        # **El bazar no se pide** (T01). Ver `_fuera_de_alcance`.
        if _fuera_de_alcance(cat_url):
            peticiones.evita(FUENTE)   # categoria de bazar: no se pide
            continue
        try:
            primera = listado(f, cat_url)
            paginas += 1
            for p in primera["items"]:
                sku = str(p.get("sku_id") or "")
                if sku:
                    productos[sku] = (p, cat_url)
            for page in range(2, primera["total_pages"] + 1):
                bloque = listado(f, cat_url, page)
                paginas += 1
                for p in bloque["items"]:
                    sku = str(p.get("sku_id") or "")
                    if sku:
                        productos[sku] = (p, cat_url)
        except HTTPStatusError as exc:
            if exc.status == 404:
                categorias_obsoletas += 1
                continue
            errores += 1
            print(f"  error HTTP en categoria {posicion}/{len(cats)} {cat_url}: {exc}")
        except Exception as exc:  # noqa: BLE001
            errores += 1
            print(f"  error en categoria {posicion}/{len(cats)} {cat_url}: {exc}")
        if posicion % 25 == 0:
            print(f"  progreso: {posicion}/{len(cats)} categorias, "
                  f"{len(productos)} productos unicos")

    if categorias_obsoletas:
        print(f"  aviso: {categorias_obsoletas} categorias del sitemap ya no existen")

    maestro = _cargar_maestro()
    nuevos = 0
    errores_detalle = 0
    faltan = len(set(productos) - set(maestro))
    if detalles_max is not None:
        presupuesto = detalles_max
    else:
        # Lo que falte, con suelo y con techo. Un presupuesto fijo deja una deuda
        # que crece sola en cuanto la cadena mete mas productos nuevos de los que
        # caben en el cupo; ver el comentario en core/config.py.
        presupuesto = min(max(config.DIA_DETALLES_POR_DIA, faltan),
                          config.DIA_DETALLES_TOPE)
    objetivo = min(max(0, presupuesto), faltan)
    if objetivo:
        print(f"  maestro: {faltan} productos sin ficha, se piden {objetivo} "
              f"(~{objetivo / config.RITMO[FUENTE] / 60:.0f} min)", flush=True)
        if faltan > objetivo:
            print(f"  aviso: quedaran {faltan - objetivo} sin ficha para manana",
                  flush=True)
    for sku in productos:
        if sku in maestro or nuevos >= max(0, presupuesto):
            continue
        try:
            maestro[sku] = _maestro_de_ficha(ficha(f, sku))
            nuevos += 1
            if nuevos % PASO_MAESTRO == 0:
                # Guardar por el camino: si se corta a mitad no se pierde nada.
                _guardar_maestro(maestro)
                print(f"  maestro: {nuevos}/{objetivo} fichas nuevas "
                      f"({len(maestro)} en total)", flush=True)
        except Exception as exc:  # noqa: BLE001
            errores_detalle += 1
            print(f"  error en ficha {sku}: {exc}")
    if nuevos:
        _guardar_maestro(maestro)
    pendientes = len(set(productos) - set(maestro))
    print(f"  {paginas} paginas, {len(productos)} productos unicos")
    print(f"  maestro: {len(maestro)} fichas, {nuevos} nuevas, {pendientes} pendientes"
          f" ({errores_detalle} errores)")

    filas = [a_registro(p, maestro.get(sku), categoria=cat)
             for sku, (p, cat) in productos.items()]
    completa = bool(filas) and errores == 0
    # Una rama entera que desaparece no se ve en el total. Ver core/cobertura.py.
    if filas and completa:
        marco = pl.DataFrame(filas, schema_overrides=ESQUEMA_BRONZE)
        # Una sola lectura del bronze anterior: `caidas` es lo que se cuenta y `vetan`
        # lo que decide. Un folleto de campana que rota se cuenta y NO veta
        # (`cobertura.RAMAS_DE_CAMPANA`); una estanteria hundida, si. Una regla, un sitio.
        detalle = cobertura.caidas(marco, FUENTE)
        caidas = [frase for _, frase in detalle]
        vetan = [frase for rama, frase in detalle if not cobertura.es_de_campana(rama, FUENTE)]
        if caidas:
            print("  ramas hundidas respecto a la ultima captura buena:")
            for linea in caidas:
                print(f"      {linea}")
        if vetan:
            completa = False
            print("  y alguna es una estanteria, no un folleto: la captura no esta completa")
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
    print(f"{FUENTE}: {len(filas)} productos, {errores} errores de catalogo, "
          f"{segundos:.0f}s")
    return 0 if completa else 1


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--detalles", type=int, default=None,
                    help="maximo de fichas maestras nuevas (EAN e ingredientes)")
    raise SystemExit(main(ap.parse_args().detalles))


_CANONICA = re.compile(r'<link rel="canonical" href="(https://www\.dia\.es/[^"]+)"')


def productos_crudo(body: bytes) -> list[dict]:
    """Para reprocesar: saca los productos del HTML de listado guardado.

    DIA guarda HTML con extension .json.gz igual que Carrefour, asi que sus
    5.410 productos tampoco se podian reprocesar. Con esto ya se pueden las
    cinco cadenas, que es la unica forma de que un arreglo del parser llegue al
    historico sin volver a pedirle nada a una web protegida por Akamai.

    Los ficheros `product-<sku>.json.gz` de este mismo directorio si son JSON:
    son las fichas maestras y no llevan precio, asi que se descartan aqui; su
    sitio es data/master.
    """
    try:
        texto = body.decode("utf-8", "replace")
        st = json_script(texto, "vike_pageContext")["INITIAL_STATE"]
    except Exception:  # noqa: BLE001
        return []
    items = (st.get("l2") or {}).get("plp_items") or []
    m = _CANONICA.search(texto)
    ctx = {"categoria": m.group(1) if m else None}
    for item in items:
        if isinstance(item, dict):
            item["_ctx"] = ctx
    return [i for i in items if isinstance(i, dict)]
