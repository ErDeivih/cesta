"""Los avisos, mirados en la cadena diaria: el §6 del encargo, la parte que faltaba.

    uv run python -m projects.cesta.avisos

El encargo pide tres cosas y dos ya estaban: **evaluarlas cuando cambian los datos**
(el vigilante de la API, `plataforma/api/vigilante.py`, mira en cuanto cambia gold) y
**dejar el resultado guardado** (`salto_en` y su frase, que es lo que pinta la
pantalla). Lo que faltaba es esto:

    - *"Evaluarlas en la cadena diaria, despues del pipeline."*
    - *"Que el resumen diario diga cuantas saltaron."*

Este paso va despues de `emparejar` (con gold ya entero) y antes del resumen, y deja
escrito `data/avisos.json`, que es lo que lee `projects/cesta/resumen.py`. Los dos
numeros que le importan al resumen son **cuantas saltaron hoy** y **cuantas siguen en
la cola del vigilante**: el segundo es el que dice si la pasada ha hecho su trabajo.

Lo mas importante de este fichero es **lo que hace cuando no puede**, y no es un caso
raro: la base de datos de casa **no publica su puerto** -- `plataforma/docker-compose.yml`
lo dice con todas las letras, *"No se publica el puerto: solo lo alcanza la API, por la
red interna"* --, asi que desde el PC donde corre esto **no se llega a PostgreSQL**. Eso
esta medido (23 sep 2026: `127.0.0.1:5432` no contesta; el 8080 si, que es Caddy).

Por eso este paso **no puede fallar el dia**: si no hay base, lo dice con palabras, deja
el resumen diciendo "no lo se" en vez de inventarse un cero, y devuelve 0. Un paso que
se cae cuando falta la base convertiria un dia bueno en un dia fallido por una linea de
resumen, y ademas taparia el resultado de las cinco cadenas y del pipeline, que es lo
que de verdad se viene a ver a las 06:00.
"""
from __future__ import annotations

import json
import os
from dataclasses import replace
from datetime import datetime

from core import config
from plataforma.api import almacen, vigilante

# Donde deja el paso lo que ha visto. Al lado de gold y no dentro: no es un dato del
# catalogo, es la nota de la cadena sobre si misma, como el fichero que `run.py`
# escribe para saber si la ejecucion anterior termino.
FICHERO = config.DATA / "avisos.json"

# Cuanto se aguanta a que la base conteste. La cadena corre a las 06:00 sin nadie
# delante, y este paso no puede quedarse esperando a un puerto que no va a contestar.
#
# Medido en el PC de casa (23 sep 2026): con tope de 3 segundos, el "no lo se" tarda
# **6,5 s** (dos pasadas: 6,7 y 6,5), porque `localhost` contesta por dos direcciones
# (IPv6 y IPv4) y el tope se aplica a cada intento. Por eso el numero esta en 3 y no en
# 30: quien lo baje tiene que saber que el reloj de este paso va al doble.
ESPERA = 3.0

# Como se dice que no se pudo. Se guarda en el fichero y se imprime, para que el
# resumen no tenga que adivinar por que no hay numeros.
SIN_BASE = ("la base de datos no se alcanza desde aqui (mirada en `plataforma/.env` y en "
            "`CESTA_POSTGRES`: si el puerto de la base no esta publicado en 127.0.0.1, "
            "este paso no llega)")

# El fichero de Compose, que es donde vive la clave de la base.
ENV_DE_COMPOSE = config.RAIZ / "plataforma" / ".env"

_ya_mirado = False


def dsn_de_casa() -> str | None:
    """El DSN de la base de casa tal como la ve **este PC**, o `None` si no se sabe.

    `CESTA_POSTGRES` manda: si esta puesto, ese es el DSN y no se busca nada mas.

    Si no esta, se lee `plataforma/.env` -- el fichero de Docker Compose -- y se arma el
    DSN con la clave de ahi. Es lo que hace que la cadena de las 06:00 funcione **sin
    tocar `ejecutar.bat`**: el paso de los avisos corre en el PC y la base en Docker, y
    desde el 23 de septiembre de 2026 el puerto esta publicado en `127.0.0.1`
    (`docker-compose.yml`), asi que se llega.

    **La clave no se copia a ningun sitio.** Escribirla en el `.bat` o en una variable de
    entorno del Programador de tareas seria una segunda copia que se queda vieja el dia
    que se cambie la de verdad -- y la de verdad es la del `.env`, que es de donde la lee
    Compose para arrancar la base. Si el fichero no esta o no tiene la clave, se devuelve
    `None` y el paso dice "no lo se", que es lo honesto.
    """
    if os.environ.get("CESTA_POSTGRES"):
        return None                 # ya hay uno puesto: no se busca nada mas
    try:
        texto = ENV_DE_COMPOSE.read_text(encoding="utf-8")
    except OSError:
        return None
    clave = ""
    for linea in texto.splitlines():
        limpia = linea.strip()
        if limpia.startswith("#") or "=" not in limpia:
            continue
        nombre, _, valor = limpia.partition("=")
        if nombre.strip() == "CESTA_CLAVE_DB":
            clave = valor.strip().strip('"').strip("'")
    if not clave:
        return None
    return f"postgresql://cesta:{clave}@127.0.0.1:5432/cesta"


