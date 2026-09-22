"""El emparejador entre cadenas: los fallos que costaron medirlo.

Los numeros de estas pruebas salen de la medicion real del 7 sep sobre 38.294
productos, usando como respuestas correctas los 1.767 pares que ya sabiamos
ciertos por codigo de barras.
"""
import pytest

from core.matching import agrupar, bloque, enlaces, idf, nivel, parecido, raiz, tokens


def test_el_plural_no_puede_romper_el_emparejamiento():
    # Carrefour escribe "Alubia morada", DIA "Alubias moradas". Es el mismo bote.
    a = tokens("Alubia morada Luengo 1 kg.", "Luengo")
    b = tokens("Alubias moradas Luengo 1 Kg", "Luengo")
    assert a == b


def test_raiz_no_destroza_palabras_cortas():
    assert raiz("gas") == "gas"
    assert raiz("arroz") == "arroz"
    assert raiz("quesos") == "queso"


def test_la_marca_cuenta_como_palabra():
    # "Fairy 654 ml" en DIA se quedaba SIN NINGUNA palabra cuando se quitaba la
    # marca, y asi no podia emparejar con nada.
    assert tokens("Fairy 654 ml", "Fairy")


def test_nombres_de_distinta_longitud_siguen_pareciendose():
    """Dice, no Jaccard: todo lo que dice el corto lo dice el largo.

    Y el IDF hace el resto: en un catalogo real "lavavajillas" o "mano" salen en
    cientos de productos y "fairy" en un punado, asi que la marca pesa mucho mas
    que el resto del nombre junto.
    """
    corto = tokens("Fairy 654 ml", "Fairy")
    largo = tokens("Lavavajillas a mano ultra poder Fairy 654 ml", "Fairy")
    relleno = [tokens(f"Lavavajillas a mano ultra poder marca{n}", f"marca{n}")
               for n in range(60)]
    pesos = idf([corto, largo, *relleno])
    assert parecido(corto, largo, pesos) > 0.4


def test_formatos_distintos_no_se_comparan():
    assert bloque(1.0, "l") != bloque(0.2, "l")
    assert bloque(None, "l") == ("?",)


def test_misma_marca_es_identico_y_distinta_marca_es_equivalente():
    a = {"marca": "Hacendado", "ean": None}
    b = {"marca": "Hacendado", "ean": None}
    c = {"marca": "Carrefour", "ean": None}
    assert nivel(a, b) == "identico"
    assert nivel(a, c) == "equivalente"


def test_el_mismo_ean_manda_por_encima_de_la_marca():
    a = {"marca": "Coca-Cola", "ean": "5449000000996"}
    b = {"marca": "CocaCola España", "ean": "5449000000996"}
    assert nivel(a, b) == "identico"


def _filas():
    return [
        {"fuente": "a", "nombre": "Leche semidesnatada Asturiana 1 L",
         "marca": "Asturiana", "cantidad": 1.0, "unidad_canon": "l", "ean": None},
        {"fuente": "b", "nombre": "Leche semidesnatada Central Lechera Asturiana",
         "marca": "Asturiana", "cantidad": 1.0, "unidad_canon": "l", "ean": None},
        {"fuente": "c", "nombre": "Tornillos de acero inoxidable",
         "marca": "Ferreteria", "cantidad": 1.0, "unidad_canon": "l", "ean": None},
    ]


def test_empareja_lo_que_es_igual_y_deja_fuera_lo_que_no():
    ls = enlaces(_filas(), umbral=0.55, usar_ean=False)
    pares = {(i, j) for i, j, _, _ in ls}
    assert (0, 1) in pares
    assert not any(2 in p for p in pares)


def test_no_empareja_dentro_de_la_misma_cadena():
    filas = _filas()
    filas[1]["fuente"] = "a"          # las dos leches en la misma cadena
    assert not enlaces(filas, umbral=0.55, usar_ean=False)


