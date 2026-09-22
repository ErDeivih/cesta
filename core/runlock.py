"""Bloqueo entre procesos para que dos recolecciones no escriban a la vez."""
from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path

from core import config


@contextmanager
def ejecucion_exclusiva(path: Path | None = None):
    path = path or config.DATA / "ejecucion.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    fh = path.open("a+b")
    if path.stat().st_size == 0:
        fh.write(b"0")
        fh.flush()
    fh.seek(0)
    try:
        if os.name == "nt":
            import msvcrt

            try:
                msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                raise RuntimeError("ya hay otra ejecucion de cesta en marcha") from exc
        else:
            import fcntl

            try:
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                raise RuntimeError("ya hay otra ejecucion de cesta en marcha") from exc
        yield
    finally:
        try:
            if os.name == "nt":
                fh.seek(0)
                msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        except OSError:
            pass
        fh.close()
