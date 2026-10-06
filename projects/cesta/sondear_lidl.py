"""Piloto Lidl: HTML publico de ofertas, sin publicar bronze ni asumir cobertura total."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.robotparser import RobotFileParser

import httpx
from selectolax.parser import HTMLParser

URL = "https://www.lidl.es/c/ofertas-semanales/a10089449"


def extraer(html: str) -> list[dict]:
    """Conserva el payload completo; ni IAN ni productId se convierten en EAN."""
    productos = {}
    for nodo in HTMLParser(html).css("[data-grid-data]"):
        dato = json.loads(nodo.attributes["data-grid-data"])
        if not isinstance(dato, dict) or not dato.get("productId"):
            raise ValueError("Ficha Lidl sin identificador; revisar cambio de esquema")
        pid = (str(dato["productId"]), str(dato.get("variantId") or ""))
        if pid in productos and productos[pid] != dato:
            raise ValueError(f"Producto {pid} repetido con datos distintos; no sobrescribir")
        productos[pid] = dato
    if not productos:
        raise ValueError("HTML sin fichas Lidl: no equivale a catalogo vacio valido")
    return list(productos.values())


def precios_region(producto: dict, region: str) -> dict:
    """Resuelve region -> regionPriceId; nunca usa el precio por defecto como sustituto.

    Devuelve condiciones crudas (normal/club, fechas, formato); NO un precio elegible.
    El campo status de la region NO es stock en una tienda.
    """
    contexto = producto.get("regionsV2", {}).get(str(region))
    if not isinstance(contexto, dict) or contexto.get("regionPriceId") is None:
        return {"estado": "region_desconocida", "precios": None}
    precios = producto.get("regionsPrices", {}).get(str(contexto["regionPriceId"]))
    return {"estado": "observado" if precios else "sin_precio_regional",
            "region": contexto.get("regionName"), "precios": precios or None}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    entrada = ap.add_mutually_exclusive_group(required=True)
    entrada.add_argument("--html", type=Path, help="HTML ya guardado, sin red")
    entrada.add_argument("--web", action="store_true", help="Dos GET: robots y una pagina publica")
    ap.add_argument("--region", help="Identificador observado en regionsV2; no codigo postal")
    a = ap.parse_args()
    if a.web:
        with httpx.Client(timeout=30, follow_redirects=False,
                          headers={"User-Agent": "CestaResearch/0.1"}) as cliente:
            robots = cliente.get("https://www.lidl.es/robots.txt")
            robots.raise_for_status()
            reglas = RobotFileParser()
            reglas.parse(robots.text.splitlines())
            if not reglas.can_fetch("CestaResearch", URL):
                raise RuntimeError("La politica publicada no permite esta ruta")
            respuesta = cliente.get(URL)
            respuesta.raise_for_status()
            html = respuesta.text
    else:
        html = a.html.read_text(encoding="utf-8")
    productos = extraer(html)
    resumen = {"fuente": URL, "cobertura": "ofertas_semanales_parcial",
               "fichas_variantes": len(productos),
               "productos_padre": len({str(p["productId"]) for p in productos}),
               "con_precios_regionales": sum(bool(p.get("regionsPrices")) for p in productos),
               "ejemplos": [{"id": p["productId"], "variante": p.get("variantId"),
                              "nombre": p.get("fullTitle"),
                              "url": p.get("canonicalUrl"),
                              "regional": precios_region(p, a.region) if a.region else None}
                             for p in productos[:3]],
               "aviso": "No integrado en ingesta; no certifica stock, identidad ni precio vigente."}
    print(json.dumps(resumen, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
