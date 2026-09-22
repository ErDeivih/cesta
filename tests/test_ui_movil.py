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
def test_la_barra_de_abajo_tiene_cuatro_destinos():
    """Cuatro, y son los cuatro de estar un rato en la tienda.

    Lo dice `docs/USABILIDAD.md`: una barra de ocho iconos no se lee, se busca a
    tientas. Si alguien anade un quinto destino, que sea decidiendolo.
    """
    fuente = NAV.read_text(encoding="utf-8")
    bloque = re.search(r"const ITEMS = \[(.*?)\] as const", fuente, re.S)
    assert bloque, "no he sabido leer los destinos de la barra: revisa esta prueba"
    destinos = re.findall(r"a:\s*'([^']+)'", bloque.group(1))
    assert destinos == ["/", "/cesta", "/escaner", "/panel"], (
        f"la barra de abajo tiene {destinos}. Son cuatro a proposito: buscar, la "
        f"cesta, el escaner y el panel. Anadir uno es una decision, no un detalle")
