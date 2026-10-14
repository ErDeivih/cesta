"""B04 — **los dos puentes, con los 300 g como caso.** *La regresion que impide que vuelvan a ser 100.*

**Por que existe este fichero.** *El 13 de octubre de 2026 el dueño reprodujo el fallo con
`scripts/auditar_puente_plan_20261013.py`* -- *dos recetas de 100 g de harina con `raciones: 2`, una
planificada para **4 comensales** y otra para 2, y **hay que comprar 300 g***.

**Y ese script IMPRIME Y NO AFIRMA.** *Un diagnostico que no falla no impide que el fallo vuelva: sirve
para mirarlo una vez, no para sostenerlo.* **Esto es lo mismo, pero con `assert`.**

**Los dos defectos que se arreglaron, y que aqui quedan fijados:**

  - **El puente del plan no escalaba por comensales y DESCARTABA la segunda contribucion.** *Daba
    `[100, 100]` en la previa, metia **una** linea con nota «Receta 1 (100 g)» y metia la segunda en
    `ya_estaban`.* **Ahora da `[300.0]`, una linea, y la nota nombra las dos recetas.**
  - **El puente de la receta escribia `round(cantidad)` UNIDADES y ninguna nota.** *300 g se convertian en
    **300 unidades de harina*** -- *o sea «300 envases»* --, **y sin nota no quedaba rastro de los gramos.**

*Se prueban con mocks y sin bases reales, como el script del dueño: **asi se puede fallar sin tocar datos
de nadie**.*
"""
from __future__ import annotations

from contextlib import ExitStack
from unittest.mock import Mock, patch

import pytest

from core import recetas as core_recetas
from core import traspaso as core_traspaso
from core.previa_compra import LineaDeCompra
from plataforma.api import almacen as api_almacen
from plataforma.api import main
from plataforma.api import recetas as api_recetas

# **El caso del dueño, con sus numeros.** *100 g por receta, recetas de 2 raciones, y 4 + 2 comensales.*
INGREDIENTE = {"texto": "harina", "cantidad": 100, "unidad": "g",
               "producto_id": "dia:fixture", "grupo_id": 1}
NECESIDAD_CORRECTA = 100 * 4 / 2 + 100 * 2 / 2      # = 300,0


def _receta(nombre: str) -> dict:
    return {"nombre": nombre, "version": 1, "raciones": 2, "ingredientes": [dict(INGREDIENTE)]}


@pytest.fixture()
def puente_del_plan():
    """El puente del plan, con sus dos recetas y **sin tocar ninguna base**."""
    planes = [
        {"receta_id": 1, "version": 1, "fecha": "2026-10-19", "comensales": 4},
        {"receta_id": 2, "version": 1, "fecha": "2026-10-20", "comensales": 2},
    ]
    nombres = {1: "Receta 1", 2: "Receta 2"}

    def leer(*args, **kwargs):
        return _receta(nombres[args[2]])

    insertar = Mock()
    with ExitStack() as pila:
        pila.enter_context(patch.object(main, "_acceso", return_value=None))
        pila.enter_context(patch.object(main.almacen, "lineas_de", return_value=[]))
        pila.enter_context(patch.object(main.almacen, "anade_linea", insertar))
        pila.enter_context(patch.object(core_recetas, "conecta", return_value=Mock()))
        pila.enter_context(patch.object(core_recetas, "plan", return_value=planes))
        pila.enter_context(patch.object(core_recetas, "leer", side_effect=leer))
        yield insertar


# ==================================================== el puente del PLAN ===

def test_la_previa_escala_por_comensales_y_suma_las_dos_recetas(puente_del_plan):
    """**300 g, que es lo que hay que comprar.** *Y era 100 y 100.*

    *La cuenta*: la receta 1 pide 100 g **para 2 raciones** y se cocina **para 4** -- *factor 2, o sea
    200 g* --; la receta 2 pide otros 100 g **para 2** -- *factor 1, o sea 100 g* --. **Total: 300 g.**

    *Y es **una sola linea**, porque el ingrediente y la unidad son los mismos: consolidar es sumar, no
    repetir.*
    """
    previa = main.previa_del_plan("lista-fixture", "2026-10-19", "2026-10-25", {"id": "fixture"})
    cantidades = [x["cantidad"] for x in previa["entrarian"]]
    assert cantidades == [pytest.approx(NECESIDAD_CORRECTA)], (
        f"la previa tiene que dar UNA linea de {NECESIDAD_CORRECTA} g, y da {cantidades}")
    assert len(previa["entrarian"]) == 1, "las dos recetas son el mismo ingrediente: una sola linea"


