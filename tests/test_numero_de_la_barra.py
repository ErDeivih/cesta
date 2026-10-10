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
NAV = APP / "componentes" / "Nav.tsx"
CONSULTAS = APP / "api" / "consultas.ts"
PUERTA = RAIZ / "plataforma" / "prueba_navegador.py"


def test_la_barra_dice_cuantas_quedan_por_coger():
    """El numero en el icono de la cesta, y solo cuando hay algo que decir."""
    nav = NAV.read_text(encoding="utf-8")
    assert "usePorCoger" in nav, "la barra no pide las que quedan por coger"
    # **Sin congelar la ruta.** Antes esto buscaba la cadena literal `a === '/cesta' && porCoger > 0`,
    # y cuando la ruta paso a ser `/compra/listas` la prueba **siguio en verde mientras la chapa ya no
    # se pintaba**: comprobaba que el codigo decia lo que decia, no que la aplicacion hiciera lo que
    # promete. Medido el 13 de octubre de 2026 -- treinta rondas despues, y lo encontro un navegador.
    # Ahora se comprueba lo que **no depende de una ruta**: que la chapa vive en el enlace de la lista
    # y que **con cero no se pinta**. El comportamiento lo mide `prueba_navegador`, que es donde se
    # puede medir.
    assert "porCoger > 0" in nav, (
        "la chapa se pintaria tambien con cero, y un cero en la barra es ruido")
    assert "/listas" in nav, "la chapa no esta en el enlace de la lista"
    assert "por coger" in nav, (
        "el numero tiene que ir tambien en palabras, para quien no ve el color")


def test_el_numero_sale_de_la_lista_correcta():
    """De la lista de casa, y por la misma puerta que la cesta (no una consulta nueva)."""
    consultas = CONSULTAS.read_text(encoding="utf-8")
    bloque = consultas[consultas.index("export function usePorCoger"):]
    bloque = bloque[:bloque.index("\n}\n") + 3]
    assert "es_de_casa" in bloque, (
        "el numero tiene que salir de la lista de casa, no de la primera que aparezca")
    assert "tachado_en === null" in bloque, (
        "lo que queda por coger son las lineas sin tachar, que es como las parte la cesta")
    # Las mismas claves de cache que la cesta: abrirla no puede pedir nada dos veces.
    for clave in ("['yo']", "['listas']", "['lista', listaId]"):
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
