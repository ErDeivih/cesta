"""El cuadro de mando. Consultas de agregacion sobre gold, cacheadas al dia.

La regla que atraviesa todo esto: **cada numero sabe sobre cuantas filas se ha
calculado y de que fecha es**. Un panel que ensena un 19,4 % sin decir sobre
cuantos grupos no es un panel, es una opinion con tipografia.

Y la regla que nacio de equivocarse: **una letra de calidad sacada del precio no
se llama calidad**. El 77 % de ellas salen de ordenar por precio, asi que
mezclarlas produce la conclusion falsa de que lo barato es peor. Aqui se filtra
por `calidad_origen` antes de sumar, siempre.
"""
from __future__ import annotations

from fastapi import APIRouter

from .catalogo import conexion, fecha_de_gold

rutas = APIRouter(prefix="/api/panel")
_cache: dict[str, tuple[str, object]] = {}


def _al_dia(clave: str, calcula):
    """Se guarda hasta que gold cambie de fecha, que es una vez al dia."""
    hoy = fecha_de_gold()
    guardado = _cache.get(clave)
    if guardado and guardado[0] == hoy:
        return guardado[1]
    valor = calcula()
    _cache[clave] = (hoy, valor)
    return valor


@rutas.get("/hoy")
def hoy():
    """El estado del dia: que entro, que se movio, y si algo canta."""
    def calcula():
        con = conexion()
        cadenas = con.execute("""
            SELECT fuente, count(*) AS productos,
                   count(*) FILTER (WHERE comparacion_fiable) AS comparables,
                   count(nutriscore) AS con_nutriscore,
                   count(ean) AS con_ean
              FROM grupos GROUP BY fuente ORDER BY fuente
        """).fetchall()
        movidos = con.execute("""
            SELECT fuente,
                   count(*) FILTER (WHERE ha_bajado) AS bajadas,
                   count(*) FILTER (WHERE ha_subido) AS subidas
              FROM derivado WHERE fecha = (SELECT max(fecha) FROM derivado)
             GROUP BY fuente ORDER BY fuente
        """).fetchall()
        # Si una cadena entra con muchos menos productos de lo normal, algo se
        # rompio. Alcampo paso de 43.643 a 23.500 al recortar el bazar; una
        # caida asi sin un cambio de alcance detras es una alarma.
        avisos = con.execute("""
            WITH por_dia AS (
                SELECT fuente, fecha, count(*) AS n FROM diario GROUP BY fuente, fecha),
            ultimo AS (SELECT fuente, max(fecha) AS f FROM por_dia GROUP BY fuente)
            SELECT p.fuente, p.n,
                   round(median(q.n) OVER (PARTITION BY p.fuente)) AS lo_normal
              FROM por_dia p JOIN ultimo u ON u.fuente = p.fuente AND u.f = p.fecha
              JOIN por_dia q ON q.fuente = p.fuente
        """).fetchall()
        alarmas = [{"cadena": a[0], "hoy": a[1], "lo_normal": int(a[2]),
                    "caida_pct": round(100 * (1 - a[1] / a[2]), 1)}
                   for a in {x[0]: x for x in avisos}.values()
                   if a[2] and a[1] < a[2] * 0.85]
        return {
            "fecha_datos": fecha_de_gold(),
            "cadenas": [{"cadena": c[0], "productos": c[1], "comparables": c[2],
                         "con_nutriscore": c[3], "con_ean": c[4]} for c in cadenas],
            "movidos": [{"cadena": m[0], "bajadas": m[1], "subidas": m[2]} for m in movidos],
            "alarmas": alarmas,
        }
    return _al_dia("hoy", calcula)


