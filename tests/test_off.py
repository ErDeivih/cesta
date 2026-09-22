"""Open Food Facts cambia el esquema del volcado sin avisar.

El 7 sep la descarga entera reventaba porque `ecoscore_grade` habia pasado a
llamarse `environmental_score_grade`: una columna accesoria tumbaba el Nutri-Score
y los ingredientes de 26.000 productos.
"""
import pytest

from core.off import _filtro_espana, _seleccion


def test_usa_el_nombre_nuevo_cuando_existe():
    sel, ausentes = _seleccion({"code", "environmental_score_grade"})
    assert '"environmental_score_grade" AS ecoscore_grade' in sel
    assert "ecoscore_grade" not in ausentes


def test_sigue_valiendo_el_nombre_viejo():
    sel, _ = _seleccion({"code", "ecoscore_grade"})
    assert "ecoscore_grade" in sel


def test_una_columna_accesoria_que_desaparece_no_tumba_la_descarga():
    sel, ausentes = _seleccion({"code", "product_name", "nutriscore_grade"})
    assert "code" in sel and "nutriscore_grade" in sel
    assert "ecoscore_grade" in ausentes      # se avisa, no se revienta


def test_sin_codigo_de_barras_no_hay_nada_que_cruzar():
    with pytest.raises(RuntimeError, match="code"):
        _seleccion({"product_name", "nutriscore_grade"})


def test_acota_a_espana_con_el_campo_que_haya():
    assert "en:spain" in _filtro_espana({"countries_tags"})
    assert "spain" in _filtro_espana({"countries"}).lower()
    with pytest.raises(RuntimeError):
        _filtro_espana({"code"})


def test_el_texto_por_idioma_prefiere_el_castellano():
    from core.off import _texto_por_idioma
    sql = _texto_por_idioma("ingredients_text", 8)
    assert "x.lang = 'es'" in sql
    assert sql.index("'es'") < sql.index("'main'")   # el orden importa
    assert "length(trim(x.text)) > 8" in sql


def test_una_lista_por_idioma_se_aplana_y_el_texto_plano_no():
    from core.off import _seleccion
    lista, _ = _seleccion({"code": "VARCHAR",
                           "ingredients_text": 'STRUCT(lang VARCHAR, "text" VARCHAR)[]'})
    assert "list_filter(ingredients_text" in lista
    plano, _ = _seleccion({"code": "VARCHAR", "ingredients_text": "VARCHAR"})
    assert "list_filter" not in plano


def test_unknown_no_es_un_nutriscore():
    """count() decia 357.495 con Nutri-Score. Los de verdad son 102.871.

    'unknown' y 'not-applicable' no son nulos, asi que contaban como dato.
    """
    from core.off import _seleccion
    lista, _ = _seleccion({"code": "VARCHAR", "nutriscore_grade": "VARCHAR"})
    assert "CASE WHEN" in lista and "'a','b','c','d','e'" in lista
