"""G01 por HTTP montado: el recibo del alta, la cantidad y los macros, y la cobertura.

Lo que esta prueba añade a las que ya existen:

- `tests/test_g01_diario_aceptacion.py` comprueba el **almacén**.
- `tests/test_aislamiento.py` comprueba **la puerta** (401 anónimo, y que B no ve ni borra lo de A).
- Ésta comprueba **el contrato de la ruta**: que el alta devuelve recibo, que `cantidad_g` y los tres
  macronutrientes llegan y se vuelven a leer, y que el día dice la **cobertura por nutriente** — que
  es lo que impide leer el subtotal como el día entero.

Sigue el patrón del proyecto para la sesión (`dependency_overrides`, el punto de sustitución que ya
usa `test_aislamiento.py`), así que **no necesita PostgreSQL** y no registra cuentas reales.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from plataforma.api import diario as api_diario
from plataforma.api import main, sesion

ANA = {"id": "ana", "usuario": "ana", "nombre": "Ana"}
LUIS = {"id": "luis", "usuario": "luis", "nombre": "Luis"}

# El caso de aceptación del documento, tal cual: 200 kcal, 10 g proteína, 5 g grasa, 20 g hidratos
# por 100 g, y **150 g consumidos** -> 300, 15, 7,5 y 30.
DE_150_G = {"fecha": "2026-10-11", "comida": "comida", "tipo": "alimento", "referencia": "yogur",
            "cantidad_g": 150, "kcal": 300, "proteinas_g": 15, "grasas_g": 7.5, "hidratos_g": 30,
            "fuente_dato": "etiqueta", "nota": ""}


@pytest.fixture(autouse=True)
def bases_limpias(tmp_path):
    """Cada prueba con su fichero: **el diario de verdad no se toca**."""
    api_diario.ruta_base(tmp_path / "diario.sqlite")
    yield
    main.app.dependency_overrides.clear()
    api_diario.ruta_base(None)


def como(quien: dict | None) -> TestClient:
    """La aplicación real, con la sesión de quien se diga; `None` deja la puerta de verdad."""
    main.app.dependency_overrides.clear()
    if quien is not None:
        main.app.dependency_overrides[sesion.usuario_actual] = lambda: quien
    return TestClient(main.app)


# --- el recibo ---------------------------------------------------------------

def test_el_alta_devuelve_recibo_y_el_dia_calculado():
    """`{id, dia}`: el identificador **y** el día entero. Es lo que sostiene un mensaje de éxito."""
    r = como(ANA).post("/api/diario", json=DE_150_G)
    assert r.status_code == 201, r.text
    cuerpo = r.json()
    assert isinstance(cuerpo["id"], int), "el recibo trae el identificador"
    conocido = cuerpo["dia"]["conocido"]
    assert conocido["kcal"] == pytest.approx(300.0)
    assert conocido["proteinas_g"] == pytest.approx(15.0)
    assert conocido["grasas_g"] == pytest.approx(7.5)
    assert conocido["hidratos_g"] == pytest.approx(30.0)


def test_lo_que_se_graba_se_vuelve_a_leer_igual():
    """Persistencia: la recarga es una lectura nueva, no la memoria del navegador."""
    como(ANA).post("/api/diario", json=DE_150_G)
    dia = como(ANA).get("/api/diario/2026-10-11").json()
    assert len(dia["entradas"]) == 1
    entrada = dia["entradas"][0]
    assert entrada["cantidad_g"] == pytest.approx(150.0)
    assert entrada["kcal"] == pytest.approx(300.0)
    assert entrada["proteinas_g"] == pytest.approx(15.0)
    assert entrada["grasas_g"] == pytest.approx(7.5)
    assert entrada["hidratos_g"] == pytest.approx(30.0)
    assert entrada["fuente_dato"] == "etiqueta"
    assert entrada["referencia"] == "yogur"


def test_lo_que_no_se_sabe_no_viaja_como_cero():
    """Sin cantidad ni macros, el servidor guarda `null`, no `0`."""
    como(ANA).post("/api/diario", json={"fecha": "2026-10-11", "comida": "comida",
                                        "kcal": 100, "fuente_dato": "etiqueta"})
    entrada = como(ANA).get("/api/diario/2026-10-11").json()["entradas"][0]
    assert entrada["cantidad_g"] is None
    assert entrada["proteinas_g"] is None
    assert entrada["grasas_g"] is None
    assert entrada["hidratos_g"] is None


# --- la cobertura ------------------------------------------------------------

def test_la_cobertura_distingue_lo_que_se_sabe_de_lo_que_no():
    """Segunda entrada sin energía y con 12 g de proteína: 300 kcal, 27 g, y 1/2 frente a 2/2."""
    como(ANA).post("/api/diario", json=DE_150_G)
    como(ANA).post("/api/diario", json={
        "fecha": "2026-10-11", "comida": "merienda", "tipo": "alimento", "referencia": "nueces",
        "kcal": None, "proteinas_g": 12, "fuente_dato": "desconocido", "nota": ""})
    dia = como(ANA).get("/api/diario/2026-10-11").json()
    assert dia["conocido"]["kcal"] == pytest.approx(300.0), "la energía conocida no se inventa"
    assert dia["conocido"]["proteinas_g"] == pytest.approx(27.0)
    assert dia["cobertura"]["kcal"]["con_dato"] == 1 and dia["cobertura"]["kcal"]["total"] == 2
    assert dia["cobertura"]["kcal"]["completa"] is False
    assert dia["cobertura"]["proteinas_g"]["con_dato"] == 2
    assert dia["cobertura"]["proteinas_g"]["completa"] is True
    assert dia["completo"] is False, "el día no se presenta como completo"


def test_el_rango_refleja_lo_que_se_acaba_de_apuntar():
    """Las tendencias son otra consulta: tiene que ver el alta, no quedarse con el dato viejo."""
    como(ANA).post("/api/diario", json=DE_150_G)
    r = como(ANA).get("/api/diario/rango?desde=2026-10-11&hasta=2026-10-11")
    assert r.status_code == 200, r.text
    dias = {d["fecha"]: d for d in r.json()["dias"]}
    assert "2026-10-11" in dias, r.json()
    assert dias["2026-10-11"]["kcal_conocida"] == pytest.approx(300.0)


# --- lo que el servidor rechaza ----------------------------------------------

def test_un_valor_negativo_se_rechaza():
    """La validación vive en el servidor: el formulario no es la puerta."""
    r = como(ANA).post("/api/diario", json={"fecha": "2026-10-11", "comida": "comida", "kcal": -1})
    assert r.status_code in (400, 422), r.text


def test_una_compra_no_es_consumo():
    r = como(ANA).post("/api/diario", json={"fecha": "2026-10-11", "comida": "comida",
                                            "tipo": "compra", "kcal": 100})
    assert r.status_code == 400, r.text


def test_una_version_de_receta_inventada_no_se_anota():
    """Y el propietario sale de la sesión: una receta de otra persona tampoco."""
    r = como(ANA).post("/api/diario", json={"fecha": "2026-10-11", "comida": "comida",
                                            "tipo": "receta", "referencia": "999999",
                                            "kcal": 100})
    assert r.status_code == 400, r.text


# --- dos comidas legítimas ---------------------------------------------------

def test_dos_comidas_legitimas_iguales_se_registran_las_dos():
    """El documento lo pide al revés de como sale una deduplicación por descuido."""
    cuerpo = {"fecha": "2026-10-11", "comida": "merienda", "tipo": "alimento",
              "referencia": "yogur", "kcal": 100, "proteinas_g": 1, "fuente_dato": "etiqueta"}
    primera = como(ANA).post("/api/diario", json=cuerpo)
    segunda = como(ANA).post("/api/diario", json=cuerpo)
    assert primera.status_code == 201 and segunda.status_code == 201
    assert primera.json()["id"] != segunda.json()["id"], "son dos operaciones distintas"
    assert len(como(ANA).get("/api/diario/2026-10-11").json()["entradas"]) == 2


def test_borrar_una_deja_la_otra_y_el_dia_cuadrado():
    """Y el borrado devuelve recibo, no `undefined`."""
    como(ANA).post("/api/diario", json=DE_150_G)
    segunda = como(ANA).post("/api/diario", json={
        "fecha": "2026-10-11", "comida": "cena", "kcal": 100, "fuente_dato": "etiqueta"}).json()["id"]
    r = como(ANA).delete(f"/api/diario/entrada/{segunda}")
    assert r.status_code == 200 and r.json()["borrada"] == segunda
    dia = como(ANA).get("/api/diario/2026-10-11").json()
    assert len(dia["entradas"]) == 1
    assert dia["conocido"]["kcal"] == pytest.approx(300.0), "queda la que no se borró"


def test_la_misma_clave_por_http_no_duplica():
    """El camino completo: la clave viaja en el cuerpo y el servidor devuelve la misma entrada."""
    cuerpo = {"fecha": "2026-10-11", "comida": "comida", "tipo": "alimento",
              "referencia": "yogur", "kcal": 300, "fuente_dato": "etiqueta",
              "clave_operacion": "op-http-1"}
    primera = como(ANA).post("/api/diario", json=cuerpo)
    segunda = como(ANA).post("/api/diario", json=cuerpo)
    assert primera.status_code == 201 and segunda.status_code == 201
    assert primera.json()["id"] == segunda.json()["id"], "la misma operación, la misma entrada"
    assert len(como(ANA).get("/api/diario/2026-10-11").json()["entradas"]) == 1


def test_dos_claves_distintas_por_http_son_dos_entradas():
    for clave in ("op-http-2", "op-http-3"):
        r = como(ANA).post("/api/diario", json={
            "fecha": "2026-10-11", "comida": "merienda", "kcal": 100,
            "fuente_dato": "etiqueta", "clave_operacion": clave})
        assert r.status_code == 201, r.text
    assert len(como(ANA).get("/api/diario/2026-10-11").json()["entradas"]) == 2
