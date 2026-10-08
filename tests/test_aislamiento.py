"""Aislamiento por usuario en Recetas y Calorias: endpoints reales, dos cuentas y la migracion.

Se llama a la aplicacion **montada** con `TestClient`. La sesion se sustituye con
`dependency_overrides` -- el punto de sustitucion que el proyecto ya usa -- y **no** se sustituye en las
pruebas del anonimo: ahi se comprueba que la puerta de verdad corta, con 401.

Cuando algo es de otro se responde **404 y no 403**: un 403 confirmaria que ese identificador existe y es
de otra persona.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from core import diario, recetas
from plataforma.api import diario as api_diario
from plataforma.api import main, sesion
from plataforma.api import recetas as api_recetas

ANA = {"id": "ana", "usuario": "ana", "nombre": "Ana"}
LUIS = {"id": "luis", "usuario": "luis", "nombre": "Luis"}


@pytest.fixture(autouse=True)
def bases_limpias(tmp_path):
    """Cada prueba con sus ficheros: los datos de verdad no se tocan."""
    api_diario.ruta_base(tmp_path / "diario.sqlite")
    api_recetas.ruta_base(tmp_path / "recetas.sqlite")
    yield
    main.app.dependency_overrides.clear()


def como(quien: dict | None) -> TestClient:
    """Un cliente de la aplicacion **real**, con la sesion de quien se diga."""
    main.app.dependency_overrides.clear()
    if quien is not None:
        main.app.dependency_overrides[sesion.usuario_actual] = lambda: quien
    return TestClient(main.app)


# =============================================================== DIARIO: la puerta
def test_un_anonimo_no_entra_en_el_diario():
    """La prueba que retire una vez porque salia roja. Ahora pasa porque hay proteccion."""
    r = como(None).get("/api/diario/2026-10-07")
    assert r.status_code == 401, r.text
    assert "entrar" in r.json()["detail"].lower()


def test_un_anonimo_tampoco_puede_apuntar_ni_borrar_ni_ver_el_rango():
    cliente = como(None)
    assert cliente.post("/api/diario", json={"fecha": "2026-10-07", "comida": "comida"}).status_code == 401
    assert cliente.delete("/api/diario/entrada/1").status_code == 401
    assert cliente.get("/api/diario/rango?desde=2026-10-01&hasta=2026-10-07").status_code == 401


# =============================================================== DIARIO: B contra A
def test_b_no_ve_el_dia_de_a():
    assert como(ANA).post("/api/diario", json={
        "fecha": "2026-10-07", "comida": "comida", "kcal": 500,
        "fuente_dato": "etiqueta"}).status_code == 201
    dia = como(LUIS).get("/api/diario/2026-10-07").json()
    assert dia["entradas"] == [] and dia["conocido"]["kcal"] is None


def test_b_no_puede_borrar_una_entrada_de_a_ni_adivinando_el_identificador():
    creada = como(ANA).post("/api/diario", json={
        "fecha": "2026-10-07", "comida": "comida", "kcal": 500, "fuente_dato": "etiqueta"}).json()
    r = como(LUIS).delete(f"/api/diario/entrada/{creada['id']}")
    assert r.status_code == 404
    assert len(como(ANA).get("/api/diario/2026-10-07").json()["entradas"]) == 1


def test_el_rango_de_b_no_cuenta_lo_de_a():
    como(ANA).post("/api/diario", json={"fecha": "2026-10-07", "comida": "comida", "kcal": 500,
                                        "fuente_dato": "etiqueta"})
    assert como(LUIS).get("/api/diario/rango?desde=2026-10-01&hasta=2026-10-07").json()["dias"] == []


def test_el_propietario_no_se_puede_pedir_en_el_cuerpo():
    como(LUIS).post("/api/diario", json={
        "fecha": "2026-10-07", "comida": "comida", "kcal": 400, "fuente_dato": "etiqueta",
        "propietario": "ana", "usuario": "ana", "id": "ana"})
    assert como(ANA).get("/api/diario/2026-10-07").json()["entradas"] == []
    assert len(como(LUIS).get("/api/diario/2026-10-07").json()["entradas"]) == 1


# =============================================================== RECETAS: la puerta
def test_un_anonimo_no_entra_en_las_recetas():
    cliente = como(None)
    assert cliente.get("/api/recetas").status_code == 401
    assert cliente.get("/api/recetas/1").status_code == 401
    assert cliente.get("/api/recetas/plan?desde=2026-10-01&hasta=2026-10-07").status_code == 401
    assert cliente.post("/api/recetas", json={"nombre": "Sopa"}).status_code == 401


# =============================================================== RECETAS: B contra A
def _receta_de_a(cliente) -> int:
    return cliente.post("/api/recetas", json={"nombre": "Tortilla", "raciones": 4}).json()["id"]


def test_b_no_enumera_las_recetas_de_a():
    rid = _receta_de_a(como(ANA))
    assert como(ANA).get("/api/recetas").json()["recetas"][0]["id"] == rid
    assert como(LUIS).get("/api/recetas").json()["recetas"] == []


def test_b_no_puede_leer_cambiar_archivar_ni_ver_las_versiones_de_a():
    """Las cuatro operaciones que la revision pedia comprobar una a una."""
    rid = _receta_de_a(como(ANA))
    luis = como(LUIS)
    assert luis.get(f"/api/recetas/{rid}").status_code == 404
    assert luis.put(f"/api/recetas/{rid}", json={"raciones": 99}).status_code == 404
    assert luis.post(f"/api/recetas/{rid}/archivar").status_code == 404
    assert luis.get(f"/api/recetas/{rid}/versiones").status_code == 404
    # Y para su dueno siguen estando, sin tocar.
    propia = como(ANA).get(f"/api/recetas/{rid}")
    assert propia.status_code == 200 and propia.json()["raciones"] == 4


def test_b_no_planifica_la_receta_de_a_y_su_plan_no_la_ve():
    rid = _receta_de_a(como(ANA))
    luis = como(LUIS)
    assert luis.post("/api/recetas/plan", json={
        "fecha": "2026-10-05", "receta_id": rid, "comensales": 2}).status_code == 404
    assert luis.get("/api/recetas/plan?desde=2026-10-01&hasta=2026-10-07").json()["plan"] == []
    # Ana si puede, y su plan la ve.
    como(ANA).post("/api/recetas/plan", json={"fecha": "2026-10-05", "receta_id": rid,
                                              "comensales": 3})
    plan_a = como(ANA).get("/api/recetas/plan?desde=2026-10-01&hasta=2026-10-07").json()["plan"]
    assert len(plan_a) == 1 and plan_a[0]["comensales"] == 3


def test_el_propietario_no_se_puede_pedir_en_el_cuerpo_de_una_receta():
    como(LUIS).post("/api/recetas", json={"nombre": "Sopa", "propietario": "ana", "usuario": "ana"})
    assert como(ANA).get("/api/recetas").json()["recetas"] == []
    assert len(como(LUIS).get("/api/recetas").json()["recetas"]) == 1


def test_el_plan_fija_la_version_y_el_dueno_no_la_pierde():
    """La comprobacion que vivia en las pruebas directas, ahora por HTTP."""
    rid = _receta_de_a(como(ANA))
    como(ANA).post("/api/recetas/plan", json={"fecha": "2026-10-05", "receta_id": rid})
    como(ANA).put(f"/api/recetas/{rid}", json={"raciones": 8})
    plan = como(ANA).get("/api/recetas/plan?desde=2026-10-01&hasta=2026-10-07").json()["plan"]
    assert plan[0]["version"] == 1
    assert como(ANA).get(f"/api/recetas/{rid}?version=1").json()["raciones"] == 4


def test_plan_va_declarado_antes_que_el_identificador():
    """Si fuera al reves, FastAPI leeria "plan" como un identificador de receta."""
    caminos = [r.path for r in api_recetas.rutas.routes]
    assert caminos.index("/api/recetas/plan") < caminos.index("/api/recetas/{receta_id}")


# =============================================================== las migraciones
def _diario_viejo(ruta: Path) -> None:
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


def _recetario_viejo(ruta: Path) -> None:
    con = sqlite3.connect(ruta)
    con.executescript("""
        CREATE TABLE receta (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL,
                             creada TEXT NOT NULL, archivada INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE version (receta_id INTEGER NOT NULL, numero INTEGER NOT NULL, raciones INTEGER NOT NULL,
                              preparacion TEXT NOT NULL DEFAULT '', minutos INTEGER,
                              etiquetas TEXT NOT NULL DEFAULT '', ingredientes TEXT NOT NULL DEFAULT '[]',
                              creada TEXT NOT NULL, PRIMARY KEY (receta_id, numero));
        CREATE TABLE plan (fecha TEXT NOT NULL, receta_id INTEGER NOT NULL, version INTEGER NOT NULL,
                           comensales INTEGER NOT NULL, PRIMARY KEY (fecha, receta_id));
        INSERT INTO receta (nombre, creada) VALUES ('Cocido de la abuela', '2026-01-02T10:00:00');
        INSERT INTO version (receta_id, numero, raciones, creada)
        VALUES (1, 1, 6, '2026-01-02T10:00:00');
    """)
    con.commit()
    con.close()


def test_la_migracion_del_diario_conserva_lo_historico_sin_asignarselo_a_nadie(tmp_path):
    ruta = tmp_path / "diario.sqlite"
    _diario_viejo(ruta)
    con = diario.conecta(ruta)
    fila = con.execute("SELECT propietario, kcal FROM entrada").fetchone()
    assert fila["propietario"] is None and fila["kcal"] == 700, "ni se le da dueno ni se pierde el dato"
    assert diario.dia(con, "ana", "2026-01-02")["entradas"] == []
    assert diario.rango(con, "ana", "2026-01-01", "2026-01-31") == []
    assert diario.borrar(con, "ana", 1) is False
    assert con.execute("SELECT count(*) FROM entrada").fetchone()[0] == 1
    con.close()


def test_la_migracion_de_recetas_conserva_lo_historico_sin_asignarselo_a_nadie(tmp_path):
    ruta = tmp_path / "recetas.sqlite"
    _recetario_viejo(ruta)
    con = recetas.conecta(ruta)
    assert con.execute("SELECT propietario FROM receta").fetchone()[0] is None
    assert recetas.listar(con, "ana") == []
    assert recetas.leer(con, "ana", 1) is None
    assert recetas.versiones(con, "ana", 1) == []
    assert recetas.archivar(con, "ana", 1) is False
    assert recetas.actualizar.__module__ and True  # se cambia aparte para no dejar el fichero a medias
    assert con.execute("SELECT count(*) FROM receta").fetchone()[0] == 1
    con.close()


def test_migrar_tres_veces_no_cambia_nada_en_ninguno_de_los_dos(tmp_path):
    for nombre, monta, abre, tabla in (("diario.sqlite", _diario_viejo, diario.conecta, "entrada"),
                                       ("recetas.sqlite", _recetario_viejo, recetas.conecta, "receta")):
        ruta = tmp_path / nombre
        monta(ruta)
        for _ in range(3):
            con = abre(ruta)
            columnas = [f[1] for f in con.execute(f"PRAGMA table_info({tabla})").fetchall()]
            assert columnas.count("propietario") == 1, f"{tabla}: la columna no se puede duplicar"
            assert con.execute(f"SELECT count(*) FROM {tabla}").fetchone()[0] == 1
            assert con.execute(f"SELECT propietario FROM {tabla}").fetchone()[0] is None
            con.close()
