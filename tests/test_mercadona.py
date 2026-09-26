"""Tests del parser de Mercadona. Sin red: fixture real capturada el 6 sep 2026.

El primer test existe por un fallo concreto: el colector recorria las categorias
raiz y devolvia 0 productos sin dar ni un error. Que no vuelva a pasar en silencio.
"""
from projects.cesta.collectors import mercadona

# /api/categories/ -> results  (recortado)
CATEGORIAS_RAIZ = {
    "results": [
        {"id": 12, "name": "Aceite, especias y salsas", "categories": [
            {"id": 112, "name": "Aceite, vinagre y sal"},
            {"id": 115, "name": "Especias"},
        ]},
        {"id": 19, "name": "Agua y refrescos", "categories": [
            {"id": 156, "name": "Agua"},
        ]},
    ]
}

# un producto tal cual viene en /api/categories/112/
PRODUCTO = {
    "id": "4241",
    "slug": "aceite-oliva-04o-hacendado-garrafa",
    "packaging": "Garrafa",
    "display_name": "Aceite de oliva 0,4º Hacendado",
    "thumbnail": "https://prod-mercadona.imgix.net/images/x.jpg",
    "share_url": "https://tienda.mercadona.es/product/4241/aceite-oliva-04o-hacendado-garrafa",
    "categories": [{"id": 12, "name": "Aceite, especias y salsas", "level": 0}],
    "unavailable_from": None,
    "is_variable_weight": False,
    "price_instructions": {
        "iva": None, "is_pack": False, "unit_size": 5, "size_format": "l",
        "bulk_price": "3.45", "unit_price": "17.25", "tax_percentage": "4.000",
        "price_decreased": False, "reference_format": "L",
        "previous_unit_price": "       17.75",
    },
}


def test_categorias_devuelve_nivel_2(monkeypatch):
    """Las raices NO traen productos: hay que bajar un nivel."""
    class FetchFalso:
        def get(self, url):
            import json

            class R:
                body = json.dumps(CATEGORIAS_RAIZ).encode()

            return R()
    monkeypatch.setattr(mercadona, "save_raw", lambda *a, **k: None)
    cats = mercadona.categorias(FetchFalso())
    assert [c["id"] for c in cats] == [112, 115, 156]


def test_precios_en_centimos_enteros():
    r = mercadona.a_registro(PRODUCTO)
    assert r["precio_cent"] == 1725              # 17,25 EUR
    assert r["precio_ref_nativo_cent"] == 345    # su etiqueta: 3,45 EUR/L
    assert r["unidad_ref_nativa"] == "l"         # ojo: es SU unidad, no la canonica
    assert r["cantidad_declarada"] == 5.0
    assert r["unidad_declarada"] == "l"


def test_precio_anterior_con_espacios():
    """Mercadona lo manda como '       17.75'. Si no se limpia, revienta."""
    assert mercadona.a_registro(PRODUCTO)["precio_anterior_nativo_cent"] == 1775


def test_peso_variable_no_inventa_formato():
    """Sin unit_size, el formato queda vacio: nada de la cadena 'None kg'."""
    p = {**PRODUCTO, "price_instructions": {
        **PRODUCTO["price_instructions"], "unit_size": None, "size_format": "kg"}}
    r = mercadona.a_registro(p)
    assert r["formato_txt"] == ""
    assert r["cantidad_declarada"] is None


def test_formato_y_campos_basicos():
    r = mercadona.a_registro(PRODUCTO)
    assert r["formato_txt"] == "5 l"
    assert r["id_fuente"] == "4241"
    assert r["disponible"] is True
    assert r["marca"] is None                # el listado no la trae, la pone la ficha


def test_formato_alimenta_al_normalizador():
    from core.normalize import parse_formato
    r = mercadona.a_registro(PRODUCTO)
    assert parse_formato(r["formato_txt"]) == (5.0, "l", 1)


def test_los_dos_precios_de_referencia_se_guardan_cada_uno_con_su_unidad():
    """`bulk_price` y `reference_price` NO van en la misma unidad.

    Medido el 26 de septiembre de 2026 sobre el bronze del día (4.324 productos): coinciden en
    3.522 y difieren en 802. El caso que lo explica es un detergente de 4,95 €: `reference_format`
    dice "lv" (lavados) y `reference_price` marca 0,155 —por lavado—, mientras que `bulk_price`
    marca 8,590, que es por litro (4,95 / 0,576 l). O sea que `bulk_price` va en la unidad del
    **tamaño** y `reference_price` en la de `reference_format`.
    """
    p = {**PRODUCTO, "display_name": "Detergente líquido Hacendado",
         "price_instructions": {**PRODUCTO["price_instructions"], "unit_size": 0.576,
                                "size_format": "l", "unit_price": "4.95",
                                "reference_format": "lv", "bulk_price": "8.590",
                                "reference_price": "0.155"}}
    r = mercadona.a_registro(p)
    assert r["unidad_ref_nativa"] == "lv"           # la unidad de la referencia
    assert r["precio_ref_nativo_cent"] == 859       # bulk_price: por litro, 8,59 EUR
    assert r["precio_referencia_nativo_cent"] == 16  # reference_price: 0,155 EUR/lavado
    # Y el que va con `unidad_ref_nativa` es el segundo: el par consistente.
    assert r["precio_ref_nativo_cent"] != r["precio_referencia_nativo_cent"]


def test_el_producto_de_siempre_tiene_los_dos_iguales():
    """En los 3.522 donde las unidades coinciden, los dos campos dicen lo mismo.

    Es la comprobación que evita leer la medición al revés: si `reference_price` fuera otra
    cosa, aquí no cuadraría.
    """
    p = {**PRODUCTO, "price_instructions": {**PRODUCTO["price_instructions"],
                                            "bulk_price": "3.45",
                                            "reference_price": "3.45"}}
    r = mercadona.a_registro(p)
    assert r["precio_ref_nativo_cent"] == r["precio_referencia_nativo_cent"] == 345
