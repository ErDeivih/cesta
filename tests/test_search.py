import duckdb

from projects.cesta.search import buscar


def catalogo():
    con = duckdb.connect()
    con.execute("""CREATE TABLE producto AS SELECT * FROM (VALUES
        ('mercadona', '1', 'Aceite de oliva virgen extra', 'Hacendado', 750, 750.0, 'l', true, 'u1', true, 'aceite oliva virgen extra'),
        ('alcampo', '2', 'Aceite de girasol', 'Auchan', 180, 180.0, 'l', true, 'u2', true, 'aceite girasol'),
        ('aldi', '3', 'Aceite de oliva sin precio', NULL, NULL, NULL, 'ud', true, 'u3', false, 'aceite oliva sin precio')
    ) t(fuente,id_fuente,nombre,marca,precio_cent,precio_unidad_cent,unidad_canon,disponible,url,precio_comparable,nombre_limpio)""")
    return con


def test_busqueda_prioriza_la_frase_y_admite_filtros():
    con = catalogo()
    assert buscar("aceite oliva", con=con)[0]["id_fuente"] == "1"
    assert buscar("aceite", fuente="alcampo", con=con)[0]["id_fuente"] == "2"
    assert buscar("aceite", marca="hacendado", con=con)[0]["id_fuente"] == "1"


def test_busqueda_conserva_productos_sin_precio():
    filas = buscar("sin precio", con=catalogo())
    assert filas[0]["precio_comparable"] is False
