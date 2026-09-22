"""Los filtros de dieta de la busqueda.

El fallo que estas pruebas cierran, encontrado el 17 de septiembre de 2026 al
probar el filtro recien hecho: buscar "galletas" con el filtro **sin gluten**
devolvia unas galletas Cuetara normales. La razon es que la busqueda trabaja por
GRUPOS -- un grupo entra si alguno de sus miembros casa -- y luego reconstruia el
grupo entero para ensenar el mas barato. Si en el grupo habia unas galletas sin
gluten y unas normales, y las normales eran mas baratas, se ensenaban las
normales bajo el filtro "sin gluten".

Para alguien celiaco eso no es un resultado flojo: es un resultado peligroso. La
regla es que el TEXTO se puede cumplir a nivel de grupo, pero un ATRIBUTO tiene
que cumplirlo cada producto que se ensena.
"""
import duckdb
import pytest

COLUMNAS = ("fuente, id_fuente, nombre, marca, cantidad, unidad_canon, ean, "
            "precio_cent, precio_unidad_cent, precio_ref_canon_cent, "
            "unidad_ref_canon, imagen, alergenos, ingredientes, origen, "
            "promo_txt, categoria, url, grupo_id, calidad, calidad_origen, "
            "calidad_nota, nutriscore, comparacion_fiable, nova, "
            "sellos, sellos_origen, certificados, conservacion, es_marca_propia, "
            "nutricion, nutricion_por, envase, descripcion, tipo_producto, "
            "dias_caducidad, peso_neto_g, grado_alcohol, promo_hasta")


def _fila(id_, nombre, precio, sellos=None, conservacion=None, propia=None, grupo=1):
    def txt(v):
        return "NULL" if v is None else f"'{v}'"
    return (f"('dia','{id_}','{nombre}','Dia',1.0,'kg','840{id_}',{precio},{precio},"
            f"{precio},'kg',NULL,NULL,NULL,NULL,NULL,'x','http://x',{grupo},NULL,NULL,"
            f"NULL,NULL,true,NULL,{txt(sellos)},'etiqueta',NULL,{txt(conservacion)},"
            f"{'NULL' if propia is None else str(propia).lower()},"
            f"NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL)")


@pytest.fixture
def gold(tmp_path, monkeypatch):
    # Un grupo con dos galletas: unas sin gluten a 3 EUR y unas normales a 1 EUR.
    # Sin la correccion, el filtro "sin gluten" ensena las de 1 EUR.
    filas = ", ".join([
        _fila("1", "Galletas Maria sin gluten", 300, sellos="sin-gluten"),
        _fila("2", "Galletas Maria", 100),
        _fila("3", "Pizza cuatro quesos", 500, conservacion="congelado", grupo=2),
        _fila("4", "Salsa barbacoa", 150, grupo=2),
    ])
    con = duckdb.connect()
    con.execute(f"CREATE TABLE g AS SELECT * FROM (VALUES {filas}) AS t({COLUMNAS})")
    con.execute(f"COPY g TO '{tmp_path / 'grupos.parquet'}' (FORMAT PARQUET)")
    for otro in ("enlaces", "precio_derivado", "resumen"):
        con.execute(f"COPY (SELECT 1 AS x) TO '{tmp_path / otro}.parquet' (FORMAT PARQUET)")
    con.execute(f"""COPY (SELECT 'dia' AS fuente, DATE '2026-09-17' AS fecha,
                                'dia:1' AS producto_id, 100 AS precio_unidad_cent)
                    TO '{tmp_path / 'precio_diario.parquet'}' (FORMAT PARQUET)""")
    con.close()
    from dataclasses import replace

    from plataforma.api import catalogo
    monkeypatch.setattr(catalogo, "AJUSTES", replace(catalogo.AJUSTES, gold=tmp_path))
    catalogo.reiniciar()
    yield
    catalogo.reiniciar()


def test_sin_filtro_manda_el_precio(gold):
    from plataforma.api import catalogo
    r = catalogo.buscar("galletas")
    assert r[0]["nombre"] == "Galletas Maria"      # las de 1 EUR


def test_con_filtro_solo_se_ensena_lo_que_lo_cumple(gold):
    from plataforma.api import catalogo
    r = catalogo.buscar("galletas", sellos=["sin-gluten"])
    assert len(r) == 1
    assert r[0]["nombre"] == "Galletas Maria sin gluten"
    assert r[0]["productos"] == 1                  # la normal no cuenta


def test_lo_mismo_con_la_conservacion(gold):
    from plataforma.api import catalogo
    r = catalogo.buscar("pizza", conservacion="congelado")
    assert [x["nombre"] for x in r] == ["Pizza cuatro quesos"]


