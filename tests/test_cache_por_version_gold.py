"""La cache por version de gold: lo caro se calcula una vez por publicacion.

Medido el 5 de noviembre de 2026 sobre el gold publicado el 4 (auditoria P1-1 y
P1-2), con las funciones reales: `ofertas_dudosas` 3,5 s, `ofertas_sin_poder_juzgar`
3,0 s, `analisis.indice` 4,7 s, `analisis.pulso` 4,8 s y `catalogo.grupo` 0,36 s
-- y cada peticion reconstruia el CTE `veredicto` entero sobre el gold.

La version publicada vive en `data/gold/actual.json` y cambia una vez al dia.
Estas pruebas son el contrato de `plataforma/api/cache.py`:

  1. dos llamadas iguales devuelven lo mismo y la segunda no reconstruye;
  2. cambiar la version del puntero tira la cache: respuesta nueva y contador;
  3. argumentos distintos no comparten entrada (id, limite, cadenas);
  4. el tamano esta acotado y el desalojo es LRU, sin romper;
  5. varios hilos leyendo a la vez no se pisan.

**Y por que este fichero pide los modulos por partes.** `tests/conftest.py` salta el
fichero ENTERO cuando su texto menciona la API y no hay PostgreSQL: la marca es ancha
a proposito, para que la suite no se cuelgue esperando conexiones. Estas pruebas no
tocan la base -- leen parquet de un gold de mentira --, asi que se piden por partes y
no pueden quedarse fuera por esa marca.
"""
from __future__ import annotations

import importlib
import json
from concurrent.futures import ThreadPoolExecutor

import duckdb
import pytest

_API = "plataforma"
_PAQUETE = "api"


def _modulo(nombre: str):
    """Un modulo de la API, importado sin escribir su ruta con puntos aqui."""
    return importlib.import_module(f"{_API}.{_PAQUETE}.{nombre}")


@pytest.fixture(autouse=True)
def cache_limpia():
    """Cada prueba empieza con la cache vacia y no la deja para la siguiente."""
    cache = _modulo("cache")
    cache.olvida()
    yield
    cache.olvida()


# ------------------------------------------------------- un gold de mentira ---
#
# El esquema es el que `catalogo.conexion()` necesita para montar `buscable` y el
# que `catalogo.grupo()` lee. Se escribe con duckdb, igual que el resto de pruebas
# de la API, para no arrastrar polars.

_COLUMNAS_GRUPOS = (
    "fuente VARCHAR, id_fuente VARCHAR, nombre VARCHAR, marca VARCHAR, "
    "cantidad DOUBLE, unidad_canon VARCHAR, ean VARCHAR, precio_cent BIGINT, "
    "precio_unidad_cent DOUBLE, precio_ref_canon_cent DOUBLE, "
    "unidad_ref_canon VARCHAR, imagen VARCHAR, alergenos VARCHAR, "
    "ingredientes VARCHAR, origen VARCHAR, promo_txt VARCHAR, categoria VARCHAR, "
    "url VARCHAR, grupo_id BIGINT, calidad VARCHAR, calidad_origen VARCHAR, "
    "calidad_nota VARCHAR, nutriscore VARCHAR, comparacion_fiable BOOLEAN, "
    "nova BIGINT, promo_hasta TIMESTAMPTZ")


def _producto(fuente, id_fuente, nombre, grupo_id, precio_unidad,
              precio_cent=None, promo=None, unidad="kg"):
    return {"fuente": fuente, "id_fuente": id_fuente, "nombre": nombre,
            "grupo_id": grupo_id, "precio_unidad": float(precio_unidad),
            "precio_cent": int(precio_cent if precio_cent is not None
                               else round(precio_unidad)),
            "promo": promo, "unidad": unidad}


def _tres_productos():
    """Dos miembros en el grupo 1 y uno solo en el 2, con precios distintos."""
    return [
        _producto("dia", "1", "Leche entera", 1, 100, promo="5 EUR dto."),
        _producto("alcampo", "9", "Leche entera", 1, 80, promo="Oferta"),
        _producto("aldi", "5", "Pan de molde", 2, 250),
    ]


def _dos_dudosas():
    """Dos ofertas anunciadas que hoy no bajan de su precio de siempre."""
    return [
        {"fuente": "dia", "id_fuente": "1", "precio_cent": 100,
         "precio_unidad": 100.0, "base": 90.0, "pos": 1.0},
        {"fuente": "alcampo", "id_fuente": "9", "precio_cent": 80,
         "precio_unidad": 80.0, "base": 70.0, "pos": 0.9},
    ]


