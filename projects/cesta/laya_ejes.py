"""Que diria Laya de nuestros ejes de atributo, medido contra lo que ya sabemos.

Esto es el banco de pruebas de `docs/LAYA.md`, y **no toca la cadena de las 06:00**:
lee `data/gold/grupos.parquet`, no escribe en gold, y solo se ejecuta a mano.

## Por que existe

`core/atributos.py` son listas de subcadenas escritas a mano: 12 ejes, 28 valores,
71 patrones. Funcionan y ya dieron un fallo clasico (`desnatad` casando dentro de
`semidesnatad`), pero cada eje nuevo es trabajo manual y **fuera de esos 12 ejes el
catalogo no dice nada**. Un modelo de decision como Laya podria declarar ejes que
hoy no declaramos.

## El banco es gratis, y esa es la gracia

Las listas a mano son la verdad de referencia: donde dicen un valor, sabemos la
respuesta. Asi que el experimento no necesita etiquetar nada nuevo -- necesita
comprobar si el modelo reproduce lo que ya sabemos. **Si no reproduce lo que ya
sabemos, no se usa para lo que no sabemos.**

Pero el banco tiene una trampa que ya esta medida (`docs/JEV-IMPLANTACION.md` §2):
las listas son subcadenas sueltas aplicadas a todo el catalogo, y hay declaraciones
**fuera de sitio** (`vino blanco` declarando `integral=blanco`, `yogur natural`
declarando `cafeina=natural`). Por eso el informe separa tres cosas, y la tercera se
audita a mano en vez de contarse como fallo del modelo:

    donde la lista declara   -> acuerdo, abstencion, o valor distinto
    donde la lista calla     -> el modelo declara igualmente: se enseña, no se juzga

## Como se ejecuta

El paquete **no entra en las dependencias del proyecto** a proposito: la cadena
diaria no puede depender de torch, y `tests/test_sin_terceros.py` vigila eso. Se
instala en un entorno aparte y se llama a este modulo con ese interprete:

    uv venv "$env:TEMP\\laya-prueba\\venv" --python 3.12
    uv pip install --python "$env:TEMP\\laya-prueba\\venv\\Scripts\\python.exe" `
        laya duckdb tzdata
    $env:USE_TF='0'   # sin esto, transformers busca TensorFlow y puede colgarse
    $env:HF_HOME="$env:TEMP\\laya-prueba\\hf"     # los pesos, fuera del proyecto
    & "$env:TEMP\\laya-prueba\\venv\\Scripts\\python.exe" -m projects.cesta.laya_ejes

    uv run python -m projects.cesta.laya_ejes --sin-modelo     # solo el banco

Los tres paquetes son el minimo medido: `laya` trae torch y transformers, `duckdb`
lee el gold y `tzdata` es lo que necesita `core/config.py` en un entorno sin la zona
horaria del sistema. **Nada de esto entra en `pyproject.toml`.**

## Lo que hay que mirar

1. **Acuerdo sobre lo declarado.** La barra de `docs/JEV-IMPLANTACION.md` §3 pide
   >= 97 %.
2. **Abstenciones.** Cuantas veces dice "no lo dice" donde la lista si sabe. Para
   una guarda es inofensivo (el que calla no bloquea); para sustituir la lista, es
   un fallo.
3. **Inventos**, auditados a mano: puede estar corrigiendo nuestras listas.
4. **La ruta del Router.** El enrutador decide por guion y tildes: un nombre de
   producto en castellano sin tildes se va al checkpoint ingles, que es el que peor
   lee el castellano. Por eso aqui se fuerza `model="multilingual"` y se cuenta
   aparte lo que el Router habria elegido solo.
"""
from __future__ import annotations

import argparse
import json
import random
import time
from collections import Counter, defaultdict

import duckdb

from core import config

# `_plano` es privada de `core.atributos` y se trae a proposito: comparar patrones
# quitando tildes y mayusculas **tiene que ser la misma operacion** que la que hace la
# lista, o la medida de la copia diria una cosa y la lista otra.
from core.atributos import EJES, _plano, valores

# La opcion de silencio. El nombre es el del proyecto: **el que calla no bloquea**,
# asi que el modelo tiene que poder decir que el nombre no declara nada.
SILENCIO = "no lo dice"

