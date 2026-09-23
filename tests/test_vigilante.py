"""El vigilante: la alerta salta cuando cambian los datos, no cuando entras a mirar.

Es el punto 6 del encargo, y el fallo era de una linea: `alertas.evalua()` solo corria
dentro de `GET /api/alertas`, asi que *"la alerta salta si entras a mirar"*. Un aviso que
solo salta cuando vas a verlo no es un aviso.

Lo que se vigila aqui, y cada cosa por su motivo:

  - **Que se apunte `salto_en` y NO `vista_en`.** Son dos cosas distintas: `vista_en` es
    "esta persona lo ha visto" y lo pone ella; apuntarlo desde el vigilante seria decir
    que alguien ha visto un aviso que no ha visto, y la pantalla lo daria por contado.
  - **Que una alerta salte una vez.** El `UPDATE` lleva `AND salto_en IS NULL`, asi que
    dos pasadas seguidas no cuentan lo mismo dos veces -- un aviso que se repite todos
    los dias deja de leerse.
  - **Que una alerta que no se cumple no se apunte.** Es la mitad que se olvida: si se
    apuntara todo lo que se mira, el aviso saldria siempre y no diria nada.
  - **Que un fallo no pare el vigilante.** Si PostgreSQL o gold no estan, la pasada
    falla y el bucle sigue: la API no se puede caer por esto.

El gold es de mentira y PostgreSQL se sustituye: una prueba que dependa del catalogo del
dia mide el calendario, no el codigo.
"""
from __future__ import annotations

import threading
from dataclasses import replace

import duckdb
import pytest

from plataforma.api import alertas, almacen, catalogo, vigilante

# Un producto por grupo, con lo que hace falta para juzgar una alerta `minimo_90d`:
# su precio por unidad de hoy y el minimo de los ultimos 90 dias.
PRODUCTOS = [
    {"grupo_id": 10, "fuente": "aldi", "nombre": "Cafe molido", "precio_cent": 100,
     "precio_unidad_cent": 100.0, "min_90d_cent": 100.0},
    {"grupo_id": 20, "fuente": "dia", "nombre": "Aceite de oliva", "precio_cent": 500,
     "precio_unidad_cent": 500.0, "min_90d_cent": 50.0},
]


@pytest.fixture
def gold(tmp_path, monkeypatch):
    def escribe(productos=PRODUCTOS):
        con = duckdb.connect()
        columnas = ("grupo_id BIGINT, fuente VARCHAR, id_fuente VARCHAR, "
                    "nombre VARCHAR, marca VARCHAR, cantidad DOUBLE, "
                    "unidad_canon VARCHAR, precio_cent BIGINT, "
                    "precio_unidad_cent DOUBLE, comparacion_fiable BOOLEAN, "
                    "calidad VARCHAR, calidad_origen VARCHAR, nutriscore VARCHAR, "
                    "nova BIGINT, ean VARCHAR, imagen VARCHAR, promo_txt VARCHAR, "
                    "promo_club BOOLEAN, promo_solo_online BOOLEAN")
        con.execute(f"CREATE TABLE g ({columnas})")
        for i, p in enumerate(productos):
            con.execute(
                f"INSERT INTO g VALUES ({','.join('?' * 19)})",
                [p["grupo_id"], p["fuente"], str(i), p["nombre"], None, 1.0, "kg",
                 p["precio_cent"], p["precio_unidad_cent"], True,
                 None, None, None, None, None, None, None, False, False])
        con.execute(f"COPY g TO '{tmp_path / 'grupos.parquet'}' (FORMAT PARQUET)")

        # El derivado de cada producto: el minimo de 90 dias y el precio base.
        con.execute("CREATE TABLE d (fuente VARCHAR, id_fuente VARCHAR, "
                    "min_90d_cent DOUBLE, precio_base_cent BIGINT, "
                    "fecha DATE)")
        for i, p in enumerate(productos):
            con.execute("INSERT INTO d VALUES (?, ?, ?, ?, DATE '2026-09-23')",
                        [p["fuente"], str(i), p["min_90d_cent"], p["precio_cent"]])
        con.execute(f"COPY d TO '{tmp_path / 'precio_derivado.parquet'}' "
                    f"(FORMAT PARQUET)")

        # El diario: `fecha_de_gold` lee de aqui, y la regla de las fechas lo necesita.
        con.execute("CREATE TABLE dia (fuente VARCHAR, id_fuente VARCHAR, "
                    "fecha DATE, precio_cent BIGINT, precio_unidad_cent DOUBLE, "
                    "unidad_canon VARCHAR)")
        for i, p in enumerate(productos):
            con.execute("INSERT INTO dia VALUES (?, ?, DATE '2026-09-23', ?, ?, 'kg')",
                        [p["fuente"], str(i), p["precio_cent"],
                         p["precio_unidad_cent"]])
        con.execute(f"COPY dia TO '{tmp_path / 'precio_diario.parquet'}' "
                    f"(FORMAT PARQUET)")
        for otro in ("enlaces", "resumen"):
            con.execute(f"COPY (SELECT 1 AS x) TO '{tmp_path / otro}.parquet' "
                        f"(FORMAT PARQUET)")
        con.close()
        catalogo.reiniciar()

    monkeypatch.setattr(catalogo, "AJUSTES", replace(catalogo.AJUSTES, gold=tmp_path))
    yield escribe
    catalogo.reiniciar()


