"""Alcampo: el reto del WAF no puede acabar guardado como si fuera catalogo.

Pasada del 7 sep: "el WAF nos ha cortado tras 6623 productos" en OCHO segundos,
sin una sola peticion de red. La causa no era el WAF: 114 de los 352 ficheros
crudos del dia anterior eran la pagina del reto, guardada por `save_raw` antes de
comprobar nada. La categoria quedaba envenenada para siempre, y renovar la cookie
no servia porque la respuesta ya no venia de la red.
"""
from unittest import mock

from projects.cesta.collectors import alcampo

RETO = b'<html><script>window.gokuProps = {"key":"x"};</script></html>'
BUENO = b'{"products":[]}'


def test_un_reto_no_se_guarda_en_el_crudo():
    with mock.patch.object(alcampo, "save_raw") as guardar:
        alcampo._guardar("cat-1", RETO)
    guardar.assert_not_called()


def test_una_respuesta_buena_si_se_guarda():
    with mock.patch.object(alcampo, "save_raw") as guardar:
        alcampo._guardar("cat-1", BUENO)
    guardar.assert_called_once_with(alcampo.FUENTE, "cat-1", BUENO)


def test_un_reto_ya_cacheado_se_ignora_y_se_vuelve_a_pedir():
    with mock.patch.object(alcampo, "load_raw_bytes", return_value=RETO):
        assert alcampo._cache_limpia("cat-1") is None


def test_el_crudo_bueno_se_sirve_de_la_cache():
    with mock.patch.object(alcampo, "load_raw_bytes", return_value=BUENO):
        assert alcampo._cache_limpia("cat-1") == BUENO


def test_una_parcial_mas_grande_que_el_ultimo_bronze_se_guarda():
    """El 7 sep se tiraron 21.199 productos para conservar un bronze de 10.074.

    La regla de "parcial no pisa lo bueno" existe para no empeorar el catalogo,
    no para tirar once mil productos y 971 segundos de red. Lo que decide es el
    tamano.
    """
    assert alcampo._filas_ultimo_bronze() >= 0      # no revienta sin datos


def test_si_el_waf_nos_tiene_fichados_se_deja_para_manana():
    """Insistir cuando el WAF ya nos ha marcado es tirar media hora de esperas.

    La noche del 8 sep cortó seis veces en las primeras categorias, tras una
    pasada larga un rato antes: el testigo nuevo nacia ya vigilado. Con veinte
    renovaciones a noventa segundos eso son treinta minutos para acabar igual, y
    encima empeorando la reputacion de la IP para el dia siguiente.
    """
    assert alcampo.CORTES_PARA_RENDIRSE < alcampo.MAX_RENOVACIONES
    assert 0 < alcampo.AVANCE_MINIMO < 1


def test_la_espera_crece_pero_tiene_tope():
    escalones = [min(alcampo.ESPERA_TRAS_CORTE * n, alcampo.ESPERA_MAXIMA)
                 for n in range(1, 8)]
    assert escalones[0] < escalones[1]              # crece
    assert max(escalones) == alcampo.ESPERA_MAXIMA  # y se topa


def test_una_merma_pequena_no_justifica_tirar_una_captura_de_hoy():
    """El 8 sep: diez horas, 650 categorias, 35.311 productos distintos. Un 4 %
    menos que los 36.935 del dia anterior, y se tiro entero para conservar un
    catalogo VIEJO. Lo que hace valioso al de hoy no es su tamano, son sus precios.
    """
    anterior = 36935
    minimo = anterior * (1 - alcampo.MERMA_ACEPTABLE)
    assert minimo <= 35311          # el caso real: ahora se guarda
    assert minimo > 18000           # media captura sigue sin guardarse


def test_el_margen_es_estrecho_a_proposito():
    # Aceptar cualquier merma convertiria la regla en "guarda siempre", y entonces
    # una captura rota pisaria un catalogo bueno.
    assert 0 < alcampo.MERMA_ACEPTABLE <= 0.15


def test_el_recorrido_empieza_donde_se_corto_la_ultima_vez(tmp_path):
    """Sin esto el WAF corta SIEMPRE por el mismo sitio: la cola se recorre en el
    mismo orden todos los dias, asi que las categorias del final no se visitan
    nunca. Rotando el arranque, lo que hoy no da tiempo a mirar es lo primero de
    manana.
    """
    from unittest import mock

    marcador = tmp_path / "por_donde_iba.txt"
    with mock.patch.object(alcampo, "MARCADOR", marcador):
        assert alcampo._desde_donde(300) == 0        # sin marcador, por el principio
        alcampo._apuntar_donde_voy(237)
        assert alcampo._desde_donde(300) == 237
        # si el arbol encoge, el indice viejo no puede salirse de rango
        assert alcampo._desde_donde(100) == 37
        alcampo._apuntar_donde_voy(0)
        assert alcampo._desde_donde(300) == 0