# Como se le explica cada valor al modelo. **A mano y a proposito**: son frases
# corrientes, no nuestros patrones. Copiar los patrones de `core/atributos.py` aqui
# haria el experimento circular -- estariamos midiendo si el modelo sabe leer
# nuestras subcadenas, que es justo lo que no hace falta comprobar.
EXPLICACION: dict[tuple[str, str], str] = {
    ("grasa", "entera"): "con toda su grasa, sin quitarsela",
    ("grasa", "semidesnatada"): "a medio camino entre la entera y la que no tiene grasa",
    ("grasa", "sin grasa"): "se le ha quitado la grasa",
    ("aceite", "virgen extra"): "aceite de oliva de la calidad mas alta, sin refinar",
    ("aceite", "virgen"): "aceite de oliva sin refinar, de calidad algo menor",
    ("aceite", "orujo"): "aceite sacado del residuo de la aceituna, ya refinado",
    ("aceite", "oliva suave"): "aceite de oliva refinado, de sabor suave",
    ("gas", "con gas"): "bebida con burbujas",
    ("gas", "sin gas"): "bebida sin burbujas",
    ("alcohol", "con alcohol"): "bebida alcoholica",
    ("alcohol", "sin alcohol"): "cerveza o similar sin alcohol",
    ("cafeina", "descafeinado"): "cafe al que se le ha quitado la cafeina",
    ("cafeina", "natural"): "cafe con su cafeina, o yogur sin sabores anadidos",
    ("azucar", "con azucar"): "lleva azucar anadido",
    ("azucar", "sin azucar"): "no lleva azucar",
    ("integral", "integral"): "hecho con el grano entero, sin refinar",
    ("integral", "blanco"): "hecho con harina refinada, o vino de uva sin piel",
    ("lactosa", "sin lactosa"): "le ha quitado la lactosa de la leche",
    ("gluten", "sin gluten"): "no lleva gluten",
    ("formato", "en polvo"): "viene en polvo para disolver",
    ("formato", "liquido"): "viene ya liquido",
    ("cafe", "molido"): "cafe molido para hacer en cafetera",
    ("cafe", "grano"): "cafe en grano entero, sin moler",
    ("cafe", "capsula"): "cafe en capsulas o monodosis",
    ("cafe", "soluble"): "cafe instantaneo, se disuelve en agua",
    ("leche", "leche de vaca"): "el producto es leche de vaca",
    ("leche", "bebida vegetal"): "no es leche de vaca, es una bebida hecha de avena, "
                                 "soja, almendra, arroz u otra planta",
}


def _explicacion(eje: str, valor: str) -> str:
    return EXPLICACION.get((eje, valor), valor)


def copia_del_patron(eje: str, valor: str) -> list[str]:
    """Los patrones de la lista que aparecen **dentro** de la explicacion.

    Esto mide si el experimento se esta haciendo trampa a si mismo. Si para
    `formato=en polvo` el enunciado dice "viene en polvo", el modelo no necesita leer
    el castellano: le basta con encontrar la subcadena que la lista ya busca, y el
    acuerdo que salga de ahi **no prueba nada** sobre un eje nuevo.

    No se prohibe: se **mide y se dice**. Las explicaciones estan escritas como las
    escribiria una persona -- que es como las escribiremos el dia que se implanten --,
    asi que el experimento es **generoso** con el modelo, y el informe tiene que
    enseñar cuanto, y cuanto del acierto viene de ahi.
    """
    plano = _plano(EXPLICACION[(eje, valor)])
    return [_plano(p) for p in dict(EJES[eje])[valor] if _plano(p) in plano]


def valores_que_copian_el_patron() -> list[tuple[str, str, list[str]]]:
    """Los (eje, valor) cuyo enunciado lleva dentro un patron de la lista."""
    fuera = []
    for eje, opciones in EJES.items():
        for valor, _patrones in opciones:
            copiados = copia_del_patron(eje, valor)
            if copiados:
                fuera.append((eje, valor, copiados))
    return fuera


