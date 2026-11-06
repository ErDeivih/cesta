"""Las ofertas de hoy: que se anuncia, como se llama y que no se inventa.

**Lo que esta pantalla promete es informacion, no un precio final.** Una oferta
anunciada no dice cuanto te descontaran en caja -- muchas ni descuentan, se
acumulan en la tarjeta o solo existen online --, asi que lo unico honesto es
ensenar el texto de la cadena, el precio de hoy y **que hace falta para
tenerla**. Por eso la prueba central es de clasificacion: si un "3x2" se
clasifica como descuento, la pantalla acaba diciendo algo que la cadena no ha
dicho.

Se prueba con textos **reales** del gold del 6 de noviembre de 2026, no con
inventados: «2ª ud al -50%», «3x2», «20% DTO.», «Precio condicionado a Lidl
Plus», «Solo online» y «5€ dto.» (que no es un tanto por ciento y por eso se
queda en «otro»).

Y se prueba **sin PostgreSQL**: las ofertas se leen de gold con DuckDB, asi que
las dos pruebas que necesitan datos usan un DuckDB en memoria con la forma de
las dos vistas que mira la consulta. La base de datos de las cuentas no pinta
nada aqui.
"""
from __future__ import annotations

import duckdb
import pytest
from fastapi.testclient import TestClient

from plataforma.api import cache, catalogo, main, movimientos


@pytest.fixture(autouse=True)
def _cache_limpia():
    """La cache de `ofertas` se indexa por version de gold, y aqui se falsea el gold.

    Sin esto, la respuesta de una prueba se queda guardada y la siguiente --
    con otro DuckDB falso -- lee la lista de la anterior. Es el mismo cuidado que
    toma `test_cache_por_version_gold.py`.
    """
    cache.olvida()
    yield
    cache.olvida()


# --------------------------------------------------------------- el tipo ---

@pytest.mark.parametrize("texto, club, online, esperado", [
    # Las mecanicas que de verdad hay en gold, con el texto tal cual.
    ("2ª ud al -50%", False, False, "segunda_unidad"),
    ("2ª UD 50% DTO EN PEPSI,7UP,LAYS,DORITOS,S.ANA", False, False, "segunda_unidad"),
    ("2x1", False, False, "segunda_unidad"),
    ("3x2", False, False, "3x2"),
    ("3 X 2 PEPSI ZERO AZÚCAR ZERO CAFEÍNA 330 ML", False, False, "3x2"),
    ("20% DTO.", False, False, "descuento"),
    ("-14%", False, False, "descuento"),
    ("Descuento -30% (05/11/26_18/11/26)", False, False, "descuento"),
    # La oferta de club no anuncia un mecanismo: lo que dice es la condicion.
    ("Precio condicionado a Lidl Plus", True, False, "club"),
    ("Club Alcampo 25% dto acumulado en tu tarjeta", True, False, "descuento"),
    # Solo online no es un mecanismo de precio, es donde se compra.
    ("Solo online", False, True, "solo_online"),
    ("-30% descuento. Solo online (05/11/2026 - 18/11/2026)", False, True, "descuento"),
    # Y lo que no encaja no se fuerza: un descuento en euros no es un porcentaje,
    # y una etiqueta de folleto no es una oferta.
    ("5€ dto.", False, False, "otro"),
    ("Envío Gratis", False, False, "otro"),
    ("Producto en Folleto (05/11/26_18/11/26)", False, False, "otro"),
])
def test_el_tipo_sale_del_texto_y_no_se_fuerza(texto, club, online, esperado):
    assert movimientos.tipo_oferta(texto, club, online) == esperado


def test_un_texto_vacio_no_revienta():
    assert movimientos.tipo_oferta(None, False, False) == "otro"


# ---------------------------------------------------------- la condicion ---

@pytest.mark.parametrize("cadena, club, online, texto, esperado", [
    ("lidl", True, False, "Precio condicionado a Lidl Plus", "Con Lidl Plus"),
    ("alcampo", True, False, "Club Alcampo 25% dto acumulado en tu tarjeta",
     "Con Club Alcampo, en tu tarjeta"),
    ("dia", True, False, "20% DTO.", "Con tarjeta DIA"),
    ("aldi", False, False, "2ª ud al -50%", "Sin club"),
    # El cupon de Carrefour no es la tarjeta, y se distinguen.
    ("carrefour", True, False, "20% en Cupón", "Con cupón Carrefour"),
    ("carrefour", True, False, "-10% Acumulación", "Con tarjeta Carrefour"),
    # Online manda sobre el club, **pero no lo calla**: si pide las dos cosas, las dice.
    ("alcampo", True, True, "2ª ud -50%. Solo Online (05/11/26_18/11/26)",
     "Solo online · con Club Alcampo, en tu tarjeta"),
])
def test_la_condicion_se_dice_en_lenguaje_de_usuario(cadena, club, online, texto, esperado):
    assert movimientos.condicion_oferta(cadena, club, online, texto) == esperado


