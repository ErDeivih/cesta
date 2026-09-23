"""Los avisos, de punta a punta: la campana, la pantalla y el punto del icono.

El punto 6 del encargo tenia dos mitades. La de dentro -- **que la alerta salte sin que
nadie abra nada** -- se arreglo con el vigilante de la API (`api/vigilante.py`, y sus
pruebas en `test_vigilante.py`). Esta es la de fuera, la que pedia el encargo con estas
palabras: *"un punto en el icono, y al abrirlo **la frase entera** --«el aceite que sigues
esta a 3,89 €/l en Alcampo, el mas barato en 90 dias»--, no un numero rojo sin contexto."*

Lo que se vigila aqui:

  - **Que una alerta diga DE QUE producto es.** Sin el nombre, la pantalla solo puede
    decir "producto", y un aviso que no dice de que es no es un aviso. La API anade la
    tarjeta del grupo, y si el grupo ya no esta en el catalogo **no la anade**: entonces
    no hay nombre que poner y la pantalla lo dice, en vez de inventarselo.
  - **Que la frase salga del servidor**, no de la pantalla: `por_que` para las que se
    cumplen hoy y `salto_texto` para las que saltaron. Recalcularla aqui daria una
    segunda version de la misma verdad, y la de la pantalla ensenaria otra cosa.
  - **Que el punto cuente lo que ha saltado**, no lo que hay: una alerta que existe y no
    se ha cumplido es una promesa. Y que se apague **a mano** (`POST /alertas/vistas`),
    porque abrir la pantalla en el autobus no puede dar por leido nada.
  - **Que la campana no sea un formulario**: pide el aviso util (`minimo_90d`) sin
    preguntar ningun numero, y sin sesion no se pinta.

El gold es de mentira y PostgreSQL se sustituye: una prueba que dependa del catalogo del
dia mide el calendario, no el codigo.
"""
from __future__ import annotations

import re
from dataclasses import replace
from pathlib import Path

import duckdb
import pytest
from fastapi.testclient import TestClient

from plataforma.api import almacen, catalogo, main

RAIZ = Path(__file__).resolve().parents[1]
SRC = RAIZ / "plataforma" / "web" / "app" / "src"
AVISOS = SRC / "paginas" / "Avisos.tsx"
CAMPANA = SRC / "componentes" / "Campana.tsx"
NAV = SRC / "componentes" / "Nav.tsx"
APP = SRC / "App.tsx"
GRUPO = SRC / "paginas" / "Grupo.tsx"

PRODUCTOS = [
    {"grupo_id": 10, "fuente": "aldi", "nombre": "Aceite de oliva virgen extra"},
]


def _leer(f: Path) -> str:
    if not f.exists():
        pytest.skip("esta copia no trae la interfaz nueva")
    return f.read_text(encoding="utf-8")


# ------------------------------------------------------------- el servidor ---

@pytest.fixture
def gold(tmp_path, monkeypatch):
    def escribe(productos=PRODUCTOS):
        con = duckdb.connect()
        con.execute("""CREATE TABLE g (
            grupo_id BIGINT, fuente VARCHAR, id_fuente VARCHAR, nombre VARCHAR,
            marca VARCHAR, cantidad DOUBLE, unidad_canon VARCHAR, precio_cent BIGINT,
            precio_unidad_cent DOUBLE, comparacion_fiable BOOLEAN, calidad VARCHAR,
            calidad_origen VARCHAR, nutriscore VARCHAR, nova BIGINT, ean VARCHAR,
            imagen VARCHAR, promo_txt VARCHAR)""")
        for i, p in enumerate(productos):
            con.execute("INSERT INTO g VALUES (?, ?, ?, ?, NULL, 1.0, 'l', 389, 389.0,"
                        " true, NULL, NULL, NULL, NULL, NULL, NULL, NULL)",
                        [p["grupo_id"], p["fuente"], str(i), p["nombre"]])
        con.execute(f"COPY g TO '{tmp_path / 'grupos.parquet'}' (FORMAT PARQUET)")
        # El derivado necesita sus columnas de verdad: `_mejor_de_cada_grupo` lee el
        # minimo de 90 dias, y un parquet con solo `fecha` tira un Binder Error.
        con.execute("CREATE TABLE d (fuente VARCHAR, id_fuente VARCHAR, "
                    "min_90d_cent DOUBLE, precio_base_cent BIGINT, fecha DATE)")
        con.execute("INSERT INTO d VALUES ('aldi', '0', 389.0, 389, DATE '2026-09-23')")
        con.execute(f"COPY d TO '{tmp_path / 'precio_derivado.parquet'}' "
                    f"(FORMAT PARQUET)")
        for otro in ("precio_diario", "enlaces", "resumen"):
            con.execute(f"COPY (SELECT DATE '2026-09-23' AS fecha) "
                        f"TO '{tmp_path / (otro + '.parquet')}' (FORMAT PARQUET)")
        con.close()
        catalogo.reiniciar()

    monkeypatch.setattr(catalogo, "AJUSTES", replace(catalogo.AJUSTES, gold=tmp_path))
    yield escribe
    catalogo.reiniciar()


