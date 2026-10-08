"""Cuando la linea dice que producto pidio, la referencia es ESE producto, en cualquier cadena.

Dos filas del mismo grupo -- una de cada marca -- donde la de identificador mas bajo **no** es la pedida. Si la
linea pide `dia:5`, la referencia tiene que ser `dia:5` y no la mas baja del grupo: eso es lo que el dueno pide
-- comparar contra lo que se pidio -- y lo que el defecto 2 denuncia que no pasa.
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


def _fila(grupo, suelto, fuente, producto, precio, gtin, marca):
    return (grupo, suelto, fuente, producto, f"Producto {producto}", precio, float(precio), True, gtin, marca)


def _con(monkeypatch, filas):
    monkeypatch.setattr(cesta, "conexion", lambda: ConexionFalsa(filas))
    monkeypatch.setattr(cesta, "_promos_vigentes", lambda ids, fecha: {})


def _referencias(mejor):
    """El canonico de cada eleccion va en el campo 5 de la fila."""
    return {clave: valor[5].id_fuente for clave, valor in mejor.items()
            if isinstance(clave, tuple) and len(clave) == 2}


def test_con_producto_pedido_la_referencia_es_ese_producto(monkeypatch):
    """La linea pide `dia:5`; el grupo tiene tambien `dia:9`, que es el de identificador mas bajo."""
    filas = [
        _fila(1, None, "dia", "dia:9", 100, "8412345678901", "MarcaA"),
        _fila(1, None, "dia", "dia:5", 110, "8412345678902", "MarcaB"),
    ]
    _con(monkeypatch, filas)
    peticion = cesta.Peticion(grupo_id=1, producto_id="dia:5", cantidad=1, nombre="Leche")
    referencias = _referencias(cesta._candidatos([peticion], cesta._fecha_de_hoy()))
    assert referencias, "no se eligio ningun candidato"
    assert referencias[cesta._llave_candidato(1, "dia:5", "dia")] == "dia:5", (
        f"la referencia es {referencias[(1, 'dia')]} y la linea pide dia:5")


def test_sin_producto_pedido_la_referencia_es_el_canonico_del_grupo(monkeypatch):
    """El limite conocido: la linea que solo trae grupo no registra que se pidio."""
    filas = [
        _fila(1, None, "dia", "dia:9", 100, "8412345678901", "MarcaA"),
        _fila(1, None, "dia", "dia:5", 110, "8412345678902", "MarcaB"),
    ]
    _con(monkeypatch, filas)
    peticion = cesta.Peticion(grupo_id=1, producto_id=None, cantidad=1, nombre="Leche")
    referencias = _referencias(cesta._candidatos([peticion], cesta._fecha_de_hoy()))
    # El identificador es texto con la forma `fuente:id` y se compara como texto:
    # `"dia:5" < "dia:9"`. Leerlo como numero es el error que ya cometi con el canonico.
    assert referencias[(1, "dia")] == "dia:5", referencias