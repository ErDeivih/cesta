"""T02: manifiesto de publicacion, y su enganche al final de la pasada.

**Que problema resuelve.** Hoy se puede saber que hay en gold, pero no *con que*: que capturas, de
que dia, con que version de la politica de alcance y con que cobertura. Sin eso, dos catalogos
distintos parecen el mismo, y una comparacion puede ser exacta y estar comparando cosas distintas.
La ampliacion lo pide en T02 con estas palabras: *"oferta trazable y publicacion por versiones"*.

**Que lleva el manifiesto:**

  - la **fecha** y el momento de generacion;
  - por cadena, la **fecha de su captura** y cuantas filas trae (una cadena que no corrio se ve);
  - la **version y la huella de la politica de alcance** (`sha256` del yml): si cambia una regla,
    el manifiesto cambia, y eso es lo que permite decir con que reglas se publico un catalogo;
  - la **huella de cada fichero de gold** (sha256 corto, filas y bytes);
  - la **cobertura declarada** por los colectores que la declaran (Lidl dice que son ofertas
    conocidas y no un catalogo completo): asi la aplicacion puede ensenarlo junto al dato;
  - y **avisos**: que cadenas no tienen captura de hoy.

**Se escribe de forma atomica** (fichero temporal y renombrado): un manifiesto a medias es peor que
no tenerlo, porque parece una publicacion valida.

Y **no puede tumbar el dia**: si falla, se avisa y se sigue. El dia se mide por el dato, no por el
manifiesto; lo que no se puede es publicar sin decir que paso.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import polars as pl

RAIZ = Path(__file__).resolve().parents[1]
GOLD = RAIZ / "data" / "gold"
BRONZE = RAIZ / "data" / "bronze"
COBERTURA = RAIZ / "data" / "cobertura"
POLITICA = RAIZ / "core" / "datos" / "alcance.yml"
MANIFIESTO = GOLD / "manifiesto.json"
VERSION_MANIFIESTO = 1

# Los ficheros que son la publicacion. `grupos_anterior` queda fuera a proposito: es una copia de
# trabajo para comparar, no algo que se publique.
PUBLICADOS = ["grupos.parquet", "enlaces.parquet", "precio_diario.parquet", "precio_derivado.parquet",
              "resumen.parquet", "promos_por_cadena.parquet"]


def huella(ruta: Path, trozos: int = 12) -> str | None:
    """Huella corta del contenido. Sirve para decir 'esto es lo que se publico', no para seguridad."""
    if not ruta.exists():
        return None
    h = hashlib.sha256()
    with ruta.open("rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()[:trozos]


def _fuentes(hoy: date | None = None) -> dict[str, dict]:
    """Por cadena: la fecha de su ultima captura, cuantas filas y si es del dia del manifiesto.

    `hoy` se pasa desde `construye` en vez de leer el reloj aqui: un modulo que recibe una fecha y
    usa otra por dentro es una trampa para quien lo llame manana.
    """
    salida: dict[str, dict] = {}
    if not BRONZE.exists():
        return salida
    dia = (hoy or date.today()).isoformat()
    for carpeta in sorted(BRONZE.iterdir()):
        if not carpeta.is_dir() or not carpeta.name.startswith("fuente="):
            continue
        fuente = carpeta.name.split("=", 1)[1]
        dias = sorted(d for d in carpeta.iterdir() if d.is_dir())
        if not dias:
            salida[fuente] = {"captura": None, "filas": 0, "de_hoy": False}
            continue
        ultimo = dias[-1]
        captura = ultimo.name.split("=", 1)[1]
        filas = 0
        for fichero in sorted(ultimo.glob("*.parquet")):
            try:
                filas += pl.read_parquet(fichero, columns=[]).height
            except Exception:  # noqa: BLE001  (una captura ilegible no invalida el manifiesto)
                filas += 0
        salida[fuente] = {"captura": captura, "filas": filas,
                          "de_hoy": captura == dia}
    return salida


def _precios() -> dict[str, str]:
    """La fecha del ultimo precio de cada cadena. **Medida aparte de la ficha.**

    G07: *«descubrimiento con sitemap antiguo no implica automaticamente precio antiguo; **medir ambos
    por separado**»*. Hasta hoy el manifiesto declaraba **una sola** fecha de captura -- la de ficha,
    que sale de `bronze` -- y los precios viven en `gold/precio_diario` con la suya. *Un catalogo con
    las fichas de hoy y los precios de anteayer producia **cero avisos** y se leia como fresco.*

    **No lanza**: sin fichero, o ilegible, se devuelve vacio y el manifiesto sale sin esa columna.
    *El dia se mide por el dato, no por el manifiesto.*
    """
    ruta = GOLD / "precio_diario.parquet"
    if not ruta.exists():
        return {}
    try:
        marco = pl.read_parquet(ruta, columns=["fuente", "fecha"])
        agrupado = marco.group_by("fuente").agg(pl.col("fecha").max().alias("ultima"))
        return {fila["fuente"]: str(fila["ultima"]) for fila in agrupado.iter_rows(named=True)}
    except Exception:  # noqa: BLE001  (un precio ilegible no invalida el manifiesto)
        return {}


def _cobertura() -> dict[str, dict]:
    """Lo que cada colector declara sobre su propia cobertura (Lidl: ofertas conocidas)."""
    salida: dict[str, dict] = {}
    if not COBERTURA.exists():
        return salida
    for fichero in sorted(COBERTURA.glob("*.json")):
        try:
            salida[fichero.stem] = json.loads(fichero.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            salida[fichero.stem] = {"aviso": "cobertura ilegible"}
    return salida


def construye(fecha: date | None = None) -> dict:
    dia = fecha or date.today()
    fuentes = _fuentes(dia)
    # **La fecha del precio, por cadena, junto a la de ficha.** *Son dos relojes distintos.*
    precios = _precios()
    for fuente, cuando in precios.items():
        fuentes.setdefault(fuente, {"captura": None, "filas": 0, "de_hoy": False})["precio"] = cuando
    for datos in fuentes.values():
        datos.setdefault("precio", None)
    ficheros = {}
    for nombre in PUBLICADOS:
        ruta = GOLD / nombre
        filas = None
        if ruta.exists():
            try:
                filas = pl.read_parquet(ruta, columns=[]).height
            except Exception:  # noqa: BLE001
                filas = None
        ficheros[nombre] = {"sha256": huella(ruta), "filas": filas,
                            "bytes": ruta.stat().st_size if ruta.exists() else None}
    avisos = []
    if not fuentes:
        avisos.append("no hay ninguna captura en bronze: esto no es un catalogo")
    for fuente, datos in fuentes.items():
        if not datos["de_hoy"]:
            avisos.append(f"{fuente}: sin captura de hoy (la ultima es {datos['captura']})")
        # **Y el precio, aparte.** *Una ficha de hoy con un precio de anteayer no es un catalogo de
        # hoy, y hasta ahora no lo decia nadie.*
        if datos["precio"] is not None and datos["precio"] != dia.isoformat() and datos["de_hoy"]:
            avisos.append(f"{fuente}: la ficha es de hoy pero el precio es de {datos['precio']}")
    sin_fichero = [n for n, d in ficheros.items() if d["sha256"] is None]
    if sin_fichero:
        avisos.append(f"falta publicar: {', '.join(sin_fichero)}")
    return {
        "version_manifiesto": VERSION_MANIFIESTO,
        "fecha": dia.isoformat(),
        "generado_en": datetime.now(timezone.utc).isoformat(),
        "politica_alcance": {"version": _version_politica(), "sha256": huella(POLITICA)},
        "fuentes": fuentes,
        "ficheros": ficheros,
        "cobertura_declarada": _cobertura(),
        "avisos": avisos,
    }


def _version_politica() -> int | None:
    try:
        import yaml

        return int(yaml.safe_load(POLITICA.read_text(encoding="utf-8")).get("version"))
    except Exception:  # noqa: BLE001
        return None


def escribe(fecha: date | None = None) -> Path | None:
    """Escribe el manifiesto de forma atomica. **Nunca lanza**: el dia no se cae por esto."""
    try:
        datos = construye(fecha)
        GOLD.mkdir(parents=True, exist_ok=True)
        temporal = MANIFIESTO.with_suffix(".json.tmp")
        temporal.write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
        # **Renombrado atomico**: un manifiesto a medias parece una publicacion valida.
        os.replace(temporal, MANIFIESTO)
        return MANIFIESTO
    except Exception as exc:  # noqa: BLE001
        print(f"[manifiesto] no se pudo escribir: {type(exc).__name__}: {exc}")
        return None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--ver", action="store_true", help="ensenar el manifiesto sin escribirlo")
    a = ap.parse_args(argv)
    if a.ver:
        print(json.dumps(construye(), ensure_ascii=False, indent=1))
        return 0
    ruta = escribe()
    if ruta is None:
        print("el manifiesto no se pudo escribir (ver el aviso de arriba)")
        return 1
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    print(f"manifiesto escrito: {ruta.relative_to(RAIZ)}")
    print(f"  politica de alcance v{datos['politica_alcance']['version']} "
          f"({datos['politica_alcance']['sha256']})")
    print(f"  cadenas: {len(datos['fuentes'])} · avisos: {len(datos['avisos'])}")
    for aviso in datos["avisos"][:6]:
        print(f"    {aviso}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
