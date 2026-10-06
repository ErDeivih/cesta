"""Mercadona: API JSON publica. Colector completo, de la red a bronze.

    GET  /api/categories/            arbol (26 categorias raiz)
    GET  /api/categories/<id>/       subcategorias CON sus productos
    GET  /api/products/<id>/         ficha: ean, ingredientes, nutricion
    PUT  /api/postal-codes/actions/change-pc/   fija el almacen

Los precios varian por almacen, asi que se fija el CP antes de recorrer nada.
Ver docs/RECON.md.
"""
from __future__ import annotations

import gzip
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import polars as pl
from selectolax.parser import HTMLParser

from core import cobertura, config, envases, peticiones, sellos
from core.fetch import Fetcher
from core.runlog import check_drift, log_run
from core.schemas import ESQUEMA_BRONZE, vacio
from core.storage import save_raw, write_parquet

BASE = "https://tienda.mercadona.es/api"
FUENTE = "mercadona"
PASO_MAESTRO = 250   # cada cuantas fichas se guarda y se informa
MASTER = config.DATA / "master" / "mercadona.json.gz"


def sesion() -> Fetcher:
    """Fetcher con el almacen ya fijado por codigo postal."""
    # Deja el recuento del dia escrito al terminar el proceso:
    peticiones.registra_al_salir(FUENTE)
    f = Fetcher(rate_per_sec=config.RITMO[FUENTE])
    f.put(
        f"{BASE}/postal-codes/actions/change-pc/",
        json={"new_postal_code": config.CODIGO_POSTAL},
        timeout=20,
    )
    return f


def categorias(f: Fetcher) -> list[dict]:
    """Devuelve las categorias de NIVEL 2, que son las que traen productos.

    Verificado: /api/categories/12/ (una raiz) responde sin 'categories' y sin
    productos; /api/categories/112/ (su hija) trae 4 bloques y 35 productos.
    Recorrer las raices devuelve cero, que es justo el fallo del 6 sep.
    """
    r = f.get(f"{BASE}/categories/")
    save_raw(FUENTE, "categories", r.body)
    raices = json.loads(r.body).get("results", [])
    return [hija for raiz in raices for hija in raiz.get("categories", [])]


def productos_de_categoria(f: Fetcher, cat_id: int) -> list[dict]:
    r = f.get(f"{BASE}/categories/{cat_id}/")
    save_raw(FUENTE, f"category-{cat_id}", r.body)
    data = json.loads(r.body)
    salida = []
    for sub in data.get("categories", []):
        salida.extend(sub.get("products", []))
    return salida


def ficha(f: Fetcher, producto_id: str) -> dict:
    """Datos maestros: ean, marca, origen, proveedores, nutricion. Una sola vez."""
    r = f.get(f"{BASE}/products/{producto_id}/")
    save_raw(FUENTE, f"product-{producto_id}", r.body)
    return json.loads(r.body)


def _texto_html(valor) -> str | None:
    if not valor:
        return None
    texto = HTMLParser(str(valor)).text(separator=" ").strip()
    return " ".join(texto.split()) or None


def _maestro_de_ficha(p: dict) -> dict:
    detalles = p.get("details") or {}
    nutricion = p.get("nutrition_information") or {}
    return {
        "ean": str(p["ean"]) if p.get("ean") else None,
        "marca": p.get("brand") or detalles.get("brand"),
        "origen": p.get("origin") or detalles.get("origin"),
        "proveedores_txt": " | ".join(
            x["name"] for x in detalles.get("suppliers") or [] if x.get("name")
        ) or None,
        "nombre_legal": detalles.get("legal_name"),
        "ingredientes": _texto_html(nutricion.get("ingredients")),
        "alergenos": _texto_html(nutricion.get("allergens")),
        # Lo que llevaba once dias en la ficha guardada sin que nadie lo mirara.
        # Mercadona no tiene campo de conservacion ni de envase, pero los dice:
        #   packaging             86 % ("Paquete", "Brik", "Pack-6")
        #   storage_instructions  64 % ("Conservar a -18 ºC")
        #   details.description  100 %
        "envase_txt": p.get("packaging"),
        "conservacion": sellos.conservacion_de_prosa(detalles.get("storage_instructions")),
        "descripcion": (detalles.get("description") or "").strip() or None,
        # Para el filtro "sin alcohol" y para no recomendarle una cerveza a
        # quien busca una bebida de malta.
        "grado_alcohol": _numero_grado(detalles.get("alcohol_by_volume")),
    }


# Mercadona escribe el grado con el simbolo de grado pegado: "13.0º", "4,8º".
_GRADO = re.compile(r"(\d+(?:[.,]\d+)?)")


def _numero_grado(valor):
    """El grado alcoholico como numero. "13.0º" -> 13.0."""
    if valor in (None, ""):
        return None
    m = _GRADO.search(str(valor).replace(",", "."))
    if not m:
        return None
    grado = float(m.group(1))
    # Por encima de 100 no es un grado, es otra cosa mal etiquetada.
    return grado if 0 <= grado <= 100 else None


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


