"""La parte de cada linea: las partes suman el total del grupo, y da igual como se parta.

Es lo que usa el cierre para escribir la compra. Si las partes no suman el total, el registro no cuadra con lo
que se enseño; y si partir la compra en dos lineas cambia el total, la promocion se esta aplicando por linea.
"""
from __future__ import annotations

from plataforma.api import cesta


def _linea(linea_id, cantidad, producto_id=None):
    return {"id": linea_id, "grupo_id": 7, "producto_id": producto_id, "cantidad": cantidad,
            "nombre_visto": "Leche", "cadena_elegida": None, "producto_movido": False}


def _monta(monkeypatch):
    def candidatos(peticiones, fecha_tope):
        mejor = {}
        for p in peticiones:
            mejor[cesta._llave_candidato(p.grupo_id, p.producto_id, "dia")] = (
                "dia:P1", 100, "Leche", "3x2", None, None, None, 200, True)
        return mejor

    monkeypatch.setattr(cesta, "_candidatos", candidatos)
    monkeypatch.setattr(cesta, "_promos_vigentes", lambda *a, **k: {})


def _partes(lineas):
    salida = cesta.coste_por_linea(lineas)
    return {k: v.get("coste_cent") for k, v in salida.items()}


def test_la_parte_de_una_linea_de_tres_es_el_total_del_grupo(monkeypatch):
    _monta(monkeypatch)
    partes = _partes([_linea("l1", 3)])
    assert partes["l1"] == 200, f"un 3x2 sobre tres unidades son 200: {partes}"


def test_las_partes_suman_lo_mismo_partiendola_en_dos(monkeypatch):
    _monta(monkeypatch)
    entera = sum(v for v in _partes([_linea("l1", 3)]).values())
    partida = sum(v for v in _partes([_linea("l1", 1), _linea("l2", 2)]).values())
    assert entera == partida == 200, (
        f"la misma compra suma {entera} en una linea y {partida} en dos: "
        "la promocion no puede aplicarse por linea")


def test_ninguna_parte_se_pierde_en_el_redondeo(monkeypatch):
    """Tres lineas de una unidad con un 3x2: 200 centimos, y ni uno menos."""
    _monta(monkeypatch)
    partes = _partes([_linea("l1", 1), _linea("l2", 1), _linea("l3", 1)])
    assert sum(partes.values()) == 200, partes
    assert all(p is not None for p in partes.values()), partes
