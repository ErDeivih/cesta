"""El catalogo: DuckDB sobre los parquet de gold.

La prueba que de verdad importa aqui es la de la recarga. `buscable` es una
COPIA del catalogo que se hace al abrir la conexion, y el pipeline reescribe
`grupos.parquet` una vez al dia. Sin mirar la fecha del fichero, cada hilo
seguia sirviendo el catalogo de ayer hasta que alguien reiniciase el
contenedor, y la cache del panel tampoco se refrescaba. La app se quedaba
congelada en silencio, que es la peor forma de quedarse congelada.
"""
import os
import time

import duckdb
import pytest


@pytest.fixture
def gold(tmp_path, monkeypatch):
    """Un gold de mentira, con lo justo para que el catalogo arranque."""
    def escribe(productos):
        con = duckdb.connect()
        con.execute(f"""
            CREATE TABLE g AS SELECT * FROM (VALUES {productos}) AS t(
                fuente, id_fuente, nombre, marca, cantidad, unidad_canon, ean,
                precio_cent, precio_unidad_cent, precio_ref_canon_cent,
                unidad_ref_canon, imagen, alergenos, ingredientes, origen,
                promo_txt, categoria, url, grupo_id, calidad, calidad_origen,
                calidad_nota, nutriscore, comparacion_fiable, nova)
        """)
        con.execute(f"COPY g TO '{tmp_path / 'grupos.parquet'}' (FORMAT PARQUET)")
        for otro in ("enlaces", "precio_derivado", "resumen"):
            con.execute(f"COPY (SELECT 1 AS x) TO '{tmp_path / otro}.parquet' (FORMAT PARQUET)")
        con.execute(f"""COPY (SELECT 'dia' AS fuente, DATE '2026-09-17' AS fecha,
                                    'dia:1' AS producto_id, 100 AS precio_unidad_cent)
                        TO '{tmp_path / 'precio_diario.parquet'}' (FORMAT PARQUET)""")
        con.close()

    uno = ("('dia','1','Leche entera','Dia',1.0,'l','84000001',100,100,100,'l',"
           "NULL,NULL,NULL,NULL,NULL,'lacteos','http://x',1,NULL,NULL,NULL,NULL,true,NULL)")
    escribe(uno)

    # `Ajustes` es un dataclass congelado a proposito: se lee del entorno una
    # vez y no cambia en caliente. Para la prueba se sustituye el objeto entero.
    from dataclasses import replace

    from plataforma.api import catalogo
    monkeypatch.setattr(catalogo, "AJUSTES", replace(catalogo.AJUSTES, gold=tmp_path))
    catalogo.reiniciar()
    yield tmp_path, escribe, uno
    catalogo.reiniciar()


def test_encuentra_lo_que_hay(gold):
    from plataforma.api import catalogo
    assert len(catalogo.buscar("leche")) == 1


def test_se_entera_de_que_el_pipeline_ha_reescrito_gold(gold):
    """El fallo que esto cierra: la app servia el catalogo de ayer para siempre."""
    tmp, escribe, uno = gold
    from plataforma.api import catalogo
    assert len(catalogo.buscar("leche")) == 1
    assert len(catalogo.buscar("pan")) == 0

    dos = uno + (",('dia','2','Pan de molde','Dia',0.5,'kg','84000002',150,300,300,"
                 "'kg',NULL,NULL,NULL,NULL,NULL,'panaderia','http://y',2,NULL,NULL,"
                 "NULL,NULL,true,NULL)")
    time.sleep(0.02)
    escribe(dos)
    os.utime(tmp / "grupos.parquet", None)

    # Sin reiniciar nada: la siguiente consulta tiene que ver el pan.
    assert len(catalogo.buscar("pan")) == 1


def test_la_fecha_se_recalcula_al_cambiar_gold(gold):
    from plataforma.api import catalogo
    assert catalogo.fecha_de_gold() == "2026-09-17"
    tmp, _, _ = gold
    os.utime(tmp / "grupos.parquet", None)
    assert catalogo.fecha_de_gold() == "2026-09-17"   # misma fecha, sin reventar


def test_un_gold_que_no_existe_no_tumba_el_proceso(tmp_path, monkeypatch):
    from dataclasses import replace

    from plataforma.api import catalogo
    monkeypatch.setattr(catalogo, "AJUSTES",
                        replace(catalogo.AJUSTES, gold=tmp_path / "no_existe"))
    assert catalogo._sello_de_gold() == 0.0


