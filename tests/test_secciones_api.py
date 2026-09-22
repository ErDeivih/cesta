"""Los pasillos: la pantalla que no se podía hacer porque el dato no cruzaba.

`core/secciones.py` llevaba desde el 17 de septiembre de 2026 con sus 849 claves
mapeadas y **sin que lo llamara nadie**. La sección no se escribía en ningún
sitio, así que no llegaba a gold, así que no existía: la regla 2 de la lista.

Estas pruebas cubren las dos mitades de la frontera. La de arriba
(`pipeline._anota_seccion`) la escribe; la de abajo (`catalogo.secciones`) la
sirve. Y la de en medio: qué pasa cuando la plataforma es más nueva que el
último gold, que es el estado normal durante las horas que van entre desplegar
un cambio y la siguiente ejecución del scraper.
"""
from dataclasses import replace

import duckdb
import polars as pl
import pytest

from plataforma.api import catalogo
from projects.cesta import pipeline

# ------------------------------------------------------------- la escritura --

def test_la_seccion_se_escribe_a_partir_de_la_categoria_de_cada_cadena():
    df = pl.DataFrame({
        "fuente": ["alcampo", "dia", "mercadona"],
        "categoria": ["Bebidas > Cervezas",
                      "https://www.dia.es/zumos-y-smoothies/naranja/c/L1",
                      "Zumos"],
    })
    out = pipeline._anota_seccion(df)
    assert out["seccion"].to_list() == ["bebidas", "bebidas", "bebidas"]


def test_una_categoria_desconocida_no_se_inventa_seccion():
    """Un producto en el pasillo equivocado es peor que uno al final."""
    df = pl.DataFrame({"fuente": ["alcampo"], "categoria": ["Rama > Que No Existe"]})
    assert pipeline._anota_seccion(df)["seccion"].to_list() == [None]


def test_sin_columna_de_categoria_la_seccion_queda_vacia_pero_existe():
    """La columna tiene que estar siempre: gold la espera en el contrato."""
    df = pl.DataFrame({"fuente": ["alcampo"]})
    out = pipeline._anota_seccion(df)
    assert "seccion" in out.columns
    assert out["seccion"].to_list() == [None]


# --------------------------------------------------------------- la lectura --

@pytest.fixture
def gold(tmp_path, monkeypatch):
    """Un gold de mentira. `con_seccion=False` imita un gold anterior al cambio."""
    def escribe(productos, con_seccion=True):
        con = duckdb.connect()
        cols = ("grupo_id BIGINT, fuente VARCHAR, id_fuente VARCHAR, nombre VARCHAR,"
                " marca VARCHAR, cantidad DOUBLE, unidad_canon VARCHAR,"
                " precio_cent BIGINT, precio_unidad_cent DOUBLE,"
                " comparacion_fiable BOOLEAN, calidad VARCHAR,"
                " calidad_origen VARCHAR, nutriscore VARCHAR, nova BIGINT,"
                " ean VARCHAR, imagen VARCHAR, promo_txt VARCHAR")
        if con_seccion:
            cols += ", seccion VARCHAR"
        con.execute(f"CREATE TABLE g ({cols})")
        for i, p in enumerate(productos):
            valores = [p.get("grupo_id", i + 1), p["fuente"], str(i), p["nombre"],
                       None, 1.0, "kg", 100, 100.0, True,
                       None, None, None, None, None, None, None]
            if con_seccion:
                valores.append(p.get("seccion"))
            marcas = ",".join("?" * len(valores))
            con.execute(f"INSERT INTO g VALUES ({marcas})", valores)
        con.execute(f"COPY g TO '{tmp_path / 'grupos.parquet'}' (FORMAT PARQUET)")
        for otro in ("enlaces", "resumen", "precio_diario", "precio_derivado"):
            con.execute(
                f"COPY (SELECT 1 AS x) TO '{tmp_path / otro}.parquet' (FORMAT PARQUET)")
        con.close()
        catalogo.reiniciar()

    monkeypatch.setattr(catalogo, "AJUSTES", replace(catalogo.AJUSTES, gold=tmp_path))
    yield escribe
    catalogo.reiniciar()


