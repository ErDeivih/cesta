"""La cobertura diaria, **declarada con lo medido** y no solo autodeclarada.

**El 4 de noviembre de 2026 la ficha del agente decia «cobertura diaria: solo Lidl,
21 dias».** Era falso, pero no era un capricho: `cobertura_declarada` -- y por tanto
el manifiesto y `GET /api/estado` -- solo llevaba lo que escriben los colectores en
`data/cobertura/`, y ahi **solo escribia Lidl**. Mercadona, Carrefour, DIA, Aldi y
Alcampo capturaban todos los dias y **no lo declaraban en ningun sitio que la
aplicacion leyera**, asi que cualquier lector del dato publicado --persona, panel o
documento-- veia una sola cadena.

Lo que se fija aqui:

  1. cada cadena de catalogo declara, al cerrar el dia, **lo que se ha medido sobre
     su bronce**: filas, referencia y de que dia es, % de la referencia, huecos y
     veredicto -- la misma regla de `veredicto`, no una copia;
  2. la declaracion dice ademas **que produjo el dia**: cuantos ids son nuevos,
     cuantos precios cambiaron y cuantos desaparecieron frente a la captura anterior;
     sin captura del dia no se inventa un cero: se declara «sin datos»;
  3. reescribir el mismo dia no duplica ni deja un fichero a medias;
  4. el manifiesto recoge esas declaraciones para las seis cadenas, de modo que
     «solo Lidl» deja de ser una lectura posible del dato publicado.
"""
from __future__ import annotations

import json
import os
from datetime import date

import polars as pl
import pytest

from core import manifiesto
from projects.cesta import cobertura_diaria

HOY = "2026-11-04"
AYER = "2026-11-03"


def _bronce(filas: list[dict]) -> pl.DataFrame:
    return pl.DataFrame(filas)


def _escribe(base, fuente: str, fecha: str, precios: dict[str, int]) -> None:
    """Una particion de bronce minima: id y precio, que es lo que la novedad necesita."""
    carpeta = base / "bronze" / f"fuente={fuente}" / f"fecha={fecha}"
    carpeta.mkdir(parents=True, exist_ok=True)
    _bronce([{"id_fuente": k, "precio_cent": v} for k, v in precios.items()]).write_parquet(
        carpeta / "part.parquet")


@pytest.fixture
def base(tmp_path, monkeypatch):
    monkeypatch.setattr(cobertura_diaria.config, "DATA", tmp_path)
    return tmp_path


# --- 1. una declaracion por cadena de catalogo y dia ------------------------

def test_cada_cadena_de_catalogo_declara_su_dia(base):
    """Las cinco cadenas que catalogan entero escriben su cobertura, no solo Lidl."""
    for fuente in cobertura_diaria.FUENTES:
        _escribe(base, fuente, AYER, {"1": 100, "2": 200})
        _escribe(base, fuente, HOY, {"1": 100, "2": 250, "3": 300})

    escritos = cobertura_diaria.declara(HOY)

    assert len(escritos) == len(cobertura_diaria.FUENTES)
    for fuente in cobertura_diaria.FUENTES:
        fichero = base / "cobertura" / f"{fuente}-{HOY}.json"
        assert fichero.is_file(), f"{fuente} no ha declarado su cobertura del dia"
        datos = json.loads(fichero.read_text(encoding="utf-8"))
        assert datos["fuente"] == fuente
        assert datos["cobertura"] == "catalogo_diario"
        assert datos["fecha"] == HOY
        assert datos["filas"] == 3
        assert datos["captura"]["filas"] == 3
        # La vara y el veredicto son los de la regla que ya existe, no una copia.
        assert datos["referencia"] == 2
        assert datos["veredicto"] == "ok"
    assert not (base / "cobertura" / f"lidl-{HOY}.json").exists(), (
        "Lidl declara la suya desde su colector, con su alcance parcial")


# --- 2. la novedad del dia, que es lo que se pide demostrar ----------------

def test_la_declaracion_dice_que_produjo_el_dia(base):
    """Nuevos, cambiados y desaparecidos frente a la captura anterior. Ese es el dato."""
    _escribe(base, "mercadona", AYER, {"a": 100, "b": 200, "c": 300})
    _escribe(base, "mercadona", HOY, {"b": 200, "c": 350, "d": 400})

    datos = cobertura_diaria.declaracion("mercadona", HOY)

    assert datos["novedad"] == {"vs": AYER, "nuevos": 1, "cambiados": 1, "desaparecen": 1}


