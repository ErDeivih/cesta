"""F05 (fase 2): **el ejecutor de fichas de Carrefour, probado sin red.**

*Es el primero que no puede leer la URL de la cola*: medido, **sólo las filas de Lidl la traen** (0 de 17.283
en Carrefour), porque `inventario.enganche` levanta la cola de bronze leyendo sólo `id_fuente`.

**Así que la URL se resuelve del catálogo** -- *y estas pruebas lo comprueban con un catálogo de mentira, sin
red y sin tocar `data/inventario.sqlite`.*
"""
from __future__ import annotations

import pytest


@pytest.fixture()
def cola(tmp_path):
    """Una cola con el esquema **del propio proyecto**. *No se toca la de verdad.*"""
    from core import inventario

    return inventario.conecta(tmp_path / "fichas.sqlite")


# **El HTML real**, el mismo que usa el lector: aceite de oliva, 900 kcal y 100 g de grasa por 100 g.
HTML = (
    '<h3 class="nutrition__info-title">Información nutricional</h3>'
    '<p class="nutrition-graph__info-text">Valores medios por 100 g.</p>'
    '<div data-cal="900 Kcal" data-fa="100 g" data-h="0 g" data-kj="3700 KJ" data-p="0 g" '
    'data-s="0 g" class="nutrition-graph__graphic-svg"></div>'
)

# Y una pagina que **no** trae tabla -- *como los listados que el colector captura.*
SIN_TABLA = "<html><body><h1>Platos preparados</h1></body></html>"


def test_pide_la_ficha_y_marca_correcto(cola):
    """**El camino bueno**: entra a la cola, se le da su URL del catálogo, y la tabla se guarda."""
    from core import inventario
    from projects.cesta import fichas_carrefour as fx

    inventario.alta(cola, "carrefour", "824301999")
    cuenta = fx.procesa(cola, 5, fetch=lambda url: HTML,
                        urls={"824301999": "https://www.carrefour.es/.../R-824301999/p"})

    assert cuenta["correctas"] == 1, cuenta
    fila = cola.execute("SELECT estado, ultimo_resultado, hash_util, evidencia FROM fichas").fetchone()
    assert fila["estado"] == inventario.CORRECTO
    assert "100 g" in (fila["ultimo_resultado"] or ""), (
        "el resultado tiene que decir la base: sin ella la tabla no se puede comparar")
    assert fila["hash_util"], "y el hash del contenido util, para detectar que cambio"
    assert "carrefour.es" in (fila["evidencia"] or ""), "y de donde se leyo"


def test_la_url_se_resuelve_del_catalogo(cola):
    """**La pieza que el ejecutor de Lidl no necesita.** *La cola no trae URL para Carrefour: 0 de 17.283.*"""
    from core import inventario
    from projects.cesta import fichas_carrefour as fx

    inventario.alta(cola, "carrefour", "824301999")
    pedidas: list[str] = []

    fx.procesa(cola, 5, fetch=lambda url: (pedidas.append(url), HTML)[1],
               urls={"824301999": "https://www.carrefour.es/.../R-824301999/p"})

    assert pedidas == ["https://www.carrefour.es/.../R-824301999/p"], (
        "la peticion tiene que ir a la URL del catalogo, que es de donde sale")


def test_sin_url_no_se_pide_nada_y_se_dice(cola):
    """**Un producto que no está en el catálogo de hoy no tiene URL, y eso es un resultado.**

    *Sin este camino, el ejecutor habria fallado en la primera fila con `fila["url"] is None`.* **Y no se
    pide nada: no hay a donde.**
    """
    from core import inventario
    from projects.cesta import fichas_carrefour as fx

    inventario.alta(cola, "carrefour", "999")
    pedidas: list[str] = []

    cuenta = fx.procesa(cola, 5, fetch=lambda url: pedidas.append(url), urls={})

    assert cuenta["sin_url"] == 1, cuenta
    assert pedidas == [], "sin URL no se pide nada"
    fila = cola.execute("SELECT estado, ultimo_resultado FROM fichas").fetchone()
    assert fila["estado"] == inventario.NO_PUBLICADO
    assert "sin url" in (fila["ultimo_resultado"] or "").lower()


def test_una_pagina_sin_tabla_no_es_un_fallo_nuestro(cola):
    """**Los listados no la traen** -- *y el colector captura listados.* **Es un dato sobre la fuente, no un
    error del ejecutor**, y por eso va a `NO_PUBLICA` y no a `ERROR_TEMPORAL`.
    """
    from core import inventario
    from projects.cesta import fichas_carrefour as fx

    inventario.alta(cola, "carrefour", "1")
    cuenta = fx.procesa(cola, 5, fetch=lambda url: SIN_TABLA, urls={"1": "https://x/p"})

    assert cuenta["no_publicado"] == 1, cuenta
    assert cola.execute("SELECT estado FROM fichas").fetchone()["estado"] == inventario.NO_PUBLICADO


def test_un_fallo_de_red_se_reintenta(cola):
    """*La red falla y se reintenta: no es culpa del producto.* **Y por eso va a `ERROR_TEMPORAL`, que es otra
    cosa que `NO_PUBLICA`.**
    """
    from core import inventario
    from projects.cesta import fichas_carrefour as fx

    def revienta(_url):
        raise TimeoutError("la red no contesta")

    inventario.alta(cola, "carrefour", "1")
    cuenta = fx.procesa(cola, 5, fetch=revienta, urls={"1": "https://x/p"})

    assert cuenta["error_temporal"] == 1, cuenta
    fila = cola.execute("SELECT estado, ultimo_resultado FROM fichas").fetchone()
    assert fila["estado"] == inventario.ERROR_TEMPORAL
    assert "TimeoutError" in (fila["ultimo_resultado"] or ""), "y el motivo, para poder mirarlo"


def test_el_limite_es_el_presupuesto(cola):
    """**No hay bucle hasta agotar.** *Pedir 17.283 fichas de golpe es una operacion de red de verdad.*"""
    from core import inventario
    from projects.cesta import fichas_carrefour as fx

    for i in range(6):
        inventario.alta(cola, "carrefour", str(i))
    urls = {str(i): f"https://x/{i}" for i in range(6)}

    cuenta = fx.procesa(cola, 2, fetch=lambda url: HTML, urls=urls)

    assert cuenta["correctas"] == 2, f"el limite tiene que respetarse: {cuenta}"
    pendientes = cola.execute(
        "SELECT count(*) FROM fichas WHERE estado = 'pendiente'").fetchone()[0]
    assert pendientes == 4, "y el resto sigue pendiente, para la siguiente ejecucion"


def test_el_hash_es_el_de_la_receta_de_la_cola():
    """**El mismo calculo que el ejecutor de Lidl.** *Uno distinto haria que la proxima pasada creyera que
    todo el contenido cambio.*
    """
    from projects.cesta import ficha_carrefour as fc
    from projects.cesta import fichas_carrefour as fx
    from projects.cesta.fichas_lidl import _hash_util

    datos = fc.lee(HTML)
    assert fx.PARSER_VERSION.startswith("carrefour-")
    # La receta es la misma: `CAMPOS_DE_FICHA` y sha256[:16].
    assert set(fc.CAMPOS_DE_FICHA) == {"nombre", "marca", "ean", "gtin_invalido", "descripcion",
                                       "url", "imagen"}
    assert len(fc.hash_util({"nombre": "x"})) == 16
    # Y con los mismos campos, los dos calculos coinciden.
    campos = {k: datos.get(k) for k in fc.CAMPOS_DE_FICHA}
    assert fc.hash_util(campos) == _hash_util(campos)
