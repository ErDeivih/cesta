"""Las preguntas que se hace quien decide, no quien compra.

Un comparador le dice a una persona dónde está su yogur más barato hoy. Esto es
otra cosa: **qué está haciendo el precio**. Quién sube, cuánto, desde cuándo, en
qué secciones, con cuántos productos detrás y con qué margen de duda.

La diferencia no es de pantalla, es de método. Un folleto enseña el precio
tachado al lado del nuevo porque quiere que parezca una ganga. Un instrumento de
medida enseña **el índice, la n y el salto entre capturas**, y deja que el que
mira saque la conclusión. Aquí se hace lo segundo.

Las tres medidas
----------------
`indice`     un índice de precios por cadena, encadenado, base 100.
`pulso`      cuántos precios se mueven, en qué dirección y cuánto.
`posicion`   dónde está cada cadena dentro de cada sección.

Por qué un Jevons encadenado y no "la media de los precios"
-----------------------------------------------------------
La media del catálogo de una cadena no mide el precio: mide **qué había en el
catálogo ese día**. Si Alcampo mete cien jamones de 90 EUR, su media sube sin
que haya subido un solo precio. Es el error clásico de composición, y con
catálogos que rotan un 1 % al día es un error grande.

Un índice encadenado no compara catálogos, compara **el mismo producto consigo
mismo** de una captura a la siguiente, y multiplica los eslabones. La media es
geométrica (Jevons) porque los precios son relativos: subir un 50 % y bajar un
33 % deja el precio donde estaba, y sólo la media geométrica lo ve.

Es, además, lo que usan los institutos de estadística con datos raspados de la
web, así que el método no es una invención de esta casa.

Tres decisiones que cambian el número, y por qué son éstas
----------------------------------------------------------
1. **Se usa el precio de venta, no el precio por unidad.** El mismo producto,
   el mismo envase: un relativo de precio de venta no puede contaminarse con un
   error de formato. Todo el historial de fallos de este proyecto -- el pack de
   30 leído como 1, el azafrán de 0,4 g -- vive en el precio por unidad. Para
   medir variación, el precio de venta es el dato limpio.
2. **El eslabón es contra la captura anterior DE ESA CADENA**, no contra el día
   anterior del calendario. Carrefour no se dejó capturar el 11, el 12 ni el 18
   de septiembre de 2026; comparando contra el calendario, esos días no tenían
   pareja y la cadena desaparecía del índice. El eslabón lleva escrito cuántos
   días cubre, porque un salto de tres días no se lee igual que uno de uno.
3. **Se recortan los relativos fuera de [1/3, 3]**, que no son ofertas sino casi
   siempre errores de dato. Se cuentan y se enseñan: un recorte silencioso es
   una decisión escondida. El 20 de septiembre de 2026 eran 10 de 260.000.
"""
from __future__ import annotations

from .catalogo import conexion, fecha_de_gold

# Fuera de esta horquilla, un cambio de precio de un dia para otro es casi
# siempre un error de lectura, no una oferta. Se cuentan aparte y se enseñan.
RECORTE_MIN = 1.0 / 3
RECORTE_MAX = 3.0

# Un movimiento por debajo de esto es redondeo o un céntimo de IVA, no una
# decisión comercial de nadie.
MINIMO_MOVIMIENTO_PCT = 0.5


def _enlaces_sql(desde: str | None) -> str:
    """Cada captura emparejada con la anterior de su propia cadena."""
    filtro = f"WHERE fecha >= '{desde}'" if desde else ""
    return f"""
    WITH dias AS (SELECT DISTINCT fuente, fecha FROM diario {filtro}),
    enlace AS (
      SELECT a.fuente, a.fecha,
             (SELECT max(b.fecha) FROM dias b
               WHERE b.fuente = a.fuente AND b.fecha < a.fecha) AS previa
        FROM dias a),
    par AS (
      SELECT e.fuente, e.fecha, e.previa,
             date_diff('day', strptime(e.previa, '%Y-%m-%d'),
                              strptime(e.fecha, '%Y-%m-%d')) AS salto,
             b.precio_cent AS antes, a.precio_cent AS hoy,
             a.precio_cent::DOUBLE / b.precio_cent AS rel
        FROM enlace e
        JOIN diario a ON a.fuente = e.fuente AND a.fecha = e.fecha
        JOIN diario b ON b.producto_id = a.producto_id AND b.fecha = e.previa
       WHERE e.previa IS NOT NULL AND a.precio_cent > 0 AND b.precio_cent > 0)
    """


