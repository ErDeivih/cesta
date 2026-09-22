"""El reprocesador: rehacer bronze desde el crudo sin tocar la red.

Dos fallos reales, encontrados el 17 de septiembre de 2026:

1. **Se comia las fichas maestras.** Llamaba a `a_registro(producto)` con un
   solo argumento, y Mercadona y DIA tienen un segundo del que salen el EAN, el
   origen, los ingredientes y los alergenos. Al reprocesar Mercadona del dia,
   su bronze paso de 4.317 EAN a 0 y de 1.443 origenes a 0, y se escribio encima
   del bueno sin decir nada. Una herramienta cuyo unico proposito es recuperar
   no puede destruir en silencio.

2. **No sabia reprocesar Carrefour ni DIA**, que guardan HTML con extension
   .json.gz: el 42 % del catalogo no se podia reprocesar, o sea que arreglar
   esos dos parsers obligaba a volver a scrapear una web con Cloudflare y otra
   con Akamai.
"""
import polars as pl
import pytest

from projects.cesta.reprocesar import _perdidas

N = 100
IDS = [str(i) for i in range(N)]


@pytest.fixture
def viejo(tmp_path):
    camino = tmp_path / "part.parquet"
    pl.DataFrame({"id_fuente": IDS,
                  "ean": [f"840{i:05d}" for i in range(N)],
                  "origen": ["España"] * 30 + [None] * (N - 30)}).write_parquet(camino)
    return camino


def test_un_bronze_que_pierde_una_columna_entera_se_detecta(viejo):
    # Exactamente lo que le paso a Mercadona: 4.317 EAN -> 0.
    nuevo = pl.DataFrame({"id_fuente": IDS, "ean": [None] * N,
                          "origen": ["España"] * 30 + [None] * (N - 30)})
    assert any(x.startswith("ean:") for x in _perdidas(nuevo, viejo))


def test_una_columna_que_desaparece_tambien(viejo):
    nuevo = pl.DataFrame({"id_fuente": IDS})
    assert any("falta la columna" in x for x in _perdidas(nuevo, viejo))


def test_un_dia_con_menos_productos_no_da_falsa_alarma(viejo):
    # Que el catalogo tenga un 5 % menos de productos un dia es normal; que una
    # columna se quede a cero, no. El margen del 10 % separa las dos cosas.
    nuevo = pl.DataFrame({"id_fuente": IDS,
                          "ean": [f"840{i:05d}" for i in range(95)] + [None] * 5,
                          "origen": ["España"] * 30 + [None] * (N - 30)})
    assert _perdidas(nuevo, viejo) == []


def test_sin_bronze_previo_no_hay_nada_que_perder(tmp_path):
    nuevo = pl.DataFrame({"id_fuente": ["1"]})
    assert _perdidas(nuevo, tmp_path / "no-existe.parquet") == []


def test_carrefour_y_dia_saben_leer_su_propio_html():
    # La prueba barata que habria evitado once dias sin poder reprocesar:
    # comprobar que la funcion existe y que ante un HTML que no entiende
    # devuelve una lista vacia en vez de reventar.
    from projects.cesta.collectors import carrefour, dia
    for mod in (carrefour, dia):
        assert callable(getattr(mod, "productos_crudo", None)), mod.__name__
        assert mod.productos_crudo(b"<html>nada</html>") == []
        assert mod.productos_crudo(b"") == []
