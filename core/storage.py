"""raw/ inmutable + parquet particionado estilo Hive."""
from __future__ import annotations

import gzip
import hashlib
import json
import os
from datetime import date, timedelta
from pathlib import Path

from core import config, peticiones

ROOT = config.DATA


# Capas que no se borran nunca. `raw` se puede tirar cuando caduca -- ocupa 338 MB
# por pasada y su unico trabajo es dejar reprocesar unas semanas --, pero bronze es
# el original tipado de cada dia y gold es lo que ve la aplicacion.
#
# Esto no es celo: el 18 de septiembre de 2026 se paso un dia entero creyendo que
# una particion de bronze se habia borrado sola. Resulto que la habian apartado a
# mano, a proposito y bien, pero la conjetura duro porque nada en el codigo decia
# que eso no pudiera pasar. Ahora lo dice.
CAPAS_INTOCABLES = ("bronze", "gold")


class BorradoProhibido(RuntimeError):
    pass


class EscrituraDePrueba(RuntimeError):
    pass


def comprueba_no_es_una_prueba(ruta: Path) -> None:
    """Una prueba no puede escribir en los datos de verdad. Nunca.

    El 21 de septiembre de 2026 `uv run pytest` **se cargo la captura de
    Carrefour del dia**: 16.560 productos reemplazados por 199 de mentira con
    la categoria "slug". Una prueba del colector llamaba a `main()`, `main()`
    daba la captura por completa y escribia su bronze, y el bronze que escribia
    era el de verdad, porque nadie habia dicho que no pudiera.

    Lo peor no es el fallo: es que estaba **escrito en las instrucciones**. El
    primer comando que se le pide a David antes de fiarse del dia es correr las
    pruebas, y correr las pruebas destruia el dia.

    Parchear esa prueba tapa este caso y deja la puerta abierta para la
    siguiente. Esto la cierra entera: bajo pytest, escribir dentro de la carpeta
    de datos real revienta. Una prueba que necesite escribir usa `tmp_path`, que
    es lo que tenia que haber hecho desde el principio.
    """
    if "PYTEST_CURRENT_TEST" not in os.environ:
        return
    ruta = Path(ruta).resolve()
    real = Path(config.RAIZ / "data").resolve()
    if ruta == real or real in ruta.parents:
        raise EscrituraDePrueba(
            f"una prueba ha intentado escribir en {ruta}, que son los datos de "
            f"verdad. Usa tmp_path y monkeypatch sobre config.DATA, o parchea "
            f"lo que escriba. Ver core/storage.comprueba_no_es_una_prueba.")


def comprueba_borrable(ruta: Path) -> None:
    """Revienta si la ruta cae dentro de una capa que no se borra."""
    ruta = Path(ruta).resolve()
    for capa in CAPAS_INTOCABLES:
        base = (ROOT / capa).resolve()
        if ruta == base or base in ruta.parents:
            raise BorradoProhibido(
                f"{ruta} esta dentro de '{capa}', que no se borra nunca. "
                f"Si la captura es mala, se **aparta**: storage.aparta(carpeta, "
                f"motivo) la mueve a data/debug/descartados con el motivo en el "
                f"nombre, y de ahi se puede recuperar. Ver docs/OPERACION.md.")


def aparta(carpeta: Path, motivo: str) -> Path:
    """Mueve una particion mala a `data/debug/descartados`, con el motivo escrito.

    Es lo que dice `docs/OPERACION.md` que hay que hacer con un bronze que no vale:
    apartarlo, no borrarlo. El nombre queda `<cadena>-<fecha>-<motivo>` y los
    controles del resumen lo leen de vuelta, asi que un dia apartado se distingue
    de un dia perdido de verdad.
    """
    carpeta = Path(carpeta)
    fuente = carpeta.parent.name.split("=", 1)[-1]
    fecha = carpeta.name.split("=", 1)[-1]
    limpio = "-".join(motivo.lower().split())
    destino = ROOT / "debug" / "descartados" / f"{fuente}-{fecha}-{limpio}"
    destino.parent.mkdir(parents=True, exist_ok=True)
    if destino.exists():
        raise FileExistsError(f"ya hay algo apartado en {destino}")
    carpeta.rename(destino)
    return destino


