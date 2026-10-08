"""Quien llama: la sesion, en un modulo comun.

Vivia dentro de `main.py`, y los routers no pueden importar de ahi sin ciclo: `main` importa los
routers, y los routers necesitarian `main`. Aqui no depende de nadie, asi que los dos pueden usarla.

**La identidad sale de la cookie y de ningun otro sitio.** Nunca del cuerpo de una peticion: si el
propietario se pudiera pedir en el JSON, el aislamiento seria decorativo.
"""
from __future__ import annotations

from fastapi import HTTPException, Request

from . import almacen

COOKIE = "cesta_sesion"


def usuario_actual(peticion: Request) -> dict:
    """El usuario de la sesion, o 401. Es la puerta de todo lo personal."""
    yo = almacen.quien(peticion.cookies.get(COOKIE))
    if yo is None:
        raise HTTPException(401, "Hay que entrar primero.")
    return yo


def usuario_opcional(peticion: Request) -> dict | None:
    """Para lo que se puede mirar sin cuenta. Devuelve None en vez de cortar."""
    return almacen.quien(peticion.cookies.get(COOKIE))
