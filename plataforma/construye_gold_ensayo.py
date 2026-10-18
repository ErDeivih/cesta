"""*** EL GOLD DE ENSAYO DEL APARTADO 8, CONSTRUIDO Y NO ADIVINADO. ***

*M00 pide un catalogo de ensayo «pequeno y versionado» que no dependa del producto del dia.*
*El que habia tenia dos productos de dos cadenas y servia para comparar y para promociones,
pero **no cubre el escenario obligatorio**: arroz (dos marcas), leche y huevos.*

*Y no se puede fabricar a mano: `grupos` tiene **62 columnas**, `enlaces` 4, `diario` 7,
`derivado` 21 y `resumen` 10.* *Escribirlas de memoria seria inventar el esquema.*

*** COMO SE HACE AQUI ***: **el esquema se copia del gold que ya funciona**
(`CREATE TABLE ... AS SELECT * FROM '<su parquet>' LIMIT 0`), *y despues se insertan las
filas.* *Asi no hay ni una columna escrita a mano, y si el esquema cambia, esto sigue
valiendo o falla al instante en vez de producir un fichero mal formado.*

*** LOS NIVELES, QUE ERA LA PIEZA QUE DECIDIA ***: `emparejar.py:7` dice que `enlaces`
lleva pares (i, j) con `parecido` y `nivel`, y en el gold real hay tres:
**`ean` · `identico` · `equivalente`**. *Las dos marcas de arroz van en **`equivalente`**:
mismo grupo, **no** el mismo articulo.* *Con `ean` o `identico` el escenario nace con las
dos marcas fusionadas, que es justo lo que M11 prohibe.*

Uso:

    uv run python -m plataforma.ensayo.construye_gold <destino> [--plantilla <gold>]
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import duckdb

# *`plataforma/construye_gold_ensayo.py` -> `plataforma` -> la raiz del proyecto: dos `parent`.*
RAIZ = Path(__file__).resolve().parent.parent
PLANTILLA_POR_DEFECTO = RAIZ / "data" / "debug" / "ensayo-gold"
VERSION = "20260101-000000"
FECHA = "2026-01-01"

# *** Las cuatro ofertas del apartado 8. ***
# *Precios en centimos, tal como los fija la especificacion: arroz 120, leche 100, huevos 180.*
OFERTAS = [
    dict(
        fuente="ensayo", id_fuente="arroz-a", ean="9000000000017",
        nombre="Arroz redondo marca A 1 kg", marca="Marca A",
        precio_cent=120, precio_unidad_cent=120.0, cantidad=1.0,
        unidad_canon="kg", unidad_ref_canon="kg", precio_ref_canon_cent=120.0,
        grupo_id=900001, producto_id="9000000000017", kcal_100g=360,
    ),
    dict(
        fuente="ensayo", id_fuente="arroz-b", ean="9000000000024",
        nombre="Arroz redondo marca B 1 kg", marca="Marca B",
        precio_cent=135, precio_unidad_cent=135.0, cantidad=1.0,
        unidad_canon="kg", unidad_ref_canon="kg", precio_ref_canon_cent=135.0,
        grupo_id=900001, producto_id="9000000000024", kcal_100g=360,
    ),
    dict(
        fuente="ensayo", id_fuente="leche-a", ean="9000000000031",
        nombre="Leche entera marca A 1 l", marca="Marca A",
        precio_cent=100, precio_unidad_cent=100.0, cantidad=1.0,
        unidad_canon="l", unidad_ref_canon="l", precio_ref_canon_cent=100.0,
        grupo_id=900002, producto_id="9000000000031", kcal_100g=None,
    ),
    dict(
        fuente="ensayo", id_fuente="huevos-a", ean="9000000000048",
        nombre="Huevos frescos marca A, pack de 6", marca="Marca A",
        precio_cent=180, precio_unidad_cent=30.0, cantidad=6,
        unidad_canon="ud", unidad_ref_canon="ud", precio_ref_canon_cent=30.0,
        grupo_id=900003, producto_id="9000000000048", kcal_100g=None,
    ),
]

# *** La unica pareja que hay que enlazar, y con su nivel. ***
# *Indices de fila en `grupos`: 0 = arroz A, 1 = arroz B.*
ENLACES = [
    dict(i=0, j=1, parecido=0.86, nivel="equivalente"),
]


# *** UNA SEGUNDA CADENA, *opcional y aparte*. ***
#
# *El apartado 8 fija **cuatro ofertas a 120, 135, 100 y 180**, y esas cifras son las de
# aceptacion: no se tocan.*
#
# *Pero con **una sola cadena** (`fuente='ensayo'` para las cuatro) hay caminos de la interfaz que
# **no se pueden ejercitar**: `fraseDePrecio` devuelve `null` sin al menos dos cadenas, asi que la
# frase del grupo -- y la salvedad que va debajo -- **no se pintan nunca**.* *Y `ahorro_exacto`
# solo tiene caso positivo si el **mismo EAN** esta en dos cadenas.*
#
# *Asi que la segunda cadena es una **variante**, no parte del escenario.* *Quien quiera las cifras
# del apartado 8 llama a `construye()` sin nada; quien quiera ejercitar esos caminos pasa
# `segunda_cadena=True`, y entonces hay dos cadenas y el **mismo EAN** en las dos.*
OFERTAS_SEGUNDA_CADENA = [
    dict(
        fuente="ensayo-b", id_fuente="arroz-a-b", ean="9000000000017",
        nombre="Arroz redondo marca A 1 kg", marca="Marca A",
        precio_cent=110, precio_unidad_cent=110.0, cantidad=1.0,
        unidad_canon="kg", unidad_ref_canon="kg", precio_ref_canon_cent=110.0,
        grupo_id=900001, producto_id="9000000000017", kcal_100g=360,
    ),
    dict(
        fuente="ensayo-b", id_fuente="arroz-b-b", ean="9000000000024",
        nombre="Arroz redondo marca B 1 kg", marca="Marca B",
        precio_cent=130, precio_unidad_cent=130.0, cantidad=1.0,
        unidad_canon="kg", unidad_ref_canon="kg", precio_ref_canon_cent=130.0,
        grupo_id=900001, producto_id="9000000000024", kcal_100g=360,
    ),
]


def construye(destino: Path, plantilla: Path = PLANTILLA_POR_DEFECTO,
              segunda_cadena: bool = False) -> dict:
    """*Crea los seis parquet y el puntero de version.* *Devuelve lo que escribio.*"""
    if destino.exists():
        shutil.rmtree(destino)
    version = destino / f"v{VERSION}"
    version.mkdir(parents=True)

    # *** La vista y el fichero NO se llaman igual, y hay que saberlo. ***
    # *`catalogo.conexion()` monta la vista `diario` sobre **`precio_diario.parquet`** y la vista
    # `derivado` sobre **`precio_derivado.parquet`** (`catalogo.py:100-101`).* *Buscar `diario.parquet`
    # es lo que hizo fallar la primera version.*
    FICHERO = {
        "grupos": "grupos.parquet",
        "enlaces": "enlaces.parquet",
        "diario": "precio_diario.parquet",
        "derivado": "precio_derivado.parquet",
        "resumen": "resumen.parquet",
    }
    # *La plantilla tiene que existir: es de donde sale el esquema.*
    for _nombre, fichero in FICHERO.items():
        if not (plantilla / fichero).exists():
            raise SystemExit(f"falta {plantilla / fichero}: sin plantilla no hay esquema")

    con = duckdb.connect(database=":memory:")

    def mismo_esquema(tabla: str) -> None:
        con.execute(
            f"CREATE TABLE {tabla} AS SELECT * FROM '{plantilla / FICHERO[tabla]}' LIMIT 0"
        )

    for tabla in ("grupos", "enlaces", "diario", "derivado", "resumen"):
        mismo_esquema(tabla)

    # --- grupos: las cuatro ofertas ---
    for o in (OFERTAS + OFERTAS_SEGUNDA_CADENA if segunda_cadena else OFERTAS):
        con.execute(
            """
            INSERT INTO grupos (fuente, id_fuente, precio_cent, precio_unidad_cent,
                precio_ref_canon_cent, unidad_ref_canon, promo, promo_txt, nombre, marca,
                cantidad, unidad_canon, ean, cantidad_fiable, comparacion_fiable,
                precio_comparable, grupo_id, kcal_100g)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [o["fuente"], o["id_fuente"], o["precio_cent"], o["precio_unidad_cent"],
             o["precio_ref_canon_cent"], o["unidad_ref_canon"], False, "", o["nombre"],
             o["marca"], o["cantidad"], o["unidad_canon"], o["ean"], True, True, True,
             o["grupo_id"], o["kcal_100g"]],
        )

    # --- enlaces: la pareja de arroz, en `equivalente` ---
    for e in ENLACES:
        con.execute(
            "INSERT INTO enlaces (i, j, parecido, nivel) VALUES (?, ?, ?, ?)",
            [e["i"], e["j"], e["parecido"], e["nivel"]],
        )

    # --- diario y derivado: una observacion por oferta y fecha ---
    for o in (OFERTAS + OFERTAS_SEGUNDA_CADENA if segunda_cadena else OFERTAS):
        con.execute(
            """INSERT INTO diario (fuente, id_fuente, precio_cent, precio_unidad_cent,
                   unidad_canon, producto_id, fecha) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            [o["fuente"], o["id_fuente"], o["precio_cent"], o["precio_unidad_cent"],
             o["unidad_canon"], o["producto_id"], FECHA],
        )
        con.execute(
            """INSERT INTO derivado (fuente, id_fuente, precio_cent, precio_unidad_cent,
                   unidad_canon, producto_id, fecha, precio_anterior_cent, variacion_cent,
                   ha_bajado, ha_subido, oferta_sospechosa)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [o["fuente"], o["id_fuente"], o["precio_cent"], o["precio_unidad_cent"],
             o["unidad_canon"], o["producto_id"], FECHA, o["precio_cent"], 0.0,
             False, False, False],
        )
        con.execute(
            """INSERT INTO resumen (producto_id, precio_hoy, en_promo, oferta_sospechosa,
                   dias_de_historico) VALUES (?, ?, ?, ?, ?)""",
            [o["producto_id"], float(o["precio_cent"]), False, False, 1],
        )

    escrito = {}
    for tabla in ("grupos", "enlaces", "diario", "derivado", "resumen"):
        for carpeta in (version, destino):
            con.execute(f"COPY {tabla} TO '{carpeta / FICHERO[tabla]}' (FORMAT PARQUET)")
        escrito[tabla] = con.execute(f"SELECT count(*) FROM {tabla}").fetchone()[0]

    (destino / "actual.json").write_text(
        json.dumps(
            {
                "version_puntero": 1,
                "version": VERSION,
                "publicado_en": "2026-10-18T00:00:00.000000",
                "ficheros": ["grupos.parquet", "enlaces.parquet", "precio_diario.parquet",
                             "precio_derivado.parquet", "resumen.parquet"],
                "nota": "Gold de ensayo del apartado 8. Sintetico. Construido por construye_gold.py.",
            },
            indent=1,
            ensure_ascii=False,
        ) + "\n",
        encoding="utf-8",
    )
    con.close()
    return escrito


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    destino = Path(args[0]).resolve()
    plantilla = Path(args[2]).resolve() if len(args) > 2 and args[1] == "--plantilla" else PLANTILLA_POR_DEFECTO
    print("  plantilla: " + str(plantilla))
    print("  destino:   " + str(destino))
    escrito = construye(destino, plantilla)
    for tabla, n in escrito.items():
        print(f"      {tabla:10} {n} filas")
    print("  hecho")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
