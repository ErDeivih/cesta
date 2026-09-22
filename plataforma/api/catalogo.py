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

from core import comparacion

from .ajustes import AJUSTES

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
    try:
        return (AJUSTES.gold / "grupos.parquet").stat().st_mtime
    except OSError:
        return 0.0


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
    con.execute(f"CREATE VIEW grupos AS SELECT * FROM '{_p(g / 'grupos.parquet')}'")
    con.execute(f"CREATE VIEW enlaces AS SELECT * FROM '{_p(g / 'enlaces.parquet')}'")
    con.execute(f"CREATE VIEW diario AS SELECT * FROM '{_p(g / 'precio_diario.parquet')}'")
    con.execute(f"CREATE VIEW derivado AS SELECT * FROM '{_p(g / 'precio_derivado.parquet')}'")
    con.execute(f"CREATE VIEW resumen AS SELECT * FROM '{_p(g / 'resumen.parquet')}'")
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

    con.execute(f"""
        CREATE TABLE buscable AS
        SELECT grupo_id, fuente, id_fuente, nombre, marca, cantidad, unidad_canon,
               precio_cent, precio_unidad_cent, comparacion_fiable, calidad,
               calidad_origen, nutriscore, nova, ean, imagen, promo_txt,
               {_o_nulo("sellos", "conservacion", "es_marca_propia", "envase",
                        "nutricion", "promo_club", "promo_solo_online",
                        "es_alcohol", "es_recall",
                        "distintivo", "precio_comparable", "seccion")},
               strip_accents(lower(nombre || ' ' || coalesce(marca, ''))) AS texto
          FROM grupos
    """)
    con.execute("CREATE INDEX buscable_grupo ON buscable(grupo_id)")
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


