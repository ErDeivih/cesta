"""G12, punto 221: **la previa de compra**, sus tres reglas y sus limites.

*Todas puras: no escriben, no consultan, no necesitan base de datos ni servidor.* Y por eso se pueden
probar con numeros, que es lo que hace falta para saber que la consolidacion y los envases son
correctos y no solo que no revientan.
"""
from __future__ import annotations

from core import previa_compra


def test_lo_que_no_tiene_cantidad_no_se_compra_ni_se_le_inventa_una():
    """*Un ingrediente anotado como «sal» no se puede convertir en una cantidad de compra.*

    **Es la regla que `core/recetas.py:escala` ya escribe**: *«lo que no tiene cantidad, no la gana…
    inventarle un cero seria convertir lo que falta en un dato falso»*.
    """
    previa = previa_compra.previa_de_compra([
        {"texto": "sal", "cantidad": None, "unidad": None},
        {"texto": "harina", "cantidad": 500, "unidad": "g"},
    ])
    assert [ln.texto for ln in previa.lineas] == ["harina"], "solo se compra lo que tiene cantidad"
    assert previa.sin_cantidad == ["sal"]
    assert "sal" in previa.nota, "y se dice, que es lo contrario de inventarselo"


def test_dos_lineas_del_mismo_producto_en_la_misma_unidad_se_suman():
    """**La consolidacion compatible**: *dos ingredientes del mismo producto y unidad son uno.*"""
    previa = previa_compra.previa_de_compra([
        {"texto": "harina", "cantidad": 200, "unidad": "g", "producto_id": "p1"},
        {"texto": "harina", "cantidad": 300, "unidad": "g", "producto_id": "p1"},
    ])
    assert len(previa.lineas) == 1
    assert previa.lineas[0].cantidad == 500
    assert len(previa.lineas[0].de_donde) == 1, "y consta de donde salio"


def test_el_mismo_producto_en_unidades_incompatibles_no_se_suma_y_se_dice():
    """**g/ml/unidades, la distincion del 221.** *Sumar 1 kg con 2 unidades daria un numero que no
    significa nada.* **No se suman, no se elige una, y se nombra el conflicto.**
    """
    previa = previa_compra.previa_de_compra([
        {"texto": "tomate", "cantidad": 1, "unidad": "kg", "producto_id": "p9"},
        {"texto": "tomate", "cantidad": 2, "unidad": "ud", "producto_id": "p9"},
    ])
    assert len(previa.lineas) == 2, "son dos lineas, no una suma inventada"
    assert previa.sin_consolidar, "y se dice que no se pudieron consolidar"
    assert "kg" in previa.sin_consolidar[0] and "ud" in previa.sin_consolidar[0]


def test_sin_producto_elegido_se_consolida_por_el_texto_y_eso_se_ve():
    """*Un ingrediente generico no tiene `producto_id`, y aun asi dos lineas iguales son una.*

    **Pero se consolidan por texto, que es mas debil**: *«harina» y «Harina» son el mismo texto; dos
    marcas distintas de harina no serian el mismo producto y aqui no se pretende que lo sean.*
    """
    previa = previa_compra.previa_de_compra([
        {"texto": "Harina", "cantidad": 100, "unidad": "g"},
        {"texto": "harina", "cantidad": 50, "unidad": "g"},
    ])
    assert len(previa.lineas) == 1 and previa.lineas[0].cantidad == 150
    assert previa.lineas[0].producto_id is None


def test_la_previa_no_escribe_nada_ni_necesita_base_de_datos():
    """**Es una funcion pura.** *Se comprueba con lo unico que se puede comprobar sin espiar: que
    recibe una lista y devuelve objetos, sin conexion por ningun lado.*"""
    import inspect
    firma = inspect.signature(previa_compra.previa_de_compra)
    assert list(firma.parameters) == ["ingredientes"], "solo la lista: ni conexion ni propietario"
    # Y no importa sqlite ni pide nada por red.
    fuente = inspect.getsource(previa_compra)
    assert "sqlite3" not in fuente and "requests" not in fuente