@rutas.get("/cadenas")
def cadenas():
    """Quien es mas barato, y cuanto se mueve cada uno."""
    def calcula():
        con = conexion()
        barata = con.execute("""
            WITH m AS (
                SELECT grupo_id, min(precio_unidad_cent) AS mn, count(DISTINCT fuente) AS c
                  FROM grupos
                 WHERE grupo_id IS NOT NULL AND comparacion_fiable AND precio_unidad_cent > 0
                 GROUP BY grupo_id HAVING c >= 2)
            SELECT g.fuente, count(*) AS compite,
                   count(*) FILTER (WHERE g.precio_unidad_cent <= m.mn * 1.001) AS gana
              FROM grupos g JOIN m USING (grupo_id)
             WHERE g.comparacion_fiable AND g.precio_unidad_cent > 0
             GROUP BY g.fuente ORDER BY 3.0 / count(*) DESC
        """).fetchall()
        movimiento = con.execute("""
            SELECT fuente, count(*) AS observaciones,
                   count(*) FILTER (WHERE ha_bajado OR ha_subido) AS movidos,
                   median(CASE WHEN ha_bajado OR ha_subido THEN abs(variacion_cent) END) AS mediana
              FROM derivado WHERE ha_bajado IS NOT NULL GROUP BY fuente
        """).fetchall()
        dispersion = con.execute("""
            WITH x AS (
                SELECT grupo_id, min(precio_unidad_cent) AS mn, max(precio_unidad_cent) AS mx,
                       count(DISTINCT fuente) AS c
                  FROM grupos
                 WHERE grupo_id IS NOT NULL AND comparacion_fiable AND precio_unidad_cent > 0
                 GROUP BY grupo_id HAVING c >= 2 AND mn > 0)
            SELECT count(*), median(100.0 * (mx - mn) / mn),
                   quantile_cont(100.0 * (mx - mn) / mn, 0.9),
                   count(*) FILTER (WHERE (mx - mn) / mn > 2)
              FROM x
        """).fetchone()
        return {
            "fecha_datos": fecha_de_gold(),
            "mas_barata": [{"cadena": b[0], "compite_en": b[1], "gana": b[2],
                            "pct": round(100 * b[2] / b[1], 1)} for b in barata],
            "movimiento": [{"cadena": m[0], "observaciones": m[1], "movidos": m[2],
                            "pct": round(100 * m[2] / m[1], 2),
                            "mediana_cent": round(m[3] or 0)} for m in movimiento],
            "dispersion": {"grupos": dispersion[0],
                           "mediana_pct": round(dispersion[1], 1),
                           "p90_pct": round(dispersion[2], 1),
                           "sospechosos": dispersion[3]},
        }
    return _al_dia("cadenas", calcula)


@rutas.get("/marcas")
def marcas():
    """Marca propia contra marca. El estudio que casi sale al reves.

    Se devuelven las dos cifras a proposito: la que sale mezclando origenes de
    calidad (y es falsa) no se devuelve nunca; la honesta va con su tamano de
    muestra al lado, que es pequeno y hay que decirlo.
    """
    def calcula():
        con = conexion()
        con.execute("""
            CREATE OR REPLACE TEMP VIEW tipo AS
            SELECT *, CASE
                WHEN fuente = 'mercadona' AND marca IN
                     ('Hacendado','Deliplus','Bosque Verde','Compy') THEN 'propia'
                WHEN fuente = 'alcampo'   AND marca LIKE 'PRODUCTO ALCAMPO%' THEN 'propia'
                WHEN fuente = 'carrefour' AND marca LIKE 'CARREFOUR%' THEN 'propia'
                WHEN fuente = 'dia'       AND (marca LIKE 'Dia%' OR marca LIKE '%de Dia') THEN 'propia'
                WHEN fuente = 'aldi'      THEN 'propia'
                ELSE 'marca' END AS clase
              FROM grupos
        """)
        precio = con.execute("""
            WITH mixtos AS (
                SELECT grupo_id FROM tipo
                 WHERE grupo_id IS NOT NULL AND comparacion_fiable AND precio_unidad_cent > 0
                 GROUP BY grupo_id
                HAVING count(*) FILTER (WHERE clase = 'propia') > 0
                   AND count(*) FILTER (WHERE clase = 'marca') > 0)
            SELECT count(DISTINCT t.grupo_id),
                   avg(CASE WHEN clase = 'propia' THEN precio_unidad_cent END),
                   avg(CASE WHEN clase = 'marca'  THEN precio_unidad_cent END)
              FROM tipo t JOIN mixtos USING (grupo_id)
             WHERE t.comparacion_fiable AND t.precio_unidad_cent > 0
        """).fetchone()
        origen = con.execute("""
            SELECT calidad_origen, count(*) FROM grupos WHERE calidad IS NOT NULL
             GROUP BY calidad_origen
        """).fetchall()
        # Cara a cara, y SOLO con letras leidas de una etiqueta de verdad.
        duelo = con.execute("""
            WITH pares AS (
                SELECT grupo_id,
                       max(CASE WHEN clase = 'propia' THEN calidad END) AS cp,
                       max(CASE WHEN clase = 'marca'  THEN calidad END) AS cm
                  FROM tipo
                 WHERE calidad IS NOT NULL AND calidad_origen LIKE 'ingredientes%'
                   AND grupo_id IS NOT NULL
                 GROUP BY grupo_id HAVING cp IS NOT NULL AND cm IS NOT NULL)
            SELECT count(*), count(*) FILTER (WHERE cp < cm),
                   count(*) FILTER (WHERE cp = cm), count(*) FILTER (WHERE cp > cm)
              FROM pares
        """).fetchone()
        propias = con.execute("""
            SELECT fuente, marca, count(*) AS n FROM tipo
             WHERE clase = 'propia' AND marca IS NOT NULL
             GROUP BY fuente, marca QUALIFY row_number() OVER
                 (PARTITION BY fuente ORDER BY count(*) DESC) <= 3
             ORDER BY fuente, n DESC
        """).fetchall()
        total_origen = sum(o[1] for o in origen) or 1
        del_precio = next((o[1] for o in origen if o[0] == "precio"), 0)
        return {
            "fecha_datos": fecha_de_gold(),
            "grupos_con_ambas": precio[0],
            "media_propia_cent": round(precio[1] or 0),
            "media_marca_cent": round(precio[2] or 0),
            "ahorro_pct": round(100 * (1 - (precio[1] or 0) / (precio[2] or 1)), 1),
            "calidad_origen": [{"origen": o[0], "productos": o[1]} for o in origen],
            "aviso": (f"{round(100 * del_precio / total_origen)} % de las letras de "
                      "calidad salen de ordenar por precio, no de leer una etiqueta. "
                      "El duelo de abajo usa solo las leidas."),
            "duelo": {"grupos": duelo[0], "gana_propia": duelo[1],
                      "empatan": duelo[2], "gana_marca": duelo[3]},
            "marcas_propias": [{"cadena": p[0], "marca": p[1], "productos": p[2]}
                               for p in propias],
        }
    return _al_dia("marcas", calcula)


