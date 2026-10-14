"""Ensayo de restauracion en un destino NUEVO y desechable, con guardas por delante.

**Por que existe.** *La restauracion de las copias **no se habia ejercido nunca*** -- *y por eso figuraba
como limitacion en el dictamen de B16.* **Y no se puede ejercer sobre casa**: *el encargo lo prohibe con
nombre propio.*

**Y lo primero que se hizo fue auditar el guion que ya existe** (`plataforma/respaldar.bat`), *como el
complemento del 14/10 manda: «no ejecutar el guion actual a ciegas: auditar sus eliminaciones y
subprocesos primero».* *Y la auditoria encontro que **ese guion no sirve para esto**: *
```
*** esta CABLEADO al servicio `db` ***  *-- *`docker compose exec -T db` es literal*
*** y su primer acto es `DROP SCHEMA public CASCADE` *** *
*** y `db` es LA BASE DE CASA ***  *-- *`POSTGRES_DB: cesta`, volumen `datos_db`, `127.0.0.1:5432`*
*** -> ejecutarlo «para probar» ES la restauracion destructiva que el encargo prohibe *** *
```

**Asi que el ensayo trae su propio destino, y su propio DSN.** *Y lo que este fichero hace **primero** no
es restaurar: es **decidir si se puede**, y negarse si no.*

**Las guardas, y cada una contra un accidente concreto:**

  1. *** El puerto *** *nunca es **5432** (casa), **5433** (facylf, ajeno) ni **5434** (pruebas compartidas).
     *Se comprueba **por numero**, y la lista es una constante con nombre.*
  2. *** El nombre *** *lleva **un prefijo propio** (`cesta-restauro-`) y **un sufijo unico**.
     *Un nombre constante podria pertenecer a otro trabajo; *uno unico, no.*
  3. *** La etiqueta de propiedad *** *-- `cesta.ensayo=restauracion` -- *es lo que permite **limpiar solo
     lo que es mio**: *si un recurso no la lleva, **no se toca**, aunque se llame parecido.*
  4. *** La identidad se comprueba ANTES de cualquier DDL *** *-- *y no despues: *lo que se verifica en el
     momento de borrar **ya se ha borrado**.*
  5. *** Y la base de datos *** *tiene que **existir y estar vacia**: *una base con tablas **no es un destino
     desechable**, es una base con datos de alguien.*

*La regla que las resume, y que es la de todo el proyecto: **lo que no se pueda acreditar como propio, no
se toca.** *
"""
from __future__ import annotations

import argparse
import socket
import subprocess
import sys
import uuid
from pathlib import Path

# **Los puertos que NO se pueden tocar, y por que cada uno.** *La lista es una constante para que se lea
# entera en un sitio: si estuvieran repartidos en condiciones, anadir uno se olvidaria en algun camino.*
PUERTOS_PROHIBIDOS = {
    5432: "la base de casa (`datos_db`)",
    5433: "facylf, que es AJENO y no se toca",
    5434: "la base de pruebas compartida",
}

# *Las bases cuyo NOMBRE no se puede reutilizar, aunque el puerto sea otro: un contenedor vecino puede
# publicar en un puerto libre y seguir siendo el de casa.*
NOMBRES_PROHIBIDOS = ("cesta-db-1", "facylf-postgres", "cesta-prueba-db")

PREFIJO = "cesta-restauro-"
ETIQUETA = "cesta.ensayo=restauracion"


class DestinoNoSeguro(RuntimeError):
    """**El ensayo se niega.** *No es un fallo del ensayo: es el ensayo haciendo su trabajo.*"""


def puerto_libre() -> int:
    """Un puerto que el sistema acaba de ceder, **fuera de los prohibidos**.

    *Y se comprueba igualmente*: *el sistema **no sabe** que 5432 es casa, asi que puede cederlo si esta
    libre. *Confiar en que «un puerto efimero no sera 5432» es confiar en una coincidencia.*
    """
    for _ in range(50):
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            puerto = s.getsockname()[1]
        if puerto not in PUERTOS_PROHIBIDOS:
            return puerto
    raise DestinoNoSeguro("no se encontro un puerto libre fuera de los prohibidos")


def nombre_unico() -> str:
    """*Nombre con **prefijo propio** y **sufijo unico**: *ni constante, ni parecido a otro trabajo.*"""
    return f"{PREFIJO}{uuid.uuid4().hex[:12]}"