def preguntas_de(nombre: str) -> dict:
    """Las 12 preguntas del mismo producto, en una sola peticion.

    Mandar 100 nombres en un `state` es el modo de fallo que la documentacion de
    estos modelos describe: para la pregunta de un producto, los otros 99 son texto
    que no viene a cuento y la precision cae. Un producto por peticion.
    """
    preguntas = {}
    for eje, opciones in EJES.items():
        criterios = {valor: _explicacion(eje, valor) for valor, _patrones in opciones}
        criterios[SILENCIO] = "el nombre del producto no lo dice"
        preguntas[eje] = {
            "type": "choice",
            "instructions": (
                f"Que {eje} declara el nombre de este producto de supermercado, "
                f"en castellano? Elige la opcion que el nombre afirma.",
            ),
            "criteria": criterios,
        }
    return preguntas


def banco(por_valor: int, semilla: int) -> tuple[list[str], dict[str, dict[str, str]]]:
    """Los nombres a preguntar y lo que dicen las listas a mano de cada uno.

    `por_valor` nombres por **(eje, valor)**, elegidos de forma determinista: se
    ordenan y se barajan con la semilla, para que dos ejecuciones pregunten lo mismo
    y la cifra se pueda comparar. Se pregunta por el valor declarado, no al azar: un
    nombre del que la lista no sabe nada no prueba nada.
    """
    con = duckdb.connect()
    filas = con.execute(
        f"SELECT DISTINCT nombre FROM read_parquet('{(config.GOLD / 'grupos.parquet').as_posix()}') "
        "WHERE nombre IS NOT NULL AND length(nombre) > 3").fetchall()

    verdad: dict[str, dict[str, str]] = {}
    for (nombre,) in filas:
        verdad[nombre] = valores(nombre)

    por_eje_valor: dict[tuple[str, str], list[str]] = defaultdict(list)
    for nombre, dicho in verdad.items():
        for eje, valor in dicho.items():
            por_eje_valor[(eje, valor)].append(nombre)

    azar = random.Random(semilla)
    elegidos: set[str] = set()
    for clave in sorted(por_eje_valor):
        nombres = sorted(por_eje_valor[clave])
        azar.shuffle(nombres)
        elegidos.update(nombres[:por_valor])
    return sorted(elegidos), verdad


def _respuesta(res: dict, eje: str) -> tuple[str | None, float | None]:
    """El valor elegido y su probabilidad, sin fiarse de la forma de la respuesta.

    Laya devuelve `{"choice": ..., "probabilities": {...}, "confidence": ...}`; la
    confianza es la de la pregunta entera y `answer_confidence` la de la opcion. Se
    recogen las dos porque la documentacion avisa de que el checkpoint que viene
    **sin recalibrar** da confianzas que no se pueden tomar al pie de la letra.
    """
    dicho = (res.get("answers") or {}).get(eje) or {}
    elegido = dicho.get("choice")
    probabilidad = (dicho.get("probabilities") or {}).get(elegido)
    return elegido, probabilidad


