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
from datetime import date
from itertools import combinations

from core import identidad
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
    # El identificador de la linea, cuando viene de una lista de verdad. Es lo que
    # permite devolver **que** linea esta en cada sublista, para que la pantalla
    # pueda quitarla o cambiarla de tienda sin adivinar por el nombre (dos lineas
    # pueden llamarse igual: "leche" y "leche").
    id: str | None = None


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
    # De que linea de la lista sale. Viaja hasta la interfaz para que el boton de
    # «repartir en dos tiendas» pueda poner la tienda de **cada** linea y no de todas
    # (con `lineas` vacio la API las pone todas en una sola, que es otra cosa).
    linea_id: str | None = None
    # **Si el producto propuesto es el que se pidio, y si no, por que.** La regla del encargo hecha
    # dato: `exacto` es el mismo producto; `probable`, que lo parece sin GTIN que lo confirme; y
    # `alternativa`, `cuarentena` o `abstiene` significan que NO es el mismo y que sustituirlo exige
    # una eleccion explicita de quien compra.
    identidad: str | None = None
    motivo: str | None = None


def _candidatos(peticiones: list[Peticion], fecha_tope: str) -> dict:
    """Por cada linea y cadena, el producto mas barato que la resuelve."""
    con = conexion()
    grupos = [p.grupo_id for p in peticiones if p.grupo_id is not None]
    sueltos = [p.producto_id for p in peticiones if p.producto_id]
    filas = []
    if grupos:
        filas += con.execute(f"""
            SELECT grupo_id, NULL, fuente, fuente || ':' || id_fuente, nombre,
                   precio_cent, precio_unidad_cent, comparacion_fiable, ean, marca
              FROM grupos
             WHERE grupo_id IN ({','.join('?' * len(grupos))}) AND precio_cent > 0
        """, grupos).fetchall()
    if sueltos:
        filas += con.execute(f"""
            SELECT NULL, fuente || ':' || id_fuente, fuente,
                   fuente || ':' || id_fuente, nombre,
                   precio_cent, precio_unidad_cent, comparacion_fiable, ean, marca
              FROM grupos
             WHERE fuente || ':' || id_fuente IN ({','.join('?' * len(sueltos))})
               AND precio_cent > 0
        """, sueltos).fetchall()

    # La promocion vigente de cada producto, del ultimo silver.
    promos = _promos_vigentes({f[3] for f in filas}, fecha_tope)

    mejor: dict = {}
    canonico: dict = {}
    for gid, pid_suelto, fuente, pid, nombre, precio, _punit, _fiable, ean, marca in filas:
        clave = (gid if gid is not None else pid_suelto, fuente)
        actual = mejor.get(clave)
        if actual is None or precio < actual[1]:
            # Seis campos: los cuatro de siempre, **el GTIN de esta fila** -- que es el producto que
            # se va a proponer -- y el canonico del grupo, que se rellena al final.
            mejor[clave] = (pid, precio, nombre, promos.get(pid), ean, None, marca)
        # **El canonico es el de menor identificador**, y no el primero que devuelva el SQL: asi la
        # referencia es la misma entre ejecuciones, que es lo que hace reproducible el veredicto.
        if clave not in canonico or str(pid) < str(canonico[clave][0]):
            canonico[clave] = (pid, nombre, ean, marca)
    for clave, (pid, nombre, ean, marca) in canonico.items():
        actual = mejor.get(clave)
        if actual is not None:
            mejor[clave] = (*actual[:5], identidad.Producto(
                fuente=clave[1], id_fuente=str(pid), nombre=nombre, gtin=ean, marca=marca), marca)
    return mejor


def _fecha_de_hoy() -> str:
    """La fecha de referencia de una peticion: hoy. En un sitio, para que sea la misma siempre."""
    return date.today().isoformat()


