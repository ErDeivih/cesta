"""F11 / `R08`: **la despensa declarada**, y los cuatro casos de su aceptacion.

*El modulo `core/despensa.py` explica el porque.* **Lo que estas pruebas fijan son las cuatro cosas que la
aceptacion nombra** (`SUPERAPP-FASE2-EMPEZAR-AQUI.md:159`): *consumo parcial, stock desconocido, unidades
incompatibles y fecha ausente* -- **mas la regla central del criterio**: ***compra no acredita consumo***.
"""
from __future__ import annotations

import pytest

from core import despensa

# --------------------------------------------------- el primer caso: el consumo parcial ---


def test_consumo_parcial_descuenta_lo_que_queda():
    """**«Consumo parcial»**, el primer caso de la aceptacion. *Se gasta parte, y queda el resto.*

    **Y queda en la unidad CANONICA, no en la que se declaro**: *`1000 g` menos `300 g` da **`0,7 kg`**, no
    `700 g`.* **Eso NO es un detalle: es la misma decision que `F10` dejo abierta** -- *«¿la linea se guarda en
    la unidad que vino, o en la canonica?»* --, *y aqui se ha tomado **sin tomarla**, porque convertir es lo que
    hace falta para poder restar.*

    *La prueba fija **lo que hace**, y **dice que es una decision**: si el dueno dice que se guarde en la que
    vino, esto es lo que hay que cambiar.*
    """
    d = despensa.Despensa()
    d.declara("harina", 1000, "g")

    queda, motivo = d.consume("harina", 300, "g")

    assert motivo == "", motivo
    assert queda is not None, queda
    # **En canonica**, y es la decision abierta del tablero.
    assert queda.cantidad == pytest.approx(0.7) and queda.unidad == "kg", queda


def test_gastarlo_todo_borra_la_existencia_y_no_deja_un_cero():
    """**Y no se deja un `cero`.** *«Cero kg» afirmaria que hay una cantidad, y **no es lo mismo que no
    haberlo** -- *es la misma distincion que `sin_precio`: un cero es una afirmacion.*
    """
    d = despensa.Despensa()
    d.declara("harina", 500, "g")

    _, motivo = d.consume("harina", 500, "g")

    assert motivo == "se acabo", motivo
    assert "harina" not in d.existencias, "no puede quedar una existencia en cero"


# ------------------------------------------- el segundo: el stock desconocido, y el tercero ---


def test_sin_saber_cuanto_hay_consumir_lo_deja_desconocido_y_lo_dice():
    """**«Stock desconocido»**, el segundo caso. Y la respuesta es **decirlo, no inventar un numero**.

    *Se declara que hay arroz **sin decir cuanto**; se gasta; y lo que queda **sigue sin saberse*** -- *que es la
    verdad, y es lo contrario de restarle a un cero.*
    """
    d = despensa.Despensa()
    d.declara("arroz")

    queda, motivo = d.consume("arroz", 200, "g")

    assert "no se sabe cuanto" in motivo, motivo
    assert queda is not None and queda.cantidad is None, queda
    assert queda.unidad == despensa.DESCONOCIDA
    assert not queda.se_sabe, "y `se_sabe` tiene que decir que no"


def test_kg_y_g_son_la_misma_unidad():
    """**«Unidades incompatibles» tiene dos mitades, y esta es la que SI se puede convertir.**

    *`kg` y `g` son la misma unidad -- la tabla de `core.normalize` lo sabe --, asi que **restar 300 g de 1 kg
    da 0,7 kg**, y no un «unidades incompatibles».*
    """
    d = despensa.Despensa()
    d.declara("harina", 1, "kg")

    queda, motivo = d.consume("harina", 300, "g")

    assert motivo == "", motivo
    assert queda is not None and queda.cantidad == pytest.approx(0.7), queda


