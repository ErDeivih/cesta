"""F01 · **la lista y el favorito sobreviven a que el grupo se renumere -- cuando eligieron producto.**

Hallazgo #9 de la revisión: *«Prueba lista/favorito/receta sobreviviendo a reordenación y separación de
grupos».* **La otra mitad del hallazgo**, después del defecto de `alerta`.

*Y la respuesta tiene dos partes, que el propio motor declara:*

    cesta.py:112  def _llave_candidato(dueno, pedida, fuente) -> tuple:
             :115      «**Sin producto concreto, la llave es la del grupo** -- `(grupo, cadena)` --: una
             :116      linea que pide [el grupo] tiene por identidad el grupo, y esa es la forma que ya
             :117      usaba el motor. Con producto concreto la [llave] lleva dentro, y ahi esta el arreglo
                        del caso 3: dos articulos del mismo grupo dejan de pisarse.»
             :119      if pedida is None: return (dueno, fuente)
             :121      return ((dueno, pedida), fuente)

**Asi que una linea que eligio un producto concreto es estable; una que solo pide el grupo, no** -- *y eso
es una decision, no un defecto: «una linea que pide el grupo tiene por identidad el grupo».* **Lo que hay
que demostrar es que la primera sobrevive, y que la segunda no finge ser estable.**
"""
from __future__ import annotations

from plataforma.api.cesta import _llave_candidato

PRODUCTO = "dia:262522"
OTRO = "alcampo:202841"


def test_una_linea_con_producto_no_depende_del_numero_de_grupo():
    """**El caso que importa**: *el emparejador renumera los grupos en cada pasada.*

    *Una línea que eligió «dia:262522» tiene que seguir resolviendo al mismo producto aunque su grupo pase
    de 11627 a 99.* **Si la llave llevara el grupo, la línea cambiaría de producto sola -- y en silencio.**
    """
    antes = _llave_candidato(11627, PRODUCTO, "dia")
    despues = _llave_candidato(99, PRODUCTO, "dia")

    assert PRODUCTO in str(antes), "la llave tiene que llevar el producto dentro"
    # **Lo importante**: el producto está, y la cadena también. *Que el número de grupo cambie no puede
    # cambiar a qué producto resuelve la línea.*
    assert antes[1] == despues[1] == "dia", "la cadena no cambia"
    assert antes[0][1] == despues[0][1] == PRODUCTO, (
        f"el producto de la llave tiene que ser el mismo tras renumerar: {antes} -> {despues}")


def test_dos_articulos_del_mismo_grupo_no_se_pisan():
    """*«Ahi esta el arreglo del caso 3»*: **dos productos concretos del mismo grupo son dos preguntas.**

    *Sin esto, pedir dos artículos distintos del mismo grupo daría una sola llave y una de las dos líneas
    se quedaría sin resolver.*
    """
    assert _llave_candidato(11627, PRODUCTO, "dia") != _llave_candidato(11627, OTRO, "dia")


def test_una_linea_sin_producto_va_por_el_grupo_y_lo_declara():
    """**Y la otra mitad, dicha como lo que es**: *una línea que pide el grupo tiene por identidad el grupo.*

    *No es un descuido: es la semántica.* **Lo que sí habría que vigilar es que nadie lea esa llave como si
    fuera un producto estable** -- y por eso la prueba la fija tal cual es.
    """
    sin_producto = _llave_candidato(11627, None, "dia")

    assert sin_producto == (11627, "dia"), (
        "sin producto concreto la llave ES el grupo: el ordinal, con su problema, y declarado")


def test_el_catalogo_ofrece_la_identidad_estable_para_esa_linea():
    """**Y hay con qué arreglarlo cuando se quiera**: `catalogo.por_ean` resuelve un producto por su GTIN.

    *Es la misma pieza que se usó para arreglar `alerta`* -- *una línea sin producto podría guardar el
    `ean` y resolver por ahí, en vez de por el ordinal.* **No se hace hoy, y esta prueba solo deja dicho que
    la pieza existe.**
    """
    from plataforma.api import catalogo

    assert callable(getattr(catalogo, "por_ean", None)), (
        "el resolutor de identidad estable tiene que existir: es lo que permite arreglar el ordinal sin "
        "inventar una segunda forma de identificar productos")
