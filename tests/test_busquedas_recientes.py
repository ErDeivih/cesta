"""Las ultimas busquedas: no volver a escribir lo mismo cada semana.

Lo pide el encargo (§8, «los detalles que hacen que parezca terminada»): *"que recuerde
las ultimas busquedas y que no exija pulsar una lupa"*. Y en esta aplicacion no es un
adorno: la compra se repite cada semana, y "leche entera" es la misma busqueda que la de
la semana pasada. Escribirla otra vez, de pie en el pasillo y con una mano, es justo el
trabajo que hay que quitar.

Lo que se vigila aqui, y cada cosa por su motivo:

  - **Que no se apunte a medias.** El texto que se busca va con 250 ms de retraso, asi
    que guardar en cuanto cambia la consulta llena la lista de "l", "le", "lec". Se
    apunta **con un segundo de calma** y solo si hay resultados: una busqueda que no
    encuentra nada no se recuerda, porque volver a pulsarla no ayuda a nadie.
  - **Que no se repita.** "Leche" cinco semanas seguidas no puede ocupar la lista cinco
    veces: se compara sin distinguir mayusculas y espacios sobrantes.
  - **Que no se rompa la pantalla si el aparato no deja escribir.** En modo privado el
    navegador deja leer y lanza al escribir; sin try/catch, un adorno tumba el buscador.
  - **Que sea de un toque.** Los chips llaman a lo mismo que los ejemplos: escribir la
    busqueda y lanzarla, sin pasar por el campo de texto.

Como las de contraste y las de movil, esto lee el codigo: son decisiones de pantalla.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
SRC = RAIZ / "plataforma" / "web" / "app" / "src"
MODULO = SRC / "estado" / "busquedasRecientes.ts"
BUSCAR = SRC / "paginas" / "Buscar.tsx"


def _leer(f: Path) -> str:
    if not f.exists():
        pytest.skip("esta copia no trae la interfaz nueva")
    return f.read_text(encoding="utf-8")


def test_se_guardan_en_el_aparato_y_con_su_version():
    """`localStorage` y no el servidor: son de este movil, y no viajan."""
    modulo = _leer(MODULO)
    assert "window.localStorage" in modulo
    assert re.search(r"const CLAVE = 'cesta\.busquedas\.v1'", modulo), \
        "la clave lleva version: el dia que cambie el formato, lo viejo no revienta"
    # Y sin permiso para escribir, la pantalla sigue funcionando.
    assert modulo.count("try {") >= 2 and "catch" in modulo


def test_no_se_apunta_a_medias_ni_lo_que_no_encuentra_nada():
    buscar = _leer(BUSCAR)
    assert "apuntaBusqueda" in buscar, "no se apunta ninguna busqueda"
    assert re.search(r"setTimeout\(\(\) => setRecientes\(apuntaBusqueda\(q\)\), 1000\)", buscar), \
        "se apunta sin dar tiempo a terminar de escribir: la lista se llena de 'l', 'le', 'lec'"
    assert "resultados.data" in buscar.split("apuntaBusqueda(q)")[0][-400:], \
        "solo se recuerda una busqueda que encontro algo"


def test_dos_veces_lo_mismo_no_ocupa_dos_sitios():
    modulo = _leer(MODULO)
    assert "toLowerCase()" in modulo, \
        "deduplicar distinguiendo mayusculas deja 'Leche' y 'leche' como dos chips"
    assert re.search(r"export const CUANTAS = (\d+)", modulo), "hay que acotar cuantas se guardan"
    assert "slice(0, CUANTAS)" in modulo


def test_los_chips_son_de_un_toque_y_solo_con_el_buscador_vacio():
    buscar = _leer(BUSCAR)
    assert "recientes.map(" in buscar, "las busquedas guardadas no se pintan"
    # Un chip hace la misma busqueda que el ejemplo pulsado: escribirla y lanzarla.
    assert re.search(r"recientes\.map\(\(q\) => \(\s*<Boton[^>]*onClick=\{\(\) => buscaEjemplo\(q\)\}",
                     buscar, re.S), \
        "el chip de una busqueda vieja tiene que lanzarla, no solo rellenar el campo"
    # Y solo en el estado vacio: con resultados en pantalla, esto es ruido.
    assert buscar.index("{!busca && (") < buscar.index("recientes.map(")
