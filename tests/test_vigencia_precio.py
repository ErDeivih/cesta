"""La fecha del precio tiene que pertenecer a la publicacion de su catalogo.

Se prueba la regla con texto, que es lo que permite tenerla sin base ni ficheros, y se comprueba que el
endpoint la manda.
"""
from __future__ import annotations

from pathlib import Path

from plataforma.api import main


def test_un_precio_del_mismo_dia_que_la_publicacion_es_coherente():
    v = main._vigencia("2026-10-07", "2026-10-07T16:15:18.911126")
    assert v["comprobable"] is True and v["coherente"] is True


def test_un_precio_anterior_a_la_publicacion_tambien():
    """El catalogo recoge el historico: precios de dias antes son lo normal."""
    v = main._vigencia("2026-10-05", "2026-10-07T16:15:18")
    assert v["coherente"] is True


def test_un_precio_posterior_a_la_publicacion_no_pertenece_a_ese_catalogo():
    """El caso que importa: un precio del dia 8 no puede venir de un catalogo publicado el 7."""
    v = main._vigencia("2026-10-08", "2026-10-07T16:15:18")
    assert v["comprobable"] is True and v["coherente"] is False
    assert "POSTERIOR" in v["motivo"]


def test_sin_datos_no_se_afirma_nada():
    """Sin fecha de publicacion no se dice que si ni que no: se dice que no se puede comprobar."""
    v = main._vigencia("2026-10-07", "")
    assert v["comprobable"] is False and "coherente" not in v


def test_el_estado_manda_la_vigencia_del_precio():
    fuente = Path(main.__file__).read_text(encoding="utf-8")
    assert '"vigencia_precio": _vigencia_del_catalogo()' in fuente
    assert "def _vigencia(" in fuente, "la regla tiene que ser una funcion aparte y probable"
