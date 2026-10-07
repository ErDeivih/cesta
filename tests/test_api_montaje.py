"""Que las rutas nuevas esten MONTADAS, no solo escritas.

La suite puede estar verde con los manejadores llamados a mano y el endpoint sin montar: paso ayer. Esta
prueba mira la fuente que no interpreta -- los caminos que la aplicacion declara en su OpenAPI -- porque
"la funcion existe" y "el endpoint se alcanza" son dos cosas distintas y solo la segunda sirve.
"""
from __future__ import annotations

from plataforma.api.main import app


def _caminos() -> set[str]:
    return set(app.openapi()["paths"])


def test_la_api_de_recetas_esta_montada_y_no_solo_escrita():
    caminos = _caminos()
    for esperado in ("/api/recetas", "/api/recetas/plan", "/api/recetas/{receta_id}",
                     "/api/recetas/{receta_id}/archivar"):
        assert esperado in caminos, f"{esperado} no esta montado en la aplicacion"


def test_la_api_del_diario_esta_montada():
    caminos = _caminos()
    for esperado in ("/api/diario/rango", "/api/diario/{fecha}", "/api/diario",
                     "/api/diario/entrada/{entrada_id}"):
        assert esperado in caminos, f"{esperado} no esta montado en la aplicacion"


def test_la_api_de_la_cesta_sigue_donde_estaba():
    """Una prueba de montaje que solo mira lo nuevo no protege lo viejo: se comprueba tambien lo de antes."""
    caminos = _caminos()
    assert "/api/estado" in caminos and "/api/panel/matching" in caminos
