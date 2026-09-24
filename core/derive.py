"""Campos derivados del histórico propio.

Aqui es donde se iguala a las cadenas que dan menos. Mercadona regala el precio
anterior y Aldi la fecha de fin de promocion; el resto no. A partir del dia ~30
nosotros tenemos ESO Y MAS para las seis, calculado igual para todas.

Entrada: polars.DataFrame de precio_diario con columnas
    producto_id, fecha, precio_unidad_cent, precio_cent, unidad_canon, promo (opcional)

`unidad_canon` no es opcional aunque el resto del proyecto la trate con cuidado: sin
ella la ventana movil mezcla EUR/kg con EUR/ud y todo lo que sale de aqui -- la base,
el minimo de 90 dias, la posicion y el descuento real -- se calcula contra un numero
que no es comparable. Ver `enriquecer()`.
"""
from __future__ import annotations

import polars as pl

VENTANA_BASE = 30      # dias para la mediana de referencia
VENTANA_PERC = 90      # dias para el percentil


def enriquecer(df: pl.DataFrame) -> pl.DataFrame:
    """Anade todos los campos derivados. Idempotente: se recalcula entero.

    **La ventana es del producto *y* de su unidad, y eso no es un detalle.** Todas
    estas columnas comparan un precio con los suyos anteriores, y un precio por
    litro no se puede comparar con uno por unidad: es la misma regla que ya sigue
    el resto del proyecto (comparar EUR/kg con EUR/ud no da un desvio, da un
    disparate).

    Medido el 24 de septiembre de 2026 sobre el gold de ese dia, cuando la ventana
    era solo por producto: **2.239 productos tienen mas de una unidad en su
    historial** -- tipicamente porque la cadena no publicaba el tamano el primer
    dia y ahora si, o al reves: "8 ml" (130.625 centimos por litro) contra el "1 ud"
    de relleno (1.045 centimos, que es el precio del envase leido como si fuera por
    litro). Con las dos unidades en la misma ventana salia:

        - 337 ofertas marcadas como falsas donde hoy es > 3x la base, **y son las
          primeras de la pantalla** porque `posicion_90d` se va a 1,0 solo;
        - 150 productos anunciados como "el mas barato de sus 90 dias" (posicion
          0,0) que solo lo parecen porque la unidad cambio;
        - 3.175 productos con un rango de 90 dias mayor de 3x, que no es un rango:
          son dos unidades.

    Partiendo por unidad, un producto que cambia de unidad **empieza de cero en la
    nueva**: su base tarda en existir y hasta entonces dice "no lo se" (`NULL`), que
    es lo honesto. Un dato que no tenemos no se inventa.
    """
    df = df.sort(["producto_id", "fecha"])
    w = {"partition_by": ["producto_id", "unidad_canon"], "order_by": "fecha"}

    df = df.with_columns([
        # --- precio anterior y variacion (lo que solo Mercadona da nativo) ---
        pl.col("precio_unidad_cent").shift(1).over(**w).alias("precio_anterior_cent"),
    ]).with_columns([
        (pl.col("precio_unidad_cent") - pl.col("precio_anterior_cent"))
            .alias("variacion_cent"),
        (pl.col("precio_unidad_cent") < pl.col("precio_anterior_cent"))
            .alias("ha_bajado"),
        (pl.col("precio_unidad_cent") > pl.col("precio_anterior_cent"))
            .alias("ha_subido"),

        # --- referencia movil: que es "precio normal" para este producto ---
        pl.col("precio_unidad_cent").rolling_median(VENTANA_BASE, min_samples=7)
            .over(**w).alias("precio_base_cent"),
        pl.col("precio_unidad_cent").rolling_min(VENTANA_PERC, min_samples=1)
            .over(**w).alias("min_90d_cent"),
        pl.col("precio_unidad_cent").rolling_max(VENTANA_PERC, min_samples=1)
            .over(**w).alias("max_90d_cent"),
        pl.col("precio_unidad_cent").rolling_mean(7, min_samples=3)
            .over(**w).alias("media_7d_cent"),
    ]).with_columns([
        # --- promocion inferida: por debajo del 95% de su precio normal ---
        (pl.col("precio_unidad_cent") < pl.col("precio_base_cent") * 0.95)
            .fill_null(False).alias("promo_inferida"),
        # --- posicion en el rango: 0 = minimo de 90 dias, 1 = maximo ---
        pl.when(pl.col("max_90d_cent") > pl.col("min_90d_cent"))
          .then((pl.col("precio_unidad_cent") - pl.col("min_90d_cent")) /
                (pl.col("max_90d_cent") - pl.col("min_90d_cent")))
          .otherwise(0.5).alias("posicion_90d"),
        # --- descuento real frente a su precio normal, no al tachado del super ---
        pl.when(pl.col("precio_base_cent") > 0)
          .then(1 - pl.col("precio_unidad_cent") / pl.col("precio_base_cent"))
          .otherwise(None).alias("descuento_real"),
    ]).with_columns([
        # --- inicio y fin de promocion observados ---
        (pl.col("promo_inferida") & ~pl.col("promo_inferida").shift(1).over(**w)
            .fill_null(False)).alias("promo_empieza"),
        (~pl.col("promo_inferida") & pl.col("promo_inferida").shift(1).over(**w)
            .fill_null(False)).alias("promo_acaba"),
        # --- oferta inflada: el "precio normal" subio justo antes de la oferta ---
        (pl.col("promo_inferida") &
         (pl.col("precio_base_cent") >
          pl.col("precio_base_cent").shift(45).over(**w) * 1.08))
            .fill_null(False).alias("oferta_sospechosa"),
    ])
    return df


def resumen_producto(df: pl.DataFrame) -> pl.DataFrame:
    """Una fila por producto con lo que la interfaz necesita hoy."""
    return (df.sort("fecha")
              .group_by("producto_id")
              .agg([
                  pl.col("precio_unidad_cent").last().alias("precio_hoy"),
                  pl.col("posicion_90d").last().alias("posicion_90d"),
                  pl.col("min_90d_cent").last().alias("min_90d"),
                  pl.col("max_90d_cent").last().alias("max_90d"),
                  pl.col("descuento_real").last().alias("descuento_real"),
                  pl.col("promo_inferida").last().alias("en_promo"),
                  pl.col("oferta_sospechosa").last().alias("oferta_sospechosa"),
                  pl.col("fecha").count().alias("dias_de_historico"),
                  # tendencia: media de 7d frente a la de hace 30
                  (pl.col("media_7d_cent").last() /
                   pl.col("media_7d_cent").shift(30).last() - 1).alias("tendencia_30d"),
              ]))


def duracion_tipica_promo(df: pl.DataFrame) -> pl.DataFrame:
    """Cuanto duran las promociones de cada cadena, aprendido de lo observado.

    Con esto estimamos 'esta oferta acaba el domingo' tambien donde la cadena no
    publica la fecha, que es en cuatro de las seis.
    """
    return (df.filter(pl.col("promo_inferida"))
              .group_by(["fuente", "producto_id"])
              .agg(pl.col("fecha").count().alias("dias"))
              .group_by("fuente")
              .agg([
                  pl.col("dias").median().alias("duracion_mediana"),
                  pl.col("dias").quantile(0.9).alias("duracion_p90"),
                  pl.len().alias("promos_observadas"),
              ]))