def test_un_sello_inventado_se_ignora_y_no_se_interpola(gold):
    # Lo que llega del cliente no toca nunca el SQL: se valida contra la lista.
    from plataforma.api import catalogo
    r = catalogo.buscar("galletas", sellos=["'; DROP TABLE buscable; --"])
    # Un resultado, que es el grupo, con sus dos galletas dentro: igual que sin
    # filtro. Y la tabla sigue viva, que es la otra mitad de la prueba.
    assert [x["productos"] for x in r] == [2]
    assert catalogo.buscar("galletas")


def test_sin_sal_no_casa_dentro_de_otro_sello(gold):
    # Los sellos van en una sola columna separados por comas; un LIKE ingenuo
    # haria que "sin-sal" casara dentro de "sin-salsa" o "sin-sal-anadida".
    from plataforma.api import catalogo
    assert catalogo.buscar("galletas", sellos=["sin-sal"]) == []


# --- una unidad por grupo, y ahorros que se sostienen ---------------------

def _fila_u(id_, nombre, precio_unidad, unidad, fuente, grupo):
    return (f"('{fuente}','{id_}','{nombre}','M',1.0,'{unidad}','84{id_}',100,"
            f"{precio_unidad},{precio_unidad},'{unidad}',NULL,NULL,NULL,NULL,NULL,'x',"
            f"'http://x',{grupo},NULL,NULL,NULL,NULL,true,NULL,NULL,NULL,NULL,NULL,"
            f"NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL)")


@pytest.fixture
def gold_unidades(tmp_path, monkeypatch):
    # Grupo 1: la manzanilla real. Dos cadenas la venden por bolsitas y una por
    # peso de hierba. Restar 76,79 EUR/kg de 0,09 EUR/ud daba 85.000 % de ahorro.
    # Grupo 2: el azafran. Todos en kg, pero uno mil veces fuera.
    filas = ", ".join([
        _fila_u("1", "Manzanilla Hornimans 25 ud", 9, "ud", "dia", 1),
        _fila_u("2", "LA MAJA Manzanilla 25 uds", 4, "ud", "alcampo", 1),
        _fila_u("3", "Manzanilla en bolsitas Hornimans", 6143, "kg", "carrefour", 1),
        _fila_u("4", "POTE Azafran 0,400 gr", 667, "kg", "alcampo", 2),
        _fila_u("5", "Azafran en hebras Pote 0,4 g", 687500, "kg", "dia", 2),
    ])
    con = duckdb.connect()
    con.execute(f"CREATE TABLE g AS SELECT * FROM (VALUES {filas}) AS t({COLUMNAS})")
    con.execute(f"COPY g TO '{tmp_path / 'grupos.parquet'}' (FORMAT PARQUET)")
    for otro in ("enlaces", "precio_derivado", "resumen"):
        con.execute(f"COPY (SELECT 1 AS x) TO '{tmp_path / otro}.parquet' (FORMAT PARQUET)")
    con.execute(f"""COPY (SELECT 'dia' AS fuente, DATE '2026-09-17' AS fecha,
                                'dia:1' AS producto_id, 100 AS precio_unidad_cent)
                    TO '{tmp_path / 'precio_diario.parquet'}' (FORMAT PARQUET)""")
    con.close()
    from dataclasses import replace

    from plataforma.api import catalogo
    monkeypatch.setattr(catalogo, "AJUSTES", replace(catalogo.AJUSTES, gold=tmp_path))
    catalogo.reiniciar()
    yield
    catalogo.reiniciar()


def test_solo_se_compara_dentro_de_una_unidad(gold_unidades):
    # Manda "ud", que la comparten dos cadenas. El de kg sigue en el grupo pero
    # no decide el ahorro: 0,09 contra 0,04 son 125 %, no 85.000 %.
    from plataforma.api import catalogo
    r = catalogo.buscar("manzanilla")[0]
    assert r["unidad"] == "ud"
    assert r["productos"] == 2
    assert r["ahorro_pct"] == 125.0
    assert not r["dudoso"]


def test_un_ahorro_increible_no_se_anuncia(gold_unidades):
    # Misma unidad las dos, pero mil veces de diferencia: uno de los dos datos
    # esta mal y no sabemos cual. Se dice, no se grita.
    from plataforma.api import catalogo
    r = catalogo.buscar("azafran")[0]
    assert r["dudoso"] is True
    assert r["ahorro_pct"] == 0.0
    # Y el grupo sigue apareciendo: esconderlo seria esconder el problema.
    assert r["cadenas"] == 2
