"""F05 (fase 2): **que el ciclo siga reconciliando la cola de fichas.**

*Medido:* la cola contaba como pendiente **7.565 fichas que ya tenian su dato** en el maestro -- *el colector
las trae y no avisa a la cola.* Se corrigio sobre la cola real (79.887 -> 72.322) **y se puso en el ciclo**
(`run.py`, tras el pipeline) para que no se vuelva a acumular.

**Estas pruebas fijan ese cableado.** *Sin ellas, alguien puede quitar la llamada en una limpieza y el
problema vuelve en silencio* -- *que es exactamente como aparecio: nadie rompio nada, simplemente las dos
vias nunca se hablaron.*

*Se lee la fuente: es lo unico comprobable sin correr el ciclo entero, que necesita red.*
"""
from __future__ import annotations

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
RUN = RAIZ / "projects" / "cesta" / "run.py"


def test_el_ciclo_reconcilia_la_cola():
    """**La llamada, en `run.py`.** *Si alguien la quita, la deuda falsa vuelve y nadie se entera.*"""
    fuente = RUN.read_text(encoding="utf-8")

    assert "reconciliar_fichas" in fuente, (
        "el ciclo tiene que reconciliar la cola: sin esto, la deuda falsa se vuelve a acumular en silencio")
    assert "reconciliacion" in fuente.lower() or "reconcilia(" in fuente, (
        "y tiene que llamar al reconciliador, no solo importarlo")


def test_la_reconciliacion_va_despues_del_pipeline():
    """**Y en su sitio.** *Los maestros los escribe el pipeline: reconciliar antes seria mirar los de ayer.*

    *Se comprueba por la posicion en la fuente -- el pipeline primero, la reconciliacion despues --, que es
    lo unico que se puede afirmar sin correr el ciclo.*
    """
    fuente = RUN.read_text(encoding="utf-8")

    pos_pipeline = fuente.index("pipeline\").main(publicar=False)")
    pos_reconcilia = fuente.index("reconciliar_fichas")

    assert pos_reconcilia > pos_pipeline, (
        "la reconciliacion tiene que ir DESPUES del pipeline: los maestros del dia los escribe el pipeline")


def test_un_fallo_al_reconciliar_no_tumba_el_dia():
    """**El catalogo esta bien aunque la cola quede sin reconciliar.** *Un fallo se avisa y se sigue* --
    *el mismo trato que el manifiesto, y por la misma razon: es mantenimiento, no el catalogo.*
    """
    fuente = RUN.read_text(encoding="utf-8")

    # El bloque de la reconciliacion, desde su comentario hasta el cierre del `except`.
    desde = fuente.index("La cola de fichas se reconcilia")
    bloque = fuente[desde:desde + 3000]

    assert "except Exception" in bloque, (
        "un fallo al reconciliar tiene que capturarse: si sube, tumba el dia por mantenimiento")
    assert 'fallos.append("inventario")' not in bloque and 'fallos.append("reconciliar")' not in bloque, (
        "y NO puede entrar en `fallos`: la cola no es el catalogo, y el dia no se pierde por ella")


def test_solo_dice_la_linea_cuando_hay_algo_que_decir():
    """**La regla de la casa.** *Con cero reconciliadas no se imprime nada* -- *una linea que sale siempre
    deja de leerse.*
    """
    fuente = RUN.read_text(encoding="utf-8")
    desde = fuente.index("La cola de fichas se reconcilia")
    bloque = fuente[desde:desde + 3000]

    assert re.search(r"if cuenta\[.reconciliadas.\]:", bloque), (
        "la linea del inventario tiene que ir dentro de un `if`: si sale siempre, deja de leerse")
