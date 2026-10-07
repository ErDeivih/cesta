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
