"""*** EL TEXTO DEL ERROR TIENE QUE QUEDAR EN ALGUN SITIO. ***

*El 18/10/2026 Carrefour fallo en **5,2 segundos** con **cero** filas, despues de haber traido
16 561 el dia anterior.* *`runs.csv` guardo `errores=1` -- **cuantos**, no **cuales** --, y en
disco no quedo nada mas: ni raw, ni bronze, ni un mensaje.*

*Asi que la causa no se pudo investigar.* *** El siguiente fallo habria sido igual de invisible.***

*Estas pruebas fijan lo que ahora si queda: el texto, con su fecha y su fuente, en un fichero
aparte que rota por tamano -- sin tocar las seis columnas de `runs.csv`, de las que dependen
`check_drift` y sus pruebas.*
"""


import pytest

from core import runlog


@pytest.fixture()
def log(tmp_path, monkeypatch):
    monkeypatch.setattr(runlog, "LOG_ERRORES", tmp_path / "errores.log")
    monkeypatch.setattr(runlog, "MAXIMO_LOG_ERRORES", 200)
    return tmp_path / "errores.log"


def test_el_texto_del_error_queda_con_fecha_y_fuente(log) -> None:
    runlog.log_error("carrefour", "HTTP 200 con desafio, no es catalogo vacio")
    assert log.exists()
    linea = log.read_text(encoding="utf-8").strip()
    partes = linea.split("\t")
    assert len(partes) == 3, "fecha, fuente y texto"
    assert partes[1] == "carrefour"
    assert "desafio" in partes[2]
    assert partes[0].startswith("20"), "la fecha ISO empieza por el año"


def test_un_texto_con_saltos_de_linea_no_rompe_el_fichero(log) -> None:
    """*El motivo de que esto no vaya en `runs.csv`: un texto multilinea dentro de una columna
    CSV lo rompe, y el CSV es la unica prueba de que una pasada ocurrio.*"""
    runlog.log_error("dia", "linea uno\nlinea dos\ntraceback...")
    lineas = log.read_text(encoding="utf-8").strip().split("\n")
    assert len(lineas) == 1, "el texto se aplana: una entrada, una linea"
    assert "linea uno | linea dos" in lineas[0]


def test_rota_cuando_crece_demasiado(log) -> None:
    for _ in range(20):
        runlog.log_error("aldi", "x" * 60)
    assert log.exists(), "el log sigue escribiendose despues de rotar"
    anterior = log.with_suffix(log.suffix + ".1")
    assert anterior.exists(), "el anterior se conserva como .1, no se borra"


def test_no_toca_las_columnas_de_runs_csv(log, tmp_path, monkeypatch) -> None:
    """*** Y la prueba que protege lo que ya funcionaba. ***"""
    monkeypatch.setattr(runlog, "LOG", tmp_path / "runs.csv")
    runlog.log_error("carrefour", "algo falló")
    runlog.log_run("carrefour", filas=0, errores=1, segundos=5.2, completa=False)
    cabecera = (tmp_path / "runs.csv").read_text(encoding="utf-8").splitlines()[0]
    assert cabecera == "ts,fuente,filas,errores,segundos,ok"
