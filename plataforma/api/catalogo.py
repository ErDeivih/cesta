"""Las consultas al catalogo. DuckDB sobre los parquet de gold, sin copiarlos.

Esta mitad del sistema **solo lee**. Gold lo escribe el pipeline una vez al dia
y la API no lo toca nunca: si un dia el scraper falla, aqui se sigue sirviendo
lo de ayer y se dice en pantalla.

Una conexion por hilo. DuckDB no es seguro entre hilos con la misma conexion, y
FastAPI atiende en un pool: compartir una sola conexion es la forma mas rapida
de ver resultados mezclados.
"""
from __future__ import annotations

import json
import re
import threading
import unicodedata
from pathlib import Path

import duckdb

from core import comparacion, version_vigente

from .ajustes import AJUSTES

# La carpeta de las pasadas versionadas del matching.
#
# Se escribe aqui en vez de importarla de `core.equivalencias`, y no es un
# descuido: ese modulo vive de polars (lo escribe el pipeline, que trabaja con
# dataframes) y **la API no puede arrastrar polars**. El 21 de septiembre de 2026
# ese mismo cruce tumbo el contenedor en un bucle de reinicios que no decia por
# que. Aqui se lee con SQL, que es lo que la API sabe hacer. Lo vigila
# `tests/test_imagen_api.py`.
CARPETA_MATCHING = "matching"

_local = threading.local()


