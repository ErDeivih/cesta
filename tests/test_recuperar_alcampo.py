"""La recuperación de Alcampo desde el crudo: que decida bien y no invente.

No se lanza un `run.py` de verdad en las pruebas: se comprueba la decisión (¿hay bronce?,
¿falló la pasada?, ¿hay crudo?), el modo `--no-lanzar` y que una pasada en curso no se toca.
"""
from __future__ import annotations

import csv
from pathlib import Path

from scripts import recuperar_alcampo as rec

HOY = "2026-11-08"


def _datos(tmp_path: Path) -> Path:
    datos = tmp_path / "data"
    datos.mkdir()
    return datos


def _runs(datos: Path, ok: bool) -> None:
    with (datos / "runs.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["ts", "fuente", "filas", "errores", "segundos", "ok"])
        w.writerow([f"{HOY}T10:00:00+00:00", "alcampo", 100, 1 if not ok else 0, 5, str(ok)])


def _raw(datos: Path) -> None:
    carpeta = datos / "raw" / "fuente=alcampo" / f"fecha={HOY}"
    carpeta.mkdir(parents=True)
    (carpeta / "a.json.gz").write_bytes(b"x")


def _bronce(datos: Path) -> None:
    carpeta = datos / "bronze" / "fuente=alcampo" / f"fecha={HOY}"
    carpeta.mkdir(parents=True)
    (carpeta / "part.parquet").write_bytes(b"x")


def test_sin_bronce_con_pasada_fallida_y_crudo_se_puede_recuperar(tmp_path):
    datos = _datos(tmp_path)
    _runs(datos, ok=False)
    _raw(datos)

    assert rec.necesita_recuperar(datos, HOY) is True
    assert rec.main(["--datos", str(datos), "--fecha", HOY, "--no-lanzar"]) == 0


def test_sin_crudo_no_se_puede_recuperar_desde_el_crudo(tmp_path):
    datos = _datos(tmp_path)
    _runs(datos, ok=False)

    assert rec.necesita_recuperar(datos, HOY) is False
    assert rec.main(["--datos", str(datos), "--fecha", HOY, "--no-lanzar"]) == 0


def test_si_el_bronce_ya_esta_no_hay_nada_que_hacer(tmp_path):
    datos = _datos(tmp_path)
    _runs(datos, ok=False)
    _raw(datos)
    _bronce(datos)

    assert rec.necesita_recuperar(datos, HOY) is False


def test_una_pasada_en_curso_no_se_toca(tmp_path):
    datos = _datos(tmp_path)
    _runs(datos, ok=False)
    _raw(datos)
    (datos / "ejecucion_en_curso.txt").write_text(f"{HOY} 10:00", encoding="utf-8")

    assert rec.main(["--datos", str(datos), "--fecha", HOY, "--no-lanzar"]) == 2


def test_una_pasada_buena_de_ayer_no_impide_recuperar_hoy(tmp_path):
    """La fila de ayer dice que ayer fue bien; hoy no hay bronce ni pasada, así que se recupera."""
    datos = _datos(tmp_path)
    _runs(datos, ok=True)
    # La fila del helper es de HOY; se reescribe con la fecha de ayer.
    ruta = datos / "runs.csv"
    ruta.write_text(
        "ts,fuente,filas,errores,segundos,ok\n"
        "2026-11-07T10:00:00+00:00,alcampo,100,0,5,True\n",
        encoding="utf-8",
    )
    _raw(datos)

    assert rec.necesita_recuperar(datos, HOY) is True


def test_ya_intentado_hoy_no_se_repite(tmp_path):
    datos = _datos(tmp_path)
    _runs(datos, ok=False)
    _raw(datos)
    (datos / f"{rec.MARCA}-{HOY}.txt").write_text("ya", encoding="utf-8")

    assert rec.main(["--datos", str(datos), "--fecha", HOY, "--no-lanzar"]) == 4
