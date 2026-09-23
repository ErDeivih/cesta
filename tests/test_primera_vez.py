"""La primera vez: la aplicacion ensenandose funcionando, y puesta de verdad.

Claude puso esto el primero de los once puntos del encargo, y con razon: *"cuando
un amigo se registra ve un buscador vacio, una cesta vacia y un panel de indices
que no significa nada. Es el peor momento de la aplicacion y el unico que todo el
mundo ve."* Y se arregla **ensenando cuatro precios reales**, no con una visita
guiada: una guia se lee una vez, cuatro precios se entienden solos.

Estas pruebas son de las cosas que no dan error cuando se rompen:

  - **El componente existe y no lo pinta nadie.** Paso exactamente eso el 23 de
    septiembre de 2026: `LoQueSeCompra.tsx` estaba escrito, compilaba, y **no lo
    llamaba ninguna pantalla**. Una tarjeta que no se pinta no se nota ni en
    `tsc` ni en el `build`: se nota abriendo la aplicacion y viendo un buscador
    pelado. Por eso la primera prueba mira quien lo llama, no que exista.
  - **Un ejemplo inventado.** Si una busqueda no devuelve nada comparable, ese
    hueco no se rellena y -- si no queda ninguno -- la tarjeta **no se pinta**.
    Es la regla de siempre: un dato que no tenemos es "no lo se".
  - **De donde sale el numero.** La diferencia se resta de los dos precios del
    grupo; no se lee un `ahorro` que venga sumado por otro camino, que es como se
    cuelan los ahorros que nadie puede reproducir.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
COMPONENTE = (RAIZ / "plataforma" / "web" / "app" / "src" / "componentes"
              / "LoQueSeCompra.tsx")
MOSAICO = (RAIZ / "plataforma" / "web" / "app" / "src" / "componentes"
           / "Mosaico.tsx")
BUSCAR = (RAIZ / "plataforma" / "web" / "app" / "src" / "paginas" / "Buscar.tsx")
CESTA = (RAIZ / "plataforma" / "web" / "app" / "src" / "paginas" / "Cesta.tsx")


@pytest.fixture(scope="module")
def componente() -> str:
    if not COMPONENTE.exists():
        pytest.skip("esta copia no trae la interfaz nueva")
    return COMPONENTE.read_text(encoding="utf-8")


def test_la_tarjeta_esta_puesta_en_la_pantalla_de_entrada():
    """Escrita y sin llamar es como no tenerla."""
    if not BUSCAR.exists():
        pytest.skip("esta copia no trae la interfaz nueva")
    buscar = BUSCAR.read_text(encoding="utf-8")

    # La cadena se alargo al entrar el mosaico (`Mosaico`, que es "lo de siempre"):
    # la pantalla de entrada pinta el mosaico, y **el mosaico decide** -- con
    # historial, la cuadricula; sin historial, esta tarjeta. La decision vive en un
    # solo sitio a proposito: con la condicion en los dos, el dia que una cambie se
    # pintan las dos cosas a la vez.
    assert re.search(r"import\s*\{[^}]*\bMosaico\b[^}]*\}\s*from", buscar), \
        "la pantalla de entrada no importa el mosaico de lo de siempre"
    assert "<Mosaico />" in buscar, \
        "la pantalla de entrada importa el mosaico pero no lo pinta"

    mosaico = MOSAICO.read_text(encoding="utf-8")
    assert re.search(r"import\s*\{[^}]*\bLoQueSeCompra\b[^}]*\}\s*from", mosaico), \
        "el mosaico no importa la tarjeta de la primera vez"
    assert "<LoQueSeCompra />" in mosaico, \
        "sin historial el mosaico no cae en la tarjeta de la primera vez"

    # Y no debajo de los resultados: cuando hay busqueda en curso, no.
    assert re.search(r"\{!busca\s*&&\s*<Mosaico\s*/>\}", buscar), \
        "esto tiene que salir solo en el estado vacio, no pegado a los resultados"


def test_sin_ejemplos_comparables_no_se_pinta_nada(componente: str):
    """Nada de rellenar huecos: o hay dato de verdad, o no hay tarjeta."""
    assert "r.comparable" in componente, \
        "los ejemplos tienen que venir de grupos comparables, no de cualquiera"
    assert re.search(r"if\s*\(\s*ejemplos\.length\s*===\s*0\s*\)\s*return\s+null", componente), \
        "sin ejemplos comparables la tarjeta tiene que devolver null"


def test_la_diferencia_se_resta_de_los_dos_precios_del_grupo(componente: str):
    """Reproducible: barato y caro del mismo grupo, en por ciento."""
    assert "precio_unidad_cent" in componente and "precio_unidad_max_cent" in componente, \
        "la diferencia se calcula con los dos precios del grupo"
    # Y no se anuncia diferencia cuando la cadena mas cara no es mas cara: el 0 %
    # de un grupo de una sola cadena no es un ahorro, es que no hay comparacion.
    assert re.search(r"caro\s*<=\s*barato\s*\)\s*return\s+null", componente), \
        "sin dos precios distintos no hay diferencia que ensenar"


def test_la_cesta_vacia_no_es_un_cartel_que_manda_a_buscar():
    """El §2 lista **la cesta vacia** entre el peor momento de la aplicacion.

    Y lo era en el sentido literal: la pantalla decia "busca un producto, abre su ficha y
    pulsa Añadir a la cesta", o sea tres pasos para volver al mismo sitio, con la
    aplicacion sin hacer nada por quien acaba de llegar. Ahora pinta la cuadricula
    (`Mosaico`, que apunta de un toque) con la compra basica o lo que compra la casa.

    Medido en un navegador el 23 de septiembre de 2026 con una cuenta recien creada: la
    pantalla ensenaba seis productos reales con su cadena mas barata (leche entera 0,96
    EUR/l en Aldi, pan de molde 1,33 EUR/kg...), y **un toque** dejaba la cesta con su
    linea, su total (0,96 EUR) y su pasillo.
    """
    if not CESTA.exists():
        pytest.skip("esta copia no trae la interfaz nueva")
    cesta = CESTA.read_text(encoding="utf-8")

    assert re.search(r"import\s*\{[^}]*\bMosaico\b[^}]*\}\s*from", cesta), \
        "la cesta no importa la cuadricula"
    # En **los dos** estados vacios: sin ninguna lista, y con la lista sin lineas. Son dos
    # ramas distintas del mismo fichero (una sale antes de pintar la lista) y las dos se
    # ven: la primera, al registrarse; la segunda, al quitar la ultima linea.
    assert cesta.count("<Mosaico limite={6} vacia />") == 2, (
        "la cuadricula no esta en los dos estados vacios de la cesta: "
        f"{cesta.count('<Mosaico limite={6} vacia />')}")
    # Y la frase deja de mandar a otra pantalla a hacer el trabajo.
    assert "abre su ficha y pulsa" not in cesta, \
        "la cesta vacia vuelve a mandar a la ficha a dar tres pasos"


def test_con_la_cesta_vacia_la_compra_basica_si_se_ensena():
    """La excepcion a la regla del mosaico, escrita y con su razon.

    En el buscador, sin historial **no se pinta la cuadricula de basicos**: son 24
    recuadros que no explican nada (`Mosaico.tsx`, regla 1). En la cesta vacia si, porque
    la pregunta que se trae a esa pantalla es *"¿que me falta?"* y con la lista vacia la
    respuesta es "todo". Lo que no puede pasar es que se ensene **sin decir de donde
    sale**: titulada "Lo de siempre", una cuadricula de la compra basica seria una mentira
    dicha en un titulo.
    """
    mosaico = MOSAICO.read_text(encoding="utf-8")
    assert "vacia = false" in mosaico, "no hay forma de pedir la cuadricula en la cesta"
    assert re.search(r"soloBasico\s*&&\s*!vacia", mosaico), \
        "`vacia` no quita el respaldo de la tarjeta de la primera vez"
    assert "TITULO[tarjetas[0]?.origen]" in mosaico, \
        "el titulo no dice de donde sale lo que se esta viendo"


def test_los_cuatro_basicos_son_cuatro_y_de_nombre_llano(componente: str):
    """Cuatro, y ninguno cuyo primer resultado sea otra cosa.

    `huevos` estuvo en la lista y se quito: medido contra la API viva, su primer
    resultado es «Media tortilla de patata con cebolla». Esto no puede volver a
    colarse sin que salte aqui, porque en pantalla se lee como un error.
    """
    m = re.search(r"const BASICOS = \[(?P<lista>[^\]]*)\]", componente)
    assert m, "no encuentro la lista de basicos"
    basicos = re.findall(r"'([^']+)'", m.group("lista"))
    assert len(basicos) == 4, f"son cuatro, no {len(basicos)}: {basicos}"
    assert "huevos" not in basicos, \
        "los huevos vuelven a estar: su primer resultado es una tortilla"


def test_el_ejemplo_tiene_que_hablar_de_lo_que_se_ha_buscado(componente: str):
    """El primero a secas no vale, y esto lo vio el navegador (23 sep 2026).

    Buscar «aceite de oliva» devolvia **«Picos sin gluten»** el primero, y la tarjeta de la
    primera vez -- lo unico que ve quien acaba de llegar -- lo pintaba como ejemplo de
    comparar precios. Cualquiera que lo lea piensa que la aplicacion esta rota, y con razon.

    La regla: **el nombre tiene que repetir la palabra buscada** (la primera, que es el
    sustantivo). Se piden cinco resultados y se coge el primero que la cumpla; si ninguno
    la cumple, esa busqueda no aporta nada y se cae sola.
    """
    assert "elQueHablaDe(" in componente, \
        "se vuelve a coger el primer resultado sin mirar si habla de lo buscado"
    assert "limite: 5" in componente, \
        "con un solo resultado no hay de donde elegir: hay que pedir unos cuantos"
    assert re.search(r"\.find\(\(r\) => r\.comparable && elQueHablaDe\(r, q\)\)", componente), \
        "hay que coger el primero comparable QUE HABLE de lo buscado, no el primero"
    # Y la regla, escrita: la palabra buscada tiene que estar en el nombre.
    assert re.search(r"llano\(r\.nombre\)\.includes\(palabra\)", componente), \
        "la comprobacion tiene que ser sobre el nombre, sin tildes ni mayusculas"