def _sin_tildes(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def _sello_de_gold() -> float:
    """Cuando se escribio gold por ultima vez.

    El pipeline reescribe `grupos.parquet` una vez al dia, y `buscable` es una
    COPIA que se hizo al abrir la conexion: sin mirar esto, cada hilo seguiria
    sirviendo el catalogo de ayer hasta que alguien reiniciase el contenedor.
    Y como la cache del panel se indexa por `fecha_de_gold()`, tampoco se
    refrescaria. La app se quedaba congelada en silencio.
    """
    # **El sello de lo que se LEE, no el del fichero suelto.** *Mientras se sirve una version, el
    # `mtime` del gold suelto es el de un fichero que puede no ser el que se lee: la cache no se
    # invalidaria al publicar, que es justo cuando tiene que invalidarse.*
    #
    # *Y sin puntero `version_vigente.sello` devuelve el del suelto, asi que el comportamiento de
    # siempre no cambia.*
    return version_vigente.sello(AJUSTES.gold, "grupos.parquet")


def sello_de_gold() -> float:
    """Lo mismo, con nombre publico: es la senal de "hay datos nuevos".

    La usa el vigilante de las alertas (`api/vigilante.py`) para no mirar cien veces
    lo que cambia una: los precios se escriben una vez al dia.
    """
    return _sello_de_gold()


def conexion() -> duckdb.DuckDBPyConnection:
    """La conexion de este hilo, con las vistas ya montadas.

    Una por hilo: DuckDB no es seguro compartiendo una entre varios, y FastAPI
    atiende en un pool. Si gold ha cambiado desde que se abrio, se rehace.
    """
    sello = _sello_de_gold()
    con = getattr(_local, "con", None)
    if con is not None:
        if getattr(_local, "sello", None) == sello:
            return con
        con.close()          # gold es otro: esta conexion mira datos viejos
        _local.con = None
    con = duckdb.connect(database=":memory:")
    g = AJUSTES.gold
    # **La version se resuelve UNA VEZ, y las cinco vistas salen de ella.**
    #
    # *Resolver el puntero cinco veces -- una por vista -- es lo que deja montar `grupos` de una
    # publicacion y `enlaces` de la siguiente si se publica a mitad de camino: la mezcla que S01
    # prohibe y que `version_vigente.ruta` existe para evitar.* Y **es la frase que hasta hoy se
    # cumplia por trivialidad**: `rutas()` estaba probado pero no lo usaba nadie.
    #
    # *Sin puntero, `ruta` devuelve los ficheros sueltos de siempre: el fallback conservador.*
    version = version_vigente.version_actual(g)

    def _de_la_version(nombre: str) -> str:
        return _p(version_vigente.ruta(g, nombre, version))

    con.execute(f"CREATE VIEW grupos AS SELECT * FROM '{_de_la_version('grupos.parquet')}'")
    con.execute(f"CREATE VIEW enlaces AS SELECT * FROM '{_de_la_version('enlaces.parquet')}'")
    con.execute(f"CREATE VIEW diario AS SELECT * FROM '{_de_la_version('precio_diario.parquet')}'")
    con.execute(f"CREATE VIEW derivado AS SELECT * FROM '{_de_la_version('precio_derivado.parquet')}'")
    con.execute(f"CREATE VIEW resumen AS SELECT * FROM '{_de_la_version('resumen.parquet')}'")
    # Una columna de busqueda sin tildes y en minusculas, calculada una vez.
    #
    # Las columnas se piden con `_o_nulo`, que comprueba antes si existen en el
    # parquet. La razon es la frontera entre las dos mitades del sistema: el
    # scraper escribe data/gold y la plataforma lo monta en solo lectura, y las
    # dos se actualizan por separado. Si la plataforma es mas nueva que el
    # ultimo gold -- porque el scraper no ha corrido desde el cambio -- pedir
    # una columna que aun no esta ahi tiraba la app entera con un Binder Error,
    # no una busqueda: la conexion se crea al arrancar. Un dato que todavia no
    # existe debe ser None, no una caida.
    disponibles = {f[0] for f in con.execute("DESCRIBE grupos").fetchall()}

    def _o_nulo(*nombres: str) -> str:
        return ", ".join(c if c in disponibles else f"NULL AS {c}" for c in nombres)

    # `promo_unidades_minimas` (las unidades que pide la mecanica de una oferta, Alcampo) va en
    # esta lista y no solo en `grupos` porque **la busqueda lee `buscable`**: una columna que
    # existe en `grupos` pero no en esta tabla tira la busqueda entera con un Binder Error.
    # Paso el 27 de septiembre de 2026: la app se quedo con «No he podido traer esto» en Buscar
    # por pedir en el SQL una columna que `buscable` no tenia.
    con.execute(f"""
        CREATE TABLE buscable AS
        SELECT grupo_id, fuente, id_fuente, nombre, marca, cantidad, unidad_canon,
               precio_cent, precio_unidad_cent, comparacion_fiable, calidad,
               calidad_origen, nutriscore, nova, ean, imagen, promo_txt,
               {_o_nulo("sellos", "conservacion", "es_marca_propia", "envase",
                        "nutricion", "promo_club", "promo_solo_online",
                        "es_alcohol", "es_recall",
                        "distintivo", "precio_comparable", "seccion",
                        "promo_unidades_minimas")},
               strip_accents(lower(nombre || ' ' || coalesce(marca, ''))) AS texto
          FROM grupos
    """)
    con.execute("CREATE INDEX buscable_grupo ON buscable(grupo_id)")
    # El diccionario de palabras del catalogo, para arreglar una busqueda con faltas
    # de ortografia (`corregir`). Se monta **una vez por conexion** -- 0,06 s medidos
    # sobre 52.417 productos -- y no en cada busqueda: cambia cuando cambia gold, y
    # gold cambia cuando esta conexion se rehace, que es exactamente cuando toca.
    con.execute("""CREATE TABLE palabras AS
        SELECT palabra, count(*) AS veces FROM buscable,
               unnest(string_split(texto, ' ')) AS t(palabra)
         WHERE length(palabra) >= 4
         GROUP BY palabra""")
    _local.con = con
    _local.sello = sello
    return con


def _p(ruta: Path) -> str:
    return str(ruta).replace("\\", "/").replace("'", "''")


def reiniciar() -> None:
    """Olvida la conexion de este hilo. Para las pruebas y para forzar recarga."""
    con = getattr(_local, "con", None)
    if con is not None:
        con.close()
    _local.con = None
    _local.sello = None
    _local.fecha = None


def fecha_de_gold() -> str:
    """El dia mas reciente que hay en el historico.

    Sostiene toda la regla de las fechas: la interfaz la pide al abrir y con
    ella sabe que precios puede dar por buenos. Se guarda junto al sello del
    fichero, para que al regenerar gold cambie sola.
    """
    con = conexion()          # rehace la conexion si gold ha cambiado
    sello = getattr(_local, "sello", None)
    if getattr(_local, "fecha_sello", None) == sello and getattr(_local, "fecha", None):
        return _local.fecha
    fila = con.execute("SELECT max(fecha)::VARCHAR FROM diario").fetchone()
    _local.fecha = fila[0] if fila and fila[0] else ""
    _local.fecha_sello = sello
    return _local.fecha


# ------------------------------------------------------------------ buscar ---

# Los sellos por los que se puede filtrar. Se valida contra esta lista y no se
# interpola nunca lo que llegue del cliente: el LIKE se construye con parametro.
SELLOS_FILTRABLES = ("sin-gluten", "sin-lactosa", "vegano", "vegetariano",
                     "ecologico", "sin-azucar", "sin-sal", "sin-aceite-palma")

# La frontera esta en core/comparacion.py, compartida con el resumen diario:
# antes habia dos numeros distintos y los dos se llamaban "imposible".
FACTOR_INCREIBLE = comparacion.FACTOR_INCREIBLE
CONSERVACIONES = ("refrigerado", "congelado", "ambiente")

# Arreglar una busqueda escrita con faltas (ver `corregir`). Dos numeros, y los dos
# estan medidos sobre el catalogo de hoy:
#
#   `PARECIDO`     0,85. Con 0,80 entraban cosas como `asucar` -> `asua`, que es peor
#                  que no corregir: cambiar una palabra por otra que no tiene nada que
#                  ver y ensenar esos resultados es peor que decir "no encuentro".
#   `LARGO_MINIMO` 4 letras. Con tres letras, `pan` esta a un cambio de letra de `paz`,
#                  `paz` de `paz`... y corregir una palabra corta acierta menos veces de
#                  las que falla.
PARECIDO = 0.85
LARGO_MINIMO = 4


def corregir(texto: str) -> str | None:
    """El texto con las palabras mal escritas arregladas, o `None` si no hay nada.

    Se busca **palabra a palabra** en el diccionario del catalogo (las palabras que
    existen de verdad, `conexion`), y se cambia solo la que no existe por la mas
    parecida **del mismo tamano** (`±1` letra). Las dos reglas tienen su porque:

      - **El mismo tamano** es lo que evita `asucar` -> `asua`. El parecido de Jaro-
        Winkler premia los prefijos, asi que sin esa condicion gana la palabra corta que
        empieza igual, y cambiar `asucar` por `asua` es peor que no corregir.
      - **La palabra que ya existe no se toca**: si esta en el diccionario, ella misma es
        su mejor candidata (parecido 1,0) y no cambia nada. Asi corregir es idempotente.
      - **A igualdad de parecido gana la palabra que mas aparece** en el catalogo. No es un
        desempate decorativo: `natral` empata casi exacto con `natrual` (que existe **una**
        vez: alguien la escribio mal en su ficha) y con `natural` (que aparece miles). El
        parecido redondeado a dos decimales agrupa a los que empatan de verdad, y ahi manda
        la frecuencia, que es lo que distingue una palabra de una errata de una tienda.

    Devuelve `None` -- y no el texto igual -- cuando no hay nada que arreglar: quien
    llama tiene que poder decir "esto es lo que has escrito" o "esto es lo que he
    entendido", y son dos frases distintas.
    """
    palabras = [p for p in _sin_tildes(texto).lower().split() if p]
    if not palabras:
        return None
    con = conexion()
    salida: list[str] = []
    cambio = False
    for p in palabras:
        if len(p) < LARGO_MINIMO:
            salida.append(p)
            continue
        fila = con.execute("""
            SELECT palabra FROM palabras
             WHERE length(palabra) BETWEEN ? AND ?
               AND jaro_winkler_similarity(palabra, ?) >= ?
             ORDER BY round(jaro_winkler_similarity(palabra, ?), 2) DESC, veces DESC
             LIMIT 1""",
            [len(p) - 1, len(p) + 1, p, PARECIDO, p]).fetchone()
        if fila and fila[0] != p:
            salida.append(fila[0])
            cambio = True
        else:
            salida.append(p)
    return " ".join(salida) if cambio else None


def buscar(texto: str, cadenas: list[str] | None = None, limite: int = 40,
           solo_comparables: bool = False, solo_con_nutricion: bool = False,
           sellos: list[str] | None = None, conservacion: str | None = None,
           solo_marca_propia: bool = False, solo_ofertas: bool = False,
           sin_alcohol: bool = False, seccion: str | None = None,
           desplazamiento: int = 0) -> list[dict]:
    """Grupos que casan con el texto, cada uno con su precio mas bajo.

    Los productos sin grupo salen igual, marcados: son 32.522 de 51.800 y
    esconderlos seria esconder el 63 % del catalogo.
    """
    palabras = [p for p in _sin_tildes(texto).lower().split() if p]
    # Sin texto no hay busqueda... salvo que se este explorando un pasillo, que
    # es una busqueda por si misma: "ensename lo que hay en congelados".
    if not palabras and not seccion:
        return []
    con = conexion()
    # Las columnas nuevas se piden **solo si estan**: gold puede ser de antes del ultimo
    # cambio de codigo (pasa cada vez que se anade un campo y aun no ha corrido la pasada), y
    # una busqueda que revienta por una columna que no existe deja la pantalla en blanco.
    # Se pregunta por **`buscable`**, que es la tabla que lee esta consulta, y no por `grupos`:
    # las dos pueden no tener las mismas columnas, y preguntarle a la que no es daba por buena
    # una columna que la consulta no encuentra (medido el 27 de septiembre de 2026).
    columnas = {f[0] for f in con.execute("DESCRIBE buscable").fetchall()}
    unidades = ("max(coalesce(promo_unidades_minimas, 0))"
                if "promo_unidades_minimas" in columnas else "0")

    # Dos grupos de condiciones, y la diferencia importa mucho.
    #
    #   `texto`     de que va la busqueda. Basta con que lo cumpla UN miembro
    #               del grupo para que el grupo entre: si buscas "leche", el
    #               grupo entero es de leche aunque un miembro se llame "L.R.
    #               Desnatada".
    #   `atributo`  que tiene que cumplir cada producto que se ensene. Un
    #               filtro de dieta NO puede relajarse a nivel de grupo.
    #
    # Al principio los dos se aplicaban solo al buscar y luego el grupo se
    # reconstruia entero, asi que "galletas sin gluten" contestaba con unas
    # galletas Cuetara normales (estaban en el mismo grupo que unas sin gluten)
    # y "pizza congelada" con una salsa barbacoa. Para alguien celiaco eso no es
    # un resultado flojo, es un resultado peligroso.
    texto_donde: list[str] = []
    texto_args: list = []
    for p in palabras:
        texto_donde.append("texto LIKE ?")
        texto_args.append(f"%{p}%")

    atributo_donde: list[str] = []
    atributo_args: list = []
    if cadenas:
        atributo_donde.append(f"fuente IN ({','.join('?' * len(cadenas))})")
        atributo_args.extend(cadenas)
    if solo_comparables:
        atributo_donde.append("comparacion_fiable")
    if solo_con_nutricion:
        # La tabla de la etiqueta vale tanto como el Nutri-Score, y llega a
        # 3.685 productos de DIA donde Open Food Facts no llega.
        atributo_donde.append("(nutriscore IS NOT NULL OR nutricion IS NOT NULL)")
    for sello in (sellos or []):
        if sello not in SELLOS_FILTRABLES:
            continue
        # Con comas a los lados para que "sin-sal" no case dentro de otro sello.
        # Los valores llegan ya ordenados y separados por comas del colector.
        atributo_donde.append("',' || coalesce(sellos, '') || ',' LIKE ?")
        atributo_args.append(f"%,{sello},%")
    if conservacion in CONSERVACIONES:
        atributo_donde.append("conservacion = ?")
        atributo_args.append(conservacion)
    if solo_marca_propia:
        atributo_donde.append("es_marca_propia")
    if solo_ofertas:
        # Ni una oferta de tarjeta ni una de solo-internet son ofertas para quien
        # busca ofertas: ninguna de las dos baja lo que pagas en la tienda. Son
        # 1.658 de tarjeta y 397 de internet, sobre 6.938 con promocion.
        atributo_donde.append(
            "promo_txt IS NOT NULL AND coalesce(promo_club, false) = false "
            "AND coalesce(promo_solo_online, false) = false")
    if sin_alcohol:
        atributo_donde.append("coalesce(es_alcohol, false) = false")
    if seccion:
        # La seccion es un atributo del producto, no del grupo: un grupo con un
        # miembro mal clasificado no arrastra al pasillo a los demas.
        atributo_donde.append("seccion = ?")
        atributo_args.append(seccion)

    filtro_casan = " AND ".join(texto_donde + atributo_donde) or "1=1"
    filtro_miembros = " AND ".join(atributo_donde) or "1=1"
    args = texto_args + atributo_args + atributo_args + [limite, max(0, int(desplazamiento))]

    filas = con.execute(f"""
        WITH casan AS (SELECT * FROM buscable WHERE {filtro_casan}),
        -- Un grupo entra si alguno de sus miembros casa con el TEXTO...
        gs AS (SELECT DISTINCT grupo_id FROM casan WHERE grupo_id IS NOT NULL),
        -- ...pero solo se ensenan los miembros que cumplen los ATRIBUTOS.
        miembros AS (
            SELECT b.* FROM buscable b JOIN gs ON b.grupo_id = gs.grupo_id
             WHERE {filtro_miembros}
        ),
        -- Un grupo puede tener productos medidos en unidades distintas: 231 de
        -- los 6.318 comparables (3,7 %) mezclan kg con ud. Pasa cuando una
        -- cadena vende la manzanilla por peso (76,79 EUR/kg de hierba) y otra
        -- por bolsitas (0,09 EUR/ud). Los dos precios son correctos y **no se
        -- pueden restar**: al hacerlo, la app anunciaba ahorros del 229.833 %.
        -- Esos 231 grupos eran el 67 % de todos los que decian "mas de 10x".
        --
        -- Asi que primero se elige UNA unidad por grupo -- la que comparten mas
        -- cadenas, y a igualdad la que tiene mas productos -- y solo se compara
        -- dentro de ella. Los productos en otra unidad siguen estando en el
        -- grupo y salen en la ficha; lo que no hacen es decidir el ahorro.
        unidades AS (
            SELECT grupo_id, unidad_canon,
                   count(DISTINCT fuente) AS c, count(*) AS n
              FROM miembros
             WHERE precio_unidad_cent > 0 AND unidad_canon IS NOT NULL
               AND coalesce(precio_comparable, true)
             GROUP BY grupo_id, unidad_canon),
        manda AS (
            SELECT grupo_id, arg_max(unidad_canon, c * 1000 + n) AS unidad
              FROM unidades GROUP BY grupo_id),
        comparables AS (
            SELECT m.* FROM miembros m JOIN manda u
              ON m.grupo_id = u.grupo_id AND m.unidad_canon = u.unidad
             -- Fuera las filas en disputa: su precio por unidad y el de la
             -- cadena se contradicen por mas del doble y no se sabe cual esta
             -- mal, asi que no pueden decidir donde sale mas barato algo.
             WHERE m.precio_unidad_cent > 0
               AND coalesce(m.precio_comparable, true)),
        porgrupo AS (
            SELECT grupo_id,
                   count(*) AS productos,
                   count(DISTINCT fuente) AS cadenas,
                   min(precio_unidad_cent) AS min_unidad,
                   max(precio_unidad_cent) AS max_unidad,
                   arg_min(nombre, precio_unidad_cent) AS nombre,
                   -- La marca del miembro mas barato. La tabla del buscador la
                   -- pedia y no la tenia: la unica forma de sacarla era
                   -- inventarla a partir del nombre, y eso es mentir.
                   arg_min(marca, precio_unidad_cent) AS marca,
                   arg_min(fuente, precio_unidad_cent) AS fuente_barata,
                   arg_min(precio_cent, precio_unidad_cent) AS precio_cent,
                   any_value(unidad_canon) AS unidad,
                   max(nutriscore) AS nutriscore,
                   arg_min(imagen, precio_unidad_cent) AS imagen,
                   -- Solo cuentan como oferta las que bajan lo que pagas HOY
                   -- en caja. Las de tarjeta se cuentan aparte y se dicen
                   -- aparte: 200 de las 221 de DIA son de tarjeta, y meterlas
                   -- en el mismo saco seria anunciar rebajas que no existen.
                   count(*) FILTER (WHERE promo_txt IS NOT NULL
                                      AND coalesce(promo_club, false) = false
                                      AND coalesce(promo_solo_online, false) = false)
                     AS con_oferta,
                   count(*) FILTER (WHERE coalesce(promo_club, false)) AS con_oferta_club,
                   count(*) FILTER (WHERE coalesce(es_recall, false)) AS con_retirada,
                   -- Cuantas unidades exige la mecanica de esa oferta, cuando la cadena lo
                   -- dice en numero (Alcampo). Es una condicion del precio, y en una lista de
                   -- resultados «oferta» a secas se lee como «mas barata hoy».
                   {unidades} AS oferta_unidades
              FROM comparables GROUP BY grupo_id)
        -- `cadenas >= 2` es lo que hace comparable a un grupo, no tener grupo_id:
        -- el emparejador se lo pone a todo, y 32.486 grupos son de un solo
        -- producto. Durante unos dias la interfaz pinto "1 cadenas · 1
        -- productos" para esos, con el sello de comparable puesto.
        SELECT grupo_id, nombre, marca, fuente_barata, precio_cent, min_unidad,
               max_unidad, unidad, cadenas, productos, nutriscore, imagen,
               con_oferta, con_oferta_club, con_retirada, oferta_unidades,
               cadenas >= 2 AS comparable,
               min_unidad > 0 AND max_unidad / min_unidad > {FACTOR_INCREIBLE} AS dudoso
          FROM porgrupo
        ORDER BY comparable DESC, cadenas DESC, min_unidad, grupo_id
        -- **`OFFSET` para poder pedir la pagina siguiente.** *Sin el, `LIMIT` es un TOPE: se ven los
        -- primeros N, y los siguientes **no se pueden pedir** -- que no es lo mismo que paginar.*
        LIMIT ? OFFSET ?
    """, args).fetchall()

    return [{
        "grupo_id": f[0], "nombre": f[1], "marca": f[2], "cadena_mas_barata": f[3],
        "precio_cent": f[4], "precio_unidad_cent": f[5],
        "precio_unidad_max_cent": f[6], "unidad": f[7],
        "cadenas": f[8], "productos": f[9], "nutriscore": f[10],
        "imagen": f[11], "con_oferta": bool(f[12]),
        "con_oferta_club": bool(f[13]), "con_retirada": bool(f[14]),
        # 0 cuando ninguna oferta exige comprar mas de una unidad: quien pinta la etiqueta
        # solo dice el numero cuando es mayor que uno.
        "oferta_unidades": int(f[15] or 0) or None,
        "comparable": bool(f[16]),
        # Un grupo dudoso sigue saliendo, y sigue diciendo donde esta mas barato.
        # Lo que no hace es poner un numero de ahorro que no se sostiene.
        "dudoso": bool(f[17]),
        "ahorro_pct": (round(100 * (f[6] - f[5]) / f[5], 1)
                       if f[16] and f[5] and not f[17] else 0.0),
    } for f in filas]


# ---------------------------------------------------------------- tarjetas ---
#
# La tarjeta del mosaico de habituales: foto, nombre, precio por unidad, unidad y
# en que cadena esta mas barato. La pide `api/habituales.py`.
#
# Se queda en lo justo a proposito: una cuadricula son 24 tarjetas, y la ficha
# entera de 24 grupos (con sus miembros, su curva y su explicacion) seria una
# consulta enorme para pintar 24 recuadros de 100 x 100.
#
# La regla de la unidad es la MISMA que la de `buscar` (ver el comentario largo de
# alli): primero se elige una unidad por grupo -- la que comparten mas cadenas -- y
# solo se compara dentro de ella, porque los precios de un grupo medidos en
# unidades distintas no se pueden restar. Se repite aqui en vez de sacarlo a un
# sitio comun porque `buscar` es la consulta que sostiene la pantalla de
# resultados y no se toca para reutilizar un trozo: lo que impide que las dos se
# separen es `test_la_tarjeta_y_la_busqueda_dicen_el_mismo_precio`, que compara las
# dos salidas sobre el mismo gold.
_TARJETAS = """
    WITH mios AS ({fuente}),
    unidades AS (
        SELECT grupo_id, unidad_canon,
               count(DISTINCT fuente) AS c, count(*) AS n
          FROM mios
         WHERE precio_unidad_cent > 0 AND unidad_canon IS NOT NULL
           AND coalesce(precio_comparable, true)
         GROUP BY grupo_id, unidad_canon),
    manda AS (
        SELECT grupo_id, arg_max(unidad_canon, c * 1000 + n) AS unidad
          FROM unidades GROUP BY grupo_id),
    comparables AS (
        SELECT m.* FROM mios m JOIN manda u
          ON m.grupo_id = u.grupo_id AND m.unidad_canon = u.unidad
         WHERE m.precio_unidad_cent > 0
           AND coalesce(m.precio_comparable, true)),
    porgrupo AS (
        SELECT grupo_id,
               count(DISTINCT fuente) AS cadenas,
               min(precio_unidad_cent) AS min_unidad,
               max(precio_unidad_cent) AS max_unidad,
               arg_min(nombre, precio_unidad_cent) AS nombre,
               arg_min(fuente, precio_unidad_cent) AS cadena_mas_barata,
               -- `arg_min` se salta los nulos, asi que la foto es la del miembro
               -- mas barato QUE TENGA foto. Un grupo sin ninguna no la manda.
               arg_min(imagen, precio_unidad_cent) AS imagen,
               -- El miembro mas barato es el que da el precio, asi que es su
               -- unidad la que tiene que ser de fiar. Con `coalesce` a falso: un
               -- gold viejo sin la columna no puede presumir de comparable.
               arg_min(coalesce(comparacion_fiable, false),
                       precio_unidad_cent) AS unidad_fiable,
               any_value(unidad_canon) AS unidad
          FROM comparables GROUP BY grupo_id)
    SELECT grupo_id, nombre, imagen, min_unidad, unidad, cadena_mas_barata,
           -- `fiable` es lo que la pantalla necesita para no inventarse una
           -- recomendacion: que la unidad sea de las que se pueden comparar
           -- (kg, l, m -- "ud" no lo es), que haya al menos otra cadena con quien
           -- comparar, y que los precios del grupo no se contradigan por mas de
           -- {factor}x, que es cuando el error somos nosotros (ver
           -- core/comparacion.py). Con una sola cadena no hay comparacion que
           -- hacer, y decir "no lo puedo comparar" es una respuesta.
           unidad_fiable
             AND cadenas >= 2
             AND NOT (min_unidad > 0 AND max_unidad / min_unidad > {factor}) AS fiable
      FROM porgrupo
"""


def _tarjeta(fila: tuple) -> dict:
    """Un grupo -> la tarjeta. Los datos que no estan no viajan.

    Nunca se manda `imagen: null` ni `imagen: ""`: la pantalla sabe dibujar su
    hueco cuando el campo no llega, y un campo vacio se lee como un dato roto.
    """
    tarjeta = {
        "grupo_id": fila[0], "nombre": fila[1],
        "precio_unidad_cent": fila[3], "unidad": fila[4],
        "cadena_mas_barata": fila[5], "fiable": bool(fila[6]),
    }
    if fila[2]:
        tarjeta["imagen"] = fila[2]
    return tarjeta


def tarjetas(grupo_ids: list[int]) -> dict[int, dict]:
    """La tarjeta de cada grupo pedido, por `grupo_id`.

    Los que no salen son los que no se pueden pintar: un grupo que ya no esta en
    gold (el emparejador se rehizo y esos ids no son los de hoy) o uno sin ningun
    precio con el que comparar. Devolverlos con el precio en blanco seria peor que
    no devolverlos: una tarjeta sin precio no se puede tocar para anadir nada, que
    es lo unico que hace la cuadricula.
    """
    ids = list(dict.fromkeys(grupo_ids))
    if not ids:
        return {}
    fuente = f"SELECT * FROM buscable WHERE grupo_id IN ({','.join('?' * len(ids))})"
    filas = conexion().execute(
        _TARJETAS.format(fuente=fuente, factor=FACTOR_INCREIBLE), ids).fetchall()
    # Por `grupo_id`, que es como lo busca quien llama: es el que une el historial
    # de PostgreSQL con el catalogo, que viven en dos sitios distintos.
    return {f[0]: _tarjeta(f) for f in filas}


# El catalogo se escribe sin tildes y en minusculas en `buscable.texto`
# (`strip_accents(lower(nombre || ' ' || marca))`), asi que los nombres que se
# piden aqui van igual: sin tildes y en minusculas.
_NOMBRES_A_GRUPOS = """
    WITH quiero(puesto, texto) AS (VALUES {valores}),
    casan AS (
        SELECT q.puesto, b.grupo_id,
               count(DISTINCT b.fuente) AS cadenas,
               min(b.precio_unidad_cent) AS precio
          FROM quiero q JOIN buscable b
            ON b.grupo_id IS NOT NULL AND b.precio_unidad_cent > 0
           -- El nombre del producto TIENE QUE EMPEZAR por lo pedido. Buscar la
           -- frase en cualquier parte del texto trae lo que solo la menciona:
           -- "huevos" devolvia Kinder Huevos de chocolate y "mantequilla" unas
           -- palomitas sabor mantequilla, que son los que mas cadenas venden de
           -- esas palabras. "Mantequilla sin sal" es mantequilla; "palomitas
           -- sabor mantequilla" no.
           AND strpos(strip_accents(lower(b.nombre)), q.texto) = 1
         GROUP BY q.puesto, b.grupo_id)
    SELECT puesto, grupo_id FROM (
        SELECT puesto, grupo_id,
               row_number() OVER (PARTITION BY puesto
                                  ORDER BY cadenas DESC, precio, grupo_id) AS n
          FROM casan) t
     WHERE n = 1
"""


def tarjetas_por_nombre(nombres: list[str]) -> list[dict]:
    """La tarjeta de cada nombre pedido, en el orden en que se pidio.

    El grupo elegido es **el que mas cadenas venden** de eso, y no el primero que
    salga en una busqueda. La diferencia no es cosmetica: `buscar` ordena por lo
    mas barato por unidad, que es lo correcto para buscar y terrible para esto --
    pidiendo "patatas" devuelve una tortilla de patatas y pidiendo "huevos" unos
    gofres de huevo, porque son mas baratos por kilo. El que venden todas las
    cadenas es, por definicion, la compra basica.

    Se usa para el ultimo de los tres origenes de `/api/habituales`: el dia que
    alguien abre la aplicacion por primera vez y no hay ningun historial, ni suyo
    ni de nadie.
    """
    if not nombres:
        return []
    valores = ", ".join("(?, ?)" for _ in nombres)
    args = [x for puesto, nombre in enumerate(nombres, start=1)
            for x in (puesto, nombre)]
    filas = conexion().execute(
        _NOMBRES_A_GRUPOS.format(valores=valores), args).fetchall()
    suyos = tarjetas([f[1] for f in filas])
    salida, vistos = [], set()
    for _puesto, grupo_id in sorted(filas):
        # Dos nombres pueden acabar en el mismo grupo ("leche" y "leche entera").
        # Se queda el primer puesto: dos tarjetas iguales en la cuadricula se leen
        # como un fallo de la aplicacion.
        if grupo_id in vistos or grupo_id not in suyos:
            continue
        vistos.add(grupo_id)
        salida.append(suyos[grupo_id])
    return salida


# --------------------------------------------------------------- los pasillos --

# El recorrido de la tienda, no el alfabeto. Se repite aqui a proposito y no se
# importa de `core.secciones`: la plataforma no importa nada del scraper -- son
# dos mitades que se despliegan por separado y solo se tocan a traves de los
# parquet de gold. Lo que llegue en la columna y no este en esta lista sale al
# final, que es lo que hay que hacer con lo desconocido.
ORDEN_SECCIONES = (
    "frutas-verduras", "carniceria", "pescaderia", "lacteos-huevos",
    "panaderia", "despensa", "desayuno-dulces", "aperitivos", "congelados",
    "preparados", "bebidas", "droguería-limpieza", "higiene-belleza",
    "parafarmacia", "bebe", "mascotas", "ecologico", "hogar", "promociones",
)
NOMBRES_SECCIONES = {
    "frutas-verduras": "Frutas y verduras",
    "carniceria": "Carnicería",
    "pescaderia": "Pescadería",
    "lacteos-huevos": "Lácteos y huevos",
    "panaderia": "Panadería",
    "despensa": "Despensa",
    "desayuno-dulces": "Desayuno y dulces",
    "aperitivos": "Aperitivos",
    "congelados": "Congelados",
    "preparados": "Platos preparados",
    "bebidas": "Bebidas",
    "droguería-limpieza": "Droguería y limpieza",
    "higiene-belleza": "Higiene y belleza",
    "parafarmacia": "Parafarmacia",
    "bebe": "Bebé",
    "mascotas": "Mascotas",
    "ecologico": "Ecológico",
    "hogar": "Hogar",
    "promociones": "Promociones",
}


def secciones(cadenas: list[str] | None = None) -> list[dict]:
    """Los pasillos con cuantos productos y cuantas cadenas tiene cada uno.

    En el orden del recorrido de la tienda. Un pasillo con productos de una
    sola cadena se marca: se puede mirar, pero ahi no hay nada que comparar.

    Devuelve lista vacia mientras `seccion` no haya llegado a gold -- es decir,
    hasta la primera ejecucion del pipeline posterior a `_anota_seccion`. Una
    lista vacia es una respuesta honesta; inventarse los pasillos, no.
    """
    con = conexion()
    disponibles = {f[0] for f in con.execute("DESCRIBE buscable").fetchall()}
    if "seccion" not in disponibles:
        return []
    donde, args = ["seccion IS NOT NULL"], []
    if cadenas:
        donde.append(f"fuente IN ({','.join('?' * len(cadenas))})")
        args.extend(cadenas)
    filas = con.execute(f"""
        SELECT seccion, count(*) AS n, count(DISTINCT fuente) AS cadenas,
               count(DISTINCT grupo_id) AS grupos
          FROM buscable
         WHERE {' AND '.join(donde)}
         GROUP BY seccion
    """, args).fetchall()
    orden = {s: i for i, s in enumerate(ORDEN_SECCIONES)}
    salida = [{
        "seccion": f[0],
        "nombre": NOMBRES_SECCIONES.get(f[0], f[0].replace("-", " ").capitalize()),
        "productos": f[1],
        "cadenas": f[2],
        "grupos": f[3],
        "comparable": f[2] > 1,
    } for f in filas]
    salida.sort(key=lambda s: (orden.get(s["seccion"], len(orden)), s["seccion"]))
    return salida


def pasillo_de_grupos(grupo_ids: list[int]) -> dict[int, dict]:
    """El pasillo de cada grupo, para poder agrupar una lista de la compra.

    La lista se usa **de pie, en movimiento y con una mano**, y por eso el pasillo
    va delante de cada tanda de lineas: en el pasillo se decide lo que se coge, no
    delante del movil. Esto es lo unico que hace falta para eso -- que pasillo es y
    en que punto del recorrido de la tienda cae --, y quien ordena y pinta las
    tandas es la pantalla, que es la que sabe cuantas secciones tiene la lista.

    **El pasillo es un atributo del producto, no del grupo** (`seccion` viaja por
    producto, ver `catalogo.buscar:225`), y un grupo tiene miembros de varias
    cadenas. Cuando no coinciden gana **el pasillo que mas miembros comparten**, y
    los empates se rompen por el orden del recorrido: asi un grupo no baila de
    pasillo entre dos ejecuciones sin que haya cambiado nada.

    Devuelve un diccionario vacio mientras `seccion` no haya llegado a gold. Una
    lista sin pasillos se pinta como siempre, sin encabezados; inventarse el
    pasillo de un producto, no.
    """
    ids = sorted({int(g) for g in grupo_ids if g is not None})
    if not ids:
        return {}
    con = conexion()
    disponibles = {f[0] for f in con.execute("DESCRIBE buscable").fetchall()}
    if "seccion" not in disponibles:
        return {}
    filas = con.execute(f"""
        SELECT grupo_id, seccion, count(*) AS n
          FROM buscable
         WHERE grupo_id IN ({','.join('?' * len(ids))}) AND seccion IS NOT NULL
         GROUP BY grupo_id, seccion
    """, ids).fetchall()
    orden = {s: i for i, s in enumerate(ORDEN_SECCIONES)}
    elegido: dict[int, tuple] = {}
    for grupo_id, seccion, n in filas:
        # Mas miembros primero; a igualdad, el que se recorre antes en la tienda.
        clave = (-n, orden.get(seccion, len(orden)), seccion)
        if grupo_id not in elegido or clave < elegido[grupo_id][0]:
            elegido[grupo_id] = (clave, seccion)
    return {
        g: {"seccion": s,
            "pasillo": NOMBRES_SECCIONES.get(s, s.replace("-", " ").capitalize()),
            "pasillo_orden": orden.get(s, len(orden))}
        for g, (_, s) in elegido.items()
    }


def con_pasillos(lineas: list[dict]) -> list[dict]:
    """Las lineas, cada una con su pasillo. **No reordena nada.**

    Se anade el pasillo a la linea en vez de mandar una lista de pasillos aparte
    porque la pantalla necesita las dos cosas juntas: al pintar una linea tiene que
    saber si empieza una tanda nueva, y con dos listas eso es cruzar indices por
    `grupo_id` en el navegador, que es donde peor se depura.

    Una linea sin pasillo **no lleva las claves**, no viaja con `null`: la pantalla
    distingue "no lo se" de "es de este pasillo" mirando si la clave esta.
    """
    pasillos = pasillo_de_grupos([ln.get("grupo_id") for ln in lineas])
    salida = []
    for linea in lineas:
        pasillo = pasillos.get(linea.get("grupo_id"))
        salida.append(linea | pasillo if pasillo else linea)
    return salida


# ------------------------------------------- la linea y su grupo, ¿son lo mismo? ---

def _mismo_producto(nombre: str, nombres_del_grupo: list[str]) -> bool:
    """¿El grupo sigue siendo el producto que la linea dice ser?

    Se comparan **las palabras significativas** (`core.matching.tokens`: sin
    articulos, sin numeros, con los plurales fuera), y vale la contencion en
    cualquiera de los dos sentidos: «Leche entera» esta dentro de «Leche entera
    Hacendado» y al reves, porque las cadenas anaden y quitan marcas y formatos del
    nombre y eso no cambia el producto.

    Un nombre sin palabras significativas no se juzga: se da por bueno. Acusar sin
    pruebas seria peor que no mirar.
    """
    from core.matching import tokens

    mio = tokens(nombre or "")
    if not mio:
        return True
    for otro in nombres_del_grupo:
        suyo = tokens(otro or "")
        if mio <= suyo or suyo <= mio:
            return True
    return False


def lineas_movidas(lineas: list[dict]) -> set[str]:
    """Los ids de las lineas cuyo grupo **ya no es** el producto que la linea dice.

    **Esto es el sintoma de que `grupo_id` es un ordinal, no una identidad.** El
    emparejador numera los grupos en el orden en que aparecen los productos
    (`core.matching.agrupar_enlaces`, el `renombre.setdefault(raiz(i), len(renombre))`),
    asi que **cada pasada puede renumerarlos**: hoy el grupo 526 es una barra de
    labios REVLON y ayer era la leche entera. Las listas, los favoritos y los avisos
    de PostgreSQL guardan ese numero.

    Medido el 28 de septiembre de 2026, con los datos de casa: las tres lineas de la
    lista de la cuenta de pruebas apuntaban a 526, 10226 y 11627, y hoy 526 es el
    pintalabios y 10226 las barritas: la pantalla ponia **la leche entera en el
    pasillo de higiene y belleza** y le ponia el precio del pintalabios. Y los avisos
    decian «TWIX ... 0,96 EUR/l», que es el precio de la leche.

    La migracion de verdad esta apuntada desde el 22 de septiembre (`docs/MODELO.md`,
    `docs/DIAGNOSTICO-MATCHING.md` §21: pasar listas y favoritos al `producto_id`
    estable). Mientras eso no este, lo que no puede pasar es **mentir**: una linea
    movida no se pinta con el precio y el pasillo de otro producto, se dice que se ha
    movido y se deja volver a buscarla.
    """
    ids = sorted({int(ln["grupo_id"]) for ln in lineas if ln.get("grupo_id") is not None})
    if not ids:
        return set()
    con = conexion()
    marcas = ",".join("?" * len(ids))
    filas = con.execute(
        f"SELECT DISTINCT grupo_id, nombre FROM buscable WHERE grupo_id IN ({marcas})",
        ids).fetchall()
    por_grupo: dict[int, list[str]] = {}
    for grupo, nombre in filas:
        por_grupo.setdefault(int(grupo), []).append(nombre or "")
    movidas: set[str] = set()
    for linea in lineas:
        grupo = linea.get("grupo_id")
        if grupo is None:
            continue
        # Un grupo que ya no existe es el caso extremo del mismo fallo: la linea
        # apunta a nada.
        if not _mismo_producto(linea.get("nombre_visto") or "", por_grupo.get(int(grupo), [])):
            movidas.add(str(linea["id"]))
    return movidas


# ------------------------------------------------------------ ficha de grupo --

def _calidad_y_origen(calidad, calidad_origen) -> tuple:
    """La letra de calidad **y de donde salio**. Pura, para poder probarla.

    *Devuelve `(letra, procedencia)`.*

    **Las dos procedencias que importan, y por que no son lo mismo:**

      - `ingredientes`: los leyo el colector de **la ficha que publica la tienda**.
      - `ingredientes_off`: los **dedujo Open Food Facts** -- *la tienda **no** los publica*.

    *Y `precio` no es calidad: es gama.* **Se devuelve `None` en `letra` para que no se confundan** --
    *mezclarlas produce la conclusion falsa de que lo barato es peor, y eso ya estaba resuelto.*
    """
    if not calidad or not calidad_origen:
        return (None, None)
    if calidad_origen.startswith("ingredientes"):
        # **Y el origen viaja con la letra**, no dentro del texto del sello: *asi la pantalla puede decir
        # la verdad sin adivinarla de una frase.*
        return (calidad, calidad_origen)
    # *`precio` y cualquier otro origen no dan calidad.*
    return (None, None)


def _por_escurrido(f: dict) -> bool:
    """¿El precio por unidad de esta fila esta calculado sobre el peso escurrido?

    Es la misma condicion que aplica `projects.cesta.pipeline.cantidad_para_el_precio`, y se
    repite aqui a proposito tan corta: la interfaz solo puede decir «EUR/kg escurrido» cuando
    de verdad se dividio por el. Etiquetar una cuenta que no es la que se hizo seria peor que
    no etiquetar nada.
    """
    esc, cantidad = f.get("peso_escurrido_g"), f.get("cantidad")
    return bool(esc and cantidad and 0 < esc < cantidad * 1000 * 0.98)


def grupo(grupo_id: int) -> dict | None:
    """Todo lo que la ficha necesita: los miembros, los equivalentes y la curva.

    Ojo con `promo_hasta`: es un ``TIMESTAMP WITH TIME ZONE`` y se pide **ya
    convertido a texto**. DuckDB, para devolverlo como objeto de fecha, importa
    `pytz` por debajo, y la imagen de la API no lo trae -- ni debe, porque la API
    no maneja zonas horarias. Sin el `::VARCHAR` la pantalla de grupo, que es la
    pantalla clave del encargo, daba 500 en cuanto un miembro tenia promocion con
    fecha; y era la mayoria. Lo vigila `test_la_ficha_del_grupo_no_necesita_pytz`,
    que esconde el modulo para reproducir lo que pasa dentro del contenedor.
    """
    con = conexion()
    disponibles = {f[0] for f in con.execute("DESCRIBE grupos").fetchall()}
    nuevas = ", ".join(
        # El unico que necesita conversion: los demas son texto o numeros.
        f"{c}::VARCHAR AS {c}" if c == "promo_hasta"
        else (c if c in disponibles else f"NULL AS {c}")
        for c in ("sellos", "sellos_origen", "certificados", "conservacion",
                  "es_marca_propia", "nutricion", "nutricion_por", "envase",
                  "descripcion", "tipo_producto", "dias_caducidad", "peso_neto_g",
                  "peso_escurrido_g",
                  "grado_alcohol", "promo_hasta", "promo_club",
                  "promo_solo_online", "es_alcohol",
                  "es_recall", "peso_variacion_pct", "distintivo", "advertencias",
                  "unidades_pack",
                  # El Eco-Score es el campo que mejor cubre Open Food Facts -- 354.831 de sus
                  # 355.038 codigos, el 99,9 % -- y hasta el 9 de octubre de 2026 se descargaba y
                  # no lo leia nadie. Va aqui, con las demas: la cadena que se interpola en el
                  # SELECT pide "solo si estan", asi que un gold de antes sigue funcionando.
                  "ecoscore",
                  # Los nutrientes por 100 g, de Open Food Facts. Cuatro de las cinco cadenas no
                  # publican nutricion: esto es lo que hace que la aplicacion de calorias calcule.
                  "kcal_100g", "hidratos_100g", "proteinas_100g", "grasas_100g",
                  "grasas_sat_100g", "azucares_100g", "sal_100g"))
    # **Por nombre, no por posicion.** Aqui habia indices (`f[35]`, `f[36]`...) y el dia que
    # alguien anadio una columna a `nuevas` -- `es_recall` entro despues -- los de detras se
    # quedaron **uno a la izquierda** sin que nada avisara. Medido el 24 de septiembre de 2026
    # sobre el gold del 23, lo que aquello costaba:
    #
    #     482 grupos daban **500** (su producto mas barato tiene `advertencias`, que es texto,
    #         y el codigo hacia `(f[40] or 0) > 1`: comparar texto con un numero revienta)
    #     3.844 productos con alcohol salian marcados como **retirados** (`es_recall` leia
    #         `es_alcohol`), que es la mentira mas cara que puede decir esta pantalla
    #     341 promociones "solo online" salian como alcohol, y con eso el filtro de
    #         "sin alcohol" escondia productos que no lo son
    #     544 productos ensenaban su `peso_variacion_pct` en el sitio del `distintivo`
    #     y `unidades_pack` no llegaba nunca a la pantalla (leia `advertencias`)
    #
    # Con nombres, anadir una columna no puede mover ninguna otra. La lista de nombres la da
    # la propia consulta (`cursor.description`), asi que el codigo y el `SELECT` no pueden
    # separarse ni por descuido.
    consulta = con.execute(f"""
        SELECT fuente, id_fuente, nombre, marca, cantidad, unidad_canon,
               precio_cent, precio_unidad_cent, comparacion_fiable,
               calidad, calidad_origen, nutriscore, nova, ean,
               imagen, alergenos, ingredientes, origen, promo_txt, url,
               {nuevas}
          FROM grupos WHERE grupo_id = ? AND precio_unidad_cent > 0
         ORDER BY precio_unidad_cent
    """, [grupo_id])
    nombres = [d[0] for d in consulta.description]
    miembros = [dict(zip(nombres, fila, strict=True)) for fila in consulta.fetchall()]
    if not miembros:
        return None

    def prod(f: dict) -> dict:
        return {    "fuente": f["fuente"], "id_fuente": f["id_fuente"],
            "producto_id": f"{f['fuente']}:{f['id_fuente']}",
            "nombre": f["nombre"], "marca": f["marca"], "cantidad": f["cantidad"],
            "unidad": f["unidad_canon"],
            "precio_cent": f["precio_cent"], "precio_unidad_cent": f["precio_unidad_cent"],
            "comparable": bool(f["comparacion_fiable"]),
            # La letra sale de leer ingredientes o de ordenar por precio. Si
            # sale del precio NO es calidad: es gama, y se dice como tal. En el
            # 77 % de los casos es lo segundo, y mezclarlas produce la
            # conclusion falsa de que lo barato es peor.
            "calidad": _calidad_y_origen(f["calidad"], f["calidad_origen"])[0],
            # **Y DE DONDE SALIO, que es lo que faltaba.** *`calidad_origen` tiene DOS valores que
            # significan cosas distintas* -- `ingredientes` (leidos de la ficha que publica la tienda)
            # e `ingredientes_off` (**deducidos por Open Food Facts**) --, *y el sello decia «leida de
            # ingredientes» **para las dos**.*
            #
            # *El caso medido el 12 de octubre de 2026*: **el President de Carrefour del grupo 11627
            # tiene `calidad_origen=ingredientes_off`, nota 100 y letra A, con su columna nativa
            # `ingredientes` VACIA.** *No es un parser roto: **la valoracion es enriquecida**, y decir
            # «leida de ingredientes» se la atribuye a Carrefour, que no los publico.*
            #
            # **A06 lo pide con estas palabras: «datos enriquecidos no se atribuyen al supermercado».**
            # *Por eso viaja el origen en su propio campo y no dentro del texto del sello* -- *asi la
            # pantalla puede decir la verdad sin tener que adivinarla de una frase.*
            "calidad_de": _calidad_y_origen(f["calidad"], f["calidad_origen"])[1],
            "gama": f["calidad"] if f["calidad_origen"] == "precio" else None,
            "nutriscore": f["nutriscore"], "nova": f["nova"], "ean": f["ean"],
            "ecoscore": f["ecoscore"],
            # Por 100 g. La ficha dira tambien por racion cuando haya racion; el dato base es este.
            "kcal_100g": f["kcal_100g"], "hidratos_100g": f["hidratos_100g"],
            "proteinas_100g": f["proteinas_100g"], "grasas_100g": f["grasas_100g"],
            "grasas_sat_100g": f["grasas_sat_100g"], "azucares_100g": f["azucares_100g"],
            "sal_100g": f["sal_100g"],
            "imagen": f["imagen"], "alergenos": f["alergenos"],
            "ingredientes": f["ingredientes"],
            "origen": f["origen"], "promo": f["promo_txt"], "url": f["url"],
            # Cuantas unidades hay que comprar para que la oferta valga, cuando la cadena lo
            # dice en numero (Alcampo, 1.639 productos de hoy). La ficha lo enseña porque es
            # una condicion del precio: «2ª unidad -50 %» no es el precio de una. **No entra
            # en ninguna cuenta**, y por eso va aparte y no como `promo_txt`.
            "promo_unidades": f.get("promo_unidades_minimas"),
            # Los sellos van con su procedencia: no es lo mismo un certificado
            # auditado que una palabra en el nombre del producto. La interfaz lo
            # dice, para no dar por seguro lo que no lo es.
            "sellos": (f["sellos"] or "").split(",") if f["sellos"] else [],
            "sellos_origen": f["sellos_origen"],
            "certificados": (f["certificados"] or "").split(",") if f["certificados"] else [],
            "conservacion": f["conservacion"], "es_marca_propia": f["es_marca_propia"],
            "nutricion": json.loads(f["nutricion"]) if f["nutricion"] else None,
            "nutricion_por": f["nutricion_por"], "envase": f["envase"],
            "descripcion": f["descripcion"],
            "tipo_producto": f["tipo_producto"], "dias_caducidad": f["dias_caducidad"],
            "peso_neto_g": f["peso_neto_g"],
            # El peso escurrido, cuando la cadena lo publica (hoy solo Mercadona, 179
            # productos: conservas y tarros). **Este es el peso sobre el que se calcula el
            # precio por kilo cuando existe**, porque es lo que se come y porque es la base
            # que usan las otras cadenas: la ventresca de Mercadona declara 111 g y dice que
            # el escurrido son 78 g, y Alcampo, Carrefour y DIA venden la misma lata
            # declarando 73 g. Medido el 26 de septiembre de 2026 y reproducible con
            # `projects.cesta.auditar_escurrido`: dividiendo por lo declarado, Mercadona
            # salia en el 59 % de la mediana de las otras cadenas (1 de 18 grupos dentro del
            # 20 %); por el escurrido, en el 98 % (13 de 18).
            "peso_escurrido_g": f["peso_escurrido_g"],
            "precio_por_escurrido": _por_escurrido(f),
            "grado_alcohol": f["grado_alcohol"],
            # Ya viene como texto de la consulta (ver el docstring): los diez
            # primeros caracteres son la fecha, "2026-09-25".
            "promo_hasta": f["promo_hasta"][:10] if f["promo_hasta"] else None,
            # Una oferta de tarjeta NO baja lo que pagas en caja: se acumula en
            # un monedero. La ficha lo dice con esas palabras.
            "promo_club": bool(f["promo_club"]),
            "promo_solo_online": bool(f["promo_solo_online"]),
            "es_alcohol": bool(f["es_alcohol"]), "es_recall": bool(f["es_recall"]),
            "peso_variacion_pct": f["peso_variacion_pct"], "distintivo": f["distintivo"],
            "advertencias": (f["advertencias"] or "").split(" | ") if f["advertencias"] else [],
            "unidades_pack": f["unidades_pack"] if (f["unidades_pack"] or 0) > 1 else None,
        }

    productos = [prod(f) for f in miembros]
    # `producto_id` viaja en cada punto del historico. Sin el, un grupo con dos
    # productos de la misma cadena da dos series que empiezan por el mismo
    # (cadena, fecha) y ninguna se puede pintar: no se sabe de cual de los dos
    # es cada precio. La interfaz lo decia en pantalla en vez de dibujar algo
    # que podria estar mezclando dos productos distintos.
    # **La unidad viaja en cada punto del historico**, y llego tarde. Con el precio por
    # unidad y la fecha no se puede decir *"es el precio mas bajo de los 18 dias que
    # tenemos"*: si la unidad cambio por el camino (`kg` un dia y `ud` otro), el minimo
    # de esa serie no significa nada, y la regla del proyecto es la misma que en las
    # alertas -- *"si la unidad cambio, no es una bajada"* (`api/alertas.py`). Se manda
    # y decide la pantalla (`logica/curva.ts`), que es donde se lee la frase.
    #
    # Y se comprueba si la columna esta, como se hace mas arriba con las de `grupos`: la
    # API tiene que poder servir un gold viejo sin caerse (es el caso de "el scraper fallo
    # y se sigue sirviendo lo de ayer", escrito en `docker-compose.yml`). Si no esta, el
    # punto viaja sin unidad y la pantalla **no dice la frase**: no puede.
    columnas_diario = {f[0] for f in con.execute("DESCRIBE diario").fetchall()}
    la_unidad = "unidad_canon" if "unidad_canon" in columnas_diario else "NULL AS unidad_canon"
    serie = con.execute(f"""
        SELECT producto_id, fuente, fecha::VARCHAR, precio_unidad_cent, {la_unidad}
          FROM diario
         WHERE producto_id IN (SELECT fuente || ':' || id_fuente FROM grupos WHERE grupo_id = ?)
         ORDER BY fecha
    """, [grupo_id]).fetchall()

    # **La unidad que decide, y el ahorro medido dentro de ella.**
    #
    # Antes esto era `productos[0]` y `productos[-1]` -- el minimo y el maximo de TODO el
    # grupo --, y eso cruza unidades: restar EUR/kg de EUR/ud no es una diferencia de
    # precio, es un disparate. La regla esta escrita en tres sitios del proyecto
    # (`core/comparacion.py`, `resumen.py`, `api/alertas.py`: *"si la unidad cambio, no es
    # una bajada"*) y la ficha del grupo se la saltaba.
    #
    # Medido sobre el gold del 23 de septiembre de 2026, antes y despues, con los mismos
    # topes que usa el resumen (`resumen.TOPE_CREIBLE` 2.900 % y `TOPE_LLAMATIVO` 200 %):
    #
    #     grupos que mezclan unidades                    125 de 39.592
    #     grupos comparables (mas de una cadena)    8.771  ->  7.918
    #       diferencias imposibles (> 2.900 %)         54  ->  0
    #       diferencias llamativas (> 200 %)          370  ->  226
    #     mediana de la diferencia                   16,5 %  ->  16,0 %
    #
    # Es decir: la mediana no se mueve -- el apaño es para la cola absurda --, **54
    # numeros imposibles dejan de salir en pantalla**, y los grupos que se quedan sin
    # comparacion (853) pierden un numero que no era comparable en vez de ensenarlo mal.
    # El caso que lo destapo, en un navegador: la ficha de `dia:147509` (azafran en un
    # pote de 0,4 g) decia *«te ahorras 6.872,01 EUR/kg»* comparando su precio por kilo
    # con el de un bote medido en unidades.
    #
    # La unidad que decide es **la que comparten mas cadenas**, que es la misma regla que
    # usa `alertas._mejor_de_cada_grupo` en su SQL (`ORDER BY count(DISTINCT fuente)
    # DESC, count(*) DESC`): asi el precio por unidad que se ensena es el que de verdad
    # se puede comparar entre cadenas.
    def _unidad_dominante(filas: list[dict]) -> str | None:
        cadenas: dict[str, set[str]] = {}
        cuantos: dict[str, int] = {}
        for p in filas:
            if p["unidad"] and p["precio_unidad_cent"]:
                cadenas.setdefault(p["unidad"], set()).add(p["fuente"])
                cuantos[p["unidad"]] = cuantos.get(p["unidad"], 0) + 1
        if not cadenas:
            return filas[0]["unidad"] if filas else None
        return max(cadenas, key=lambda u: (len(cadenas[u]), cuantos[u]))

    unidad = _unidad_dominante(productos)
    # Y dentro de la unidad, **solo los precios en los que se puede confiar**: es la
    # misma regla que `resumen.ahorro()` (`comparacion_fiable` y `precio_comparable`), que
    # lleva desde el primer dia sin contar las filas en disputa. Si solo hay uno, no hay
    # ahorro que anunciar: cero, y la pantalla no pinta la frase.
    del_mismo = [p for p in productos
                 if p["unidad"] == unidad and p["precio_unidad_cent"] and p["comparable"]]
    barato = del_mismo[0]["precio_unidad_cent"] if del_mismo else None
    caro = del_mismo[-1]["precio_unidad_cent"] if del_mismo else None

    # *** `ahorro_pct` ES LA HORQUILLA DEL GRUPO, *y no el ahorro de un articulo*. ***
    #
    # *Esto filtra por **unidad** y por **comparable**, y **no por EAN**.* *Asi que dice cuanto
    # va del mas barato al mas caro **del grupo de equivalencias**, que pueden ser articulos
    # distintos: el 18/10/2026, en la ficha del azafran `dia/147509`, daba 41 % comparando el
    # **Pote** con el **Hacendado**.*
    #
    # *** No se cambia su significado ***, *porque seis pantallas lo usan como horquilla
    # (`Grupo.tsx`, `Favoritos.tsx`, `TablaResultados.tsx`, `LoQueSeCompra.tsx`, `Panel.tsx`) y
    # cambiarlo las romperia en silencio.* *Lo que se añade es **el dato que faltaba**: por cada
    # producto, cuanto se ahorra contra **su mismo articulo** -- mismo EAN y misma base.*
    #
    # *Sin EAN no se afirma nada: `ahorro_exacto_pct` queda en `None`, que no es cero.*
    def _exacto(p: dict) -> tuple[float | None, int | None]:
        """*El ahorro contra las ofertas del **mismo EAN** y la **misma base**.*"""
        su_ean = (p.get("ean") or "").strip()
        suyo = p.get("precio_unidad_cent")
        if not su_ean or not suyo or not p.get("comparable"):
            return None, None
        iguales = [
            q["precio_unidad_cent"]
            for q in productos
            if (q.get("ean") or "").strip() == su_ean
            and q.get("unidad") == p.get("unidad")
            and q.get("precio_unidad_cent")
            and q.get("comparable")
        ]
        if len(iguales) < 2:
            return None, None  # *no hay con que comparar su propio articulo*
        el_mas_barato = min(iguales)
        if suyo <= el_mas_barato:
            return 0.0, 0
        return (
            round(100 * (suyo - el_mas_barato) / el_mas_barato, 1),
            int(suyo - el_mas_barato),
        )

    for _p in productos:
        _pct, _cent = _exacto(_p)
        _p["ahorro_exacto_pct"] = _pct
        _p["ahorro_exacto_cent"] = _cent
    return {
        "grupo_id": grupo_id,
        "nombre": productos[0]["nombre"],
        "imagen": next((p["imagen"] for p in productos if p["imagen"]), None),
        "unidad": unidad,
        "productos": productos,
        "cadenas": len({p["fuente"] for p in productos}),
        # Con una sola cadena en esa unidad no hay ahorro que anunciar: cero, y la
        # pantalla dice "sin comparacion" o no lo pinta.
        "ahorro_pct": round(100 * (caro - barato) / barato, 1) if barato else 0.0,
        "ahorro_cent": (caro - barato) if barato is not None else 0,
        # Y con cuantas cadenas se puede comparar **de verdad**: las que miden este
        # producto en esa unidad. Es lo que la frase necesita para no contar cadenas
        # que estan midiendo otra cosa.
        "cadenas_comparables": len({p["fuente"] for p in del_mismo}),
        "serie": [{"producto_id": s[0], "fuente": s[1], "fecha": s[2],
                   "precio_unidad_cent": s[3], "unidad_canon": s[4]}
                  for s in serie],
    }


def explicacion(grupo_id: int) -> dict | None:
    """Por que los productos de este grupo acabaron juntos, o None si no se sabe.

    El dato ya esta calculado: sale de `equivalencia.parquet` de la ultima pasada
    del matching, que trae un par aceptado por fila con su metodo, su confianza y
    sus `features`. No se recalcula el parecido aqui: el emparejador ya decidio
    los grupos, y deducirlos otra vez daria una segunda version de la misma
    verdad -- la que ensena la ficha no seria la que formo el grupo.

    Devuelve **None** cuando no hay nada que contar: un grupo de un solo
    producto, uno que no tiene ningun par entre sus miembros, o un gold sin
    ninguna pasada de matching. La ruta omite el campo en ese caso. Un
    `{"pares": 0}` se leeria como "se emparejaron por nada", y eso no es lo mismo
    que "no lo sabemos".

    Los grupos se forman por transitividad, asi que un miembro puede no tener
    ningun par directo con otro. Eso no es un error, y se dice en
    `productos_sin_par`.
    """
    gold = AJUSTES.gold
    eids = _ejecuciones(gold)
    if not eids:
        return None
    # La misma pasada que usa el panel de auditoria, y a proposito: si la ficha y
    # el panel pudieran estar mirando pasadas distintas, ninguno de los dos
    # explicaria el grupo que se esta viendo.
    eid = eids[-1]
    ruta = gold / CARPETA_MATCHING / f"ejecucion={eid}" / "equivalencia.parquet"
    if not ruta.exists():
        return None

    con = conexion()
    # `mios` son los productos que ENSENA la ficha: `grupo()` solo lista los que
    # tienen precio, y la explicacion tiene que hablar de los mismos productos
    # que se ven en la pantalla, no de otros que esten en el grupo sin precio que
    # comparar. El `DISTINCT` no sobra: una clave repetida multiplicaria los
    # pares por el JOIN.
    total = con.execute(
        "SELECT count(DISTINCT fuente || ':' || id_fuente) FROM grupos "
        "WHERE grupo_id = ? AND precio_unidad_cent > 0", [grupo_id]).fetchone()[0]
    filas = con.execute(f"""
        WITH mios AS (
            SELECT DISTINCT fuente || ':' || id_fuente AS producto_id
              FROM grupos WHERE grupo_id = ? AND precio_unidad_cent > 0
        )
        SELECT e.producto_a, e.producto_b, e.nivel, e.metodo, e.confianza, e.features
          FROM read_parquet('{_p(ruta)}') e
          JOIN mios a ON e.producto_a = a.producto_id
          JOIN mios b ON e.producto_b = b.producto_id
    """, [grupo_id]).fetchall()
    if not filas:
        return None

    # Un par puede venir DOS veces en el fichero -- una por EAN y otra por nombre
    # -- y son dos pruebas del mismo hecho, no dos pares: contar filas diria que
    # el grupo 11580 tiene 44 pares cuando tiene 42. De cada par se guarda su
    # prueba mas fuerte, que es la que lo acepto.
    fuerza: dict[tuple[str, str], float] = {}
    rasgos: dict[tuple[str, str], str] = {}
    for a, b, _nivel, _metodo, confianza, features in filas:
        # El fichero no promete el orden de los dos lados: se ordena la clave
        # para que (a, b) y (b, a) sean el mismo par.
        clave = (a, b) if a <= b else (b, a)
        if clave not in fuerza or confianza > fuerza[clave]:
            fuerza[clave] = confianza
            rasgos[clave] = features

    valores = list(fuerza.values())
    niveles = sorted({f[2] for f in filas if f[2]})
    metodos = sorted({f[3] for f in filas if f[3]})
    # A igualdad de confianza, el primero por clave: el par mas flojo de un grupo
    # no puede salir distinto segun en que orden vengan las filas del parquet.
    flojo = min(fuerza, key=lambda p: (fuerza[p], p))

    salida: dict = {"ejecucion": eid, "pares": len(fuerza)}
    # Los niveles y los metodos que haya, TODOS. Si el grupo se junto por varios
    # caminos, elegir uno seria contar la mitad de la historia, y esto es
    # justamente la historia. Nada viaja vacio: si la columna no dijera nada, el
    # campo no se manda.
    if niveles:
        salida["nivel"] = "+".join(niveles)
    if metodos:
        salida["metodo"] = "+".join(metodos)
    salida["confianza_minima"] = round(min(valores), 4)
    salida["confianza_media"] = round(sum(valores) / len(valores), 4)
    # El par mas flojo es el que sostiene el grupo con menos evidencia, o sea el
    # que hay que poder auditar. Se dice cual es para que `features` no sea un
    # JSON sin dueno: son las suyas, tal y como las escribio el pipeline.
    salida["par_mas_flojo"] = f"{flojo[0]} · {flojo[1]}"
    if rasgos.get(flojo):
        salida["features"] = rasgos[flojo]
    # Las filas del fichero solo se dicen cuando no coinciden con los pares, que
    # es cuando un par se encontro por dos caminos. Cuando son iguales, repetir
    # el mismo numero seria ruido en una tabla de dos columnas.
    if len(filas) != len(fuerza):
        salida["enlaces"] = len(filas)
    # La transitividad: miembros del grupo sin ningun par directo con otro. Solo
    # se dice si hay alguno; un cero aqui no es un dato, es la ausencia del
    # problema, y los campos vacios no se mandan.
    sin_par = total - len({p for clave in fuerza for p in clave})
    if sin_par > 0:
        salida["productos_sin_par"] = sin_par
    return salida


def producto(producto_id: str) -> dict | None:
    fuente, _, id_fuente = producto_id.partition(":")
    fila = conexion().execute("""
        SELECT grupo_id, nombre, marca, cantidad, unidad_canon, precio_cent,
               precio_unidad_cent, comparacion_fiable, nutriscore, peso_escurrido_g
          FROM grupos WHERE fuente = ? AND id_fuente = ?
    """, [fuente, id_fuente]).fetchone()
    if not fila:
        return None
    return {"producto_id": producto_id, "fuente": fuente, "grupo_id": fila[0],
            "nombre": fila[1], "marca": fila[2], "cantidad": fila[3],
            "unidad": fila[4], "precio_cent": fila[5],
            "precio_unidad_cent": fila[6], "comparable": bool(fila[7]),
            "nutriscore": fila[8],
            "peso_escurrido_g": fila[9],
            "precio_por_escurrido": _por_escurrido(
                {"peso_escurrido_g": fila[9], "cantidad": fila[3]})}


# El escaner de codigo de barras (docs/API.md, tarea 8).
#
# Es la funcion que mas se usa en el pasillo y la que mas rapido contesta la
# pregunta util: *esto que tengo en la mano, esta mas barato en otro sitio?*.
# Se acepta el codigo como lo lea el lector: con espacios, con guiones o con
# ceros a la izquierda (EAN-13 y UPC-12 son el mismo numero escrito distinto).
_MIN_DIGITOS = 8
_MAX_DIGITOS = 14


def normaliza_ean(codigo: str | None) -> str | None:
    """Lo que el lector haya leido -> digitos sin ceros a la izquierda, o None.

    Los ceros de delante se quitan porque la misma caja es ``8410655002410`` en
    EAN-13 y ``08410655002410`` segun como venga; y en la base se guardan del
    mismo modo, para que las dos formas encuentren lo mismo.
    """
    digitos = re.sub(r"\D", "", str(codigo or ""))
    if not (_MIN_DIGITOS <= len(digitos) <= _MAX_DIGITOS):
        return None
    limpio = digitos.lstrip("0")
    return limpio if len(limpio) >= _MIN_DIGITOS else None


def por_ean(codigo: str) -> dict:
    """La ficha de un producto por su codigo de barras, y su comparacion.

    `codigo` tiene que venir ya normalizado con `normaliza_ean`; el 400 por un
    codigo mal formado lo da la ruta, que es donde toca.
    """
    fila = conexion().execute("""
        SELECT grupo_id, fuente, id_fuente, nombre, marca, cantidad, unidad_canon,
               precio_cent, precio_unidad_cent, comparacion_fiable, nutriscore
          FROM grupos
         WHERE ltrim(regexp_replace(ean, '[^0-9]', '', 'g'), '0') = ?
         ORDER BY precio_unidad_cent
         LIMIT 1
    """, [codigo]).fetchone()
    comun = {"fecha_datos": fecha_de_gold()}
    if not fila:
        return comun | {
            "encontrado": False, "motivo": "desconocido",
            "sugerencia": "Puede ser marca propia de Alcampo o Aldi, que no "
                          "publican codigo de barras.",
        }
    grupo_id = fila[0]
    g = grupo(grupo_id) if grupo_id is not None else None
    # `comparacion` es null, no una lista vacia, cuando el producto solo esta en
    # una cadena. Vacia se lee como "he mirado y no hay nada mas barato"; null se
    # lee como "no puedo comparar". No es lo mismo.
    comparacion = None
    if g and len(g["productos"]) > 1:
        barato = min(p["precio_unidad_cent"] for p in g["productos"])
        comparacion = [
            {"fuente": p["fuente"], "precio_cent": p["precio_cent"],
             "precio_unidad_cent": p["precio_unidad_cent"],
             "diferencia_pct": round(100 * (p["precio_unidad_cent"] - barato)
                                     / barato, 1) if barato else None}
            for p in g["productos"]
        ]
    return comun | {
        "encontrado": True,
        "producto": {
            "producto_id": f"{fila[1]}:{fila[2]}", "fuente": fila[1],
            "id_fuente": fila[2], "nombre": fila[3], "marca": fila[4],
            "cantidad": fila[5], "unidad": fila[6], "precio_cent": fila[7],
            "precio_unidad_cent": fila[8], "comparable": bool(fila[9]),
            "nutriscore": fila[10],
        },
        "grupo_id": grupo_id,
        "comparacion": comparacion,
    }


# --- El panel de auditoria del matching -------------------------------------
#
# Lo que el encargo pide y lo que NO pide. Pide **explicabilidad**: que cada par
# aceptado pueda auditarse y se vea por que se acepto. NO pide botones de
# aprobar ni de rechazar: en este proyecto no hay validacion humana, nunca, y por
# eso aqui no hay ni un endpoint de escritura. Esto solo lee.
#
# Lee de `data/gold/matching/`, que es el modelo versionado de la Fase 1: cada
# pasada en su carpeta, con sus metricas y sus pares con `features`. Nada se
# sobrescribe, asi que se puede comparar una pasada con la anterior, que es la
# metrica de estabilidad que pide el plan.


def _ejecuciones(gold: Path) -> list[str]:
    raiz = gold / CARPETA_MATCHING
    return sorted(p.name.split("=")[1] for p in raiz.glob("ejecucion=*") if p.is_dir())


def _metricas_de(ejecucion_id: str, gold: Path) -> dict[str, float]:
    ruta = gold / CARPETA_MATCHING / f"ejecucion={ejecucion_id}" / "metrica.parquet"
    if not ruta.exists():
        return {}
    filas = conexion().execute(
        f"SELECT metrica, valor FROM read_parquet('{_p(ruta)}')").fetchall()
    return {m: v for m, v in filas}


def matching(limite: int = 20) -> dict:
    """Las metricas de la ultima pasada y una muestra de pares con su motivo."""
    gold = AJUSTES.gold
    eids = _ejecuciones(gold)
    if not eids:
        return {"fecha_datos": fecha_de_gold(), "ultima": None, "metricas": [],
                "anterior": None, "cambios": None, "pares": [], "ejecuciones": []}
    eid = eids[-1]
    carpeta = gold / CARPETA_MATCHING / f"ejecucion={eid}"
    resumen = {}
    ficha = carpeta / "resumen.json"
    if ficha.exists():
        try:
            resumen = json.loads(ficha.read_text(encoding="utf-8"))
        except ValueError:
            resumen = {}
    metricas = _metricas_de(eid, gold)
    anterior = eids[-2] if len(eids) > 1 else None
    cambios = None
    if anterior:
        previas = _metricas_de(anterior, gold)
        cambios = [
            {"metrica": m, "antes": previas.get(m), "ahora": v,
             "delta": round(v - previas.get(m, 0.0), 4)}
            for m, v in metricas.items()
        ]

    pares = []
    ruta = carpeta / "equivalencia.parquet"
    if ruta.exists():
        filas = conexion().execute(
            f"SELECT producto_a, producto_b, fuente_a, fuente_b, nivel, metodo, "
            f"       confianza, features "
            f"  FROM read_parquet('{_p(ruta)}') LIMIT {int(limite)}").fetchall()
        # Los nombres no viajan en la equivalencia (alli solo hay claves
        # estables), asi que se piden al catalogo de una vez.
        claves = [f[0] for f in filas] + [f[1] for f in filas]
        nombres = {}
        if claves:
            marcadores = ",".join("?" * len(claves))
            nombres = {
                f"{f[0]}:{f[1]}": f[2]
                for f in conexion().execute(
                    f"SELECT fuente, id_fuente, nombre FROM grupos "
                    f"WHERE fuente || ':' || id_fuente IN ({marcadores})",
                    claves).fetchall()
            }
        for f in filas:
            try:
                rasgos = json.loads(f[7])
            except (TypeError, ValueError):
                rasgos = {}
            pares.append({
                "producto_a": f[0], "producto_b": f[1],
                "nombre_a": nombres.get(f[0]), "nombre_b": nombres.get(f[1]),
                "fuente_a": f[2], "fuente_b": f[3], "nivel": f[4],
                "metodo": f[5], "confianza": f[6], "features": rasgos,
            })
    return {
        "fecha_datos": fecha_de_gold(),
        "ultima": {"ejecucion_id": eid, "version_modelo": resumen.get("version_modelo"),
                   "productos": resumen.get("productos"),
                   "umbral": resumen.get("umbral"),
                   "huella_catalogo": resumen.get("huella_catalogo")},
        "metricas": [{"metrica": m, "valor": v} for m, v in metricas.items()],
        "anterior": {"ejecucion_id": anterior} if anterior else None,
        "cambios": cambios,
        "pares": pares,
        "ejecuciones": eids,
    }