def _entero(valor) -> int | None:
    try:
        n = int(float(str(valor)))
    except (TypeError, ValueError):
        return None
    return n if n > 1 else None      # "1 unidad" no es un pack, es lo normal


def _gramos(valor) -> int | None:
    """Los kilos que publica Mercadona, en gramos. 0,65 -> 650."""
    if valor in (None, ""):
        return None
    try:
        kilos = float(str(valor).replace(",", "."))
    except (TypeError, ValueError):
        return None
    return round(kilos * 1000) if kilos > 0 else None


def a_registro(p: dict, maestro: dict | None = None) -> dict:
    """parse puro: dict de la API -> fila de bronze. Sin red, testeable."""
    pi = p.get("price_instructions") or {}

    def cent(v):
        return None if v in (None, "") else round(float(str(v).strip()) * 100)

    tam = pi.get("unit_size")
    formato = f"{tam} {pi.get('size_format') or ''}".strip() if tam is not None else ""

    r = vacio()
    r.update({
        "fuente": FUENTE,
        "id_fuente": str(p.get("id")),
        "nombre": p.get("display_name"),
        "marca": p.get("brand") or (maestro or {}).get("marca"),
        "ean": (maestro or {}).get("ean"),
        "origen": (maestro or {}).get("origen"),
        "proveedores_txt": (maestro or {}).get("proveedores_txt"),
        "nombre_legal": (maestro or {}).get("nombre_legal"),
        "ingredientes": (maestro or {}).get("ingredientes"),
        "alergenos": (maestro or {}).get("alergenos"),
        "envase": envases.lee((maestro or {}).get("envase_txt"))[0],
        "conservacion": (maestro or {}).get("conservacion"),
        "descripcion": (maestro or {}).get("descripcion"),
        "grado_alcohol": (maestro or {}).get("grado_alcohol"),
        "formato_txt": formato,           # vacio si unit_size es None (peso variable)
        "cantidad_declarada": float(tam) if tam is not None else None,
        "unidad_declarada": (pi.get("size_format") or "").lower() or None,
        "precio_cent": cent(pi.get("unit_price")) or 0,
        # Mercadona publica DOS precios de referencia, y no son el mismo numero: en
        # el bronze del 26 de septiembre de 2026 (4.324 productos) coinciden en
        # 3.522 y **difieren en 802**.
        #
        # El motivo, comprobado con la aritmetica: **`bulk_price` va en la unidad del
        # TAMANO y `reference_price` en la de `reference_format`**, que no siempre son
        # la misma.
        #
        #   Detergente 0,81 l, 3,65 EUR   reference_format "lv"  bulk 451 (EUR/l)
        #                                                          reference 14 (EUR/lavado)
        #   Huevos 24 ud, 5,25 EUR        reference_format "dz"  bulk  22 (EUR/ud)
        #                                                          reference 262 (EUR/docena)
        #   Manzanilla 26 g, 0,85 EUR     reference_format "100 g" bulk 3269 (EUR/kg)
        #                                                          reference 327 (EUR/100 g)
        #
        # En los tres, dividir el precio entre la cantidad del nombre da el `bulk_price`
        # y no el `reference_price`: el que lleva la unidad de `reference_format` es el
        # otro. El comentario que habia aqui decia justo lo contrario.
        #
        # Se guardan los dos, cada uno con lo suyo, y **el par consistente no decide
        # todavia**: de los 33 productos del dia con `reference_format` de dosis ("lv",
        # "dc", "dz") la unidad canonica de la referencia queda a None, o sea que ese
        # numero no entra hoy en ninguna comparacion (0 de 33 lo usan). Se captura
        # porque es lo que publica la cadena, y porque el dia que esa referencia se use
        # el numero tendra que ir con su unidad.
        "precio_ref_nativo_cent": cent(pi.get("bulk_price")),
        "unidad_ref_nativa": (pi.get("reference_format") or "").lower() or None,
        "precio_referencia_nativo_cent": cent(pi.get("reference_price")),
        "precio_anterior_nativo_cent": cent(pi.get("previous_unit_price")),
        "ha_bajado_nativo": bool(pi.get("price_decreased")),
        "iva": pi.get("tax_percentage"),
        "es_pack": bool(pi.get("is_pack")),
        "unidades_envase": _entero(pi.get("total_units")),
        # El peso escurrido DE VERDAD, que Mercadona publica en el listado y
        # nadie leia. Es el que hace honesta la comparacion de una conserva: en
        # un bote de aceitunas, comparar por peso total en vez de por escurrido
        # cambia cual es mas barato. (DIA tiene un campo que se llama asi y no
        # lo es; ver core/schemas.py.)
        "peso_escurrido_g": _gramos(pi.get("drained_weight")),
        # `requires_age_check` marca los que llevan alcohol. Es el filtro que
        # pide cualquiera que no beba, y del nombre no se saca: "cerveza 0,0"
        # lleva la palabra cerveza.
        "es_alcohol": bool((p.get("badges") or {}).get("requires_age_check")) or None,
        "peso_variable": bool(p.get("is_variable_weight")),
        "categoria": (p.get("categories") or [{}])[0].get("name"),
        "disponible": not p.get("unavailable_from"),
        "url": p.get("share_url"),
        "imagen": p.get("thumbnail"),
        "capturado_en": datetime.now(timezone.utc),
    })
    return r


