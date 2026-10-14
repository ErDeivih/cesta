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


# ============ la telemetria: toda salida deja fila, y ninguna escribe bronze ============
#
# **El complemento del 14/10 lo pide con estas palabras**: *«implementar registro de intento y resultado
# terminal en TODOS los caminos... **fixture de region desconocida y excepcion de red debe dejar evidencia
# de fallo, y no escribir bronze**»*.
#
# *Y el motivo es el que ya esta escrito en `lidl.py`: *** **una fuente que falla CALLANDO es
# indistinguible de una que no corre** ***, *y esa confusion es la que hace que «ausencia de fila» se lea
# como «no se ejecuto» en vez de «se intento y no salio».*

def _sin_bronze(monkeypatch):
    """*Ni por `storage` ni por el modulo del colector: escribir bronze es lo que no puede pasar.*"""
    from core import storage

    escrito: list = []
    monkeypatch.setattr(storage, "write_parquet", lambda *a, **k: escrito.append(a))
    monkeypatch.setattr(lidl, "write_parquet", lambda *a, **k: escrito.append(a))
    return escrito


def test_sin_region_acreditada_deja_FILA_y_no_escribe_bronze(tmp_path, monkeypatch, capsys):
    """**El camino que imprimia la causa y retornaba 1 sin tocar `runs.csv`.**

    *`region_del_cp` acredita la region **por el nombre que la fuente publica**, y si no casa **no se elige
    «la mas parecida»**: se para.* *Y parar esta bien; **parar sin dejar rastro, no** -- *porque entonces
    **la ausencia de fila se lee como que Lidl no corre**, y no como que corrio y no pudo.*
    """
    from core import config

    filas: list = []
    monkeypatch.setattr(lidl, "log_run", lambda *a, **k: filas.append(a))
    escrito = _sin_bronze(monkeypatch)
    # *Un CP que no acredita contra lo que la pagina publica: sin `--region`, se intenta por nombre.*
    monkeypatch.setattr(config, "CODIGO_POSTAL", "00000")
    fixture = tmp_path / "ofertas.html"
    fixture.write_text(ficha(oferta_simple()), encoding="utf-8")

    codigo = lidl.main(["--html", str(fixture), "--escribir"])

    assert codigo == 1, "sin region acreditada no se sigue"
    assert len(filas) == 1, f"tiene que quedar UNA fila de intento, y hay {len(filas)}: {filas}"
    assert filas[0][1] == 0 and filas[0][2] == 1, f"0 filas y 1 error: {filas[0]}"
    assert escrito == [], "y NO se escribe bronze"
    assert "region" in capsys.readouterr().out.lower(), "y la causa se dice"


def test_si_la_peticion_falla_deja_FILA_y_no_escribe_bronze(monkeypatch, capsys):
    """**La excepcion de red, que salia por el `traceback` sin registrar.**

    *Una peticion que revienta **no puede llevarse por delante la fila del CSV**: sin ella, el fallo
    **borra su propia huella**.*
    """
    filas: list = []
    monkeypatch.setattr(lidl, "log_run", lambda *a, **k: filas.append(a))
    escrito = _sin_bronze(monkeypatch)
    monkeypatch.setattr(lidl, "_robots_permite", lambda f: True)

    class RedCaida:
        def get(self, url):  # *la firma del fetcher de verdad*
            raise RuntimeError("la red se cayo")

    monkeypatch.setattr(lidl, "Fetcher", lambda **k: RedCaida())

    codigo = lidl.main(["--web", "--escribir"])

    assert codigo == 1, "una peticion que falla no es un exito"
    assert len(filas) == 1, f"tiene que quedar UNA fila, y hay {len(filas)}: {filas}"
    assert filas[0][1] == 0 and filas[0][2] == 1, f"0 filas y 1 error: {filas[0]}"
    assert escrito == [], "y NO se escribe bronze"
    assert "la red se cayo" in capsys.readouterr().out, "y la causa se dice"
