"""Dividir una misma compra en lineas no puede cambiar su coste.

**El caso que reproduce el dueno:** un producto a 100 centimos con oferta `3x2`. Pedir tres unidades devuelve
200 centimos; partirlas en dos lineas de una y dos devuelve 300. La promocion es la misma y la compra tambien.

**Por que pasa:** `_candidatos` ya suma las cantidades para **elegir** el candidato -- arreglo del defecto 3 --
pero el coste que se paga vuelve a salir de la cantidad de **cada linea**, y luego se suman esos costes ya
separados. Elegir bien no es cobrar bien.

La prueba **no** mira el candidato elegido: mira el **total pagado**. Una prueba de igualdad del candidato es la
que dejo pasar esto.

**Todo lo que usa esta observado, no supuesto** (ronda 101): `_candidatos(peticiones, fecha_tope)` devuelve un
diccionario por `(grupo_o_producto, fuente)`; `3x2` es una promocion real del catalogo (1.625 filas) que lee
`core.promos.lee(texto)`; y `donde_comprar` devuelve `{una_tienda, repartido, lineas}`, con el dinero en
`una_tienda[i]["total_cent"]`.
"""
from __future__ import annotations

from plataforma.api import cesta


def _peticion(cantidad, pid="dia:P1", gid=7):
    return cesta.Peticion(grupo_id=gid, producto_id=pid, cantidad=cantidad, nombre="Leche entera")


def _fila_con_3x2(precio=100):
    """La fila como la devuelve `_candidatos`: con la oferta `3x2` y el coste de las tres unidades."""
    return (("dia:P1", precio, "Leche entera", "3x2", None, None, None, 200, True))


def _monta(monkeypatch):
    """El mismo candidato para las unidades, se pidan como se pidan."""

    def candidatos(peticiones, fecha_tope):
        mejor = {}
        for p in peticiones:
            clave = cesta._llave_candidato(
            p.grupo_id if p.grupo_id is not None else p.producto_id, p.producto_id, "dia")
            mejor[clave] = _fila_con_3x2()
        return mejor

    monkeypatch.setattr(cesta, "_candidatos", candidatos)
    monkeypatch.setattr(cesta, "_promos_vigentes", lambda *a, **k: {})


def _total(peticiones):
    """El total de la mejor tienda, que es lo que se paga."""
    devuelto = cesta.donde_comprar(peticiones, ["dia"], 3)
    tiendas = devuelto.get("una_tienda") or []
    assert tiendas, devuelto
    return tiendas[0]["total_cent"]


def test_tres_en_una_linea_y_en_dos_cuestan_lo_mismo(monkeypatch):
    _monta(monkeypatch)
    de_tres = _total([_peticion(3)])
    de_una_y_dos = _total([_peticion(1), _peticion(2)])
    assert de_tres == de_una_y_dos, (
        f"la misma compra cuesta {de_tres} en una linea y {de_una_y_dos} en dos: "
        "dividir lineas no puede cambiar el precio")
    assert de_tres == 200, f"un 3x2 sobre tres unidades de 100 centimos son 200, no {de_tres}"


def test_el_3x2_se_aplica_en_la_linea_de_tres(monkeypatch):
    """El suelo: sin esto, la prueba de arriba podria pasar por estar mal las dos."""
    _monta(monkeypatch)
    devuelto = cesta.donde_comprar([_peticion(3)], ["dia"], 3)
    tienda = devuelto["una_tienda"][0]
    assert tienda["total_cent"] == 200 and tienda["total_sin_ofertas_cent"] == 300, tienda
