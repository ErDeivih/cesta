"""Que ha bajado, que ha subido, y que oferta no es una oferta.

Por que este fichero es corto
-----------------------------
Las dos funcionalidades que se le copian a la competencia -- las "bajadas de esta
semana" de Precios del Super y el "verificador de ofertas" de PrecioReal -- ya
estaban calculadas. `core/derive.py` lleva semanas escribiendo en
`gold/precio_derivado.parquet` las columnas `ha_bajado`, `variacion_cent`,
`precio_anterior_cent`, `min_90d_cent`, `posicion_90d`, `descuento_real` y
`oferta_sospechosa`. Lo que faltaba no era el analisis: era **ensenarlo**.

Asi que esto es una consulta, no una capa nueva. Y por eso conviene decir en que
somos mejores que lo que copiamos:

    ellos      comparan el precio de hoy con el de la captura anterior
    nosotros   tenemos trece dias de serie, la ventana de 90 dias y el control
               de diferencias increibles, asi que podemos distinguir una bajada
               de un formato mal leido

Esa distincion es toda la diferencia entre una pantalla util y una pantalla que
anuncia que el azafran ha bajado de 6.875 a 6,67 EUR/kg.
"""
from __future__ import annotations

from core import comparacion
from plataforma.api import catalogo

# Una variacion mayor que esto no es una bajada: es un error de lectura. Es el
# mismo numero que usa el buscador y el resumen diario, y vive en un solo sitio a
# proposito -- hubo una epoca con dos umbrales distintos llamados igual.
FACTOR_INCREIBLE = comparacion.FACTOR_INCREIBLE

# Por debajo de esto, una "bajada" es ruido de redondeo del precio por unidad.
MINIMO_PCT = 3.0

# Cuanto puede diferir la cantidad de un dia a otro sin que deje de ser el mismo
# producto. Es la comprobacion que de verdad separa una bajada de un cambio de
# formato, y costo descubrirla: la primera version de esta pantalla, probada
# contra los datos del 18 de septiembre de 2026, encabezaba con ocho productos de
# Alcampo todos exactamente al -96,7 %.
#
#     NATURTIERRA Berberina    594,00 -> 19,80 EUR/ud
#     AQUILEA Descanso       1.020,00 -> 34,00 EUR/ud
#
# Dividir por treinta no es una oferta: son envases de 30 unidades que un dia se
# leyeron como una y al siguiente como treinta. El precio de venta no se habia
# movido. La cantidad se deduce de `precio_cent / precio_unidad_cent`, y si no
# coincide entre los dos dias, lo que cambio fue la lectura del formato.
TOLERANCIA_CANTIDAD = 0.02


