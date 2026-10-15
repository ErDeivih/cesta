"""El mosaico de lo de siempre: la cuadricula que anade de un toque.

Es la mejora de mas valor que le quedaba al buscador (`docs/PANTALLAS.md:50-62` y
`docs/DISENO.md`, mejora 33): anadir algo que compras siempre pasa de **escribir, elegir
y anadir** a **un toque**. La API ya estaba desde el 23 de septiembre de 2026 -- con
`origen` en cada tarjeta y rellenando por escalones --; lo que faltaba era la pantalla.

Lo que se vigila aqui, y cada cosa porque se puede romper sin que nada avise:

  - **Que este puesta.** Es el fallo que ya paso una vez en esta sesion: el componente
    escrito, compilando, y sin pintarlo ninguna pantalla. Ni `tsc` ni el `build` dicen
    nada de un componente que nadie llama.
  - **Que sin historial salga la tarjeta de la primera vez**, no una cuadricula de 24
    productos basicos. Primero se entiende para que sirve la aplicacion, despues se usa.
  - **Que un 404 no sea un error rojo.** Mientras la imagen de la API que corre no tenga
    la ruta, esto contesta 404; quien acaba de abrir la aplicacion no tiene la culpa.
  - **Que el `origen` se diga cuando la cuadricula mezcla escalones**, y no cuando todas
    las tarjetas son del mismo: una tarjeta basica y una tuya no valen lo mismo, y doce
    etiquetas iguales en una cuadricula que no mezcla son ruido.
  - **Que sea un toque de verdad**: sin dialogo, sin selector de lista y sin preguntar la
    cantidad. Y que el boton diga si ya esta dentro, que es el error facil de verdad
    (pulsarlo tres veces).

Como las de contraste y las de movil, esto lee el codigo: son decisiones de pantalla, y
volver a un dialogo o a un rojo por un 404 no da ningun error de compilacion.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
SRC = RAIZ / "plataforma" / "web" / "app" / "src"
MOSAICO = SRC / "componentes" / "Mosaico.tsx"
BUSCAR = SRC / "paginas" / "Buscar.tsx"
CONSULTAS = SRC / "api" / "consultas.ts"


def _leer(f: Path) -> str:
    if not f.exists():
        pytest.skip("esta copia no trae la interfaz nueva")
    return f.read_text(encoding="utf-8")


def test_el_mosaico_esta_puesto_en_la_pantalla_de_entrada():
    buscar = _leer(BUSCAR)
    assert re.search(r"import\s*\{[^}]*\bMosaico\b[^}]*\}\s*from", buscar), \
        "la pantalla de entrada no importa el mosaico"
    assert "<Mosaico />" in buscar, \
        "la pantalla de entrada importa el mosaico pero no lo pinta: es el fallo que ya " \
        "paso con la tarjeta de la primera vez"


def test_sin_historial_sale_la_tarjeta_de_la_primera_vez():
    """Una cuadricula de 24 productos basicos no explica para que sirve esto."""
    mosaico = _leer(MOSAICO)
    assert "soloBasico" in mosaico and "<LoQueSeCompra />" in mosaico, \
        "sin historial (o con solo basicos) el mosaico tiene que caer en la tarjeta " \
        "de la primera vez, no pintar 24 recuadros"


def test_un_404_no_es_una_pantalla_roja():
    """El endpoint puede no estar desplegado, y eso no es culpa de quien abre la app."""
    mosaico = _leer(MOSAICO)
    assert "tarjetas.length === 0" in mosaico, \
        "sin tarjetas hay que caer al mismo sitio que sin historial"
    assert "habituales.isError" not in mosaico, \
        "un error del endpoint no puede pintarse: todavia puede no estar desplegado"


def test_la_cuadricula_anade_de_un_toque_y_sin_dialogo():
    mosaico = _leer(MOSAICO)
    assert "anade.mutate(" in mosaico, "el boton de cada tarjeta anade al pulsar"
    # Un toque es un toque: nada de preguntar la cantidad ni a que lista.
    for prohibido in ("cantidad:", "Selector", "prompt(", "confirm("):
        assert prohibido not in mosaico, \
            f"el mosaico no puede preguntar nada antes de anadir ({prohibido})"
    assert "En la cesta" in mosaico, \
        "el boton tiene que decir si ya esta dentro: pulsarlo tres veces es el error " \
        "facil de verdad"
    # Y 44 px de alto, que es el minimo que se pulsa andando.
    assert "min-h-[44px]" in mosaico


def test_el_origen_se_dice_solo_cuando_la_cuadricula_mezcla():
    mosaico = _leer(MOSAICO)
    assert "mezcla" in mosaico and "h.origen" in mosaico, \
        "sin decir el origen, la cuadricula ensena 'lo que sueles comprar' con lo que " \
        "compra otro"
    assert re.search(r"mezcla\s*&&", mosaico), \
        "doce etiquetas iguales en una cuadricula que no mezcla son ruido"


def test_sin_foto_no_se_inventa_una():
    """*** Y el relleno es el TOKEN, *no un gris de fabrica. *** *

    *Hasta el 15/10/2026 esto buscaba `bg-neutral-100` *-- *el gris de Tailwind --, *y
    ese gris paso a **`bg-marfil`**, *que es el mismo papel del resto de la app.* *

    *Y **lo que esta prueba tiene que defender no es el NOMBRE del color**: *es que
    **hay un hueco** y que **no hay una imagen inventada.** *Asi que se comprueba en
    **dos aserciones**, *para que el fallo diga **cual de las dos** se rompio* *-- *que
    es lo que hacia ilegible la version de una sola linea.* *
    """
    mosaico = _leer(MOSAICO)
    assert "h.imagen ?" in mosaico, (
        "sin foto hay que dejar el hueco, no una imagen de relleno")
    assert "bg-marfil" in mosaico, (
        "el hueco de una ficha sin foto necesita su relleno (`bg-marfil`, que es el "
        "papel del tema): sin el, una ficha sin imagen queda sin fondo y no se lee "
        "como un hueco, sino como un fallo de carga")


def test_la_consulta_pide_lo_habitual_con_su_limite():
    consultas = _leer(CONSULTAS)
    assert "'/habituales'" in consultas, "la consulta no pide `/api/habituales`"
    assert "useAnadeALaCesta" in consultas, \
        "anadir a la lista tiene que estar en un solo sitio: la lista de casa, y " \
        "creandola si no hay ninguna"
