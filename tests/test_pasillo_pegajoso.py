"""El pasillo de la lista, pegado arriba: la mitad de pantalla de la condicion (c).

El encargo lo pide asi: *"el pasillo como **separador pegajoso**"*, y el motivo esta
en como se usa esta pantalla -- de pie, en movimiento y con una mano. Lo que hay que
saber mientras se empuja el carro es **en que pasillo se esta**, no el indice de la
fila; con nueve lineas de seis pasillos, leer los nueve nombres para saber que queda
aqui es trabajo que se hace andando.

Lo que vigila esta prueba, y por que cada cosa:

  - **Que el encabezado sea pegajoso de verdad** (`sticky`), y que lo sea **debajo de
    la cabecera**, no debajo de ella: la cabecera de la aplicacion tambien es
    `sticky top-0`, asi que un pasillo pegado en `top: 0` se mete detras y se ve a
    medias. Por eso existe `--alto-cabecera`.
  - **Que esa altura se mida, no se escriba.** La cabecera no tiene una altura fija:
    envuelve en movil y el desplegable de "Estado de las cadenas" la hace mas alta.
    Un `top-14` escrito a mano acierta hoy y falla el dia que cambie una linea de
    texto, y eso no da ningun error: se ve mal y ya esta.
  - **Que un dato que no tenemos no se rellene.** Las lineas sin pasillo van las
    ultimas y **sin encabezado**: no se les pone "otros" ni el nombre del grupo.
  - **Que el orden de dentro de un pasillo no se toque.** `sort` es estable y el
    orden que importa (`en_carrito, anadido_en`) lo manda la API: si aqui se
    reordenara por otro criterio, habria dos ordenes peleandose en cada recarga.

Como las de contraste y las de movil, esto lee el codigo: es una decision de pantalla,
y volver a un encabezado que se va con el scroll no da ningun error de compilacion.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
SRC = RAIZ / "plataforma" / "web" / "app" / "src"
CESTA = SRC / "paginas" / "Cesta.tsx"
CABECERA = SRC / "componentes" / "Cabecera.tsx"
TIPOS = SRC / "tipos.ts"


def _leer(f: Path) -> str:
    if not f.exists():
        pytest.skip("esta copia no trae la interfaz nueva")
    return f.read_text(encoding="utf-8")


def test_el_pasillo_esta_pegado_debajo_de_la_cabecera_y_no_detras():
    cesta = _leer(CESTA)
    assert "sticky" in cesta and "top-[var(--alto-cabecera" in cesta, \
        "el encabezado de pasillo tiene que quedarse pegado bajo la cabecera"
    # Y con `z` por debajo de la cabecera (z-30 en Cabecera.tsx): por encima taparia
    # la fecha de los datos, que es lo que sostiene la regla de las fechas.
    assert re.search(r"sticky top-\[var\(--alto-cabecera.*?z-10", cesta), \
        "el pasillo no puede tapar la cabecera"


def test_la_altura_de_la_cabecera_se_mide_y_se_publica():
    cabecera = _leer(CABECERA)
    assert "--alto-cabecera" in cabecera, \
        "nadie publica la altura de la cabecera: el pasillo se pegaria en top: 0"
    assert "getBoundingClientRect" in cabecera, \
        "la altura tiene que medirse, no escribirse a mano"
    assert "ResizeObserver" in cabecera, \
        "y tiene que volver a medirse cuando la cabecera cambie de alto (movil, desplegable)"


def test_las_lineas_sin_pasillo_van_al_final_y_sin_encabezado():
    cesta = _leer(CESTA)
    assert "Number.MAX_SAFE_INTEGER" in cesta, \
        "una linea sin pasillo no puede colocarse al principio: va al final"
    assert re.search(r"\{pasillo && \(", cesta), \
        "una linea sin pasillo no lleva encabezado: no se le inventa un nombre"
    # El corte en tandas va por nombre de pasillo, para no pintar dos veces el mismo.
    assert re.search(r"ultima\[0\] === nombre", cesta)


def test_el_orden_de_dentro_de_un_pasillo_no_se_toca():
    cesta = _leer(CESTA)
    assert "[...lineas].sort(" in cesta, \
        "se ordena una copia: la lista que llega de la API no se muta"
    # El unico criterio de orden es la posicion en el recorrido de la tienda.
    assert "pasillo_orden" in cesta and "anadido_en" not in cesta.split("function porPasillo")[1].split("function UnaLinea")[0], \
        "dentro de un pasillo no se reordena por otra cosa: el orden lo manda la API"


def test_el_tipo_de_la_linea_lleva_el_pasillo_y_es_opcional():
    tipos = _leer(TIPOS)
    bloque = tipos.split("export interface Linea {")[1].split("}")[0]
    for campo in ("seccion?", "pasillo?", "pasillo_orden?"):
        assert campo in bloque, \
            f"falta `{campo}` en `Linea`: la pantalla no podria leer el pasillo"