def _casi(monkeypatch, alertas_: list[dict]):
    """El vigilante con las alertas de PostgreSQL sustituidas y lo apuntado recogido."""
    # **Se tira la memoria de los avisos en cada prueba.** El vigilante evalua con
    # `evalua_con_memoria`, que recuerda el veredicto mientras el sello de gold no
    # cambie -- y el sello es el `mtime` del fichero. Dos golds de prueba distintos
    # pueden caer en el mismo instante, y entonces una prueba se comeria el veredicto de
    # la anterior: verde por el motivo equivocado.
    alertas.olvida()
    pendientes = list(alertas_)
    apuntadas: list[tuple[str, str]] = []
    vistas: list = []

    def marca(alerta_id, texto):
        if any(a == alerta_id for a, _t in apuntadas):
            return False            # ya estaba apuntada: el UPDATE no cambia nada
        apuntadas.append((alerta_id, texto))
        return True

    monkeypatch.setattr(almacen, "alertas_por_saltar", lambda: list(pendientes))
    monkeypatch.setattr(almacen, "marca_alerta_saltada", marca)
    monkeypatch.setattr(almacen, "marca_alertas_vistas",
                        lambda usuario_id, ids: vistas.append(ids) or 0)
    return apuntadas, vistas


def test_una_alerta_que_se_cumple_se_apunta_sin_darla_por_vista(gold, monkeypatch):
    """Esta al minimo de 90 dias: salta. Y lo hace sin que nadie abra la pantalla."""
    gold()
    apuntadas, vistas = _casi(monkeypatch, [
        {"id": "a1", "grupo_id": 10, "tipo": "minimo_90d", "umbral_cent": None}])

    r = vigilante.una_pasada()
    assert r == {"miradas": 1, "saltan": 1, "apuntadas": 1}
    assert [a for a, _t in apuntadas] == ["a1"], \
        "la alerta que se cumple tiene que quedar apuntada"
    assert vistas == [], (
        "el vigilante ha tocado `vista_en`: eso es decir que alguien ha visto un aviso "
        "que no ha visto, y la pantalla lo daria por contado")
    # Y se guarda la frase, no solo la hora: la frase se mide contra el gold de hoy, y
    # manana gold es otro. Sin guardarla, el aviso cambiaria de texto solo.
    texto = apuntadas[0][1]
    assert "90 dias" in texto and "aldi" in texto, \
        f"la frase guardada no explica el aviso: {texto!r}"


def test_una_alerta_que_no_se_cumple_no_se_apunta(gold, monkeypatch):
    """Hoy esta a 5,00 y el minimo de 90 dias es 0,50: no ha saltado nada."""
    gold()
    apuntadas, _ = _casi(monkeypatch, [
        {"id": "a2", "grupo_id": 20, "tipo": "minimo_90d", "umbral_cent": None}])

    r = vigilante.una_pasada()
    assert r == {"miradas": 1, "saltan": 0, "apuntadas": 0}
    assert apuntadas == [], "se ha apuntado una alerta que no se cumple"


