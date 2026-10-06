"""El alcance dentro de los colectores: que no se pida lo que no es cesta.

Cada cadena enseña la categoria **antes** de pedir, y por eso se puede ahorrar la peticion. Este
fichero prueba las cuatro formas, con sus dos cautelas en todas: **solo se salta lo excluido**
(lo que hay que revisar se pide: ahi va media despensa) y **si el clasificador falla, se pide
igual** (una peticion de mas es barata; perder una rama de comida cuesta el dia).

Los nombres y las direcciones son reales del catalogo del 6 de octubre de 2026.
"""
from projects.cesta.collectors import alcampo, carrefour, dia, mercadona


# --- Alcampo: el nombre de su arbol de categorias ---------------------------------------------
def test_alcampo_no_pide_el_bazar():
    assert alcampo._fuera_de_alcance({"name": "Hogar y Decoración"}) is True
    assert alcampo._fuera_de_alcance({"name": "Juguetes"}) is True
    assert alcampo._fuera_de_alcance({"rama": "Hogar y Decoración", "name": "Textil hogar"}) is True


def test_alcampo_si_pide_la_comida_y_lo_dudoso():
    assert alcampo._fuera_de_alcance({"name": "Frescos"}) is False
    assert alcampo._fuera_de_alcance({"rama": "Frescos", "name": "Pescaderia"}) is False
    assert alcampo._fuera_de_alcance({"name": "Desayuno y Merienda"}) is False
    assert alcampo._fuera_de_alcance({}) is False


# --- Carrefour: la URL de la categoria ---------------------------------------------------------
def test_carrefour_no_pide_el_bazar():
    assert carrefour._fuera_de_alcance("hogar-y-decoracion/textil-hogar") is True
    assert carrefour._fuera_de_alcance("juguetes") is True


def test_carrefour_si_pide_la_comida():
    assert carrefour._fuera_de_alcance("drogueria-y-limpieza/detergentes") is False
    assert carrefour._fuera_de_alcance("congelados/masas") is False
    assert carrefour._fuera_de_alcance("") is False


# --- DIA: el pasillo, dentro de la URL del sitemap ---------------------------------------------
def test_dia_no_pide_el_bazar():
    assert dia._fuera_de_alcance("https://www.dia.es/compra-online/bazar-y-jardin/c/L100") is True
    assert dia._fuera_de_alcance("https://www.dia.es/compra-online/juguetes/c/L200") is True


def test_dia_si_pide_la_comida():
    """Nombres reales: `limpieza-y-hogar` es cesta (bolsas de basura, lejia) y no bazar."""
    assert dia._fuera_de_alcance("https://www.dia.es/compra-online/limpieza-y-hogar/c/L10") is False
    assert dia._fuera_de_alcance("https://www.dia.es/compra-online/verano/barbacoa/c/L20") is False
    assert dia._fuera_de_alcance("https://www.dia.es/carnes-y-pescados/c/L30") is False


def test_dia_ante_la_duda_pide():
    assert dia._fuera_de_alcance("") is False
    assert dia._fuera_de_alcance("no es una url") is False


# --- Mercadona: el nombre de su categoria de nivel 2 -------------------------------------------
def test_mercadona_no_pide_el_bazar():
    assert mercadona._fuera_de_alcance({"name": "Bazar y papelería"}) is True
    assert mercadona._fuera_de_alcance({"name": "Jardín y piscina"}) is True


def test_mercadona_si_pide_la_comida():
    assert mercadona._fuera_de_alcance({"name": "Bodega"}) is False
    assert mercadona._fuera_de_alcance({"name": "Cuidado del cabello"}) is False
    assert mercadona._fuera_de_alcance({"name": "Charcutería"}) is False


def test_mercadona_ante_la_duda_pide():
    assert mercadona._fuera_de_alcance({}) is False
    assert mercadona._fuera_de_alcance({"name": None}) is False
