"""El auditor del crudo: encontrar solo los campos que nadie lee.

Siete veces seguidas aparecio un dato guardado en data/raw que ningun colector
leia, y las siete porque a alguien se le ocurrio mirar a mano. Esto lo dice solo.
"""
from collections import Counter

from projects.cesta import auditar_crudo
from projects.cesta.auditar_crudo import RUIDO, _aplana, _lee_fuente


def test_aplana_rutas_con_puntos():
    r = _aplana({"currentPrice": {"priceValue": 3.99, "validUntil": 123}})
    assert r == {"currentPrice.priceValue": 3.99, "currentPrice.validUntil": 123}


def test_una_lista_de_objetos_se_describe_por_el_primero():
    r = _aplana({"assets": [{"type": "primary"}, {"type": "certificate"}]})
    assert r == {"assets[].type": "primary"}


def test_una_lista_de_valores_se_deja_entera():
    r = _aplana({"categoryIDs": ["milsani", "yogures"]})
    assert r == {"categoryIDs": ["milsani", "yogures"]}


def test_el_ruido_se_filtra():
    # Identificadores internos y marcas del CDN no son datos del producto.
    for ruta in ("objectID", "price.id", "x.uuid", "metaTitle", "criteo.plpData",
                 "_ctx", "tracking.gtm"):
        assert RUIDO.search(ruta), ruta
    for ruta in ("currentPrice.validUntil", "isRecall", "allergens[].name",
                 "catchweight.minQuantity.value"):
        assert not RUIDO.search(ruta), ruta


def test_lee_las_claves_que_pide_un_colector_de_verdad():
    # Sobre el codigo real: si `aldi.py` dejara de pedir `isFreezing`, el
    # auditor tiene que poder avisarlo.
    claves = _lee_fuente("aldi")
    assert "isFreezing" in claves
    assert "brandName" in claves
    assert "noExisteEsteCampo" not in claves


# --- el falso positivo que costo media hora --------------------------------
#
# El 18 de septiembre de 2026 el auditor senalo `iconAttributes[].file` en el
# 52 % del catalogo de Alcampo. El colector ya lee esa lista entera, por
# `iconAttributes[].label`, que dice lo mismo en cristiano. Media hora midiendo
# algo que ya estaba hecho. No se puede descartar solo -- hay hermanos que si
# aportan, como `promotions[].type` frente a `promotions[].description` -- pero
# decirlo ahorra la media hora.

def test_avisa_de_que_un_hermano_de_ese_sitio_si_se_lee():
    presentes = Counter({"iconAttributes[].file": 10, "iconAttributes[].label": 10})
    assert auditar_crudo._hermanos_leidos(
        "iconAttributes[].file", presentes, {"label"}) == ["label"]


def test_si_no_se_lee_ningun_hermano_no_dice_nada():
    presentes = Counter({"promotions[].type": 5, "promotions[].limitReached": 5})
    assert auditar_crudo._hermanos_leidos("promotions[].type", presentes, set()) == []


def test_un_campo_de_primer_nivel_no_tiene_hermanos_que_mirar():
    presentes = Counter({"published": 5, "nombre": 5})
    assert auditar_crudo._hermanos_leidos("published", presentes, {"nombre"}) == []


def test_no_se_confunde_con_otra_rama_que_empiece_igual():
    presentes = Counter({"price.currency": 5, "priceTag.label": 5})
    assert auditar_crudo._hermanos_leidos(
        "price.currency", presentes, {"label"}) == []
