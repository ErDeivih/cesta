"""El mosaico de lo habitual: lo que esta persona compra una y otra vez.

La pantalla de buscar, con el campo vacio, no puede estar en blanco: ahi es donde
se anade de **un toque** en vez de escribir, elegir y anadir, que es lo que hace
que una lista se use o se abandone. Lo que se ensena sale de aqui.

De donde sale cada mitad
------------------------
El **historial** es de esta persona y vive en PostgreSQL (`lista_linea`): cuantas
veces ha anadido cada grupo. No sale de gold, y esa es la diferencia entre "lo que
suele comprar" y "lo mas barato del catalogo".

La **tarjeta** -- nombre, foto, precio por unidad, unidad, cadena mas barata y
`fiable` -- es de hoy y vive en gold: se lee con DuckDB, en `catalogo.tarjetas`.
El historial dice QUE productos; gold dice COMO estan hoy. Un grupo que ya no esta
en gold no se puede pintar y no viaja.

Tres origenes, y se dice cual de cada tarjeta
--------------------------------------------
El primer dia no hay historial, y el primer dia es justo el que se queda sin
pensar. Asi que hay tres escalones y **cada tarjeta dice de donde sale**, para que la
pantalla pueda ser honesta: *"todavia no se lo que sueles comprar"*, *"esto lo compra la
casa"*, *"esto es la compra basica"*.

    "tuyo"       lo que esta persona ha anadido mas veces
    "de todos"   lo que mas gente ha anadido en toda la casa. Es un recuento
                 agregado: no dice quien, y por eso se puede ensenar
    "basico"     una lista fija de la compra basica, para que la cuadricula no
                 este vacia ni con la base de datos recien creada

**Se rellena hasta `limite`, bajando escalones**, y el orden es el de lo que mas dice de
esta persona: primero lo suyo, despues lo de la casa, despues la compra basica. Medido el
23 de septiembre de 2026 contra la base viva: con **una sola** linea propia, la respuesta
era un mosaico de **una** tarjeta -- el problema numero uno del encargo (la primera vez)
reapareciendo dentro del endpoint construido para resolverlo. Un mosaico de una tarjeta no
es un mosaico, y *"casi vacio"* se ve casi vacio.

**El `origen` va en cada tarjeta**, y no uno por respuesta. Una tarjeta basica y una tuya
no valen lo mismo, y con un solo campo por respuesta la pantalla no tendria como decirlo:
una cuadricula puede tener las dos cosas a la vez, y ahora las tiene. Lo que se dice una
vez es `origenes`, la lista de escalones que han entrado, para que la pantalla sepa si
tiene que explicar algo.

Y un grupo **no se repite**: si lo que compras es "leche entera" y ademas esta en la
compra basica, sale una vez, en el escalon de mas arriba. Repetirlo para llenar la
cuadricula seria inflar el mosaico con lo mismo.

Lo que NO viaja, y por que
--------------------------
`veces` y `ultima_vez` son la historia de esta persona, asi que solo se mandan en las
tarjetas de `"tuyo"`. En "de todos" el recuento es de todo el mundo y en "basico" no hay
recuento ninguno: mandarlos con el mismo nombre en los tres casos seria otra vez dos
numeros distintos llamandose igual (ver `core/comparacion.py`), y la pantalla no tendria
como saber que esta leyendo.

El porque del decaimiento
-------------------------
El documento del encargo deja elegir entre contar solo los ultimos 90 dias o
pesar por recencia, y pide escribir por que. Se eligio **pesar**, con una vida
media de 30 dias, y las razones estan escritas donde vive la consulta
(`almacen.historial_de`), junto a las otras dos decisiones del historial: contar
tambien las lineas borradas y contar solo lo que anadio esta persona.
"""
from __future__ import annotations

from . import almacen, catalogo

# Cuantos candidatos se piden por cada tarjeta que se quiere ensenar.
#
# No es un adorno: el historial vive en PostgreSQL y el catalogo en gold, y los
# dos se escriben por caminos distintos. Un grupo que el emparejador ya no
# reconoce no se puede pintar, y sin este margen la cuadricula se quedaria corta
# sin que nadie sepa por que. Se piden tres veces mas de los que hacen falta; cada
# candidato de mas es una fila de una tabla de decenas de miles.
MARGEN = 3

