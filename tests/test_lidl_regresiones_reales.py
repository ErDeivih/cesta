from datetime import datetime, timezone

import pytest

from projects.cesta.collectors import lidl


def oferta(precios):
    return {"productId": 1, "title": "Zanahoria 1 kg", "canonicalUrl": "/p/zanahoria/p1",
            "regionsV2": {"28": {"regionPriceId": "1"}}, "regionsPrices": {"1": precios},
            "keyfacts": {"wonCategoryPrimary": "Alimentacion/Frutas y hortalizas"}}


def precio(valor=1.15, **extra):
    return {"price": valor, "startDate": "2026-10-04T22:00Z",
            "endDateExclusive": "2026-10-11T22:00Z", "packaging": {"text": "1 kg"}, **extra}


AHORA = datetime(2026, 10, 6, tzinfo=timezone.utc)


def test_precio_numerico_real_no_lanza_y_conserva_formato():
    r = lidl.a_registro(oferta({"currentPrice": precio()}), "28", AHORA)
    assert r["precio_cent"] == 115
    assert r["formato_txt"] == "1 kg"
    assert r["disponible"] is None
    assert r["url"].startswith("https://www.lidl.es/")
    assert r["categoria"] == "Alimentacion/Frutas y hortalizas"


def test_club_con_fecha_y_precio_anterior_reales():
    r = lidl.a_registro(oferta({"currentLidlPlusPrice": {"price": precio(1.49, oldPrice=1.99)}}), "28", AHORA)
    assert (r["precio_cent"], r["precio_anterior_nativo_cent"], r["promo_club"]) == (149, 199, True)
    assert r["promo_hasta"] is not None


def test_normal_no_se_marca_club_por_existir_otra_oferta():
    r = lidl.a_registro(oferta({"currentPrice": precio(2), "currentLidlPlusPrice": {"price": precio(1)}}), "28", AHORA)
    assert r["precio_cent"] == 200
    assert r["promo_club"] is False


@pytest.mark.parametrize("fecha", [datetime(2026, 10, 1, tzinfo=timezone.utc),
                                   datetime(2026, 10, 11, 22, tzinfo=timezone.utc)])
def test_futura_o_vencida_no_es_precio_vigente(fecha):
    assert lidl.a_registro(oferta({"currentPrice": precio()}), "28", fecha)["precio_cent"] is None


@pytest.mark.parametrize("valor", [float("nan"), float("inf"), True, -1, "roto"])
def test_importes_invalidos(valor):
    assert lidl._centimos(valor) is None


def test_sin_fecha_y_region_desconocida_no_aprueban():
    o = oferta({"currentPrice": {"price": 2}})
    assert lidl.a_registro(o, "28", AHORA)["precio_cent"] is None
    assert lidl.a_registro(o, "999", AHORA)["precio_cent"] is None
