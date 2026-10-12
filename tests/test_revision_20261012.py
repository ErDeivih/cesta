"""Regresiones de la revision: cantidades finitas, conversion y estado del catalogo."""
import duckdb
import pytest
from fastapi.testclient import TestClient

from core.previa_compra import previa_de_compra
from plataforma.api import main
from projects.cesta import run


@pytest.mark.parametrize("cantidad", [True, float("nan"), float("inf"), -float("inf")])
def test_no_se_compra_una_cantidad_no_valida(cantidad):
    previa = previa_de_compra([{"texto": "harina", "cantidad": cantidad, "unidad": "g"}])
    assert previa.lineas == []
    assert previa.sin_cantidad == ["harina"]


def test_volumen_compatible_sin_convertir_masa():
    previa = previa_de_compra([
        {"texto": "leche", "cantidad": 250, "unidad": "ml"},
        {"texto": "leche", "cantidad": 1, "unidad": "l"},
    ])
    assert len(previa.lineas) == 1
    assert (previa.lineas[0].cantidad, previa.lineas[0].unidad) == (1.25, "l")
    assert not previa.sin_consolidar


def test_estado_cuenta_productos_distintos_del_ultimo_dia_por_cadena(monkeypatch):
    con = duckdb.connect(":memory:")
    con.execute("""
        CREATE TABLE diario (fuente VARCHAR, id_fuente VARCHAR, fecha DATE);
        INSERT INTO diario VALUES
            ('dia', 'viejo', '2026-10-10'), ('dia', 'a', '2026-10-11'),
            ('dia', 'b', '2026-10-11'), ('dia', 'b', '2026-10-11'),
            ('aldi', 'c', '2026-10-10'), ('aldi', 'd', '2026-10-09');
    """)
    monkeypatch.setattr(main.catalogo, "conexion", lambda: con)
    monkeypatch.setattr(main.catalogo, "fecha_de_gold", lambda: "2026-10-11")
    monkeypatch.setattr(main, "_version_del_catalogo", lambda: "ensayo")
    monkeypatch.setattr(main, "_vigencia_del_catalogo", lambda: {})
    try:
        cliente = TestClient(main.app)
        respuesta = cliente.get("/api/estado")
        assert respuesta.status_code == 200
        assert respuesta.json()["cadenas"] == [
            {"cadena": "aldi", "productos": 1, "ultimo_dia": "2026-10-10", "al_dia": False},
            {"cadena": "dia", "productos": 2, "ultimo_dia": "2026-10-11", "al_dia": True},
        ]
    finally:
        con.close()


def test_la_paginacion_llega_desde_http_al_catalogo(monkeypatch):
    recibidos = []

    def busca(*args, **kwargs):
        recibidos.append(kwargs["desplazamiento"])
        return [{"grupo_id": 42}]

    monkeypatch.setattr(main.catalogo, "buscar", busca)
    monkeypatch.setattr(main.catalogo, "fecha_de_gold", lambda: "2026-10-11")
    cliente = TestClient(main.app)
    assert cliente.get("/api/buscar?q=leche&desplazamiento=40").status_code == 200
    assert cliente.get("/api/buscar?q=leche").status_code == 200
    assert cliente.get("/api/buscar?q=leche&desplazamiento=-1").status_code == 422
    assert recibidos == [40, 0]


def test_un_colector_con_cli_incompatible_no_termina_el_ejecutor(monkeypatch):
    from types import SimpleNamespace

    def colector():
        raise SystemExit(2)

    monkeypatch.setattr(run.importlib, "import_module", lambda nombre: SimpleNamespace(main=colector))
    nombre, bien, _ = run._una_cadena("lidl")
    assert nombre == "lidl"
    assert bien is False
