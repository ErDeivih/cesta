"""Las alertas: la función que tienen todos los de la competencia y nosotros no.

La tabla `alerta` estaba en `sql/001_esquema.sql` **desde el primer día**, con
sus tres tipos escritos en un CHECK, y no la usaba nadie: ni un endpoint, ni una
consulta, ni un botón. Un diseño terminado y muerto, como estaba
`core/secciones.py`.

Lo que estas pruebas vigilan no es que salte: es que **no salte cuando no
debe**. Un aviso llega solo y sin contexto, así que un falso positivo aquí es
peor que en una pantalla, donde por lo menos se ve al lado de lo demás.
"""
from dataclasses import replace

import duckdb
import pytest

from plataforma.api import alertas, catalogo


@pytest.fixture
def gold(tmp_path, monkeypatch):
    """Un gold de mentira con productos, serie de precios y derivados."""
    def escribe(productos, diario=(), derivado=()):
        con = duckdb.connect()
        con.execute("CREATE TABLE g (grupo_id BIGINT, fuente VARCHAR,"
                    " id_fuente VARCHAR, nombre VARCHAR, marca VARCHAR,"
                    " cantidad DOUBLE, unidad_canon VARCHAR, precio_cent BIGINT,"
                    " precio_unidad_cent DOUBLE, comparacion_fiable BOOLEAN,"
                    " calidad VARCHAR, calidad_origen VARCHAR, nutriscore VARCHAR,"
                    " nova BIGINT, ean VARCHAR, imagen VARCHAR, promo_txt VARCHAR,"
                    " promo_club BOOLEAN, promo_solo_online BOOLEAN)")
        for p in productos:
            con.execute("INSERT INTO g VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", [
                p["grupo_id"], p["fuente"], p["id"], p.get("nombre", "Algo"), None,
                1.0, p.get("unidad", "l"), p.get("venta", 100),
                float(p["ud"]), p.get("fiable", True),
                None, None, None, None, None, None, p.get("promo_txt"),
                p.get("club", False), p.get("online", False)])
        con.execute(f"COPY g TO '{tmp_path / 'grupos.parquet'}' (FORMAT PARQUET)")

        con.execute("CREATE TABLE d (fuente VARCHAR, id_fuente VARCHAR,"
                    " precio_cent BIGINT, precio_unidad_cent DOUBLE,"
                    " unidad_canon VARCHAR, producto_id VARCHAR, fecha VARCHAR)")
        for f in diario:
            con.execute("INSERT INTO d VALUES (?,?,?,?,?,?,?)", [
                f["fuente"], f["id"], f["venta"], float(f["ud"]),
                f.get("unidad", "l"), f"{f['fuente']}:{f['id']}", f["fecha"]])
        con.execute(f"COPY d TO '{tmp_path / 'precio_diario.parquet'}' (FORMAT PARQUET)")

        con.execute("CREATE TABLE x (fuente VARCHAR, id_fuente VARCHAR,"
                    " fecha VARCHAR, precio_unidad_cent DOUBLE,"
                    " precio_base_cent DOUBLE, posicion_90d DOUBLE,"
                    " min_90d_cent DOUBLE, max_90d_cent DOUBLE)")
        for f in derivado:
            con.execute("INSERT INTO x VALUES (?,?,?,?,?,?,?,?)", [
                f["fuente"], f["id"], f.get("fecha", "2026-09-21"),
                float(f.get("ud", 0)), float(f.get("base", 0)),
                f.get("pos", 0.5), float(f["min90"]), float(f.get("max90", 999))])
        con.execute(f"COPY x TO '{tmp_path / 'precio_derivado.parquet'}' (FORMAT PARQUET)")

        for otro in ("enlaces", "resumen"):
            con.execute(
                f"COPY (SELECT 1 AS x) TO '{tmp_path / otro}.parquet' (FORMAT PARQUET)")
        con.close()
        catalogo.reiniciar()

    monkeypatch.setattr(catalogo, "AJUSTES", replace(catalogo.AJUSTES, gold=tmp_path))
    yield escribe
    catalogo.reiniciar()


def _alerta(tipo, grupo_id=1, umbral=None):
    return {"id": "a1", "grupo_id": grupo_id, "tipo": tipo, "umbral_cent": umbral}


# ------------------------------------------------------------- "baja de X" --

def test_salta_cuando_baja_del_umbral(gold):
    gold([{"grupo_id": 1, "fuente": "dia", "id": "1", "ud": 110, "venta": 110}])
    saltan = alertas.evalua([_alerta("baja_de", umbral=120)])
    assert len(saltan) == 1
    assert "1,10" in saltan[0]["por_que"].replace(".", ",")


def test_no_salta_si_todavia_esta_por_encima(gold):
    gold([{"grupo_id": 1, "fuente": "dia", "id": "1", "ud": 130, "venta": 130}])
    assert alertas.evalua([_alerta("baja_de", umbral=120)]) == []


def test_una_alerta_de_umbral_sin_umbral_no_salta_nunca(gold):
    """Mejor callar que inventarse el número que quería la persona."""
    gold([{"grupo_id": 1, "fuente": "dia", "id": "1", "ud": 50, "venta": 50}])
    assert alertas.evalua([_alerta("baja_de")]) == []


# ------------------------------------------------------- el mínimo de 90 días --

