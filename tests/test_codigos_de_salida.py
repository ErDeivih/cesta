"""*** EL DIA DEGRADADO NO SE REINTENTA. ***

*`run.py` devuelve **3** cuando el dia esta hecho pero falta alguna cadena, y **1** cuando hay que
reintentarlo.*

*Y `ejecutar.bat` escribe la marca diaria mirando ese codigo: si solo la escribe con `0`, un dia
degradado **se reintentaria en cada arranque** -- noventa minutos para volver a chocar con el
mismo WAF que ya corto.*

*** Ese acoplamiento no lo vigila nadie ***: ni un test de Python ni el tipado. Si alguien cambia
el codigo del degradado, o cambia el `if` del .bat, el fallo aparece como una recoleccion que se
repite todos los dias y nadie sabe por que.

*Estas pruebas lo dejan escrito por los dos lados.*
"""

from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def _veredicto(resultados, fallos):
    from projects.cesta import run

    return run._veredicto(resultados, fallos)


def _res(diccionario):
    return [(n, v, 1.0) for n, v in diccionario.items()]


def test_el_dia_limpio_es_cero() -> None:
    assert _veredicto(_res({"dia": True, "carrefour": True}), []) == 0


def test_el_dia_degradado_es_tres_y_no_cero() -> None:
    """*Tres, para que se distinga de un dia limpio; y no uno, porque el dia esta hecho.*"""
    codigo = _veredicto(_res({"dia": True, "carrefour": False}), ["carrefour"])
    assert codigo == 3, "el degradado tiene su propio codigo (M18)"
    assert codigo != 1, "y NO es un dia perdido: no se reintenta"


def test_sin_pipeline_o_sin_ninguna_cadena_es_uno() -> None:
    assert _veredicto(_res({"dia": True}), ["pipeline"]) == 1
    assert _veredicto(_res({"dia": False}), ["dia"]) == 1


def test_el_bat_escribe_la_marca_tambien_con_tres() -> None:
    """*** El acoplamiento que nadie mas vigila. ***"""
    bat = (RAIZ / "ejecutar.bat").read_text(encoding="utf-8", errors="replace")
    assert "!CODIGO!==3" in bat, (
        "ejecutar.bat tiene que aceptar 3 como dia hecho: si solo acepta 0, el degradado se "
        "reintenta en cada arranque"
    )
    # *Y las dos ramas escriben la marca, no solo la del 0.*
    i = bat.index("!CODIGO!==3")
    tramo = bat[i:i + 400]
    assert 'echo !HOY!> "%MARCA%"' in tramo, "la rama del 3 tiene que escribir la marca"


def test_el_codigo_de_verdad_llega_al_bat() -> None:
    """*El .bat recoge `errorlevel` del run, no un valor inventado en el propio .bat.*"""
    bat = (RAIZ / "ejecutar.bat").read_text(encoding="utf-8", errors="replace")
    assert "set CODIGO=!errorlevel!" in bat
