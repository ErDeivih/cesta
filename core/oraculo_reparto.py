"""**El oraculo de asignaciones**: el minimo de verdad, enumerando todas, para cestas pequenas.

Por que existe
--------------
La revision de fase 2 lo pidio con estas palabras: *«oraculo exhaustivo independiente de asignaciones y
promociones condicionadas al conjunto»*. Y el criterio de F06 anade el resto:

    «Aplicar promociones a cada conjunto **realmente asignado** [...] No elegir partes de un descuento
     calculado sobre una cesta que al final no se compra en esa tienda.»
    «**Aceptacion:** casos combinatorios con contraejemplos, **discrepancias cero** para escenarios
     cubiertos, **suma de partes igual al total**; garantias y limites del algoritmo publicados.»

**Independiente quiere decir independiente.** Este modulo **no importa nada de
`plataforma/api/cesta.py`**: ni el optimizador, ni la aritmetica de promociones, ni la agrupacion. La
mecanica de la oferta **entra ya leida** (`Oferta`), asi que el oraculo no depende ni del parser de
castellano de folleto. *Si los dos coinciden, es porque los dos calculan bien, no porque compartan el
mismo codigo.*

Que cubre y que no
------------------
**Cubre** las mecanicas cuyo alcance no esta en duda: sin oferta, `nxm` (3x2), `enesima` (2a unidad
-50 %), `porcentaje`, `precio_fijo`, `lote` y `descuento_fijo`. *Todas se aplican al conjunto de
unidades de **ese producto en esa tienda**, que es lo que hace el motor.*

**No cubre `umbral`** («5 EUR dto comprando 20 EUR»), y a proposito: *el texto del folleto no dice si el
umbral es del producto o del ticket entero, y el motor ha elegido una lectura sin publicarla.* Medido el
13 de octubre de 2026: dos lineas **distintas** de 12 EUR con esa oferta dan **2400** centimos con la
lectura del motor y **1900** con la del ticket. **Mientras eso no se decida, un oraculo que la incluya
estaria eligiendo una de las dos lecturas y llamandola verdad.**

Como se usa
-----------
    peticiones = [PeticionDeLinea("l1", "p1", 2), PeticionDeLinea("l2", "p1", 2)]
    oferta = {"alcampo": {"l1": (100, Oferta("nxm", 3, 2)), "l2": (100, Oferta("nxm", 3, 2))},
              "dia":     {"l1": (80, SIN_OFERTA), "l2": (80, SIN_OFERTA)}}
    oraculo(peticiones, oferta, max_tiendas=2)
      -> {"total_cent": ..., "asignacion": {...}, "cadenas": [...], "exhaustivo": True}
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product as _producto_cartesiano


@dataclass(frozen=True)
class Oferta:
    """La mecanica de una oferta, **ya leida**. El oraculo no lee castellano de folleto."""

    tipo: str = "sin_regla"
    a: int = 0
    b: int = 0

    def coste(self, unidades: int, precio_cent: int) -> int:
        """Lo que se paga por esas unidades de ese producto. **Aritmetica propia**, a proposito."""
        if unidades <= 0 or precio_cent <= 0:
            return 0
        lleno = unidades * precio_cent
        if self.tipo == "sin_regla":
            return lleno
        if self.tipo == "nxm":                       # 3x2: de cada a unidades se pagan b
            grupos, sueltas = divmod(unidades, self.a)
            return grupos * self.b * precio_cent + sueltas * precio_cent
        if self.tipo == "enesima":                   # 2a unidad -50 %
            grupos, sueltas = divmod(unidades, self.a)
            rebajadas = grupos
            return round((unidades - rebajadas) * precio_cent
                         + rebajadas * precio_cent * (100 - self.b) / 100)
        if self.tipo == "porcentaje":
            return round(lleno * (100 - self.b) / 100)
        if self.tipo == "precio_fijo":               # cada unidad cuesta `a`
            return unidades * self.a
        if self.tipo == "lote":                      # `a` unidades por `b` centimos
            lotes, sueltas = divmod(unidades, self.a)
            return lotes * self.b + sueltas * precio_cent
        if self.tipo == "descuento_fijo":            # `a` centimos menos por unidad
            return max(0, lleno - unidades * self.a)
        raise ValueError(f"mecanica fuera del alcance del oraculo: {self.tipo!r}")


SIN_OFERTA = Oferta()


@dataclass(frozen=True)
class Linea:
    """Lo que la lista pide: **una linea**, con su producto y su cantidad."""

    linea_id: str
    producto_id: str
    cantidad: int


def coste_del_conjunto(lineas: list[tuple[Linea, int, Oferta]]) -> int:
    """**Lo que cuesta de verdad un conjunto de lineas que se compran en la MISMA tienda.**

    *Se agrupa por producto -- que es lo que hace una promocion de cantidad -- y cada linea aporta su
    `precio_cent` y su `Oferta`.* **Se suman las unidades de ese producto en esa tienda** y se aplica la
    oferta al total: *es la parte que el motor llama agrupar, y aqui esta escrita otra vez.*
    """
    por_producto: dict[str, list[tuple[Linea, int, Oferta]]] = {}
    for linea, precio, oferta in lineas:
        por_producto.setdefault(linea.producto_id, []).append((linea, precio, oferta))

    total = 0
    for grupo in por_producto.values():
        unidades = sum(x[0].cantidad for x in grupo)
        _linea, precio, oferta = grupo[0]
        total += oferta.coste(unidades, precio)
    return total


def oraculo(peticiones: list[Linea], oferta: dict[str, dict[str, tuple[int, Oferta]]],
            max_tiendas: int) -> dict:
    """**Todas las asignaciones, enumeradas.** El minimo de verdad para lo que se le pase.

    `oferta[cadena][linea_id] = (precio_cent, Oferta)`, y **una linea que no aparezca ahi no se puede
    comprar en esa cadena**: las asignaciones que la dejen sin sitio se descartan enteras, *porque un
    total al que le falta una linea no es un total, es otro numero.*

    Devuelve el mejor reparto de **una o mas** tiendas, y el mejor de **dos o mas** -- que es contra lo
    que se compara `donde_comprar`, que separa justo esas dos preguntas.
    """
    cadenas = sorted(oferta)
    if not peticiones or not cadenas:
        return {"total_cent": None, "asignacion": None, "cadenas": [], "exhaustivo": True,
                "reparto_dos_o_mas": None, "asignaciones_vistas": 0}

    mejor: dict | None = None
    mejor_dos: dict | None = None
    vistas = 0

    # **El producto cartesiano es la exhaustividad.** Cada linea elige tienda, sin descartar ninguna
    # combinacion por lista: *lo que se descarta despues es lo que no se puede comprar.*
    for combinacion in _producto_cartesiano(cadenas, repeat=len(peticiones)):
        usadas = sorted(set(combinacion))
        if len(usadas) > max_tiendas:
            continue
        vistas += 1

        por_cadena: dict[str, list[tuple[Linea, int, Oferta]]] = {}
        completa = True
        for linea, cadena in zip(peticiones, combinacion, strict=True):
            sitio = oferta.get(cadena, {}).get(linea.linea_id)
            if sitio is None:
                completa = False
                break
            por_cadena.setdefault(cadena, []).append((linea, sitio[0], sitio[1]))
        if not completa:
            continue

        total = sum(coste_del_conjunto(x) for x in por_cadena.values())
        candidato = {"total_cent": total,
                     "asignacion": dict(zip((x.linea_id for x in peticiones), combinacion,
                                            strict=True)),
                     "cadenas": usadas}
        if mejor is None or total < mejor["total_cent"]:
            mejor = candidato
        if len(usadas) >= 2 and (mejor_dos is None or total < mejor_dos["total_cent"]):
            mejor_dos = candidato

    salida = dict(mejor) if mejor else {"total_cent": None, "asignacion": None, "cadenas": []}
    salida["reparto_dos_o_mas"] = mejor_dos
    salida["exhaustivo"] = True
    salida["asignaciones_vistas"] = vistas
    return salida
