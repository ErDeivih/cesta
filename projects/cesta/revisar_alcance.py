"""Ejecucion seca del alcance: que pediria y que excluiria, sobre el catalogo que ya hay.

**No toca la red.** Clasifica lo que ya esta en gold con la politica de `core/datos/alcance.yml`
y dice: por cadena, cuantos productos entran, cuantos salen y por que; y **que ramas se quedan
sin un solo producto de cesta**, que son las candidatas a dejar de pedirse.

    uv run python -m projects.cesta.revisar_alcance
    uv run python -m projects.cesta.revisar_alcance --ramas
    uv run python -m projects.cesta.revisar_alcance --fuente alcampo --ejemplos 12

La parte de "peticiones estimadas frente a realizadas" que pide la aceptacion de T01 (**informe
por fuente de incluidos, excluidos, pendientes, peticiones estimadas y posteriormente
realizadas**) se completa cuando la politica este **dentro** de los colectores: entonces lo
realizado se puede contar de verdad. Aqui se estima lo que se dejaria de pedir, que es la mitad
que se puede medir hoy y la que decide si merece la pena el cambio.

Detalle deliberado: las ramas se leen del primer nivel de la categoria de cada cadena, con el
mismo criterio que el control de cobertura (`core/cobertura._rama`), para que las cuentas de los
dos instrumentos se puedan comparar.
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict

import duckdb

from core import alcance, config
from core.cobertura import _rama


def _catalogo() -> list[tuple[str, str, str]]:
    """(fuente, nombre, categoria) de gold. Sin red: es lo que ya esta guardado."""
    ruta = (config.DATA / "gold" / "grupos.parquet").as_posix()
    con = duckdb.connect()
    con.execute("SET enable_progress_bar=false")
    filas = con.execute(
        f"""SELECT fuente, nombre, coalesce(categoria, '') AS categoria
            FROM read_parquet('{ruta}')""").fetchall()
    return [(f, n or "", c) for f, n, c in filas]


def ramas_sin_cesta(clasificados: dict[tuple[str, str], Counter]) -> list[tuple[str, str, int]]:
    """Las ramas donde **no hay ni un solo producto incluido**: (fuente, rama, excluidos).

    Son las candidatas a dejar de pedirse. Una rama con algo dentro no se toca: se sigue pidiendo
    y se filtra producto a producto, porque una rama mixta casi nunca es basura entera.
    """
    fuera = []
    for (fuente, rama), cuenta in sorted(clasificados.items()):
        if cuenta[alcance.INCLUIDO] == 0 and cuenta[alcance.EXCLUIDO] > 0:
            fuera.append((fuente, rama, cuenta[alcance.EXCLUIDO]))
    return sorted(fuera, key=lambda t: -t[2])


# Palabras que dicen "esto es comida". Sirven solo para vigilar la politica, no para clasificar:
# si un producto **excluido** cae en una categoria de estas, algo se ha torcido.
_COMIDA = ("fresco", "frescos", "fruta", "frutas", "verdura", "verduras", "hortaliza",
           "hortalizas", "carne", "carnes", "carniceria", "pescado", "pescaderia", "marisco",
           "mariscos", "lacteo", "lacteos", "leche", "yogur", "yogures", "queso", "quesos",
           "panaderia", "bolleria", "despensa", "alimentacion", "bebida", "bebidas", "refresco",
           "refrescos", "zumo", "zumos", "cafe", "conserva", "conservas", "pasta", "arroz",
           "legumbre", "legumbres", "aceite", "aceites", "salsa", "salsas", "congelado",
           "congelados", "helado", "helados", "embutido", "embutidos", "charcuteria", "galletas",
           "cereales", "huevos", "pollo", "cerdo", "vacuno", "chocolate", "mermelada", "pan",
           # "frutos" a secas sacaba una vela de frutos rojos: se pide la pareja.
           "frutos secos",
           "azucar", "harina", "especias")

# Palabras que **no** son comida aunque aparezcan en la misma frase o en un folleto de
# alimentacion. Sin esto, el aviso marcaba champu, apositos y colonia.
_NO_COMIDA = ("champu", "jabon", "gel", "desodorante", "tinte", "crema", "serum", "colutorio",
              "detergente", "limpiador", "ambientador", "insecticida", "repelente", "suavizante",
              "lejia", "maquillaje", "solar", "aposito", "apositos", "compresa", "compresas",
              "panal", "panales", "perfume", "colonia", "mascarilla", "cepillo", "moldear", "papel",
              "bolsas", "pilas", "recambio", "fregona", "estropajo", "bayeta", "tampones",
              "complemento", "barritas", "gominolas", "colageno", "spray", "higiene",
              "auditiva", "aromatica", "vela", "velas")

# Palabras de un folleto o de una campana: dentro de ellos cabe de todo, asi que no
# sirven como señal de que algo sea comida.
_DE_FOLLETO = frozenset({"folleto", "folletos", "promocion", "promociones", "oferta",
                         "ofertas", "campana", "campanas", "stock", "fuera", "novedades",
                         "recomendados", "destacados", "oportunidades"})


def alimentos_excluidos(filas: list[tuple[str, str, str]]) -> list[tuple[str, str, str]]:
    """Productos **excluidos** que caen en una categoria de comida: tendria que estar vacio.

    Lo pidio el dueno antes de activar ninguna exclusion: *"reducir catalogo no debe eliminar
    alimentos o consumibles validos"*. Si sale algo aqui, la politica se ha pasado de larga y se
    ve **con el nombre y la regla delante**, no como un porcentaje.
    """
    fuera = []
    for fuente, nombre, categoria in filas:
        d = alcance.clasificar_alcance(nombre, categoria)
        if d.estado != alcance.EXCLUIDO:
            continue
        # **Por palabras enteras, no por trozos.** Este aviso heredo el defecto que se acaba de
        # curar en la politica: con `p in plano`, "pan" casa con "pantalon" y "leche" con "leche
        # solar", y la lista traia un delineador de ojos y una crema solar como si fueran comida.
        # Una lista asi no sirve para decidir si la politica esta bien.
        # **Dos señales: comida en el nombre y pasillo de comida.** El aviso existe para decir
        # "la politica esta excluyendo comida", y eso es justo lo que comprueba: que el nombre del
        # producto hable de comida **y** que su pasillo sea de comida. Con una sola señal salian
        # sesenta cosas que no lo son -- un batido suplemento con sabor a chocolate, un aceite
        # para el pelo, caramelos de la tos -- y perseguirlas una a una era la via sin salida de
        # las seis rondas anteriores. Seis palabras de folleto se filtran: dentro de un folleto
        # cabe de todo.
        del_nombre = [p for p in alcance._palabras(nombre or "") if p not in _DE_FOLLETO]
        del_pasillo = [p for p in alcance._palabras(categoria or "") if p not in _DE_FOLLETO]
        if any(p in del_nombre for p in _NO_COMIDA):
            continue
        # Y se dice **que palabra** lo disparo: sin eso, ajustar es adivinar.
        disparo = next((p for p in _COMIDA if p in del_nombre), None)
        if disparo and any(p in del_pasillo for p in _COMIDA):
            termino = d.evidencias.get("termino")
            fuera.append((fuente, nombre,
                          f"{d.regla_id}" + (f' por "{termino}"' if termino else "")
                          + f' :: disparo "{disparo}" :: {categoria[:44]}'))
    return fuera


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--fuente", help="mirar solo una cadena")
    ap.add_argument("--ramas", action="store_true",
                    help="ensenar las ramas que se quedan sin un solo producto de cesta")
    ap.add_argument("--minimo", type=int, default=1,
                    help="productos excluidos minimos para listar una rama")
    ap.add_argument("--ejemplos", type=int, default=6, help="ejemplos por cadena y estado")
    ap.add_argument("--seguridad", action="store_true",
                    help="solo la comprobacion de que no se excluye comida")
    a = ap.parse_args()

    try:
        filas = _catalogo()
    except Exception as exc:  # noqa: BLE001
        print(f"No hay catalogo que mirar ({type(exc).__name__}). Ejecuta el pipeline antes.")
        return 0
    if a.fuente:
        filas = [f for f in filas if f[0] == a.fuente]
    if not filas:
        print("No hay productos que clasificar con ese filtro.")
        return 0

    print(f"Politica version {alcance.version()}, {len(filas):,} productos clasificados "
          f"(sin tocar la red)\n".replace(",", "."))

    por_fuente: dict[str, Counter] = defaultdict(Counter)
    por_rama: dict[tuple[str, str], Counter] = defaultdict(Counter)
    ejemplos: dict[tuple[str, str], list[str]] = defaultdict(list)
    for fuente, nombre, categoria in filas:
        d = alcance.clasificar_alcance(nombre, categoria)
        por_fuente[fuente][d.estado] += 1
        por_rama[(fuente, _rama(categoria, fuente))][d.estado] += 1
        if len(ejemplos[(fuente, d.estado)]) < a.ejemplos:
            # **La regla y la palabra que decidieron**, no solo el resultado: sin esto, corregir
            # un falso positivo es adivinar (se aprendio con seis productos excluidos por una
            # palabra del titulo que resultaba ser de comida).
            termino = d.evidencias.get("termino")
            ejemplos[(fuente, d.estado)].append(
                f"{nombre[:50]}  [{categoria[:38]}]  <- {d.regla_id}"
                + (f" por \"{termino}\"" if termino else ""))

    print(f"  {'cadena':<11}{'entran':>10}{'salen':>10}{'a revisar':>11}{'% fuera':>10}")
    total = Counter()
    for fuente in sorted(por_fuente):
        c = por_fuente[fuente]
        n = sum(c.values())
        fuera = c[alcance.EXCLUIDO]
        total.update(c)
        print(f"  {fuente:<11}{c[alcance.INCLUIDO]:>10,}{fuera:>10,}{c[alcance.REVISAR]:>11,}"
              f"{100 * fuera / n:>9.1f}%".replace(",", "."))
    n = sum(total.values())
    print(f"  {'TOTAL':<11}{total[alcance.INCLUIDO]:>10,}{total[alcance.EXCLUIDO]:>10,}"
          f"{total[alcance.REVISAR]:>11,}{100 * total[alcance.EXCLUIDO] / n:>9.1f}%"
          .replace(",", "."))

    sin_cesta = [t for t in ramas_sin_cesta(por_rama) if t[2] >= a.minimo]
    if sin_cesta:
        print(f"\n  ramas sin un solo producto de cesta ({len(sin_cesta)}): candidatas a dejar "
              f"de pedirse")
        for fuente, rama, cuantos in sin_cesta[:25]:
            print(f"    {cuantos:>6,}  {fuente:<11} {rama[:60]}".replace(",", "."))
        if len(sin_cesta) > 25:
            print(f"    ... y {len(sin_cesta) - 25} mas")
        print("    (las peticiones que se ahorran se contaran cuando la politica este dentro de "
              "los colectores: es la parte de 'realizadas' de la aceptacion de T01)")

    seguridad = alimentos_excluidos(filas)
    print()
    if seguridad:
        print(f"  **AVISO: {len(seguridad)} alimentos o consumibles validos excluidos** "
              f"(la politica se ha pasado):")
        for fuente, nombre, detalle in seguridad[:12]:
            print(f"    {fuente:<11} {nombre[:44]}  {detalle}")
        print("    Reducir catalogo no puede llevarse comida: revisa la politica antes de seguir.")
    else:
        print("  seguridad: ningun producto de categoria de comida queda excluido")

    if a.ramas:
        return 0

    print()
    for fuente in sorted(por_fuente):
        for estado in (alcance.EXCLUIDO, alcance.REVISAR):
            lista = ejemplos.get((fuente, estado), [])
            if not lista:
                continue
            print(f"  {fuente} / {estado} (ejemplos):")
            for ejemplo in lista:
                print(f"    {ejemplo}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
