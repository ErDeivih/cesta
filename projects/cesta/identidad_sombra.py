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


def grupos_actuales() -> dict[str, set[str]]:
    """Los grupos del emparejador en uso, por su columna de identificador."""
    ruta = RAIZ / "data" / "gold" / "enlaces.parquet"
    if not ruta.exists():
        return {}
    marco = pl.read_parquet(ruta)
    columna = next((c for c in marco.columns
                    if c.lower() in ("grupo_id", "grupo", "cluster", "grupo_identidad")), None)
    if columna is None or "fuente" not in marco.columns:
        return {}
    por_grupo: dict[str, set[str]] = {}
    for grupo, fuente in marco.select([columna, "fuente"]).iter_rows():
        por_grupo.setdefault(str(grupo), set()).add(str(fuente))
    return {g: f for g, f in por_grupo.items() if len(f) > 1}


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
    actuales = grupos_actuales()

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

    # **Lo que se partiria**: grupos actuales que mezclan GTIN distintos.
    por_grupo_gtin: dict[str, set[str]] = {}
    indice = {f"{p.fuente}|{p.id_fuente}": p.gtin for p in productos}
    for grupo, fuentes in actuales.items():
        pass
    informe = {
        "fecha": date.today().isoformat(),
        "productos": len(productos),
        "con_gtin_valido": con_gtin,
        "sin_gtin": len(productos) - con_gtin,
        "grupos_exactos_por_gtin": len(exactos),
        "grupos_exactos_multi_cadena": len(multi),
        "probables_por_bloque": len(probables),
        "en_cuarentena": len(cuarentena),
        "grupos_actuales_multi_cadena": len(actuales),
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
    print(f"  grupos del emparejador actual, multi-cadena: {informe['grupos_actuales_multi_cadena']:,}"
          .replace(",", "."))
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