# ------------------------------------------------ con datos (DuckDB falso) ---

def _con_filas(filas_buscable=(), filas_diario=(), filas_grupos=()):
    """Un DuckDB con la forma de `buscable`, `diario` y `grupos`, sin PostgreSQL.

    Las columnas son las que usa la consulta de verdad, ni una mas: si la
    consulta pide otra, la prueba se entera aqui y no en produccion. Y
    `promo_hasta` vive en `grupos` y no en `buscable` -- que es como esta en gold,
    y por eso la consulta la lee de alli.
    """
    con = duckdb.connect(":memory:")
    con.execute("""
        CREATE TABLE buscable (
            grupo_id BIGINT, fuente VARCHAR, id_fuente VARCHAR, nombre VARCHAR,
            marca VARCHAR, imagen VARCHAR, unidad_canon VARCHAR, promo_txt VARCHAR,
            promo_club BOOLEAN, promo_solo_online BOOLEAN)
    """)
    con.execute("""
        CREATE TABLE diario (fuente VARCHAR, id_fuente VARCHAR, fecha VARCHAR,
                             precio_cent BIGINT)
    """)
    con.execute("""
        CREATE TABLE grupos (fuente VARCHAR, id_fuente VARCHAR, promo_hasta TIMESTAMPTZ)
    """)
    for fila in filas_buscable:
        con.execute("INSERT INTO buscable VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", fila)
    for fila in filas_diario:
        con.execute("INSERT INTO diario VALUES (?, ?, ?, ?)", fila)
    for fila in filas_grupos:
        con.execute("INSERT INTO grupos VALUES (?, ?, ?)", fila)
    return con


def _oferta(grupo, fuente, id_fuente, nombre, promo, precio, *, club=False, online=False,
            hasta=None, unidad="ud", marca=None):
    return ((grupo, fuente, id_fuente, nombre, marca or fuente.upper(), None, unidad, promo,
             club, online),
            (fuente, id_fuente, "2026-11-06", precio),
            (fuente, id_fuente, hasta))


def test_sin_gold_no_revienta_y_contesta_vacio(monkeypatch):
    """Un gold vacio no es un fallo: es que hoy no hay ofertas, y se dice."""
    monkeypatch.setattr(catalogo, "conexion", lambda: _con_filas())
    assert movimientos.ofertas() == []


def test_las_ofertas_salen_con_el_precio_de_hoy_y_sin_precio_final(monkeypatch):
    """La oferta es informativa: el precio es el de hoy y no se resta nada.

    Lo que no puede aparecer es un campo con el precio "de after" o el ahorro:
    no lo sabemos -- un 3x2 no baja el precio de una unidad -- y la pantalla que
    lo pintara estaria inventando.
    """
    datos = _oferta(7, "dia", "111", "Pizza 4 quesos 400 g", "20% DTO.", 207, club=True,
                    hasta="2026-11-18 23:59:00+00")
    monkeypatch.setattr(catalogo, "conexion",
                        lambda: _con_filas([datos[0]], [datos[1]], [datos[2]]))

    (oferta,) = movimientos.ofertas()
    assert oferta["precio_cent"] == 207, "el precio es el de hoy, no uno calculado"
    assert oferta["tipo"] == "descuento"
    assert oferta["exige_club"] is True and oferta["solo_online"] is False
    assert oferta["condicion"] == "Con tarjeta DIA"
    assert oferta["unidad"] == "ud"
    # *La fecha de fin se lee en UTC: a las 23:59 UTC del 18 en Madrid ya es dia 19.*
    assert oferta["hasta"] == "2026-11-18"
    assert "precio_final_cent" not in oferta and "ahorro_cent" not in oferta
    # Las claves que la ficha necesita para enlazar y para pintar.
    assert {"grupo_id", "cadena", "nombre", "marca", "id_fuente", "promo_txt",
            "hasta"} <= set(oferta)


def test_ordena_por_relevancia_y_no_repite_el_mismo_producto(monkeypatch):
    """Primero lo que baja el precio, luego el club, luego las etiquetas.

    Y el mismo producto dos veces -- dos `id_fuente` de la misma cadena con el
    mismo nombre y el mismo precio -- es una fila, no dos.
    """
    filas = [
        _oferta(1, "alcampo", "a1", "Anchoa al vinagre", "2ª ud -50%. Solo Online", 406,
                club=True, online=True),
        _oferta(2, "dia", "d1", "Pizza 4 quesos", "20% DTO.", 207, club=True),
        _oferta(3, "aldi", "b1", "Cápsulas de café", "2ª ud al -50%", 247),
        _oferta(4, "dia", "d2", "Turrones", "3x2", 150, club=True),
        _oferta(5, "lidl", "l1", "Yogur griego fresa", "Precio condicionado a Lidl Plus", 135,
                club=True),
        _oferta(6, "carrefour", "c1", "Envío a casa", "Envío Gratis", 500),
        # El mismo producto, dos identificadores de la cadena.
        _oferta(7, "aldi", "b2", "Cápsulas de café", "2ª ud al -50%", 247),
    ]
    monkeypatch.setattr(catalogo, "conexion",
                        lambda: _con_filas([f[0] for f in filas], [f[1] for f in filas],
                                           [f[2] for f in filas]))

    lista = movimientos.ofertas(limite=50)
    assert [o["nombre"] for o in lista] == [
        "Pizza 4 quesos",              # descuento y con club
        "Cápsulas de café",            # 2ª unidad sin club
        "Turrones",                    # 3x2
        "Yogur griego fresa",          # precio club, sin mecanica
        "Envío a casa",                # etiqueta: no es una oferta de precio
        # *Y la segunda de 2ª unidad, que es online, detras: dentro de su tipo el
        # orden es club primero, tienda antes que internet y lo mas barato antes.*
        "Anchoa al vinagre",
    ]
    assert len(lista) == 6, "el mismo producto con dos ids no son dos ofertas"


