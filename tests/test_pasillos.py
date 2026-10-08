"""El pasillo de cada linea de la lista, que es lo que permite pintarla por tandas.

Es la mitad de datos de la condicion (c) de la barra: *"la lista en dos secciones,
**con pasillo pegajoso** y sin aviso rojo cuando no hay cobertura"*. La otra mitad
(las dos secciones y el aviso) esta hecha y probada; esta es la que faltaba.

Lo que se vigila aqui:

  - **De donde sale el pasillo.** El pasillo es un atributo del **producto**, no del
    grupo, y un grupo tiene miembros de varias cadenas: cuando no coinciden gana el
    que mas miembros comparten, y los empates se rompen por el orden del recorrido de
    la tienda. Sin una regla escrita, el mismo grupo cambia de pasillo entre dos
    ejecuciones sin que haya cambiado nada, y la lista se reordena sola delante de
    quien la esta mirando.
  - **Que un dato que no tenemos no se rellena.** Un grupo que no esta en gold, o un
    producto sin pasillo, **no viaja con `pasillo: null`**: no lleva las claves. La
    pantalla tiene que poder distinguir "no lo se" de "es de este pasillo".
  - **Que el pasillo no reordena nada en la API.** El orden de las lineas lo decide
    PostgreSQL (`en_carrito, anadido_en`) y aqui no se toca: quien reparte en tandas y
    las coloca en el recorrido de la tienda es la pantalla, que es la que sabe cuantas
    secciones tiene la lista.

El gold es de mentira y PostgreSQL no se toca: el historial y las lineas se
sustituyen. Una prueba que dependa del catalogo del dia mide el calendario, no el
codigo.
"""
from __future__ import annotations

import duckdb
import pytest
from fastapi.testclient import TestClient

from plataforma.api import almacen, catalogo, cesta, main

# --------------------------------------------------------------- gold falso ---

# Los dos productos de grupo 10 dicen "lacteos-huevos" y uno dice "despensa": gana
# el que mas miembros comparten.
# Los dos del grupo 20 estan en pasillos distintos: es el empate, y se rompe por el
# recorrido de la tienda (`frutas-verduras` va antes que `bebidas`).
PRODUCTOS = [
    {"fuente": "aldi", "nombre": "Leche entera", "grupo_id": 10,
     "seccion": "lacteos-huevos"},
    {"fuente": "dia", "nombre": "Leche entera brik", "grupo_id": 10,
     "seccion": "lacteos-huevos"},
    {"fuente": "carrefour", "nombre": "Leche entera carrefour", "grupo_id": 10,
     "seccion": "despensa"},
    {"fuente": "aldi", "nombre": "Platanos", "grupo_id": 20, "seccion": "bebidas"},
    {"fuente": "dia", "nombre": "Manzanas", "grupo_id": 20,
     "seccion": "frutas-verduras"},
    # Un producto sin pasillo: el grupo no puede salir en el diccionario.
    {"fuente": "dia", "nombre": "Pan de molde", "grupo_id": 30, "seccion": None},
]


@pytest.fixture
def gold(tmp_path, monkeypatch):
    """Escribe un `data/gold` minimo y apunta el catalogo ahi.

    `con_seccion=False` escribe el mismo catalogo **sin la columna**, que es como
    esta gold hasta que el pipeline la anota: entonces no hay pasillos y la lista se
    pinta de un tiron, como antes.
    """
    def escribe(productos=PRODUCTOS, con_seccion=True):
        con = duckdb.connect()
        # Las columnas son las que `catalogo.conexion` necesita para montar
        # `buscable`: las que no son opcionales tienen que existir aunque vengan
        # vacias, o la vista no se puede crear.
        columnas = ("grupo_id BIGINT, fuente VARCHAR, id_fuente VARCHAR, "
                    "nombre VARCHAR, marca VARCHAR, cantidad DOUBLE, "
                    "unidad_canon VARCHAR, precio_cent BIGINT, "
                    "precio_unidad_cent DOUBLE, comparacion_fiable BOOLEAN, "
                    "calidad VARCHAR, calidad_origen VARCHAR, nutriscore VARCHAR, "
                    "nova BIGINT, ean VARCHAR, imagen VARCHAR, promo_txt VARCHAR")
        if con_seccion:
            columnas += ", seccion VARCHAR"
        con.execute(f"CREATE TABLE g ({columnas})")
        for i, p in enumerate(productos):
            valores = [p.get("grupo_id", i + 1), p["fuente"], str(i), p["nombre"],
                       None, 1.0, "kg", p.get("precio_cent", 100),
                       p.get("precio_unidad_cent", 100.0), True,
                       None, None, None, None, None, None, None]
            if con_seccion:
                valores.append(p.get("seccion"))
            con.execute(f"INSERT INTO g VALUES ({','.join('?' * len(valores))})",
                        valores)
        con.execute(f"COPY g TO '{tmp_path / 'grupos.parquet'}' (FORMAT PARQUET)")
        con.execute(f"COPY (SELECT DATE '2026-09-23' AS fecha) "
                    f"TO '{tmp_path / 'precio_diario.parquet'}' (FORMAT PARQUET)")
        for otro in ("enlaces", "resumen", "precio_derivado"):
            con.execute(f"COPY (SELECT 1 AS x) TO '{tmp_path / otro}.parquet' "
                        f"(FORMAT PARQUET)")
        con.close()
        catalogo.reiniciar()

    from dataclasses import replace
    monkeypatch.setattr(catalogo, "AJUSTES", replace(catalogo.AJUSTES, gold=tmp_path))
    yield escribe
    catalogo.reiniciar()


