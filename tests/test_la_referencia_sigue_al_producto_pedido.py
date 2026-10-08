"""Con producto pedido en una linea por grupo, la referencia es ese producto en todas las cadenas.

El caso del encargo: un grupo con dos marcas, la linea pidiendo una de ellas, y el canonico del grupo siendo la
otra. La referencia no puede ser el miembro cualquiera: tiene que ser lo pedido.
"""
from __future__ import annotations

from plataforma.api import cesta


class ConexionFalsa:
    def __init__(self, filas):
        self.filas = filas

    def execute(self, sql, params=None):
        return self

    def fetchall(self):
        return self.filas


def _fila(grupo, fuente, producto, precio, gtin, marca):
    return (grupo, None, fuente, producto, f"Producto {producto}", precio, float(precio), True, gtin, marca)


def _referencias(monkeypatch):
    filas = [
        _fila(1, "dia", "dia:9", 100, "8412345678901", "MarcaA"),
        _fila(1, "mercadona", "mercadona:3", 110, "8412345678902", "MarcaB"),
    ]
    monkeypatch.setattr(cesta, "conexion", lambda: ConexionFalsa(filas))
    monkeypatch.setattr(cesta, "_promos_vigentes", lambda ids, fecha: {})
    # La linea va **por grupo** y ademas registra que producto se pidio.
    peticion = cesta.Peticion(grupo_id=1, producto_id="mercadona:3", cantidad=1, nombre="Leche")
    mejor = cesta._candidatos([peticion], cesta._fecha_de_hoy())
    return {clave[1]: valor[5].id_fuente for clave, valor in mejor.items()
            if isinstance(clave, tuple) and len(clave) == 2}


def test_la_referencia_es_el_producto_pedido_en_las_dos_cadenas(monkeypatch):
    referencias = _referencias(monkeypatch)
    assert set(referencias) == {"dia", "mercadona"}, referencias
    assert referencias["dia"] == "mercadona:3", (
        f"en dia la referencia es {referencias['dia']}: se esta comparando con el canonico del grupo, no con lo pedido")
    assert referencias["mercadona"] == "mercadona:3", referencias


def test_el_canonico_sigue_siendo_el_del_grupo_cuando_no_se_pidio_producto(monkeypatch):
    """El limite conocido, que no se rompe con este arreglo."""
    filas = [
        _fila(1, "dia", "dia:9", 100, "8412345678901", "MarcaA"),
        _fila(1, "mercadona", "mercadona:3", 110, "8412345678902", "MarcaB"),
    ]
    monkeypatch.setattr(cesta, "conexion", lambda: ConexionFalsa(filas))
    monkeypatch.setattr(cesta, "_promos_vigentes", lambda ids, fecha: {})
    peticion = cesta.Peticion(grupo_id=1, producto_id=None, cantidad=1, nombre="Leche")
    mejor = cesta._candidatos([peticion], cesta._fecha_de_hoy())
    referencias = {clave[1]: valor[5].id_fuente for clave, valor in mejor.items()
                   if isinstance(clave, tuple) and len(clave) == 2}
    assert referencias["dia"] == "dia:9", referencias
