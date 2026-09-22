"""Cuando una diferencia de precio deja de ser una oferta y pasa a ser un error.

Esta regla vivia duplicada: la interfaz usaba un factor de 30 y el resumen diario
un 200 %, y los dos llamaban "imposible" a cosas distintas. El resumen del 18 de
septiembre de 2026 avisaba de "340 grupos con diferencias imposibles" cuando la
mayoria eran diferencias **reales y grandes**, que es justo lo que esta
aplicacion existe para encontrar.

Las dos fronteras, medidas el 17 de septiembre sobre 6.324 grupos comparables:

    hasta 30x    ahorros de verdad, incluidos los buenos: preservativos de marca
                 blanca frente a Durex (28x), cerveza de marca blanca frente a
                 Estrella Galicia (28x), tampones frente a Tampax (25x)
    por encima   los 15 casos eran errores, todos: azafran de Alcampo etiquetado
                 "400g" cuando son 400 mg, un champan comparado por botella
                 contra el mismo por unidad, dorada a 7.120 EUR/kg

Ningun producto cuesta treinta veces mas en un supermercado que en otro. Si
nuestros datos lo dicen, los equivocados somos nosotros.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import polars as pl

FACTOR_INCREIBLE = 30.0

# A partir de aqui la diferencia es lo bastante grande como para mirarla, aunque
# sea real. Es la lista de trabajo, no la de errores.
FACTOR_LLAMATIVO = 3.0


def unidad_dominante(df: pl.DataFrame) -> pl.DataFrame:
    """Una sola unidad por grupo: la que comparten mas cadenas.

    Un grupo puede tener productos medidos en unidades distintas -- la manzanilla
    en bolsitas y la misma manzanilla al peso de la hierba -- y esos precios son
    los dos correctos y **no se pueden restar**. Sin esta regla, la aplicacion
    llego a anunciar ahorros del 229.833 %.
    """
    # Polars se importa aqui dentro, y no arriba, a proposito.
    #
    # De este modulo la API solo se lleva `FACTOR_INCREIBLE`, que es un numero.
    # Con el `import` arriba, ese numero arrastraba polars entero al contenedor
    # de la API -- que no lo tiene instalado, porque no manipula dataframes --, y
    # el 21 de septiembre de 2026 eso dejo `cesta-api` en un bucle de reinicios:
    # moria al importarse, antes de llegar a ninguna ruta, con un
    # ModuleNotFoundError que solo se veia en el log del contenedor.
    #
    # La frontera entre las dos mitades del sistema es real: el pipeline vive de
    # dataframes y la API vive de SQL. Una constante compartida no puede obligar
    # a la segunda a cargar las herramientas de la primera.
    import polars as pl

    base = df.filter(pl.col("precio_unidad_cent").is_not_null()
                     & (pl.col("precio_unidad_cent") > 0)
                     & pl.col("unidad_canon").is_not_null())
    manda = (base.group_by(["grupo_id", "unidad_canon"])
                 .agg(pl.col("fuente").n_unique().alias("cadenas"),
                      pl.len().alias("n"))
                 .with_columns((pl.col("cadenas") * 1000 + pl.col("n")).alias("peso"))
                 .sort("peso", descending=True)
                 .group_by("grupo_id").first()
                 .select("grupo_id", "unidad_canon"))
    return base.join(manda, on=["grupo_id", "unidad_canon"], how="semi")
