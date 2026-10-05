"""El alcance dentro de los colectores (T01): que no se pida lo que no es cesta.

Dos formas de saberlo, segun lo que cada cadena enseñe **antes** de pedir:

  - Alcampo da un arbol de categorias con nombre (`{"name": "Hogar y Decoracion"}`), y su colector
    salta la rama entera.
  - Carrefour lleva la categoria en la URL (`supermercado/<slug>/<catId>/c`), asi que puede
    saltarla antes de pedir el listado, que es donde esta el ahorro.

En las dos, la regla es la misma y tiene dos cautelas que se prueban aqui: **solo se salta lo
excluido** (lo que hay que revisar se pide: media despensa de Alcampo sale en `revisar`), y **si el
clasificador falla se pide igual** (una peticion de mas es barata; perder una captura cuesta el
dia).
"""
from projects.cesta.collectors import alcampo, carrefour


def test_alcampo_no_pide_el_bazar():
    assert alcampo._fuera_de_alcance({"name": "Hogar y Decoración"}) is True
    assert alcampo._fuera_de_alcance({"name": "Juguetes"}) is True
    assert alcampo._fuera_de_alcance({"rama": "Hogar y Decoración", "name": "Textil hogar"}) is True


def test_alcampo_si_pide_la_comida_y_lo_dudoso():
    assert alcampo._fuera_de_alcance({"name": "Frescos"}) is False
    assert alcampo._fuera_de_alcance({"rama": "Frescos", "name": "Pescaderia"}) is False
    assert alcampo._fuera_de_alcance({"name": "Desayuno y Merienda"}) is False
    assert alcampo._fuera_de_alcance({}) is False


def test_carrefour_no_pide_el_bazar():
    assert carrefour._fuera_de_alcance("hogar-y-decoracion/textil-hogar") is True
    assert carrefour._fuera_de_alcance("juguetes") is True
    assert carrefour._fuera_de_alcance("moda-infantil/ropa") is True


def test_carrefour_si_pide_la_comida_y_lo_dudoso():
    assert carrefour._fuera_de_alcance("drogueria-y-limpieza/detergentes") is False
    assert carrefour._fuera_de_alcance("cuidado-personal-e-higiene/higiene-bucal") is False
    assert carrefour._fuera_de_alcance("congelados/masas") is False
    assert carrefour._fuera_de_alcance("") is False
