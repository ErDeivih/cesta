"""El mosaico de lo habitual: de donde sale, que se manda y que no.

`GET /api/habituales` es la ruta que convierte anadir un producto en **un toque**,
y tiene una parte que se queda sin pensar siempre: el primer dia, cuando no hay
historial. Estas pruebas cubren las dos cosas.

Lo que se vigila aqui, y por que:

    · que los tres origenes se distingan. La cuadricula se pinta igual en los tres
      casos y significan cosas muy distintas: sin el campo `origen` la pantalla
      ensenaria "lo que sueles comprar" con lo que compra otro
    · que con el historial vacio la pantalla NO se vea vacia
    · que `veces` y `ultima_vez` solo viajen cuando son de esta persona
    · que ningun campo viaje vacio: ni `null`, ni `""`, ni un cero que se lea
      como gratis
    · que la regla del historial -- contar tambien lo borrado, contar solo lo
      anadido por esta persona, y pesar por recencia -- este donde se cree que
      esta, porque el SQL no se puede ejecutar sin PostgreSQL en estas pruebas

El gold es de mentira (`gold`, abajo) y el historial se sustituye: una prueba que
dependa del catalogo del dia mide el calendario, no el codigo.
"""
from __future__ import annotations

import re
from dataclasses import replace

import duckdb
import pytest
from fastapi.testclient import TestClient

from plataforma.api import almacen, catalogo, habituales, main

# --------------------------------------------------- un gold de mentira ---


@pytest.fixture
def gold(tmp_path, monkeypatch):
    """Escribe un `data/gold` minimo y apunta el catalogo ahi.

    Productos: `{"fuente", "nombre", "grupo_id"?, "precio_unidad_cent"?,
    "unidad_canon"?, "comparacion_fiable"?, "imagen"?}`. Lo que no se diga sale
    con los valores de un producto normal: 100 centimos por kilo y comparable.
    """
    def escribe(productos):
        con = duckdb.connect()
        con.execute("""
            CREATE TABLE g (
                grupo_id BIGINT, fuente VARCHAR, id_fuente VARCHAR, nombre VARCHAR,
                marca VARCHAR, cantidad DOUBLE, unidad_canon VARCHAR,
                precio_cent BIGINT, precio_unidad_cent DOUBLE,
                comparacion_fiable BOOLEAN, calidad VARCHAR,
                calidad_origen VARCHAR, nutriscore VARCHAR, nova BIGINT,
                ean VARCHAR, imagen VARCHAR, promo_txt VARCHAR)
        """)
        for i, p in enumerate(productos):
            valores = [p.get("grupo_id", i + 1), p["fuente"], str(i), p["nombre"],
                       None, 1.0, p.get("unidad_canon", "kg"),
                       p.get("precio_cent", 100), p.get("precio_unidad_cent", 100.0),
                       p.get("comparacion_fiable", True),
                       None, None, None, None, None, p.get("imagen"), None]
            con.execute(f"INSERT INTO g VALUES ({','.join('?' * len(valores))})",
                        valores)
        con.execute(f"COPY g TO '{tmp_path / 'grupos.parquet'}' (FORMAT PARQUET)")
        # `fecha_de_gold` lee esta columna: sin ella la ruta no puede decir de que
        # dia son los precios, y la fecha es lo que sostiene la regla de las fechas.
        con.execute(f"COPY (SELECT DATE '2026-09-23' AS fecha) "
                    f"TO '{tmp_path / 'precio_diario.parquet'}' (FORMAT PARQUET)")
        for otro in ("enlaces", "resumen", "precio_derivado"):
            con.execute(f"COPY (SELECT 1 AS x) TO '{tmp_path / otro}.parquet' "
                        f"(FORMAT PARQUET)")
        con.close()
        catalogo.reiniciar()
        # La compra basica se cachea por fecha de gold, y aqui todas las pruebas
        # escriben el mismo dia: sin vaciarla, la segunda veria la primera.
        habituales._basico = ("", [])

    monkeypatch.setattr(catalogo, "AJUSTES", replace(catalogo.AJUSTES, gold=tmp_path))
    yield escribe
    catalogo.reiniciar()


TRES_CADENAS = [
    {"fuente": "aldi", "nombre": "Leche entera", "grupo_id": 10, "imagen": "foto"},
    {"fuente": "dia", "nombre": "Leche entera brik", "grupo_id": 10,
     "precio_unidad_cent": 110.0},
    {"fuente": "carrefour", "nombre": "Pan de molde", "grupo_id": 20,
     "precio_unidad_cent": 200.0},
]