def mide(nombres: list[str], verdad: dict[str, dict[str, str]], modelo: str) -> dict:
    """Una peticion por nombre, y la comparacion contra las listas a mano."""
    import laya  # a proposito: el paquete vive fuera del proyecto, no es dependencia

    t0 = time.perf_counter()
    router = laya.Router()
    print(f"  cargando el checkpoint: {time.perf_counter() - t0:.0f} s", flush=True)

    cuenta: Counter = Counter()
    por_eje: dict[str, Counter] = defaultdict(Counter)
    # El mismo recuento, pero por **(eje, valor de la verdad)**: es lo que permite
    # decir cuanto del acierto viene de un enunciado que copia el patron de la lista.
    por_par: dict[tuple[str, str], Counter] = defaultdict(Counter)
    invenciones: list[str] = []
    desacuerdos: list[str] = []
    pares: list[str] = []
    rutas: Counter = Counter()
    segundos = 0.0

    for i, nombre in enumerate(nombres, 1):
        preguntas = preguntas_de(nombre)
        t1 = time.perf_counter()
        # `model="multilingual"` **forzado**: el enrutador manda el castellano sin
        # tildes al checkpoint ingles, y el ingles es el que peor lo lee.
        res = router.predict(nombre, preguntas, model=modelo)
        segundos += time.perf_counter() - t1
        rutas[res["routing"]["model"]] += 1

        dicho = verdad[nombre]
        for eje in EJES:
            elegido, _p = _respuesta(res, eje)
            esperado = dicho.get(eje)
            if esperado is None:
                if elegido and elegido != SILENCIO:
                    invenciones.append(f"{nombre} -> {eje}={elegido}")
                cuenta["callaba_el_modelo_tambien"] += 1
                continue
            pares.append(f"{nombre} :: {eje}: {esperado} -> {elegido or '(nada)'}")
            if elegido == esperado:
                cuenta["acuerdo"] += 1
                por_eje[eje]["acuerdo"] += 1
                por_par[(eje, esperado)]["acuerdo"] += 1
            elif elegido == SILENCIO:
                cuenta["abstencion"] += 1
                por_eje[eje]["abstencion"] += 1
                por_par[(eje, esperado)]["abstencion"] += 1
                desacuerdos.append(f"{nombre} :: {eje}: la lista dice {esperado}, "
                                   f"el modelo calla")
            else:
                cuenta["distinto"] += 1
                por_eje[eje]["distinto"] += 1
                por_eje[eje][f"dice:{elegido}"] += 1
                por_par[(eje, esperado)]["distinto"] += 1
                desacuerdos.append(f"{nombre} :: {eje}: la lista dice {esperado}, "
                                   f"el modelo dice {elegido}")
        if i % 25 == 0:
            print(f"  {i}/{len(nombres)}  ({segundos / i:.2f} s por peticion)",
                  flush=True)

    declarado = cuenta["acuerdo"] + cuenta["abstencion"] + cuenta["distinto"]
    return {
        "nombres": len(nombres),
        "declarado": declarado,
        "acuerdo": cuenta["acuerdo"],
        "abstencion": cuenta["abstencion"],
        "distinto": cuenta["distinto"],
        "acuerdo_pct": 100.0 * cuenta["acuerdo"] / declarado if declarado else 0.0,
        "callaba_el_modelo_tambien": cuenta["callaba_el_modelo_tambien"],
        "invenciones": len(invenciones),
        "por_eje": {eje: dict(c) for eje, c in sorted(por_eje.items())},
        # Los listados enteros, no un resumen: un desacuerdo hay que poder auditar uno
        # a uno sin volver a correr el modelo.
        "desacuerdos": desacuerdos,
        "todas_las_invenciones": invenciones,
        "ejemplos_de_invencion": invenciones[:40],
        "pares": pares,
        "generosidad": generosidad(por_par),
        "rutas": dict(rutas),
        "segundos_por_peticion": segundos / max(len(nombres), 1),
    }


def generosidad(por_par: dict[tuple[str, str], Counter]) -> dict:
    """Cuanto del acierto viene de un enunciado que ya lleva el patron dentro.

    Se parte el banco en dos: los valores cuyo enunciado **copia** un patron de la
    lista -- donde el modelo puede acertar sin leer nada, solo encontrando la
    subcadena -- y los que no. Si el acierto se concentra en los primeros, la cifra
    del informe no mide lo que dice medir, y hay que decirlo.
    """
    copiados = {(eje, valor) for eje, valor, _p in valores_que_copian_el_patron()}
    cuenta: Counter = Counter()
    for (eje, valor), c in por_par.items():
        clave = "copia" if (eje, valor) in copiados else "limpio"
        for resultado in ("acuerdo", "abstencion", "distinto"):
            cuenta[f"{clave}_{resultado}"] += c.get(resultado, 0)
    fuera = {}
    for clave in ("copia", "limpio"):
        total = sum(cuenta[f"{clave}_{r}"] for r in ("acuerdo", "abstencion", "distinto"))
        fuera[clave] = {
            "pares": total,
            "acuerdo": cuenta[f"{clave}_acuerdo"],
            "acuerdo_pct": 100.0 * cuenta[f"{clave}_acuerdo"] / total if total else 0.0,
        }
    return fuera


