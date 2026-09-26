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
from pathlib import Path
from unittest import mock

from projects.cesta.collectors import alcampo


def test_un_bajon_manda_al_buscador():
    """El caso del 25 de septiembre: el arbol no basto y hay que barrer."""
    assert alcampo.hay_que_barrer(0, 23_924, 28_977) is True


def test_la_referencia_es_el_mayor_de_la_semana_y_no_el_ultimo():
    """**El segundo fallo, el del 26 de septiembre de 2026.** Ese dia la condicion ya
    estaba arreglada y el barrido **volvio a no ejecutarse**: la referencia era el bronze
    mas reciente, que era el ya degradado de esa misma manana (23.932), asi que
    `filas < anterior * 0,95` era falso por construccion. Un catalogo degradado se
    convertia en la vara con la que medirse.

    Se mira el bronze de verdad de este arbol: la ultima captura BUENA tiene que ser la de
    28.977 (el 24 de septiembre), no la degradada de despues.
    """
    with mock.patch.object(alcampo.config, "DATA", Path("data").resolve()):
        anterior = alcampo._filas_ultimo_bronze()
    if anterior == 0:
        import pytest
        pytest.skip("no hay bronze de Alcampo en este arbol")
    assert anterior >= 28_000, (
        f"la ultima captura buena sale {anterior}: si ronda los 23.900, se esta mirando "
        f"la captura degradada y el barrido no se disparara")
    assert alcampo.hay_que_barrer(0, 23_932, anterior) is True


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


def test_con_los_repetidos_dentro_la_condicion_mentia():
    """**El tercer fallo, el del 26 de septiembre de 2026 por la tarde.**

    Al ejecutar el colector a mano para comprobar el barrido, no barría: la condición se
    evaluaba con `filas` **antes de quitar los repetidos**. La API de Alcampo devuelve el
    subárbol entero en cada categoría, así que el mismo producto sale en la rama y en la
    hoja: ese día fueron **28.783 filas crudas para 23.932 productos**, un 20 % de repetidos.

    Y contra una referencia de 28.977, `28.783 < 28.977 × 0,95` es falso. O sea que el
    barrido no se ejecutaba **con la captura dos días corta**, que es justo cuando hace
    falta: los repetidos hinchaban la cuenta hasta hacerla parecer sana.

    Las dos cuentas, con los mismos dos números del día:
    """
    filas_crudas, repetidos = alcampo._sin_repetidos(
        [{"id_fuente": str(i % 23_932)} for i in range(28_783)])
    assert len(filas_crudas) == 23_932
    assert repetidos == 4_851
    # La cuenta limpia dispara el barrido; la hinchada, no.
    assert alcampo.hay_que_barrer(0, len(filas_crudas), 28_977) is True
    assert alcampo.hay_que_barrer(0, 28_783, 28_977) is False


def test_los_repetidos_se_quedan_con_la_ultima_aparicion():
    """Es lo que hacía `unique(keep="last")` al guardar: la misma regla, no otra."""
    filas, repetidos = alcampo._sin_repetidos([
        {"id_fuente": "1", "nombre": "viejo"},
        {"id_fuente": "2", "nombre": "solo"},
        {"id_fuente": "1", "nombre": "nuevo"},
    ])
    assert repetidos == 1
    assert {f["id_fuente"]: f["nombre"] for f in filas} == {"1": "nuevo", "2": "solo"}


def test_una_fila_sin_identificador_no_cuenta_como_producto():
    """Sin `id_fuente` no hay URL ni ficha: no es un producto, es un resto."""
    filas, repetidos = alcampo._sin_repetidos([{"id_fuente": None}, {"id_fuente": "7"}])
    assert [f["id_fuente"] for f in filas] == ["7"]
    assert repetidos == 1


def test_un_termino_con_forma_rara_no_tumba_el_barrido_ni_la_captura():
    """**El cuarto fallo, y el peor de los cuatro, medido el 26 de septiembre de 2026.**

    Con el barrido ya disparándose, el primer término de los 600 trajo una respuesta con
    `data` en texto y `productos_de_busqueda` reventó con
    `'str' object has no attribute 'get'`. Y como aquel `except` hacía `errores += 1` y
    `detener = True`, la pasada entera terminó diciendo **"es una captura rota" y no guardó
    nada**: un término raro de una fase *extra* decidía el destino del catálogo del día.

    Ahora una respuesta sin forma de búsqueda son cero productos y el barrido sigue con el
    término siguiente; lo único que corta el barrido entero es el WAF.
    """
    f = mock.Mock()
    casos = [
        ({"data": "texto en vez de un diccionario"}, []),
        ({"data": {"products": "texto"}}, []),
        ({"data": {"products": {"productEntities": "texto"}}}, []),
        ({"data": {}}, []),
        ({"data": {"products": {"productEntities": {
            "1": {"name": "Leche"}, "2": "no es un producto"}}}}, [{"name": "Leche"}]),
    ]
    for estado, esperado in casos:
        with mock.patch.object(alcampo, "_estado", return_value=estado):
            assert alcampo.productos_de_busqueda(f, "leche") == esperado, estado


def test_una_pagina_sin_estado_en_la_busqueda_es_un_corte_del_waf():
    """Si no hay estado que leer no es «esta búsqueda no tiene resultados»: es que la página
    no llegó entera, y eso el barrido tiene que tratarlo como un corte."""
    import pytest

    f = mock.Mock()
    with mock.patch.object(alcampo, "_estado", return_value="una cadena"):
        with pytest.raises(alcampo.RetoWAF):
            alcampo.productos_de_busqueda(f, "leche")


def test_el_barrido_tiene_presupuesto_de_tiempo():
    """A una peticion cada 6,7 s, los 600 terminos del turno son casi 67 minutos, mas que
    el recorrido entero. Se recorre lo que quepa y se dice cuanto quedo."""
    fuente = (alcampo.__file__)
    with open(fuente, encoding="utf-8") as f:
        codigo = f.read()
    assert "PRESUPUESTO_BARRIDO_S" in codigo and "agotado = True" in codigo, (
        "el barrido se ha quedado sin presupuesto de tiempo: puede doblar la tarea")
    assert "hay_que_barrer" in codigo, "la condicion del barrido tiene que ser una funcion"
