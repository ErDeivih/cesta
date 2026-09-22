"""Las equivalencias entre cadenas, versionadas. Una ejecucion no pisa a la otra.

Hasta hoy, `emparejar` reescribia `data/gold/enlaces.parquet` cada dia, y esos
enlaces eran **pares de posiciones** en la lista de productos (por eso existia
`enlaces_huella.json`: si el catalogo se reordena, los indices apuntan a otros
productos y los grupos salen con cosas que no tienen nada que ver). Aqui se
arreglan las dos cosas:

  - cada par se identifica por `producto_id = "fuente:id_fuente"`, que no cambia
    aunque el catalogo se reordene, se anada una cadena o se caiga un dia;
  - cada pasada escribe su propio directorio, con su fecha y su huella del
    catalogo, asi que **se puede comparar una pasada con la anterior y volver
    atras**. Es lo que pedia el encargo: nunca sobrescribir.

Lo que se guarda por ejecucion, en `data/gold/matching/ejecucion=<id>/`:

    equivalencia.parquet   un par aceptado por fila, con su metodo y sus features
    metrica.parquet        una metrica por fila, con su objetivo y si lo cumple
    resumen.json           de que catalogo salio y con que codigo

Y `data/gold/matching/ultima.json` dice cual es la ultima, para no tener que
listar directorios cada vez.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import polars as pl

from core import config
from core.matching import _ean, _marca

# Version del modelo que produce las equivalencias. Sube cuando cambia el
# algoritmo de una forma que invalida comparar con la pasada anterior.
VERSION_MODELO = "2026-09-22.1"

CARPETA = "matching"


def producto_id(fuente: str, id_fuente) -> str:
    """La clave estable de un producto. No es su posicion en ninguna lista."""
    return f"{fuente}:{id_fuente}"


def id_de_ejecucion(cuando=None) -> str:
    """`20260922-143012`. Ordenable como texto, que es todo lo que hace falta."""
    t = cuando or config.ahora_local()
    return t.strftime("%Y%m%d-%H%M%S")


def huella_catalogo(filas: list[dict]) -> str:
    """Firma de QUE productos hay, en que orden.

    No basta con contar filas: dos catalogos del mismo tamano pueden tener los
    productos en otro orden, y entonces los indices de posicion emparejan cosas
    al azar. Esto firma la secuencia entera de (fuente, id).
    """
    h = hashlib.sha1()
    for f in filas:
        h.update(f"{f.get('fuente')}\x00{f.get('id_fuente')}\n".encode())
    return h.hexdigest()


def features(a: dict, b: dict, parecido: float) -> dict:
    """Por que se acepto este par, en claro y en numeros.

    El encargo pide explicabilidad: cada par tiene que poder auditarse sin que
    nadie apruebe nada. Esto es lo que se ensena en el panel.
    """
    ea, eb = _ean(a.get("ean")), _ean(b.get("ean"))
    ma, mb = _marca(a.get("marca")), _marca(b.get("marca"))
    pa, pb = a.get("precio_unidad_cent"), b.get("precio_unidad_cent")
    ratio = None
    if pa and pb and min(pa, pb) > 0:
        ratio = round(max(pa, pb) / min(pa, pb), 3)
    ca, cb = a.get("cantidad"), b.get("cantidad")
    return {
        "parecido": round(parecido, 4),
        "ean_igual": bool(ea and eb and ea == eb),
        "ean_en_los_dos": bool(ea and eb),
        "marca_igual": bool(ma and ma == mb),
        "cantidad_igual": bool(ca is not None and ca == cb),
        "unidad_igual": bool(a.get("unidad_canon")
                             and a.get("unidad_canon") == b.get("unidad_canon")),
        "seccion_igual": bool(a.get("seccion")
                              and a.get("seccion") == b.get("seccion")),
        "ratio_precio_unidad": ratio,
    }


def filas_de_equivalencia(filas: list[dict], enlaces_: list[tuple],
                          ejecucion_id: str) -> list[dict]:
    """Los pares aceptados, con clave estable, features y de donde salieron."""
    salida = []
    for i, j, parecido, nivel in enlaces_:
        a, b = filas[i], filas[j]
        salida.append({
            "producto_a": producto_id(a["fuente"], a["id_fuente"]),
            "producto_b": producto_id(b["fuente"], b["id_fuente"]),
            "fuente_a": a["fuente"],
            "fuente_b": b["fuente"],
            "nivel": nivel,
            "metodo": "ean" if nivel == "ean" else "nombre",
            "confianza": round(float(parecido), 4),
            "features": json.dumps(features(a, b, parecido), ensure_ascii=False),
            "ejecucion_id": ejecucion_id,
        })
    return salida


def escribe_ejecucion(ejecucion_id: str, equivalencias: list[dict],
                      metricas: dict[str, float], resumen: dict,
                      gold: Path | None = None) -> Path:
    """Escribe la pasada entera. Nunca toca las anteriores."""
    raiz = (gold or config.GOLD) / CARPETA
    carpeta = raiz / f"ejecucion={ejecucion_id}"
    carpeta.mkdir(parents=True, exist_ok=True)
    from core.storage import write_parquet_file
    if equivalencias:
        write_parquet_file(
            pl.DataFrame(equivalencias, infer_schema_length=None),
            carpeta / "equivalencia.parquet")
    if metricas:
        write_parquet_file(
            pl.DataFrame({
                "ejecucion_id": [ejecucion_id] * len(metricas),
                "metrica": list(metricas),
                "valor": [float(v) for v in metricas.values()],
            }),
            carpeta / "metrica.parquet")
    (carpeta / "resumen.json").write_text(
        json.dumps({**resumen, "ejecucion_id": ejecucion_id,
                    "version_modelo": VERSION_MODELO},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    (raiz / "ultima.json").write_text(
        json.dumps({"ejecucion_id": ejecucion_id}, ensure_ascii=False),
        encoding="utf-8")
    return carpeta


def ultima(gold: Path | None = None) -> str | None:
    """El id de la ultima pasada, o None si no hay ninguna."""
    raiz = (gold or config.GOLD) / CARPETA
    marca = raiz / "ultima.json"
    if marca.exists():
        try:
            return json.loads(marca.read_text(encoding="utf-8"))["ejecucion_id"]
        except (KeyError, ValueError):
            pass
    carpetas = sorted(p.name.split("=")[1]
                      for p in raiz.glob("ejecucion=*") if p.is_dir())
    return carpetas[-1] if carpetas else None


def lee_equivalencias(ejecucion_id: str | None = None,
                      gold: Path | None = None) -> pl.DataFrame:
    """Las equivalencias de una pasada. Sin argumentos, las de la ultima."""
    raiz = (gold or config.GOLD) / CARPETA
    eid = ejecucion_id or ultima(gold)
    if not eid:
        return pl.DataFrame()
    ruta = raiz / f"ejecucion={eid}" / "equivalencia.parquet"
    return pl.read_parquet(ruta) if ruta.exists() else pl.DataFrame()


def metricas_de(ejecucion_id: str, gold: Path | None = None) -> dict[str, float]:
    raiz = (gold or config.GOLD) / CARPETA
    ruta = raiz / f"ejecucion={ejecucion_id}" / "metrica.parquet"
    if not ruta.exists():
        return {}
    d = pl.read_parquet(ruta)
    return dict(zip(d["metrica"].to_list(), d["valor"].to_list(), strict=True))


if __name__ == "__main__":
    for eid in sorted(p.name.split("=")[1]
                      for p in (config.GOLD / CARPETA).glob("ejecucion=*")):
        m = metricas_de(eid)
        print(f"{eid}  {len(lee_equivalencias(eid))} equivalencias  " +
              "  ".join(f"{k}={v:.3f}" for k, v in list(m.items())[:4]))
