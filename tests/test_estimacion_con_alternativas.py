"""La estimacion y el coste por linea no cuentan las alternativas, y no revientan con su clave.

**La forma autentica, observada en `_candidatos` y no supuesta:**

    mejor[(grupo_o_producto, fuente)]      = (*fila, exacta)     <- el precio es v[1]
    mejor[(grupo_o_producto, "alternativa")] = (*fila, False)    <- un elemento mas

El lector descomponia la clave como un par, y la **alternativa tiene tres**, asi que reventaba al ejecutarse.
La suite estaba verde: lo encontro el ensayo de punta a punta sobre la lista de la compra.

Y la alternativa **no puede entrar en el total exacto**: la revision dice que un aviso de alternativa no
autoriza una sustitucion.
"""
from __future__ import annotations

from plataforma.api import cesta


def _mejor_con_forma_autentica(precios, precio_alternativa):
    """Las claves, tal como las construye `_candidatos`: un par para lo canonico, un trio la alternativa."""
    mejor = {}
    for cadena, precio in precios.items():
        mejor[(7, cadena)] = (7, precio, "MANZANAS", None, None, None, None, True)
    mejor[(7, "alternativa")] = (7, precio_alternativa, "PERAS", None, None, None, None, False)
    return mejor


def _una_linea():
    return {"id": "l1", "nombre_visto": "MANZANAS", "cantidad": 2, "grupo_id": 7,
            "producto_id": None, "en_carrito": False, "tachado_en": None}


def test_la_estimacion_no_revienta_con_la_clave_de_la_alternativa(monkeypatch):
    mejor = _mejor_con_forma_autentica({"DIA": 100, "MERCADONA": 90}, 50)
    monkeypatch.setattr(cesta, "_candidatos", lambda peticiones, fecha: mejor)
    resultado = cesta.estimacion([_una_linea()])
    assert resultado["sin_precio"] == 0, resultado
    assert resultado["total_cent"] == 180, resultado


def test_la_alternativa_barata_no_entra_en_el_total(monkeypatch):
    """5 centimos no pueden ganar a 90: la sustitucion no esta autorizada."""
    mejor = _mejor_con_forma_autentica({"DIA": 100, "MERCADONA": 90}, 5)
    monkeypatch.setattr(cesta, "_candidatos", lambda peticiones, fecha: mejor)
    assert cesta.estimacion([_una_linea()])["total_cent"] == 180


def test_el_coste_por_linea_lee_la_misma_forma(monkeypatch):
    """`coste_por_linea` guarda el precio al cerrar la compra: si revienta, no se puede cerrar."""
    mejor = _mejor_con_forma_autentica({"DIA": 100, "MERCADONA": 90}, 50)
    monkeypatch.setattr(cesta, "_candidatos", lambda peticiones, fecha: mejor)
    costes = cesta.coste_por_linea([_una_linea()])
    assert costes, costes
