"""F05 (fase 2): **la tabla de nutrición de Día, del crudo a un dato usable.**

*Medido sobre el crudo de hoy:* Día publica `kilo_calories`, `energy`, `fat`, `carbohydrate`, `sugars`,
`protein` y `salt`, **cada uno con su unidad**, más `ingredients`. *Y **no** lo publican Mercadona,
Alcampo ni Aldi, medidos por claves.*

*Estas pruebas usan un cuerpo con la forma real y **no llaman a la red**; y hay una contra un fichero de
verdad, que se salta si no hay crudo.*
"""
from __future__ import annotations

import gzip
import json
from pathlib import Path

import pytest

from projects.cesta import ficha_dia as fd

# **La forma real, copiada de `data/raw/fuente=dia/`.** *Los nutrientes con `uom`, los textos con `<p>`, y
# el `&nbsp;` que Día mete dentro del `<strong>`.*
CUERPO = {
    "sku_id": "310847",
    "ean_code": "8480017328212",
    "product_name": {"name": "Nombre específico de producto", "value": "Yogur natural"},
    "brand_description": {"name": "Marca", "value": "DIA"},
    "energy": {"name": "Valor Energético (KJ)", "uom": "kJ", "value": 257},
    "kilo_calories": {"name": "Kcal", "uom": "kcal", "value": 54},
    "fat": {"name": "Grasas", "uom": "g", "value": 3.5},
    "protein": {"name": "Proteínas", "uom": "g", "value": 3.3},
    "salt": {"name": "Sal", "uom": "g", "value": 0.1},
    "ingredients": {"name": "Ingredientes",
                    "value": "<p><strong>Leche&nbsp;</strong>entera pasteurizada y fermentos lácticos.</p>"},
    "width": {"name": "Ancho Ud", "uom": "cm", "value": 13},   # no es nutrición: no debe salir
}


def test_lee_los_nutrientes_con_su_unidad():
    """**Lo que ninguna otra cadena medida publica.** *Y con el `uom` al lado, para no suponer gramos.*"""
    leido = fd.lee(CUERPO)

    assert leido["kcal"] == {"valor": 54.0, "uom": "kcal"}
    assert leido["energia_kj"] == {"valor": 257.0, "uom": "kJ"}
    assert leido["grasas"] == {"valor": 3.5, "uom": "g"}
    assert leido["proteinas"] == {"valor": 3.3, "uom": "g"}


def test_lee_los_ingredientes_y_les_quita_el_marcado():
    """*Día usa `<p>` y `<strong>`, y un `&nbsp;` dentro — que si no se quita deja `Leche entera` roto.*"""
    leido = fd.lee(CUERPO)

    assert leido["ingredientes"] == "Leche entera pasteurizada y fermentos lácticos."
    assert "<" not in leido["ingredientes"]
    assert "&nbsp;" not in leido["ingredientes"]


def test_no_cuela_campos_que_no_son_nutricion():
    """**`width` tiene la misma forma que un nutriente** —`{name, uom, value}`— *y no es nutrición.*

    *Es la trampa de esta fuente: la forma es idéntica para el ancho del paquete y para las grasas, así
    que se lee **por nombre de campo**, no por forma.*
    """
    leido = fd.lee(CUERPO)

    assert "width" not in leido
    assert "ancho" not in leido
    assert "cm" not in json.dumps(leido)


def test_la_identidad_para_poder_casarla_con_el_producto():
    """*Sin esto la ficha no se puede guardar en la cola: no se sabe de qué producto es.*"""
    leido = fd.lee(CUERPO)

    assert leido["id"] == "310847"
    assert leido["ean"] == "8480017328212"
    assert leido["nombre"] == "Yogur natural"
    assert leido["marca"] == "DIA"


def test_lo_que_la_fuente_no_trae_no_aparece():
    """**Medido: los nutrientes están en 3 de las 4 fichas.** *En la cuarta no pueden salir en blanco.*"""
    sin_nutrientes = {"sku_id": "1", "ingredients": {"name": "Ingredientes", "value": "<p>Agua.</p>"}}
    leido = fd.lee(sin_nutrientes)

    assert leido["ingredientes"] == "Agua."
    for clave in ("kcal", "grasas", "proteinas", "sal"):
        assert clave not in leido, f"{clave} no está en la fuente y no puede aparecer"


def test_tolera_lo_que_no_es_una_ficha():
    """*La fuente cambia de forma, y un cuerpo raro no puede reventar la pasada entera.*"""
    assert fd.lee({}) == {}
    assert fd.lee("no es un producto") == {}
    assert fd.lee({"energy": None}) == {}
    assert fd.lee({"energy": {"name": "x"}}) == {}       # sin `value` no hay dato


def test_una_etiqueta_de_texto_no_se_convierte_en_numero():
    """*«trazas» es información, y convertirla a número la perdería.*"""
    leido = fd.lee({"fat": {"name": "Grasas", "uom": "g", "value": "trazas"}})

    assert leido["grasas"] == {"valor": "trazas", "uom": "g"}


def test_los_nutrientes_se_pueden_separar_de_lo_demas():
    """*Para saber si una ficha sirve para enseñar una tabla, sin mirar campo a campo.*"""
    leido = fd.lee(CUERPO)

    assert set(fd.los_nutrientes(leido)) == {"kcal", "energia_kj", "grasas", "proteinas", "sal"}
    assert "ingredientes" not in fd.los_nutrientes(leido)


# ---------------------------------------------------------------------------------------------
# Y contra el crudo de verdad, si está.
# ---------------------------------------------------------------------------------------------


def _una_ficha_de_dia():
    """La primera ficha de Día de hoy con nutrientes, o `None`. *No baja nada.*"""
    for carpeta in sorted(Path("data/raw").glob("fuente=dia/fecha=*"), reverse=True):
        for f in sorted(carpeta.glob("*.json.gz")):
            try:
                cuerpo = json.loads(gzip.decompress(f.read_bytes()))
            except Exception:  # noqa: BLE001
                continue
            if isinstance(cuerpo, dict) and fd.los_nutrientes(fd.lee(cuerpo)):
                return f, cuerpo
    return None


def test_contra_el_crudo_real():
    """**La prueba que vale**: sobre un fichero de Día de verdad, no sobre uno que he escrito yo.

    *Medido hoy: hay 4 fichas JSON y en 3 de ellas está la tabla.* **Si no hay crudo se salta** -- el crudo
    es del entorno, no del código --, *pero cuando lo hay se comprueba, y hoy se ejecuta.*
    """
    hallado = _una_ficha_de_dia()
    if hallado is None:
        pytest.skip("no hay crudo de Día con nutrientes en data/raw")

    fichero, cuerpo = hallado
    leido = fd.lee(cuerpo)
    nutrientes = fd.los_nutrientes(leido)

    assert nutrientes, f"{fichero.name}: hay tabla y no se ha leído"
    # **Y algún nutriente tiene que ser un número**: si todos fueran texto, no habría tabla.
    numeros = [v["valor"] for v in nutrientes.values() if isinstance(v["valor"], float)]
    assert numeros, f"{fichero.name}: la tabla no trae ni un número: {nutrientes}"
