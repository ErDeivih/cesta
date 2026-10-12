"""Una copia de la base de casa, con fecha y con retencion.

**Por que existe, y en que se diferencia de `plataforma/prueba_copia.py`.**

`prueba_copia.py` **comprueba que una copia se puede restaurar** -- *y esta bien que exista* --, pero hace
su propia base desechable, la vuelca, la restaura en otro contenedor y **borra el volcado al terminar**.
*Eso demuestra que el mecanismo funciona; **no deja ninguna copia de nada**.*

**Este hace lo otro**: *una copia **de verdad**, de **la base de casa**, con su fecha, guardada, y con una
retencion que impide que se acumulen para siempre.*

> **La distincion, dicha en una linea**: *aquel contesta «¿se puede restaurar?»; este contesta «¿hay una
> copia de ayer?».* **Hacen falta los dos, y hasta ahora solo estaba el primero.**

**Y lo que NO hace, porque es lo que el encargo prohibe y lo que me costo 716 usuarios:**

  - **no toca el `5433`** (`facylf-postgres`): *es de otro encargo*;
  - **no toca la base de pruebas** (`cesta-prueba-db`, el `5434`): *es desechable, y no merece copia*;
  - **no borra ningun contenedor**: *lee de `cesta-db-1` con `docker exec` y escribe en un fichero*;
  - **no escribe en el catalogo**: *`data/gold` no se toca.*

**Como se usa:**

    uv run python -m plataforma.copia_programada              # hace una copia y aplica la retencion
    uv run python -m plataforma.copia_programada --listar      # dice que hay
    uv run python -m plataforma.copia_programada --retencion 7

*Y para que se haga sola, una tarea de Windows o un `cron` que lo llame.* **No se instala ninguna**: *eso
se decide, no se hace por cuenta propia.*
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
# **Los volcados van a `data/`, que esta ignorado en git.** *Una copia de la base de casa en el
# repositorio seria un fichero con datos de casa dentro, y eso no se commitea ni por descuido.*
DESTINO = RAIZ / "data" / "copias"
CONTENEDOR = "cesta-db-1"
USUARIO = "cesta"
BASE = "cesta"
RETENCION_POR_DEFECTO = 7
# *Un volcado por debajo de esto no es una copia: es un fichero del que se supone algo.* **La misma guarda
# que usa `prueba_copia`**, y por la misma razon.
MINIMO_BYTES = 1000


def _corre(args, timeout=600):
    return subprocess.run(args, capture_output=True, timeout=timeout)


def esta_el_contenedor() -> bool:
    r = _corre(["docker", "inspect", "-f", "{{.State.Running}}", CONTENEDOR], timeout=60)
    return r.returncode == 0 and b"true" in (r.stdout or b"").lower()


def volcado() -> bytes:
    """El `pg_dump` de la base de casa, leido por `docker exec`. *No publica puerto: se lee por dentro.*"""
    r = _corre(["docker", "exec", CONTENEDOR, "pg_dump", "-U", USUARIO, "-d", BASE])
    if r.returncode != 0:
        raise RuntimeError(f"pg_dump fallo: {(r.stderr or b'').decode('utf-8', 'replace')[:300]}")
    return r.stdout or b""


def copias() -> list[Path]:
    """Los volcados que hay, **del mas reciente al mas viejo**. *Por el nombre, que lleva la fecha.*"""
    if not DESTINO.exists():
        return []
    return sorted(DESTINO.glob("cesta-*.sql"), reverse=True)


def hace(momento: datetime | None = None) -> Path:
    """Hace una copia y devuelve su camino. **Y no la deja pasar si sale vacia.**"""
    if not esta_el_contenedor():
        raise RuntimeError(f"el contenedor {CONTENEDOR} no esta corriendo: no hay nada que copiar")
    datos = volcado()
    if len(datos) < MINIMO_BYTES:
        # *Se para aqui y no se escribe nada.* **Un fichero vacio con nombre de copia es peor que no
        # tener copia**: el dia que se necesite, parecera que la hay.
        raise RuntimeError(f"el volcado son {len(datos)} bytes, menos de {MINIMO_BYTES}: NO se guarda")
    DESTINO.mkdir(parents=True, exist_ok=True)
    sello = (momento or datetime.now()).strftime("%Y%m%d-%H%M%S")
    camino = DESTINO / f"cesta-{sello}.sql"
    if camino.exists():
        raise ValueError(f"ya hay una copia con ese sello: {camino.name}")
    camino.write_bytes(datos)
    return camino


def aplica_retencion(cuantas: int = RETENCION_POR_DEFECTO) -> list[Path]:
    """**Borra las mas viejas, y solo las que sobran.** *Devuelve las que se llevo.*

    *Sin esto, las copias se acumulan hasta llenar el disco, y entonces la copia se convierte en el
    problema.* **Y se borran las **viejas**, nunca las nuevas: si algo va mal, la copia mas reciente es la
    que se quiere.**
    """
    todas = copias()
    sobran = todas[max(0, cuantas):] if cuantas > 0 else []
    for camino in sobran:
        camino.unlink(missing_ok=True)
    return sobran


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="copia_programada", description=__doc__.split("\n")[0])
    ap.add_argument("--retencion", type=int, default=RETENCION_POR_DEFECTO,
                    help=f"cuantas copias se guardan (por defecto {RETENCION_POR_DEFECTO})")
    ap.add_argument("--listar", action="store_true", help="solo dice que hay, sin copiar nada")
    a = ap.parse_args(argv)

    if a.listar:
        hay = copias()
        print(f"copias en {DESTINO}: {len(hay)}")
        for camino in hay:
            print(f"   {camino.name}  {camino.stat().st_size / 1024:.1f} KB")
        return 0

    try:
        camino = hace()
    except (RuntimeError, ValueError) as fallo:
        print(f"NO se hizo la copia: {fallo}")
        return 1
    print(f"copia hecha: {camino.name}  ({camino.stat().st_size / 1024:.1f} KB)")

    fuera = aplica_retencion(a.retencion)
    if fuera:
        print(f"retencion ({a.retencion}): retiradas {len(fuera)}")
        for camino in fuera:
            print(f"   {camino.name}")
    print(f"quedan {len(copias())} copias")
    return 0


if __name__ == "__main__":
    sys.exit(main())
