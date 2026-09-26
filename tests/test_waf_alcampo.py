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

    Se comprueba en el codigo porque abrir un navegador de verdad en una prueba es justo lo
    que no se hace; la medicion con la ventana delante esta hecha a mano y escrita en
    `core/waf.py` (ventana en `-2400,-2400` con el escritorio empezando en `-1.920`: sus
    ultimos 900 px caian en el monitor de la izquierda).
    """
    fuente = (waf.__file__)
    with open(fuente, encoding="utf-8") as f:
        codigo = f.read()
    assert "ARGS_FUERA_DE_LA_VISTA" in codigo, "la ventana se abre donde se ve"
    # Los argumentos tienen que acabar en la configuracion del navegador, con cualquiera
    # de las dos formas de escribirlo (clave de diccionario o asignacion a la clave).
    assert re.search(r"args[\"']?\s*[:=]|\[\s*[\"']args[\"']\s*\]\s*=", codigo), (
        "los argumentos no se estan pasando al navegador")
    # Y solo cuando hay ventana: en modo oculto no hace falta colocarla.
    assert "if not headless:" in codigo


def test_la_posicion_se_calcula_con_el_escritorio_de_verdad():
    """**El segundo fallo, y el que explicaba por que el dueno seguia viendola.**

    `-2400,-2400` escrito a mano no esta fuera de la vista en un escritorio de dos monitores:
    aqui el escritorio virtual empieza en x=-1.920, asi que una ventana de 1.382 px colocada
    en -2.400 asoma 900 px por el monitor de la izquierda.

    Y no basta con contar con el tamano que pedimos: **Chromium no hace caso de
    `--window-size`** cuando el perfil ya tiene el suyo (900x700 pedidos, 1.382x1.034 reales),
    asi que el margen se calcula con el escritorio entero. Se comprueba con varios
    escritorios de mentira: uno solo, dos en fila y dos en cruz.
    """
    for esc in ((0, 0, 1920, 1080), (-1920, 0, 3840, 1083), (-3840, -1080, 5760, 2160)):
        x, y = waf.posicion_fuera(esc, 900, 700)
        assert x + 900 <= esc[0], f"la ventana asoma por la derecha en {esc}"
        assert y + 700 <= esc[1], f"la ventana asoma por abajo en {esc}"
        # Y ni maximizada, que es lo que de verdad puede pasar (1.382x1.034 medidos).
        assert x + esc[2] <= esc[0], f"maximizada asoma por la derecha en {esc}"
        assert y + esc[3] <= esc[1], f"maximizada asoma por abajo en {esc}"
    # La posicion del primer arreglo, con el escritorio de dos monitores de verdad:
    assert not (-2400 + 1382 <= -1920), (
        "el control de la cuenta: -2400 con un monitor a la izquierda si asomaba")


def test_el_escritorio_de_verdad_se_lee_y_no_se_supone():
    """La funcion que mira las metricas del sistema devuelve un rectangulo usable.

    En este ordenador es el de dos monitores; en cualquier otro, el suyo. Si no se puede
    preguntar al sistema, hay un rectangulo de emergencia del que sale una posicion que no
    cae dentro de nada razonable.
    """
    esc = waf.escritorio()
    assert len(esc) == 4
    assert esc[2] > 0 and esc[3] > 0
    x, y = waf.posicion_fuera(esc, 900, 700)
    assert x < esc[0] and y < esc[1]


def test_el_colector_reintenta_con_la_misma_sesion_antes_del_navegador():
    """La politica, escrita en un numero: dos reintentos sin navegador, y luego se
    renueva. Si esto se pone a cero, cada corte vuelve a abrir una ventana."""
    assert alcampo.REINTENTOS_SIN_NAVEGADOR >= 1, (
        "sin reintentos, cada reto del WAF abre un navegador a la vista: medido, "
        "13 veces en un dia")
    assert alcampo.REINTENTOS_SIN_NAVEGADOR <= 5, (
        "demasiados reintentos: la espera crece con cada corte y se topa en 90s, "
        "asi que insistir sale mas caro que renovar la sesion")

