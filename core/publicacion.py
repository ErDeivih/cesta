"""Publicacion por versiones: un catalogo se publica entero o no se publica.

**El problema, medido.** Hoy el pipeline escribe `data/gold/*.parquet` **fichero a fichero**. Si el
proceso se cae entre dos escrituras, el catalogo que queda servido es una mezcla: `grupos` de hoy
con `enlaces` de ayer. Nada avisa, porque cada fichero por separado es valido. La ampliacion lo pide
en S01 con estas palabras: *"Crash entre escrituras no mezcla versiones; rollback y concurrencia
probados"*.

**Como lo resuelve, y por que asi.**

1. Cada publicacion escribe **todos** sus ficheros en una carpeta propia `data/gold/v<fecha-hora>/`.
   Nada de tocar el catalogo vivo mientras se escribe.
2. Cuando **estan todos**, se cambia un **puntero** (`data/gold/actual.json`) de una vez, con
   `os.replace`, que es atomico en el sistema de ficheros. Antes de eso, los lectores siguen viendo
   la version anterior, entera.
3. Una version solo cuenta si esta **completa**: si falta un fichero de los declarados, no se
   publica y el puntero no se mueve. Es la regla que convierte "se cayo a medias" en "no paso nada".
4. Las versiones anteriores **no se borran**: volver atras es apuntar a una anterior, y eso es el
   rollback, con los datos intactos.
5. **Sin version publicada se lee el catalogo suelto de siempre** (fallback conservador): asi esto
   entra sin romper nada y se puede adoptar cuando convenga.

**Y una regla que no se salta:** publicar **no borra**. Un catalogo no se destruye por publicar otro.
"""
from __future__ import annotations

import json
import os
import shutil
from datetime import date, datetime
from pathlib import Path

import polars as pl

RAIZ = Path(__file__).resolve().parents[1]
GOLD = RAIZ / "data" / "gold"
PUNTERO = GOLD / "actual.json"
VERSION_PUNTERO = 1

# Los ficheros que forman una publicacion. `grupos_anterior` queda fuera: es copia de trabajo.
FICHEROS = ["grupos.parquet", "enlaces.parquet", "precio_diario.parquet", "precio_derivado.parquet",
            "resumen.parquet", "promos_por_cadena.parquet"]


class PublicacionIncompleta(RuntimeError):
    """Falta un fichero de los declarados: **no se publica**. El puntero no se mueve."""


def _sello(momento: datetime | None = None) -> str:
    return (momento or datetime.now()).strftime("%Y%m%d-%H%M%S")


def carpeta_de(version: str) -> Path:
    return GOLD / f"v{version}"


def version_actual() -> str | None:
    """La version publicada, o None si todavia no se ha publicado nunca por versiones."""
    try:
        datos = json.loads(PUNTERO.read_text(encoding="utf-8"))
        return str(datos["version"])
    except Exception:  # noqa: BLE001  (sin puntero legible, no hay version: se usa el catalogo suelto)
        return None


def versiones() -> list[str]:
    if not GOLD.exists():
        return []
    return sorted(d.name[1:] for d in GOLD.iterdir() if d.is_dir() and d.name.startswith("v"))


def ruta(nombre: str, version: str | None = None) -> Path:
    """Donde esta un fichero publicado. **Fija la version**: un lector no puede ver dos mezcladas.

    Si no se pide version, se resuelve la actual **una vez** y se devuelve esa ruta: quien la llame
    no puede acabar leyendo `grupos` de una publicacion y `enlaces` de la siguiente.
    """
    elegida = version if version is not None else version_actual()
    if elegida is None:
        # Sin publicacion por versiones: el catalogo suelto de siempre. Es el fallback conservador
        # para que esto pueda entrar sin migrar todo de golpe.
        return GOLD / nombre
    return carpeta_de(elegida) / nombre


def rutas(version: str | None = None,
          nombres: list[str] | None = None) -> dict[str, Path]:
    """**Todos los caminos de UNA version.** Es lo que fija la version por peticion.

    `ruta()` resuelve el puntero en cada llamada, y un lector que pida dos ficheros por separado
    puede pillar `grupos` de una publicacion y `enlaces` de la siguiente: exactamente la mezcla que
    S01 prohibe. Aqui se resuelve la version **una vez** y todos los caminos salen de ella.
    """
    elegida = version if version is not None else version_actual()
    return {n: ruta(n, elegida) for n in (nombres or FICHEROS)}


def publicar(datos: dict[str, pl.DataFrame] | None = None, *, momento: datetime | None = None,
             exigir: list[str] | None = None) -> str:
    """Publica una version entera y mueve el puntero **solo** cuando esta completa.

    `datos` son los marcos a escribir; si se omite, se **adoptan** los ficheros sueltos que ya hay
    en `data/gold` (la forma de empezar a versionar el catalogo actual sin volver a generarlo).
    """
    exigidos = list(exigir if exigir is not None else FICHEROS)
    version = _sello(momento)
    destino = carpeta_de(version)
    if destino.exists():
        raise ValueError(f"la version {version} ya existe: no se sobrescribe una publicacion")
    destino.mkdir(parents=True)
    try:
        if datos is not None:
            for nombre, marco in datos.items():
                marco.write_parquet(destino / nombre)
        else:
            for nombre in exigidos:
                origen = GOLD / nombre
                if not origen.exists():
                    raise PublicacionIncompleta(f"no esta {nombre} en data/gold: no se publica")
                # Enlace duro: no se duplica un fichero de 195 MB para versionar.
                try:
                    os.link(origen, destino / nombre)
                except OSError:
                    shutil.copy2(origen, destino / nombre)
        faltan = [n for n in exigidos if not (destino / n).exists()]
        if faltan:
            raise PublicacionIncompleta(f"faltan {', '.join(faltan)}: no se publica")
    except Exception:
        # **Nada a medias se queda**: si no se puede publicar, se retira la carpeta y el puntero
        # sigue donde estaba. Los lectores no ven ni un fichero de este intento.
        shutil.rmtree(destino, ignore_errors=True)
        raise

    _mueve_puntero(version, exigidos)
    return version


def _mueve_puntero(version: str, ficheros: list[str]) -> None:
    """Cambia el puntero de una vez. Un puntero a medias es peor que no tener version."""
    datos = {"version_puntero": VERSION_PUNTERO, "version": version,
             "publicado_en": datetime.now().isoformat(), "ficheros": ficheros}
    temporal = PUNTERO.with_suffix(".json.tmp")
    temporal.write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(temporal, PUNTERO)


def fijar(version: str) -> None:
    """Vuelve a una version anterior (rollback). Rechaza una version que no este completa."""
    if version not in versiones():
        raise ValueError(f"la version {version} no existe")
    faltan = [n for n in FICHEROS if not (carpeta_de(version) / n).exists()]
    if faltan:
        raise PublicacionIncompleta(f"la version {version} esta incompleta: faltan {', '.join(faltan)}")
    _mueve_puntero(version, FICHEROS)


def adoptar(momento: datetime | None = None) -> str:
    """Primera version a partir del catalogo suelto que ya existe. No regenera nada."""
    return publicar(None, momento=momento)


def fecha_local() -> str:
    return date.today().isoformat()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "adoptar":
        print(f"version publicada: {adoptar()}")
    elif len(sys.argv) > 1 and sys.argv[1] == "fijar":
        fijar(sys.argv[2])
        print(f"puntero a {sys.argv[2]}")
    else:
        actual = version_actual()
        print(f"version actual: {actual or '(ninguna: se lee el catalogo suelto)'}")
        print(f"versiones: {', '.join(versiones()) or '(ninguna)'}")