def test_la_segunda_receta_no_se_descarta_como_repetida(puente_del_plan):
    """**El defecto que el dueño describio con estas palabras**: «descartando la segunda receta como
    repetida».

    *Antes*: el bucle metia la primera harina, hacia `ya.add("harina")` y **la segunda se iba a
    `ya_estaban`** -- *con sus 100 g dentro*. **Ahora no hay segunda: las dos se suman antes de escribir.**
    """
    recibo = main.traer_del_plan("lista-fixture", "2026-10-19", "2026-10-25", {"id": "fixture"})
    assert recibo["anadidos"] == 1
    assert recibo["ya_estaban"] == [], (
        "la segunda receta no puede salir como «ya estaba»: aporta 100 g que hay que comprar")
    assert recibo["sin_catalogo"] == []


def test_la_nota_nombra_las_dos_recetas_y_el_total(puente_del_plan):
    """**Y la nota, que es donde se lee el detalle.** *Antes decia «del plan: Receta 1 (100 g)».*

    **No solo callaba una receta: decia 100 g cuando hay que comprar 300.** *La nota contesta a «cuanto
    hay que comprar», y con la cantidad de la primera no contesta nada.*
    """
    main.traer_del_plan("lista-fixture", "2026-10-19", "2026-10-25", {"id": "fixture"})
    llamadas = puente_del_plan.call_args_list
    assert len(llamadas) == 1, f"una sola linea, y hubo {len(llamadas)}"
    nota = llamadas[0].args[7]
    assert "Receta 1" in nota and "Receta 2" in nota, f"la nota tiene que nombrar las dos: {nota!r}"
    assert "300" in nota, f"y decir el total: {nota!r}"
    # *Y la unidad, que es lo que distingue 300 g de 300 unidades.*
    assert "g" in nota, f"y la unidad: {nota!r}"


def test_la_cantidad_de_la_linea_es_una_unidad_y_no_300(puente_del_plan):
    """**El campo `cantidad` cuenta envases, no gramos.** *Es la mitad del fallo del otro puente.*

    *La linea se anade con **1** unidad y el detalle en la nota.* **Si aqui apareciera 300, la lista diria
    «300 envases de harina»** -- *que es justo el defecto que el otro puente tenia.*
    """
    main.traer_del_plan("lista-fixture", "2026-10-19", "2026-10-25", {"id": "fixture"})
    cantidad = puente_del_plan.call_args_list[0].args[6]
    assert cantidad == 1, f"una unidad, y se puso {cantidad}"


def test_sin_raciones_no_se_inventa_un_factor(puente_del_plan):
    """**Y si la receta no declara raciones, no se multiplica.**

    *Multiplicar por un numero que no consta seria peor que no escalar*: **no escalar se ve, y un factor
    inventado no.** *Asi que se deja la cantidad como esta, y la prueba lo fija para que nadie «arregle» el
    hueco suponiendo.*
    """
    def leer_sin_raciones(*args, **kwargs):
        r = _receta("Receta 1")
        del r["raciones"]
        return r

    with patch.object(core_recetas, "leer", side_effect=leer_sin_raciones):
        previa = main.previa_del_plan("lista-fixture", "2026-10-19", "2026-10-25", {"id": "fixture"})
    # *Las dos recetas suman 100 + 100, sin factor: 200, y no 300.*
    assert [x["cantidad"] for x in previa["entrarian"]] == [pytest.approx(200.0)]


# ================================================== el puente de la RECETA ===

def test_la_receta_a_la_lista_pone_una_unidad_y_el_detalle_en_la_nota():
    """**El defecto simetrico, y peor.** *Aqui se escribia `round(ln.cantidad) or 1`.*

    *300 g de harina se anadi an como **300 unidades*** -- *o sea «300 envases»* -- **y con `nota=None`, asi
    que no quedaba ni rastro de los gramos.** *Quien mirara la lista veria «harina · 300» sin forma de saber
    si son paquetes o gramos.*

    **Lo que se fija aqui**: *una unidad, y la nota con la cantidad y la unidad de la receta.*
    """
    linea = LineaDeCompra(clave="dia:fixture|g", texto="harina", producto_id="dia:fixture",
                          cantidad=300.0, unidad="g")
    insertar = Mock()

    def captura(con, propietario, receta_id, *, insertar=None, **kw):
        insertar([linea])
        return {"lineas": 1}

    with ExitStack() as pila:
        pila.enter_context(patch.object(api_recetas, "_con", return_value=Mock()))
        pila.enter_context(patch.object(api_almacen, "listas_de",
                                        return_value=[{"id": "lista-fixture"}]))
        pila.enter_context(patch.object(api_almacen, "anade_linea", insertar))
        pila.enter_context(patch.object(core_traspaso, "pasar_a_lista", side_effect=captura))
        api_recetas.a_la_lista(1, api_recetas.ALaLista(lista_id="lista-fixture"), {"id": "fixture"})

    assert insertar.call_count == 1, "una linea"
    argumentos = insertar.call_args_list[0].args
    assert argumentos[6] == 1, f"UNA unidad, y se puso {argumentos[6]}"
    nota = argumentos[7]
    assert nota and "300" in nota and "g" in nota, f"y la nota con los gramos: {nota!r}"
    assert "harina" in nota, f"y el ingrediente: {nota!r}"


