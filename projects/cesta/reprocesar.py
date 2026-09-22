"""Rehace bronze desde el crudo guardado, sin tocar la red.

Para esto se guarda el crudo: cuando cambia el parser, se reprocesa el historico
entero en segundos en vez de volver a scrapear.

    uv run python -m projects.cesta.reprocesar --fuente mercadona
    uv run python -m projects.cesta.reprocesar --fuente mercadona --fecha 2026-09-06

Dos cosas que este fichero hacia mal, arregladas el 17 de septiembre de 2026
---------------------------------------------------------------------------
1. **Se comia las fichas maestras.** Llamaba a `a_registro(producto)` con un
   solo argumento. Mercadona y DIA tienen un segundo argumento, `maestro`, de
   donde salen el EAN, el origen, los ingredientes y los alergenos, porque esos
   datos no estan en la respuesta del listado sino en la ficha de cada producto,
   que se guarda aparte en data/master. Al reprocesar Mercadona del 17 de
   septiembre, el bronze paso de 4.317 EAN a 0, de 1.443 origenes a 0 y de 2.747
   listas de ingredientes a 0, y se escribio encima del bueno sin avisar. Una
   herramienta cuyo unico proposito es recuperar no puede destruir en silencio.

2. **No sabia reprocesar Carrefour ni DIA.** Las dos guardan HTML con extension
   .json.gz, y el extractor generico hacia `json.loads` y se rendia. O sea que
   el 42 % del catalogo (21.826 productos) no se podia reprocesar: cualquier
   mejora en esos dos parsers exigia volver a scrapear. Ahora cada colector
   puede declarar `productos_crudo(body)` y ellos dos ya la tienen.

Y una red de seguridad: si el bronze nuevo pierde datos que tenia el viejo, no
se escribe. Hay que pedirlo a proposito con --forzar.
"""
from __future__ import annotations

import argparse
import gzip
import importlib
import json
from datetime import date

import polars as pl

from core import config
from core.schemas import ESQUEMA_BRONZE
from core.storage import write_parquet


def _perdidas(nuevo: pl.DataFrame, camino) -> list[str]:
    """Columnas que el bronze viejo tenia llenas y el nuevo deja vacias."""
    if not camino.exists():
        return []
    try:
        viejo = pl.read_parquet(camino)
    except Exception:  # noqa: BLE001
        return []
    fuera = []
    for col in viejo.columns:
        antes = viejo[col].drop_nulls().len()
        if col not in nuevo.columns:
            if antes:
                fuera.append(f"{col}: {antes} -> falta la columna")
            continue
        ahora = nuevo[col].drop_nulls().len()
        # Un margen del 10 % absorbe que un dia el catalogo tenga menos
        # productos; una columna que se queda a cero o pierde la mitad, no.
        if antes and ahora < antes * 0.9:
            fuera.append(f"{col}: {antes} -> {ahora}")
    return fuera


def reprocesar(fuente: str, fecha: str | None = None, forzar: bool = False) -> int:
    mod = importlib.import_module(f"projects.cesta.collectors.{fuente}")
    # Las fichas maestras: sin esto, reprocesar borra el EAN, el origen, los
    # ingredientes y los alergenos de las cadenas que los publican aparte.
    cargar = getattr(mod, "_cargar_maestro", None)
    maestro = cargar() if cargar else None
    if maestro:
        print(f"  fichas maestras: {len(maestro)}")
    base = config.RAW / f"fuente={fuente}"
    if not base.exists():
        print(f"no hay crudo de {fuente}")
        return 1

    dias = [d for d in sorted(base.iterdir()) if d.is_dir()]
    if fecha:
        dias = [d for d in dias if d.name == f"fecha={fecha}"]

    total = 0
    for dia in dias:
        filas = []
        propio = getattr(mod, "productos_crudo", None)
        extraer = propio or _productos
        # Los nombres son content-addressed, no cronologicos. Procesar por mtime
        # garantiza que `keep="last"` conserve la captura mas reciente del dia.
        for f in sorted(dia.glob("*.json.gz"),
                        key=lambda p: (p.stat().st_mtime_ns, p.name)):
            crudo = gzip.decompress(f.read_bytes())
            if propio:
                datos = crudo
            else:
                try:
                    datos = json.loads(crudo)
                except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                    print(f"  aviso: {f.name} no contiene JSON valido: {exc}")
                    continue
            for producto in extraer(datos):
                # Dos pasadas a proposito: `a_registro` recibe la ficha DE ESE
                # producto, no el diccionario entero, y la clave (`id_fuente`)
                # la calcula el propio colector. Se le pregunta primero por ella
                # en vez de adivinar aqui como se llama el id en cada cadena.
                fila = mod.a_registro(producto)
                if maestro:
                    ficha = maestro.get(str(fila.get("id_fuente")))
                    if ficha:
                        fila = mod.a_registro(producto, ficha)
                filas.append(fila)
        if not filas:
            print(f"  {dia.name}: sin productos")
            continue
        df = pl.DataFrame(filas, schema_overrides=ESQUEMA_BRONZE)
        df = df.unique(subset=["fuente", "id_fuente"], keep="last")
        dia_fecha = date.fromisoformat(dia.name.split("=", 1)[1])
        destino = (config.DATA / "bronze" / f"fuente={fuente}"
                   / f"fecha={dia_fecha.isoformat()}" / "part.parquet")
        perdidas = _perdidas(df, destino)
        if perdidas and not forzar:
            print(f"  {dia.name}: NO se escribe, el bronze nuevo pierde datos:")
            for linea in perdidas:
                print(f"      {linea}")
            print("      (si es lo que quieres, repite con --forzar)")
            continue
        write_parquet(df, "bronze", fuente, day=dia_fecha)
        print(f"  {dia.name}: {len(df)} productos")
        total += len(df)
    print(f"reprocesadas {total} filas de {fuente}")
    return 0


def _productos(datos) -> list[dict]:
    """Saca la lista de productos de cualquiera de las respuestas guardadas."""
    if isinstance(datos, dict):
        if "categories" in datos:
            return [p for sub in datos["categories"] for p in sub.get("products", [])]
        if "products" in datos:
            return datos["products"]
        if "id" in datos and "price_instructions" in datos:
            return [datos]
    return []


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fuente", required=True)
    ap.add_argument("--fecha")
    ap.add_argument("--forzar", action="store_true",
                    help="escribe aunque el bronze nuevo pierda datos")
    raise SystemExit(reprocesar(**vars(ap.parse_args())))
