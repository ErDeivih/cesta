"""Las dos pantallas que se le copian a la competencia, y por que son mejores.

"Bajadas de esta semana" es de Precios del Super; el "verificador de ofertas",
de PrecioReal. Las dos las teniamos calculadas desde hacia semanas en
`gold/precio_derivado.parquet` y no se ensenaban en ningun sitio.

Lo que aportamos nosotros es lo que estas pruebas vigilan: que una bajada sea
una bajada de verdad y no un cambio de formato. La primera version de esta
pantalla, probada contra los datos reales del 18 de septiembre de 2026,
encabezaba con ocho productos de Alcampo todos exactamente al -96,7 %:

    NATURTIERRA Berberina    594,00 -> 19,80 EUR/ud
    AQUILEA Descanso       1.020,00 -> 34,00 EUR/ud

Dividir por treinta no es una oferta: son envases de 30 unidades que un dia se
leyeron como una unidad y al siguiente como treinta.
"""
from dataclasses import replace

import duckdb
import pytest

from plataforma.api import catalogo, movimientos


@pytest.fixture
def gold(tmp_path, monkeypatch):
    """Un gold de mentira con una serie de precios que se puede dibujar a mano."""
    def escribe(diario, grupos, derivado=None):
        con = duckdb.connect()
        con.execute("CREATE TABLE d (fuente VARCHAR, id_fuente VARCHAR, "
                    "precio_cent BIGINT, precio_unidad_cent DOUBLE, "
                    "unidad_canon VARCHAR, producto_id VARCHAR, fecha VARCHAR)")
        for f in diario:
            con.execute("INSERT INTO d VALUES (?,?,?,?,?,?,?)",
                        [f["fuente"], f["id"], f["venta"], f["unidad"], f["canon"],
                         f"{f['fuente']}:{f['id']}", f["fecha"]])
        con.execute(f"COPY d TO '{tmp_path / 'precio_diario.parquet'}' (FORMAT PARQUET)")

        con.execute("CREATE TABLE g (grupo_id BIGINT, fuente VARCHAR, id_fuente VARCHAR,"
                    " nombre VARCHAR, marca VARCHAR, cantidad DOUBLE,"
                    " unidad_canon VARCHAR, precio_cent BIGINT,"
                    " precio_unidad_cent DOUBLE, comparacion_fiable BOOLEAN,"
                    " calidad VARCHAR, calidad_origen VARCHAR, nutriscore VARCHAR,"
                    " nova BIGINT, ean VARCHAR, imagen VARCHAR, promo_txt VARCHAR,"
                    " promo_club BOOLEAN)")
        for f in grupos:
            con.execute("INSERT INTO g VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        [f.get("grupo_id", 1), f["fuente"], f["id"], f["nombre"],
                         None, 1.0, f.get("canon", "kg"), 100, 100.0, True,
                         None, None, None, None, None, None,
                         f.get("promo_txt"), f.get("promo_club")])
        con.execute(f"COPY g TO '{tmp_path / 'grupos.parquet'}' (FORMAT PARQUET)")

        con.execute("CREATE TABLE x (fuente VARCHAR, id_fuente VARCHAR, fecha VARCHAR,"
                    " precio_cent BIGINT, precio_unidad_cent DOUBLE,"
                    " precio_base_cent DOUBLE,"
                    " posicion_90d DOUBLE, min_90d_cent DOUBLE, max_90d_cent DOUBLE)")
        for f in (derivado or []):
            con.execute("INSERT INTO x VALUES (?,?,?,?,?,?,?,?,?)",
                        [f["fuente"], f["id"], f["fecha"], f.get("venta", 100),
                         f["unidad"], f["base"],
                         f.get("pos", 0.5), f.get("min", 0.0), f.get("max", 0.0)])
        con.execute(f"COPY x TO '{tmp_path / 'precio_derivado.parquet'}' (FORMAT PARQUET)")

        for otro in ("enlaces", "resumen"):
            con.execute(f"COPY (SELECT 1 AS x) TO '{tmp_path / otro}.parquet' (FORMAT PARQUET)")
        con.close()
        catalogo.reiniciar()

    monkeypatch.setattr(catalogo, "AJUSTES", replace(catalogo.AJUSTES, gold=tmp_path))
    yield escribe
    catalogo.reiniciar()


def _serie(fuente, id_, dias):
    """dias = [(fecha, venta_cent, unidad_cent)]"""
    return [{"fuente": fuente, "id": id_, "venta": v, "unidad": u,
             "canon": "kg", "fecha": f} for f, v, u in dias]


def test_una_bajada_de_verdad_sale(gold):
    gold(_serie("aldi", "1", [("2026-09-11", 400, 400.0), ("2026-09-18", 300, 300.0)]),
         [{"fuente": "aldi", "id": "1", "nombre": "Leche entera"}])
    r = movimientos.bajadas(dias=7)
    assert len(r) == 1
    assert r[0]["variacion_pct"] == -25.0
    assert r[0]["precio_unidad_antes_cent"] == 400.0


