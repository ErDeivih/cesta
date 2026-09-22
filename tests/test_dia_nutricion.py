"""DIA publica mucho mas de lo que guardabamos.

Medido el 17 de septiembre sobre 800 fichas del crudo: tabla nutricional en el
66 %, y dias de caducidad, tipo de producto, peso escurrido y envase en el
100 %. Todo eso estaba descargado en `data/raw/` desde el primer dia y no
llegaba a bronze. Es el mismo patron que ya paso cuatro veces: el precio por
kilo de Alcampo, la marca de Aldi, los packs de DIA y las ofertas de Carrefour.
"""
import json

from projects.cesta.collectors import dia
from projects.cesta.collectors.dia import _maestro_de_ficha, _numero


def _ficha(**extra):
    base = {
        "ean_code": "8411700012217",
        "product": {"value": "Leche entera"},
        "brand_description": {"value": "Dia"},
        "quantity_per_unit": 1,
        "measurement_unit_description": {"value": "L"},
    }
    base.update(extra)
    return base


# --- los numeros vienen envueltos ---------------------------------------

def test_el_numero_sale_de_dentro_del_envoltorio():
    # DIA manda cada valor como {"value": 3.1, "uom": "g"}
    assert _numero({"value": 3.1, "uom": "g"}) == 3.1
    assert _numero(3.1) == 3.1
    assert _numero("3,1") == 3.1            # coma decimal


def test_lo_que_no_es_un_numero_no_se_inventa():
    assert _numero(None) is None
    assert _numero({"value": None}) is None
    assert _numero({"value": "No Aplica"}) is None   # DIA lo escribe asi
    assert _numero("") is None
    assert _numero("pendiente") is None


# --- la tabla nutricional -----------------------------------------------

def test_la_tabla_completa_se_guarda_como_json():
    f = _ficha(energy={"value": 820, "uom": "kJ"}, fat={"value": 15, "uom": "g"},
               saturated_fat={"value": 5, "uom": "g"},
               carbohydrate={"value": 2.6, "uom": "g"},
               sugars={"value": 1.3, "uom": "g"},
               protein={"value": 13, "uom": "g"},
               salt={"value": 2, "uom": "g"},
               nutri_size={"value": 100}, nutri_measurement_unit={"value": "g"})
    tabla = json.loads(_maestro_de_ficha(f)["nutricion"])
    assert tabla == {"energia_kj": 820.0, "grasas": 15.0, "saturadas": 5.0,
                     "hidratos": 2.6, "azucares": 1.3, "proteinas": 13.0, "sal": 2.0}
    assert _maestro_de_ficha(f)["nutricion_por"] == "100g"


def test_media_tabla_es_peor_que_ninguna():
    # Si no hay ni energia ni proteinas, no se guarda nada: media tabla se
    # ensena como si estuviera completa y eso enganya.
    f = _ficha(sugars={"value": 1.3, "uom": "g"})
    assert _maestro_de_ficha(f)["nutricion"] is None


def test_con_solo_proteinas_si_se_guarda():
    f = _ficha(protein={"value": 13, "uom": "g"})
    assert json.loads(_maestro_de_ficha(f)["nutricion"]) == {"proteinas": 13.0}


def test_sin_tabla_no_hay_campo():
    assert _maestro_de_ficha(_ficha())["nutricion"] is None
    assert _maestro_de_ficha(_ficha())["nutricion_por"] is None


def test_por_cuanto_esta_expresada():
    f = _ficha(protein={"value": 1.7},
               nutri_size={"value": 100}, nutri_measurement_unit={"value": "ml"})
    assert _maestro_de_ficha(f)["nutricion_por"] == "100ml"


# --- los cuatro campos que nadie mas publica ----------------------------

def test_los_dias_de_caducidad_son_un_entero():
    # Ninguna otra app de la competencia tiene este dato.
    f = _ficha(days_to_expiration={"value": 135})
    assert _maestro_de_ficha(f)["dias_caducidad"] == 135


def test_el_peso_neto_solo_se_cree_si_es_creible():
    # `drained_weight` NO es peso escurrido por mucho que se llame asi: coincide
    # con la cantidad neta en 4.323 de 4.995 productos y para un litro de aceite
    # dice 916, que es la densidad. Se guarda como peso neto, y solo cuando esta
    # entre la mitad y el doble de lo declarado.
    f = _ficha(drained_weight={"value": 916, "uom": "g"},
               quantity_per_unit=1, measure_unit="l")
    assert _maestro_de_ficha(f)["peso_neto_g"] == 916
    # 8.000 g para un refresco de 2 litros es el peso de una caja, no del envase.
    f = _ficha(drained_weight={"value": 8000, "uom": "g"},
               quantity_per_unit=2, measure_unit="l")
    assert _maestro_de_ficha(f)["peso_neto_g"] is None


