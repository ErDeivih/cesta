"""F10: **dos recetas con un ingrediente compartido** -- lo que la aceptacion nombra y nadie ha ejercido.

La aceptacion de F10 (`docs/SUPERAPP-FASE2-EMPEZAR-AQUI.md:151`) dice:

> **Aceptacion:** dos recetas con **ingrediente compartido**, **mezcla kg/g compatible y ud incompatible**,
> cantidad...

**Y las tres reglas estan en `core/previa_compra.py`**, leidas en la ronda 120:

```
14  1. **La consolidacion es por producto Y unidad.** *Dos lineas del mismo producto en kilos se suman;
15     una en kilos y otra en unidades **no**, y se dice por que.* **Sumar 1 kg con 2 unidades daria un
16     numero que no significa nada.**
17  2. **Lo que no tiene cantidad no se compra.**
21  3. **Los envases son enteros.**
```

*Van contra el modulo puro: **sin red, sin base y sin tocar datos de nadie.***
"""
from __future__ import annotations

import pytest

from core import previa_compra


def _linea(previa) -> dict:
    """El resultado como diccionario, *porque `Previa` es un `dataclass`*."""
    from dataclasses import asdict

    return asdict(previa)


def _comprable(previa) -> dict[str, float]:
    """`{texto: cantidad}` de lo que se puede comprar, para comparar sin depender del orden."""
    d = _linea(previa)
    return {fila["texto"]: fila["cantidad"] for fila in d["lineas"]}


# ---------------------------------------------------------------------------------------------
# «Mezcla kg/g compatible»
# ---------------------------------------------------------------------------------------------


def test_la_misma_unidad_suma():
    """**Dos recetas que piden harina, las dos en kg, se suman.** *Es la regla 1, la mitad facil.*"""
    previa = previa_compra.previa_de_compra([
        {"texto": "harina", "cantidad": 1, "unidad": "kg"},
        {"texto": "harina", "cantidad": 0.5, "unidad": "kg"},
    ])

    assert _comprable(previa)["harina"] == 1.5, _linea(previa)


@pytest.mark.xfail(strict=True, reason=(
    "DEFECTO MEDIDO: `_unidad_canon` no usa `normalize._UNIDADES`, asi que `g` y `kg` son dos "
    "unidades distintas y `1 kg` + `500 g` NO se suman -- se nombran como incompatibles, igual que "
    "`kg` y `ud`, cuando la aceptacion de F10 los distingue (\"kg/g COMPATIBLE y ud INCOMPATIBLE\"). "
    "EL ARREGLO SE PROBO Y FUNCIONA -- `_unidad_canon` con la tabla y la cantidad por su factor da "
    "1,5 kg --, PERO CAMBIA LA UNIDAD QUE SE ENSENA: `test_g12_previa.py` espera `500` (en g) y el "
    "arreglo da `0,5` (en kg). Asi que no son tres lineas: HAY QUE DECIDIR si la linea se guarda en "
    "la unidad que vino -- y solo se convierte para comparar -- o en la canonica. Es decision del "
    "dueno, y por eso el arreglo esta revertido y esto queda fijado."))
def test_kg_y_g_SI_se_suman_porque_son_la_misma_unidad():
    """**«Mezcla kg/g compatible»** -- *el caso que la aceptacion nombra, y que **no** funcionaba.*

    *`1 kg` de harina y `500 g` de harina **son 1,5 kg de verdad**.* **Y el modulo los dejaba en dos lineas y
    los nombraba como incompatibles**, igual que hace con `kg` y `ud` -- *medido en la ronda 121.*

    **El arreglo**: `_unidad_canon` usa la tabla de `core.normalize` -- `"g": ("kg", 0.001)` --, y la cantidad se
    convierte con su factor. *Cambiar el nombre de la unidad sin cambiar el numero seria sumar peras con
    manzanas y decir que son todas peras.*

    *Esta prueba **antes era tolerante** -- aceptaba sumar **o** nombrar --, y por eso **pasaba con el defecto**.
    Ahora exige el resultado bueno: **una linea de 1,5 kg, y nada sin consolidar.***
    """
    previa = previa_compra.previa_de_compra([
        {"texto": "harina", "cantidad": 1, "unidad": "kg"},
        {"texto": "harina", "cantidad": 500, "unidad": "g"},
    ])
    d = _linea(previa)

    assert _comprable(previa) == {"harina": 1.5}, (
        f"1 kg y 500 g son 1,5 kg, y salio: {d['lineas']}")
    assert d["sin_consolidar"] == [], (
        f"y no hay nada que nombrar: {d['sin_consolidar']}")
    # **Y en la unidad canonica**, no en la que vino primero.
    assert {f["unidad"] for f in d["lineas"]} == {"kg"}, d["lineas"]


