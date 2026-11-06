"""Pautas de salud: la ruta, el enlace, las cifras y sus fuentes, comprobados leyendo.

Lo que se puede comprobar leyendo el codigo y no da error al incumplirlo: que la ruta exista
dentro del armazon de Calorias, que se llegue desde el diario y desde el propio objetivo, que
**todas** las fuentes esten declaradas con su fecha y su enlace, que el objetivo use la misma
clave que lee Calorias y que la pantalla no prescriba ni ensene la cuenta.

La cuenta con datos conocidos, el «sin datos no calcula» y el objetivo que solo existe al
elegirlo se miden montando el componente en `Pautas.test.tsx`; en `tests/salud.test.mjs` se mide
la aritmetica sola. Aqui solo se vigila lo que una prueba de componente no ve.
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
SALUD = SRC / "logica" / "salud.ts"

# Las ocho fuentes verificadas el 2026-11-06, con el enlace que se abre.
FUENTES = (
    "https://europepmc.org/article/MED/2305711",
    "https://www.efsa.europa.eu/en/press/news/nda100326",
    "https://www.who.int/news-room/fact-sheets/detail/healthy-diet",
    "https://www.who.int/news-room/fact-sheets/detail/sodium-reduction",
    "https://www.who.int/news-room/fact-sheets/detail/alcohol",
    "https://www.fao.org/4/y5686e/y5686e00.htm",
    "https://www.cdc.gov/healthy-weight-growth/losing-weight/index.html",
    "https://www.aesan.gob.es/nutricion/recomendaciones-dieteticas",
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


def test_el_objetivo_del_diario_tiene_su_por_que_a_mano():
    """Junto al objetivo, un enlace corto que explica de donde sale. Y de 44 px."""
    diario = _leer(DIARIO)
    enlaces = re.findall(r"<Link\b[^>]*>", diario, re.S)
    por_que = [e for e in enlaces if 'aria-label="Por qué este objetivo"' in e]
    assert por_que, "el objetivo no tiene enlace al «por que»"
    assert any('to="/calorias/pautas"' in e for e in por_que), (
        "el «por que» no lleva a las pautas")
    assert all("min-h-[44px]" in e for e in por_que), (
        "el enlace del «por que» no llega a 44 px")
    assert "Por qué" in por_que[0], "el enlace no dice «Por que»"


def test_todas_las_fuentes_estan_declaradas_con_su_fecha_y_su_enlace():
    salud = _leer(SALUD)
    for url in FUENTES:
        assert f"url: '{url}'" in salud, f"falta la fuente {url}"
    # Cada fuente lleva su fecha, y son las ocho verificadas.
    assert salud.count("fecha:") >= len(FUENTES), "hay fuentes sin fecha"

    # Y el enlace que se pinta abre fuera y lleva `rel`.
    texto = _leer(PAUTAS)
    ancla = re.search(r"<a\b[^>]*target=\"_blank\"[^>]*>", texto, re.S)
    assert ancla, "ninguna fuente se abre fuera"
    assert 'rel="noopener noreferrer"' in ancla.group(0), "la fuente externa no lleva rel"


def test_la_estimacion_es_mifflin_y_el_objetivo_usa_la_clave_del_diario():
    salud = _leer(SALUD)
    assert "10 * peso + 6.25 * altura - 5 * edad" in salud, "la estimacion no es la declarada"
    assert "? 5 : -161" in salud, "faltan los dos terminos de la estimacion"
    assert "ACTIVIDAD[actividad]" in salud, "la estimacion no aplica la actividad"
    assert "nivel.factor" in salud, "el nivel de actividad no multiplica el gasto"

    pautas = _leer(PAUTAS)
    assert "calcularEstimacion" in pautas, "la pantalla no usa la cuenta declarada"
    assert "objetivo:${hoy()}" in pautas, "el objetivo no usa la clave que lee Calorias"
    assert "kcal: estimacion.centro" in pautas, "el objetivo no guarda la cifra que se enseña"
    # Lo que se guarda lleva el motivo y el reparto, sin romper lo que ya lee el diario.
    assert "motivo: estimacion.objetivo" in pautas, "no se guarda la eleccion"
    assert "ajuste: estimacion.ajuste" in pautas, "no se guarda el ajuste"
    assert "macros: gramosDeMacros(estimacion.centro)" in pautas, "no se guardan los macros"


def test_no_prescribe_y_no_ensena_la_cuenta():
    texto = _leer(PAUTAS)
    for prohibido in (
        "deberías", "déficit", "IMC", "adelgazar", "fórmula", "objetivo automático",
        "Mifflin", "PAL", "TDEE",
    ):
        assert prohibido not in texto, f"la pantalla prescribe o habla de como esta hecha: {prohibido}"
    assert "deber[ií]as" not in texto
    # El aviso vive en `salud.ts` y la pantalla lo usa: no se copia en dos sitios.
    assert "AVISO_MEDICO" in texto, "falta el limite, y no es relleno"
    assert (
        "No es consejo médico. Si tienes una condición de salud, consulta con un profesional."
        in _leer(SALUD)
    ), "el aviso medico no es el texto acordado"
