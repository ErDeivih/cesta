"""Pedir fichas desde la cola: presupuesto, hash, proxima revision y errores bien separados.

Todo sin red: la descarga se inyecta. Lo que se fija aqui es el comportamiento del proceso, que es
donde se puede hacer dano en silencio: que respete el presupuesto, que un fallo de red no se confunda
con un dato que falta, que cierre la ficha con hash y revision, y que reanudar no repita.
"""
from __future__ import annotations

from datetime import datetime

import pytest

from core import inventario
from projects.cesta import fichas_lidl

FICHA = """
<script type="application/ld+json">
{"@type":"Product","name":"Galletas rellenas","sku":"11000174",
 "brand":{"name":"Sondey"},"description":"<ul><li>Rellenas.</li></ul>",
 "gtin13":["1234567890128"],"offers":[{"price":"1.49"}],
 "url":"https://www.lidl.es/p/x/p11000174"}
</script>"""


@pytest.fixture
def con(tmp_path):
    """Una cola con tres candidatos de Lidl, ya dados de alta."""
    con = inventario.conecta(tmp_path / "inventario.sqlite")
    for i in (11000174, 11000175, 11000176):
        inventario.alta(con, "lidl", str(i), url=f"https://www.lidl.es/p/x/p{i}")
    return con


def test_una_ficha_leida_cierra_su_fila_con_hash_y_revision(con):
    cuenta = fichas_lidl.procesa(con, 1, fetch=lambda url: FICHA,
                                ahora=datetime(2026, 10, 7, 10, 0))
    assert cuenta == {"leidas": 1, "correctas": 1, "no_publicado": 0, "error_temporal": 0}
    fila = con.execute("SELECT * FROM fichas").fetchone()
    assert fila["estado"] == inventario.CORRECTO
    assert fila["hash_util"] and len(fila["hash_util"]) == 16
    assert fila["parser_version"] == fichas_lidl.PARSER_VERSION
    assert fila["proxima_revision"] == "2026-11-06"
    assert fila["lease_hasta"] is None, "al cerrar se suelta el lease"


def test_el_presupuesto_se_respeta_y_no_hay_bucle_hasta_agotar(con):
    """Una ejecucion con limite 2 pide dos fichas y para, aunque queden candidatos."""
    pedidas = []

    def fetch(url):
        pedidas.append(url)
        return FICHA

    cuenta = fichas_lidl.procesa(con, 2, fetch=fetch)
    assert cuenta["leidas"] == 2
    assert len(pedidas) == 2
    pendientes = con.execute("SELECT count(*) FROM fichas WHERE estado = ?",
                             (inventario.PENDIENTE,)).fetchone()[0]
    assert pendientes == 1, "la tercera sigue esperando: no se agota la cola en una ejecucion"


def test_un_fallo_de_red_no_es_un_dato_que_falta(con):
    """Se reintenta la ficha; no se apunta como si el producto no tuviera ficha."""
    def fetch(url):
        raise TimeoutError("la red no contesta")

    cuenta = fichas_lidl.procesa(con, 1, fetch=fetch)
    assert cuenta["error_temporal"] == 1 and cuenta["no_publicado"] == 0
    fila = con.execute("SELECT * FROM fichas").fetchone()
    assert fila["estado"] == inventario.ERROR_TEMPORAL
    assert "TimeoutError" in fila["ultimo_resultado"]
    assert fila["proxima_revision"] is None, "un error temporal se reintenta, no se agenda a 30 dias"


def test_una_pagina_sin_ficha_es_un_dato_sobre_la_fuente(con):
    """La pagina vive pero no publica el detalle: `no_publicado`, que no es un fallo nuestro."""
    cuenta = fichas_lidl.procesa(con, 1, fetch=lambda url: "<html>sin datos</html>")
    assert cuenta["no_publicado"] == 1
    fila = con.execute("SELECT * FROM fichas").fetchone()
    assert fila["estado"] == inventario.NO_PUBLICADO
    assert fila["proxima_revision"] is not None, "se volvera a mirar por si publica mas adelante"


def test_reanudar_no_repite_la_que_ya_esta_correcta(con):
    """El encargo lo pide con estas palabras: reanudar sin duplicar."""
    fichas_lidl.procesa(con, 1, fetch=lambda url: FICHA, ahora=datetime(2026, 10, 7, 10, 0))
    # Otra pasada, el mismo dia: la correcta no vuelve (su revision es a 30 dias).
    cuenta = fichas_lidl.procesa(con, 5, fetch=lambda url: FICHA,
                                ahora=datetime(2026, 10, 7, 11, 0))
    assert cuenta["leidas"] == 2, "no puede volver a por la que ya esta correcta"
    # Y pasados los 30 dias, si vuelve.
    cuenta = fichas_lidl.procesa(con, 5, fetch=lambda url: FICHA,
                                ahora=datetime(2026, 11, 7, 11, 0))
    assert cuenta["leidas"] == 3, "vencida la revision, se vuelve a mirar"


def _datos(**cambios):
    base = {"nombre": "Galletas rellenas", "marca": "Sondey", "ean": "4056489123459",
            "gtin_invalido": None, "descripcion": "Rellenas de crema de chocolate.",
            "url": "https://www.lidl.es/p/x/p1", "imagen": "https://cdn/x.jpg",
            "precio_cent": 149}
    base.update(cambios)
    return base


def test_el_hash_no_cambia_si_cambia_el_precio():
    """**El precio no es parte de la ficha.** *Antes si lo era: una oferta nueva marcaba «la ficha
    cambio», y la columna que existe para vigilar la ficha vigilaba el escaparate.*"""
    assert fichas_lidl._hash_util(_datos()) == fichas_lidl._hash_util(_datos(precio_cent=99))


def test_el_hash_cambia_si_cambia_el_gtin_invalido():
    """**Cuando el codigo no valida, `ean` es `None` y el codigo vive en `gtin_invalido`.**

    Hashear `ean` a secas dejaba que **dos fichas con GTIN invalido distinto** dieran el mismo hash.
    """
    a = fichas_lidl._hash_util(_datos(ean=None, gtin_invalido="4056489123456"))
    b = fichas_lidl._hash_util(_datos(ean=None, gtin_invalido="4056489123450"))
    assert a != b, "dos codigos invalidos distintos no pueden compartir huella"


def test_el_hash_cambia_si_cambian_la_descripcion_o_la_imagen():
    """Los dos campos de contenido que la fuente **si** publica."""
    assert fichas_lidl._hash_util(_datos()) != fichas_lidl._hash_util(_datos(descripcion="Otra cosa"))
    assert fichas_lidl._hash_util(_datos()) != fichas_lidl._hash_util(_datos(imagen="https://cdn/y.jpg"))
