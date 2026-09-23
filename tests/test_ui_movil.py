"""Las reglas de movil del proyecto, comprobadas.

Estas reglas estan escritas en los documentos y en comentarios del codigo, y hasta
hoy **no las comprobaba nadie**: se cumplian porque quien escribio las pantallas se
acordo. Eso dura hasta la primera prisa.

Son cuatro, y las cuatro tienen un motivo concreto que ya costo caro en la interfaz
vieja:

1. **44 px para pulsar.** Se usa de pie, con una mano y el carro en la otra. Un
   boton de 24 px se falla, y fallar en la tienda es pulsar dos veces.
2. **16 px en los campos.** Por debajo, Safari hace zoom al enfocar el campo, la
   pagina se queda descolocada y hay que pellizcar para volver.
3. **La raya del iPhone.** Sin `safe-area-inset-bottom`, la barra de abajo se come
   el ultimo boton en los moviles que tienen raya.
4. **Cuatro destinos en la barra de abajo, y no cambian.** Es una decision escrita
   en `docs/USABILIDAD.md`: una barra de ocho iconos no se lee, se busca a tientas.

No comprueba el aspecto -- eso no se puede comprobar leyendo -- sino las reglas que
se pueden comprobar leyendo, que son justo las que no dan error al incumplirlas.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
APP = RAIZ / "plataforma" / "web" / "app"
UI = APP / "src" / "componentes" / "ui.tsx"
NAV = APP / "src" / "componentes" / "Nav.tsx"
PUERTA = RAIZ / "plataforma" / "prueba_navegador.py"

sin_interfaz = pytest.mark.skipif(
    not APP.exists(), reason="esta copia no trae la interfaz nueva")


@sin_interfaz
def test_el_boton_nunca_baja_de_44_px():
    """El minimo para pulsar con el pulgar sin fallar.

    Se mira `Boton`, que es el sitio por el que pasan todos: si el minimo vive en
    un solo sitio, no hay que revisar catorce pantallas cada vez que se toca una.
    """
    fuente = UI.read_text(encoding="utf-8")
    assert "min-h-[44px]" in fuente, (
        "el boton ha perdido los 44 px minimos: se usa de pie, con una mano y el "
        "carro en la otra, y un boton bajo se falla")
    # Y en las dos ramas: el compacto tambien tiene que llegar a 44.
    assert fuente.count("min-h-[44px]") >= 2, (
        "solo una de las dos variantes del boton conserva los 44 px")


def _etiqueta_completa(texto: str, inicio: int) -> str:
    """El texto de una etiqueta JSX, desde `<x` hasta su `>` de cierre.

    **No vale cortar en el primer `>`**, y esto se aprendio midiendo: el
    `<select>` de `FiltrosBusqueda.tsx` lleva `onChange={(e) => ...}`, o sea un `>`
    dentro de una llave, y cortando ahi el `className` -- que va despues -- se
    quedaba fuera del trozo mirado. La prueba pasaba sin haber mirado nada: el
    mismo fallo silencioso que persigue, cometido por la prueba.

    Se recorre contando llaves y comillas, y el `>` que cierra es el que esta fuera
    de las dos y no forma parte de un `=>`.
    """
    i, comillas, llaves = inicio, None, 0
    while i < len(texto):
        c = texto[i]
        if comillas:
            if c == comillas:
                comillas = None
        elif c in "\"'`":
            comillas = c
        elif c == "{":
            llaves += 1
        elif c == "}":
            llaves -= 1
        elif c == ">" and llaves == 0 and texto[i - 1] != "=":
            return texto[inicio:i + 1]
        i += 1
    return texto[inicio:]


@sin_interfaz
def test_ningun_campo_de_texto_baja_de_16_px():
    """16 px o Safari hace zoom al enfocar, que descuadra la pagina entera."""
    diminutos = []
    for fichero in sorted((APP / "src").rglob("*.tsx")):
        texto = fichero.read_text(encoding="utf-8")
        for etiqueta in ("<input", "<select", "<textarea"):
            for trozo in re.finditer(re.escape(etiqueta), texto):
                etiqueta_completa = _etiqueta_completa(texto, trozo.start())
                if re.search(r"text-(xs|sm|\[1[0-5]px\])", etiqueta_completa):
                    linea = texto[:trozo.start()].count("\n") + 1
                    diminutos.append(f"{fichero.name}:{linea}")
    assert not diminutos, (
        "hay campos con la letra por debajo de 16 px, y Safari hara zoom al "
        "enfocarlos:\n  " + "\n  ".join(diminutos) +
        "\nEl tamano se hereda del `html` a proposito: quita la clase del campo.")


@sin_interfaz
def test_la_barra_de_abajo_reserva_la_raya_del_iphone():
    """Sin esto, en un iPhone con raya el ultimo boton queda debajo."""
    fuente = NAV.read_text(encoding="utf-8")
    assert "env(safe-area-inset-bottom)" in fuente, (
        "la barra de abajo ya no reserva el hueco de la raya del iPhone: el "
        "ultimo boton se queda debajo y no se puede pulsar")


@sin_interfaz
def test_la_barra_de_abajo_tiene_cinco_destinos_y_el_quinto_es_una_decision():
    """Cuatro de estar un rato en la tienda, y **Avisos**, que es otra cosa.

    Lo dice `docs/USABILIDAD.md`: una barra de ocho iconos no se lee, se busca a
    tientas. El quinto entro el 23 de septiembre de 2026 **decidido y escrito**, no
    colado: Avisos no es un sitio donde estar, es **lo unico que la aplicacion hace por
    ti mientras no la miras**, y es la respuesta a *"¿ha bajado algo de lo mio?"*. El
    encargo de esa fecha pide literalmente *"un punto en el icono"*, y un punto necesita
    un icono donde estar -- dentro de otra pantalla seria esconderlo en una esquina.
    """
    fuente = NAV.read_text(encoding="utf-8")
    bloque = re.search(r"const ITEMS = \[(.*?)\] as const", fuente, re.S)
    assert bloque, "no he sabido leer los destinos de la barra: revisa esta prueba"
    destinos = re.findall(r"a:\s*'([^']+)'", bloque.group(1))
    assert destinos == ["/", "/cesta", "/escaner", "/avisos", "/panel"], (
        f"la barra de abajo tiene {destinos}. Son cinco a proposito: buscar, la cesta, "
        f"el escaner, los avisos y el panel. Anadir otro es una decision, no un detalle")
    # Y el porque tiene que estar donde se lee, que es con los destinos.
    assert "lo unico que" in fuente and "punto en el icono" in fuente, \
        "el quinto destino tiene que llevar su razon escrita al lado"


def test_los_objetivos_de_la_ficha_del_producto_tienen_44_px():
    """Los cuatro que se escaparon por no medir esa pantalla (23 sep 2026).

    La puerta medía todas las pantallas menos la ficha del producto, y ahí había **cuatro
    objetivos por debajo de 44 px** desde el primer día, medidos en un móvil de 390 x 844:

        el enlace al producto de al lado, en la tabla    161 x 19
        (y el mismo enlace con el nombre en dos líneas)  158 x 39
        el desplegable «Ingredientes»                    324 x 20

    El enlace es la forma de saltar a la ficha de otro producto del grupo, que es lo que se
    hace **con el paquete en la mano**, y el desplegable abre los ingredientes, que es donde
    se mira si algo lleva lo que no se puede comer. Ninguno de los dos se acierta de pie a
    19 px. La pantalla entró en la pasada de la puerta en el mismo cambio.
    """
    ficha = (APP / "src" / "paginas" / "Producto.tsx").read_text(encoding="utf-8")
    assert re.search(r"<summary[^>]*min-h-\[44px\]", ficha), \
        "el desplegable de ingredientes vuelve a tener su altura de texto (20 px)"
    assert re.search(r"<Link to=\{`/producto/\$\{p\.fuente\}.*?min-h-\[44px\]", ficha, re.S), \
        "el enlace al producto de al lado vuelve a medir 19 px"
    # Y la puerta tiene que medir esta pantalla, que es de donde salió el fallo.
    puerta = PUERTA.read_text(encoding="utf-8")
    assert '/producto/{con_historial[0]}/{con_historial[1]}' in puerta, \
        "la ficha del producto no está en la lista de pantallas que se miden"
    assert "/escaner" in puerta, "la pantalla del escáner tampoco"


def test_la_puerta_mide_que_ninguna_pantalla_se_deslice_de_lado():
    """Una página que se sale obliga a moverla con el pulgar para leer el final de las
    líneas, y en la tienda eso es soltar el carro.

    Las tablas anchas se deslizan **dentro de su caja** (`TablaScroll`), que es a propósito:
    lo que no puede deslizarse es la página. La puerta lo mide en cada pantalla que visita
    (`documentElement.scrollWidth` contra `clientWidth`) y el 23 de septiembre de 2026, con
    ocho pantallas, todas dan 390 de 390.
    """
    puerta = PUERTA.read_text(encoding="utf-8")
    assert "document.documentElement.scrollWidth" in puerta, \
        "la puerta no comprueba que la pagina quepa a lo ancho"
    assert "la pagina no se sale de la pantalla" in puerta, \
        "la comprobacion del ancho no dice lo que está midiendo"


def test_la_puerta_mide_que_las_cuatro_respuestas_quepan_en_la_primera_pantalla():
    """(a) no la puede cerrar una prueba, pero lo que no quepa queda descartado antes.

    La condicion (a) se juzga con el movil en la mano y **sin saber donde esta el boton**:
    una respuesta que obliga a desplazar la pantalla no se lee en quince segundos ni
    sabiendo donde esta. La puerta del navegador mide la **banda util** del movil
    (`_franja_util`: la cabecera y la barra de abajo se comen 109 y 57 px de los 844) y
    comprueba que las cuatro respuestas caben enteras dentro, con la pantalla arriba:

        1 y 3  la primera linea de la lista             y=557..573
        2      la frase del grupo al que se llega
               buscando                                  y=520..564
        4      "lo tuyo que ha bajado", con su tabla     y=437..557
        4      la seccion de los avisos                 y=186..210

    Medido asi el 23 de septiembre de 2026, con la banda util en 109..787. Esto **no**
    quiere decir que (a) este cumplida -- eso lo dice una persona --, pero si alguna de
    las cuatro se fuera por debajo de 787, seria imposible cumplirla y se sabria por que.
    """
    puerta = PUERTA.read_text(encoding="utf-8")
    assert "def _franja_util(" in puerta, \
        "la puerta no sabe cual es la banda util de la pantalla"
    assert "def _cabe_en_la_primera(" in puerta, \
        "la puerta no comprueba si una respuesta cabe en la primera pantalla"
    assert "--alto-cabecera" in puerta and "la banda util" in puerta, \
        "la banda util tiene que salir de la cabecera de verdad, no de un numero a ojo"
    for que in ("1 y 3: la primera linea de la lista se ve sin desplazar",
                "2: la frase que contesta «¿esto esta caro?» se ve sin desplazar",
                "4: lo tuyo que ha bajado se ve sin desplazar",
                "4: la seccion de los avisos se ve sin desplazar"):
        assert que in puerta, f"la puerta no comprueba «{que}»"