def test_un_cambio_de_formato_no_es_una_bajada(gold):
    # El caso real: mismo precio de venta, el precio por unidad dividido por 30
    # porque el envase de 30 unidades un dia se leyo como una.
    gold(_serie("alcampo", "2", [("2026-09-11", 594, 594.0), ("2026-09-18", 594, 19.8)]),
         [{"fuente": "alcampo", "id": "2", "nombre": "NATURTIERRA Berberina"}])
    assert movimientos.bajadas(dias=7) == []


def test_si_el_precio_de_venta_no_se_mueve_no_hay_bajada(gold):
    gold(_serie("alcampo", "3", [("2026-09-11", 200, 400.0), ("2026-09-18", 200, 300.0)]),
         [{"fuente": "alcampo", "id": "3", "nombre": "Algo raro"}])
    assert movimientos.bajadas(dias=7) == []


def test_un_cambio_de_unidad_no_se_compara(gold):
    filas = [{"fuente": "dia", "id": "4", "venta": 400, "unidad": 400.0,
              "canon": "ud", "fecha": "2026-09-11"},
             {"fuente": "dia", "id": "4", "venta": 300, "unidad": 300.0,
              "canon": "kg", "fecha": "2026-09-18"}]
    gold(filas, [{"fuente": "dia", "id": "4", "nombre": "Queso al peso"}])
    assert movimientos.bajadas(dias=7) == []


def test_una_subida_solo_sale_si_se_pide(gold):
    gold(_serie("aldi", "5", [("2026-09-11", 174, 174.0), ("2026-09-18", 349, 349.0)]),
         [{"fuente": "aldi", "id": "5", "nombre": "Galletas con formas"}])
    assert movimientos.bajadas(dias=7) == []
    subidas = movimientos.bajadas(dias=7, subidas=True)
    assert len(subidas) == 1 and subidas[0]["variacion_pct"] > 100


def test_el_ruido_de_redondeo_no_es_una_bajada(gold):
    gold(_serie("aldi", "6", [("2026-09-11", 100, 100.0), ("2026-09-18", 99, 99.0)]),
         [{"fuente": "aldi", "id": "6", "nombre": "Algo de un centimo menos"}])
    assert movimientos.bajadas(dias=7) == []


def test_la_bajada_de_tarjeta_sale_marcada(gold):
    gold(_serie("dia", "7", [("2026-09-11", 400, 400.0), ("2026-09-18", 300, 300.0)]),
         [{"fuente": "dia", "id": "7", "nombre": "Jamon", "promo_txt": "2ª ud 50%",
           "promo_club": True}])
    r = movimientos.bajadas(dias=7)
    assert len(r) == 1 and r[0]["solo_con_tarjeta"] is True


# --- el verificador de ofertas ---------------------------------------------

def test_una_oferta_que_no_baja_el_precio_se_denuncia(gold):
    gold(_serie("carrefour", "8", [("2026-09-18", 500, 500.0)]),
         [{"fuente": "carrefour", "id": "8", "nombre": "Mayonesa", "promo_txt": "5€ dto."}],
         derivado=[{"fuente": "carrefour", "id": "8", "fecha": "2026-09-18",
                    "unidad": 500.0, "base": 480.0, "pos": 1.0}])
    r = movimientos.ofertas_dudosas()
    assert len(r) == 1
    assert "cuesta mas que su precio de siempre" in r[0]["por_que"]


def test_una_oferta_que_si_baja_el_precio_no_se_denuncia(gold):
    gold(_serie("carrefour", "9", [("2026-09-18", 300, 300.0)]),
         [{"fuente": "carrefour", "id": "9", "nombre": "Aceite", "promo_txt": "-20%"}],
         derivado=[{"fuente": "carrefour", "id": "9", "fecha": "2026-09-18",
                    "unidad": 300.0, "base": 400.0, "pos": 0.1}])
    assert movimientos.ofertas_dudosas() == []


def test_sin_texto_de_oferta_no_hay_nada_que_verificar(gold):
    gold(_serie("aldi", "10", [("2026-09-18", 300, 300.0)]),
         [{"fuente": "aldi", "id": "10", "nombre": "Sin promo"}],
         derivado=[{"fuente": "aldi", "id": "10", "fecha": "2026-09-18",
                    "unidad": 300.0, "base": 200.0, "pos": 1.0}])
    assert movimientos.ofertas_dudosas() == []


