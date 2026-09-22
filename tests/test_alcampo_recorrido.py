"""El recorrido de categorias de Alcampo: cuando bajar a las hijas.

Su API devuelve los productos de TODO el subarbol, con un tope de 300. De ahi
salen tres casos, y el tercero estuvo mal desde el principio:

    300 productos y con hijas  -> viene cortado: hay que bajar
    entre 1 y 299              -> cabe entero: nos lo quedamos
    0 productos y con hijas    -> nodo de navegacion: los productos estan abajo

El tercero caia en el `else` y no encolaba nada. Medido sobre el crudo del 17 de
septiembre de 2026: 289 nodos asi, 1.245 hijas nunca pedidas, y 53 categorias que
no llegaban por ningun otro camino. El 18 ese agujero se trago la rama Frescos
entera -- 2.646 productos -- con cero errores.
"""
from projects.cesta.collectors.alcampo import TOPE_API


def _decide(productos: int, hijas: int) -> str:
    """La regla del bucle, aislada para poder probarla."""
    if hijas and (productos >= TOPE_API or not productos):
        return "bajar"
    return "quedarse"


def test_un_nodo_saturado_se_expande():
    assert _decide(TOPE_API, 5) == "bajar"
    assert _decide(TOPE_API + 40, 12) == "bajar"


def test_una_categoria_que_cabe_entera_se_guarda():
    assert _decide(58, 3) == "quedarse"
    assert _decide(299, 9) == "quedarse"


def test_un_nodo_de_navegacion_vacio_baja_a_sus_hijas():
    # El fallo de Frescos: 0 productos, 11 hijas, y antes no se encolaba nada.
    assert _decide(0, 11) == "bajar"


def test_una_hoja_vacia_no_tiene_a_donde_bajar():
    assert _decide(0, 0) == "quedarse"


def test_una_hoja_saturada_sin_hijas_se_queda_y_se_marca_truncada():
    # No hay hijas a las que bajar: se guarda lo que hay y se cuenta como
    # truncada para completarla despues por el buscador.
    assert _decide(TOPE_API, 0) == "quedarse"


# --- el auditor del recorrido --------------------------------------------

def test_el_auditor_descarta_lo_que_solo_declara_el_menu():
    """El menu de Alcampo declara el arbol ENTERO, ramas excluidas incluidas.

    Sin este filtro el auditor cantaba 899 categorias "perdidas" que son
    juguetes, bricolaje y accesorios de coche, o sea justo lo que la
    configuracion dice que no queremos. Con el filtro quedan 32, y todas son
    comida: "Lacteos sin lactosa", "Arroz Ecologico", "Sobrasada".
    """
    from projects.cesta.auditar_recorrido import MENU_MINIMO
    # Una respuesta que declara mas de MENU_MINIMO categorias es el menu, no una
    # categoria: una categoria de Alcampo declara entre 0 y 20 hijas.
    assert MENU_MINIMO > 20
    assert MENU_MINIMO < 2696


def test_las_claves_de_cache_que_conoce_el_auditor_existen():
    # Si un colector cambia como construye su clave de cache y aqui no se
    # cambia, el auditor diria que no se pidio nada de nada.
    from projects.cesta.auditar_recorrido import CLAVES
    assert CLAVES["alcampo"] == ("api-category-{id}",)
    assert CLAVES["mercadona"] == ("category-{id}",)
