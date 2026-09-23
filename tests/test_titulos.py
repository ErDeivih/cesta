"""El titulo de la pestana: con diez abiertas, saber cual es cual.

Lo pide el encargo (§8): *"el titulo de cada pantalla en la pestana, para quien la tenga
abierta entre otras diez"*. Y es literal: con el buscador, la cesta, el panel y tres fichas
abiertas, todas con el mismo titulo, no hay forma de saber cual es cual.

Lo que se vigila aqui:

  - **Que haya un titulo por ruta**, y que las rutas con dato propio (la ficha, el grupo)
    lo mejoren con el nombre del producto: "Producto" y "Leche entera Hacendado" no se
    parecen en nada cuando hay diez pestanas abiertas.
  - **Que lleve el nombre de la aplicacion.** Una pestana que solo dice "La cesta" no dice
    de que aplicacion es.
  - **Que no se escriba el titulo en cada pantalla a mano.** Con nueve pantallas, la
    decima nace sin titulo; el mapa esta en un sitio (`App.tituloDe`) y las dos pantallas
    que saben mas lo mejoran por el orden natural de los efectos (el dato llega despues
    que la ruta).

Como las de contraste y las de movil, esto lee el codigo: un `document.title` que falta no
da ningun error de compilacion.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
SRC = RAIZ / "plataforma" / "web" / "app" / "src"
TITULO = SRC / "componentes" / "Titulo.tsx"
APP = SRC / "App.tsx"
FICHA = SRC / "paginas" / "Producto.tsx"
GRUPO = SRC / "paginas" / "Grupo.tsx"


def _leer(f: Path) -> str:
    if not f.exists():
        pytest.skip("esta copia no trae la interfaz nueva")
    return f.read_text(encoding="utf-8")


def test_hay_un_titulo_por_ruta_y_dice_de_que_aplicacion_es():
    app = _leer(APP)
    assert "document.title" in app, "nadie pone el titulo de la pestana"
    assert "export function tituloDe(" in app, \
        "el titulo por ruta tiene que estar en un sitio solo, no repartido por pantallas"
    for ruta, nombre in (("'/'", "Buscar"), ("'/cesta'", "La cesta"),
                         ("'/panel'", "Panel"), ("'/escaner'", "Escáner")):
        assert nombre in app, f"falta el titulo de la ruta {ruta}"
    assert re.search(r"if \(ruta\.startsWith\('/grupo/'\)", app), \
        "la ficha y el grupo necesitan su titulo de arranque"
    assert re.search(r"if \(ruta\.startsWith\('/unirme/'\)", app), \
        "la invitacion tambien es una pantalla y tambien se abre en una pestana"


def test_el_nombre_de_la_aplicacion_va_siempre():
    titulo = _leer(TITULO)
    assert re.search(r"export const SUFIJO = '· Cesta'", titulo), \
        "una pestana que solo dice 'La cesta' no dice de que aplicacion es"
    assert "document.title = limpio ?" in titulo


def test_las_pantallas_que_saben_mas_mejoran_el_titulo():
    for fichero in (FICHA, GRUPO):
        fuente = _leer(fichero)
        assert "useTitulo(" in fuente, \
            f"{fichero.name} no pone el nombre del producto en la pestana"
        assert "useTitulo(grupo?.nombre)" in fuente or "useTitulo(producto?.nombre" in fuente, \
            f"{fichero.name} llama a `useTitulo` sin el dato: el titulo no mejora"
