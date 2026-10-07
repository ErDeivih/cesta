"""Informe de cobertura del inventario, y sus pruebas: lo que S02 pide y hoy no existe.

**Que responde.** El encargo pide un panel de calidad separado del consumo: *"cobertura por
campo/cadena, edad de fichas, deuda de cola, fallos de parser, identidad desconocida y versiones
publicadas"* (SUPERAPP-02 §8). Esto es la parte de fichas, con el inventario que se acaba de
levantar.

**Las tres preguntas, y por que se contestan juntas:**

  - **¿Cuanta deuda hay?** Fichas en `pendiente` y fichas vencidas (con `proxima_revision` pasada):
    es el trabajo que la cola tiene delante.
  - **¿Que edad tienen las fichas?** Distribucion por tramos de `ficha_en`. Una ficha de hace ocho
    meses puede estar bien o puede estar contando una formula que ya no existe: no se puede saber sin
    la fecha, y por eso la fecha viaja con el dato desde S02.
  - **¿Que falta de verdad?** Cuantas fichas tienen `hash_util` (contenido util registrado) y cuantas
    no. Cero fichas con hash hoy es el resultado honesto, no un fallo del informe.

**Lo que este informe no dice:** nada sobre el surtido real de una cadena. Cuenta lo **descubierto**,
y el numero de descubiertos no demuestra cobertura completa de ninguna fuente.
"""
from __future__ import annotations

import argparse
import sys
from datetime import date, datetime

from core import inventario

TRAMOS = ((7, "menos de una semana"), (30, "menos de un mes"), (90, "menos de tres meses"),
          (365, "menos de un año"))


def _tramo(ficha_en: str | None, hoy: date) -> str:
    if not ficha_en:
        return "sin ficha"
    try:
        dias = (hoy - date.fromisoformat(ficha_en[:10])).days
    except ValueError:
        return "sin ficha"
    for limite, etiqueta in TRAMOS:
        if dias < limite:
            return etiqueta
    return "mas de un año"


def informe(con=None, *, hoy: date | None = None, ahora: datetime | None = None) -> dict:
    """Los numeros del inventario. Devuelve el diccionario ademas de imprimirlo, para poder probarlo."""
    propio = con is None
    con = con or inventario.conecta()
    dia = hoy or date.today()
    momento = (ahora or datetime.now()).isoformat()

    por_fuente: dict[str, dict] = {}
    for fila in con.execute("SELECT * FROM fichas"):
        fuente = por_fuente.setdefault(fila["fuente"], {
            "fichas": 0, "pendiente": 0, "en_curso": 0, "con_ficha": 0, "con_hash": 0,
            "vencidas": 0, "sin_ficha": 0, "edades": {}})
        fuente["fichas"] += 1
        fuente[fila["estado"]] = fuente.get(fila["estado"], 0) + 1
        if fila["ficha_en"]:
            fuente["con_ficha"] += 1
        else:
            fuente["sin_ficha"] += 1
        if fila["hash_util"]:
            fuente["con_hash"] += 1
        if fila["proxima_revision"] and fila["proxima_revision"] <= momento:
            fuente["vencidas"] += 1
        tramo = _tramo(fila["ficha_en"], dia)
        fuente["edades"][tramo] = fuente["edades"].get(tramo, 0) + 1

    total = {clave: sum(f.get(clave, 0) for f in por_fuente.values())
             for clave in ("fichas", "pendiente", "en_curso", "con_ficha", "con_hash", "vencidas")}

    print(f"Inventario de fichas · {total['fichas']:,} productos descubiertos "
          f"(no es el surtido de ninguna cadena)".replace(",", "."))
    print(f"  {'fuente':<11}{'fichas':>9}{'sin ficha':>11}{'con ficha':>11}{'con hash':>10}"
          f"{'vencidas':>10}")
    for fuente in sorted(por_fuente):
        f = por_fuente[fuente]
        print(f"  {fuente:<11}{f['fichas']:>9,}{f['sin_ficha']:>11,}{f['con_ficha']:>11,}"
              f"{f['con_hash']:>10,}{f['vencidas']:>10,}".replace(",", "."))
    print(f"  {'TOTAL':<11}{total['fichas']:>9,}{total['fichas'] - total['con_ficha']:>11,}"
          f"{total['con_ficha']:>11,}{total['con_hash']:>10,}{total['vencidas']:>10,}"
          .replace(",", "."))
    print(f"\n  deuda de cola: {total['pendiente']:,} pendientes · "
          f"{total['en_curso']:,} en curso · {total['vencidas']:,} vencidas".replace(",", "."))
    print("  edades de las fichas:")
    edades: dict[str, int] = {}
    for f in por_fuente.values():
        for tramo, cuantas in f["edades"].items():
            edades[tramo] = edades.get(tramo, 0) + cuantas
    for tramo in [e for _, e in TRAMOS] + ["mas de un año", "sin ficha"]:
        if edades.get(tramo):
            print(f"    {edades[tramo]:>7,}  {tramo}".replace(",", "."))
    print("\n  Este informe cuenta lo DESCUBIERTO, no el surtido de una cadena: un numero de filas")
    print("  no demuestra cobertura completa de ninguna fuente.")
    if propio:
        con.close()
    return {"total": total, "por_fuente": por_fuente, "edades": edades}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--fuente", help="solo una cadena")
    a = ap.parse_args(argv)
    if a.fuente:
        con = inventario.conecta()
        datos = informe(con)
        fuente = datos["por_fuente"].get(a.fuente)
        print(f"\n{a.fuente}: {fuente}" if fuente else f"\n{a.fuente}: sin fichas registradas")
        con.close()
        return 0
    informe()
    return 0


if __name__ == "__main__":
    sys.exit(main())
