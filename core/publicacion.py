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

import hashlib
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
                # **COPIA, no enlace duro.** *Y esto era un defecto, medido el 12 de octubre de 2026.*
                #
                # La version anterior hacia `os.link` «para no duplicar un fichero de 195 MB».
                # *La premisa era falsa dos veces*: el fichero mayor son **19,2 MB** (no 195), y
                # **un enlace duro no aisla la version de lo que le pase al fichero suelto**.
                #
                # *Lo que se midio*: `fsutil hardlink list data\gold\precio_diario.parquet` devuelve
                # **tres nombres para un solo fichero** -- el suelto, `v20261007-103000` y
                # `v20261011-124542` --, y el enlace seguia **intacto**. Eso prueba que el pipeline
                # **reescribe los parquet in situ**: con un enlace, esa escritura **cambia el
                # contenido de una version ya publicada**. *De ahi que `v20261007-103000` se llame
                # 7 de octubre y su contenido sea del 11* -- *y que `/api/estado` lo delate con
                # `vigencia_precio.coherente=false`, que es lo unico que ha estado funcionando bien.*
                #
                # **Una version publicada tiene que ser inmutable por si misma, no por la buena
                # conducta de quien escriba el catalogo suelto.** *30 MB por version es el precio,
                # y es barato.*
                shutil.copy2(origen, destino / nombre)
        faltan = [n for n in exigidos if not (destino / n).exists()]
        if faltan:
            raise PublicacionIncompleta(f"faltan {', '.join(faltan)}: no se publica")
    except Exception:
        # **Nada a medias se queda**: si no se puede publicar, se retira la carpeta y el puntero
        # sigue donde estaba. Los lectores no ven ni un fichero de este intento.
        shutil.rmtree(destino, ignore_errors=True)
        raise

    # **El mismo instante en las dos mitades del sello.** La carpeta se llama `v<momento>` y el
    # puntero se sella con `publicado_en`: si uno lleva el `momento` y el otro la hora real, una
    # publicacion retrofechada queda **incoherente para `/api/estado`**, que compara las dos fechas.
    _mueve_puntero(version, exigidos, momento)
    return version


def _huella(camino: Path) -> str:
    """El SHA-256 de un fichero publicado. **Es lo que hace la coherencia demostrable.**

    Sin esto, «la version es coherente» se sostiene en que el nombre de la carpeta y la fecha del
    puntero digan lo mismo -- *y eso no prueba nada sobre el contenido*: el 12 de octubre de 2026 se
    midio una version llamada 7 de octubre **cuyo `precio_diario.parquet` era del 11**, porque un
    enlace duro la ataba al fichero suelto y el pipeline lo reescribio in situ.
    """
    h = hashlib.sha256()
    with camino.open("rb") as f:
        for trozo in iter(lambda: f.read(1 << 20), b""):
            h.update(trozo)
    return h.hexdigest()


def huellas(version: str | None = None) -> dict[str, str]:
    """La huella de cada fichero de una version, o de la publicada si no se dice cual."""
    elegida = version if version is not None else version_actual()
    if elegida is None:
        return {}
    carpeta = carpeta_de(elegida)
    return {n: _huella(carpeta / n) for n in FICHEROS if (carpeta / n).exists()}


def comprueba(version: str | None = None) -> dict[str, list[str]]:
    """**Contrasta el contenido publicado con lo que el puntero dice que se publico.**

    Devuelve `{"cambiados": [...], "ausentes": [...], "sin_huella": [...]}`. *Es la comprobacion que
    `/api/estado` no podia hacer con fechas*: una version puede tener el nombre correcto y el
    contenido de otra, y **eso solo se ve mirando los bytes**.
    """
    elegida = version if version is not None else version_actual()
    if elegida is None:
        return {"cambiados": [], "ausentes": [], "sin_huella": []}
    try:
        datos = json.loads(PUNTERO.read_text(encoding="utf-8"))
        guardadas = dict(datos.get("huellas") or {})
    except Exception:  # noqa: BLE001
        guardadas = {}
    carpeta = carpeta_de(elegida)
    cambiados, ausentes, sin_huella = [], [], []
    for n in FICHEROS:
        camino = carpeta / n
        if not camino.exists():
            ausentes.append(n)
        elif n not in guardadas:
            sin_huella.append(n)
        elif _huella(camino) != guardadas[n]:
            cambiados.append(n)
    return {"cambiados": cambiados, "ausentes": ausentes, "sin_huella": sin_huella}


def _mueve_puntero(version: str, ficheros: list[str],
                   momento: datetime | None = None) -> None:
    """Cambia el puntero de una vez. Un puntero a medias es peor que no tener version.

    `momento` es el mismo que nombra la carpeta, para que las dos fechas digan lo mismo. *Sin el,
    una publicacion retrofechada se veia incoherente: la carpeta en enero y el puntero en octubre.*
    Al **volver atras** (`fijar`) no se pasa: ahi lo que importa es **cuando se movio el puntero**,
    no cuando se publico la version a la que se vuelve.
    """
    datos = {"version_puntero": VERSION_PUNTERO, "version": version,
             "publicado_en": (momento or datetime.now()).isoformat(), "ficheros": ficheros,
             # **La huella de lo que se publico.** *Es lo que permite distinguir «esta version
             # cambio por debajo» de «la fecha no cuadra», que no son lo mismo.*
             "huellas": {n: _huella(carpeta_de(version) / n) for n in ficheros}}
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
