"""La vista previa del plan dice que entraria, y no toca la lista.

El recetario es SQLite de verdad, en un directorio temporal: es la unica forma de comprobar que se lee **la
version que el plan guardo** y no la ultima. El lado de la lista va sustituido, que es lo que aqui no se prueba.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from core import recetas as nucleo
from plataforma.api import main
from plataforma.api import recetas as api_recetas


def _recetario_con_plan(tmp_path, monkeypatch):
    api_recetas.ruta_base(tmp_path / "recetas.sqlite")
    con = nucleo.conecta(tmp_path / "recetas.sqlite")
    rid = nucleo.crear(con, "ana", "Lentejas", raciones=4,
                       ingredientes=[{"texto": "lentejas", "cantidad": 400, "unidad": "g"}])
    nucleo.planificar(con, "ana", "2026-10-05", rid, comensales=4)
    # **Y se cambia la receta despues**: el plan tiene que seguir mandando la version 1.
    nucleo.actualizar(con, "ana", rid, ingredientes=[{"texto": "lentejas", "cantidad": 999, "unidad": "g"}])
    con.close()
    return rid


def _cliente(monkeypatch, en_la_lista):
    monkeypatch.setattr(main.almacen, "lineas_de", lambda lista_id: list(en_la_lista))
    monkeypatch.setattr(main, "_acceso", lambda *a, **k: "dueno")
    main.app.dependency_overrides[main.usuario_actual] = lambda: {
        "id": "ana", "usuario": "ana", "nombre": "Ana"}
    return TestClient(main.app)


def test_la_previa_dice_lo_que_entraria(tmp_path, monkeypatch):
    _recetario_con_plan(tmp_path, monkeypatch)
    cliente = _cliente(monkeypatch, [])
    r = cliente.get("/api/listas/lo-que-sea/desde-el-plan?desde=2026-10-01&hasta=2026-10-07")
    main.app.dependency_overrides.clear()
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert cuerpo["total"] == 1, cuerpo
    assert cuerpo["entrarian"][0]["nombre"] == "lentejas", cuerpo
    assert cuerpo["entrarian"][0]["cantidad"] == 400, "tiene que ser la version que el plan guardo, no la ultima"
    assert cuerpo["entrarian"][0]["receta"] == "Lentejas"


def test_lo_que_ya_esta_se_dice_aparte_y_no_entra(tmp_path, monkeypatch):
    _recetario_con_plan(tmp_path, monkeypatch)
    cliente = _cliente(monkeypatch, [{"nombre_visto": "Lentejas"}])
    r = cliente.get("/api/listas/lo-que-sea/desde-el-plan?desde=2026-10-01&hasta=2026-10-07")
    main.app.dependency_overrides.clear()
    cuerpo = r.json()
    assert cuerpo["total"] == 0 and cuerpo["entrarian"] == [], cuerpo
    assert cuerpo["ya_estaban"] == ["lentejas"], cuerpo


def test_la_previa_no_toca_la_lista(tmp_path, monkeypatch):
    """Es un GET: si escribiera, la vista previa dejaria de ser previa."""
    _recetario_con_plan(tmp_path, monkeypatch)
    anadidas = []
    monkeypatch.setattr(main.almacen, "anade_linea",
                        lambda *a, **k: anadidas.append(a) or {"id": "x"})
    cliente = _cliente(monkeypatch, [])
    cliente.get("/api/listas/lo-que-sea/desde-el-plan?desde=2026-10-01&hasta=2026-10-07")
    main.app.dependency_overrides.clear()
    assert anadidas == [], anadidas

def test_la_accion_mete_lo_que_la_previa_dijo(tmp_path, monkeypatch):
    """Lo que la previa anuncia es lo que la accion escribe: comparten el calculo."""
    _recetario_con_plan(tmp_path, monkeypatch)
    en_la_lista = []

    def anade(lista_id, usuario_id, linea_id, nombre, grupo_id=None, producto_id=None,
              cantidad=1, nota=None, cadena_elegida=None):
        fila = {"id": linea_id, "nombre_visto": nombre, "nota": nota, "cantidad": cantidad}
        en_la_lista.append(fila)
        return fila

    monkeypatch.setattr(main.almacen, "anade_linea", anade)
    cliente = _cliente(monkeypatch, en_la_lista)
    previa = cliente.get("/api/listas/lo-que-sea/desde-el-plan?desde=2026-10-01&hasta=2026-10-07").json()
    r = cliente.post("/api/listas/lo-que-sea/desde-el-plan?desde=2026-10-01&hasta=2026-10-07")
    main.app.dependency_overrides.clear()
    assert r.status_code == 201, r.text
    assert r.json()["anadidos"] == previa["total"] == 1, (r.json(), previa)
    assert en_la_lista[0]["nombre_visto"] == "lentejas"
    # **Una unidad, y el detalle en la nota**: la lista cuenta envases, la receta habla en gramos.
    assert en_la_lista[0]["cantidad"] == 1, en_la_lista[0]
    assert "400" in (en_la_lista[0]["nota"] or ""), en_la_lista[0]


def test_pulsar_dos_veces_no_duplica(tmp_path, monkeypatch):
    _recetario_con_plan(tmp_path, monkeypatch)
    en_la_lista = []

    def anade(lista_id, usuario_id, linea_id, nombre, grupo_id=None, producto_id=None,
              cantidad=1, nota=None, cadena_elegida=None):
        fila = {"id": linea_id, "nombre_visto": nombre, "nota": nota}
        en_la_lista.append(fila)
        return fila

    monkeypatch.setattr(main.almacen, "anade_linea", anade)
    cliente = _cliente(monkeypatch, en_la_lista)
    primera = cliente.post("/api/listas/lo-que-sea/desde-el-plan?desde=2026-10-01&hasta=2026-10-07").json()
    segunda = cliente.post("/api/listas/lo-que-sea/desde-el-plan?desde=2026-10-01&hasta=2026-10-07").json()
    main.app.dependency_overrides.clear()
    assert len(en_la_lista) == 1, f"ha dejado {len(en_la_lista)} lineas donde cabe una"
    assert primera["anadidos"] == 1 and segunda["anadidos"] == 0, (primera, segunda)
    assert segunda["ya_estaban"] == ["lentejas"], segunda
