"""Las ofertas son reglas sobre cuantas unidades compras, no precios."""
from core.promos import lee, unidades_optimas


def test_nxm_paga_dos_de_cada_tres():
    m = lee("3x2  (10/09/2026 al 23/09/2026)")
    assert m.tipo == "nxm"
    assert m.coste(3, 100) == 200
    assert m.coste(2, 100) == 200          # sin el grupo completo, no hay regalo
    assert m.coste(6, 100) == 400
    assert m.coste(7, 100) == 500          # cuatro grupos no, dos y una suelta


def test_segunda_unidad_rebaja_solo_la_segunda():
    # Este es el caso mas frecuente de todos y el que mas facil se cuenta mal:
    # "-50%" NO significa la mitad de todo, significa la mitad de una de cada dos.
    m = lee("2ª unidad -50%")
    assert m.tipo == "enesima"
    assert m.coste(1, 100) == 100
    assert m.coste(2, 100) == 150
    assert m.coste(3, 100) == 250
    assert m.coste(4, 100) == 300


def test_el_simbolo_ordinal_no_es_un_acento():
    # NFD no descompone "ª", asi que sin traducirlo a mano "2ª unidad -50%"
    # caia en la regla del porcentaje suelto y salia la mitad de todo.
    assert lee("2ª unidad -50%").coste(2, 100) == 150
    assert lee("2a unidad -50%").coste(2, 100) == 150


def test_porcentaje_suelto_se_aplica_a_todo():
    assert lee("-30% Días Locos").coste(2, 200) == 280


def test_precio_fijo_ignora_el_precio_del_producto():
    m = lee("Todo a 1€ (14/09/2026 - 08/10/2026)")
    assert m.tipo == "precio_fijo"
    assert m.coste(2, 250) == 200


def test_umbral_descuenta_por_cada_vez_que_se_alcanza():
    m = lee("5€ dto. comprando 20€ en Nestle")
    assert m.tipo == "umbral"
    assert m.coste(3, 500) == 1500         # 15 EUR: no llega a 20
    assert m.coste(4, 500) == 1500         # 20 EUR: llega una vez, -5


def test_un_descuento_de_solo_internet_no_baja_el_ticket_de_la_tienda():
    """El texto real de Alcampo, y son 397 promociones del catalogo.

    La mecanica se lee igual -- sigue siendo un umbral de 5 EUR por cada 20 --
    pero el descuento **no existe si vas a la tienda**, asi que no se resta del
    total de una cesta que se va a comprar a pie. Es el mismo trato que el de la
    tarjeta, y por la misma razon: se ensena, no se resta.
    """
    m = lee("5€ dto. comprando 20€ en Nestle. Exclusivo Online.")
    assert m.tipo == "umbral"           # la regla se entiende igual
    assert m.solo_online is True
    assert m.util is False
    assert m.coste(4, 500) == 2000      # 20 EUR enteros, sin el descuento


def test_las_formas_de_decir_solo_online_que_usan_las_cadenas():
    for txt in ("Cupón 1€ descuento. Solo Online.",
                "15% dto en estos productos NEUTROGENA. Exclusivo online",
                "Sólo online", "Exclusiva web", "solo en internet"):
        assert lee(txt).solo_online is True, txt


def test_una_oferta_normal_no_se_marca_como_de_internet():
    for txt in ("2ª unidad -50%", "3x2", "-20%", "Todo a 1€"):
        assert lee(txt).solo_online is False, txt


def test_los_descuentos_de_tarjeta_no_bajan_lo_que_pagas_hoy():
    # Ese dinero no se descuenta en caja: se acumula en un monedero. Restarlo
    # seria mentir sobre lo que vas a pagar.
    m = lee("Club Alcampo 2ª unidad -50% acum en tu tarjeta")
    assert m.acumulable
    assert not m.util
    assert m.coste(2, 100) == 200
    assert lee("2x1 Acumula").coste(2, 100) == 200


def test_lo_que_no_es_una_oferta_no_lo_parece():
    for texto in ("Producto en Folleto (10/09/26_23/09/26)", "Novedad Alcampo",
                  "Stock Fuera (Unidades Limitadas)", "En pack, más fácil",
                  "PROTEÍNA, CALIDAD, SABOR", None, ""):
        m = lee(texto)
        assert not m.util, texto
        assert m.coste(2, 100) == 200, texto


def test_un_nxm_absurdo_no_se_acepta():
    # "24x33" es un formato de pack, no una oferta.
    assert not lee("pack 24 x 33 cl").util


def test_sugiere_llevar_una_mas_solo_cuando_baja_el_precio_unitario():
    assert unidades_optimas(lee("3x2"), 2) == 3           # la tercera sale gratis
    assert unidades_optimas(lee("2ª unidad -50%"), 2) == 2   # ya esta aprovechada
    assert unidades_optimas(lee("-30%"), 2) == 2          # no depende de cuantas
    assert unidades_optimas(lee("Novedad Alcampo"), 2) == 2

# ------------------------------------------------------------------- el 3x2, con datos controlados ---
#
# **Los numeros son mios, no del catalogo.** El ensayo de punta a punta prueba el 3x2 con un producto
# real (589 centimos, oferta 3x2), y por eso depende de que una cadena publique un 3x2 esa manana.
# Esto no: es la cuenta, con numeros fijos. Es la diferencia entre probar el motor y probar el catalogo.
#
# Y son **las dos formas que pide el encargo**: una linea de tres, y dos lineas de una y dos, **las dos
# persistiendo exactamente 200 centimos en total**. Medido el 13 de octubre de 2026.


def test_el_3x2_con_datos_controlados_da_200_las_dos_formas():
    """Una linea de tres, y dos lineas de una y dos: el mismo total."""
    promo = lee("3x2")
    assert promo.coste(3, 100) == 200, "una linea de tres"
    assert promo.coste(1 + 2, 100) == 200, "dos lineas de una y dos"


def test_el_reparto_conserva_el_total_al_centimo():
    """Las partes de un grupo suman el total: 67 + 133 = 200."""
    from plataforma.api.almacen import _lo_que_se_paga

    partes = [_lo_que_se_paga(100, 67, 1), _lo_que_se_paga(100, 133, 2)]
    assert sum(partes) == 200, partes
