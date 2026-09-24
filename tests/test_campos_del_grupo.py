"""Cada campo de la ficha sale **de su columna**, y esto es lo que costo el dia que no.

El 24 de septiembre de 2026, anadiendo una comprobacion del reparto entre dos tiendas a la
puerta del navegador, salio un `FALLO` que no tenia nada que ver: la pantalla del grupo 0 no
decia por que no llevaba frase, y era porque **`/api/grupo/0` contestaba 500**.

La causa llevaba ahi desde que alguien anadio una columna a la lista de `nuevas` de
`catalogo.grupo()`: `prod()` leia la fila **por posicion** (`f[35]`, `f[36]`...), asi que todo
lo que iba detras de la columna nueva se quedo **uno a la izquierda**, sin que nada avisara.
Medido sobre el gold del 23 de septiembre de 2026:

    482 grupos daban 500         su producto mas barato tiene `advertencias`, que es texto, y
                                 el codigo hacia `(f[40] or 0) > 1`: comparar texto con un
                                 numero revienta. Es el 1,1 % de los 44.434 grupos.
    3.844 productos con alcohol  salian marcados como **retirados** (`es_recall` leia
                                 `es_alcohol`), que es la mentira mas cara que puede decir
                                 esta pantalla
    341 promociones solo online  salian como alcohol, y con eso el filtro de "sin alcohol"
                                 escondia productos que no lo son
    544 productos                ensenaban su `peso_variacion_pct` en el sitio del `distintivo`
    unidades_pack                no llegaba nunca a la pantalla (leia `advertencias`)

Arreglado leyendo **por nombre**: los nombres los da la propia consulta (`cursor.description`),
asi que anadir una columna no puede mover ninguna otra. Y esta prueba es la que impide que
vuelva: un grupo de mentira con **un valor distinto en cada columna**, para que un desajuste se
vea como lo que es -- un campo con el valor de otro.
"""
from __future__ import annotations

from dataclasses import replace

import duckdb
import pytest

from plataforma.api import catalogo

# Una fila donde **cada columna tiene un valor que solo puede venir de ella**. Si dos campos
# se intercambian, esta prueba lo dice con los dos valores delante.
FILA = {
    "fuente": "dia", "id_fuente": "77", "nombre": "Producto de prueba",
    "marca": "Marca", "cantidad": 1.0, "unidad_canon": "l", "ean": "8412345678905",
    "precio_cent": 150, "precio_unidad_cent": 150.0,
    "precio_ref_canon_cent": 150, "unidad_ref_canon": "l",
    "imagen": "http://imagen", "alergenos": "ALERGENOS", "ingredientes": "INGREDIENTES",
    "origen": "ORIGEN", "promo_txt": "PROMO", "categoria": "despensa", "url": "http://x",
    "grupo_id": 1, "calidad": "B", "calidad_origen": "ingredientes",
    "calidad_nota": 7.5, "nutriscore": "b", "comparacion_fiable": True, "nova": 3,
    # Y las que se corrieron:
    "sellos": "sin-gluten", "sellos_origen": "etiqueta",
    "certificados": "certificado", "conservacion": "ambiente",
    "es_marca_propia": True, "nutricion": '{"energia_kj": 100}',
    "nutricion_por": "100 g", "envase": "botella", "descripcion": "DESCRIPCION",
    "tipo_producto": "bebida", "dias_caducidad": 30, "peso_neto_g": 1000,
    "grado_alcohol": 4.5, "promo_club": True, "promo_solo_online": True,
    "es_alcohol": False, "es_recall": True, "peso_variacion_pct": 25.0,
    "distintivo": "DISTINTIVO", "advertencias": "AVISO UNO | AVISO DOS",
    "unidades_pack": 6,
}


