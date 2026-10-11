"""F09: **el aislamiento del recetario, medido** -- `R03` y el septimo caso de la aceptacion.

El criterio (`docs/SUPERAPP-COMPETENCIA-Y-REA.md:103`) pide, para `R03`:

> **Borrador recuperable y version persistente**; diario antiguo permanece estable.

Y la aceptacion de F09 nombra, como septimo caso: *«**aislamiento**»*.

**Y `core/recetas.py` lo dice de si mismo en su tercera linea:**

```
:3    **Privacidad, implementada.** Cada receta tiene propietario, y **todas** las operaciones lo exig[en]...
:11   **Lo historico, sin dueno, queda conservado e inaccesible.** ...
:15   **Cada version es autocontenida**: guarda sus raciones, su preparacion y sus ingredientes **copi[ados]**...
```

**Tres afirmaciones, y las tres se pueden probar.** *Van contra un SQLite temporal: **no tocan datos de nadie**,
que es lo que la aceptacion pide con «recetas de fixture» y lo que el encargo pide con «preserva datos reales».*
"""
from __future__ import annotations

import contextlib

import pytest

from core import recetas


@pytest.fixture()
def con(tmp_path):
    """Un recetario vacio, en un fichero temporal. *No se toca el de nadie.*"""
    return recetas.conecta(tmp_path / "recetas.sqlite")


UNA = [{"texto": "harina", "cantidad": 200, "unidad": "g"},
       {"texto": "leche", "cantidad": 100, "unidad": "ml"},
       {"texto": "sal"}]


def _receta(con, dueno: str, nombre: str = "Tortilla") -> int:
    """**`crear` devuelve el id**, no un diccionario -- *lo dijo el `TypeError`, no mi recuerdo.*"""
    nueva = recetas.crear(con, dueno, nombre, raciones=2, ingredientes=UNA)
    return nueva["id"] if isinstance(nueva, dict) else int(nueva)


# ---------------------------------------------------------------------------------------------
# «Cada receta tiene propietario, y todas las operaciones lo exigen»
# ---------------------------------------------------------------------------------------------


def test_el_dueno_lee_la_suya_y_el_otro_no(con):
    """**La afirmacion central.** *Y se prueban las dos mitades: que el dueno **si** pueda, y que el de fuera
    **no** -- porque sin la primera, la segunda pasaria por un modulo que no deja leer nada a nadie.*
    """
    mia = _receta(con, "ana")

    assert recetas.leer(con, "ana", mia) is not None, "la duena tiene que poder leer la suya"
    assert recetas.leer(con, "luis", mia) is None, (
        "**y el de fuera NO**: si esto falla, la receta se expone")


def test_el_de_fuera_no_puede_cambiarla(con):
    """*Y no solo leerla: **cambiarla tampoco**.* **El mismo patron que `_acceso` en las listas.**"""
    mia = _receta(con, "ana")

    # **El de fuera intenta cambiarla, y no puede.** *`actualizar` devuelve `None` o levanta: las dos son
    # correctas, lo que no vale es que cambie.*
    with pytest.raises(Exception):  # noqa: B017  (cualquier fallo vale, menos el exito)
        recetas.actualizar(con, "luis", mia, nombre="Secuestrada")

    vuelta = recetas.leer(con, "ana", mia)
    assert vuelta is not None and vuelta["nombre"] != "Secuestrada", (
        "y la receta sigue siendo la de ana")


def test_el_de_fuera_no_puede_archivarla(con):
    """*Borrar lo de otro es la version fuerte del mismo fallo.*

    **Y lo que importa no es si levanta: es si BORRA.** *La primera version de esta prueba pedia una excepcion,
    y `archivar` **no la da** -- pero **puede que no haga nada**, y eso tambien seria correcto.* **El
    instrumento estaba midiendo la forma y no el fondo** -- *una `WHERE propietario` que no casa ninguna fila
    devuelve 0 y es un exito silencioso, que es exactamente lo que se quiere.*
    """
    mia = _receta(con, "ana")

    # **No se exige que falle: se exige que NO borre.** *Es la misma leccion de la lista vacia que contaba
    # como distinta, y de la asercion que pasaba con cualquier encabezado.*
    with contextlib.suppress(Exception):
        recetas.archivar(con, "luis", mia)

    assert recetas.leer(con, "ana", mia) is not None, (
        "**la de ana sigue ahi**: si esto falla, el de fuera puede borrar lo de otro")