# La compra basica. Es el ultimo recurso, para el dia en que no hay historial ni
# suyo ni de nadie: sin esto, la pantalla de buscar se abre en blanco y parece
# rota justo cuando alguien la prueba por primera vez.
#
# Se escriben como NOMBRES y no como `grupo_id` a proposito: los identificadores
# de grupo son de la ultima pasada del emparejador y cambian cuando se rehace
# (ver el comentario del esquema, `plataforma/sql/001_esquema.sql`). Un nombre se
# puede volver a buscar; un id de la semana pasada, no.
#
# Los 24 son la compra de cualquier casa, elegidos para que se reconozcan en una
# foto de 100 x 100. Sin tildes y en minusculas, que es como esta escrito el texto
# del catalogo (`strip_accents(lower(...))` en `catalogo.conexion`).
#
# La frase tiene que identificar EL producto y no solo mencionarlo, porque de cada
# nombre se elige el grupo que mas cadenas venden. Medido sobre el catalogo del 23
# de septiembre de 2026: con "huevos" ganaba un Kinder de chocolate, con "patatas"
# unas patatas congeladas y con "papel higienico" unas toallitas humedas, que son
# los productos que mas cadenas venden de esas palabras. "Papel higienico 2 capas"
# si es el paquete de rollos.
BASICOS = (
    "leche entera", "pan de molde", "huevos", "aceite de oliva",
    "arroz", "macarrones", "tomate frito", "atun en aceite",
    "agua mineral", "yogur natural", "platano", "manzanas",
    "cebollas", "patatas malla", "pollo", "jamon cocido",
    "queso", "mantequilla", "cafe molido", "galletas",
    "papel higienico 2 capas", "detergente", "gel de ducha", "pasta de dientes",
)

# La compra basica resuelta se guarda hasta que gold cambie de fecha, que es una
# vez al dia. Buscar 24 nombres y montar 24 tarjetas se nota, y los nombres no
# cambian: lo unico que cambia es el catalogo, y de eso avisa la fecha.
_basico: tuple[str, list[dict]] = ("", [])


def _compra_basica() -> list[dict]:
    """Las tarjetas de `BASICOS`, resueltas contra el catalogo de hoy."""
    global _basico
    hoy = catalogo.fecha_de_gold()
    if _basico[0] == hoy:
        return _basico[1]
    hechas = catalogo.tarjetas_por_nombre(list(BASICOS))
    _basico = (hoy, hechas)
    return hechas


def _con_historial(tarjeta: dict, hist: dict) -> dict:
    """La tarjeta de gold con lo que solo sabe PostgreSQL: veces y cuando."""
    return tarjeta | {"veces": hist["veces"], "ultima_vez": hist["ultima_vez"]}


def lista(usuario_id: str, limite: int = 24) -> dict:
    """El mosaico: las tarjetas de lo habitual, **hasta `limite`**, con su origen.

    `limite` es lo que se ensena; a cada escalon se le piden `MARGEN` veces mas.
    """
    limite = max(1, int(limite))
    candidatos = limite * MARGEN
    puestas: list[dict] = []
    vistas: set[int] = set()
    origenes: list[str] = []

    def anade(origen: str, tarjetas: list[dict]) -> None:
        """Suma tarjetas hasta el limite, sin repetir grupo, con su origen."""
        antes = len(puestas)
        for t in tarjetas:
            if len(puestas) >= limite:
                break
            gid = int(t["grupo_id"])
            if gid in vistas:
                continue
            vistas.add(gid)
            puestas.append({**t, "origen": origen})
        if len(puestas) > antes:
            origenes.append(origen)

    suyos = almacen.historial_de(usuario_id, candidatos)
    if suyos:
        tarjetas = catalogo.tarjetas([h["grupo_id"] for h in suyos])
        # El orden lo decide PostgreSQL (lo reciente pesa mas) y aqui no se toca:
        # se recorren los candidatos en su orden y se saltan los que no tienen
        # tarjeta. `tarjetas` es un diccionario, y recorrerlo daria el orden del
        # catalogo, que no es el del habito.
        propias = [_con_historial(tarjetas[h["grupo_id"]], h)
                   for h in suyos if h["grupo_id"] in tarjetas]
        anade("tuyo", propias)

    if len(puestas) < limite:
        de_todos = almacen.mas_comprados(candidatos)
        if de_todos:
            tarjetas = catalogo.tarjetas([h["grupo_id"] for h in de_todos])
            ajenas = [tarjetas[h["grupo_id"]] for h in de_todos
                      if h["grupo_id"] in tarjetas]
            anade("de todos", ajenas)

    if len(puestas) < limite:
        anade("basico", _compra_basica())

    # Sin catalogo no hay nada que pintar: la lista vacia es una respuesta honesta
    # y la pantalla ya sabe decir "no lo se" (ver `catalogo.secciones`, que hace lo
    # mismo mientras el scraper no ha escrito la columna que necesita).
    return {"origenes": origenes, "habituales": puestas[:limite],
            "fecha_datos": catalogo.fecha_de_gold()}