@pytest.fixture
def gold(tmp_path, monkeypatch):
    con = duckdb.connect()
    columnas = ", ".join(f"{c} {t}" for c, t in (
        ("fuente", "VARCHAR"), ("id_fuente", "VARCHAR"), ("nombre", "VARCHAR"),
        ("marca", "VARCHAR"), ("cantidad", "DOUBLE"), ("unidad_canon", "VARCHAR"),
        ("ean", "VARCHAR"), ("precio_cent", "BIGINT"), ("precio_unidad_cent", "DOUBLE"),
        ("precio_ref_canon_cent", "BIGINT"), ("unidad_ref_canon", "VARCHAR"),
        ("imagen", "VARCHAR"), ("alergenos", "VARCHAR"), ("ingredientes", "VARCHAR"),
        ("origen", "VARCHAR"), ("promo_txt", "VARCHAR"), ("categoria", "VARCHAR"),
        ("url", "VARCHAR"), ("grupo_id", "BIGINT"), ("calidad", "VARCHAR"),
        ("calidad_origen", "VARCHAR"), ("calidad_nota", "DOUBLE"), ("nutriscore", "VARCHAR"),
        ("comparacion_fiable", "BOOLEAN"), ("nova", "BIGINT"), ("sellos", "VARCHAR"),
        ("sellos_origen", "VARCHAR"), ("certificados", "VARCHAR"), ("conservacion", "VARCHAR"),
        ("es_marca_propia", "BOOLEAN"), ("nutricion", "VARCHAR"), ("nutricion_por", "VARCHAR"),
        ("envase", "VARCHAR"), ("descripcion", "VARCHAR"), ("tipo_producto", "VARCHAR"),
        ("dias_caducidad", "BIGINT"), ("peso_neto_g", "BIGINT"), ("grado_alcohol", "DOUBLE"),
        ("promo_club", "BOOLEAN"), ("promo_solo_online", "BOOLEAN"), ("es_alcohol", "BOOLEAN"),
        ("es_recall", "BOOLEAN"), ("peso_variacion_pct", "DOUBLE"),
        ("distintivo", "VARCHAR"), ("advertencias", "VARCHAR"), ("unidades_pack", "BIGINT")))
    con.execute(f"CREATE TABLE g ({columnas})")
    con.execute(f"INSERT INTO g VALUES ({','.join('?' * len(FILA))})", list(FILA.values()))
    # `promo_hasta` es la unica que la consulta pide ya convertida a texto, y tiene que estar
    # como `TIMESTAMPTZ` de verdad: sin la columna, `catalogo` monta un `NULL AS promo_hasta`
    # y DuckDB se queja de que no se puede referenciar antes de definirla.
    con.execute("""
        ALTER TABLE g ADD COLUMN promo_hasta TIMESTAMPTZ;
        UPDATE g SET promo_hasta = TIMESTAMPTZ '2026-09-25 00:00:00+02';
    """)
    con.execute(f"COPY g TO '{tmp_path / 'grupos.parquet'}' (FORMAT PARQUET)")
    con.execute(f"""
        COPY (SELECT 'dia:77' AS producto_id, 'dia' AS fuente, DATE '2026-09-23' AS fecha,
                     150 AS precio_cent, 150.0 AS precio_unidad_cent, 'l' AS unidad_canon)
        TO '{tmp_path / 'precio_diario.parquet'}' (FORMAT PARQUET)""")
    for otro in ("enlaces", "resumen", "precio_derivado", "equivalencia"):
        con.execute(f"COPY (SELECT 1 AS x) TO '{tmp_path / (otro + '.parquet')}' "
                    f"(FORMAT PARQUET)")
    con.close()
    monkeypatch.setattr(catalogo, "AJUSTES", replace(catalogo.AJUSTES, gold=tmp_path))
    catalogo.reiniciar()
    yield
    catalogo.reiniciar()


def test_cada_campo_sale_de_su_columna(gold):
    """El desajuste de un indice se ve aqui como un campo con el valor de otro."""
    producto = catalogo.grupo(1)["productos"][0]
    esperado = {
        "advertencias": ["AVISO UNO", "AVISO DOS"],
        "distintivo": "DISTINTIVO",
        "peso_variacion_pct": 25.0,
        "es_recall": True,
        "es_alcohol": False,
        "unidades_pack": 6,
        "promo_solo_online": True,
        "promo_club": True,
        "grado_alcohol": 4.5,
        "descripcion": "DESCRIPCION",
        "envase": "botella",
        "nutricion_por": "100 g",
        "tipo_producto": "bebida",
        "conservacion": "ambiente",
        "certificados": ["certificado"],
        "sellos": ["sin-gluten"],
        "sellos_origen": "etiqueta",
        "origen": "ORIGEN",
        "ingredientes": "INGREDIENTES",
        "alergenos": "ALERGENOS",
        "imagen": "http://imagen",
        "url": "http://x",
        "promo": "PROMO",
        "calidad": "B",
        "nutriscore": "b", "nova": 3, "ean": "8412345678905",
        "unidad": "l", "comparable": True,
        # Esta viaja como texto ya convertido (`promo_hasta::VARCHAR`), y solo sus diez
        # primeros caracteres son la fecha.
        "promo_hasta": "2026-09-25",
    }
    for campo, valor in esperado.items():
        assert producto[campo] == valor, (
            f"«{campo}» no trae su valor, trae {producto[campo]!r}: los indices de la fila "
            f"se han vuelto a mover de sitio (mira `prod()` y el orden de `nuevas`)")


def test_una_advertencia_no_tumba_la_ficha(gold):
    """Eran 482 grupos: el texto de `advertencias` comparado con un numero, y 500."""
    assert catalogo.grupo(1) is not None, "la ficha del grupo se ha caido"
