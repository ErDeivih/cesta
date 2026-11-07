"""El vigilante de la ingesta: que diga solo si la cadena diaria sigue sola y sin errores.

**Datos sinteticos en `tmp_path`, y nada mas.** Ni el `data/` de verdad, ni `runs.csv` real,
ni PostgreSQL: un vigilante que se prueba contra su propio dia no se prueba. Cada prueba
monta una carpeta `data/` minima (bronce, gold, runs, cobertura, la marca del dia) y le pide
al vigilante que opine sobre un dia fijo, el 2026-11-05.

Lo que se comprueba, en el orden en que importa:

  - el caso bueno sale **0** y sin avisos (si esto no se puede probar, un 1 no significa nada);
  - una cadena que **no trajo nada** es fallo, y se nombra la cadena;
  - una cadena que trajo **de menos** frente a su referencia es aviso (la regla es la de
    `cobertura_diaria.veredicto`, no una copia de aqui);
  - el **gold de ayer** es fallo si la pasada ya cerro, aviso si sigue en marcha;
  - los avisos que se quedan **callados** (la nota de avisos de ayer, o con `error`, o una
    pasada que empezo y no termino) se dicen;
  - un `data/` vacio **no puede salir 0**.
"""
from __future__ import annotations

import csv
import datetime as dt
import json
from pathlib import Path
from zoneinfo import ZoneInfo

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from scripts import vigilar_ingesta

HOY = "2026-11-05"
AYER = "2026-11-04"
ANTEAYER = "2026-11-03"

#: Las seis que dejan fila en `runs.csv`: las cinco de catalogo y Lidl.
CADENAS = ("carrefour", "dia", "mercadona", "aldi", "alcampo", "lidl")

#: Filas de una captura normal. Cualquier numero vale mientras sea el mismo todos los dias.
FILAS = 1000


# ------------------------------------------------------------------ el data/ de mentira ---


def _parquet(ruta: Path, filas: int) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.table({"id_fuente": [f"p{i}" for i in range(filas)]}), ruta)


def _bronce(datos: Path, fuente: str, fecha: str, filas: int) -> None:
    """Una particion de bronce con `filas` filas. Es el dato del que salen las cuentas."""
    _parquet(datos / "bronze" / f"fuente={fuente}" / f"fecha={fecha}" / "part.parquet", filas)


def _runs(datos: Path, filas: dict[str, int], fecha: str = HOY, ok: bool = True,
          errores: int = 0) -> None:
    """`data/runs.csv` con la pasada del dia. El `ts` va en UTC, como el de verdad."""
    ruta = datos / "runs.csv"
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["ts", "fuente", "filas", "errores", "segundos", "ok"])
        for fuente, n in filas.items():
            w.writerow([f"{fecha}T09:00:00.000000+00:00", fuente, n, errores, 5.0, str(ok)])


def _gold(datos: Path, fechas: dict[str, str]) -> None:
    ruta = datos / "gold" / "precio_diario.parquet"
    ruta.parent.mkdir(parents=True, exist_ok=True)
    # Con tipos explicitos: con un diccionario vacio, pyarrow inferiria columnas nulas y el
    # parquet de la prueba no se pareceria al de verdad (dos columnas de texto).
    pq.write_table(pa.table({"fuente": pa.array(list(fechas), pa.string()),
                             "fecha": pa.array(list(fechas.values()), pa.string())}), ruta)


def _actual(datos: Path, fecha: str = HOY, version: str = "20261105-120000") -> None:
    ruta = datos / "gold" / "actual.json"
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps({"version_puntero": 1, "version": version,
                                "publicado_en": f"{fecha}T12:00:00", "ficheros": []}),
                    encoding="utf-8")


def _cobertura(datos: Path, cadenas=CADENAS, fecha: str = HOY) -> None:
    for fuente in cadenas:
        ruta = datos / "cobertura" / f"{fuente}-{fecha}.json"
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(json.dumps({"fuente": fuente, "fecha": fecha,
                                    "veredicto": "ok", "filas": FILAS}),
                        encoding="utf-8")


