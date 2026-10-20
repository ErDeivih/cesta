"""*** UN DIA SIN CAPTURA ES UN HUECO, NO UN DIA QUE NO EXISTIO. ***

*El caso que lo motiva es real: **Carrefour no capturo el 18 de octubre de 2026** (7 de 44 dias medidos), y la serie
salia del servidor **solo con los dias capturados**.* *Asi que el 17 y el 19 llegaban al cliente **como si fueran
consecutivos**, y la chispa unia los dos puntos como si el precio hubiera cambiado de un dia para otro.*

*Y el cliente llevaba meses preparado: `chispa.ts` tiene una prueba llamada «un dia sin valor se coloca como HUECO,
no se salta», con el motivo escrito -- «saltarlo juntaria dos dias que no son seguidos, y la linea mentiria».*
*** Faltaba mandarselos. ***
"""

from core.serie_con_huecos import rellena_huecos


def fila(fecha: str, precio, producto_id="cesta:1", fuente="carrefour"):
    return {"producto_id": producto_id, "fuente": fuente, "fecha": fecha,
            "precio_unidad_cent": precio, "unidad_canon": "kg"}


def test_sin_huecos_la_serie_se_devuelve_igual():
    """*Nada que rellenar: los mismos puntos y los mismos precios.*"""
    serie = [fila("2026-10-17", 120), fila("2026-10-18", 125), fila("2026-10-19", 130)]
    r = rellena_huecos(serie)
    assert [f["fecha"] for f in r] == ["2026-10-17", "2026-10-18", "2026-10-19"]
    assert [f["precio_unidad_cent"] for f in r] == [120, 125, 130]


def test_un_dia_que_falta_entra_como_hueco():
    """*** El caso del 18: entre el 17 y el 19 falta uno, y tiene que aparecer. ***"""
    serie = [fila("2026-10-17", 120), fila("2026-10-19", 130)]
    r = rellena_huecos(serie)
    assert [f["fecha"] for f in r] == ["2026-10-17", "2026-10-18", "2026-10-19"]
    assert r[1]["precio_unidad_cent"] is None, "el hueco no lleva precio"
    assert r[0]["precio_unidad_cent"] == 120, "y los que estaban no se tocan"
    assert r[2]["precio_unidad_cent"] == 130


def test_varios_dias_seguidos_sin_captura():
    """*La racha mas larga medida fue de 2 dias.*"""
    serie = [fila("2026-09-11", 100), fila("2026-09-14", 110)]
    r = rellena_huecos(serie)
    assert [f["fecha"] for f in r] == ["2026-09-11", "2026-09-12", "2026-09-13", "2026-09-14"]
    assert [f["precio_unidad_cent"] for f in r] == [100, None, None, 110]


def test_no_se_rellena_fuera_del_rango_del_producto():
    """*** Un producto que empezo a verse el 12 no tiene huecos antes del 12. ***"""
    serie = [fila("2026-10-12", 100), fila("2026-10-14", 110)]
    r = rellena_huecos(serie)
    # *Solo el 13, entre el primero y el ultimo. Nada antes del 12 ni despues del 14.*
    assert [f["fecha"] for f in r] == ["2026-10-12", "2026-10-13", "2026-10-14"]


def test_cada_producto_tiene_su_propio_rango():
    """*Dos productos de la misma cadena, sin compartir huecos.*"""
    serie = [
        fila("2026-10-17", 120, "cesta:1"),
        fila("2026-10-19", 130, "cesta:1"),
        fila("2026-10-18", 200, "cesta:2"),
    ]
    r = rellena_huecos(serie)
    unos = [f for f in r if f["producto_id"] == "cesta:1"]
    otros = [f for f in r if f["producto_id"] == "cesta:2"]
    assert [f["fecha"] for f in unos] == ["2026-10-17", "2026-10-18", "2026-10-19"]
    # *El segundo solo tiene un dia: ni huecos antes ni despues.*
    assert [f["fecha"] for f in otros] == ["2026-10-18"]


def test_una_serie_vacia_no_inventa_nada():
    assert rellena_huecos([]) == []


def test_una_fecha_ilegible_no_se_coloca():
    """*Sin fecha no hay rango: la fila se devuelve tal cual, no se descarta.*"""
    r = rellena_huecos([fila("2026-10-17", 120), fila("no es fecha", 200)])
    assert len(r) == 2
    assert any(f["fecha"] == "no es fecha" for f in r)
