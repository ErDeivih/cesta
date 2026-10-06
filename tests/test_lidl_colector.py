"""Pruebas del colector de Lidl: cobertura parcial, EAN que no se inventa y precio que no se confunde.

Todo con HTML de fixture (sin red). Lo que se fija aqui:

  - la fila cumple el esquema de bronze del proyecto (`ProductoRaw`), que es lo que impide que un
    colector nuevo meta columnas raras o tipos cambiados;
  - el EAN **no** se inventa a partir de `ians`;
  - el precio tachado va al campo del precio anterior y **no** al precio que se cobra;
  - el alcance se aplica, y una oferta de bazar no se guarda;
  - la cobertura se declara parcial, y el aviso lo dice con palabras.
"""
from __future__ import annotations

import html as html_mod
import json

import pytest

from core.schemas import ProductoRaw
from projects.cesta.collectors import lidl


def ficha(d: dict) -> str:
    return '<div data-grid-data="' + html_mod.escape(json.dumps(d), quote=True) + '"></div>'


def oferta_simple(**extra) -> dict:
    base = {
        "productId": 123456,
        "variantId": "v1",
        "fullTitle": "Aceite de oliva virgen extra 1 l",
        "brand": {"name": "Marca Ejemplo"},
        "basePrice": {"text": "1 l"},
        "canonicalUrl": "https://www.lidl.es/p/aceite",
        "regionsV2": {"28": {"regionPriceId": "7", "regionName": "Madrid"}},
        "regionsPrices": {"7": {"currentPrice": {"price": {"price": 4.99}},
                                "oldPrice": {"price": {"price": 6.49}}}},
    }
    base.update(extra)
    return base


def test_la_fila_cumple_el_esquema_del_proyecto():
    """Si no cumple el esquema de bronze, no entra: es la puerta que protege el pipeline."""
    filas, _ = lidl.captura(ficha(oferta_simple()), "28")
    assert filas.height == 1
    fila = filas.to_dicts()[0]
    ProductoRaw(**{k: v for k, v in fila.items()
                   if k in ProductoRaw.model_fields})   # no lanza = cumple
    assert fila["fuente"] == "lidl"
    assert fila["nombre"] == "Aceite de oliva virgen extra 1 l"
    assert fila["marca"] == "Marca Ejemplo"
    assert fila["formato_txt"] == "1 l"
    assert fila["precio_cent"] == 499


def test_no_inventa_ean_con_los_identificadores_internos():
    """`ians` es un identificador interno, no un codigo de barras comprobado."""
    filas, _ = lidl.captura(ficha(oferta_simple(ians=["123456"], gtin="no-es-un-gtin")), "28")
    assert filas.to_dicts()[0]["ean"] is None


def test_el_precio_tachado_no_es_el_precio():
    """Anunciar una bajada que no existe es lo mas facil de hacer mal con estos datos."""
    filas, _ = lidl.captura(ficha(oferta_simple()), "28")
    fila = filas.to_dicts()[0]
    assert fila["precio_cent"] == 499
    assert fila["precio_anterior_nativo_cent"] == 649


def test_sin_precio_de_region_no_se_usa_el_general_como_sustituto():
    """El precio por defecto de la ficha no es el de la region: si no se sabe, se deja vacio."""
    sin_region = oferta_simple(regionsV2={}, regionsPrices={}, price={"price": {"price": 9.99}})
    filas, resumen = lidl.captura(ficha(sin_region), "28")
    fila = filas.to_dicts()[0]
    assert fila["precio_cent"] is None, "se ha colado el precio general como si fuera el de la region"
    assert resumen["guardados"] == 1


def test_el_alcance_se_aplica_y_el_bazar_no_se_guarda():
    bazar = oferta_simple(productId=999, fullTitle="Funda elástica para sofá de 3 plazas",
                          campaignName="Hogar y decoración")
    comida = oferta_simple(productId=1000, fullTitle="Leche entera 1 l",
                           campaignName="Frescos")
    filas, resumen = lidl.captura(ficha(bazar) + ficha(comida), "28")
    nombres = [f["nombre"] for f in filas.to_dicts()]
    assert nombres == ["Leche entera 1 l"]
    assert resumen["fuera_de_alcance"] == 1


def test_un_padre_con_varias_variantes_son_filas_distintas():
    """Los sabores de un mismo producto comparten `productId`: si se funden, se pierde el sabor."""
    a = oferta_simple(productId=555, variantId="fresa", fullTitle="Kéfir de fresa 500 g")
    b = oferta_simple(productId=555, variantId="natural", fullTitle="Kéfir natural 500 g")
    filas, resumen = lidl.captura(ficha(a) + ficha(b), "28")
    assert filas.height == 2
    assert resumen["productos_padre"] == 1
    assert {f["id_fuente"] for f in filas.to_dicts()} == {"555-fresa", "555-natural"}


def test_la_cobertura_se_declara_parcial_y_lo_dice():
    _, resumen = lidl.captura(ficha(oferta_simple()), "28")
    assert resumen["cobertura"] == "ofertas_semanales_parcial"
    assert "no su catalogo completo" in resumen["aviso"]
    assert "stock" in resumen["aviso"]


@pytest.mark.parametrize("contenido", ["", "<html>bloqueado</html>",
                                       ficha({"title": "sin identificador"})])
def test_html_vacio_o_roto_no_es_un_exito(contenido):
    """No hay que confundir 'no hay ofertas' con 'no he podido leer las ofertas'."""
    with pytest.raises(ValueError):
        lidl.captura(contenido, "28")


def test_una_captura_manual_no_toca_el_pipeline(tmp_path, monkeypatch, capsys):
    """La pasada diaria descubre las cadenas: escribir bronze sin querer la haria lanzar Lidl.

    Con `--escribir` detras de una bandera, un sondeo a mano no puede alimentar el pipeline. Esta
    prueba es la que impide que ese detalle se pierda en un refactor.
    """
    from core import storage

    escrito = []
    monkeypatch.setattr(storage, "write_parquet", lambda *a, **k: escrito.append(a))
    monkeypatch.setattr(lidl, "write_parquet", lambda *a, **k: escrito.append(a))
    fixture = tmp_path / "ofertas.html"
    fixture.write_text(ficha(oferta_simple()), encoding="utf-8")
    codigo = lidl.main(["--html", str(fixture), "--region", "28"])
    assert codigo == 0
    assert escrito == [], "una captura manual ha escrito bronze"
    assert "sin --escribir" in capsys.readouterr().out
