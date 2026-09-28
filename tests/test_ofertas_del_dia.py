"""Las ofertas vigentes: la particion del ultimo dia, y no silver entero.

**Esto no es una optimizacion de gusto: es una lentitud medida en el contenedor.** La consulta de
las ofertas buscaba el ultimo dia asi:

    FROM read_parquet('/datos/silver/**/*.parquet', hive_partitioning=1)
    WHERE fecha = (SELECT max(fecha) FROM read_parquet(...))

o sea **recorrer todo silver dos veces** (1.066.573 filas, 106 particiones, 105 MB) para quedarse
con un dia. Medido dentro de `cesta-api-1` con `data/debug/silver.py` el 27 de septiembre de 2026:
**2,10 s** la consulta de antes y **0,04 s** la de ahora, con el mismo resultado (7.908 ofertas).
Y como `_candidatos` la llama, los tres endpoints de la cesta la pagaban: medido con
`data/debug/peticiones.py`, `/api/listas/{id}` 2,07 s, `/donde` 2,66 s y `/reparto` 4,50 s, y la
pantalla de la lista -- que pide las tres a la vez -- tardaba **4,3 s** en quedarse quieta, en la
pantalla que se usa de pie en la tienda.

La fecha ya estaba en el nombre de la carpeta (`fuente=dia/fecha=2026-09-28`): preguntarsela a
los parquet era leer 105 MB para nada.
"""
from __future__ import annotations

import ast
import dataclasses
import pathlib

import polars as pl
import pytest

from plataforma.api import cesta

CESTA = pathlib.Path(__file__).resolve().parents[1] / "plataforma" / "api" / "cesta.py"


def _escribe(raiz: pathlib.Path, fuente: str, fecha: str, ofertas: dict[str, str]) -> None:
    """Una particion de silver como las de verdad: la fuente y la fecha, en la ruta.

    Las claves son el `id_fuente` **pelado** (`147509`), como en silver de verdad: la clave que
    usa el codigo (`fuente:id_fuente`) la compone la consulta. Escribirla ya compuesta daba
    `dia:dia:1` y la prueba decia que no habia ofertas cuando si las habia.
    """
    carpeta = raiz / "silver" / f"fuente={fuente}" / f"fecha={fecha}"
    carpeta.mkdir(parents=True, exist_ok=True)
    pl.DataFrame({
        "id_fuente": list(ofertas),
        "promo_txt": list(ofertas.values()),
    }).write_parquet(carpeta / "productos.parquet")


@pytest.fixture
def silver(tmp_path, monkeypatch):
    """Un silver de mentira, con su conexion en memoria y sin tocar el de casa."""
    import duckdb

    raiz = tmp_path / "datos"
    monkeypatch.setattr(cesta, "AJUSTES",
                        dataclasses.replace(cesta.AJUSTES, gold=raiz / "gold"))
    monkeypatch.setattr(cesta, "conexion", duckdb.connect)
    monkeypatch.setattr(cesta, "_PROMOS_POR_FECHA", {})
    return raiz


def test_se_lee_la_particion_del_ultimo_dia_y_nada_mas(silver):
    """La de ayer no se mira: la oferta vigente es la del ultimo dia que hay escrito."""
    _escribe(silver, "dia", "2026-09-27", {"1": "2a unidad -50%"})
    _escribe(silver, "dia", "2026-09-28", {"1": "3x2"})
    _escribe(silver, "aldi", "2026-09-28", {"7": "llevate 2"})
    # Una cadena que no ha rascado hoy: su ultima particion es la de ayer.
    _escribe(silver, "mercadona", "2026-09-27", {"9": "2x1"})

    assert cesta._ultima_fecha_silver() == "2026-09-28"
    ofertas = cesta._promos_vigentes({"dia:1", "aldi:7", "mercadona:9"})
    # La de hoy, la de la otra cadena de hoy... y **la de mercadona no**: se queda con el ultimo
    # dia de silver, no con el ultimo dia de cada cadena. Es lo que hacia antes y no se cambia.
    assert ofertas == {"dia:1": "3x2", "aldi:7": "llevate 2"}, ofertas


def test_el_dia_siguiente_se_lee_sin_reiniciar(silver):
    """La cache es **por fecha**: una pasada del dia no puede quedarse invisible."""
    _escribe(silver, "dia", "2026-09-27", {"1": "2x1"})
    assert cesta._promos_vigentes({"dia:1"}) == {"dia:1": "2x1"}
    # Llega el dia siguiente: la oferta cambia y hay que verlo sin reiniciar el contenedor.
    _escribe(silver, "dia", "2026-09-28", {"1": "3x2"})
    assert cesta._ultima_fecha_silver() == "2026-09-28"
    assert cesta._promos_vigentes({"dia:1"}) == {"dia:1": "3x2"}


def test_sin_silver_no_se_cae_y_no_hay_ofertas(silver):
    """Sin silver, la cesta tiene que seguir dando un total (el `except` de siempre)."""
    assert cesta._ultima_fecha_silver() is None
    assert cesta._promos_vigentes({"dia:1"}) == {}


def test_la_consulta_no_vuelve_a_recorrer_silver_entero():
    """Lo que costo 2,10 s en el contenedor, escrito para que no vuelva."""
    fuente = CESTA.read_text(encoding="utf-8")
    assert "SELECT max(fecha)" not in _solo_el_codigo(fuente), (
        "ha vuelto la consulta que recorria todo silver dos veces por peticion: 2,10 s en el "
        "contenedor, y la pantalla de la lista paga tres veces")
    assert 'glob("fuente=*/fecha=*")' in fuente, (
        "la fecha del ultimo dia se saca de los nombres de las carpetas, no de los parquet")
    # Y la razon, donde se lee.
    assert "data/debug/silver.py" in fuente and "2,10 s" in fuente, (
        "el numero medido tiene que estar al lado del codigo que lo arregla")


def _solo_el_codigo(fuente: str) -> str:
    """El codigo sin sus propios comentarios.

    Hace falta porque aqui los comentarios **citan la consulta que se quito** para contar por que
    se quito, y buscarla a pelo encontraba la explicacion en vez del codigo.
    """
    arbol = ast.parse(fuente)
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Module | ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            texto = ast.get_docstring(nodo, clean=False)
            if texto:
                fuente = fuente.replace(texto, "")
    return fuente

