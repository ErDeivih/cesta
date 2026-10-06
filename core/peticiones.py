"""Contar las peticiones de verdad, donde ocurren: en el que las hace.

**Por que existe.** La ampliacion del 6 de octubre de 2026 pide *"Medir peticiones realmente
evitadas, no inferirlas restando filas de dos dias con distinta disponibilidad"*. Restar filas de
dos dias es lo que parece una medida y no lo es: si un dia la cadena publica menos, la resta lo
llama ahorro. Aqui se cuenta **el acto de pedir** y **el acto de decidir no pedir**, que son dos
cosas que ocurren en un sitio concreto del codigo y se pueden incrementar.

Tres numeros, y cada uno significa una cosa distinta:

  - `peticiones`: peticiones HTTP **enviadas**. Lo cuenta `core/fetch.py` en el momento de pedir.
  - `cache`: respuestas que ya estaban guardadas y **no** generaron peticion. Lo cuenta
    `core/storage.py` al leer. Sin esto, "menos peticiones" no distingue ahorro de averia.
  - `evitadas`: decisiones de **no pedir por politica** (una rama de bazar). Lo declara el colector
    justo cuando decide saltarsela.

Y lo que **no** hace: no estima lo que habria pasado. "Evitadas" es un recuento de decisiones, no
una prediccion de lo que la cadena habria servido.

Un proceso por cadena escribe su propio fichero (`data/peticiones/<fuente>-<fecha>.json`) al
terminar, porque la pasada diaria lanza las cinco cadenas en procesos separados. Si el proceso se
cae, no deja fichero: eso tambien es informacion, y el informe lo dice en vez de inventar un cero.
"""
from __future__ import annotations

import atexit
import contextlib
import json
import os
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

RAIZ = Path(__file__).resolve().parents[1]
CARPETA = RAIZ / "data" / "peticiones"

# El estado del proceso. Un diccionario y tres enteros: nada que pueda fallar a mitad de una captura
# de dos horas, que es lo que no se puede permitir en la tarea de las 06:00.
_peticiones: Counter = Counter()     # por host
_cache: Counter = Counter()          # por fuente
_evitadas: Counter = Counter()       # por fuente
_registrado: set[str] = set()
_ya_escrito = False


def pide(url: str) -> None:
    """Se ha **enviado** una peticion HTTP. Se cuenta el host, que es lo que dice a quien."""
    # Contar no puede tumbar una captura de dos horas: si algo falla, se sigue sin contar.
    with contextlib.suppress(Exception):
        _peticiones[urlsplit(url).netloc or url] += 1


def de_cache(fuente: str) -> None:
    """Se ha servido de la copia guardada: no ha habido peticion."""
    with contextlib.suppress(Exception):
        _cache[fuente] += 1


def evita(fuente: str, motivo: str = "fuera-de-alcance") -> None:
    """Se ha decidido **no pedir** algo, y por que. Es una decision, no una suposicion."""
    with contextlib.suppress(Exception):
        _evitadas[fuente] += 1
        _registrado.add(motivo)


def reinicia() -> None:
    """Para las pruebas: deja el contador a cero."""
    _peticiones.clear()
    _cache.clear()
    _evitadas.clear()
    _registrado.clear()


def resumen() -> dict:
    return {
        "peticiones": sum(_peticiones.values()),
        "por_host": dict(_peticiones),
        "cache": sum(_cache.values()),
        "por_fuente_cache": dict(_cache),
        "evitadas": sum(_evitadas.values()),
        "por_fuente_evitadas": dict(_evitadas),
        "motivos": sorted(_registrado),
    }


def escribe(fuente: str, hoy: date | None = None) -> Path | None:
    """Deja el recuento en `data/peticiones/<fuente>-<fecha>.json`. Nunca lanza."""
    global _ya_escrito
    try:
        dia = (hoy or date.today()).isoformat()
        CARPETA.mkdir(parents=True, exist_ok=True)
        ruta = CARPETA / f"{fuente}-{dia}.json"
        datos = resumen()
        # Si no hubo ni una peticion ni una decision, no se escribe nada: un fichero con ceros
        # pareceria una captura que fue bien y no pidio nada, y eso no es lo mismo que no correr.
        if not (datos["peticiones"] or datos["cache"] or datos["evitadas"]):
            return None
        datos["fuente"] = fuente
        ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
        _ya_escrito = True
        return ruta
    except Exception:  # noqa: BLE001  (escribir el recuento no puede tumbar la pasada)
        return None


def registra_al_salir(fuente: str) -> None:
    """Deja escrito el recuento cuando el proceso termina, sin que el colector tenga que acordarse.

    Se engancha aqui y no en cada colector porque son cinco y la tarea diaria los lanza por
    separado: un contador que hay que acordarse de cerrar es un contador que un dia no se cierra.
    """
    # **Las pruebas no escriben el recuento del dia.** Un recorrido de prueba deja un fichero con
    # peticiones y lecturas de cache que nunca ocurrieron en una captura real, y el informe del dia
    # lo leeria como si esa cadena hubiera corrido. Se comprueba una condicion que existe
    # (`PYTEST_CURRENT_TEST`) en vez de filtrar despues en el informe.
    if "PYTEST_CURRENT_TEST" in os.environ:
        return
    atexit.register(escribe, fuente)
