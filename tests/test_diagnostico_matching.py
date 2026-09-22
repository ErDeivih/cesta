"""El diagnostico de matching de la Fase 0: que las cuentas no se inventen nada.

Estas pruebas no miden el catalogo real (eso lo hace
`uv run python -m projects.cesta.diagnostico_matching`): comprueban que las
cuentas que salen en `docs/DIAGNOSTICO-MATCHING.md` se calculan como dicen sus
definiciones. Si una definicion cambia, el informe cambia con ella y no antes.
"""
from projects.cesta.diagnostico_matching import (
    calidad_formato,
    dispersion_grupos,
    grupos_y_cadenas,
    por_que_falla,
    sospechosos,
    tope_ean,
    tope_por_bloque,
)


def fila(fuente, nombre, marca=None, cantidad=None, unidad=None, ean=None,
         precio_unidad=None, seccion=None, grupo=0):
    return {
        "fuente": fuente, "nombre": nombre, "marca": marca, "cantidad": cantidad,
        "unidad_canon": unidad, "ean": ean, "precio_unidad_cent": precio_unidad,
        "precio_cent": precio_unidad, "cat1": seccion, "grupo_id": grupo,
        "ean_n": ean, "marca_n": marca.lower() if marca else None,
    }


def test_tope_ean_solo_cuenta_pares_entre_cadenas():
    """Dos filas con el mismo EAN en la MISMA cadena no son un tope de nada."""
    filas = [
        fila("dia", "Leche entera", "Puleva", 1.0, "l", "8410000000001"),
        fila("dia", "Leche entera 2", "Puleva", 1.0, "l", "8410000000001"),
        fila("carrefour", "Leche entera", "Puleva", 1.0, "l", "8410000000001"),
    ]
    t = tope_ean(filas, [])
    assert t["verdad"] == 2
    assert t["ean_multicadena"] == 1


def test_tope_ean_ignora_los_ean_que_solo_esta_en_una_cadena():
    filas = [
        fila("dia", "Leche", "Puleva", 1.0, "l", "8410000000001"),
        fila("carrefour", "Leche", "Puleva", 1.0, "l", "8410000000002"),
    ]
    assert tope_ean(filas, [])["verdad"] == 0


def test_tope_por_bloque_necesita_dos_cadenas_y_la_misma_clave():
    filas = [
        fila("dia", "Arroz", cantidad=1.0, unidad="kg", seccion="despensa"),
        fila("carrefour", "Arroz", cantidad=1.0, unidad="kg", seccion="despensa"),
        # Misma seccion pero otro formato: no es comparable.
        fila("aldi", "Arroz", cantidad=0.5, unidad="kg", seccion="despensa"),
        # Sin formato: no entra.
        fila("mercadona", "Arroz", seccion="despensa"),
    ]
    t = tope_por_bloque(filas)
    assert t["bloques"] == 1
    assert t["productos"] == 2
    assert t["pares_1a1"] == 1


def test_sospechosos_no_llama_fallo_a_dos_marcas_distintas():
    """El objetivo del proyecto es comparar marcas blancas: EAN distinto es normal."""
    filas = [
        fila("dia", "Leche entera", marca="Dia", cantidad=1.0, unidad="l",
             ean="1111111111111", precio_unidad=100),
        fila("carrefour", "Leche entera", marca="Carrefour", cantidad=1.0,
             unidad="l", ean="2222222222222", precio_unidad=100),
    ]
    s = sospechosos(filas, [(0, 1, 1.0, "equivalente")])
    assert s["ean_distinto"] == [(0, 1, 1.0, "equivalente")]
    assert s["marca_igual_ean_distinto"] == []


def test_sospechosos_detecta_la_misma_marca_con_dos_codigos():
    filas = [
        fila("dia", "San Miguel 33 cl", marca="San Miguel", cantidad=0.33,
             unidad="l", ean="1111111111111"),
        fila("carrefour", "San Miguel sin gluten", marca="San Miguel",
             cantidad=0.33, unidad="l", ean="2222222222222"),
    ]
    s = sospechosos(filas, [(0, 1, 0.91, "identico")])
    assert len(s["marca_igual_ean_distinto"]) == 1


