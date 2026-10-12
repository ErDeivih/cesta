"""A06 — La procedencia de la calidad: **lo que publica la tienda no es lo que deduce un tercero**.

**El caso que lo destapo, medido el 12 de octubre de 2026.** El `President` de Carrefour del grupo
`11627` trae **`calidad_origen=ingredientes_off`, nota 100 y letra A**, y su columna nativa
`ingredientes` esta **vacia**. *No es un parser roto: **la valoracion es enriquecida desde Open Food
Facts**.*

**Y el sello decia «leida de ingredientes» para las dos procedencias** -- asi que *un dato de un tercero
**se atribuia al supermercado**.* **A06 lo pide con estas palabras: «datos enriquecidos no se atribuyen
al supermercado».**

**Por que esto importa mas de lo que parece.** *Un sello que dice de donde sale el dato es lo que
distingue*:
  - «Carrefour no publica los ingredientes de este producto, y esto es una estimacion de OFF», de
  - «Carrefour publica estos ingredientes y de ahi sale la letra».

*Son dos frases distintas sobre la misma letra A*, y **la primera no puede disfrazarse de la segunda**
-- *que es la misma regla que se aplico con Lidl (`A05`) y con las decisiones del buscador.*

**Y estas pruebas son de la regla pura**, que se extrajo de `catalogo.prod` **precisamente para poder
probarla**: *estaba en linea dentro de una funcion anidada, y ahi no hay forma de mirarla.*
"""
from __future__ import annotations

from plataforma.api.catalogo import _calidad_y_origen

# ---------------------------------------------------------- las dos procedencias ---

def test_los_ingredientes_de_la_tienda_dan_calidad_y_dicen_que_son_suyos():
    """*La via fuerte*: **la tienda publica los ingredientes y la letra sale de leerlos.**"""
    letra, de = _calidad_y_origen("A", "ingredientes")
    assert letra == "A"
    assert de == "ingredientes"


def test_los_deducidos_por_off_dan_calidad_pero_NO_se_atribuyen_a_la_tienda():
    """**El caso del President de Carrefour.** *La letra es la misma y la procedencia no.*

    *Y es la prueba que A06 pide*: **la letra se conserva** -- *el dato sirve* --, **y la procedencia dice
    `ingredientes_off`** -- *la pantalla puede decir que no es de la tienda.*
    """
    letra, de = _calidad_y_origen("A", "ingredientes_off")
    assert letra == "A", "la letra no se tira: el dato sirve"
    assert de == "ingredientes_off", "y la procedencia NO es la de la tienda"
    assert de != "ingredientes"


def test_las_dos_procedencias_no_se_confunden_nunca():
    """**La distincion, en una linea.** *Si esto se rompiera, las dos frases volverian a ser una.*"""
    assert _calidad_y_origen("A", "ingredientes") != _calidad_y_origen("A", "ingredientes_off")


# ------------------------------------------------------------- lo que NO es calidad ---

def test_el_precio_no_da_calidad_ni_procedencia_de_calidad():
    """**`precio` no es calidad: es gama.** *Y `_calidad_y_origen` devuelve `None` en los dos campos.*

    *La conclusion que esto evita*: **mezclar las dos produce la conclusion falsa de que lo barato es
    peor**, y por eso la API manda `gama` en su propio campo y no aqui.
    """
    assert _calidad_y_origen("A", "precio") == (None, None)


def test_sin_letra_no_hay_nada_que_atribuir():
    """*Y sin letra, los dos campos a `None`* -- **no se rellena con una procedencia por defecto.**"""
    assert _calidad_y_origen(None, "ingredientes") == (None, None)
    assert _calidad_y_origen(None, None) == (None, None)
    assert _calidad_y_origen("A", None) == (None, None)


def test_una_procedencia_desconocida_no_se_disfraza_de_la_de_la_tienda():
    """**Lo que impide el `startswith`, y conviene que este fijado.**

    *Una procedencia que empiece por «ingredientes» pasa* -- *y es lo que se quiere, porque
    `ingredientes_off` es una de ellas y hay que dejar sitio a variantes futuras como
    `ingredientes_ocr`.* **Pero una que no empiece por ahi no da calidad**, *aunque traiga una letra*.
    """
    assert _calidad_y_origen("A", "ocr_propio") == (None, None)
    assert _calidad_y_origen("A", "estimado") == (None, None)
    # *Y una variante nueva de la familia si pasa, que es la parte util.*
    assert _calidad_y_origen("B", "ingredientes_ocr") == ("B", "ingredientes_ocr")


def test_la_funcion_no_depende_de_nada_de_fuera():
    """*Es pura.* **Si necesitara el catalogo, no se podria probar el caso del President sin tener el
    President** -- *y el caso del President es justamente el que hay que poder fijar.*
    """
    import inspect

    fuente = inspect.getsource(_calidad_y_origen)
    assert "conexion(" not in fuente, "no puede consultar el catalogo"
    assert "SELECT" not in fuente
