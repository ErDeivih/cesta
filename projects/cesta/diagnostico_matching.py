"""Fase 0: diagnostico del matching con numeros. NO modifica nada.

    uv run python -m projects.cesta.diagnostico_matching

Lee `data/gold/grupos.parquet` (una fila por producto con su grupo_id) y
`data/gold/enlaces.parquet` (los pares que el emparejador acepto) y saca:

  1. cuantos productos, grupos y grupos con >=2 cadenas hay hoy
  2. cuantos pares con el mismo EAN entre cadenas (el tope alcanzable) y
     cuantos de ellos estan hoy en el mismo grupo (recall contra el tope)
  3. cuantos pares aceptados tienen unidad distinta, precio por unidad que
     difiere >60 %, o dos EAN distintos (contradiccion dura)
  4. ejemplos concretos de malas asociaciones, con nombre, cadena y motivo

Solo lee. Escribe `docs/DIAGNOSTICO-MATCHING.md` con los numeros.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict

import polars as pl

from core import config
from core.matching import (
    _ean,
    dice,
    enlaces,
    idf,
    parecido,
    tokens,
    trigramas,
)

# Un par esta "sospechoso por precio" cuando el precio por unidad de uno es mas
# de un 60 % mayor que el del otro. Es el umbral que pide el plan (Fase 0).
FACTOR_PRECIO = 1.60
# Por debajo de esto el precio por unidad no distingue nada (centimos de ruido).
PRECIO_MINIMO_CENT = 5


def carga() -> tuple[pl.DataFrame, pl.DataFrame]:
    g = pl.read_parquet(config.GOLD / "grupos.parquet")
    e = pl.read_parquet(config.GOLD / "enlaces.parquet")
    return g, e


def filas_utiles(g: pl.DataFrame) -> list[dict]:
    return g.select([
        "fuente", "id_fuente", "nombre", "marca", "cantidad", "unidad_canon", "ean",
        "precio_cent", "precio_unidad_cent", "precio_ref_canon_cent",
        "unidad_ref_canon", "categoria", "seccion", "grupo_id",
        "comparacion_fiable", "precio_comparable",
    ]).to_dicts()


def normaliza(filas: list[dict]) -> None:
    """Prepara las tres claves de comparacion que el diagnostico necesita.

    `seccion` es la unica taxonomia que las cinco cadenas comparten (20 valores);
    `categoria` no sirve para comparar porque cada cadena la escribe a su manera
    ("Bebidas > Cervezas > ..." en Carrefour, "la-despensa/desayuno" en Mercadona,
    "Cuidado facial y corporal" en Alcampo).
    """
    for f in filas:
        f["ean_n"] = _ean(f.get("ean"))
        f["cat1"] = (f.get("seccion") or "").strip().lower() or None
        f["marca_n"] = " ".join((f.get("marca") or "").lower().split()) or None


def seccion(t: str) -> None:
    print(f"\n=== {t} ===")


def grupos_y_cadenas(filas, g) -> dict:
    n_grupos = g["grupo_id"].n_unique()
    tamaños = Counter(g["grupo_id"].to_list())
    por_grupo_cadenas: dict[int, set] = defaultdict(set)
    for f in filas:
        por_grupo_cadenas[f["grupo_id"]].add(f["fuente"])
    comparables = {k for k, v in por_grupo_cadenas.items() if len(v) > 1}
    productos_comp = sum(tamaños[k] for k in comparables)
    reparto = Counter(len(v) for v in por_grupo_cadenas.values())
    solos = sum(1 for v in tamaños.values() if v == 1)
    # Grupos con varios productos pero todos de la MISMA cadena: no comparan nada
    # entre cadenas, solo dicen que una cadena publica el mismo producto dos veces.
    solo_una_cadena = sum(1 for v in por_grupo_cadenas.values() if len(v) == 1) - solos
    # Un grupo donde una cadena mete dos productos distintos: o son dos
    # variantes del mismo producto (pack y unidad) o es un enlace de mas.
    cuenta: dict[int, Counter] = defaultdict(Counter)
    for f in filas:
        cuenta[f["grupo_id"]][f["fuente"]] += 1
    repetidos = sum(1 for k, v in por_grupo_cadenas.items()
                    if len(v) > 1 and any(n > 1 for n in cuenta[k].values()))
    return {
        "n_grupos": n_grupos,
        "tamaños": tamaños,
        "comparables": comparables,
        "productos_comparables": productos_comp,
        "solos": solos,
        "solo_una_cadena": solo_una_cadena,
        "reparto_cadenas": reparto,
        "grupos_con_cadena_repetida": repetidos,
    }


def tope_ean(filas, links) -> dict:
    """El techo de calidad: pares entre cadenas con el mismo codigo de barras."""
    por_ean: dict[str, list[int]] = defaultdict(list)
    for i, f in enumerate(filas):
        if f["ean_n"]:
            por_ean[f["ean_n"]].append(i)
    verdad: set[tuple[int, int]] = set()
    por_par_cadenas: Counter = Counter()
    ean_multicadena = 0
    for ids in por_ean.values():
        if len({filas[i]["fuente"] for i in ids}) < 2:
            continue
        ean_multicadena += 1
        for a in range(len(ids)):
            for b in range(a + 1, len(ids)):
                i, j = ids[a], ids[b]
                if filas[i]["fuente"] == filas[j]["fuente"]:
                    continue
                verdad.add((min(i, j), max(i, j)))
                par = tuple(sorted((filas[i]["fuente"], filas[j]["fuente"])))
                por_par_cadenas[par] += 1
    mismo_grupo = sum(1 for i, j in verdad
                      if filas[i]["grupo_id"] == filas[j]["grupo_id"])
    pares = {(min(i, j), max(i, j)) for i, j, _, _ in links}
    enlazados = len(pares & verdad)
    return {
        "con_ean": sum(1 for f in filas if f["ean_n"]),
        "ean_multicadena": ean_multicadena,
        "verdad": len(verdad),
        "pares": verdad,
        "mismo_grupo": mismo_grupo,
        "enlazados": enlazados,
        "por_par_cadenas": por_par_cadenas,
    }


def sospechosos(filas, links) -> dict:
    """Mide los pares aceptados contra las senales duras.

    La distincion que importa: un par "equivalente" (marca blanca de una cadena
    frente a la de otra) tiene por definicion dos EAN distintos y eso NO es un
    fallo, es justo lo que el proyecto quiere emparejar. Lo que si es un fallo
    demostrable es un par con la MISMA marca y dos EAN distintos: dos codigos de
    barras diferentes son dos productos diferentes, aunque el texto se parezca.
    """
    unidad, precio, cat = [], [], []
    mismo_ean, ean_distinto, marca_igual_ean_distinto = [], [], []
    for i, j, _par, nivel in links:
        a, b = filas[i], filas[j]
        ua, ub = a.get("unidad_canon"), b.get("unidad_canon")
        if ua and ub and ua != ub:
            unidad.append((i, j, _par, nivel))
        pa, pb = a.get("precio_unidad_cent"), b.get("precio_unidad_cent")
        if (pa and pb and min(pa, pb) >= PRECIO_MINIMO_CENT
                and ua and ub and ua == ub):
            r = max(pa, pb) / min(pa, pb)
            if r > FACTOR_PRECIO:
                precio.append((i, j, _par, nivel, r))
        if a["ean_n"] and b["ean_n"]:
            if a["ean_n"] == b["ean_n"]:
                mismo_ean.append((i, j, _par, nivel))
            else:
                ean_distinto.append((i, j, _par, nivel))
                if a["marca_n"] and a["marca_n"] == b["marca_n"]:
                    marca_igual_ean_distinto.append((i, j, _par, nivel))
        if a["cat1"] and b["cat1"] and a["cat1"] != b["cat1"]:
            cat.append((i, j, _par, nivel))
    return {"unidad": unidad, "precio": precio, "categoria": cat,
            "mismo_ean": mismo_ean, "ean_distinto": ean_distinto,
            "marca_igual_ean_distinto": marca_igual_ean_distinto}


def grupos_contradictorios(filas) -> dict:
    """Grupos con dos EAN distintos dentro.

    Dos casos muy distintos:
      - misma marca: dos productos del mismo fabricante con codigos de barras
        diferentes son DOS productos (entera y desnatada, 1 L y 1,5 L). Es un
        error demostrable, no una opinion.
      - distinta marca: es lo normal y lo deseado -- la marca blanca de una
        cadena nunca comparte EAN con la de otra. No cuenta como error.
    """
    por_grupo: dict[int, set] = defaultdict(set)
    marcas: dict[int, set] = defaultdict(set)
    for f in filas:
        if f["ean_n"]:
            por_grupo[f["grupo_id"]].add(f["ean_n"])
            if f["marca_n"]:
                marcas[f["grupo_id"]].add(f["marca_n"])
    todos = {k for k, v in por_grupo.items() if len(v) > 1}
    misma = {k for k in todos if len(marcas[k]) == 1 and k in marcas}
    return {"todos": todos, "misma_marca": misma}


def unidad_por_grupo(filas) -> list[int]:
    por_grupo: dict[int, set] = defaultdict(set)
    for f in filas:
        if f.get("unidad_canon"):
            por_grupo[f["grupo_id"]].add(f["unidad_canon"])
    return [k for k, v in por_grupo.items() if len(v) > 1]


def seccion_por_grupo(filas) -> list[int]:
    por_grupo: dict[int, set] = defaultdict(set)
    for f in filas:
        if f.get("cat1"):
            por_grupo[f["grupo_id"]].add(f["cat1"])
    return [k for k, v in por_grupo.items() if len(v) > 1]


# Secciones que son un pasillo transversal, no un tipo de producto: dos productos
# del mismo grupo pueden caer en "promociones" o "ecologico" sin que eso sea un
# error. Para medir la hipotesis 5 (categoria) hay que quitarlas.
SECCIONES_TRANSVERSALES = {"promociones", "ecologico", "hogar"}


def seccion_mezclada_real(filas) -> list[int]:
    por_grupo: dict[int, set] = defaultdict(set)
    for f in filas:
        c = f.get("cat1")
        if c and c not in SECCIONES_TRANSVERSALES:
            por_grupo[f["grupo_id"]].add(c)
    return [k for k, v in por_grupo.items() if len(v) > 1]


# Topes a partir de los cuales una cantidad es imposible en un supermercado
# online (un saco de 25 kg de pienso existe; 63 litros de suavizante, no).
ABSURDOS = {"kg": 25.0, "l": 25.0, "ud": 250.0, "m": 200.0}


def calidad_formato(filas) -> dict:
    """Cuanta confianza merece el campo que el plan quiere usar como puerta dura.

    El bloqueo propuesto (categoria + marca + cantidad/unidad) solo puede
    funcionar si `cantidad` y `unidad_canon` son de fiar. Esto lo mide, cadena a
    cadena, porque de aqui depende media Fase 2.
    """
    res: dict[str, dict] = {}
    for f in filas:
        c = res.setdefault(f["fuente"], {"n": 0, "sin_cantidad": 0, "ud": 0,
                                         "absurdo": 0, "ud_cantidad_1": 0,
                                         "sin_unidad": 0})
        c["n"] += 1
        cant, uni = f.get("cantidad"), f.get("unidad_canon")
        if cant is None:
            c["sin_cantidad"] += 1
            continue
        if not uni:
            c["sin_unidad"] += 1
            continue
        if uni == "ud":
            c["ud"] += 1
            if float(cant) == 1.0:
                c["ud_cantidad_1"] += 1
        tope = ABSURDOS.get(uni)
        if tope and float(cant) > tope:
            c["absurdo"] += 1
    return res


def sin_formato(filas) -> int:
    return sum(1 for f in filas if f.get("cantidad") is None or not f.get("unidad_canon"))


def tope_por_bloque(filas) -> dict:
    """El otro tope: cuantos productos PODRIAN tener alternativa en otra cadena.

    El tope del EAN (1.821 pares) solo cubre marca nacional y no sirve para medir
    el objetivo real del proyecto, que es comparar la marca blanca de una cadena
    con la de otra. Este es el techo de verdad: se agrupa por la clave de bloqueo
    que propone el plan -- (seccion, unidad_canon, cantidad) -- y se cuenta
    cuantos productos caen en un bloque con >=2 cadenas. Si la seccion se
    equivoca, esto baja; si el formato es ilegible, el producto no entra.
    """
    bloques: dict[tuple, Counter] = defaultdict(Counter)
    for f in filas:
        c, u = f.get("cantidad"), f.get("unidad_canon")
        if c is None or not u or not f.get("cat1"):
            continue
        bloques[(f["cat1"], u, round(float(c), 3))][f["fuente"]] += 1
    utiles = {k: v for k, v in bloques.items() if len(v) > 1}
    productos = sum(sum(v.values()) for v in utiles.values())
    pares = 0
    for v in utiles.values():
        fuentes = sorted(v)
        for x in range(len(fuentes)):
            for y in range(x + 1, len(fuentes)):
                pares += min(v[fuentes[x]], v[fuentes[y]])
    return {"bloques": len(utiles), "productos": productos, "pares_1a1": pares}


def dispersion_grupos(filas) -> dict:
    """Grupos demasiado anchos: el bloqueo numero uno segun el BACKLOG (§2).

    El BACKLOG dejo escrito que hoy hay 405 grupos con mas del 200 % de
    dispersion dentro (el mas caro cuesta mas del triple que el mas barato) y que
    eso mide lo ancho que es el grupo, no el ahorro. Aqui se comprueba con el
    catalogo de hoy, solo en grupos donde comparar precios significa algo
    (kg/l/m): mezclar un bote de 500 g con uno de 1 kg en 'ud' no cuenta.
    """
    precios: dict[int, list[float]] = defaultdict(list)
    for f in filas:
        p, u = f.get("precio_unidad_cent"), f.get("unidad_canon")
        if p and u in ("kg", "l", "m"):
            precios[f["grupo_id"]].append(float(p))
    ratios = {}
    for k, v in precios.items():
        if len(v) > 1 and min(v) > 0:
            ratios[k] = max(v) / min(v)
    tramos = Counter()
    for r in ratios.values():
        if r > 3.0:
            tramos[">200 %"] += 1
        elif r > 2.0:
            tramos["100-200 %"] += 1
        elif r > 1.5:
            tramos["50-100 %"] += 1
        else:
            tramos["<50 %"] += 1
    return {"con_precio": len(ratios), "tramos": tramos,
            "mas_200": tramos.get(">200 %", 0),
            "peores": sorted(ratios.items(), key=lambda x: -x[1])[:10]}


def por_que_falla(filas, verdad, ls_sin_ean) -> dict:
    """Descompone los pares ciertos que el emparejador por nombre NO encuentra.

    Cada par que hoy sabemos cierto por EAN falla por una de cuatro razones, y
    cada una se arregla en una fase distinta del plan:

      formato ilegible      -> dato (parseo), no algoritmo
      unidad distinta       -> dato o venta por peso frente a por unidad
      misma unidad, otra cantidad -> pack frente a pieza suelta
      mismo formato         -> aqui si falla el algoritmo: o el umbral o la
                               eleccion mutua (un tercero le robo el candidato)
    """
    pares = {(min(i, j), max(i, j)) for i, j, _, _ in ls_sin_ean}
    acertados = pares & verdad
    fallados = sorted(verdad - pares)
    motivos: Counter = Counter()
    detalle: list[dict] = []

    docs = [tokens(f.get("nombre") or "", f.get("marca")) for f in filas]
    tris = [trigramas(f.get("nombre") or "", f.get("marca")) for f in filas]
    pesos = idf(docs)

    for i, j in fallados:
        a, b = filas[i], filas[j]
        ca, cb = a.get("cantidad"), b.get("cantidad")
        ua, ub = a.get("unidad_canon"), b.get("unidad_canon")
        s = max(parecido(docs[i], docs[j], pesos), 0.85 * dice(tris[i], tris[j]))
        if not ua or not ub or ca is None or cb is None:
            clase = "formato ilegible en alguno de los dos"
        elif ua != ub:
            clase = "una cadena lo vende en otra unidad"
        elif abs(float(ca) - float(cb)) > 1e-6:
            clase = "misma unidad, cantidad distinta (pack frente a unidad)"
        elif s >= 0.55:
            clase = "puntua sobre el umbral y otro se lleva la pareja"
        else:
            clase = "mismo formato y por debajo del umbral"
        motivos[clase] += 1
        detalle.append({"clase": clase, "parecido": round(s, 3),
                        "a": f"{a['nombre']} [{a['fuente']}] {ca}{ua or ''}",
                        "b": f"{b['nombre']} [{b['fuente']}] {cb}{ub or ''}"})
    return {"acertados": len(acertados), "fallados": len(fallados),
            "motivos": motivos, "detalle": detalle}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="diagnostico_matching")
    ap.add_argument("--json", action="store_true", help="vuelca los numeros en JSON")
    ap.add_argument("--ejemplos", type=int, default=20)
    a = ap.parse_args(argv)

    g, e = carga()
    filas = filas_utiles(g)
    normaliza(filas)
    links = list(zip(e["i"].to_list(), e["j"].to_list(),
                     e["parecido"].to_list(), e["nivel"].to_list(), strict=True))

    R = {}
    seccion("1. catalogo y grupos")
    r = grupos_y_cadenas(filas, g)
    R["productos"] = g.height
    R["grupos"] = r["n_grupos"]
    R["grupos_comparables"] = len(r["comparables"])
    R["productos_comparables"] = r["productos_comparables"]
    R["productos_solos"] = r["solos"]
    print(f"productos: {g.height}")
    print(f"grupos: {r['n_grupos']}  (de 1 producto: {r['solos']}, "
          f"de >=2: {r['n_grupos'] - r['solos']})")
    print(f"grupos con >=2 cadenas: {len(r['comparables'])}")
    print(f"grupos con varios productos pero una sola cadena: "
          f"{r['solo_una_cadena']}")
    R["grupos_una_sola_cadena"] = r["solo_una_cadena"]
    print(f"productos dentro de un grupo comparable: {r['productos_comparables']} "
          f"({100 * r['productos_comparables'] / g.height:.1f} % del catalogo)")
    print(f"reparto de cadenas por grupo: "
          f"{dict(sorted(r['reparto_cadenas'].items()))}")
    print(f"grupos con la misma cadena repetida: {r['grupos_con_cadena_repetida']}")
    R["grupos_cadena_repetida"] = r["grupos_con_cadena_repetida"]
    R["sin_cantidad_ni_unidad"] = sin_formato(filas)
    print(f"productos sin cantidad/unidad (bloque '?'): {R['sin_cantidad_ni_unidad']}")

    seccion("2. tope alcanzable por EAN")
    t = tope_ean(filas, links)
    R.update({k: v for k, v in t.items() if k not in ("por_par_cadenas", "pares")})
    print(f"productos con EAN: {t['con_ean']} ({100 * t['con_ean'] / g.height:.1f} %)")
    print(f"EAN distintos presentes en >=2 cadenas: {t['ean_multicadena']}")
    print(f"pares entre cadenas con el mismo EAN (TOPE): {t['verdad']}")
    print(f"  de esos, hoy en el MISMO grupo: {t['mismo_grupo']} "
          f"({100 * t['mismo_grupo'] / max(t['verdad'], 1):.1f} %)")
    print(f"  de esos, unidos por un enlace directo: {t['enlazados']} "
          f"({100 * t['enlazados'] / max(t['verdad'], 1):.1f} %)")
    R["recall_tope"] = 100 * t["mismo_grupo"] / max(t["verdad"], 1)
    print("  tope por par de cadenas:")
    for par, n in t["por_par_cadenas"].most_common():
        print(f"    {'/'.join(par):28s} {n:6d}")

    tp = tope_por_bloque(filas)
    R["tope_bloque"] = tp
    print("  el EAN no es el tope util (solo marca nacional). Tope por bloque "
          "(seccion+unidad+cantidad):")
    print(f"    bloques con >=2 cadenas: {tp['bloques']}")
    print(f"    productos que caben en alguno: {tp['productos']} "
          f"({100 * tp['productos'] / g.height:.1f} % del catalogo)")
    print(f"    pares 1-a-1 maximos que se podrian formar: {tp['pares_1a1']}")
    print(f"    hoy hay {r['productos_comparables']} productos comparables dentro "
          f"de grupos: {100 * r['productos_comparables'] / max(tp['productos'], 1):.0f} % "
          f"del tope")

    seccion("3. sospechosos dentro de lo aceptado")
    s = sospechosos(filas, links)
    R["enlaces"] = len(links)
    R["identicos"] = sum(1 for x in links if x[3] == "identico")
    R["equivalentes"] = R["enlaces"] - R["identicos"]
    print(f"enlaces aceptados: {len(links)} "
          f"({R['identicos']} identicos, {R['equivalentes']} equivalentes)")
    for clave, etiqueta in (
            ("unidad", "unidad canonica distinta"),
            ("precio", "precio/unidad difiere >60 %"),
            ("categoria", "seccion distinta"),
            ("mismo_ean", "mismo EAN (acierto demostrable)"),
            ("ean_distinto", "EAN distinto (normal entre marcas)"),
            ("marca_igual_ean_distinto", "MISMA marca y EAN distinto (fallo)")):
        v = s[clave]
        R[clave] = len(v)
        print(f"  {etiqueta:40s} {len(v):6d} "
              f"({100 * len(v) / len(links):.1f} % de los enlaces)")
    con_ean = len(s["mismo_ean"]) + len(s["ean_distinto"])
    R["enlaces_con_ean_en_ambos"] = con_ean
    print(f"  enlaces con EAN en los dos lados: {con_ean} "
          f"({100 * con_ean / len(links):.1f} % del total)")
    gc = grupos_contradictorios(filas)
    R["grupos_con_ean_distinto"] = len(gc["todos"])
    R["grupos_misma_marca_ean_distinto"] = len(gc["misma_marca"])
    prods = sum(1 for f in filas if f["grupo_id"] in gc["misma_marca"])
    R["productos_en_grupo_misma_marca_ean_distinto"] = prods
    ug = unidad_por_grupo(filas)
    sg = seccion_por_grupo(filas)
    comp = r["comparables"]
    R["grupos_comparables_unidad_mixta"] = len([k for k in ug if k in comp])
    R["grupos_comparables_seccion_mixta"] = len([k for k in sg if k in comp])
    R["grupos_con_ean_distinto_comparables"] = len(
        [k for k in gc["todos"] if k in comp])
    print(f"grupos con dos EAN distintos dentro: {len(gc['todos'])} "
          f"({R['grupos_con_ean_distinto_comparables']} de ellos comparables)")
    print(f"  de esos, con la MISMA marca: {len(gc['misma_marca'])} grupos, "
          f"{prods} productos")
    print(f"grupos con unidad mixta: {len(ug)} "
          f"({R['grupos_comparables_unidad_mixta']} comparables)")
    print(f"grupos con seccion mixta: {len(sg)} "
          f"({R['grupos_comparables_seccion_mixta']} comparables)")
    sm = seccion_mezclada_real(filas)
    R["grupos_seccion_mixta_real"] = len([k for k in sm if k in comp])
    print(f"  quitando las secciones transversales "
          f"({', '.join(sorted(SECCIONES_TRANSVERSALES))}): "
          f"{R['grupos_seccion_mixta_real']} comparables")

    dg = dispersion_grupos(filas)
    R["dispersion"] = {"con_precio": dg["con_precio"],
                       "tramos": dict(dg["tramos"]), "mas_200": dg["mas_200"]}
    print(f"grupos con precio por unidad comparable (kg/l/m): {dg['con_precio']}")
    for tramo in (">200 %", "100-200 %", "50-100 %", "<50 %"):
        if dg["tramos"].get(tramo):
            print(f"    el mas caro cuesta {tramo:10s} que el mas barato: "
                  f"{dg['tramos'][tramo]:5d} grupos")
    print(f"  (el BACKLOG §2 dejo escrito que eran 405 los grupos de mas del "
          f"200 %; hoy son {dg['mas_200']})")

    seccion("3b. calidad del campo de formato (lo que el bloqueo daria por bueno)")
    cf = calidad_formato(filas)
    R["calidad_formato"] = cf
    print(f"  {'cadena':11s} {'prod':>6s} {'sin cant':>9s} {'en ud':>7s} "
          f"{'ud=1':>6s} {'absurdo':>8s}")
    for fuente, c in sorted(cf.items(), key=lambda x: -x[1]["n"]):
        print(f"  {fuente:11s} {c['n']:6d} {c['sin_cantidad']:9d} {c['ud']:7d} "
              f"{c['ud_cantidad_1']:6d} {c['absurdo']:8d}")
    print("  absurdo = cantidad imposible para esa unidad ("
          + ", ".join(f"{k}>{v:g}" for k, v in ABSURDOS.items()) + ")")

    # Fase 0, punto 3: por que falla. Se recalcula el emparejamiento por nombre
    # con el EAN escondido (lo mismo que hace `emparejar --medir`) y se mira
    # par a par que le paso a cada uno de los que hoy sabemos ciertos.
    seccion("4. por que falla: los pares ciertos que el nombre no encuentra")
    print("  recalculando enlaces sin EAN (unos 45 s)...")
    ls_por_nombre = enlaces(filas, umbral=0.55, usar_ean=False)
    fallo = por_que_falla(filas, t["pares"], ls_por_nombre)
    R["recall_por_nombre"] = 100 * fallo["acertados"] / max(t["verdad"], 1)
    R["fallos_por_motivo"] = dict(fallo["motivos"])
    print(f"  el emparejador por nombre encuentra {fallo['acertados']} de "
          f"{t['verdad']} ({R['recall_por_nombre']:.0f} %)")
    print(f"  se le escapan {fallo['fallados']}, y el motivo es:")
    for motivo, n in fallo["motivos"].most_common():
        print(f"    {motivo:52s} {n:5d} "
              f"({100 * n / max(fallo['fallados'], 1):.0f} %)")
    anchos = [d["parecido"] for d in fallo["detalle"]
              if d["clase"] == "mismo formato y por debajo del umbral"]
    if anchos:
        anchos.sort()
        print(f"  de los que fallan por umbral, parecido mediano "
              f"{anchos[len(anchos) // 2]:.2f} (min {anchos[0]:.2f}, "
              f"max {anchos[-1]:.2f})")
    R["fallos_detalle"] = fallo["detalle"][:60]

    seccion("5. ejemplos de malas asociaciones")
    ya = set()
    ejemplos = []

    def anade(i, j, motivo, extra=""):
        if len(ejemplos) >= a.ejemplos:
            return
        clave = (filas[i]["grupo_id"], motivo)
        if clave in ya:
            return
        ya.add(clave)
        ejemplos.append({
            "motivo": motivo, "extra": extra,
            "grupo": int(filas[i]["grupo_id"]),
            "a": f"{filas[i]['nombre']} [{filas[i]['fuente']}] "
                 f"{filas[i]['marca'] or '-'} {filas[i]['cantidad'] or '?'}"
                 f"{filas[i]['unidad_canon'] or ''} ean={filas[i]['ean_n'] or '-'} "
                 f"pud={filas[i]['precio_unidad_cent']}",
            "b": f"{filas[j]['nombre']} [{filas[j]['fuente']}] "
                 f"{filas[j]['marca'] or '-'} {filas[j]['cantidad'] or '?'}"
                 f"{filas[j]['unidad_canon'] or ''} ean={filas[j]['ean_n'] or '-'} "
                 f"pud={filas[j]['precio_unidad_cent']}",
        })

    for i, j, p, niv in s["marca_igual_ean_distinto"][:14]:
        anade(i, j, "misma marca, dos EAN distintos", f"nivel={niv} p={p:.2f}")
    for i, j, p, _niv, rr in sorted(s["precio"], key=lambda x: -x[4])[:8]:
        anade(i, j, "precio por unidad dispar", f"x{rr:.2f} p={p:.2f}")
    for i, j, p, niv in s["unidad"][:8]:
        anade(i, j, "unidad canonica distinta", f"nivel={niv} p={p:.2f}")
    for i, j, p, niv in s["categoria"][:8]:
        anade(i, j, "seccion distinta", f"nivel={niv} p={p:.2f}")

    for n, ex in enumerate(ejemplos, 1):
        print(f"\n{n:2d}. [{ex['motivo']}] {ex['extra']}")
        print(f"    grupo {ex['grupo']}")
        print(f"    A: {ex['a']}")
        print(f"    B: {ex['b']}")

    R["ejemplos"] = ejemplos
    if a.json:
        (config.GOLD / "diagnostico_matching.json").write_text(
            json.dumps(R, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        print(f"\nescrito {config.GOLD / 'diagnostico_matching.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