def test_con_un_hueco_se_compara_con_la_ultima_captura_que_hay(base):
    """Un domingo sin captura no convierte el lunes en «todo nuevo»: se compara con el sabado."""
    _escribe(base, "mercadona", "2026-11-01", {"a": 100, "b": 200})
    _escribe(base, "mercadona", HOY, {"a": 120, "b": 200})

    datos = cobertura_diaria.declaracion("mercadona", HOY)

    assert datos["novedad"]["vs"] == "2026-11-01"
    assert datos["novedad"]["cambiados"] == 1
    assert datos["novedad"]["nuevos"] == 0


def test_sin_captura_del_dia_no_se_inventa_la_novedad(base):
    """Un dia sin bronce no es «cero precios nuevos»: es desconocido, y se dice."""
    _escribe(base, "mercadona", AYER, {"a": 100})

    datos = cobertura_diaria.declaracion("mercadona", HOY)

    assert datos["filas"] == 0
    assert datos["veredicto"] == "sin datos"
    assert datos["novedad"]["nuevos"] is None
    assert datos["novedad"]["cambiados"] is None
    assert datos["captura"] is None


# --- 3. reescribir no duplica ni deja basura -------------------------------

def test_reescribir_el_mismo_dia_es_idempotente(base):
    _escribe(base, "dia", HOY, {"a": 100, "b": 200})

    cobertura_diaria.declara(HOY)
    primero = (base / "cobertura" / f"dia-{HOY}.json").read_text(encoding="utf-8")
    cobertura_diaria.declara(HOY)

    ficheros = list((base / "cobertura").glob("dia-*.json"))
    assert len(ficheros) == 1
    segundo = json.loads(ficheros[0].read_text(encoding="utf-8"))
    assert json.loads(primero)["captura"]["filas"] == segundo["captura"]["filas"]
    assert not list((base / "cobertura").glob("*.tmp")), "no puede quedar un temporal a medias"


# --- 4. el manifiesto recoge lo declarado, y ya no es «solo Lidl» ----------

def test_el_manifiesto_recoge_la_cobertura_declarada_de_cada_cadena(base, monkeypatch):
    monkeypatch.setattr(manifiesto, "COBERTURA", base / "cobertura")
    _escribe(base, "mercadona", HOY, {"a": 100})
    _escribe(base, "carrefour", HOY, {"a": 100})
    cobertura_diaria.declara(HOY)

    declarada = manifiesto._cobertura()

    assert f"mercadona-{HOY}" in declarada
    assert f"carrefour-{HOY}" in declarada
    assert declarada[f"mercadona-{HOY}"]["filas"] == 1
    assert len([k for k in declarada if k.startswith(("mercadona-", "carrefour-"))]) == 2


# --- 5. la cadena diaria la escribe al cerrar ------------------------------

def test_la_cadena_diaria_declara_la_cobertura():
    """`run.py` tiene que dejar la declaracion escrita al final del dia, no solo el aviso."""
    import inspect

    from projects.cesta import run

    fuente = inspect.getsource(run)
    assert ".declara(" in fuente, (
        "la cadena diaria imprime el aviso de cobertura pero no deja la declaracion escrita")


def test_la_declaracion_lleva_la_fecha_pedida_y_no_la_del_reloj(base):
    """Se pasa la fecha; un modulo que recibe una fecha y usa otra es una trampa."""
    _escribe(base, "aldi", "2026-10-30", {"a": 100})
    datos = cobertura_diaria.declaracion("aldi", "2026-10-30")
    assert datos["fecha"] == "2026-10-30"
    assert isinstance(date.fromisoformat(datos["fecha"]), date)


# --- 6. la variacion es contra la ULTIMA captura, no contra la primera -------
#
# **Es un defecto que la revisión adversarial encontró en el codigo que ya existia** (el
# `vs_anterior_pct` del 4/11/2026): `calendario` va de ayer hacia atras, y recorrerlo con
# `reversed` empezaba por el dia mas antiguo de la ventana. Alc. publicaba «+1,7 % sobre la
# captura anterior» comparando contra el 5/10 cuando lo real era **+2,8 %** contra el 3/11; en
# Aldi el signo salia al reves (+6,8 % publicado frente a -4,4 % real).

def test_la_variacion_es_contra_la_ultima_captura_y_no_contra_la_primera_de_la_ventana():
    serie = {"2026-10-29": 1000, "2026-10-31": 2000, "2026-11-03": 4000,
             "2026-11-04": 4400}
    v = cobertura_diaria.veredicto(serie, "2026-11-04", dias=7)
    assert v["vs_anterior_pct"] == 10.0, (
        "tiene que comparar con el 3/11 (4400/4000), no con el 29/10 (4400/1000)")


