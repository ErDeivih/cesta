import pytest

from core.alcance import clasificar_alcance


@pytest.mark.parametrize("nombre", ["Fiambrera de cristal", "Vasos reutilizables",
                                    "Botella reutilizable 1 l", "Bolsa reutilizable"])
def test_reutilizable_cotidiano_autorizado(nombre):
    d = clasificar_alcance(nombre, "Hogar y Decoracion > Menaje")
    assert d.estado == "incluido"
    assert d.familia_id == "hogar_reutilizable"


def test_no_reabre_todo_el_bazar():
    assert clasificar_alcance("Televisor 55 pulgadas", "Electrodomesticos").estado == "excluido"