def test_una_alerta_salta_una_vez(gold, monkeypatch):
    """Dos pasadas seguidas no cuentan lo mismo dos veces."""
    gold()
    apuntadas, _ = _casi(monkeypatch, [
        {"id": "a1", "grupo_id": 10, "tipo": "minimo_90d", "umbral_cent": None}])

    primera = vigilante.una_pasada()
    segunda = vigilante.una_pasada()
    assert primera["apuntadas"] == 1
    assert segunda["saltan"] == 1, "la condicion sigue siendo cierta"
    assert segunda["apuntadas"] == 0, (
        "la segunda pasada ha vuelto a apuntar la misma alerta: el aviso saldria dos "
        "veces y dejaria de leerse")
    assert [a for a, _t in apuntadas] == ["a1"]


def test_sin_alertas_pendientes_no_se_mira_nada(gold, monkeypatch):
    """El caso normal: nadie tiene alertas, y el vigilante no hace ninguna consulta."""
    gold()
    monkeypatch.setattr(almacen, "alertas_por_saltar", lambda: [])
    assert vigilante.una_pasada() == {"miradas": 0, "saltan": 0, "apuntadas": 0}


def test_un_fallo_no_para_el_vigilante():
    """Si gold o PostgreSQL no estan, el bucle sigue: la API no se cae por esto."""
    parar = threading.Event()
    vueltas: list[int] = []

    def pasada_que_falla():
        vueltas.append(1)
        if len(vueltas) >= 3:
            parar.set()
        raise RuntimeError("gold no esta")

    vigilante.en_marcha(parar, 0.001, pasada=pasada_que_falla,
                        sello=lambda: float(len(vueltas)))
    assert len(vueltas) >= 3, (
        "el vigilante se ha parado al primer fallo: una pasada que falla no puede "
        "acabar con el bucle")


def test_solo_hace_una_pasada_cuando_gold_cambia():
    """Los precios se escriben una vez al dia: mirar cien veces lo mismo no adelanta."""
    parar = threading.Event()
    hechas: list[int] = []

    def pasada():
        hechas.append(1)
        if len(hechas) >= 4:
            parar.set()
        return {"miradas": 0, "saltan": 0, "apuntadas": 0}

    # El sello cambia cada vuelta: entonces hay que hacer una pasada cada vez.
    vigilante.en_marcha(parar, 0.001, pasada=pasada,
                        sello=lambda: float(len(hechas) + 1))
    assert len(hechas) == 4

    # Y si el sello NO cambia, solo la primera. El temporizador se arma **antes** de
    # entrar en el bucle, que no termina solo: es un `while` que espera a que le digan.
    parar2 = threading.Event()
    threading.Timer(0.05, parar2.set).start()
    hechas2: list[int] = []
    vigilante.en_marcha(parar2, 0.01, pasada=lambda: hechas2.append(1) or
                        {"miradas": 0, "saltan": 0, "apuntadas": 0},
                        sello=lambda: 7.0)
    assert hechas2 == [1], (
        f"con gold sin cambiar ha hecho {len(hechas2)} pasadas y solo tocaba una")


def test_arranca_y_para_dejan_la_api_como_estaba(monkeypatch):
    """El hilo se enciende una vez, se puede parar, y no se encienden dos."""
    monkeypatch.setattr(almacen, "alertas_por_saltar", lambda: [])
    vigilante.arranca(intervalo=60)
    primero = vigilante._hilo
    vigilante.arranca(intervalo=60)
    assert vigilante._hilo is primero, "se ha encendido un segundo vigilante"
    vigilante.para()
    assert vigilante._hilo is None and vigilante._parar is None


def test_el_vigilante_mira_lo_mismo_que_la_pantalla(gold, monkeypatch):
    """Sin dos reglas: lo que salta en la pantalla y lo que apunta el vigilante.

    Los dos llaman a `alertas.evalua`, que es el unico sitio que sabe de precios. Esto
    lo fija para que nadie escriba una segunda comprobacion "parecida" en el vigilante.
    """
    gold()
    alerta = {"id": "a1", "grupo_id": 10, "tipo": "minimo_90d", "umbral_cent": None}
    _casi(monkeypatch, [alerta])
    saltan_aqui = alertas.evalua([{**alerta, "usuario_id": "u1"}])
    assert len(saltan_aqui) == 1
    assert vigilante.una_pasada()["saltan"] == len(saltan_aqui)
