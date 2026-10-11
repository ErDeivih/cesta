"""El numero de la barra: cuantas quedan por coger, desde cualquier pantalla.

Es la pregunta 3 del encargo -- *"¿voy tachando bien?"* -- contestada **sin abrir la lista**, y
lo tenia la interfaz vieja en el icono de la cesta (`app.js:507-509`, el `pin-lista`): era una
de las cosas que se pierden al servir `dist`. Medido en un navegador el 24 de septiembre de
2026, con una cuenta nueva: sin nada en la lista no hay chapa, con una linea dice 1, y con la
lista entera tachada desaparece.

Y una leccion de instrumento, la septima de esta sesion: la primera version de la comprobacion
leia el `innerText` **del enlace** y sacaba **22** donde ponia 2 -- `innerText` pega el numero
de la chapa con la etiqueta, «Cesta22 por coger». El numero estaba bien y el que mentia era el
que miraba. Ahora se lee la chapa (el `span` con `aria-hidden` y solo digitos), y el texto para
quien no ve el color sigue en el `sr-only`.
"""
from __future__ import annotations

import pathlib

RAIZ = pathlib.Path(__file__).resolve().parents[1]
APP = RAIZ / "plataforma" / "web" / "app" / "src"
# **El componente que se sirve, no el que se leia antes.** Medido el 11 de octubre de 2026: todas
# las rutas montan `LayoutSuite` (`App.tsx`) y su menu es `Suite.tsx` -- el mismo `Menu` para el
# lateral de escritorio y el cajon del movil --; `Nav.tsx` **solo lo importa `Cabecera.tsx`, y a
# `Cabecera` no lo importa nadie**. Es decir: la prueba comprobaba el texto de un componente muerto
# y por eso estuvo verde un mes con la chapa sin pintarse. Se comprueba el fichero servido.
SUITE = APP / "componentes" / "Suite.tsx"
CONSULTAS = APP / "api" / "consultas.ts"
PUERTA = RAIZ / "plataforma" / "prueba_navegador.py"


def test_la_barra_dice_cuantas_quedan_por_coger():
    """El numero en el icono de la cesta, y solo cuando hay algo que decir."""
    suite = SUITE.read_text(encoding="utf-8")
    assert "usePorCogerDeCasa" in suite, "el menu no pide las que quedan por coger en la casa"
    # **Sin congelar la ruta.** Antes esto buscaba la cadena literal `a === '/cesta' && porCoger > 0`,
    # y cuando la ruta paso a ser `/compra/listas` la prueba **siguio en verde mientras la chapa ya no
    # se pintaba**: comprobaba que el codigo decia lo que decia, no que la aplicacion hiciera lo que
    # promete. Medido el 13 de octubre de 2026 -- treinta rondas despues, y lo encontro un navegador.
    # Ahora se comprueba lo que **no depende de una ruta**: que la chapa vive en el enlace de la lista
    # y que **con cero no se pinta**. El comportamiento lo mide `prueba_navegador`, que es donde se
    # puede medir.
    assert "estado.pendientes > 0" in suite, (
        "la chapa se pintaria tambien con cero, y un cero en la barra es ruido")
    assert "'/compra/listas'" in suite, "la chapa no esta en el enlace de la lista"
    assert "por coger en la lista de casa" in suite, (
        "el numero tiene que ir tambien en palabras, y decir DE QUE LISTA es: un numero sin "
        "decir de donde sale no se puede comprobar")
    # **Las tres situaciones que no son un cero.** Antes el contador devolvia `0` mientras cargaba,
    # si fallaba la peticion y si de verdad no habia nada: tres cosas con la misma cara.
    for caso in ("'cargando'", "'error'", "'sin-lista'"):
        assert caso in suite or caso in CONSULTAS.read_text(encoding="utf-8"), (
            f"el contador no distingue {caso} de un cero real")
    assert "Sin lista de casa" in suite, (
        "sin lista de casa hay que decirlo, no contar otra lista en silencio")


def test_el_numero_sale_de_la_lista_correcta():
    """De la lista de casa, y por la misma puerta que la cesta (no una consulta nueva)."""
    consultas = CONSULTAS.read_text(encoding="utf-8")
    bloque = consultas[consultas.index("export function usePorCogerDeCasa"):]
    bloque = bloque[:bloque.index("\n}\n") + 3]
    assert "es_de_casa" in bloque, (
        "el numero tiene que salir de la lista de casa, no de la primera que aparezca")
    # **Y sin elegir otra en silencio.** El `?? listas[0]` contaba una lista que no era la de casa
    # sin decirlo: si no hay lista de casa, esto devuelve `sin-lista` y la pantalla lo dice.
    # **Se mira la linea que elige la lista, no el bloque entero**: el comentario de al lado
    # explica el antipatron que evita y nombrarlo ahi no es cometerlo.
    linea = next(x for x in bloque.splitlines() if x.strip().startswith("const casa ="))
    assert "es_de_casa" in linea, "el contador no mira la lista de casa"
    assert "listas[0]" not in linea and "listas.data?.[0]" not in linea, (
        "no se elige otra lista cuando no hay lista de casa: se dice que no hay")
    assert "?? null" in linea, (
        "sin lista de casa el estado tiene que ser `sin-lista`, no otra lista")
    assert "tachado_en === null" in bloque, (
        "lo que queda por coger son las lineas sin tachar, que es como las parte la cesta")
    # Las mismas claves de cache que la cesta: abrirla no puede pedir nada dos veces.
    for clave in ("['yo']", "['listas']", "['lista', casa?.id]"):
        assert clave in bloque, f"la consulta no comparte la clave {clave} con la cesta"


def test_la_puerta_lee_la_chapa_y_no_el_texto_del_enlace():
    """`innerText` del enlace pega el numero con la etiqueta: 2 se lee como 22."""
    puerta = PUERTA.read_text(encoding="utf-8")
    assert "la barra dice las que quedan por coger" in puerta, (
        "la puerta no comprueba el numero de la barra")
    assert 'span[aria-hidden="true"]' in puerta and "/^\\\\d+$/" in puerta, (
        "la comprobacion tiene que leer la chapa, no el texto entero del enlace")
    assert "Cesta22 por coger" in puerta, (
        "el caso que lo destapo tiene que estar contado donde se lee")
