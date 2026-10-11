"""F05 (fase 2): **ingredientes y alérgenos de Mercadona, del crudo a un dato usable.**

*Medido:* Mercadona publica `ingredients` y `allergens` -- **en texto con HTML** -- dentro de un bloque que
se llama `nutrition_information` y **no trae nutrición**. *Las cifras no las publica ninguna de las cinco
cadenas medidas.*

*Estas pruebas usan un cuerpo con la forma real, medido, y **no llaman a la red**.*
"""
from __future__ import annotations

import gzip
import json
from pathlib import Path

import pytest

from projects.cesta import ficha_mercadona as fm

# **La forma real, copiada de un fichero de `data/raw/fuente=mercadona/`.** *No es inventada: los dos
# campos, el marcado `<strong>` dentro y el `ingredients` de nivel 1 a `null`.*
CUERPO = {
    "id": "18290",
    "display_name": "Tarta de nata",
    "ean": "8412345678901",
    "ingredients": None,                      # el de nivel 1 viene nulo; el bueno está dentro
    "nutrition_information": {
        "allergens": "Contiene <strong>soja y productos a base de soja</strong>. Contiene "
                     "<strong>cereales que contengan gluten</strong>.",
        "ingredients": "<strong>INGREDIENTES</strong>: Preparado de nata batida "
                       "(<strong>leche</strong> desnatada, azúcar), galleta (harina de "
                       "<strong>trigo</strong>, azúcar).",
    },
}


def test_lee_ingredientes_y_alergenos_del_bloque():
    """*El bloque se llama `nutrition_information` y NO trae nutrición: trae estos dos.*"""
    leido = fm.lee(CUERPO)

    assert "ingredientes" in leido
    assert "alergenos" in leido
    assert leido["ingredientes"].startswith("INGREDIENTES: Preparado de nata batida")


def test_quita_el_marcado_sin_perder_el_texto():
    """**El `<strong>` marca los alérgenos, no decora.** *Se quita la etiqueta y se conserva la palabra.*"""
    leido = fm.lee(CUERPO)

    assert "<strong>" not in leido["ingredientes"]
    assert "<strong>" not in leido["alergenos"]
    # Y el texto que marcaban sigue ahí: si esto fallara, se habría tirado el alérgeno.
    assert "soja y productos a base de soja" in leido["alergenos"]
    assert "leche" in leido["ingredientes"]
    assert "trigo" in leido["ingredientes"]


def test_no_deja_espacios_raros_al_quitar_el_marcado():
    """*`a </strong>.` no puede quedar como `a .` -- es texto que se enseña.*"""
    assert fm.sin_marcado("Contiene <strong>leche</strong>.") == "Contiene leche."
    assert fm.sin_marcado("a  b") == "a b"
    assert fm.sin_marcado("  <b>x</b>  ") == "x"


def test_lo_que_la_fuente_no_trae_no_aparece():
    """**La distinción que F05 pide no perder**: *«no lo publica» no es «lo publicamos en blanco»*.

    *Un campo ausente no se rellena con cadena vacía: si se rellenara, contar cobertura daría por buena una
    ficha que no tiene nada.*
    """
    leido = fm.lee({"id": "1", "nutrition_information": {"allergens": "Contiene leche."}})

    assert "alergenos" in leido
    assert "ingredientes" not in leido, "un campo que la fuente no trae no puede salir vacío"


def test_tolera_que_venga_vacio_o_no_venga():
    """*La fuente cambia de forma entre días, y un `None` no puede reventar la pasada entera.*"""
    assert fm.lee({}) == {}
    assert fm.lee({"nutrition_information": None}) == {}
    assert fm.lee({"nutrition_information": {"ingredients": "   "}}) == {}
    assert fm.lee("esto no es un producto") == {}


def test_la_tiene_distingue_los_que_traen_ficha():
    """*Para poder contar cuántos de los capturados la traen -- que es la medida de cobertura.*"""
    assert fm.la_tiene(CUERPO) is True
    assert fm.la_tiene({"id": "1"}) is False


# ---------------------------------------------------------------------------------------------
# Y contra el crudo de verdad, si está -- que es lo que convierte lo anterior en algo comprobado.
# ---------------------------------------------------------------------------------------------


def _un_crudo_de_mercadona():
    """El primer fichero de hoy con ficha, o `None`. *No baja nada: lee lo que el colector ya guardó.*"""
    for carpeta in sorted(Path("data/raw").glob("fuente=mercadona/fecha=*"), reverse=True):
        for f in sorted(carpeta.glob("*.json.gz")):
            try:
                cuerpo = json.loads(gzip.decompress(f.read_bytes()))
            except Exception:  # noqa: BLE001
                continue
            if isinstance(cuerpo, dict) and fm.la_tiene(cuerpo):
                return f, cuerpo
    return None


def test_contra_el_crudo_real():
    """**La prueba que vale**: sobre un fichero de verdad, no sobre uno que he escrito yo.

    *Si no hay crudo -- otra máquina, otro día -- se salta en vez de fallar*: el crudo es un dato del
    entorno, no del código. **Pero cuando lo hay, se comprueba de verdad.**
    """
    hallado = _un_crudo_de_mercadona()
    if hallado is None:
        pytest.skip("no hay crudo de Mercadona con ficha en data/raw")

    fichero, cuerpo = hallado
    leido = fm.lee(cuerpo)

    assert leido, f"{fichero.name}: la fuente trae ficha y no se ha leído nada"
    for clave, texto in leido.items():
        assert "<" not in texto or clave in ("id", "ean", "nombre"), (
            f"{fichero.name}: queda marcado sin quitar en {clave}: {texto[:80]}")
    # Y el texto es largo: una ficha no son dos palabras.
    if "ingredientes" in leido:
        assert len(leido["ingredientes"]) > 40, f"{fichero.name}: ingredientes sospechosamente cortos"
