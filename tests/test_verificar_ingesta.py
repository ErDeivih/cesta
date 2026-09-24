"""`verificar_ingesta`: la comprobacion de que lo que dio la cadena llego a bronze.

Lo que se fija aqui, y por que cada cosa:

  - **El grano del informe.** Un producto declarado y no guardado tiene que salir como
    problema, y uno con explicacion documentada **no**. La primera version contaba los
    explicados en un diccionario de recuentos y luego los restaba de un conjunto de ids: decia
    «3 con explicacion» y a la vez «3 sin explicacion». Se vigila con un caso de juguete que
    reproduce las dos clases.
  - **El enlace lleva su id donde lo construimos nosotros** (Alcampo, Aldi), y **no** donde lo
    da la cadena (Carrefour publica `R-<referencia>`). La regla del 21 de septiembre de 2026
    --23.776 enlaces de Alcampo en 404 por guardar el `productId` en vez del
    `retailerProductId`-- es la que justifica la comprobacion; la excepcion de Carrefour es la
    que evita 1.212 falsas alarmas al dia.
  - **La paginacion declarada.** Carrefour y DIA dicen cuantas paginas tiene una categoria, y
    si se piden menos, faltan productos.

Se prueba con datos de mentira en `tmp_path`, que es obligatorio ademas: escribir en `data/`
desde una prueba revienta a proposito (`core/storage.comprueba_no_es_una_prueba`).
"""
from __future__ import annotations

import gzip
import hashlib
import json
from datetime import date

import polars as pl
import pytest

from core import config
from projects.cesta import verificar_ingesta as vi

FECHA = date(2026, 9, 24)


@pytest.fixture
def datos(tmp_path, monkeypatch):
    """Un `data/` de mentira con su raw y su bronze, y `config` apuntando ahi."""
    monkeypatch.setattr(config, "DATA", tmp_path)
    monkeypatch.setattr(config, "RAW", tmp_path / "raw")
    return tmp_path


def _guardar(datos, fuente: str, clave: str, cuerpo: bytes) -> None:
    carpeta = datos / "raw" / f"fuente={fuente}" / f"fecha={FECHA.isoformat()}"
    carpeta.mkdir(parents=True, exist_ok=True)
    prefijo = hashlib.sha1(clave.encode()).hexdigest()[:12]
    (carpeta / f"{prefijo}-{hashlib.sha256(cuerpo).hexdigest()[:12]}.json.gz").write_bytes(
        gzip.compress(cuerpo))


def _bronze(datos, fuente: str, ids: list[str], urls: list[str] | None = None) -> None:
    """Un bronze de juguete. El enlace va al dominio de verdad de la cadena: la comprobacion
    del host no es decoracion, y con un `example.com` todas las pruebas se llenarian de
    «enlace fuera de su dominio»."""
    carpeta = datos / "bronze" / f"fuente={fuente}" / f"fecha={FECHA.isoformat()}"
    carpeta.mkdir(parents=True, exist_ok=True)
    if urls is None:
        urls = [f"https://{vi.HOST[fuente]}/p/{i}" for i in ids]
    pl.DataFrame({"id_fuente": ids, "url": urls}).write_parquet(carpeta / "part.parquet")


def test_un_producto_que_falta_sin_explicacion_es_un_problema(datos):
    """El caso que da sentido a la herramienta: la cadena lo dio y no esta."""
    _guardar(datos, "mercadona", "category-1", json.dumps(
        {"categories": [{"products": [{"id": 1, "share_url": "https://x/product/1/a"},
                                      {"id": 2, "share_url": "https://x/product/2/b"}]}]}
    ).encode())
    _bronze(datos, "mercadona", ["1"])

    inf = vi.revisa("mercadona", FECHA.isoformat())

    assert inf.faltan == {"2"}
    assert inf.faltan_sin_explicar == {"2"}
    assert len(inf.problemas()) == 1


def test_un_producto_que_falta_con_explicacion_no_es_un_problema(datos):
    """Aldi publica la ficha en su sitemap y su API no le da precio: no hay nada que guardar.

    Y esta es la prueba del fallo que tuvo la primera version: decia «3 con explicacion» y a
    la vez «3 sin explicacion», porque restaba un diccionario de recuentos de un conjunto de
    ids. Con los ids guardados, cada uno cae de un lado o del otro.
    """
    sitemap = b'<url><loc>https://www.aldi.es/p/algo-111.html</loc></url>'
    _guardar(datos, "aldi", "sitemap-products", sitemap)
    _guardar(datos, "aldi", "pds-222", json.dumps(
        {"products": [{"objectID": "222", "productSlug": "otra"}]}).encode())
    _bronze(datos, "aldi", ["222"])

    inf = vi.revisa("aldi", FECHA.isoformat())

    assert inf.faltan == {"111"}
    assert inf.faltan_sin_explicar == set(), "una ficha sin precio en la API esta explicada"
    assert inf.problemas() == []
    assert sum(len(v) for v in inf.explicados.values()) == 1


