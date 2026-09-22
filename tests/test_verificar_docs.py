"""El control que vigila que las cifras de los documentos sigan siendo verdad.

Y, sobre todo, que no diga "ok" cuando no ha comparado nada. El 18 de septiembre
de 2026, en un ensayo con un catalogo de mentira de 123 productos, las nueve
comprobaciones salieron en verde y el control termino diciendo "los numeros de
los documentos cuadran con los datos de hoy". No cuadraban: "123" estaba dentro
de "1.234" en algun documento, y el "0" de las capas que no habian corrido estaba
en todas partes.
"""
from projects.cesta.verificar_docs import _citado, _miles


def test_una_cifra_que_esta_de_verdad_cuenta():
    assert _citado("52.575", ["hoy el catalogo son 52.575 productos"])


def test_un_trozo_de_otra_cifra_no_cuenta():
    # "123" dentro de "1.234" era el falso positivo original.
    assert not _citado("123", ["el emparejador hizo 1.234 enlaces"])
    assert not _citado("575", ["hoy el catalogo son 52.575 productos"])


def test_dentro_de_una_fecha_tampoco():
    assert not _citado("18", ["medido el 2026-09-18 por la manana"])


def test_el_cero_nunca_se_da_por_citado():
    # "0 productos con Nutri-Score" no es una cifra que verificar: es una capa
    # que no ha corrido.
    assert not _citado("0", ["0 productos con Nutri-Score", "cero de cero"])


def test_la_cifra_pegada_a_puntuacion_normal_si_cuenta():
    assert _citado("6.448", ["comparables 6.448."])
    assert _citado("6.448", ["(6.448)"])


def test_los_miles_se_escriben_con_punto():
    assert _miles(52575) == "52.575"
    assert _miles(123) == "123"


def test_un_numero_de_dos_cifras_no_vale_como_vigilancia():
    # En un ensayo con 60 productos, "60" aparecia en algun documento por
    # casualidad y la comprobacion salia en verde sin haber vigilado nada.
    assert not _citado("60", ["hay 60 categorias en el menu"])
    assert _citado("761", ["761 productos con certificado"])
