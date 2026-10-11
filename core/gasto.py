"""Cuanto se ha pagado, **y cuanto de eso no se sabe**.

**Por que existe.** G05 pide, en Compra: *«Gasto pagado semanal/mensual a partir de compras guardadas
e importes conocidos. **Separar fechas de compra y de precios. Cobertura de importes historicos `NULL`
visible**»*. Y hasta hoy, en la aplicacion **no se sumaba el gasto en ningun sitio**: la pagina se llama
«Gasto y ahorro» y sus diez secciones son del catalogo.

**La regla, y es la razon de que este modulo exista.** Un importe que falta **no es un cero**. Si se
suma como cero, el total sale redondo, mas bajo de lo real, y **nada en la pantalla dice que falta
algo**: es la forma mas silenciosa de mentir que tiene esta aplicacion. Aqui:

- `total_cent` suma **solo las lineas con importe**, y se acompana de **cuantas lineas entraron y
  cuantas no**;
- **un periodo sin ninguna linea con importe tiene `total_cent = None`, no `0`** -- *no es que se
  gastara cero, es que no se sabe*;
- y `completo` dice si el numero se puede leer como el total del periodo: **`False` en cuanto hay una
  linea sin importe**, aunque el total sea grande y creible.

**Y las dos fechas, que G05 pide separar.** La compra agrupa por **la fecha en que se cerro**, y cada
linea aporta **el importe que se archivo ese dia** -- no el precio de hoy. *Recalcular una compra de
ayer con los precios de hoy seria explicar lo que paso con datos que no existian*; es la misma razon
por la que la migracion 013 guarda `importe_cent`.

**Una compra sin lineas con importe no aporta un cero: no aporta nada, y se cuenta como un periodo del
que no se sabe.** Es la misma distincion que `{valor, faltantes}` en `estado/cocina.ts`, y la de la
columna «Recortados» del indice: *el dato que falta se declara.*
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import date, datetime
from typing import Any

MES = "mes"
SEMANA = "semana"


def _fecha_de_compra(fila: Mapping[str, Any]) -> date | None:
    """La fecha en que se cerro la compra. **No la del precio: la de la compra.**"""
    for clave in ("fecha_compra", "fecha", "cerrada_en", "creada_en"):
        valor = fila.get(clave)
        if valor is None:
            continue
        if isinstance(valor, datetime):
            return valor.date()
        if isinstance(valor, date):
            return valor
        texto = str(valor)[:10]
        try:
            return date.fromisoformat(texto)
        except ValueError:
            continue
    return None


def _importe(fila: Mapping[str, Any]) -> int | None:
    """El importe archivado de la linea, o `None` si no se sabe.

    **Cero no es lo mismo que no saberlo**: un `0` explicito (algo que salio gratis) cuenta como
    importe conocido y **no** como cobertura que falta.
    """
    for clave in ("importe_cent", "total_cent"):
        if clave in fila and fila[clave] is not None:
            try:
                return int(fila[clave])
            except (TypeError, ValueError):
                return None
    return None


def periodo_de(fecha: date, periodo: str) -> str:
    """La clave del periodo: `2026-10` para el mes, `2026-W42` para la semana ISO."""
    if periodo == SEMANA:
        anio, semana, _ = fecha.isocalendar()
        return f"{anio}-W{semana:02d}"
    return f"{fecha.year:04d}-{fecha.month:02d}"


def gasto_por_periodo(
    lineas: Iterable[Mapping[str, Any]], periodo: str = MES
) -> list[dict[str, Any]]:
    """El gasto por periodo, **con su cobertura**.

    `lineas` son lineas de compras cerradas: cada una con la fecha de **su compra** y su
    `importe_cent`, que puede faltar. Devuelve, por periodo y de mas antiguo a mas reciente:

        {"periodo", "total_cent", "lineas", "con_importe", "sin_importe", "completo"}

    **`total_cent` es `None` -- no `0` -- cuando ninguna linea del periodo tiene importe**, y
    `completo` es `False` en cuanto hay una sin importe. *Un total que parece completo y no lo esta
    es peor que no dar total.*
    """
    if periodo not in (MES, SEMANA):
        raise ValueError(f"periodo tiene que ser {MES!r} o {SEMANA!r}, y llego {periodo!r}")

    por_periodo: dict[str, dict[str, Any]] = {}
    sin_fecha = 0
    for fila in lineas:
        fecha = _fecha_de_compra(fila)
        if fecha is None:
            # **Una linea sin fecha no se puede poner en un periodo**, y meterla en el de hoy
            # inventaria una compra. Se cuenta aparte y se declara.
            sin_fecha += 1
            continue
        clave = periodo_de(fecha, periodo)
        acumulado = por_periodo.setdefault(
            clave,
            {"periodo": clave, "total_cent": 0, "lineas": 0, "con_importe": 0, "sin_importe": 0},
        )
        acumulado["lineas"] += 1
        importe = _importe(fila)
        if importe is None:
            acumulado["sin_importe"] += 1
        else:
            acumulado["total_cent"] += importe
            acumulado["con_importe"] += 1

    filas: list[dict[str, Any]] = []
    for clave in sorted(por_periodo):
        a = por_periodo[clave]
        # **Sin ninguna linea con importe no hay total: hay una ausencia.** Un cero aqui se leeria
        # como «ese mes no gaste nada», que es lo contrario de «no se sabe».
        conocido = a["con_importe"] > 0
        filas.append(
            {
                "periodo": clave,
                "total_cent": a["total_cent"] if conocido else None,
                "lineas": a["lineas"],
                "con_importe": a["con_importe"],
                "sin_importe": a["sin_importe"],
                "completo": a["sin_importe"] == 0,
            }
        )

    if sin_fecha:
        # Y lo que no se pudo colocar se dice, en vez de desaparecer del total sin avisar.
        filas.append(
            {
                "periodo": None,
                "total_cent": None,
                "lineas": sin_fecha,
                "con_importe": 0,
                "sin_importe": sin_fecha,
                "completo": False,
            }
        )
    return filas


# --- y el grano que hay de verdad: compras enteras ---------------------------
#
# `almacen.compras_de` **ya devuelve `total_cent`, `lineas` y `sin_precio`**: el cierre calculo el
# total y conto cuantas lineas no tenian precio, y lo archivo. *Su propio docstring lo dice: «la
# pantalla no las ensena hoy; esto existe para que el dia que se pidan no haya que volver a decidir el
# modelo»*. Asi que esto no recorre lineas: **agrupa compras que ya traen su cobertura** -- que es la
# forma `{valor, faltantes}` que el proyecto usa en `estado/cocina.ts`.


def _fecha_cierre(fila: Mapping[str, Any]) -> date | None:
    """La fecha en que se cerro la compra. `compras_de` la manda como `cerrada_en` en ISO."""
    return _fecha_de_compra(fila)


def gasto_de_compras(
    compras: Iterable[Mapping[str, Any]], periodo: str = MES
) -> list[dict[str, Any]]:
    """El gasto por periodo, **a partir de compras que ya traen su total y su cobertura**.

    Cada fila es una compra de `almacen.compras_de`: `cerrada_en`, `total_cent`, `lineas` y
    `sin_precio`. La diferencia con `gasto_por_periodo` es el grano -- *aqui la cobertura viene
    guardada por compra, no hay que contarla* --, y la regla es la misma:

    - **`total_cent` cuenta solo si la compra tiene algun importe conocido.** Una compra con
      `total_cent` a `None` **o con `sin_precio == lineas`** no aporta cero: **no aporta nada**, y el
      periodo se queda sin total conocido si no hay otra;
    - **`completo` es `False` en cuanto una compra tiene lineas sin precio**, aunque su total venga
      puesto: *ese total es el de las lineas que si lo tienen;*
    - y un periodo **sin ninguna compra con importe tiene `total_cent = None`, no `0`**.
    """
    if periodo not in (MES, SEMANA):
        raise ValueError(f"periodo tiene que ser {MES!r} o {SEMANA!r}, y llego {periodo!r}")

    por_periodo: dict[str, dict[str, Any]] = {}
    sin_fecha = 0
    for fila in compras:
        fecha = _fecha_cierre(fila)
        if fecha is None:
            sin_fecha += 1
            continue
        clave = periodo_de(fecha, periodo)
        a = por_periodo.setdefault(
            clave,
            {"periodo": clave, "total_cent": 0, "compras": 0, "con_importe": 0,
             "sin_importe": 0, "lineas_sin_precio": 0},
        )
        a["compras"] += 1
        lineas = int(fila.get("lineas") or 0)
        sin_precio = int(fila.get("sin_precio") or 0)
        # **El numero de LINEAS sin precio, no solo el de compras.** `compra.sin_precio` lo guarda
        # el cierre, y sin esto la pantalla solo podia decir «esta compra no esta completa», no
        # **cuanto** le falta. *Una cobertura que no dice cuanto falta informa a medias.*
        a["lineas_sin_precio"] += sin_precio
        total = fila.get("total_cent")
        # **Una compra de la que no se sabe el total no suma cero.** Se reconoce por las dos vias:
        # el total ausente, o que **ninguna** de sus lineas tuviera precio.
        sabe = total is not None and not (lineas > 0 and sin_precio >= lineas)
        if sabe:
            a["total_cent"] += int(total)
            a["con_importe"] += 1
        else:
            a["sin_importe"] += 1
        if sin_precio > 0:
            a["completo"] = False

    filas: list[dict[str, Any]] = []
    for clave in sorted(por_periodo):
        a = por_periodo[clave]
        filas.append(
            {
                "periodo": clave,
                "total_cent": a["total_cent"] if a["con_importe"] > 0 else None,
                "compras": a["compras"],
                "con_importe": a["con_importe"],
                "sin_importe": a["sin_importe"],
                "lineas_sin_precio": a["lineas_sin_precio"],
                "completo": a.get("completo", True),
            }
        )
    if sin_fecha:
        filas.append(
            {
                "periodo": None, "total_cent": None, "compras": sin_fecha,
                "con_importe": 0, "sin_importe": sin_fecha, "lineas_sin_precio": 0,
                "completo": False,
            }
        )
    return filas
