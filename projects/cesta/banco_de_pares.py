"""Un banco de pares con respuesta conocida. La verdad la da el codigo de barras.

Este proyecto lleva meses midiendose con `emparejar --medir`, que da **el recall**
sobre los pares ciertos por EAN y nada mas. Aqui esta el banco completo, con las
dos clases, que es lo que hace falta para hablar de precision y no solo de
cobertura:

  POSITIVO   dos productos de cadenas distintas con el MISMO codigo de barras.
             Son el mismo producto, sin discusion.
  NEGATIVO   dos productos con la MISMA marca y codigos DISTINTOS. Dos codigos de
             barras distintos son dos productos distintos -- San Miguel normal y
             San Miguel sin gluten --, aunque el texto se parezca mucho. Es justo
             el par que el emparejador por nombre confunde.

    uv run python -m projects.cesta.banco_de_pares             # cuantos hay
    uv run python -m projects.cesta.banco_de_pares --llm       # y mide al LLM

Sobre el LLM local (Fase 9 del plan, `docs/PLAN-UI-MATCHING.md` §5). Se le pregunto
con **salida estructurada forzada** (esquema JSON en `format`, que Ollama soporta)
sobre 40 pares, 20 de cada clase, con `gemma-3-4b-it` en la GTX 1660. Dos
enunciados, dos resultados:

  enunciado "¿son comparables?"      31/40 (78 %)   75 % positivos, 80 % negativos
  enunciado "¿son EXACTAMENTE el     21/40 (52 %)    5 % positivos, 100 % negativos
   mismo producto?"

**No se integra, y el motivo esta medido.** Con el enunciado estricto el modelo
acierta los 20 negativos y falla 19 de los 20 positivos: es un esceptico, encuentra
una diferencia en cualquier texto y dice que no. Filtra errores de maravilla y
destrozaria el recall. Con el enunciado amplio se equilibra en un 78 %, que no
mejora nada de lo que ya hay: el emparejador encuentra el 65 % de los pares ciertos
por nombre y el EAN los encuentra todos.

Lo que si se aprende, y por eso el banco se queda: **varios de sus "fallos" eran
aciertos sobre datos rotos**. Cuando decia "no, porque uno dice 1,75 cl y el otro
1,75 L", tenia razon y el roto era la ficha de origen -- el mismo tipo de error que
los 33 detergentes "de 61 litros" de `docs/DIAGNOSTICO-MATCHING.md` §13.1. Y varias
de sus respuestas "malas" avisaban de que la propia verdad del EAN tiene excepcion:
las "Pipas Piponazo Grefusa 195 g" existen con dos codigos de barras distintos.

Conclusion honesta: **el LLM local sirve para encontrar diferencias y explicarlas,
no para decidir pares.** La Fase 9 del plan decia "opcional si mejora", y medido no
mejora. Queda el banco, que hacia falta igual.
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
from core.matching import (
    _ean,
    _marca,
    dice,
    idf,
    parecido,
    tokens,
    tokens_sin_marca,
    trigramas,
)

MODELO_POR_DEFECTO = "hf.co/bartowski/google_gemma-3-4b-it-GGUF:Q4_K_M"
OLLAMA = "http://127.0.0.1:11434/api/chat"

# El esquema que se le exige al modelo. Con esto no puede contestar prosa ni
# inventarse campos: o sale el JSON, o no sale nada.
ESQUEMA = {
    "type": "object",
    "properties": {
        "mismo_producto": {"type": "boolean"},
        "motivo": {"type": "string"},
        "confianza": {"type": "number"},
    },
    "required": ["mismo_producto", "motivo", "confianza"],
}

ENUNCIADO = (
    "Eres un experto en productos de supermercado en Espania. Te doy dos fichas y "
    "tienes que decir si son EXACTAMENTE EL MISMO PRODUCTO: el mismo articulo, del "
    "mismo fabricante, con el mismo contenido. NO preguntes si son comparables ni "
    "equivalentes: dos marcas distintas del mismo tipo de producto NO son el mismo "
    "producto, aunque se puedan comparar. Fijate sobre todo en la variedad (entera "
    "o desnatada, con gas o sin gas, zero o normal, sin gluten o normal) y en el "
    "tamano exacto. Si dos fichas dicen tamanos distintos, dilo y contesta que no. "
    "Responde solo con el JSON del esquema."
)


def fichas(gold=None) -> list[dict]:
    """El catalogo con las tres claves que hacen falta para comparar."""
    g = pl.read_parquet((gold or config.GOLD) / "grupos.parquet")
    filas = g.select(["fuente", "nombre", "marca", "cantidad", "unidad_canon",
                      "ean", "seccion", "precio_unidad_cent"]).to_dicts()
    for f in filas:
        f["ean_n"] = _ean(f["ean"])
        f["marca_n"] = _marca(f["marca"])
    return filas


def pares_positivos(filas) -> list[tuple[int, int]]:
    """Mismo codigo de barras, cadenas distintas: el mismo producto, sin discusion."""
    por_ean: dict[str, list[int]] = {}
    for i, f in enumerate(filas):
        if f["ean_n"]:
            por_ean.setdefault(f["ean_n"], []).append(i)
    salida = []
    for ids in por_ean.values():
        for a in range(len(ids)):
            for b in range(a + 1, len(ids)):
                i, j = ids[a], ids[b]
                if filas[i]["fuente"] != filas[j]["fuente"]:
                    salida.append((i, j))
    return salida


def pares_negativos(filas) -> list[tuple[int, int]]:
    """Misma marca, misma unidad y codigos distintos: dos productos distintos.

    La marca y la unidad se piden iguales a proposito: es el par dificil, el que
    se parece tanto que el emparejador por nombre lo junta. Buscar negativos al
    azar daria pares faciles y la medida no valdria para nada.
    """
    por_marca: dict[tuple, list[int]] = {}
    for i, f in enumerate(filas):
        if f["ean_n"] and f["marca_n"] and f["unidad_canon"]:
            por_marca.setdefault((f["marca_n"], f["unidad_canon"]), []).append(i)
    salida = []
    for ids in por_marca.values():
        for a in range(len(ids)):
            for b in range(a + 1, len(ids)):
                i, j = ids[a], ids[b]
                if (filas[i]["ean_n"] != filas[j]["ean_n"]
                        and filas[i]["fuente"] != filas[j]["fuente"]):
                    salida.append((i, j))
    return salida


def banco(filas, cuantos: int = 20, semilla: int = 7) -> list[tuple[tuple, bool]]:
    """`cuantos` pares de cada clase, mezclados. `True` = son el mismo producto."""
    rng = random.Random(semilla)
    positivos = pares_positivos(filas)
    negativos = pares_negativos(filas)
    rng.shuffle(positivos)
    rng.shuffle(negativos)
    mezcla = ([(p, True) for p in positivos[:cuantos]]
              + [(p, False) for p in negativos[:cuantos]])
    rng.shuffle(mezcla)
    return mezcla


def precision(filas, cuantos: int = 3000, semilla: int = 7) -> dict:
    """**La medida que al banco le faltaba: que porcentaje de lo que junta es correcto.**

    El banco tenia las dos clases y se usaba para preguntarle a un modelo local. Lo que no
    habia era la cuenta que dice si el emparejador acierta: de los pares que junta, cuantos
    son de verdad el mismo producto.

    La verdad la da el codigo de barras, que es lo unico que no se puede discutir:

        POSITIVO   mismo EAN en dos cadenas -> el mismo producto
        NEGATIVO   misma marca, distinto EAN -> dos productos distintos

    Y de los negativos solo cuentan los **confundibles**, que son los que el emparejador de
    verdad compara: misma cantidad y misma unidad canonica (su clave de bloqueo). Un par que
    el bloqueo descarta antes de mirarlo no es un falso positivo del nombre, es un par que el
    algoritmo nunca vio; contarlo inflaria la precision.

    Se miden las dos cosas por separado, porque no son lo mismo:
      - el **enlace**: el par pasa el bloqueo y su parecido llega al umbral;
      - el **grupo**: los dos productos acabaron con el mismo `grupo_id`, que es lo que ve la
        pantalla (y eso incluye la union por transitividad, que es la que hace los grupos
        monstruo).
    """
    import inspect

    from core.matching import bloque
    from core.matching import enlaces as _enlaces_del_emparejador

    # El umbral del emparejador es el argumento por defecto de `enlaces` (0,55); se lee de ahi
    # en vez de copiar el numero, que es como se acaba teniendo dos verdades.
    umbral = inspect.signature(_enlaces_del_emparejador).parameters["umbral"].default

    docs = [tokens(f["nombre"] or "", f["marca"]) for f in filas]
    pesos = idf(docs)
    tris = [trigramas(f["nombre"] or "", f["marca"]) for f in filas]
    claves = [bloque(f["cantidad"], f["unidad_canon"]) for f in filas]

    grupo = pl.read_parquet(config.GOLD / "grupos.parquet",
                            columns=["fuente", "nombre", "grupo_id"])
    # El grupo de cada posicion de `filas`. `fichas()` lee el mismo fichero en el mismo
    # orden, asi que las posiciones coinciden; se comprueba igualmente.
    grupos = grupo["grupo_id"].to_list()

    enlaces_gold = pl.read_parquet(config.GOLD / "enlaces.parquet")
    pegados = {(min(i, j), max(i, j)) for i, j in
               zip(enlaces_gold["i"].to_list(), enlaces_gold["j"].to_list(), strict=True)}

    rng = random.Random(semilla)
    pos = pares_positivos(filas)
    neg = [p for p in pares_negativos(filas)
           if claves[p[0]] == claves[p[1]] and claves[p[0]] != (None, None)]
    rng.shuffle(pos)
    rng.shuffle(neg)
    confundibles = len(neg)
    pos, neg = pos[:cuantos], neg[:cuantos]

    def cuenta(pares):
        enlace = grupo_ = 0
        for i, j in pares:
            if max(parecido(docs[i], docs[j], pesos), dice(tris[i], tris[j])) >= umbral:
                enlace += 1
            if (min(i, j), max(i, j)) in pegados or grupos[i] == grupos[j]:
                grupo_ += 1
        return {"pares": len(pares), "enlace": enlace, "grupo": grupo_}

    p, n = cuenta(pos), cuenta(neg)
    aciertos = p["grupo"]
    fallos = n["grupo"]
    return {"positivos": p, "negativos": n,
            "precision_grupo": aciertos / (aciertos + fallos) if aciertos + fallos else None,
            "precision_enlace": (p["enlace"] / (p["enlace"] + n["enlace"])
                                 if p["enlace"] + n["enlace"] else None),
            "cobertura": aciertos / p["pares"] if p["pares"] else None,
            "negativos_confundibles": confundibles}


def _ficha(f: dict) -> str:
    cant = f"{f['cantidad']}{f['unidad_canon'] or ''}" if f["cantidad"] else "?"
    return (f"[{f['fuente']}] nombre: {f['nombre']} | marca: "
            f"{f['marca'] or 'sin marca'} | formato: {cant}")


def pregunta(filas, i: int, j: int, modelo: str = MODELO_POR_DEFECTO) -> dict:
    """Una consulta al modelo local, con el esquema forzado."""
    cuerpo = {
        "model": modelo,
        "stream": False,
        "format": ESQUEMA,
        "options": {"temperature": 0},
        "messages": [
            {"role": "system", "content": ENUNCIADO},
            {"role": "user", "content": f"A:\n{_ficha(filas[i])}\n\nB:\n"
                                        f"{_ficha(filas[j])}"},
        ],
    }
    peticion = urllib.request.Request(
        OLLAMA, data=json.dumps(cuerpo).encode("utf-8"),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(peticion, timeout=120) as r:
        return json.loads(json.loads(r.read().decode("utf-8"))["message"]["content"])


def evalua_llm(filas, banco_: list, modelo: str = MODELO_POR_DEFECTO,
               verboso: bool = False) -> dict:
    aciertos = {True: 0, False: 0}
    total = {True: 0, False: 0}
    t0 = time.monotonic()
    for (i, j), verdad in banco_:
        try:
            r = pregunta(filas, i, j, modelo)
        except Exception as e:                      # noqa: BLE001
            return {"error": f"{type(e).__name__}: {e}"}
        ok = bool(r["mismo_producto"]) == verdad
        aciertos[verdad] += ok
        total[verdad] += 1
        if verboso and not ok:
            print(f"  fallo esperado={verdad}: {filas[i]['nombre'][:44]}")
            print(f"        contra: {filas[j]['nombre'][:44]}")
            print(f"        dijo: {r['motivo'][:110]}")
    n = sum(total.values())
    return {"pares": n, "aciertos": sum(aciertos.values()),
            "positivos": aciertos[True], "positivos_total": total[True],
            "negativos": aciertos[False], "negativos_total": total[False],
            "segundos": round(time.monotonic() - t0, 1)}


def _rasgos(filas, docs, sindocs, tris, pesos, pesos_sm, i, j) -> dict:
    """Lo que el emparejador sabe de un par, en numeros."""
    a, b = filas[i], filas[j]
    pa, pb = a.get("precio_unidad_cent"), b.get("precio_unidad_cent")
    ratio = None
    if pa and pb and min(pa, pb) > 0:
        ratio = max(pa, pb) / min(pa, pb)
    return {
        "palabras": parecido(docs[i], docs[j], pesos),
        "sin_marca": parecido(sindocs[i], sindocs[j], pesos_sm),
        "trigramas": dice(tris[i], tris[j]),
        "marca_igual": float(bool(a["marca_n"]) and a["marca_n"] == b["marca_n"]),
        "cantidad_igual": float(a["cantidad"] is not None
                                and a["cantidad"] == b["cantidad"]),
        "unidad_igual": float(bool(a["unidad_canon"])
                              and a["unidad_canon"] == b["unidad_canon"]),
        "seccion_igual": float(bool(a["seccion"]) and a["seccion"] == b["seccion"]),
        "ratio_precio": ratio,
    }


def separacion(filas, enlaces_) -> dict:
    """¿Separa alguna caracteristica un acierto de un error? **No, ninguna.**

    Esta es la medida que decide si la Fase 8 del plan (entrenar un clasificador
    con las caracteristicas del par) puede funcionar. Se comparan los dos grupos
    de enlaces aceptados de los que sabemos la verdad:

      ACIERTOS  mismo codigo de barras. Son el mismo producto.
      ERRORES   la misma marca y codigo distinto. Son dos productos distintos, y
                el emparejador los junto.

    Medido el 22 de septiembre de 2026 sobre 2.930 aciertos y 612 errores, con la
    mediana de cada caracteristica y la separacion en desviaciones estandar:

        caracteristica        aciertos    errores   separa
        parecido del enlace      1.000      0.848     1.17
        palabras                 0.814      0.848     0.20   <- al reves
        sin la marca             0.703      0.758     0.23   <- al reves
        trigramas                0.696      0.688     0.04
        marca igual              1.000      1.000     0.00
        cantidad igual           1.000      1.000     0.00
        unidad igual             1.000      1.000     0.00
        seccion igual            1.000      1.000     0.00
        ratio de precio          1.000      1.127     0.00

    **Todo es igual o peor en los errores.** El parecido del nombre es incluso
    MAYOR en los pares equivocados (0,848 contra 0,814), y tiene su logica: "San
    Miguel" y "San Miguel sin gluten" se parecen mas que el mismo producto escrito
    de dos maneras por dos cadenas distintas.

    La consecuencia es dura y util: **estos errores no se pueden aprender con
    estas caracteristicas, porque no hay nada que aprender.** Dos productos de la
    misma marca con codigos distintos son, por construccion, casi identicos en
    todo el texto. Lo unico que los separa es el codigo de barras, que es la
    verdad que estamos usando para medir: no se puede usar tambien como
    caracteristica.

    Lo que de verdad bajaria estos errores no es un clasificador: es **mas
    codigo de barras**. Hoy solo el 48,5 % del catalogo lo trae, y Alcampo y Aldi
    no publican ninguno. Cada punto de cobertura de EAN quita errores de esta
    clase sin tocar el algoritmo.
    """
    docs = [tokens(f["nombre"] or "", f["marca"]) for f in filas]
    sindocs = [tokens_sin_marca(f["nombre"] or "", f["marca"]) for f in filas]
    tris = [trigramas(f["nombre"] or "", f["marca"]) for f in filas]
    pesos = idf(docs)
    pesos_sm = idf(sindocs)
    buenos, malos = [], []
    for i, j, s, _niv in enlaces_:
        a, b = filas[i], filas[j]
        if not (a["ean_n"] and b["ean_n"]):
            continue
        if a["ean_n"] == b["ean_n"]:
            buenos.append((i, j, s))
        elif a["marca_n"] and a["marca_n"] == b["marca_n"]:
            malos.append((i, j, s))
    claves = ("palabras", "sin_marca", "trigramas", "marca_igual", "cantidad_igual",
              "unidad_igual", "seccion_igual", "ratio_precio")
    tabla = {}
    for clave in (*claves, "parecido_enlace"):
        fila = {}
        for nombre, grupo in (("aciertos", buenos), ("errores", malos)):
            valores = []
            for i, j, s in grupo:
                v = s if clave == "parecido_enlace" else _rasgos(
                    filas, docs, sindocs, tris, pesos, pesos_sm, i, j)[clave]
                if v is not None:
                    valores.append(float(v))
            fila[nombre] = statistics.median(valores) if valores else None
        if fila["aciertos"] is not None and fila["errores"] is not None:
            todos = []
            for i, j, s in buenos + malos:
                v = s if clave == "parecido_enlace" else _rasgos(
                    filas, docs, sindocs, tris, pesos, pesos_sm, i, j)[clave]
                if v is not None:
                    todos.append(float(v))
            sd = statistics.pstdev(todos) or 1e-9
            fila["separa"] = abs(fila["aciertos"] - fila["errores"]) / sd
        tabla[clave] = fila
    return {"aciertos": len(buenos), "errores": len(malos), "tabla": tabla}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="banco_de_pares")
    ap.add_argument("--llm", action="store_true",
                    help="mide tambien al modelo local (tarda y usa la GPU)")
    ap.add_argument("--separacion", action="store_true",
                    help="mide si alguna caracteristica separa aciertos de errores")
    ap.add_argument("--precision", action="store_true",
                    help="mide que porcentaje de lo que junta el emparejador es correcto")
    ap.add_argument("--cuantos-pares", type=int, default=3000,
                    help="pares de cada clase para la medida de precision (3000)")
    ap.add_argument("--modelo", default=MODELO_POR_DEFECTO)
    ap.add_argument("--cuantos", type=int, default=20, help="pares de cada clase")
    a = ap.parse_args(argv)

    filas = fichas()
    positivos = pares_positivos(filas)
    negativos = pares_negativos(filas)
    print(f"catalogo: {len(filas)} productos")
    print(f"  pares ciertos por EAN entre cadenas: {len(positivos)}")
    print(f"  pares de la misma marca con EAN distinto: {len(negativos)}")
    print("  (el primero es el techo alcanzable; el segundo es lo que hay que NO")
    print("   juntar, y el emparejador por nombre los confunde)")

    if a.separacion:
        enlaces_gold = pl.read_parquet(config.GOLD / "enlaces.parquet")
        ls = list(zip(enlaces_gold["i"].to_list(), enlaces_gold["j"].to_list(),
                      enlaces_gold["parecido"].to_list(),
                      enlaces_gold["nivel"].to_list(), strict=True))
        r = separacion(filas, ls)
        print(f"\n  enlaces aceptados con verdad conocida: {r['aciertos']} aciertos, "
              f"{r['errores']} errores")
        print(f"  {'caracteristica':18s} {'aciertos':>9s} {'errores':>9s} "
              f"{'separa':>8s}")
        for clave, fila in r["tabla"].items():
            sep = fila.get("separa")
            print(f"  {clave:18s} {fila['aciertos']:9.3f} {fila['errores']:9.3f} "
                  f"{sep:8.2f}" if sep is not None else
                  f"  {clave:18s} {fila['aciertos']:9.3f} {fila['errores']:9.3f} "
                  f"{'-':>8s}")
        print("  Conclusion: ninguna separa. No hay nada que aprender con estas")
        print("  caracteristicas. Ver el docstring de `separacion`.")
        return 0

    if a.precision:
        r = precision(filas, a.cuantos_pares)
        p, n = r["positivos"], r["negativos"]
        print(f"\n  pares medidos: {p['pares']} ciertos por EAN, {n['pares']} de la misma "
              f"marca con EAN distinto ({r['negativos_confundibles']} confundibles en total)")
        print(f"  {'':22s} {'lo junta':>9s} {'de':>7s} {'%':>7s}")
        for nombre, c in (("mismo producto (EAN)", p), ("dos productos distintos", n)):
            pct = 100 * c["grupo"] / max(c["pares"], 1)
            print(f"  {nombre:22s} {c['grupo']:>9} {c['pares']:>7} {pct:6.1f} %")
        print(f"  precision (de lo que junta, cuanto es correcto): "
              f"{100 * r['precision_grupo']:.1f} %")
        print(f"  cobertura (de los pares ciertos, cuantos junta):  "
              f"{100 * r['cobertura']:.1f} %")
        print(f"  y por la via del enlace (bloqueo + umbral): precision "
              f"{100 * r['precision_enlace']:.1f} %")
        return 0

    if not a.llm:
        return 0
    banco_ = banco(filas, a.cuantos)
    print(f"\nmidiendo al modelo {a.modelo} sobre {len(banco_)} pares...")
    r = evalua_llm(filas, banco_, a.modelo, verboso=True)
    if "error" in r:
        print(f"  no se pudo: {r['error']}")
        return 1
    print(f"\n  aciertos {r['aciertos']}/{r['pares']} "
          f"({100 * r['aciertos'] / max(r['pares'], 1):.0f} %)")
    print(f"  mismo EAN:                {r['positivos']}/{r['positivos_total']}")
    print(f"  misma marca, EAN distinto: {r['negativos']}/{r['negativos_total']}")
    print(f"  en {r['segundos']}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