def test_no_se_acusa_a_una_cadena_cuando_la_cantidad_cambio(gold):
    """El caso que encontro el navegador el 24 de septiembre de 2026.

    La pantalla encabezaba con "Ampollas en stick anti-friccion Compeed 8 ml" a
    1.306,25 EUR/l frente a "su precio de siempre" 10,45 EUR/l. No era un disparate
    de la cadena: un dia el envase se leyo como **una unidad** (1.045 centimos, que
    es el precio del envase leido como si fuera por litro) y otro como sus **8 ml**
    (349 centimos / 0,008 l = 130.625 centimos/l). La cantidad deducida se va de 1 a
    0,008 y los dos numeros no son del mismo producto.

    Hoy la oferta **no se acusa**, y se cuenta aparte para poder decirlo: es un "no
    lo se", no un "no hay ninguna".
    """
    dias = [("2026-09-10", 1045, 1045.0), ("2026-09-12", 1045, 1045.0),
            ("2026-09-14", 1045, 1045.0), ("2026-09-20", 349, 43625.0),
            ("2026-09-24", 349, 43625.0)]
    gold(_serie("carrefour", "11", dias),
         [{"fuente": "carrefour", "id": "11", "nombre": "Ampollas anti-friccion 8 ml",
           "canon": "l", "promo_txt": "-15%"}],
         derivado=[{"fuente": "carrefour", "id": "11", "fecha": f, "venta": v,
                    "unidad": u, "base": 1045.0 if f < "2026-09-20" else 349.0,
                    "pos": 1.0}
                   for f, v, u in dias])
    assert movimientos.ofertas_dudosas() == []
    assert movimientos.ofertas_sin_poder_juzgar() == {
        "por_varias_unidades": 0, "sin_descuento_de_precio": 0,
        "cantidad_cambiada": 1, "total": 1}


def test_una_oferta_con_la_cantidad_estable_si_se_acusa(gold):
    """La otra mitad: con la presentacion quieta, la oferta que no baja se denuncia."""
    dias = [("2026-09-10", 500, 500.0), ("2026-09-14", 500, 500.0),
            ("2026-09-18", 500, 500.0), ("2026-09-24", 500, 500.0)]
    gold(_serie("dia", "12", dias),
         [{"fuente": "dia", "id": "12", "nombre": "Mayonesa 500 g", "canon": "kg",
           "promo_txt": "5 EUR dto."}],
         derivado=[{"fuente": "dia", "id": "12", "fecha": f, "venta": v, "unidad": u,
                    "base": 480.0, "pos": 1.0}
                   for f, v, u in dias])
    r = movimientos.ofertas_dudosas()
    assert len(r) == 1 and r[0]["unidad"] == "kg"
    assert movimientos.ofertas_sin_poder_juzgar()["total"] == 0


def test_un_3x2_no_se_acusa_de_mentir(gold):
    """**El 63 % de la lista era esto, y era un error de la pantalla.**

    Un 3x2 no baja el precio de una unidad: baja el de la tercera. Decir "anuncia
    oferta y hoy cuesta mas que su precio de siempre" es verdad y no significa nada,
    porque el descuento no esta en el precio de una unidad. Medido el 24 de
    septiembre de 2026: 2.195 ofertas "3x2" y 848 "2ª unidad -50 %" entre las 5.488
    acusadas. Se cuentan aparte, con su motivo, y la pantalla lo dice.
    """
    dias = [("2026-09-10", 500, 500.0), ("2026-09-18", 500, 500.0),
            ("2026-09-24", 500, 500.0)]
    gold(_serie("carrefour", "13", dias),
         [{"fuente": "carrefour", "id": "13", "nombre": "Galletas 1 kg", "canon": "kg",
           "promo_txt": "3x2"}],
         derivado=[{"fuente": "carrefour", "id": "13", "fecha": f, "venta": v,
                    "unidad": u, "base": 480.0, "pos": 1.0}
                   for f, v, u in dias])
    assert movimientos.ofertas_dudosas() == []
    assert movimientos.ofertas_sin_poder_juzgar()["por_varias_unidades"] == 1


def test_un_stock_fuera_no_es_una_oferta(gold):
    """Y el segundo motivo: hay etiquetas de marketing en el campo de las ofertas."""
    dias = [("2026-09-10", 500, 500.0), ("2026-09-18", 500, 500.0),
            ("2026-09-24", 500, 500.0)]
    gold(_serie("aldi", "14", dias),
         [{"fuente": "aldi", "id": "14", "nombre": "Cafe 1 kg", "canon": "kg",
           "promo_txt": "Stock Fuera (Unidades Limitadas)"}],
         derivado=[{"fuente": "aldi", "id": "14", "fecha": f, "venta": v, "unidad": u,
                    "base": 480.0, "pos": 1.0}
                   for f, v, u in dias])
    assert movimientos.ofertas_dudosas() == []
    assert movimientos.ofertas_sin_poder_juzgar()["sin_descuento_de_precio"] == 1
