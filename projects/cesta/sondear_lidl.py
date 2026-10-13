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


# **De donde sale la region, que es la pregunta que B03 deja abierta.**
#
# *El `--region` de Lidl es un identificador de `regionsV2` (un numero), y **un codigo postal no es ese
# numero**.* **Asi que la correspondencia hay que acreditarla, no suponerla** -- *y eso es lo que el plan
# prohibe: «no convertir CP en id de region sin correspondencia».*
#
# **Y se puede acreditar, porque la propia fuente publica los nombres.** *Las 55 regiones vienen con
# `regionName`, y de ahi sale la tabla.*
#
# *Pero los nombres traen lo que traen:* **«Badajoz» viene escrito «Badajoz» con tilde en la a, «Ceuta» con
# un espacio detras, y hay una region llamada «Cat 2».** *Asi que el emparejamiento **normaliza** -- minusculas
# y sin tildes -- **y si no encuentra, dice que no sabe.*** **No hay emparejamiento difuso ni por parecido:
# un CP que no case se queda sin region, y sin region no se publica.**
_PROVINCIAS_POR_CP = {
    "01": "alava", "02": "albacete", "03": "alicante", "04": "almeria", "05": "avila",
    "06": "badajoz", "07": "baleares", "08": "barcelona", "09": "burgos", "10": "caceres",
    "11": "cadiz", "12": "castellon", "13": "ciudad real", "14": "cordoba", "15": "a coruna",
    "16": "cuenca", "17": "girona", "18": "granada", "19": "guadalajara", "20": "guipuzcoa",
    "21": "huelva", "22": "huesca", "23": "jaen", "24": "leon", "25": "lleida",
    "26": "la rioja", "27": "lugo", "28": "madrid", "29": "malaga", "30": "murcia",
    "31": "navarra", "32": "ourense", "33": "asturias", "34": "palencia", "35": "las palmas",
    "36": "pontevedra", "37": "salamanca", "38": "santa cruz de tenerife", "39": "cantabria",
    "40": "segovia", "41": "sevilla", "42": "soria", "43": "tarragona", "44": "teruel",
    "45": "toledo", "46": "valencia", "47": "valladolid", "48": "vizcaya", "49": "zamora",
    "50": "zaragoza", "51": "ceuta", "52": "melilla",
}


def _sin_tildes(texto: str) -> str:
    """*Minusculas, sin tildes y sin espacios de sobra.* **Para emparejar nombres como los escribe la
    fuente, no como los escribiria un formulario.**"""
    tabla = str.maketrans("áéíóúàèìòùäëïöüâêîôûãõñç", "aeiouaeiouaeiouaeiouaonc")
    return " ".join(str(texto or "").lower().translate(tabla).split())


def region_del_cp(cp: str, regiones: dict) -> dict:
    """**De codigo postal a `regionPriceId`, acreditando la correspondencia por el NOMBRE publicado.**

    *`regiones` es el `regionsV2` tal cual viene en la captura: `{id: {regionName, regionPriceId}}`.*

    Devuelve siempre un diccionario con `estado`, y **nunca inventa**: si el CP no es de dos digitos
    conocidos, o si su provincia no aparece entre los nombres de la fuente, devuelve
    `region_desconocida` -- *y quien lo llame tiene que negarse a publicar, no elegir la primera.*
    """
    dos = str(cp or "").strip()[:2]
    provincia = _PROVINCIAS_POR_CP.get(dos)
    if provincia is None:
        return {"estado": "cp_desconocido", "region": None, "nombre": None,
                "motivo": f"el CP «{cp}» no empieza por un codigo de provincia conocido"}
    for ident, datos in (regiones or {}).items():
        if not isinstance(datos, dict) or datos.get("regionPriceId") is None:
            continue
        if _sin_tildes(datos.get("regionName")) == provincia:
            return {"estado": "acreditada", "region": str(ident),
                    "nombre": datos.get("regionName"), "provincia": provincia}
    # **Y aqui esta lo que el plan pide**: *no hay «la mas parecida».*
    return {"estado": "region_desconocida", "region": None, "nombre": None, "provincia": provincia,
            "motivo": f"la fuente no publica ninguna region llamada «{provincia}»"}


def regiones_del_html(html: str) -> dict:
    """**Las 55 regiones que la propia fuente publica.** *De aqui sale la tabla, no de una lista nuestra.*"""
    regiones: dict = {}
    for nodo in HTMLParser(html).css("[data-grid-data]"):
        dato = json.loads(nodo.attributes["data-grid-data"])
        for ident, datos in (dato.get("regionsV2") or {}).items():
            if isinstance(datos, dict) and datos.get("regionPriceId") is not None:
                regiones[str(ident)] = datos
    return regiones


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
