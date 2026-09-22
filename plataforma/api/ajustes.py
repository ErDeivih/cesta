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