@rutas.get("/historico")
def historico():
    """Cuantas observaciones hay cada dia, y que analisis se desbloquean cuando."""
    def calcula():
        con = conexion()
        dias = con.execute("""
            SELECT fecha::VARCHAR, count(*), count(DISTINCT fuente)
              FROM diario GROUP BY fecha ORDER BY fecha
        """).fetchall()
        n = len(dias)
        pendientes = [
            {"que": "tendencia_30d", "necesita": 30, "faltan": max(0, 30 - n),
             "para": "saber que sube y que baja de verdad"},
            {"que": "oferta_sospechosa", "necesita": 45, "faltan": max(0, 45 - n),
             "para": "cazar la subida previa a la oferta"},
            {"que": "posicion_90d", "necesita": 90, "faltan": max(0, 90 - n),
             "para": "decir si esto no estaba tan barato desde hace meses"},
            {"que": "estacionalidad", "necesita": 365, "faltan": max(0, 365 - n),
             "para": "saber en que epoca del ano compensa"},
        ]
        return {"fecha_datos": fecha_de_gold(), "dias": n,
                "serie": [{"fecha": d[0], "observaciones": d[1], "cadenas": d[2]} for d in dias],
                "pendientes": pendientes}
    return _al_dia("historico", calcula)


@rutas.get("/movidos")
def movidos(limite: int = 60):
    """Lo que se ha movido hoy, de mas a menos. Entre mil y dos mil filas al dia."""
    def calcula():
        con = conexion()
        filas = con.execute("""
            SELECT d.fuente, g.nombre, g.marca, g.unidad_canon, g.grupo_id,
                   d.precio_unidad_cent, d.variacion_cent, d.ha_bajado
              FROM derivado d
              JOIN grupos g ON g.fuente = d.fuente AND g.id_fuente = d.id_fuente
             WHERE d.fecha = (SELECT max(fecha) FROM derivado)
               AND (d.ha_bajado OR d.ha_subido) AND d.precio_unidad_cent > 0
             ORDER BY abs(d.variacion_cent) / nullif(d.precio_unidad_cent, 0) DESC
             LIMIT ?
        """, [limite]).fetchall()
        return {"fecha_datos": fecha_de_gold(),
                "movidos": [{"cadena": f[0], "nombre": f[1], "marca": f[2],
                             "unidad": f[3], "grupo_id": f[4],
                             "precio_unidad_cent": f[5], "variacion_cent": round(f[6]),
                             "baja": bool(f[7])} for f in filas]}
    return _al_dia(f"movidos-{limite}", calcula)
