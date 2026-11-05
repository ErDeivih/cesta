"""Las tendencias enseñan los huecos, no ceros, y no inventan una media.

Se lee el codigo, como las demas pruebas de contrato del frontend, porque aqui el fallo no da error: un
grafico que dibuja cero donde no hay dato se ve perfectamente bien y miente.
"""
from __future__ import annotations

from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "plataforma" / "web" / "app" / "src"


def _leer(relativa: str) -> str:
    ruta = SRC / relativa
    if not ruta.exists():
        pytest.skip("esta copia no trae la interfaz nueva")
    return ruta.read_text(encoding="utf-8")


def test_la_ruta_de_tendencias_tiene_su_pantalla():
    app = _leer("App.tsx")
    assert "Tendencias" in app
    assert 'path="/calorias/tendencias"' in app


def test_un_dia_sin_dato_se_dice_y_no_se_dibuja_como_cero():
    pantalla = _leer("paginas/Tendencias.tsx")
    assert "d.kcal_conocida === null" in pantalla
    # *Cambió el 5/11/2026 con la auditoría (§8): la frase que explicaba la decisión de diseño
    # —«no se dibuja, porque un cero no es lo mismo que no saber»— se borró; el hueco se sigue
    # diciendo con la palabra, que es lo que esta prueba tiene que proteger.*
    assert "Sin dato de energía en este día" in pantalla, "el hueco se dice con palabras"
    # Y el otro lado del ternario sigue dibujando la barra y su cifra: el hueco no la recibe.
    assert "bg-bosque" in pantalla and "kcal conocidas" in pantalla


def test_la_media_solo_cuenta_los_dias_que_traen_dato():
    """Meter los huecos como ceros hundiria la media, y no seria la media de nada."""
    pantalla = _leer("paginas/Tendencias.tsx")
    assert "filas.filter((d) => d.kcal_conocida !== null)" in pantalla
    # *La frase vieja («no hay media que dar») se sustituyó por la que dice el §8:
    # «Sin dato de calorías en estos días.»*
    assert "Sin dato de calorías en estos días" in pantalla


def test_la_pantalla_declara_que_mide():
    pantalla = _leer("paginas/Tendencias.tsx")
    assert "No es todo lo que comiste" in pantalla


def test_el_gancho_del_rango_va_con_la_cuenta_en_la_clave():
    api = _leer("api/diario.ts")
    assert "useRango" in api
    assert "queryKey: ['diario-rango', cuenta, desde, hasta]" in api
