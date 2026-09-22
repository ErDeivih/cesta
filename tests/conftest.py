"""Lo que vale para todas las pruebas.

Nada de esto prueba codigo: son las dos redes que impiden que una prueba pase o
falle segun lo que haya ese dia en el disco. Una prueba que depende del estado de
`data/gold/` no mide el codigo, mide el calendario.
"""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def sin_vectores_en_disco(monkeypatch):
    """Apaga el cache de embeddings para las pruebas que no van de eso.

    `core.matching.enlaces()` lee `data/gold/embedding.parquet` si existe y lo mete
    como un canal mas. Eso esta bien en produccion y es terrible en una prueba:
    el mismo test pasa o falla segun si alguien acaba de calcular los vectores.

    Paso de verdad el 22 de septiembre de 2026, con el calculo de vectores a
    medias: dos pruebas de enlaces por EAN empezaron a fallar sin que nadie
    tocara el emparejador.

    Las pruebas que SI van de embeddings piden el modulo entero y usan las
    funciones de verdad, que no pasan por aqui.
    """
    from core import embeddings

    monkeypatch.setattr(embeddings, "carga", lambda *a, **k: {})
    # `disponible()` es la otra puerta, y la que de verdad se usa desde que el
    # canal de vectores lee el parquet **en SQL** en vez de traerlo a Python.
    # Apagando solo `carga()` las pruebas volverian a leer `data/gold/` de verdad.
    monkeypatch.setattr(embeddings, "disponible", lambda *a, **k: None)