def _completo(datos: Path) -> Path:
    """Un dia perfecto: seis cadenas, gold de hoy, todo declarado y la marca del dia.

    Es el punto de partida de casi todas las pruebas: cada una le rompe una cosa.
    """
    for fuente in CADENAS:
        for fecha in (ANTEAYER, AYER, HOY):
            _bronce(datos, fuente, fecha, FILAS)
    _runs(datos, {fuente: FILAS for fuente in CADENAS})
    _gold(datos, {fuente: HOY for fuente in CADENAS})
    _actual(datos)
    _cobertura(datos)
    (datos / "ultima_ejecucion.txt").write_text(HOY + "\n", encoding="utf-8")
    (datos / "avisos.json").write_text(
        json.dumps({"cuando": f"{HOY}T12:00:00+01:00", "saltaron_hoy": 0}), encoding="utf-8")
    (datos.parent / "metricas-cesta.json").write_text(
        json.dumps({"fecha_datos": HOY}), encoding="utf-8")
    return datos


@pytest.fixture()
def datos(tmp_path: Path) -> Path:
    """`tmp_path/data`, con la raiz del proyecto un nivel mas arriba (metricas viven ahi)."""
    return _completo(tmp_path / "data")


def _vigila(datos: Path, fecha: str = HOY, ahora=None) -> dict:
    return vigilar_ingesta.vigila(datos=datos, fecha=fecha, ahora=ahora)


def _codigos(informe: dict) -> set[str]:
    return {a["codigo"] for a in informe["avisos"]}


def _aviso(informe: dict, codigo: str) -> dict:
    encontrados = [a for a in informe["avisos"] if a["codigo"] == codigo]
    assert encontrados, f"no hay aviso {codigo!r}: {_codigos(informe)}"
    return encontrados[0]


# ------------------------------------------------------------------------ el caso bueno ---


def test_todo_bien_sale_cero_y_sin_avisos(datos, capsys):
    informe = _vigila(datos)

    assert informe["estado"] == "ok", informe["avisos"]
    assert informe["avisos"] == [], "un dia entero no puede tener avisos"
    assert informe["fecha"] == HOY
    assert {c["fuente"] for c in informe["cadenas"]} == set(CADENAS)
    assert all(c["estado"] == "ok" for c in informe["cadenas"]), informe["cadenas"]

    assert vigilar_ingesta.main(["--datos", str(datos), "--fecha", HOY]) == 0
    salida = capsys.readouterr().out
    assert "✗" not in salida, f"un dia bueno no puede llevar cruces: {salida}"
    assert "ESTADO: OK" in salida


def test_el_json_que_deja_en_disco_y_el_que_saca_por_stdout_son_el_mismo(datos, capsys):
    codigo = vigilar_ingesta.main(["--datos", str(datos), "--fecha", HOY, "--json"])
    salida = capsys.readouterr().out
    por_stdout = json.loads(salida)

    assert codigo == 0
    assert {"fecha", "estado", "cadenas", "avisos"} <= set(por_stdout)
    assert por_stdout["fecha"] == HOY

    en_disco = json.loads((datos / "avisos_ingesta.json").read_text(encoding="utf-8"))
    assert en_disco == por_stdout, "el fichero y lo que se imprime tienen que ser lo mismo"


# ------------------------------------------------------------------- una cadena que falta ---


