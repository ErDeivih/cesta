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
para esto no se pagan.

**Y tarda mas de lo que parece.** La primera estimacion salio de medir con lotes
de texto repetido y corto: 45 productos por segundo. Con los nombres de verdad
son **14 por segundo**, o sea **62 minutos** para los 52.567. La leccion es la de
siempre en este proyecto y va escrita aqui para no repetirla: medir con datos de
verdad, no con una muestra comoda.

De ahi que `calcula` sea **incremental**: en la tarea diaria solo entran los
productos nuevos (unos cientos, segundos), no los 52.000 otra vez.

**Los vectores son para PROPONER candidatos, no para decidir.** Los candidatos que
salen de aqui pasan despues por la asignacion hungara y por los dos frenos de
grupo, igual que los que salen del nombre. El embedding acerca; el resto decide.
"""
from __future__ import annotations

import json
import time
import urllib.error
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

# Lo que mide bge-m3. Se escribe para poder guardar un vector de ceros cuando un
# texto no se puede embeber, sin que se descuadre la tabla.
DIMENSION = 1024


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

    Lote de 64 y no de 16 -- medido, 49 contra 39 productos por segundo --, y
    tampoco mas: con 128 no mejora.

    **Y si un lote falla, no se cae el trabajo entero.** Medido el 22 de septiembre
    de 2026: a los 9.024 vectores la API contesto `HTTP 400` y el proceso murio,
    que en un trabajo de una hora es la peor forma de perderlo.

    **La causa NO esta identificada, y conviene decirlo asi.** Se comprobo lo que
    parecia obvio y no era: no hay textos vacios (0 de 52.567), ni larguisimos (la
    mediana son 74 caracteres y el mas largo 482), y el lote exacto que fallo
    **vuelve a funcionar si se le manda a mano**, con los 64 textos y sus 5.577
    caracteres. Tambien falla en el primer lote despues de reanudar, lo que apunta
    a algo del arranque y no del contenido.

    Como la causa no esta identificada, lo que se hace es no depender de ella: el
    lote se reintenta **texto a texto**, y al que sigue fallando se le guarda un
    vector de ceros y se cuenta. Un vector de ceros no se parece a nada, asi que
    ese producto simplemente no tendra candidatos por significado, que es
    exactamente lo que pasaria si no estuviera calculado. Y el error se registra
    **con el cuerpo de la respuesta**, que es lo que faltaba para poder mirarlo.
    """
    salida: list[list[float]] = []
    for pos in range(0, len(textos), lote):
        trozo = textos[pos:pos + lote]
        try:
            salida.extend(_pide(trozo, modelo))
            continue
        except urllib.error.HTTPError as e:
            # El cuerpo de la respuesta es lo que dice POR QUE. Sin el, un 400
            # solo dice "Bad Request" y no hay por donde mirarlo.
            try:
                detalle = e.read().decode("utf-8", errors="replace")[:300]
            except Exception:                       # noqa: BLE001
                detalle = "(sin cuerpo)"
            print(f"  lote en {pos} fallo ({e}): {detalle}; se reintenta texto a "
                  f"texto", flush=True)
        for t in trozo:
            try:
                salida.extend(_pide([t], modelo))
            except Exception as e:                  # noqa: BLE001
                print(f"  no se pudo embeber ({type(e).__name__}): {t[:60]!r}",
                      flush=True)
                salida.append([0.0] * DIMENSION)
    return salida


def _pide(textos: list[str], modelo: str) -> list[list[float]]:
    cuerpo = {"model": modelo, "input": textos}
    peticion = urllib.request.Request(
        OLLAMA, data=json.dumps(cuerpo).encode("utf-8"),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(peticion, timeout=900) as r:
        return json.loads(r.read().decode("utf-8"))["embeddings"]


def camino(salida: Path | None = None) -> Path:
    return salida or (config.GOLD / NOMBRE_CACHE)


def calcula(filas: list[dict], modelo: str = MODELO_POR_DEFECTO,
            salida: Path | None = None, lote: int = LOTE,
            cada: int = 1000, rehacer: bool = False) -> Path:
    """Embebe **lo que falte** del catalogo y devuelve donde quedo.

    Es incremental a proposito, por dos motivos:

    - Un catalogo de 52.567 productos son **62 minutos** de GPU medidos (14 por
      segundo con los nombres de verdad). Si el proceso se corta a la mitad, sin
      esto se pierde entero; con esto se retoma donde iba.
    - En la **tarea diaria** solo entran los productos nuevos, que son unos
      cientos. Volver a embeber los 52.000 cada manana seria absurdo, y es lo que
      pasaria con un calculo de una sola pasada.

    Se guarda con `producto_id` y no con la posicion en la lista: los vectores
    tienen que sobrevivir a que el catalogo se reordene manana, igual que las
    equivalencias (ver `core/equivalencias.py`).
    """
    from core.storage import write_parquet_file

    destino = camino(salida)
    previos = {} if rehacer else carga(destino)
    claves = [f"{f['fuente']}:{f['id_fuente']}" for f in filas]
    pendientes = [(k, texto_de(f)) for k, f in zip(claves, filas, strict=True)
                  if k not in previos]
    print(f"  {len(previos)} vectores ya calculados, {len(pendientes)} por hacer",
          flush=True)
    if not pendientes:
        return destino

    def guarda(hechos: list[tuple[str, list[float]]]):
        juntos = dict(previos)
        juntos.update(dict(hechos))
        write_parquet_file(
            pl.DataFrame({"producto_id": list(juntos), "e": list(juntos.values())},
                         schema={"producto_id": pl.Utf8,
                                 "e": pl.List(pl.Float32)}),
            destino)

    t0 = time.monotonic()
    hechos: list[tuple[str, list[float]]] = []
    for pos in range(0, len(pendientes), lote):
        trozo = pendientes[pos:pos + lote]
        vectores = embebe([t for _k, t in trozo], modelo, lote)
        hechos.extend(zip((k for k, _t in trozo), vectores, strict=True))
        if cada and len(hechos) % cada < lote:
            guarda(hechos)          # por si se corta: no se pierde lo hecho
            ritmo = len(hechos) / max(time.monotonic() - t0, 1e-9)
            falta = (len(pendientes) - len(hechos)) / max(ritmo, 1e-9)
            print(f"  {len(hechos)}/{len(pendientes)} vectores  {ritmo:.0f}/s  "
                  f"faltan {falta / 60:.0f} min", flush=True)
    guarda(hechos)
    print(f"  {len(hechos)} vectores en {time.monotonic() - t0:.0f}s -> {destino}",
          flush=True)
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