def test_kg_y_ud_no_se_restan_y_se_dice_por_que():
    """**Y esta es la mitad que no.** *Un kilo de harina y dos unidades de harina **no se restan**.*

    *Es el mismo defecto que `F10` fijo con `xfail` en `previa_compra` (`kg/g` no se sumaban); **aqui si se
    convierte**, porque se usa la misma tabla -- *y lo que no se puede convertir **se dice**.*
    """
    d = despensa.Despensa()
    d.declara("harina", 1, "kg")

    queda, motivo = d.consume("harina", 2, "ud")

    assert "incompatibles" in motivo, motivo
    assert queda is not None and queda.cantidad == 1, "y la existencia no se toca"


def test_una_unidad_que_no_se_conoce_no_se_resta():
    """*Una existencia en una unidad que no esta en la tabla **no se puede descontar de nada**, y se dice.*"""
    d = despensa.Despensa()
    d.declara("cosas", 3, "puñados")

    _, motivo = d.consume("cosas", 1, "puñados")

    assert "no se puede convertir" in motivo, motivo


# --------------------------- el cuarto: la fecha ausente, y la regla central del criterio ---


def test_la_fecha_es_opcional_y_una_sin_fecha_no_es_un_problema():
    """**«Fecha ausente»**, el cuarto caso -- *y la respuesta es que **no pasa nada**: el criterio dice
    «ubicacion/caducidad **opcional**».*

    *Una existencia sin caducidad **no esta incompleta**: esta declarada sin fecha, que es lo que se sabe.*
    """
    d = despensa.Despensa()
    e = d.declara("leche", 1, "l")

    assert e.caduca == "", "sin fecha"
    assert e.donde == "", "y sin ubicacion"
    assert e.se_sabe, "y eso no impide saber cuanto hay"


def test_no_hay_ninguna_funcion_que_sume_una_compra():
    """**LA REGLA CENTRAL DEL CRITERIO: «compra no acredita consumo ni stock restante».**

    *Y esta puesta **en el camino**, no en un comentario: **no existe la funcion**, asi que **no se puede llamar
    por error**.* *Es la misma forma que el `raise` de `diario.py:154` (una receta sin version no entra) y que
    el `rechaza compra` de `diario.py:140`.*

    **No es un olvido, y esta prueba lo fija**: *si algun dia alguien anade `suma_compra`, esta prueba falla y
    **la decision se vuelve a tomar a proposito**.*
    """
    for nombre in ("suma_compra", "anade_compra", "compra", "registra_compra", "suma"):
        assert not hasattr(despensa.Despensa, nombre), (
            f"`Despensa.{nombre}` existe: **una compra no puede acreditar consumo** (R08). "
            "Si de verdad hay que anadirla, hay que decidirlo a proposito y quitar esta prueba.")
        assert not hasattr(despensa, nombre), f"`despensa.{nombre}` existe, y no puede"


# ------------------------------------------------------------- y R10: lo que falta ---


def test_lo_que_falta_separa_disponibles_de_faltantes_y_dice_el_motivo():
    """**`R10`: «explicar ingredientes disponibles/faltantes».** *Y cada faltante lleva **su motivo** -- la
    forma que el proyecto usa en `sin_cantidad`, `sin_consolidar` y `faltantes`.*
    """
    d = despensa.Despensa()
    d.declara("harina", 1, "kg")
    d.declara("sal")

    hay, falta = d.lo_que_falta([{"texto": "harina"}, {"texto": "sal"}, {"texto": "levadura"}])

    assert [x["texto"] for x in hay] == ["harina", "sal"], hay
    assert [x["texto"] for x in falta] == ["levadura"], falta
    assert falta[0]["motivo"] == "no esta en la despensa", falta
    # **Y la sal, que hay pero no se sabe cuanto, CUENTA COMO DISPONIBLE** -- *que es lo que se pregunta: si
    # hace falta comprarla. Y no hace.*
    assert hay[1]["hay"] == despensa.DESCONOCIDA, hay
