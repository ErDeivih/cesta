"""Donde sale mas barata la lista. La consulta que justifica el proyecto.

Dos respuestas, y hay que dar las dos porque la buena depende del dia:

    TODO EN UNA TIENDA    lo que cuesta la lista entera en cada cadena, y que
                          le falta a cada una, dicho por su nombre
    REPARTIDO             la mejor combinacion de dos tiendas

No es aprendizaje automatico ni falta que hace: con cinco cadenas y un maximo de
dos tiendas son diez combinaciones. Se calculan todas y se coge la mejor.

Lo que si tiene miga, y esta resuelto aqui, es que **una oferta no es un precio:
es una regla sobre cuantas unidades compras**. "2a unidad -50%" no abarata el
producto, abarata el par. Sin eso, el reparto sale peor que el real.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from core.promos import lee as lee_promo

from .ajustes import AJUSTES
from .catalogo import conexion

CADENAS = ("alcampo", "aldi", "carrefour", "dia", "mercadona")


@dataclass
class Peticion:
    """Una linea de la lista: que se quiere y cuanto."""
    grupo_id: int | None
    producto_id: str | None
    cantidad: int
    nombre: str


@dataclass
class Eleccion:
    """Que producto concreto resuelve una linea en una cadena dada."""
    producto_id: str
    nombre: str
    fuente: str
    unidades: int
    coste_cent: int
    coste_sin_oferta_cent: int
    promo_txt: str | None
    sugerencia: str | None


def _candidatos(peticiones: list[Peticion], fecha_tope: str) -> dict:
    """Por cada linea y cadena, el producto mas barato que la resuelve."""
    con = conexion()
    grupos = [p.grupo_id for p in peticiones if p.grupo_id is not None]
    sueltos = [p.producto_id for p in peticiones if p.producto_id]
    filas = []
    if grupos:
        filas += con.execute(f"""
            SELECT grupo_id, NULL, fuente, fuente || ':' || id_fuente, nombre,
                   precio_cent, precio_unidad_cent, comparacion_fiable
              FROM grupos
             WHERE grupo_id IN ({','.join('?' * len(grupos))}) AND precio_cent > 0
        """, grupos).fetchall()
    if sueltos:
        filas += con.execute(f"""
            SELECT NULL, fuente || ':' || id_fuente, fuente,
                   fuente || ':' || id_fuente, nombre,
                   precio_cent, precio_unidad_cent, comparacion_fiable
              FROM grupos
             WHERE fuente || ':' || id_fuente IN ({','.join('?' * len(sueltos))})
               AND precio_cent > 0
        """, sueltos).fetchall()

    # La promocion vigente de cada producto, del ultimo silver.
    promos = _promos_vigentes({f[3] for f in filas})

    mejor: dict = {}
    for gid, pid_suelto, fuente, pid, nombre, precio, _punit, _fiable in filas:
        clave = (gid if gid is not None else pid_suelto, fuente)
        actual = mejor.get(clave)
        if actual is None or precio < actual[1]:
            mejor[clave] = (pid, precio, nombre, promos.get(pid))
    return mejor


def _promos_vigentes(producto_ids: set[str]) -> dict[str, str]:
    """El texto de oferta de cada producto, si lo hay.

    Vive en silver y no en gold, porque gold se queda con lo que sirve para
    comparar. Se lee la particion del dia mas reciente y ya esta.
    """
    if not producto_ids:
        return {}
    con = conexion()
    ruta = str(AJUSTES.gold.parent / "silver" / "**" / "*.parquet").replace("\\", "/")
    try:
        filas = con.execute(f"""
            SELECT fuente || ':' || id_fuente, promo_txt
              FROM read_parquet('{ruta}', hive_partitioning=1)
             WHERE fecha = (SELECT max(fecha) FROM read_parquet('{ruta}', hive_partitioning=1))
               AND promo_txt IS NOT NULL
        """).fetchall()
    except Exception:  # noqa: BLE001 - sin silver, sin ofertas, pero el
        # calculo de la cesta tiene que seguir dando un total.
        return {}
    return {f[0]: f[1] for f in filas if f[0] in producto_ids}


def _resolver(peticion: Peticion, fuente: str, mejor: dict) -> Eleccion | None:
    clave = (peticion.grupo_id if peticion.grupo_id is not None else peticion.producto_id, fuente)
    hallado = mejor.get(clave)
    if hallado is None:
        return None
    pid, precio, nombre, promo_txt = hallado
    mecanica = lee_promo(promo_txt)
    sin_oferta = peticion.cantidad * precio
    coste = mecanica.coste(peticion.cantidad, precio)

    # "Llevate una mas": solo cuando anadir una unidad baja el precio unitario.
    sugerencia = None
    if mecanica.util:
        from core.promos import unidades_optimas
        n = unidades_optimas(mecanica, peticion.cantidad)
        if n > peticion.cantidad:
            ahorro = round(coste / peticion.cantidad - mecanica.coste(n, precio) / n)
            if ahorro > 0:
                sugerencia = (f"llevando {n} en vez de {peticion.cantidad}, "
                              f"{ahorro / 100:.2f} EUR menos por unidad")
    return Eleccion(pid, nombre, fuente, peticion.cantidad, coste, sin_oferta,
                    promo_txt if mecanica.util else None, sugerencia)


def donde_comprar(peticiones: list[Peticion],
                  cadenas: list[str] | None = None,
                  max_tiendas: int | None = None) -> dict:
    """Las dos respuestas: en una tienda, y repartido."""
    if not peticiones:
        return {"una_tienda": [], "repartido": None, "lineas": 0}
    disponibles = [c for c in (cadenas or CADENAS) if c in CADENAS]
    max_t = max_tiendas or AJUSTES.max_tiendas
    mejor = _candidatos(peticiones, "")

    # Cada cadena, por su cuenta.
    por_cadena: dict[str, list[Eleccion | None]] = {}
    for fuente in disponibles:
        por_cadena[fuente] = [_resolver(p, fuente, mejor) for p in peticiones]

    una_tienda = []
    for fuente, elecciones in por_cadena.items():
        tiene = [e for e in elecciones if e]
        faltan = [p.nombre for p, e in zip(peticiones, elecciones, strict=True) if not e]
        if not tiene:
            continue
        una_tienda.append({
            "cadena": fuente,
            "total_cent": sum(e.coste_cent for e in tiene),
            "total_sin_ofertas_cent": sum(e.coste_sin_oferta_cent for e in tiene),
            "encontrados": len(tiene),
            "faltan": faltan,          # por su nombre, no como un numero
            "productos": [_serializa(e) for e in tiene],
        })
    # Primero las que lo tienen todo, y dentro de esas la mas barata.
    una_tienda.sort(key=lambda x: (len(x["faltan"]), x["total_cent"]))

    repartido = _mejor_reparto(peticiones, por_cadena, max_t, una_tienda)
    return {"una_tienda": una_tienda, "repartido": repartido, "lineas": len(peticiones)}


def _mejor_reparto(peticiones, por_cadena, max_tiendas, una_tienda) -> dict | None:
    """La mejor combinacion de hasta `max_tiendas`, si gana a ir a una sola."""
    if max_tiendas < 2 or len(por_cadena) < 2:
        return None
    completas = [x for x in una_tienda if not x["faltan"]]
    referencia = completas[0]["total_cent"] if completas else None

    mejor = None
    for combo in combinations(sorted(por_cadena), min(max_tiendas, len(por_cadena))):
        total, eleccion, faltan = 0, [], []
        for i, p in enumerate(peticiones):
            opciones = [por_cadena[c][i] for c in combo if por_cadena[c][i]]
            if not opciones:
                faltan.append(p.nombre)
                continue
            e = min(opciones, key=lambda x: x.coste_cent)
            total += e.coste_cent
            eleccion.append(e)
        if not eleccion:
            continue
        usadas = sorted({e.fuente for e in eleccion})
        if len(usadas) < 2:
            continue                       # no es un reparto, es una tienda
        if mejor is None or (len(faltan), total) < (len(mejor["faltan"]), mejor["total_cent"]):
            mejor = {"cadenas": usadas, "total_cent": total, "faltan": faltan,
                     "productos": [_serializa(e) for e in eleccion],
                     "reparto": {c: sum(1 for e in eleccion if e.fuente == c) for c in usadas}}
    if mejor is None:
        return None
    if referencia is not None:
        mejor["ahorro_cent"] = referencia - mejor["total_cent"]
        # Ir a dos tiendas cuesta tiempo. Si el ahorro es ridiculo, se dice.
        mejor["merece_la_pena"] = mejor["ahorro_cent"] >= 150
    return mejor


def _serializa(e: Eleccion) -> dict:
    return {"producto_id": e.producto_id, "nombre": e.nombre, "cadena": e.fuente,
            "unidades": e.unidades, "coste_cent": e.coste_cent,
            "coste_sin_oferta_cent": e.coste_sin_oferta_cent,
            "promo": e.promo_txt, "sugerencia": e.sugerencia}


def estimacion(lineas: list[dict]) -> dict:
    """Lo que va a costar la lista, ahora mismo, cogiendo cada cosa donde este
    mas barata.

    No es el calculo de "donde la compro": eso pide ir a una tienda o a dos y
    tiene en cuenta lo que le falta a cada una. Esto es el numero que se mira
    mientras se anaden cosas, y por eso tiene que salir siempre y rapido.
    """
    if not lineas:
        return {"total_cent": 0, "en_carrito_cent": 0, "por_recoger_cent": 0,
                "lineas": 0, "sin_precio": 0}
    peticiones = [Peticion(x.get("grupo_id"), x.get("producto_id"),
                           x.get("cantidad", 1), x.get("nombre_visto", "")) for x in lineas]
    mejor = _candidatos(peticiones, "")
    total = en_carro = sin_precio = 0
    for linea, peticion in zip(lineas, peticiones, strict=True):
        clave = peticion.grupo_id if peticion.grupo_id is not None else peticion.producto_id
        precios = [v[1] for (k, _), v in mejor.items() if k == clave]
        if not precios:
            sin_precio += 1
            continue
        coste = min(precios) * peticion.cantidad
        total += coste
        if linea.get("en_carrito") or linea.get("tachado_en"):
            en_carro += coste
    return {"total_cent": total, "en_carrito_cent": en_carro,
            "por_recoger_cent": total - en_carro, "lineas": len(lineas),
            "sin_precio": sin_precio}
