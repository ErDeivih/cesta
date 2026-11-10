"""Repetir la compra de la semana anterior: los tres estados de cada linea.

David lo pidio asi (sesion 6): *«que se pueda repetir la compra de la semana
anterior en un clic»*. Lo que hace falta para eso no es una copia de la compra:
es **decidir, linea a linea, que pasaria al repetirla**, antes de escribir nada.
De ahi los tres estados, que son tres cosas distintas y no un booleano:

    falta          la lista no la tiene: se puede anadir
    ya_estaba      la lista ya la tiene: repetir no puede duplicarla
    sin_catalogo   la compra no guarda producto ni grupo detras: no hay nada
                   que volver a comprar «tal cual»

**La vista previa y la accion comparten este modulo**, que es lo que impide el
fallo clasico de esta casa: una previa que dice una cosa y un boton que hace
otra. `main._repetir_la_compra` (para el GET) y el POST usan el mismo
`estado_de`.

**La identidad se compara como en el resto del proyecto**, y el orden importa:

  1. `producto_id`, que es el articulo concreto;
  2. `grupo_id`, **solo cuando la compra no guarda producto** -- no es un fallback
     del anterior: dos articulos del mismo grupo son dos productos distintos, y
     una linea que pidio `dia:A` no queda repetida porque la lista tenga `dia:B`
     del mismo grupo (`test_dos_productos_del_mismo_grupo` lo fija al reves);
  3. **el nombre normalizado, y solo cuando falta el destino**: una linea sin
     producto ni grupo es «pendiente de identificar», y ahi el texto es lo unico
     que queda. *Entre dos lineas CON destino no se mira el nombre a proposito*:
     dos marcas distintas con el mismo texto son dos compras distintas, y
     fundirlas es el defecto que `main._ya_estaba` documenta. Tambien se mira el
     nombre contra una **pendiente** de la lista, que es la otra mitad de esa
     misma regla.

`sin_catalogo` gana a `falta` en cuanto no hay destino y el nombre no esta: una
linea que la compra no supo identificar no se puede repetir tal cual, y decirlo
es mejor que apuntar una linea a medias.

**Idempotencia por operacion, no por resultado.** El id de cada linea nueva sale
de `(lista, compra, linea de la compra)` con `core.traspaso.id_de_linea`, la
misma cuenta que usan los dos puentes. Asi repetir la misma compra dos veces da
los mismos ids, y `almacen.anade_linea` -- que ya es un upsert -- los actualiza
en vez de duplicarlos si algo se cuela entre la comprobacion y la escritura.
Otra compra (otra semana) es otra operacion y da ids distintos.
"""
from __future__ import annotations

from core import traspaso

# Los tres estados. Son los valores exactos del contrato JSON.
FALTA = "falta"
YA_ESTABA = "ya_estaba"
SIN_CATALOGO = "sin_catalogo"
ESTADOS = (FALTA, YA_ESTABA, SIN_CATALOGO)

# La operacion, en la clave del id deterministico. Cambiarla cambia los ids.
OPERACION = "repetir-compra"


def normaliza(nombre: object) -> str:
    """El nombre comparable: sin espacios en los bordes y en minusculas."""
    return str(nombre or "").strip().lower()


def claves_de_la_lista(lineas: list[dict]) -> dict[str, set]:
    """Lo que ya hay en la lista, por las tres formas de identificar una linea.

    Se devuelven las tres por separado, y no un `set` de tuplas, porque cada una
    contesta una pregunta distinta: *¿esta este producto?*, *¿esta este grupo?* y
    *¿esta una linea pendiente que se llame asi?*.
    """
    nombres = {normaliza(x.get("nombre_visto")) for x in lineas}
    nombres.discard("")
    return {
        "productos": {str(x["producto_id"]) for x in lineas if x.get("producto_id")},
        "grupos": {int(x["grupo_id"]) for x in lineas if x.get("grupo_id") is not None},
        "nombres": nombres,
        "pendientes": {normaliza(x.get("nombre_visto")) for x in lineas
                       if not x.get("producto_id") and x.get("grupo_id") is None},
    }


def estado_de(comprada: dict, claves: dict) -> str:
    """Que le pasaria a **una** linea de la compra al repetirla. Puro.

    `comprada` es una fila de `almacen.lineas_de_compra`; `claves`, lo que hay en
    la lista. No escribe nada ni necesita base: es la regla, y por eso se puede
    probar sola.
    """
    producto = comprada.get("producto_id")
    grupo = comprada.get("grupo_id")
    tiene_destino = bool(producto) or grupo is not None
    # 1. El articulo concreto, si la compra lo guardo: es la identidad mas fina.
    if producto:
        if str(producto) in claves["productos"]:
            return YA_ESTABA
    # 2. El grupo, **solo para una linea que no trae producto**. No es un fallback: dos articulos
    #    del mismo grupo son dos productos distintos (`test_dos_productos_del_mismo_grupo`), y una
    #    linea que pidio `dia:A` no queda repetida porque la lista tenga `dia:B` del mismo grupo.
    elif grupo is not None and int(grupo) in claves["grupos"]:
        return YA_ESTABA
    nombre = normaliza(comprada.get("nombre"))
    # 3. El nombre: cuando la compra no tiene destino -- una linea «pendiente de identificar», y
    #    ahi el texto es lo unico que queda -- o cuando la lista ya tiene una pendiente con ese
    #    nombre. Entre dos lineas CON destino no se mira el nombre, y el porque esta arriba.
    if nombre and not tiene_destino:
        return YA_ESTABA if nombre in claves["nombres"] else SIN_CATALOGO
    if nombre and nombre in claves["pendientes"] and nombre in claves["nombres"]:
        return YA_ESTABA
    return FALTA


