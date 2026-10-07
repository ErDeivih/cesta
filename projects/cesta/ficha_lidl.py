"""Una ficha real de Lidl, guardada: el paso previo para poder escribir su lector sin inventarlo.

**Por que este paso y no el lector directamente.** Un lector de ficha se escribe mirando una ficha de
verdad; escribirlo de memoria es inventarse la estructura, y luego el parser falla en silencio con
datos que parecen buenos. El encargo lo pide al reves de lo que apetece: **fixtures primero**.

**Lo que hace, con los mismos limites que el descubridor:** robots.txt primero, **una** peticion, y lo
descargado se guarda en crudo (mecanismos del proyecto) y en copia legible para poder analizarlo sin
volver a la red. Nada de paginacion ni reintentos infinitos.

**Lo que informa, para saber con que contamos antes de escribir nada:** si la ficha trae datos
estructurados (`application/ld+json`), y si aparecen las señales de ingredientes, nutricion y precio.
Es una **cota inferior**, no una promesa: ver la palabra no prueba que exista la tabla.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
ROBOTS_URL = "https://www.lidl.es/robots.txt"
# La ficha observada y documentada en SUPERAPP-02 §5: marca, titulo, descripcion e imagenes.
URL_OBSERVADA = "https://www.lidl.es/p/sondey-galletas-rellenas/p11000174"
COPIA_LOCAL = RAIZ / "data" / "lidl-ficha-ejemplo.html"

RE_LDJSON = re.compile(r'type=["\']application/ld\+json["\']', re.IGNORECASE)
SENALES = {
    "ingredientes": ("ingredient", "ingrediente"),
    "nutricion": ("nutrition", "nutricional", "kcal", "energia"),
    "precio": ("price", "precio", "€"),
    "alergenos": ("allergen", "alergeno"),
}


def estructura_de(html: str) -> dict:
    """Que ofrece la ficha, por señales. **Cota inferior**: no prueba que el dato exista."""
    plano = html.lower()
    return {
        "bytes": len(html),
        "bloques_ldjson": len(RE_LDJSON.findall(html)),
        **{nombre: any(s in plano for s in señales) for nombre, señales in SENALES.items()},
    }


RE_BLOQUE = re.compile(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', re.S | re.I)
RE_ETIQUETA = re.compile(r"<[^>]+>")


def sin_html(texto: str) -> str:
    """La descripcion de la ficha viene con etiquetas: se convierte a texto, no se pinta."""
    return " ".join(RE_ETIQUETA.sub(" ", texto or "").split())


def gtin_valido(codigo) -> str | None:
    """El GTIN si tiene 13 digitos y el digito de control cuadra; None si no.

    No es un adorno: un GTIN valido con procedencia es lo que permite afirmar identidad en S04, y uno
    que no cuadra **no se usa**. Se valida aqui para que no entre en el catalogo como si valiera.
    """
    digitos = re.sub(r"\D", "", str(codigo or ""))
    if len(digitos) != 13:
        return None
    suma = sum(int(d) * (3 if i % 2 else 1) for i, d in enumerate(digitos[:12]))
    return digitos if (10 - suma % 10) % 10 == int(digitos[12]) else None


def productos_de(html: str) -> list[dict]:
    """Los bloques `@type=Product` del HTML. Los `Organization` de la cadena se ignoran."""
    salida = []
    for bloque in RE_BLOQUE.findall(html):
        try:
            dato = json.loads(bloque.strip())
        except Exception:  # noqa: BLE001  (un bloque ilegible no invalida la ficha)
            continue
        for elemento in (dato if isinstance(dato, list) else [dato]):
            if isinstance(elemento, dict) and elemento.get("@type") == "Product":
                salida.append(elemento)
    return salida


def lee(html: str, *, url: str | None = None) -> dict:
    """El primer producto de la ficha, en campos que el proyecto entiende.

    Lo que no se sabe queda vacio, y `gtin_invalido` guarda el codigo que **no** paso la validacion:
    ausencia y codigo erroneo son cosas distintas y se representan distinto.
    """
    productos = productos_de(html)
    if not productos:
        raise ValueError("la ficha no trae ningun bloque de producto")
    p = productos[0]
    marca = p.get("brand")
    ofertas = p.get("offers") or []
    if isinstance(ofertas, dict):
        ofertas = [ofertas]
    # Un solo importe inequivoco: si hay mas de una condicion, no se elige por el usuario.
    importes = {round(float(o["price"]) * 100) for o in ofertas
                if isinstance(o, dict) and str(o.get("price", "")).replace(".", "", 1).isdigit()}
    codigo = p.get("gtin13")
    if isinstance(codigo, list):
        codigo = codigo[0] if codigo else None
    return {
        "fuente": "lidl",
        "id_fuente": str(p.get("sku") or ""),
        "nombre": p.get("name"),
        "marca": (marca or {}).get("name") if isinstance(marca, dict) else marca,
        "descripcion": sin_html(p.get("description")),
        # `gtin13` validado; `sku` (identificador interno) jamas como EAN.
        "ean": gtin_valido(codigo),
        "gtin_invalido": codigo if (codigo and not gtin_valido(codigo)) else None,
        "url": p.get("url") or url,
        "imagen": (p.get("image") or [None])[0] if isinstance(p.get("image"), list) else p.get("image"),
        "precio_cent": importes.pop() if len(importes) == 1 else None,
        "condiciones": ofertas,
    }


def descarga(url: str = URL_OBSERVADA, destino: Path | None = None) -> str:
    """Baja **una** ficha, comprobando antes robots.txt, y la deja guardada en crudo y en legible."""
    from urllib.robotparser import RobotFileParser

    from core import config, peticiones
    from core.fetch import Fetcher
    from core.storage import save_raw

    peticiones.registra_al_salir("lidl")
    f = Fetcher(rate_per_sec=config.RITMO.get("lidl", 1.0))
    robots = f.get(ROBOTS_URL)
    reglas = RobotFileParser()
    reglas.parse(robots.body.decode("utf-8", "replace").splitlines())
    if not reglas.can_fetch("CestaResearch", url):
        raise RuntimeError("la politica publicada de la web no permite esa ruta")
    respuesta = f.get(url)
    save_raw("lidl", f"ficha-{url.rstrip('/').split('/')[-1]}", respuesta.body)
    html = respuesta.body.decode("utf-8", "replace")
    copia = destino or COPIA_LOCAL
    copia.parent.mkdir(parents=True, exist_ok=True)
    copia.write_text(html, encoding="utf-8")
    return html


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    entrada = ap.add_mutually_exclusive_group(required=True)
    entrada.add_argument("--url", help=f"ficha a bajar (una peticion); por defecto {URL_OBSERVADA}")
    entrada.add_argument("--html", type=Path, help="ficha ya guardada (sin red)")
    a = ap.parse_args(argv)
    if a.html:
        html = a.html.read_text(encoding="utf-8")
    else:
        url = a.url or URL_OBSERVADA
        try:
            html = descarga(url)
        except Exception as exc:  # noqa: BLE001  (si no se puede bajar, se dice y se para)
            print(f"no se pudo bajar la ficha: {type(exc).__name__}: {exc}")
            return 1
        print(f"ficha bajada y guardada en {COPIA_LOCAL.relative_to(RAIZ).as_posix()}")
    datos = estructura_de(html)
    print(f"  {datos['bytes']:,} bytes · bloques de datos estructurados: {datos['bloques_ldjson']}"
          .replace(",", "."))
    for nombre in SENALES:
        print(f"  {nombre:<13} {'si' if datos[nombre] else 'no'} (señal en el texto, cota inferior)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
