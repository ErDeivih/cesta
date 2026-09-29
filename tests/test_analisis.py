"""Las medidas del panel, y las dos trampas en las que caí al escribirlas.

Las dos son la misma trampa con dos disfraces: **comparar catálogos en vez de
comparar productos**. Un número que sale de promediar surtidos distintos parece
un precio y no lo es, y como no revienta nada, se queda.
"""
from dataclasses import replace

import duckdb
import pytest

from plataforma.api import analisis, catalogo


@pytest.fixture
def gold(tmp_path, monkeypatch):
    """Un gold de mentira: la serie de precios y la tabla de productos."""
    def escribe(diario, grupos=(), con_seccion=True):
        con = duckdb.connect()
        con.execute("CREATE TABLE d (fuente VARCHAR, id_fuente VARCHAR,"
                    " precio_cent BIGINT, precio_unidad_cent DOUBLE,"
                    " unidad_canon VARCHAR, producto_id VARCHAR, fecha VARCHAR)")
        for f in diario:
            con.execute("INSERT INTO d VALUES (?,?,?,?,?,?,?)",
                        [f["fuente"], f["id"], f["precio"],
                         float(f.get("unidad", f["precio"])), "kg",
                         f"{f['fuente']}:{f['id']}", f["fecha"]])
        con.execute(f"COPY d TO '{tmp_path / 'precio_diario.parquet'}' (FORMAT PARQUET)")

        cols = ("grupo_id BIGINT, fuente VARCHAR, id_fuente VARCHAR, nombre VARCHAR,"
                " marca VARCHAR, cantidad DOUBLE, unidad_canon VARCHAR,"
                " precio_cent BIGINT, precio_unidad_cent DOUBLE,"
                " comparacion_fiable BOOLEAN, calidad VARCHAR, calidad_origen VARCHAR,"
                " nutriscore VARCHAR, nova BIGINT, ean VARCHAR, imagen VARCHAR,"
                " promo_txt VARCHAR")
        if con_seccion:
            cols += ", seccion VARCHAR"
        con.execute(f"CREATE TABLE g ({cols})")
        for i, p in enumerate(grupos):
            v = [p.get("grupo_id"), p["fuente"], str(i), p.get("nombre", f"p{i}"),
                 None, 1.0, p.get("unidad_canon", "kg"), 100,
                 float(p["precio_unidad"]), True,
                 None, None, None, None, None, None, None]
            if con_seccion:
                v.append(p.get("seccion"))
            con.execute(f"INSERT INTO g VALUES ({','.join('?' * len(v))})", v)
        con.execute(f"COPY g TO '{tmp_path / 'grupos.parquet'}' (FORMAT PARQUET)")
        for otro in ("enlaces", "resumen", "precio_derivado"):
            con.execute(
                f"COPY (SELECT 1 AS x) TO '{tmp_path / otro}.parquet' (FORMAT PARQUET)")
        con.close()
        catalogo.reiniciar()

    monkeypatch.setattr(catalogo, "AJUSTES", replace(catalogo.AJUSTES, gold=tmp_path))
    yield escribe
    catalogo.reiniciar()


def _serie(fuente, id_, dias):
    return [{"fuente": fuente, "id": id_, "fecha": f, "precio": p} for f, p in dias]


def _indice_de(r, cadena):
    return next(s for s in r["series"] if s["cadena"] == cadena)


# ------------------------------------------------------------------ el índice --

def test_un_catalogo_mas_caro_no_es_un_precio_mas_alto(gold):
    """La trampa de la composición, que es por la que el índice existe.

    La media del catálogo sube en cuanto la cadena mete productos caros, sin que
    haya subido un solo precio. Con catálogos que rotan un 1 % al día, medir así
    es medir el surtido.
    """
    filas = _serie("dia", "1", [("2026-09-01", 100), ("2026-09-02", 100)])
    # El día 2 aparecen dos jamones de 90 EUR que el día 1 no estaban.
    filas += [{"fuente": "dia", "id": "caro1", "fecha": "2026-09-02", "precio": 9000},
              {"fuente": "dia", "id": "caro2", "fecha": "2026-09-02", "precio": 9000}]
    gold(filas)
    assert _indice_de(analisis.indice(), "dia")["indice"] == 100.0


