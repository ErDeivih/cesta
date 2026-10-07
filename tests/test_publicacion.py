"""Puerta de S01: caida entre escrituras, rollback, concurrencia y fallback.

Cada prueba corresponde a una frase del criterio de aceptacion del paquete, y ninguna se apoya en
mirar el codigo: se ejecutan publicaciones de verdad sobre un directorio temporal.
"""
from __future__ import annotations

import json
from datetime import datetime

import polars as pl
import pytest

from core import publicacion


@pytest.fixture
def gold(tmp_path, monkeypatch):
    """Un gold de mentira, con sus ficheros sueltos y su puntero, para no tocar el de verdad."""
    monkeypatch.setattr(publicacion, "GOLD", tmp_path)
    monkeypatch.setattr(publicacion, "PUNTERO", tmp_path / "actual.json")
    for nombre in publicacion.FICHEROS:
        pl.DataFrame({"x": [1, 2]}).write_parquet(tmp_path / nombre)
    return tmp_path


def _momento(minuto: int) -> datetime:
    return datetime(2026, 10, 7, 10, minuto, 0)


def test_sin_version_publicada_se_lee_el_catalogo_suelto(gold):
    """Fallback conservador: esto entra sin migrar nada y sin romper a nadie."""
    assert publicacion.version_actual() is None
    assert publicacion.ruta("grupos.parquet") == gold / "grupos.parquet"


def test_publicar_adopta_el_catalogo_y_mueve_el_puntero(gold):
    version = publicacion.adoptar(_momento(0))
    assert publicacion.version_actual() == version
    assert (gold / f"v{version}" / "grupos.parquet").exists()
    # Nada a medias ni temporales sueltos.
    assert not list(gold.glob("*.tmp"))


def test_una_caida_entre_escrituras_no_mezcla_versiones(gold, monkeypatch):
    """El caso que da nombre al paquete: se cae escribiendo el segundo fichero."""
    publicacion.adoptar(_momento(0))
    buena = publicacion.version_actual()

    escritos = {"n": 0}
    original = pl.DataFrame.write_parquet

    def write_parquet(self, destino, *a, **k):
        escritos["n"] += 1
        if escritos["n"] == 2:
            raise OSError("se cayo el disco a mitad de la publicacion")
        return original(self, destino, *a, **k)

    monkeypatch.setattr(pl.DataFrame, "write_parquet", write_parquet)
    datos = {n: pl.DataFrame({"x": [9]}) for n in publicacion.FICHEROS}
    with pytest.raises(OSError):
        publicacion.publicar(datos, momento=_momento(30))

    # El puntero no se ha movido y la carpeta a medias se retiro: los lectores ven lo de antes.
    assert publicacion.version_actual() == buena
    assert not publicacion.carpeta_de("20261007-103000").exists()


def test_una_version_incompleta_no_se_publica(gold):
    """Si falta un fichero declarado, no hay publicacion: el puntero no se mueve."""
    (gold / "promos_por_cadena.parquet").unlink()
    with pytest.raises(publicacion.PublicacionIncompleta):
        publicacion.adoptar(_momento(0))
    assert publicacion.version_actual() is None


def test_rollback_a_la_version_anterior(gold):
    """Volver atras es apuntar a una anterior, con los datos intactos."""
    vieja = publicacion.adoptar(_momento(0))
    nueva = publicacion.publicar({n: pl.DataFrame({"x": [8]}) for n in publicacion.FICHEROS},
                                momento=_momento(30))
    assert publicacion.version_actual() == nueva
    publicacion.fijar(vieja)
    assert publicacion.version_actual() == vieja
    # Las dos versiones siguen ahi: publicar no borra.
    assert publicacion.versiones() == sorted([vieja, nueva])


def test_fijar_rechaza_una_version_incompleta(gold):
    publicacion.adoptar(_momento(0))
    rota = "20260101-000000"
    publicacion.carpeta_de(rota).mkdir()
    with pytest.raises(publicacion.PublicacionIncompleta):
        publicacion.fijar(rota)


def test_una_peticion_ve_una_sola_version(gold):
    """Concurrencia: quien lee varios ficheros los lee de la MISMA publicacion, o no los lee."""
    publicacion.adoptar(_momento(0))
    caminos = publicacion.rutas()
    assert len({c.parent for c in caminos.values()}) == 1, "una peticion ha mezclado versiones"
    # Y tras publicar otra, la peticion anterior sigue apuntando a la suya.
    publicacion.publicar({n: pl.DataFrame({"x": [7]}) for n in publicacion.FICHEROS},
                         momento=_momento(30))
    assert {c.parent for c in caminos.values()} == {publicacion.carpeta_de("20261007-100000")}


def test_publicar_no_sobrescribe_una_version_existente(gold):
    momento = _momento(0)
    publicacion.publicar({n: pl.DataFrame({"x": [1]}) for n in publicacion.FICHEROS}, momento=momento)
    with pytest.raises(ValueError):
        publicacion.publicar({n: pl.DataFrame({"x": [2]}) for n in publicacion.FICHEROS},
                             momento=momento)


def test_el_puntero_dice_que_se_publico(gold):
    version = publicacion.adoptar(_momento(0))
    datos = json.loads((gold / "actual.json").read_text(encoding="utf-8"))
    assert datos["version"] == version
    assert set(datos["ficheros"]) == set(publicacion.FICHEROS)
    assert datos["publicado_en"]
