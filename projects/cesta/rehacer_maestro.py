"""Rehace las fichas maestras desde el crudo guardado, sin tocar la red.

Por que hace falta
------------------
`reprocesar.py` rehace bronze desde el crudo, pero bronze no lo es todo: el EAN,
los ingredientes, los alergenos, el origen, la tabla nutricional y la caducidad
no vienen del listado, sino de la ficha de cada producto, y viven en
data/master/<cadena>.json.gz. Ese fichero **solo lo escribia el colector al
scrapear**, asi que mejorar el lector de fichas no servia de nada hasta la
siguiente pasada completa de fichas, que en DIA son 5.410 peticiones a una web
detras de Akamai y en Mercadona 4.378.

Eso paso de verdad: el 16 de septiembre se enseno a `dia.py` a leer la tabla
nutricional, los dias de caducidad, el peso escurrido, el envase y el tipo de
producto. Cinco campos nuevos, cero productos con ellos, porque el maestro
seguia siendo el del dia 7. Y las fichas del dia 7 estaban guardadas enteras en
data/raw todo el tiempo.

Este fichero las vuelve a leer. No pide nada a nadie.

    uv run python -m projects.cesta.rehacer_maestro --fuente dia
    uv run python -m projects.cesta.rehacer_maestro --fuente mercadona

Como encuentra las fichas
-------------------------
`save_raw` guarda cada respuesta con el nombre `sha1(clave)[:12]-sha256(cuerpo)[:12]`,
o sea que la clave original no se puede leer del nombre del fichero. Pero si se
puede ir al reves: se sabe que la clave de una ficha es "product-<id>" y se sabe
que ids hay (estan en bronze), asi que se calcula el hash de cada clave posible y
se busca ese prefijo. De los 5.411 productos de DIA aparecen 5.410.
"""
from __future__ import annotations

import argparse
import glob
import gzip
import hashlib
import importlib
import json
import os
import time

import polars as pl

from core import config

# El campo del JSON de la ficha que lleva el id, por si hace falta comprobar que
# el fichero es de verdad una ficha y no otra respuesta con el mismo prefijo.
CLAVE_ID = {"dia": "sku_id", "mercadona": "id"}


def _ids_conocidos(fuente: str) -> list[str]:
    partes = sorted(glob.glob(str(config.DATA / "bronze" / f"fuente={fuente}"
                                  / "fecha=*" / "part.parquet")))
    if not partes:
        return []
    vistos: dict[str, None] = {}
    for parte in partes:
        for x in pl.read_parquet(parte, columns=["id_fuente"])["id_fuente"].to_list():
            if x:
                vistos[str(x)] = None
    return list(vistos)


def rehacer(fuente: str, escribir: bool = True, segundos: float = 0.0) -> int:
    t0 = time.monotonic()
    mod = importlib.import_module(f"projects.cesta.collectors.{fuente}")
    de_ficha = getattr(mod, "_maestro_de_ficha", None)
    if de_ficha is None:
        print(f"{fuente} no tiene fichas maestras")
        return 1

    ids = _ids_conocidos(fuente)
    if not ids:
        print(f"no hay bronze de {fuente} del que sacar los ids")
        return 1
    por_hash = {hashlib.sha1(f"product-{i}".encode()).hexdigest()[:12]: i for i in ids}

    # El crudo mas reciente gana: una ficha se puede haber vuelto a pedir.
    candidatos: dict[str, tuple[int, str]] = {}
    for carpeta in sorted(glob.glob(str(config.RAW / f"fuente={fuente}" / "fecha=*"))):
        for nombre in os.listdir(carpeta):
            ident = por_hash.get(nombre.split("-", 1)[0])
            if ident is None:
                continue
            camino = os.path.join(carpeta, nombre)
            marca = os.stat(camino).st_mtime_ns
            if ident not in candidatos or marca > candidatos[ident][0]:
                candidatos[ident] = (marca, camino)

    # Reanudable a proposito. Leer 5.410 ficheros pequenos de disco tarda
    # varios minutos cuando data/ esta en un disco lento o en un recurso de red,
    # y quedarse a medias y tener que empezar de cero es lo que hace que una
    # herramienta asi no se use nunca. Lo leido se va dejando en un fichero
    # parcial; volver a lanzarlo continua donde iba.
    parcial = config.DATA / "master" / f"{fuente}.parcial.json.gz"
    maestro, rotas = {}, 0
    if parcial.exists():
        try:
            maestro = json.loads(gzip.decompress(parcial.read_bytes()))
            print(f"  continuo: {len(maestro)} fichas ya leidas")
        except Exception:  # noqa: BLE001
            maestro = {}

    hecho = 0
    for ident, (_, camino) in candidatos.items():
        if ident in maestro:
            continue
        if segundos and time.monotonic() - t0 > segundos:
            parcial.parent.mkdir(parents=True, exist_ok=True)
            parcial.write_bytes(gzip.compress(
                json.dumps(maestro, ensure_ascii=False, sort_keys=True).encode()))
            print(f"  pausa: {len(maestro)} de {len(candidatos)} fichas; "
                  f"vuelve a lanzarlo para continuar")
            return 2
        hecho += 1
        try:
            with open(camino, "rb") as fh:
                ficha = json.loads(gzip.decompress(fh.read()))
        except Exception:  # noqa: BLE001
            rotas += 1
            continue
        if not isinstance(ficha, dict) or CLAVE_ID.get(fuente, "id") not in ficha:
            rotas += 1
            continue
        maestro[ident] = de_ficha(ficha)

    anterior = mod._cargar_maestro()
    print(f"{fuente}: {len(maestro)} fichas leidas del crudo "
          f"({len(ids)} ids conocidos, {rotas} descartadas)")
    _compara(anterior, maestro)
    if not escribir:
        print("  (--ver: no se escribe nada)")
        return 0
    if len(maestro) < len(anterior) * 0.9:
        print(f"  NO se escribe: el maestro nuevo tiene {len(maestro)} fichas y "
              f"el viejo {len(anterior)}")
        return 1
    mod._guardar_maestro(maestro)
    # El parcial ya no sirve. Si el sistema de ficheros no deja borrarlo (pasa
    # con carpetas montadas en solo-anadir), se vacia, que tiene el mismo efecto:
    # la proxima vez se lee, sale un diccionario vacio y se empieza de cero.
    if parcial.exists():
        try:
            parcial.unlink()
        except OSError:
            parcial.write_bytes(gzip.compress(b"{}"))
    print(f"  escrito data/master/{fuente}.json.gz")
    return 0


def _compara(antes: dict, ahora: dict) -> None:
    """Campo a campo, cuantas fichas lo tenian y cuantas lo tienen."""
    campos = sorted({k for f in ahora.values() for k in f}
                    | {k for f in antes.values() for k in f})
    for campo in campos:
        a = sum(1 for f in antes.values() if f.get(campo) is not None)
        b = sum(1 for f in ahora.values() if f.get(campo) is not None)
        if a != b:
            flecha = "+" if b > a else "-"
            print(f"    {flecha} {campo:20s} {a:5d} -> {b:5d}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="rehacer_maestro")
    ap.add_argument("--fuente", required=True)
    ap.add_argument("--ver", action="store_true", help="solo mide, no escribe")
    ap.add_argument("--segundos", type=float, default=0.0,
                    help="pausa y guarda el avance pasados N segundos")
    a = ap.parse_args(argv)
    return rehacer(a.fuente, escribir=not a.ver, segundos=a.segundos)


if __name__ == "__main__":
    raise SystemExit(main())
