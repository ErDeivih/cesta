"""G11, punto 211: **el umbral se aplica a la CESTA, no a la linea.**

G11 lo manda asi: *«Revisar optimizacion por linea cuando el precio depende del grupo comprado en una
tienda. Repartir primero el descuento de una cesta completa y elegir luego las partes mas baratas
puede romper las condiciones del descuento: **comprobarlo y recalcular promociones por asignacion
efectiva**»*.

**El defecto, medido antes de arreglarlo.** `Mecanica.coste(unidades, precio_cent)` recibe **el precio
de un solo producto** y calcula `lleno = unidades * precio_cent`. Con «5 EUR dto comprando 20 EUR»:

    por linea:  4 lineas de 5,00 EUR   ->  4 x 500 = 2000 cent   (SIN descuento)
    una linea:  un producto de 20,00 EUR ->          1500 cent   (con descuento)
    la cesta:   son 20,00 EUR          ->  deberia ser 1500 cent

    DIFERENCIA: 500 cent = 5,00 EUR

*Y en un folleto «compra 20 EUR» es el total de la compra, no el de un articulo.* **No es una
limitacion teorica: es una oferta real que el modelo no podia representar.**

**Lo que hace esto, y lo que NO.** Aplica las mecanicas cuyo umbral depende del **conjunto** -- hoy,
`umbral` -- sobre el total de la cesta, y devuelve **cuanto se descuenta** y **como se reparte**.
*No toca `Mecanica.coste`: esa funciona, y sus 18 casos del oraculo lo demuestran.* **El reparto se
hace por asignacion efectiva: se reparte en proporcion a lo que aporta cada linea, y el resto de
céntimos se le da a las de mas importe, para que la suma cuadre exactamente** -- *que es lo que el
punto 213 exige: la suma de `importe_cent` tiene que dar el total, al céntimo.*
"""
from __future__ import annotations

from dataclasses import dataclass

from core import promos


@dataclass(frozen=True)
class LineaDeCesta:
    """Una linea: cuantas unidades y a que precio. *El `id` es para devolver el reparto.*"""
    id: str
    unidades: int
    precio_cent: int
    oferta: str = ""


def mecanicas_de_umbral(textos: list[str]) -> list[promos.Mecanica]:
    """Las mecanicas de esos textos cuyo **umbral depende del conjunto de la cesta**."""
    salida = []
    for texto in textos:
        if not texto:
            continue
        m = promos.lee(texto)
        if m.tipo == "umbral" and not m.acumulable and not m.solo_online:
            salida.append(m)
    return salida


def descuento_de_cesta(lineas: list[LineaDeCesta], textos: list[str]) -> int:
    """**Cuanto se descuenta la cesta entera.** *Cero si no llega al umbral.*

    El umbral se comprueba contra el total **ya sin las ofertas de linea**: *el folleto dice «compra
    20 EUR», y lo que se compra es el importe de las lineas.*
    """
    total = sum(ln.unidades * ln.precio_cent for ln in lineas)
    descuento = 0
    for m in mecanicas_de_umbral(textos):
        # `b` es el umbral en euros; `a` lo que se descuenta por cada tramo completo.
        tramo = m.b * 100 if m.b else 0
        if tramo <= 0:
            continue
        veces = total // tramo
        descuento += veces * m.a * 100
    # **Nunca mas que la cesta**: un descuento mayor que el importe no significa que te paguen.
    return min(descuento, total)


def reparto_del_descuento(lineas: list[LineaDeCesta], descuento_cent: int) -> dict[str, int]:
    """**El reparto por asignacion efectiva**, al céntimo y sin perder ninguno.

    *Se reparte en proporcion a lo que aporta cada linea; y el resto de la division se le da a las de
    mayor importe, que es lo que hace que la suma cuadre sin inventar céntimos.*
    """
    if descuento_cent <= 0 or not lineas:
        return {ln.id: 0 for ln in lineas}
    importes = {ln.id: ln.unidades * ln.precio_cent for ln in lineas}
    total = sum(importes.values())
    if total <= 0:
        return {ln.id: 0 for ln in lineas}
    bruto = {i: descuento_cent * imp // total for i, imp in importes.items()}
    resto = descuento_cent - sum(bruto.values())
    # El resto, a las de mas importe; y a igualdad, por `id` para que sea determinista.
    for i in sorted(importes, key=lambda i: (-importes[i], i))[:resto]:
        bruto[i] += 1
    return bruto
