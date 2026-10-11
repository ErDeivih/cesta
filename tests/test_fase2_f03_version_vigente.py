"""F03 (fase 2): **que version se sirve, sin arrastrar polars.**

Por que existe
--------------
El pendiente declarado de S01 es que la API lea la version publicada con `rutas()`. *Y el propio
documento de estado avisa de por que no se hizo de la forma obvia*: `core/publicacion.py` **importa
polars**, y meterlo en la API es meter polars en el proceso que atiende a quien compra --
**«causo reinicios de `cesta-api` el 21 de septiembre»**--. El camino que el documento apunta es
*«sacar la lectura a un modulo pequeno sin polars que usen los dos»*.

Ese modulo es `core/version_vigente.py`, y esto lo comprueba.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from core import version_vigente as vv


@pytest.fixture
def gold(tmp_path):
    """Un gold de mentira con una version publicada y sus ficheros."""
    for nombre in ("grupos.parquet", "enlaces.parquet"):
        (tmp_path / nombre).write_bytes(b"suelto")
    (tmp_path / "v20261007-103000").mkdir()
    for nombre in ("grupos.parquet", "enlaces.parquet"):
        (tmp_path / "v20261007-103000" / nombre).write_bytes(b"publicado")
    (tmp_path / vv.PUNTERO).write_text(
        json.dumps({"version": "20261007-103000", "publicado_en": "2026-10-07T10:30:00"}),
        encoding="utf-8")
    return tmp_path


def test_sin_puntero_se_lee_el_catalogo_suelto(tmp_path):
    """**El fallback conservador**: esto entra sin migrar nada de golpe."""
    (tmp_path / "grupos.parquet").write_bytes(b"suelto")

    assert vv.version_actual(tmp_path) is None
    assert vv.ruta(tmp_path, "grupos.parquet") == tmp_path / "grupos.parquet"


def test_con_puntero_se_lee_la_version(gold):
    """*Y no el suelto: son dos cosas distintas y confundirlas es servir lo que no se publico.*"""
    assert vv.version_actual(gold) == "20261007-103000"
    assert vv.publicado_en(gold) == "2026-10-07T10:30:00"
    assert vv.ruta(gold, "grupos.parquet") == gold / "v20261007-103000" / "grupos.parquet"
    assert vv.ruta(gold, "grupos.parquet").read_bytes() == b"publicado"


def test_una_version_explicita_es_la_que_manda(gold):
    """**Lo que impide mezclar**: *quien pide dos ficheros resuelve la version una vez y la pasa.*

    *Sin esto, resolver el puntero dos veces puede dar `grupos` de una publicacion y `enlaces` de la
    siguiente -- la mezcla que S01 prohibe.*
    """
    (gold / "v20260901-090000").mkdir()
    (gold / "v20260901-090000" / "grupos.parquet").write_bytes(b"vieja")

    assert vv.ruta(gold, "grupos.parquet", "20260901-090000").read_bytes() == b"vieja"
    # Y el puntero no se ha tocado por pedir una version concreta.
    assert vv.version_actual(gold) == "20261007-103000"


def test_un_puntero_ilegible_es_como_no_tenerlo(tmp_path):
    """*Mejor servir el catalogo suelto que reventar la peticion porque un JSON quedo cortado.*"""
    (tmp_path / "grupos.parquet").write_bytes(b"suelto")
    (tmp_path / vv.PUNTERO).write_text("{esto no es json", encoding="utf-8")

    assert vv.version_actual(tmp_path) is None
    assert vv.publicado_en(tmp_path) is None
    assert vv.ruta(tmp_path, "grupos.parquet") == tmp_path / "grupos.parquet"


def test_el_sello_es_el_de_lo_que_se_lee(gold):
    """**Cachear por el `mtime` del suelto mientras se sirve una version es cachear por otro fichero.**

    *Y el dia que la API lea la version, la cache tiene que invalidarse **al publicar**, que es justo
    cuando cambia lo que se lee.*
    """
    import os
    import time

    sello_suelto = vv.sello(gold, "grupos.parquet", "20261007-103000")
    # Se toca el suelto: **el sello de la version no puede cambiar**.
    time.sleep(0.01)
    os.utime(gold / "grupos.parquet")
    assert vv.sello(gold, "grupos.parquet", "20261007-103000") == sello_suelto

    # Y se toca la version: **ahi si**.
    os.utime(gold / "v20261007-103000" / "grupos.parquet")
    assert vv.sello(gold, "grupos.parquet", "20261007-103000") != sello_suelto


def test_no_arrastra_polars():
    """**La restriccion, comprobada y no confiada.** *Es la razon por la que este modulo existe.*

    *`sys.modules` despues de importarlo, en un interprete limpio: si polars -- o duckdb, o cualquier
    otra cosa pesada -- entrara por la puerta de atras, se veria aqui.*
    """
    codigo = (
        "import sys; import core.version_vigente; "
        "pesados = [m for m in ('polars', 'duckdb', 'pyarrow') if m in sys.modules]; "
        "print(','.join(pesados))"
    )
    hecho = subprocess.run([sys.executable, "-c", codigo],
                           cwd=Path(__file__).resolve().parents[1],
                           capture_output=True, text=True, timeout=120)
    assert hecho.returncode == 0, hecho.stderr[-400:]
    assert hecho.stdout.strip() == "", (
        f"`core/version_vigente` tiene que poder usarse desde la API: arrastra {hecho.stdout.strip()}")
