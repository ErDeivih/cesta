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


def _cli() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--plan", action="store_true",
                    help="decir el destino que usaria y las guardas que ha pasado, sin crear nada")
    ap.add_argument("--limpiar", action="store_true",
                    help="borrar SOLO los contenedores con la etiqueta del ensayo")
    a = ap.parse_args()
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
