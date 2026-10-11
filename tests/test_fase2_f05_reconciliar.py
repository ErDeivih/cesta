"""F05 (fase 2): **el mapeo del reconciliador, probado.**

*Medido:* la cola cuenta como pendiente **7.476 fichas que ya estan hechas** -- 4.655 de Dia y 2.821 de
Mercadona --, porque el colector las guarda en el maestro y **no avisa a la cola**.

*Para reconciliar hay que marcar `correcto` con el **mismo hash** que usaria el ejecutor*, y ese hash se
calcula sobre `CAMPOS_DE_FICHA` (`fichas_lidl.py:56`), con nombres **normalizados** que **los maestros no
usan**. **Traducirlos es de lo que va esto**, y estas pruebas fijan la traduccion.

*No llaman a la red ni tocan la cola.*
"""
from __future__ import annotations

import pytest

from projects.cesta import reconciliar_fichas as rf

# **Las formas reales**, copiadas de los maestros. *Dia guarda `{"name", "value"}`; Mercadona guarda el
# texto con marcado.*
DE_DIA = {
    "sku_id": "310847",
    "product_name": {"name": "Nombre específico de producto", "value": "Yogur natural"},
    "brand_description": {"name": "Marca", "value": "DIA"},
    "ean_code": "8480017328212",
    "ingredients": {"name": "Ingredientes", "value": "<p><strong>Leche&nbsp;</strong>entera.</p>"},
    "nutricion": '{"energia_kcal": 54, "proteinas": 3.3}',
    "nutricion_por": "100g",
}

DE_MERCADONA = {
    "id": "18290",
    "display_name": "Tarta de nata",
    "brand": "Hacendado",
    "ean": "8412345678901",
    "ingredients": "<strong>INGREDIENTES</strong>: nata, azúcar.",
    "allergens": "Contiene <strong>leche</strong>.",
}


def test_traduce_los_campos_de_dia():
    """**Los nombres de Dia no son los de la cola**: `product_name` -> `nombre`,
    `brand_description` -> `marca`, `ean_code` -> `ean`."""
    campos = rf.campos_de_ficha("dia", DE_DIA)

    assert campos["nombre"] == "Yogur natural"
    assert campos["marca"] == "DIA"
    assert campos["ean"] == "8480017328212"


def test_traduce_los_campos_de_mercadona():
    """*Los suyos son otros, y por eso el mapeo es por cadena y no uno solo.*"""
    campos = rf.campos_de_ficha("mercadona", DE_MERCADONA)

    assert campos["nombre"] == "Tarta de nata"
    assert campos["marca"] == "Hacendado"
    assert campos["ean"] == "8412345678901"


def test_quita_el_marcado_antes_de_hashear():
    """**El hash tiene que ser comparable.** *Si se calculara sobre el texto con `<strong>`, dos lecturas del
    mismo contenido con distinto envoltorio darian hashes distintos -- y el ejecutor no los reconoceria.*
    """
    campos = rf.campos_de_ficha("dia", DE_DIA)

    # Dia trae el nombre en una forma con `value`, y el ingrediente con `<p>` y `&nbsp;`.
    assert campos["nombre"] == "Yogur natural"
    assert not any("<" in v for v in campos.values()), campos


def test_una_cadena_desconocida_no_traduce_nada():
    """**Mejor no reconciliar que reconciliar con un mapeo adivinado.** *Un campo mal traducido escribiria
    en la cola un hash que no casa con el que escriba el ejecutor, y la proxima pasada creeria que todo
    cambio.*
    """
    assert rf.campos_de_ficha("aldi", DE_DIA) == {}
    assert rf.campos_de_ficha("carrefour", DE_MERCADONA) == {}
    assert rf.campos_de_ficha("dia", "no es un registro") == {}


def test_lo_que_la_fuente_no_trae_no_aparece():
    """*Un campo ausente no se rellena: `_hash_util` ya lo trata como cadena vacia, y rellenarlo aqui seria
    inventar un dato para que cuadre.*
    """
    campos = rf.campos_de_ficha("dia", {"sku_id": "1", "product_name": {"value": "Solo el nombre"}})

    assert campos == {"nombre": "Solo el nombre"}, campos


def test_el_dato_de_la_ficha_es_lo_que_cuenta():
    """**No basta con que el producto este en el maestro**: *tiene que tener su dato, o el reconciliador
    marcaria `correcto` una ficha vacia.*
    """
    # Con nutricion: si.
    assert rf.tiene_ficha("dia", DE_DIA) is True
    # Y con ingredientes, tambien -- *Mercadona no tiene nutricion y si ingredientes.*
    assert rf.tiene_ficha("mercadona", DE_MERCADONA) is True

    # **Pero un registro sin dato no cuenta**, aunque tenga nombre y marca.
    sin_dato = {"product_name": {"value": "Yogur"}, "brand_description": {"value": "DIA"}}
    assert rf.tiene_ficha("dia", sin_dato) is False

    # Y una cadena sin mapeo, nunca.
    assert rf.tiene_ficha("aldi", DE_DIA) is False


