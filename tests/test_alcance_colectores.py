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
from core import cobertura
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


def test_el_producto_se_clasifica_otra_vez_antes_de_bronze():
    """Lo pide el contrato: saltar la rama no basta, hay que mirar el producto.

    Se mira el codigo porque aqui no hay red ni captura que hacer: lo que se fija es que la
    ultima puerta **existe**, que usa la misma funcion que el control de cobertura (para que
    colector y control no puedan discrepar) y que va **antes** de escribir bronze.
    """
    from pathlib import Path

    fuente = Path("projects/cesta/collectors/alcampo.py").read_text(encoding="utf-8")
    assert "cobertura.solo_cesta_familiar(df)" in fuente, (
        "la captura se guarda sin clasificar el producto: una categoria mixta cuela bazar")
    assert (fuente.index("solo_cesta_familiar(df)")
            < fuente.index('write_parquet(df, "bronze", FUENTE)')), (
        "el filtro tiene que ir ANTES de escribir bronze")


def test_el_filtro_quita_bazar_y_deja_lo_que_hay_que_revisar():
    """La mitad que importa: no se lleva por delante la comida pendiente de clasificar."""
    import polars as pl

    marco = pl.DataFrame({
        "nombre": ["Funda elastica para sofa", "Pimientos tricolor", "Aceite de oliva 1 l"],
        "categoria": ["Hogar y Decoracion > Textil hogar", "Frescos > Verduras",
                      "Desayuno y Merienda > Aceites"],
    })
    quedan = cobertura.solo_cesta_familiar(marco)
    assert quedan.height == 2, "tiene que quedarse la comida, incluida la que hay que revisar"
    assert "Funda" not in quedan["nombre"].to_list()
