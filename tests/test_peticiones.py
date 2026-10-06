"""El contador de peticiones: que cuente lo que dice contar, y que no invente ceros.

Es un instrumento, y los instrumentos de este proyecto se prueban como el codigo que miden. Lo que
se fija aqui: que cada acto sume donde toca, que "sin recuento" no se convierta en un cero, y que
escribir el fichero no pueda tumbar una captura de dos horas.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from core import peticiones


@pytest.fixture(autouse=True)
def _limpio():
    peticiones.reinicia()
    yield
    peticiones.reinicia()


def test_cuenta_peticiones_por_host():
    peticiones.pide("https://www.dia.es/compra-online/limpieza/c?offset=0")
    peticiones.pide("https://www.dia.es/compra-online/limpieza/c?offset=24")
    peticiones.pide("https://www.aldi.es/productos/x.html")
    r = peticiones.resumen()
    assert r["peticiones"] == 3
    assert r["por_host"] == {"www.dia.es": 2, "www.aldi.es": 1}


def test_distingue_cache_de_peticion():
    """Sin esta distincion, "menos peticiones" no separa ahorro de averia."""
    peticiones.pide("https://www.mercadona.es/api/categories/")
    peticiones.de_cache("mercadona")
    peticiones.de_cache("mercadona")
    r = peticiones.resumen()
    assert r["peticiones"] == 1
    assert r["cache"] == 2
    assert r["por_fuente_cache"] == {"mercadona": 2}


def test_las_evitadas_son_decisiones_con_su_motivo():
    peticiones.evita("alcampo", "fuera-de-alcance")
    peticiones.evita("alcampo", "fuera-de-alcance")
    r = peticiones.resumen()
    assert r["evitadas"] == 2
    assert r["por_fuente_evitadas"] == {"alcampo": 2}
    assert r["motivos"] == ["fuera-de-alcance"]


def test_no_escribe_fichero_si_no_hubo_nada(tmp_path, monkeypatch):
    """Un fichero con ceros pareceria una captura que fue bien y no pidio nada: no es lo mismo."""
    monkeypatch.setattr(peticiones, "CARPETA", tmp_path)
    assert peticiones.escribe("dia", date(2026, 10, 6)) is None
    assert not list(tmp_path.iterdir())


def test_escribe_el_fichero_del_dia_con_su_nombre(tmp_path, monkeypatch):
    monkeypatch.setattr(peticiones, "CARPETA", tmp_path)
    peticiones.pide("https://www.dia.es/x")
    peticiones.evita("dia")
    ruta = peticiones.escribe("dia", date(2026, 10, 6))
    assert ruta is not None and ruta.name == "dia-2026-10-06.json"
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    assert datos["fuente"] == "dia" and datos["peticiones"] == 1 and datos["evitadas"] == 1


def test_contar_no_puede_tumbar_una_captura(monkeypatch):
    """La tarea de las 06:00 no se rompe por un contador: si algo falla, se sigue."""
    monkeypatch.setattr(peticiones, "CARPETA", Path("Z:/servidor/que/no/existe"))
    peticiones.pide("https://www.dia.es/x")
    assert peticiones.escribe("dia") is None      # no lanza, devuelve None
    assert peticiones.resumen()["peticiones"] == 1


def test_el_informe_dice_sin_recuento_y_no_cero(tmp_path, monkeypatch, capsys):
    """Una cadena que no dejo fichero no es un cero: es que no corrio o se cayo."""
    from projects.cesta import peticiones as informe
    monkeypatch.setattr(informe, "CARPETA", tmp_path)
    informe.un_dia("2026-10-06")
    salida = capsys.readouterr().out
    assert "no hay ningun recuento" in salida
    assert "puede que no corriera" in salida


def test_el_informe_suma_las_cadenas_que_si_dejaron_recuento(tmp_path, monkeypatch, capsys):
    from projects.cesta import peticiones as informe
    monkeypatch.setattr(informe, "CARPETA", tmp_path)
    (tmp_path / "dia-2026-10-06.json").write_text(json.dumps(
        {"fuente": "dia", "peticiones": 10, "cache": 3, "evitadas": 2,
         "por_host": {"www.dia.es": 10}}), encoding="utf-8")
    informe.un_dia("2026-10-06")
    salida = capsys.readouterr().out
    assert "10" in salida and "3" in salida and "2" in salida
    assert "sin recuento" in salida          # las otras cuatro lo dicen


def test_las_pruebas_no_dejan_recuento_del_dia(monkeypatch):
    """Un fichero escrito por una prueba es un dato falso en el informe del dia.

    Paso de verdad: al ejecutar el informe aparecio un recuento de Carrefour con 0 peticiones y 2
    lecturas de cache, escrito al recorrer el camino de la cache desde una prueba.
    """
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "tests/test_peticiones.py::test_x")
    monkeypatch.setattr(peticiones, "escribe", lambda *a, **k: pytest.fail("no debe escribirse"))
    peticiones.registra_al_salir("carrefour")     # no registra nada: no hay nada que escribir
