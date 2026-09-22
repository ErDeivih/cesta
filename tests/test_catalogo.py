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
        # `promo_hasta` con zona horaria, que es como lo escribe el pipeline. Se
        # anade aqui y no en las tuplas de arriba para no tocar las pruebas que
        # ya existian, pero tiene que estar: sin una columna TIMESTAMPTZ de
        # verdad, la prueba de pytz no probaria nada.
        con.execute("""
            ALTER TABLE g ADD COLUMN promo_hasta TIMESTAMPTZ;
            UPDATE g SET promo_hasta = TIMESTAMPTZ '2026-09-25 00:00:00+02';
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


def test_la_busqueda_trae_la_marca(gold):
    """La tabla del buscador la pedia y no la tenia.

    La unica forma de sacarla sin este campo era adivinarla a partir del nombre,
    y eso es inventarse un dato. Es la marca del miembro **mas barato** del
    grupo, que es el que la fila ensena.
    """
    from plataforma.api import catalogo
    assert catalogo.buscar("leche")[0]["marca"] == "Dia"


def test_el_historico_dice_de_que_producto_es_cada_punto(gold):
    """Sin esto, dos productos de la misma cadena dan series indistinguibles.

    El grupo de la prueba tiene un solo producto, asi que lo que se comprueba es
    que el campo viaja; el caso que lo justifica de verdad se vio en el catalogo
    real: un grupo con 8 productos de 2 cadenas, 6 de ellos de la misma, donde
    sin `producto_id` no se sabe de cual es cada precio.
    """
    from plataforma.api import catalogo
    serie = catalogo.grupo(1)["serie"]
    assert serie, "el grupo deberia tener historico en el gold de mentira"
    assert serie[0]["producto_id"] == "dia:1"
    assert serie[0]["fecha"] == "2026-09-17"


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


# --- el panel de auditoria del matching ---------------------------------
# Explicabilidad sin validacion humana: cada par con su motivo, y ni un endpoint
# de escritura. El encargo lo dice asi: nadie va a aprobar nada, nunca.


def _pasada(gold, eid, enlaces, metricas):
    from core import equivalencias as equiv
    filas = [
        {"fuente": "dia", "id_fuente": "1", "nombre": "Leche entera",
         "marca": "Dia", "cantidad": 1.0, "unidad_canon": "l", "ean": "84000001",
         "precio_unidad_cent": 100, "seccion": "lacteos"},
        {"fuente": "alcampo", "id_fuente": "9", "nombre": "Leche entera",
         "marca": "ALCAMPO", "cantidad": 1.0, "unidad_canon": "l", "ean": None,
         "precio_unidad_cent": 80, "seccion": "lacteos"},
    ]
    equiv.escribe_ejecucion(eid, equiv.filas_de_equivalencia(filas, enlaces, eid),
                            metricas, {"productos": 2, "umbral": 0.55},
                            gold=gold)


def test_el_panel_sin_ninguna_pasada_no_revienta(gold):
    from plataforma.api import catalogo
    r = catalogo.matching()
    assert r["ultima"] is None
    assert r["pares"] == []
    assert r["ejecuciones"] == []
    assert r["fecha_datos"] == "2026-09-17"


def test_el_panel_ensena_el_motivo_de_cada_par(gold):
    tmp, _escribe, _uno = gold
    from plataforma.api import catalogo
    _pasada(tmp, "20260922-090000", [(0, 1, 0.72, "equivalente")],
            {"enlaces": 1.0, "grupos_comparables": 1.0})
    r = catalogo.matching()
    assert r["ultima"]["ejecucion_id"] == "20260922-090000"
    assert r["ultima"]["umbral"] == 0.55
    assert r["metricas"] == [{"metrica": "enlaces", "valor": 1.0},
                             {"metrica": "grupos_comparables", "valor": 1.0}]
    p = r["pares"][0]
    # Los nombres se piden al catalogo: en la equivalencia solo hay claves
    # estables. El segundo producto no esta en este catalogo de mentira (solo
    # tiene `dia:1`), y eso **no puede tumbar la respuesta**: pasa de verdad
    # cuando una cadena no captura ese dia, y el par se sigue pudiendo auditar
    # aunque falte un lado.
    assert p["nombre_a"] == "Leche entera"
    assert p["nombre_b"] is None
    assert p["producto_b"] == "alcampo:9"
    assert p["metodo"] == "nombre"
    # Y el motivo, que es lo que hace auditable el resultado.
    assert p["features"]["unidad_igual"] is True
    assert p["features"]["seccion_igual"] is True
    assert p["features"]["ean_en_los_dos"] is False


def test_el_panel_compara_con_la_pasada_anterior(gold):
    """La estabilidad entre ejecuciones, que es una metrica del plan."""
    tmp, _escribe, _uno = gold
    from plataforma.api import catalogo
    _pasada(tmp, "20260922-090000", [(0, 1, 0.9, "x")], {"enlaces": 10.0})
    _pasada(tmp, "20260922-140000", [(0, 1, 0.8, "x")], {"enlaces": 12.0})
    r = catalogo.matching()
    assert r["ejecuciones"] == ["20260922-090000", "20260922-140000"]
    assert r["ultima"]["ejecucion_id"] == "20260922-140000"
    assert r["anterior"]["ejecucion_id"] == "20260922-090000"
    assert r["cambios"] == [{"metrica": "enlaces", "antes": 10.0, "ahora": 12.0,
                             "delta": 2.0}]


def test_el_panel_solo_lee(gold):
    """No hay validacion humana: mirar el panel no puede cambiar nada.

    Es la prueba que guarda la ley del encargo. Si algun dia alguien anade aqui
    un boton de aprobar, esto es lo que tiene que saltar.
    """
    tmp, _escribe, _uno = gold
    from plataforma.api import catalogo
    _pasada(tmp, "20260922-090000", [(0, 1, 0.9, "x")], {"enlaces": 1.0})
    antes = sorted(p.name for p in (tmp / "matching").rglob("*"))
    catalogo.matching()
    catalogo.matching(5)
    despues = sorted(p.name for p in (tmp / "matching").rglob("*"))
    assert antes == despues


# --- la ficha del grupo y la zona horaria -------------------------------
# El fallo que esto cierra, encontrado el 22 de septiembre de 2026: la pantalla
# de grupo -- la clave del encargo -- daba 500 en casi todos los grupos
# comparables. `promo_hasta` es un TIMESTAMP WITH TIME ZONE y DuckDB, para
# devolverlo como objeto de fecha, importa `pytz` por debajo. La imagen de la API
# no lo trae, porque la API no maneja zonas horarias. En el entorno de desarrollo
# tampoco estaba, y aun asi ninguna prueba lo vio: el catalogo de mentira no
# tenia ninguna columna con zona horaria.


def test_la_ficha_del_grupo_trae_la_fecha_de_la_promocion(gold):
    from plataforma.api import catalogo
    g = catalogo.grupo(1)
    assert g is not None
    assert g["productos"][0]["promo_hasta"] == "2026-09-25"


def test_la_ficha_del_grupo_no_necesita_pytz(gold, monkeypatch):
    """Se esconde `pytz` para reproducir lo que pasa DENTRO del contenedor.

    Poner `None` en `sys.modules` hace que cualquier `import pytz` falle aunque
    el modulo este instalado, que es exactamente la diferencia entre el entorno de
    desarrollo y la imagen de la API. Sin esto, la prueba pasaria en los dos
    sitios y no protegeria nada.
    """
    import sys

    from plataforma.api import catalogo
    monkeypatch.setitem(sys.modules, "pytz", None)
    g = catalogo.grupo(1)
    assert g is not None
    assert g["productos"][0]["promo_hasta"] == "2026-09-25"
