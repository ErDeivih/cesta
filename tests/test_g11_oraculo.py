"""G11, punto 210: **el oraculo por enumeracion exhaustiva, independiente del codigo de produccion.**

G11 lo pide asi: *«construir un oraculo por enumeracion exhaustiva en cestas pequenas,
**independiente del codigo de produccion**. Comparar asignaciones tienda/producto y coste final»*.

**Y por que tiene que ser independiente, lo dice el propio proyecto** en `banco_verdad.py`:
*«un control que comparte vocabulario con lo que vigila puede confirmar sus propios errores, y eso no
es medir: es repetir»*. *Un oraculo que llame a `promos.coste` para saber cuanto cuesta no comprueba
nada: **confirma lo que ya hacia**.*

Asi que aqui **no se importa `core.promos` ni `plataforma.api.cesta`**. La aritmetica de las ofertas
esta escrita **desde la definicion**, y la comparacion es contra la produccion. *Si las dos coinciden,
la coincidencia es un dato; si discrepan, es un defecto localizado en una de las dos.*

**Que se enumera.** No una cesta de la tienda, sino **todas las asignaciones** de una cesta pequena:
*un producto que tres cadenas venden a precios distintos, con sus ofertas, y la decision de **donde
comprarlo**.* El universo es pequeno a proposito: **enumeracion exhaustiva** quiere decir que se
miran **todas** las combinaciones, no las mas prometedoras. *Es el 208 leido al pie de la letra:
«evaluar todos los candidatos elegibles… no preseleccionar el menor €/unidad»*.
"""
from __future__ import annotations

from dataclasses import dataclass

import pytest

# --- La aritmetica del oraculo, escrita desde la definicion --------------------------------
#
# **Sin importar `promos`.** Cada regla es lo que dice el folleto, traducido a cuentas.

def coste_3x2(unidades: int, precio_cent: int, a: int = 3, b: int = 2) -> int:
    """Un 3x2 es «de cada 3, pagas 2». *Con 4 unidades pagas 3; con 5, pagas 4.*"""
    pagadas = (unidades // a) * b + (unidades % a)
    return pagadas * precio_cent


def coste_segunda(unidades: int, precio_cent: int, pct: int = 50) -> int:
    """Una 2a unidad al -50 %: *de cada dos unidades, una va rebajada.*"""
    rebajadas = unidades // 2
    enteras = unidades - rebajadas
    # El redondeo, al centimo, que es lo que se cobra.
    return round(enteras * precio_cent + rebajadas * precio_cent * (100 - pct) / 100)


def coste_club(unidades: int, precio_cent: int) -> int:
    """**El club no baja el precio de hoy.** *El dinero se acumula en un monedero.*"""
    return unidades * precio_cent


# --- La cesta y su enumeracion --------------------------------------------------------------

@dataclass(frozen=True)
class Precio:
    """Lo que cuesta un producto en una tienda, con su oferta."""
    tienda: str
    precio_cent: int
    oferta: str = ""          # "3x2" | "segunda" | "club" | ""


def coste_del_oraculo(p: Precio, unidades: int) -> int:
    """Lo que se paga **en caja** por esas unidades en esa tienda, segun el oraculo."""
    if p.oferta == "3x2":
        return coste_3x2(unidades, p.precio_cent)
    if p.oferta == "segunda":
        return coste_segunda(unidades, p.precio_cent)
    if p.oferta == "club":
        return coste_club(unidades, p.precio_cent)
    return unidades * p.precio_cent


def asignaciones(precios: list[Precio], unidades: int) -> list[tuple[Precio, int]]:
    """**TODAS las asignaciones**: cada tienda con su coste, ordenadas por coste.

    *No se descarta ninguna antes de calcular.* Es el 208: **el mas barato por unidad no es el mas
    barato al pagar**, asi que ordenar por €/unidad antes de mirar la oferta elegiria mal.
    """
    return sorted(((p, coste_del_oraculo(p, unidades)) for p in precios), key=lambda x: x[1])


# --- Y el cotejo contra la produccion -------------------------------------------------------

CASOS = [
    # (texto de la oferta, unidades, precio)  -- las mecanicas del 212
    ("3x2", 1), ("3x2", 2), ("3x2", 3), ("3x2", 4), ("3x2", 5), ("3x2", 6),
    ("2a unidad -50%", 1), ("2a unidad -50%", 2), ("2a unidad -50%", 3), ("2a unidad -50%", 4),
    ("Club Alcampo 15 % dto acum en tu tarjeta", 1),
    ("Club Alcampo 15 % dto acum en tu tarjeta", 4),
]


@pytest.mark.parametrize(("oferta", "unidades"), CASOS)
def test_el_oraculo_y_la_produccion_dan_lo_mismo(oferta: str, unidades: int):
    """**La comparacion del 210**, mecanica a mecanica y cantidad a cantidad.

    *El oraculo calcula desde la definicion; la produccion, con `promos.lee(...).coste(...)`.*
    Si coinciden, coinciden dos implementaciones escritas por separado.
    """
    from core import promos

    precio = 100
    mio = coste_del_oraculo(Precio("x", precio, "3x2" if oferta == "3x2" else
                                   ("segunda" if "2a unidad" in oferta else "club")), unidades)
    suyo = promos.lee(oferta).coste(unidades, precio)
    assert mio == suyo, f"«{oferta}» con {unidades} unidades: oraculo {mio}, produccion {suyo}"


def test_el_mas_barato_por_unidad_puede_ser_el_mas_caro_al_pagar():
    """**El 208, con la aritmetica del oraculo.** *Es el caso que el 210 existe para poder ver.*

    Un envase de 1,00 EUR con 2a unidad al -50 % cuesta 1,50 por dos; uno de 0,90 EUR sin oferta
    cuesta 1,80. **El mas barato por unidad es el caro al pagar.**
    """
    con_oferta = Precio("a", 100, "segunda")
    sin_oferta = Precio("b", 90, "")
    # **Sin comparacion encadenada**: `a < b is False` se lee como `(a < b) and (b is False)`,
    # y eso no es lo que quiero decir. *El de la oferta es MAS CARO por unidad.*
    assert con_oferta.precio_cent > sin_oferta.precio_cent, (
        "el de la oferta es el mas caro por unidad: 1,00 contra 0,90")
    orden = asignaciones([con_oferta, sin_oferta], 2)
    assert orden[0][0] is con_oferta, "y si es el mas barato al pagar por dos"
    assert orden[0][1] == 150 and orden[1][1] == 180


def test_la_enumeracion_mira_todas_las_tiendas_y_no_descarta_ninguna():
    """**Exhaustiva quiere decir todas.** *Tres tiendas, ninguna descartada antes de calcular.*"""
    precios = [Precio("cara", 200, "3x2"), Precio("media", 150, ""), Precio("barata", 100, "club")]
    vistas = asignaciones(precios, 3)
    assert len(vistas) == 3, "las tres se evaluan"
    # A 3 unidades: cara 3x2 = 400, media 450, barata club = 300 (el club paga lleno pero es barata)
    assert dict((p.tienda, c) for p, c in vistas) == {"cara": 400, "media": 450, "barata": 300}
    assert vistas[0][0].tienda == "barata"
