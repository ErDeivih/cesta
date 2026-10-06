"""El manifiesto de publicacion (T02): que firma, y que no puede romper.

Lo que se fija aqui: que lleve la version y la huella de la politica de alcance (sin eso no se puede
decir con que reglas se publico un catalogo), que la huella cambie cuando cambia el contenido, que
se escriba de forma atomica, que una cadena sin captura de hoy salga como aviso y no como cero, y
que un fallo suyo no lance.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from core import manifiesto


def test_lleva_la_version_y_la_huella_de_la_politica():
    """Es lo que permite decir con que reglas se publico: si cambia una regla, cambia el manifiesto."""
    datos = manifiesto.construye(date(2026, 10, 6))
    assert datos["politica_alcance"]["version"] >= 2
    assert len(datos["politica_alcance"]["sha256"]) == 12


def test_la_huella_distingue_contenidos(tmp_path):
    uno = tmp_path / "a.bin"
    otro = tmp_path / "b.bin"
    uno.write_bytes(b"catalogo A")
    otro.write_bytes(b"catalogo B")
    assert manifiesto.huella(uno) != manifiesto.huella(otro)
    assert manifiesto.huella(uno) == manifiesto.huella(uno)
    assert manifiesto.huella(tmp_path / "no-existe") is None


def test_dice_que_ficheros_de_gold_se_publican():
    datos = manifiesto.construye(date(2026, 10, 6))
    for nombre in ("grupos.parquet", "enlaces.parquet", "precio_diario.parquet"):
        assert nombre in datos["ficheros"]
        assert datos["ficheros"][nombre]["sha256"], f"{nombre} sin huella"
    # `grupos_anterior` es copia de trabajo, no publicacion.
    assert "grupos_anterior.parquet" not in datos["ficheros"]


def test_la_cobertura_declarada_se_recoge():
    """Lidl declara que son ofertas conocidas: la aplicacion tiene que poder ensenarlo."""
    datos = manifiesto.construye(date(2026, 10, 6))
    assert isinstance(datos["cobertura_declarada"], dict)


def test_una_cadena_sin_captura_de_hoy_es_un_aviso_no_un_cero():
    datos = manifiesto.construye(date(1999, 1, 1))     # una fecha en la que nada es de hoy
    assert datos["avisos"]
    if datos["fuentes"]:
        assert any("sin captura de hoy" in a for a in datos["avisos"])


def test_escribe_de_forma_atomica_y_no_deja_temporales(tmp_path, monkeypatch):
    monkeypatch.setattr(manifiesto, "GOLD", tmp_path)
    monkeypatch.setattr(manifiesto, "MANIFIESTO", tmp_path / "manifiesto.json")
    ruta = manifiesto.escribe(date(2026, 10, 6))
    assert ruta is not None and ruta.exists()
    assert not list(tmp_path.glob("*.tmp")), "ha quedado un temporal: el renombrado no fue atomico"
    json.loads(ruta.read_text(encoding="utf-8"))       # es JSON valido


def test_un_fallo_escribiendo_no_lanza(tmp_path, monkeypatch):
    """El dia no se cae por el manifiesto: se avisa y se sigue."""
    monkeypatch.setattr(manifiesto, "GOLD", Path("Z:/no/existe"))
    monkeypatch.setattr(manifiesto, "MANIFIESTO", Path("Z:/no/existe/manifiesto.json"))
    assert manifiesto.escribe() is None                # no lanza