def _alerta(grupo_id, **extra):
    base = {"id": "a1", "grupo_id": grupo_id, "tipo": "minimo_90d", "umbral_cent": None,
            "creada_en": "2026-09-20T10:00:00", "vista_en": None,
            "salto_en": "2026-09-23T06:12:00",
            "salto_texto": "esta al precio mas bajo de los ultimos 90 dias: 3,89 EUR/l"}
    return base | extra


def _cliente(monkeypatch, alertas_):
    monkeypatch.setattr(almacen, "alertas_de", lambda usuario_id: [dict(a) for a in alertas_])
    main.app.dependency_overrides[main.usuario_actual] = lambda: {
        "id": "u1", "usuario": "ana", "nombre": "Ana"}
    return TestClient(main.app)


def test_la_alerta_dice_de_que_producto_es(gold, monkeypatch):
    """`GET /api/alertas` anade la tarjeta del grupo: nombre, precio y unidad."""
    gold()
    cliente = _cliente(monkeypatch, [_alerta(10)])
    r = cliente.get("/api/alertas")
    main.app.dependency_overrides.clear()
    assert r.status_code == 200, r.text
    alerta = r.json()["alertas"][0]
    assert alerta["nombre"] == "Aceite de oliva virgen extra", \
        "una alerta sin nombre: la pantalla solo puede decir 'producto'"
    assert alerta["precio_unidad_cent"] == 389.0
    assert alerta["unidad"] == "l"
    # Y la frase guardada viaja tal cual: la pantalla no la recalcula.
    assert alerta["salto_texto"].startswith("esta al precio mas bajo")
    assert alerta["salto_en"] and alerta["vista_en"] is None


def test_un_grupo_que_ya_no_esta_no_se_inventa_un_nombre(gold, monkeypatch):
    """Si el emparejador se rehizo y ese grupo no es de hoy, no hay tarjeta."""
    gold()
    cliente = _cliente(monkeypatch, [_alerta(999999)])
    r = cliente.get("/api/alertas")
    main.app.dependency_overrides.clear()
    alerta = r.json()["alertas"][0]
    assert "nombre" not in alerta, \
        "un grupo que no esta en gold no puede llevar nombre: no lo sabemos"
    # Y la alerta sigue estando: el aviso existio, aunque el producto ya no se venda.
    assert alerta["salto_en"]


# --------------------------------------------------------------- la pantalla ---

def test_la_frase_viene_del_servidor_y_no_se_recalcula():
    avisos = _leer(AVISOS)
    assert "s.por_que" in avisos, "las que se cumplen hoy tienen que usar la frase del servidor"
    assert "a.salto_texto" in avisos, \
        "las que saltaron guardan su frase: se midio contra el gold de ese dia, y gold " \
        "es otro cada manana"
    # Nada de montar la frase aqui con precios: eso seria una segunda version de la
    # misma verdad, y la de la pantalla ensenaria otra cosa.
    for prohibido in ("precio_unidad_antes", "ha bajado un ", "más barato que en"):
        assert prohibido not in avisos, f"la pantalla esta escribiendo la frase ({prohibido})"


def test_el_punto_cuenta_lo_que_ha_saltado_y_se_apaga_a_mano():
    nav = _leer(NAV)
    assert "useAvisosSinVer" in nav and "sinVer > 0" in nav, \
        "el punto del icono tiene que salir solo cuando hay algo que ver"
    assert "aria-hidden" in nav and "sr-only" in nav, \
        "un punto no dice cuanto: hace falta el numero, y para quien no ve el color"
    avisos = _leer(AVISOS)
    assert "marcarVistas" in avisos and "Ya los he visto" in avisos, \
        "el punto no puede apagarse solo por abrir la pantalla"
    assert "vista_en" in avisos, "lo que se apaga es `vista_en`, no `salto_en`"


def test_la_campana_pide_el_aviso_util_sin_preguntar_nada():
    campana = _leer(CAMPANA)
    assert "crearAlerta(grupoId)" in campana, \
        "la campana tiene que poder pedir el aviso, o la pantalla estara vacia siempre"
    assert "minimo_90d" in _leer(SRC / "api" / "alertas.ts"), \
        "el tipo por defecto es el que no exige saber cuanto deberia costar algo"
    for prohibido in ("umbral_cent:", "Selector", "prompt(", "confirm(", "<input"):
        assert prohibido not in campana, \
            f"la campana no puede pedir numeros ni abrir un dialogo ({prohibido})"
    assert "sesion.data?.usuario" in campana and "return null" in campana, \
        "sin sesion no hay campana: no se puede guardar una alerta sin saber de quien es"


def test_la_campana_esta_en_la_ficha_y_la_pantalla_en_la_navegacion():
    grupo = _leer(GRUPO)
    assert "<Campana grupoId={id} />" in grupo, \
        "la campana tiene que estar en la ficha del producto, que es donde se decide"
    app = _leer(APP)
    assert re.search(r"path=\"/avisos\"", app), "la pantalla de avisos no tiene ruta"
    assert "Avisos" in app, "la ruta no tiene titulo en la pestana"
    nav = _leer(NAV)
    assert "{ a: '/avisos'" in nav, "la pantalla no esta en la barra de abajo"
