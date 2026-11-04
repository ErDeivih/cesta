"""Las metricas que lee el panel: que miren el dia de datos y digan lo que dicen.

**Por que existe.** David pidio el 4/11/2026 mas datos de Cesta en el panel, y la metrica
que de verdad dice si el producto sirve no es «cuantos productos hay» sino **cuantos se
pueden comparar hoy**: grupos con precio en mas de una cadena. Escribirlas a mano es
garantizar que un dia esten viejas; por eso salen de un modulo y se reescriben al final de
la pasada, como `CIFRAS.md`.

Lo que se fija aqui:
  1. `cadenas` dice, por cadena, si tiene datos en el dia y cuantos dias lleva guardados;
  2. `comparables_con_precio` y `en_varias_cadenas` se miden **sobre el mismo dia**
     (mezclar «hoy» con «algun dia» daria una razon que no significa nada);
  3. `ultima_ejecucion` se da en hora local y `dias_historial` cuenta dias distintos;
  4. se escribe un JSON valido y atomico en la raiz del proyecto.
"""
from __future__ import annotations

import json

import polars as pl

from projects.cesta import metricas


def _prepara(tmp_path, monkeypatch) -> None:
    """Un gold minimo con dos cadenas que se comparan en el grupo 1 y una que no tiene precio."""
    monkeypatch.setattr(metricas.config, "DATA", tmp_path / "data")
    data = tmp_path / "data"
    (data / "gold").mkdir(parents=True)
    grupos = pl.DataFrame([
        {"fuente": "mercadona", "id_fuente": "a", "grupo_id": 1,
         "precio_comparable": True, "precio_cent": 100},
        {"fuente": "mercadona", "id_fuente": "b", "grupo_id": 2,
         "precio_comparable": True, "precio_cent": 200},
        {"fuente": "dia", "id_fuente": "a", "grupo_id": 1,
         "precio_comparable": True, "precio_cent": 110},
        {"fuente": "dia", "id_fuente": "c", "grupo_id": 3,
         "precio_comparable": True, "precio_cent": 300},
        {"fuente": "alcampo", "id_fuente": "x", "grupo_id": 4,
         "precio_comparable": True, "precio_cent": None},
        # Sin precio en el catalogo (foto vieja) pero con precio hoy en `precio_diario`:
        # cuenta como comparable con precio, que es la definicion del panel.
        {"fuente": "mercadona", "id_fuente": "d", "grupo_id": 5,
         "precio_comparable": True, "precio_cent": None},
    ])
    grupos.write_parquet(data / "gold" / "grupos.parquet")
    precios = pl.DataFrame([
        {"fuente": "mercadona", "id_fuente": "a", "fecha": "2026-11-04", "precio_cent": 100},
        {"fuente": "mercadona", "id_fuente": "b", "fecha": "2026-11-04", "precio_cent": 200},
        {"fuente": "mercadona", "id_fuente": "d", "fecha": "2026-11-04", "precio_cent": 500},
        {"fuente": "dia", "id_fuente": "a", "fecha": "2026-11-04", "precio_cent": 110},
        {"fuente": "mercadona", "id_fuente": "a", "fecha": "2026-11-03", "precio_cent": 99},
        {"fuente": "dia", "id_fuente": "a", "fecha": "2026-11-03", "precio_cent": 111},
        {"fuente": "dia", "id_fuente": "c", "fecha": "2026-11-03", "precio_cent": 300},
    ])
    precios.write_parquet(data / "gold" / "precio_diario.parquet")
    (data / "runs.csv").write_text(
        "ts,fuente,filas,errores,segundos,ok\n"
        "2026-11-04T12:58:00.979372+00:00,mercadona,2,0,1.0,True\n",
        encoding="utf-8")


def test_las_metricas_miran_el_dia_de_datos(tmp_path, monkeypatch):
    _prepara(tmp_path, monkeypatch)

    datos = metricas.construye()

    assert datos["fecha_datos"] == "2026-11-04"
    assert datos["cadenas"] == [
        {"nombre": "alcampo", "hoy": False, "dias": 0},
        {"nombre": "dia", "hoy": True, "dias": 2},
        {"nombre": "mercadona", "hoy": True, "dias": 2},
    ]
    # Hoy hay precio en los grupos 1, 2 y 5 (el 3 solo ayer y el 4 no tiene precio).
    assert datos["comparables_con_precio"] == 3
    # Y de esos, solo el grupo 1 tiene precio en mas de una cadena.
    assert datos["en_varias_cadenas"] == 1
    assert datos["dias_historial"] == 2
    # La ultima pasada esta en UTC; el panel la lee en hora de Madrid.
    assert datos["ultima_ejecucion"] == "2026-11-04T13:58:00+01:00"


def test_sin_datos_no_inventa_cifras(tmp_path, monkeypatch):
    monkeypatch.setattr(metricas.config, "DATA", tmp_path / "data")
    (tmp_path / "data").mkdir()

    datos = metricas.construye()

    assert datos["cadenas"] == []
    assert datos["comparables_con_precio"] == 0
    assert datos["en_varias_cadenas"] == 0
    assert datos["dias_historial"] == 0
    assert datos["ultima_ejecucion"] is None


def test_escribe_json_valido_y_atomico(tmp_path, monkeypatch):
    _prepara(tmp_path, monkeypatch)

    ruta = metricas.escribe()

    assert ruta == tmp_path / "metricas-cesta.json"
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    assert datos["en_varias_cadenas"] == 1
    assert not list(tmp_path.glob("*.tmp")), "no puede quedar un temporal a medias"


def test_la_pasada_diaria_lo_reescribe():
    """Si solo lo escribiera un humano, el panel ensenaria un dia viejo sin avisar."""
    import inspect

    from projects.cesta import run

    fuente = inspect.getsource(run)
    assert "metricas" in fuente and ".escribe(" in fuente, (
        "la cadena diaria tiene que reescribir las metricas del panel al cerrar el dia")