def auditoria(nombres: list[str], verdad: dict[str, dict[str, str]]) -> list[dict]:
    """Los casos que la auditoria del 17 de septiembre encontro mal en nuestras listas.

    Son declaraciones **fuera de sitio**: la subcadena dispara en un producto que no
    tiene nada que ver. Aqui no se cuenta acuerdo: se enseña que dice el modelo, para
    ver si los corrige. Es la condicion 2 de la barra de `docs/JEV-IMPLANTACION.md`.
    """
    casos = [
        ("yogur natural", "cafeina", "natural"),
        ("vino blanco", "integral", "blanco"),
        ("orujo de hierbas", "aceite", "orujo"),
    ]
    fuera = []
    for aguja, eje, valor in casos:
        # Los nombres reales del catalogo que disparan esa declaracion.
        reales = [n for n, dicho in verdad.items()
                  if dicho.get(eje) == valor and aguja.lower() in n.lower()]
        if reales:
            fuera.append({"caso": aguja, "eje": eje, "valor": valor,
                          "en_el_catalogo": len(reales), "ejemplo": sorted(reales)[0]})
    return fuera


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="laya_ejes", description=__doc__.split("\n")[0])
    ap.add_argument("--por-valor", type=int, default=8,
                    help="nombres por (eje, valor) que declara la lista a mano")
    ap.add_argument("--semilla", type=int, default=23)
    ap.add_argument("--modelo", default="multilingual",
                    help="checkpoint de Laya: english, multilingual o typed-decisions")
    ap.add_argument("--sin-modelo", action="store_true",
                    help="solo enseñar el banco, sin instalar ni cargar nada")
    ap.add_argument("--json", default="", help="escribir el resultado en este fichero")
    a = ap.parse_args(argv)

    nombres, verdad = banco(a.por_valor, a.semilla)
    pares = sum(len(verdad[n]) for n in nombres)
    print(f"  nombres en el banco                     {len(nombres):>7,}")
    print(f"  (producto, eje) con verdad declarada    {pares:>7,}")
    print(f"  ejes cubiertos                          {len(EJES):>7,}")

    if a.sin_modelo:
        for clave, cuantos in sorted(
                Counter((e, v) for n in nombres for e, v in verdad[n].items()).items()):
            print(f"    {clave[0]:<10} {clave[1]:<14} {cuantos:>5,}")
        return 0

    try:
        r = mide(nombres, verdad, a.modelo)
    except ImportError as e:  # el paquete vive fuera del proyecto, a proposito
        print(f"  no lo se: falta el paquete de Laya ({e}). Mira la receta del docstring,")
        print("  o corre con --sin-modelo para ver solo el banco.")
        return 2

    print(f"\n  acuerdo sobre lo declarado   {r['acuerdo']:>6,}  "
          f"({r['acuerdo_pct']:.1f} %  -- la barra pide 97 %)")
    print(f"  se abstiene (dice que calla) {r['abstencion']:>6,}")
    print(f"  declara otro valor           {r['distinto']:>6,}")
    print(f"  la lista callaba y el modelo tambien "
          f"{r['callaba_el_modelo_tambien']:>6,}")
    print(f"  la lista callaba y el modelo declara  {r['invenciones']:>6,}"
          "   (se auditan a mano)")
    print(f"  ruta elegida por el Router   {r['rutas']}")
    print(f"  segundos por peticion        {r['segundos_por_peticion']:.2f} s (CPU)")

    g = r["generosidad"]
    copian = valores_que_copian_el_patron()
    print(f"\n  generosidad del enunciado: {len(copian)} de "
          f"{sum(len(o) for o in EJES.values())} valores llevan dentro un patron de "
          f"la lista")
    for clave, nombre in (("copia", "donde el enunciado copia el patron"),
                          ("limpio", "donde el enunciado no copia nada")):
        print(f"    {nombre:<38} {g[clave]['pares']:>5} pares, "
              f"{g[clave]['acuerdo_pct']:>5.1f} % de acuerdo")
    for eje, valor, copiados in copian:
        print(f"      {eje}={valor:<16} copia {copiados}")

    print("\n  por eje (acuerdo / abstencion / distinto):")
    for eje, cuenta in r["por_eje"].items():
        print(f"    {eje:<10} {cuenta.get('acuerdo', 0):>5} /"
              f" {cuenta.get('abstencion', 0):>5} / {cuenta.get('distinto', 0):>5}")

    fuera = auditoria(nombres, verdad)
    if fuera:
        print("\n  las declaraciones fuera de sitio que la auditoria ya encontro:")
        for c in fuera:
            print(f"    {c['caso']:<18} declaraba {c['eje']}={c['valor']}"
                  f"   ({c['en_el_catalogo']} fichas, ej. {c['ejemplo'][:40]})")

    if a.json:
        with open(a.json, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"modelo": a.modelo, "por_valor": a.por_valor, **r}, f,
                      ensure_ascii=False, indent=2)
        print(f"\n  escrito {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
