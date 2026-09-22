"""Parsers de Aldi y Alcampo, con respuestas reales capturadas el 6 sep 2026."""
from projects.cesta.collectors import alcampo, aldi, carrefour, dia

# --- Aldi: GET /api/product/pds/940600?scope=es_pen -------------------------
ALDI = {
    "objectID": "940600",
    "name": "Uva de mesa roja sin semillas",
    "productSlug": "uva-de-mesa-roja-sin-semillas-940600",
    "salesUnit": "500 g unidad",
    "isAvailable": True,
    "mainCategoryID": "frutas",
    "assets": [{"type": "primary", "url": "https://s7g10.scene7.com/is/image/x"}],
    "currentPrice": {
        "priceValue": 1.49,
        "strikePrice": {"strikePriceValue": 2.29},
        "basePrice": [{"basePriceValue": 2.98, "basePriceScale": "kg"}],
        "priceTagLabels": {"promoText1": "-34%"},
        "validFrom": 1788127200, "validUntil": 1788731999,
    },
}

# --- Alcampo: window.__INITIAL_STATE__.data.products.productEntities --------
ALCAMPO_HTML = {
    "productId": "6b7102b8-64c0-4e66-a144-1b87c75965a9",
    "retailerProductId": "10739",
    "name": "Croissant relleno de chocolate y naranja 2 uds. 180 g.",
    "brand": "BOLLERÍA",
    "packSizeDescription": "180 g",
    "available": True,
    "categoryPath": ["Frescos", "Pastelería", "Palmeras, croissants y napolitanas"],
    "price": {
        "current": {"amount": "1.59", "currency": "EUR"},
        "unit": {"label": "fop.price.per.kg", "current": {"amount": "8.83"}},
    },
}

# --- Alcampo: la misma tienda, pero por su API (otra forma) -----------------
ALCAMPO_API = {
    "productId": "00e69d61-5c65-441b-b171-6b667022e828",
    "retailerProductId": "882535",
    "name": "LA ESPAÑOLA Aceite de oliva virgen extra garrafa de 5 l.",
    "brand": "LA ESPAÑOLA",
    "packSizeDescription": "5000ml",
    "available": True,
    "price": {"amount": "19.95", "currency": "EUR"},
    "unitPrice": {"price": {"amount": "3.99"}, "unitName": "per_litre"},
    "promotions": [{"description": "Producto en Folleto (27/08/26_09/09/26)"}],
}

DIA = {
    "brand": "Dia Mari Marinera",
    "display_name": "Filetes de merluza del cabo sin piel 600 g",
    "image": "/product_images/72170/72170_ISO_0_ES.jpg",
    "prices": {
        "measure_unit": "KILO", "price": 5.89, "price_per_unit": 9.82,
        "strikethrough_price": 6.49, "is_promo_price": True,
    },
    "sku_id": "72170", "units_in_stock": 13,
    "url": "/congelados-y-helados/pescado-y-marisco/p/72170", "weight": 0,
}

DIA_FICHA = {
    "ean_code": "8480017240330",
    "brand_description": {"name": "Marca", "value": "Dia Mari Marinera"},
    "manufacturer_contact_name": {"name": "Fabricante", "value": "Fabricante SA"},
    "product": {"name": "Nombre", "value": "Filetes de merluza congelados"},
    "ingredients": {"name": "Ingredientes", "value": "<p><strong>Merluza</strong>.</p>"},
    "allergen_statement": {"name": "Alérgenos", "value": "Contiene pescado"},
    "quantity_per_unit": 600,
    "measurement_unit_description": {"name": "Unidad", "value": "g"},
    "iva_tax_value": 10,
}

CARREFOUR = {
    "brand": "SIMPL", "measure_unit": "ud", "name": "Fregona SIMPL - Amarilla",
    "price": "0,74 €", "price_per_unit": "0,74 €",
    "product_id": "VC4AECOMM-241417", "sku_id": "2414170000",
    "units_in_stock": 16, "url": "/supermercado/fregona-simpl-amarilla/R-X/p",
    "images": {"desktop": "https://static.carrefour.es/fregona.jpg"},
}


def test_aldi_precios_y_promocion():
    r = aldi.a_registro(ALDI)
    assert r["precio_cent"] == 149
    assert r["precio_ref_nativo_cent"] == 298      # su EUR/kg
    assert r["unidad_ref_nativa"] == "kg"
    assert r["precio_anterior_nativo_cent"] == 229
    assert r["promo"] is True
    assert r["promo_txt"] == "-34%"