def test_sospechosos_mide_el_precio_por_unidad_solo_en_la_misma_unidad():
    iguales = [
        fila("dia", "A", cantidad=1.0, unidad="l", precio_unidad=100),
        fila("carrefour", "A", cantidad=1.0, unidad="l", precio_unidad=200),
    ]
    assert len(sospechosos(iguales, [(0, 1, 1.0, "x")])["precio"]) == 1
    # 100 -> 200 es exactamente el doble, por encima del 60 %.
    distintas = [
        fila("dia", "A", cantidad=0.5, unidad="kg", precio_unidad=100),
        fila("carrefour", "A", cantidad=1.0, unidad="l", precio_unidad=900),
    ]
    assert sospechosos(distintas, [(0, 1, 1.0, "x")])["precio"] == []


def test_grupos_y_cadenas_cuenta_los_grupos_de_una_sola_cadena():
    filas = [
        fila("dia", "A", grupo=0),
        fila("carrefour", "A", grupo=0),
        fila("dia", "B", grupo=1),
        fila("dia", "B2", grupo=1),
        fila("aldi", "C", grupo=2),
    ]
    import polars as pl

    g = pl.DataFrame({"grupo_id": [0, 0, 1, 1, 2]})
    r = grupos_y_cadenas(filas, g)
    assert r["n_grupos"] == 3
    assert len(r["comparables"]) == 1
    assert r["productos_comparables"] == 2
    assert r["solos"] == 1
    assert r["solo_una_cadena"] == 1


def test_calidad_formato_cuenta_los_absurdos():
    filas = [
        fila("dia", "Azafran", cantidad=0.0004, unidad="kg"),
        fila("alcampo", "Azafran", cantidad=0.4, unidad="kg"),
        fila("dia", "Suavizante", cantidad=63.0, unidad="l"),
        fila("dia", "Sin formato"),
    ]
    c = calidad_formato(filas)["dia"]
    assert c["n"] == 3
    assert c["sin_cantidad"] == 1
    assert c["absurdo"] == 1          # los 63 litros de suavizante
    assert calidad_formato(filas)["alcampo"]["absurdo"] == 0


def test_dispersion_de_grupo_solo_mira_kg_l_m():
    filas = [
        fila("dia", "A", cantidad=1.0, unidad="kg", precio_unidad=100, grupo=0),
        fila("carrefour", "A", cantidad=1.0, unidad="kg", precio_unidad=400, grupo=0),
        # En 'ud' cada cadena cuenta cosas distintas: no entra en la medida.
        fila("dia", "B", cantidad=1.0, unidad="ud", precio_unidad=100, grupo=1),
        fila("carrefour", "B", cantidad=6.0, unidad="ud", precio_unidad=900, grupo=1),
    ]
    d = dispersion_grupos(filas)
    assert d["con_precio"] == 1
    assert d["mas_200"] == 1


def test_por_que_falla_clasifica_los_cuatro_motivos():
    filas = [
        # 0-1: mismo formato, nombres que no se parecen nada.
        fila("dia", "Zzz", cantidad=1.0, unidad="kg"),
        fila("carrefour", "Qqq", cantidad=1.0, unidad="kg"),
        # 2-3: uno sin formato.
        fila("dia", "Leche entera Puleva"),
        fila("carrefour", "Leche entera Puleva", cantidad=1.0, unidad="l"),
        # 4-5: unidades distintas.
        fila("dia", "Arroz", cantidad=1.0, unidad="kg"),
        fila("carrefour", "Arroz", cantidad=1.0, unidad="ud"),
    ]
    verdad = {(0, 1), (2, 3), (4, 5)}
    r = por_que_falla(filas, verdad, [])
    assert r["acertados"] == 0
    assert r["fallados"] == 3
    assert r["motivos"]["formato ilegible en alguno de los dos"] == 1
    assert r["motivos"]["una cadena lo vende en otra unidad"] == 1
    assert r["motivos"]["mismo formato y por debajo del umbral"] == 1


def test_por_que_falla_no_cuenta_los_que_si_encuentra():
    filas = [
        fila("dia", "Leche entera Puleva", cantidad=1.0, unidad="l"),
        fila("carrefour", "Leche entera Puleva", cantidad=1.0, unidad="l"),
    ]
    r = por_que_falla(filas, {(0, 1)}, [(0, 1, 1.0, "identico")])
    assert r["acertados"] == 1
    assert r["fallados"] == 0
