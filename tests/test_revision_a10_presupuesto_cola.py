"""El presupuesto de la cola: **cuántas noches son 72 319 fichas, y quién se las lleva.**

**Lo que estas pruebas fijan.**

 1. **El ritmo es peticiones por segundo, y va en el denominador.** *Confundirlo con segundos por petición
    da un número **plausible y equivocado**, que es la peor clase de error* -- *y sale un factor de 44 en
    Alcampo.*
 2. **Alcampo se lleva el 91,7 % del tiempo.** *Eso no es un detalle del informe: **es el informe**.*
 3. **Sin decir cuántas horas tiene una noche, no se contestan las noches.** *Suponer ocho sería
    inventarse el contexto.*
 4. **Un ritmo de cero no termina nunca**, y `inf` lo dice *en vez de reventar con una división.*

*Las cifras de fichas son las medidas el 13 de octubre de 2026 en `data/inventario.sqlite`.*
"""
from __future__ import annotations

import math

import pytest

from core import config
from core.presupuesto import Tramo, cuello_de_botella, presupuesto

# *Las 72 319 pendientes, por cadena, medidas.*
COLA = {"alcampo": 43603, "carrefour": 17280, "lidl": 5026, "aldi": 3206, "dia": 1637, "mercadona": 1567}


def _tramos():
    return [Tramo(c, n, config.RITMO[c]) for c, n in COLA.items()]


# ================================================== el ritmo, en el denominador ===

def test_el_tiempo_es_fichas_dividido_por_el_ritmo():
    """**La fórmula, y el error que evita.**

    *`RITMO` son **peticiones por segundo** -- se comprobó leyendo el uso:
    `Fetcher(rate_per_sec=config.RITMO[FUENTE])`.* **Si se multiplicara en vez de dividir**, *Alcampo
    saldría a 0,15 segundos por ficha en lugar de 6,7*, **y el total parecería de dos horas en lugar de
    88.** *Un número plausible y equivocado por un factor de 44.*
    """
    assert Tramo("x", 100, 2.0).segundos == 50.0, "100 fichas a 2 por segundo son 50 segundos"
    assert Tramo("x", 100, 0.5).segundos == 200.0
    # *Y el caso de Alcampo, que es el que importa.*
    assert Tramo("alcampo", 1, 0.15).segundos == pytest.approx(6.667, abs=0.001)


def test_los_ritmos_declarados_son_los_que_se_creen():
    """*Y la comprobación de que `config.RITMO` dice lo que este cálculo supone.*

    **Si alguien cambiara `RITMO` a segundos por petición, esta prueba no fallaría** -- *y por eso el
    comentario de Alcampo, que dice «una cada 6,7 s» junto a un `0,15`, es la evidencia de que son
    peticiones por segundo.* *Se fija aquí para que el cambio se note.*
    """
    assert config.RITMO["alcampo"] == 0.15, "y su comentario dice: una cada 6,7 segundos"
    assert config.RITMO["mercadona"] == 2.0
    assert all(v > 0 for v in config.RITMO.values()), "un ritmo de cero no terminaría nunca"


# ============================================ el total, y quién se lo lleva ===

def test_la_cola_entera_son_ochenta_y_ocho_horas():
    """**El número que no existía**, con las cifras del 13 de octubre de 2026.

    *88,1 horas de reloj en peticiones.* **Y eso sin contar lo que tarda cada respuesta**, que es
    trabajo real de red: *el presupuesto es de **espera**, y por tanto un suelo, no un techo.*
    """
    d = presupuesto(_tramos())
    assert d["horas"] == pytest.approx(88.1, abs=0.2), d["horas"]


def test_alcampo_se_lleva_nueve_decimas_partes_del_tiempo():
    """**Y esto es el hallazgo, no un adorno.**

    *43 603 fichas a 0,15 por segundo son **80,7 horas** -- el **91,7 %** del total.* **La cola no son
    seis cadenas: es Alcampo más un error de redondeo.**
    """
    d = presupuesto(_tramos())
    alcampo = next(t for t in d["tramos"] if t["cadena"] == "alcampo")
    assert alcampo["horas"] == pytest.approx(80.7, abs=0.2)
    assert alcampo["parte"] == pytest.approx(0.917, abs=0.005)
    # *Y las otras cinco juntas no llegan a una décima parte.*
    resto = sum(t["parte"] for t in d["tramos"] if t["cadena"] != "alcampo")
    assert resto < 0.1


def test_el_cuello_de_botella_se_nombra():
    """*Y se nombra aparte, porque un total repartido y un total que es una sola cadena son dos problemas
    distintos* -- **y el número de horas no los distingue.**"""
    d = presupuesto(_tramos())
    assert cuello_de_botella(d) == "alcampo"
    assert d["el_mas_caro"] == "alcampo"


def test_el_mas_caro_no_es_el_de_mas_fichas_siempre():
    """**La razón de que se mire el tiempo y no el tamaño.**

    *Una cadena con cien fichas a una cada diez segundos tarda más que otra con mil a diez por segundo.*
    **Ordenar por número de fichas daría la respuesta equivocada**, y es lo primero que uno hace.
    """
    pocas_y_lentas = Tramo("lenta", 100, 0.1)     # 1000 s
    muchas_y_rapidas = Tramo("rapida", 1000, 10.0)  # 100 s
    d = presupuesto([pocas_y_lentas, muchas_y_rapidas])
    assert d["el_mas_caro"] == "lenta", "la de menos fichas es la que más tarda"
    assert cuello_de_botella(d) == "lenta"


# ==================================================== las noches, y lo que no ===

def test_sin_decir_cuantas_horas_tiene_una_noche_no_se_contestan_las_noches():
    """**Suponer ocho horas sería inventarse el contexto.**

    *Una máquina encendida sólo por la tarde y una que lo está siempre dan números distintos.* **Se pide el
    dato; no se adivina.**
    """
    d = presupuesto(_tramos())
    assert d["noches"] is None, "sin horas_por_noche no se contesta, en vez de suponer"
    # *Y con el dato, sí.*
    d4 = presupuesto(_tramos(), horas_por_noche=4)
    assert d4["noches"] == pytest.approx(22.0, abs=0.5), d4["noches"]


def test_una_cola_vacia_no_es_un_error_ni_divide_por_cero():
    """*Y sin nada que hacer, cero.* **Con su `el_mas_caro` en `None`, que es la verdad.**"""
    d = presupuesto([])
    assert d["segundos"] == 0 and d["horas"] == 0
    assert d["el_mas_caro"] is None
    assert cuello_de_botella(d) is None


def test_un_ritmo_de_cero_no_termina_nunca_y_no_revienta():
    """**`inf`, y no una división por cero.**

    *Un ritmo de cero significa «a este paso no termina nunca», y `inf` es exactamente eso.* **Reventar
    obligaría a quien llama a envolverlo en un `try`, y devolver cero seria decir que es instantáneo.**
    """
    t = Tramo("parada", 500, 0.0)
    assert math.isinf(t.segundos)
    d = presupuesto([t, Tramo("normal", 100, 1.0)])
    assert math.isinf(d["horas"])
    assert d["el_mas_caro"] == "parada"
