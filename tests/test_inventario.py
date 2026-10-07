"""Puerta de S02: estado, proxima revision y evidencia por producto; reanudar sin duplicar.

Cada prueba es una frase del criterio de aceptacion del paquete o una regla de SUPERAPP-02 §3, y se
ejecutan contra una base de verdad en un directorio temporal.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

import polars as pl
import pytest

from core import inventario


@pytest.fixture
def con(tmp_path):
    return inventario.conecta(tmp_path / "inventario.sqlite")


def test_ver_el_mismo_producto_dos_veces_no_duplica(con):
    """Reanudar sin duplicar: la clave es unica y el alta es un upsert."""
    inventario.alta(con, "dia", "123", dia=date(2026, 10, 6))
    inventario.alta(con, "dia", "123", dia=date(2026, 10, 7))
    filas = con.execute("SELECT * FROM fichas").fetchall()
    assert len(filas) == 1
    assert filas[0]["descubierto_en"] == "2026-10-06"     # la primera vez se conserva
    assert filas[0]["visto_en"] == "2026-10-07"           # la ultima se actualiza


def test_un_producto_que_no_aparece_hoy_no_se_retira(con):
    """Ayer estaba y hoy no: sigue en el inventario, con su fecha."""
    inventario.alta(con, "aldi", "A1", dia=date(2026, 10, 6))
    inventario.alta(con, "aldi", "A2", dia=date(2026, 10, 7))
    assert con.execute("SELECT count(*) FROM fichas WHERE fuente='aldi'").fetchone()[0] == 2


def test_el_lease_impide_que_dos_procesos_cojan_la_misma_ficha(con):
    inventario.alta(con, "dia", "1")
    inventario.alta(con, "dia", "2")
    primera = inventario.tomar(con, 1)
    segunda = inventario.tomar(con, 5)
    assert len(primera) == 1
    assert primera[0]["id_fuente"] != segunda[0]["id_fuente"] if segunda else True
    assert len(segunda) == 1, "la ficha ya cogida no puede salir otra vez"


def test_un_lease_vencido_vuelve_a_la_cola_solo(con):
    """Si el proceso se muere, no hay que arreglar nada a mano."""
    inventario.alta(con, "dia", "1")
    momento = datetime(2026, 10, 7, 10, 0)
    assert len(inventario.tomar(con, 5, ahora=momento)) == 1
    assert inventario.tomar(con, 5, ahora=momento + timedelta(minutes=5)) == []
    recuperada = inventario.tomar(con, 5, ahora=momento + timedelta(hours=2))
    assert len(recuperada) == 1, "el lease caducado tiene que volver a la cola"


def test_terminar_pone_fecha_a_la_siguiente_revision(con):
    inventario.alta(con, "dia", "1")
    momento = datetime(2026, 10, 7, 10, 0)
    inventario.tomar(con, 5, ahora=momento)
    inventario.terminar(con, ("dia", "1", "", ""), inventario.CORRECTO, hash_util="abc",
                        parser_version="2026.10", ahora=momento)
    fila = con.execute("SELECT * FROM fichas").fetchone()
    assert fila["estado"] == inventario.CORRECTO
    assert fila["proxima_revision"] == (momento + timedelta(days=30)).date().isoformat()
    assert fila["hash_util"] == "abc" and fila["parser_version"] == "2026.10"
    assert fila["lease_hasta"] is None, "al cerrar se suelta el lease"


def test_un_conflicto_acorta_la_revision_a_siete_dias(con):
    inventario.alta(con, "dia", "1")
    momento = datetime(2026, 10, 7, 10, 0)
    inventario.terminar(con, ("dia", "1", "", ""), inventario.PARCIAL, conflicto=True, ahora=momento)
    assert con.execute("SELECT proxima_revision FROM fichas").fetchone()[0] == "2026-10-14"


def test_un_404_no_retira_el_producto_ni_borra_su_historial(con):
    """Regla del contrato: `no_encontrado`, con su fecha, y la fila sigue ahi."""
    inventario.alta(con, "carrefour", "X", dia=date(2026, 9, 1))
    inventario.terminar(con, ("carrefour", "X", "", ""), inventario.NO_ENCONTRADO,
                        resultado="404", ahora=datetime(2026, 10, 7))
    fila = con.execute("SELECT * FROM fichas").fetchone()
    assert fila["estado"] == inventario.NO_ENCONTRADO
    assert fila["descubierto_en"] == "2026-09-01"
    assert fila["proxima_revision"] is not None, "se volvera a mirar"


def test_el_resumen_dice_que_hay_en_cada_estado(con):
    inventario.alta(con, "dia", "1")
    inventario.alta(con, "dia", "2")
    inventario.alta(con, "aldi", "3")
    inventario.terminar(con, ("dia", "1", "", ""), inventario.CORRECTO)
    res = inventario.resumen(con)
    assert res["dia"][inventario.CORRECTO] == 1
    assert res["dia"][inventario.PENDIENTE] == 1
    assert res["aldi"][inventario.PENDIENTE] == 1


def test_el_enganche_levanta_el_inventario_del_bronze_historico(tmp_path, con):
    """La union de todas las capturas, sin pedir nada a la red: es el punto de partida de S02."""
    for fecha, ids in (("2026-10-05", ["a", "b"]), ("2026-10-06", ["b", "c"])):
        dia = tmp_path / "bronze" / "fuente=dia" / f"fecha={fecha}"
        dia.mkdir(parents=True)
        pl.DataFrame({"id_fuente": ids, "nombre": ["x", "y"]}).write_parquet(dia / "p.parquet")
    # Devuelve **productos distintos**, no altas procesadas: es el dato que interesa y el que
    # evita el error de contar 30 dias del mismo producto como 30 productos.
    registrados = inventario.enganche(con, tmp_path / "bronze", progreso=False)
    assert registrados == 3
    assert con.execute("SELECT count(*) FROM fichas").fetchone()[0] == 3
    fila = con.execute("SELECT * FROM fichas WHERE id_fuente='b'").fetchone()
    assert fila["descubierto_en"] == "2026-10-05" and fila["visto_en"] == "2026-10-06"
    assert fila["evidencia"], "cada ficha tiene que decir de donde salio"