def test_solo_se_enlaza_la_eleccion_mutua():
    """Si B ya tiene en la cadena de A algo que le pega mejor, A no se le cuelga.

    Sin esta condicion el parecido se propagaba en cadena y llegaba a meter tres
    mil productos en un grupo: medido, la precision caia por debajo del 1%.
    """
    filas = [
        # cadena a
        {"fuente": "a", "nombre": "Yogur natural", "marca": "X",
         "cantidad": 0.125, "unidad_canon": "kg", "ean": None},
        {"fuente": "a", "nombre": "Yogur natural azucarado con fresa", "marca": "X",
         "cantidad": 0.125, "unidad_canon": "kg", "ean": None},
        # cadena b: identico al segundo de la cadena a
        {"fuente": "b", "nombre": "Yogur natural azucarado con fresa", "marca": "Y",
         "cantidad": 0.125, "unidad_canon": "kg", "ean": None},
    ]
    pares = {(i, j) for i, j, _, _ in enlaces(filas, umbral=0.5, usar_ean=False)}
    assert (1, 2) in pares       # la pareja de verdad
    assert (0, 2) not in pares   # el otro no se cuela


def test_el_mismo_ean_empareja_aunque_el_nombre_no_se_parezca():
    filas = [
        {"fuente": "a", "nombre": "Refresco de cola", "marca": "X",
         "cantidad": 0.33, "unidad_canon": "l", "ean": "5449000000996"},
        {"fuente": "b", "nombre": "Coca Cola lata", "marca": "Y",
         "cantidad": 0.33, "unidad_canon": "l", "ean": "5449000000996"},
    ]
    assert agrupar(filas)[0] == agrupar(filas)[1]


def test_emparejar_no_lee_los_argumentos_de_run():
    """`run.py --solo alcampo` reventaba: argparse de emparejar leia sys.argv.

    main() se llama dentro del proceso de run.py, asi que tiene que recibir sus
    argumentos explicitamente y no fisgar en la linea de ordenes ajena.
    """
    import sys
    from unittest import mock

    from projects.cesta import emparejar

    with mock.patch.object(sys, "argv", ["run.py", "--solo", "alcampo"]):
        with mock.patch.object(emparejar, "catalogo_actual",
                               side_effect=FileNotFoundError("sin silver")):
            try:
                emparejar.main([])
            except FileNotFoundError:
                pass          # llego hasta los datos: argparse no protesto
            except SystemExit as exc:
                raise AssertionError(f"argparse leyo sys.argv: {exc}") from None


def test_las_unidades_fiables_no_incluyen_ud():
    """En "ud" cada cadena cuenta una cosa: Mercadona vende un paquete de seis
    rollos como 1 ud y publica el precio por rollo. Medido sobre 4.780 grupos,
    en "ud" una de cada cuatro comparaciones da una diferencia imposible.
    """
    from projects.cesta.emparejar import UNIDADES_FIABLES

    assert "ud" not in UNIDADES_FIABLES
    assert set(UNIDADES_FIABLES) == {"kg", "l", "m"}


def test_sin_marca_dos_marcas_blancas_se_reconocen():
    """Es para lo que existe el proyecto: comparar el Hacendado con el Carrefour."""
    from core.matching import idf, parecido, tokens_sin_marca

    a = tokens_sin_marca("Leche entera Hacendado", "Hacendado")
    b = tokens_sin_marca("Leche entera Carrefour Classic", "Carrefour")
    assert "leche" in a and "leche" in b
    assert "hacendado" not in a and "carrefour" not in b
    assert parecido(a, b, idf([a, b])) > 0.6


def test_los_trigramas_salvan_lo_que_una_cadena_junta_y_otra_separa():
    from core.matching import dice, trigramas

    junto = trigramas("Galleta chocowafer Milka", "Milka")
    separado = trigramas("Galletas choco wafer Milka", "Milka")
    assert dice(junto, separado) > 0.7


def test_un_equivalente_no_puede_robarle_el_sitio_al_identico():
    """Con una sola eleccion por cadena, el mejor candidato de un Hacendado
    pasaba a ser el Carrefour equivalente y se perdia el Hacendado identico de
    la otra cadena. Medido: el acierto caia del 53 % al 43 %.
    """
    filas = [
        {"fuente": "a", "nombre": "Leche entera Hacendado", "marca": "Hacendado",
         "cantidad": 1.0, "unidad_canon": "l", "ean": None},
        {"fuente": "b", "nombre": "Leche entera Hacendado", "marca": "Hacendado",
         "cantidad": 1.0, "unidad_canon": "l", "ean": None},
        {"fuente": "b", "nombre": "Leche entera Carrefour", "marca": "Carrefour",
         "cantidad": 1.0, "unidad_canon": "l", "ean": None},
    ]
    ls = enlaces(filas, umbral=0.55, usar_ean=False)
    pares = {(i, j): niv for i, j, _, niv in ls}
    assert pares.get((0, 1)) == "identico"        # no se pierde
    assert pares.get((0, 2)) == "equivalente"     # y ademas se encuentra


