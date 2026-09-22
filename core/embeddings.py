"""Los vectores de los nombres de producto, cacheados. Fase 3 del plan.

Lo que hace falta saber de esta pieza esta medido en
`docs/DIAGNOSTICO-MATCHING.md` §22, y es la unica de las tres fases avanzadas que
paso su prueba:

    grupo                                 mediana
    ciertos que el nombre ya encuentra      0.890
    ciertos que el nombre NO encuentra      0.823   <- 99 % por encima del azar
    negativos dificiles (misma marca)       0.680
    pares al azar entre cadenas             0.414

    umbral 0,65 -> precision 0,70, recall 0,97
    umbral 0,76 -> precision 0,90, recall 0,89   <- el mejor F1
    umbral 0,80 -> precision 0,94, recall 0,78

**Se usa bge-m3 servido por Ollama**, que es el modelo que nombra el plan, y asi
no hay que instalar `sentence-transformers` ni `torch`: 2,5 GB de dependencias
para esto no se pagan. A 45 productos por segundo, el catalogo entero (52.567)
son unos 20 minutos, y se guarda en un parquet para no repetirlo cada dia.

**Los vectores son para PROPONER candidatos, no para decidir.** Los candidatos que
salen de aqui pasan despues por la asignacion hungara y por los dos frenos de
grupo, igual que los que salen del nombre. El embedding acerca; el resto decide.
"""
from __future__ import annotations

import json
import time
import urllib.request
from pathlib import Path

import polars as pl

from core import config

MODELO_POR_DEFECTO = "bge-m3"
OLLAMA = "http://127.0.0.1:11434/api/embed"
NOMBRE_CACHE = "embedding.parquet"
LOTE = 64

# El umbral medido: 0,76 da precision 0,90 con recall 0,89 contra los negativos
# dificiles, que son el peor caso. Mas alto se pierde recall; mas bajo se cuelan
# productos distintos. Ver `docs/DIAGNOSTICO-MATCHING.md` §22.
UMBRAL = 0.76


def texto_de(f: dict) -> str:
    """Lo que se embebe: nombre, marca y formato, en ese orden.

    El formato va porque un litro no es medio litro, y va detras del nombre
    porque el nombre es lo que mas dice de un producto.
    """
    partes = [f.get("nombre") or ""]
    if f.get("marca"):
        partes.append(str(f["marca"]))
    if f.get("cantidad") and f.get("unidad_canon"):
        partes.append(f"{f['cantidad']} {f['unidad_canon']}")
    return " | ".join(p for p in partes if p)


