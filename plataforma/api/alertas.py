"""Avisar cuando algo baja. La funcion que tienen todos los de la competencia.

La tabla `alerta` esta en `sql/001_esquema.sql` **desde el primer dia** con sus
tres tipos escritos, y no la usaba nadie: ni un endpoint, ni una consulta, ni un
boton. Un disenno terminado y muerto, como estaba `core/secciones.py`.

Es ademas lo unico de esta categoria que tienen todos -- Precios del Super,
PrecioReal, RadarSuper, la extension de supermarket-tracker -- y lo unico que
convierte un historico en algo que te busca a ti en vez de esperar a que entres.

Los tres tipos, y por que son esos
----------------------------------
    baja_de            "avisame si baja de 1,20 EUR/l"
    minimo_90d         "avisame cuando este mas barato que nunca en 90 dias"
    cualquier_bajada   "avisame si baja, sin mas"

`minimo_90d` es la buena y la que no tiene casi nadie: no hay que saber de
antemano cuanto deberia costar algo. `baja_de` exige poner un numero, y la
mayoria de la gente no sabe cual poner hasta que ve la curva.

Lo que NO cuenta como bajada
----------------------------
Exactamente lo mismo que no cuenta en `movimientos`, y por la misma razon: el 18
de septiembre de 2026 la primera pantalla de bajadas encabezaba con ocho
productos de Alcampo al -96,7 %, que eran envases de 30 unidades leidos como
uno. Una alerta que salta por eso es peor que una pantalla que lo ensena, porque
llega sola y sin contexto.

    · si la unidad cambio, no es una bajada
    · si la cantidad implicita cambio, cambio el formato y no el precio
    · si el precio de venta no se movio, no se movio nada
    · si solo baja con la tarjeta de la cadena, no baja en caja

Y una alerta se dispara **una vez**. `vista_en` guarda cuando se conto; mientras
la condicion siga siendo cierta no se vuelve a contar, porque un aviso que se
repite todos los dias deja de leerse -- que es la leccion de `CIFRAS.md`.
"""
from __future__ import annotations

from core.comparacion import FACTOR_INCREIBLE

from . import catalogo

# `FACTOR_INCREIBLE` se importa, **no se copia**, y esto es un arreglo del 27 de septiembre de
# 2026 con su medición detrás: aquí había un `20.0` propio mientras el resto del proyecto usa
# **30** (`core/comparacion.py`, importado igual por `catalogo.py` y `movimientos.py`). El
# comentario decía «la misma red de seguridad que en `movimientos`» y no lo era: una bajada de
# 25× disparaba una alerta aquí y la pantalla de bajadas la rechazaba como imposible, así que
# el aviso podía saltar por un movimiento que el propio proyecto considera un error de dato.
# Es exactamente lo que avisa el anexo de fórmulas: un número compartido vive en un módulo que
# los demás importan; copiado en dos sitios acaba siendo distinto.
TOLERANCIA_CANTIDAD = 0.02

TIPOS = ("baja_de", "minimo_90d", "cualquier_bajada")