def fecha_de(compra: dict | None) -> str | None:
    """El dia de la compra, ISO y sin la hora; `None` si no hay compra."""
    if not compra:
        return None
    sello = str(compra.get("cerrada_en") or "")
    return sello[:10] or None


def previa(compra: dict | None, lineas_compra: list[dict],
           lineas_lista: list[dict],
           en_casa: set[str] | None = None) -> dict:
    """**El contrato del GET**: que pasaria, sin tocar la lista.

    Con `compra=None` devuelve la forma entera con los contadores a cero: la
    pantalla necesita siempre los mismos campos, y `null` no es una lista vacia
    de otra forma -- la previa de una lista sin compras es exactamente esto.

    `en_casa` son los textos de la despensa declarada, ya normalizados. Se marca
    cada linea con `en_casa: true/false`, y **`None` cuando no se pudo leer la
    despensa** -- que no es lo mismo que «no hay nada»: un `false` afirmaria que
    no lo tienes sin haber mirado. La comparacion es **por nombre en minusculas**,
    como en la previa de un plan: la despensa guarda texto, no identidad de
    producto. Y la marca **no cambia lo que se añade**: repetir reproduce la
    compra; saber que ya lo tienes es informacion para decidir, no una regla que
    borre lineas por su cuenta.
    """
    if compra is None:
        return {"compra_id": None, "fecha": None, "lineas": [],
                "faltan": 0, "ya_estaban": 0, "sin_catalogo": 0,
                "en_casa": 0, "faltan_en_casa": 0}
    claves = claves_de_la_lista(lineas_lista)
    lineas = []
    cuenta = dict.fromkeys(ESTADOS, 0)
    for comprada in lineas_compra:
        estado = estado_de(comprada, claves)
        cuenta[estado] += 1
        lineas.append({
            "nombre": comprada.get("nombre"),
            "producto_id": comprada.get("producto_id"),
            "grupo_id": comprada.get("grupo_id"),
            "cantidad": int(comprada.get("cantidad") or 1),
            "estado": estado,
            "en_casa": (None if en_casa is None
                        else normaliza(comprada.get("nombre")) in en_casa),
        })
    return {"compra_id": str(compra["compra_id"]), "fecha": fecha_de(compra),
            "lineas": lineas, "faltan": cuenta[FALTA],
            "ya_estaban": cuenta[YA_ESTABA], "sin_catalogo": cuenta[SIN_CATALOGO],
            "en_casa": sum(1 for l in lineas if l["en_casa"] is True),
            "faltan_en_casa": sum(1 for l in lineas
                                  if l["estado"] == FALTA and l["en_casa"] is False)}


def nota_de(comprada: dict) -> str | None:
    """La nota que tenia la linea comprada, si se conserva. En blanco no es nota."""
    nota = comprada.get("nota")
    if nota is None:
        return None
    limpia = str(nota).strip()
    return limpia or None


def id_de_linea(lista_id: str, compra_id: str, comprada: dict,
                indice: int = 0) -> str:
    """El id determinista del alta: la misma compra repetida da los mismos ids.

    La clave lleva **la linea de la compra** (`linea_id`), no el producto: una
    compra puede tener dos lineas del mismo articulo -- la lista puede tener dos
    lineas iguales -- y con la clave por producto las dos caerian en el mismo id
    y una pisaria a la otra. `indice` es la ultima red para una linea de compra
    sin identificador propio.
    """
    suya = comprada.get("linea_id") or comprada.get("id")
    if not suya:
        suya = (f"{comprada.get('producto_id')}|{comprada.get('grupo_id')}"
                f"|{normaliza(comprada.get('nombre'))}|{indice}")
    return traspaso.id_de_linea(lista_id, f"{OPERACION}|{compra_id}|{suya}")


def anadibles(lista_id: str, compra_id: str, lineas_compra: list[dict],
              lineas_lista: list[dict]) -> list[dict]:
    """**Las lineas que de verdad hay que escribir**, ya con su id y su nota.

    Es el otro lado de `previa`, con la misma regla: solo las que estan `falta`.
    Se calcula en vez de leerlo de la previa porque la previa no lleva el id ni
    la nota -- son cosas de la accion, no de lo que se enseña antes de pulsar.
    """
    claves = claves_de_la_lista(lineas_lista)
    salida = []
    for indice, comprada in enumerate(lineas_compra):
        if estado_de(comprada, claves) != FALTA:
            continue
        salida.append({
            "id": id_de_linea(lista_id, compra_id, comprada, indice),
            "nombre": comprada.get("nombre"),
            "producto_id": comprada.get("producto_id"),
            "grupo_id": comprada.get("grupo_id"),
            "cantidad": int(comprada.get("cantidad") or 1),
            "nota": nota_de(comprada),
        })
    return salida
