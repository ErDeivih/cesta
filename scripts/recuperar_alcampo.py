"""Recupera el día cuando Alcampo se queda sin captura pero su crudo está en disco.

**Por qué existe.** El 7/11/2026 Alcampo falló por el reto de AWS WAF: se quedó en 22.897
productos con 1 error, el colector rechazó la captura por incompleta y no escribió la partición
de bronce. El crudo ya estaba en `data/raw/`; un `ejecutar.bat --forzar` lo reutilizó y recuperó
el día en 272 s. Esto automatiza exactamente esa recuperación, una vez al día y solo para
Alcampo.

**Qué hace.** Mira `runs.csv` y el bronce de hoy. Si Alcampo no tiene su captura buena, hay crudo
de hoy y no se ha intentado ya, lanza `projects.cesta.run --solo alcampo
--sin-comprobar-precios` (que reutiliza el crudo y publica) y deja constancia. Si no hay crudo,
no inventa: avisa de que no se puede recuperar desde el crudo.

Códigos de salida:
  0  no había nada que recuperar, o se recuperó
  1  se intentó y no se pudo
  2  hay una pasada en curso: no se toca
  3  no hay crudo del día: no se puede recuperar desde el crudo
  4  ya se intentó hoy
"""
from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

from core import config

RAIZ = Path(__file__).resolve().parents[1]
FUENTE = "alcampo"
MARCA = "recuperacion-alcampo"


def _hoy_local() -> str:
    return str(config.hoy_local())


def _ultima_pasada(datos: Path, fuente: str) -> dict | None:
    ruta = datos / "runs.csv"
    if not ruta.is_file():
        return None
    ultima = None
    with ruta.open(newline="", encoding="utf-8") as fh:
        for fila in csv.DictReader(fh):
            if fila.get("fuente") == fuente:
                ultima = fila
    return ultima


def _bronce(datos: Path, fecha: str) -> bool:
    carpeta = datos / "bronze" / f"fuente={FUENTE}" / f"fecha={fecha}"
    return carpeta.is_dir() and any(carpeta.glob("*.parquet"))


def _crudo(datos: Path, fecha: str) -> bool:
    carpeta = datos / "raw" / f"fuente={FUENTE}" / f"fecha={fecha}"
    return carpeta.is_dir() and any(carpeta.iterdir())


def necesita_recuperar(datos: Path, fecha: str) -> bool:
    """¿Alcampo falló **hoy** y hay crudo para reintentar sin volver a la red?"""
    if _bronce(datos, fecha):
        return False
    pasada = _ultima_pasada(datos, FUENTE)
    if pasada:
        # **La fila tiene que ser de HOY.** Una pasada buena de ayer no dice nada de hoy; si
        # se mira solo `ok`, el vigilante no recuperaría el día que Alcampo no ha corrido.
        ts = pasada.get("ts", "")
        if ts.startswith(fecha) and pasada.get("ok", "").lower() == "true":
            return False
    return _crudo(datos, fecha)


def _marca(datos: Path, fecha: str) -> Path:
    return datos / f"{MARCA}-{fecha}.txt"


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Recupera Alcampo desde el crudo si falló hoy.")
    ap.add_argument("--datos", help="carpeta de datos (por defecto, data/)")
    ap.add_argument("--fecha", help="día AAAA-MM-DD (por defecto, hoy en Madrid)")
    ap.add_argument("--no-lanzar", action="store_true",
                    help="solo decir si se podría recuperar; no lanza la pasada")
    args = ap.parse_args(argv)

    datos = Path(args.datos) if args.datos else config.DATA
    fecha = args.fecha or _hoy_local()

    if (datos / "ejecucion_en_curso.txt").exists():
        print("hay una pasada en curso: no se relanza nada")
        return 2
    if not necesita_recuperar(datos, fecha):
        print("nada que recuperar: Alcampo tiene bronce o no hay crudo de hoy")
        return 0
    if _marca(datos, fecha).exists():
        print(f"ya se intentó recuperar {FUENTE} el {fecha}")
        return 4
    if args.no_lanzar:
        print(f"se recuperaría {FUENTE} del {fecha} desde el crudo")
        return 0

    print(f"recuperando {FUENTE} del {fecha} desde el crudo...")
    proc = subprocess.run(
        [sys.executable, "-m", "projects.cesta.run", "--solo", FUENTE,
         "--sin-comprobar-precios"],
        cwd=RAIZ,
    )
    _marca(datos, fecha).write_text(
        f"intento de recuperacion de {FUENTE} {fecha}; codigo {proc.returncode}\n",
        encoding="utf-8",
    )
    if proc.returncode == 0 and _bronce(datos, fecha):
        (datos / "INGESTA-DETENIDA.txt").unlink(missing_ok=True)
        print(f"{FUENTE} recuperado: bronce del {fecha} presente")
        return 0
    print(f"{FUENTE} no se pudo recuperar: mira data/ejecuciones.log")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
