"""Respalda las dos SQLite de la casa **desde el volumen**, y **de forma consistente**.

**Por que existe.** *`plataforma/respaldar.bat` declara: *** «**Es lo UNICO que hay que respaldar.**» *** *
*-- *refiriendose a PostgreSQL.* **Y no lo es**: *el `recetas.sqlite` y el `diario.sqlite` **no son crudo ni
se recalculan** -- *son **lo que la casa ha escrito*** --, *y el propio `docker-compose.yml:60-66` lo dice **y
avisa de que el respaldo no los ve**: *** «`robocopy data\\raw` **no los ve**». ***

**Las tres decisiones que hacen que esto sirva, y no solo que exista:**

  1. *** SE RESPALDA EL VOLUMEN, no el fichero del host. *** *No son el mismo: *el compose explica por que
     **no** es un `bind` a `../data` -- *«ahi ya escribe el pipeline, y dos escritores sobre el mismo fichero
     es justo lo que el `ro` de arriba evita»* --, *asi que **`data/recetas.sqlite` del host no es el que la
     web usa.** *
  2. *** SE COPIA CON `VACUUM INTO`, no con `copy`. *** *Una SQLite **abierta y escribiendose** copiada a
     mano **puede salir a medias**, *y un respaldo **que parece un respaldo y no lo es** es **peor que no
     tenerlo**, *porque alguien confiaria en el.* `VACUUM INTO` da una copia **coherente aunque haya
     escrituras** -- *y el contenedor tiene SQLite 3.46.1, que lo soporta (pide >= 3.27).*
  3. *** Y SE SOPORTA QUE EL FICHERO NO EXISTA. *** *El `diario.sqlite` **se crea al primer apunte**: *en el
     volumen puede no estar todavia, *y eso **no es un fallo** -- *es un diario en el que nadie ha escrito.*
     *Lo que **no** se hace es inventar un fichero vacio para que la copia «salga»: *eso diria que hay un
     diario, *y no lo hay.*

*Y el destino es el mismo `data/respaldos` que usa el respaldo de PostgreSQL, con el mismo sello de tiempo.*
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# *Las dos, y por que cada una.* **Y son las dos que la casa escribe**: *el recetario (Recetas) y el diario
# (lo que cada uno ha comido).*
BASES = ("recetas.sqlite", "diario.sqlite")

# *Donde viven dentro del contenedor: el volumen `datos_api` esta montado en `/app/data`.*
DENTRO = "/app/data"
SERVICIO = "api"


def _compose(*args: str) -> subprocess.CompletedProcess:
    """*Desde `plataforma/`, que es donde esta el `docker-compose.yml`.*"""
    return subprocess.run(
        ["docker", "compose", *args],
        cwd=str(Path(__file__).resolve().parents[1] / "plataforma"),
        capture_output=True, check=False)


def respalda(bases=BASES, destino: Path | None = None) -> list[dict]:
    """**Una copia coherente por cada base que exista.** *Y de la que no exista, se dice.*

    *El orden importa*: *`VACUUM INTO` **dentro** del contenedor -- *alli la base se abre y se cierra sola* --,
    *y **despues** se saca el fichero.* *Copiar primero y compactar despues seria copiar el fichero abierto.*
    """
    destino = destino or (Path(__file__).resolve().parents[1] / "data" / "respaldos")
    destino.mkdir(parents=True, exist_ok=True)
    hechas: list[dict] = []
    for base in bases:
        # *Existe?* **Y si no, se dice y se sigue**: *no todos los ficheros tienen por que existir.*
        hay = _compose("exec", "-T", SERVICIO, "test", "-f", f"{DENTRO}/{base}")
        if hay.returncode != 0:
            hechas.append({"base": base, "estado": "no_existe",
                           "nota": "no esta en el volumen: se crea al primer uso, y no se inventa"})
            continue
        temporal = f"/tmp/{base}.copia"
        # *** `VACUUM INTO` y no `copy`: la copia tiene que ser coherente con la base ABIERTA. *** *
        copia = _compose("exec", "-T", SERVICIO, "python", "-c",
                         "import sqlite3,sys;"
                         f"c=sqlite3.connect('{DENTRO}/{base}');"
                         f"c.execute(\"VACUUM INTO '{temporal}'\");"
                         "c.close()")
        if copia.returncode != 0:
            hechas.append({"base": base, "estado": "fallo",
                           "nota": copia.stderr.decode(errors="replace").strip()[:200]})
            continue
        # *Y se saca del contenedor con `cp`, que es la via del propio compose.*
        saca = _compose("cp", f"{SERVICIO}:{temporal}", str(destino / base))
        _compose("exec", "-T", SERVICIO, "rm", "-f", temporal)
        if saca.returncode != 0:
            hechas.append({"base": base, "estado": "fallo",
                           "nota": saca.stderr.decode(errors="replace").strip()[:200]})
            continue
        hechas.append({"base": base, "estado": "copiada",
                       "bytes": (destino / base).stat().st_size})
    return hechas


def _cli() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--destino", type=Path, default=None)
    a = ap.parse_args()
    for uno in respalda(destino=a.destino):
        if uno["estado"] == "copiada":
            print(f"  {uno['base']}: copiada, {uno['bytes']} bytes")
        else:
            print(f"  {uno['base']}: {uno['estado']} -- {uno['nota']}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(_cli())