def test_los_pasillos_salen_en_el_orden_del_recorrido_no_en_alfabetico(gold):
    """Un supermercado se recorre, no se lee. La fruta primero y la lejía al final."""
    gold([
        {"fuente": "dia", "nombre": "Lejía", "seccion": "droguería-limpieza"},
        {"fuente": "dia", "nombre": "Manzana", "seccion": "frutas-verduras"},
        {"fuente": "dia", "nombre": "Leche", "seccion": "lacteos-huevos"},
    ])
    assert [s["seccion"] for s in catalogo.secciones()] == [
        "frutas-verduras", "lacteos-huevos", "droguería-limpieza"]


def test_cada_pasillo_dice_cuantos_productos_y_cuantas_cadenas(gold):
    gold([
        {"fuente": "dia", "nombre": "Leche entera", "seccion": "lacteos-huevos"},
        {"fuente": "aldi", "nombre": "Leche desnatada", "seccion": "lacteos-huevos"},
        {"fuente": "dia", "nombre": "Manzana", "seccion": "frutas-verduras"},
    ])
    por_nombre = {s["seccion"]: s for s in catalogo.secciones()}
    assert por_nombre["lacteos-huevos"]["productos"] == 2
    assert por_nombre["lacteos-huevos"]["cadenas"] == 2
    assert por_nombre["lacteos-huevos"]["comparable"] is True


def test_un_pasillo_de_una_sola_cadena_se_marca_como_no_comparable(gold):
    """Se puede mirar, pero ahí no hay nada que comparar. Decirlo evita la
    decepción de entrar y encontrarse una sola columna de precios."""
    gold([{"fuente": "dia", "nombre": "Manzana", "seccion": "frutas-verduras"}])
    assert catalogo.secciones()[0]["comparable"] is False


def test_los_pasillos_respetan_las_cadenas_que_se_miran(gold):
    gold([
        {"fuente": "dia", "nombre": "Manzana", "seccion": "frutas-verduras"},
        {"fuente": "aldi", "nombre": "Lejía", "seccion": "droguería-limpieza"},
    ])
    assert [s["seccion"] for s in catalogo.secciones(["dia"])] == ["frutas-verduras"]


def test_un_gold_anterior_al_cambio_devuelve_lista_vacia_y_no_revienta(gold):
    """El estado normal entre desplegar y la siguiente ejecución del scraper.

    La plataforma se actualiza sola y gold sólo cuando corre el scraper. Pedir
    una columna que todavía no está tiraba la app entera con un Binder Error --
    no la pantalla, la app, porque la conexión se crea al arrancar. Una lista
    vacía es una respuesta honesta; inventarse los pasillos, no.
    """
    gold([{"fuente": "dia", "nombre": "Manzana"}], con_seccion=False)
    assert catalogo.secciones() == []


# --------------------------------------------------------- buscar por pasillo --

def test_mirar_un_pasillo_es_una_busqueda_sin_texto(gold):
    gold([
        {"fuente": "dia", "nombre": "Manzana golden", "seccion": "frutas-verduras"},
        {"fuente": "dia", "nombre": "Lejía", "seccion": "droguería-limpieza"},
    ])
    r = catalogo.buscar("", seccion="frutas-verduras")
    assert [x["nombre"] for x in r] == ["Manzana golden"]


def test_sin_texto_y_sin_pasillo_no_se_contesta_el_catalogo_entero(gold):
    gold([{"fuente": "dia", "nombre": "Manzana", "seccion": "frutas-verduras"}])
    assert catalogo.buscar("") == []


def test_el_pasillo_afina_la_busqueda_de_texto(gold):
    """"Leche" en el pasillo de lácteos no puede traer leche corporal."""
    gold([
        {"fuente": "dia", "nombre": "Leche entera", "seccion": "lacteos-huevos"},
        {"fuente": "dia", "nombre": "Leche corporal", "seccion": "higiene-belleza"},
    ])
    r = catalogo.buscar("leche", seccion="lacteos-huevos")
    assert [x["nombre"] for x in r] == ["Leche entera"]