def bajadas(dias: int = 7, cadenas: list[str] | None = None, limite: int = 60,
            subidas: bool = False, grupos: list[int] | None = None) -> list[dict]:
    """Lo que mas ha cambiado de precio en los ultimos `dias`.

    Se mira **el precio por unidad**, no el precio de venta: un pack que pasa de
    seis a cuatro unidades y baja de precio no ha bajado nada, y esa es
    exactamente la clase de "oferta" que esta pantalla no debe anunciar.

    Se comparan dos dias concretos -- el mas reciente que hay y el de hace
    `dias` -- en vez de encadenar variaciones diarias. Encadenar suma el ruido de
    cada dia; comparar los extremos contesta la pregunta que se hace la gente,
    que es "¿esta mas barato que la semana pasada?".

    `grupos` es **"solo lo mio"**: la lista de grupos de esta persona (sus listas y
    sus favoritos, ver `almacen.mis_grupos`). Se filtra **en SQL y no despues**: con
    un `LIMIT` de 60 por detras, filtrar en Python lo que ya viene recortado dejaria
    fuera bajadas mias que no estan entre las sesenta mayores del catalogo -- y la
    pregunta es "¿ha bajado algo de lo mio?", no "¿de lo mio hay algo entre lo mas
    bajado del catalogo?".

    Una lista **vacia** de grupos no es "sin filtro": es que esta persona no tiene
    nada apuntado, y entonces no hay nada que contestar. Se distingue con `None`, que
    es "no me filtres".
    """
    con = catalogo.conexion()
    signo = ">" if subidas else "<"
    args: list = [dias]
    filtro_cadena = ""
    if cadenas:
        filtro_cadena = " AND d.fuente IN (" + ",".join("?" * len(cadenas)) + ")"
        args.extend(cadenas)
    filtro_grupo = ""
    if grupos is not None:
        if not grupos:
            return []
        filtro_grupo = " AND b.grupo_id IN (" + ",".join("?" * len(grupos)) + ")"
    args.extend([MINIMO_PCT, TOLERANCIA_CANTIDAD, FACTOR_INCREIBLE])
    args.extend(grupos or [])
    args.append(limite)

    filas = con.execute(f"""
        WITH ventana AS (
            SELECT max(fecha)::VARCHAR AS hoy,
                   (max(fecha::DATE) - INTERVAL (?) DAY)::DATE::VARCHAR AS antes
              FROM diario),
        -- `arg_min` sobre la fecha: si el dia exacto de hace N no existe --
        -- porque esa cadena no se capturo ese dia -- se coge el primero que haya
        -- a partir de ahi. Exigir la fecha exacta dejaba fuera a Carrefour
        -- entero cualquier semana con un dia de bloqueo.
        antes AS (
            SELECT d.fuente, d.id_fuente,
                   arg_min(d.precio_unidad_cent, d.fecha) AS precio_antes,
                   arg_min(d.precio_cent, d.fecha) AS venta_antes,
                   arg_min(d.unidad_canon, d.fecha) AS unidad_antes,
                   min(d.fecha)::VARCHAR AS fecha_antes
              FROM diario d, ventana v
             WHERE d.fecha::VARCHAR >= v.antes AND d.fecha::VARCHAR < v.hoy
               AND d.precio_unidad_cent > 0
             GROUP BY d.fuente, d.id_fuente),
        ahora AS (
            SELECT d.fuente, d.id_fuente, d.precio_unidad_cent AS precio_hoy,
                   d.precio_cent, d.unidad_canon
              FROM diario d, ventana v
             WHERE d.fecha::VARCHAR = v.hoy AND d.precio_unidad_cent > 0{filtro_cadena})
        SELECT b.grupo_id, b.nombre, b.marca, a.fuente, b.imagen, a.unidad_canon,
               a.precio_cent, a.precio_hoy, n.precio_antes, n.fecha_antes,
               100.0 * (a.precio_hoy - n.precio_antes) / n.precio_antes AS pct,
               b.promo_txt, coalesce(b.promo_club, false) AS es_club,
               n.venta_antes
          FROM ahora a
          JOIN antes n USING (fuente, id_fuente)
          JOIN buscable b USING (fuente, id_fuente)
         WHERE abs(100.0 * (a.precio_hoy - n.precio_antes) / n.precio_antes) >= ?
           AND a.precio_hoy {signo} n.precio_antes
           -- La unidad tiene que ser la misma: comparar EUR/kg con EUR/ud es
           -- comparar dos cosas distintas, no ver una bajada.
           AND a.unidad_canon IS NOT DISTINCT FROM n.unidad_antes
           -- Y la cantidad tambien. Se deduce del propio precio, y si no
           -- coincide, lo que cambio fue el formato y no el precio: es el caso
           -- de los envases de 30 unidades leidos como uno.
           AND abs(a.precio_cent / a.precio_hoy
                   - n.venta_antes / n.precio_antes)
               <= ? * (n.venta_antes / n.precio_antes)
           -- Y el precio de venta se tiene que haber movido en el mismo sentido:
           -- lo que paga la gente en caja es la prueba de que hubo cambio.
           AND (a.precio_cent - n.venta_antes) {signo} 0
           -- La red de seguridad de siempre, por si algo se cuela.
           AND greatest(a.precio_hoy, n.precio_antes)
               / least(a.precio_hoy, n.precio_antes) < ?{filtro_grupo}
         ORDER BY abs(100.0 * (a.precio_hoy - n.precio_antes) / n.precio_antes) DESC
         LIMIT ?
    """, args).fetchall()

    return [{
        "grupo_id": f[0], "nombre": f[1], "marca": f[2], "cadena": f[3],
        "imagen": f[4], "unidad": f[5], "precio_cent": f[6],
        "precio_unidad_cent": round(f[7], 2),
        "precio_unidad_antes_cent": round(f[8], 2),
        "desde": f[9],
        "variacion_pct": round(f[10], 1),
        "promo_txt": f[11],
        # Una bajada que solo existe con la tarjeta no es una bajada para quien
        # no la tiene. Se ensena, marcada, y quien mira decide.
        "solo_con_tarjeta": bool(f[12]),
        "precio_antes_cent": f[13],
    } for f in filas]