def indice(desde: str | None = None) -> dict:
    """Índice de precios por cadena, base 100 en la primera captura comparable.

    Devuelve una serie por cadena y, con ella, lo que hace falta para no
    leerla mal: cuántos productos sostienen cada eslabón, cuántos días cubre y
    cuántos relativos se recortaron.
    """
    con = conexion()
    filas = con.execute(f"""
        {_enlaces_sql(desde)}
        SELECT fecha, fuente, any_value(salto) AS salto,
               count(*) FILTER (WHERE rel BETWEEN ? AND ?) AS n,
               count(*) FILTER (WHERE rel NOT BETWEEN ? AND ?) AS recortados,
               exp(avg(ln(rel)) FILTER (WHERE rel BETWEEN ? AND ?)) AS factor
          FROM par
         GROUP BY fecha, fuente
         ORDER BY fecha, fuente
    """, [RECORTE_MIN, RECORTE_MAX] * 3).fetchall()

    series: dict[str, list[dict]] = {}
    nivel: dict[str, float] = {}
    for fecha, fuente, salto, n, recortados, factor in filas:
        if not n or factor is None:
            continue
        nivel[fuente] = nivel.get(fuente, 100.0) * factor
        series.setdefault(fuente, []).append({
            "fecha": fecha, "indice": round(nivel[fuente], 3),
            "variacion_pct": round(100 * (factor - 1), 3),
            "productos": n, "dias_del_salto": salto, "recortados": recortados,
        })
    return {
        "fecha_datos": fecha_de_gold(),
        "base": "100 en la primera captura de cada cadena",
        "metodo": "Jevons encadenado sobre el precio de venta del mismo producto",
        "series": [{
            "cadena": c,
            "indice": puntos[-1]["indice"],
            "variacion_pct": round(puntos[-1]["indice"] - 100, 2),
            "capturas": len(puntos),
            "puntos": puntos,
        } for c, puntos in sorted(series.items())],
    }


def pulso(desde: str | None = None) -> dict:
    """Cuántos precios se mueven en cada captura, hacia dónde y cuánto.

    No es una lista de ofertas: es la frecuencia y la amplitud con la que cada
    cadena toca sus precios. Una cadena que mueve el 4 % de su catálogo cada día
    y otra que lo mueve una vez al mes se comportan de forma distinta, y eso se
    decide con este número, no con el precio de un yogur.
    """
    con = conexion()
    filas = con.execute(f"""
        {_enlaces_sql(desde)}
        , m AS (SELECT *, 100.0 * (rel - 1) AS pct FROM par
                 WHERE rel BETWEEN ? AND ?)
        SELECT fecha, fuente, any_value(salto) AS salto, count(*) AS vistos,
               count(*) FILTER (WHERE abs(pct) >= ?) AS movidos,
               count(*) FILTER (WHERE pct <= -?) AS bajan,
               count(*) FILTER (WHERE pct >= ?) AS suben,
               median(pct) FILTER (WHERE pct <= -?) AS mediana_bajada,
               median(pct) FILTER (WHERE pct >= ?) AS mediana_subida
          FROM m GROUP BY fecha, fuente ORDER BY fecha, fuente
    """, [RECORTE_MIN, RECORTE_MAX] + [MINIMO_MOVIMIENTO_PCT] * 5).fetchall()
    return {
        "fecha_datos": fecha_de_gold(),
        "umbral_pct": MINIMO_MOVIMIENTO_PCT,
        "capturas": [{
            "fecha": f[0], "cadena": f[1], "dias_del_salto": f[2],
            "vistos": f[3], "movidos": f[4],
            "movidos_pct": round(100 * f[4] / f[3], 2) if f[3] else 0.0,
            "bajan": f[5], "suben": f[6],
            "mediana_bajada_pct": round(f[7], 2) if f[7] is not None else None,
            "mediana_subida_pct": round(f[8], 2) if f[8] is not None else None,
        } for f in filas],
    }