def test_las_listas_no_mezclan_duenos(con):
    """**Y de propina: `listar` no ensena lo de otro.** *Es la operacion que mas facil es escribir mal* --
    *un `SELECT * FROM receta` sin `WHERE propietario` --, y **la que mas se usaria**.*"""
    _receta(con, "ana", "Tortilla")
    _receta(con, "luis", "Paella")

    de_ana = recetas.listar(con, "ana")
    de_luis = recetas.listar(con, "luis")

    assert [r["nombre"] for r in de_ana] == ["Tortilla"], de_ana
    assert [r["nombre"] for r in de_luis] == ["Paella"], de_luis


# ---------------------------------------------------------------------------------------------
# «Cada version es autocontenida»
# ---------------------------------------------------------------------------------------------


def test_una_version_no_cambia_porque_cambie_la_receta(con):
    """**`R03`: «version persistente».** *Editar una receta **no puede** cambiar lo que ya estaba* -- *si no,
    **el diario antiguo, que anoto la version 1, apuntaria a algo que ya no dice lo mismo**.*

    *Y eso es `R03` entero visto desde el diario: «**diario antiguo permanece estable**».*
    """
    mia = _receta(con, "ana", "Tortilla")
    antes = recetas.leer(con, "ana", mia)
    assert antes is not None

    # **Se edita**, y con otro ingrediente -- *que es lo que cambiaria el sentido de lo ya anotado.*
    recetas.actualizar(con, "ana", mia,
                       ingredientes=[{"texto": "patata", "cantidad": 300, "unidad": "g"}])

    # **La version 1 sigue diciendo lo que decia.**
    v1 = recetas.leer(con, "ana", mia, version=1)
    assert v1 is not None, "la version 1 tiene que seguir existiendo"
    nombres = [i["texto"] for i in v1["ingredientes"]]
    assert "harina" in nombres, f"la version 1 cambio: {nombres}"

    # Y la ultima dice lo nuevo, para que la prueba no pase por no guardar nada.
    ultima = recetas.leer(con, "ana", mia)
    assert [i["texto"] for i in ultima["ingredientes"]] == ["patata"]


def test_las_versiones_son_una_lista_y_crecen(con):
    """*«Version persistente» tambien quiere decir que se pueden **enumerar**.*"""
    mia = _receta(con, "ana")
    assert recetas.versiones(con, "ana", mia) == [1]

    recetas.actualizar(con, "ana", mia, nombre="Tortilla de patata")
    assert recetas.versiones(con, "ana", mia) == [1, 2]


def test_las_versiones_de_otro_tampoco_se_ven(con):
    """*El aislamiento vale para **todo**, no solo para leer: tambien para saber cuantas versiones hay.*"""
    mia = _receta(con, "ana")

    assert recetas.versiones(con, "luis", mia) == [], (
        "las versiones de una receta ajena no son publicas")


# ---------------------------------------------------------------------------------------------
# R04: el escalado
# ---------------------------------------------------------------------------------------------


def test_el_escalado_no_le_inventa_cantidad_a_lo_que_no_la_tiene():
    """**`R04` y su frase mas concreta**: *«lo que no tiene cantidad, **no la gana**»*.

    *La sal no tiene cantidad, y despues de escalar tampoco: **inventarle un cero seria convertir un dato que
    falta en un dato falso**.*
    """
    escalados = recetas.escala(UNA, 2, 4)

    por_nombre = {i["texto"]: i for i in escalados}
    assert por_nombre["sal"].get("cantidad") is None, (
        f"a la sal le ha aparecido una cantidad: {por_nombre['sal']}")


def test_el_escalado_multiplica_y_no_suma(con):
    """**La razon de que `R04` se cumpla aqui por construccion.** *`escala` recorre los ingredientes **de uno en
    uno**: no puede sumar g con ml porque **no suma nada con nada**.*

    *La suma esta en otro sitio -- «Plan→lista», que es **F10** --, y por eso esta prueba **no** la cubre.*
    """
    escalados = recetas.escala(UNA, 2, 4)

    por_nombre = {i["texto"]: i for i in escalados}
    assert por_nombre["harina"]["cantidad"] == 400, "200 g para 2 raciones son 400 g para 4"
    assert por_nombre["leche"]["cantidad"] == 200, "y los ml se multiplican igual, sin convertirse"

    # **Y cada ingrediente conserva su unidad**: no hay ninguna suma que pueda mezclarlas.
    assert por_nombre["harina"]["unidad"] == "g"
    assert por_nombre["leche"]["unidad"] == "ml"
