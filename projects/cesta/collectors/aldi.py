"""Aldi: sitemap oficial de productos + API de producto por lotes.

Verificado el 6 sep 2026:
  - robots.txt publica `.aldi-nord-sitemap-products.xml`, con URLs cuyo sufijo es
    el ID. El rastreo del menu queda como plan B si ese indice cambia.
  - Los IDs estan en el HTML como "objectID":"940600" (30 por pagina de hoja).
  - Precios: GET /api/product/pds/<id1>,<id2>,...?scope=es_pen
    Regala EUR/kg ya calculado, precio tachado, % de descuento y validUntil.
"""
from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone

import polars as pl

from core import certificados, cobertura, config, peticiones, sellos
from core.fetch import Fetcher
from core.runlog import check_drift, log_run
from core.schemas import ESQUEMA_BRONZE, vacio
from core.storage import load_raw_bytes, save_raw, write_parquet

BASE = "https://www.aldi.es"
FUENTE = "aldi"
LOTE = 20
MAX_VUELTAS = 6

_CATEGORIA = re.compile(r'(?:https://www\.aldi\.es)?(/productos/[a-z0-9\-/]+\.html)', re.IGNORECASE)
_ID = re.compile(r'"objectID"\s*:\s*"(\d+)"')
_ID_SITEMAP = re.compile(r"-(\d+)\.html</loc>")


def rastrear(f: Fetcher) -> tuple[set[str], set[str]]:
    """Sigue el menu hasta agotar categorias. Devuelve (categorias, ids)."""
    try:
        body = load_raw_bytes(FUENTE, "sitemap-products")
        if body is None:
            r = f.get(f"{BASE}/sitemaps/.aldi-nord-sitemap-products.xml")
            body = r.body
            save_raw(FUENTE, "sitemap-products", body)
        ids_sitemap = set(_ID_SITEMAP.findall(body.decode("utf-8", "replace")))
        if ids_sitemap:
            return {"sitemap-productos"}, ids_sitemap
    except Exception as exc:  # noqa: BLE001
        print(f"  aviso: sitemap de productos no disponible; uso el menu: {exc}")

    vistas: set[str] = {"/productos.html"}
    pendientes = ["/productos.html"]
    ids: set[str] = set()
    vueltas = 0

    while pendientes and vueltas < MAX_VUELTAS:
        vueltas += 1
        siguiente = []
        for ruta in pendientes:
            try:
                r = f.get(BASE + ruta)
            except Exception as exc:  # noqa: BLE001
                print(f"  error en {ruta}: {exc}")
                continue
            save_raw(FUENTE, ruta, r.body)
            html = r.body.decode("utf-8", "replace")
            ids.update(_ID.findall(html))
            for nueva in _CATEGORIA.findall(html):
                if nueva not in vistas:
                    vistas.add(nueva)
                    siguiente.append(nueva)
        pendientes = siguiente
    return vistas, ids


def productos(f: Fetcher, ids: list[str]) -> tuple[list[dict], int]:
    salida = []
    errores = 0
    for i in range(0, len(ids), LOTE):
        lote = ids[i:i + LOTE]
        url = f"{BASE}/api/product/pds/{','.join(lote)}?scope={config.ALDI_SCOPE}"
        try:
            clave = f"pds-{lote[0]}"
            body = load_raw_bytes(FUENTE, clave)
            if body is None:
                r = f.get(url)
                body = r.body
                save_raw(FUENTE, clave, body)
            salida.extend(json.loads(body).get("products", []))
        except Exception as exc:  # noqa: BLE001
            errores += 1
            print(f"  error en lote {i // LOTE}: {exc}")
            continue
    return salida, errores


def _marca(p: dict) -> str | None:
    """La marca de Aldi, que si la publica aunque el nombre no la lleve.

    Durante nueve dias esta linea decia `None` con un comentario que afirmaba
    que "Aldi no separa la marca del nombre". Si la separa: `brandName` viene en
    el 91,2 % de los productos y hay 229 marcas distintas (MILSANI, LACURA,
    CHOCEUR...). Casi todas son marca propia de Aldi, que es justo lo que hace
    falta saber para compararla con Hacendado o con Carrefour.

    Se le quita el simbolo de marca registrada porque no aporta nada y estorba
    al emparejador, que compara palabra a palabra.
    """
    marca = (p.get("brandName") or "").replace("\u00ae", "").replace("\u2122", "").strip()
    return marca or None