def posicion() -> dict:
    """Dónde está cada cadena dentro de cada sección, comparando lo comparable.

    La pregunta que decide de verdad no es "¿quién es más barato?" sino "¿en qué
    soy caro?". Una cadena puede estar un 20 % por debajo en lácteos y un 25 %
    por encima en pescadería, y la media de las dos no se parece a ninguna.

    El primer intento de esta función comparaba **la mediana de EUR/kg de cada
    cadena en cada sección**, y estaba mal. Salía esto:

        higiene-belleza    mercadona +2.246 %
        bebe               carrefour   +150 %

    Mercadona no vende el champú veintidós veces más caro: vende maquillaje y
    colonia, que pesan poco y cuestan mucho, donde Carrefour vende garrafas de
    gel. La mediana de la sección no mide el precio, mide **qué hay dentro de la
    sección**. Es el mismo error de composición contra el que avisa el índice,
    cometido dos funciones más abajo.

    Así que se compara sólo lo emparejado: dentro de cada grupo comparable, cada
    cadena contra la mediana de ese grupo, y luego la mediana de esos desvíos
    por sección. Eso ya no depende del surtido, porque todos los términos de la
    resta son el mismo producto.

    Devuelve lista vacía mientras `seccion` no haya llegado a gold.
    """
    con = conexion()
    columnas = {f[0] for f in con.execute("DESCRIBE buscable").fetchall()}
    if "seccion" not in columnas:
        return {"fecha_datos": fecha_de_gold(), "secciones": []}
    filas = con.execute("""
        WITH base AS (
          SELECT grupo_id, seccion, fuente, unidad_canon, precio_unidad_cent
            FROM buscable
           WHERE seccion IS NOT NULL AND grupo_id IS NOT NULL
             AND precio_unidad_cent > 0 AND unidad_canon IS NOT NULL
             AND coalesce(comparacion_fiable, false)),
        -- Un grupo puede mezclar unidades (la manzanilla a granel contra las
        -- bolsitas). Se queda con la unidad que comparten mas cadenas: restar
        -- EUR/kg de EUR/ud no da un desvio, da un disparate.
        unidad AS (
          SELECT grupo_id, unidad_canon,
                 row_number() OVER (PARTITION BY grupo_id
                     ORDER BY count(DISTINCT fuente) DESC, count(*) DESC) AS puesto
            FROM base GROUP BY grupo_id, unidad_canon),
        limpio AS (
          SELECT b.* FROM base b JOIN unidad u
            ON u.grupo_id = b.grupo_id AND u.unidad_canon = b.unidad_canon
           WHERE u.puesto = 1),
        -- Contra las OTRAS cadenas del grupo, no contra todas incluida ella.
        --
        -- Con la mediana del grupo entero, la cadena que cae en medio da
        -- exactamente +0,0 % por construccion, no por barata: con tres cadenas
        -- en un grupo, la del medio ES la mediana. Salian tres cadenas clavadas
        -- en cero en casi todas las secciones, que es un artefacto del metodo
        -- disfrazado de empate.
        --
        -- Dejando fuera a la propia cadena, el punto de comparacion ya no
        -- depende de ella y el cero deja de estar regalado.
        referencia AS (
          SELECT l.grupo_id, l.fuente, median(o.precio_unidad_cent) AS mediana
            FROM limpio l JOIN limpio o
              ON o.grupo_id = l.grupo_id AND o.fuente <> l.fuente
           GROUP BY l.grupo_id, l.fuente),
        desvio AS (
          SELECT l.seccion, l.fuente,
                 100.0 * (l.precio_unidad_cent - r.mediana) / r.mediana AS pct
            FROM limpio l JOIN referencia r
              ON r.grupo_id = l.grupo_id AND r.fuente = l.fuente)
        SELECT seccion, fuente, count(*) AS n, median(pct) AS desvio_pct
          FROM desvio GROUP BY seccion, fuente
         HAVING count(*) >= 15
         ORDER BY seccion, desvio_pct
    """).fetchall()
    por_seccion: dict[str, list] = {}
    for seccion, fuente, n, pct in filas:
        por_seccion.setdefault(seccion, []).append({
            "cadena": fuente, "productos": n, "desvio_pct": round(pct, 1)})
    return {
        "fecha_datos": fecha_de_gold(),
        "medida": "mediana del desvío de cada producto respecto a la mediana "
                  "de las OTRAS cadenas de su grupo comparable",
        "secciones": [{"seccion": s, "cadenas": c,
                       "productos": sum(x["productos"] for x in c)}
                      for s, c in por_seccion.items()],
    }
