from pathlib import Path

import pytest

from core.runlock import ejecucion_exclusiva


def test_impide_dos_ejecuciones_simultaneas(tmp_path: Path):
    lock = tmp_path / "run.lock"
    with (ejecucion_exclusiva(lock),
          pytest.raises(RuntimeError, match="otra ejecucion"),
          ejecucion_exclusiva(lock)):
        pass


def test_el_bloqueo_se_libera_al_salir(tmp_path: Path):
    lock = tmp_path / "run.lock"
    with ejecucion_exclusiva(lock):
        pass
    with ejecucion_exclusiva(lock):
        pass