def _mejor_de_cada_grupo(grupos: list[int]) -> dict[int, dict]:
    """El producto mas barato de cada grupo hoy, con lo que hace falta juzgarlo.

    "Mas barato" con las reglas de la cesta: no cuentan ni las ofertas de
    tarjeta ni las de solo internet, porque ninguna de las dos baja lo que se
    paga en la caja de la tienda.
    """
    if not grupos:
        return {}
    con = catalogo.conexion()
    marcas = ",".join("?" * len(grupos))
    filas = con.execute(f"""
        WITH miembros AS (
            SELECT b.grupo_id, b.fuente, b.id_fuente, b.nombre, b.marca, b.imagen,
                   b.unidad_canon, b.precio_cent, b.precio_unidad_cent, b.promo_txt
              FROM buscable b
             WHERE b.grupo_id IN ({marcas})
               AND b.precio_unidad_cent > 0
               AND coalesce(b.comparacion_fiable, true)
               AND NOT coalesce(b.promo_club, false)
               AND NOT coalesce(b.promo_solo_online, false)),
        -- Una unidad por grupo: restar EUR/kg de EUR/ud no da una bajada, da un
        -- disparate. Se queda la que comparten mas cadenas.
        unidad AS (
            SELECT grupo_id, unidad_canon,
                   row_number() OVER (PARTITION BY grupo_id
                       ORDER BY count(DISTINCT fuente) DESC, count(*) DESC) AS puesto
              FROM miembros GROUP BY grupo_id, unidad_canon),
        limpio AS (
            SELECT m.* FROM miembros m JOIN unidad u
              ON u.grupo_id = m.grupo_id AND u.unidad_canon = m.unidad_canon
             WHERE u.puesto = 1),
        mejor AS (
            SELECT grupo_id,
                   arg_min(fuente, precio_unidad_cent) AS fuente,
                   arg_min(id_fuente, precio_unidad_cent) AS id_fuente,
                   arg_min(nombre, precio_unidad_cent) AS nombre,
                   arg_min(marca, precio_unidad_cent) AS marca,
                   arg_min(imagen, precio_unidad_cent) AS imagen,
                   arg_min(unidad_canon, precio_unidad_cent) AS unidad,
                   arg_min(precio_cent, precio_unidad_cent) AS precio_cent,
                   min(precio_unidad_cent) AS precio_unidad_cent,
                   arg_min(promo_txt, precio_unidad_cent) AS promo_txt
              FROM limpio GROUP BY grupo_id)
        SELECT m.*, x.min_90d_cent, x.precio_base_cent
          FROM mejor m
          LEFT JOIN (SELECT fuente, id_fuente,
                            arg_max(min_90d_cent, fecha) AS min_90d_cent,
                            arg_max(precio_base_cent, fecha) AS precio_base_cent
                       FROM derivado GROUP BY fuente, id_fuente) x
            USING (fuente, id_fuente)
    """, list(grupos)).fetchall()
    return {f[0]: {
        "grupo_id": f[0], "cadena": f[1], "id_fuente": f[2], "nombre": f[3],
        "marca": f[4], "imagen": f[5], "unidad": f[6], "precio_cent": f[7],
        "precio_unidad_cent": round(f[8], 2), "promo_txt": f[9],
        "min_90d_cent": round(f[10], 2) if f[10] is not None else None,
        "precio_base_cent": round(f[11], 2) if f[11] is not None else None,
    } for f in filas}


def _bajadas_de_verdad(claves: list[tuple[str, str]]) -> dict[tuple[str, str], dict]:
    """Para cada producto, si su precio bajo **de verdad** en la ultima captura.

    Las cuatro condiciones de `movimientos`, escritas una sola vez y aplicadas
    igual aqui: misma unidad, misma cantidad implicita, el precio de venta
    movido y nada de factores imposibles.
    """
    if not claves:
        return {}
    con = catalogo.conexion()
    marcas = ",".join("(?, ?)" for _ in claves)
    args: list = []
    for fuente, id_fuente in claves:
        args.extend([fuente, id_fuente])
    args.extend([TOLERANCIA_CANTIDAD, FACTOR_INCREIBLE])
    filas = con.execute(f"""
        WITH quiero(fuente, id_fuente) AS (VALUES {marcas}),
        fechas AS (
            SELECT d.fuente, d.id_fuente, max(d.fecha) AS hoy,
                   max(d.fecha) FILTER (
                       WHERE d.fecha < (SELECT max(fecha) FROM diario x
                                         WHERE x.fuente = d.fuente
                                           AND x.id_fuente = d.id_fuente)) AS antes
              FROM diario d JOIN quiero q USING (fuente, id_fuente)
             GROUP BY d.fuente, d.id_fuente),
        par AS (
            SELECT f.fuente, f.id_fuente,
                   h.precio_unidad_cent AS hoy_ud, h.precio_cent AS hoy_venta,
                   h.unidad_canon AS hoy_unidad,
                   a.precio_unidad_cent AS antes_ud, a.precio_cent AS antes_venta,
                   a.unidad_canon AS antes_unidad, f.antes AS fecha_antes
              FROM fechas f
              JOIN diario h ON h.fuente = f.fuente AND h.id_fuente = f.id_fuente
                           AND h.fecha = f.hoy
              JOIN diario a ON a.fuente = f.fuente AND a.id_fuente = f.id_fuente
                           AND a.fecha = f.antes
             WHERE h.precio_unidad_cent > 0 AND a.precio_unidad_cent > 0)
        SELECT fuente, id_fuente, hoy_ud, antes_ud, fecha_antes,
               (hoy_ud < antes_ud
                AND hoy_unidad IS NOT DISTINCT FROM antes_unidad
                AND abs(hoy_venta / hoy_ud - antes_venta / antes_ud)
                    <= ? * (antes_venta / antes_ud)
                AND hoy_venta < antes_venta
                AND greatest(hoy_ud, antes_ud) / least(hoy_ud, antes_ud) < ?
               ) AS bajo
          FROM par
    """, args).fetchall()
    return {(f[0], f[1]): {"hoy": round(f[2], 2), "antes": round(f[3], 2),
                           "desde": f[4], "bajo": bool(f[5])} for f in filas}


