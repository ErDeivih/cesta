"""Calidad A/B/C: se lee de la etiqueta, no se opina."""
from core.calidad import analiza, letras, por_precio, puntua


def test_cuenta_los_aditivos_escritos_de_cualquier_manera():
    s = analiza("Agua, acidulante (E-330), conservador E202, colorante E 150d")
    assert s["aditivos"] == 3


def test_sin_lista_de_ingredientes_no_hay_nota():
    assert analiza(None) is None
    assert analiza("   ") is None
    assert puntua(None) is None


def test_mas_aditivos_baja_la_nota():
    limpio = puntua("Tomate, sal")
    sucio = puntua("Tomate, sal, E-330, E-202, E-150d, E-621, E-471")
    assert limpio > sucio


def test_el_aceite_de_palma_penaliza():
    con = puntua("Harina, azucar, aceite de palma")
    sin = puntua("Harina, azucar, aceite de girasol")
    assert sin > con


def test_un_porcentaje_alto_del_principal_sube_la_nota():
    # Con una lista limpia la nota ya esta en el tope, asi que se compara sobre
    # dos mermeladas igual de aditivadas: lo unico que cambia es la fruta.
    mucha = puntua("Fresa 65%, azucar, E-330, E-440, conservador E-202")
    poca = puntua("Fresa 30%, azucar, E-330, E-440, conservador E-202")
    assert mucha > poca


def test_con_menos_de_tres_productos_no_se_reparten_letras():
    # Un tercil sobre dos productos es ruido con aspecto de dato.
    assert letras([90.0, 40.0]) == [None, None]


def test_reparte_por_terciles_dentro_del_grupo():
    assert letras([100.0, 90.0, 50.0, 40.0, 10.0, 5.0]).count("A") >= 1
    assert letras([100.0, 90.0, 50.0, 40.0, 10.0, 5.0])[0] == "A"
    assert letras([100.0, 90.0, 50.0, 40.0, 10.0, 5.0])[-1] == "C"


def test_los_productos_sin_ingredientes_no_reciben_letra_de_etiqueta():
    assert letras([80.0, 60.0, 40.0, None])[-1] is None


def test_el_respaldo_por_precio_da_la_A_al_mas_caro():
    assert por_precio([100.0, 200.0, 300.0, 400.0])[-1] == "A"


def test_los_ingredientes_de_la_cadena_mandan_sobre_los_de_fuera():
    from projects.cesta.emparejar import composicion
    filas = [{"fuente": "dia", "id_fuente": "1", "ean": "8480000123456"}]
    propios = {("dia", "1"): "Tomate, sal"}
    fuera = {"8480000123456": {"ingredientes": "Otra cosa distinta"}}
    textos, procedencias = composicion(filas, propios, fuera)
    assert textos == ["Tomate, sal"]
    assert procedencias == ["cadena"]


def test_si_la_cadena_no_publica_ingredientes_se_usan_los_de_fuera():
    from projects.cesta.emparejar import composicion
    filas = [{"fuente": "carrefour", "id_fuente": "9", "ean": "8480000123456"}]
    fuera = {"8480000123456": {"ingredientes": "Tomate, sal, E-330"}}
    textos, procedencias = composicion(filas, {}, fuera)
    assert textos == ["Tomate, sal, E-330"]
    assert procedencias == ["off"]      # el origen viaja con el dato


def test_sin_ingredientes_en_ninguna_parte_no_se_inventa_nada():
    from projects.cesta.emparejar import composicion
    filas = [{"fuente": "aldi", "id_fuente": "3", "ean": None}]
    textos, procedencias = composicion(filas, {}, {"123": {"ingredientes": "x"}})
    assert textos == [None] and procedencias == [None]
