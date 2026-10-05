"""Auditoria de solo lectura: distingue grupos comerciales de identidad exacta.

No recalcula grupos ni modifica datos. Emite JSON reproducible por stdout.
"""
from __future__ import annotations

import json
import unicodedata
from pathlib import Path

import polars as pl

from core import config
from core.matching import _ean


def medir(raiz: Path) -> dict:
    df = pl.read_parquet(raiz / "gold" / "grupos.parquet")
    filas = df.to_dicts()
    grupos: dict[int, list[dict]] = {}
    for fila in filas:
        if fila.get("grupo_id") is not None:
            grupos.setdefault(fila["grupo_id"], []).append(fila)
    multi = {g: fs for g, fs in grupos.items() if len({f["fuente"] for f in fs}) > 1}
    varios_ean = {
        g: fs for g, fs in multi.items()
        if len({_ean(f.get("ean")) for f in fs if _ean(f.get("ean"))}) > 1
    }
    varios_formatos = {
        g: fs for g, fs in multi.items()
        if len({(f.get("unidad_canon"), round(f["cantidad"], 4))
                for f in fs if f.get("cantidad_fiable") and f.get("cantidad")}) > 1
    }
    ejemplos = []
    for gid, fs in multi.items():
        if any("asturiana" in (f.get("nombre") or "").lower()
               and "leche entera" in (f.get("nombre") or "").lower() for f in fs):
            ejemplos.append({"grupo_id": gid, "miembros": [
                {k: f.get(k) for k in ("fuente", "id_fuente", "nombre", "ean",
                                       "cantidad", "unidad_canon", "precio_cent")}
                for f in fs]})
    particiones = {}
    for capa in ("bronze", "silver"):
        ultimas = {}
        for ruta in sorted((raiz / capa).glob("fuente=*/fecha=*/part.parquet")):
            ultimas[ruta.parent.parent.name.removeprefix("fuente=")] = ruta
        particiones[capa] = {
            fuente: {"fecha": ruta.parent.name.removeprefix("fecha="),
                     "filas": pl.scan_parquet(ruta).select(pl.len()).collect().item()}
            for fuente, ruta in ultimas.items()
        }
    fuera = []
    for f in filas:
        rama = (f.get("categoria") or "").split(" > ")[0].strip().lower()
        rama = "".join(c for c in unicodedata.normalize("NFD", rama)
                       if unicodedata.category(c) != "Mn")
        if f["fuente"] == "alcampo" and rama in config.RAMAS_EXCLUIDAS_ALCAMPO:
            fuera.append(f)
    return {
        "productos": len(filas), "grupos_multicadena": len(multi),
        "grupos_multicadena_con_varios_ean": len(varios_ean),
        "grupos_multicadena_con_varios_formatos_fiables": len(varios_formatos),
        "aviso": "EAN distintos no prueban por si solos incompatibilidad, pero tampoco identidad.",
        "columnas_ausentes_gold": [k for k in ("disponible", "capturado_en", "tienda_id")
                                  if k not in df.columns],
        "calidad_por_origen": df.group_by("calidad_origen").len().to_dicts(),
        "alcampo_en_ramas_excluidas": len(fuera),
        "ejemplos_fuera_alcance": [{k: f.get(k) for k in ("nombre", "categoria")}
                                  for f in fuera[:5]],
        "particiones": particiones, "ejemplos_leche": ejemplos[:8],
    }


if __name__ == "__main__":
    print(json.dumps(medir(config.DATA), ensure_ascii=False, indent=2, default=str))
