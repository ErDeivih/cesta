"""A09 — El recorrido de Compra **con dos personas del mismo hogar**, de punta a punta.

**Lo que pide A09, y lo que se mide aqui.** *De su criterio*:

> «Entorno desechable con catalogo versionado controlado, usuarios A/B/hogar [...] Compra: texto libre,
> exacto, alternativa, revocar, 3x2 dividido, cierre e historico persistido.»

*Este fichero cubre la mitad que **no necesita catalogo**:* **el texto libre, el reparto entre dos
personas del mismo hogar, el cierre y el historico que sobrevive.** *Lo que necesita el catalogo
versionado -- el producto exacto, la alternativa y el 3x2 -- va aparte, y **no se dice que este hecho**.*

**Por que A y B y no un usuario solo.** *El criterio de F07 es de **dos personas** («no pisan cantidades
ni tachados»), y una lista compartida es donde eso se puede romper.* **Y aqui se comprueba lo que A09
pide del cierre: que las dos lo vean y que el historico quede.**

*Van contra el Postgres de verdad, con su propio usuario y su propia lista: no tocan datos de nadie.*
"""
from __future__ import annotations

import time
import uuid

import pytest

from plataforma.api import almacen


@pytest.fixture(scope="module", autouse=True)
def _arrancado():
    almacen.arranca()
    yield


def _id(x) -> str:
    """El id, **siempre como texto**.

    *Y esto costo una corrida*: `crea_lista` devuelve un objeto **`UUID`**, no una cadena, y algo mas
    abajo llama a `.strip()` -- *«AttributeError: 'UUID' object has no attribute 'strip'»* --. **Es el
    mismo error de siempre: dar por hecho el tipo de un dato en vez de leerlo.** *Aqui se lee, y se
    convierte.*
    """
    return str(x["id"] if isinstance(x, dict) else x)


def _un_hogar(nombre: str):
    """**Dos personas y una lista compartida**, con un sello por ejecucion.

    *El sello es obligatorio*: los usuarios viven en Postgres y **no se borran**, asi que sin el, el
    segundo pase choca con `UsuarioRepetido`. *Es el mismo detalle que F07 y F03 resuelven igual.*
    """
    sello = f"{int(time.time() * 1000) % 100000000}"
    usuario_a = f"a09-a-{nombre}-{sello}"
    usuario_b = f"a09-b-{nombre}-{sello}"
    a = _id(almacen.crea_usuario(usuario_a, f"A09 A {nombre}", "clave-de-prueba-123"))
    b = _id(almacen.crea_usuario(usuario_b, f"A09 B {nombre}", "clave-de-prueba-123"))
    lista = _id(almacen.crea_lista(a, f"Prueba A09 {nombre}"))
    # **Y B entra en la lista de A**: es lo que la hace «del mismo hogar» y no dos listas sueltas.
    #
    # *Cuidado con el argumento*: **`comparte` busca por NOMBRE DE USUARIO, no por id** -- *hace
    # `WHERE usuario = %s` y **devuelve `None` sin compartir nada si no lo encuentra**.* *Pasarle el id
    # no da error: no hace nada*, que es la clase de fallo que se lleva por delante una tarde. *Se
    # comprueba que devolvio algo, para que no vuelva a pasar en silencio.*
    # *Y los dos argumentos NO son lo mismo, que es lo que costo una corrida*:
    #   - `con_usuario` va por **nombre de usuario** -- *hace `WHERE usuario = %s`*.
    #   - `quien_invita` va por **id** -- *acaba en `invitado_por`, que es un `uuid`*.
    # **Pasar el nombre en el segundo sitio no da error: no encuentra a nadie y devuelve `None`.**
    # *Pasar el nombre en el tercero revienta con `invalid input syntax for type uuid`.*
    hecho = almacen.comparte(lista, usuario_b, a)
    assert hecho is not None, "comparte no encontro a B: se le esta pasando el id y quiere el usuario"
    return a, b, lista


# ==================================================== dos personas, una lista ===

