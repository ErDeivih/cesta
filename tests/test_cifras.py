"""CIFRAS.md tiene que escribirlo alguien, no sólo decir que se escribe.

El fichero llevaba desde el 19 de septiembre de 2026 diciendo de sí mismo «se
reescribe entero después de cada pasada», y no lo reescribía nadie. La
consecuencia: `verificar_docs` cerraba **todos los días** con ocho cifras
caducadas que eran las del 19 esperando en un fichero que se suponía automático.

Un aviso que hay que descartar a mano cada día deja de leerse a la semana, y el
día que avise de algo de verdad tampoco se leerá.
"""
import duckdb
import pytest

from core import config
from projects.cesta import cifras, verificar_docs


@pytest.fixture
def gold(tmp_path, monkeypatch):
    """Un gold mínimo con las columnas que miran las comprobaciones."""
    def escribe(productos):
        con = duckdb.connect()
        con.execute("CREATE TABLE g (grupo_id BIGINT, fuente VARCHAR, ean VARCHAR,"
                    " nutriscore VARCHAR, comparacion_fiable BOOLEAN,"
                    " sellos VARCHAR, certificados VARCHAR, nutricion VARCHAR,"
                    " envase VARCHAR, promo_txt VARCHAR, promo_club BOOLEAN,"
                    " promo_solo_online BOOLEAN)")
        for p in productos:
            con.execute("INSERT INTO g VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", [
                p.get("grupo_id"), p["fuente"], p.get("ean"), p.get("nutriscore"),
                p.get("comparable", True), p.get("sellos"), p.get("certificados"),
                p.get("nutricion"), p.get("envase"), p.get("promo_txt"),
                p.get("promo_club", False), p.get("promo_solo_online", False)])
        (tmp_path / "gold").mkdir(exist_ok=True)
        con.execute(f"COPY g TO '{tmp_path / 'gold' / 'grupos.parquet'}' (FORMAT PARQUET)")
        con.close()

    monkeypatch.setattr(config, "DATA", tmp_path)
    monkeypatch.setattr(config, "GOLD", tmp_path / "gold")
    yield escribe


def test_las_cifras_escritas_son_las_que_el_verificador_va_a_buscar(gold, tmp_path,
                                                                    monkeypatch):
    """La prueba que cierra el círculo: se escribe y acto seguido se comprueba.

    Si el escritor y el comprobador tuvieran cada uno su SQL acabarían midiendo
    cosas distintas y el aviso volvería sin que nada estuviera mal. Comparten
    tabla justo para que esta prueba no pueda pasar por casualidad.
    """
    gold([{"fuente": "dia", "ean": "1", "grupo_id": 1},
          {"fuente": "aldi", "ean": "2", "grupo_id": 1},
          {"fuente": "dia", "ean": None, "grupo_id": None}])
    destino = tmp_path / "CIFRAS.md"
    monkeypatch.setattr(cifras, "DESTINO", destino)
    monkeypatch.setattr(verificar_docs, "DOCS", [destino])

    assert cifras.main() == 0
    assert verificar_docs.main() == 0, destino.read_text(encoding="utf-8")


def test_el_documento_lleva_la_fecha_de_la_ejecucion(gold, tmp_path, monkeypatch):
    from datetime import date
    gold([{"fuente": "dia", "ean": "1"}])
    monkeypatch.setattr(cifras, "DESTINO", tmp_path / "CIFRAS.md")
    texto = cifras.documento(date(2026, 9, 20))
    assert "20 de septiembre de 2026" in texto


def test_sin_gold_no_se_escribe_nada(tmp_path, monkeypatch):
    """Escribir un CIFRAS.md vacío sería peor: parecería que hoy no hay nada."""
    monkeypatch.setattr(config, "GOLD", tmp_path / "no-existe")
    destino = tmp_path / "CIFRAS.md"
    monkeypatch.setattr(cifras, "DESTINO", destino)
    assert cifras.main() == 0
    assert not destino.exists()


def test_una_comprobacion_nueva_no_se_queda_fuera_del_documento(gold, tmp_path,
                                                                monkeypatch):
    """Lo que se añada a COMPROBACIONES tiene que salir, aunque no se apartede.

    Si una cifra nueva no entrara en ningún apartado, desaparecería del
    documento y el verificador volvería a avisar de ella para siempre.
    """
    gold([{"fuente": "dia", "ean": "1"}])
    monkeypatch.setattr(cifras, "APARTADOS", (("Catalogo", ()),))
    texto = cifras.documento()
    for nombre, *_ in verificar_docs.COMPROBACIONES:
        assert nombre in texto, nombre
