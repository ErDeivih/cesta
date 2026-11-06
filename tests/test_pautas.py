"""Pautas de salud: la ruta, el enlace y las fuentes, comprobados leyendo.

Lo que se puede comprobar leyendo el codigo y no da error al incumplirlo: que la ruta exista
dentro del armazon de Calorias, que se llegue desde el diario, que **todas** las fuentes se
abran fuera con su `rel`, que el objetivo use la misma clave que lee Calorias y que la pantalla
no prescriba.

La cuenta con datos conocidos y el «sin datos no calcula» se miden montando el componente en
`Pautas.test.tsx`; aqui solo se vigila lo que una prueba de componente no ve.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
SRC = RAIZ / "plataforma" / "web" / "app" / "src"
APP = SRC / "App.tsx"
DIARIO = SRC / "paginas" / "Diario.tsx"
PAUTAS = SRC / "paginas" / "Pautas.tsx"

FUENTES = (
    "https://www.who.int/news-room/fact-sheets/detail/healthy-diet",
    "https://www.efsa.europa.eu/es/press/news/130110",
    "https://efsa.onlinelibrary.wiley.com/doi/10.2903/j.efsa.2013.3005",
    "https://www.fao.org/4/y5686e/y5686e00.htm",
    "https://cpage.mpr.gob.es/publicacion/recomendaciones-dieteticas-saludables-y-sostenibles-"
    "complementadas-con-recomendaciones-de-actividad-fisica-para-la-poblacion-espanola-"
    "2022-069220082-0001/",
    "https://europepmc.org/article/MED/2305711",
)


def _leer(fichero: Path) -> str:
    if not fichero.exists():
        pytest.skip("esta copia no trae la interfaz nueva")
    return fichero.read_text(encoding="utf-8")


def test_la_ruta_vive_en_calorias_y_se_llega_desde_el_diario():
    app = _leer(APP)
    assert "import('./paginas/Pautas')" in app, "la pantalla no esta cargada en las rutas"
    assert 'path="/calorias/pautas"' in app, "la ruta no existe"
    assert re.search(
        r'<Route\s+path="/calorias/pautas"\s+element=\{<LayoutSuite app="calorias"><Pautas /></LayoutSuite>\}',
        app.replace("\n", " "),
    ), "la pantalla no va dentro del armazon de Calorias"
    assert "if (ruta.startsWith('/calorias/pautas')) return 'Pautas de salud'" in app, (
        "la pestaña se llamaria como el diario")

    diario = _leer(DIARIO)
    assert 'to="/calorias/pautas"' in diario, "desde el diario no se llega a las pautas"
    assert "Pautas de salud" in diario, "el enlace no dice a donde va"


def test_todas_las_fuentes_son_externas_y_llevan_rel():
    texto = _leer(PAUTAS)
    # Las seis se pintan con la misma plantilla de enlace: si la plantilla lleva `target` y
    # `rel`, las seis lo llevan. Que se pinten las seis lo mide `Pautas.test.tsx` montado.
    ancla = re.search(r"<a\b[^>]*target=\"_blank\"[^>]*>", texto, re.S)
    assert ancla, "ninguna fuente se abre fuera"
    assert 'rel="noopener noreferrer"' in ancla.group(0), "la fuente externa no lleva rel"
    for url in FUENTES:
        assert f"url: '{url}'" in texto, f"falta la fuente {url}"


def test_la_estimacion_es_mifflin_y_el_objetivo_usa_la_clave_del_diario():
    texto = _leer(PAUTAS)
    assert "10 * peso + 6.25 * altura - 5 * edad" in texto, "la estimacion no es la declarada"
    assert "? 5 : -161" in texto, "faltan los dos terminos de la estimacion"
    assert "FACTOR[actividad]" in texto, "la estimacion no aplica la actividad"
    assert "objetivo:${hoy()}" in texto, "el objetivo no usa la clave que lee Calorias"
    assert "{ kcal: rango.centro }" in texto, "el objetivo no guarda el valor que se enseña"


def test_no_prescribe_y_no_ensena_la_formula():
    texto = _leer(PAUTAS)
    for prohibido in ("deberías", "déficit", "IMC", "adelgazar", "fórmula", "objetivo automático"):
        assert prohibido not in texto, f"la pantalla prescribe o explica de mas: {prohibido}"
    assert "No es consejo médico." in texto, "falta el limite, y no es relleno"
    assert "deber[ií]as" not in texto
