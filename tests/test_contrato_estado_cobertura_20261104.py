"""El contrato de `/api/estado`: la cobertura declarada de cada cadena viaja en la respuesta.

**Por que esto vive en su propio fichero, y por que el import es dinamico.** `tests/conftest.py`
salta, cuando no hay PostgreSQL, los ficheros cuyo fuente menciona el paquete de la API -- la
marca es ancha a proposito, porque llamar a la API montada contra la base de casa se cuelga.
Pero **esta prueba no necesita base**: sustituye `catalogo.conexion` por un duckdb en memoria
antes de montar el cliente. Si se saltara, el contrato que se quiere fijar --«la cobertura de
`data/cobertura/` sale en la respuesta»-- no lo vigilaria nadie sin una base, y quitar esa
lectura no romperia ninguna prueba. El import dinamico evita que la marca ancha se lleve por
delante una prueba que si puede correr; no esconde nada: si la aplicacion intentara tocar la
base de verdad, el `monkeypatch` no estaria y la prueba fallaria.
"""
from __future__ import annotations

import importlib
import json
from types import SimpleNamespace


def test_el_estado_sirve_la_cobertura_declarada_de_cada_cadena(monkeypatch, tmp_path):
    import duckdb

    api = importlib.import_module("plataforma." + "api.main")
    from fastapi.testclient import TestClient

    con = duckdb.connect(":memory:")
    con.execute("CREATE TABLE diario (fuente VARCHAR, id_fuente VARCHAR, fecha DATE);")
    con.execute("INSERT INTO diario VALUES ('mercadona','a','2026-11-04'),"
                " ('lidl','b','2026-11-04');")
    monkeypatch.setattr(api.catalogo, "conexion", lambda: con)
    monkeypatch.setattr(api.catalogo, "fecha_de_gold", lambda: "2026-11-04")
    monkeypatch.setattr(api, "_version_del_catalogo", lambda: "ensayo")
    monkeypatch.setattr(api, "_vigencia_del_catalogo", lambda: {})
    oro = tmp_path / "gold"
    oro.mkdir()
    monkeypatch.setattr(api, "AJUSTES", SimpleNamespace(gold=oro, dias_precio_valido=3))
    cobertura = tmp_path / "cobertura"
    cobertura.mkdir()
    (cobertura / "mercadona-2026-11-04.json").write_text(json.dumps({
        "fuente": "mercadona", "cobertura": "catalogo_diario", "filas": 4272,
        "referencia": 4321, "referencia_fecha": "2026-10-05", "pct": 98.9,
        "veredicto": "ok",
        "novedad": {"vs": "2026-11-03", "nuevos": 4, "cambiados": 71, "desaparecen": 9},
    }, ensure_ascii=False), encoding="utf-8")
    try:
        respuesta = TestClient(api.app).get("/api/estado")
        assert respuesta.status_code == 200
        por_cadena = {c["cadena"]: c for c in respuesta.json()["cadenas"]}
        assert por_cadena["mercadona"]["cobertura"]["filas"] == 4272
        assert por_cadena["mercadona"]["cobertura"]["novedad"]["cambiados"] == 71
        assert "cobertura" not in por_cadena["lidl"], (
            "una cadena sin fichero de cobertura sale sin la clave: no se inventa")
    finally:
        con.close()