def _filtro_de_cadenas(cadenas: list[str] | None) -> tuple[str, list]:
    """El trozo de SQL y sus argumentos para mirar solo unas cadenas."""
    if not cadenas:
        return "", []
    return (" AND x.fuente IN (" + ",".join("?" * len(cadenas)) + ")", list(cadenas))


# El texto de promocion no solo dice *que* hay oferta: dice **como funciona**, y no
# todas se pueden juzgar con el precio de una unidad.
#
# Medido el 24 de septiembre de 2026 sobre el gold de ese dia, de las 5.488 ofertas
# anunciadas cuyo precio de hoy no baja de su precio de siempre:
#
#     3.454 (63 %)  dependen de cuantas unidades compres   ("3x2" 2.195, "2ª unidad
#                   -50 %" 848+48+..., "Todo a 1 EUR" 653, "5 EUR dto. comprando 20")
#        345        no anuncian un descuento de precio      ("En pack, mas facil",
#                   "Stock Fuera (Unidades Limitadas)", "Novedad Alcampo", "Producto
#                   en Folleto", "Super Precio", "Nuestra seleccion de vinos...")
#
# Acusar a las primeras es sencillamente un error de esa pantalla: un 3x2 no baja el
# precio de una unidad, baja el de la tercera, asi que "hoy cuesta mas que su precio
# de siempre" es verdad y no significa nada. Las segundas son etiquetas de marketing
# metidas en el mismo campo que las ofertas.
#
# Asi que se juzga **solo** lo que anuncia un descuento sobre el precio de ese
# producto, y lo demas se cuenta y se dice. El orden importa: `sin_precio` va antes
# que `varias` porque "Stock Fuera (Unidades Limitadas)" trae la palabra "unidades".
MECANICAS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("sin_precio", ("stock fuera", "novedad", "folleto", "seleccion", "selección",
                    "super precio", "protein", "proteín", "mas facil", "más facil")),
    ("varias", ("unidad", "3x2", "2x1", "4x3", "3x1", "lote", "pack", "comprando",
                "gratis", "2ª", "2a ud")),
)

# El texto de promocion, tal cual viene de la cadena.
_COLUMNA_MECANICA = "lower(coalesce(b.promo_txt, ''))"


def _case_mecanica() -> str:
    """El `CASE` de SQL que clasifica el texto, hecho desde `MECANICAS`.

    Se genera desde Python para que la lista de patrones viva en **un solo sitio**:
    escrita a mano en el SQL, la primera correccion se haria en un lado y no en el
    otro, y el numero que la pantalla enseña dejaria de ser el de la lista.
    """
    partes = []
    for mecanica, patrones in MECANICAS:
        for patron in patrones:
            partes.append(f"WHEN {_COLUMNA_MECANICA} LIKE '%{patron}%' THEN '{mecanica}'")
    return "CASE " + " ".join(partes) + " ELSE 'precio' END"


