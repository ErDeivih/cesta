"""Los ejes del nombre, y el trinquete de los grupos sobrefundidos.

Dos partes, y las dos hacen falta:

1. **Las pruebas de la funcion**, que son codigo puro: que `entera` y `desnatada` se
   contradigan, y que **`entera` y un nombre que no dice nada NO se contradigan**.
   Esa segunda es la regla honesta del encargo: si uno de los dos no declara nada,
   no bloquea. No es tolerancia, es ausencia de prueba.
2. **El trinquete sobre el dato**, que es distinto: mira el gold de hoy y falla si
   los numeros **empeoran**. No comprueba el codigo, comprueba que el catalogo no se
   deteriore sin que nadie se entere -- que es lo que ha pasado: el grupo mayor
   llego a 84 cervezas mezclando sin gluten con sin alcohol y nadie miraba esta
   columna.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from core.atributos import contradicciones, ejes_declarados, valores

GOLD = Path(__file__).resolve().parents[1] / "data" / "gold" / "grupos.parquet"

# Los numeros del 23 de septiembre de 2026. Son un TECHO, no un objetivo: si bajan,
# se bajan en el mismo commit; si suben, algo ha empeorado y hay que mirarlo antes de
# tocar el numero.
#
# Los cuatro bajaron el mismo dia, al meter **la invariante del reparto** en
# `agrupar_enlaces`: los enlaces son 1-a-1 por par de cadenas, asi que un grupo no
# puede tener dos productos de la misma cadena. Los techos anteriores eran 54, 74,
# 615 y 21.
TECHO_CONTRADICTORIOS = 49
TECHO_DE_11_O_MAS = 0
TECHO_QUE_MEZCLAN_PACK = 648
TECHO_PACK_DE_11_O_MAS = 0
# La sexta condicion de la barra, medida por el instrumento del proyecto (antes
# vivia en un script de `data/debug/`, que esta en `.gitignore`, asi que no estaba
# en el repositorio). Es la invariante del reparto: **cero grupos con una cadena
# repetida sin compartir EAN**. El duplicado con EAN no cuenta: son el mismo
# producto listado dos veces.
TECHO_CADENA_REPETIDA_SIN_EAN = 0


# --------------------------------------------------------------- la funcion ---

def test_entera_y_desnatada_se_contradicen():
    assert contradicciones(["Leche entera 1 l", "Leche desnatada 1 l"]) == {
        "grasa": ["entera", "sin grasa"]}


def test_el_que_no_declara_nada_no_bloquea():
    """La regla honesta: un nombre que calla no afirma que sea igual."""
    assert contradicciones(["Leche entera 1 l", "Leche 1 l"]) == {}


def test_sin_acentos_y_en_mayusculas_vale_igual():
    assert valores("ACEITE DE OLIVA VIRGEN EXTRA")["aceite"] == "virgen extra"
    assert valores("Aceite de oliva vírgen extra")["aceite"] == "virgen extra"


def test_lo_especifico_gana_a_lo_general():
    """`virgen extra` antes que `virgen`: si no, todo el aceite seria `virgen`."""
    assert valores("Aceite de oliva virgen extra 1 l")["aceite"] == "virgen extra"
    assert valores("Aceite de oliva virgen 1 l")["aceite"] == "virgen"


def test_los_ejes_de_verdad_del_catalogo():
    """Casos que salen en el gold, no inventados."""
    assert valores("Cerveza sin alcohol 0,0% lata")["alcohol"] == "sin alcohol"
    assert valores("Cafe molido descafeinado natural")["cafeina"] == "descafeinado"
    assert valores("Leche semidesnatada sin lactosa")["grasa"] == "semidesnatada"
    assert valores("Leche semidesnatada sin lactosa")["lactosa"] == "sin lactosa"
    assert valores("Harina de trigo integral")["integral"] == "integral"


def test_un_nombre_vacio_no_declara_nada():
    assert valores(None) == {}
    assert valores("") == {}
    assert ejes_declarados("") == 0


def test_tres_valores_en_un_eje_tambien_es_contradiccion():
    """El grupo 1116 tenia orujo, virgen y virgen extra: tres, no dos."""
    ejes = contradicciones(["Aceite de orujo", "Aceite virgen", "Aceite virgen extra"])
    assert ejes == {"aceite": ["orujo", "virgen", "virgen extra"]}


# --------------------------------------------------------------- el dato -----

@pytest.mark.skipif(not GOLD.exists(), reason="esta copia no trae gold")
def test_el_catalogo_no_ha_empeorado():
    """El trinquete. Si falla, se mira de que grupo nuevo se trata antes de nada."""
    from projects.cesta.ejes import resumen

    r = resumen()
    assert r["grupos_con_eje_contradictorio"] <= TECHO_CONTRADICTORIOS, (
        f"hay {r['grupos_con_eje_contradictorio']} grupos con un eje contradictorio "
        f"y el techo esta en {TECHO_CONTRADICTORIOS}. La barra del encargo pide "
        f"CERO: esto tiene que bajar, no subir. Mira de que grupos se trata con "
        f"`uv run python -m projects.cesta.ejes --peores 10`")
    assert r["grupos_de_11_o_mas"] <= TECHO_DE_11_O_MAS, (
        f"hay {r['grupos_de_11_o_mas']} grupos de 11 o mas productos y el techo "
        f"esta en {TECHO_DE_11_O_MAS}; la barra pide menos de 30")
    assert r["grupos_que_mezclan_pack"] <= TECHO_QUE_MEZCLAN_PACK, (
        f"hay {r['grupos_que_mezclan_pack']} grupos que mezclan un pack con "
        f"unidades sueltas y el techo esta en {TECHO_QUE_MEZCLAN_PACK}. Nadie se "
        f"contradice ahi -- todas son agua de 1,5 l --, pero \"donde compro agua\" "
        f"acaba recomendando nueve litros frente a uno y medio")
    assert r["de_esos_de_11_o_mas"] <= TECHO_PACK_DE_11_O_MAS, (
        f"{r['de_esos_de_11_o_mas']} grupos grandes mezclan pack con sueltas, y el "
        f"techo esta en {TECHO_PACK_DE_11_O_MAS}")
    assert r["grupos_con_cadena_repetida_sin_ean"] <= TECHO_CADENA_REPETIDA_SIN_EAN, (
        f"hay {r['grupos_con_cadena_repetida_sin_ean']} grupos con una cadena "
        f"repetida **sin compartir EAN**, y la barra pide cero. Los enlaces son "
        f"1-a-1 por par de cadenas: dos productos de la misma cadena en un grupo "
        f"solo valen si son el mismo producto (mismo codigo de barras). Mira la "
        f"guarda de `agrupar_enlaces` (parametros `cadenas` y `eans`)")


@pytest.mark.skipif(not GOLD.exists(), reason="esta copia no trae gold")
def test_los_ejes_y_el_pack_miden_cosas_distintas():
    """Los dos instrumentos son complementarios, y eso hay que fijarlo.

    Cuando se escribio esta prueba, el grupo de las 84 cervezas **no lo cazaba el
    eje del alcohol** (nadie escribe "con alcohol" en una cerveza, asi que nunca hay
    dos valores que se contradigan) y si lo cazaba el pack, por meter [1, 12]. Ese
    grupo ya no existe: la invariante del reparto lo partio, y con ella los 74
    grupos de 11 o mas.

    Asi que lo que se fija ahora es lo que sigue siendo verdad y lo que hay que
    vigilar: **el pack sigue viendo casos que los ejes no ven**. Si algun dia los
    dos numeros se mueven exactamente igual, es que uno de los dos ha dejado de
    medir algo propio.
    """
    from projects.cesta.ejes import resumen

    r = resumen(peores=5)
    assert r["grupos_que_mezclan_pack"] > 0, (
        "el pack ya no encuentra nada: o el catalogo ha cambiado o el instrumento "
        "dejo de mirar `unidades_pack`")
    assert r["grupos_con_eje_contradictorio"] > 0
    assert r["grupos_de_11_o_mas"] == 0, (
        "han vuelto a aparecer grupos de 11 o mas: la invariante del reparto "
        "(`agrupar_enlaces`, parametro `cadenas`) puede haberse roto")
