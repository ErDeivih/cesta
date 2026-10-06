"""Diagnostico reproducible de comparacion y riqueza del catalogo, sin escrituras.

No sustituye T03 ni publica identidades. Evalua pares de grupos existentes y
recupera pares adicionales por GTIN. El parecido textual solo ordena revision.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import unicodedata
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

import polars as pl

from core import config
from core.atributos import valores

CAMPOS = ("ingredientes", "alergenos", "nutricion", "nutricion_por", "descripcion",
          "conservacion", "origen", "ean", "envase", "peso_neto_g", "peso_escurrido_g")


def presente(valor):
    if valor is None:
        return False
    if isinstance(valor, float) and not math.isfinite(valor):
        return False
    if isinstance(valor, str):
        return valor.strip().lower() not in ("", "null", "none", "{}", "[]")
    return True


def gtin(valor):
    """Validacion estructural, NO prueba de asignacion por GS1 ni de identidad."""
    if not isinstance(valor, str):
        return None
    s = valor.strip()
    if len(s) not in (8, 12, 13, 14) or not re.fullmatch(r"[0-9]+", s):
        return None
    if len(set(s)) == 1:
        return None
    suma = sum(int(c) * (3 if i % 2 == 0 else 1)
               for i, c in enumerate(reversed(s[:-1])))
    return s.zfill(14) if (-suma) % 10 == int(s[-1]) else None


def _texto(s):
    return " ".join(re.findall(r"[a-z0-9]+", "".join(
        c for c in unicodedata.normalize("NFD", str(s or "").lower())
        if unicodedata.category(c) != "Mn")))


def evaluar(a, b):
    """Veto de contradicciones antes de cualquier semejanza; ausencia != igualdad."""
    conflictos = []
    for campo in ("marca", "envase", "conservacion", "tipo_producto"):
        if (presente(a.get(campo)) and presente(b.get(campo))
                and _texto(a[campo]) != _texto(b[campo])):
            conflictos.append(campo)
    ea, eb = valores(a.get("nombre")), valores(b.get("nombre"))
    conflictos.extend(f"atributo:{k}" for k in sorted(ea.keys() & eb.keys()) if ea[k] != eb[k])
    formatos = []
    for f in (a, b):
        q = f.get("cantidad")
        fiable = f.get("cantidad_fiable") is True
        formatos.append((f.get("unidad_canon"), round(float(q), 6))
                        if fiable and isinstance(q, (int, float)) and math.isfinite(q)
                        and q > 0 and presente(f.get("unidad_canon")) else None)
    if all(formatos) and formatos[0] != formatos[1]:
        conflictos.append("formato")
    if (all(presente(f.get("unidades_pack")) for f in (a, b))
            and a["unidades_pack"] != b["unidades_pack"]):
        conflictos.append("unidades_pack")
    ga, gb = gtin(a.get("ean")), gtin(b.get("ean"))
    ta, tb = set(_texto(a.get("nombre")).split()), set(_texto(b.get("nombre")).split())
    similitud = len(ta & tb) / len(ta | tb) if ta | tb else 0.0
    if conflictos:
        estado = "conflicto"
    elif ga and gb and ga != gb:
        estado = "codigos_distintos_no_identidad"
    elif ga and ga == gb:
        estado = "candidato_exacto_gtin" if all(formatos) else "gtin_sin_formato_verificado"
    else:
        estado = "evidencia_insuficiente"
    return {"estado": estado, "conflictos": conflictos, "similitud_texto": round(similitud, 4)}


def medir(ruta: Path):
    df = pl.read_parquet(ruta)
    necesarias = {"fuente", "id_fuente", "nombre", "grupo_id"}
    if not necesarias <= set(df.columns) or df.is_empty():
        raise ValueError("Catalogo vacio o faltan columnas obligatorias")
    filas = df.to_dicts()
    fuentes = {}
    for fuente in sorted({f["fuente"] for f in filas}):
        fs = [f for f in filas if f["fuente"] == fuente]
        campos = {k: {"presentes": sum(presente(f.get(k)) for f in fs),
                      "columna_existe": k in df.columns} for k in CAMPOS}
        nutricion_util = 0
        for f in fs:
            try:
                n = json.loads(f.get("nutricion") or "null")
            except (TypeError, ValueError):
                continue
            if (isinstance(n, dict) and f.get("nutricion_por") in ("100g", "100ml")
                    and any(isinstance(v, (int, float)) and not isinstance(v, bool)
                            and math.isfinite(v) and v >= 0 for v in n.values())):
                nutricion_util += 1
        fuentes[fuente] = {"productos": len(fs), "campos": campos,
                           "nutricion_numerica_con_base": nutricion_util,
                           "gtin_estructura_valida": sum(gtin(f.get("ean")) is not None for f in fs)}
    bloques = defaultdict(list)
    for i, f in enumerate(filas):
        if f["grupo_id"] is not None:
            bloques[("grupo", str(f["grupo_id"]))].append(i)
        g = gtin(f.get("ean"))
        if g:
            bloques[("gtin", g)].append(i)
    vistos = set()
    estados = Counter()
    ejemplos = defaultdict(list)
    for bloque in bloques.values():
        for i, j in combinations(bloque, 2):
            if filas[i]["fuente"] == filas[j]["fuente"] or (i, j) in vistos:
                continue
            vistos.add((i, j))
            resultado = evaluar(filas[i], filas[j])
            estado = resultado["estado"]
            estados[estado] += 1
            if len(ejemplos[estado]) < 5:
                ejemplos[estado].append({**resultado, "productos": [
                    {k: f.get(k) for k in ("fuente", "id_fuente", "nombre", "ean")}
                    for f in (filas[i], filas[j])]})
    return {"productos": len(filas), "fuentes": fuentes, "pares_evaluados": len(vistos),
            "estados_pares": dict(estados), "ejemplos": dict(ejemplos),
            "limites": ["Solo grupos existentes y GTIN: no mide recall global ni descubre todo.",
                        "Candidato no es identidad publicada; GTIN valido no certifica asignacion.",
                        "Presencia de nutricion no certifica exactitud ni cobertura de calorias.",
                        "No modifica datos, grupos, listas ni colectores."]}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--catalogo", type=Path, default=config.DATA / "gold" / "grupos.parquet")
    args = ap.parse_args()
    print(json.dumps(medir(args.catalogo), ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