def test_el_tipo_de_producto_es_fino():
    # "Leche infantil", no "Lacteos". Sirve para bloquear emparejamientos entre
    # productos que se llaman parecido y no son lo mismo.
    f = _ficha(product_type={"value": "Leche infantil"})
    assert _maestro_de_ficha(f)["tipo_producto"] == "Leche infantil"


def test_el_envase_se_guarda_tal_cual_lo_dice_la_cadena():
    # La ficha maestra guarda las palabras de DIA; normalizar es trabajo de
    # `a_registro`, para no tener que releer 5.410 fichas al cambiar el
    # vocabulario.
    assert _maestro_de_ficha(_ficha(
        package_format_description={"value": "frasco"}))["envase_txt"] == "frasco"


def test_el_envase_llega_normalizado_a_bronze():
    from core.envases import lee
    # El "frasco" de DIA y el "Tarro" de Mercadona son la misma opcion del filtro.
    assert lee("frasco")[0] == "tarro"
    assert lee("Tarro")[0] == "tarro"


def test_la_caducidad_centinela_no_pasa():
    # 999 es el "no caduca" de DIA y sale en 1.272 fichas. Si se dejara pasar,
    # la despensa avisaria de que se acaba el arroz dentro de dos anos y medio.
    assert _maestro_de_ficha(_ficha(days_to_expiration={"value": 999}))["dias_caducidad"] is None
    assert _maestro_de_ficha(_ficha(days_to_expiration={"value": 240}))["dias_caducidad"] == 240


def test_una_ficha_pelada_no_revienta():
    r = _maestro_de_ficha(_ficha())
    for campo in ("nutricion", "nutricion_por", "dias_caducidad",
                  "peso_neto_g", "envase_txt", "tipo_producto"):
        assert r[campo] is None, campo


def test_un_cero_no_se_confunde_con_no_haber_dato():
    # `days_to_expiration: 0` no tiene sentido, pero si llegara no debe
    # guardarse como 0 y hacer creer que caduca hoy.
    assert _maestro_de_ficha(_ficha(days_to_expiration={"value": 0}))["dias_caducidad"] is None


def test_la_tabla_va_directamente_a_nutricion_sin_pasar_por_ingredientes():
    # Son dos cosas distintas y la ficha las ensena por separado.
    f = _ficha(protein={"value": 13}, ingredients="Leche entera de vaca")
    r = _maestro_de_ficha(f)
    assert r["nutricion"] and r["ingredientes"]


# --- la auditoria de FICHAS del 19 de septiembre de 2026 --------------------
#
# Hasta ese dia se habia auditado el crudo de los **listados** y nunca el de las
# **fichas**, que es donde esta lo bueno: la de DIA tiene unas 200 claves. Dos de
# ellas tapaban huecos que marcaban 0 % en gold, y el motor para leerlas ya
# existia desde hacia semanas.

def test_la_conservacion_sale_de_storage_instructions():
    """`conservacion` de DIA estaba al 0 % y el dato llevaba semanas ahi.

    DIA escribe `storage_instructions` con las mismas palabras que Mercadona, y
    `sellos.conservacion_de_prosa` ya sabia leerlas. El dato estaba, el motor
    estaba, y nadie los habia juntado. Medido sobre 460 fichas reales: 30 %.
    """
    from core import sellos
    casos = [("Conservar a -18 ºC", "congelado"),
             ("Manténgase en lugar fresco, seco y alejado de la luz", "ambiente"),
             ("Conservar refrigerado entre 0 y 4 ºC", "refrigerado")]
    for texto, espera in casos:
        m = dia._maestro_de_ficha({"storage_instructions": texto})
        assert sellos.conservacion_de_prosa(m["conservacion_txt"]) == espera, texto


def test_el_origen_prefiere_el_pais_y_si_no_el_fabricante():
    # Medido: pais en el 29 % de las fichas, fabricante en el 41 %. Juntos, 69 %.
    assert dia._origen_de_ficha({"manufacturer_contact_country": "Unión Europea",
                                 "manufacturer_name": "Freudenberg"}) == "Unión Europea"
    assert dia._origen_de_ficha({"manufacturer_name": "Freudenberg"}) == "Freudenberg"
    assert dia._origen_de_ficha({}) is None


def test_una_direccion_postal_no_es_un_origen():
    # Un domicilio social no dice de donde viene el producto. Ponerlo en `origen`
    # seria vender por procedencia lo que solo es una oficina.
    assert dia._origen_de_ficha(
        {"manufacturer_address": "C/ Can Gurri 1A, Pol. Ind. 08150 Barcelona"}) is None


def test_los_codigos_de_barras_de_mas_se_guardan_pero_no_emparejan():
    # Entre los secundarios esta el del **pack**. Emparejar por ahi haria que un
    # pack de seis y una unidad suelta fueran el mismo producto.
    m = dia._maestro_de_ficha({"secondary_eans": ["5000159409254", "5000159407236"]})
    assert m["eans_extra"] == ["5000159409254", "5000159407236"]
    from core.schemas import vacio
    assert "eans_extra" not in vacio()