def _ultima_fecha_silver(hasta: str | None = None) -> str | None:
    """La fecha de la ultima particion que hay escrita en silver, o `None`.

    Se mira **en el disco y no en los ficheros**: el nombre de la carpeta ya lo dice
    (`data/silver/fuente=dia/fecha=2026-09-28/...`), y abrir los parquet para preguntarles una
    fecha que esta en su ruta es leer 105 MB para nada.

    **Esto es el arreglo de una lentitud medida.** Hasta el 27 de septiembre de 2026 la consulta
    de las ofertas hacia `WHERE fecha = (SELECT max(fecha) FROM read_parquet('...silver/**'))`,
    o sea **un recorrido entero de silver dos veces en cada peticion** (1.066.573 filas, 106
    particiones, 105 MB) para quedarse con el ultimo dia. Medido **dentro del contenedor** con
    `data/debug/silver.py` (que es donde importa: silver llega por el montaje de Docker en
    Windows y cada lectura cuesta mas que en el disco del PC): **2,10 s la consulta de antes y
    0,04 s la de ahora**, con el mismo resultado (7.908 ofertas).

    Y no se pagaba una vez: `_candidatos` llama aqui, asi que la pagaban **los tres endpoints de
    la cesta**. Medido con `data/debug/peticiones.py`: `/api/listas/{id}` 2,07 s, `/donde` 2,66 s
    y `/reparto` 4,50 s, y la pantalla de la lista (que pide las tres a la vez) tardaba **4,3 s**
    en quedarse quieta -- justo la pantalla que se usa de pie en la tienda. El comentario de
    `_promos_vigentes` ya decia «se lee la particion del dia mas reciente»: ahora es verdad.
    """
    silver = AJUSTES.gold.parent / "silver"
    ultima: str | None = None
    for ruta in silver.glob("fuente=*/fecha=*"):
        fecha = ruta.name.removeprefix("fecha=")
        # **El tope.** Una particion posterior a la fecha de referencia no se elige: sus ofertas
        # todavia no estaban vigentes, y aplicarlas seria enseñar un precio que aun no existe.
        if hasta and fecha > hasta:
            continue
        if ultima is None or fecha > ultima:
            ultima = fecha
    return ultima


# Las ofertas del ultimo dia, ya leidas: `{producto: texto}`. Se guarda **por fecha**, porque el
# dia que silver tenga otra particion hay que volver a leer, y sin esto una pasada del dia no se
# veria hasta reiniciar el contenedor.
_PROMOS_POR_FECHA: dict[str, dict[str, str]] = {}


def _promos_vigentes(producto_ids: set[str], fecha_tope: str | None = None) -> dict[str, str]:
    """El texto de oferta de cada producto, si lo hay.

    Vive en silver y no en gold, porque gold se queda con lo que sirve para
    comparar. Se lee la particion del dia mas reciente y ya esta (y se guarda: los
    precios se escriben una vez al dia).
    """
    if not producto_ids:
        return {}
    try:
        fecha = _ultima_fecha_silver(fecha_tope)
        if fecha is None:
            return {}
        tabla = _PROMOS_POR_FECHA.get(fecha)
        if tabla is None:
            con = conexion()
            dia = AJUSTES.gold.parent / "silver" / "fuente=*" / f"fecha={fecha}" / "*.parquet"
            # A barras normales: DuckDB en Windows acepta las dos, pero la ruta se compone con el
            # separador del sistema y el SQL se lee mejor con una sola forma.
            ruta = str(dia).replace("\\", "/")
            filas = con.execute(f"""
                SELECT fuente || ':' || id_fuente, promo_txt
                  FROM read_parquet('{ruta}', hive_partitioning=1)
                 WHERE promo_txt IS NOT NULL
            """).fetchall()
            tabla = {f[0]: f[1] for f in filas}
            _PROMOS_POR_FECHA.clear()
            _PROMOS_POR_FECHA[fecha] = tabla
    except Exception:  # noqa: BLE001 - sin silver, sin ofertas, pero el
        # calculo de la cesta tiene que seguir dando un total.
        return {}
    return {k: v for k, v in tabla.items() if k in producto_ids}


def _resolver(peticion: Peticion, fuente: str, mejor: dict) -> Eleccion | None:
    clave = (peticion.grupo_id if peticion.grupo_id is not None else peticion.producto_id, fuente)
    hallado = mejor.get(clave)
    if hallado is None:
        return None
    pid, precio, nombre, promo_txt, ean, referencia, marca = [*hallado, None, None, None][:7]
    # **El veredicto, antes de proponer nada.** Si no es el mismo producto, el coste que sigue es el
    # de una alternativa, y eso tiene que viajar en la respuesta para que nadie lo sustituya callando.
    veredicto = None
    if referencia is not None:
        propuesto = identidad.Producto(fuente=fuente, id_fuente=str(pid), nombre=nombre,
                                      gtin=ean, marca=marca)
        veredicto = identidad.decide(referencia, propuesto)
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
                    promo_txt if mecanica.util else None, sugerencia,
                    linea_id=peticion.id,
                    identidad=veredicto["estado"] if veredicto else None,
                    motivo="; ".join(veredicto["motivos"]) if veredicto else None)


def donde_comprar(peticiones: list[Peticion],
                  cadenas: list[str] | None = None,
                  max_tiendas: int | None = None) -> dict:
    """Las dos respuestas: en una tienda, y repartido."""
    if not peticiones:
        return {"una_tienda": [], "repartido": None, "lineas": 0}
    disponibles = [c for c in (cadenas or CADENAS) if c in CADENAS]
    max_t = max_tiendas or AJUSTES.max_tiendas
    mejor = _candidatos(peticiones, _fecha_de_hoy())

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