def test_una_cadena_sin_captura_es_fallo_y_la_nombra(datos, capsys):
    """Mercadona no dejo ni fila en `runs.csv` ni particion de bronce: no trajo nada."""
    _runs(datos, {f: FILAS for f in CADENAS if f != "mercadona"})
    for parte in (datos / "bronze" / "fuente=mercadona").glob("fecha=*"):
        for fichero in parte.glob("*.parquet"):
            fichero.unlink()
        parte.rmdir()

    informe = _vigila(datos)

    assert informe["estado"] == "fallo"
    aviso = _aviso(informe, "sin_pasada")
    assert aviso["cadena"] == "mercadona"
    assert aviso["gravedad"] == "fallo"
    assert "sin_bronce" not in _codigos(informe), "sin pasada ya lo dice todo: no se repite"

    assert vigilar_ingesta.main(["--datos", str(datos), "--fecha", HOY]) == 1
    salida = capsys.readouterr().out
    assert any("✗" in linea and "mercadona" in linea for linea in salida.splitlines()), salida
    assert any("✓" in linea and "dia" in linea for linea in salida.splitlines()), salida


def test_antes_del_margen_de_arranque_no_se_avisa_de_que_falte(datos):
    """**Un aviso a las 05:00 seria prematuro.** La pasada se programa a las 06:00 y el margen
    de arranque llega hasta las 08:00: dentro de el, que no haya pasada es un aviso
    `en_margen_arranque`, no un fallo. Pasado el margen, si sigue sin pasada, sí es fallo."""
    # Sin pasada de hoy y sin gold de hoy: el escenario de «todavia no ha empezado».
    (datos / "runs.csv").unlink()
    _gold(datos, {fuente: AYER for fuente in CADENAS})
    _actual(datos, fecha=AYER)
    zona = ZoneInfo("Europe/Madrid")
    margen = dt.datetime(2026, 11, 5, 8, 0, tzinfo=zona)

    temprano = vigilar_ingesta.vigila(
        datos=datos,
        ahora=dt.datetime(2026, 11, 5, 5, 0, tzinfo=zona),
        margen_hasta=margen,
    )
    assert temprano["estado"] == "aviso", temprano["estado"]
    assert "sin_pasada" not in _codigos(temprano)
    assert "en_margen_arranque" in _codigos(temprano)
    assert all(a["gravedad"] == "aviso" for a in temprano["avisos"]), temprano["avisos"]

    # A las 09:00 el margen ya pasó: el mismo árbol sí es un fallo.
    tarde = vigilar_ingesta.vigila(
        datos=datos,
        ahora=dt.datetime(2026, 11, 5, 9, 0, tzinfo=zona),
        margen_hasta=margen,
    )
    assert tarde["estado"] == "fallo", tarde["estado"]
    assert "sin_pasada" in _codigos(tarde)


def test_una_pasada_que_no_acabo_bien_es_fallo(datos):
    _runs(datos, {f: FILAS for f in CADENAS}, ok=False, errores=3)

    informe = _vigila(datos)

    assert informe["estado"] == "fallo"
    assert _aviso(informe, "pasada_no_ok")["cadena"] in CADENAS


# ------------------------------------------------------------------------ la captura corta ---


def test_una_captura_corta_es_aviso_con_la_referencia_de_la_regla(datos):
    """Carrefour trae 600 donde suele traer 1000: 60 % contra el maximo de la ventana.

    No se comprueba contra un 90 % escrito aqui: se comprueba que el aviso dice lo que diga
    `cobertura_diaria.veredicto`, que es la unica regla.
    """
    for fecha in (ANTEAYER, AYER):
        _bronce(datos, "carrefour", fecha, 1000)
    _bronce(datos, "carrefour", HOY, 600)
    _runs(datos, {**{f: FILAS for f in CADENAS}, "carrefour": 600})

    informe = _vigila(datos)

    assert informe["estado"] == "aviso", informe["estado"]
    aviso = _aviso(informe, "captura_corta")
    assert aviso["cadena"] == "carrefour"
    assert aviso["gravedad"] == "aviso"
    carrefour = next(c for c in informe["cadenas"] if c["fuente"] == "carrefour")
    assert carrefour["referencia"]["veredicto"] == "corta"
    assert carrefour["referencia"]["filas"] == 600
    assert carrefour["referencia"]["referencia"] == 1000
    assert carrefour["referencia"]["pct"] == 60.0
    assert vigilar_ingesta.main(["--datos", str(datos), "--fecha", HOY]) == 1
    # **Y con --solo-fallos un aviso NO hace fallar la cadena diaria.** El dia esta hecho
    # (trajo datos, solo que menos); lo que no puede es salir 0 cuando de verdad hay un fallo.
    assert vigilar_ingesta.main(["--datos", str(datos), "--fecha", HOY, "--solo-fallos"]) == 0


