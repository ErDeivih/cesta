"""El orden de los favoritos: lo que ha bajado arriba, y lo que no se puede medir al final.

La pantalla de favoritos dice desde el primer dia, en su propio texto, que va «ordenada por lo
que ha cambiado y no alfabeticamente». El 30 de septiembre de 2026 se leyo el codigo contra esa
frase y no era verdad: la API devolvia los favoritos en el orden en que se anadieron. El orden
vive en `main._orden_de_favoritos`, y esto lo fija, porque es una funcion pura y no hace falta
ni base de datos ni navegador.
"""
from plataforma.api.main import _orden_de_favoritos


def _f(nombre, pct=None, comparable=True, motivo=None):
    return {"nombre": nombre, "comparable": comparable, "motivo": motivo,
            "variacion_pct": pct}


def test_lo_que_ha_bajado_va_primero_y_lo_que_mas_primero():
    favs = [_f("quieto", 0.0), _f("baja poco", -2.0), _f("baja mucho", -18.0),
            _f("sube", 4.0)]
    assert [f["nombre"] for f in sorted(favs, key=_orden_de_favoritos)] == [
        "baja mucho", "baja poco", "sube", "quieto"]


def test_lo_que_no_se_puede_comparar_va_al_final_y_con_su_motivo():
    """Un favorito sin historico no se puede poner en medio: no se sabe donde va."""
    favs = [_f("sin historico", comparable=False, motivo="sin historico"),
            _f("sube", 4.0), _f("baja", -3.0)]
    orden = [f["nombre"] for f in sorted(favs, key=_orden_de_favoritos)]
    assert orden == ["baja", "sube", "sin historico"]


def test_un_movimiento_de_un_centimo_no_se_llama_igual():
    """Un 0,4 % en el precio por unidad es un centimo en un euro: es un dato, no ruido.

    El umbral de `movimientos.MINIMO_PCT` (3 %) es para **no anunciar una bajada** en la
    pantalla de bajadas. Aqui se viene a ver que se ha movido, y esconder un 0,4 % seria
    esconder el movimiento que hay.
    """
    favs = [_f("igual", 0.0), _f("baja un pelo", -0.4), _f("sube un pelo", 0.3)]
    assert [f["nombre"] for f in sorted(favs, key=_orden_de_favoritos)] == [
        "baja un pelo", "sube un pelo", "igual"]


def test_dos_que_han_bajado_lo_mismo_se_ordenan_por_su_nombre():
    """Con el mismo cambio, el orden tiene que ser el mismo dos veces: por nombre."""
    favs = [_f("Zumo", -5.0), _f("Aceite", -5.0)]
    assert [f["nombre"] for f in sorted(favs, key=_orden_de_favoritos)] == ["Aceite", "Zumo"]
