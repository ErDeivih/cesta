"""Por que el emparejador no encuentra un par que SI es cierto. La auditoria dirigida.

Por que existe
--------------
`--medir` dice cuantos pares ciertos encuentra (hoy 1.161 de 1.799, un 65 %) y eso es un numero
util y **no dice nada sobre que hacer despues**. Un par que no se encuentra puede faltar por
cuatro motivos muy distintos, y el arreglo de cada uno es otro:

    A  el bloqueo por formato no los junta      -> no se comparan nunca (se arregla en datos)
    B  el bloqueo por palabras no los junta     -> mismo formato, cero palabras en comun
    C  se comparan y no se parecen              -> por debajo del umbral: aqui si ayuda un modelo
    D  se parecen y aun asi no se enlazan       -> la asignacion 1-a-1 o el veto de precio

Separarlos es el diagnostico con mejor relacion valor/precio del emparejamiento: dice donde esta
el recall que falta, y sin el, "mejorar el matcher" es una apuesta.

Como se mide, y por que asi
---------------------------
Se corre **el emparejador de verdad** (`core.matching.enlaces`, con `usar_ean=False`, que es como
se mide) y despues, para cada par cierto que no ha salido, se recalcula su parecido **con las
mismas funciones** (`parecido`, `dice`, `idf`) y se miran las mismas condiciones de candidato
que mira `enlaces`: mismo bloque, alguna palabra en comun que no sea demasiado frecuente, y sin
veto de precio. No se reimplementa la logica de decision: se le pregunta al mismo codigo.

    uv run python -m projects.cesta.auditar_pares
    uv run python -m projects.cesta.auditar_pares --ejemplos 5

Sale de aqui una lista de trabajo ordenada: los del monton C son los que puede arreglar un
matcher mejor; los A y B solo los arregla el dato o el bloqueo.
"""
from __future__ import annotations

import argparse
import itertools
from collections import Counter

from core import matching
from projects.cesta import emparejar

# La misma constante que usa la medicion: si aqui se pusiera otra, el reparto de montones no
# hablaria del emparejador que corre de verdad.
UMBRAL = emparejar.UMBRAL


def carga() -> list[dict]:
    """Las filas, tal y como las carga `emparejar` para medir (mismas columnas, mismo orden)."""
    df = emparejar.catalogo_actual()
    columnas = list(dict.fromkeys(
        [*emparejar.CAMPOS_PARA_EMPAREJAR, "id_fuente", "cantidad", "unidad_canon",
         "precio_cent", "precio_unidad_cent", "precio_ref_canon_cent",
         "unidad_ref_canon", "ean"]))
    filas = df.select([c for c in columnas if c in df.columns]).to_dicts()
    emparejar._completa_cantidad(filas)
    return filas


def verdad(filas: list[dict]) -> set[tuple[int, int]]:
    """Los pares ciertos: mismo codigo de barras en dos cadenas distintas."""
    por_ean: dict[str, list[int]] = {}
    for i, f in enumerate(filas):
        e = emparejar._ean(f.get("ean"))
        if e:
            por_ean.setdefault(e, []).append(i)
    return {(min(a, b), max(a, b))
            for ids in por_ean.values()
            for a, b in itertools.combinations(ids, 2)
            if filas[a]["fuente"] != filas[b]["fuente"]}