# El SQL del verificador, en un sitio y usado por las tres funciones de abajo: la que
# devuelve las ofertas y las que cuentan lo que se queda fuera. Dos copias de esta
# consulta se separarian a la primera correccion, y entonces los numeros que la
# pantalla enseña dejarian de hablar de la misma lista.
#
# `{veredicto}` es lo unico que cambia entre ellas.
_DUDOSAS_SQL = """
        WITH hist AS (
            SELECT x.fuente, x.id_fuente, x.fecha, x.precio_unidad_cent,
                   x.precio_base_cent, x.posicion_90d, x.min_90d_cent, x.max_90d_cent,
                   -- La cantidad que **deduce** el precio: 3,49 EUR por unidad de un
                   -- producto de 2,0057 kg dan 1,74 EUR/kg. `bajadas()` ya usa esta
                   -- cuenta (`TOLERANCIA_CANTIDAD`) para no confundir una bajada con
                   -- un cambio de formato; aqui hace falta por lo mismo.
                   x.precio_cent / nullif(x.precio_unidad_cent, 0) AS cantidad,
                   row_number() OVER (PARTITION BY x.fuente, x.id_fuente
                                      ORDER BY x.fecha DESC) AS n
              FROM derivado x
             WHERE true{filtro}),
        con_cantidad AS (
            SELECT h.*,
                   -- La cantidad normal de los ultimos VENTANA_BASE dias: la misma
                   -- ventana con la que `core/derive.py` calcula el precio de siempre.
                   -- Si dentro de esa ventana la presentacion cambio, la mediana mezcla
                   -- dos productos y **no se puede acusar a nadie**.
                   median(cantidad) OVER (PARTITION BY fuente, id_fuente
                                          ORDER BY fecha DESC
                                          ROWS BETWEEN CURRENT ROW AND ? FOLLOWING)
                       AS cantidad_ventana
              FROM hist h),
        veredicto AS (
            SELECT u.*, b.grupo_id, b.nombre, b.marca, b.imagen, b.promo_txt,
                   coalesce(b.promo_club, false) AS es_club, b.unidad_canon,
                   -- Anuncia oferta y hoy no cuesta menos de lo que cuesta siempre.
                   (u.precio_base_cent IS NOT NULL
                    AND u.precio_unidad_cent >= u.precio_base_cent) AS es_dudosa,
                   -- **Y la presentacion no ha cambiado: el mismo producto, la misma
                   -- cantidad.** Sin esto la lista encabezaba con "Ampollas Compeed
                   -- 8 ml" a 1.306,25 EUR/l frente a "su precio de siempre" 10,45
                   -- EUR/l: no es un disparate de la cadena, es que un dia la cantidad
                   -- se leyo como 1 y otro como 0,008. Lo encontro el navegador al
                   -- pintar la unidad, que hasta hoy no se pintaba.
                   (u.cantidad_ventana IS NOT NULL
                    AND abs(u.cantidad - u.cantidad_ventana)
                        <= ? * u.cantidad_ventana) AS cantidad_comparable,
                   -- Y el texto dice si el descuento es sobre el precio de **esta**
                   -- unidad o sobre cuantas compres. Ver `MECANICAS`.
                   {mecanica} AS mecanica
              FROM con_cantidad u
              JOIN buscable b USING (fuente, id_fuente)
             WHERE u.n = 1 AND b.promo_txt IS NOT NULL)
"""


def ofertas_dudosas(limite: int = 60, cadenas: list[str] | None = None) -> list[dict]:
    """Ofertas anunciadas que el historico no sostiene.

    La pregunta del "verificador de ofertas" no es cuanto cuesta, es **si el
    descuento que anuncian existe**. Aqui se contesta cruzando dos cosas que ya
    estaban en gold y que nadie habia puesto una al lado de la otra: el texto de
    promocion que publica la cadena (`promo_txt`, en 6.885 productos) y lo que
    dice la serie de precios de ese mismo producto (`precio_base_cent`, la
    mediana movil, y `posicion_90d`).

    Una oferta es dudosa cuando el precio de hoy **no esta por debajo** de lo que
    ese producto cuesta normalmente. Sin margen de cortesia: si cuesta lo mismo
    de siempre, el cartel no dice la verdad.

    **Pero solo se juzga lo que se puede juzgar**, y eso son dos condiciones mas
    (`ofertas_sin_poder_juzgar` cuenta el resto, y la pantalla lo dice):

    - la oferta tiene que ser un descuento sobre el precio de **esta** unidad: un
      3x2 o una "2ª unidad -50 %" no bajan el precio de una, bajan el de la
      tercera, y acusarlas es un error de esta pantalla (eran el 63 % de la lista);
    - la cantidad que deduce el precio no puede haber cambiado dentro de la
      ventana, o los dos numeros no son del mismo producto.

    Nota sobre un control que todavia no puede funcionar
    ----------------------------------------------------
    `core/derive.py` calcula ademas `oferta_sospechosa`, que es mas exigente:
    marca el caso feo de verdad, subir el precio normal justo antes de anunciar
    la oferta. Compara con `shift(45)`, o sea con el precio base de hace 45 dias,
    y **hoy hay trece dias de historico**, asi que sale False en las 593.509
    filas. No esta roto: esta dormido, y despierta solo cuando la serie llegue a
    los 45 dias. Basar esta pantalla en el habria sido ensenar una pantalla vacia
    durante seis semanas.
    """
    con = catalogo.conexion()
    filtro, args = _filtro_de_cadenas(cadenas)
    filas = con.execute(
        _DUDOSAS_SQL.format(filtro=filtro, mecanica=_case_mecanica())
        + """ SELECT grupo_id, nombre, marca, fuente, imagen, promo_txt,
                     precio_unidad_cent, precio_base_cent, posicion_90d,
                     min_90d_cent, max_90d_cent, es_club, unidad_canon
                FROM veredicto
               WHERE es_dudosa AND cantidad_comparable AND mecanica = 'precio'
               ORDER BY posicion_90d DESC NULLS LAST,
                        precio_unidad_cent / precio_base_cent DESC
               LIMIT ?""",
        [*args, comparacion.VENTANA_BASE, TOLERANCIA_CANTIDAD, limite]).fetchall()

    return [{
        "grupo_id": f[0], "nombre": f[1], "marca": f[2], "cadena": f[3],
        "imagen": f[4], "promo_txt": f[5],
        "precio_unidad_cent": round(f[6], 2) if f[6] is not None else None,
        "precio_base_cent": round(f[7], 2) if f[7] is not None else None,
        "posicion_90d": round(f[8], 2) if f[8] is not None else None,
        "min_90d_cent": round(f[9], 2) if f[9] is not None else None,
        "max_90d_cent": round(f[10], 2) if f[10] is not None else None,
        "solo_con_tarjeta": bool(f[11]),
        # **La unidad, que faltaba.** `precio_unidad_cent` es EUR/kg o EUR/l, no
        # euros: enseñarlo sin decir de qué unidad habla es enseñar un número que
        # no significa lo que parece (1,29 € el kilo contra 1,29 € el envase).
        # La pantalla no lo tenía porque el endpoint no lo daba.
        "unidad": f[12],
        "por_que": _por_que(f[6], f[7], f[8]),
    } for f in filas]


