"""Las ofertas se eligen por la fecha de referencia, no por la ultima que haya en disco.

Lo que se fija: que `fecha_tope` **corte** -- una particion posterior no se usa -- y que los cuatro
endpoints de la cesta pasen una fecha de verdad y no cadena vacia, que era el parametro decorativo.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from plataforma.api import cesta


@pytest.fixture
def silver(tmp_path, monkeypatch):
    """Un silver de mentira con dos dias: el 1 y el 5."""
    for fecha, fuente in (("2026-10-01", "dia"), ("2026-10-05", "dia")):
        (tmp_path / "silver" / f"fuente={fuente}" / f"fecha={fecha}").mkdir(parents=True)
    monkeypatch.setattr(cesta, "AJUSTES", SimpleNamespace(gold=tmp_path / "gold"))
    return tmp_path


def test_sin_tope_se_elige_la_ultima(silver):
    assert cesta._ultima_fecha_silver() == "2026-10-05"


def test_con_tope_no_se_elige_una_particion_posterior(silver):
    """Es lo que impide aplicar una oferta que todavia no estaba vigente."""
    assert cesta._ultima_fecha_silver("2026-10-03") == "2026-10-01"
    assert cesta._ultima_fecha_silver("2026-10-05") == "2026-10-05"
    assert cesta._ultima_fecha_silver("2026-09-30") is None, "antes del primer dia no hay nada"


def test_los_cuatro_endpoints_pasan_una_fecha_de_verdad():
    """El fallo original: los cuatro llamantes pasaban cadena vacia."""
    fuente = (cesta.__file__ and __import__("pathlib").Path(cesta.__file__).read_text(
        encoding="utf-8")) or ""
    assert '_candidatos(peticiones, "")' not in fuente, "quedan llamantes con cadena vacia"
    assert fuente.count("_candidatos(peticiones, _fecha_de_hoy())") == 4
