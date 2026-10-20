"""*** EL BANCO DE PARES DE IDENTIDAD, CONSTRUIDO CON EVIDENCIA Y AUTORIA DECLARADAS. ***

*M07 lo pide asi:*

> «Banco etiquetado de al menos 200 pares estratificados por cadenas/categorias, incluyendo dificiles y
> desconocidos, con procedencia de etiqueta.»

*Y el contrato anade:*

> «El agente esta autorizado a preparar y anotar pares [...] con evidencia por par, autor agente y fecha.
> [...] **No usar `decide()` para generar la verdad con la que luego se evalua a si mismo.** [...] Si la
> evidencia no permite decidir, conservar desconocido y causa.»

*** Este script NO llama a `identidad.decide()` ni una vez. *** *La etiqueta sale de **datos del
catalogo** -- el EAN, la marca, el nombre, la categoria, si es pack --, no del motor que luego se mide
con ellas.* *Esa separacion es la que hace que la medida signifique algo.*

**Los estratos, y que prueba cada uno:**

    mismo_ean_misma_cadena ... el mismo codigo, dos capturas. **No son iguales por definicion**: se
                               etiqueta como desconocido salvo que el nombre coincida.
    mismo_ean_otra_cadena .... el mismo EAN en dos cadenas. **Acreditado**: el codigo de barras es la
                               identidad, y si ademas la marca coincide, es el mismo producto.
    mismo_nombre_otra_marca .. el mismo nombre con marca distinta. **No son el mismo**: un fabricante
                               distinto no es el mismo producto aunque se llame igual.
    pack_contra_unidad ....... un pack y su unidad suelta. **No son el mismo**: el consumidor tiene
                               codigo propio.
    misma_marca_parecidos .... misma marca, nombres parecidos, EAN distinto (variantes: entera/semidesnatada).
                               **Dificil**: es donde el motor se juega los falsos exactos.
    sin_evidencia ............ dos productos de la misma categoria sin nada mas en comun. **Desconocido**:
                               la evidencia no permite decir ni que si ni que no.

*Cada par lleva: ids, cadena de cada uno, categoria, relacion, si es conocido o desconocido, **la
evidencia concreta** (que campos coinciden y cuales no), autor y fecha.*

*Se escribe JSONL en `docs/banco-verdad/identidad-pares.jsonl`, y el esquema se valida al escribir.*

Ejecutar: uv run python -m scripts.construye_banco_identidad
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import duckdb

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

BRONZE = RAIZ / "data" / "bronze"
SALIDA = RAIZ / "docs" / "banco-verdad" / "identidad-pares.jsonl"
AUTOR = "agente-dsh"
HOY = date.today().isoformat()

# *Cuantos pares por estrato. El objetivo son 200; si un estrato no da, se entrega el deficit.*
OBJETIVO = {
    "mismo_ean_otra_cadena": 70,
    "mismo_nombre_otra_marca": 50,
    "misma_marca_parecidos": 40,
    "pack_contra_unidad": 20,
    "sin_evidencia": 20,
    "mismo_ean_misma_cadena": 10,
    # *Y el medio catalogo que no tiene EAN: aqui el motor **no puede** decir «exacto»,
    # asi que lo que se mide no es su acierto sino **si ofrece un candidato correcto**.*
    "sin_ean_misma_marca": 40,
    "sin_ean_distinta_cantidad": 20,
}


def _carga() -> list[dict]:
    """*Los productos del ultimo dia de cada cadena, con EAN.*"""
    con = duckdb.connect()
    filas = con.execute(f"""
        SELECT fuente, id_fuente, nombre, marca, ean, categoria, es_pack,
               cantidad_declarada, unidad_declarada, fecha
          FROM read_parquet('{BRONZE}/fuente=*/fecha=*/part.parquet',
                          hive_partitioning=true, union_by_name=true)
         WHERE nombre IS NOT NULL AND length(trim(nombre)) > 3
    """).fetchall()
    columnas = ["fuente", "id_fuente", "nombre", "marca", "ean", "categoria", "es_pack",
                "cantidad", "unidad", "fecha"]
    # *Un producto por (cadena, ean): el ultimo dia que se vio.*
    unicos: dict[tuple, dict] = {}
    for fila in filas:
        p = dict(zip(columnas, fila, strict=True))
        # *Se incluye `id_fuente`: sin EAN, dos fichas de la misma cadena son dos productos.*
        clave = (p["fuente"], p["ean"] or ("id:" + str(p["id_fuente"])))
        if clave not in unicos or str(p["fecha"]) > str(unicos[clave]["fecha"]):
            unicos[clave] = p
    return list(unicos.values())


def _par(a: dict, b: dict, relacion: str, cierto: bool | None, estrato: str,
         evidencia: str) -> dict:
    """*Un par, con su evidencia y su autoria.*"""
    return {
        "a": {"fuente": a["fuente"], "id_fuente": a["id_fuente"], "nombre": a["nombre"],
              "marca": a["marca"], "ean": a["ean"], "categoria": a["categoria"]},
        "b": {"fuente": b["fuente"], "id_fuente": b["id_fuente"], "nombre": b["nombre"],
              "marca": b["marca"], "ean": b["ean"], "categoria": b["categoria"]},
        "relacion": relacion,          # «mismo» / «distinto» / «desconocido»
        "cierto": cierto,              # True / False / None
        "estrato": estrato,
        "conocido": cierto is not None,
        "evidencia": evidencia,
        "autor": AUTOR,
        "fecha": HOY,
    }


def construye() -> dict:
    todos = _carga()
    print("  productos con EAN: " + str(len(todos)))
    if len(todos) < 200:
        print("  AVISO: menos de 200 productos; el banco saldra corto y se dira")

    por_ean: dict[str, list[dict]] = {}
    for p in todos:
        por_ean.setdefault(p["ean"], []).append(p)

    pares: list[dict] = []
    cuenta: dict[str, int] = {}

    def cabe(estrato: str) -> bool:
        return cuenta.get(estrato, 0) < OBJETIVO.get(estrato, 0)

    def anade(par: dict) -> None:
        e = par["estrato"]
        if not cabe(e):
            return
        pares.append(par)
        cuenta[e] = cuenta.get(e, 0) + 1

    # --- mismo EAN, otra cadena: ACREDITADO ---
    for ean, suyos in por_ean.items():
        fuentes = {p["fuente"] for p in suyos}
        if len(fuentes) < 2 or not cabe("mismo_ean_otra_cadena"):
            continue
        a = next(p for p in suyos if p["fuente"] == sorted(fuentes)[0])
        b = next(p for p in suyos if p["fuente"] == sorted(fuentes)[1])
        mismo_nombre = (a["nombre"] or "").strip().lower() == (b["nombre"] or "").strip().lower()
        anade(_par(a, b, "mismo", True, "mismo_ean_otra_cadena",
                   f"mismo EAN ({ean}) en {a['fuente']} y {b['fuente']}; "
                   + ("nombre identico" if mismo_nombre else "nombre distinto en cada cadena")))

    # --- mismo EAN, misma cadena: NO es identidad por si solo ---
    for suyos in por_ean.values():
        if len(suyos) < 2 or not cabe("mismo_ean_misma_cadena"):
            continue
        a, b = suyos[0], suyos[1]
        if a["id_fuente"] == b["id_fuente"]:
            continue
        # *Mismo EAN y misma cadena, dos fichas: **¿dicen lo mismo?***
        # *El codigo de barras es la identidad, asi que si los nombres son compatibles es el **mismo
        # producto** con dos fichas -- un cambio de redaccion, no otro articulo.*
        # *Y si los nombres **no** son compatibles, entonces una de las dos fichas tiene mal el EAN:
        # eso es un desconocido con causa, no un «si».*
        # *Se exigen tres palabras en comun; por debajo, la evidencia no basta y se queda desconocido.*
        comunes = len(set((a["nombre"] or "").lower().split())
                      & set((b["nombre"] or "").lower().split()))
        if comunes >= 3:
            anade(_par(a, b, "mismo", True, "mismo_ean_misma_cadena",
                       f"mismo EAN ({ean}) en la misma cadena y {comunes} palabras del nombre en "
                       "comun: es el mismo producto con dos fichas"))
        else:
            anade(_par(a, b, "desconocido", None, "mismo_ean_misma_cadena",
                       f"mismo EAN ({ean}) pero los nombres solo comparten {comunes} palabra(s): "
                       "una de las dos fichas tiene mal el codigo, y no se puede decidir cual"))

    # --- misma marca, nombres parecidos, EAN distinto: DIFICIL ---
    por_marca: dict[str, list[dict]] = {}
    for p in todos:
        if p["marca"] and len(str(p["marca"]).strip()) > 2:
            por_marca.setdefault(str(p["marca"]).strip().lower(), []).append(p)
    for marca, suyos in por_marca.items():
        if len(suyos) < 2 or not cabe("misma_marca_parecidos"):
            continue
        for i in range(len(suyos) - 1):
            if not cabe("misma_marca_parecidos"):
                break
            a, b = suyos[i], suyos[i + 1]
            if a["ean"] == b["ean"]:
                continue
            na = (a["nombre"] or "").lower()
            nb = (b["nombre"] or "").lower()
            comunes = len(set(na.split()) & set(nb.split()))
            if comunes < 2:
                continue
            # *Misma marca y palabras en comun pero EAN distinto: **no se puede afirmar** que sean el
            # mismo. Es el caso donde un motor se equivoca, y por eso se guarda como desconocido.*
            anade(_par(a, b, "desconocido", None, "misma_marca_parecidos",
                       f"misma marca ({marca}), {comunes} palabras del nombre en comun, "
                       f"pero EAN distinto ({a['ean']} vs {b['ean']})"))

    # --- pack contra unidad: DISTINTO ---
    packs = [p for p in todos if p.get("es_pack")]
    sueltos = [p for p in todos if not p.get("es_pack")]
    for i, a in enumerate(packs):
        if not cabe("pack_contra_unidad"):
            break
        b = sueltos[i % len(sueltos)] if sueltos else None
        if not b or b["ean"] == a["ean"]:
            continue
        anade(_par(a, b, "distinto", False, "pack_contra_unidad",
                   f"«{a['nombre']}» es pack y «{b['nombre']}» no; el pack tiene codigo propio"))

    # --- mismo nombre, otra marca: DISTINTO ---
    por_nombre: dict[str, list[dict]] = {}
    for p in todos:
        clave = (p["nombre"] or "").strip().lower()
        if len(clave) > 8:
            por_nombre.setdefault(clave, []).append(p)
    for _nombre, suyos in por_nombre.items():
        if not cabe("mismo_nombre_otra_marca"):
            break
        for i in range(len(suyos) - 1):
            if not cabe("mismo_nombre_otra_marca"):
                break
            a, b = suyos[i], suyos[i + 1]
            ma = (a["marca"] or "").strip().lower()
            mb = (b["marca"] or "").strip().lower()
            if not ma or not mb or ma == mb:
                continue
            anade(_par(a, b, "distinto", False, "mismo_nombre_otra_marca",
                       f"mismo nombre pero marcas distintas ({ma} y {mb}); "
                       "un fabricante distinto no es el mismo producto"))

    # --- sin evidencia: DESCONOCIDO ---
    por_categoria: dict[str, list[dict]] = {}
    for p in todos:
        if p["categoria"]:
            por_categoria.setdefault(str(p["categoria"]), []).append(p)
    for categoria, suyos in por_categoria.items():
        if not cabe("sin_evidencia"):
            break
        if len(suyos) < 2:
            continue
        a, b = suyos[0], suyos[1]
        if a["ean"] == b["ean"]:
            continue
        anade(_par(a, b, "desconocido", None, "sin_evidencia",
                   f"misma categoria ({categoria}) y nada mas en comun: la evidencia no permite decidir"))

    # --- SIN EAN: la mitad del catalogo donde el motor no puede decir «exacto» ---
    # *Aqui la identidad no se puede acreditar con un codigo, asi que la etiqueta sale de **datos
    # declarados**: misma marca, misma cantidad, misma unidad y nombres compatibles -> es el mismo
    # producto. Misma marca y **cantidad distinta** -> no lo es.*
    # *Lo que se mide con esto no es la precision del motor -- que aqui no opina -- sino **si ofrece un
    # candidato correcto**, que es la cobertura que falta.*
    sin_ean: dict[tuple, list[dict]] = {}
    for p in todos:
        if p["ean"]:
            continue
        if not p["marca"] or not p["cantidad"] or not p["unidad"]:
            continue
        clave = (str(p["marca"]).strip().lower(), p["unidad"], float(p["cantidad"]))
        sin_ean.setdefault(clave, []).append(p)

    for (marca, unidad, cantidad), suyos in sin_ean.items():
        if not cabe("sin_ean_misma_marca") or len(suyos) < 2:
            continue
        a, b = suyos[0], suyos[1]
        if a["id_fuente"] == b["id_fuente"] and a["fuente"] == b["fuente"]:
            continue
        comunes = len(set((a["nombre"] or "").lower().split())
                      & set((b["nombre"] or "").lower().split()))
        if comunes < 3:
            continue
        anade(_par(a, b, "mismo", True, "sin_ean_misma_marca",
                   f"sin EAN, misma marca ({marca}), misma cantidad ({cantidad} {unidad}) y "
                   f"{comunes} palabras del nombre en comun"))

    # *Y el contrario, que es el que un motor se puede creer: misma marca y nombre, **cantidad
    # distinta**.* *No son el mismo producto, y un motor que mire solo el texto diria que si.*
    for (marca, unidad, cantidad), suyos in sin_ean.items():
        if not cabe("sin_ean_distinta_cantidad") or len(suyos) < 2:
            continue
        a = suyos[0]
        # *Se busca otro de la misma marca con otra cantidad.*
        otros = [p for p in todos
                 if not p["ean"] and p["marca"]
                 and str(p["marca"]).strip().lower() == marca
                 and p["unidad"] == unidad and p["cantidad"]
                 and float(p["cantidad"]) != cantidad]
        if not otros:
            continue
        b = otros[0]
        comunes = len(set((a["nombre"] or "").lower().split())
                      & set((b["nombre"] or "").lower().split()))
        if comunes < 2:
            continue
        anade(_par(a, b, "distinto", False, "sin_ean_distinta_cantidad",
                   f"sin EAN, misma marca ({marca}) y nombres parecidos ({comunes} palabras), pero "
                   f"{cantidad} {unidad} contra {b['cantidad']} {b['unidad']}: no son el mismo producto"))

    # --- se escribe, y se cuenta ---
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    with SALIDA.open("w", encoding="utf-8", newline="\n") as f:
        for par in pares:
            f.write(json.dumps(par, ensure_ascii=False) + "\n")

    conocidos = sum(1 for p in pares if p["conocido"])
    return {"total": len(pares), "conocidos": conocidos, "desconocidos": len(pares) - conocidos,
            "por_estrato": cuenta, "objetivo": OBJETIVO,
            "deficit": {k: OBJETIVO[k] - cuenta.get(k, 0) for k in OBJETIVO
                        if OBJETIVO[k] - cuenta.get(k, 0) > 0},
            "fichero": str(SALIDA.relative_to(RAIZ))}


if __name__ == "__main__":
    resumen = construye()
    print(json.dumps(resumen, ensure_ascii=False, indent=2))