def ofertas_sin_poder_juzgar(cadenas: list[str] | None = None) -> dict:
    """Cuantas ofertas anunciadas **no se pueden juzgar**, y por que.

    Tres familias, y las tres se cuentan porque la pantalla las dice en voz alta:
    es la regla de siempre -- un dato que no tenemos es "no lo se", y aqui el dato
    que falta es el precio normal de *ese* producto:

        por_varias_unidades          el descuento depende de cuantas compres
                                     ("3x2", "2ª unidad -50 %", "Todo a 1 EUR"):
                                     el precio de una unidad no lo puede ver
        sin_descuento_de_precio      el texto no anuncia un descuento sobre el
                                     precio ("Stock Fuera", "Novedad", folleto)
        cantidad_cambiada            el tamaño declarado cambio dentro de la
                                     ventana: los dos numeros no son del mismo
                                     producto ("Ampollas Compeed 8 ml" a 1.306,25
                                     EUR/l contra "su precio de siempre" 10,45)
    """
    con = catalogo.conexion()
    filtro, args = _filtro_de_cadenas(cadenas)
    fila = con.execute(
        _DUDOSAS_SQL.format(filtro=filtro, mecanica=_case_mecanica())
        + """ SELECT
                 count(*) FILTER (WHERE mecanica = 'varias'),
                 count(*) FILTER (WHERE mecanica = 'sin_precio'),
                 count(*) FILTER (WHERE mecanica = 'precio' AND NOT cantidad_comparable)
              FROM veredicto
             WHERE es_dudosa""",
        [*args, comparacion.VENTANA_BASE, TOLERANCIA_CANTIDAD]).fetchone()
    por_varias, sin_precio, cantidad = (int(x or 0) for x in fila)
    return {"por_varias_unidades": por_varias, "sin_descuento_de_precio": sin_precio,
            "cantidad_cambiada": cantidad,
            "total": por_varias + sin_precio + cantidad}


def _por_que(hoy, base, posicion) -> str:
    """La frase que explica por que esa oferta no lo parece. En cristiano."""
    if hoy is not None and base is not None and hoy >= base:
        if hoy > base:
            return "anuncia oferta y hoy cuesta mas que su precio de siempre"
        return "anuncia oferta y cuesta exactamente lo de siempre"
    if posicion is not None and posicion >= 0.8:
        return "anuncia oferta y esta entre los precios mas altos de los ultimos 90 dias"
    return "anuncia oferta y el historico no ve ninguna bajada"
