"""A09, parte del 3x2 — **el descuento de cesta, dividido entre las lineas sin perder un centimo**.

**Lo que pide el encargo**, de F01: *«producto A solicitado, alternativa B aceptada, tres unidades y
promocion 3x2; comprobar identidad, tienda, cantidad e importe desde estimacion hasta historico».*

*De esas cinco cosas, esta prueba cubre **el importe con promocion**:* **que el descuento que se le
concede a la cesta acabe repartido entre sus lineas, y que la suma cuadre exactamente.**

**Por que el reparto tiene su propia regla y no una division sin mas.** *120 centimos entre tres lineas
que aportan lo mismo son 40 cada una, y no hay problema.* **Pero 100 centimos entre tres dan 33,33...**, y
*una aplicacion que redondee a la ligera pierde un centimo por el camino* -- *y el centimo que se pierde
es el que hace que el total de la lista no cuadre con el ticket, que es la primera cosa que alguien
comprueba.*

**El contrato, leido de su docstring y fijado aqui entero:**
  - *se reparte **en proporcion a lo que aporta cada linea**;*
  - *el **resto** de la division se le da a las de **mayor importe**;*
  - *y a igualdad de importe, por `id`, **para que sea determinista**;*
  - *y **la suma tiene que dar el descuento entero**.*
"""
from __future__ import annotations

import pytest

from core.cesta_umbral import LineaDeCesta, descuento_de_cesta, reparto_del_descuento


def ln(id_: str, unidades: int, precio_cent: int) -> LineaDeCesta:
    return LineaDeCesta(id=id_, unidades=unidades, precio_cent=precio_cent)


# ================================================== la invariante que no se negocia ===

@pytest.mark.parametrize("descuento", [1, 2, 3, 7, 99, 100, 101, 333, 1000])
def test_la_suma_del_reparto_da_el_descuento_entero(descuento):
    """**La invariante, y es la unica que no se negocia**: *la suma de lo repartido es **exactamente** el
    descuento.*

    *Ni un centimo de mas -- seria regalar dinero -- ni uno de menos -- seria perderlo.* **Y se prueba con
    descuentos que NO son divisibles a proposito**: *100 entre 3 da 33,33, y ahi es donde se pierde el
    centimo.*
    """
    lineas = [ln("a", 1, 100), ln("b", 1, 100), ln("c", 1, 100)]
    reparto = reparto_del_descuento(lineas, descuento)
    assert sum(reparto.values()) == descuento, (
        f"el reparto pierde o regala centimos: {reparto} suma {sum(reparto.values())}, "
        f"y el descuento es {descuento}")


def test_el_reparto_es_proporcional_a_lo_que_aporta_cada_linea():
    """*La linea que vale el doble recibe el doble.* **No a partes iguales.**

    *Repartir a partes iguales seria mas facil y estaria mal*: **una linea de 2 centimos y otra de 200
    no pueden llevarse lo mismo**, porque el descuento es una proporcion de lo que cada una aporta.
    """
    lineas = [ln("caro", 1, 200), ln("barato", 1, 100)]
    reparto = reparto_del_descuento(lineas, 300)
    assert reparto["caro"] == 200, reparto
    assert reparto["barato"] == 100, reparto
    # *Y la proporcion se mantiene con un descuento parcial.*
    reparto2 = reparto_del_descuento(lineas, 150)
    assert reparto2["caro"] == 100 and reparto2["barato"] == 50, reparto2


