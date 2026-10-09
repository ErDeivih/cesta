"""La ruta de la ficha existe y esta publicada, y el diario conserva las suyas.

Se comprueba contra `app.openapi()["paths"]`, que es el contrato que la aplicacion publica y se construye
sin servidor y sin Docker. La primera version leia `app.routes` y no encontraba **nada** -- ni lo nuevo ni
lo que ya habia --, porque los routers incluidos son objetos anidados y sus rutas estan dentro.
"""
from __future__ import annotations


def _rutas_publicadas() -> set[str]:
    from plataforma.api.main import app

    return set(app.openapi()["paths"])


def test_la_ruta_de_la_ficha_esta_publicada():
    assert "/api/diario/desde-ficha" in _rutas_publicadas()


def test_las_rutas_del_diario_siguen_estando():
    """La nueva no ha sustituido a ninguna: el diario tenia cuatro y ahora cinco."""
    rutas = _rutas_publicadas()
    for esperada in ("/api/diario/rango", "/api/diario/{fecha}",
                     "/api/diario/entrada/{entrada_id}"):
        assert esperada in rutas, esperada


def test_la_ruta_de_recetas_sigue_publicada():
    """Y el recetario tambien, que es la otra mitad de lo que se va a enchufar."""
    assert "/api/recetas" in _rutas_publicadas()


def test_la_aritmetica_del_endpoint_es_la_del_modulo():
    """El endpoint no calcula: llama. Si esto se separara, habria dos cuentas de lo mismo."""
    from core import diario

    valores = diario.de_ficha({"kcal_100g": 485.0}, 150)
    assert valores["kcal"] == 727.5
    assert valores["proteinas_g"] is None      # lo que no se sabe no es cero
