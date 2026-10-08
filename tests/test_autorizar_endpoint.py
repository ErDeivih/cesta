"""El endpoint de autorizar existe, pide permiso de escritura y lee de la base.

Las pruebas de `tests/` sustituyen PostgreSQL a proposito, asi que aqui no se puede llamar de verdad al
endpoint: lo que se comprueba es lo que **no** depende de la base y que si se puede afirmar leyendo el codigo
-- que la puerta es la de escritura, que la autorizacion se lee de la base y no del cuerpo, y que las
respuestas de "no existe" y "de otro" son la misma.
"""
from __future__ import annotations

from pathlib import Path

from plataforma.api import main


def _fuente() -> str:
    return Path(main.__file__).read_text(encoding="utf-8")


def test_el_endpoint_de_autorizar_existe():
    fuente = _fuente()
    assert '@app.post("/api/listas/{lista_id}/lineas/{linea_id}/autorizar")' in fuente
    assert "def autorizar_linea(" in fuente


def test_autorizar_pide_permiso_de_ESCRITURA():
    """No basta con poder mirar la lista: autorizar la cambia para todos."""
    fuente = _fuente()
    assert "_acceso(lista_id, usuario, hace_falta_escribir=True)" in fuente


def test_la_autorizacion_se_lee_de_la_base():
    fuente = _fuente()
    assert "almacen.autorizacion_de(lista_id)" in fuente
    assert "_autorizadas.get(str(ln.get(\"id\")), False)" in fuente


def test_no_se_distingue_entre_no_existe_y_no_es_tuya():
    """404 para las dos: decir cual existe seria contarlo."""
    fuente = _fuente()
    assert 'detail="esa linea no esta en esa lista"' in fuente


def test_la_autorizacion_entra_en_todos_los_sitios_que_calculan_precios():
    """La estimacion de la lista y el reparto por tiendas: los dos deciden con `autorizada`."""
    fuente = _fuente()
    assert fuente.count("almacen.autorizacion_de(lista_id)") >= 2, \
        "el cruce tiene que estar en todos los sitios donde se reunen las lineas"
