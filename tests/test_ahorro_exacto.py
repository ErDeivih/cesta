"""*** LA HORQUILLA DEL GRUPO NO ES EL AHORRO DEL ARTICULO. ***

*El 18/10/2026 la ficha del azafran `dia/147509` decia «cuesta un 41 % mas que en Mercadona»
comparando un **Pote** con un **Hacendado**: otro EAN, otro articulo.*

*La raiz estaba en `catalogo.grupo()`: `ahorro_pct` sale de la horquilla del grupo
(`unidad` y `comparable`, **sin mirar el EAN**).* *Y eso es **verdad**: la horquilla existe.*

*Lo que se añade aqui es **el dato que faltaba**: por cada producto, cuanto se ahorra contra
**su mismo articulo** -- mismo EAN y misma base.* *Sin EAN no se afirma: queda `None`, que
**no es cero**.*

*Y `ahorro_pct` **no se toca**, porque seis pantallas lo usan como horquilla y cambiarlo las
romperia en silencio.*
"""

import os
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def gold(tmp_path_factory) -> Path:
    """*El gold del apartado 8, construido con el generador versionado.*"""
    from plataforma.construye_gold_ensayo import construye

    destino = tmp_path_factory.mktemp("gold8")
    construye(destino)
    return destino


@pytest.fixture(scope="module")
def catalogo(gold):
    os.environ["CESTA_GOLD"] = str(gold)
    sys.modules.pop("plataforma.api.catalogo", None)

    sys.modules.pop("plataforma.api.ajustes", None)
    from plataforma.api import catalogo as mod

    return mod


def test_la_horquilla_del_grupo_se_conserva(catalogo) -> None:
    """*`ahorro_pct` sigue siendo la horquilla: de 120 a 135 es un 12,5 %.*"""
    g = catalogo.grupo(900001)
    assert g["ahorro_pct"] == 12.5
    assert g["ahorro_cent"] == 15


def test_dos_marcas_distintas_NO_tienen_ahorro_exacto(catalogo) -> None:
    """*Arroz A y arroz B: mismo grupo, **otro EAN**. No hay ahorro del articulo.*"""
    g = catalogo.grupo(900001)
    for p in g["productos"]:
        assert p["ahorro_exacto_pct"] is None, (
            f"{p['marca']} no puede tener ahorro exacto: su unico comparable es otra marca"
        )
        assert p["ahorro_exacto_cent"] is None


def test_y_None_no_es_cero(catalogo) -> None:
    """*La diferencia importa: `None` es «no hay con que comparar», `0` es «no te ahorras nada».*
    *Confundirlos fue el defecto del `ahorro_pct: 0.0` como centinela.*"""
    g = catalogo.grupo(900001)
    exactos = [p["ahorro_exacto_pct"] for p in g["productos"]]
    assert all(x is None for x in exactos)
    assert not any(x == 0 for x in exactos), "None no puede convertirse en 0"


def test_la_leche_y_los_huevos_no_presentan_ahorro(catalogo) -> None:
    """*Una sola oferta por grupo: no hay horquilla ni ahorro exacto que anunciar.*"""
    for gid in (900002, 900003):
        g = catalogo.grupo(gid)
        assert g["ahorro_pct"] == 0.0
        assert g["ahorro_cent"] == 0
        assert len(g["productos"]) == 1
