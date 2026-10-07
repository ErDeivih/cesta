"""El informe de cobertura: que cuente lo que dice contar y que no invente cobertura.

Lo que se fija: que la deuda de cola se cuente bien (pendientes, en curso y vencidas), que las
edades se repartan en tramos con las fichas sin fecha aparte, y que un inventario vacio diga cero
sin reventar. Y la regla de la casa: el informe cuenta lo **descubierto**, no el surtido.
"""
from __future__ import annotations

from datetime import date, datetime

import pytest

from core import inventario
from projects.cesta import informe_inventario as informe


@pytest.fixture
def con(tmp_path):
    return inventario.conecta(tmp_path / "inventario.sqlite")


def test_un_inventario_vacio_son_ceros_y_no_un_error(con, capsys):
    datos = informe.informe(con, hoy=date(2026, 10, 7))
    assert datos["total"]["fichas"] == 0
    assert "no es el surtido de ninguna cadena" in capsys.readouterr().out


def test_cuenta_la_deuda_de_cola(con):
    for i in range(3):
        inventario.alta(con, "dia", f"p{i}")                    # pendientes
    inventario.alta(con, "dia", "c1")
    inventario.terminar(con, ("dia", "c1", "", ""), inventario.CORRECTO,
                        ahora=datetime(2026, 9, 1, 10, 0))       # vencida (revisión a 30 días)
    inventario.alta(con, "dia", "e1")
    inventario.tomar(con, 5, ahora=datetime(2026, 10, 7, 10, 0))  # alguna queda en curso
    datos = informe.informe(con, hoy=date(2026, 10, 7), ahora=datetime(2026, 10, 7, 10, 0))
    assert datos["total"]["fichas"] == 5
    assert datos["total"]["vencidas"] == 1
    assert datos["total"]["en_curso"] >= 1


def test_las_edades_van_por_tramos_y_las_sin_fecha_aparte(con):
    inventario.alta(con, "dia", "reciente")
    inventario.terminar(con, ("dia", "reciente", "", ""), inventario.CORRECTO,
                        ahora=datetime(2026, 10, 1, 10, 0))
    inventario.alta(con, "dia", "vieja")
    inventario.terminar(con, ("dia", "vieja", "", ""), inventario.CORRECTO,
                        ahora=datetime(2025, 1, 1, 10, 0))
    inventario.alta(con, "dia", "nunca")
    datos = informe.informe(con, hoy=date(2026, 10, 7))
    assert datos["edades"]["menos de una semana"] == 1
    assert datos["edades"]["mas de un año"] == 1
    assert datos["edades"]["sin ficha"] == 1


def test_el_hash_cuenta_lo_que_tiene_contenido_util_registrado(con):
    """Cero con hash hoy es el resultado honesto, no un fallo del informe."""
    inventario.alta(con, "dia", "1")
    inventario.alta(con, "dia", "2")
    inventario.terminar(con, ("dia", "1", "", ""), inventario.CORRECTO, hash_util="abc")
    datos = informe.informe(con, hoy=date(2026, 10, 7))
    assert datos["total"]["con_hash"] == 1
    assert datos["total"]["con_ficha"] == 1
