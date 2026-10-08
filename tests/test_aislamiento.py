"""Aislamiento por usuario: endpoints reales, dos cuentas, y la migracion de los registros antiguos.

Se llama a la aplicacion **montada** con `TestClient`, que es el patron que ya usa el proyecto. La sesion
se sustituye con `dependency_overrides` -- que es el punto de sustitucion que el proyecto ya usa -- y
**no** se sustituye en la prueba del anonimo: ahi se comprueba que la puerta de verdad corta.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from core import diario
from plataforma.api import diario as api_diario
from plataforma.api import main, sesion

ANA = {"id": "ana", "usuario": "ana", "nombre": "Ana"}
LUIS = {"id": "luis", "usuario": "luis", "nombre": "Luis"}


@pytest.fixture(autouse=True)
def base_limpia(tmp_path):
    """Cada prueba con su fichero: el diario de verdad no se toca."""
    api_diario.ruta_base(tmp_path / "diario.sqlite")
    yield
    main.app.dependency_overrides.clear()


def como(quien: dict | None):
    """Un cliente de la aplicacion **real**, con la sesion de quien se diga."""
    main.app.dependency_overrides.clear()
    if quien is not None:
        main.app.dependency_overrides[sesion.usuario_actual] = lambda: quien
    return TestClient(main.app)


def apuntar(cliente, kcal=500, comida="comida", fecha="2026-10-07"):
    return cliente.post("/api/diario", json={
        "fecha": fecha, "comida": comida, "tipo": "alimento", "kcal": kcal,
        "fuente_dato": "etiqueta"})


# --------------------------------------------------------------- la puerta: 401
def test_un_anonimo_no_entra_en_el_diario():
    """La prueba que retire la ronda pasada porque salia roja. Ahora pasa porque hay proteccion."""
    r = como(None).get("/api/diario/2026-10-07")
    assert r.status_code == 401, r.text
    assert "entrar" in r.json()["detail"].lower()


def test_un_anonimo_tampoco_puede_apuntar_ni_borrar_ni_ver_el_rango():
    cliente = como(None)
    assert cliente.post("/api/diario", json={"fecha": "2026-10-07", "comida": "comida"}).status_code == 401
    assert cliente.delete("/api/diario/entrada/1").status_code == 401
    assert cliente.get("/api/diario/rango?desde=2026-10-01&hasta=2026-10-07").status_code == 401


# --------------------------------------------------------------- B contra A
def test_b_no_ve_el_dia_de_a():
    ana = como(ANA)
    assert apuntar(ana, kcal=500).status_code == 201
    luis = como(LUIS)
    dia = luis.get("/api/diario/2026-10-07").json()
    assert dia["entradas"] == [], "el diario de A no puede aparecer en el de B"
    assert dia["conocido"]["kcal"] is None


def test_b_no_puede_borrar_una_entrada_de_a_ni_adivinando_el_identificador():
    ana = como(ANA)
    creada = apuntar(ana, kcal=500).json()
    identificador = creada["id"]
    luis = como(LUIS)
    r = luis.delete(f"/api/diario/entrada/{identificador}")
    assert r.status_code == 404, "404 y no 403: un 403 confirmaria que existe y es de otro"
    # Y sigue estando para su dueno.
    assert len(como(ANA).get("/api/diario/2026-10-07").json()["entradas"]) == 1


def test_el_rango_de_b_no_cuenta_lo_de_a():
    apuntar(como(ANA), kcal=500)
    dias = como(LUIS).get("/api/diario/rango?desde=2026-10-01&hasta=2026-10-07").json()["dias"]
    assert dias == []
    propios = como(ANA).get("/api/diario/rango?desde=2026-10-01&hasta=2026-10-07").json()["dias"]
    assert len(propios) == 1 and propios[0]["kcal_conocida"] == 500


# --------------------------------------------------------------- el propietario no se dicta
def test_el_propietario_no_se_puede_pedir_en_el_cuerpo():
    """Si el dueno pudiera venir en el JSON, el aislamiento seria decorativo."""
    r = como(LUIS).post("/api/diario", json={
        "fecha": "2026-10-07", "comida": "comida", "kcal": 400, "fuente_dato": "etiqueta",
        "propietario": "ana", "usuario": "ana", "id": "ana"})
    assert r.status_code == 201, "el campo de mas no rompe: simplemente se ignora"
    # Lo que importa: la entrada es de Luis, no de Ana.
    assert como(ANA).get("/api/diario/2026-10-07").json()["entradas"] == []
    assert len(como(LUIS).get("/api/diario/2026-10-07").json()["entradas"]) == 1


# --------------------------------------------------------------- la migracion
def _base_vieja(ruta: Path) -> None:
    """Una base como la de antes del aislamiento: sin columna de propietario, con una entrada dentro."""
    con = sqlite3.connect(ruta)
    con.executescript("""
        CREATE TABLE entrada (
            id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT NOT NULL, comida TEXT NOT NULL,
            tipo TEXT NOT NULL, referencia TEXT, version TEXT, cantidad_g REAL, unidad TEXT,
            kcal REAL, proteinas_g REAL, grasas_g REAL, hidratos_g REAL,
            fuente_dato TEXT NOT NULL, nota TEXT, creada TEXT NOT NULL);
        INSERT INTO entrada (fecha, comida, tipo, kcal, fuente_dato, creada)
        VALUES ('2026-01-02', 'comida', 'alimento', 700, 'etiqueta', '2026-01-02T14:00:00');
    """)
    con.commit()
    con.close()


def test_la_migracion_conserva_lo_historico_sin_asignarselo_a_nadie(tmp_path):
    """El registro viejo sigue ahi, no aparece para nadie y **no se le da dueno por conveniencia**."""
    ruta = tmp_path / "diario.sqlite"
    _base_vieja(ruta)

    con = diario.conecta(ruta)                    # migra al abrir
    fila = con.execute("SELECT propietario, kcal FROM entrada").fetchone()
    assert fila["propietario"] is None, "no se le asigna dueno: no se sabe de quien es"
    assert fila["kcal"] == 700, "y no se pierde el dato"

    # Inaccesible para cualquiera, incluido el que acaba de entrar.
    assert diario.dia(con, "ana", "2026-01-02")["entradas"] == []
    assert diario.dia(con, "luis", "2026-01-02")["entradas"] == []
    assert diario.rango(con, "ana", "2026-01-01", "2026-01-31") == []
    # Y tampoco se puede borrar por identificador.
    assert diario.borrar(con, "ana", 1) is False
    assert con.execute("SELECT count(*) FROM entrada").fetchone()[0] == 1
    con.close()


def test_migrar_dos_veces_no_cambia_nada(tmp_path):
    """Repetir la migracion no puede duplicar columnas ni tocar los registros."""
    ruta = tmp_path / "diario.sqlite"
    _base_vieja(ruta)
    for _ in range(3):
        con = diario.conecta(ruta)
        columnas = [f[1] for f in con.execute("PRAGMA table_info(entrada)").fetchall()]
        assert columnas.count("propietario") == 1
        assert con.execute("SELECT count(*) FROM entrada").fetchone()[0] == 1
        assert con.execute("SELECT propietario FROM entrada").fetchone()[0] is None
        con.close()


def test_lo_nuevo_si_lleva_dueno_desde_el_principio(tmp_path):
    con = diario.conecta(tmp_path / "diario.sqlite")
    diario.apunta(con, "ana", "2026-10-07", "comida", kcal=300, fuente_dato=diario.ETIQUETA)
    assert con.execute("SELECT propietario FROM entrada").fetchone()[0] == "ana"
    con.close()