def una_pasada(momento: datetime | None = None) -> dict:
    """Mira las alertas pendientes y apunta lo que ha visto, o dice que no ha podido.

    Devuelve siempre un diccionario: con `{"error": ...}` cuando no se ha podido
    mirar. Nunca levanta una excepcion, y eso es a proposito -- quien llama es la
    cadena diaria, y una linea de resumen no puede tumbar el dia.

    `almacen.arranca()` trae ademas las migraciones, que son idempotentes: es el
    mismo camino que hace la API al arrancar. El dia que la base se alcance desde
    aqui, la cadena deja el esquema al dia sin que nadie se acuerde de hacerlo.
    """
    cuando = momento or config.ahora_local()
    mio = not almacen.arrancado()
    # **La base de casa, si no hay un DSN puesto en el entorno.** Se hace antes de
    # `arranca()` y una sola vez por proceso: el pool se construye con `AJUSTES.postgres`,
    # asi que despues de arrancarlo ya no serviria de nada.
    global _ya_mirado
    if not _ya_mirado:
        _ya_mirado = True
        if (dsn := dsn_de_casa()) is not None:
            almacen.AJUSTES = replace(almacen.AJUSTES, postgres=dsn)
    try:
        almacen.arranca(espera=ESPERA)
        r = vigilante.una_pasada()
        cuadro = almacen.avisos_del_dia()
    except Exception as exc:  # noqa: BLE001
        return {"cuando": cuando.isoformat(timespec="seconds"),
                "error": f"{SIN_BASE}: {type(exc).__name__}"}
    finally:
        # El pool se cierra **solo si lo ha abierto este paso**. La API arranca el suyo
        # y lo cierra al terminar; aqui hay que cerrarlo porque el proceso se acaba en
        # el acto, pero cerrarle el almacen a quien ya lo tenia abierto -- la propia
        # API, o una prueba de punta a punta que llama a esto a mitad -- seria dejarlo
        # sin base a mitad de camino.
        if mio:
            almacen.para()
    return {"cuando": cuando.isoformat(timespec="seconds"),
            "miradas": r["miradas"], "saltan": r["saltan"], "apuntadas": r["apuntadas"],
            "saltaron_hoy": cuadro["saltaron_hoy"], "sin_saltar": cuadro["sin_saltar"],
            "por_mirar": cuadro["por_mirar"]}


def escribe(lo_que_hay: dict) -> None:
    """Deja el resultado donde lo lee el resumen. Un fallo aqui no puede parar nada."""
    try:
        FICHERO.parent.mkdir(parents=True, exist_ok=True)
        FICHERO.write_text(json.dumps(lo_que_hay, ensure_ascii=False, indent=1),
                           encoding="utf-8")
    except OSError as exc:
        print(f"[avisos] no he podido dejar la nota en {FICHERO}: {exc}")


def lee() -> dict | None:
    """Lo que dejo la ultima pasada, o None si no hay nada que leer."""
    try:
        return json.loads(FICHERO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def frase(lo_que_hay: dict | None) -> str:
    """La linea del resumen, en castellano y sin adornos.

    Se escribe aqui y no en `resumen.py` porque es la traduccion de lo que este paso
    midio: el resumen ensena la frase, no la interpreta.
    """
    if lo_que_hay is None:
        return ("avisos: no lo se -- la cadena no ha podido mirarlos (no hay nota de "
                "la pasada)")
    if "error" in lo_que_hay:
        return f"avisos: no lo se -- {lo_que_hay['error']}"
    saltaron = lo_que_hay.get("saltaron_hoy", 0)
    apuntadas = lo_que_hay.get("apuntadas", 0)
    por_mirar = lo_que_hay.get("por_mirar", 0)
    cuando = str(lo_que_hay.get("cuando", ""))[11:16]
    texto = (f"avisos: {saltaron} saltaron hoy"
             f" | {apuntadas} en esta pasada de {lo_que_hay.get('miradas', 0)} miradas")
    if por_mirar:
        texto += f" | {por_mirar} esperando su dia"
    if cuando:
        texto += f" ({cuando})"
    return texto


def main(argv: list[str] | None = None) -> int:
    """El paso de la cadena. Devuelve 0 **siempre**, y eso es la mitad del contrato."""
    lo_que_hay = una_pasada()
    escribe(lo_que_hay)
    # El resumen imprime la linea limpia (la lee de `FICHERO`); aqui se dice con el
    # prefijo de los pasos para poder seguir una ejecucion de la cadena de arriba
    # abajo y saber en que punto se miro.
    print(f"[avisos] {frase(lo_que_hay)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