def _cliente(monkeypatch, historial=(), de_todos=()):
    """El cliente con sesion, y el historial de PostgreSQL sustituido."""
    monkeypatch.setattr(almacen, "historial_de",
                        lambda usuario_id, limite=72: list(historial))
    monkeypatch.setattr(almacen, "mas_comprados", lambda limite=72: list(de_todos))
    main.app.dependency_overrides[main.usuario_actual] = lambda: {
        "id": "u1", "usuario": "ana", "nombre": "Ana"}
    return TestClient(main.app)


def _pide(cliente, **params):
    r = cliente.get("/api/habituales", params=params)
    assert r.status_code == 200, r.text
    return r.json()


def _vacios(dato, camino=""):
    """Los campos que no deberian viajar, con su camino dentro del JSON.

    Un `false` NO es un campo vacio: `fiable: false` es un dato -- "aqui no hay
    comparacion en la que fiarse" -- y es justo lo que la pantalla necesita para
    no inventarse una recomendacion. Por eso el cero se mira solo en los numeros.
    """
    malos = []
    if isinstance(dato, dict):
        for clave, valor in dato.items():
            malos += _vacios(valor, f"{camino}.{clave}")
    elif isinstance(dato, list):
        for i, valor in enumerate(dato):
            malos += _vacios(valor, f"{camino}[{i}]")
    elif (dato is None or dato == ""
          or (isinstance(dato, (int, float)) and not isinstance(dato, bool)
              and dato == 0)):
        malos.append(camino)
    return malos


# ------------------------------------------------------------ la sesion ---

def test_sin_sesion_no_se_ensena_el_historial():
    """Esto es el historial de compra de una persona, no el catalogo.

    Sin cookie no se llega ni a la base de datos: `quien(None)` devuelve None sin
    abrir conexion, asi que esta prueba no necesita PostgreSQL.
    """
    cliente = TestClient(main.app)
    r = cliente.get("/api/habituales")
    assert r.status_code == 401, r.text


def test_el_limite_por_defecto_es_24(monkeypatch, gold):
    gold(TRES_CADENAS)
    visto: list = []
    monkeypatch.setattr(almacen, "historial_de",
                        lambda usuario_id, limite=72: (visto.append(limite), [])[1])
    monkeypatch.setattr(almacen, "mas_comprados", lambda limite=72: [])
    main.app.dependency_overrides[main.usuario_actual] = lambda: {"id": "u1"}
    try:
        TestClient(main.app).get("/api/habituales")
    finally:
        main.app.dependency_overrides.clear()
    # Al historial se le piden mas de los que se ensenan: un grupo puede no estar
    # ya en gold, y sin margen la cuadricula se quedaria corta sin decir por que.
    assert visto == [24 * habituales.MARGEN]


@pytest.mark.parametrize("limite", [0, -1, 61, 500])
def test_un_limite_imposible_es_una_peticion_mal_formada(monkeypatch, gold, limite):
    gold(TRES_CADENAS)
    cliente = _cliente(monkeypatch)
    try:
        assert cliente.get("/api/habituales", params={"limite": limite}).status_code == 422
    finally:
        main.app.dependency_overrides.clear()


# ------------------------------------------------------------ los origenes ---

def test_lo_suyo_dice_que_es_suyo_y_cuando_lo_anadio(monkeypatch, gold):
    gold(TRES_CADENAS)
    cliente = _cliente(monkeypatch, historial=[
        {"grupo_id": 20, "veces": 9, "ultima_vez": "2026-09-16"},
        {"grupo_id": 10, "veces": 2, "ultima_vez": "2026-09-02"},
    ])
    try:
        cuerpo = _pide(cliente)
    finally:
        main.app.dependency_overrides.clear()
    assert cuerpo["origen"] == "tuyo"
    # El orden lo decide PostgreSQL (lo reciente pesa mas): la ruta no lo toca.
    assert [h["grupo_id"] for h in cuerpo["habituales"]] == [20, 10]
    primero = cuerpo["habituales"][0]
    assert primero["veces"] == 9
    assert primero["ultima_vez"] == "2026-09-16"
    assert primero["nombre"] == "Pan de molde"
    assert primero["precio_unidad_cent"] == 200.0
    assert primero["unidad"] == "kg"
    assert primero["cadena_mas_barata"] == "carrefour"
    assert primero["fiable"] is False        # solo una cadena: no hay con quien comparar
    assert cuerpo["fecha_datos"] == "2026-09-23"


