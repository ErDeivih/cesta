"""El canonico de un grupo no depende de la cadena.

Dos filas del mismo grupo en dos tiendas, con el identificador mas bajo en la segunda. La referencia con la que
se juzga cada candidato tiene que ser **la misma** en las dos: si cambia con la tienda, el mismo producto sale
exacto en una y alternativa en otra, y los veredictos no se pueden comparar.
"""
from __future__ import annotations

from plataforma.api import cesta


class ConexionFalsa:
    """Lo justo para `_candidatos`: una consulta que devuelve las filas que le demos."""

    def __init__(self, filas):
        self.filas = filas

    def execute(self, sql, params=None):
        return self

    def fetchall(self):
        return self.filas


def _fila(grupo, fuente, producto, precio, gtin, marca):
    """Las diez columnas que `_candidatos` descompone, en su orden."""
    return (grupo, None, fuente, producto, f"Producto {producto}", precio, float(precio), True, gtin, marca)


def _dos_cadenas(monkeypatch):
    filas = [
        _fila(1, "dia", "dia:9", 100, "8412345678901", "MarcaA"),
        _fila(1, "mercadona", "mercadona:3", 110, "8412345678902", "MarcaB"),
    ]
    monkeypatch.setattr(cesta, "conexion", lambda: ConexionFalsa(filas))
    monkeypatch.setattr(cesta, "_promos_vigentes", lambda ids, fecha: {})
    peticion = cesta.Peticion(grupo_id=1, producto_id=None, cantidad=1, nombre="Leche")
    return cesta._candidatos([peticion], cesta._fecha_de_hoy())


def test_el_canonico_es_el_mismo_en_las_dos_cadenas(monkeypatch):
    mejor = _dos_cadenas(monkeypatch)
    # El canonico de cada eleccion va en el campo 5 de la fila: `fila = (pid, precio, nombre, promo, ean,
    # referencia, marca, coste)`.
    referencias = {}
    for clave, valor in mejor.items():
        if isinstance(clave, tuple) and len(clave) == 2:
            referencias[clave[1]] = valor[5].id_fuente
    assert set(referencias) == {"dia", "mercadona"}, referencias
    assert referencias["dia"] == referencias["mercadona"], (
        f"la referencia cambia con la cadena: {referencias}")


def test_el_canonico_del_grupo_es_el_de_identificador_mas_bajo(monkeypatch):
    """Sigue siendo un miembro del grupo, pero el mismo para todas las cadenas."""
    mejor = _dos_cadenas(monkeypatch)
    referencia = next(v[5] for k, v in mejor.items() if isinstance(k, tuple) and len(k) == 2)
    # El campo que se compara es texto con la forma `fuente:id`, y se compara como texto:
    # `"dia:9" < "mercadona:3"`. La regla -- el identificador mas bajo -- es la de siempre.
    assert referencia.id_fuente == "dia:9", referencia.id_fuente