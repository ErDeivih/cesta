"""Cuando la sustitucion esta confirmada, la respuesta lo dice.

Sin esto, el producto devuelto es B -- lo aceptado -- pero la etiqueta dice `alternativa`, que es lo que el motor
proponia **antes** de que nadie aceptara nada. Lo mostrado y lo aceptado tienen que coincidir tambien en eso.
"""
from __future__ import annotations

from core import identidad
from plataforma.api import cesta

REFERENCIA = identidad.Producto(fuente="dia", id_fuente="A", nombre="Leche", gtin="4056489574392")


def _peticion(confirmada_para=None):
    return cesta.Peticion(grupo_id=7, producto_id="dia:A", cantidad=1, nombre="Leche",
                          autorizado=confirmada_para is not None,
                          autorizado_producto=confirmada_para,
                          autorizado_cadena="dia" if confirmada_para else None)


def _monta(monkeypatch):
    def candidatos(peticiones, fecha_tope):
        mejor = {}
        for p in peticiones:
            clave = cesta._llave_candidato(p.grupo_id, p.producto_id, "dia")
            mejor[clave] = ("dia:A", 200, "Leche entera", None, "8412345678905",
                            REFERENCIA, None, 200, False)
            mejor[(*clave, "alternativa")] = ("dia:B", 100, "Leche de otra marca", None,
                                              "8412345678999", None, None, 100)
        return mejor

    monkeypatch.setattr(cesta, "_candidatos", candidatos)
    monkeypatch.setattr(cesta, "_promos_vigentes", lambda *a, **k: {})


def _elegido(peticion):
    devuelto = cesta.donde_comprar([peticion], ["dia"], 3)
    return devuelto["una_tienda"][0]["productos"][0]


def test_con_la_sustitucion_confirmada_el_estado_es_confirmada(monkeypatch):
    _monta(monkeypatch)
    elegido = _elegido(_peticion(confirmada_para="dia:B"))
    assert elegido["producto_id"] == "dia:B", elegido
    assert elegido["identidad"] == "confirmada", (
        f"se aplico lo aceptado y la etiqueta dice {elegido['identidad']!r}: el estado de la eleccion "
        "tiene que viajar en la respuesta")


def test_sin_confirmar_el_estado_sigue_siendo_alternativa(monkeypatch):
    """El suelo: lo que no se ha aceptado se sigue llamando por su nombre."""
    _monta(monkeypatch)
    elegido = _elegido(_peticion(confirmada_para=None))
    assert elegido["identidad"] == identidad.ALTERNATIVA, elegido
    assert elegido["autorizada"] is False, elegido