def test_lo_suyo_solo_ensena_lo_que_se_puede_pintar(monkeypatch, gold):
    """Un grupo que ya no esta en gold no tiene tarjeta, y no se inventa.

    Es lo que pasa cuando se rehace el emparejador: los identificadores de grupo
    son de la ultima pasada, y el historial de PostgreSQL sigue apuntando a los de
    la anterior. La pantalla se queda con las tarjetas que existen.
    """
    gold(TRES_CADENAS)
    cliente = _cliente(monkeypatch, historial=[
        {"grupo_id": 999999, "veces": 40, "ultima_vez": "2026-09-20"},
        {"grupo_id": 10, "veces": 2, "ultima_vez": "2026-09-02"},
    ])
    try:
        cuerpo = _pide(cliente)
    finally:
        main.app.dependency_overrides.clear()
    assert cuerpo["origen"] == "tuyo"
    assert [h["grupo_id"] for h in cuerpo["habituales"]] == [10]


def test_sin_historial_se_ensena_lo_de_todos_y_sin_decir_tus_veces(monkeypatch, gold):
    """El primer dia. Y `veces` no viaja: ahi el recuento es de todo el mundo.

    Mandarlo con el mismo nombre que en el historial propio seria otra vez dos
    numeros distintos llamandose igual, que es el error que ya se pago una vez con
    "imposible" (ver core/comparacion.py).
    """
    gold(TRES_CADENAS)
    cliente = _cliente(monkeypatch, de_todos=[
        {"grupo_id": 10, "veces": 7, "ultima_vez": "2026-09-21", "personas": 2},
        {"grupo_id": 20, "veces": 3, "ultima_vez": "2026-09-10", "personas": 1},
    ])
    try:
        cuerpo = _pide(cliente)
    finally:
        main.app.dependency_overrides.clear()
    assert cuerpo["origen"] == "de todos"
    assert [h["grupo_id"] for h in cuerpo["habituales"]] == [10, 20]
    for h in cuerpo["habituales"]:
        assert "veces" not in h and "ultima_vez" not in h
    assert cuerpo["habituales"][0]["precio_unidad_cent"] == 100.0


def test_sin_historial_ni_de_nadie_la_pantalla_no_se_ve_vacia(monkeypatch, gold):
    """El caso que se queda sin pensar: la base recien creada.

    Es la forma de aceptar el encargo -- *con historial vacio la pantalla no se ve
    vacia* --, y sin esto lo primero que ve alguien que prueba la aplicacion es
    una pantalla en blanco.
    """
    gold([
        {"fuente": "aldi", "nombre": "Leche entera", "grupo_id": 10, "imagen": "foto"},
        {"fuente": "dia", "nombre": "Leche entera brik", "grupo_id": 10},
    ])
    cliente = _cliente(monkeypatch)
    try:
        cuerpo = _pide(cliente)
    finally:
        main.app.dependency_overrides.clear()
    assert cuerpo["origen"] == "basico"
    assert cuerpo["habituales"], "con historial vacio la cuadricula no puede ir vacia"
    for h in cuerpo["habituales"]:
        assert not _vacios(h), h
        assert h["precio_unidad_cent"] > 0
        assert "veces" not in h and "ultima_vez" not in h


def test_un_historial_que_no_se_puede_pintar_baja_al_siguiente_origen(monkeypatch, gold):
    """Tener historial no basta: tiene que haber algo que ensenar.

    Si todos los grupos que alguien compraba han desaparecido del catalogo, la
    pantalla se queda vacia igual que si no hubiera historial, y `origen` lo dice:
    "de todos", que es de donde sale lo que se esta ensenando.
    """
    gold(TRES_CADENAS)
    cliente = _cliente(monkeypatch,
                       historial=[{"grupo_id": 777, "veces": 5, "ultima_vez": "2026-09-01"}],
                       de_todos=[{"grupo_id": 20, "veces": 4, "ultima_vez": "2026-09-02",
                                  "personas": 2}])
    try:
        cuerpo = _pide(cliente)
    finally:
        main.app.dependency_overrides.clear()
    assert cuerpo["origen"] == "de todos"
    assert [h["grupo_id"] for h in cuerpo["habituales"]] == [20]


def test_el_limite_manda(monkeypatch, gold):
    gold(TRES_CADENAS)
    cliente = _cliente(monkeypatch, historial=[
        {"grupo_id": 10, "veces": 9, "ultima_vez": "2026-09-16"},
        {"grupo_id": 20, "veces": 2, "ultima_vez": "2026-09-02"},
    ])
    try:
        cuerpo = _pide(cliente, limite=1)
    finally:
        main.app.dependency_overrides.clear()
    assert [h["grupo_id"] for h in cuerpo["habituales"]] == [10]


# ------------------------------------------------------------- la tarjeta ---

