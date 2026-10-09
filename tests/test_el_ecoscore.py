"""El Eco-Score, de Open Food Facts al catalogo.

Es el campo que mejor cubre OFF -- 354.831 de sus 355.038 codigos, el 99,9 % -- y el unico de los cuatro
que no se leia: se descargaba y se tiraba.

**La prueba fija la forma, no una lista de valores.** La primera version asumia que un Eco-Score solo puede
ser a/b/c/d/e, la escribi sin medir, y fallo: hay mas. Ahora se comprueba lo que de verdad no puede pasar
--que el campo traiga texto largo, o un numero, o nada-- que es lo que se veria en la ficha.
"""
from __future__ import annotations

import pytest

from projects.cesta.emparejar import externo_por_ean


@pytest.fixture(scope="module")
def externo():
    datos = externo_por_ean()
    if not datos:
        pytest.skip("falta data/externo/off_es.parquet (uv run python -m core.off)")
    return datos


def test_trae_las_cuatro_cosas(externo):
    """Ingredientes, Nutri-Score, NOVA y Eco-Score. Si falta una clave no es un dato que falte: es un
    nombre mal escrito, y por eso se comprueba el nombre y no solo que haya algo."""
    muestra = list(externo.values())[:400]
    assert all(set(v) == {"ingredientes", "nutriscore", "nova", "ecoscore"} for v in muestra)


def test_el_ecoscore_cubre_mas_que_el_nutriscore(externo):
    """Medido el 9 de octubre de 2026: 99,9 % de la base de OFF contra el 29 % del Nutri-Score. Si esto
    se diera la vuelta, algo habria cambiado en el fichero y habria que volver a medir."""
    eco = sum(1 for v in externo.values() if v.get("ecoscore"))
    nut = sum(1 for v in externo.values() if v.get("nutriscore"))
    assert eco > nut, (eco, nut)


def test_un_grado_es_una_etiqueta_corta(externo):
    """Un grado es una letra o una palabra corta en minusculas -- `a`, `unknown`, `not-applicable` -- y
    nunca un texto largo ni un numero. Si esto falla, la columna se ha leido de otro sitio."""
    valores = {str(v["ecoscore"]) for v in externo.values() if v.get("ecoscore")}
    malos = {g for g in valores if not (1 <= len(g) <= 16 and g == g.lower())}
    assert not malos, sorted(malos)[:8]
