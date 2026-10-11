"""F03 (fase 2): **la publicacion va antes de lo que se calcula despues.**

Por que existe
--------------
La revision de fase 2 lo dejo como hallazgo: *«`pipeline.py` todavia captura fallo de publicar; **el
ciclo reconstruye grupos despues del pipeline**. Auditar cierre de version y estado diario.»*

**Y F03 lo dice como criterio**: *«Construir/publicar **todos los derivados de una version antes del
puntero**»*.

La cadena, medida el 13 de octubre de 2026
------------------------------------------
    run.py:235   pipeline.main()   -> escribe gold y PUBLICA (sella la version)
    run.py:245   emparejar.main()  -> reescribe data/gold/grupos.parquet y enlaces.parquet

**Y quien lee, lee la version**: `publicacion.ruta()` resuelve el puntero y devuelve
`v<version>/grupos.parquet`, no el gold suelto. *El gold suelto es la copia de trabajo; la version es
lo que se sirve.*

Asi que **lo que `emparejar` calcula no lo ve nadie**: se escribe en gold, y los lectores siguen con la
version que se publico **antes**, que es la de antes del emparejado.

**Medido sobre el estado real**, no deducido: la ultima version publicada (`20261011-124542`) tiene
`grupos.parquet` y `enlaces.parquet` **distintos** de los de `data/gold` -- **los dos unicos ficheros que
escribe `emparejar`** --, y los otros cuatro identicos. *Los cuatro que nadie reescribe despues coinciden;
los dos que si, no.*
"""
from __future__ import annotations

from datetime import datetime

import polars as pl
import pytest

from core import publicacion
from core.storage import write_parquet_file
from projects.cesta import pipeline


@pytest.fixture
def gold(tmp_path, monkeypatch):
    """El mismo gold de mentira que usa `tests/test_publicacion.py`: **no se toca el de verdad**."""
    monkeypatch.setattr(publicacion, "GOLD", tmp_path)
    monkeypatch.setattr(publicacion, "PUNTERO", tmp_path / "actual.json")
    for nombre in publicacion.FICHEROS:
        pl.DataFrame({"x": [1]}).write_parquet(tmp_path / nombre)
    return tmp_path


def test_lo_que_se_escribe_despues_de_publicar_no_llega_a_quien_lee(gold):
    """**El hallazgo, reproducido.** *Publicar fija la version; lo que se escriba despues no entra.*

    *Y no es que el lector vea un fichero viejo por casualidad: `ruta()` resuelve el puntero, asi que lo
    que se sirve es la version y **nunca** el gold suelto mientras haya version.*

    **Se escribe con `write_parquet_file`, que es el escritor del proyecto** -- renombra, no escribe en
    el sitio --: *con un `write_parquet` a secas la prueba mediria otra cosa, y de hecho lo hacia.*
    """
    # 1. El pipeline escribe gold y publica. **Es lo que hace hoy, dentro de `pipeline.main()`.**
    write_parquet_file(pl.DataFrame({"x": [1]}), gold / "grupos.parquet")
    publicacion.adoptar(datetime(2026, 10, 7, 10, 0, 0))

    # 2. Y despues `emparejar` reescribe grupos en gold, que es lo que hace el ciclo.
    write_parquet_file(pl.DataFrame({"x": [2]}), gold / "grupos.parquet")

    # **Lo que lee quien compra es la version**, no el gold suelto.
    publicado = pl.read_parquet(publicacion.ruta("grupos.parquet"))
    assert publicado["x"].to_list() == [1], "el lector ve lo que se publico"

    # **Y por eso lo que escribio `emparejar` no lo ve nadie.**
    en_gold = pl.read_parquet(gold / "grupos.parquet")
    assert en_gold["x"].to_list() == [2], "el gold suelto si tiene lo de despues"
    assert publicado["x"].to_list() != en_gold["x"].to_list(), (
        "lo que se calcula DESPUES de publicar no llega a quien lee: la publicacion tiene que ir "
        "al final de todo lo que escribe gold, no en medio")


def test_publicar_despues_si_recoge_lo_que_se_escribio_antes(gold):
    """*El otro lado, y es el arreglo*: si se publica **despues**, el lector ve lo ultimo.

    **No basta con que el fichero este escrito**: tiene que estar dentro de la version.
    """
    write_parquet_file(pl.DataFrame({"x": [1]}), gold / "grupos.parquet")
    write_parquet_file(pl.DataFrame({"x": [2]}), gold / "grupos.parquet")   # el emparejado, primero
    publicacion.adoptar(datetime(2026, 10, 7, 10, 0, 0))                    # y se publica despues

    assert pl.read_parquet(publicacion.ruta("grupos.parquet"))["x"].to_list() == [2]


