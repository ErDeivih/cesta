"""F01 (fase 2): **el producto efectivo que se compra cuando se acepta una alternativa.**

Hallazgo de partida de la revisión, literal: *«`coste_por_linea` filtra candidatos cuya llave termina en
`alternativa`; `test_g03_cierre.py` prueba archivar el producto del grupo, **no el sustituto**. Probar
compra realmente realizada del sustituto aceptado, su identidad/precio/promoción/tienda y recibo. **No
dar por correcto ese contrato por estar verde.**»*

**Que se prueba aqui, y con que fuerza.** No es una lectura: se ejecuta el motor real -- `_candidatos`,
`_llave_candidato`, `identidad.decide`, `_es_la_confirmada`, `_elige`, `coste_por_linea` -- y **solo se
sustituyen las dos fuentes de datos**: la conexion a Postgres y el texto de promociones de silver. *La
logica que decide el precio y la identidad es la de produccion, sin copia.*

**El escenario es el del encargo**: producto **A** pedido, alternativa **B** aceptada en la tienda
**alcampo**, **tres unidades** y oferta **3x2 de B**. La estimacion y el cierre tienen que decir lo
mismo: **B, alcampo, 3 unidades y 500 centimos** (un 3x2 sobre 250 son dos pagadas).

*Y por que importa mas que un redondeo*: si el cierre guarda A, el historico registra un producto que
nadie compro y un precio que nadie pago, y **el diario y el gasto heredan ese error**.
"""
from __future__ import annotations

import pytest

from plataforma.api import cesta

# --- El catalogo controlado ------------------------------------------------------------------
#
# Columnas que devuelve la consulta de `_candidatos`:
#   grupo_id, pid_suelto, fuente, pid, nombre, precio_cent, precio_unidad_cent,
#   comparacion_fiable, ean, marca
#
# **Grupo 100 con dos articulos de la misma cadena**: A (el pedido, 300 c) y B (la alternativa
# aceptada, 250 c). *EAN distinto a proposito: dos codigos distintos son dos productos distintos.*

GRUPO = 100
A = "alcampo:P-A"
B = "alcampo:P-B"
TIENDA = "alcampo"

FILAS = [
    (GRUPO, None, TIENDA, A, "Refresco de cola 2 L", 300, 150, True, "8412345678905", "MarcaA"),
    (GRUPO, None, TIENDA, B, "Refis cola 2 L", 250, 125, True, "8499999999992", "MarcaB"),
]
PROMOS = {B: "3x2"}

#: Lo que cuesta de verdad: 3 unidades de B con un 3x2 son **dos pagadas** = 500.
COSTE_ESPERADO = 500
UNIDADES = 3


class _Cursor:
    def __init__(self, filas):
        self._filas = filas

    def fetchall(self):
        return self._filas


class _Conexion:
    """La conexion de mentira: responde a las dos consultas de `_candidatos`, y con su forma.

    *Se distingue cual es cual por el SQL, y se devuelve la forma que pide cada una*: la del grupo
    lleva `grupo_id` en la primera columna y la del producto suelto lleva `NULL` ahi. **Devolver la
    misma forma a las dos es como se escribe una prueba que no toca el codigo que dice tocar.**
    """

    def execute(self, sql, params):
        if "grupo_id IN" in sql:
            return _Cursor([f for f in FILAS if f[0] in list(params)])
        ids = list(params)
        return _Cursor([(None, f[3], f[2], f[3], f[4], f[5], f[6], f[7], f[8], f[9])
                        for f in FILAS if f[3] in ids])


@pytest.fixture()
def motor(monkeypatch):
    """El motor real, con las dos fuentes de datos controladas."""
    monkeypatch.setattr(cesta, "conexion", lambda: _Conexion())
    monkeypatch.setattr(cesta, "_promos_vigentes", lambda ids, fecha=None: dict(PROMOS))