def _por_que(alerta: dict, mejor: dict, bajada: dict | None) -> str | None:
    """La frase del aviso, o None si esta alerta no salta hoy."""
    hoy = mejor["precio_unidad_cent"]
    if alerta["tipo"] == "baja_de":
        umbral = alerta.get("umbral_cent")
        if umbral is None or hoy > umbral:
            return None
        return (f"ha bajado de {umbral / 100:.2f} EUR/{mejor['unidad']}: "
                f"hoy {hoy / 100:.2f} en {mejor['cadena']}")
    if alerta["tipo"] == "minimo_90d":
        minimo = mejor.get("min_90d_cent")
        # Sin historico suficiente no se inventa un minimo: se calla. Decir "es
        # el mas barato de 90 dias" con cinco dias de serie es mentir con datos.
        if minimo is None or hoy > minimo + 0.5:
            return None
        return (f"esta al precio mas bajo de los ultimos 90 dias: "
                f"{hoy / 100:.2f} EUR/{mejor['unidad']} en {mejor['cadena']}")
    if alerta["tipo"] == "cualquier_bajada":
        if not bajada or not bajada["bajo"]:
            return None
        pct = 100 * (bajada["hoy"] - bajada["antes"]) / bajada["antes"]
        return (f"ha bajado un {abs(pct):.1f} % desde el {bajada['desde']}: "
                f"{bajada['hoy'] / 100:.2f} EUR/{mejor['unidad']} en "
                f"{mejor['cadena']}")
    return None


def evalua(alertas: list[dict]) -> list[dict]:
    """Cuales de estas alertas saltan hoy, con la frase que las explica.

    Recibe las alertas ya leidas de PostgreSQL (este modulo no toca la base de
    datos: aqui solo se mira gold, que es de solo lectura) y devuelve las que
    saltan, cada una con el producto que la hizo saltar.

    **Esto mira gold entero y por eso es caro: no se llama en cada visita a la
    pantalla.** Para eso esta `evalua_con_memoria`, que es lo que usan la API y el
    vigilante.
    """
    if not alertas:
        return []
    grupos = sorted({int(a["grupo_id"]) for a in alertas})
    mejores = _mejor_de_cada_grupo(grupos)
    quiere_bajada = [a for a in alertas if a["tipo"] == "cualquier_bajada"]
    claves = sorted({(mejores[int(a["grupo_id"])]["cadena"],
                      mejores[int(a["grupo_id"])]["id_fuente"])
                     for a in quiere_bajada if int(a["grupo_id"]) in mejores})
    bajadas = _bajadas_de_verdad(claves)

    saltan = []
    for a in alertas:
        mejor = mejores.get(int(a["grupo_id"]))
        if not mejor:
            continue
        bajada = bajadas.get((mejor["cadena"], mejor["id_fuente"]))
        frase = _por_que(a, mejor, bajada)
        if frase:
            saltan.append({**mejor, "alerta_id": str(a["id"]), "tipo": a["tipo"],
                           "umbral_cent": a.get("umbral_cent"), "por_que": frase})
    return saltan


