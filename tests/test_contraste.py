"""El contraste, calculado. No es una opinion sobre si se lee: son numeros.

Estas pruebas existen porque los dos fallos que arreglan **no daban ningun error**:
la aplicacion funcionaba igual de bien con la letra a 4,35:1 y el boton a 4,10:1.
Un fallo que no se ve en una prueba normal y que no se ve en pantalla hasta que
alguien mayor lo intenta leer en la calle.

La formula es la de WCAG 2.1 (luminancia relativa), y el minimo para texto normal
es 4,5:1. Se calcula aqui en vez de copiar el numero del informe del diseno: un
numero copiado se queda viejo el dia que alguien cambia un color del tema.
"""
from __future__ import annotations

from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
APP = RAIZ / "plataforma" / "web" / "app"
SRC = APP / "src"
CSS = SRC / "estilos.css"

sin_interfaz = pytest.mark.skipif(
    not APP.exists(), reason="esta copia no trae la interfaz nueva")

MINIMO_TEXTO = 4.5


def _luminancia(color: str) -> float:
    canales = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    lineal = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
              for c in canales]
    return 0.2126 * lineal[0] + 0.7152 * lineal[1] + 0.0722 * lineal[2]


def contraste(uno: str, otro: str) -> float:
    """La razon de contraste WCAG entre dos colores `#rrggbb`."""
    a, b = _luminancia(uno), _luminancia(otro)
    return round((max(a, b) + 0.05) / (min(a, b) + 0.05), 2)


def _valor_del_token(nombre: str, tema: str = ":root") -> str:
    """El valor de una variable del tema, leido de `estilos.css`.

    Se lee del fichero y no se escribe aqui a proposito: si manana alguien cambia
    el token, la prueba mide el token nuevo.
    """
    texto = CSS.read_text(encoding="utf-8")
    if tema == "oscuro":
        texto = texto.split("prefers-color-scheme: dark", 1)[1]
    import re
    m = re.search(rf"{nombre}:\s*(#[0-9a-fA-F]{{6}})", texto)
    assert m, f"no he sabido leer `{nombre}` de estilos.css"
    return m.group(1)


@sin_interfaz
def test_la_letra_pequena_sobre_el_fondo_de_pagina_se_lee():
    """El fallo que tenia 29 sitios a 4,35:1, con el minimo en 4,5.

    La letra pequeña de esta aplicacion no es decoracion: son las fechas de los
    precios, la procedencia de los sellos y los "no lo se". Es justo el texto que
    hace creible lo demas, y era el peor de leer.
    """
    tinta = _valor_del_token("--tinta-suave")
    fondo = _valor_del_token("--fondo")
    r = contraste(tinta, fondo)
    assert r >= MINIMO_TEXTO, (
        f"la letra secundaria da {r}:1 sobre el fondo y el minimo es {MINIMO_TEXTO}")

    tinta_oscura = _valor_del_token("--tinta-suave", "oscuro")
    oscuro = _valor_del_token("--fondo", "oscuro")
    r_oscuro = contraste(tinta_oscura, oscuro)
    assert r_oscuro >= MINIMO_TEXTO, (
        f"la letra secundaria da {r_oscuro}:1 en el tema oscuro y el minimo es "
        f"{MINIMO_TEXTO}")


@sin_interfaz
def test_el_boton_principal_llega_al_minimo_en_los_dos_temas():
    """Blanco sobre `sky-600` en oscuro se quedaba en 4,10:1.

    Se mira el color del boton en el codigo (`ui.tsx`) y el blanco del texto, que
    es el que pone el propio boton.
    """
    fuente = (SRC / "componentes" / "ui.tsx").read_text(encoding="utf-8")
    import re
    oscuro = re.search(r"dark:bg-sky-(\d+)", fuente)
    assert oscuro, "el boton principal ya no declara un fondo para el tema oscuro"
    ESCALA = {"500": "#0ea5e9", "600": "#0284c7", "700": "#0369a1", "800": "#075985"}
    elegido = ESCALA[oscuro.group(1)]
    r = contraste("#ffffff", elegido)
    assert r >= MINIMO_TEXTO, (
        f"el boton principal en oscuro usa sky-{oscuro.group(1)} ({elegido}) y el "
        f"texto blanco da {r}:1, por debajo de {MINIMO_TEXTO}")

    # Y el hover, que es donde estaba el peor caso (2,77:1) y que el informe del
    # diseno no llego a medir.
    hover = re.search(r"dark:hover:bg-sky-(\d+)", fuente)
    if hover:
        r_hover = contraste("#ffffff", ESCALA[hover.group(1)])
        assert r_hover >= MINIMO_TEXTO, (
            f"el hover del boton principal da {r_hover}:1 en el tema oscuro")