def embebe(textos: list[str], modelo: str = MODELO_POR_DEFECTO,
           lote: int = LOTE) -> list[list[float]]:
    """Los vectores de una lista de textos, por lotes.

    Lote de 64 y no de 16: medido, 45 productos por segundo contra 39. Por encima
    de 64 no mejora.
    """
    salida: list[list[float]] = []
    for pos in range(0, len(textos), lote):
        cuerpo = {"model": modelo, "input": textos[pos:pos + lote]}
        peticion = urllib.request.Request(
            OLLAMA, data=json.dumps(cuerpo).encode("utf-8"),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(peticion, timeout=900) as r:
            salida.extend(json.loads(r.read().decode("utf-8"))["embeddings"])
    return salida


def camino(salida: Path | None = None) -> Path:
    return salida or (config.GOLD / NOMBRE_CACHE)


def calcula(filas: list[dict], modelo: str = MODELO_POR_DEFECTO,
            salida: Path | None = None, lote: int = LOTE,
            cada: int = 1000) -> Path:
    """Embebe el catalogo entero y lo deja en un parquet. Devuelve donde.

    Se guarda con `producto_id` y no con la posicion en la lista: los vectores
    tienen que sobrevivir a que el catalogo se reordene manana, igual que las
    equivalencias (ver `core/equivalencias.py`).
    """
    from core.storage import write_parquet_file

    destino = camino(salida)
    textos = [texto_de(f) for f in filas]
    claves = [f"{f['fuente']}:{f['id_fuente']}" for f in filas]
    t0 = time.monotonic()
    vectores: list[list[float]] = []
    for pos in range(0, len(textos), lote):
        vectores.extend(embebe(textos[pos:pos + lote], modelo, lote))
        hechos = len(vectores)
        if cada and hechos % cada < lote:
            ritmo = hechos / max(time.monotonic() - t0, 1e-9)
            falta = (len(textos) - hechos) / max(ritmo, 1e-9)
            print(f"  {hechos}/{len(textos)} vectores  {ritmo:.0f}/s  "
                  f"faltan {falta / 60:.0f} min", flush=True)
    write_parquet_file(
        pl.DataFrame({"producto_id": claves, "e": vectores},
                     schema={"producto_id": pl.Utf8, "e": pl.List(pl.Float32)}),
        destino)
    print(f"  {len(vectores)} vectores en {time.monotonic() - t0:.0f}s -> {destino}")
    return destino


def carga(salida: Path | None = None) -> dict[str, list[float]]:
    """Los vectores cacheados, por `producto_id`. {} si no se han calculado."""
    destino = camino(salida)
    if not destino.exists():
        return {}
    d = pl.read_parquet(destino)
    return dict(zip(d["producto_id"].to_list(), d["e"].to_list(), strict=True))


def candidatos(filas: list[dict], vectores: dict[str, list[float]],
               umbral: float = UMBRAL, tope_por_producto: int = 25) -> list[tuple]:
    """Pares candidatos por parecido de significado, dentro del bloque canonico.

    Devuelve `(i, j, parecido)` con `i < j`, listo para la asignacion.

    **El coseno se calcula en SQL, no en Python.** Comparar 52.000 vectores de
    1.024 dimensiones entre si en Python son 17.000 millones de multiplicaciones y
    no termina nunca; DuckDB lo hace vectorizado en segundos. Y no hace falta
    FAISS ni hnswlib: la busqueda se limita al bloque canonico (seccion + formato),
    que es donde el plan la pone, y ahi cada consulta mira decenas o cientos de
    productos, no 52.000. Una dependencia menos.

    `tope_por_producto` recorta los vecinos de cada producto, que es lo que evita
    que un bloque gordo meta decenas de miles de pares en la asignacion. Se queda
    con los mas parecidos.
    """
    if not vectores:
        return []
    import duckdb

    filas_utiles = []
    for i, f in enumerate(filas):
        clave = f"{f['fuente']}:{f['id_fuente']}"
        v = vectores.get(clave)
        cantidad, unidad = f.get("cantidad"), f.get("unidad_canon")
        if v is None or cantidad is None or not unidad:
            continue
        filas_utiles.append({
            "i": i, "cadena": f["fuente"], "e": list(v),
            "bloque": f"{(f.get('seccion') or '?')}|{unidad}|{round(float(cantidad), 3)}",
        })
    if not filas_utiles:
        return []
    con = duckdb.connect()
    con.execute("CREATE TABLE v(i INTEGER, cadena VARCHAR, bloque VARCHAR, "
                "e FLOAT[])")
    con.executemany("INSERT INTO v VALUES (?, ?, ?, ?)",
                    [(x["i"], x["cadena"], x["bloque"], x["e"]) for x in filas_utiles])
    pares = con.execute(f"""
        WITH parecidos AS (
            SELECT a.i AS i, b.i AS j,
                   list_cosine_similarity(a.e, b.e) AS s
              FROM v a JOIN v b
                ON a.bloque = b.bloque AND a.cadena <> b.cadena AND a.i < b.i
             WHERE list_cosine_similarity(a.e, b.e) >= {umbral}
        ), con_puesto AS (
            SELECT i, j, s,
                   row_number() OVER (PARTITION BY i ORDER BY s DESC) AS puesto_i,
                   row_number() OVER (PARTITION BY j ORDER BY s DESC) AS puesto_j
              FROM parecidos
        )
        SELECT i, j, s FROM con_puesto
         WHERE puesto_i <= {tope_por_producto} AND puesto_j <= {tope_por_producto}
    """).fetchall()
    con.close()
    return [(i, j, float(s)) for i, j, s in pares]


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(prog="core.embeddings")
    ap.add_argument("--modelo", default=MODELO_POR_DEFECTO)
    a = ap.parse_args()
    g = pl.read_parquet(config.GOLD / "grupos.parquet")
    filas = g.select(["fuente", "id_fuente", "nombre", "marca", "cantidad",
                      "unidad_canon"]).to_dicts()
    print(f"embediendo {len(filas)} productos con {a.modelo}...")
    calcula(filas, a.modelo)