# --------------------------------------------------------------- la memoria ---
#
# **Por que existe esto, y esta medido.** El §6 del encargo pide *"dejar el resultado
# guardado, para que abrir la aplicacion sea instantaneo"*, y no lo era: `GET
# /api/alertas` tardaba **469 ms** (453-484 ms, cinco veces, en el PC de casa, con
# UNA sola alerta) porque `evalua` recorre el historico de 90 dias entero para juzgar
# una pregunta. En un movil por Tailscale, eso es mas todavia.
#
# La clave lleva **el sello de gold**: los precios se escriben una vez al dia, asi que
# el veredicto de una alerta no puede cambiar mientras gold no cambie. Y como el
# vigilante pasa por aqui a las 06:00 **en este mismo proceso**, la primera persona que
# abra la pantalla ya encuentra la respuesta hecha: la pasa el vigilante, no ella.
#
# Lo que se guarda **no lleva el id de nadie**: la clave es la pregunta ("este grupo,
# este tipo, este umbral") y el valor es la respuesta. Dos personas con la misma alerta
# comparten respuesta, y por eso una respuesta guardada no puede llevar dentro el
# `alerta_id` de la primera que pregunto -- el id se pone al devolver, alerta a alerta.
_memoria: dict = {"sello": None, "veredicto": {}}

# Lo que devuelve `evalua` y **no** es la respuesta a la pregunta, sino de quien
# pregunto. Se quita antes de guardar.
_DE_QUIEN_PREGUNTA = ("alerta_id", "tipo", "umbral_cent", "por_que")


def olvida() -> None:
    """Tira lo recordado. Para las pruebas y para el dia que gold cambie de golpe."""
    _memoria["sello"] = None
    _memoria["veredicto"] = {}


def _clave(alerta: dict) -> tuple:
    """La pregunta, sin quien la hace."""
    return (int(alerta["grupo_id"]), str(alerta["tipo"]), alerta.get("umbral_cent"))


def evalua_con_memoria(alertas: list[dict]) -> list[dict]:
    """`evalua`, mirando gold una vez por dia en vez de una vez por visita.

    Devuelve exactamente lo mismo que `evalua`, con el `alerta_id` de cada una.
    """
    if not alertas:
        return []
    sello = catalogo.sello_de_gold()
    if _memoria["sello"] != sello:
        # Gold nuevo: todo lo recordado es del dia anterior y ya no vale.
        olvida()
        _memoria["sello"] = sello
    veredicto: dict = _memoria["veredicto"]

    faltan = [a for a in alertas if _clave(a) not in veredicto]
    if faltan:
        # Las que faltan, **de golpe**: `evalua` mira gold una vez por llamada, asi que
        # preguntar de una en una seria mirar gold una vez por alerta.
        saltan = {s["alerta_id"]: s for s in evalua(faltan)}
        for a in faltan:
            salto = saltan.get(str(a["id"]))
            veredicto[_clave(a)] = None if salto is None else {
                "por_que": salto["por_que"],
                "mejor": {k: v for k, v in salto.items() if k not in _DE_QUIEN_PREGUNTA}}

    fuera = []
    for a in alertas:
        guardado = veredicto.get(_clave(a))
        if guardado:
            fuera.append({**guardado["mejor"], "alerta_id": str(a["id"]), "tipo": a["tipo"],
                          "umbral_cent": a.get("umbral_cent"),
                          "por_que": guardado["por_que"]})
    return fuera