# Aldi no manda `validUntil` vacio cuando un precio no caduca: manda el 31 de
# diciembre de 2030. Es un centinela, y durante once dias se escribio tal cual en
# `promo_hasta`, asi que la plataforma creia que 1.645 de los 2.065 productos de
# Aldi (el 79,7 %) tenian una oferta que acaba dentro de cuatro anos. Cualquier
# pantalla de "ofertas que se acaban" habria empezado por esa basura.
CENTINELA = datetime(2030, 1, 1, tzinfo=timezone.utc)

# Las marcas propias de Aldi aparecen en `categoryIDs` como si fueran una
# categoria mas. Es la unica cadena que lo regala asi: 478 productos (23,2 %),
# frente a los 63 que marca el logotipo de la casa.
MARCAS_PROPIAS = frozenset({
    "milsani", "la-tabla", "esselt", "el-horno", "golden_seafood", "tandil",
    "lacura-nature", "moser-roth", "mamia",
})

# Dentro de shortDescription Aldi escribe fichas con forma de "Clave: valor".
# `Origen` sale en 212 productos (10,3 %) y es el unico sitio donde Aldi dice de
# donde viene algo con el nombre del pais; el certificado de origen nacional
# solo puede decir "Espana".
_ORIGEN = re.compile(r"^\s*Origen(?:\s+de\s+\w+)?\s*:\s*(.+)$", re.MULTILINE | re.IGNORECASE)


def _origen(p: dict) -> str | None:
    m = _ORIGEN.search(p.get("shortDescription") or "")
    if not m:
        return None
    # "Espana, Francia, Italia." -> "Espana, Francia, Italia"
    return m.group(1).strip().rstrip(".").strip() or None


def _descripcion(p: dict) -> str | None:
    """Lo que Aldi cuenta del producto, sin el aviso legal.

    `longDescription` existe en el 79,2 % pero es "El precio puede variar para
    las tiendas ubicadas en las Islas Baleares" en el 99,3 % de los casos, asi
    que no se guarda. `shortDescription` (62,7 %) si es del producto.
    """
    texto = (p.get("shortDescription") or "").strip()
    return texto or None


def _fin_de_oferta(cp: dict, p: dict) -> datetime | None:
    """Cuando se acaba la oferta. None si no hay oferta o si no caduca.

    Se exige que HAYA oferta (precio tachado o texto de promocion) antes de
    dar una fecha: en Aldi el `validUntil` de un precio normal es la vigencia
    del precio, no el fin de una oferta, y vale el centinela de 2030.
    """
    def ts(v):
        return None if not v else datetime.fromtimestamp(v, timezone.utc)

    hay_oferta = bool(cp.get("strikePrice") or (cp.get("priceTagLabels") or {}).get("promoText1"))
    fecha = ts(cp.get("validUntil")) if hay_oferta else None
    if fecha is None:
        # La ventana tambien puede venir en `promotionPrices`, que ademas trae
        # `validFrom`: 62 de las 174 promociones de hoy aun no han empezado.
        for pr in (p.get("promotionPrices") or []):
            if pr.get("priceValue") == cp.get("priceValue") and pr.get("validUntil"):
                fecha = ts(pr["validUntil"])
                break
    return None if (fecha is None or fecha >= CENTINELA) else fecha