def reparto_por_tienda(peticiones: list[Peticion],
                       asignadas: list[str | None],
                       cadenas: list[str] | None = None) -> dict:
    """La lista partida en sublistas: una por tienda **elegida**.

    Es lo que pidio el dueno el 25 de septiembre de 2026, y es otra pregunta que
    `donde_comprar`: aquello propone donde sale mas barata la lista entera; esto
    **respeta lo que la persona ya ha decidido** («el pan en DIA, que me pilla de
    camino») y enseña tres cosas:

      - cada sublista con su precio final, con las ofertas aplicadas **y separadas**
        de lo que costaria sin ellas, para poder decir cuanto ahorran;
      - el total de la lista entera, que es la suma de las sublistas;
      - lo que queda **sin decidir**, con la opcion mas barata de cada cosa al lado,
        para poder decidirlo.

    Una linea asignada a una tienda donde no hay nada que la resuelva no suma: se
    dice por su nombre («en Mercadona no lo hay»), que es la misma regla de
    `donde_comprar`. Una linea **sin decidir** tampoco suma al total: sumarla por
    la mas barata daria un total que no se corresponde con ninguna compra posible.

    Las ofertas se aplican con `core.promos`, que sabe que una oferta es una regla
    sobre cuantas unidades compras: "2a unidad -50%" no abarata el producto, abarata
    el par, y con `cantidad=1` no se aplica.
    """
    disponibles = [c for c in (cadenas or CADENAS) if c in CADENAS]
    mejor = _candidatos(peticiones, _fecha_de_hoy())
    sublistas: dict[str, list[dict]] = {}
    sin_encontrar: dict[str, list[str]] = {}
    sin_asignar: list[dict] = []
    total = total_sin = 0
    resueltas = 0

    for peticion, elegida in zip(peticiones, asignadas, strict=True):
        opciones = {c: _resolver(peticion, c, mejor) for c in disponibles}
        hay = {c: e for c, e in opciones.items() if e is not None}
        if elegida is None:
            if not hay:
                sin_asignar.append(_sin_asignar(peticion, {}, None, False))
                continue
            barata = min(hay, key=lambda c: hay[c].coste_cent)
            sin_asignar.append(_sin_asignar(peticion, hay, barata, True))
            continue
        eleccion = hay.get(elegida)
        if eleccion is None:
            sin_encontrar.setdefault(elegida, []).append(peticion.nombre)
            continue
        fila = _serializa(eleccion) | {
            "linea_id": peticion.id,
            "cantidad": peticion.cantidad,
            "opciones": _opciones(hay),
            "elegida": elegida,
            # Lo que costaria lo mismo en las otras tiendas, para poder cambiar sin
            # abrir otra pantalla: es la pregunta que se hace de pie en el pasillo.
            "mas_barata": min(hay, key=lambda c: hay[c].coste_cent),
        }
        sublistas.setdefault(elegida, []).append(fila)
        total += eleccion.coste_cent
        total_sin += eleccion.coste_sin_oferta_cent
        resueltas += 1

    salida = []
    for cadena in disponibles:
        filas = sublistas.get(cadena, [])
        # Una tienda con lineas que **no tiene** sale igual, con cero y con el
        # motivo: si no, la linea desaparece de la pantalla y parece que se ha
        # borrado sola. Es la misma regla que `donde_comprar` ("faltan, dichos por
        # su nombre") aplicada a lo que ya se ha decidido.
        if not filas and not sin_encontrar.get(cadena):
            continue
        gastado = sum(f["coste_cent"] for f in filas)
        sin_oferta = sum(f["coste_sin_oferta_cent"] for f in filas)
        salida.append({
            "cadena": cadena,
            "lineas": filas,
            "unidades": sum(f["cantidad"] for f in filas),
            "total_cent": gastado,
            "total_sin_ofertas_cent": sin_oferta,
            "ahorro_cent": sin_oferta - gastado,
            # Las ofertas que de verdad se aplican en esta sublista, con lo que
            # ahorran cada una: es la explicacion que se pide al enseñar el precio.
            "ofertas": [
                {"nombre": f["nombre"], "promo": f["promo"],
                 "ahorro_cent": f["coste_sin_oferta_cent"] - f["coste_cent"]}
                for f in filas
                if f["promo"] and f["coste_sin_oferta_cent"] > f["coste_cent"]
            ],
            "sin_encontrar": sin_encontrar.get(cadena, []),
        })
    salida.sort(key=lambda x: (-x["total_cent"], x["cadena"]))

    # Lo que costaria si no se hubiera decidido nada: es la comparacion honesta
    # («asi pagas 41,20; todo en DIA serian 39,80»), y sale de la funcion de al lado.
    referencia = donde_comprar(peticiones, disponibles) if peticiones else {}
    return {
        "sublistas": salida,
        "sin_asignar": sin_asignar,
        # Arriba y aparte, para que ninguna linea pueda desaparecer sin decirlo.
        "sin_encontrar": [{"cadena": c, "nombres": n} for c, n in sin_encontrar.items()],
        "total_cent": total,
        "total_sin_ofertas_cent": total_sin,
        "ahorro_cent": total_sin - total,
        "lineas": len(peticiones),
        "decididas": resueltas,
        "sin_precio": len([x for x in sin_asignar if not x["hay_precio"]]),
        "una_tienda": referencia.get("una_tienda", []),
        "repartido": referencia.get("repartido"),
    }