def test_ningun_campo_viaja_vacio(monkeypatch, gold):
    """Ni `null`, ni `""`, ni un cero que se lea como gratis.

    Un grupo sin foto no manda `imagen`: la pantalla sabe dibujar su hueco, y un
    campo vacio se lee como un dato roto. Un dato que no tenemos es "no lo se".
    """
    gold(TRES_CADENAS)          # el grupo 20 no tiene imagen; el 10 si
    cliente = _cliente(monkeypatch, historial=[
        {"grupo_id": 10, "veces": 9, "ultima_vez": "2026-09-16"},
        {"grupo_id": 20, "veces": 2, "ultima_vez": "2026-09-02"},
    ])
    try:
        cuerpo = _pide(cliente)
    finally:
        main.app.dependency_overrides.clear()
    assert _vacios(cuerpo) == []
    tarjetas = {h["grupo_id"]: h for h in cuerpo["habituales"]}
    assert tarjetas[10]["imagen"] == "foto"
    assert "imagen" not in tarjetas[20]


def test_un_grupo_sin_precio_no_tiene_tarjeta(gold):
    """Una tarjeta sin precio no se puede tocar para anadir nada, que es lo unico
    que hace la cuadricula. Se queda fuera en vez de salir con el precio en blanco."""
    gold([{"fuente": "aldi", "nombre": "Leche entera", "grupo_id": 10},
          {"fuente": "aldi", "nombre": "Sin precio", "grupo_id": 30,
           "precio_unidad_cent": 0.0, "precio_cent": 0}])
    assert set(catalogo.tarjetas([10, 30])) == {10}


def test_una_sola_cadena_no_es_comparable(gold):
    """Con una sola cadena no hay comparacion que hacer, y decirlo es una respuesta.

    La pantalla usa `fiable` para no inventarse una recomendacion: es la regla de
    la ficha de producto -- *"no puedo compararlo: no lo encuentro en otras
    cadenas"* -- aplicada a la cuadricula.
    """
    gold([{"fuente": "aldi", "nombre": "Solo aqui", "grupo_id": 10},
          {"fuente": "aldi", "nombre": "En dos", "grupo_id": 20},
          {"fuente": "dia", "nombre": "En dos", "grupo_id": 20}])
    tarjetas = catalogo.tarjetas([10, 20])
    assert tarjetas[10]["fiable"] is False
    assert tarjetas[20]["fiable"] is True


def test_una_unidad_que_no_se_puede_comparar_no_es_fiable(gold):
    """"ud" no esta en `UNIDADES_FIABLES` (kg, l, m): dos precios por unidad de un
    grupo medido en unidades no se pueden comparar entre cadenas."""
    gold([{"fuente": "aldi", "nombre": "Docena", "grupo_id": 10, "unidad_canon": "ud",
           "comparacion_fiable": False},
          {"fuente": "dia", "nombre": "Docena", "grupo_id": 10, "unidad_canon": "ud",
           "comparacion_fiable": False}])
    assert catalogo.tarjetas([10])[10]["fiable"] is False


def test_dos_precios_que_se_contradicen_no_son_fiables(gold):
    """El mismo grupo a 1 EUR/kg y a 101 EUR/kg no es una oferta: somos nosotros.

    Es la frontera de `core/comparacion.py` (30x), la misma que usa la busqueda
    para marcar un grupo como dudoso.
    """
    gold([{"fuente": "aldi", "nombre": "Raro", "grupo_id": 10,
           "precio_unidad_cent": 100.0},
          {"fuente": "dia", "nombre": "Raro", "grupo_id": 10,
           "precio_unidad_cent": 10100.0}])
    assert catalogo.tarjetas([10])[10]["fiable"] is False


