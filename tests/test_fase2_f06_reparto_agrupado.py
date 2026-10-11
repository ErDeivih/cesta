"""F06 (fase 2): el reparto se decide con costes **sin agrupar**, y por eso pierde el que ahorra.

Por que existe
--------------
La revision de fase 2 lo dejo como hallazgo: *«Multi-tienda sin demostrar — el oraculo cubre
aritmetica, no asignaciones multi-tienda»*, y pide *«oraculo exhaustivo independiente de asignaciones
y promociones condicionadas al conjunto»*. Esto es el primer trozo: **la discrepancia, reproducida.**

El defecto esta en el cableado de `reparto_por_tienda`, y son cinco lineas:

    por_cadena[fuente] = [_resolver(p, fuente, mejor) for p in peticiones]   # SIN agrupar
    ...
    resueltas = _agrupa_y_reparte([e for e in elecciones if e])              # agrupadas, LOCAL
    ...
    repartido = _mejor_reparto(peticiones, por_cadena, max_t, una_tienda)    # recibe las SIN agrupar

**`una_tienda` se calcula con los costes agrupados y `_mejor_reparto` compara con los de linea.** Los
dos lados de la comparacion se calculan distinto, y el resultado es que **el reparto se infravalora**:
dos lineas del mismo producto en una tienda cuestan de verdad menos que la suma de sus partes, asi que
al optimizador le parece caro concentrarlas y **se pierde el reparto que si ahorra**.

*Es el criterio de aceptacion de F06 fallando, con sus palabras:* **«suma de partes igual al total»**.

El escenario de abajo, con numeros
----------------------------------
    alcampo   el mismo producto p1 en dos lineas de 2 unidades, a 1,00 EUR, con 3x2
              -> por linea: 2,00 + 2,00 = 4,00   (ninguna llega a tres)
              -> agrupado:  4 unidades, un grupo de 3 -> 3,00
              y la tercera linea p2 a 1,00 EUR con 3x2 -> 1,00
    dia       solo p2, a 0,50 EUR

    una tienda, alcampo ............ 4,00   (agrupado: 3,00 + 1,00)
    reparto  p1 en alcampo, p2 en dia   3,00 + 0,50 = 3,50   <- el bueno
    lo que dice hoy el optimizador      4,00 + 0,50 = 4,50   <- p1 sin agrupar

    ahorro real del reparto: 0,50 EUR.  El motor cree que el reparto CUESTA 0,50 mas.
"""
from __future__ import annotations

from plataforma.api import cesta


def eleccion(pid, fuente, unidades, precio, promo=None):
    """Una eleccion con **su coste por linea**, que es lo que devuelve `_resolver`."""
    return cesta.Eleccion(pid, f"Producto {pid}", fuente, unidades, unidades * precio,
                          unidades * precio, promo, None, linea_id=pid, identidad="exacto",
                          autorizada=True)


def peticion(pid, cantidad):
    return cesta.Peticion(grupo_id=1, producto_id=None, cantidad=cantidad, nombre=pid, id=pid)


def _reparto(monkeypatch, por_cadena, peticiones):
    """`donde_comprar` de verdad -- **el optimizador** --, con el catalogo sustituido.

    *Se sustituye `_resolver`, no `_candidatos`: lo que se prueba es el cableado que agrupa -- o que no
    agrupa -- antes de decidir, y eso pasa despues de resolver.* **`reparto_por_tienda` no es esta
    funcion**: aquella respeta las tiendas que la persona ya decidio, y no optimiza nada.
    """
    monkeypatch.setattr(cesta, "_candidatos", lambda *a, **k: {})
    monkeypatch.setattr(cesta, "_resolver",
                        lambda p, fuente, mejor: por_cadena.get(fuente, {}).get(p.id))
    return cesta.donde_comprar(peticiones, ["alcampo", "dia"], max_tiendas=2)


# El mismo producto en dos lineas: p1. Y otro producto: p2.
LINEAS = [peticion("p1", 2), peticion("p1", 2), peticion("p2", 1)]
# Dos lineas de p1 se distinguen por su `id`, pero `_agrupa_y_reparte` agrupa por producto y cadena.
LINEAS[1].id = "p1b"

POR_CADENA = {
    "alcampo": {
        "p1": eleccion("p1", "alcampo", 2, 100, "3x2"),
        "p1b": eleccion("p1", "alcampo", 2, 100, "3x2"),
        "p2": eleccion("p2", "alcampo", 1, 100, "3x2"),
    },
    "dia": {"p2": eleccion("p2", "dia", 1, 50)},
}


def test_el_reparto_se_decide_con_los_costes_agrupados(monkeypatch):
    """**La suma de las partes tiene que ser el total de verdad de cada tienda.**

    *p1 con 3x2 son 3,00 EUR en alcampo -- cuatro unidades, un grupo de tres --, no 4,00; y con p2 a
    0,50 en dia el reparto cuesta 3,50, no 4,50.*
    """
    salida = _reparto(monkeypatch, POR_CADENA, LINEAS)
    repartido = salida["repartido"]

    assert repartido is not None, (
        f"el reparto de p1 a alcampo y p2 a dia ahorra 0,50 EUR y tiene que proponerse: {salida}")
    assert repartido["total_cent"] == 350, (
        f"el reparto cuesta 3,50 EUR (p1 agrupado en alcampo, 3,00, mas p2 en dia, 0,50); "
        f"decir {repartido['total_cent']} es cobrar p1 sin agrupar: {repartido}")


def test_una_sola_tienda_ya_calculaba_agrupado(monkeypatch):
    """*El otro lado, para que se vea que la incoherencia es entre los dos.*

    La referencia de una sola tienda **si** agrupa: alcampo son 4,00 EUR, no 5,00. *Y el reparto tiene
    que compararse contra ese numero, no contra otro.*
    """
    salida = _reparto(monkeypatch, POR_CADENA, LINEAS)

    alcampo = next(x for x in salida["una_tienda"] if x["cadena"] == "alcampo")
    assert alcampo["total_cent"] == 400, (
        f"alcampo: p1 agrupado 3,00 + p2 1,00 = 4,00 EUR: {alcampo}")
    # Y el ahorro del reparto sale de restar dos numeros calculados **igual**.
    repartido = salida["repartido"]
    assert repartido["ahorro_cent"] == alcampo["total_cent"] - repartido["total_cent"], (
        f"el ahorro tiene que ser la resta de los dos totales: {repartido}")
