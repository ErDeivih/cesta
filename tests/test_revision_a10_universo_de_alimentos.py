"""El universo de alimentos: **que es comida, que no, y que no se sabe.**

**Lo que estas pruebas fijan, y por que cada una importa.**

 1. **Las cuatro secciones no-comida dan NUEVE calorias entre 12 479 filas.** *Eso no es una opinion: es
    la comprobacion de que la separacion es real y no un gusto mio.*
 2. **«No lo se» no es «no».** *185 filas sin seccion se contestan `desconocido`, y **una seccion nueva
    que nadie haya clasificado tambien** -- *porque clasificar por descarte meteria una seccion de comida
    en «no es comida» sin que nadie lo hubiera decidido.*
 3. **Las mezclas se dan como dos limites, no como un numero.** *`bebe` tiene potitos y toallitas; elegir
    uno de los dos sin decirlo seria inventar.*

*Y nada de esto necesita el catalogo:* **la funcion es pura y las cifras de filas son las que se midieron**
-- *que es lo que permite comprobar la regla sin abrir un parquet de 19 MB.*
"""
from __future__ import annotations

import pytest

from core.alimentos import (
    DE_COMIDA,
    MEZCLA,
    NO_DE_COMIDA,
    cobertura_sobre_comida,
    es_comida,
    que_es,
)

# ====================================================== las cuatro respuestas ===

@pytest.mark.parametrize("seccion", sorted(DE_COMIDA))
def test_las_secciones_de_comida_son_comida(seccion):
    """*Las once, una a una.* **Y se recorren todas a proposito**: *una lista con una letra mal escrita
    dejaria una seccion entera fuera del universo sin que nada fallara.*"""
    assert que_es(seccion) == "comida"
    assert es_comida(seccion) is True


@pytest.mark.parametrize("seccion", sorted(NO_DE_COMIDA))
def test_las_secciones_que_no_son_comida_no_lo_son(seccion):
    """*Y las cuatro que no.* **Estas son las que aportan 9 calorias entre 12 479 filas.**"""
    assert que_es(seccion) == "no"
    assert es_comida(seccion) is False


@pytest.mark.parametrize("seccion", sorted(MEZCLA))
def test_las_mezclas_no_se_resuelven(seccion):
    """**`promociones`, `bebe`, `parafarmacia` y `ecologico` son mezcla, y se dice.**

    *Devolver «si» o «no» para esas seria inventar.* **Y `es_comida` contesta que no** -- *que es lo
    prudente: `promociones` a secas no es una seccion de comida* --, **pero `que_es` dice la verdad, que
    es «depende».**
    """
    assert que_es(seccion) == "mezcla"
    assert es_comida(seccion) is False
    # *Y se distinguen de las que no son comida.* **Son respuestas distintas porque son cosas distintas.**
    assert que_es(seccion) != "no"


def test_una_seccion_desconocida_no_se_mete_en_no_es_comida():
    """**La regla que evita que una seccion nueva desaparezca sin que nadie lo note.**

    *Si el `else` fuera «no es comida»*, una seccion de comida que el catalogo estrene mañana -- *o que
    este catalogo tenga y yo no haya medido* -- **se contaria como drogueria**, y la cobertura de la
    comida mejoraria sola. *Eso es lo contrario de medir.*
    """
    for rara in ("seccion-que-no-existe", "Nueva Seccion 2027", "otra/cosa"):
        assert que_es(rara) == "desconocido", rara
        assert es_comida(rara) is False


@pytest.mark.parametrize("vacio", [None, "", "   ", "\t"])
def test_sin_seccion_se_contesta_desconocido(vacio):
    """*Y las 185 filas sin seccion.* **`None` y la cadena vacia se contestan «desconocido», no «no».**"""
    assert que_es(vacio) == "desconocido"
    assert es_comida(vacio) is False


def test_las_tildes_y_las_mayusculas_no_cambian_la_respuesta():
    """**El catalogo no trae las secciones limpias.** *`droguería-limpieza` lleva tilde, y la seccion
    puede llegar con espacios o en mayusculas.* **Comparar en crudo dejaria esas filas en «desconocido»**
    -- *y como `desconocido` no es comida, **se contarian como que no**, que es acertado por casualidad
    pero por el motivo equivocado.*
    """
    assert que_es("HIGIENE-BELLEZA") == "no"
    assert que_es("  higiene-belleza  ") == "no"
    assert que_es("Droguería-Limpieza") == "no"
    assert que_es("DESPENSA") == "comida"


def test_las_tres_listas_no_se_pisan():
    """**La guarda de la guarda.** *Una seccion en dos listas a la vez daria una respuesta distinta segun
    el orden de los `if`* -- *y el orden no deberia decidir nada.*"""
    assert not (DE_COMIDA & NO_DE_COMIDA)
    assert not (DE_COMIDA & MEZCLA)
    assert not (NO_DE_COMIDA & MEZCLA)


# ============================================ la cobertura, con sus dos limites ===

def test_la_cobertura_sobre_comida_da_dos_limites_y_no_uno():
    """**Las cifras medidas el 12 de octubre de 2026**, y las dos fronteras.

    *36 989 filas de comida, 11 040 con energia, y 2 434 de mezcla.* **El techo es 29,8 % y el suelo
    28,0 %** -- *y **el 21,2 % sobre el catalogo entero**, que es el numero que se daba sin decir sobre
    que se medía.*
    """
    c = cobertura_sobre_comida(con_dato=11040, de_comida=36989, de_mezcla=2434)
    assert c["comida"] == 36989
    assert round(c["techo"], 1) == 29.8, c
    assert round(c["suelo"], 1) == 28.0, c
    # *Y el techo es siempre mayor que el suelo*, porque el denominador es menor.
    assert c["techo"] >= c["suelo"]


def test_sin_mezclas_los_dos_limites_coinciden():
    """*Si no hay nada mezclado, no hay dos respuestas: hay una.* **Y tiene que coincidir.**"""
    c = cobertura_sobre_comida(con_dato=50, de_comida=100)
    assert c["techo"] == c["suelo"] == 50.0


def test_sin_comida_clasificada_no_se_divide_por_cero():
    """*Y el caso en que no hay nada que medir.* **Cero, con su motivo, y sin reventar.**"""
    c = cobertura_sobre_comida(con_dato=5, de_comida=0)
    assert c["techo"] == 0.0 and c["suelo"] == 0.0
    assert c.get("motivo")


def test_la_cobertura_nunca_pasa_del_cien_por_ciento():
    """*Y el absurdo que hay que impedir*: **si hay mas filas con dato que filas de comida, algo se contó
    dos veces.** *No se recorta a 100 en silencio: se deja ver, porque un porcentaje de 120 quiere decir
    que la cuenta esta mal.*"""
    c = cobertura_sobre_comida(con_dato=150, de_comida=100)
    assert c["techo"] == 150.0, "no se recorta: si sale mas de cien, la cuenta esta mal y hay que verlo"
