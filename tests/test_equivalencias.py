"""Las equivalencias versionadas: clave estable, motivo guardado y nada pisado.

Lo que se prueba aqui es lo que el encargo pide de la Fase 1: que un par se
identifique por algo que no cambia, que cada pasada guarde POR QUE acepto cada
par, y que una pasada no pueda destruir la anterior.
"""
import json
from datetime import datetime

import polars as pl

from core import equivalencias as eq


def fila(fuente, id_fuente, nombre="Leche entera", marca="Puleva", cantidad=1.0,
         unidad="l", ean=None, precio_unidad=100, seccion="lacteos-huevos"):
    return {"fuente": fuente, "id_fuente": id_fuente, "nombre": nombre,
            "marca": marca, "cantidad": cantidad, "unidad_canon": unidad,
            "ean": ean, "precio_unidad_cent": precio_unidad, "seccion": seccion}


def test_el_id_de_producto_no_depende_de_su_posicion():
    """Es el fallo que tenia `enlaces.parquet`: pares de POSICIONES.

    Si el catalogo se reordena, los indices apuntan a otros productos y los
    grupos salen con cosas que no tienen nada que ver, en silencio.
    """
    a = eq.producto_id("dia", "12345")
    assert a == "dia:12345"
    # El mismo producto, en otra posicion de la lista, da el mismo id.
    filas = [fila("mercadona", "1"), fila("dia", "12345")]
    assert eq.producto_id(filas[1]["fuente"], filas[1]["id_fuente"]) == a


def test_la_huella_del_catalogo_cambia_si_cambia_el_orden():
    uno = [fila("dia", "1"), fila("dia", "2")]
    dos = [fila("dia", "2"), fila("dia", "1")]
    assert eq.huella_catalogo(uno) != eq.huella_catalogo(dos)
    assert eq.huella_catalogo(uno) == eq.huella_catalogo([fila("dia", "1"),
                                                          fila("dia", "2")])


def test_el_id_de_ejecucion_se_ordena_como_texto():
    a = eq.id_de_ejecucion(datetime(2026, 9, 22, 9, 5, 0))
    b = eq.id_de_ejecucion(datetime(2026, 9, 22, 14, 30, 12))
    assert a == "20260922-090500"
    assert sorted([b, a]) == [a, b]


def test_las_features_dicen_por_que_se_acepto_el_par():
    a = fila("dia", "1", ean="1111111111111", precio_unidad=100)
    b = fila("carrefour", "9", marca="Carrefour", ean="2222222222222",
             precio_unidad=300)
    f = eq.features(a, b, 0.72)
    assert f["parecido"] == 0.72
    assert f["ean_en_los_dos"] is True
    assert f["ean_igual"] is False          # dos codigos: dos productos
    assert f["marca_igual"] is False        # es una equivalencia, no el mismo
    assert f["cantidad_igual"] is True
    assert f["unidad_igual"] is True
    assert f["seccion_igual"] is True
    assert f["ratio_precio_unidad"] == 3.0


def test_la_equivalencia_guarda_metodo_y_clave_estable():
    filas = [fila("dia", "1"), fila("carrefour", "9")]
    e = eq.filas_de_equivalencia(filas, [(0, 1, 1.0, "ean"),
                                         (0, 1, 0.7, "equivalente")], "X")
    assert [x["metodo"] for x in e] == ["ean", "nombre"]
    assert e[0]["producto_a"] == "dia:1"
    assert e[0]["producto_b"] == "carrefour:9"
    assert json.loads(e[0]["features"])["parecido"] == 1.0


def test_una_pasada_no_pisa_a_la_anterior(tmp_path):
    """Nunca sobrescribir: es lo que pide el encargo, y aqui se comprueba."""
    filas = [fila("dia", "1"), fila("carrefour", "9")]
    uno = eq.escribe_ejecucion("20260922-090000",
                               eq.filas_de_equivalencia(filas, [(0, 1, 0.9, "x")], "a"),
                               {"enlaces": 1.0}, {"productos": 2}, gold=tmp_path)
    dos = eq.escribe_ejecucion("20260922-140000",
                               eq.filas_de_equivalencia(filas, [(0, 1, 0.8, "x")], "b"),
                               {"enlaces": 1.0}, {"productos": 2}, gold=tmp_path)
    assert uno != dos
    assert (uno / "equivalencia.parquet").exists()
    assert (dos / "equivalencia.parquet").exists()
    # La ultima manda, y la anterior sigue entera.
    assert eq.ultima(tmp_path) == "20260922-140000"
    assert eq.lee_equivalencias("20260922-090000", tmp_path)["confianza"][0] == 0.9
    assert eq.lee_equivalencias(gold=tmp_path)["confianza"][0] == 0.8
    assert eq.metricas_de("20260922-140000", tmp_path) == {"enlaces": 1.0}


def test_las_metricas_se_leen_por_ejecucion(tmp_path):
    eq.escribe_ejecucion("20260922-090000", [], {"enlaces": 3.0, "grupos": 2.0},
                         {"productos": 0}, gold=tmp_path)
    assert eq.metricas_de("20260922-090000", tmp_path) == {"enlaces": 3.0,
                                                           "grupos": 2.0}


def test_sin_ninguna_pasada_no_revienta(tmp_path):
    assert eq.ultima(tmp_path) is None
    assert eq.lee_equivalencias(gold=tmp_path).is_empty()


def test_la_ultima_se_deduce_de_las_carpetas_si_falta_el_marcador(tmp_path):
    eq.escribe_ejecucion("20260922-090000", [], {"a": 1.0}, {}, gold=tmp_path)
    eq.escribe_ejecucion("20260922-100000", [], {"a": 1.0}, {}, gold=tmp_path)
    (tmp_path / eq.CARPETA / "ultima.json").unlink()
    assert eq.ultima(tmp_path) == "20260922-100000"


def test_la_tabla_de_equivalencias_tiene_las_columnas_del_modelo(tmp_path):
    """El modelo de docs/DIAGNOSTICO-MATCHING.md §8, comprobado de verdad."""
    filas = [fila("dia", "1"), fila("carrefour", "9")]
    eq.escribe_ejecucion("20260922-090000",
                         eq.filas_de_equivalencia(filas, [(0, 1, 0.9, "x")], "a"),
                         {"enlaces": 1.0}, {"productos": 2}, gold=tmp_path)
    d = eq.lee_equivalencias(gold=tmp_path)
    for columna in ("producto_a", "producto_b", "nivel", "metodo", "confianza",
                    "features", "ejecucion_id"):
        assert columna in d.columns
    assert isinstance(d, pl.DataFrame)
