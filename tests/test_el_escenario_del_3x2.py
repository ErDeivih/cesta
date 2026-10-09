"""El escenario del 3x2, en las cuatro superficies que dan precio.

Producto a 100 centimos, oferta `3x2`, tres unidades. Lo que se exige es **igualdad exacta** en 200 centimos:
- **lista** (`estimacion`), que es el numero que se mira;
- **reparto** (`reparto_por_tienda`), que es el que se decide por tienda;
- **cierre** (`coste_por_linea`), que es lo que se guarda;
- **historico**, que es la cuenta con la que se escribe el registro (`_lo_que_se_paga`).

Cada una, **en una linea y en dos**. Y una compra prevista a 200 y guardada a 100 no pasa: se compara exacto.
"""
from __future__ import annotations

from plataforma.api import cesta
from plataforma.api.almacen import _lo_que_se_paga

PRECIO = 100
PROMO = "3x2"
ESPERADO = 200


def _monta(monkeypatch):
    """Un unico candidato, a 100 centimos, con 3x2. Nada de azar: siempre el mismo."""

    def candidatos(peticiones, fecha_tope):
        mejor = {}
        for p in peticiones:
            for fuente in ("dia",):
                mejor[cesta._llave_candidato(p.grupo_id, p.producto_id, fuente)] = (
                    "dia:P1", PRECIO, "Leche", PROMO, None, None, None, ESPERADO, True)
        return mejor

    monkeypatch.setattr(cesta, "_candidatos", candidatos)
    monkeypatch.setattr(cesta, "_promos_vigentes", lambda *a, **k: {})


def _linea(linea_id, cantidad):
    return {"id": linea_id, "grupo_id": 7, "producto_id": "dia:P1", "cantidad": cantidad,
            "nombre_visto": "Leche", "cadena_elegida": None, "producto_movido": False}


def _pet(cantidad):
    return cesta.Peticion(grupo_id=7, producto_id="dia:P1", cantidad=cantidad, nombre="Leche")


def _lista(cantidades):
    return cesta.estimacion([_linea(f"l{i}", c) for i, c in enumerate(cantidades)])["total_cent"]


def _reparto(cantidades):
    r = cesta.reparto_por_tienda([_pet(c) for c in cantidades], ["dia"] * len(cantidades), ["dia"])
    return r["sublistas"][0]["total_cent"]


def _cierre(cantidades):
    salida = cesta.coste_por_linea([_linea(f"l{i}", c) for i, c in enumerate(cantidades)])
    return sum(int(v["coste_cent"]) for v in salida.values())


def _historico(cantidades):
    """La cuenta con la que se escribe el registro, linea a linea."""
    salida = cesta.coste_por_linea([_linea(f"l{i}", c) for i, c in enumerate(cantidades)])
    return sum(_lo_que_se_paga(v["precio_cent"], v["coste_cent"], c)
               for v, c in zip((salida[f"l{i}"] for i in range(len(cantidades))), cantidades, strict=True))


def test_la_lista_da_200_en_una_linea_y_en_dos(monkeypatch):
    _monta(monkeypatch)
    assert _lista([3]) == ESPERADO, "tres en una linea"
    assert _lista([1, 2]) == ESPERADO, "una y dos en dos lineas"


def test_el_reparto_da_200_en_una_linea_y_en_dos(monkeypatch):
    _monta(monkeypatch)
    assert _reparto([3]) == ESPERADO
    assert _reparto([1, 2]) == ESPERADO


def test_el_cierre_guarda_200_en_una_linea_y_en_dos(monkeypatch):
    _monta(monkeypatch)
    assert _cierre([3]) == ESPERADO
    assert _cierre([1, 2]) == ESPERADO


def test_el_historico_se_escribe_con_200_en_una_linea_y_en_dos(monkeypatch):
    _monta(monkeypatch)
    assert _historico([3]) == ESPERADO
    assert _historico([1, 2]) == ESPERADO


def test_lo_previsto_y_lo_guardado_son_el_mismo_numero(monkeypatch):
    """La invariante del dueno, junta: la lista y el cierre no pueden discrepar."""
    _monta(monkeypatch)
    assert _lista([1, 2]) == _cierre([1, 2]) == ESPERADO