def test_sin_formato_se_exige_que_el_nombre_sea_casi_el_mismo():
    from core.matching import UMBRAL_SIN_FORMATO

    # 334 de los 1.767 pares ciertos tienen el formato sin leer en algun lado.
    # Ahi no se puede comprobar el tamano, asi que el liston del nombre sube.
    assert UMBRAL_SIN_FORMATO > 0.8
    filas = [
        {"fuente": "a", "nombre": "Chocolate negro 70% cacao Valor", "marca": "Valor",
         "cantidad": None, "unidad_canon": None, "ean": None},
        {"fuente": "b", "nombre": "Chocolate negro 70% cacao Valor", "marca": "Valor",
         "cantidad": None, "unidad_canon": None, "ean": None},
        {"fuente": "b", "nombre": "Chocolate con leche Valor", "marca": "Valor",
         "cantidad": None, "unidad_canon": None, "ean": None},
    ]
    # Relleno de la misma cadena: no empareja con nadie, pero hace que "cacao" y
    # "valor" sean palabras raras. La segunda pasada solo mira quien comparte una
    # palabra rara, y en un catalogo de tres productos no hay nada raro.
    filas += [{"fuente": "a", "nombre": f"Chocolate corriente numero {n}",
               "marca": f"marca{n}", "cantidad": None, "unidad_canon": None,
               "ean": None} for n in range(80)]
    pares = {(i, j) for i, j, _, _ in enlaces(filas, umbral=0.55, usar_ean=False)}
    assert (0, 1) in pares
    assert (0, 2) not in pares


# ---------------------------------------------------------------------------
# La asignacion 1-a-1 (algoritmo hungaro)
# ---------------------------------------------------------------------------
# Es la pieza que sustituyo a "cada producto elige al mejor y vale si la
# eleccion es mutua". Estas pruebas fijan lo que tiene que cumplir, incluido el
# caso en el que elegir por codicia da un resultado peor que el optimo.


def test_asignacion_1a1_no_repite_ningun_producto():
    from core.matching import _asignacion_1a1

    # Dos de la izquierda quieren a la misma de la derecha. Solo uno puede.
    pares = _asignacion_1a1([(0, 10, 0.9), (1, 10, 0.8), (1, 11, 0.7)], 0.5)
    assert len(pares) == 2
    izquierdas = [i for i, _j, _s in pares]
    derechas = [j for _i, j, _s in pares]
    assert len(set(izquierdas)) == len(izquierdas)
    assert len(set(derechas)) == len(derechas)


def test_asignacion_1a1_gana_a_elegir_por_codicia():
    from core.matching import _asignacion_1a1

    # Por codicia: el 0 se lleva el 10 (0,90) y el 1 se queda con el 11 (0,30):
    # total 1,20. Optimo: 0 con el 11 (0,80) y 1 con el 10 (0,85): total 1,65.
    # Es exactamente el fallo que se midio el 22 de septiembre: 137 de los 701
    # pares ciertos se perdian asi, por no mirar el conjunto.
    candidatos = [(0, 10, 0.90), (0, 11, 0.80), (1, 10, 0.85), (1, 11, 0.30)]
    pares = dict(((i, j), s) for i, j, s in _asignacion_1a1(candidatos, 0.5))
    assert sum(pares.values()) == pytest.approx(1.65)
    assert pares[(0, 11)] == 0.80
    assert pares[(1, 10)] == 0.85


def test_asignacion_1a1_respeta_el_umbral():
    from core.matching import _asignacion_1a1

    # Un par por debajo del liston no se acepta aunque este solo.
    assert _asignacion_1a1([(0, 10, 0.40)], 0.55) == []
    assert _asignacion_1a1([(0, 10, 0.60)], 0.55) == [(0, 10, 0.60)]