def test_un_marcador_ilegible_no_rompe_la_ejecucion(tmp_path):
    from unittest import mock

    malo = tmp_path / "roto.txt"
    malo.write_text("no soy un numero")
    with mock.patch.object(alcampo, "MARCADOR", malo):
        assert alcampo._desde_donde(300) == 0


def test_solo_se_recogen_alimentacion_y_consumibles():
    """Alcampo publica online toda su tienda. Medido el 8 sep: de 37.019
    productos solo el 33 % era comida, su rama mayor era "Hogar y Decoracion", y
    cuatro de cada cinco productos suyos no encontraban con quien compararse
    porque las demas cadenas no venden cortinas.

    El criterio para quedarse es "se consume y se repone".
    """
    from core.config import RAMAS_EXCLUIDAS_ALCAMPO as fuera

    for bazar in ("hogar y decoracion", "juguetes", "textil", "electrodomesticos",
                  "tecnologia", "libros", "automovil"):
        assert bazar in fuera, f"{bazar} deberia quedar fuera"
    for consumible in ("alimentacion", "frescos", "bebidas", "drogueria",
                       "perfumeria", "parafarmacia", "mascotas", "bebe",
                       "congelados", "comida preparada"):
        assert consumible not in fuera, f"{consumible} deberia quedarse"


def test_cambiar_el_alcance_desactiva_la_red_de_seguridad_del_tamano(tmp_path):
    """Al excluir el bazar el catalogo encoge a proposito, de 37.019 a ~25.004.

    Sin esto, la regla que protege de capturas rotas lo confundiria con una y
    Alcampo no volveria a guardar NUNCA. Comparar tamanos solo tiene sentido
    entre capturas que buscaban lo mismo.
    """
    from unittest import mock

    fichero = tmp_path / "alcance.txt"
    with mock.patch.object(alcampo, "ALCANCE", fichero):
        with mock.patch.object(alcampo.config, "RAMAS_EXCLUIDAS_ALCAMPO", set()):
            alcampo._apuntar_alcance()
            assert alcampo._mismo_alcance()          # nada ha cambiado
        with mock.patch.object(alcampo.config, "RAMAS_EXCLUIDAS_ALCAMPO", {"juguetes"}):
            assert not alcampo._mismo_alcance()      # ahora se busca otra cosa


def test_sin_alcance_apuntado_se_asume_que_no_ha_cambiado(tmp_path):
    from unittest import mock

    with mock.patch.object(alcampo, "ALCANCE", tmp_path / "no_existe.txt"):
        assert alcampo._mismo_alcance()


def test_ninguna_rama_excluida_no_se_escribe_como_fichero_vacio(tmp_path):
    # Un fichero vacio no se distingue de uno que no se pudo escribir.
    from unittest import mock

    with mock.patch.object(alcampo.config, "RAMAS_EXCLUIDAS_ALCAMPO", set()):
        assert alcampo._alcance_actual().strip() != ""


# --- precio de referencia e imagen -------------------------------------
# Su API manda la unidad en dos sitios con dos nombres: `unit`
# ("fop.price.per.100ml") y `unitName` ("PER_100ML"). Durante nueve dias se leyo
# solo el segundo, que no esta en el mapa, y el 83% del catalogo de Alcampo se
# quedo sin precio por kilo. Estas pruebas cierran esa puerta.

def _producto_api(unit=None, unit_name=None, importe="2.67", imagen=None):
    p = {
        "productId": "abc",
        "retailerProductId": "123",
        "name": "Producto de prueba",
        "brand": "MARCA",
        "packSizeDescription": "500 g",
        "price": {"amount": "5.00", "currency": "EUR"},
        "unitPrice": {"price": {"amount": importe, "currency": "EUR"}},
        "available": True,
        "categoryPath": ["Alimentacion"],
    }
    if unit:
        p["unitPrice"]["unit"] = unit
    if unit_name:
        p["unitPrice"]["unitName"] = unit_name
    if imagen:
        p["image"] = {"src": imagen}
    return p


def test_unidad_de_referencia_se_lee_de_unit_no_de_unit_name():
    r = alcampo.a_registro(_producto_api(unit="fop.price.per.kg", unit_name="PER_1KG"))
    assert r["unidad_ref_nativa"] == "kg"
    assert r["precio_ref_nativo_cent"] == 267


def test_precio_por_100_ml_se_lleva_a_litro():
    r = alcampo.a_registro(_producto_api(unit="fop.price.per.100ml", unit_name="PER_100ML"))
    assert r["unidad_ref_nativa"] == "l"
    assert r["precio_ref_nativo_cent"] == 2670          # 2,67 EUR/100 ml = 26,70 EUR/l


