"""Tira el crudo viejo. Se ejecuta al final de cada recoleccion.

Sin esto el disco se llena solo: 338 MB de crudo por pasada, 123 GB al ano, sobre
158 GB libres. El dia que no quepa, la ejecucion falla de madrugada y nadie se
entera hasta que faltan precios de una semana.

El crudo sirve para dos cosas: reanudar una ejecucion cortada (el mismo dia) y
reprocesar el historico si cambia un parser (semanas, no anos). Bronze guarda lo
mismo ya tipado, ocupa mil veces menos y no se toca nunca.

    uv run python -m projects.cesta.limpiar            # aplica config.DIAS_RAW
    uv run python -m projects.cesta.limpiar --ensayo   # dice que borraria
"""
from __future__ import annotations

import argparse
import shutil
from datetime import timedelta

from core import config, storage


def carpetas_caducadas(dias: int) -> list:
    """Carpetas fecha=* del crudo mas viejas que `dias`. Vacio si dias <= 0."""
    if dias <= 0:
        return []
    limite = config.hoy_local() - timedelta(days=dias)
    viejas = []
    for carpeta in sorted((config.DATA / "raw").glob("fuente=*/fecha=*")):
        try:
            fecha = carpeta.name.split("=", 1)[1]
            if fecha < limite.isoformat():
                viejas.append(carpeta)
        except (IndexError, ValueError):
            continue          # nombre raro: no se toca nada que no se entienda
    return viejas


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="limpiar")
    ap.add_argument("--dias", type=int, default=config.DIAS_RAW)
    ap.add_argument("--ensayo", action="store_true",
                    help="decir que se borraria, sin borrar nada")
    a = ap.parse_args(argv)

    viejas = carpetas_caducadas(a.dias)
    if not viejas:
        return 0
    megas = 0.0
    for carpeta in viejas:
        megas += sum(f.stat().st_size for f in carpeta.rglob("*") if f.is_file()) / 1e6
    if a.ensayo:
        print(f"  se borrarian {len(viejas)} carpetas de crudo ({megas:.0f} MB)")
        return 0
    borradas = 0
    for carpeta in viejas:
        # Cinturon: esta funcion solo mira dentro de `raw`, pero es la unica del
        # proyecto que llama a rmtree y el dia que alguien le cambie la raiz por
        # descuido conviene que reviente aqui y no en bronze.
        storage.comprueba_borrable(carpeta)
        try:
            shutil.rmtree(carpeta)
            borradas += 1
        except OSError as exc:
            print(f"  no se pudo borrar {carpeta.name}: {exc}")
    print(f"  crudo: {borradas} dias de mas de {a.dias} dias borrados "
          f"({megas:.0f} MB liberados)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
