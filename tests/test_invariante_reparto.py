"""La invariante del reparto: un grupo no puede tener dos productos de la misma cadena.

Es el cambio que mas ha limpiado el catalogo en esta sesion -- grupos de 11+ de 74 a
0, y la cadena repetida sin EAN de 1.385 a 0 -- y **no tenia prueba unitaria**: las
pruebas de `test_matching.py` pasaron sin tocarse, porque la guarda solo actua cuando
se le pasan las cadenas.

Asi que esto fija las tres cosas que pueden romperse sin que nadie se entere:

1. Que **rechace** la union que dejaria una cadena repetida.
2. Que **admita el duplicado legitimo**: dos fichas de la misma cadena con el **mismo
   EAN** son el mismo producto listado dos veces, y esos 38 casos del catalogo no son
   una infraccion.
3. Que **sin el parametro se comporte como antes**, que es lo que hace que las
   pruebas viejas sigan valiendo y que un llamante que no pase cadenas no se lleve
   una sorpresa.

Y el porque de la invariante, que es del encargo y conviene tenerlo aqui al lado: el
reparto de los enlaces es **1-a-1 por par de cadenas**, asi que un grupo correcto no
puede tener dos productos de la misma cadena. La union por componentes conexas era lo
que rompia esa promesa sin que ningun enlace individual estuviera mal.
"""
from __future__ import annotations

from core.matching import agrupar_enlaces

# Dos productos de DIA y uno de Aldi. El enlace mas fuerte es el de los dos de DIA,
# que es justo el que no se puede aceptar.
ENLACES = [
    (0, 1, 0.95, "equivalente"),
    (0, 2, 0.90, "equivalente"),
    (1, 2, 0.90, "equivalente"),
]
CADENAS = ["dia", "dia", "aldi"]


def test_rechaza_la_union_que_dejaria_una_cadena_repetida():
    grupos = agrupar_enlaces(ENLACES, 3, cadenas=CADENAS, eans=[None] * 3)
    assert grupos[0] != grupos[1], (
        "dos productos de la misma cadena han acabado en el mismo grupo: la "
        "invariante del reparto no esta actuando")
    # El de Aldi se queda con uno de los dos de DIA, no con los dos.
    assert grupos[0] == grupos[2] or grupos[1] == grupos[2]
    assert len({grupos[0], grupos[1], grupos[2]}) == 2


def test_admite_el_duplicado_legitimo_con_el_mismo_ean():
    """Dos fichas de DIA con el mismo codigo de barras son el mismo producto.

    Son 38 casos en todo el catalogo, y bloquearlos seria quitar de la comparacion
    un producto que si esta, listado dos veces.
    """
    grupos = agrupar_enlaces(ENLACES, 3, cadenas=CADENAS, eans=["EAN1", "EAN1", None])
    assert grupos[0] == grupos[1] == grupos[2], (
        "el duplicado legitimo (misma cadena y mismo EAN) se ha bloqueado")


def test_sin_el_parametro_se_comporta_como_antes():
    """Un llamante que no pase cadenas no puede llevarse una sorpresa."""
    grupos = agrupar_enlaces(ENLACES, 3)
    assert grupos[0] == grupos[1] == grupos[2]


def test_un_producto_sin_ean_no_se_da_por_el_mismo_que_otro():
    """Sin codigo no hay prueba: dos de la misma cadena y sin EAN no se juntan.

    Tratar el silencio como "podria ser el mismo" seria inventar la prueba que no
    tenemos, que es lo contrario de la regla del proyecto.
    """
    grupos = agrupar_enlaces(ENLACES, 3, cadenas=CADENAS, eans=[None, None, None])
    assert grupos[0] != grupos[1]
