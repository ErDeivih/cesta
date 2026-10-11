"""F11 / `R08`: **la despensa declarada** -- version local pequeña, no inventario logistico.

El criterio (`docs/SUPERAPP-COMPETENCIA-Y-REA.md:108`) dice:

> **Existencias declaradas**, ubicacion/caducidad **opcional**; **compra no acredita consumo ni stock restante**.

**Y su aceptacion** (`SUPERAPP-FASE2-EMPEZAR-A-QUI.md:159`) nombra cuatro casos: **consumo parcial**, **stock
desconocido**, **unidades incompatibles** y **fecha ausente**.

**Medido el 11 de octubre de 2026** (`docs/investigaciones/F11-despensa.md` §2), *la despensa **no existe** -- y lo
dicen **cuatro capas**: ninguna de las 13 tablas es de despensa, no hay `api/despensa.py`, la pantalla solo tiene
**«Stock Fuera»** (que es una mecanica de cadena), y `preferencia` esta **vacia**.*

## Y la regla central ya estaba escrita, en otro sitio

**`core/diario.py:140` la tiene desde antes:**

> *«**Rechaza `compra` a proposito.** **Comprar no es comer**: si una compra entrara aqui...»*

**Y `R08` dice lo mismo con otras palabras**: *«**compra no acredita consumo ni stock restante**»* -- *comprar algo
**no quiere decir** que se haya consumido, ni que quede, ni que no.*

> **Es la misma disciplina que atraviesa toda la fase**: *`sin_precio` (un cero afirmaria que salio gratis),
> `nombre_visto`, `fuente_dato`... **y aqui: una compra no es un consumo.***

## Y lo que este modulo hace, y lo que **no**

**Hace tres cosas**: *declarar lo que hay, **descontar lo que se consume**, y **decir lo que falta** para una
receta -- con sus unidades y **sin inventar** lo que no se sabe.*

**Y no hace la cuarta, a proposito**: ***no hay ninguna funcion que sume una compra a la despensa.*** *No es un
olvido: es **la regla del criterio puesta en el camino** -- *si la funcion no existe, no se puede llamar por
error.* **Es la misma forma que el `raise` de `diario.py:154`** (*una receta sin version no entra*).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from core.normalize import _UNIDADES

#: *Lo que **no** se sabe, dicho.* **Una existencia sin cantidad es distinta de una con cero** -- *y por eso no se
#: guarda como `0`, que afirmaria que no queda nada.*
DESCONOCIDA = "desconocida"


def _a_canonica(cantidad: float, unidad: str | None) -> tuple[float, str] | None:
    """**La cantidad, en la unidad canonica** -- *o `None` si la unidad no se conoce.*

    *Es la respuesta a **«unidades incompatibles»**, el tercer caso de la aceptacion*: **`kg` y `g` son la misma
    unidad** (la tabla de `core.normalize` lo sabe: `"g": ("kg", 0.001)`), **y `kg` y `ud` no lo son.**

    *Y devuelve `None` en vez de dejar la unidad como venga*: **una existencia en una unidad que no se sabe
    convertir no se puede descontar de nada** -- *y decirlo es mejor que restar dos numeros que no son lo mismo.*
    """
    clave = (unidad or "").strip().lower()
    if clave not in _UNIDADES:
        return None
    canon, factor = _UNIDADES[clave]
    return float(cantidad) * factor, canon


@dataclass
class Existencia:
    """**Lo que hay declarado de un producto.** *No lo que se compro: **lo que queda**.*

    *`cantidad` puede ser `None`, y entonces **es que no se sabe** (`DESCONOCIDA`) -- que es **distinto de cero**,
    y es el segundo caso de la aceptacion.*
    """

    texto: str
    cantidad: float | None = None
    unidad: str = ""
    #: *Ubicacion y caducidad son **opcionales**, como pide el criterio.*
    donde: str = ""
    caduca: str = ""

    @property
    def se_sabe(self) -> bool:
        """*Si se sabe cuanto hay.* **Una existencia sin cantidad no se puede descontar** -- *y no es un error:
        es lo que hay.*"""
        return isinstance(self.cantidad, (int, float))

    @property
    def canonica(self) -> tuple[float, str] | None:
        """*(cantidad, unidad canonica), o `None` si no se sabe o la unidad no se conoce.*"""
        if not self.se_sabe:
            return None
        return _a_canonica(self.cantidad or 0.0, self.unidad)


@dataclass
class Despensa:
    """**Lo que hay en casa, declarado.** *Y las tres operaciones que el criterio pide.*"""

    existencias: dict[str, Existencia] = field(default_factory=dict)

    def declara(self, texto: str, cantidad: float | None = None, unidad: str = "",
                donde: str = "", caduca: str = "") -> Existencia:
        """**Declarar lo que hay** -- *y **sobrescribe**, porque declarar es decir lo que hay **ahora**.*"""
        e = Existencia(texto=str(texto).strip(), cantidad=cantidad,
                       unidad=(unidad or "").strip().lower(), donde=donde, caduca=caduca)
        self.existencias[e.texto.lower()] = e
        return e

    def consume(self, texto: str, cantidad: float, unidad: str = "") -> tuple[Existencia | None, str]:
        """**Descontar lo que se gasta** -- *el primer caso de la aceptacion, «consumo parcial».*

        **Y devuelve un motivo cuando no puede**, en vez de restar a ciegas. *Tres motivos, y son distintos:*

        - **no esta declarado** -- *no se puede descontar lo que no se ha declarado*
        - **no se sabe cuanto hay** -- *«stock desconocido»: **queda menos, y no se sabe cuanto*** -- *asi que se
          pasa a `DESCONOCIDA`, que es **decir la verdad** en vez de inventar un numero*
        - **la unidad no se puede convertir** -- *«unidades incompatibles»: **no se resta `kg` de `ud`***

        *Y devuelve la existencia **como queda**, para poder enseñarla.*
        """
        clave = str(texto).strip().lower()
        e = self.existencias.get(clave)
        if e is None:
            return None, "no esta declarado"

        objetivo = _a_canonica(cantidad, unidad or e.unidad)
        if objetivo is None:
            return e, f"la unidad no se puede convertir: {unidad or e.unidad or '(ninguna)'}"
        suyo = e.canonica

        # **Sin cantidad declarada, consumir la deja desconocida** -- *el segundo caso de la aceptacion.*
        if suyo is None:
            e.cantidad = None
            e.unidad = DESCONOCIDA
            return e, "queda menos, y no se sabe cuanto"

        # **Y si la unidad de la existencia no se puede convertir con la que se gasta, no se resta.**
        if suyo[1] != objetivo[1]:
            return e, f"unidades incompatibles: {suyo[1]} y {objetivo[1]}"

        resto = suyo[0] - objetivo[0]
        if resto <= 0:
            # *Se acabo: se borra la existencia, **no se deja un cero** -- que afirmaria que hay «cero kg», y no
            # es lo mismo que no haberlo.*
            del self.existencias[clave]
            return Existencia(texto=e.texto, cantidad=0.0, unidad=suyo[1]), "se acabo"
        e.cantidad, e.unidad = resto, suyo[1]
        return e, ""

    def lo_que_falta(self, ingredientes: list[dict]) -> tuple[list[dict], list[dict]]:
        """**Lo que hay y lo que falta** para una receta -- *que es lo que `R10` pide explicar.*

        *Devuelve `(disponibles, faltantes)`, y **cada faltante lleva su motivo** -- *la misma forma que
        `sin_cantidad`, `sin_consolidar` y `faltantes`: **lo que no se puede hacer se dice, con su razon**.*
        """
        disponibles: list[dict] = []
        faltantes: list[dict] = []

        for ing in ingredientes:
            texto = str(ing.get("texto") or "").strip()
            if not texto:
                continue
            e = self.existencias.get(texto.lower())
            if e is None:
                faltantes.append({"texto": texto, "motivo": "no esta en la despensa"})
                continue
            if not e.se_sabe:
                # *Hay, y no se sabe cuanto: **se cuenta como disponible**, porque lo que se pregunta es si
                # hace falta comprarlo -- y no hace.*
                disponibles.append({"texto": texto, "hay": DESCONOCIDA})
                continue
            disponibles.append({"texto": texto, "hay": e.cantidad, "unidad": e.unidad})

        return disponibles, faltantes
