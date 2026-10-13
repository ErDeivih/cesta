"""B04 — **el contrato de `_del_plan`**: la red que hace falta antes de unificar los puentes.

**Por que existe.** *El plan de unificacion (`docs/investigaciones/B04-unificar-los-puentes.md`) dice que
`_del_plan` deberia devolver `LineaDeCompra` en vez del diccionario que inventa hoy.* **Y un cambio asi,
sin una prueba que fije lo que hay ahora, se hace a ciegas.**

> **Las siete pruebas de `test_b04_los_dos_puentes.py` afirman el RESULTADO de los puentes** -- *que la
> previa de 300 g y que la nota nombre las dos recetas* --, **y eso esta bien y no debe cambiar.**
> **Lo que falta es una que afirme la FORMA.**

**Asi que esto fija el contrato actual, campo por campo.** *Cuando llegue el refactor, estas pruebas diran
exactamente que se ha roto; y las que dejen de aplicar se retiran a proposito, no por descuido.*

*Con mocks y sin bases reales, como el resto de B04.*
"""
from __future__ import annotations

from contextlib import ExitStack
from unittest.mock import Mock, patch

import pytest

from core import recetas as core_recetas
from plataforma.api import main

INGREDIENTE = {"texto": "harina", "cantidad": 100, "unidad": "g",
               "producto_id": "dia:fixture", "grupo_id": 7}


def _con_plan(ingredientes: list[dict], comensales: int = 4, raciones: int = 2,
             ya_en_la_lista: list[dict] | None = None):
    """`_del_plan` con un plan de una receta, y sin tocar ninguna base."""
    planes = [{"receta_id": 1, "version": 1, "fecha": "2026-10-19", "comensales": comensales}]

    def leer(*args, **kwargs):
        return {"nombre": "Receta 1", "version": 1, "raciones": raciones,
                "ingredientes": [dict(x) for x in ingredientes]}

    with ExitStack() as pila:
        pila.enter_context(patch.object(main.almacen, "lineas_de",
                                        return_value=ya_en_la_lista or []))
        pila.enter_context(patch.object(core_recetas, "conecta", return_value=Mock()))
        pila.enter_context(patch.object(core_recetas, "plan", return_value=planes))
        pila.enter_context(patch.object(core_recetas, "leer", side_effect=leer))
        return main._del_plan("lista-fixture", "fixture", "2026-10-19", "2026-10-25")


# ================================== la forma que devuelve HOY: dos valores ===
#
# **Y esto se corrigio a proposito.** *La primera version de esta prueba pedia TRES valores*
# -- *contando la `Previa` del refactor* --, **y fallo con «not enough values to unpack
# (expected 3, got 2)»**: *describia el destino, no lo que hay.*
#
# *Una prueba que describe el destino no es una red: es un deseo.* **Lo que hace falta antes
# de refactorizar es fijar LO QUE HAY**, para que el dia del cambio se sepa exactamente que se
# rompio.

def test_devuelve_los_campos_que_los_consumidores_leen():
    """**El contrato, campo por campo.** *Estas son las claves que `previa_del_plan` y `traer_del_plan`
    leen hoy* -- *y por eso estan aqui: **si el refactor las cambia, esta prueba lo dice**, en vez de que
    se entere un 500 en produccion.*

    *`receta` y `recetas` son las dos formas del mismo dato*: *la primera para el caso de una sola receta,
    la segunda para la nota que nombra varias.* **Y `_del_plan` devuelve las dos a proposito.**
    """
    lineas, _ya = _con_plan([INGREDIENTE])
    assert len(lineas) == 1, f"una linea, y hay {len(lineas)}"
    uno = lineas[0]
    for clave in ("nombre", "cantidad", "unidad", "producto_id", "grupo_id", "receta", "recetas"):
        assert clave in uno, f"falta «{clave}»: los consumidores la leen. Hay: {sorted(uno)}"
    assert uno["nombre"] == "harina"
    assert uno["producto_id"] == "dia:fixture"
    assert uno["grupo_id"] == 7