def test_asignacion_1a1_con_listas_de_tamanos_distintos():
    from core.matching import _asignacion_1a1

    # Dos de un lado, tres del otro: se emparejan los dos que pueden.
    pares = _asignacion_1a1([(0, 10, 0.9), (1, 11, 0.9), (1, 12, 0.8)], 0.5)
    assert sorted((i, j) for i, j, _s in pares) == [(0, 10), (1, 11)]
    # Y al reves, con mas a la izquierda que a la derecha.
    pares = _asignacion_1a1([(0, 10, 0.9), (1, 10, 0.8), (2, 10, 0.7)], 0.5)
    assert len(pares) == 1
    assert pares[0][:2] == (0, 10)


def test_asignacion_1a1_sin_candidatos():
    from core.matching import _asignacion_1a1

    assert _asignacion_1a1([], 0.5) == []


def test_la_asignacion_deja_un_grupo_sin_repetir_cadena():
    """Dos productos de la misma cadena no pueden acabar con la misma pareja.

    Es lo que el diagnostico encontro en 1.378 grupos comparables el 22 de
    septiembre: la misma cadena repetida dentro de un grupo.
    """
    filas = [
        {"fuente": "a", "nombre": "Leche entera Hacendado", "marca": "Hacendado",
         "cantidad": 1.0, "unidad_canon": "l", "ean": None},
        {"fuente": "a", "nombre": "Leche entera Hacendado brik", "marca": "Hacendado",
         "cantidad": 1.0, "unidad_canon": "l", "ean": None},
        {"fuente": "b", "nombre": "Leche entera Hacendado", "marca": "Hacendado",
         "cantidad": 1.0, "unidad_canon": "l", "ean": None},
    ]
    ls = enlaces(filas, umbral=0.55, usar_ean=False)
    # El producto 2 (cadena b) no puede estar en dos enlaces del mismo canal.
    del_2 = [x for x in ls if 2 in (x[0], x[1])]
    assert len(del_2) == 1


def test_identico_exige_el_mismo_codigo_de_barras():
    """La marca sola no hace identico a nada: dos codigos distintos son dos productos.

    Antes `nivel()` llamaba identico a dos productos con EAN distinto solo por
    compartir marca, y medido el 22 de septiembre mentia en el 30 % de los casos
    comprobables (442 de 1.475).
    """
    from core.matching import nivel

    igual_marca = {"marca": "San Miguel", "ean": "8410655002410"}
    otra = {"marca": "San Miguel", "ean": "8410655000010"}
    assert nivel(igual_marca, otra) == "equivalente"
    assert nivel(igual_marca, dict(igual_marca)) == "identico"
    # Sin codigos que comparar, la marca si decide.
    assert nivel({"marca": "San Miguel"}, {"marca": "San Miguel"}) == "identico"
    assert nivel({"marca": "San Miguel"}, {"marca": "Amstel"}) == "equivalente"
    # Un solo codigo tampoco basta para llamarlo identico.
    assert nivel(igual_marca, {"marca": "San Miguel"}) == "identico"


def test_el_veto_de_precio_solo_actua_cuando_se_puede_comparar():
    """30 veces, no el 60 % del plan: por debajo hay ahorros reales de 28x.

    Un veto al 60 % habria marcado 3.191 de 17.789 enlaces (medido el 22 de
    septiembre), o sea la mitad del valor del comparador. Y solo actua con la
    misma unidad, con precio en los dos lados y con el formato de fiar.
    """
    from core.matching import precio_imposible

    base = {"unidad_canon": "kg", "precio_comparable": True}
    barato = {**base, "precio_unidad_cent": 100}
    caro = {**base, "precio_unidad_cent": 5000}
    assert precio_imposible(barato, caro)          # x50: imposible
    assert not precio_imposible(barato, {**base, "precio_unidad_cent": 2000})  # x20
    # Sin la misma unidad no se compara: EUR/kg contra EUR/lavado no dice nada.
    assert not precio_imposible(barato, {**caro, "unidad_canon": "ud"})
    assert not precio_imposible(barato, {**caro, "unidad_canon": None})
    # La cadena ya dijo que su precio por unidad no es comparable.
    assert not precio_imposible(barato, {**caro, "precio_comparable": False})
    # Falta un precio.
    assert not precio_imposible(barato, {**base, "precio_unidad_cent": None})
    assert not precio_imposible(barato, {**base, "precio_unidad_cent": 2})