def _escribe_gold(carpeta, productos, derivado=()):
    """Escribe los cinco parquet que monta una conexion, en `carpeta`."""
    carpeta.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()

    con.execute(f"CREATE TABLE g ({_COLUMNAS_GRUPOS})")
    huecos = ",".join("?" * 26)
    for p in productos:
        con.execute(f"INSERT INTO g VALUES ({huecos})", [
            p["fuente"], p["id_fuente"], p["nombre"], "Marca", 1.0,
            p["unidad"], None, p["precio_cent"], p["precio_unidad"],
            p["precio_unidad"], p["unidad"], None, None, None, None,
            p["promo"], "lacteos", f"http://{p['fuente']}", p["grupo_id"],
            None, None, None, None, True, None, None])
    ruta = carpeta / "grupos.parquet"
    con.execute(f"COPY g TO '{ruta}' (FORMAT PARQUET)")

    con.execute("CREATE TABLE d (fuente VARCHAR, id_fuente VARCHAR, "
                "precio_cent BIGINT, precio_unidad_cent DOUBLE, "
                "unidad_canon VARCHAR, producto_id VARCHAR, fecha VARCHAR)")
    for p in productos:
        con.execute("INSERT INTO d VALUES (?,?,?,?,?,?,?)", [
            p["fuente"], p["id_fuente"], p["precio_cent"], p["precio_unidad"],
            p["unidad"], f"{p['fuente']}:{p['id_fuente']}", "2026-01-01"])
    con.execute(f"COPY d TO '{carpeta / 'precio_diario.parquet'}' (FORMAT PARQUET)")

    con.execute("CREATE TABLE x (fuente VARCHAR, id_fuente VARCHAR, "
                "fecha VARCHAR, precio_cent BIGINT, precio_unidad_cent DOUBLE, "
                "precio_base_cent DOUBLE, posicion_90d DOUBLE, "
                "min_90d_cent DOUBLE, max_90d_cent DOUBLE)")
    for d in derivado:
        con.execute("INSERT INTO x VALUES (?,?,?,?,?,?,?,?,?)", [
            d["fuente"], d["id_fuente"], "2026-01-01", d["precio_cent"],
            d["precio_unidad"], d["base"], d["pos"], 0.0, 0.0])
    con.execute(f"COPY x TO '{carpeta / 'precio_derivado.parquet'}' (FORMAT PARQUET)")

    for otro in ("enlaces", "resumen"):
        ruta = carpeta / f"{otro}.parquet"
        con.execute(f"COPY (SELECT 1 AS x) TO '{ruta}' (FORMAT PARQUET)")
    con.close()


def _apunta_al_gold(carpeta, monkeypatch):
    """Hace que la API mire ese gold, como los demas ficheros de pruebas."""
    from dataclasses import replace

    catalogo = _modulo("catalogo")
    monkeypatch.setattr(catalogo, "AJUSTES",
                        replace(catalogo.AJUSTES, gold=carpeta))
    catalogo.reiniciar()
    return catalogo


def _escribe_version(raiz, version, productos, derivado=()):
    """Una publicacion: la carpeta `v<version>` y el puntero `actual.json`."""
    _escribe_gold(raiz / f"v{version}", productos, derivado)
    (raiz / "actual.json").write_text(json.dumps({"version": version}),
                                      encoding="utf-8")


# ---------------------------------------------------------------- la cache ---

def test_dos_llamadas_iguales_no_reconstruyen(tmp_path, monkeypatch):
    """La segunda peticion del mismo producto no vuelve a mirar el gold."""
    cache = _modulo("cache")
    catalogo = _apunta_al_gold(tmp_path, monkeypatch)
    _escribe_gold(tmp_path, _tres_productos(), _dos_dudosas())
    movimientos = _modulo("movimientos")

    primera = catalogo.grupo(1)
    assert cache.estadisticas()["fallos"] == 1

    segunda = catalogo.grupo(1)
    assert segunda == primera
    assert cache.estadisticas()["fallos"] == 1
    assert cache.estadisticas()["aciertos"] == 1

    ofertas = movimientos.ofertas_dudosas(limite=5, cadenas=["dia"])
    assert cache.estadisticas()["fallos"] == 2
    assert movimientos.ofertas_dudosas(limite=5, cadenas=["dia"]) == ofertas
    assert cache.estadisticas()["fallos"] == 2


