"""El crudo viejo se tira solo. Si no, el disco se llena y la ejecucion falla.

Medido el 7 sep: 338 MB de crudo por pasada, 123 GB al ano sobre 158 GB libres.
El fallo llegaria de madrugada, sin nadie mirando, y no se notaria hasta que
faltaran precios de una semana.
"""
from datetime import timedelta
from unittest import mock

from core import config
from projects.cesta import limpiar


def _crudo(tmp_path, *fechas):
    for i, fecha in enumerate(fechas):
        d = tmp_path / "raw" / f"fuente=cadena{i % 2}" / f"fecha={fecha}"
        d.mkdir(parents=True)
        (d / "algo.json.gz").write_bytes(b"x" * 100)
    return tmp_path


def test_borra_lo_viejo_y_respeta_lo_reciente(tmp_path):
    hoy = config.hoy_local()
    viejo = (hoy - timedelta(days=40)).isoformat()
    reciente = (hoy - timedelta(days=3)).isoformat()
    _crudo(tmp_path, viejo, reciente)
    with mock.patch.object(config, "DATA", tmp_path):
        viejas = limpiar.carpetas_caducadas(30)
    assert [c.name for c in viejas] == [f"fecha={viejo}"]


def test_con_cero_dias_no_se_borra_nada(tmp_path):
    _crudo(tmp_path, "2020-01-01")
    with mock.patch.object(config, "DATA", tmp_path):
        assert limpiar.carpetas_caducadas(0) == []
        assert limpiar.carpetas_caducadas(-5) == []


def test_una_carpeta_con_nombre_raro_no_se_toca(tmp_path):
    (tmp_path / "raw" / "fuente=x" / "fecha=basura").mkdir(parents=True)
    with mock.patch.object(config, "DATA", tmp_path):
        assert limpiar.carpetas_caducadas(30) == []


def test_el_ensayo_no_borra(tmp_path):
    viejo = (config.hoy_local() - timedelta(days=99)).isoformat()
    _crudo(tmp_path, viejo)
    with mock.patch.object(config, "DATA", tmp_path):
        limpiar.main(["--ensayo"])
        assert (tmp_path / "raw" / "fuente=cadena0" / f"fecha={viejo}").exists()
        limpiar.main([])
        assert not (tmp_path / "raw" / "fuente=cadena0" / f"fecha={viejo}").exists()
