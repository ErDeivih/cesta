"""Sondea si Alcampo y Aldi publican ficha de producto con EAN o nutricion.

Por que existe este fichero
---------------------------
Alcampo y Aldi son el 50 % del catalogo y ninguno de los dos publica codigo de
barras en el listado, que es lo unico que estamos pidiendo. Sin EAN no hay cruce
con Open Food Facts, y por tanto no hay Nutri-Score, ni NOVA, ni ingredientes,
ni sellos para 25.628 productos.

DIA y Mercadona si lo dan, pero no en el listado: lo dan en la **ficha** de cada
producto, y por eso los dos tienen un maestro incremental que solo pide fichas
que todavia no conoce. Si Alcampo o Aldi tuvieran algo parecido, se les podria
hacer exactamente lo mismo.

Este script no recolecta nada: solo llama a un punado de direcciones candidatas
con UN producto y cuenta que trae cada respuesta. Se mira el resultado y se
decide. Tirar 25.000 peticiones a ciegas contra el WAF de Alcampo seria la forma
mas rapida de que nos cierren la puerta que hoy tenemos abierta.

    uv run python -m projects.cesta.sondear_fichas

Si alguna direccion contesta con ean/gtin o con nutricion, el siguiente paso es
un maestro incremental calcado al de DIA (`collectors/dia.py`, `_ficha`), con su
ritmo lento y su fichero permanente: el EAN de un producto no cambia, asi que se
pide una vez en la vida y el catalogo entero se cubre en unas semanas sin que se
note.
"""
from __future__ import annotations

import re

from core import config
from core.fetch import Fetcher

# Las senales que buscamos en la respuesta, con los nombres que suelen tener.
SENALES = {
    "ean": ("ean", "gtin", "barcode", "eanCode", "ean_code", "upc"),
    "ingredientes": ("ingredient", "ingredientes", "composition"),
    "nutricion": ("nutrition", "nutriment", "energy", "kcal", "nutritional"),
    "alergenos": ("allergen", "alergen"),
    "origen": ("origin", "origen", "countryOfOrigin", "provenance"),
}

ALCAMPO = "https://www.compraonline.alcampo.es"
ALDI = "https://www.aldi.es"


def _candidatas_alcampo(pid: str) -> list[str]:
    """Su web es una SPA: la ficha se pinta con una llamada que no vemos."""
    return [
        f"{ALCAMPO}/api/v5/products/{pid}",
        f"{ALCAMPO}/api/v6/products/{pid}",
        f"{ALCAMPO}/api/v5/products/{pid}/details",
        f"{ALCAMPO}/products/{pid}",                      # el HTML, por si trae JSON dentro
        f"{ALCAMPO}/api/v5/products?productIds={pid}",
    ]


def _candidatas_aldi(slug: str, oid: str) -> list[str]:
    return [
        f"{ALDI}/p/{slug}",                               # el HTML de la ficha
        f"{ALDI}/api/v1/products/{oid}",
        f"{ALDI}/api/products/{oid}",
        f"{ALDI}/.rest/aldi/products/{oid}",
    ]


def _resumir(cuerpo: bytes) -> str:
    """Que senales aparecen en la respuesta, y cuantas veces."""
    try:
        texto = cuerpo.decode("utf-8", "replace")
    except Exception:  # noqa: BLE001 - un sondeo no puede tumbarse porque una
        return "(ilegible)"   # respuesta venga en un formato que no esperabamos
    bajo = texto.lower()
    hallado = []
    for etiqueta, palabras in SENALES.items():
        veces = sum(bajo.count(w.lower()) for w in palabras)
        if veces:
            hallado.append(f"{etiqueta}x{veces}")
    return ", ".join(hallado) or "nada de lo que buscamos"


def _muestra_ean(cuerpo: bytes) -> str | None:
    """Un numero de 8 a 14 cifras pegado a una clave que suene a codigo."""
    texto = cuerpo.decode("utf-8", "replace")
    m = re.search(r'"(?:ean|gtin|barcode|ean_?[Cc]ode|upc)\w*"\s*:\s*"?(\d{8,14})', texto)
    return m.group(1) if m else None


def _probar(f: Fetcher, url: str) -> None:
    # Un sondeo prueba direcciones que pueden no existir: cualquier fallo es un
    # resultado valido y hay que seguir con la siguiente.
    try:
        r = f.get(url)
    except Exception as exc:  # noqa: BLE001
        print(f"    {url[-58:]:58}  {type(exc).__name__}")
        return
    cuerpo = r.body or b""
    marca = _muestra_ean(cuerpo)
    extra = f"  <-- EAN {marca}" if marca else ""
    print(f"    {url[-58:]:58}  {len(cuerpo):>8}b  {_resumir(cuerpo)}{extra}")


def _un_producto(fuente: str) -> dict | None:
    """Un producto cualquiera del ultimo bronze de esa cadena."""
    import duckdb

    ruta = config.DATA / "bronze" / f"fuente={fuente}"
    dias = sorted(p.name for p in ruta.glob("fecha=*"))
    if not dias:
        return None
    patron = str(ruta / dias[-1] / "*.parquet")
    fila = duckdb.sql(
        f"select id_fuente, url, nombre from read_parquet('{patron}') limit 1"
    ).fetchone()
    return {"id": fila[0], "url": fila[1], "nombre": fila[2]} if fila else None


def main() -> int:
    print("Sondeo de fichas de producto. No recolecta: solo pregunta una vez.\n")

    p = _un_producto("alcampo")
    if p:
        pid = (p["url"] or "").rsplit("/", 1)[-1]
        print(f"ALCAMPO  {p['nombre'][:54]}")
        print(f"         productId {pid}")
        # Medio segundo entre peticiones: son cinco llamadas, no hay prisa, y
        # Alcampo esta detras de un WAF al que no conviene darle motivos.
        f = Fetcher(rate_per_sec=0.5)
        for url in _candidatas_alcampo(pid):
            _probar(f, url)
        print()

    p = _un_producto("aldi")
    if p:
        slug = (p["url"] or "").rsplit("/", 1)[-1]
        print(f"ALDI     {p['nombre'][:54]}")
        print(f"         slug {slug}  objectID {p['id']}")
        f = Fetcher(rate_per_sec=1.0)
        for url in _candidatas_aldi(slug, p["id"]):
            _probar(f, url)
        print()

    print("Lectura del resultado:")
    print("  - Si alguna linea acaba en '<-- EAN', esa es la direccion buena y")
    print("    toca escribir el maestro incremental copiando el de DIA.")
    print("  - Si solo sale 'nutricionxN' sin EAN, sigue mereciendo la pena: la")
    print("    nutricion es lo que nos falta, el EAN solo era el camino para")
    print("    llegar a ella.")
    print("  - Si todas dicen 'nada de lo que buscamos' o dan error, la respuesta")
    print("    es que esas dos cadenas no lo publican y hay que dejarlo escrito.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
