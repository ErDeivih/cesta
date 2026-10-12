"""Copia de seguridad y restauracion, en un entorno separado, comprobando su contenido.

**Por que existe.** No habia nada: ni un `pg_dump`, ni una restauracion, ni una comprobacion sobre la base
restaurada. Una copia que nunca se ha restaurado no es una copia: es un fichero del que se supone algo.

**Lo que hace, y en este orden:**

  1. levanta un PostgreSQL desechable en el **5434** y corre el ensayo de punta a punta -- que deja datos de
     verdad: listas, lineas, una compra y, sobre todo, **una sustitucion confirmada con su producto y su
     cadena**;
  2. **vuelca** esa base con `pg_dump`;
  3. levanta un **entorno separado** -- otro contenedor, el **5435**, otra base -- y **restaura** el volcado;
  4. **comprueba el contenido** en el entorno restaurado: las filas estan, y **la confirmacion conserva su
     producto y su cadena**;
  5. y recoge los dos contenedores.

**Lo que NO hace:** no toca la base de casa, **ni la de pruebas**. El contenedor de casa no publica su
5432, y esta prueba usa **nombres y puertos propios** -- `cesta-copia-ensayo` en el `5436` y
`cesta-copia-db` en el `5437` --, *asi que se puede correr con la base de pruebas en pie.*

    uv run python -m plataforma.prueba_copia
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

# **Nombres y puertos PROPIOS, y esto era un defecto.** *Antes el ensayo se llamaba `cesta-prueba-db` y
# usaba el `5434` -- que es **el contenedor que ya existe** y que sostiene la suite de `pytest`.* Y el guion
# **empieza y termina con `docker rm -f` de ese nombre**, asi que correrlo dejaba la base de pruebas **en
# blanco**: *un volumen nuevo y vacio, y los 716 usuarios que tenia en un volumen que ya nadie monta.*
#
# *Medido el 12 de octubre de 2026, antes de decidir si se corria.* **Y no se corrio precisamente por
# eso** -- *un guion que se lleva por delante el entorno de los demas no es autocontenido: es invasivo.*
#
# *Con nombres propios si es lo que dice ser*: **hace su base, la usa y la retira, sin tocar la de
# nadie.** *Los puertos, al 5436 y al 5437, que no los usa nada mas.*
ENSAYO = "cesta-copia-ensayo"
COPIA = "cesta-copia-db"
PUERTO_ENSAYO = "127.0.0.1:5436:5432"
PUERTO_COPIA = "127.0.0.1:5437:5432"
# **En `data/`, que esta ignorado**: un volcado de una base desechable en la raiz del
# repositorio es basura, y de la que parece una copia de verdad.
VOLCADO = "data/copia-de-cesta.sql"
FALLOS: list[str] = []


def corre_env(args, timeout=2400, entrada=None, cwd=None, env=None):
    """Como `corre`, pero **con un entorno puesto**. *Es lo que permite que el ensayo apunte a la base de
    esta prueba y no a la que tenga el entorno de quien la lance.*"""
    return subprocess.run(args, capture_output=True, timeout=timeout, input=entrada, cwd=cwd, env=env)


def corre(args, timeout=2400, entrada=None, cwd=None):
    # **`cwd` hace falta de verdad**: el ensayo tiene que correr desde la raiz del proyecto. Sin este parametro
    # el guion se cae en el primer paso con un `TypeError`, que es como se supo (primera ejecucion).
    return subprocess.run(args, capture_output=True, timeout=timeout, input=entrada, cwd=cwd)


def texto(r) -> str:
    return (r.stdout or b"").decode("utf-8", "replace") + (r.stderr or b"").decode("utf-8", "replace")


def arranca(nombre: str, puertos: str) -> bool:
    corre(["docker", "rm", "-f", nombre], timeout=120)
    r = corre(["docker", "run", "--rm", "-d", "--name", nombre,
               "-e", "POSTGRES_PASSWORD=prueba", "-e", "POSTGRES_USER=cesta", "-e", "POSTGRES_DB=cesta",
               "-p", puertos, "postgres:16-alpine"], timeout=300)
    if r.returncode != 0:
        print("   no se pudo arrancar:", texto(r)[:200])
        return False
    for _ in range(30):
        time.sleep(2)
        if corre(["docker", "exec", nombre, "pg_isready", "-U", "cesta"], timeout=60).returncode == 0:
            return True
    return False


def consulta(contenedor: str, sql: str) -> str:
    r = corre(["docker", "exec", contenedor, "psql", "-U", "cesta", "-d", "cesta", "-tAc", sql], timeout=120)
    return texto(r).strip()


def revisa(nombre: str, valor, esperado) -> None:
    if valor != esperado:
        FALLOS.append(nombre)
        print(f"   FALLO: {nombre} -> {valor!r}, se esperaba {esperado!r}")
    else:
        print(f"   {nombre}: {valor}")


def main() -> int:
    print("== copia de seguridad y restauracion, en un entorno separado")
    print("\n-- 1. el ensayo, que deja datos de verdad")
    if not arranca(ENSAYO, PUERTO_ENSAYO):
        print("   no hay base de ensayo: se para")
        return 1
    print(f"   base de ensayo lista en el {PUERTO_ENSAYO.split(':')[1]}")
    # **La raiz del proyecto, sin adivinar separadores.** Partir `__file__` por barras funciona en Linux y
    # en Windows no: `pathlib` sabe cual toca. Se importa aqui, junto a su uso, para no tocar la cabecera.
    import pathlib

    raiz = str(pathlib.Path(__file__).resolve().parents[1])
    # **Y EL ENSAYO TIENE QUE APUNTAR A *ESTA* BASE, que es el defecto que esto arregla.**
    #
    # *Medido el 12 de octubre de 2026, al correrlo por primera vez:* **el ensayo heredaba el
    # `CESTA_POSTGRES` de quien lo lanzaba** -- *que apuntaba a la base de pruebas, en el `5434`* --,
    # **mientras `pg_dump` volcaba el contenedor nuevo**, vacio. *Resultado: **un volcado de 643 bytes**,
    # o sea la cabecera y nada mas.*
    #
    # *Y funcionaba antes **solo porque** el nombre y el puerto coincidian por casualidad con lo que el
    # entorno tenia puesto.* **Un guion que depende de que el entorno apunte donde el cree es un guion que
    # se rompe el dia que alguien cambia el entorno** -- *y encima se rompe en silencio, con un volcado
    # vacio que parece un volcado.*
    #
    # *Lo cazo la guarda de los 1000 bytes*, que ya estaba escrita: **«si el volcado tiene menos de 1000
    # bytes, no se sigue»**. *Sin ella, se habria restaurado una base vacia y las comprobaciones de
    # contenido habrian fallado una a una sin decir por que.*
    entorno = {**os.environ, "CESTA_POSTGRES": f"postgresql://cesta:prueba@127.0.0.1:{PUERTO_ENSAYO.split(':')[1]}/cesta"}
    e = corre_env(["uv", "run", "python", "-m", "plataforma.prueba_e2e"], cwd=raiz, env=entorno)
    if e.returncode != 0:
        FALLOS.append("el ensayo")
        print("   FALLO: el ensayo no pasa; sin datos buenos no se prueba la copia")
        print(texto(e)[-800:])
        corre(["docker", "rm", "-f", ENSAYO], timeout=120)
        return 1
    print("   el ensayo pasa y deja sus datos")

    print("\n-- 2. el volcado")
    r = corre(["docker", "exec", ENSAYO, "pg_dump", "-U", "cesta", "-d", "cesta"], timeout=600)
    volcado = r.stdout or b""
    print(f"   pg_dump devuelve {len(volcado)} bytes")
    if r.returncode != 0 or len(volcado) < 1000:
        FALLOS.append("el volcado")
        print("   FALLO:", texto(r)[-400:])
        corre(["docker", "rm", "-f", ENSAYO], timeout=120)
        return 1
    with open(VOLCADO, "wb") as f:
        f.write(volcado)
    print(f"   guardado en {VOLCADO}")

    print("\n-- 3. el entorno separado: otro contenedor, otra base")
    if not arranca(COPIA, PUERTO_COPIA):
        FALLOS.append("el entorno separado")
        corre(["docker", "rm", "-f", ENSAYO], timeout=120)
        return 1
    print(f"   base separada lista en el {PUERTO_COPIA.split(':')[1]}")
    r = corre(["docker", "exec", "-i", COPIA, "psql", "-U", "cesta", "-d", "cesta",
               "-v", "ON_ERROR_STOP=1"], timeout=900, entrada=volcado)
    if r.returncode != 0:
        FALLOS.append("la restauracion")
        print("   FALLO en la restauracion:", texto(r)[-600:])
    else:
        print("   restaurado sin error")

    print("\n-- 4. el contenido, en el entorno restaurado")
    for tabla in ("lista", "lista_linea", "compra"):
        en_ensayo = consulta(ENSAYO, f"SELECT count(*) FROM {tabla}")
        en_copia = consulta(COPIA, f"SELECT count(*) FROM {tabla}")
        print(f"   {tabla}: {en_ensayo} en el ensayo, {en_copia} en la copia")
        if not en_ensayo or en_ensayo != en_copia:
            FALLOS.append(f"las filas de {tabla}")
            print(f"   FALLO: {tabla} no cuadra entre el original y la copia")

    # **Y lo que importa de esta sesion**: la sustitucion confirmada conserva su producto y su cadena.
    sql = ("SELECT autorizado_producto || '|' || autorizado_cadena FROM lista_linea"
           " WHERE autorizado IS TRUE LIMIT 1")
    confirmada = consulta(COPIA, sql)
    revisa("la confirmacion restaurada (producto|cadena)", confirmada, "dia:74397|dia")

    print("\n-- 5. recoger")
    for nombre in (ENSAYO, COPIA):
        corre(["docker", "rm", "-f", nombre], timeout=120)
        print(f"   {nombre}: retirado")

    # Y el volcado se retira: era para comprobar que se restaura, no para guardarlo.
    Path(VOLCADO).unlink(missing_ok=True)
    print(f"\n== {'TODO BIEN' if not FALLOS else str(len(FALLOS)) + ' FALLO(S)'}")
    return 1 if FALLOS else 0


if __name__ == "__main__":
    sys.exit(main())
