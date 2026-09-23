"""Los ejes contradictorios del catalogo, contados. Es el medidor del encargo.

La barra de aceptacion pide **cero grupos con eje contradictorio** y **menos de 30
grupos de 11+ productos**. Esto mide las dos cosas sobre el gold de hoy, y sirve de
trinquete: `projects/cesta/verificar_docs` no lo mira, pero las pruebas si.

    uv run python -m projects.cesta.ejes
    uv run python -m projects.cesta.ejes --peores 5
"""
from __future__ import annotations

import argparse
from collections import Counter

import duckdb

from core import config
from core.atributos import contradicciones


def _filas() -> list[tuple]:
    """`grupo_id`, `nombre`, `fuente`, `precio_unidad_cent` y `unidades_pack`.

    `fuente` entra aqui por la **sexta condicion de la barra**: los enlaces son
    1-a-1 **por par de cadenas**, asi que un grupo correcto no puede tener dos
    productos de la misma cadena. Se mide con los datos que ya se estaban leyendo,
    asi que no cuesta ninguna consulta mas.
    """
    con = duckdb.connect()
    return con.execute(
        f"SELECT grupo_id, nombre, fuente, ean, precio_unidad_cent, unidades_pack "
        f"FROM read_parquet('{(config.GOLD / 'grupos.parquet').as_posix()}') "
        f"WHERE grupo_id IS NOT NULL AND precio_unidad_cent > 0").fetchall()


def resumen(peores: int = 0) -> dict:
    """Los grupos con eje contradictorio, el pack, y el reparto por tamaño.

    Dos dimensiones distintas, y hay que verlas por separado porque el arreglo no
    es el mismo:

    - **Los ejes**: el grupo mezcla *entera* con *desnatada*. Ahi hay una
      contradiccion, y lo que corta es lo que el nombre declara.
    - **El pack**: el grupo mezcla una botella de 1,5 l con un pack de 6x1,5 l. Ahi
      **nadie se contradice** -- todas son agua de 1,5 l --, y el precio por litro
      se puede comparar perfectamente. El problema es otro: `unidades_pack`, o sea
      que "donde compro agua" acabe recomendando nueve litros frente a uno y medio.
    """
    por_grupo: dict[int, list[str]] = {}
    tamano: Counter = Counter()
    packs: dict[int, set[int]] = {}
    cadenas: dict[int, list[str]] = {}
    eans: dict[int, list[str | None]] = {}
    for grupo_id, nombre, fuente, ean, _precio, unidades in _filas():
        gid = int(grupo_id)
        por_grupo.setdefault(gid, []).append(nombre or "")
        tamano[gid] += 1
        cadenas.setdefault(gid, []).append(fuente)
        eans.setdefault(gid, []).append(ean)
        # Un nulo se lee como 1: una botella suelta no declara pack, y tratar el
        # silencio como "1" es lo unico que tiene sentido aqui (al contrario que en
        # los ejes, donde el silencio no bloquea). Si no, cada botella suelta
        # contaria como un tamaño distinto.
        packs.setdefault(gid, set()).add(int(unidades or 1))

    contradictorios = {}
    for grupo_id, nombres in por_grupo.items():
        ejes = contradicciones(nombres)
        if ejes:
            contradictorios[grupo_id] = ejes

    grandes = {g: n for g, n in tamano.items() if n >= 11}
    grandes_malos = {g: e for g, e in contradictorios.items() if tamano[g] >= 11}
    mezclan_pack = {g: v for g, v in packs.items() if len(v) > 1}
    # La invariante del reparto: mas productos que cadenas distintas significa que
    # alguna cadena esta repetida. Es la condicion que mas limpio el catalogo -- los
    # 74 de 74 grupos grandes la incumplian -- y no necesita umbral ninguno.
    #
    # **Pero el duplicado legitimo no es una infraccion**: dos fichas de la misma
    # cadena con el **mismo EAN** son el mismo producto listado dos veces, y la
    # guarda de `agrupar_enlaces` las admite a proposito. Asi que se cuentan las dos
    # cosas por separado, y la barra pide **cero sin EAN**.
    def _sin_ean(gid: int) -> bool:
        vistas: dict[str, set[str]] = {}
        for cadena, ean in zip(cadenas[gid], eans[gid], strict=True):
            vistas.setdefault(cadena, set()).add(ean or f"?{cadena}")
        return any(len(codigos) > 1 for codigos in vistas.values())

    repetida = {g: n for g, n in tamano.items() if len(set(cadenas[g])) < n}
    repetida_sin_ean = {g: n for g, n in repetida.items() if _sin_ean(g)}

    return {
        "grupos": len(por_grupo),
        "grupos_con_eje_contradictorio": len(contradictorios),
        "grupos_de_11_o_mas": len(grandes),
        "de_esos_con_eje_contradictorio": len(grandes_malos),
        "grupos_que_mezclan_pack": len(mezclan_pack),
        "de_esos_de_11_o_mas": sum(1 for g in mezclan_pack if tamano[g] >= 11),
        "grupos_con_cadena_repetida": len(repetida),
        "grupos_con_cadena_repetida_sin_ean": len(repetida_sin_ean),
        "repetida_sin_ean_de_11_o_mas": sum(
            1 for g in repetida_sin_ean if tamano[g] >= 11),
        "peores": sorted(
            ((tamano[g], g, e) for g, e in contradictorios.items()),
            reverse=True)[:peores] if peores else [],
        "peores_pack": sorted(
            ((tamano[g], g, sorted(v)) for g, v in mezclan_pack.items()),
            reverse=True)[:peores] if peores else [],
        "peores_repetida": sorted(
            ((tamano[g], g, len(set(cadenas[g]))) for g in repetida_sin_ean),
            reverse=True)[:peores] if peores else [],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="ejes")
    ap.add_argument("--peores", type=int, default=0,
                    help="cuantos grupos enseñar, por tamaño")
    a = ap.parse_args(argv)

    r = resumen(peores=a.peores)
    print(f"  grupos                                  {r['grupos']:>7,}")
    print(f"  con algun eje contradictorio            "
          f"{r['grupos_con_eje_contradictorio']:>7,}   (la barra pide 0)")
    print(f"  grupos de 11 o mas productos            "
          f"{r['grupos_de_11_o_mas']:>7,}   (la barra pide < 30)")
    print(f"  de esos, con eje contradictorio         "
          f"{r['de_esos_con_eje_contradictorio']:>7,}")
    print(f"  que mezclan un pack con sueltas         "
          f"{r['grupos_que_mezclan_pack']:>7,}")
    print(f"  de esos, de 11 o mas                    {r['de_esos_de_11_o_mas']:>7,}")
    print(f"  con la misma cadena repetida            "
          f"{r['grupos_con_cadena_repetida']:>7,}   (incluye el duplicado con EAN)")
    print(f"  de esa, SIN compartir EAN               "
          f"{r['grupos_con_cadena_repetida_sin_ean']:>7,}   (la barra pide 0)")
    print(f"  de esos, de 11 o mas                    "
          f"{r['repetida_sin_ean_de_11_o_mas']:>7,}")
    for n, grupo_id, ejes in r["peores"]:
        print(f"    eje:  grupo {grupo_id} ({n} productos): {ejes}")
    for n, grupo_id, tamanos in r["peores_pack"]:
        print(f"    pack: grupo {grupo_id} ({n} productos): unidades {tamanos}")
    for n, grupo_id, cuantas in r["peores_repetida"]:
        print(f"    cadena repetida: grupo {grupo_id} ({n} productos, "
              f"{cuantas} cadenas distintas)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
