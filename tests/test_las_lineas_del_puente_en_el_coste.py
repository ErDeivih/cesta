"""Las lineas que meten los puentes, en la cuenta de la lista.

Un ingrediente de receta es texto libre: no tiene producto ni grupo, asi que **no tiene precio** y la lista lo
dice. Y no puede llevarse la oferta de otra linea: sin producto, no hay grupo de compra al que pertenecer.
"""
from __future__ import annotations

from plataforma.api import cesta


def _del_puente(linea_id, nombre, cantidad):
    """Como las mete `desde-el-plan`: sin grupo y sin producto."""
    return {"id": linea_id, "grupo_id": None, "producto_id": None, "cantidad": cantidad,
            "nombre_visto": nombre, "cadena_elegida": None, "producto_movido": False}


def _de_la_lista(linea_id, cantidad):
    return {"id": linea_id, "grupo_id": 7, "producto_id": "dia:P1", "cantidad": cantidad,
            "nombre_visto": "Leche", "cadena_elegida": None, "producto_movido": False}


def _monta(monkeypatch):
    def candidatos(peticiones, fecha_tope):
        mejor = {}
        for p in peticiones:
            if p.grupo_id is None and p.producto_id is None:
                continue        # sin producto no hay candidato, y eso es lo correcto
            mejor[cesta._llave_candidato(p.grupo_id, p.producto_id, "dia")] = (
                "dia:P1", 100, "Leche", "3x2", None, None, None, 200, True)
        return mejor

    monkeypatch.setattr(cesta, "_candidatos", candidatos)
    monkeypatch.setattr(cesta, "_promos_vigentes", lambda *a, **k: {})


def test_una_linea_sin_producto_se_cuenta_aparte_y_no_se_le_inventa_precio(monkeypatch):
    _monta(monkeypatch)
    r = cesta.estimacion([_del_puente("l1", "lentejas", 1)])
    assert r["total_cent"] == 0 and r["sin_precio"] == 1, (
        f"un ingrediente sin producto no tiene precio, y la lista tiene que decirlo: {r}")


def test_y_no_rompe_el_reparto_de_las_que_si_tienen_precio(monkeypatch):
    """Mezcladas: la de producto aplica su oferta por su grupo, y la del puente no entra ni estorba."""
    _monta(monkeypatch)
    solo_producto = cesta.estimacion([_de_la_lista("l1", 3)])
    mezcladas = cesta.estimacion([_del_puente("l0", "lentejas", 1), _de_la_lista("l1", 3)])
    assert mezcladas["total_cent"] == solo_producto["total_cent"] == 200, (mezcladas, solo_producto)
    assert mezcladas["sin_precio"] == 1, mezcladas


def test_dos_lineas_del_puente_no_se_agrupan_entre_ellas(monkeypatch):
    """Sin producto no hay grupo de compra: dos ingredientes no comparten ninguna oferta."""
    _monta(monkeypatch)
    r = cesta.estimacion([_del_puente("l1", "lentejas", 1), _del_puente("l2", "lentejas", 2)])
    assert r["total_cent"] == 0 and r["sin_precio"] == 2, r
