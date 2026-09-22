"""Fase 3: ¿los embeddings encuentran pares que el nombre no encuentra?

Lo que hay que medir, y nada mas: de los 640 pares que sabemos ciertos por EAN y
el emparejador por nombre NO encuentra, ¿cuantos acerca un embedding? Y para que
el numero signifique algo, se compara contra pares al azar entre cadenas, que no
son nada.

Si el embedding no separa esos dos grupos, la Fase 3 (indice ANN con embeddings)
no aporta y se dice. Si los separa, aporta y hay que decidir el coste.

    uv run python -m projects.cesta.embeddings --modelo bge-m3
"""
from __future__ import annotations

import argparse
import json
import random
import statistics
import time
import urllib.request

import polars as pl

from core import config
from core.matching import _ean, enlaces

OLLAMA = "http://127.0.0.1:11434/api/embed"
MODELO_POR_DEFECTO = "bge-m3"


def embebe(textos: list[str], modelo: str, lote: int = 16) -> list[list[float]]:
    """Los vectores de una lista de textos, por lotes."""
    salida = []
    for pos in range(0, len(textos), lote):
        cuerpo = {"model": modelo, "input": textos[pos:pos + lote]}
        peticion = urllib.request.Request(
            OLLAMA, data=json.dumps(cuerpo).encode("utf-8"),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(peticion, timeout=600) as r:
            salida.extend(json.loads(r.read().decode("utf-8"))["embeddings"])
    return salida


def coseno(a: list[float], b: list[float]) -> float:
    producto = sum(x * y for x, y in zip(a, b, strict=True))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    return producto / (na * nb) if na and nb else 0.0


def texto_de(f: dict) -> str:
    partes = [f["nombre"] or ""]
    if f.get("marca"):
        partes.append(f["marca"])
    if f.get("cantidad") and f.get("unidad_canon"):
        partes.append(f"{f['cantidad']} {f['unidad_canon']}")
    return " | ".join(partes)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="embeddings")
    ap.add_argument("--modelo", default=MODELO_POR_DEFECTO)
    ap.add_argument("--al-azar", type=int, default=300,
                    help="cuantos pares al azar para el control")
    a = ap.parse_args(argv)

    g = pl.read_parquet(config.GOLD / "grupos.parquet")
    filas = g.select(["fuente", "nombre", "marca", "cantidad", "unidad_canon",
                      "ean"]).to_dicts()
    for f in filas:
        f["ean_n"] = _ean(f["ean"])

    # Los pares ciertos por EAN, y cuales de ellos el nombre ya encuentra.
    verdad = {}
    por_ean: dict[str, list[int]] = {}
    for i, f in enumerate(filas):
        if f["ean_n"]:
            por_ean.setdefault(f["ean_n"], []).append(i)
    for ids in por_ean.values():
        for p in range(len(ids)):
            for q in range(p + 1, len(ids)):
                i, j = ids[p], ids[q]
                if filas[i]["fuente"] != filas[j]["fuente"]:
                    verdad[(min(i, j), max(i, j))] = True
    encontrados = {(min(i, j), max(i, j))
                   for i, j, _s, _n in enlaces(filas, umbral=0.55, usar_ean=False)}
    perdidos = sorted(set(verdad) - encontrados)
    ganados = sorted(set(verdad) & encontrados)
    print(f"pares ciertos: {len(verdad)}   el nombre encuentra {len(ganados)}, "
          f"se le escapan {len(perdidos)}")

    rng = random.Random(11)
    azar = []
    while len(azar) < a.al_azar:
        i, j = rng.randrange(len(filas)), rng.randrange(len(filas))
        if i == j or filas[i]["fuente"] == filas[j]["fuente"]:
            continue
        azar.append((min(i, j), max(i, j)))

    muestra_perdidos = rng.sample(perdidos, min(150, len(perdidos)))
    muestra_ganados = rng.sample(ganados, min(150, len(ganados)))
    muestra_azar = azar[:a.al_azar]

    # Y el grupo que de verdad decide si esto sirve para JUZGAR y no solo para
    # buscar candidatos: los negativos dificiles del banco de pares. Misma marca,
    # misma unidad y codigo distinto: dos productos distintos que se parecen
    # muchisimo. Si el embedding los acerca tanto como a los aciertos, no sirve
    # para decidir, solo para proponer candidatos.
    por_marca: dict[tuple, list[int]] = {}
    for i, f in enumerate(filas):
        if f["ean_n"] and f["marca"] and f["unidad_canon"]:
            clave = (f["marca"].lower().strip(), f["unidad_canon"])
            por_marca.setdefault(clave, []).append(i)
    dificiles = []
    for ids in por_marca.values():
        for p in range(len(ids)):
            for q in range(p + 1, len(ids)):
                i, j = ids[p], ids[q]
                if (filas[i]["ean_n"] != filas[j]["ean_n"]
                        and filas[i]["fuente"] != filas[j]["fuente"]):
                    dificiles.append((i, j))
    rng.shuffle(dificiles)
    muestra_dificiles = dificiles[:200]

    indice = sorted({i for par in (muestra_perdidos + muestra_ganados
                                   + muestra_azar + muestra_dificiles)
                     for i in par})
    print(f"embediendo {len(indice)} productos con {a.modelo}...")
    t0 = time.monotonic()
    vectores = embebe([texto_de(filas[i]) for i in indice], a.modelo)
    vec = {i: v for i, v in zip(indice, vectores, strict=True)}
    print(f"  {time.monotonic() - t0:.0f}s, dimension {len(vectores[0])}")

    def reparto(pares):
        return [coseno(vec[i], vec[j]) for i, j in pares if i in vec and j in vec]

    r_perdidos = reparto(muestra_perdidos)
    r_ganados = reparto(muestra_ganados)
    r_azar = reparto(muestra_azar)
    r_dificiles = reparto(muestra_dificiles)
    print(f"\n{'grupo':34s} {'mediana':>8s} {'p25':>7s} {'p75':>7s}")
    for nombre, valores in (("ciertos que el nombre NO encuentra", r_perdidos),
                            ("ciertos que el nombre SI encuentra", r_ganados),
                            ("NEGATIVOS DIFICILES (misma marca,", r_dificiles),
                            ("  otro codigo: son distintos)", r_dificiles),
                            ("pares al azar entre cadenas", r_azar)):
        if valores:
            valores.sort()
            print(f"{nombre:34s} {statistics.median(valores):8.3f} "
                  f"{valores[len(valores) // 4]:7.3f} "
                  f"{valores[3 * len(valores) // 4]:7.3f}")

    # ¿Cuantos de los perdidos quedarian por encima del percentil 95 del azar?
    if r_azar and r_perdidos:
        r_azar.sort()
        corte = r_azar[int(0.95 * (len(r_azar) - 1))]
        por_encima = sum(1 for v in r_perdidos if v > corte)
        print(f"\ncorte = percentil 95 del azar = {corte:.3f}")
        print(f"  de los perdidos, {por_encima}/{len(r_perdidos)} "
              f"({100 * por_encima / len(r_perdidos):.0f} %) lo superan")
        print(f"  eso son ~{round(por_encima / len(r_perdidos) * len(perdidos))} "
              f"de los {len(perdidos)} que se escapan, si la muestra es fiel")

    # Y la comparacion que decide si vale para JUZGAR: los dificiles, ¿se
    # confunden con los aciertos?
    if r_dificiles and r_perdidos:
        medio_perdidos = statistics.median(r_perdidos)
        medio_dificiles = statistics.median(r_dificiles)
        print(f"\n  mediana de los aciertos que se escapan: {medio_perdidos:.3f}")
        print(f"  mediana de los DOS PRODUCTOS DISTINTOS: {medio_dificiles:.3f}")
        print(f"  diferencia: {medio_perdidos - medio_dificiles:+.3f}")

    # El barrido que convierte las distribuciones en una decision: a cada umbral,
    # cuantos aciertos se recuperan y cuantos pares distintos se cuelan.
    positivos_todos = r_perdidos + r_ganados
    print(f"\n{'umbral':>7s} {'recupera':>9s} {'se cuelan':>10s} "
          f"{'precision':>10s} {'recall':>8s}")
    mejor = None
    for paso in range(50, 91):
        u = paso / 100
        bien = sum(1 for v in positivos_todos if v >= u)
        mal = sum(1 for v in r_dificiles if v >= u)
        if not bien + mal:
            continue
        prec = bien / (bien + mal)
        rec = bien / len(positivos_todos)
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0
        if mejor is None or f1 > mejor[0]:
            mejor = (f1, u, prec, rec, bien, mal)
        if paso % 5 == 0:
            print(f"{u:7.2f} {bien:9d} {mal:10d} {prec:10.2f} {rec:8.2f}")
    if mejor:
        print(f"\n  el mejor F1 esta en {mejor[1]:.2f}: precision {mejor[2]:.2f}, "
              f"recall {mejor[3]:.2f}")
        print(f"  recupera {mejor[4]} de {len(positivos_todos)} pares ciertos y "
              f"deja pasar {mejor[5]} pares de productos distintos")
        print("  Ojo: los 'se cuelan' se miden contra los negativos DIFICILES, que")
        print("  son el peor caso; en el catalogo real la mayoria de los pares")
        print("  parecidos no son de la misma marca.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
