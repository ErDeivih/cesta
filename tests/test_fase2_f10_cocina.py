"""F10 / `R05`: **el modo cocina** -- paso actual, ingredientes usados, temporizadores y reanudacion.

*El modulo `core/cocina.py` explica la decision central: **un temporizador NO es una cuenta atras, es una hora de
fin** -- *y por eso **reanudar es volver a leer**, y **funciona sin conexion** porque no hay nada que consultar.*
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from core import cocina

AHORA = datetime(2026, 10, 11, 12, 0, tzinfo=timezone.utc)


def _con_pasos() -> cocina.Cocina:
    return cocina.Cocina(receta_id=7, version=2,
                         pasos=["Pochar la cebolla 10 minutos",
                                "Anadir el tomate",
                                "Hervir 1 h 30 min"])


# ----------------------------------------------------------- el paso actual ---


def test_sin_empezar_no_estas_en_el_paso_cero():
    """**Y la distincion importa.** *«No he empezado» y «voy por el primero» **se dicen distinto**, y por eso
    `paso` empieza en `None`.*
    """
    c = _con_pasos()
    assert c.paso is None, "sin empezar no se esta en ningun paso"
    assert c.reanuda(AHORA)["paso_actual"] is None

    assert c.empieza() == 0
    assert c.reanuda(AHORA)["paso_actual"].startswith("Pochar"), c.reanuda(AHORA)


def test_acabar_no_es_un_paso():
    """**Y `None` es lo que permite decir «terminada».** *Un `avanza` que se quedara en el ultimo diria que
    siempre falta un paso mas.*
    """
    c = _con_pasos()
    c.empieza()
    assert c.avanza() == 1
    assert c.avanza() == 2
    assert c.avanza() is None, "despues del ultimo paso ya no hay paso"
    assert c.avanza() is None, "y sigue sin haberlo"


def test_avanzar_sin_haber_empezado_empieza():
    """*No es un error: es ponerse.* **`avanza` sin empezar equivale a empezar**, y no a saltarse el paso 0.*"""
    c = _con_pasos()
    assert c.avanza() == 0


# ----------------------------------------------------- los ingredientes usados ---


def test_un_ingrediente_usado_dos_veces_se_cuenta_una():
    """*Echar la sal en dos pasos **no es echar el doble**.* **Contarla dos veces haria que la lista de lo que
    falta mintiera** -- *y esa lista es lo que `R10` pide explicar.*
    """
    c = _con_pasos()
    c.usa("sal")
    c.usa("sal")
    c.usa("  sal  ")

    assert c.usados == ["sal"], c.usados


def test_lo_que_falta_es_lo_que_no_se_ha_echado():
    """**`R10`, en su sentido de cocina**: *«faltante» aqui quiere decir **lo que queda por usar**, no lo que no
    hay en casa.*
    """
    c = _con_pasos()
    c.usa("cebolla")

    assert c.lo_que_falta(["cebolla", "tomate", "sal"]) == ["tomate", "sal"]


# ------------------------------------------------------------ los temporizadores ---


def test_un_temporizador_es_una_hora_de_fin_y_no_una_cuenta_atras():
    """**La decision central del modulo.** *Se guarda **cuando empezo**, y lo que queda se **calcula**.*

    *Y por eso **reanudar es volver a leer**: se puede preguntar cuanto queda **sin haber estado contando** --
    *que es lo que hace que funcione con la pantalla apagada, recargada o sin conexion.*
    """
    c = _con_pasos()
    t = c.pon_temporizador(10, ahora=AHORA)

    assert t.empezo_en == AHORA, "se guarda el instante, no un contador"
    assert t.acaba_en == AHORA + timedelta(minutes=10)
    assert t.queda(AHORA) == timedelta(minutes=10)
    assert t.queda(AHORA + timedelta(minutes=4)) == timedelta(minutes=6)
    assert not t.ha_terminado(AHORA + timedelta(minutes=4))
    assert t.ha_terminado(AHORA + timedelta(minutes=10))


def test_un_temporizador_pasado_dice_cuanto_se_paso_y_no_desaparece():
    """*Un temporizador que se paso **no es un temporizador que no existe**.* **Se dice**, porque «se paso hace 2
    minutos» es exactamente lo que hay que saber al volver.
    """
    c = _con_pasos()
    c.pon_temporizador(5, ahora=AHORA)

    r = c.reanuda(AHORA + timedelta(minutes=7))["temporizadores"][0]

    assert r["terminado"] is True
    assert r["queda_segundos"] == -120, f"tiene que decir que se paso 2 minutos: {r}"


def test_reanudar_no_pierde_nada_y_da_lo_que_la_pantalla_necesita():
    """**«Reanudacion sin conexion cuando sea viable».** *Todo lo que devuelve `reanuda` esta **calculado en el
    momento de leer**, asi que no hay nada que consultar y nada que se pueda perder.*
    """
    c = _con_pasos()
    c.empieza()
    c.avanza()
    c.usa("cebolla")
    c.pon_temporizador(10, ahora=AHORA)

    r = c.reanuda(AHORA + timedelta(minutes=3))

    assert r["paso"] == 1
    assert r["usados"] == ["cebolla"] and r["hechos"] == 1
    assert r["temporizadores"][0]["queda_segundos"] == 7 * 60


# ------------------------------------------------ y lo que un paso dice de tiempo ---


def test_los_minutos_de_un_paso_se_leen_y_no_se_inventan():
    """**«1 h 30 min» son 90 minutos, «90 s» son 2, y un paso que no dice tiempo no tiene ninguno.**

    *Lo ultimo es lo importante: **un paso que no dice «15 minutos» no tiene 15 minutos** -- ponerle uno seria
    **inventarle una instruccion a quien cocina**.* *Es la regla de «lo que no tiene cantidad no la gana» (`R04`).*
    """
    assert cocina.minutos_de("Hervir 1 h 30 min") == 90
    assert cocina.minutos_de("Pochar 10 minutos") == 10
    assert cocina.minutos_de("Cocer 90 s") == 2, "se redondea hacia arriba: un segundo de menos es de menos"
    assert cocina.minutos_de("Anadir el tomate") is None, "no se inventa"
    assert cocina.minutos_de(None) is None
    assert cocina.minutos_de("") is None


def test_un_temporizador_de_paso_que_no_dice_minutos_no_se_puede_poner():
    """*No se inventa: si el paso no dice cuanto, **no hay temporizador** -- y quien cocina decide.*"""
    c = _con_pasos()
    assert cocina.minutos_de(c.pasos[1]) is None, c.pasos[1]
    # *Y ponerlo seria una decision de quien cocina, no del lector de recetas.*
    with pytest.raises(TypeError):
        c.pon_temporizador(None)  # type: ignore[arg-type]