def save_raw(source: str, key: str, body: bytes, *, day: date | None = None) -> Path:
    """Guarda una respuesta sin sobrescribir capturas distintas del mismo endpoint.

    El nombre combina endpoint y contenido: repetir una respuesta exacta no duplica
    datos, pero una respuesta nueva el mismo dia queda preservada para reprocesar.
    """
    day = day or config.hoy_local()
    d = ROOT / "raw" / f"fuente={source}" / f"fecha={day.isoformat()}"
    comprueba_no_es_una_prueba(d)
    d.mkdir(parents=True, exist_ok=True)
    key_hash = hashlib.sha1(key.encode()).hexdigest()[:12]
    body_hash = hashlib.sha256(body).hexdigest()[:12]
    name = f"{key_hash}-{body_hash}"
    path = d / f"{name}.json.gz"
    if not path.exists():
        temporal = path.with_suffix(path.suffix + ".tmp")
        temporal.write_bytes(gzip.compress(body))
        temporal.replace(path)
    return path


def write_parquet(df, layer: str, source: str, *, day: date | None = None) -> Path:
    """df: polars.DataFrame. layer: bronze | silver | gold."""
    day = day or config.hoy_local()
    d = ROOT / layer / f"fuente={source}" / f"fecha={day.isoformat()}"
    d.mkdir(parents=True, exist_ok=True)
    path = d / "part.parquet"
    write_parquet_file(df, path)
    return path


def write_parquet_file(df, path: Path) -> Path:
    """Escribe en el mismo volumen y reemplaza solo cuando el fichero esta completo."""
    path = Path(path)
    comprueba_no_es_una_prueba(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporal = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        df.write_parquet(temporal)
        temporal.replace(path)
    finally:
        if temporal.exists():
            temporal.unlink()
    return path


def load_raw_bytes(source: str, key: str, *, day: date | None = None) -> bytes | None:
    """Ultima captura de hoy para reanudar una ejecucion interrumpida sin red."""
    day = day or config.hoy_local()
    d = ROOT / "raw" / f"fuente={source}" / f"fecha={day.isoformat()}"
    if not d.exists():
        return None
    key_hash = hashlib.sha1(key.encode()).hexdigest()[:12]
    candidatos = sorted(
        d.glob(f"{key_hash}-*.json.gz"),
        key=lambda p: (p.stat().st_mtime_ns, p.name),
    )
    if not candidatos:
        return None
    # Se sirve de la copia guardada: **no hay peticion**. Sin contarlo, "menos peticiones" no
    # distingue ahorro de averia. Ver `core/peticiones.py`.
    peticiones.de_cache(source)
    return gzip.decompress(candidatos[-1].read_bytes())


def load_raw_reciente(source: str, key: str, dias: int = 10) -> tuple[bytes, date] | None:
    """La captura mas reciente de esa clave, sea de hoy o de dias anteriores.

    Para lo que no cambia de un dia para otro. El 11 y el 12 de sep Carrefour
    devolvio HTTP 403 al pedir su sitemap de categorias, y como sin categorias no
    hay recorrido, se perdio el catalogo ENTERO de esos dos dias -- por un indice
    de secciones que es practicamente el mismo todas las semanas. Teniendolo de
    ayer, un 403 pasa de tirar el dia a no ser nada.
    """
    hoy = config.hoy_local()
    for atras in range(dias + 1):
        dia = hoy - timedelta(days=atras)
        cuerpo = load_raw_bytes(source, key, day=dia)
        if cuerpo is not None:
            return cuerpo, dia
    return None


def load_raw(path: Path) -> dict:
    return json.loads(gzip.decompress(Path(path).read_bytes()))