def test_salta_al_tocar_el_minimo_de_noventa_dias(gold):
    """La buena, y la que casi nadie tiene: no hay que saber de antemano
    cuánto debería costar algo."""
    gold([{"grupo_id": 1, "fuente": "dia", "id": "1", "ud": 100, "venta": 100}],
         derivado=[{"fuente": "dia", "id": "1", "min90": 100}])
    saltan = alertas.evalua([_alerta("minimo_90d")])
    assert len(saltan) == 1
    assert "90 dias" in saltan[0]["por_que"]


def test_no_salta_si_ya_estuvo_mas_barato(gold):
    gold([{"grupo_id": 1, "fuente": "dia", "id": "1", "ud": 150, "venta": 150}],
         derivado=[{"fuente": "dia", "id": "1", "min90": 100}])
    assert alertas.evalua([_alerta("minimo_90d")]) == []


def test_sin_historico_no_se_inventa_un_minimo(gold):
    """Decir «el más barato en 90 días» con cinco días de serie es mentir."""
    gold([{"grupo_id": 1, "fuente": "dia", "id": "1", "ud": 100, "venta": 100}])
    assert alertas.evalua([_alerta("minimo_90d")]) == []


# -------------------------------------------------------- "cualquier bajada" --

def _serie(fuente, id_, dias, unidad="l"):
    return [{"fuente": fuente, "id": id_, "fecha": f, "venta": v, "ud": u,
             "unidad": unidad} for f, v, u in dias]


def test_salta_con_una_bajada_de_verdad(gold):
    gold([{"grupo_id": 1, "fuente": "dia", "id": "1", "ud": 80, "venta": 80}],
         diario=_serie("dia", "1", [("2026-09-20", 100, 100),
                                    ("2026-09-21", 80, 80)]))
    saltan = alertas.evalua([_alerta("cualquier_bajada")])
    assert len(saltan) == 1
    assert "20,0 %" in saltan[0]["por_que"].replace(".", ",")


def test_un_cambio_de_formato_no_dispara_una_alerta(gold):
    """El 18 de septiembre de 2026 la primera pantalla de bajadas encabezaba con
    ocho productos de Alcampo al -96,7 %: envases de 30 unidades leídos como uno.

    Una alerta que salta por eso es peor que una pantalla que lo enseña, porque
    llega sola y sin nada al lado con lo que contrastarla. Aquí el precio de
    venta **no se ha movido** y el de unidad se ha dividido por 30.
    """
    gold([{"grupo_id": 1, "fuente": "dia", "id": "1", "ud": 10, "venta": 300}],
         diario=_serie("dia", "1", [("2026-09-20", 300, 300),
                                    ("2026-09-21", 300, 10)]))
    assert alertas.evalua([_alerta("cualquier_bajada")]) == []


def test_cambiar_de_unidad_no_es_bajar_de_precio(gold):
    gold([{"grupo_id": 1, "fuente": "dia", "id": "1", "ud": 50, "venta": 100}],
         diario=[{"fuente": "dia", "id": "1", "fecha": "2026-09-20",
                  "venta": 100, "ud": 100, "unidad": "ud"},
                 {"fuente": "dia", "id": "1", "fecha": "2026-09-21",
                  "venta": 100, "ud": 50, "unidad": "kg"}])
    assert alertas.evalua([_alerta("cualquier_bajada")]) == []


# ------------------------------------------------- lo que no cuenta como barato --

def test_una_oferta_de_tarjeta_no_hace_saltar_una_alerta(gold):
    """No baja lo que se paga en la caja de la tienda, así que no baja."""
    gold([
        {"grupo_id": 1, "fuente": "dia", "id": "barato", "ud": 90, "venta": 90,
         "club": True},
        {"grupo_id": 1, "fuente": "aldi", "id": "normal", "ud": 130, "venta": 130},
    ])
    assert alertas.evalua([_alerta("baja_de", umbral=100)]) == []


def test_una_oferta_de_solo_internet_tampoco(gold):
    gold([
        {"grupo_id": 1, "fuente": "dia", "id": "barato", "ud": 90, "venta": 90,
         "online": True},
        {"grupo_id": 1, "fuente": "aldi", "id": "normal", "ud": 130, "venta": 130},
    ])
    assert alertas.evalua([_alerta("baja_de", umbral=100)]) == []


def test_se_avisa_del_mas_barato_de_todas_las_cadenas(gold):
    gold([
        {"grupo_id": 1, "fuente": "carrefour", "id": "caro", "ud": 200, "venta": 200},
        {"grupo_id": 1, "fuente": "aldi", "id": "barato", "ud": 90, "venta": 90},
    ])
    saltan = alertas.evalua([_alerta("baja_de", umbral=100)])
    assert saltan[0]["cadena"] == "aldi"


def test_un_grupo_que_ya_no_existe_no_revienta(gold):
    """Un producto retirado deja su alerta huérfana. Se calla, no se cae."""
    gold([{"grupo_id": 1, "fuente": "dia", "id": "1", "ud": 100, "venta": 100}])
    assert alertas.evalua([_alerta("baja_de", grupo_id=999, umbral=500)]) == []


def test_sin_alertas_no_se_consulta_nada(gold):
    gold([])
    assert alertas.evalua([]) == []


# ------------------------------------------------------------- la migración --

def test_una_alerta_por_persona_grupo_y_tipo():
    """Pulsar dos veces la campana no puede dejar dos avisos iguales: el día que
    salten llegarían por duplicado."""
    from pathlib import Path
    sql = (Path(__file__).resolve().parents[1] / "plataforma" / "sql"
           / "004_alertas.sql").read_text(encoding="utf-8")
    assert "alerta_unica" in sql
    assert "ON alerta(usuario_id, grupo_id, tipo)" in sql