def test_tres_unidades_al_precio_de_dos_se_reparten_entre_sus_lineas():
    """**El 3x2, en su forma mas simple**: *tres unidades que valen 100 cada una, y se perdona una.*

    *Seleccionadas como lineas distintas -- que es lo que pasa de verdad cuando son productos distintos de
    la misma promocion* --, **el descuento se reparte entre las tres sin perder nada.**
    """
    lineas = [ln("u1", 1, 100), ln("u2", 1, 100), ln("u3", 1, 100)]
    reparto = reparto_del_descuento(lineas, 100)
    assert sum(reparto.values()) == 100
    # *Y al aportar lo mismo, el centimo que sobra no puede ser siempre de la misma*: **el desempate por
    # `id` hace que sea determinista, no que sea injusto** -- *y hay que decir cual es, no suponerlo.*
    assert sorted(reparto.values(), reverse=True)[0] - sorted(reparto.values())[0] <= 1, reparto
    # *Y tres lineas iguales con 100 de descuento: 34, 33, 33 -- el resto va a la primera por `id`.*
    assert reparto == {"u1": 34, "u2": 33, "u3": 33}, reparto


def test_el_reparto_es_determinista_a_igualdad_de_importe():
    """**Y esto se prueba llamando dos veces**, que es la unica forma de saberlo.

    *Si el reparto dependiera del orden en que llegan las lineas*, dos peticiones iguales darian totales
    distintos por linea y **el mismo total** -- *que es el peor de los fallos: parece que funciona.*
    *El desempate por `id` es lo que lo evita, y aqui queda fijado.*
    """
    lineas = [ln("b", 1, 100), ln("a", 1, 100), ln("c", 1, 100)]
    primero = reparto_del_descuento(lineas, 100)
    segundo = reparto_del_descuento(list(reversed(lineas)), 100)
    assert primero == segundo, f"el reparto cambia segun el orden: {primero} contra {segundo}"


def test_nunca_se_reparte_mas_de_lo_que_vale_una_linea():
    """*Y el limite que impide un absurdo*: **a una linea no se le puede descontar mas de lo que cuesta.**

    *El reparto es proporcional, asi que no deberia pasar* -- **pero eso es un argumento, no una
    comprobacion**, y una linea con descuento negativo o mayor que su importe haria que la lista cuadrara
    por casualidad y el ticket no.
    """
    lineas = [ln("a", 1, 10), ln("b", 1, 1000)]
    reparto = reparto_del_descuento(lineas, 1010)
    for linea in lineas:
        suyo = reparto[linea.id]
        importe = linea.unidades * linea.precio_cent
        assert 0 <= suyo <= importe, (
            f"a {linea.id} se le descuenta {suyo} y vale {importe}")


def test_un_descuento_de_cero_o_negativo_no_reparte_nada():
    """*Y sin descuento no hay nada que repartir.* **Cero para todas, y no un diccionario vacio** -- *la
    pantalla espera una entrada por linea.*"""
    lineas = [ln("a", 1, 100), ln("b", 1, 100)]
    assert reparto_del_descuento(lineas, 0) == {"a": 0, "b": 0}
    assert reparto_del_descuento(lineas, -50) == {"a": 0, "b": 0}


def test_sin_lineas_no_hay_reparto_y_no_revienta():
    """**Cero lineas y un descuento mayor que cero** *no puede dividir por cero.*"""
    assert reparto_del_descuento([], 500) == {}


def test_una_cesta_que_vale_cero_no_reparte_nada():
    """*Y si el importe total es cero, no hay proporcion que aplicar.* **Cero, sin dividir por cero.**"""
    lineas = [ln("a", 0, 100), ln("b", 1, 0)]
    assert reparto_del_descuento(lineas, 500) == {"a": 0, "b": 0}


# ============================================ el descuento de la cesta, que es la fuente ===
#
# **Y aqui conviene decir algo, para no apuntarme lo que ya estaba**: `descuento_de_cesta` YA tiene
# pruebas en `tests/test_g11_oraculo.py` -- el tope de que nunca sea mayor que la cesta, y el caso de no
# llegar al umbral. *Las de abajo no las sustituyen: comprueban la otra mitad del recorrido* -- **que lo
# que la cesta descuenta acabe cuadrando con lo que se reparte entre sus lineas**, *que es donde el
# 3x2 se puede perder un centimo.*