def test_la_nota_de_la_receta_cuenta_los_envases_y_lo_que_sobra():
    """**Y lo que `previa_compra` ya calculaba y se tiraba.** *Los envases enteros y el sobrante.*

    *A08 calculo los envases y el sobrante, y `a_la_lista` los tiraba.* **Son la respuesta a «cuantos
    paquetes compro», que es la segunda pregunta de una lista de la compra.**
    """
    linea = LineaDeCompra(clave="dia:fixture|g", texto="harina", producto_id="dia:fixture",
                          cantidad=1400.0, unidad="g", envases=2, tamano_envase=1000.0,
                          unidad_envase="g", sobrante=600.0, de_donde=["harina", "masa"])
    insertar = Mock()

    def captura(con, propietario, receta_id, *, insertar=None, **kw):
        insertar([linea])
        return {"lineas": 1}

    with ExitStack() as pila:
        pila.enter_context(patch.object(api_recetas, "_con", return_value=Mock()))
        pila.enter_context(patch.object(api_almacen, "listas_de",
                                        return_value=[{"id": "lista-fixture"}]))
        pila.enter_context(patch.object(api_almacen, "anade_linea", insertar))
        pila.enter_context(patch.object(core_traspaso, "pasar_a_lista", side_effect=captura))
        api_recetas.a_la_lista(1, api_recetas.ALaLista(lista_id="lista-fixture"), {"id": "fixture"})

    nota = insertar.call_args_list[0].args[7]
    assert "2 envases" in nota, f"los envases, que ya estaban calculados: {nota!r}"
    assert "600" in nota, f"y lo que sobra: {nota!r}"
    assert "masa" in nota, f"y de que ingredientes salio: {nota!r}"
    # **Y LA CANTIDAD, que es el fallo que el dueño reprodujo el 14/10.**
    #
    # *Esta prueba construia el caso exacto -- **1,4 kg en envase de 1 kg** -- y miraba **solo la nota**.
    # Y por eso **`1` pasaba desapercibido**: las dos lineas de arriba se cumplian **con la cantidad
    # mal**, porque «2 envases» vivia **unicamente en el texto**.*
    #
    # **Un ensayo que comprueba la nota y no la cantidad no fija el defecto: lo tapa.**
    assert insertar.call_args_list[0].args[6] == 2, (
        "DOS envases, y se guardo "
        f"{insertar.call_args_list[0].args[6]}: «dos envases» estaba solo en la nota")


# ============================== los envases, que es lo que se perdia ==========
#
# **El fallo del dueño, del 14/10/2026, en sus palabras**: *«se calculan dos envases, pero se guarda
# cantidad 1; "dos envases" queda solamente en la nota».*
#
# *Y el `1` tenia un motivo escrito -- `traer_del_plan` decia «la lista cuenta unidades de un producto y la
# receta habla en gramos: poner 400 en `cantidad` diria "400 envases"» --, **y el motivo era cierto**:
# *400 si seria mentira.* **Pero `1` tampoco es la respuesta cuando la previa calcula dos.**
#
# *La unidad correcta ya estaba en el sistema: `previa_compra` **«cuenta los envases enteros»**.*

def _el_puente_del_plan_con(linea):
    """El puente del plan con UNA linea ya calculada, **sin red y sin bases**."""
    insertar = Mock()
    with ExitStack() as pila:
        pila.enter_context(patch.object(main, "_acceso", return_value=None))
        pila.enter_context(patch.object(main.almacen, "lineas_de", return_value=[]))
        pila.enter_context(patch.object(main.almacen, "anade_linea", insertar))
        pila.enter_context(patch.object(main, "_del_plan", return_value=([linea], set(), None)))
        main.traer_del_plan("lista-fixture", "2026-10-19", "2026-10-25", {"id": "fixture"})
    return insertar