@pytest.mark.xfail(strict=True, reason=(
    "DEFECTO MEDIDO: `_unidad_canon` no usa `normalize._UNIDADES`, asi que `g` y `kg` son dos "
    "unidades distintas y `1 kg` + `500 g` NO se suman -- se nombran como incompatibles, igual que "
    "`kg` y `ud`, cuando la aceptacion de F10 los distingue (\"kg/g COMPATIBLE y ud INCOMPATIBLE\"). "
    "EL ARREGLO SE PROBO Y FUNCIONA -- `_unidad_canon` con la tabla y la cantidad por su factor da "
    "1,5 kg --, PERO CAMBIA LA UNIDAD QUE SE ENSENA: `test_g12_previa.py` espera `500` (en g) y el "
    "arreglo da `0,5` (en kg). Asi que no son tres lineas: HAY QUE DECIDIR si la linea se guarda en "
    "la unidad que vino -- y solo se convierte para comparar -- o en la canonica. Es decision del "
    "dueno, y por eso el arreglo esta revertido y esto queda fijado."))
def test_g_y_kg_al_reves_dan_lo_mismo():
    """*El orden no puede cambiar el resultado: **500 g y 1 kg son 1,5 kg igual**.* *Una consolidacion que
    dependa del orden es una consolidacion que miente la mitad de las veces.*
    """
    previa = previa_compra.previa_de_compra([
        {"texto": "harina", "cantidad": 500, "unidad": "g"},
        {"texto": "harina", "cantidad": 1, "unidad": "kg"},
    ])

    assert _comprable(previa) == {"harina": 1.5}, _linea(previa)["lineas"]


# ---------------------------------------------------------------------------------------------
# «ud incompatible»
# ---------------------------------------------------------------------------------------------


def test_kg_y_ud_no_se_suman_y_se_dice_por_que():
    """**La mitad que el criterio nombra aparte: «ud incompatible».**

    *Un kilo de harina y dos unidades de harina **no son tres de nada**.* **Y el modulo tiene que decirlo** --
    *no sumarlo, y no elegir una de las dos unidades en silencio.*
    """
    previa = previa_compra.previa_de_compra([
        {"texto": "harina", "cantidad": 1, "unidad": "kg"},
        {"texto": "harina", "cantidad": 2, "unidad": "ud"},
    ])
    d = _linea(previa)

    # **No se suma**: no puede haber una linea de harina con cantidad 3.
    assert _comprable(previa).get("harina") != 3, (
        f"sumo 1 kg con 2 ud: {d['comprable']}")
    # **Y se nombra**, con sus dos unidades.
    assert d["sin_consolidar"], (
        f"no se sumo, pero tampoco se dice: {d}")
    texto = " ".join(d["sin_consolidar"]).lower()
    assert "harina" in texto, d["sin_consolidar"]


def test_ml_y_g_tampoco_se_suman():
    """*La misma regla con las otras dos unidades de la frase del criterio: **«g/ml/ud»**.*

    *100 ml de leche y 100 g de leche **no son 200 de nada**.*
    """
    previa = previa_compra.previa_de_compra([
        {"texto": "leche", "cantidad": 100, "unidad": "ml"},
        {"texto": "leche", "cantidad": 100, "unidad": "g"},
    ])
    d = _linea(previa)

    assert _comprable(previa).get("leche") != 200, f"sumo ml con g: {d['comprable']}"
    assert d["sin_consolidar"], f"y no lo dice: {d}"


# ---------------------------------------------------------------------------------------------
# Las otras dos reglas
# ---------------------------------------------------------------------------------------------


def test_lo_que_no_tiene_cantidad_no_se_compra():
    """**Regla 2**, y con su motivo: *«inventarle un cero seria convertir un dato que falta en un dato falso»*
    -- *que es la misma frase que `escala`, en `core/recetas.py`.*
    """
    previa = previa_compra.previa_de_compra([
        {"texto": "sal"},
        {"texto": "harina", "cantidad": 1, "unidad": "kg"},
    ])
    d = _linea(previa)

    assert "sal" not in _comprable(previa), f"la sal se compro sin saber cuanto: {d['comprable']}"
    assert any("sal" in x for x in d["sin_cantidad"]), (
        f"y no se dice que la sal no se compra: {d['sin_cantidad']}")


def test_sin_unidad_tampoco_se_compra():
    """*Y **sin unidad** es el mismo caso con otro nombre: «3 de que».* *La ronda 120 lo vio escrito:
    «3 de que. **Se dice, no se supone**»*."""
    previa = previa_compra.previa_de_compra([{"texto": "harina", "cantidad": 3}])
    d = _linea(previa)

    assert "harina" not in _comprable(previa), d["lineas"]
    assert any("harina" in x for x in d["sin_cantidad"]), d["sin_cantidad"]


def test_la_previa_no_escribe_nada():
    """**Y la promesa del modulo**: *«Esto es la previa y **solo** la previa. No escribe en ninguna lista, no
    toca ninguna base»* (`previa_compra.py:7`).

    *Se comprueba por lo que se puede comprobar aqui: que la funcion **es pura** -- la misma entrada da la misma
    salida, y la entrada **no se modifica**.* **Eso es lo que hace que se pueda llamar sin miedo antes de
    decidir.**
    """
    ingredientes = [{"texto": "harina", "cantidad": 1, "unidad": "kg"}]
    copia = [dict(i) for i in ingredientes]

    una = _linea(previa_compra.previa_de_compra(ingredientes))
    otra = _linea(previa_compra.previa_de_compra(ingredientes))

    assert una == otra, "la misma entrada tiene que dar la misma salida"
    assert ingredientes == copia, "y la entrada no se puede modificar"