# --- lo que hace comparable a un grupo ---------------------------------
# 32.486 grupos son de un solo producto: el emparejador pone grupo_id a todo.
# Durante unos dias la interfaz pinto "1 cadenas · 1 productos" con el sello de
# comparable puesto, porque se miraba `grupo_id IS NOT NULL` en vez de contar
# cadenas.

def test_un_producto_solo_en_su_grupo_no_es_comparable(gold):
    from plataforma.api import catalogo
    r = catalogo.buscar("leche")[0]
    assert r["cadenas"] == 1
    assert r["comparable"] is False
    assert r["ahorro_pct"] == 0.0


def test_dos_cadenas_en_el_mismo_grupo_si_son_comparables(gold):
    tmp, escribe, uno = gold
    from plataforma.api import catalogo
    dos = uno + (",('alcampo','9','Leche entera','ALCAMPO',1.0,'l',NULL,80,80,80,"
                 "'l',NULL,NULL,NULL,NULL,NULL,'lacteos','http://z',1,NULL,NULL,"
                 "NULL,NULL,true,NULL)")
    time.sleep(0.02)
    escribe(dos)
    os.utime(tmp / "grupos.parquet", None)
    r = catalogo.buscar("leche")[0]
    assert r["cadenas"] == 2
    assert r["comparable"] is True
    assert r["ahorro_pct"] == 25.0        # de 0,80 a 1,00 es un 25 % mas


# --- el escaner de codigo de barras (docs/API.md, tarea 8) --------------
# La funcion que mas se usa en el pasillo: lo que tengo en la mano, ¿esta mas
# barato en otro sitio?


@pytest.mark.parametrize("leido,esperado", [
    ("84000001", "84000001"),
    (" 84000001 ", "84000001"),          # el lector deja espacios
    ("840-000-01", "84000001"),          # o guiones
    ("084000001", "84000001"),           # UPC-12 y EAN-13 son el mismo numero
    ("00000084000001", "84000001"),
])
def test_el_codigo_se_acepta_como_lo_lea_el_lector(leido, esperado):
    from plataforma.api import catalogo
    assert catalogo.normaliza_ean(leido) == esperado


@pytest.mark.parametrize("malo", ["", None, "123", "abcdefgh", "1" * 15,
                                  "00000000"])
def test_un_codigo_que_no_es_un_codigo(malo):
    """Un codigo mal formado es un 400; uno bueno que no conocemos, no."""
    from plataforma.api import catalogo
    assert catalogo.normaliza_ean(malo) is None


def test_el_escaner_encuentra_el_producto(gold):
    from plataforma.api import catalogo
    r = catalogo.por_ean("84000001")
    assert r["encontrado"] is True
    assert r["producto"]["producto_id"] == "dia:1"
    assert r["grupo_id"] == 1
    assert r["fecha_datos"] == "2026-09-17"


def test_solo_en_una_cadena_la_comparacion_es_null_no_vacia(gold):
    """`null` se lee "no puedo comparar"; `[]` se lee "no hay nada mas barato".

    No es lo mismo, y el contrato de `docs/API.md` lo pide asi a proposito.
    """
    from plataforma.api import catalogo
    assert catalogo.por_ean("84000001")["comparacion"] is None


def test_con_dos_cadenas_la_comparacion_lleva_la_diferencia(gold):
    tmp, escribe, uno = gold
    from plataforma.api import catalogo
    dos = uno + (",('alcampo','9','Leche entera','ALCAMPO',1.0,'l','84000002',80,"
                 "80,80,'l',NULL,NULL,NULL,NULL,NULL,'lacteos','http://z',1,NULL,"
                 "NULL,NULL,NULL,true,NULL)")
    time.sleep(0.02)
    escribe(dos)
    os.utime(tmp / "grupos.parquet", None)
    r = catalogo.por_ean("84000001")
    assert [c["fuente"] for c in r["comparacion"]] == ["alcampo", "dia"]
    # De 0,80 a 1,00 hay un 25 % mas caro.
    assert r["comparacion"][0]["diferencia_pct"] == 0.0
    assert r["comparacion"][1]["diferencia_pct"] == 25.0


def test_un_codigo_que_no_tenemos_lo_dice_con_una_pista(gold):
    """Sin excusas: no lo tengo, y por que puede ser."""
    from plataforma.api import catalogo
    r = catalogo.por_ean("99999999")
    assert r["encontrado"] is False
    assert r["motivo"] == "desconocido"
    assert "Alcampo" in r["sugerencia"] and "Aldi" in r["sugerencia"]