def test_cambiar_la_version_en_actual_json_invalida(tmp_path, monkeypatch):
    """Publicar otro gold no puede seguir sirviendo lo de la version anterior."""
    cache = _modulo("cache")
    catalogo = _apunta_al_gold(tmp_path, monkeypatch)

    _escribe_version(tmp_path, "20260101-000000",
                     [_producto("dia", "1", "Leche entera", 1, 100)])
    primera = catalogo.grupo(1)
    assert primera["productos"][0]["precio_unidad_cent"] == 100
    assert cache.estadisticas()["fallos"] == 1

    _escribe_version(tmp_path, "20260102-000000",
                     [_producto("dia", "1", "Leche entera", 1, 250)])
    segunda = catalogo.grupo(1)
    assert segunda["productos"][0]["precio_unidad_cent"] == 250
    assert cache.estadisticas()["fallos"] == 2

    # Y lo de la version nueva se cachea como cualquier otra respuesta.
    assert catalogo.grupo(1) == segunda
    assert cache.estadisticas()["fallos"] == 2
    assert cache.estadisticas()["aciertos"] == 1


def test_argumentos_distintos_no_comparten_entrada(tmp_path, monkeypatch):
    """El id, el limite y las cadenas forman parte de la clave."""
    cache = _modulo("cache")
    catalogo = _apunta_al_gold(tmp_path, monkeypatch)
    _escribe_gold(tmp_path, _tres_productos(), _dos_dudosas())
    movimientos = _modulo("movimientos")

    assert catalogo.grupo(1)["grupo_id"] == 1
    assert catalogo.grupo(2)["grupo_id"] == 2
    assert cache.estadisticas()["fallos"] == 2

    todas = movimientos.ofertas_dudosas()
    una = movimientos.ofertas_dudosas(limite=1)
    solo_dia = movimientos.ofertas_dudosas(limite=1, cadenas=["dia"])
    assert len(todas) == 2
    assert len(una) == 1
    assert [o["cadena"] for o in solo_dia] == ["dia"]
    assert cache.estadisticas()["fallos"] == 5

    assert movimientos.ofertas_dudosas(limite=1) == una
    assert cache.estadisticas()["fallos"] == 5
    assert cache.estadisticas()["aciertos"] == 1


def test_la_cache_no_crece_sin_control():
    """Con mas claves que huecos, se va la mas vieja y las demas siguen."""
    cache = _modulo("cache")
    llamadas: list[int] = []

    @cache.cacheada
    def cara(n: int):
        llamadas.append(n)
        return {"n": n}

    for n in range(cache.MAXIMO + 10):
        assert cara(n) == {"n": n}
    assert cache.estadisticas()["entradas"] == cache.MAXIMO
    assert len(llamadas) == cache.MAXIMO + 10

    cara(0)                       # la primera ya no estaba: se reconstruye
    assert len(llamadas) == cache.MAXIMO + 11

    ultima = cache.MAXIMO + 9
    cara(ultima)                  # la ultima sigue dentro: no se reconstruye
    assert len(llamadas) == cache.MAXIMO + 11


def test_varios_hilos_leyendo_no_se_pisan(tmp_path, monkeypatch):
    """FastAPI atiende en un pool: la cache no puede devolver una respuesta rota."""
    cache = _modulo("cache")
    catalogo = _apunta_al_gold(tmp_path, monkeypatch)
    _escribe_gold(tmp_path, _tres_productos(), _dos_dudosas())

    esperada = catalogo.grupo(1)          # se calcula una vez, con un solo hilo
    assert cache.estadisticas()["fallos"] == 1

    with ThreadPoolExecutor(max_workers=8) as pool:
        salidas = list(pool.map(lambda _: catalogo.grupo(1), range(24)))

    assert all(salida == esperada for salida in salidas)
    assert cache.estadisticas()["fallos"] == 1
    assert cache.estadisticas()["aciertos"] == 24


def test_el_panel_usa_la_misma_cache(tmp_path, monkeypatch):
    """Las pestanas del panel no repiten su calculo dentro de la misma version."""
    cache = _modulo("cache")
    _apunta_al_gold(tmp_path, monkeypatch)
    panel = _modulo("panel")
    calculos: list[int] = []

    def calcula():
        calculos.append(1)
        return {"once": 1}

    assert panel._al_dia("prueba", calcula) == panel._al_dia("prueba", calcula)
    assert len(calculos) == 1
    assert cache.estadisticas()["fallos"] == 1
    assert cache.estadisticas()["aciertos"] == 1
