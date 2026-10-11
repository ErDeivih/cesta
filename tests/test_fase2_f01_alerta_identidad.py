"""F01 · **la alerta sigue al producto cuando el grupo se renumera.**

Hallazgo #9 de la revisión: *«resolver cualquier consumidor aún ligado a ordinal»*. **El consumidor era
`alerta`**, y el defecto tenía daño medido: *la única alerta de la base decía «Central Lechera Asturiana
brik 1 l.» y el miembro de carrefour de su grupo hoy es «Président brik 1 l.».*

*`grupo_id` es un ordinal que el emparejador **renumera en cada pasada** -- lo avisa el propio código, en
`main.py`, `cesta.py` y `catalogo.py`. El `ean` no cambia.*

**Estas pruebas no necesitan base ni red**: comprueban la resolución, que es donde estaba el defecto.
"""
from __future__ import annotations

from plataforma.api import alertas, catalogo

EAN = "8410297010200"


def test_con_ean_se_usa_el_grupo_de_hoy_y_no_el_guardado(monkeypatch):
    """**El arreglo.** *La alerta se creó para el grupo 11627; hoy ese producto está en otro grupo.*

    *Sin esto, una alerta creada antes de una reordenación vigila el producto que hoy ocupa el número
    viejo -- y el fallo es silencioso, porque las alertas son de bajada de precio.*
    """
    monkeypatch.setattr(catalogo, "por_ean", lambda ean: {"grupo_id": 99_999} if ean == EAN else {})

    assert alertas._grupo_de_hoy({"grupo_id": 11627, "ean": EAN}) == 99_999, (
        "con ean hay que vigilar el grupo de HOY, no el ordinal que se guardo al crear la alerta")


def test_sin_ean_se_queda_con_el_guardado(monkeypatch):
    """**Las alertas anteriores a la migración 016 no tienen `ean`, y tienen que seguir funcionando.**

    *Perder el aviso seria peor que darlo con la clave vieja*: es la parte conservadora del arreglo.
    """
    monkeypatch.setattr(catalogo, "por_ean", lambda ean: {"grupo_id": 99_999})

    assert alertas._grupo_de_hoy({"grupo_id": 11627}) == 11627


def test_si_el_producto_ya_no_esta_tampoco_se_pierde_la_alerta(monkeypatch):
    """*Un producto descatalogado no puede dejar a la persona sin el aviso que pidió.*

    **Se conserva el grupo guardado** -- que es lo que la alerta hacía antes del arreglo -- en vez de
    quedarse sin vigilar nada.
    """
    monkeypatch.setattr(catalogo, "por_ean", lambda ean: {})

    assert alertas._grupo_de_hoy({"grupo_id": 11627, "ean": EAN}) == 11627


def test_si_el_catalogo_falla_la_alerta_no_revienta(monkeypatch):
    """**Que no se pueda resolver no puede tumbar la pasada entera.** *Una excepción aqui dejaria sin
    evaluar todas las alertas, no solo esta.*
    """
    def _revienta(_ean):
        raise RuntimeError("el catalogo no contesta")

    monkeypatch.setattr(catalogo, "por_ean", _revienta)

    assert alertas._grupo_de_hoy({"grupo_id": 11627, "ean": EAN}) == 11627


def test_la_clave_de_memoria_usa_el_ean_cuando_lo_hay():
    """**Dos alertas del mismo producto tienen que compartir veredicto**, que es para lo que existe la
    memoria: *mirar gold una vez por día en vez de una vez por visita.*

    *Con el ordinal en la clave, dos alertas del mismo producto creadas a los dos lados de una
    reordenación se calcularían dos veces -- y peor: una podría quedar sin veredicto.*
    """
    una = {"grupo_id": 11627, "ean": EAN, "tipo": "minimo_90d", "umbral_cent": None}
    otra = {"grupo_id": 55, "ean": EAN, "tipo": "minimo_90d", "umbral_cent": None}

    assert alertas._clave(una) == alertas._clave(otra), (
        "el mismo producto es la misma pregunta, aunque el ordinal haya cambiado")

    # Y sin ean la clave sigue siendo el grupo guardado, como antes.
    vieja = {"grupo_id": 11627, "tipo": "minimo_90d", "umbral_cent": None}
    assert alertas._clave(vieja) == (11627, "minimo_90d", None)


def test_no_queda_ninguna_decision_de_alerta_usando_el_ordinal():
    """**La guarda que impide que el defecto vuelva.** *Se lee la fuente: si alguien vuelve a decidir con
    `a["grupo_id"]` en vez de con `_grupo_de_hoy`, esto lo dice.*
    """
    from pathlib import Path

    fuente = (Path(__file__).resolve().parents[1]
              / "plataforma" / "api" / "alertas.py").read_text(encoding="utf-8")

    assert 'int(a["grupo_id"])' not in fuente, (
        "la evaluacion tiene que usar `_grupo_de_hoy`, que resuelve por `ean`: decidir con el ordinal es "
        "el defecto que la migracion 016 arregla")
    assert "def _grupo_de_hoy" in fuente
