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

# ---------------------------------------------------------------- la base ---

# *** SI NO HAY BASE, LOS TESTS QUE LA NECESITAN SE SALTAN. NO SE CUELGAN. ***
#
# *El 21 de octubre de 2026 se intento correr `pytest -q tests/` sin PostgreSQL y **se quedo seis minutos sin
# sacar una linea**: cada intento de conexion espera su `connect_timeout`, y son cientos.*
#
# *** Y de ahi salio una frase que estuvo diecinueve rondas en el estado: «la suite no se puede correr». ***
# *Falso: **1.345 pruebas de los 135 ficheros que no tocan la base pasan en cinco minutos**.*
# *Lo que pasa es que, sin este bloque, **la suite no falla rapido: se cuelga**, y un cuelgue parece un
# impedimento.*
#
# *Se mira una vez por sesion, con **dos segundos** de tope, y si no hay base se saltan los ficheros que la
# usan -- con el motivo escrito, para que se vea en el resumen.*
_SIN_BASE = None

# *** La marca, lo mas estrecha posible, y por que. ***
#
# *La primera version miraba tambien `plataforma.api` y `almacen`, y saltaba **111 ficheros**.*
# *Se probaron tres de ellos sin base -- `test_ahorro_exacto`, `test_analisis`, `test_alertas` -- y
# **33 pruebas pasaron en 7,2 s**.* *** O sea que 100 de los 111 no necesitaban la base: solo la
# mencionaban. ***
#
# *** Se probo a estrecharla a `psycopg`/`CESTA_POSTGRES`/`ConnectionPool`, y NO sirve: con esa marca
# `pytest -q tests/` se vuelve a colgar. *** *Los ficheros que caen solo por la marca ancha no importan
# `psycopg`, pero **llaman a la API, y la API conecta**.*
#
# *Asi que la marca se queda ancha -- conserva el «no se cuelga» -- y se dice lo que se ha medido:*
# *tres de esos ficheros (`test_ahorro_exacto`, `test_analisis`, `test_alertas`) **pasan sin base, 33
# pruebas en 7,2 s**.* *** Ese es el suelo medido de pruebas que este salto esconde: al menos 33. ***
# *No se sabe cuantas mas hay sin irlas sacando de una en una, y por eso se dice «al menos».*
#
# *** Y donde esta el cuelgue, que se busco y se encontro: *** *no es el `connect_timeout` de la conexion
# -- se probo un DSN que rechaza al instante (`127.0.0.1:1`) y **seguia colgado**.*
#
#     `almacen.py:59`  `def arranca(espera: float = 30)`
#     `almacen.py:80`  `tope = max(int(espera), 3)`          -> 30
#     `almacen.py:99`  `_pool.wait(timeout=tope * 2 + 5)`    -> **65 segundos por intento**
#
# *Y `arranca()` se llama por modulo.* *** 65 s x N no es lento: es un cuelgue. ***
#
# *El arreglo de verdad, para cuando se retome: **`arranca(espera=1)` en las pruebas**, o una marca de
# pytest que lo haga.* *No se hace aqui porque toca `plataforma/api/almacen.py` y hay que verlo con la base
# delante.*
_MARCAS = ("plataforma.api", "plataforma.almacen", "almacen", "psycopg")


def _hay_base() -> bool:
    """*Un unico intento, corto. Si no contesta en dos segundos, no hay base.*"""
    global _SIN_BASE
    if _SIN_BASE is not None:
        return not _SIN_BASE
    try:
        import psycopg

        from plataforma.api.ajustes import AJUSTES

        psycopg.connect(AJUSTES.postgres, connect_timeout=2).close()
        _SIN_BASE = False
    except (OSError, RuntimeError, psycopg.Error):
        # *** Aqui coger `Exception` es lo correcto y aun asi ruff tiene razon en avisar. ***
        # *Lo que se pregunta es «¿hay base?», y **cualquier** fallo contesta que no: que no exista el
        # modulo, que la variable este mal, que la red no llegue, que el servidor rechace.* *Estrechar la
        # lista haria que un fallo no previsto se convirtiera en un `pytest` que no arranca.*
        # *Se nombran los tres que de verdad ocurren, y se deja constancia del motivo.*
        _SIN_BASE = True
    return not _SIN_BASE


def pytest_collection_modifyitems(config, items):
    """*Salta los tests de base cuando no la hay, en vez de dejar que esperen.*

    *Se puede apagar con `CESTA_SALTAR_SIN_BASE=0`, y hace falta para una cosa concreta: **medir si un
    fichero necesita la base de verdad o solo la menciona**.* *Sin la salida, el propio salto impide
    averiguarlo.*
    """
    import os

    if os.environ.get("CESTA_SALTAR_SIN_BASE", "1") != "1":
        return
    if _hay_base():
        return
    import pytest as _pytest

    marca = _pytest.mark.skip(reason="sin PostgreSQL: este fichero necesita la base")
    saltados = 0
    for item in items:
        fichero = getattr(item, "fspath", None)
        if fichero is None:
            continue
        try:
            fuente = fichero.read_text(encoding="utf-8")
        except OSError:
            continue
        if any(m in fuente for m in _MARCAS):
            item.add_marker(marca)
            saltados += 1
    if saltados:
        print(f"\n  sin base: {saltados} pruebas de PostgreSQL saltadas")