def audita(ejemplos: int = 0) -> dict:
    filas = carga()
    cierto = verdad(filas)
    print(f"  verdad: {len(cierto)} pares entre cadenas con el mismo EAN", flush=True)

    # El emparejador de verdad, en el modo en que se mide.
    ls = matching.enlaces(filas, umbral=UMBRAL, usar_ean=False,
                          usar_vectores=emparejar.USAR_VECTORES)
    enlazados = {(min(i, j), max(i, j)) for i, j, _s, _n in ls}
    print(f"  el emparejador enlaza {len(ls)} pares, y de los ciertos encuentra "
          f"{len(enlazados & cierto)} ({100 * len(enlazados & cierto) / max(len(cierto), 1):.0f} %)",
          flush=True)

    # Lo mismo que calcula `enlaces` por dentro, para poder preguntar por un par concreto.
    adelgazadas = matching.adelgaza(filas)
    docs = [matching.tokens(f.get("nombre") or "", f.get("marca")) for f in adelgazadas]
    sin_marca = [matching.tokens_sin_marca(f.get("nombre") or "", f.get("marca"))
                 for f in adelgazadas]
    tris = [matching.trigramas(f.get("nombre") or "", f.get("marca")) for f in adelgazadas]
    pesos = matching.idf(docs)
    pesos_sin_marca = matching.idf(sin_marca)

    # Cuantas veces aparece cada palabra dentro de su bloque: `enlaces` descarta las listas de
    # mas de 400, o sea las palabras que no distinguen nada en ese bloque.
    por_bloque: dict[tuple, list[int]] = {}
    for i, f in enumerate(adelgazadas):
        if docs[i]:
            por_bloque.setdefault(matching.bloque(f.get("cantidad"), f.get("unidad_canon")),
                                  []).append(i)
    frecuencia: dict[tuple, Counter] = {}
    for clave, indices in por_bloque.items():
        cuenta: Counter = Counter()
        for i in indices:
            for palabra in docs[i]:
                cuenta[palabra] += 1
        frecuencia[clave] = cuenta

    montones: Counter = Counter()
    muestra: dict[str, list[str]] = {}
    for i, j in sorted(cierto):
        if (i, j) in enlazados:
            montones["encontrado"] += 1
            continue
        a, b = adelgazadas[i], adelgazadas[j]
        clave = matching.bloque(a.get("cantidad"), a.get("unidad_canon"))
        comunes = docs[i] & docs[j]
        utilizables = [w for w in comunes if frecuencia.get(clave, Counter())[w] <= 400]
        parecido_ = None
        if clave != matching.bloque(b.get("cantidad"), b.get("unidad_canon")):
            monton = "A  el bloqueo por formato no los junta"
        elif not utilizables:
            monton = ("B  mismo formato, ninguna palabra en comun"
                      if not comunes else "B  mismo formato, la palabra comun es demasiado comun")
        else:
            parecido_ = max(matching.parecido(docs[i], docs[j], pesos),
                            matching.PESO_TRIGRAMAS * matching.dice(tris[i], tris[j]))
            if matching._marca(a.get("marca")) != matching._marca(b.get("marca")):
                parecido_ = max(parecido_,
                                matching.parecido(sin_marca[i], sin_marca[j], pesos_sin_marca))
            if matching.precio_imposible(a, b):
                monton = "D  el veto de precio los separa"
            elif parecido_ >= UMBRAL:
                monton = "D  se parecen y aun asi no se enlazan (asignacion 1-a-1)"
            else:
                monton = "C  se comparan y no se parecen (por debajo del umbral)"
        montones[monton] += 1
        if ejemplos and len(muestra.get(monton, [])) < ejemplos:
            cuanto = f"{parecido_:.2f}  " if parecido_ is not None else "      "
            muestra.setdefault(monton, []).append(
                f"{cuanto}{a.get('nombre', '')[:44]} ({a.get('fuente')})  <->  "
                f"{b.get('nombre', '')[:44]} ({b.get('fuente')})")
    return {"pares": len(cierto), "montones": dict(montones), "ejemplos": muestra,
            "enlazados": len(enlazados)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="auditar_pares", description=__doc__.split("\n")[0])
    ap.add_argument("--ejemplos", type=int, default=0)
    a = ap.parse_args(argv)
    r = audita(ejemplos=a.ejemplos)
    total = r["pares"]
    print(f"\n  de los {total} pares ciertos, por que falta cada uno:")
    for monton, cuantos in sorted(r["montones"].items()):
        print(f"    {monton:<62} {cuantos:>5,}  ({100.0 * cuantos / total:.1f} %)")
    for monton, lineas in r["ejemplos"].items():
        print(f"\n  ejemplos de «{monton}»:")
        for linea in lineas:
            print(f"    {linea}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