def test_lidl_no_se_compara_contra_el_maximo(datos):
    """Lidl son ofertas semanales parciales (82-110 filas): su serie no es comparable.

    La lista de las que si se comparan la dice `cobertura_diaria.FUENTES`, no este fichero.
    """
    _bronce(datos, "lidl", HOY, 60)          # muy por debajo de sus 1000 de la prueba
    _runs(datos, {**{f: FILAS for f in CADENAS}, "lidl": 60})

    informe = _vigila(datos)

    assert "captura_corta" not in _codigos(informe)
    lidl = next(c for c in informe["cadenas"] if c["fuente"] == "lidl")
    assert lidl["referencia"] is None
    assert lidl["estado"] == "ok"


# -------------------------------------------------------------------------- el gold de hoy ---


def test_gold_atrasado_con_la_pasada_cerrada_es_fallo(datos):
    """La pasada acabo (no hay marca de ejecucion en curso) y gold sigue en el dia anterior."""
    _gold(datos, {fuente: AYER for fuente in CADENAS})
    _actual(datos, fecha=AYER)

    informe = _vigila(datos)

    assert informe["estado"] == "fallo"
    aviso = _aviso(informe, "gold_atrasado")
    assert aviso["gravedad"] == "fallo"
    assert informe["gold"]["fecha_max"] == AYER
    assert _vigila(datos)["avisos"], "un gold de ayer no puede pasar por bueno"
    assert vigilar_ingesta.main(["--datos", str(datos), "--fecha", HOY]) == 1
    # Un fallo de verdad sigue saliendo 1 aunque se pida --solo-fallos.
    assert vigilar_ingesta.main(
        ["--datos", str(datos), "--fecha", HOY, "--solo-fallos"]) == 1


def test_gold_de_una_cadena_que_se_quedo_atras_se_nombra(datos):
    _gold(datos, {**{f: HOY for f in CADENAS}, "aldi": AYER})

    informe = _vigila(datos)

    aviso = _aviso(informe, "cadena_gold_atrasada")
    assert aviso["cadena"] == "aldi"
    assert informe["gold"]["fecha_max"] == HOY


def test_un_gold_sin_filas_no_es_un_gold_bueno(datos):
    """Un `precio_diario` vacio no es «aun no ha publicado»: es un gold que no tiene nada."""
    _gold(datos, {})

    informe = _vigila(datos)

    aviso = _aviso(informe, "sin_gold")
    assert aviso["gravedad"] == "fallo"
    assert informe["estado"] == "fallo"
    assert "None" not in aviso["texto"], "el motivo no puede decir «gold sigue en el None»"


# --------------------------------------------------------------- la pasada que sigue viva ---