def _peticion() -> cesta.Peticion:
    """La linea del encargo: A pedido, B aceptado en la tienda, tres unidades."""
    return cesta.Peticion(GRUPO, A, UNIDADES, "Refresco de cola 2 L",
                          autorizado=True, autorizado_producto=B, autorizado_cadena=TIENDA)


def _linea_guardada() -> dict:
    """La misma linea como la lee el cierre: **de la base, con lo que se confirmo**."""
    return {"id": "L1", "grupo_id": GRUPO, "producto_id": A, "cantidad": UNIDADES,
            "nombre_visto": "Refresco de cola 2 L", "autorizado": True,
            "autorizado_producto": B, "autorizado_cadena": TIENDA,
            "cadena_elegida": TIENDA, "producto_movido": None}


# --- 1. La estimacion: se afirma que ya es correcta -------------------------------------------


def test_la_estimacion_cobra_la_alternativa_confirmada(motor):
    """La estimacion **si** honra la sustitucion aceptada: B, su precio y su oferta.

    *Esto ya funciona -- el comentario de `_elige` cita el fallo que reprodujo el dueno
    (`confirmado=dia:B; elegido=dia:A`) -- y se fija aqui para que sirva de referencia de lo que el
    cierre tiene que igualar.* **Si esta prueba falla, el que se ha roto es el camino bueno.**
    """
    resultado = cesta.donde_comprar([_peticion()], [TIENDA])
    tienda = resultado["una_tienda"][0]

    assert tienda["cadena"] == TIENDA
    assert tienda["total_cent"] == COSTE_ESPERADO, "3 unidades de B con 3x2 son dos pagadas"
    elegido = tienda["productos"][0]
    assert elegido["producto_id"] == B, "se cobra y se enseña la alternativa aceptada, no A"


# --- 2. El cierre: la discrepancia, en forma ejecutable ---------------------------------------


def test_el_cierre_guarda_la_alternativa_confirmada_y_no_el_pedido(motor):
    """**El contrato de F01, y ahora se cumple.**

    El cierre escribe lo que se compro: si la persona acepto B en alcampo y se lleva tres, el
    historico tiene que decir **B, alcampo, 3 y 500**. *Un cierre que guardaba A a 300 no era un
    redondeo distinto: era otro producto y otro dinero.*

    *Esta prueba nacio con `xfail(strict)` porque el defecto estaba sin arreglar. Se le quito la marca
    al arreglarlo* -- **y el `strict` existia justo para obligar a eso.**
    """
    salida = cesta.coste_por_linea([_linea_guardada()])
    linea = salida["L1"]

    assert linea["cadena"] == TIENDA
    assert linea["producto_id"] == B, "el producto efectivo es el aceptado, no el pedido"
    assert linea["precio_cent"] == 250, "el precio unitario es el de B, no el de A"
    assert linea["coste_cent"] == COSTE_ESPERADO, "y el importe, el 3x2 sobre B"


# --- 3. Y que la discrepancia no venga de la estimacion ---------------------------------------


def test_estimacion_y_cierre_dan_el_mismo_numero(motor):
    """**La discrepancia, a cero.** *Es la sucesora de la prueba que medía el defecto.*

    Mientras el defecto existia, la prueba de esta posicion afirmaba que los dos caminos
    **discrepaban** -- 900 contra 500 --. Ahora afirma el contrato: **lo que se estima y lo que se
    archiva son el mismo producto, la misma tienda, la misma cantidad y el mismo dinero.**

    *Se conserva en vez de borrarla porque la igualdad es el criterio, y una prueba que afirma la
    igualdad es la que impide que la discrepancia vuelva.*
    """
    estimado = cesta.donde_comprar([_peticion()], [TIENDA])["una_tienda"][0]["total_cent"]
    salida = cesta.coste_por_linea([_linea_guardada()])["L1"]

    assert estimado == COSTE_ESPERADO
    assert salida["coste_cent"] == estimado, "la estimacion y el cierre no pueden discrepar"
