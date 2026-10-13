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


def test_sin_el_parametro_de_zonas_nada_cambia():
    """**Y quien no pase zonas tampoco.** *La tercera vez que este fichero hace la misma comprobacion.*

    *Es la prueba que la ronda 77 dijo que habia que escribir «primero», y resulta que **ya estaba escrita dos
    veces** -- una por `cadenas` y otra por `nombres`. Esta es la del tercer parametro.*

    **Y es la que importa de verdad**, porque `regiones` cambia la CLAVE de la invariante por dentro: *sin zonas,
    la clave pasa a ser `(cadena, None)` en vez de `cadena`.* **Otro tipo, y tiene que dar el mismo resultado.**

    *Si esta prueba fallara, querría decir que el cambio de B03 rompio el reparto de las cinco fuentes que no
    declaran zona -- o sea, **todo el catalogo menos Lidl**.*
    """
    de_antes = agrupar_enlaces(ENLACES, 3, cadenas=CADENAS, eans=[None] * 3)
    con_el_parametro = agrupar_enlaces(ENLACES, 3, cadenas=CADENAS, eans=[None] * 3,
                                       regiones=None)
    assert de_antes == con_el_parametro, (
        "pasar `regiones=None` tiene que dar exactamente lo mismo que no pasarlo")
    # *Y con zonas vacias en todas las filas, tampoco: es el caso de una fuente que publica la columna pero no
    # la rellena.*
    con_vacias = agrupar_enlaces(ENLACES, 3, cadenas=CADENAS, eans=[None] * 3,
                                 regiones=[None, None, None])
    assert de_antes == con_vacias, (
        "una columna de zona vacia tiene que comportarse como no tenerla")


def test_un_producto_sin_ean_no_se_da_por_el_mismo_que_otro():
    """Sin codigo no hay prueba: dos de la misma cadena y sin EAN no se juntan.

    Tratar el silencio como "podria ser el mismo" seria inventar la prueba que no
    tenemos, que es lo contrario de la regla del proyecto.
    """
    grupos = agrupar_enlaces(ENLACES, 3, cadenas=CADENAS, eans=[None, None, None])
    assert grupos[0] != grupos[1]


# ------------------------------------------- la segunda red: el eje declarado ---
#
# La invariante de arriba caza lo que se funde **entre** cadenas. Queda lo que se
# funde **dentro** de un grupo que, mirado por cadenas, es legitimo: tres cadenas,
# tres productos, y dos de ellos no son el mismo producto. Eso no lo dice el
# precio -- y el precio no puede decirlo, porque hay ahorros reales de 28x entre
# marca blanca y marca --: lo dice **el nombre**.
#
# Medido el 23 de septiembre de 2026, con la invariante ya puesta: 49 grupos con
# eje contradictorio, todos de 2 o 3 productos. La barra del encargo pide cero.

# Tres cadenas distintas (o sea que la invariante del reparto no tiene nada que
# decir) y dos de los tres nombres se contradicen: virgen contra virgen extra.
ACEITES = ["Aceite de oliva virgen 1 l", "Aceite de oliva virgen extra 1 l",
           "Aceite de oliva suave 1 l"]
TRES_CADENAS = ["aldi", "dia", "mercadona"]
ENLACES_ACEITE = [(0, 1, 0.95, "equivalente"), (0, 2, 0.90, "equivalente"),
                  (1, 2, 0.90, "equivalente")]


def test_dos_nombres_que_se_contradicen_no_van_al_mismo_grupo():
    sin_nombres = agrupar_enlaces(ENLACES_ACEITE, 3, cadenas=TRES_CADENAS)
    assert len(set(sin_nombres)) == 1, (
        "sin nombres los tres se juntan: es el estado del que se parte, y por eso "
        "la segunda red hace falta")

    con_nombres = agrupar_enlaces(ENLACES_ACEITE, 3, cadenas=TRES_CADENAS,
                                  nombres=ACEITES)
    assert con_nombres[0] != con_nombres[1], (
        "`virgen` y `virgen extra` han acabado en el mismo grupo: el nombre lo "
        "declara y el eje tiene que cortar")


def test_el_que_calla_no_bloquea():
    """Ausencia de prueba no es tolerancia.

    Un producto que no dice de que aceite es no esta afirmando que sea igual: es
    que no lo sabemos. Bloquear por silencio quitaria comparaciones legitimas, que
    es el error caro en esta aplicacion.
    """
    grupos = agrupar_enlaces(
        [(0, 1, 0.95, "equivalente")], 2, cadenas=["aldi", "dia"],
        nombres=["Aceite de oliva virgen 1 l", "Aceite de oliva 1 l"])
    assert grupos[0] == grupos[1], "el silencio ha bloqueado una union legitima"


def test_una_entera_y_una_semidesnatada_sin_lactosa_no_son_el_mismo_producto():
    """El eje que corta puede no ser el que uno mira primero.

    `semidesnatada sin lactosa` y `entera` no se parecen solo por un adjetivo: son
    dos productos distintos en el eje de la grasa, y el nombre lo dice. Con los
    nombres a ojo, "sin lactosa" tapa lo que de verdad separa a los dos.
    """
    grupos = agrupar_enlaces(
        [(0, 1, 0.95, "equivalente")], 2, cadenas=["aldi", "dia"],
        nombres=["Leche entera 1 l", "Leche semidesnatada sin lactosa 1 l"])
    assert grupos[0] != grupos[1]


def test_sin_el_parametro_de_nombres_nada_cambia():
    """Un llamante que no pase nombres no puede llevarse una sorpresa."""
    assert agrupar_enlaces(ENLACES_ACEITE, 3, cadenas=TRES_CADENAS) == \
        agrupar_enlaces(ENLACES_ACEITE, 3, cadenas=TRES_CADENAS, nombres=None)
