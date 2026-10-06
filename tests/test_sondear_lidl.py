import html
import json

import pytest

from projects.cesta.sondear_lidl import extraer, precios_region


def ficha(d):
    return '<div data-grid-data="' + html.escape(json.dumps(d), quote=True) + '"></div>'


def test_conserva_campos_y_no_inventa_ean():
    p = {"productId": 123, "ians": ["123"], "desconocido": {"nuevo": 4}}
    assert extraer(ficha(p)) == [p]
    assert "ean" not in extraer(ficha(p))[0]
    assert extraer(ficha(p) + ficha(p)) == [p]


def test_region_no_es_id_de_precio_y_club_no_es_precio_general():
    p = {"regionsV2": {"28": {"regionPriceId": "1", "regionName": "Ejemplo"}},
         "regionsPrices": {"1": {"currentLidlPlusPrice": {"price": {"price": 1.49}}}},
         "price": {"price": 9.99}}
    r = precios_region(p, "28")
    assert r["precios"] == p["regionsPrices"]["1"]
    assert precios_region(p, "999")["precios"] is None


@pytest.mark.parametrize("contenido", ["", "<html>bloqueado</html>", ficha({"title": "x"})])
def test_vacio_o_esquema_roto_no_es_exito(contenido):
    with pytest.raises(ValueError):
        extraer(contenido)


def test_duplicado_conflictivo_no_se_sobrescribe():
    with pytest.raises(ValueError):
        extraer(ficha({"productId": 1, "price": 1}) + ficha({"productId": 1, "price": 2}))


def test_variantes_del_mismo_padre_no_se_fusionan():
    a = {"productId": 1, "variantId": 11, "title": "Kefir fresa"}
    b = {"productId": 1, "variantId": 12, "title": "Kefir frutas variadas"}
    assert extraer(ficha(a) + ficha(b)) == [a, b]
