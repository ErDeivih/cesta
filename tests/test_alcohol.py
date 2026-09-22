"""Si un producto lleva alcohol.

Solo Alcampo y Mercadona lo declaran (1.589 y 223 productos); las otras tres
cadenas, nada. Un filtro "sin alcohol" que fallara en tres de cinco devolveria
vino a quien no bebe, asi que se deduce del nombre y de la categoria.

La asimetria que lo hace seguro: es un filtro de EXCLUSION. Pasarse solo es
molesto (desaparece un vinagre de Jerez); quedarse corto es lo peligroso. Al
contrario que "sin gluten", que es de inclusion y ahi pasarse es lo grave.
"""
from core.alcohol import deduce


def test_las_bebidas_obvias():
    for x in ("Cerveza Mahou 33 cl", "Vino tinto crianza Rioja", "Ron Barceló añejo",
              "Ginebra Larios 1 l", "Whisky escocés", "Vodka Absolut",
              "Sidra natural asturiana", "Cava brut nature", "Vermut rojo"):
        assert deduce(x) is True, x


def test_lo_que_dice_que_no_lleva_no_lleva():
    for x in ("Cerveza 0,0% sin alcohol", "Cerveza sin alcohol tostada",
              "Vino blanco desalcoholizado", "Cerveza triple zero",
              "Tinto de verano 0,0% limón"):
        assert deduce(x) is False, x


def test_champu_no_es_champan():
    """El fallo que costo veinte puntos de precision.

    La primera version buscaba "champ" y **champu** empieza igual, asi que
    marcaba como alcohol todos los champus anticaspa del catalogo. Es el mismo
    error que "eco" dentro de "seco" en core/sellos.py, cometido el mismo dia.
    """
    for x in ("H&S Citrus fresh Champú anticaspa de uso diario",
              "PANTENE Nutri-plex Champú con antioxidantes",
              "Champú Argan Oil Deliplus cabello seco"):
        assert deduce(x) is False, x


def test_la_comida_que_se_llama_como_una_bebida():
    for x in ("Vinagre de Jerez al Pedro Ximénez", "Carrilladas de cerdo al vino dulce",
              "Cóctel de frutos secos", "Aceite de orujo de oliva",
              "Mejillones en escabeche", "Hielo cóctel"):
        assert deduce(x) is False, x


def test_la_categoria_basta_cuando_el_nombre_no_dice_nada():
    assert deduce("Selección del sumiller", "bebidas-alcoholicas/vinos") is True
    assert deduce("Selección del sumiller", "lacteos-huevos") is False


def test_el_grado_manda_sobre_todo():
    # Si Mercadona publica el grado, es el dato mas fuerte que hay.
    assert deduce("Bebida de malta", None, 4.8) is True
    assert deduce("Cerveza artesana", None, 0.0) is False


def test_sin_nombre_no_se_inventa():
    assert deduce(None) is False
    assert deduce("") is False