def main(detalles_max: int | None = None) -> int:
    t0, errores_catalogo, errores_detalle, filas = time.monotonic(), 0, 0, []
    try:
        f = sesion()
        cats = categorias(f)
    except Exception as exc:  # noqa: BLE001
        log_run(FUENTE, 0, 1, time.monotonic() - t0)
        print(f"  no se pudo iniciar el catalogo: {exc}")
        return 1
    print(f"  {len(cats)} categorias de nivel 2")
    vacias = 0
    productos_catalogo = []
    for cat in cats:
        try:
            productos = productos_de_categoria(f, cat["id"])
            if not productos:
                vacias += 1
            productos_catalogo.extend(productos)
        except Exception as exc:  # noqa: BLE001
            errores_catalogo += 1
            print(f"  error en categoria {cat.get('id')} {cat.get('name')}: {exc}")
    if vacias:
        print(f"  aviso: {vacias} categorias sin productos")

    # La ficha contiene el EAN, marca, fabricante e ingredientes. Se conserva en
    # un maestro local y cada dia solo se consultan productos todavia desconocidos.
    maestro = _cargar_maestro()
    presupuesto = config.MERCADONA_DETALLES_POR_DIA if detalles_max is None else detalles_max
    faltan = len({str(p.get("id")) for p in productos_catalogo} - set(maestro))
    objetivo = min(max(0, presupuesto), faltan)
    if objetivo:
        print(f"  maestro: {faltan} productos sin ficha, se piden {objetivo} "
              f"(~{objetivo / config.RITMO[FUENTE] / 60:.0f} min)", flush=True)
    nuevos = 0
    for p in productos_catalogo:
        producto_id = str(p.get("id"))
        if producto_id not in maestro and nuevos < max(0, presupuesto):
            try:
                maestro[producto_id] = _maestro_de_ficha(ficha(f, producto_id))
                nuevos += 1
                if nuevos % PASO_MAESTRO == 0:
                    # Guardar por el camino: descargar 4.000 fichas son 40 minutos,
                    # y perderlas por un Ctrl+C seria absurdo. Y decir algo, que si
                    # no parece colgado.
                    _guardar_maestro(maestro)
                    print(f"  maestro: {nuevos}/{objetivo} fichas nuevas "
                          f"({len(maestro)} en total)", flush=True)
            except Exception as exc:  # noqa: BLE001
                errores_detalle += 1
                print(f"  error en ficha {producto_id}: {exc}")
        filas.append(a_registro(p, maestro.get(producto_id)))
    if nuevos:
        _guardar_maestro(maestro)
    pendientes = len({str(p.get("id")) for p in productos_catalogo} - set(maestro))
    print(f"  maestro: {len(maestro)} fichas, {nuevos} nuevas, {pendientes} pendientes"
          f" ({errores_detalle} errores)")

    completa = bool(filas) and errores_catalogo == 0
    # Una rama entera que desaparece no se ve en el total. Ver core/cobertura.py.
    if filas and completa:
        caidas = cobertura.revisa(
            pl.DataFrame(filas, schema_overrides=ESQUEMA_BRONZE), FUENTE)
        if caidas:
            completa = False
            print("  faltan ramas enteras respecto a la ultima captura buena:")
            for linea in caidas:
                print(f"      {linea}")
    if completa:
        # tipos explicitos: una columna que sale entera a None se queda como Null
        # y rompe la union de esquemas mas adelante. Mejor fijarlo aqui.
        df = pl.DataFrame(filas, schema_overrides=ESQUEMA_BRONZE)
        df = df.unique(subset=["fuente", "id_fuente"], keep="last")   # idempotencia
        write_parquet(df, "bronze", FUENTE)
        filas = df.to_dicts()
    elif filas:
        print("  ejecucion parcial: se conserva el ultimo bronze completo")

    segundos = time.monotonic() - t0
    aviso = check_drift(FUENTE, len(filas))
    log_run(FUENTE, len(filas), errores_catalogo, segundos, completa)
    if aviso:
        print(f"  {aviso}")
    print(f"{FUENTE}: {len(filas)} productos, {errores_catalogo} errores de catalogo, "
          f"{segundos:.0f}s")
    return 0 if completa else 1


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--detalles", type=int, default=None,
                    help="maximo de fichas maestras nuevas (EAN, marca, ingredientes)")
    raise SystemExit(main(ap.parse_args().detalles))