def _opciones(hay: dict) -> list[dict]:
    """Lo que cuesta esta misma linea en cada tienda, de mas barata a mas cara."""
    return [{"cadena": c, "coste_cent": e.coste_cent,
             "coste_sin_oferta_cent": e.coste_sin_oferta_cent, "promo": e.promo_txt}
            for c, e in sorted(hay.items(), key=lambda x: x[1].coste_cent)]


def _sin_asignar(peticion: Peticion, hay: dict, barata: str | None, hay_precio: bool) -> dict:
    return {"linea_id": peticion.id, "nombre": peticion.nombre,
            "cantidad": peticion.cantidad,
            "hay_precio": hay_precio, "mas_barata": barata,
            "coste_cent": hay[barata].coste_cent if barata else None,
            "producto_id": hay[barata].producto_id if barata else None,
            "opciones": _opciones(hay)}


def _serializa(e: Eleccion) -> dict:
    return {"producto_id": e.producto_id, "nombre": e.nombre, "cadena": e.fuente,
            "unidades": e.unidades, "coste_cent": e.coste_cent,
            "coste_sin_oferta_cent": e.coste_sin_oferta_cent,
            "promo": e.promo_txt, "sugerencia": e.sugerencia,
            "linea_id": e.linea_id}


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
    mejor = _candidatos(peticiones, _fecha_de_hoy())
    total = en_carro = sin_precio = 0
    for linea, peticion in zip(lineas, peticiones, strict=True):
        # **Una linea que apunta a otro producto no se cuenta.** El `grupo_id` es un
        # ordinal que se renumera en cada pasada, asi que esta linea puede estar
        # apuntando a un pintalabios cuando dice «leche entera»: sumarle su precio
        # seria meter un numero falso en el total. Cuenta como «sin precio», que ya
        # es una cara que la pantalla sabe enseñar. Ver `catalogo.lineas_movidas`.
        if linea.get("producto_movido"):
            sin_precio += 1
            continue
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


def coste_por_linea(lineas: list[dict]) -> dict[str, dict]:
    """Lo que cuesta **cada linea**, por separado, para guardarlo al cerrar la compra.

    Es la misma cuenta que `estimacion` -- el candidato mas barato de cada linea -- pero
    linea a linea, que es lo que hace falta para guardar una compra con sus precios. La
    diferencia es cual se elige: **si la linea tiene tienda decidida (`cadena_elegida`), se
    guarda el precio de esa tienda**; si no la tiene, el mas barato de hoy. Guardar la mas
    barata cuando alguien decidio comprarlo en DIA apuntaria un precio que no se pago.

    Devuelve `{linea_id: {"cadena", "precio_cent"}}`, y `precio_cent` es **None** cuando no
    hay precio que dar: la linea apunta a otro producto (`producto_movido`, el caso de
    `catalogo.lineas_movidas`) o el producto no esta en el catalogo. Quien lo guarde lo
    cuenta aparte -- un cero ahi seria afirmar que salio gratis.
    """
    salida: dict[str, dict] = {}
    if not lineas:
        return salida
    peticiones = [Peticion(x.get("grupo_id"), x.get("producto_id"),
                           x.get("cantidad", 1), x.get("nombre_visto", "")) for x in lineas]
    mejor = _candidatos(peticiones, _fecha_de_hoy())
    for linea, peticion in zip(lineas, peticiones, strict=True):
        cadena = precio = None
        if not linea.get("producto_movido"):
            clave = peticion.grupo_id if peticion.grupo_id is not None else peticion.producto_id
            suyos = [(fuente, v[1]) for (k, fuente), v in mejor.items() if k == clave]
            elegida = linea.get("cadena_elegida")
            if elegida and any(f == elegida for f, _ in suyos):
                cadena, precio = elegida, next(p for f, p in suyos if f == elegida)
            elif suyos:
                cadena, precio = min(suyos, key=lambda par: par[1])
        salida[str(linea.get("id"))] = {"cadena": cadena, "precio_cent": precio}
    return salida