def comprueba_nombre(nombre: str) -> None:
    """**Antes de crear nada**: *que el nombre sea de este ensayo.*"""
    if nombre in NOMBRES_PROHIBIDOS:
        raise DestinoNoSeguro(f"«{nombre}» es un contenedor que NO es de este ensayo")
    if not nombre.startswith(PREFIJO):
        raise DestinoNoSeguro(
            f"«{nombre}» no lleva el prefijo «{PREFIJO}» de este ensayo: "
            "un nombre sin prefijo podria pertenecer a otro trabajo")


def comprueba_puerto(puerto: int) -> None:
    """**Antes de publicar nada**: *que el puerto no sea de nadie.*"""
    if puerto in PUERTOS_PROHIBIDOS:
        raise DestinoNoSeguro(
            f"el puerto {puerto} es {PUERTOS_PROHIBIDOS[puerto]}: el ensayo no lo toca")


def comprueba_dsn(dsn: str) -> None:
    """**Antes de cualquier DDL**, sobre el DSN que el ensayo se ha construido.

    *Y se comprueba **el DSN y no la intencion**: *entre decir «voy a usar el 55001» y **usarlo** caben
    muchas lineas, *y **una de ellas puede cambiar el DSN.** *
    """
    from urllib.parse import urlparse

    trozo = urlparse(dsn)
    try:
        puerto = trozo.port
    except ValueError as fallo:  # pragma: no cover - *un puerto no numerico no deberia llegar aqui*
        raise DestinoNoSeguro(f"el DSN no declara un puerto legible: {fallo}") from fallo
    if puerto is None:
        raise DestinoNoSeguro("el DSN no declara puerto")
    comprueba_puerto(puerto)
    if trozo.hostname not in ("127.0.0.1", "localhost"):
        raise DestinoNoSeguro(
            f"el destino tiene que ser loopback, y es «{trozo.hostname}»: "
            "el encargo prohibe publicar nada")
    if not trozo.path or trozo.path in ("/", ""):
        raise DestinoNoSeguro("el DSN no nombra una base")


def comprueba_base_vacia(cur) -> None:
    """**La base tiene que existir y estar VACIA.** *Y era **una regla escrita y no comprobada*** hasta
    que se escribio esta funcion: *el docstring la pedia desde el principio y **nadie la ejecutaba.** *

    *Una base **con tablas** no es un destino desechable: *es **una base con datos de alguien**, *y
    restaurar encima de ella **sobrescribe lo que hubiera** -- *que es exactamente lo que el encargo
    prohibe.*

    *Y se pregunta por `information_schema.tables` **filtrando por `public`**: *es el esquema que el guion
    viejo borraba, asi que es **el que hay que saber si tiene algo.** *
    """
    cur.execute(
        "SELECT count(*) FROM information_schema.tables "
        "WHERE table_schema = 'public' AND table_type = 'BASE TABLE'")
    fila = cur.fetchone()
    cuantas = int((fila[0] if isinstance(fila, (list, tuple)) else fila) or 0)
    if cuantas:
        raise DestinoNoSeguro(
            f"la base tiene {cuantas} tablas: NO es un destino desechable, es una base con datos de "
            "alguien -- y restaurar encima sobrescribe lo que hubiera")


def contenedores_con_etiqueta() -> list[str]:
    """**Solo los que llevan LA etiqueta del ensayo.** *Es lo que autoriza a borrarlos.*

    *Si un contenedor no la lleva, **no es mio**, aunque su nombre empiece por el prefijo: *el prefijo lo
    puede escribir cualquiera; **la etiqueta la pone este ensayo al crear.** *
    """
    salida = subprocess.run(
        ["docker", "ps", "-a", "--filter", f"label={ETIQUETA}", "--format", "{{.Names}}"],
        capture_output=True, text=True, check=False)
    if salida.returncode != 0:
        raise DestinoNoSeguro(
            f"no se pudo preguntar a Docker por la etiqueta «{ETIQUETA}»: {salida.stderr.strip()}")
    return [linea.strip() for linea in salida.stdout.splitlines() if linea.strip()]


def limpia_lo_propio(nombre: str | None = None) -> list[str]:
    """**Borra lo que lleva la etiqueta**, y nada mas. *Y lo dice.*

    *Y si se le pasa un `nombre`, **solo lo borra si esta en la lista de los etiquetados**: *asi el
    ensayo no puede borrar un contenedor que **no creo**, aunque se llame igual que el suyo.*
    """
    propios = contenedores_con_etiqueta()
    if nombre is not None:
        if nombre not in propios:
            raise DestinoNoSeguro(
                f"«{nombre}» NO lleva la etiqueta «{ETIQUETA}»: no lo ha creado este ensayo, "
                "asi que no se borra")
        propios = [nombre]
    borrados: list[str] = []
    for uno in propios:
        # *`-v` para llevarse tambien su volumen: **es suyo, y lo creo el mismo.** *
        subprocess.run(["docker", "rm", "-f", "-v", uno], capture_output=True, text=True, check=False)
        borrados.append(uno)
    return borrados


