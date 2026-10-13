"""Todo lo que cambia entre tu portatil y el contenedor, en un sitio."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _ruta(nombre: str, por_defecto: Path) -> Path:
    return Path(os.environ.get(nombre, por_defecto)).resolve()


@dataclass(frozen=True)
class Ajustes:
    gold: Path
    postgres: str
    origenes: tuple[str, ...]
    dias_sesion: int
    max_tiendas: int
    dias_precio_valido: int
    registro_abierto: bool

    @classmethod
    def del_entorno(cls) -> Ajustes:
        raiz = Path(__file__).resolve().parents[2]
        return cls(
            gold=_ruta("CESTA_GOLD", raiz / "data" / "gold"),
            postgres=os.environ.get(
                "CESTA_POSTGRES",
                "postgresql://cesta:cesta@localhost:5432/cesta"),
            origenes=tuple(
                o.strip() for o in
                os.environ.get("CESTA_ORIGENES", "http://localhost:8080").split(",")
                if o.strip()),
            # Larga a proposito: tu madre no entra todas las semanas y no tiene
            # gracia pedirle la clave cada vez. El riesgo es pequeno cuando lo
            # unico que llega aqui es un movil que ya esta dentro de Tailscale.
            dias_sesion=int(os.environ.get("CESTA_DIAS_SESION", "30")),
            # Un reparto entre cinco tiendas que ahorra ocho euros no lo hace
            # nadie, y ofrecerlo es ruido con aspecto de consejo.
            max_tiendas=int(os.environ.get("CESTA_MAX_TIENDAS", "2")),
            # Un precio de hace mas de esto se ensena con su fecha, pero no
            # decide en que tienda comprar.
            dias_precio_valido=int(os.environ.get("CESTA_DIAS_PRECIO", "3")),
            # Abierto a proposito: hoy a esta pagina solo se llega desde
            # Tailscale, que ya es una red de invitados uno a uno, y pedir
            # ademas un codigo era un trasto para nada.
            #
            # Se cierra con CESTA_REGISTRO=cerrado en el .env, **y hay que
            # cerrarlo el dia que el servicio se publique con Cloudflare
            # Tunnel** (docs/DESPLIEGUE.md 4.2): ahi la pagina de registro queda
            # en internet.
            registro_abierto=os.environ.get(
                "CESTA_REGISTRO", "abierto").strip().lower() != "cerrado",
        )


AJUSTES = Ajustes.del_entorno()


# **Y los puertos que NO son de pruebas, nombrados una vez.**
#
# *El 13 de octubre de 2026 se perdieron **716 usuarios, 2529 listas y 2533 lineas** de la base de pruebas por
# no tener esto*: *se le paso a `plataforma/prueba_copia.py` un `CESTA_POSTGRES` que apuntaba al `5434`, su e2e
# rehizo el esquema, y **la base se vacio**.* **Y no fue un fallo del script: fue que nada impedia apuntarlo.**
#
# *Los tres puertos que hay en esta casa, y para que es cada uno:*
#
#   - **5432**: la base de casa. **La de verdad.**
#   - **5433**: `facylf`. **De otro proyecto**, y el encargo pide no tocarlo.
#   - **5434**: la de pruebas. *La unica que un ensayo puede rehacer.*
#
# **Asi que un ensayo que rehace esquema tiene que comprobar esto ANTES**, y la comprobacion vive aqui para que
# sea la misma en todos -- *que es lo que evita que el proximo script invente la suya y se equivoque.*
PUERTOS_PROTEGIDOS = {"5432": "la base de casa", "5433": "facylf, que es de otro proyecto"}


def comprueba_que_es_una_prueba(dsn: str) -> None:
    """**Se niega a seguir si el DSN apunta a una base que no es de pruebas.**

    *No comprueba que la base exista, ni que sea alcanzable, ni que este vacia* -- **solo que su puerto sea el
    de pruebas.** *Que es lo unico que se puede saber sin conectarse, y lo unico que hace falta para no
    destruir la de casa.*

    *Y si el DSN no trae puerto, **tambien se niega**:* **un DSN sin puerto es un DSN del que no se sabe donde
    apunta**, *y «no se sabe» no es «es de pruebas».*
    """
    import re

    if not dsn:
        raise ValueError(
            "sin DSN: no se puede saber si es una base de pruebas. "
            "Un ensayo que rehace esquema necesita un CESTA_POSTGRES explicito.")
    hallado = re.search(r":(\d{2,5})/", dsn)
    if hallado is None:
        raise ValueError(
            f"el DSN no dice su puerto, y «no se sabe» no es «es de pruebas»: {dsn.split('@')[-1]}")
    puerto = hallado.group(1)
    if puerto in PUERTOS_PROTEGIDOS:
        raise ValueError(
            f"el puerto {puerto} es {PUERTOS_PROTEGIDOS[puerto]}, y un ensayo que rehace esquema "
            f"no puede apuntarle. Usa el 5434: CESTA_POSTGRES='postgresql://cesta:prueba@127.0.0.1:5434/cesta'")