def buscar(texto: str, cadenas: list[str] | None = None, limite: int = 40,
           solo_comparables: bool = False, solo_con_nutricion: bool = False,
           sellos: list[str] | None = None, conservacion: str | None = None,
           solo_marca_propia: bool = False, solo_ofertas: bool = False,
           sin_alcohol: bool = False, seccion: str | None = None) -> list[dict]:
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
    args = texto_args + atributo_args + atributo_args + [limite]

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
                   count(*) FILTER (WHERE coalesce(es_recall, false)) AS con_retirada
              FROM comparables GROUP BY grupo_id)
        -- `cadenas >= 2` es lo que hace comparable a un grupo, no tener grupo_id:
        -- el emparejador se lo pone a todo, y 32.486 grupos son de un solo
        -- producto. Durante unos dias la interfaz pinto "1 cadenas · 1
        -- productos" para esos, con el sello de comparable puesto.
        SELECT grupo_id, nombre, fuente_barata, precio_cent, min_unidad, max_unidad,
               unidad, cadenas, productos, nutriscore, imagen, con_oferta,
               con_oferta_club, con_retirada,
               cadenas >= 2 AS comparable,
               min_unidad > 0 AND max_unidad / min_unidad > {FACTOR_INCREIBLE} AS dudoso
          FROM porgrupo
        ORDER BY comparable DESC, cadenas DESC, min_unidad
        LIMIT ?
    """, args).fetchall()

    return [{
        "grupo_id": f[0], "nombre": f[1], "cadena_mas_barata": f[2],
        "precio_cent": f[3], "precio_unidad_cent": f[4],
        "precio_unidad_max_cent": f[5], "unidad": f[6],
        "cadenas": f[7], "productos": f[8], "nutriscore": f[9],
        "imagen": f[10], "con_oferta": bool(f[11]),
        "con_oferta_club": bool(f[12]), "con_retirada": bool(f[13]),
        "comparable": bool(f[14]),
        # Un grupo dudoso sigue saliendo, y sigue diciendo donde esta mas barato.
        # Lo que no hace es poner un numero de ahorro que no se sostiene.
        "dudoso": bool(f[15]),
        "ahorro_pct": (round(100 * (f[5] - f[4]) / f[4], 1)
                       if f[14] and f[4] and not f[15] else 0.0),
    } for f in filas]


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


# ------------------------------------------------------------ ficha de grupo --

def grupo(grupo_id: int) -> dict | None:
    """Todo lo que la ficha necesita: los miembros, los equivalentes y la curva."""
    con = conexion()
    disponibles = {f[0] for f in con.execute("DESCRIBE grupos").fetchall()}
    nuevas = ", ".join(
        c if c in disponibles else f"NULL AS {c}"
        for c in ("sellos", "sellos_origen", "certificados", "conservacion",
                  "es_marca_propia", "nutricion", "nutricion_por", "envase",
                  "descripcion", "tipo_producto", "dias_caducidad", "peso_neto_g",
                  "grado_alcohol", "promo_hasta", "promo_club",
                  "promo_solo_online", "es_alcohol",
                  "es_recall", "peso_variacion_pct", "distintivo", "advertencias",
                  "unidades_pack"))
    miembros = con.execute(f"""
        SELECT fuente, id_fuente, nombre, marca, cantidad, unidad_canon,
               precio_cent, precio_unidad_cent, comparacion_fiable,
               calidad, calidad_origen, nutriscore, nova, ean,
               imagen, alergenos, ingredientes, origen, promo_txt, url,
               {nuevas}
          FROM grupos WHERE grupo_id = ? AND precio_unidad_cent > 0
         ORDER BY precio_unidad_cent
    """, [grupo_id]).fetchall()
    if not miembros:
        return None

    def prod(f):
        return {
            "fuente": f[0], "id_fuente": f[1], "producto_id": f"{f[0]}:{f[1]}",
            "nombre": f[2], "marca": f[3], "cantidad": f[4], "unidad": f[5],
            "precio_cent": f[6], "precio_unidad_cent": f[7],
            "comparable": bool(f[8]),
            # La letra sale de leer ingredientes o de ordenar por precio. Si
            # sale del precio NO es calidad: es gama, y se dice como tal. En el
            # 77 % de los casos es lo segundo, y mezclarlas produce la
            # conclusion falsa de que lo barato es peor.
            "calidad": f[9] if f[10] and f[10].startswith("ingredientes") else None,
            "gama": f[9] if f[10] == "precio" else None,
            "nutriscore": f[11], "nova": f[12], "ean": f[13],
            "imagen": f[14], "alergenos": f[15], "ingredientes": f[16],
            "origen": f[17], "promo": f[18], "url": f[19],
            # Los sellos van con su procedencia: no es lo mismo un certificado
            # auditado que una palabra en el nombre del producto. La interfaz lo
            # dice, para no dar por seguro lo que no lo es.
            "sellos": (f[20] or "").split(",") if f[20] else [],
            "sellos_origen": f[21],
            "certificados": (f[22] or "").split(",") if f[22] else [],
            "conservacion": f[23], "es_marca_propia": f[24],
            "nutricion": json.loads(f[25]) if f[25] else None,
            "nutricion_por": f[26], "envase": f[27], "descripcion": f[28],
            "tipo_producto": f[29], "dias_caducidad": f[30],
            "peso_neto_g": f[31], "grado_alcohol": f[32],
            "promo_hasta": f[33].date().isoformat() if f[33] else None,
            # Una oferta de tarjeta NO baja lo que pagas en caja: se acumula en
            # un monedero. La ficha lo dice con esas palabras.
            "promo_club": bool(f[34]),
            "es_alcohol": bool(f[35]), "es_recall": bool(f[36]),
            "peso_variacion_pct": f[37], "distintivo": f[38],
            "advertencias": (f[39] or "").split(" | ") if f[39] else [],
            "unidades_pack": f[40] if (f[40] or 0) > 1 else None,
        }

    productos = [prod(f) for f in miembros]
    serie = con.execute("""
        SELECT fuente, fecha::VARCHAR, precio_unidad_cent
          FROM diario
         WHERE producto_id IN (SELECT fuente || ':' || id_fuente FROM grupos WHERE grupo_id = ?)
         ORDER BY fecha
    """, [grupo_id]).fetchall()

    barato = productos[0]["precio_unidad_cent"]
    caro = productos[-1]["precio_unidad_cent"]
    return {
        "grupo_id": grupo_id,
        "nombre": productos[0]["nombre"],
        "imagen": next((p["imagen"] for p in productos if p["imagen"]), None),
        "unidad": productos[0]["unidad"],
        "productos": productos,
        "cadenas": len({p["fuente"] for p in productos}),
        "ahorro_pct": round(100 * (caro - barato) / barato, 1) if barato else 0.0,
        "ahorro_cent": caro - barato,
        "serie": [{"fuente": s[0], "fecha": s[1], "precio_unidad_cent": s[2]} for s in serie],
    }


def producto(producto_id: str) -> dict | None:
    fuente, _, id_fuente = producto_id.partition(":")
    fila = conexion().execute("""
        SELECT grupo_id, nombre, marca, cantidad, unidad_canon, precio_cent,
               precio_unidad_cent, comparacion_fiable, nutriscore
          FROM grupos WHERE fuente = ? AND id_fuente = ?
    """, [fuente, id_fuente]).fetchone()
    if not fila:
        return None
    return {"producto_id": producto_id, "fuente": fuente, "grupo_id": fila[0],
            "nombre": fila[1], "marca": fila[2], "cantidad": fila[3],
            "unidad": fila[4], "precio_cent": fila[5],
            "precio_unidad_cent": fila[6], "comparable": bool(fila[7]),
            "nutriscore": fila[8]}


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
