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


@pytest.fixture()
def catalogo(gold, monkeypatch):
    """*El catalogo apuntando al gold del apartado 8, SIN reimportar el modulo.*

    *Antes esto hacia `sys.modules.pop("plataforma.api.catalogo")` y lo volvia a importar.*
    *Funcionaba sola y rompia la suite entera: los demas modulos se quedaban con la
    referencia vieja, y a partir de ahi habia dos `catalogo` vivos.*
    """
    import dataclasses

    from plataforma.api import catalogo as mod

    monkeypatch.setattr(mod, "AJUSTES", dataclasses.replace(mod.AJUSTES, gold=gold))
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


def test_con_dos_cadenas_el_ahorro_exacto_es_un_numero_de_verdad(monkeypatch) -> None:
    """*** El caso positivo, que con una sola cadena no se podia probar. ***

    *Con `segunda_cadena=True`, el arroz A esta en **dos** cadenas con el **mismo EAN**: 110 y
    120.* *Asi que su ahorro exacto es **9,1 %** -- y no es la horquilla del grupo, que es **22,7 %**
    (de 110 a 135, que son **articulos distintos**).*

    *** Que los dos numeros sean distintos es la prueba de que el contrato los distingue. ***
    *Con una sola cadena los dos eran `None` o `0`, y no se podia demostrar nada.*
    """
    import tempfile
    from pathlib import Path as _P

    from plataforma.construye_gold_ensayo import construye

    destino = _P(tempfile.mkdtemp(prefix="gold2-"))
    construye(destino, segunda_cadena=True)
    # *** NO BASTA CON `sys.modules.pop`. ***
    # *Cuando ya se importo `catalogo` en este mismo fichero, el modulo tiene la referencia vieja a
    # `AJUSTES`, y volver a importarlo devuelve **el mismo objeto**: el gold seguia siendo el de la
    # primera prueba, con una sola cadena, y `grupo()` devolvia `cadenas = 1`.*
    # *Se cambia el atributo y `monkeypatch` lo devuelve como estaba al terminar.*
    # *`AJUSTES` es un dataclass **congelado**: `setattr` da FrozenInstanceError.*
    # *Se sustituye el nombre entero en el modulo, que es lo que lee `grupo()`.*
    import dataclasses

    from plataforma.api import catalogo as mod

    monkeypatch.setattr(mod, "AJUSTES", dataclasses.replace(mod.AJUSTES, gold=destino))
    g = mod.grupo(900001)
    assert g["cadenas"] == 2
    # *La horquilla del grupo.*
    assert g["ahorro_pct"] == 22.7
    # *Y el ahorro contra su mismo articulo, que es otro numero.*
    por_fuente = {(p["marca"], p["fuente"]): p for p in g["productos"]}
    a_en_ensayo = por_fuente[("Marca A", "ensayo")]
    assert a_en_ensayo["ahorro_exacto_pct"] == 9.1
    assert a_en_ensayo["ahorro_exacto_cent"] == 10
    # *El mas barato de su propio EAN no se ahorra nada, y es 0, no None: hay con que comparar.*
    a_en_b = por_fuente[("Marca A", "ensayo-b")]
    assert a_en_b["ahorro_exacto_pct"] == 0.0
    # *** Y la comprobacion que importa ***: *la horquilla y el exacto NO coinciden.*
    assert g["ahorro_pct"] != a_en_ensayo["ahorro_exacto_pct"], (
        "si coincidieran, no se podria demostrar que el contrato los distingue"
    )


def test_la_leche_y_los_huevos_no_presentan_ahorro(catalogo) -> None:
    """*Una sola oferta por grupo: no hay horquilla ni ahorro exacto que anunciar.*"""
    for gid in (900002, 900003):
        g = catalogo.grupo(gid)
        assert g["ahorro_pct"] == 0.0
        assert g["ahorro_cent"] == 0
        assert len(g["productos"]) == 1