def test_una_version_publicada_no_se_muta_si_el_escritor_renombra(gold):
    """**El enlace duro aguanta, pero solo porque los escritores renombran.** *Y eso hay que fijarlo.*

    `publicar()` **no copia**: hace un enlace duro (`os.link`) para no duplicar un fichero de 195 MB.
    *Eso significa que la version publicada y el gold suelto **son el mismo inodo** al publicar.*

    **Lo que la salva es que `write_parquet_file` escribe en un temporal y renombra**: el gold suelto pasa
    a ser otro inodo y la version conserva el suyo. *Un escritor que escribiera **en el sitio** mutaria
    todas las versiones publicadas que compartan ese inodo -- hacia atras en el tiempo.*

    *Esta prueba fija la invariante: si alguien cambia el escritor por uno que no renombre, salta aqui.*
    """
    write_parquet_file(pl.DataFrame({"x": [1]}), gold / "grupos.parquet")
    publicacion.adoptar(datetime(2026, 10, 7, 10, 0, 0))

    # El escritor del proyecto: temporal y renombrado.
    write_parquet_file(pl.DataFrame({"x": [2]}), gold / "grupos.parquet")

    publicado = pl.read_parquet(publicacion.ruta("grupos.parquet"))
    suelto = pl.read_parquet(gold / "grupos.parquet")
    assert publicado["x"].to_list() == [1], "la version publicada no puede cambiar sola"
    assert suelto["x"].to_list() == [2]


def test_el_pipeline_dice_que_ha_fallado_si_no_puede_publicar(gold, monkeypatch):
    """**La otra mitad del hallazgo**: *«`pipeline.py` todavia captura fallo de publicar»*.

    `main()` publica dentro de un `try` y, si falla, **lo imprime y devuelve 0**. *Y quien lo llama,
    `run.py:235`, **descarta el resultado**: `importlib.import_module(...).main()` sin mirarlo.* Asi que
    un fallo de publicacion **no llega al veredicto del dia**, y el puntero se queda donde estaba sin
    que nadie se entere.

    *Se sustituyen los colaboradores, no el pipeline: lo que se prueba es **el codigo de salida**, que es
    lo unico que el ciclo mira.*
    """
    monkeypatch.setattr(pipeline, "_cargar_bronze",
                        lambda: pl.DataFrame({"fuente": ["dia"], "fecha": ["2026-10-11"]}))
    monkeypatch.setattr(pipeline, "a_silver",
                        lambda df: pl.DataFrame({"fuente": ["dia"], "fecha": ["2026-10-11"]}))
    monkeypatch.setattr(pipeline, "write_parquet", lambda *a, **k: None)
    monkeypatch.setattr(pipeline, "_tirar_silver_posterior", lambda *a, **k: None)
    monkeypatch.setattr(pipeline, "a_gold", lambda *a, **k: None)
    monkeypatch.setattr(pipeline, "registrar_vistas", lambda *a, **k: None)
    monkeypatch.setattr(publicacion, "publicar",
                        lambda *a, **k: (_ for _ in ()).throw(OSError("disco lleno")))

    salida = pipeline.main()

    assert salida != 0, (
        "si no se puede publicar, el pipeline no puede decir que ha ido bien: el puntero se queda "
        "atras y el veredicto del dia tiene que verlo")


def test_el_resumen_distingue_capturado_procesado_y_publicado():
    """**La tercera pata del resumen.** *F03 pide que distinga **capturado / procesado / publicado**.*

    Decia lo capturado (`cadenas: 5 | todas de hoy`) y lo procesado (`catalogo: N productos`), **pero
    no que se esta sirviendo**: un dia que no publico se leia igual que uno que si. *Y `/api/estado`
    declaraba la incoherencia mientras el resumen callaba.*

    *Se lee la fuente, como hace `tests/test_la_pasada_publica.py` con la pasada: es lo unico
    comprobable sin montar un silver y un gold de mentira, y fija **las tres frases** que importan.*
    """
    fuente = (__import__("pathlib").Path(__file__).resolve().parents[1]
              / "projects" / "cesta" / "resumen.py").read_text(encoding="utf-8")

    assert '"  publicado: v' in fuente, "el resumen tiene que decir que version se sirve"
    assert "NO hay version publicada" in fuente, "y decir cuando no hay ninguna"
    assert "NO se esta sirviendo" in fuente, (
        "y avisar cuando hay catalogo procesado que no se sirve: *es lo que de verdad importa de esta "
        "linea, no que haya version, sino que la version no se quede atras*")

    # **Y el aviso tiene que poder compararse**: se calcula despues de tener las fechas del silver.
    pos_fechas = fuente.index("fechas = _fechas_por_cadena()")
    pos_publicado = fuente.index("publicado: v")
    assert pos_publicado > pos_fechas, (
        "lo publicado se compara con el silver, asi que se calcula despues de leer las fechas")
