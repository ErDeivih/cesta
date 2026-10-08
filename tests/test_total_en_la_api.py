"""El total que se enseña suma solo lo autorizado, y lo que se queda fuera se dice.

Se lee el codigo, como en las demas pruebas de contrato del proyecto, porque aqui el fallo no da error:
un total que suma de mas da un numero creible y equivocado, que es lo peor que puede dar.
"""
from __future__ import annotations

from pathlib import Path

from plataforma.api import cesta


def _fuente() -> str:
    return Path(cesta.__file__).read_text(encoding="utf-8")


def test_el_total_de_la_cadena_suma_solo_lo_autorizado():
    fuente = _fuente()
    assert 'total["total_cent"]' in fuente, "el total tiene que salir de _total_autorizado"
    assert "sum(e.coste_cent for e in tiene)" not in fuente, \
        "volvio a sumarse todo lo resuelto, incluido lo no autorizado"


def test_lo_que_no_cuenta_se_expone_con_su_motivo():
    fuente = _fuente()
    assert '"pendientes": total["pendientes"]' in fuente, \
        "sin pendientes, la pantalla no puede ofrecer las alternativas linea a linea"
    assert '"sin_autorizar": len(total["pendientes"])' in fuente


def test_una_cadena_que_no_autoriza_no_puede_ordenarse_como_completa():
    """Ordenar solo por `faltan` colocaba delante una cadena que resuelve pero no autoriza nada."""
    fuente = _fuente()
    assert 'key=lambda x: (len(x["faltan"]), x["sin_autorizar"], x["total_cent"])' in fuente


def test_el_total_sigue_siendo_la_suma_de_lo_que_cuenta():
    """La regla en si, probada con elecciones de verdad: una cuenta y otra no."""
    cuenta = cesta.Eleccion("p1", "Leche", "dia", 1, 199, 199, None, None,
                            autorizada=True)
    no_cuenta = cesta.Eleccion("p2", "Otra leche", "dia", 1, 149, 149, None, None,
                               identidad="alternativa", motivo="GTIN distinto", autorizada=False)
    total = cesta._total_autorizado([cuenta, no_cuenta])
    assert total["total_cent"] == 199, "los 149 no pueden entrar en el total"
    assert total["completo"] is False and len(total["pendientes"]) == 1
