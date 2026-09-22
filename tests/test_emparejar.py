"""El canal de vectores tiene que ser **opt-in**, no opt-out.

Esta prueba existe por un fallo que no da error, solo tarda: hasta el 23 de
septiembre de 2026 `enlaces()` traia `usar_vectores=True` por defecto, con el
razonamiento de que si no habia vectores cacheados no pasaba nada. Y era verdad
mientras la cache estaba a medias. El dia que se completo (52.567 vectores, el
catalogo entero) el razonamiento se dio la vuelta: el emparejamiento con vectores
**no termino en 62 minutos** y hubo que pararlo, contra 90 segundos sin ellos.

Y como el defecto era `True`, cualquiera que llamara a `enlaces()` se metia en ese
camino sin decirlo: la tarea diaria de las 06:00, el diagnostico y el medidor de
la Fase 3. Sin un error, sin un aviso, sin nada: solo tres horas de reloj.

La causa de fondo esta en `core.embeddings.candidatos` y esta sin arreglar (una
consulta con el JOIN por bloque sobre toda la tabla, y el coseno calculado dos
veces por par). Mientras eso no se arregle, el canal se pide a proposito.

Lo que aqui se prueba no es "los vectores van mal": es que **no se encienden
solos**. La calidad esta medida y es buena (`docs/DIAGNOSTICO-MATCHING.md` §22).
"""
from __future__ import annotations

import inspect

from core import embeddings
from core.matching import enlaces
from projects.cesta import emparejar


def _filas():
    return [
        {"fuente": "a", "nombre": "Leche semidesnatada Asturiana 1 L",
         "marca": "Asturiana", "cantidad": 1.0, "unidad_canon": "l", "ean": None},
        {"fuente": "b", "nombre": "Leche semidesnatada Central Lechera Asturiana",
         "marca": "Asturiana", "cantidad": 1.0, "unidad_canon": "l", "ean": None},
    ]


def test_el_defecto_de_enlaces_no_enciende_los_vectores():
    """El parametro, leido de la firma: si alguien lo vuelve a poner en `True`,
    esta prueba lo dice antes de que lo diga el reloj a las tres de la manana."""
    defecto = inspect.signature(enlaces).parameters["usar_vectores"].default
    assert defecto is False, (
        "`enlaces()` vuelve a traer los vectores encendidos por defecto: "
        "cualquier llamada que no lo diga se mete en un camino que tarda horas "
        "(medido: mas de 62 minutos contra 90 segundos). Si `candidatos` ya esta "
        "arreglado, cambia esto y mide otra vez antes de dejarlo asi.")


def test_una_llamada_normal_no_toca_los_vectores(monkeypatch):
    """La comprobacion de verdad: que no los cargue, no que lo diga la firma."""
    def revienta(*_a, **_k):
        raise AssertionError(
            "`enlaces()` ha cargado los vectores sin que se lo pidieran")

    monkeypatch.setattr(embeddings, "carga", revienta)
    # Asi es como llama la pasada diaria: sin decir nada de vectores.
    enlaces(_filas(), umbral=0.55, usar_ean=False)


def test_pidiendolos_si_los_carga(monkeypatch):
    """El otro lado, para que la prueba anterior no pase por no hacer nada."""
    llamadas = []

    def falsa(*_a, **_k):
        llamadas.append(True)
        return {}

    monkeypatch.setattr(embeddings, "carga", falsa)
    enlaces(_filas(), umbral=0.55, usar_ean=False, usar_vectores=True)
    assert llamadas, "pidiendo los vectores, `enlaces()` no los ha pedido"


def test_la_pasada_diaria_lleva_los_vectores_apagados():
    """El interruptor de la tarea de las 06:00, en un solo sitio."""
    assert emparejar.USAR_VECTORES is False, (
        "la pasada diaria ha vuelto a encender el canal de vectores, que hoy "
        "tarda mas de una hora: lee el comentario de `USAR_VECTORES` en "
        "`projects/cesta/emparejar.py` antes de cambiarlo")


def test_lo_que_el_resumen_dice_de_los_vectores_es_lo_que_se_uso():
    """El resumen decia "si" solo porque el fichero de vectores existia.

    Con el canal apagado, dos pasadas con numeros distintos parecerian iguales.
    """
    fuente = inspect.getsource(emparejar.main)
    assert "USAR_VECTORES and emb.camino().exists()" in fuente, (
        "el resumen ha vuelto a deducir si se usaron los vectores mirando si el "
        "fichero existe, en vez de mirar si la pasada los uso")