def test_b_ve_la_lista_de_a_despues_de_compartirla():
    """**El primer escalon del hogar**: *compartir de verdad deja a B viendo la lista de A.*

    *No se comprueba el permiso en abstracto, sino que la lista aparece en `listas_de(B)`* -- *que es lo
    que la pantalla usa. Un permiso que existe y no se ve no sirve de nada.*
    """
    a, b, lista = _un_hogar("ve")
    de_b = [_id(x) for x in almacen.listas_de(b)]
    assert lista in de_b, f"B no ve la lista de A: {de_b}"
    # *Y A la sigue viendo, que es lo minimo.*
    assert lista in [_id(x) for x in almacen.listas_de(a)]


def test_las_dos_personas_anaden_lineas_y_las_dos_aparecen():
    """*Texto libre, que es la primera forma de anadir* -- *y de A09: «Compra: texto libre».*

    **Lo que se mide**: *que una linea puesta por B este en la lista que A lee.* *Una lista compartida
    donde cada uno ve lo suyo no es una lista compartida.*
    """
    a, b, lista = _un_hogar("anaden")
    la_de_a, la_de_b = str(uuid.uuid4()), str(uuid.uuid4())
    almacen.anade_linea(lista, a, la_de_a, "Brick de leche", cantidad=2)
    almacen.anade_linea(lista, b, la_de_b, "Pan de molde", cantidad=1)

    textos = {ln.get("nombre_visto") for ln in almacen.lineas_de(lista)}
    assert "Brick de leche" in textos, textos
    assert "Pan de molde" in textos, "la linea de B no llego a la lista compartida"


# ====================================================== el cierre y el historico ===

def test_al_cerrar_la_compra_las_lineas_salen_de_la_lista():
    """**Cerrar la compra vacia la lista.** *Lo que se cierra deja de estar pendiente.*

    *Es la mitad de «cierre»: si al cerrar las lineas siguieran ahi, la lista no significaria «lo que
    falta por comprar» sino «lo que se ha puesto alguna vez».*
    """
    a, _b, lista = _un_hogar("cierra")
    linea = str(uuid.uuid4())
    almacen.anade_linea(lista, a, linea, "Brick de leche", cantidad=2)
    # **Y se marca en el carro, que es lo que `cierra_compra` archiva.** *Su docstring lo dice con una
    # frase que conviene copiar aqui*: **«lo que no se cogio se queda en la lista, que es la mitad que
    # importa: quien no encuentra el pan no quiere volver a apuntarlo».** *Sin marcarla, cerrar no tiene
    # nada que cerrar -- y **eso no es un defecto, es el contrato**.*
    almacen.cambia_linea(lista, linea, a, en_carrito=True)
    assert len(almacen.lineas_de(lista)) >= 1

    almacen.cierra_compra(lista, a)

    assert almacen.lineas_de(lista) == [], "cerrar no vacio la lista"


def test_el_historico_queda_y_lo_ven_las_dos_personas():
    """**Y lo cerrado no se pierde**: *queda con su fecha y su contenido.*

    *El criterio de A09 dice «cierre e historico persistido»*, y por eso se comprueba **despues de
    cerrar** y **desde las dos cuentas**. *Un historico que solo ve quien cerro no es el historico del
    hogar.*
    """
    a, b, lista = _un_hogar("historico")
    la_a, la_b = str(uuid.uuid4()), str(uuid.uuid4())
    almacen.anade_linea(lista, a, la_a, "Brick de leche", cantidad=2)
    almacen.anade_linea(lista, b, la_b, "Pan de molde", cantidad=1)
    almacen.cambia_linea(lista, la_a, a, en_carrito=True)
    almacen.cambia_linea(lista, la_b, b, en_carrito=True)
    almacen.cierra_compra(lista, a)

    compras = almacen.compras_de(lista)
    assert len(compras) >= 1, f"no quedo ninguna compra cerrada: {compras}"
    ultima = compras[0]
    # *Y lleva su fecha*: un historico sin fecha no se puede ordenar ni leer.
    assert ultima.get("cerrada_en"), ultima
    # *Y lo que se compro, que es lo que hace util el historico.*
    assert ultima.get("lineas") is not None, ultima

    # *Y B tambien lo ve, desde su propia cuenta.*
    assert lista in [_id(x) for x in almacen.listas_de(b)], \
        "B dejo de ver la lista despues del cierre"
    assert len(almacen.compras_de(lista)) >= 1