def test_el_umbral_se_comprueba_contra_lo_que_se_compra():
    """**«5 EUR dto comprando 20 EUR»**: *el umbral se mide contra el importe de las lineas.*

    *El formato no es el que uno escribria* -- *yo puse «Compra 20 EUR y te descontamos 5 EUR» y
    `descuento_de_cesta` devolvio cero las cuatro veces*, **sin fallar**: *un texto que no reconoce no es
    un error, es una promocion que no aplica.* **Y el formato de verdad se leyo de
    `tests/test_g11_oraculo.py`, que ya lo usaba** -- *sexta vez en tres rondas que asumir me cuesta una
    corrida.*

    *Y el descuento no se aplica a cada linea por separado*: **es de la cesta entera**, y por eso hay que
    repartirlo despues.
    """
    lineas = [ln("a", 2, 1000)]  # *2 x 10 EUR = 20 EUR*
    assert descuento_de_cesta(lineas, ["5 EUR dto comprando 20 EUR"]) == 500
    # *Y por debajo del umbral, cero.*
    assert descuento_de_cesta([ln("a", 1, 1000)], ["5 EUR dto comprando 20 EUR"]) == 0


def test_un_descuento_no_puede_ser_mayor_que_la_cesta():
    """**«Nunca mas que la cesta: un descuento mayor que el importe no significa que te paguen.»**
    *Es la linea que su propio codigo documenta, y conviene que este fijada.*"""
    lineas = [ln("a", 1, 100)]  # *1 EUR*
    # *Un tramo de 1 EUR que devuelve 5 por tramo.*
    assert descuento_de_cesta(lineas, ["5 EUR dto comprando 1 EUR"]) == 100


def test_el_umbral_no_se_cuenta_dos_veces_con_la_misma_mecanica():
    """*Y el tramo se cuenta **entero**, no una vez por pasarse.* **30 EUR con tramo de 20 dan un tramo,
    no dos** -- *y 40 dan dos, que es lo que «por cada 20» significa.*"""
    textos = ["5 EUR dto comprando 20 EUR"]
    assert descuento_de_cesta([ln("a", 3, 1000)], textos) == 500, "30 EUR: un tramo"
    assert descuento_de_cesta([ln("a", 4, 1000)], textos) == 1000, "40 EUR: dos tramos"


def test_lo_repartido_siempre_cuadra_con_el_descuento_de_la_cesta():
    """**La prueba que junta las dos mitades**, que es lo que el recorrido hace de verdad: *se calcula el
    descuento de la cesta y se reparte entre sus lineas.*

    *Y la invariante se comprueba al final, sobre el caso completo*: **lo que se le quita a la cesta es
    exactamente lo que se reparte entre las lineas.** *Si esto no cuadrara, el total de la pantalla y el
    ticket dirian cosas distintas.*
    """
    # *3x0,95 + 2x1,30 + 1x2,49 = 7,94 EUR, y el umbral es de 10: **no llegaba**.*
    # **Lo cazo la propia asercion de abajo** -- «o la prueba no mide nada» --, que es para lo que
    # estaba escrita.* *Una prueba que pasa sin llegar al umbral no prueba el descuento: prueba que
    # no hay descuento.*
    lineas = [ln("leche", 3, 195), ln("pan", 4, 130), ln("huevos", 1, 249)]  # *10,54 EUR*
    textos = ["2 EUR dto comprando 10 EUR"]
    descuento = descuento_de_cesta(lineas, textos)
    reparto = reparto_del_descuento(lineas, descuento)

    assert descuento > 0, "el caso tiene que llegar al umbral, o la prueba no mide nada"
    assert sum(reparto.values()) == descuento, f"no cuadra: {reparto} contra {descuento}"
    for linea in lineas:
        assert 0 <= reparto[linea.id] <= linea.unidades * linea.precio_cent
