"""Publicacion en sombra de la identidad nueva: propone, compara e informa. No toca nada.

    uv run python -m projects.cesta.identidad_sombra

Lee el catalogo de gold, propone grupos **exactos** por GTIN valido, cuenta aparte los **probables**, y
compara con los grupos del emparejador que esta en uso. El informe se guarda en
`data/identidad-sombra/` y **no se modifica ni un dato**: activar esto es una decision posterior y con
la medida delante.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

import duckdb
import polars as pl

from core import alcance, identidad

RAIZ = Path(__file__).resolve().parents[2]
SOMBRA = RAIZ / "data" / "identidad-sombra"


def catalogo() -> list[identidad.Producto]:
    """Los productos de gold como fichas del motor, con la familia del alcance."""
    ruta = (RAIZ / "data" / "gold" / "grupos.parquet").as_posix()
    con = duckdb.connect()
    con.execute("SET enable_progress_bar=false")
    columnas = {c[0] for c in con.execute(
        f"describe select * from read_parquet('{ruta}')").fetchall()}
    campos = ["fuente", "coalesce(nombre, '') as nombre", "coalesce(categoria, '') as categoria"]
    campos.append("ean" if "ean" in columnas else "null as ean")
    campos.append("marca" if "marca" in columnas else "null as marca")
    campos.append("id_fuente" if "id_fuente" in columnas else "nombre as id_fuente")
    filas = con.execute(f"select {', '.join(campos)} from read_parquet('{ruta}')").fetchall()
    salida = []
    for fuente, nombre, categoria, ean, marca, id_fuente in filas:
        decision = alcance.clasificar_alcance(nombre, categoria)
        salida.append(identidad.Producto(
            fuente=fuente, id_fuente=str(id_fuente), nombre=nombre, marca=marca,
            gtin=ean, familia=decision.familia_id or "desconocida"))
    return salida


def componentes_actuales() -> dict[int, set[int]]:
    """Los grupos del emparejador en uso, calculados como componentes conexas de sus aristas.

    `enlaces.parquet` trae `(i, j, parecido, nivel)`: son aristas entre **posiciones de fila** de
    `grupos.parquet`, no filas con identificador de grupo. Se agrupan con union-find, que para 22.750
    aristas es instantaneo y no necesita recursion.
    """
    ruta = RAIZ / "data" / "gold" / "enlaces.parquet"
    if not ruta.exists():
        return {}
    marco = pl.read_parquet(ruta, columns=["i", "j"])
    padre: dict[int, int] = {}

    def raiz(x: int) -> int:
        padre.setdefault(x, x)
        while padre[x] != x:
            padre[x] = padre[padre[x]]
            x = padre[x]
        return x

    for i, j in marco.iter_rows():
        ri, rj = raiz(int(i)), raiz(int(j))
        if ri != rj:
            padre[rj] = ri

    componentes: dict[int, set[int]] = {}
    for nodo in list(padre):
        componentes.setdefault(raiz(nodo), set()).add(nodo)
    return {k: v for k, v in componentes.items() if len(v) > 1}


def comparar_con_el_actual(productos: list[identidad.Producto],
                           componentes: dict[int, set[int]]) -> dict:
    """Que le pasaria a cada grupo de hoy si se aplicara la identidad nueva.

    Se apoya en que la posicion de `productos` es la fila de `grupos.parquet`, que es a lo que apuntan
    los indices de las aristas.
    """
    se_parten = sobreviven = sin_gtin = 0
    ejemplos = []
    for miembros in componentes.values():
        if any(indice >= len(productos) for indice in miembros):
            continue
        gtimes = {productos[i].gtin for i in miembros if productos[i].gtin}
        cadenas = {productos[i].fuente for i in miembros}
        if len(gtimes) > 1:
            se_parten += 1
            if len(ejemplos) < 5:
                ejemplos.append({
                    "cadenas": sorted(cadenas), "gtins": sorted(gtimes)[:4],
                    "productos": [productos[i].nombre for i in sorted(miembros)][:4]})
        elif len(gtimes) == 1 and len(cadenas) > 1:
            sobreviven += 1
        else:
            sin_gtin += 1
    return {"componentes_actuales": len(componentes), "se_parten": se_parten,
            "sobreviven_como_exactos": sobreviven, "sin_gtin_comparable": sin_gtin,
            "ejemplos_que_se_parten": ejemplos}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--guardar", action="store_true", help="escribir el informe en data/")
    a = ap.parse_args(argv)

    productos = catalogo()
    exactos = identidad.candidatos_por_gtin(productos)
    probables = identidad.candidatos_por_bloque(productos)
    con_gtin = sum(1 for p in productos if p.gtin)

    # Cadenas por grupo exacto: los que de verdad permiten comparar precios.
    multi = {g: m for g, m in exactos.items() if len({p.fuente for p in m}) > 1}
    comparacion = comparar_con_el_actual(productos, componentes_actuales())

    # **Cuarentena**: un grupo exacto con presentaciones incompatibles dentro. Es lo que hay que mirar.
    cuarentena = []
    for gtin, miembros in exactos.items():
        for i, uno in enumerate(miembros):
            for otro in miembros[i + 1:]:
                veredicto = identidad.decide(uno, otro)
                if veredicto["estado"] not in (identidad.EXACTO,):
                    cuarentena.append({"gtin": gtin, "a": f"{uno.fuente}/{uno.id_fuente}",
                                       "b": f"{otro.fuente}/{otro.id_fuente}",
                                       "estado": veredicto["estado"],
                                       "motivos": veredicto["motivos"]})

    informe = {
        "fecha": date.today().isoformat(),
        "productos": len(productos),
        "con_gtin_valido": con_gtin,
        "sin_gtin": len(productos) - con_gtin,
        "grupos_exactos_por_gtin": len(exactos),
        "grupos_exactos_multi_cadena": len(multi),
        "probables_por_bloque": len(probables),
        "en_cuarentena": len(cuarentena),
        "comparacion_con_el_actual": comparacion,
        "familias": dict(Counter(p.familia for p in productos).most_common(8)),
        "aviso": ("Sombra: propone y compara, no publica ni modifica nada. Los grupos exactos solo "
                  "usan GTIN valido; los probables se cuentan aparte y no son identidad."),
    }
    print(f"catalogo: {informe['productos']:,} productos · con GTIN valido: "
          f"{informe['con_gtin_valido']:,} · sin GTIN: {informe['sin_gtin']:,}".replace(",", "."))
    print(f"  grupos exactos por GTIN: {informe['grupos_exactos_por_gtin']:,} "
          f"(de ellos, multi-cadena: {informe['grupos_exactos_multi_cadena']:,})".replace(",", "."))
    print(f"  probables por bloque (NO son identidad): {informe['probables_por_bloque']:,}"
          .replace(",", "."))
    print(f"  en cuarentena (mismo GTIN con presentacion incompatible): "
          f"{informe['en_cuarentena']:,}".replace(",", "."))
    print(f"  grupos del emparejador actual (componentes conexas): "
          f"{comparacion['componentes_actuales']:,}".replace(",", "."))
    print(f"    SE PARTIRIAN al aplicar GTIN valido: {comparacion['se_parten']:,}"
          .replace(",", "."))
    print(f"    sobreviven como exactos (un GTIN, varias cadenas): "
          f"{comparacion['sobreviven_como_exactos']:,}".replace(",", "."))
    print(f"    sin GTIN comparable: {comparacion['sin_gtin_comparable']:,}".replace(",", "."))
    for caso in comparacion["ejemplos_que_se_parten"][:3]:
        print(f"      se parte {caso['cadenas']}: {caso['productos'][:2]}")
    for caso in cuarentena[:5]:
        print(f"    cuarentena {caso['gtin']}: {caso['a']} vs {caso['b']} -- {caso['motivos'][0]}")

    if a.guardar:
        SOMBRA.mkdir(parents=True, exist_ok=True)
        destino = SOMBRA / f"identidad-{informe['fecha']}.json"
        destino.write_text(json.dumps({**informe, "cuarentena": cuarentena[:200]},
                                      ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  informe guardado en {destino.relative_to(RAIZ).as_posix()}")
    print(f"  {informe['aviso']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
