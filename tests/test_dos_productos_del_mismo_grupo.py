"""Dos articulos concretos del mismo grupo no pueden compartir referencia.

**El caso:** dos lineas de la lista piden dos productos concretos del **mismo grupo antiguo** (`dia:A` a 100 y
`dia:B` a 150). El motor tiene que resolver **cada una contra la suya**: la referencia de `A` para la primera y
la de `B` para la segunda.

**Hoy:** `pedido[grupo]` guarda solo una, y `mejor` se indexa por `(grupo, fuente)`, asi que **las dos lineas
salen con el mismo producto**. Y como la cantidad que decide la oferta se suma por grupo, la promocion de un
producto se calcula con las unidades del otro.

**La independencia del orden es la prueba dura:** si el resultado cambia al reordenar las lineas, la identidad
depende de por donde se empiece, que es lo mismo que decir que no hay identidad por linea.
"""
from __future__ import annotations

from plataforma.api import cesta

FILAS = (
    # Cuidado con el orden de las columnas: grupo_id, pid_suelto, fuente, pid, nombre,
    # precio_cent, precio_unidad_cent, comparacion_fiable, ean, marca
    (7, None, "dia", "dia:A", "Leche A", 100, 100, 1, "8410000000001", "Marca A"),
    (7, None, "dia", "dia:B", "Leche B", 150, 150, 1, "8410000000002", "Marca B"),
)


class _Filas:
    def __init__(self, filas):
        self._filas = filas

    def fetchall(self):
        return list(self._filas)


class _Conexion:
    """Devuelve las dos filas del grupo. La consulta de sueltos no trae nada."""

    def execute(self, sql, parametros=None):
        return _Filas(FILAS if "grupo_id IN" in sql else [])


def _peticion(producto_id, linea_id):
    return cesta.Peticion(grupo_id=7, producto_id=producto_id, cantidad=1,
                          nombre=f"Leche {producto_id[-1]}", id=linea_id)


def _monta(monkeypatch):
    monkeypatch.setattr(cesta, "conexion", lambda: _Conexion())
    monkeypatch.setattr(cesta, "_promos_vigentes", lambda *a, **k: {})


def _por_linea(peticiones):
    """El producto con el que sale cada linea, por su identificador."""
    devuelto = cesta.donde_comprar(peticiones, ["dia"], 3)
    tiendas = devuelto.get("una_tienda") or []
    assert tiendas, devuelto
    return {p["linea_id"]: p["producto_id"] for p in tiendas[0]["productos"]}


def test_cada_linea_sale_con_su_producto(monkeypatch):
    _monta(monkeypatch)
    salida = _por_linea([_peticion("dia:A", "l1"), _peticion("dia:B", "l2")])
    assert salida["l1"] == "dia:A" and salida["l2"] == "dia:B", (
        f"cada linea tiene que salir con el suyo y salio {salida}")


def test_el_orden_de_las_lineas_no_cambia_nada(monkeypatch):
    """Las dos ordenes, y el mismo resultado para cada linea."""
    _monta(monkeypatch)
    al_derecho = _por_linea([_peticion("dia:A", "l1"), _peticion("dia:B", "l2")])
    al_reves = _por_linea([_peticion("dia:B", "l2"), _peticion("dia:A", "l1")])
    assert al_derecho == al_reves, (
        f"el resultado depende del orden: {al_derecho} frente a {al_reves}")