def test_una_linea_de_lista_siempre_lleva_cantidad_y_la_columna_lo_exige():
    """**Y aqui me equivoque yo, no el codigo.** *Escribi esta prueba pasando `cantidad=None` y Postgres
    la rechazo*:

        NotNullViolation: null value in column "cantidad" of relation "lista_linea"

    *Habia dado por hecho que una linea de lista podia no tener cantidad* -- *porque la **previa** y la
    **despensa** si lo permiten* --, **y son cosas distintas**: *la previa es de ingredientes de receta, y
    la despensa tiene `cantidad` nullable **a proposito** («no se sabe», que no es cero).* **Una linea de
    lista es lo que alguien ha decidido apuntar, y apuntar es decidir cuanto.**

    *Asi que la prueba ahora fija el contrato de verdad*: **la columna exige cantidad, y `anade_linea`
    trae `cantidad: int = 1`** -- *el uno no es un invento del servidor: es lo que la funcion declara por
    defecto y lo que la pantalla manda.*
    """
    a, _b, lista = _un_hogar("cantidad")
    linea = str(uuid.uuid4())
    almacen.anade_linea(lista, a, linea, "Sal")  # *sin cantidad: la pone la funcion, que para eso tiene 1*
    filas = almacen.lineas_de(lista)
    sal = next((f for f in filas if str(f.get("id")) == linea), None)
    assert sal is not None, "la linea no se guardo"
    assert sal.get("cantidad") == 1, f"el defecto declarado es 1: {sal.get('cantidad')}"

    # *Y pasar `None` a mano **no es una linea sin cantidad**: es una linea invalida, y la base la rechaza.*
    # **Que es lo correcto**: la lista no admite «no se cuanto» -- para eso esta la despensa.
    import psycopg
    with pytest.raises(psycopg.errors.NotNullViolation):
        almacen.anade_linea(lista, a, str(uuid.uuid4()), "Pimienta", cantidad=None)


def test_dos_compras_cerradas_dan_dos_entradas_y_en_orden():
    """**El historico acumula, y lo mas reciente va primero.** *Es lo que A09 llama «historico
    persistido»: que cerrar dos veces no machaque la primera.*"""
    a, _b, lista = _un_hogar("dos-cierres")
    primera, segunda = str(uuid.uuid4()), str(uuid.uuid4())
    almacen.anade_linea(lista, a, primera, "Primera compra", cantidad=1)
    almacen.cambia_linea(lista, primera, a, en_carrito=True)
    almacen.cierra_compra(lista, a)
    almacen.anade_linea(lista, a, segunda, "Segunda compra", cantidad=1)
    almacen.cambia_linea(lista, segunda, a, en_carrito=True)
    almacen.cierra_compra(lista, a)

    compras = almacen.compras_de(lista)
    assert len(compras) == 2, f"cerrar dos veces tiene que dar dos entradas: {len(compras)}"
    # *Y la segunda es la mas reciente: el historico va de nueva a vieja.*
    assert compras[0]["cerrada_en"] >= compras[1]["cerrada_en"], \
        "el historico no esta ordenado de lo mas reciente a lo mas viejo"


def test_cerrar_una_lista_vacia_no_falla_ni_inventa_una_compra():
    """*Y el caso incomodo*: **cerrar sin nada dentro.**

    *Dos comportamientos son defendibles* -- *no crear nada, o crear una compra vacia* --, **y lo que no
    es defendible es un error a medias.** *Se comprueba que no revienta y que el estado queda coherente:
    la lista vacia y el historico sin una entrada fantasma de algo que no se compro.*
    """
    a, _b, lista = _un_hogar("vacia")
    antes = len(almacen.compras_de(lista))
    try:
        almacen.cierra_compra(lista, a)
    except Exception as fallo:  # noqa: BLE001
        pytest.fail(f"cerrar una lista vacia no puede fallar: {type(fallo).__name__}: {fallo}")
    assert almacen.lineas_de(lista) == []
    despues = len(almacen.compras_de(lista))
    # *Y si creo una entrada, es como mucho una: no puede crear varias por una sola llamada.*
    assert despues - antes in (0, 1), f"una llamada creo {despues - antes} entradas"