def _docker(*args: str, entrada: bytes | None = None) -> subprocess.CompletedProcess:
    """*Un solo sitio por donde sale lo que se ejecuta, para poder leerlo entero.*"""
    return subprocess.run(["docker", *args], input=entrada, capture_output=True, check=False)


def _espera(cur, limite_s: int = 60) -> None:
    """*Y se espera a que la base **conteste**, no a que el contenedor exista.*"""
    import time

    for _ in range(limite_s):
        try:
            cur.execute("SELECT 1")
            return
        except Exception:  # noqa: BLE001  - *mientras arranca, cualquier fallo es «todavia no»*
            time.sleep(1)
    raise DestinoNoSeguro(f"la base no contesto en {limite_s} s")


def _conecta(dsn: str, limite_s: int = 90):
    """**Espera a que la BASE conteste, no a que el contenedor exista.**

    *Y esto es un arreglo medido, no una precaucion*: *el ensayo corrio entero por primera vez, el
    contenedor dijo *** `Up Less than a second` *** -- *o sea **arrancado** --, y `psycopg.connect`
    **revento**: *** «server closed the connection unexpectedly» ***.* *Porque **`Up` es el contenedor y
    no la base**: *PostgreSQL **tarda un poco mas** en aceptar conexiones, *y en ese hueco **la puerta esta
    abierta y nadie atiende.** *

    *Asi que **la espera envuelve la conexion**, *y no un `SELECT` posterior: *reintentar **conectar** es
    lo unico que cubre ese hueco.* *Y si se agota, **se dice cuanto se espero**, *en vez de dejar un error
    de red que parece otra cosa.* *
    """
    import time

    import psycopg

    ultimo: Exception | None = None
    for _ in range(limite_s):
        try:
            return psycopg.connect(dsn, connect_timeout=5)
        except Exception as fallo:  # noqa: BLE001  - *mientras arranca, cualquier fallo es «todavia no»*
            ultimo = fallo
            time.sleep(1)
    raise DestinoNoSeguro(f"la base del ensayo no acepto la conexion en {limite_s} s: {ultimo}")


def restaura_las_sqlite(destino=None, sello: str = "") -> list[dict]:
    """*** LA SEGUNDA PATA: las dos SQLite, que el ensayo NO cubria. ***

    *El complemento pide las tres: *** «PostgreSQL, recetas/diario SQLite Y PERMISOS/SNAPSHOTS, no solo una
    tabla vacia». *** *Y este ensayo solo restauraba PostgreSQL.*

    **Que es «restaurar» una SQLite, y que no.** *No hay servidor que levantar: *el fichero **se copia a su
    sitio**, *y lo que hay que comprobar es que **se abre y tiene lo que tenia**.* *Asi que aqui:*

      1. *Se coge **la copia** que dejo el respaldo* (`recetas_<sello>.sqlite`, hecha con `VACUUM INTO`).
      2. *Y **se abre**, y se le pregunta: *`pragma integrity_check`, *las tablas, *y **cuantas filas**
         tiene cada una.*
      3. *Y **si el fichero no esta, se dice**: *el diario **se crea al primer apunte**, *y no existir
         **no es un fallo** -- *es un diario en el que nadie ha escrito.* *Lo que **no** se hace es
         inventar una copia vacia para que la prueba «salga».*

    *Y no se toca ninguna base existente*: *se lee **la copia**, *que esta en `data/respaldos`.*
    """
    import sqlite3
    from pathlib import Path as _P

    # *Las dos que la casa escribe, y las mismas que respalda `scripts/respaldar_sqlite.py`.*
    BASES = ("recetas.sqlite", "diario.sqlite")
    carpeta = destino or (_P(__file__).resolve().parents[1] / "data" / "respaldos")
    hechas: list[dict] = []
    for base in BASES:
        # *La copia lleva sello, como las de PostgreSQL: *`recetas_<sello>.sqlite`.*
        candidatas = sorted(carpeta.glob(f"{base[:-len('.sqlite')]}_*.sqlite"))
        if sello:
            candidatas = [c for c in candidatas if sello in c.name] or candidatas
        if not candidatas:
            hechas.append({"base": base, "estado": "sin_copia",
                           "nota": "no hay copia con sello: se crea al respaldar, y no se inventa"})
            continue
        copia = candidatas[-1]
        con = sqlite3.connect(f"file:{copia}?mode=ro", uri=True)
        try:
            integridad = con.execute("pragma integrity_check").fetchone()[0]
            tablas = [r[0] for r in con.execute(
                "select name from sqlite_master where type='table' and name not like 'sqlite_%' order by name")]
            # *Las tablas salen de `sqlite_master` del propio fichero, no de fuera.*
            filas = {t: con.execute(f"select count(*) from {t}").fetchone()[0] for t in tablas}
        finally:
            con.close()
        hechas.append({"base": base, "estado": "abre", "fichero": copia.name,
                       "integridad": integridad, "filas": filas})
    return hechas


