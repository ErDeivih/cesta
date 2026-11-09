"""El minimo de cada producto y si el precio de hoy **vuelve** a el.

    .\\.venv\\Scripts\\python.exe -m projects.cesta.minimos

Lo que pide David (10/11, madrugada): *guardar el minimo visto y su fecha por
producto, y marcar cuando el precio vuelve a ese minimo.* Sin avisos emergentes:
una marca en la lista y este fichero de resumen.

Deja dos cosas, y las dos son el contrato con la API:

    data/minimos.parquet         una fila por producto, con su minimo y su fecha
    data/minimos-resumen.json    el resumen que se puede leer sin abrir un parquet

Por que «vuelve» no es «esta en el minimo»
------------------------------------------
La primera version marcaba **25.328 de 52.106** productos con precio hoy: casi
la mitad, porque un producto que repite el mismo precio todos los dias esta
siempre en su minimo. Eso no dice nada. **Volver es haber estado por encima y
haber vuelto**, asi que `vuelve_al_minimo` exige ademas que haya dias, entre la
fecha del minimo previo y hoy, con el precio por encima del minimo con la misma
tolerancia de 0,5 centimos que usa `plataforma/api/alertas.py`. Medido con esa
condicion el 9/11/2026 sobre el gold real: **1.480 productos vuelven de verdad**
y **125** son minimo nuevo. Esos son los numeros que valen.

El resto de decisiones, y por que:

  - **El minimo es de todo el historico disponible**, no de 90 dias: el proyecto
    tiene 64 dias y la funcion que pide David no dice ventana. `ventana_dias`
    viaja en el resumen para que quien lo lea sepa sobre cuantos dias se midio.
  - **Empates: la fecha mas antigua.** Es la primera vez que se alcanzo ese
    precio, y es la unica que se puede comprobar.
  - **Sin precio hoy no se marca** (`vuelve_al_minimo` y `nuevo_minimo` son
    falso, no nulo): no hay nada que comparar, y un nulo se leeria como un dato
    roto. El historico si se guarda: manana puede volver.
  - **Producto con un solo dia**: no tiene minimo previo, asi que no vuelve ni
    estrena minimo. El primer dia no es «su minimo historico».
  - **Los nombres salen de `grupos.parquet`** (`nombre`, `marca`, `grupo_id`),
    que es donde el emparejador los deja. Un `producto_id` suelto no le dice
    nada a nadie. Si el fichero no esta, el resumen sale sin nombres: peor es
    inventarlos.

Esto **no toca `data/gold`**: lo lee. El artefacto va a `data/` porque la API lo
monta junto a gold (`CESTA_GOLD=/datos/gold` -> `/datos/minimos.parquet`), y la
seleccion de solo lectura es del contenedor, no de este paso.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import polars as pl

from core import config
from core.storage import write_parquet_file

# La misma tolerancia que `plataforma/api/alertas.py` (medio centimo). Se repite
# aqui, y no se copia un valor distinto, porque las dos miden lo mismo: «¿este
# precio es el mismo?». La API importa su propio medio centimo para leer el
# artefacto; lo que impide que se separen es `test_minimos`, que compara la
# salida del pipeline con lo que la funcion de la API devuelve.
TOLERANCIA_CENT = 0.5

NOMBRE_ARTEFACTO = "minimos.parquet"
NOMBRE_RESUMEN = "minimos-resumen.json"

# Las columnas que necesita el calculo. Se piden explicitas: el gold de verdad
# trae mas de setenta en `grupos`, y leer de mas en un fichero de 2,8 millones de
# filas es tiempo que la pasada de la manana no tiene.
COLUMNAS = ("fuente", "id_fuente", "producto_id", "precio_cent",
            "precio_unidad_cent", "unidad_canon", "fecha")

# El esquema del artefacto, y el orden en que se escribe. Se declara a mano para
# que la tabla vacia (un gold sin precios) tenga la misma forma que la llena y la
# API no tenga que defenderse de dos artefactos distintos.
ESQUEMA = {
    "producto_id": pl.Utf8,
    "fecha_datos": pl.Utf8,
    "fuente": pl.Utf8,
    "id_fuente": pl.Utf8,
    "precio_hoy_cent": pl.Int64,
    "precio_hoy_unidad_cent": pl.Float64,
    "unidad_canon": pl.Utf8,
    "minimo_previo_cent": pl.Int64,
    "minimo_previo_fecha": pl.Utf8,
    "minimo_cent": pl.Int64,
    "minimo_fecha": pl.Utf8,
    "dias_con_precio": pl.Int64,
    "dias_por_encima": pl.Int64,
    "ultima_por_encima": pl.Utf8,
    "vuelve_al_minimo": pl.Boolean,
    "nuevo_minimo": pl.Boolean,
}

# Los campos de cada elemento de las dos listas del resumen, en el orden en que
# se leen. `nombre`, `marca` y `grupo_id` se anaden despues si `grupos.parquet`
# los trae.
CAMPOS_DESTACADOS = (
    "producto_id", "fuente", "id_fuente",
    "precio_hoy_cent", "precio_hoy_unidad_cent", "unidad_canon",
    "minimo_cent", "minimo_fecha",
    "minimo_previo_cent", "minimo_previo_fecha",
    "dias_por_encima", "ultima_por_encima",
)


def _ruta_diario(gold: Path) -> Path:
    return Path(gold) / "precio_diario.parquet"


def _lee_diario(gold: Path) -> pl.DataFrame:
    """El historico con las columnas justas del calculo."""
    return pl.read_parquet(_ruta_diario(gold), columns=list(COLUMNAS))


def calcula(gold: Path | None = None) -> pl.DataFrame:
    """El artefacto: una fila por producto con su minimo, su fecha y sus marcas.

    `gold` se puede pasar para las pruebas; sin el se lee el de la pasada
    (`config.GOLD`). No escribe nada: `escribe` es quien lo deja en disco.
    """
    gold = Path(gold) if gold is not None else config.GOLD
    diario = _lee_diario(gold)
    if diario.is_empty():
        return pl.DataFrame(schema=ESQUEMA)

    fecha_datos = diario["fecha"].max()
    con_precio = diario.filter(pl.col("precio_cent").is_not_null())

    # -- el producto de hoy: precio, precio por unidad y unidad del dia de datos --
    #
    # La fila de hoy puede existir con el importe vacio (`precio_cent` nulo). Es
    # «hoy no lo se», no un cero: viaja como nulo y las dos marcas quedan falsas.
    hoy = diario.filter(pl.col("fecha") == fecha_datos).select(
        "producto_id", "unidad_canon",
        pl.col("precio_cent").alias("precio_hoy_cent"),
        pl.col("precio_unidad_cent").alias("precio_hoy_unidad_cent"))

    # `fuente` e `id_fuente` son la identidad del producto (`producto_id` es
    # `fuente:id_fuente`); se toman una vez por producto y no de la fila de hoy,
    # porque un producto sin precio hoy tambien tiene identidad.
    identidad = diario.group_by("producto_id").agg(
        pl.col("fuente").first().alias("fuente"),
        pl.col("id_fuente").first().alias("id_fuente"))

    # -- el minimo de los dias ANTERIORES a hoy, y la primera vez que se alcanzo --
    previo = con_precio.filter(pl.col("fecha") < fecha_datos)
    min_previo = previo.group_by("producto_id").agg(
        pl.col("precio_cent").min().alias("minimo_previo_cent"))
    fecha_previo = (
        previo.join(min_previo, on="producto_id")
        .filter(pl.col("precio_cent") == pl.col("minimo_previo_cent"))
        .group_by("producto_id")
        .agg(pl.col("fecha").min().alias("minimo_previo_fecha")))
    previos = min_previo.join(fecha_previo, on="producto_id", how="left")

    # -- el minimo de TODO el historico hasta hoy, con su fecha --
    min_total = con_precio.group_by("producto_id").agg(
        pl.col("precio_cent").min().alias("minimo_cent"))
    fecha_total = (
        con_precio.join(min_total, on="producto_id")
        .filter(pl.col("precio_cent") == pl.col("minimo_cent"))
        .group_by("producto_id")
        .agg(pl.col("fecha").min().alias("minimo_fecha")))
    total = min_total.join(fecha_total, on="producto_id", how="left")

    dias = con_precio.group_by("producto_id").agg(
        pl.col("fecha").n_unique().cast(pl.Int64).alias("dias_con_precio"))

    # -- el «subio y volvio»: dias por encima del minimo previo, despues de el --
    #
    # Solo cuentan los dias **posteriores** a la fecha del minimo previo y
    # anteriores a hoy (los de `previo`, que no incluye hoy). Un producto que no
    # movio el precio desde su minimo no esta «volviendo»: esta quieto.
    por_encima = (
        previo.join(previos, on="producto_id", how="inner")
        .filter((pl.col("fecha") > pl.col("minimo_previo_fecha"))
                & (pl.col("precio_cent")
                   > pl.col("minimo_previo_cent") + TOLERANCIA_CENT))
        .group_by("producto_id")
        .agg(pl.col("fecha").n_unique().cast(pl.Int64).alias("dias_por_encima"),
             pl.col("fecha").max().alias("ultima_por_encima")))

    tabla = (
        diario.select("producto_id").unique()
        .join(identidad, on="producto_id", how="left")
        .join(hoy, on="producto_id", how="left")
        .join(previos, on="producto_id", how="left")
        .join(total, on="producto_id", how="left")
        .join(dias, on="producto_id", how="left")
        .join(por_encima, on="producto_id", how="left")
        .with_columns(
            pl.lit(str(fecha_datos)).alias("fecha_datos"),
            pl.col("dias_por_encima").fill_null(0).cast(pl.Int64))
        .with_columns(
            # `vuelve_al_minimo`: hay precio hoy, hay minimo de antes, el precio
            # esta a menos de medio centimo de el **y** subio y volvio.
            (
                pl.col("precio_hoy_cent").is_not_null()
                & pl.col("minimo_previo_cent").is_not_null()
                & (pl.col("precio_hoy_cent")
                   <= pl.col("minimo_previo_cent") + TOLERANCIA_CENT)
                & (pl.col("dias_por_encima") > 0)
            ).alias("vuelve_al_minimo"),
            # `nuevo_minimo`: hoy esta por debajo del minimo de antes con margen.
            (
                pl.col("precio_hoy_cent").is_not_null()
                & pl.col("minimo_previo_cent").is_not_null()
                & (pl.col("precio_hoy_cent")
                   < pl.col("minimo_previo_cent") - TOLERANCIA_CENT)
            ).alias("nuevo_minimo"),
        )
        .select(list(ESQUEMA))
        .sort("producto_id")
    )
    return tabla.cast(ESQUEMA)


def _ventana_dias(gold: Path) -> int:
    """Sobre cuantos dias distintos se ha medido. Se dice, no se adivina."""
    try:
        fechas = pl.read_parquet(_ruta_diario(gold), columns=["fecha"])
    except OSError:
        return 0
    return int(fechas["fecha"].n_unique())


def _nombres(gold: Path) -> pl.DataFrame | None:
    """`nombre`, `marca` y `grupo_id` de cada producto, si el gold los trae."""
    ruta = Path(gold) / "grupos.parquet"
    try:
        grupos = pl.read_parquet(
            ruta, columns=["fuente", "id_fuente", "nombre", "marca", "grupo_id"])
    except (OSError, pl.exceptions.PolarsError):
        return None
    return grupos.unique(subset=["fuente", "id_fuente"], keep="first")


def _elemento(fila: dict) -> dict:
    """Un producto del artefacto -> el elemento del resumen, con lo que se sabe."""
    elemento = {campo: fila.get(campo) for campo in CAMPOS_DESTACADOS}
    if fila.get("nombre") is not None:
        elemento["nombre"] = fila["nombre"]
        elemento["marca"] = fila.get("marca")
        elemento["grupo_id"] = fila.get("grupo_id")
    return elemento


def resumen(tabla: pl.DataFrame, gold: Path | None = None) -> dict:
    """El fichero de resumen de David, a partir del artefacto ya calculado.

    Los dos numeros que importan son el tamano de `vuelven_al_minimo` y el de
    `nuevos_minimos`: es lo que se comprueba de un vistazo cuando la pasada
    termina.
    """
    gold = Path(gold) if gold is not None else config.GOLD
    if tabla.is_empty():
        return {"fecha_datos": None, "ventana_dias": _ventana_dias(gold),
                "productos": 0, "con_historial": 0,
                "vuelven_al_minimo": [], "nuevos_minimos": [],
                "generado": config.ahora_local().isoformat(timespec="seconds")}

    nombres = _nombres(gold)
    destacados = tabla.filter(
        pl.col("vuelve_al_minimo") | pl.col("nuevo_minimo"))
    if nombres is not None and not destacados.is_empty():
        destacados = destacados.join(
            nombres, on=["fuente", "id_fuente"], how="left")

    def _lista(condicion: pl.Expr) -> list[dict]:
        return [_elemento(fila)
                for fila in destacados.filter(condicion).iter_rows(named=True)]

    return {
        "fecha_datos": str(tabla["fecha_datos"].max()),
        "ventana_dias": _ventana_dias(gold),
        "productos": int(tabla.height),
        "con_historial": int(
            tabla.filter(pl.col("minimo_previo_cent").is_not_null()).height),
        "vuelven_al_minimo": _lista(pl.col("vuelve_al_minimo")),
        "nuevos_minimos": _lista(pl.col("nuevo_minimo")),
        "generado": config.ahora_local().isoformat(timespec="seconds"),
    }


def escribe(gold: Path | None = None,
            datos: Path | None = None) -> tuple[Path, Path]:
    """Deja el artefacto y el resumen, **atomicos**, y devuelve sus rutas.

    Atomics los dos: tmp + `replace`. Una lectura de la API a mitad de escritura
    encontraria un parquet truncado o un JSON medio escrito, y eso se defiende
    mal desde el otro lado.
    """
    gold = Path(gold) if gold is not None else config.GOLD
    destino = Path(datos) if datos is not None else config.DATA

    tabla = calcula(gold)
    resumen_json = resumen(tabla, gold)

    ruta_artefacto = write_parquet_file(tabla, destino / NOMBRE_ARTEFACTO)
    ruta_resumen = destino / NOMBRE_RESUMEN
    ruta_resumen.parent.mkdir(parents=True, exist_ok=True)
    temporal = ruta_resumen.with_name(ruta_resumen.name + ".tmp")
    temporal.write_text(json.dumps(resumen_json, ensure_ascii=False, indent=1),
                        encoding="utf-8")
    os.replace(temporal, ruta_resumen)
    return ruta_artefacto, ruta_resumen


def frase(lo_que_hay: dict) -> str:
    """La linea de la pasada, en castellano y con los dos numeros que importan."""
    cuando = str(lo_que_hay.get("fecha_datos") or "sin fecha")
    return (f"minimos: {cuando} | {lo_que_hay.get('productos', 0)} productos"
            f" ({lo_que_hay.get('con_historial', 0)} con historial)"
            f" | {len(lo_que_hay.get('vuelven_al_minimo', []))} vuelven al minimo"
            f" | {len(lo_que_hay.get('nuevos_minimos', []))} nuevos minimos")


def main(argv: list[str] | None = None) -> int:
    """El paso de la cadena. Escribe los dos ficheros y cuenta lo que dejo."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--ver", action="store_true",
                    help="calcula y ensena el resumen, sin escribir nada")
    args = ap.parse_args(argv)

    if args.ver:
        tabla = calcula()
        print(json.dumps(resumen(tabla), ensure_ascii=False, indent=1))
        return 0

    ruta_artefacto, ruta_resumen = escribe()
    lo_que_hay = json.loads(ruta_resumen.read_text(encoding="utf-8"))
    print(f"[minimos] {frase(lo_que_hay)}")
    print(f"[minimos] artefacto en {ruta_artefacto.name} "
          f"| resumen en {ruta_resumen.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
