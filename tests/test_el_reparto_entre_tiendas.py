"""El reparto entre tiendas: la sublista aplica las ofertas, que es lo que promete.

Una sublista es una tienda. Dentro de ella, dos lineas del mismo producto **comparten la oferta**; a tiendas
distintas no se agrupan nunca, y eso aqui sale gratis: cada sublista es su propia tienda.
"""
from __future__ import annotations

from plataforma.api import cesta


def _monta(monkeypatch):
    def candidatos(peticiones, fecha_tope):
        mejor = {}
        for p in peticiones:
            mejor[cesta._llave_candidato(p.grupo_id, p.producto_id, "dia")] = (
                "dia:P1", 100, "Leche", "3x2", None, None, None, 200, True)
        return mejor

    monkeypatch.setattr(cesta, "_candidatos", candidatos)
    monkeypatch.setattr(cesta, "_promos_vigentes", lambda *a, **k: {})


def _pet(cantidad):
    return cesta.Peticion(grupo_id=7, producto_id="dia:P1", cantidad=cantidad, nombre="Leche")


def _reparte(cantidades):
    r = cesta.reparto_por_tienda([_pet(c) for c in cantidades],
                                 ["dia"] * len(cantidades), ["dia"])
    sublistas = r.get("sublistas") or []
    assert sublistas, r
    return sublistas[0]["total_cent"], r


def test_una_sublista_de_tres_aplica_el_3x2(monkeypatch):
    _monta(monkeypatch)
    total, _ = _reparte([3])
    assert total == 200, f"un 3x2 sobre tres unidades son 200, y la sublista dice {total}"


def test_partir_la_compra_en_dos_no_cambia_el_total_de_la_sublista(monkeypatch):
    _monta(monkeypatch)
    entera, _ = _reparte([3])
    partida, _ = _reparte([1, 2])
    assert entera == partida == 200, f"entera {entera}, partida {partida}"


def test_el_total_de_la_lista_es_la_suma_de_las_sublistas(monkeypatch):
    _monta(monkeypatch)
    _, r = _reparte([1, 2])
    assert r.get("total_cent") == sum(s["total_cent"] for s in r["sublistas"]), r
