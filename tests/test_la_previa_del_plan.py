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
                       # **Con destino**: un ingrediente enlazado con el catalogo si se puede
                       # anadir a la lista. La tabla exige `linea_con_destino`. Medido el 13 de
                       # octubre de 2026: sin esto, el puente no metia nada -- correctamente -- y
                       # esta prueba lo daba por malo.
                       ingredientes=[{"texto": "lentejas", "cantidad": 400, "unidad": "g",
                                      "producto_id": "dia:1000"}])
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


def test_un_ingrediente_escrito_a_mano_ENTRA_como_pendiente_y_se_dice(tmp_path, monkeypatch):
    """**El caso que rompia el puente, y que ahora se resuelve al reves.** Una receta escrita a mano
    tiene ingredientes que no estan enlazados con el catalogo.

    *Y este ensayo decia, con fecha: **«la tabla exige `linea_con_destino`: no se pueden anadir...
    Medido el 13 de octubre de 2026»** -- *y fijaba que **no entraba**, que **no se mandaba a la base**,
    y que se decia.*

    **Y lo que cambio no fue el criterio: fue el suelo.** *La migracion `014_la_linea_sin_destino.sql`
    quito esa restriccion, y dice por que*: *«la restriccion protegia la comparacion y **prohibia la
    lista**: quien no encontraba el producto en el catalogo **no podia apuntarlo, y acababa apuntandolo
    en otro sitio»*.

    **Y la sal es exactamente ese caso** -- *la mitad de una lista de la compra de verdad, y el ejemplo
    que el complemento del 14/10 nombra.*

    **Lo que se fija ahora**: *la sal **entra**, con su nombre y su cantidad, **sin destino** -- que es
    lo que la hace «pendiente de identificar» --, **sin precio ni equivalencia inventados**, y
    **diciendolo** en la nota.
    """
    api_recetas.ruta_base(tmp_path / "recetas.sqlite")
    con = nucleo.conecta(tmp_path / "recetas.sqlite")
    rid = nucleo.crear(con, "ana", "A mano", raciones=2,
                       ingredientes=[{"texto": "sal", "cantidad": 1, "unidad": "pizca"}])
    nucleo.planificar(con, "ana", "2026-10-05", rid, comensales=2)
    con.close()

    anadidas = []
    monkeypatch.setattr(main.almacen, "anade_linea",
                        lambda *a, **k: anadidas.append(a) or {"id": "x"})
    monkeypatch.setattr(main, "_acceso", lambda *a, **k: "dueno")
    main.app.dependency_overrides[main.usuario_actual] = lambda: {
        "id": "ana", "usuario": "ana", "nombre": "Ana"}
    cliente = _cliente(monkeypatch, [])
    previa = cliente.get(
        "/api/listas/lo-que-sea/desde-el-plan?desde=2026-10-01&hasta=2026-10-07").json()
    r = cliente.post("/api/listas/lo-que-sea/desde-el-plan?desde=2026-10-01&hasta=2026-10-07")
    main.app.dependency_overrides.clear()

    # *La previa sigue diciendo que la sal no tiene catalogo: eso no cambia, porque no hay producto.*
    assert previa["sin_catalogo"] == ["sal"], previa
    # **Y la previa ya cuenta la pendiente.** *Decia `total: 0` mientras el POST apuntaba 1: **prometia
    # menos de lo que hacia**, que es mentir igual que prometer de mas.* *Ahora los dos numeros dicen lo
    # mismo, y `sin_catalogo` sigue nombrandola para que la pantalla la enseñe como pendiente.*
    assert previa["total"] == 1, (
        f"la previa tiene que contar la pendiente: dice {previa.get('total')} y el POST apunta 1")
    assert len(previa["entrarian"]) == 1, previa
    assert r.status_code == 201, r.text
    # **Y el POST SI la apunta.** *Antes `anadidos` era 0 y `anadidas` estaba vacio: **eso probaba
    # rechazo, no conservacion** -- que es exactamente lo que el complemento del 14/10 senala.*
    assert r.json()["anadidos"] == 1, r.json()
    assert r.json()["sin_catalogo"] == ["sal"], r.json()
    assert len(anadidas) == 1, "la sal tiene que llegar a la base"
    argumentos = anadidas[0]
    assert argumentos[3] == "sal", f"con su nombre: {argumentos[3]!r}"
    assert argumentos[4] is None and argumentos[5] is None, (
        "SIN destino -- ni grupo ni producto --, que es lo que la hace «pendiente de identificar»")
    assert argumentos[6] == 1, "y con su cantidad"
    assert "pendiente de identificar" in (argumentos[7] or ""), argumentos[7]
