"""Banco de verdad del alcance: etiquetas humanas, independientes del vocabulario del clasificador.

**Por que existe.** El 6 de octubre de 2026 el control de seguridad decia "cero alimentos
excluidos" y a la vez mostraba tres falsos descartes reales. Un control que comparte vocabulario y
supuestos con lo que vigila puede confirmar sus propios errores, y eso no es medir: es repetir. La
ampliacion lo pide con estas palabras: *"Crear un banco de verdad independiente del vocabulario del
clasificador y del control. Muestrear incluidos, excluidos y revision por cadena/familia; guardar
IDs, etiquetas y motivos. Medir falsos descartes y bazar aceptado por separado, con tamano de
muestra."*

**Como funciona, y por que asi:**

1. `muestrear` saca una muestra **estratificada** (cadena x estado, y dentro de los incluidos por
   familia), **determinista** (semilla fija: la misma muestra hoy y manana, que es lo que permite
   comparar mediciones) y la escribe **sin la decision de la politica**. El que etiqueta lee el
   nombre y la categoria del producto, no el veredicto: si lo leyera, etiquetaria lo que le acaban
   de decir.
2. `etiquetar` es humano. Se edita `etiquetas.csv` a mano con `etiqueta` = `cesta` | `no_cesta` |
   `duda`, un `motivo` y quien firma. La duda es una respuesta legitima: forzar un si o un no en un
   caso limite es como se fabrican los numeros bonitos.
3. `informe` mide **por separado** los dos errores que importan, cada uno con su denominador:
   - **falso descarte**: etiqueta `cesta` y la politica dice `excluido`;
   - **bazar aceptado**: etiqueta `no_cesta` y la politica dice `incluido`;
   - y `revisar` se cuenta aparte, porque no es un error: es una pregunta pendiente.

Uso:

    uv run python -m projects.cesta.banco_verdad muestrear --por-estrato 5
    uv run python -m projects.cesta.banco_verdad informe
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

from core import alcance, config

BANCO = Path(__file__).resolve().parents[2] / "docs" / "banco-verdad"
MUESTRA = BANCO / "muestra.csv"
CIEGA = BANCO / "para-etiquetar.csv"
ETIQUETAS = BANCO / "etiquetas.csv"
SEMILLA = 20261006
CESTA, NO_CESTA, DUDA = "cesta", "no_cesta", "duda"
CAMPOS_MUESTRA = ["id", "fuente", "nombre", "categoria", "estado_politica", "familia_politica"]
CAMPOS_ETIQUETAS = ["id", "etiqueta", "motivo", "quien", "fecha"]


def _id(fuente: str, nombre: str, categoria: str) -> str:
    """Identificador estable de la ficha: la misma ficha da el mismo id siempre.

    Es lo que permite que una etiqueta puesta hoy siga valiendo cuando el catalogo cambie: la
    etiqueta se pega a la ficha (cadena + nombre + categoria), no a la posicion en una lista.
    """
    semilla = f"{fuente}|{nombre}|{categoria}".encode()
    return hashlib.sha1(semilla).hexdigest()[:12]


def catalogo() -> list[dict]:
    """Todo gold, con su decision de la politica. Sin tocar la red y sin modificar nada."""
    ruta = (config.DATA / "gold" / "grupos.parquet").as_posix()
    con = duckdb.connect()
    con.execute("SET enable_progress_bar=false")
    filas = con.execute(
        f"""SELECT fuente, coalesce(nombre, '') AS nombre, coalesce(categoria, '') AS categoria
            FROM read_parquet('{ruta}')""").fetchall()
    fichas = []
    for fuente, nombre, categoria in filas:
        d = alcance.clasificar_alcance(nombre, categoria)
        fichas.append({"id": _id(fuente, nombre, categoria), "fuente": fuente, "nombre": nombre,
                       "categoria": categoria, "estado_politica": d.estado,
                       "familia_politica": d.familia_id or ""})
    return fichas


def muestrear(fichas: list[dict], por_estrato: int) -> list[dict]:
    """Muestra estratificada por cadena y estado, y dentro de los incluidos por familia.

    Aleatorio **con semilla fija** y ordenado por id: reproducible. Y se baraja dentro del estrato
    para no coger siempre las mismas fichas por orden alfabetico -- que en un catalogo es casi
    siempre la misma marca.
    """
    azar = random.Random(SEMILLA)
    por_estrato_filas: dict[tuple, list[dict]] = defaultdict(list)
    for ficha in fichas:
        clave = (ficha["fuente"], ficha["estado_politica"])
        if ficha["estado_politica"] == alcance.INCLUIDO:
            clave = (*clave, ficha["familia_politica"] or "sin_familia")
        por_estrato_filas[clave].append(ficha)

    muestra: list[dict] = []
    for clave in sorted(por_estrato_filas, key=lambda c: tuple(str(p) for p in c)):
        grupo = sorted(por_estrato_filas[clave], key=lambda f: f["id"])
        # Si el estrato es mas pequeno que la cuota, se coge entero: mejor muestra pequena y dicha
        # que rellenar con lo que no toca.
        elegidas = azar.sample(grupo, min(por_estrato, len(grupo)))
        muestra.extend(sorted(elegidas, key=lambda f: f["id"]))
    return muestra


def _escribe_muestra(muestra: list[dict]) -> None:
    BANCO.mkdir(parents=True, exist_ok=True)
    with MUESTRA.open("w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=CAMPOS_MUESTRA)
        escritor.writeheader()
        for fila in muestra:
            escritor.writerow({k: fila[k] for k in CAMPOS_MUESTRA})
    # **Y una copia ciega, sin la decision de la politica.** Es la que se lee para etiquetar: ver
    # el veredicto antes de etiquetar es la forma mas rapida de no medir nada.
    with CIEGA.open("w", encoding="utf-8", newline="") as f:
        campos = ["id", "fuente", "nombre", "categoria"]
        escritor = csv.DictWriter(f, fieldnames=campos)
        escritor.writeheader()
        for fila in muestra:
            escritor.writerow({k: fila[k] for k in campos})


def _lee_etiquetas() -> dict[str, dict]:
    if not ETIQUETAS.exists():
        return {}
    with ETIQUETAS.open(encoding="utf-8", newline="") as f:
        return {fila["id"]: fila for fila in csv.DictReader(f) if fila.get("id")}


def informe() -> int:
    """Los dos errores, por separado, con su denominador y por cadena."""
    if not MUESTRA.exists():
        print("No hay muestra. Ejecuta primero: banco_verdad muestrear")
        return 0
    with MUESTRA.open(encoding="utf-8", newline="") as f:
        muestra = list(csv.DictReader(f))
    etiquetas = _lee_etiquetas()

    etiquetadas = [f for f in muestra if f["id"] in etiquetas]
    sin_etiquetar = len(muestra) - len(etiquetadas)
    print(f"Muestra: {len(muestra)} fichas · etiquetadas: {len(etiquetadas)} · "
          f"sin etiquetar: {sin_etiquetar}")
    if sin_etiquetar:
        # Una muestra a medias se dice: un porcentaje sobre la parte etiquetada no es el total.
        print(f"  (las cuentas de abajo son sobre las {len(etiquetadas)} etiquetadas, no sobre "
              f"las {len(muestra)})")
    if not etiquetadas:
        return 0

    dudas = [f for f in etiquetadas if etiquetas[f["id"]]["etiqueta"] == DUDA]
    validas = [f for f in etiquetadas if etiquetas[f["id"]]["etiqueta"] in (CESTA, NO_CESTA)]

    falsos = [f for f in validas
              if etiquetas[f["id"]]["etiqueta"] == CESTA and f["estado_politica"] == alcance.EXCLUIDO]
    bazar = [f for f in validas
             if etiquetas[f["id"]]["etiqueta"] == NO_CESTA
             and f["estado_politica"] == alcance.INCLUIDO]

    print(f"\n  falsos descartes (cesta que la politica tira):   {len(falsos):>3} de "
          f"{sum(1 for f in validas if etiquetas[f['id']]['etiqueta'] == CESTA):>3} etiquetadas "
          f"como cesta")
    print(f"  bazar aceptado (no cesta que entra como cesta):  {len(bazar):>3} de "
          f"{sum(1 for f in validas if etiquetas[f['id']]['etiqueta'] == NO_CESTA):>3} etiquetadas "
          f"como no cesta")
    print(f"  dudas (no cuentan como acierto ni como fallo):   {len(dudas):>3}")

    # Lo que la politica deja en `revisar` **no es un error**: es una pregunta pendiente, y se
    # cuenta aparte. Meterlo con los errores inflaria el fallo y escondaria lo que hay que hacer.
    pendientes = [f for f in validas if f["estado_politica"] == alcance.REVISAR]
    print(f"\n  pendientes de decision (la politica dice revisar y hay etiqueta): {len(pendientes)}")
    for etiqueta, cuantos in Counter(etiquetas[f["id"]]["etiqueta"]
                                     for f in pendientes).most_common():
        print(f"    {cuantos:>3} etiquetadas como {etiqueta}")

    print("\n  por cadena (falsos descartes / bazar aceptado / dudas):")
    por: dict[str, Counter] = defaultdict(Counter)
    for f in etiquetadas:
        etiqueta = etiquetas[f["id"]]["etiqueta"]
        if f in falsos:
            por[f["fuente"]]["falso_descarte"] += 1
        elif f in bazar:
            por[f["fuente"]]["bazar_aceptado"] += 1
        elif etiqueta == DUDA:
            por[f["fuente"]]["duda"] += 1
        else:
            por[f["fuente"]]["acuerdo"] += 1
    for fuente in sorted(por):
        c = por[fuente]
        print(f"    {fuente:<11} {c['falso_descarte']:>3} / {c['bazar_aceptado']:>3} / "
              f"{c['duda']:>3}   (acuerdo {c['acuerdo']})")

    if falsos or bazar:
        print("\n  los casos que hay que mirar, con su motivo:")
        for titulo, lista in (("FALSO DESCARTE", falsos), ("BAZAR ACEPTADO", bazar)):
            for ficha in lista[:12]:
                etiqueta = etiquetas[ficha["id"]]
                print(f"    {titulo:<14} {ficha['fuente']:<10} {ficha['nombre'][:44]:<46} "
                      f"[{ficha['categoria'][:26]}]")
                print(f"                   etiqueta: {etiqueta.get('motivo', '')[:70]}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="orden", required=True)
    m = sub.add_parser("muestrear", help="saca la muestra estratificada (sin la decision)")
    m.add_argument("--por-estrato", type=int, default=5,
                   help="fichas por combinacion de cadena, estado y familia")
    sub.add_parser("informe", help="mide falsos descartes y bazar aceptado, por separado")
    a = ap.parse_args(argv)

    if a.orden == "muestrear":
        fichas = catalogo()
        muestra = muestrear(fichas, a.por_estrato)
        _escribe_muestra(muestra)
        estados = Counter(f["estado_politica"] for f in muestra)
        familias = len({f["familia_politica"] for f in muestra})
        print(f"Muestra de {len(muestra)} fichas escrita en {MUESTRA.relative_to(BANCO.parents[1])}")
        print(f"  por estado: {dict(estados)}")
        print(f"  familias distintas: {familias}")
        print("  la decision de la politica va en la muestra, pero **el que etiqueta mira el "
              "nombre y la categoria de la ficha y no la columna**")
        return 0
    return informe()


if __name__ == "__main__":
    sys.exit(main())