def corre(copia) -> dict:
    """**El recorrido entero, en un destino que se crea y se destruye.**

    *Y el orden importa*: **primero las guardas**, *y **despues** el contenedor.* *Al reves, ya habria algo
    que limpiar cuando la guarda se niegue.*
    """
    import gzip

    nombre, puerto = nombre_unico(), puerto_libre()
    comprueba_nombre(nombre)
    comprueba_puerto(puerto)
    dsn = f"postgresql://cesta:ensayo@127.0.0.1:{puerto}/cesta"
    comprueba_dsn(dsn)

    # **La identidad, otra vez, sobre lo que se va a crear.** *Por si algo cambio entre la guarda y aqui.*
    comprueba_dsn(dsn)
    print(f"  destino: «{nombre}», puerto {puerto}, etiqueta «{ETIQUETA}»")
    print(f"  y NO se toca: {', '.join(str(p) for p in PUERTOS_PROHIBIDOS)}")

    creado = _docker("run", "-d", "--name", nombre, "--label", ETIQUETA,
                     "-e", "POSTGRES_USER=cesta", "-e", "POSTGRES_PASSWORD=ensayo",
                     "-e", "POSTGRES_DB=cesta", "-p", f"127.0.0.1:{puerto}:5432",
                     "postgres:16-alpine")
    if creado.returncode != 0:
        raise DestinoNoSeguro(f"no se pudo crear el contenedor: {creado.stderr.decode()[:200]}")
    # *** Y SE COMPRUEBA QUE ARRANCO, que es lo que este ensayo NO hacia. *** *
    #
    # *La primera vez que se corrio de verdad, `docker run -d` devolvio un id, el guion se puso a esperar
    # un puerto que **nadie escuchaba**, y el contenedor se quedo en *** `Created` *** -- *creado y **sin
    # arrancar**.* *Y el guion no lo miro: **dio por hecho que un id es un contenedor corriendo.** *
    #
    # *Y de ahi salieron dos cosas, las dos dichas*: *la espera se fue a **60 s por intento**, *y *
    # *** `docker rm -f` se quedo BLOQUEADO *** *sobre ese contenedor -- *que es un modo de fallo conocido
    # de Docker cuando un `run` no llega a arrancar, *y **no se arregla insistiendo**.* *
    #
    # *Asi que se pregunta por el estado **antes de esperar nada**, y con la orden que **si responde**:
    # `docker ps --filter name=... --format {{.Status}}`.* *`docker inspect` **se cuelga** en un
    # contenedor `Created` -- *comprobado* --, *asi que **no se usa para esto.** *
    #
    # *Y `Up` es lo que se busca, que es la misma leccion del `findstr /i running` que dejo a Cesta sin
    # respaldo: **se pregunta por el estado, y se lee lo que de verdad dice.** *
    estado = _docker("ps", "-a", "--filter", f"name=^{nombre}$", "--format", "{{.Status}}")
    dicho = estado.stdout.decode(errors="replace").strip()
    if not dicho.startswith("Up"):
        raise DestinoNoSeguro(
            f"el contenedor «{nombre}» NO arranco: su estado es «{dicho or 'ninguno'}». "
            "Un id de `docker run -d` no es un contenedor corriendo, y esperar su puerto solo gasta "
            "el plazo. Y NO se insiste: un contenedor atascado en `Created` bloquea `docker rm -f`, "
            "asi que lo que hay que hacer es mirarlo, no reintentar")
    print(f"  arranco: {dicho}")
    # *Y se comprueba que el que lleva la etiqueta es ESTE: lo que autoriza a borrarlo despues.*
    if nombre not in contenedores_con_etiqueta():
        limpia_lo_propio(nombre)  # *no lo borra: no lleva etiqueta; y avisa*
        raise DestinoNoSeguro(f"«{nombre}» se creo pero NO aparece con la etiqueta «{ETIQUETA}»")

    resultado: dict = {"contenedor": nombre, "puerto": puerto}
    try:
        with _conecta(dsn) as con, con.cursor() as cur:
            # *** LA GUARDA, ANTES DE CUALQUIER DDL. *** *
            comprueba_base_vacia(cur)
            print("  la base esta vacia: se puede restaurar aqui")

        with gzip.open(copia, "rb") as fuente:
            crudo = fuente.read()
        print(f"  copia: {copia.name} -> {len(crudo)} bytes descomprimidos")
        metido = _docker("exec", "-i", nombre, "psql", "-U", "cesta", "-d", "cesta",
                         "-v", "ON_ERROR_STOP=1", "-q", entrada=crudo)
        if metido.returncode != 0:
            raise DestinoNoSeguro(
                f"el restaurado fallo: {metido.stderr.decode(errors='replace')[:300]}")

        with _conecta(dsn) as con, con.cursor() as cur:
            # *** Y `lista_acceso`, QUE ES LA TERCERA PATA: LOS PERMISOS. *** *
            #
            # *El complemento pide «PostgreSQL, recetas/diario SQLite *** Y PERMISOS/SNAPSHOTS***», *
            # *y `lista_acceso` es **la tabla que acredita quien puede que** sobre cada lista.* *
            # *Comprobar su recuento **despues de restaurar** es lo que dice que **los permisos
            # viajaron en la copia** -- *y sin esto, el ensayo restauraba datos **sin comprobar que
            # vinieran los permisos.*** *
            for tabla in ("lista_linea", "usuario", "lista", "compra", "lista_acceso"):
                cur.execute(f"SELECT count(*) FROM {tabla}")  # *tabla de una lista fija, no de fuera*
                resultado[tabla] = cur.fetchone()[0]
        return resultado
    finally:
        # *** Y LA SEGUNDA PATA: las dos SQLite -- CON SU PROPIO `try`, QUE ES UN ARREGLO MEDIDO. *** *
        #
        # *La primera version las ponia **aqui, antes de limpiar**, y una corrida fallo con `NameError`
        # **en esta misma rama**: *asi que **la limpieza no se ejecuto**, *y **quedo un contenedor
        # huerfano** (`cesta-restauro-4deeaf18fecb`, que hubo que quitar a mano).* *
        #
        # *O sea: **un paso de la limpieza no puede impedir la limpieza.*** *Por eso va con su `try`, *
        # y **la limpieza queda la ultima y sin nada delante que pueda reventar.** *
        try:
            for uno in restaura_las_sqlite(sello=copia.stem.split("_")[-1]):
                if uno["estado"] == "abre":
                    print(f"  {uno['fichero']}: abre, integridad {uno['integridad']}, filas {uno['filas']}")
                    resultado[uno["base"]] = uno["filas"]
                else:
                    print(f"  {uno['base']}: {uno['estado']} -- {uno['nota']}")
        except Exception as fallo:  # noqa: BLE001  - *y la limpieza sigue pase lo que pase*
            print(f"  las SQLite no se pudieron comprobar: {fallo}")
        # **Y se limpia SOLO lo acreditado.** *`limpia_lo_propio(nombre)` se niega si no lleva la etiqueta,
        # asi que no puede llevarse por delante un contenedor que no es suyo.*
        for uno in limpia_lo_propio(nombre):
            print(f"  limpiado (era suyo): {uno}")
        print(f"  y queda: {resultado}")


