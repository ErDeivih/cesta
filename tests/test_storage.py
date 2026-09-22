"""El crudo es la unica capa irrecuperable: nunca debe sobrescribirse."""

import gzip

import pytest

from core import config, storage


def test_raw_es_inmutable_y_deduplica_el_mismo_contenido(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "ROOT", tmp_path)

    primero = storage.save_raw("fuente", "endpoint", b"version 1")
    repetido = storage.save_raw("fuente", "endpoint", b"version 1")
    segundo = storage.save_raw("fuente", "endpoint", b"version 2")

    assert primero == repetido
    assert primero != segundo
    assert gzip.decompress(primero.read_bytes()) == b"version 1"
    assert gzip.decompress(segundo.read_bytes()) == b"version 2"
    assert len(list(primero.parent.glob("*.json.gz"))) == 2
    assert storage.load_raw_bytes("fuente", "endpoint") == b"version 2"


def test_parquet_se_escribe_sin_dejar_temporales(tmp_path):
    import polars as pl

    destino = tmp_path / "tabla.parquet"
    storage.write_parquet_file(pl.DataFrame({"x": [1, 2]}), destino)
    assert pl.read_parquet(destino)["x"].to_list() == [1, 2]
    assert not list(tmp_path.glob("*.tmp"))


def test_load_raw_reciente_busca_hacia_atras(tmp_path):
    """Para lo que no cambia de un dia para otro, como el indice de secciones."""
    from datetime import timedelta
    from unittest import mock

    from core import config, storage

    with mock.patch.object(storage, "ROOT", tmp_path):
        hoy = config.hoy_local()
        anteayer = hoy - timedelta(days=2)
        storage.save_raw("carrefour", "sitemap-index", b"<loc>viejo</loc>", day=anteayer)
        assert storage.load_raw_bytes("carrefour", "sitemap-index") is None   # hoy no hay
        encontrado = storage.load_raw_reciente("carrefour", "sitemap-index")
        assert encontrado is not None
        cuerpo, dia = encontrado
        assert cuerpo == b"<loc>viejo</loc>" and dia == anteayer


def test_load_raw_reciente_no_se_va_demasiado_atras(tmp_path):
    from datetime import timedelta
    from unittest import mock

    from core import config, storage

    with mock.patch.object(storage, "ROOT", tmp_path):
        muy_viejo = config.hoy_local() - timedelta(days=40)
        storage.save_raw("carrefour", "sitemap-index", b"x", day=muy_viejo)
        assert storage.load_raw_reciente("carrefour", "sitemap-index", dias=10) is None


# --- bronze no se borra nunca ----------------------------------------------
#
# El 18 de septiembre de 2026 se paso un dia entero conjeturando quien habia
# borrado una particion de bronze. La habian apartado a mano, a proposito y bien;
# pero la conjetura duro porque nada en el codigo decia que borrarla no fuera
# posible. Ahora lo dice, y ademas hay una forma correcta de apartar.

def test_no_se_puede_borrar_nada_de_bronze(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "ROOT", tmp_path)
    carpeta = tmp_path / "bronze" / "fuente=alcampo" / "fecha=2026-09-18"
    carpeta.mkdir(parents=True)
    with pytest.raises(storage.BorradoProhibido) as exc:
        storage.comprueba_borrable(carpeta)
    assert "se **aparta**" in str(exc.value)


def test_tampoco_la_raiz_de_bronze_ni_gold(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "ROOT", tmp_path)
    for capa in ("bronze", "gold"):
        (tmp_path / capa).mkdir(parents=True, exist_ok=True)
        with pytest.raises(storage.BorradoProhibido):
            storage.comprueba_borrable(tmp_path / capa)


def test_el_crudo_si_se_puede_borrar(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "ROOT", tmp_path)
    carpeta = tmp_path / "raw" / "fuente=aldi" / "fecha=2026-08-01"
    carpeta.mkdir(parents=True)
    storage.comprueba_borrable(carpeta)          # no revienta


def test_apartar_deja_el_motivo_en_el_nombre_y_conserva_el_dato(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "ROOT", tmp_path)
    carpeta = tmp_path / "bronze" / "fuente=alcampo" / "fecha=2026-09-18"
    carpeta.mkdir(parents=True)
    (carpeta / "part.parquet").write_bytes(b"datos")

    destino = storage.aparta(carpeta, "sin frescos")

    assert destino.name == "alcampo-2026-09-18-sin-frescos"
    assert (destino / "part.parquet").read_bytes() == b"datos"
    assert not carpeta.exists()


def test_apartar_dos_veces_lo_mismo_no_pisa_lo_de_antes(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "ROOT", tmp_path)
    for _ in range(2):
        carpeta = tmp_path / "bronze" / "fuente=alcampo" / "fecha=2026-09-18"
        carpeta.mkdir(parents=True, exist_ok=True)
    storage.aparta(tmp_path / "bronze" / "fuente=alcampo" / "fecha=2026-09-18",
                   "sin frescos")
    (tmp_path / "bronze" / "fuente=alcampo" / "fecha=2026-09-18").mkdir(parents=True)
    with pytest.raises(FileExistsError):
        storage.aparta(tmp_path / "bronze" / "fuente=alcampo" / "fecha=2026-09-18",
                       "sin frescos")


# --- una prueba no puede escribir en los datos de verdad --------------------

def test_una_prueba_no_puede_escribir_en_los_datos_de_verdad(monkeypatch):
    """El 21 de septiembre de 2026 `pytest` se cargó la captura de Carrefour.

    16.560 productos reemplazados por 199 de mentira con la categoría "slug".
    Una prueba del colector llamaba a `main()`, `main()` daba el día por bueno y
    escribía su bronze, y el bronze que escribía era el de verdad.

    Lo peor no fue el fallo: fue que estaba **escrito en las instrucciones**. El
    primer comando que se pide antes de fiarse del día es correr las pruebas, y
    correr las pruebas destruía el día.
    """
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "de mentira")
    real = config.RAIZ / "data" / "bronze" / "fuente=carrefour" / "fecha=2026-09-21"
    with pytest.raises(storage.EscrituraDePrueba):
        storage.comprueba_no_es_una_prueba(real / "part.parquet")


def test_fuera_de_pytest_no_estorba(monkeypatch):
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    storage.comprueba_no_es_una_prueba(config.RAIZ / "data" / "bronze" / "x.parquet")


def test_una_prueba_si_puede_escribir_en_su_carpeta_temporal(monkeypatch, tmp_path):
    """Que es lo que tenía que haber hecho desde el principio."""
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "de mentira")
    storage.comprueba_no_es_una_prueba(tmp_path / "bronze" / "part.parquet")
