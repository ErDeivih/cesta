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
    return _con_el_id_como_texto(yo)


def usuario_opcional(peticion: Request) -> dict | None:
    """Para lo que se puede mirar sin cuenta. Devuelve None en vez de cortar."""
    yo = almacen.quien(peticion.cookies.get(COOKIE))
    return None if yo is None else _con_el_id_como_texto(yo)


def _con_el_id_como_texto(yo: dict) -> dict:
    """**El `id` del usuario, siempre como texto.** *Y esto se aprendio midiendo.*

    *Encontrado el 14 de octubre de 2026, **al abrir `prueba_e2e.py` a Recetas.*** *La ruta de crear
    receta reventaba con:*

        `sqlite3.ProgrammingError: Error binding parameter 3: type 'UUID' is not supported`

    *Y **no era la ruta**: *era que `plataforma/api/recetas.py` pasa `usuario["id"]` **a pelo** a
    `core/recetas.crear`, *que **declara `propietario: str`** *y **se lo da a SQLite**, *que **no acepta
    un `UUID`.*** *

    *** Y el mismo fichero ya usaba `str()` para el id de las LISTAS** *(-- `l345` --), *y **no para el
    del usuario**: *doce sitios con `usuario["id"]` crudo.* *O sea: **el defecto era la inconsistencia**,
    *no un sitio concreto.* *

    *** Y el criterio lo tenia escrito el propio proyecto** *, en el mismo sitio donde este error
    aparecio la primera vez* *(-- `tests/test_revision_a09_compra_hogar.py:34-42` --):*

        *** «El id, **siempre como texto**. *Y esto costo una corrida*: `crea_lista` devuelve un objeto
        `UUID`, no una cadena, y algo mas abajo llama a `.strip()` -- «AttributeError: 'UUID' object has
        no attribute 'strip'» --. **Es el mismo error de siempre: dar por hecho el tipo de un dato en
        vez de leerlo.** *Aqui se lee, y se convierte.» ***

    *Asi que **se convierte en LA PUERTA** -- *una vez, y no en las doce rutas* --, *y **aqui queda el
    motivo escrito para el siguiente que lo lea.***

    *Y **por que no se veia por HTTP**: *porque el `id` de la sesion **ya es cadena** al leerlo de la
    base; *el `UUID` solo aparece cuando el usuario lo inyecta un ensayo con
    `dependency_overrides[usuario_actual]` *-- *que es **justo lo que hizo `prueba_e2e.py`,**
    *y **por eso lo encontro.*** *
    """
    if yo is not None and yo.get("id") is not None:
        yo = {**yo, "id": str(yo["id"])}
    return yo