# ------------------------------------------------------------------ pasillos ---


def test_el_pasillo_del_grupo_es_el_que_mas_miembros_comparten(gold):
    """Tres miembros en dos pasillos: gana el que dos comparten."""
    gold()
    pasillos = catalogo.pasillo_de_grupos([10, 20])
    assert pasillos[10]["seccion"] == "lacteos-huevos", \
        "con dos de tres miembros, gana el pasillo de la mayoria"
    assert pasillos[10]["pasillo"] == "Lácteos y huevos", \
        "el nombre que se pinta sale de NOMBRES_SECCIONES, no del slug"


def test_el_empate_lo_rompe_el_recorrido_de_la_tienda(gold):
    """Y no el alfabeto, ni el orden en que llegaron las filas."""
    gold()
    pasillos = catalogo.pasillo_de_grupos([20])
    assert pasillos[20]["seccion"] == "frutas-verduras"
    assert pasillos[20]["pasillo_orden"] < catalogo.ORDEN_SECCIONES.index("bebidas")


def test_un_grupo_sin_pasillo_no_viaja_con_pasillo_nulo(gold):
    """Sin dato no hay clave: la pantalla distingue "no lo se" de "es de aqui"."""
    gold()
    pasillos = catalogo.pasillo_de_grupos([10, 20, 30, 999])
    assert 30 not in pasillos, "un producto sin seccion no inventa un pasillo"
    assert 999 not in pasillos, "un grupo que no esta en gold tampoco"


def test_sin_la_columna_en_gold_no_hay_pasillos_y_no_se_inventan(gold):
    """La plataforma se despliega por separado del scraper: puede llegar antes.

    Y una lista sin pasillos se pinta de un tiron, como se pintaba ayer. Lo que no
    se hace es rellenar el hueco con el nombre del grupo ni con "otros".
    """
    gold(con_seccion=False)
    assert catalogo.pasillo_de_grupos([10, 20]) == {}


def test_con_pasillos_no_reordena_y_no_toca_las_lineas_sin_grupo(gold):
    """El pasillo se **anade**; el orden sigue siendo el de la API."""
    gold()
    lineas = [
        {"id": "a", "grupo_id": 20, "nombre_visto": "Platanos"},
        {"id": "b", "grupo_id": 999, "nombre_visto": "Algo que ya no esta"},
        {"id": "c", "grupo_id": None, "producto_id": "dia:1",
         "nombre_visto": "Suelto"},
        {"id": "d", "grupo_id": 10, "nombre_visto": "Leche entera"},
    ]
    salida = catalogo.con_pasillos(lineas)
    assert [x["id"] for x in salida] == ["a", "b", "c", "d"], \
        "la API no reordena: eso lo decide la pantalla con las dos secciones"
    assert salida[0]["pasillo"] == "Frutas y verduras"
    assert "pasillo" not in salida[1], "un grupo que no esta en gold no lleva pasillo"
    assert "pasillo" not in salida[2], "una linea suelta (sin grupo) tampoco"
    assert salida[3]["pasillo_orden"] == catalogo.ORDEN_SECCIONES.index(
        "lacteos-huevos")


def test_el_orden_del_pasillo_es_el_de_la_tienda_y_no_el_alfabeto(gold):
    """Lo que hace util el separador: el orden en que se recorre la tienda."""
    gold()
    orden = {s: i for i, s in enumerate(catalogo.ORDEN_SECCIONES)}
    assert orden["frutas-verduras"] < orden["carniceria"] < orden["lacteos-huevos"]
    # Una seccion que no este en la lista (una cadena nueva) sale al final: es lo
    # que hay que hacer con lo desconocido, no colocarla en medio.
    assert catalogo.pasillo_de_grupos([10])[10]["pasillo_orden"] < len(
        catalogo.ORDEN_SECCIONES)


