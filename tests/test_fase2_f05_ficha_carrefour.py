"""F05 (fase 2): **la ficha de Carrefour, de su HTML a un dato usable.**

*Medido pidiendo **una** ficha con `robots.txt` comprobado:* la pagina de producto de Carrefour **si trae
nutricion** -- *en atributos `data-*`, porque **no es una tabla HTML*** -- y **los listados no**, que es por lo
que sus 2.004 crudos no tenian ni una cifra.

*Estas pruebas usan el HTML real medido, y **no llaman a la red**.*
"""
from __future__ import annotations

import gzip
import re
from pathlib import Path

import pytest

from projects.cesta import ficha_carrefour as fc

# **El HTML real, copiado de la ficha que se pidio** (aceite de oliva Dcoop, `R-824301999`). *Los atributos
# van DESPUES de la clase, que es como vienen en la pagina.*
HTML = (
    '<div class="pdp-view__nutrition-info">'
    '<div class="nutrition"><div class="nutrition__graphic">'
    '<h3 class="nutrition__info-title">       Información nutricional     </h3>'
    '<div class="nutrition__data"><div class="nutrition__graphic-content">'
    '<div class="nutrition-graph">'
    '<p class="nutrition-graph__info-text">     Valores medios por 100 g.   </p>'
    '<div data-cal="900 Kcal" data-fi="" data-fa="100 g" data-h="0 g" '
    'data-kj="3700 KJ" data-p="0 g" data-s="0 g" class="nutrition-graph__graphic-svg">'
    '<div class="n"></div></div></div></div></div></div></div>'
)


def test_lee_los_nutrientes_del_atributo():
    """**La tabla esta en `data-*`, no en un `<table>`.** *Por eso el crudo de listados no la tenia.*"""
    leido = fc.lee(HTML)

    assert leido["kcal"] == {"valor": 900.0, "uom": "Kcal"}
    assert leido["energia_kj"] == {"valor": 3700.0, "uom": "KJ"}
    assert leido["grasas"] == {"valor": 100.0, "uom": "g"}
    assert leido["hidratos"] == {"valor": 0.0, "uom": "g"}
    assert leido["proteinas"] == {"valor": 0.0, "uom": "g"}
    assert leido["sal"] == {"valor": 0.0, "uom": "g"}


def test_lee_la_base_por_que_esta_expresada():
    """**Sin la base, la tabla no se puede comparar** -- *y el proyecto ya decidio que ensenar una que no se
    puede comparar es peor que no tenerla (`dia.py:_nutricion`).*
    """
    assert fc.base(HTML) == "100 g"
    assert fc.lee(HTML)["por"] == "100 g"


def test_un_atributo_vacio_no_es_un_cero():
    """**`data-fi=""` es fibra que la fuente no dice, no fibra cero.** *Y la diferencia importa: un cero dice
    «no tiene», un vacio dice «no lo dice».*

    *Es la misma regla que `ficha_dia` y `ficha_mercadona`: lo que falta se dice, no se rellena.*
    """
    leido = fc.lee(HTML)

    assert "fibra" not in leido, "un atributo vacio no puede salir como cero"
    # Y lo que SI viene, sale -- para que la prueba no pase por no leer nada.
    assert "grasas" in leido


def test_los_numeros_son_los_del_aceite_de_oliva():
    """**La comprobacion de que los numeros son reales.** *900 kcal y 100 g de grasa por 100 g **es** lo que
    tiene el aceite de oliva.* **Si un dia el lector devolviera otra cosa, esto lo dice.**
    """
    leido = fc.lee(HTML)

    assert leido["kcal"]["valor"] == 900.0
    assert leido["grasas"]["valor"] == 100.0
    assert leido["hidratos"]["valor"] == 0.0


def test_una_pagina_sin_titulo_de_nutricion_no_da_nada():
    """**Los listados no la traen**, y una pagina que no la tenga no puede devolver un diccionario con la
    base y nada mas -- *eso contaria como ficha.*
    """
    sin = '<div class="nutrition-graph__graphic-svg" data-cal="1 Kcal"></div>'
    assert fc.lee(sin) == {}

    # Y una sin el bloque, tampoco.
    con_titulo_sin_bloque = "<h3>Información nutricional</h3><p>Valores medios por 100 g.</p>"
    assert [k for k in fc.lee(con_titulo_sin_bloque) if k != "por"] == []


def test_tolera_lo_que_no_es_html():
    """*La fuente cambia de forma, y un cuerpo raro no puede reventar la pasada entera.*"""
    assert fc.lee({}) == {}
    assert fc.lee("") == {}
    assert fc.lee("texto sin nada") == {}
    assert fc.la_tiene("texto sin nada") is False


# ---------------------------------------------------------------------------------------------
# Y contra el crudo de verdad, si está.
# ---------------------------------------------------------------------------------------------


def _una_ficha_de_carrefour():
    """La ficha cacheada, buscándola por lo que tiene. *No baja nada: lee lo que ya está en `data/raw`.*"""
    for carpeta in sorted(Path("data/raw").glob("fuente=carrefour/fecha=*"), reverse=True):
        for f in sorted(carpeta.glob("*.json.gz"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                t = gzip.decompress(f.read_bytes()).decode("utf-8", "replace")
            except Exception:  # noqa: BLE001
                continue
            if fc.la_tiene(t) and len(t) > 100_000:
                return f, t
    return None


def test_contra_la_ficha_real():
    """**La prueba que vale**: sobre la ficha que se pidió, no sobre el HTML que he escrito yo.

    *Si no hay ficha en crudo -- otra máquina -- se salta. Pero cuando la hay, se comprueba de verdad.*
    """
    hallado = _una_ficha_de_carrefour()
    if hallado is None:
        pytest.skip("no hay ficha de Carrefour con tabla en data/raw")

    fichero, html = hallado
    leido = fc.lee(html)

    assert leido, f"{fichero.name}: la pagina trae tabla y no se ha leido"
    assert "por" in leido, f"{fichero.name}: sin base, la tabla no se puede comparar"
    # **Y algún nutriente tiene que ser un número de verdad.**
    numeros = [v["valor"] for k, v in leido.items() if k != "por" and isinstance(v, dict)]
    assert numeros, f"{fichero.name}: la tabla no trae ni un numero: {leido}"
    assert all(isinstance(n, float) for n in numeros), leido
    # Y la base es la comparable que el proyecto exige.
    assert re.match(r"^\d+\s*(g|ml)$", leido["por"]), (
        f"{fichero.name}: la base tiene que ser comparable, y es {leido['por']!r}")