def a_registro(p: dict) -> dict:
    cp = p.get("currentPrice") or {}
    base = (cp.get("basePrice") or [{}])[0]
    tachado = (cp.get("strikePrice") or {}).get("strikePriceValue")
    etiquetas = cp.get("priceTagLabels") or {}

    def cent(v):
        return None if v is None else round(float(v) * 100)

    def ts(v):
        return None if not v else datetime.fromtimestamp(v, timezone.utc)

    # Los logotipos de certificacion: 1.106 productos (53,6 %) llevan al menos
    # uno, y de ahi salen sellos, origen, marca propia y las certificaciones de
    # tercero. Once dias leyendo `assets` para quedarnos solo con la foto.
    logos = [a.get("url") for a in (p.get("assets") or []) if a.get("type") == "certificate"]
    cert = certificados.lee(logos)
    propia_por_categoria = bool(MARCAS_PROPIAS & set(p.get("categoryIDs") or []))

    # Los sellos vienen por dos caminos que se suman: el certificado (auditado,
    # 342 productos) y la frase que escribe Aldi (132 mas). Se juntan y se
    # ordenan para que dos productos con los mismos sellos tengan el mismo texto.
    de_texto = sellos.de_prosa(p.get("shortDescription"))
    todos = set((cert.get("sellos") or "").split(",")) | set((de_texto or "").split(","))
    if "bio" in (p.get("categoryIDs") or []):
        todos.add("ecologico")   # la gama ecologica de la casa, la propia Aldi
    todos.discard("")

    fin_oferta = _fin_de_oferta(cp, p)

    r = vacio()
    r.update({
        "fuente": FUENTE,
        "id_fuente": str(p.get("objectID")),
        "nombre": p.get("name"),
        "marca": _marca(p),
        "formato_txt": p.get("salesUnit"),
        "precio_cent": cent(cp.get("priceValue")),
        "precio_ref_nativo_cent": cent(base.get("basePriceValue")),
        "unidad_ref_nativa": (base.get("basePriceScale") or "").lower() or None,
        "precio_anterior_nativo_cent": cent(tachado),
        "ha_bajado_nativo": tachado is not None,
        # Hay oferta si hay precio tachado, si hay texto de promocion o si el
        # precio de hoy es el de una ventana promocional de `promotionPrices`.
        # Con la primera condicion sola se quedaban fuera 75 ofertas de las 170
        # que tienen ventana: las que bajan el precio sin tachar nada.
        "promo": bool(tachado or etiquetas.get("promoText1") or fin_oferta),
        "promo_txt": etiquetas.get("promoText1"),
        "promo_hasta": fin_oferta,
        "peso_variable": False,
        "categoria": p.get("mainCategoryID"),
        "disponible": bool(p.get("isAvailable")),
        "url": f"{BASE}/p/{p['productSlug']}" if p.get("productSlug") else None,
        "imagen": next((a.get("url") for a in (p.get("assets") or [])
                        if a.get("type") == "primary"), None),
        "descripcion": _descripcion(p),
        # El texto gana al certificado: el logotipo solo sabe decir "Espana" y
        # la ficha dice "Espana, Francia, Italia", que es la verdad.
        "origen": _origen(p) or cert.get("origen"),
        "sellos": ",".join(sorted(todos)) or None,
        "certificados": cert.get("certificados"),
        "es_marca_propia": bool(cert.get("es_marca_propia")) or propia_por_categoria or None,
        # Lo unico que Aldi dice de la cadena de frio. No hay senal de
        # refrigerado, asi que los frescos se quedan a None, que es la respuesta
        # honesta: no lo sabemos.
        "conservacion": "congelado" if p.get("isFreezing") else None,
        # Aldi marca aqui los lotes retirados de la venta. Hoy vale False en los
        # 2.065 productos, y aun asi merece la pena guardarlo: cuando deje de
        # ser cero, sabemos exactamente en que listas de la compra esta ese
        # producto. Ninguna app de la competencia avisa de retiradas.
        "es_recall": bool(p.get("isRecall")) or None,
        "capturado_en": datetime.now(timezone.utc),
    })
    return r


def main() -> int:
    t0 = time.monotonic()
    # Deja el recuento del dia escrito al terminar el proceso:
    peticiones.registra_al_salir(FUENTE)
    f = Fetcher(rate_per_sec=config.RITMO[FUENTE])

    cats, ids = rastrear(f)
    print(f"  {len(cats)} categorias, {len(ids)} ids de producto")
    if not ids:
        log_run(FUENTE, 0, 1, time.monotonic() - t0)
        print("  no se encontro ningun id: la pagina ha cambiado, revisar el patron")
        return 1

    datos, errores = productos(f, sorted(ids))
    filas = [a_registro(p) for p in datos]
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
    print(f"{FUENTE}: {len(filas)} productos, {errores} errores, {segundos:.0f}s")
    return 0 if completa else 1


if __name__ == "__main__":
    raise SystemExit(main())


def productos_crudo(body: bytes) -> list[dict]:
    """Para reprocesar desde el crudo: solo las respuestas de la API traen precios."""
    try:
        return json.loads(body).get("products", [])
    except Exception:  # noqa: BLE001
        return []       # las paginas HTML de categoria no llevan precio
