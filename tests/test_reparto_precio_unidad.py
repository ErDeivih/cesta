"""La comparativa lleva el precio por unidad y la unidad del producto elegido.

**Para que.** El reparto y ``donde`` ya dicen *que producto* y *cuanto cuesta*
cada linea, pero no *cuanto cuesta por kilo o por litro*: sin ese dato, la
comparativa no puede explicar por que un envase grande sale mejor, ni se puede
ensenar el precio normalizado que el resto de la aplicacion ya usa.

**Que se vigila, y en este orden:**

  1. **Que los dos campos viajen**, con el valor del producto **elegido** para esa
     linea -- la alternativa confirmada incluida -- y no el de otro candidato.
  2. **Que ``null`` sea ``null``**: si el producto no declara precio por unidad o
     la unidad, no se manda ``0``. *Un cero ahi afirma que es gratis.*
  3. **Que no se rompa lo de siempre**: los campos de antes siguen, y los totales
     no cambian por esto.

Como en ``test_minimos``, el modulo se resuelve por nombre para que la marca de
``conftest.py`` no salte el fichero sin PostgreSQL: aqui solo se sustituyen las
dos fuentes de datos (la conexion y el silver de ofertas), no la logica.
"""
from __future__ import annotations

import importlib

from plataforma import api as _api

cesta = importlib.import_module(f"{_api.__name__}.cesta")

# Las columnas que devuelve la consulta de `_candidatos`, en su orden. La unidad
# va detras de `marca`, que no mueve ninguna de las diez de siempre.
COLUMNAS = ("grupo_id", "pid_suelto", "fuente", "pid", "nombre", "precio_cent",
            "precio_unidad_cent", "comparacion_fiable", "ean", "marca", "unidad_canon")

FILA = (7, None, "dia", "dia:1", "Leche entera 1 l", 125, 95.0, True,
        "8412345678905", "Marca", "l")

CAMPOS_DE_SIEMPRE = ("producto_id", "nombre", "cadena", "unidades", "coste_cent",
                     "coste_sin_oferta_cent", "promo", "sugerencia", "linea_id",
                     "identidad", "motivo", "autorizada", "alternativa")


class _Filas:
    def __init__(self, filas):
        self._filas = filas

    def fetchall(self):
        return list(self._filas)


class _Conexion:
    """La fuente de datos controlada: las filas que le demos, y sus columnas."""

    def __init__(self, filas, columnas=COLUMNAS):
        self.filas = filas
        self.columnas = columnas

    def execute(self, sql, parametros=None):
        if "DESCRIBE" in sql:
            return _Filas([(c,) for c in self.columnas])
        return _Filas(self.filas if "grupo_id IN" in sql else [])


def _monta(monkeypatch, filas=None, columnas=COLUMNAS):
    monkeypatch.setattr(cesta, "conexion",
                        lambda: _Conexion(filas if filas is not None else [FILA], columnas))
    monkeypatch.setattr(cesta, "_promos_vigentes", lambda ids, fecha=None: {})


def _peticion():
    return cesta.Peticion(grupo_id=7, producto_id=None, cantidad=1,
                          nombre="Leche entera 1 l", id="l1")


def _producto(monkeypatch, **monta_kw):
    _monta(monkeypatch, **monta_kw)
    salida = cesta.donde_comprar([_peticion()], ["dia"], 3)
    return salida["una_tienda"][0]["productos"][0]


# --------------------------------------------------- el contrato de `_serializa` ---


def test_la_eleccion_serializada_lleva_precio_por_unidad_y_unidad():
    eleccion = cesta.Eleccion("dia:1", "Leche entera 1 l", "dia", 1, 125, 125, None, None,
                              precio_unidad_cent=95.0, unidad="l")
    serializada = cesta._serializa(eleccion)
    assert serializada["precio_unidad_cent"] == 95.0
    assert serializada["unidad"] == "l"


def test_sin_dato_los_dos_campos_son_null_y_no_cero():
    """`null` no es `0`: un cero diria que el producto es gratis por unidad."""
    serializada = cesta._serializa(cesta.Eleccion("dia:1", "Leche", "dia", 1, 125, 125, None, None))
    assert serializada["precio_unidad_cent"] is None
    assert serializada["unidad"] is None


def test_los_campos_de_siempre_siguen_en_la_eleccion_serializada():
    serializada = cesta._serializa(cesta.Eleccion(
        "dia:1", "Leche", "dia", 1, 125, 125, None, None,
        precio_unidad_cent=95.0, unidad="l"))
    for campo in CAMPOS_DE_SIEMPRE:
        assert campo in serializada, f"se perdio {campo} al anadir el precio por unidad"


# ------------------------------------------------ el producto elegido, de verdad ---


def test_el_producto_elegido_lleva_su_precio_por_unidad_y_su_unidad(monkeypatch):
    producto = _producto(monkeypatch)
    assert producto["producto_id"] == "dia:1"
    assert producto["precio_unidad_cent"] == 95.0
    assert producto["unidad"] == "l"


def test_sin_la_columna_de_la_unidad_en_el_catalogo_se_manda_null(monkeypatch):
    """Gold viejo: la columna no esta. Se degrada a `null`, que es «no se sabe»."""
    producto = _producto(monkeypatch, filas=[FILA[:10]], columnas=COLUMNAS[:-1])
    assert producto["precio_unidad_cent"] == 95.0
    assert producto["unidad"] is None


def test_sin_precio_por_unidad_el_campo_es_null_y_la_unidad_sigue(monkeypatch):
    fila = (*FILA[:6], None, *FILA[7:])
    producto = _producto(monkeypatch, filas=[fila])
    assert producto["precio_unidad_cent"] is None
    assert producto["unidad"] == "l"


def test_los_totales_no_cambian_por_llevar_el_precio_por_unidad(monkeypatch):
    _monta(monkeypatch)
    tienda = cesta.donde_comprar([_peticion()], ["dia"], 3)["una_tienda"][0]
    assert tienda["total_cent"] == 125, tienda
    assert tienda["productos"][0]["coste_cent"] == 125


def test_las_lineas_del_reparto_tambien_llevan_el_precio_por_unidad(monkeypatch):
    """La sublista es la pantalla donde se comparan las lineas ya decididas."""
    _monta(monkeypatch)
    salida = cesta.reparto_por_tienda([_peticion()], ["dia"], ["dia"])
    linea = salida["sublistas"][0]["lineas"][0]
    assert linea["precio_unidad_cent"] == 95.0
    assert linea["unidad"] == "l"


def test_la_alternativa_confirmada_lleva_el_precio_por_unidad_de_la_alternativa(monkeypatch):
    """Lo que se compra es la alternativa aceptada: sus campos, no los del pedido."""
    otra = (7, None, "dia", "dia:2", "Leche de otra marca", 100, 80.0, True,
            "8499999999992", "MarcaB", "l")
    _monta(monkeypatch, filas=[FILA, otra])
    peticion = cesta.Peticion(7, "dia:1", 1, "Leche entera 1 l", "l1",
                              autorizado=True, autorizado_producto="dia:2",
                              autorizado_cadena="dia")
    producto = cesta.donde_comprar([peticion], ["dia"], 3)["una_tienda"][0]["productos"][0]
    assert producto["producto_id"] == "dia:2"
    assert producto["precio_unidad_cent"] == 80.0
    assert producto["unidad"] == "l"