def test_el_eslabon_es_contra_la_captura_anterior_de_esa_cadena(gold):
    """Carrefour no se dejó capturar el 11, el 12 ni el 18 de septiembre de 2026.

    Comparando contra el día anterior del calendario, esos días no tenían pareja
    y la cadena entera desaparecía del índice. El eslabón salta el hueco y dice
    cuántos días cubre.
    """
    filas = _serie("carrefour", "1", [("2026-09-01", 100), ("2026-09-04", 110)])
    filas += _serie("dia", "9", [("2026-09-01", 100), ("2026-09-02", 100),
                                 ("2026-09-03", 100), ("2026-09-04", 100)])
    gold(filas)
    carr = _indice_de(analisis.indice(), "carrefour")
    assert carr["indice"] == 110.0
    assert carr["puntos"][-1]["dias_del_salto"] == 3


def test_la_media_es_geometrica_y_por_eso_vuelve_a_cien(gold):
    """Subir un 50 % y luego bajar un 33,3 % deja el precio donde estaba.

    Con media aritmética de porcentajes daría +8,3 %: un índice que inventa una
    subida que nadie ha pagado.
    """
    gold(_serie("aldi", "1", [("2026-09-01", 300), ("2026-09-02", 450),
                              ("2026-09-03", 300)]))
    assert _indice_de(analisis.indice(), "aldi")["indice"] == pytest.approx(100.0, abs=0.01)


def test_un_relativo_imposible_se_recorta_y_se_cuenta(gold):
    """Dividir por treinta no es una oferta: es un pack leído como unidad.

    Se recorta, pero se dice cuántos. Un recorte silencioso es una decisión
    escondida dentro de un número.
    """
    filas = _serie("alcampo", "malo", [("2026-09-01", 3000), ("2026-09-02", 100)])
    filas += _serie("alcampo", "bueno", [("2026-09-01", 100), ("2026-09-02", 100)])
    gold(filas)
    punto = _indice_de(analisis.indice(), "alcampo")["puntos"][-1]
    assert punto["recortados"] == 1
    assert punto["productos"] == 1
    assert _indice_de(analisis.indice(), "alcampo")["indice"] == 100.0


def test_el_indice_dice_sobre_cuantos_productos_se_sostiene(gold):
    gold(_serie("dia", "1", [("2026-09-01", 100), ("2026-09-02", 100)])
         + _serie("dia", "2", [("2026-09-01", 200), ("2026-09-02", 200)]))
    assert _indice_de(analisis.indice(), "dia")["puntos"][-1]["productos"] == 2


def test_el_indice_lee_el_historico_una_vez_y_no_tres(gold):
    """La copia del histórico, que es lo que arregló la pestaña «Índice» del panel.

    La consulta nombraba la vista `diario` **tres veces** (los días, la captura de hoy y la
    anterior), y dentro del contenedor de la API eso costaba **34,3 s** con 24 capturas y
    1.135.124 filas; con el histórico copiado una vez a una tabla temporal, **1,7 s** y las
    mismas 107 filas (medido el 29 de septiembre de 2026, 2 hilos y 2,2 GiB). Se veía en la
    pantalla: `/api/indice` contestaba en 42,6 s, la puerta espera 20 s, y la pestaña se
    quedaba en «Cargando el índice…».

    Aquí no se fija un tiempo -- eso depende de la máquina -- sino la forma: que la captura
    anterior salga de una ventana, que no haya subconsulta correlacionada y que la consulta
    use la copia.
    """
    gold(_serie("dia", "1", [("2026-09-01", 100), ("2026-09-02", 110)]))

    sql = analisis._enlaces_sql(None, "diario_d")
    assert "lag(fecha) OVER (PARTITION BY fuente ORDER BY fecha)" in sql
    assert "(SELECT max(" not in sql
    assert sql.count("FROM diario_d") + sql.count("JOIN diario_d") == 3

    assert _indice_de(analisis.indice(), "dia")["indice"] == pytest.approx(110.0)
    con = catalogo.conexion()
    assert analisis._diario_materializado(con) == "diario_d"      # la segunda vez no cuesta
    copias = con.execute("SELECT count(*) FROM information_schema.tables"
                         " WHERE table_name = 'diario_d'").fetchone()[0]
    assert copias == 1