# ------------------------------------------------------------ la ruta entera ---


def _lineas_falsas():
    return [
        {"id": "1", "grupo_id": 10, "producto_id": None, "nombre_visto": "Leche",
         "cantidad": 1, "nota": None, "tachado_en": None,
         "anadido_en": "2026-09-23T10:00:00", "en_carrito": False,
         "anadido_por": "Ana", "tachado_por": None},
        {"id": "2", "grupo_id": 20, "producto_id": None, "nombre_visto": "Platanos",
         "cantidad": 1, "nota": None, "tachado_en": None,
         "anadido_en": "2026-09-23T10:01:00", "en_carrito": False,
         "anadido_por": "Ana", "tachado_por": None},
    ]


def test_la_ruta_de_la_lista_manda_el_pasillo_en_cada_linea(gold, monkeypatch):
    """El contrato que consume la pantalla, probado entero y sin PostgreSQL."""
    gold()
    monkeypatch.setattr(almacen, "lineas_de", lambda lista_id: _lineas_falsas())
    monkeypatch.setattr(almacen, "autorizacion_de", lambda lista_id: {})
    # **La autorizacion, sustituida como las demas.** El endpoint la pide para decidir que cuenta
    # en el total, y sin sustituirla iria al almacen de verdad, que aqui no esta arrancado.
    monkeypatch.setattr(almacen, "autorizacion_de", lambda lista_id: {})
    monkeypatch.setattr(almacen, "novedades", lambda lista_id, usuario_id: [])
    monkeypatch.setattr(almacen, "marca_visita", lambda lista_id, usuario_id: None)
    monkeypatch.setattr(almacen, "quienes_en", lambda lista_id: [])
    # La estimacion tiene sus propias pruebas y necesita silver del dia; aqui lo que
    # se prueba es el pasillo, asi que se sustituye.
    monkeypatch.setattr(cesta, "estimacion",
                        lambda lineas: {"total_cent": 0, "en_carrito_cent": 0,
                                        "por_recoger_cent": 0, "lineas": len(lineas),
                                        "sin_precio": 0})
    monkeypatch.setattr(main, "_acceso", lambda *a, **k: "dueno")
    main.app.dependency_overrides[main.usuario_actual] = lambda: {
        "id": "u1", "usuario": "ana", "nombre": "Ana"}
    cliente = TestClient(main.app)

    r = cliente.get("/api/listas/lo-que-sea")
    assert r.status_code == 200, r.text
    lineas = r.json()["lineas"]
    assert [x["pasillo"] for x in lineas] == ["Lácteos y huevos", "Frutas y verduras"]
    assert [x["pasillo_orden"] for x in lineas] == [
        catalogo.ORDEN_SECCIONES.index("lacteos-huevos"),
        catalogo.ORDEN_SECCIONES.index("frutas-verduras")]
    # Y el orden de salida sigue siendo el de PostgreSQL, no el del recorrido.
    assert [x["id"] for x in lineas] == ["1", "2"]
    main.app.dependency_overrides.clear()


def test_sin_pasillos_la_ruta_devuelve_lo_de_siempre(gold, monkeypatch):
    """Con gold sin la columna, la respuesta es la de ayer: ni pasillos ni errores."""
    gold(con_seccion=False)
    monkeypatch.setattr(almacen, "lineas_de", lambda lista_id: _lineas_falsas())
    monkeypatch.setattr(almacen, "autorizacion_de", lambda lista_id: {})
    monkeypatch.setattr(almacen, "novedades", lambda lista_id, usuario_id: [])
    monkeypatch.setattr(almacen, "marca_visita", lambda lista_id, usuario_id: None)
    monkeypatch.setattr(almacen, "quienes_en", lambda lista_id: [])
    monkeypatch.setattr(cesta, "estimacion",
                        lambda lineas: {"total_cent": 0, "en_carrito_cent": 0,
                                        "por_recoger_cent": 0, "lineas": len(lineas),
                                        "sin_precio": 0})
    monkeypatch.setattr(main, "_acceso", lambda *a, **k: "dueno")
    main.app.dependency_overrides[main.usuario_actual] = lambda: {
        "id": "u1", "usuario": "ana", "nombre": "Ana"}
    cliente = TestClient(main.app)

    r = cliente.get("/api/listas/lo-que-sea")
    assert r.status_code == 200, r.text
    for linea in r.json()["lineas"]:
        assert "pasillo" not in linea
    main.app.dependency_overrides.clear()