def test_la_tarjeta_y_la_busqueda_dicen_el_mismo_precio(gold):
    """Guarda de la duplicacion: la regla de la unidad esta escrita en los dos sitios.

    `tarjetas` no reutiliza la consulta de `buscar` -- reutilizarla obligaria a
    tocar la consulta que sostiene la pantalla de resultados --, asi que la unica
    forma de que no se separen es esta prueba: los dos tienen que decir el mismo
    nombre, el mismo precio, la misma unidad y la misma cadena para el mismo grupo.
    """
    gold([
        # El mismo grupo con la manzanilla en dos unidades: la que manda es la que
        # comparten mas cadenas, y los precios de la otra no pueden decidir.
        {"fuente": "aldi", "nombre": "Manzanilla", "grupo_id": 10,
         "unidad_canon": "kg", "precio_unidad_cent": 200.0},
        {"fuente": "dia", "nombre": "Manzanilla", "grupo_id": 10,
         "unidad_canon": "kg", "precio_unidad_cent": 300.0},
        {"fuente": "dia", "nombre": "Manzanilla bolsitas", "grupo_id": 10,
         "unidad_canon": "ud", "precio_unidad_cent": 5.0, "comparacion_fiable": False},
        {"fuente": "aldi", "nombre": "Pan", "grupo_id": 20},
    ])
    resultados = catalogo.buscar("manzanilla") + catalogo.buscar("pan")
    assert resultados, "la busqueda no ha devuelto nada: la prueba no miraria nada"
    tarjetas = catalogo.tarjetas([r["grupo_id"] for r in resultados])
    for r in resultados:
        t = tarjetas[r["grupo_id"]]
        assert t["nombre"] == r["nombre"]
        assert t["precio_unidad_cent"] == r["precio_unidad_cent"]
        assert t["unidad"] == r["unidad"]
        assert t["cadena_mas_barata"] == r["cadena_mas_barata"]
        # La foto es el unico campo que se presenta distinto: la busqueda manda
        # `imagen: null` y la tarjeta no manda el campo. Es el mismo dato, y la
        # regla de la casa es que lo que no hay no viaja vacio.
        assert t.get("imagen") == r["imagen"]


# -------------------------------------- las tres reglas del historial ---
#
# El SQL del historial solo se puede ejecutar con PostgreSQL delante, y estas
# pruebas no lo tienen. Lo que se vigila aqui es que las tres decisiones que el
# encargo pide esten escritas donde se cree que estan: si alguien reescribe la
# consulta y se lleva una por delante, se entera aqui y no en el mosaico.

def _sql(suyo: bool = True) -> str:
    return " ".join(almacen.consulta_historial(suyo).split())


def test_el_historial_cuenta_las_lineas_borradas():
    """Una lista se vacia al terminar la compra; el habito no.

    `lista_linea` no borra de verdad: pone `borrado_en` y las limpia a los 30 dias.
    Filtrando por `borrado_en IS NULL` -- que es lo que hace el resto de la API
    para ensenar una lista -- el historial de quien usa la lista como se usa una
    lista estaria siempre vacio.
    """
    assert "borrado_en" not in _sql()


def test_el_historial_es_el_de_esta_persona():
    """En una lista compartida se apunta lo que trae el otro, y eso no es tu habito.

    Y con `anadido_por` de por medio, quien solo puede mirar una lista no saca de
    aqui lo que hay dentro de ella.
    """
    assert "anadido_por = %(u)s" in _sql()
    assert "anadido_por = %(u)s" not in _sql(suyo=False), (
        "el recuento de todos no puede filtrar por autor: es de todos a proposito")


def test_el_historial_pesa_por_recencia_y_no_corta_por_fecha():
    """Lo que se eligio, y lo que se descarto, en una linea.

    Se eligio pesar (vida media de `VIDA_MEDIA_DIAS`) en vez de contar solo los
    ultimos 90 dias: con un corte, un producto desaparece de la cuadricula de un
    dia para otro al cruzar el dia 90, y `veces` tendria que pasar a significar
    "veces en 90 dias". El porque entero, en `almacen.historial_de`.
    """
    sql = _sql()
    assert "power(0.5" in sql and str(almacen.VIDA_MEDIA_DIAS) in sql
    assert "interval" not in sql, "hay un corte por fecha donde deberia haber decaimiento"
    assert "ORDER BY peso DESC" in sql


def test_veces_es_el_recuento_entero_y_el_peso_solo_ordena():
    """`veces` es lo que de verdad hizo la persona; el decaimiento decide el orden."""
    sql = _sql()
    assert "count(*) AS veces" in sql
    # El decaimiento es la suma que se llama `peso`, y `peso` solo aparece en el
    # ORDER BY: si alguien lo metiera dentro de `veces`, la pantalla diria un
    # numero que no es el de veces que se anadio.
    assert re.search(r"sum\(power\(0\.5::float8.*?\)\) AS peso", sql), sql
    assert "veces *" not in sql


def test_el_historial_no_se_trae_la_tabla_entera():
    assert "LIMIT %(n)s" in _sql()


def test_el_empate_no_baile_entre_dos_peticiones():
    """Sin un ultimo criterio estable, la cuadricula cambiaria de orden sola.

    PostgreSQL no promete el orden de dos filas empatadas, y un mosaico que se
    recoloca cada vez que se abre se lee como un fallo.
    """
    assert "ORDER BY peso DESC, veces DESC, grupo_id" in _sql()
    assert ("ORDER BY personas DESC, peso DESC, veces DESC, grupo_id"
            in _sql(suyo=False))