def test_el_puente_del_plan_guarda_dos_envases_y_no_uno():
    """**1,4 kg en envase de 1 kg son DOS envases, y hay que comprar dos.**

    *Es la regresion del fallo del dueño, en el puente del plan: **la cantidad que se persiste tiene que
    ser la que la previa calculo**, porque es la que leen el coste, el cierre y el historico.*
    """
    linea = LineaDeCompra(clave="dia:fixture|g", texto="harina", producto_id="dia:fixture",
                          cantidad=1400.0, unidad="g", envases=2, tamano_envase=1000.0,
                          unidad_envase="g", sobrante=600.0)
    insertar = _el_puente_del_plan_con(linea)
    assert insertar.call_count == 1, "una linea"
    argumentos = insertar.call_args_list[0].args
    assert argumentos[6] == 2, f"DOS envases, y se guardo {argumentos[6]}"
    assert "2 envases" in argumentos[7] and "600" in argumentos[7], argumentos[7]


def test_el_puente_del_plan_guarda_tres_envases_cuando_hacen_falta_tres():
    """**Y tres, cuando hacen falta tres.** *2,4 kg en envase de 1 kg: la cantidad sigue a los envases.*"""
    linea = LineaDeCompra(clave="dia:fixture|g", texto="harina", producto_id="dia:fixture",
                          cantidad=2400.0, unidad="g", envases=3, tamano_envase=1000.0,
                          unidad_envase="g", sobrante=600.0)
    insertar = _el_puente_del_plan_con(linea)
    assert insertar.call_args_list[0].args[6] == 3, "TRES envases"


def test_con_tamano_desconocido_la_nota_lo_dice_y_no_se_afirma_un_envase():
    """**Y cuando no se sabe el tamaño, se DICE -- no se calla.**

    *`lista_linea.cantidad` es `integer NOT NULL`, asi que «no se sabe» **no cabe en la columna** y queda
    `1`. **Y por eso la nota tiene que decirlo**: *callarlo se leia como «un envase basta», que es justo lo
    que no se sabe.*
    """
    # *Sin `envases`: es lo que devuelve `previa_compra` cuando no conoce el tamaño del envase.*
    linea = LineaDeCompra(clave="dia:fixture|g", texto="harina", producto_id="dia:fixture",
                          cantidad=1400.0, unidad="g")
    assert linea.envases is None, "el andamio tiene que dejar los envases sin calcular"
    insertar = _el_puente_del_plan_con(linea)
    argumentos = insertar.call_args_list[0].args
    assert "no se sabe el tamano del envase" in argumentos[7], (
        f"la nota tiene que decir que no se sabe, y dice {argumentos[7]!r}")
    assert argumentos[6] == 1, "y la columna queda en 1, porque es NOT NULL"


def test_la_receta_tambien_dice_cuando_no_se_sabe_el_tamano():
    """**Y el otro puente, igual.** *Los dos puentes tienen que decir lo mismo, o uno de los dos miente.*"""
    linea = LineaDeCompra(clave="dia:fixture|g", texto="harina", producto_id="dia:fixture",
                          cantidad=1400.0, unidad="g")
    insertar = Mock()

    def captura(con, propietario, receta_id, *, insertar=None, **kw):
        insertar([linea])
        return {"lineas": 1}

    with ExitStack() as pila:
        pila.enter_context(patch.object(api_recetas, "_con", return_value=Mock()))
        pila.enter_context(patch.object(api_almacen, "listas_de",
                                        return_value=[{"id": "lista-fixture"}]))
        pila.enter_context(patch.object(api_almacen, "anade_linea", insertar))
        pila.enter_context(patch.object(core_traspaso, "pasar_a_lista", side_effect=captura))
        api_recetas.a_la_lista(1, api_recetas.ALaLista(lista_id="lista-fixture"), {"id": "fixture"})

    argumentos = insertar.call_args_list[0].args
    assert "no se sabe el tamano del envase" in argumentos[7], argumentos[7]
    assert argumentos[6] == 1, "y la columna queda en 1"


