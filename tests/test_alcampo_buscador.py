"""El barrido del buscador de Alcampo: cuando toca y por que.

El 25 de septiembre de 2026 la captura de Alcampo se quedo en **23.924 productos contra
28.977** del dia anterior (un 17,5 % menos) y el barrido del buscador -- que es el
segundo camino de descubrimiento, el que tapa justo ese agujero -- **no llego a correr**.

La condicion era `if truncadas and not detener`, o sea que hiciera falta que una categoria
**hoja** tocara el tope de 300 productos. Medido en el crudo de tres dias seguidos:

    2026-09-23   respuestas 421   al tope  29   hojas al tope  0
    2026-09-24   respuestas 543   al tope  44   hojas al tope  0
    2026-09-25   respuestas 410   al tope  28   hojas al tope  0

Cero, cero y cero: una categoria con 300 productos casi siempre tiene hijas, y entonces no
es hoja. La guarda no era una guarda, era una puerta cerrada.
"""
from projects.cesta.collectors import alcampo


def test_un_bajon_manda_al_buscador():
    """El caso del 25 de septiembre: el arbol no basto y hay que barrer."""
    assert alcampo.hay_que_barrer(0, 23_924, 28_977) is True


def test_una_captura_normal_no_dispara_el_barrido():
    """Barrer cuesta casi 67 minutos de reloj (600 terminos a una peticion cada 6,7 s):
    no se hace porque si, se hace cuando la captura se ha quedado corta."""
    assert alcampo.hay_que_barrer(0, 29_000, 28_977) is False
    assert alcampo.hay_que_barrer(0, 28_977, 28_977) is False


def test_una_hoja_al_tope_sigue_mandando_al_buscador():
    """Lo de antes no se quita: cuando pasa, sigue valiendo."""
    assert alcampo.hay_que_barrer(3, 29_000, 28_977) is True


def test_sin_ultima_captura_no_se_barre():
    """La primera vez no hay con que comparar: recorrer 600 terminos por si acaso, en la
    primera pasada, es gastar la noche sin saber si hace falta."""
    assert alcampo.hay_que_barrer(0, 100, None) is False
    assert alcampo.hay_que_barrer(0, 100, 0) is False


def test_el_margen_tiene_un_valor_razonable():
    """El margen es la frontera entre «un dia normal» y «ha faltado algo»: por debajo del
    1 % seria ruido del catalogo (hay dias que entran y salen productos), y por encima del
    20 % se dejarian pasar bajones de verdad como el del 17,5 %."""
    assert 0.01 <= alcampo.MARGEN_BAJON <= 0.20
    assert alcampo.PRESUPUESTO_BARRIDO_S <= 3600, (
        "el barrido no puede durar mas que la tarea entera: se recorta y se dice cuanto "
        "quedo")


def test_el_barrido_tiene_presupuesto_de_tiempo():
    """A una peticion cada 6,7 s, los 600 terminos del turno son casi 67 minutos, mas que
    el recorrido entero. Se recorre lo que quepa y se dice cuanto quedo."""
    fuente = (alcampo.__file__)
    with open(fuente, encoding="utf-8") as f:
        codigo = f.read()
    assert "PRESUPUESTO_BARRIDO_S" in codigo and "agotado = True" in codigo, (
        "el barrido se ha quedado sin presupuesto de tiempo: puede doblar la tarea")
    assert "hay_que_barrer" in codigo, "la condicion del barrido tiene que ser una funcion"
