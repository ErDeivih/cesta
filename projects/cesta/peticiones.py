"""Informe de peticiones del dia: lo enviado, lo servido de cache y lo no pedido a proposito.

    uv run python -m projects.cesta.peticiones                # hoy
    uv run python -m projects.cesta.peticiones --fecha 2026-10-06
    uv run python -m projects.cesta.peticiones --dias 7       # la semana, para ver la tendencia

Lee lo que cada cadena dejo escrito al terminar (`data/peticiones/<fuente>-<fecha>.json`). Cada
cadena corre en su propio proceso, asi que cada fichero lleva **sus** peticiones: no hay que
adivinar a quien pertenece un host.

**Lo que este informe no dice, y es importante:** no estima lo que habria pasado sin la politica.
"Evitadas" son decisiones de no pedir, contadas cuando se tomaron. Que una cadena no haya dejado
fichero **no es un cero**: es que no corrio o se cayo, y se dice asi.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
CARPETA = RAIZ / "data" / "peticiones"
CADENAS = ["alcampo", "aldi", "carrefour", "dia", "mercadona"]


def _lee(dia: str) -> dict[str, dict]:
    datos: dict[str, dict] = {}
    for cadena in CADENAS:
        ruta = CARPETA / f"{cadena}-{dia}.json"
        if not ruta.exists():
            continue
        try:
            datos[cadena] = json.loads(ruta.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            print(f"  aviso: el recuento de {cadena} del {dia} no se puede leer: {exc}")
    return datos


def un_dia(dia: str) -> int:
    datos = _lee(dia)
    print(f"Peticiones del {dia}")
    if not datos:
        # Decir lo que pasa y no poner ceros: no hay dato, no hay "cero peticiones".
        print("  no hay ningun recuento de ese dia. Ninguna cadena lo dejo escrito:")
        print("  puede que no corriera, o que se cayera antes de terminar.")
        return 0
    print(f"  {'cadena':<11}{'enviadas':>10}{'de cache':>10}{'evitadas':>10}   hosts")
    total = {"peticiones": 0, "cache": 0, "evitadas": 0}
    for cadena in CADENAS:
        if cadena not in datos:
            print(f"  {cadena:<11}{'sin recuento':>30}   (no corrio o no termino)")
            continue
        d = datos[cadena]
        for clave in total:
            total[clave] += int(d.get(clave, 0))
        hosts = ", ".join(sorted(d.get("por_host", {})))
        print(f"  {cadena:<11}{d.get('peticiones', 0):>10,}{d.get('cache', 0):>10,}"
              f"{d.get('evitadas', 0):>10,}   {hosts[:40]}".replace(",", "."))
    print(f"  {'TOTAL':<11}{total['peticiones']:>10,}{total['cache']:>10,}"
          f"{total['evitadas']:>10,}".replace(",", "."))

    motivos: dict[str, int] = {}
    for d in datos.values():
        for motivo in d.get("motivos", []):
            motivos[motivo] = motivos.get(motivo, 0) + 1
    if motivos:
        print(f"  motivos de lo no pedido: {', '.join(sorted(motivos))}")
    print("\n  (las evitadas son decisiones de no pedir, contadas al tomarlas; no son una\n"
          "   estimacion de lo que la cadena habria servido)")
    return 0


def varios(dias: int, hasta: date) -> int:
    print(f"Peticiones de los ultimos {dias} dias (hasta {hasta.isoformat()})\n")
    print(f"  {'fecha':<12}{'enviadas':>10}{'de cache':>10}{'evitadas':>10}  cadenas")
    for i in range(dias - 1, -1, -1):
        dia = (hasta - timedelta(days=i)).isoformat()
        datos = _lee(dia)
        if not datos:
            print(f"  {dia:<12}{'—':>10}{'—':>10}{'—':>10}  sin recuento")
            continue
        enviadas = sum(int(d.get("peticiones", 0)) for d in datos.values())
        cache = sum(int(d.get("cache", 0)) for d in datos.values())
        evitadas = sum(int(d.get("evitadas", 0)) for d in datos.values())
        print(f"  {dia:<12}{enviadas:>10,}{cache:>10,}{evitadas:>10,}  "
              f"{len(datos)}".replace(",", "."))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--fecha", help="dia a mirar (por defecto, hoy)")
    ap.add_argument("--dias", type=int, help="mirar los ultimos N dias")
    a = ap.parse_args(argv)
    if a.dias:
        return varios(a.dias, date.fromisoformat(a.fecha) if a.fecha else date.today())
    return un_dia(a.fecha or date.today().isoformat())


if __name__ == "__main__":
    sys.exit(main())