def _cli() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--plan", action="store_true",
                    help="decir el destino que usaria y las guardas que ha pasado, sin crear nada")
    ap.add_argument("--limpiar", action="store_true",
                    help="borrar SOLO los contenedores con la etiqueta del ensayo")
    ap.add_argument("--correr", type=Path, default=None,
                    help="la copia .sql.gz a restaurar en un destino nuevo y desechable")
    a = ap.parse_args()
    if a.correr is not None:
        corre(a.correr)
        return 0
    if a.limpiar:
        for uno in limpia_lo_propio():
            print(f"  borrado (llevaba la etiqueta): {uno}")
        return 0
    # *El plan: se decide el destino y se comprueban las guardas, sin tocar Docker.*
    nombre, puerto = nombre_unico(), puerto_libre()
    dsn = f"postgresql://cesta:ensayo@127.0.0.1:{puerto}/cesta_ensayo"
    comprueba_nombre(nombre)
    comprueba_dsn(dsn)
    print(f"  destino: contenedor «{nombre}», puerto {puerto}, etiqueta «{ETIQUETA}»")
    print(f"  y NO se toca: {', '.join(f'{p} ({m})' for p, m in PUERTOS_PROHIBIDOS.items())}")
    print(f"  dsn: {dsn}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(_cli())
