"""Las metricas de Cesta que lee el panel de proyectos.

**Por que existe.** David pidio el 2026-11-04 mas datos de Cesta en su panel, y la metrica
que de verdad dice si el producto sirve no es «cuantos productos hay» sino **cuantos se
pueden comparar hoy**: grupos con precio en mas de una cadena. Un numero escrito a mano
envejece; este sale del gold y se reescribe al cerrar la pasada, como `docs/CIFRAS.md`.

**Las dos cifras que importan van sobre el MISMO dia** (`fecha_datos`): mezclar «cuantos
comparables hay» (catalogo) con «cuantos tienen 2+ cadenas» (hoy) daria una razon que no
significa nada. `comparables_con_precio` son los grupos comparables con precio ese dia y
`en_varias_cadenas`, de esos, los que tienen precio en 2 o mas cadenas.

Se escribe en la **raiz del proyecto** (`metricas-cesta.json`), porque es donde lo busca el
panel, y de forma atomica: un JSON a medias se leeria como una foto valida.

    uv run python -m projects.cesta.metricas
    uv run python -m projects.cesta.metricas --ver
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

import polars as pl

from core import config

NOMBRE = "metricas-cesta.json"
TZ = ZoneInfo("Europe/Madrid")


def _lee(ruta: Path, columnas: list[str] | None = None) -> pl.DataFrame | None:
    if not ruta.is_file():
        return None
    try:
        return pl.read_parquet(ruta, columns=columnas)
    except Exception:  # noqa: BLE001  (un gold ilegible no inventa cifras: se dice a cero)
        return None


def _fecha_de_datos(precios: pl.DataFrame | None) -> str | None:
    if precios is None or precios.is_empty():
        return None
    return str(precios["fecha"].max())


def _ultima_ejecucion() -> str | None:
    """La ultima pasada de `runs.csv`, en hora de Madrid.

    `ts` esta en UTC; el panel lo lee una persona, y una pasada a las 23:30Z es del dia
    siguiente en Madrid. Se da la marca completa en local, no el prefijo UTC.
    """
    ruta = config.DATA / "runs.csv"
    if not ruta.is_file():
        return None
    try:
        marco = pl.read_csv(ruta, infer_schema_length=0)
        if marco.is_empty() or "ts" not in marco.columns:
            return None
        sello = max(marco["ts"].to_list())
        return dt.datetime.fromisoformat(sello).astimezone(TZ).isoformat(timespec="seconds")
    except Exception:  # noqa: BLE001  (un CSV ilegible no tumba el panel)
        return None


def _ingesta() -> dict | None:
    """El estado que dejo el vigilante de la ingesta, para que el panel no tenga que mirarlo.

    Se lee `data/avisos_ingesta.json` (lo escribe `scripts.vigilar_ingesta` al cerrar la
    pasada). Sin fichero, `None`: no se inventa un «todo bien» que nadie ha comprobado.
    """
    ruta = config.DATA / "avisos_ingesta.json"
    if not ruta.is_file():
        return None
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        avisos = datos.get("avisos") or []
        return {
            "fecha": datos.get("fecha"),
            "estado": datos.get("estado"),
            "avisos": len(avisos),
            "codigos": sorted({str(a.get("codigo")) for a in avisos if a.get("codigo")}),
        }
    except (OSError, ValueError):
        return {"fecha": None, "estado": "ilegible", "avisos": 0, "codigos": []}


def construye() -> dict:
    """La foto de hoy: cadenas, comparables y dias de historial. Sin datos, ceros."""
    grupos = _lee(config.DATA / "gold" / "grupos.parquet")
    precios = _lee(config.DATA / "gold" / "precio_diario.parquet")
    fecha = _fecha_de_datos(precios)

    cadenas: list[dict] = []
    if grupos is not None or precios is not None:
        fuentes: set[str] = set()
        if grupos is not None:
            fuentes |= set(grupos["fuente"].unique().to_list())
        if precios is not None:
            fuentes |= set(precios["fuente"].unique().to_list())
        fechas_por_cadena: dict[str, set[str]] = {}
        if precios is not None:
            for fila in (
                precios.select(["fuente", "fecha"]).unique().iter_rows(named=True)
            ):
                fechas_por_cadena.setdefault(fila["fuente"], set()).add(str(fila["fecha"]))
        for fuente in sorted(fuentes):
            suyas = fechas_por_cadena.get(fuente, set())
            cadenas.append({"nombre": fuente, "hoy": fecha in suyas if fecha else False,
                            "dias": len(suyas)})

    comparables = 0
    en_varias = 0
    if grupos is not None and not grupos.is_empty() and precios is not None and fecha:
        comparables_df = grupos.filter(pl.col("precio_comparable") == True)  # noqa: E712
        # **El precio que cuenta es el de HOY**, no el `precio_cent` del catalogo (que es una
        # foto del ultimo precio por producto y puede venir vacia): si hay fila de precio del
        # dia con importe, el producto tiene precio hoy.
        hoy = precios.filter(
            (pl.col("fecha") == fecha) & pl.col("precio_cent").is_not_null()
        ).select(["fuente", "id_fuente"])
        del_dia = comparables_df.select(["fuente", "id_fuente", "grupo_id"]).join(
            hoy, on=["fuente", "id_fuente"], how="inner"
        )
        comparables = del_dia["grupo_id"].n_unique()
        por_grupo = del_dia.group_by("grupo_id").agg(
            pl.col("fuente").n_unique().alias("cadenas")
        )
        en_varias = por_grupo.filter(pl.col("cadenas") >= 2).height

    dias = precios["fecha"].n_unique() if precios is not None else 0
    return {
        "fecha_datos": fecha,
        "cadenas": cadenas,
        "ultima_ejecucion": _ultima_ejecucion(),
        "comparables_con_precio": int(comparables),
        "en_varias_cadenas": int(en_varias),
        "dias_historial": int(dias),
        "ingesta": _ingesta(),
    }


def escribe(destino: Path | None = None) -> Path:
    """Escribe el JSON de forma atomica y devuelve la ruta. Donde el panel lo busca por defecto."""
    ruta = destino or (config.DATA.parent / NOMBRE)
    datos = construye()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    temporal = ruta.with_suffix(".json.tmp")
    temporal.write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(temporal, ruta)
    return ruta


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--ver", action="store_true", help="ensena el JSON sin escribirlo")
    a = ap.parse_args(argv)
    if a.ver:
        print(json.dumps(construye(), ensure_ascii=False, indent=1))
        return 0
    ruta = escribe()
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    print(f"metricas escritas: {ruta}")
    print(f"  fecha de datos: {datos['fecha_datos']} · "
          f"{datos['en_varias_cadenas']} de {datos['comparables_con_precio']} comparables "
          f"con precio en 2+ cadenas · {datos['dias_historial']} dias de historial")
    return 0


if __name__ == "__main__":
    sys.exit(main())