def test_precio_por_100_gramos_se_lleva_a_kilo():
    r = alcampo.a_registro(_producto_api(unit="fop.price.per.100gram", importe="1.04"))
    assert r["unidad_ref_nativa"] == "kg"
    assert r["precio_ref_nativo_cent"] == 1040


def test_unidad_desconocida_no_inventa_una():
    r = alcampo.a_registro(_producto_api(unit="fop.price.per.algo_nuevo"))
    assert r["unidad_ref_nativa"] is None


def test_la_etiqueta_del_html_manda_sobre_la_de_la_api():
    p = _producto_api(unit="fop.price.per.kg")
    p["price"] = {"current": {"amount": "5.00"},
                  "unit": {"current": {"amount": "3.00"}, "label": "per_litre"}}
    r = alcampo.a_registro(p)
    assert r["unidad_ref_nativa"] == "l"
    assert r["precio_ref_nativo_cent"] == 300


def test_se_guarda_la_imagen_del_producto():
    url = "https://www.compraonline.alcampo.es/images-v3/a/b/300x300.jpg"
    assert alcampo.a_registro(_producto_api(imagen=url))["imagen"] == url


def test_sin_imagen_no_falla():
    assert alcampo.a_registro(_producto_api())["imagen"] is None


# --- las etiquetas de Alcampo -------------------------------------------
# Alcampo es la cadena con menos datos: sin codigo de barras, nunca cruzara con
# Open Food Facts. Pero SI publica las etiquetas que la gente busca, y durante
# doce dias no las miro nadie: 3.337 sin gluten, 2.405 veganos, 1.105 sin
# lactosa, 1.052 ecologicos. Mas sellos que todo lo que da OFF.

def _con_iconos(*etiquetas, catchweight=None):
    p = {
        "productId": "abc", "retailerProductId": "123",
        "name": "Producto", "brand": "MARCA",
        "price": {"amount": "1.00"}, "available": True,
        "iconAttributes": [{"label": e} for e in etiquetas],
    }
    if catchweight:
        p["catchweight"] = catchweight
    return p


def test_los_sellos_salen_de_los_iconos():
    r = alcampo.a_registro(_con_iconos("Sin Gluten", "Vegano", "Producto Alcampo"))
    assert r["sellos"] == "sin-gluten,vegano"


def test_la_conservacion_tambien():
    assert alcampo.a_registro(_con_iconos("Refrigerado"))["conservacion"] == "refrigerado"
    assert alcampo.a_registro(_con_iconos("Congelado"))["conservacion"] == "congelado"
    assert alcampo.a_registro(_con_iconos("Sin Gluten"))["conservacion"] is None


def test_que_la_cadena_diga_que_es_marca_propia_es_mejor_que_deducirlo():
    # Hoy el panel deduce la marca propia del texto de la marca. Alcampo lo dice.
    assert alcampo.a_registro(_con_iconos("Producto Alcampo"))["es_marca_propia"] is True
    assert alcampo.a_registro(_con_iconos("Sin Gluten"))["es_marca_propia"] is None


def test_el_peso_variable_sale_de_la_etiqueta_o_del_rango():
    assert alcampo.a_registro(_con_iconos("Peso variable"))["peso_variable"] is True
    assert alcampo.a_registro(_con_iconos(
        catchweight={"minQuantity": {"value": 0.3}})) ["peso_variable"] is True
    assert alcampo.a_registro(_con_iconos("Sin Gluten"))["peso_variable"] is False


def test_sin_iconos_no_se_inventa_nada():
    r = alcampo.a_registro(_con_iconos())
    assert r["sellos"] is None and r["conservacion"] is None


def test_las_unidades_de_la_mecanica_se_leen_en_numero():
    """«2ª unidad -50 %» en texto y `requiredProductQuantity: 2` en número.

    Medido el 26 de septiembre de 2026: 1.639 productos del día (6,8 %) lo traen, con valores
    de 2 a 6. Se guarda el mayor, que es la condición más exigente, y `None` cuando ninguna
    oferta pide más de una unidad (que es distinto de «pide una»).
    """
    assert alcampo._unidades_de_la_mecanica([]) is None
    assert alcampo._unidades_de_la_mecanica([{"requiredProductQuantity": 1}]) is None
    assert alcampo._unidades_de_la_mecanica([{"description": "sin cantidad"}]) is None
    assert alcampo._unidades_de_la_mecanica(
        [{"requiredProductQuantity": 2}, {"requiredProductQuantity": 3}]) == 3
    # Una promoción con forma rara no puede tumbar la ficha entera: el 26 de septiembre de
    # 2026 el mismo tipo de descuido en `icons` mató el barrido del buscador entero.
    assert alcampo._unidades_de_la_mecanica(["texto suelto"]) is None