def test_la_pasada_en_curso_no_se_confunde_con_un_fallo(datos):
    """Con la marca de hoy puesta, lo que aun no ha llegado es «en curso», no «no vino».

    El reloj **se pasa a mano** (las 11:30 del dia que se mira): con el reloj de verdad, esta
    prueba pasaria o fallaria segun la hora a la que se corra la suite, porque una marca de las
    10:14 con mas de seis horas encima ya es una pasada muerta.
    """
    (datos / "ejecucion_en_curso.txt").write_text(f"{HOY} 10:14", encoding="utf-8")
    _runs(datos, {f: FILAS for f in CADENAS if f != "carrefour"})
    for fichero in (datos / "bronze" / "fuente=carrefour" / f"fecha={HOY}").glob("*.parquet"):
        fichero.unlink()
    _gold(datos, {fuente: AYER for fuente in CADENAS})
    _actual(datos, fecha=AYER)

    informe = _vigila(datos, ahora=dt.datetime(2026, 11, 5, 11, 30,
                                              tzinfo=ZoneInfo("Europe/Madrid")))

    assert informe["en_curso"] is True
    assert informe["estado"] == "aviso", informe["estado"]
    aviso = _aviso(informe, "en_curso")
    assert aviso["cadena"] == "carrefour" and aviso["gravedad"] == "aviso"
    assert "sin_pasada" not in _codigos(informe)
    assert _aviso(informe, "gold_pendiente")["gravedad"] == "aviso"
    assert all(a["gravedad"] == "aviso" for a in informe["avisos"]), "en marcha no es un fallo"


def test_una_pasada_que_empezo_y_no_termino_se_dice(datos):
    """La marca de ayer sigue ahi: la pasada murio y `run.py` solo lo cuenta en el log."""
    (datos / "ejecucion_en_curso.txt").write_text(f"{AYER} 10:14", encoding="utf-8")

    informe = _vigila(datos)

    aviso = _aviso(informe, "pasada_a_medias")
    assert AYER in aviso["texto"]


# ------------------------------------------------------------------ los avisos callados ---


def test_los_avisos_de_ayer_son_un_aviso_que_se_queda_callado(datos):
    (datos / "avisos.json").write_text(
        json.dumps({"cuando": f"{AYER}T12:00:00+01:00"}), encoding="utf-8")

    informe = _vigila(datos)

    aviso = _aviso(informe, "avisos_de_ayer")
    assert aviso["gravedad"] == "aviso"


def test_los_avisos_que_no_se_pudieron_mirar_se_dicen(datos):
    """La cadena imprime «no lo se» y sigue: eso, sin alguien que lo lea, es un aviso mudo."""
    (datos / "avisos.json").write_text(
        json.dumps({"cuando": f"{HOY}T12:00:00+01:00",
                    "error": "la base de datos no se alcanza desde aqui"}), encoding="utf-8")

    informe = _vigila(datos)

    aviso = _aviso(informe, "avisos_sin_mirar")
    assert "no se alcanza" in aviso["texto"]


def test_sin_nota_de_avisos_tambien_se_dice(datos):
    (datos / "avisos.json").unlink()

    assert "avisos_sin_mirar" in _codigos(_vigila(datos))


def test_dos_dias_sin_cerrar_la_cadena_es_un_aviso(datos):
    """Lo que de verdad hay que cazar: la tarea programada dejo de cerrar dias."""
    (datos / "ultima_ejecucion.txt").write_text(ANTEAYER + "\n", encoding="utf-8")

    aviso = _aviso(_vigila(datos), "cadena_parada")

    assert "2026-11-03" in aviso["texto"]


def test_sin_cobertura_declarada_de_hoy_es_aviso(datos):
    for ruta in (datos / "cobertura").glob(f"*-{HOY}.json"):
        ruta.unlink()

    aviso = _aviso(_vigila(datos), "cobertura_sin_declarar")

    assert aviso["gravedad"] == "aviso"


# -------------------------------------------------------------------- nada que leer es fallo ---


def test_sin_datos_no_puede_salir_cero(tmp_path):
    """Un `data/` vacio no es «todo bien»: es que no se puede decir nada, y eso es un fallo."""
    vacio = tmp_path / "vacio"
    vacio.mkdir()

    informe = vigilar_ingesta.vigila(datos=vacio, fecha=HOY)

    assert informe["estado"] == "fallo"
    assert vigilar_ingesta.main(["--datos", str(vacio), "--fecha", HOY]) == 1
    assert _aviso(informe, "sin_pasada")["gravedad"] == "fallo"