def test_los_filtros_de_los_chips_llegan_a_la_consulta(monkeypatch):
    """El chip de «Club» filtra por condicion, no por tipo: es lo que se pulsa."""
    filas = [
        _oferta(1, "dia", "d1", "Pizza", "20% DTO.", 207, club=True),
        _oferta(2, "aldi", "b1", "Café", "-14%", 247),
        _oferta(3, "alcampo", "a1", "Anchoa", "2ª ud -50%. Solo Online", 406, online=True),
        _oferta(4, "dia", "d2", "Turrones", "3x2", 150),
    ]
    monkeypatch.setattr(catalogo, "conexion",
                        lambda: _con_filas([f[0] for f in filas], [f[1] for f in filas],
                                           [f[2] for f in filas]))

    assert {o["nombre"] for o in movimientos.ofertas(club=True)} == {"Pizza"}
    assert {o["nombre"] for o in movimientos.ofertas(solo_online=True)} == {"Anchoa"}
    assert {o["nombre"] for o in movimientos.ofertas(tipos=["descuento"])} == {"Pizza", "Café"}
    # *`cadenas` filtra en el SQL, no recortando la respuesta ya limitada.*
    assert {o["cadena"] for o in movimientos.ofertas(cadenas=["dia"])} == {"dia"}
    # «2ª unidad» incluye el 3x2: es la misma pregunta -- cuantas unidades.
    assert {o["nombre"] for o in movimientos.ofertas(
        tipos=["segunda_unidad", "3x2"])} == {"Anchoa", "Turrones"}
    # Y el limite se respeta despues de filtrar.
    assert len(movimientos.ofertas(limite=1)) == 1


# ------------------------------------------------------------- el endpoint ---

OFERTA = {
    "grupo_id": 1, "cadena": "lidl", "nombre": "Yogur griego de fresa", "marca": "LIDL",
    "id_fuente": "111", "imagen": None, "precio_cent": 135, "unidad": "kg",
    "promo_txt": "Precio condicionado a Lidl Plus", "tipo": "club",
    "exige_club": True, "solo_online": False, "condicion": "Con Lidl Plus",
    "hasta": "2026-11-18",
}


def test_el_endpoint_contesta_sin_sesion_y_pasa_los_filtros(monkeypatch):
    pedido: dict = {}

    def ofertas(limite=60, cadenas=None, tipos=None, club=False, solo_online=False):
        pedido.update({"limite": limite, "cadenas": cadenas, "tipos": tipos,
                       "club": club, "solo_online": solo_online})
        return [OFERTA]

    monkeypatch.setattr(movimientos, "ofertas", ofertas)
    monkeypatch.setattr(catalogo, "fecha_de_gold", lambda: "2026-11-06")

    # Sin cabecera de sesion: las ofertas son publicas.
    r = TestClient(main.app).get(
        "/api/ofertas?limite=5&cadenas=dia,aldi&tipos=descuento,3x2&club=true&solo_online=true")
    assert r.status_code == 200, r.text
    assert pedido == {"limite": 5, "cadenas": ["dia", "aldi"],
                      "tipos": ["descuento", "3x2"], "club": True, "solo_online": True}
    assert r.json() == {"fecha_datos": "2026-11-06", "resultados": [OFERTA]}


def test_sin_ofertas_el_endpoint_contesta_200_y_una_lista_vacia(monkeypatch):
    monkeypatch.setattr(movimientos, "ofertas", lambda *a, **k: [])
    monkeypatch.setattr(catalogo, "fecha_de_gold", lambda: "2026-11-06")
    r = TestClient(main.app).get("/api/ofertas")
    assert r.status_code == 200, r.text
    assert r.json() == {"fecha_datos": "2026-11-06", "resultados": []}


def test_la_ruta_esta_montada_de_verdad():
    """«La funcion existe» y «el endpoint se alcanza» son dos cosas distintas."""
    assert "/api/ofertas" in set(main.app.openapi()["paths"])
