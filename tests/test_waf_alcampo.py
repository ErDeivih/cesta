"""El navegador del WAF: que no se abra una ventana si no hace falta.

El 25 de septiembre de 2026 el dueno dijo *"a veces salta el navegador"* sobre la
tarea de Alcampo, y era verdad: el WAF corta entre 8 y 13 veces al dia (13 el 24 de
septiembre, 10 el 23) y **cada corte abria Chrome a la vista**. La tarea de las seis
de la manana le robaba el foco al ordenador una docena de veces.

Lo que se fija aqui:

  1. **`waf.renueva` prueba primero sin ventana** y solo abre la ventana si el modo
     oculto no pasa el reto. El orden importa y esta razonado en el modulo: el modo
     oculto pasa menos retos, pero cuando pasa, pasa, y no molesta a nadie.
  2. **El colector reintenta con la misma sesion antes de tocar el navegador.**
     Muchos cortes son del momento (una racha de peticiones) y con la espera la
     misma cookie vuelve a valer.
"""
import re
from unittest import mock

from core import waf
from projects.cesta.collectors import alcampo


def _sesion(via="sin_ventana"):
    return {"cookies": {"aws-waf-token": "x"}, "user_agent": "Chrome", "via": via}


def test_renueva_prueba_sin_ventana_y_no_abre_nada_si_pasa():
    llamadas = []

    def obtener(dominio, url, headless=None):
        llamadas.append(headless)
        return _sesion()

    with mock.patch.object(waf, "obtener", obtener):
        sesion = waf.renueva("compraonline.alcampo.es", "https://x/cat")

    assert llamadas == [True], "se ha abierto (o probado) ventana sin necesidad"
    assert sesion["via"] == "sin_ventana"


def test_si_sin_ventana_no_pasa_el_reto_se_abre_la_ventana():
    """Quedarse sin catalogo por no abrir una ventana seria cambiar un dato por una
    comodidad. La ventana es el ultimo recurso, no un recurso prohibido."""
    llamadas = []

    def obtener(dominio, url, headless=None):
        llamadas.append(headless)
        if headless:
            raise RuntimeError("no pasa el reto sin ventana")
        return _sesion("con_ventana")

    with mock.patch.object(waf, "obtener", obtener):
        sesion = waf.renueva("compraonline.alcampo.es", "https://x/cat")

    assert llamadas == [True, False]
    assert sesion["via"] == "con_ventana"


def test_la_ventana_se_abre_fuera_de_la_vista():
    """Una ventana de Chrome en medio del escritorio mientras trabajas es lo que el dueno
    senalo dos dias seguidos. El reto necesita un navegador de verdad, **no** que se vea:
    los mismos retos pasan con la ventana colocada fuera del area visible.

    Se comprueba en el codigo porque la posicion no se puede medir sin abrir un navegador
    de verdad, y abrirlo en una prueba es justo lo que no se hace."""
    fuente = (waf.__file__)
    with open(fuente, encoding="utf-8") as f:
        codigo = f.read()
    assert "ARGS_FUERA_DE_LA_VISTA" in codigo, "la ventana se abre donde se ve"
    assert "--window-position=-2400,-2400" in codigo, (
        "la ventana tiene que colocarse fuera del area visible")
    # Los argumentos tienen que acabar en la configuracion del navegador, con cualquiera
    # de las dos formas de escribirlo (clave de diccionario o asignacion a la clave).
    assert re.search(r"args[\"']?\s*[:=]|\[\s*[\"']args[\"']\s*\]\s*=", codigo), (
        "los argumentos no se estan pasando al navegador")
    # Y solo cuando hay ventana: en modo oculto no hace falta colocarla.
    assert "if not headless:" in codigo


def test_el_colector_reintenta_con_la_misma_sesion_antes_del_navegador():
    """La politica, escrita en un numero: dos reintentos sin navegador, y luego se
    renueva. Si esto se pone a cero, cada corte vuelve a abrir una ventana."""
    assert alcampo.REINTENTOS_SIN_NAVEGADOR >= 1, (
        "sin reintentos, cada reto del WAF abre un navegador a la vista: medido, "
        "13 veces en un dia")
    assert alcampo.REINTENTOS_SIN_NAVEGADOR <= 5, (
        "demasiados reintentos: la espera crece con cada corte y se topa en 90s, "
        "asi que insistir sale mas caro que renovar la sesion")

