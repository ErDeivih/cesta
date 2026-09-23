"""«Deshacer» en la lista: la accion destructiva de esta pantalla, y cuando hace falta.

§3.4 del encargo: *"tachar sin querer pasa. Borrar una linea sin querer pasa. **Cada accion
destructiva deja un «deshacer» durante unos segundos**, y ninguna pide confirmacion:
confirmar cada toque es peor que deshacer el que sobra."*

Lo que se vigila aqui:

  - **Que exista**, y que no pregunte nada antes de quitar (nada de `confirm`).
  - **Y que salga tambien cuando la lista se queda VACIA**, que es lo que encontro el
    navegador el 23 de septiembre de 2026: el «Deshacer» vivia dentro del lado "si hay
    lineas" de un ternario, asi que al quitar **la ultima** linea la lista se vaciaba, ese
    lado no se pintaba... y el «Deshacer» desaparecia justo cuando mas falta hace. Ninguna
    prueba de codigo lo veia, porque el bloque estaba escrito y el texto estaba en el
    fichero: lo que fallaba era **donde** estaba.
  - **Que el id viaje.** Reanadir sin el id no deshace: crea otra linea y deja la compra
    duplicada, que es peor que no poder deshacer (`almacen.py:288` lo dice con el `ON
    CONFLICT (id) DO UPDATE ... borrado_en = NULL`).
"""
from __future__ import annotations

from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
CESTA = RAIZ / "plataforma" / "web" / "app" / "src" / "paginas" / "Cesta.tsx"


def _cesta() -> str:
    if not CESTA.exists():
        pytest.skip("esta copia no trae la interfaz nueva")
    return CESTA.read_text(encoding="utf-8")


def test_quitar_una_linea_deja_deshacer_y_no_pregunta_nada():
    cesta = _cesta()
    assert "Has quitado" in cesta and "Deshacer" in cesta, \
        "quitar una linea no deja forma de volver atras"
    assert "confirm(" not in cesta, \
        "una confirmacion por cada toque es peor que deshacer el que sobra"
    # El id es la llave: sin el, reanadir crea otra linea en vez de resucitar esta.
    assert "quitada.id" in cesta, \
        "el «Deshacer» tiene que reanadir con EL MISMO id, o duplica la compra"


def test_el_deshacer_no_se_esconde_cuando_la_lista_se_queda_vacia():
    """El caso que encontro el navegador: quitar la ultima linea.

    Se comprueba la forma del codigo a proposito: el fallo era **donde** estaba el bloque
    (dentro del lado "si hay lineas" de un ternario), no lo que decia. Un ternario sobre
    `lineas.length === 0` es exactamente lo que lo escondia.
    """
    cesta = _cesta()
    assert "lineas.length === 0 ?" not in cesta, (
        "la lista vuelve a estar partida por un ternario: lo que se pinte en el lado "
        "'si hay lineas' desaparece cuando quitas la ultima, y ahi esta el «Deshacer»")
    # El vacio se pinta como una pieza mas, y el deshacer es hermano suyo.
    assert "lineas.length === 0 &&" in cesta, \
        "el «la lista esta vacia» tiene que ser una pieza mas, no un lado del ternario"
    assert cesta.index("Has quitado") < cesta.index("por coger ·"), \
        "el «Deshacer» tiene que ir con la lista, no dentro de un lado que puede no pintarse"
