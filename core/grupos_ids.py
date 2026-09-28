"""Que un grupo conserve su numero de una pasada a la siguiente.

**El problema, medido.** El emparejador numera los grupos **en el orden en que aparecen los
productos** (`core.matching.agrupar_enlaces` termina con
`renombre.setdefault(raiz(i), len(renombre))`), asi que cualquier cambio del catalogo mueve los
numeros. Y ese numero no se queda dentro del pipeline: **las listas de la compra, los favoritos y
los avisos lo guardan en PostgreSQL**. Medido el 28 de septiembre de 2026 con los datos de casa:
de las 54 lineas de la lista de la cuenta de pruebas, **43** apuntaban a un grupo que ya no era su
producto -- la leche entera salia en el pasillo «Higiene y belleza», porque el grupo 526 es hoy una
barra de labios REVROL -- y la estimacion decia 298,71 EUR cuando lo que se podia contar eran
10,56.

**Lo que hace esto.** El numero deja de depender de la posicion y pasa a heredarse: cada grupo de
hoy mira con que grupo de ayer comparte mas productos y **se queda con ese numero**; los que no
tienen con quien (grupos nuevos) reciben uno libre por encima del mayor usado. Un id de ayer **se
da una sola vez**, asi que dos grupos de hoy no pueden acabar con el mismo numero.

Tres decisiones que se ven en el codigo:

  - **La herencia va por solape de miembros, no por nombre del grupo.** Dos pasadas seguidas del
    mismo dia, o un dia que solo cambia un producto por grupo, dan el mismo numero; un grupo que
    crece o mengua un poco tambien.
  - **Gana el solape grande, y los empates se rompen de forma fija** (el id de ayer mas bajo). Un
    empate no puede decidirse "como salga": la misma entrada tiene que dar la misma salida en el
    PC y en el contenedor.
  - **Un id retirado no se reutiliza.** Se reparten numeros por encima del mayor de ayer, asi que
    el grupo que desaparece deja su hueco y nadie hereda su nombre.

Sin fichero de ayer (la primera pasada, o un borrado) se numera como siempre: mirar hacia atras no
puede ser una condicion para que la pasada del dia funcione.
"""
from __future__ import annotations

import polars as pl

# Como se llama la clave de un producto: la misma que usa todo el proyecto para hablar de un
# producto concreto entre dos almacenes (`fuente:id_fuente`).
COLUMNA_CLAVE = "clave"


def clave_de(fuente: str, id_fuente: str) -> str:
    """`dia:147509`. Es la identidad estable que ya usa medio proyecto."""
    return f"{fuente}:{id_fuente}"


def estabiliza(nuevos: pl.DataFrame, anteriores: pl.DataFrame | None) -> pl.DataFrame:
    """`nuevos` (columnas `clave` y `grupo`) con su `grupo_id` estable.

    `anteriores` es la tabla de ayer: `clave` y `grupo_id`. Si no hay, se numera como siempre.
    """
    if anteriores is None or anteriores.height == 0:
        return nuevos.with_columns(pl.col("grupo").cast(pl.Int32).alias("grupo_id"))

    viejos = anteriores.select(
        [COLUMNA_CLAVE, pl.col("grupo_id").cast(pl.Int32).alias("grupo_viejo")])

    # **Cuanto se solapa cada grupo de hoy con cada grupo de ayer.** Un `inner join` por producto
    # y contar: es lo que dice "este grupo de hoy es aquel de ayer".
    solapes = (
        nuevos.select([COLUMNA_CLAVE, pl.col("grupo").alias("grupo_nuevo")])
        .join(viejos, on=COLUMNA_CLAVE, how="inner")
        .group_by(["grupo_nuevo", "grupo_viejo"])
        .agg(pl.len().alias("miembros"))
        # De mas solape a menos, y los empates por el id de ayer mas bajo y luego por el grupo de
        # hoy: un empate no se puede resolver "como salga" si el resultado tiene que ser el mismo
        # en el PC y en el contenedor.
        .sort(["miembros", "grupo_viejo", "grupo_nuevo"], descending=[True, False, False])
    )

    hereda: dict[int, int] = {}
    usados: set[int] = set(anteriores["grupo_id"].cast(pl.Int32).to_list())
    for fila in solapes.iter_rows(named=True):
        grupo_hoy = int(fila["grupo_nuevo"])
        de_ayer = int(fila["grupo_viejo"])
        if grupo_hoy in hereda or de_ayer in hereda.values():
            continue          # ese grupo de hoy ya tiene numero, o ese numero de ayer ya es de otro
        hereda[grupo_hoy] = de_ayer

    siguiente = (max(usados) + 1) if usados else 0
    mapa: dict[int, int] = {}
    for grupo in sorted(nuevos["grupo"].unique().to_list()):
        if grupo in hereda:
            mapa[grupo] = hereda[grupo]
            continue
        while siguiente in usados:
            siguiente += 1
        mapa[grupo] = siguiente
        usados.add(siguiente)
        siguiente += 1

    return nuevos.with_columns(
        pl.col("grupo").replace_strict(mapa, default=None, return_dtype=pl.Int32)
        .alias("grupo_id"))


def tabla_de(filas: list[dict], grupo_id: pl.Series) -> pl.DataFrame:
    """La tabla que se guarda para la pasada de mañana: `clave` y `grupo_id`."""
    return pl.DataFrame({
        COLUMNA_CLAVE: [clave_de(f["fuente"], str(f["id_fuente"])) for f in filas],
        "grupo_id": grupo_id.cast(pl.Int32),
    })