def test_los_maestros_reales_traen_lo_que_el_mapeo_espera():
    """**La prueba que vale**: sobre los maestros de verdad, no sobre uno que he escrito yo.

    *Si no hay maestros -- otra maquina -- se salta; pero cuando los hay, se comprueba.* **Es lo que
    convierte el mapeo en algo medido y no en una suposicion sobre nombres de campo.**
    """
    import gzip
    import json
    from pathlib import Path

    vistos = 0
    for fuente in ("dia", "mercadona"):
        p = Path("data/master") / f"{fuente}.json.gz"
        if not p.exists():
            continue
        maestro = json.loads(gzip.decompress(p.read_bytes()))
        for registro in list(maestro.values())[:400]:
            campos = rf.campos_de_ficha(fuente, registro)
            if campos:
                vistos += 1
                assert "nombre" in campos or "ean" in campos, (
                    f"{fuente}: un registro traducible sin nombre ni ean: {list(campos)}")
                assert not any("<" in v for v in campos.values()), (
                    f"{fuente}: queda marcado en {campos}")

    if vistos == 0:
        pytest.skip("no hay maestros con registros traducibles en data/master")


# ---------------------------------------------------------------------------------------------
# El reconciliador, sobre una cola de mentira -- sin red y sin tocar la de verdad.
# ---------------------------------------------------------------------------------------------


@pytest.fixture()
def cola(tmp_path):
    """Una cola con el esquema **del propio proyecto**, en un fichero temporal.

    *La primera version escribia el `CREATE TABLE` a mano y le faltaban columnas -- `descubierto_en` y
    otras --: el esquema de una tabla no se copia, se pide.* **`inventario.conecta` lo crea**, y asi la
    prueba no se queda atras cuando el esquema cambie.
    """
    from core import inventario

    return inventario.conecta(tmp_path / "fichas.sqlite")


def test_reconcilia_lo_que_ya_tiene_ficha(cola):
    """**El arreglo del defecto.** *Un pendiente cuya ficha ya esta en el maestro pasa a `correcto`.*"""
    from core import inventario
    from projects.cesta import reconciliar_fichas as rf

    inventario.alta(cola, "dia", "310847")
    cuenta = rf.reconcilia(cola, {"dia": {"310847": DE_DIA}})

    assert cuenta["reconciliadas"] == 1
    fila = cola.execute("SELECT estado, hash_util, evidencia FROM fichas").fetchone()
    assert fila["estado"] == inventario.CORRECTO
    assert fila["hash_util"], "tiene que quedar el hash: es lo que detecta que el contenido cambio"
    assert "maestro" in (fila["evidencia"] or ""), (
        "y de donde vino: una marca correcto sin decir de donde es una marca que nadie audita")


def test_no_toca_lo_que_no_tiene_ficha(cola):
    """**Y no marca correcto lo que no lo esta.** *Un producto con nombre y marca pero sin dato sigue
    pendiente: darlo por bueno seria dar por buena una ficha vacia.*
    """
    from core import inventario
    from projects.cesta import reconciliar_fichas as rf

    inventario.alta(cola, "dia", "1")
    rf.reconcilia(cola, {"dia": {"1": {"product_name": {"value": "Yogur"}}}})

    fila = cola.execute("SELECT estado FROM fichas").fetchone()
    assert fila["estado"] == inventario.PENDIENTE


def test_una_cadena_sin_maestro_se_cuenta_y_no_se_toca(cola):
    """*Alcampo, Carrefour y Aldi no tienen maestro: sus pendientes **no se pueden contrastar**, y se cuenta
    en vez de darlos por buenos.*
    """
    from core import inventario
    from projects.cesta import reconciliar_fichas as rf

    inventario.alta(cola, "alcampo", "824179")
    cuenta = rf.reconcilia(cola, {"dia": {"310847": DE_DIA}})

    assert cuenta["reconciliadas"] == 0
    assert cuenta["sin_maestro"] == 1
    assert cola.execute("SELECT estado FROM fichas").fetchone()["estado"] == inventario.PENDIENTE


def test_el_hash_es_el_del_ejecutor(cola):
    """**La parte que decidia.** *El hash tiene que salir de la misma funcion que usa `fichas_lidl`, o la
    proxima pasada creeria que todo el contenido cambio.*
    """
    from core import inventario
    from projects.cesta import reconciliar_fichas as rf
    from projects.cesta.fichas_lidl import CAMPOS_DE_FICHA, _hash_util

    inventario.alta(cola, "dia", "310847")
    rf.reconcilia(cola, {"dia": {"310847": DE_DIA}})

    campos = rf.campos_de_ficha("dia", DE_DIA)
    esperado = _hash_util({k: campos.get(k) for k in CAMPOS_DE_FICHA})
    guardado = cola.execute("SELECT hash_util FROM fichas").fetchone()["hash_util"]
    assert guardado == esperado, "el hash de la cola y el del ejecutor tienen que ser el mismo"