@sin_interfaz
def test_la_formula_da_los_numeros_conocidos():
    """La comprobacion de la propia herramienta, para que no mida de mas.

    `#767676` sobre blanco es el ejemplo clasico: da exactamente 4,54, el primer
    gris que pasa el minimo de WCAG. Y blanco sobre negro da 21.
    """
    assert contraste("#767676", "#ffffff") == pytest.approx(4.54, abs=0.02)
    assert contraste("#ffffff", "#000000") == pytest.approx(21.0, abs=0.1)
    assert contraste("#737373", "#f5f5f5") == pytest.approx(4.35, abs=0.02)


@sin_interfaz
def test_el_limite_de_un_campo_se_ve():
    """El borde de un campo estaba a 1,48:1, y el minimo de WCAG 1.4.11 es 3.

    Sin limite visible, un campo de texto parece un trozo de la pagina: no se sabe
    donde se puede escribir.
    """
    fuente = (SRC / "componentes" / "ui.tsx").read_text(encoding="utf-8")
    import re
    # Se busca por la **firma del campo** (`px-3 py-2` con su borde claro y su borde
    # oscuro en la misma cadena de clase), no por el nombre del componente ni por un
    # patron suelto. Las tres versiones anteriores de esta prueba fallaron por
    # adivinar: la primera cogia el borde de una tarjeta y medía `neutral-200`, y la
    # segunda no encontraba los componentes. La firma no se puede confundir.
    ESCALA = {"300": "#d4d4d4", "400": "#a3a3a3", "500": "#737373",
              "600": "#525252", "700": "#404040"}
    campos = re.findall(
        r"border-neutral-(\d+) bg-white px-3 py-2 dark:border-neutral-(\d+)", fuente)
    assert campos, (
        "no he sabido leer la firma de un campo en `ui.tsx`: si has cambiado esas "
        "clases, cambia tambien esta prueba a proposito")

    for claro, oscuro in campos:
        r = contraste(ESCALA[claro], "#ffffff")
        assert r >= 3.0, (
            f"el borde de un campo da {r}:1 sobre blanco (neutral-{claro}) y el "
            f"minimo para un limite de control es 3")
        r_oscuro = contraste(ESCALA[oscuro], "#262626")
        assert r_oscuro >= 3.0, (
            f"el borde de un campo da {r_oscuro}:1 en el tema oscuro "
            f"(neutral-{oscuro}) y el minimo es 3")


@sin_interfaz
def test_el_marcador_de_un_campo_se_lee():
    """En el buscador es **la unica etiqueta visible**: el `<label>` es `sr-only`.

    El que trae Tailwind de serie da 2,54:1, asi que el campo no dice que se
    escribe en el. Se le pone el gris de la letra secundaria, y con `opacity: 1`
    porque Firefox aplica la suya propia al marcador.
    """
    css = CSS.read_text(encoding="utf-8")
    assert "::placeholder" in css, (
        "no hay regla para el marcador: vuelve el gris de Tailwind, que da 2,54:1")
    bloque = css.split("::placeholder", 1)[1].split("}", 1)[0]
    assert "var(--tinta-suave)" in bloque, (
        "el marcador ya no usa el gris de la letra secundaria")
    assert "opacity" in bloque, (
        "sin `opacity: 1`, Firefox aclara el marcador con su propia opacidad")

    r = contraste(_valor_del_token("--tinta-suave"), "#ffffff")
    assert r >= MINIMO_TEXTO, f"el marcador daria {r}:1 sobre blanco"
