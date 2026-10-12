"""**Cuánto se tarda en vaciar una cola de fichas**, y por qué eso no es una división.

**Por qué existe.** *La cola tiene 72 319 fichas pendientes y no tenía fecha.* **«Pendiente» sin un
presupuesto no dice cuánto falta** -- *y una cola que no se puede fechar es una cola que no se puede
decidir.*

**Y no es una división porque cada cadena va a su ritmo.** *`config.RITMO` declara **peticiones por
segundo** -- y se comprobó leyendo cómo se usa: `Fetcher(rate_per_sec=config.RITMO[FUENTE])` --, y no son
parecidos:*

    mercadona 2,0   aldi 2,0   dia 1,0   carrefour 1,0   lidl 1,0   alcampo 0,15

**Alcampo va a una cada 6,7 segundos** -- *y su comentario dice por qué:*

> *«AWS WAF: una cada 4 s evitaba el corte que se veía a 1/s, pero el 8 sep el reto escaló a pedir un clic
> humano tras siete cortes. Menos presión es la única palanca que queda del lado del código.»*

**Así que el presupuesto no se calcula: se mide por cadena, y luego se suma.** *Y el resultado tiene una
forma que conviene mirar antes de decidir nada.*
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Tramo:
    """Una cadena: cuántas fichas le quedan y a qué ritmo se piden."""
    cadena: str
    fichas: int
    por_segundo: float

    @property
    def segundos(self) -> float:
        """**Lo que tarda este tramo**, *con el ritmo como denominador.*

        *`por_segundo` es peticiones por segundo, así que el tiempo de una ficha es su inverso.* **Un ritmo
        de cero no se puede invertir, y devolver `inf` es lo honesto**: *significa «a este paso no termina
        nunca», que es exactamente lo que un ritmo de cero quiere decir.*
        """
        if self.por_segundo <= 0:
            return float("inf")
        return self.fichas / self.por_segundo


def presupuesto(tramos: list[Tramo], horas_por_noche: float | None = None) -> dict:
    """**El total, el desglose, y cuántas noches son.**

    *`horas_por_noche` es lo que convierte segundos en una decisión.* **Se pasa y no se supone**: *una
    máquina que sólo está encendida por la tarde y una que lo está siempre dan números distintos, y elegir
    uno por cuenta propia sería inventarse el contexto.*
    """
    if not tramos:
        return {"segundos": 0.0, "horas": 0.0, "tramos": [], "noches": None, "el_mas_caro": None}

    with_tiempo = [(t, t.segundos) for t in tramos]
    total = sum(s for _, s in with_tiempo)
    # *El más caro, y no el más grande.* **Una cadena con pocas fichas a un ritmo lentísimo puede pesar
    # más que otra con muchas y rápidas** -- y es lo que hay que mirar primero.
    mas_caro = max(with_tiempo, key=lambda par: par[1])[0] if with_tiempo else None

    salida = {
        "segundos": total,
        "horas": total / 3600.0,
        "el_mas_caro": mas_caro.cadena if mas_caro else None,
        "tramos": [
            {"cadena": t.cadena, "fichas": t.fichas, "por_segundo": t.por_segundo,
             "horas": s / 3600.0,
             # *Y la parte del total que se lleva cada una*, que es lo que hace visible el desequilibrio.
             "parte": (s / total) if total > 0 else 0.0}
            for t, s in with_tiempo
        ],
    }
    # *Y las noches, sólo si se ha dicho cuántas horas tiene una.* **Sin ese dato no se contesta**, en vez
    # de suponer que una noche son ocho horas.
    salida["noches"] = (total / 3600.0 / horas_por_noche) if horas_por_noche else None
    return salida


def cuello_de_botella(datos: dict) -> str | None:
    """*La cadena que se lleva más de la mitad del tiempo*, si la hay.

    **Existe porque un total repartido entre seis cadenas y un total que es una sola cadena son dos
    problemas distintos** -- *y el número de horas no los distingue.*
    """
    for t in datos.get("tramos", []):
        if t["parte"] > 0.5:
            return t["cadena"]
    return None