def test_la_paginacion_declarada_que_no_se_pidio_sale(datos):
    """DIA dice cuantas paginas tiene la categoria; si se piden menos, faltan productos."""
    sitemap = (b"<url><loc>https://www.dia.es/x/y/c/L1</loc></url>"
               b"<url><loc>https://www.dia.es/x/z/c/L2</loc></url>")
    _guardar(datos, "dia", "sitemap", sitemap)
    _guardar(datos, "dia", "https://www.dia.es/x/y/c/L1-1", b'{"total_pages":3}')
    _guardar(datos, "dia", "https://www.dia.es/x/y/c/L1-2", b'{"items":[]}')
    _guardar(datos, "dia", "https://www.dia.es/x/z/c/L2-1", b'{"total_pages":1}')
    _bronze(datos, "dia", ["1"])

    inf = vi.revisa("dia", FECHA.isoformat())

    # De L1 se pidieron 2 de 3 paginas, y de L2 la unica que tiene.
    assert inf.paginas_esperadas == 4
    assert inf.paginas_pedidas == 3
    assert inf.categorias_cortas == ["https://www.dia.es/x/y/c/L1: 2 de 3"]


def test_una_categoria_del_sitemap_sin_pedir_se_cuenta_aparte(datos):
    """No se pidio, o la cadena devolvio 404: desde fuera no se distingue, y se dice asi."""
    _guardar(datos, "dia", "sitemap", b"<url><loc>https://www.dia.es/x/z/c/L9</loc></url>")
    _bronze(datos, "dia", [])

    inf = vi.revisa("dia", FECHA.isoformat())

    assert inf.sin_pedir == ["https://www.dia.es/x/z/c/L9"]
    assert inf.problemas() == [], "una categoria que la cadena sirve rota no es un fallo nuestro"


def test_el_enlace_tiene_que_llevar_su_id_donde_lo_construimos(datos):
    """Alcampo construye la URL con el `retailerProductId`; el `productId` interno daba 404."""
    _guardar(datos, "alcampo", "api-category-9", json.dumps(
        {"productGroups": [{"products": [
            {"retailerProductId": "881352", "productId": "uuid-1", "name": "Calamar"},
        ]}]}).encode())
    carpeta = datos / "bronze" / "fuente=alcampo" / f"fecha={FECHA.isoformat()}"
    carpeta.mkdir(parents=True, exist_ok=True)
    pl.DataFrame({"id_fuente": ["881352"],
                  "url": ["https://www.compraonline.alcampo.es/products/uuid-1"]}
                 ).write_parquet(carpeta / "part.parquet")

    inf = vi.revisa("alcampo", FECHA.isoformat())

    assert inf.url_sin_id == ["881352 -> https://www.compraonline.alcampo.es/products/uuid-1"]
    assert any("no llevan su propio id" in p for p in inf.problemas())


def test_en_carrefour_el_enlace_lo_da_la_cadena_y_no_se_le_exige_su_id(datos):
    """Su URL publica es `R-<referencia>` y su `product_id` no aparece: no es un fallo."""
    _guardar(datos, "carrefour", "cat1-0", json.dumps({"criteo": {"plpData": {"results": {
        "items": [{"product_id": "VC4AECOMM-1"}]}}}}).encode())
    carpeta = datos / "bronze" / "fuente=carrefour" / f"fecha={FECHA.isoformat()}"
    carpeta.mkdir(parents=True, exist_ok=True)
    pl.DataFrame({"id_fuente": ["VC4AECOMM-1"],
                  "url": ["https://www.carrefour.es/supermercado/algo/R-prod720101/p"]}
                 ).write_parquet(carpeta / "part.parquet")

    inf = vi.revisa("carrefour", FECHA.isoformat())

    assert len(inf.url_sin_id) == 1
    assert not any("no llevan su propio id" in p for p in inf.problemas()), (
        "el enlace de Carrefour lo da la cadena: se comprueba en vivo, no aqui")


def test_un_enlace_repetido_o_fuera_de_su_dominio_sale(datos):
    _guardar(datos, "mercadona", "category-1", json.dumps(
        {"categories": [{"products": [{"id": 1, "share_url": "https://tienda.mercadona.es/product/1/a"}]}]}
    ).encode())
    carpeta = datos / "bronze" / "fuente=mercadona" / f"fecha={FECHA.isoformat()}"
    carpeta.mkdir(parents=True, exist_ok=True)
    pl.DataFrame({"id_fuente": ["1", "2"],
                  "url": ["https://otro.example/product/1/a",
                          "https://otro.example/product/1/a"]}
                 ).write_parquet(carpeta / "part.parquet")

    inf = vi.revisa("mercadona", FECHA.isoformat())

    assert inf.enlaces_repetidos == 1
    assert len(inf.url_fuera_de_su_host) == 2