def test_la_variacion_salta_los_dias_sin_captura(base):
    serie = {"2026-10-30": 200, "2026-11-04": 300}
    v = cobertura_diaria.veredicto(serie, "2026-11-04", dias=7)
    assert v["vs_anterior_pct"] == 50.0, "el dia sin captura no es una captura"


def test_la_referencia_es_el_dia_mas_reciente_entre_los_empatados():
    """Si el maximo se repite, la vara se atribuye al dia **mas reciente**, no al mas viejo."""
    serie = {"2026-10-30": 2951, "2026-10-31": 2951, "2026-11-04": 2709}
    v = cobertura_diaria.veredicto(serie, "2026-11-04", dias=6)
    assert v["referencia"] == 2951
    assert v["referencia_fecha"] == "2026-10-31"


def test_el_run_se_busca_por_el_dia_local_y_no_por_el_prefijo_utc(base):
    """Una pasada a las 00:30 de Madrid es el dia anterior en UTC: el prefijo UTC la perderia."""
    (base / "runs.csv").write_text(
        "ts,fuente,filas,errores,segundos,ok\n"
        "2026-11-04T23:30:00+00:00,mercadona,4272,0,102.2,True\n",
        encoding="utf-8")
    assert cobertura_diaria.run_del_dia("mercadona", "2026-11-05") is not None, (
        "esa pasada es del 5/11 en hora de Madrid")
    assert cobertura_diaria.run_del_dia("mercadona", "2026-11-04") is None


def test_si_una_declaracion_falla_no_deja_el_conjunto_a_medias(base, monkeypatch):
    """Escribir de uno en uno y sustituir sobre la marcha deja, al fallar a mitad, dos ficheros
    del dia y tres de ayer: el manifiesto lo publicaria como si fuera todo de hoy."""
    destino = base / "cobertura"
    destino.mkdir(parents=True)
    for fuente in cobertura_diaria.FUENTES:
        (destino / f"{fuente}-{AYER}.json").write_text('{"de": "ayer"}', encoding="utf-8")
    for fuente in cobertura_diaria.FUENTES:
        _escribe(base, fuente, HOY, {"a": 100})

    original = cobertura_diaria.declaracion
    llamadas = {"n": 0}

    def declaracion_que_falla(fuente, fecha, serie=None):
        llamadas["n"] += 1
        if llamadas["n"] == 3:
            raise RuntimeError("el disco se lleno a mitad")
        return original(fuente, fecha, serie=serie)

    monkeypatch.setattr(cobertura_diaria, "declaracion", declaracion_que_falla)
    with pytest.raises(RuntimeError):
        cobertura_diaria.declara(HOY)

    assert not list(destino.glob(f"*-{HOY}.json")), (
        "un fallo a mitad no puede dejar publicada media declaracion del dia")
    assert not list(destino.glob("*.tmp")), "no puede quedar un temporal a medias"


def test_si_falla_la_sustitucion_a_mitad_se_restaura_lo_anterior(base, monkeypatch):
    """El renombrado de cada fichero es atomico, pero el conjunto no: si el tercero falla, los
    dos primeros ya estan del dia. Se guarda lo anterior y se restaura, para que el manifiesto no
    publique una mezcla de dos dias."""
    destino = base / "cobertura"
    destino.mkdir(parents=True)
    for fuente in cobertura_diaria.FUENTES:
        (destino / f"{fuente}-{HOY}.json").write_text('{"de": "antes"}', encoding="utf-8")
        _escribe(base, fuente, HOY, {"a": 100, "b": 200})

    real = os.replace
    llamadas = {"n": 0}

    def replace_que_falla(*args, **kwargs):
        llamadas["n"] += 1
        if llamadas["n"] == 3:
            raise OSError("el antivirus bloqueo el tercer renombrado")
        return real(*args, **kwargs)

    monkeypatch.setattr(cobertura_diaria.os, "replace", replace_que_falla)
    with pytest.raises(OSError):
        cobertura_diaria.declara(HOY)

    assert not list(destino.glob("*.tmp")), "no pueden quedar temporales"
    for fuente in cobertura_diaria.FUENTES:
        contenido = (destino / f"{fuente}-{HOY}.json").read_text(encoding="utf-8")
        assert contenido == '{"de": "antes"}', (
            f"{fuente} quedo escrito del dia: el conjunto no se deshizo")


def test_la_declaracion_lleva_la_clave_huecos_del_contrato(base):
    """El contrato nombra `huecos`; ademas de los dos numeros de los que sale."""
    _escribe(base, "mercadona", HOY, {"a": 100})
    datos = cobertura_diaria.declaracion("mercadona", HOY)
    assert datos["huecos"] == datos["dias_sin_datos"]
    assert isinstance(datos["huecos"], int)


