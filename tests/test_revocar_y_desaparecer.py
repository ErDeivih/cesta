"""Revocar la confirmacion, y que B desaparezca del catalogo.

Los dos casos que la revision del dueno pide y que no estaban cubiertos. En los dos, la salida correcta es la
misma: **confirmacion pendiente**, y el producto que se devuelve no puede pasar por aceptado.
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


def _monta(monkeypatch, con_alternativa=True):
    """A es el canonico (200, GTIN distinto del pedido); B la alternativa (100)."""

    def candidatos(peticiones, fecha_tope):
        mejor = {}
        for p in peticiones:
            clave = cesta._llave_candidato(p.grupo_id, p.producto_id, "dia")
            mejor[clave] = ("dia:A", 200, "Leche entera", None, "8412345678905",
                            REFERENCIA, None, 200, False)
            if con_alternativa:
                mejor[(*clave, "alternativa")] = ("dia:B", 100, "Leche de otra marca", None,
                                                  "8412345678999", None, None, 100)
        return mejor

    monkeypatch.setattr(cesta, "_candidatos", candidatos)
    monkeypatch.setattr(cesta, "_promos_vigentes", lambda *a, **k: {})


def _producto(peticion):
    devuelto = cesta.donde_comprar([peticion], ["dia"], 3)
    tiendas = devuelto.get("una_tienda") or []
    assert tiendas, devuelto
    return tiendas[0]["productos"][0]


def test_una_confirmacion_revocada_deja_de_contar(monkeypatch):
    """Tenia confirmacion para B y ya no la tiene: no puede seguir valiendo lo de ayer."""
    _monta(monkeypatch)
    elegido = _producto(_peticion(confirmada_para=None))
    assert elegido["autorizada"] is False, (
        f"sin confirmacion vigente, la sustitucion no cuenta: {elegido}")
    assert elegido["producto_id"] == "dia:A", elegido


def test_si_b_desaparece_se_declara_pendiente_y_no_se_cobra_a(monkeypatch):
    """La confirmacion apunta a B, y el motor ya no propone B: pendiente, y no A por lo aceptado."""
    _monta(monkeypatch, con_alternativa=False)
    elegido = _producto(_peticion(confirmada_para="dia:B"))
    assert elegido["autorizada"] is False, (
        f"si B no esta, la confirmacion queda pendiente: {elegido}")
    assert elegido["producto_id"] == "dia:A", (
        "no se sustituye por A: A se enseña, pero no pasa por lo aceptado")
