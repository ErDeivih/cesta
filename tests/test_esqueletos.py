"""Los estados de carga: un hueco del tamaño de lo que va a venir.

Es la ultima fila del §8 del encargo -- *"los estados de carga: nada de saltos de
maquetacion. Un hueco del tamaño de lo que va a venir"* -- y la unica que quedaba abierta
de esa seccion.

El fallo que se arregla, dicho con el caso peor: en la lista de la compra, `Cargando` era
una linea de texto. Cuando llegaba la lista, esa linea se convertia en nueve filas y **todo
lo de abajo bajaba de golpe** -- en la pantalla que se usa de pie y con una mano, con el
pulgar ya camino de un boton. Eso no es una espera: es pulsar lo que no era.

Lo que se vigila aqui:

  - **Que `Cargando` reserve sitio** y no sea una linea suelta.
  - **Que el esqueleto tenga la forma de lo que viene**: filas con el mismo hueco entre
    ellas que la lista de verdad (`gap-2`), y una cuadricula de tres columnas para el
    mosaico. Un esqueleto con la forma equivocada reserva el sitio equivocado y encima
    promete algo que no es.
  - **Que no se pierda el aviso para quien no ve**: `role="status"` y un texto para
    lectores de pantalla, porque un bloque gris no dice nada a un lector.
  - **Que se use donde de verdad salta la maquetacion**: los resultados del buscador, las
    lineas de la lista y la cuadricula del mosaico.

Como las de contraste y las de movil, esto lee el codigo: un salto de maquetacion no da
ningun error de compilacion.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
SRC = RAIZ / "plataforma" / "web" / "app" / "src"
UI = SRC / "componentes" / "ui.tsx"
BUSCAR = SRC / "paginas" / "Buscar.tsx"
CESTA = SRC / "paginas" / "Cesta.tsx"
MOSAICO = SRC / "componentes" / "Mosaico.tsx"


def _leer(f: Path) -> str:
    if not f.exists():
        pytest.skip("esta copia no trae la interfaz nueva")
    return f.read_text(encoding="utf-8")


def test_el_esqueleto_reserva_sitio_y_tiene_forma():
    ui = _leer(UI)
    assert re.search(r"export function Esqueleto\(", ui), \
        "no hay esqueleto de filas: los estados de carga vuelven a ser una linea de texto"
    assert re.search(r"export function EsqueletoRejilla\(", ui), \
        "la cuadricula tambien necesita su hueco: es otra forma"
    # Un hueco del tamaño de lo que viene, no un adorno: altura propia y el mismo
    # hueco entre filas que la lista de verdad.
    assert "style={{ height: alto }}" in ui, \
        "las filas del esqueleto tienen que tener altura: si no, no reservan nada"
    assert 'className="grid gap-2"' in ui, \
        "el hueco entre filas tiene que ser el de la lista de verdad (`gap-2`)"
    assert "animate-pulse" in ui, "un bloque quieto se lee como contenido roto"


def test_el_cargando_de_pantalla_completa_tambien_reserva():
    ui = _leer(UI)
    bloque = ui.split("export function Cargando(")[1].split("export function Esqueleto(")[0]
    assert "min-h-[" in bloque, \
        "`Cargando` sigue siendo una linea suelta: al llegar el contenido, todo salta"
    assert 'role="status"' in bloque


def test_el_aviso_llega_a_quien_no_ve_el_bloque():
    ui = _leer(UI)
    assert ui.count('className="sr-only">Cargando') >= 2, \
        "un bloque gris no dice nada a un lector de pantalla: hace falta el texto"
    assert ui.count('role="status"') >= 3, \
        "los estados de carga se anuncian con `role=status`, no con un div mudo"


def test_se_usa_donde_de_verdad_salta_la_maquetacion():
    """Los tres sitios donde el contenido llega y empuja: resultados, lista y cuadricula."""
    buscar = _leer(BUSCAR)
    assert "<Esqueleto filas=" in buscar, \
        "los resultados del buscador siguen llegando de golpe sobre una linea de texto"
    cesta = _leer(CESTA)
    assert "<Esqueleto filas=" in cesta, \
        "la lista de la compra es donde mas duele un salto: el pulgar ya va camino del boton"
    mosaico = _leer(MOSAICO)
    assert "<EsqueletoRejilla" in mosaico, \
        "la cuadricula del mosaico tiene su propia forma y su propio hueco"