def test_si_el_historico_no_se_puede_leer_la_captura_no_es_sin_datos(base, monkeypatch):
    """`filas_por_dia()` devuelve {} si no puede leer el bronce. Eso no convierte el dia en
    «no hubo captura»: la particion esta y tiene filas; se declara lo que se sabe y lo que no."""
    _escribe(base, "mercadona", HOY, {"a": 100, "b": 200})
    monkeypatch.setattr(cobertura_diaria, "filas_por_dia", lambda: {})

    datos = cobertura_diaria.declaracion("mercadona", HOY)

    assert datos["captura"]["filas"] == 2
    assert datos["filas"] == 2
    assert datos["veredicto"] == "sin referencia"
    assert datos["pct"] is None and datos["referencia"] is None
    assert datos["huecos"] is None and datos["dias_sin_datos"] is None, (
        "si no se pudo leer el historico, los huecos tampoco se saben: null, no un cero")
    assert "no se pudo leer con fiabilidad" in datos["aviso"]


def test_una_particion_ilegible_tampoco_es_sin_datos(base, monkeypatch):
    """Una particion que existe pero cuyo parquet no se puede leer no es una ausencia de captura:
    se declara «sin referencia», no «sin datos» con un fichero ahi al lado."""
    carpeta = base / "bronze" / "fuente=mercadona" / f"fecha={HOY}"
    carpeta.mkdir(parents=True)
    (carpeta / "part.parquet").write_bytes(b"esto no es un parquet")
    monkeypatch.setattr(cobertura_diaria, "filas_por_dia", lambda: {})

    datos = cobertura_diaria.declaracion("mercadona", HOY)

    assert datos["captura"] is not None and datos["captura"]["ficheros"] == 1
    assert datos["captura"]["filas"] == 0
    assert datos["veredicto"] == "sin referencia"
    assert datos["filas"] == 0
    assert datos["huecos"] is None
    assert "no hubo captura" not in datos["aviso"]


def test_si_falla_la_lectura_de_lo_anterior_no_quedan_temporales(base, monkeypatch):
    """El escenario que cita el codigo (fichero bloqueado) tambien puede fallar al LEER lo
    anterior. Eso no puede dejar los cinco `.tmp` en data/cobertura/."""
    destino = base / "cobertura"
    destino.mkdir(parents=True)
    for fuente in cobertura_diaria.FUENTES:
        (destino / f"{fuente}-{HOY}.json").write_text('{"de": "antes"}', encoding="utf-8")
        _escribe(base, fuente, HOY, {"a": 100})

    original = type(base).read_bytes

    def read_bytes_que_falla(self):
        if "cobertura" in str(self):
            raise OSError("el antivirus tiene el fichero abierto")
        return original(self)

    monkeypatch.setattr(type(base), "read_bytes", read_bytes_que_falla)
    with pytest.raises(OSError):
        cobertura_diaria.declara(HOY)
    monkeypatch.undo()

    assert not list((base / "cobertura").glob("*.tmp")), "no pueden quedar temporales"


# --- 7. el enganche en la cadena diaria, en el orden correcto ---------------

def test_la_declaracion_va_antes_del_manifiesto_en_la_cadena_diaria():
    """El manifiesto lee `data/cobertura/`; si se declarara despues, lo publicado iria un dia
    por detras y volveria a decir «solo Lidl». Se comprueba **el orden** en el fuente y que no
    viva dentro del `try` del emparejador (un fallo ahi se la llevaria por delante)."""
    import inspect

    from projects.cesta import run

    fuente = inspect.getsource(run)
    posicion_declaracion = fuente.index(".declara(")
    posicion_manifiesto = fuente.index('importlib.import_module("core.manifiesto")')
    assert posicion_declaracion < posicion_manifiesto, (
        "la declaracion tiene que escribirse antes de que se genere el manifiesto")
    emparejar = fuente.index('importlib.import_module("projects.cesta.emparejar")')
    assert posicion_declaracion < emparejar, (
        "la declaracion no puede depender de que el emparejador haya ido bien")
    # **El dia se fija al empezar la pasada**: una captura que cruza la medianoche no puede
    # escribir la declaracion (vacia) del dia siguiente.
    assert "fecha_de_la_pasada = str(config.hoy_local())" in fuente, (
        "la cadena diaria tiene que fijar el dia de la pasada al empezar")
    assert ".declara(fecha_de_la_pasada)" in fuente, (
        "la declaracion tiene que ser la del dia de la pasada, no la del reloj al final")
