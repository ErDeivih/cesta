"""Estar sin cobertura en un supermercado no es un fallo, y no se anuncia como tal.

Lo pide el encargo (punto 2, la lista): *"que no se note cuando no hay cobertura --
estar sin red en un supermercado no es un fallo que merezca un aviso rojo."* Y es la
condicion (c) de la barra.

Lo que habia antes era esto, en `paginas/Cesta.tsx`:

    {cambia.isError && (
      <Aviso tono="mal" titulo="No he podido guardar el cambio">
        ... Sin la cola de cambios de la interfaz antigua, aqui no se pinta un
        cambio que el servidor no ha aceptado.

Dos cosas distintas en el mismo saco, y las dos mal:

  - **Un fallo de red pintado en rojo**, con `role="alert"` (lo pone `Aviso` cuando el
    tono es `mal`). En el pasillo, sin cobertura, eso se lee como "la aplicacion se ha
    roto" y la lista se deja de usar justo donde mas sirve. No es un fallo de nadie: es
    lo normal, y lo unico que hace falta saber es que el cambio no se ha guardado y que
    hay que volver a pulsar.
  - **Una explicacion para quien programa**, dentro del aviso que lee quien esta en la
    caja: la cola de cambios de la interfaz antigua no le importa a nadie que este
    haciendo la compra.

Y un tercer agujero que salio al mirar esto: si lo que no llega es **la propia lista**
--abrir la aplicacion en el pasillo sin cobertura--, `detalle.isError` no se miraba en
ninguna parte. El estado de carga desaparecia, quedaba el encabezado y **la pantalla en
blanco**, sin decir nada. Eso si que parece una aplicacion rota.

Estas pruebas leen el codigo, como las de contraste y las de movil: lo que se vigila es
una decision de pantalla, y un cambio que devuelva el rojo no da ningun error de
compilacion.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
SRC = RAIZ / "plataforma" / "web" / "app" / "src"
CLIENTE = SRC / "api" / "cliente.ts"
CESTA = SRC / "paginas" / "Cesta.tsx"


def _leer(f: Path) -> str:
    if not f.exists():
        pytest.skip("esta copia no trae la interfaz nueva")
    return f.read_text(encoding="utf-8")


def test_sin_red_es_typeerror_y_esta_en_un_solo_sitio():
    """La regla que decide si algo es "sin cobertura" vive en `cliente.ts`.

    Si cada pantalla la comprobara por su cuenta, el texto y el color acabarian
    discrepando: un aviso que dice "sin conexion" pintado en rojo.
    """
    cliente = _leer(CLIENTE)
    assert re.search(r"export function esSinRed\(e: unknown\): boolean \{\s*return e instanceof TypeError", cliente), \
        "`esSinRed` tiene que ser el unico juez de 'no hay red'"
    # Y el mismo hecho ya se trataba asi al escribir el mensaje: una sola regla.
    assert "e instanceof TypeError" in cliente


def test_un_fallo_de_red_no_va_en_rojo_y_uno_de_la_api_si():
    cesta = _leer(CESTA)
    assert "esSinRed(cambia.error)" in cesta, \
        "al no poder guardar un cambio hay que distinguir la red de la API"
    assert "esSinRed(detalle.error)" in cesta, \
        "al no poder traer la lista, lo mismo"

    # El aviso de sin cobertura es neutro y no es una alerta.
    sin_cobertura = re.findall(
        r'<Aviso tono="(\w+)" titulo="Sin cobertura">', cesta)
    assert sin_cobertura == ["aviso", "aviso"], \
        f"los dos casos de sin cobertura van en tono neutro, no en {sin_cobertura}"
    assert 'tono="mal" titulo="No he podido guardar el cambio"' in cesta, \
        "cuando la API contesta que no, sigue siendo un fallo que hay que mirar"


def test_el_aviso_no_le_habla_al_de_la_caja_de_la_interfaz_antigua():
    """El aviso que se lee en la caja no explica decisiones de programacion."""
    cesta = _leer(CESTA)
    assert "interfaz antigua" not in cesta, \
        "el aviso vuelve a hablar de la interfaz antigua a quien esta comprando"


def test_si_no_llega_la_lista_se_dice_algo():
    """La pantalla en blanco es lo que mas se parece a una aplicacion rota."""
    cesta = _leer(CESTA)
    assert "detalle.isError" in cesta, \
        "si falla traer la lista no se pinta nada: ni aviso, ni reintento"
