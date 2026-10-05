"""Cuanto trajo cada cadena hoy, comparado con lo que esa cadena sabe traer.

**Por que existe, habiendo ya un control de cobertura.** En `core/cobertura.py` hay dos
controles, y los dos son buenos; lo que se les escapa es concreto:

  - `revisa()` compara **rama por rama contra el bronze anterior**. Eso caza "hoy falta Frescos
    entero", que es el caso del 18 de septiembre de 2026. Lo que no caza es una bajada lenta:
    desde el momento en que la captura de ayer ya viene corta, la de ayer es la vara y el
    hundimiento se mide contra si mismo. Alcampo paso de 37.019 filas de bronze a 24.120 a lo
    largo de dos dias y **ninguna rama se hundio de golpe**: todas bajaron un poco.
  - `sin_bronze()` mira las cadenas que **dijeron haber ido bien** y no dejaron fichero. Bien
    pensado (una cadena que se nego a escribir ya devuelve error), pero deja fuera justo el otro
    caso: la cadena que **falla y no escribe nada**. Alcampo no trajo una sola captura del 2 al 5
    de octubre y ningun control lo dijo: el verificador de la ingesta comprueba coherencia --lo
    que la cadena declaro, lo guardamos-- y una cadena que no llega a declarar nada es coherente
    consigo misma.

De ahi las dos decisiones de aqui:

  1. **La referencia es el maximo de una ventana larga**, no la captura de ayer ni la mediana de
     los ultimos dias. La pregunta no es "trajiste lo mismo que ayer" sino "trajiste lo que esta
     cadena es capaz de traer". Con la mediana, la captura corta se acaba dando por buena.
  2. **Se mira cada cadena, haya dicho lo que haya dicho.** Que una cadena falle y no traiga nada
     es exactamente lo que hay que ver, no una razon para no mirar.

    uv run python -m projects.cesta.cobertura_diaria                # hoy
    uv run python -m projects.cesta.cobertura_diaria --fecha 2026-10-02 --dias 30

Sale 0 si todas traen lo suyo y 1 si alguna se quedo corta o no trajo nada. **No arregla nada:
avisa**, y en la cadena diaria se llama sin hacer fallar el dia --como `verificar_docs`--, porque
una cadena corta no es motivo para no recoger las otras cuatro.
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys

import duckdb

from core import config

FUENTES = ("alcampo", "aldi", "carrefour", "dia", "mercadona")

# Por debajo de esto, la captura se considera corta. Alcampo paso de 37.019 a 24.120 filas (el
# 65 %) sin que saltara nada, asi que el umbral tiene que estar muy por encima de ese 65 %: una
# cadena que pierde uno de cada tres productos esta rota, y una que pierde uno de cada diez
# tambien merece que alguien lo mire.
MINIMO_PCT = 90.0
DIAS_DE_VENTANA = 30


def filas_por_dia(dias: int = DIAS_DE_VENTANA) -> dict[str, dict[str, int]]:
    """{fuente: {fecha: filas}} leido del bronze. Sin ficheros, un diccionario vacio."""
    carpeta = config.DATA / "bronze"
    if not carpeta.exists():
        return {}
    patron = (carpeta / "**" / "*.parquet").as_posix()
    con = duckdb.connect()
    con.execute("SET enable_progress_bar=false")
    try:
        filas = con.execute(
            f"""SELECT CAST(fecha AS VARCHAR) AS fecha, fuente, count(*) AS n
                FROM read_parquet('{patron}', hive_partitioning=true)
                WHERE fecha IS NOT NULL
                GROUP BY 1, 2""").fetchall()
    except Exception:  # noqa: BLE001
        return {}
    salida: dict[str, dict[str, int]] = {}
    for fecha, fuente, n in filas:
        salida.setdefault(fuente, {})[fecha] = n
    return salida


def veredicto(serie: dict[str, int], hoy: str, dias: int = DIAS_DE_VENTANA,
              minimo_pct: float = MINIMO_PCT) -> dict:
    """Como de corta es la captura de `hoy` frente al maximo de la ventana.

    `serie` es {fecha: filas} de UNA cadena. Devuelve, con nombres que se puedan leer en un
    aviso: `hoy`, `filas`, `referencia` (el maximo de la ventana, sin contar hoy), `pct`,
    `dias_sin_datos` (huecos dentro de la ventana) y `veredicto` (`ok`, `corta` o `sin datos`).

    El maximo y no la mediana, a proposito: ver la cabecera. Sin contar hoy, para que una captura
    buena no suba su propia vara.

    **La ventana es el calendario, no las fechas que hay en la serie.** Un dia sin fichero no
    aparece en `serie` --no hay nada que leer--, y la primera version contaba los huecos mirando
    la serie, asi que una cadena que llevaba cuatro dias sin traer nada salia con **cero huecos**.
    Justo el caso que esto existe para cazar.
    """
    fin = dt.date.fromisoformat(hoy)
    calendario = [(fin - dt.timedelta(days=i)).isoformat() for i in range(1, dias + 1)]
    referencia = max((serie.get(f, 0) for f in calendario), default=0)
    filas_hoy = serie.get(hoy, 0)
    pct = (100.0 * filas_hoy / referencia) if referencia else 0.0
    dias_sin_datos = sum(1 for f in calendario if not serie.get(f))
    if filas_hoy == 0:
        estado = "sin datos"
    elif referencia and pct < minimo_pct:
        estado = "corta"
    else:
        estado = "ok"
    return {"hoy": hoy, "filas": filas_hoy, "referencia": referencia,
            "pct": round(pct, 1), "dias_en_la_ventana": len(calendario),
            "dias_sin_datos": dias_sin_datos, "veredicto": estado}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--fecha", help="el dia a mirar (por defecto, hoy)")
    ap.add_argument("--dias", type=int, default=DIAS_DE_VENTANA,
                    help="tamano de la ventana con la que se compara")
    ap.add_argument("--minimo-pct", type=float, default=MINIMO_PCT)
    a = ap.parse_args()

    hoy = a.fecha or dt.date.today().isoformat()
    series = filas_por_dia()
    if not series:
        print("No hay bronze que mirar todavia. Ejecuta el pipeline antes.")
        return 0

    print(f"la cobertura del {hoy}, contra el maximo de los {a.dias} dias anteriores\n")
    print(f"  {'cadena':<11}{'filas':>10}{'referencia':>12}{'%':>7}  {'huecos':>7}   veredicto")
    malas = []
    for fuente in FUENTES:
        v = veredicto(series.get(fuente, {}), hoy, dias=a.dias, minimo_pct=a.minimo_pct)
        huecos = f"{v['dias_sin_datos']}/{v['dias_en_la_ventana']}"
        print(f"  {fuente:<11}{v['filas']:>10,}{v['referencia']:>12,}{v['pct']:>6.1f}%  "
              f"{huecos:>7}   {v['veredicto']}".replace(",", "."))
        if v["veredicto"] != "ok":
            malas.append((fuente, v))

    print()
    if not malas:
        print("Todas las cadenas traen lo que suelen traer.")
        return 0
    print(f"{len(malas)} cadena(s) que no traen lo suyo:")
    for fuente, v in malas:
        if v["veredicto"] == "sin datos":
            print(f"  {fuente}: **no trajo nada** el {v['hoy']}. En la ventana faltan "
                  f"{v['dias_sin_datos']} de {v['dias_en_la_ventana']} dias.")
        else:
            print(f"  {fuente}: {v['filas']:,} filas contra {v['referencia']:,} de referencia "
                  f"({v['pct']}%).".replace(",", "."))
    print("\nMira el registro del dia: `data/ejecuciones.log` dice que cadena fallo y por que.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
