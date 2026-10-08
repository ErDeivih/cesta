"""Aceptar la alternativa B tiene que devolver y cobrar B, nunca A.

**El caso del dueno:** `confirmado=dia:B; elegido=dia:A; autorizada=True; coste=200`. La confirmacion se
persistio bien y `_es_la_confirmada` la comprueba bien; lo que falla es que la eleccion se construye con el
producto **hallado** -- el canonico A -- en vez de con el que se acepto.

La prueba no mira la autorizacion, que ya estaba bien: mira **el producto y el precio que salen**.
"""
from __future__ import annotations

from core import identidad
from plataforma.api import cesta

REFERENCIA = identidad.Producto(fuente="dia", id_fuente="A", nombre="Leche entera",
                                gtin="4056489574392", marca=None)


def _peticion(confirmada_para=None, cantidad=1):
    return cesta.Peticion(grupo_id=7, producto_id="dia:A", cantidad=cantidad, nombre="Leche entera",
                          autorizado=confirmada_para is not None,
                          autorizado_producto=confirmada_para,
                          autorizado_cadena="dia" if confirmada_para else None)


def _monta(monkeypatch):
    """A es el canonico (200 centimos, GTIN distinto del pedido) y B es la alternativa (100 centimos)."""

    def candidatos(peticiones, fecha_tope):
        mejor = {}
        for p in peticiones:
            clave = cesta._llave_candidato(
            p.grupo_id if p.grupo_id is not None else p.producto_id, p.producto_id, "dia")
            # A: el canonico, con OTRO GTIN, asi que no es el producto pedido.
            mejor[clave] = (("dia:A", 200, "Leche entera", None, "8412345678905",
                             REFERENCIA, None, 200, False))
            # B: la alternativa que el motor propone hoy.
            mejor[(*clave, "alternativa")] = ("dia:B", 100, "Leche de otra marca", None,
                                              "8412345678999", None, None, 100)
        return mejor

    monkeypatch.setattr(cesta, "_candidatos", candidatos)
    monkeypatch.setattr(cesta, "_promos_vigentes", lambda *a, **k: {})


def _producto(peticion):
    devuelto = cesta.donde_comprar([peticion], ["dia"], 3)
    tiendas = devuelto.get("una_tienda") or []
    assert tiendas, devuelto
    productos = tiendas[0]["productos"]
    assert productos, tiendas[0]
    return productos[0]


def test_con_b_confirmada_se_devuelve_y_se_cobra_b(monkeypatch):
    _monta(monkeypatch)
    elegido = _producto(_peticion(confirmada_para="dia:B"))
    assert elegido["producto_id"] == "dia:B", (
        f"se confirmo dia:B y se devuelve {elegido['producto_id']}: "
        "lo aceptado y lo mostrado tienen que ser el mismo producto")
    assert elegido["coste_cent"] == 100, (
        f"se confirmo dia:B (100 centimos) y se cobra {elegido['coste_cent']}: "
        "lo aceptado y lo cobrado tienen que ser el mismo producto")


def test_sin_confirmacion_no_se_cobra_la_alternativa(monkeypatch):
    """El suelo: sin confirmar, la alternativa **no** puede pasar por buena."""
    _monta(monkeypatch)
    elegido = _producto(_peticion(confirmada_para=None))
    assert elegido["autorizada"] is False, elegido
    assert elegido["producto_id"] == "dia:A", elegido


def test_confirmada_para_otro_producto_no_vale(monkeypatch):
    """Y confirmar algo que el motor **no** propone hoy no autoriza nada."""
    _monta(monkeypatch)
    elegido = _producto(_peticion(confirmada_para="dia:Z"))
    assert elegido["autorizada"] is False, elegido