def test_aldi_guarda_el_fin_de_la_oferta():
    """Es la unica cadena que publica cuando acaba la promocion."""
    assert aldi.a_registro(ALDI)["promo_hasta"].year == 2026


def test_aldi_formato_alimenta_al_normalizador():
    from core.normalize import parse_formato
    assert parse_formato(aldi.a_registro(ALDI)["formato_txt"]) == (0.5, "kg", 1)


def test_alcampo_lee_la_forma_del_html():
    r = alcampo.a_registro(ALCAMPO_HTML)
    assert r["precio_cent"] == 159
    assert r["precio_ref_nativo_cent"] == 883
    assert r["unidad_ref_nativa"] == "kg"
    assert r["marca"] == "BOLLERÍA"
    assert r["categoria"].startswith("Frescos > Pastelería")


def test_alcampo_lee_tambien_la_forma_de_su_api():
    """Las dos formas conviven: el HTML da price.current, la API da price.amount."""
    r = alcampo.a_registro(ALCAMPO_API)
    assert r["precio_cent"] == 1995
    assert r["precio_ref_nativo_cent"] == 399
    assert r["unidad_ref_nativa"] == "l"
    assert r["promo"] is True


def test_dia_lee_precio_y_enriquece_con_su_ficha():
    maestro = dia._maestro_de_ficha(DIA_FICHA)
    r = dia.a_registro(DIA, maestro, "Pescado y marisco")
    assert r["precio_cent"] == 589
    assert r["precio_ref_nativo_cent"] == 982
    assert r["unidad_ref_nativa"] == "kilo"
    assert r["formato_txt"] == "600 g"
    assert r["ean"] == "8480017240330"
    assert r["ingredientes"] == "Merluza ."
    assert r["promo"] is True


def test_carrefour_lee_los_precios_con_coma():
    r = carrefour.a_registro(CARREFOUR, "limpieza/fregonas")
    assert r["precio_cent"] == 74
    assert r["precio_ref_nativo_cent"] == 74
    assert r["unidad_ref_nativa"] == "ud"
    assert r["imagen"].endswith("fregona.jpg")


def test_todos_los_colectores_devuelven_el_mismo_esquema():
    """Si un colector se inventa una columna, la union de cadenas revienta."""
    from core.schemas import ESQUEMA_BRONZE
    from projects.cesta.collectors import mercadona
    from tests.test_mercadona import PRODUCTO

    for registro in (aldi.a_registro(ALDI), alcampo.a_registro(ALCAMPO_HTML),
                     carrefour.a_registro(CARREFOUR), dia.a_registro(DIA),
                     mercadona.a_registro(PRODUCTO)):
        assert set(registro) == set(ESQUEMA_BRONZE), set(registro) ^ set(ESQUEMA_BRONZE)


# --- Aldi: la marca ----------------------------------------------------
# Durante nueve dias el colector ponia `marca: None` con un comentario que
# decia que Aldi no la separa del nombre. Si la separa: `brandName` viene en el
# 91,2 % de los productos, con 229 marcas distintas.

def _aldi_producto(brand=None):
    return {
        "objectID": "601602604",
        "name": "Grageas de chocolate",
        "productSlug": "grageas-de-chocolate-601602604",
        "salesUnit": "400 g unidad",
        "brandName": brand,
        "currentPrice": {"priceValue": 3.49,
                         "basePrice": [{"basePriceValue": 8.73, "basePriceScale": "kg"}]},
        "isAvailable": True,
        "mainCategoryID": "chocolates",
    }


def test_aldi_guarda_la_marca():
    from projects.cesta.collectors import aldi
    assert aldi.a_registro(_aldi_producto("MILSANI"))["marca"] == "MILSANI"


def test_aldi_quita_el_simbolo_de_marca_registrada():
    # El simbolo estorba al emparejador, que compara palabra a palabra.
    from projects.cesta.collectors import aldi
    assert aldi.a_registro(_aldi_producto("CHOCEUR®"))["marca"] == "CHOCEUR"
    assert aldi.a_registro(_aldi_producto("TRADER JOE'S™"))["marca"] == "TRADER JOE'S"


def test_aldi_sin_marca_no_pone_cadena_vacia():
    # Una cadena vacia no es lo mismo que "no lo sabemos", y el emparejador
    # trata los dos casos distinto.
    from projects.cesta.collectors import aldi
    assert aldi.a_registro(_aldi_producto(None))["marca"] is None
    assert aldi.a_registro(_aldi_producto("  ® "))["marca"] is None