def test_la_cantidad_ya_viene_escalada():
    """**El escalado es de `_del_plan`, no de quien llama.** *100 g de una receta de 2 raciones para 4
    comensales son 200 g, y salen ya multiplicados.*"""
    lineas, _ya = _con_plan([INGREDIENTE], comensales=4, raciones=2)
    assert lineas[0]["cantidad"] == pytest.approx(200.0)


def test_devuelve_tambien_los_nombres_que_ya_estaban_en_la_lista():
    """*El segundo valor de la tupla: los nombres ya presentes, en minusculas.* **Es lo que hace que
    pulsar dos veces no duplique.**"""
    # *Por el parametro y no con un parche de fuera*: `_con_plan` parchea `lineas_de` dentro,
    # asi que un parche exterior lo pisa sin querer -- **y la prueba pasaba con `ya` vacio.**
    _lineas, ya = _con_plan([INGREDIENTE],
                            ya_en_la_lista=[{"nombre_visto": "Harina"}, {"nombre_visto": None}])
    assert ya == {"harina", ""}, f"y el None se convierte en cadena vacia, no revienta: {ya}"


def test_hoy_devuelve_dos_valores_y_el_refactor_pedira_tres():
    """**El contrato de hoy, dicho tal cual: DOS valores.** *Las lineas y los nombres ya presentes.*

    *Y aqui queda escrito lo que el refactor va a cambiar*, para que no se descubra por sorpresa:
    `docs/investigaciones/B04-unificar-los-puentes.md` pide que `_del_plan` devuelva **tambien la
    `Previa`** -- *porque hoy se tira, y con ella `sin_cantidad` y `sin_consolidar`, que son informacion
    que el criterio de B04 pide.*

    **Esta prueba es la que se retirara el dia del refactor**, *y se retira a proposito y con este
    comentario delante: no por descuido.*
    """
    resultado = _con_plan([INGREDIENTE])
    assert isinstance(resultado, tuple), "devuelve una tupla"
    assert len(resultado) == 2, (
        f"hoy son DOS valores -- lineas y ya --, y son {len(resultado)}. "
        "Si esto cambia, el refactor de unificacion ha empezado: mira B04-unificar-los-puentes.md")


def test_lo_que_no_tiene_destino_sigue_llegando_y_se_puede_decir():
    """**El ingrediente sin producto ni grupo no se pierde: llega, y con sus dos destinos en `None`.**

    *Es la regla de la fase: **lo que no se sabe se dice**, y no se deja que se confunda con un cero.*
    **Un ingrediente escrito a mano no tiene destino** -- *y quien lo mire tiene que poder verlo, en vez de
    que el puente lo prometa y la base lo rechace con un 500, que es lo que pasaba antes.*
    """
    sin_destino = {"texto": "sal", "cantidad": 5, "unidad": "g"}
    lineas, _ya = _con_plan([sin_destino])
    assert len(lineas) == 1, "tiene que llegar igual: no tener destino no es no existir"
    assert lineas[0]["producto_id"] is None and lineas[0]["grupo_id"] is None
    assert lineas[0]["nombre"] == "sal"


def test_sin_recetas_en_el_plan_no_hay_lineas_y_no_revienta():
    """*Y el caso vacio.* **Ni lineas ni excepcion.**"""
    with ExitStack() as pila:
        pila.enter_context(patch.object(main.almacen, "lineas_de", return_value=[]))
        pila.enter_context(patch.object(core_recetas, "conecta", return_value=Mock()))
        pila.enter_context(patch.object(core_recetas, "plan", return_value=[]))
        lineas, ya = main._del_plan("lista-fixture", "fixture", "2026-10-19", "2026-10-25")
    assert lineas == [] and ya == set()
