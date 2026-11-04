"""Rehace el dia SIN red: bronze ya esta -> silver, gold, emparejador, manifiesto, publicacion.

Es el tramo final del ciclo diario (`projects/cesta/run.py`) sin los colectores, para
cuando el crudo del dia ya esta en disco y solo falta convertirlo. No pide una sola
pagina a ninguna cadena.

    uv run python -m scripts.rehacer_dia_sin_red
"""
from __future__ import annotations

import importlib
import time


def main() -> int:
    t0 = time.monotonic()
    fallos: list[str] = []

    print("=== 1. pipeline (bronze -> silver -> gold), sin publicar ===", flush=True)
    try:
        bien = importlib.import_module("projects.cesta.pipeline").main(publicar=False) == 0
        if not bien:
            fallos.append("pipeline")
    except Exception as exc:  # noqa: BLE001
        print(f"[pipeline] FALLO: {type(exc).__name__}: {exc}", flush=True)
        fallos.append("pipeline")

    if not fallos:
        print("\n=== 2. emparejador ===", flush=True)
        try:
            importlib.import_module("projects.cesta.emparejar").main([])
        except Exception as exc:  # noqa: BLE001
            print(f"[emparejar] FALLO: {type(exc).__name__}: {exc}", flush=True)
            fallos.append("emparejar")

    if not fallos:
        print("\n=== 3. manifiesto y publicacion ===", flush=True)
        try:
            importlib.import_module("core.manifiesto").escribe()
        except Exception as exc:  # noqa: BLE001
            print(f"[manifiesto] aviso: {type(exc).__name__}: {exc}", flush=True)
        try:
            importlib.import_module("core.publicacion").publicar()
        except Exception as exc:  # noqa: BLE001
            print(f"[publicacion] FALLO: {type(exc).__name__}: {exc}", flush=True)
            fallos.append("publicacion")

    print(f"\n=== rehacer dia: {time.monotonic() - t0:.0f}s, fallos: {fallos or 'ninguno'} ===")
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