def test_la_receta_guarda_dos_envases_y_no_uno():
    """**Y el caso del dueño en el puente de la receta**: *1,4 kg en envase de 1 kg, **dos**.*"""
    linea = LineaDeCompra(clave="dia:fixture|g", texto="harina", producto_id="dia:fixture",
                          cantidad=1400.0, unidad="g", envases=2, tamano_envase=1000.0,
                          unidad_envase="g", sobrante=600.0)
    insertar = Mock()

    def captura(con, propietario, receta_id, *, insertar=None, **kw):
        insertar([linea])
        return {"lineas": 1}

    with ExitStack() as pila:
        pila.enter_context(patch.object(api_recetas, "_con", return_value=Mock()))
        pila.enter_context(patch.object(api_almacen, "listas_de",
                                        return_value=[{"id": "lista-fixture"}]))
        pila.enter_context(patch.object(api_almacen, "anade_linea", insertar))
        pila.enter_context(patch.object(core_traspaso, "pasar_a_lista", side_effect=captura))
        api_recetas.a_la_lista(1, api_recetas.ALaLista(lista_id="lista-fixture"), {"id": "fixture"})

    argumentos = insertar.call_args_list[0].args
    assert argumentos[6] == 2, f"DOS envases, y se guardo {argumentos[6]}"
    assert "2 envases" in argumentos[7] and "600" in argumentos[7], argumentos[7]
    # **Y LA CANTIDAD, que es el fallo que el dueño reprodujo el 14/10.**
    #
    # *Esta prueba construia el caso exacto -- **1,4 kg en envase de 1 kg** -- y miraba **solo la nota**.
    # Y por eso **`1` pasaba desapercibido**: las dos lineas de arriba se cumplian **con la cantidad
    # mal**, porque «2 envases» vivia **unicamente en el texto**.*
    #
    # **Un ensayo que comprueba la nota y no la cantidad no fija el defecto: lo tapa.**
    assert insertar.call_args_list[0].args[6] == 2, (
        "DOS envases, y se guardo "
        f"{insertar.call_args_list[0].args[6]}: «dos envases» estaba solo en la nota")


def test_la_receta_preserva_el_ARTICULO_ELEGIDO_y_no_lo_degrada():
    """**El articulo elegido, que se perdia SIEMPRE en el puente de la receta.**

    *`a_la_lista` hacia `int(ln.producto_id) if (ln.producto_id or "").isdigit() else None`. Y los
    identificadores del catalogo son **`fuente:id`** -- `dia:1234`, `carrefour:5678` --, asi que
    **ninguno es `isdigit()`**: *la linea salia con `producto_id = None` **siempre**.*

    *Y `lista_linea.producto_id` es **`text`**, no un entero: el `int()` no era una conversion necesaria,
    era **una perdida**.*

    **Lo que se fija aqui**: *un ingrediente con **producto exacto y sin grupo** llega a la lista **con su
    producto**, y **no se degrada a `None`** -- *porque **un grupo es una familia**, y **la persona eligio
    un articulo**.* *Y cuando trae los dos, se conservan **los dos**.*
    """
    # *Producto exacto SIN grupo: el caso que se perdia del todo.*
    exacto = LineaDeCompra(clave="dia:fixture|g", texto="harina", producto_id="dia:fixture",
                           cantidad=300.0, unidad="g")
    # *Y con grupo, que es «evitar el rechazo» pero no «preservar el elegido».*
    con_grupo = LineaDeCompra(clave="dia:fixture|g", texto="harina", producto_id="dia:fixture",
                              grupo_id=7, cantidad=300.0, unidad="g")
    for linea, esperado_grupo in ((exacto, None), (con_grupo, 7)):
        insertar = Mock()

        # *La variable del bucle se liga como argumento, que es lo que pide `ruff` y lo que evita
        # que las dos vueltas compartan la ultima `linea`.*
        def captura(con, propietario, receta_id, *, _la=linea, insertar=None, **kw):
            insertar([_la])
            return {"lineas": 1}

        with ExitStack() as pila:
            pila.enter_context(patch.object(api_recetas, "_con", return_value=Mock()))
            pila.enter_context(patch.object(api_almacen, "listas_de",
                                            return_value=[{"id": "lista-fixture"}]))
            pila.enter_context(patch.object(api_almacen, "anade_linea", insertar))
            pila.enter_context(patch.object(core_traspaso, "pasar_a_lista", side_effect=captura))
            api_recetas.a_la_lista(1, api_recetas.ALaLista(lista_id="lista-fixture"),
                                   {"id": "fixture"})

        argumentos = insertar.call_args_list[0].args
        assert argumentos[5] == "dia:fixture", (
            f"el articulo elegido tiene que llegar entero, y llego {argumentos[5]!r}")
        assert argumentos[4] == esperado_grupo, (
            f"y el grupo, {esperado_grupo}: {argumentos[4]!r}")
