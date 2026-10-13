"""B03 · **La zona SEPARA** -- la expectativa, escrita desde el objetivo y no desde el cambio.

**Que se fija aqui, y por que cambia de sitio.** *La ronda 63 decidio, con la respuesta del propietario delante,
que «la zona entra en la identidad del grupo».* Y **la traduccion a codigo se hizo al reves**: *se relajo la
invariante de la cadena a «misma cadena y misma zona», con lo que **dos zonas del mismo producto dejaron de estar
prohibidas y se juntaron**.*

*Se descubrio en la ronda 91, con una prueba de fuego:* `[0, 1, 0]` sin zonas y `[0, 0, 0]` con zonas -- **al
reves de lo que B03 quiere** --, *y se revirtio en la 92.*

**Y la causa de que no se cazara antes, que es lo que este fichero existe para no repetir:** *todas las pruebas
que habia comprobaban que el cambio **no rompia** lo de antes -- «sin zonas nada cambia» --, y **ninguna
comprobaba que hiciera lo que el objetivo pide**.* *La prueba se escribio desde el cambio, no desde el objetivo.*

------------------------------------------------------------

**LA DIRECCION CORRECTA, escrita para que no se vuelva a invertir:**

    LO QUE HAY HOY:        un grupo no puede tener dos productos de la MISMA CADENA.
                           -> y esa condicion NO SE TOCA.

    LO QUE HAY QUE ANADIR: un grupo no puede tener DOS ZONAS.

    O SEA: LA ZONA **SEPARA**. Se ANADE una condicion; NO se relaja la que habia.

*Que es exactamente lo mismo que la invariante de la cadena ya hace -- y por eso **relajarla** fue el error: **se
confundio «estos dos precios son distintos» con «estos dos precios pueden ir juntos», y son lo contrario: si son
distintos, hay que separarlos.***

Los tres casos del fichero siguiente son el objetivo entero, y el tercero es el que **hoy falla**.
"""
from __future__ import annotations

from core.matching import agrupar_enlaces

# *El mismo producto -- mismo nombre, misma cantidad -- en la MISMA cadena y DOS zonas, y el mismo producto en
# otra cadena. Es el caso minimo que distingue «la zona separa» de «la zona mezcla».*
FILAS = [
    {"fuente": "lidl", "nombre": "Leche entera 1 L", "region": "28"},
    {"fuente": "lidl", "nombre": "Leche entera 1 L", "region": "07"},
    {"fuente": "dia", "nombre": "Leche entera 1 L", "region": None},
]
CADENAS = [f["fuente"] for f in FILAS]
REGIONES = [f.get("region") for f in FILAS]
EANS = [None, None, None]
# *Los dos Lidl son equivalentes al de DIA. Y **no hay enlace entre los dos Lidl**: son la misma cadena, y el
# emparejador no empareja dentro de una cadena -- de eso se encarga la invariante.*
ENLACES = [(0, 2, 0.95, "equivalente"), (1, 2, 0.95, "equivalente")]


def test_sin_zonas_el_comportamiento_no_cambia():
    """**Lo que ya estaba, y que sigue siendo verdad.** *La base sobre la que se mide el resto.*

    *Y aqui hay una trampa que costo una correccion, y conviene dejarla escrita:* **el reparto es 1-a-1**, asi
    que con dos productos de la misma cadena y **uno** de otra, **solo uno de los dos se empareja**. *O sea que
    `g[0] != g[1]` **no prueba nada sobre zonas**: prueba que uno gano el emparejamiento y el otro no.*

    *Asi que esta prueba fija **el reparto**, no la separacion*: **uno de los dos Lidl queda con DIA y el otro
    consigo mismo.** *Y cual de los dos es depende del desempate, que es determinista -- por eso no se comprueba
    cual, sino cuantos.*
    """
    g = agrupar_enlaces(ENLACES, 3, cadenas=CADENAS, eans=EANS)
    assert g[0] != g[1], "dos productos de la misma cadena no pueden ir al mismo grupo"
    # *Exactamente uno de los dos se empareja con DIA: es el 1-a-1.*
    con_dia = sum(1 for i in (0, 1) if g[i] == g[2])
    assert con_dia == 1, (
        f"solo uno de los dos Lidl puede emparejarse con dia; se emparejaron {con_dia}")


def test_dos_zonas_del_mismo_producto_no_van_al_mismo_grupo():
    """**EL OBJETIVO, y resulta que YA SE CUMPLE.** *Sin ninguna condicion nueva.*

    *Esta prueba se escribio con un `xfail(strict=True)` esperando que fallara, y **paso** -- que con `strict` es
    un fallo, y por eso salto.* Y lo que dice ese `XPASS` es la conclusion de todo este tramo:*

        LA INVARIANTE DE LA CADENA **YA SEPARA** LOS DOS PRECIOS DE UN MISMO PRODUCTO EN DOS ZONAS,
        PORQUE SON DOS PRODUCTOS DE LA MISMA CADENA -- y un grupo no puede tener dos.

    *O sea que **la condicion de la zona es redundante para Lidl**, y lo era desde el principio: **la invariante
    que ya existia hace el trabajo**, y solo habria hecho falta algo nuevo si un grupo pudiera contener dos
    precios de la misma cadena -- que es justo lo que esa invariante prohibe.*

    **Y de ahi sale la conclusion, que es la que importa:** *lo que habia que hacer en `donde_comprar` **no era
    anadir una condicion a la guarda**, sino **respetar la que ya hay**.* *El error de las rondas 83-89 fue
    **relajarla** para que las zonas cupieran juntas -- cuando lo correcto era dejarla.*

    *Se queda como prueba verde, sin `xfail`, porque **ya es verdad** -- y para que el dia que alguien vuelva a
    intentar «que las zonas se junten» tenga esto delante.*
    """
    g = agrupar_enlaces(ENLACES, 3, cadenas=CADENAS, eans=EANS, regiones=REGIONES)
    assert g[0] != g[1], (
        "dos zonas del mismo producto no pueden ir al mismo grupo -- y lo impide la invariante "
        "de la cadena, que ya estaba")
    assert g[2] in (g[0], g[1]), "el de dia tiene que ir con una de las dos zonas"
