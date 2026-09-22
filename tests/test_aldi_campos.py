"""Lo que Aldi publicaba y no leiamos.

Tres cosas medidas el 17 de septiembre de 2026 sobre la captura del dia:

  * `currentPrice.validUntil` vale **2030-12-31** en 1.645 de los 2.065
    productos. Es un centinela de "este precio no caduca", y se escribia tal cual
    en `promo_hasta`, asi que la plataforma creia que el 79,7 % del catalogo de
    Aldi tenia una oferta que acaba dentro de cuatro anos.
  * `isFreezing` marca 130 congelados. Es la unica senal de frio que da Aldi.
  * `shortDescription` (62,7 %) es la unica frase que Aldi escribe del producto,
    y dentro lleva el origen ("Origen: España, Francia") y sellos de dieta.
"""
from datetime import datetime, timezone

from projects.cesta.collectors.aldi import a_registro


def _p(**extra):
    base = {"objectID": "940600", "name": "Aceite de oliva suave",
            "currentPrice": {"priceValue": 3.99}}
    base.update(extra)
    return base


def test_el_centinela_de_2030_no_es_una_oferta():
    r = a_registro(_p(currentPrice={"priceValue": 3.99,
                                    "validUntil": int(datetime(2030, 12, 31,
                                                               tzinfo=timezone.utc).timestamp()),
                                    "strikePrice": {"strikePriceValue": 6.55}}))
    assert r["promo_hasta"] is None


def test_una_oferta_de_verdad_si_trae_fecha():
    fin = int(datetime(2026, 9, 20, 21, 59, 59, tzinfo=timezone.utc).timestamp())
    r = a_registro(_p(currentPrice={"priceValue": 3.99, "validUntil": fin,
                                    "strikePrice": {"strikePriceValue": 6.55}}))
    assert r["promo_hasta"].date().isoformat() == "2026-09-20"
    assert r["promo"] is True


def test_un_precio_normal_que_caduca_no_es_una_oferta():
    # Sin precio tachado ni texto de promocion, `validUntil` es la vigencia del
    # precio, no el fin de una oferta.
    fin = int(datetime(2026, 9, 22, tzinfo=timezone.utc).timestamp())
    r = a_registro(_p(currentPrice={"priceValue": 3.99, "validUntil": fin}))
    assert r["promo_hasta"] is None
    assert r["promo"] is False


def test_una_bajada_sin_tachar_tambien_es_oferta():
    # 75 de las 170 ofertas de hoy bajan el precio sin tachar nada: solo se ven
    # en `promotionPrices`. Con la regla vieja se quedaban fuera.
    fin = int(datetime(2026, 9, 20, tzinfo=timezone.utc).timestamp())
    r = a_registro(_p(currentPrice={"priceValue": 2.91},
                      promotionPrices=[{"priceValue": 2.91, "validUntil": fin}]))
    assert r["promo"] is True
    assert r["promo_hasta"].date().isoformat() == "2026-09-20"


def test_los_congelados():
    assert a_registro(_p(isFreezing=True))["conservacion"] == "congelado"
    # Aldi no dice nada de los refrigerados, y "no lo sabemos" es None, no
    # "ambiente": inventarlo seria peor que no tenerlo.
    assert a_registro(_p(isFreezing=False))["conservacion"] is None


def test_el_origen_del_texto_gana_al_del_logotipo():
    # El logotipo solo sabe decir "España"; la ficha dice de que paises es.
    r = a_registro(_p(shortDescription="Origen: España, Francia, Italia.\nCategoría: I",
                      assets=[{"type": "certificate", "url": "https://x/01_A_Origen_nacional"}]))
    assert r["origen"] == "España, Francia, Italia"


def test_los_sellos_suman_certificado_y_texto():
    r = a_registro(_p(shortDescription="Sin azúcares añadidos. Con avellanas.",
                      assets=[{"type": "certificate", "url": "https://x/07_Sin_gluten"}]))
    assert r["sellos"] == "sin-azucar,sin-gluten"


def test_la_marca_propia_por_categoria():
    # Aldi mete sus marcas en `categoryIDs` como si fueran una categoria mas:
    # 478 productos, frente a los 63 que marca el logotipo de la casa.
    assert a_registro(_p(categoryIDs=["milsani", "yogures"]))["es_marca_propia"] is True
    assert a_registro(_p(categoryIDs=["yogures"]))["es_marca_propia"] is None


def test_la_descripcion_no_es_el_aviso_legal():
    # `longDescription` existe en el 79,2 % y es "El precio puede variar para las
    # tiendas ubicadas en las Islas Baleares" el 99,3 % de las veces.
    r = a_registro(_p(shortDescription="Con sal. Textura crujiente.",
                      longDescription="El precio puede variar para las tiendas..."))
    assert r["descripcion"] == "Con sal. Textura crujiente."