# ------------------------------------------------------------------- el pulso --

def test_el_pulso_separa_lo_que_baja_de_lo_que_sube(gold):
    gold(_serie("dia", "baja", [("2026-09-01", 100), ("2026-09-02", 80)])
         + _serie("dia", "sube", [("2026-09-01", 100), ("2026-09-02", 120)])
         + _serie("dia", "quieto", [("2026-09-01", 100), ("2026-09-02", 100)]))
    c = analisis.pulso()["capturas"][0]
    assert (c["vistos"], c["movidos"], c["bajan"], c["suben"]) == (3, 2, 1, 1)
    assert c["mediana_bajada_pct"] == -20.0


def test_un_centimo_de_redondeo_no_es_un_movimiento(gold):
    """Con el umbral a cero, la mitad del catálogo "se mueve" todos los días por
    céntimos de IVA, y el número deja de significar nada."""
    gold(_serie("dia", "1", [("2026-09-01", 1000), ("2026-09-02", 1001)]))
    assert analisis.pulso()["capturas"][0]["movidos"] == 0


# ---------------------------------------------------------------- la posición --

def test_la_posicion_no_puede_medir_el_surtido(gold):
    """La trampa en la que caí de verdad, y que sólo se vio mirando la salida.

    La primera versión comparaba la mediana de EUR/kg de cada cadena en cada
    sección. Daba `mercadona +2.246 %` en higiene: Mercadona no vende el champú
    veintidós veces más caro, vende maquillaje donde Carrefour vende garrafas.

    Aquí las dos cadenas tienen **el mismo precio** en el único producto que
    comparten, y una además vende un artículo carísimo que la otra no tiene. El
    desvío tiene que ser cero para las dos.
    """
    grupos = [
        {"grupo_id": 1, "fuente": "dia", "precio_unidad": 500, "seccion": "despensa"},
        {"grupo_id": 1, "fuente": "aldi", "precio_unidad": 500, "seccion": "despensa"},
        # Sólo en Dia, sin pareja: no puede mover la posición de nadie.
        {"grupo_id": 2, "fuente": "dia", "precio_unidad": 90000, "seccion": "despensa"},
    ]
    gold([], grupos * 20)
    seccion = analisis.posicion()["secciones"][0]
    assert {c["cadena"]: c["desvio_pct"] for c in seccion["cadenas"]} == {
        "dia": 0.0, "aldi": 0.0}


def test_la_cadena_de_en_medio_no_se_regala_un_cero(gold):
    """Contra la mediana del grupo entero, la del medio da +0,0 % por definición.

    Salían tres cadenas clavadas en cero en casi todas las secciones, que no era
    un empate sino el método midiéndose a sí mismo. Comparando contra las OTRAS,
    la de en medio ya tiene que ganárselo.
    """
    grupos = [
        {"grupo_id": 1, "fuente": "aldi", "precio_unidad": 80, "seccion": "despensa"},
        {"grupo_id": 1, "fuente": "dia", "precio_unidad": 100, "seccion": "despensa"},
        {"grupo_id": 1, "fuente": "carrefour", "precio_unidad": 200, "seccion": "despensa"},
    ]
    gold([], grupos * 20)
    por = {c["cadena"]: c["desvio_pct"] for c in analisis.posicion()["secciones"][0]["cadenas"]}
    # dia esta entre 80 y 200: la mediana de las otras es 140, asi que sale
    # barata (-28,6 %), no empatada.
    assert por["dia"] == pytest.approx(-28.6, abs=0.1)
    assert por["aldi"] < por["dia"] < por["carrefour"]


def test_sin_seccion_en_gold_la_posicion_esta_vacia_y_no_revienta(gold):
    gold([], [{"grupo_id": 1, "fuente": "dia", "precio_unidad": 100}], con_seccion=False)
    assert analisis.posicion()["secciones"] == []


def test_un_grupo_de_una_sola_cadena_no_dice_nada_de_nadie(gold):
    """Sin alguien enfrente no hay posición que medir."""
    gold([], [{"grupo_id": 1, "fuente": "dia", "precio_unidad": 100,
               "seccion": "despensa"}] * 40)
    assert analisis.posicion()["secciones"] == []
