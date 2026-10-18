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

from dataclasses import dataclass, replace
from datetime import date
from itertools import combinations, product

from core import identidad
from core.promos import lee as lee_promo

from .ajustes import AJUSTES
from .catalogo import conexion

# **Las cadenas, y la distincion que faltaba.** *Esto era una sola tupla de cinco, y al lado
# `projects/cesta/run.py` tenia `ORDEN` con seis* -- *porque Lidl entra en la captura. La diferencia
# entre las dos listas **no estaba dicha en ningun sitio**, asi que se leia como un descuido.*
#
# **Y no es un descuido: son dos cosas distintas.**
#
#   - **`CADENAS_QUE_SE_CAPTURAN`**: de las que hay colector y se les pide el catalogo. *Seis.*
#   - **`CADENAS`**: de las que se puede **comparar precios**. *Cinco.*
#
# **Por que Lidl no esta en la segunda, y no es una decision pendiente.** *`collectors/lidl.py` publica
# **ofertas semanales parciales**, no el surtido completo.* *Meterlo en las comparaciones haria que
# pareciera tener precio para cosas que no cataloga* -- **y un «Lidl no lo tiene» que en realidad es «no
# lo hemos capturado» es exactamente la clase de mentira que esta fase lleva cazando.** *Se declara
# capturada y no comparable, y se dice por que.*
#
# **Y la lista esta repetida en `projects/cesta/auditar_escurrido.py` y `projects/cesta/peticiones.py`**
# -- *no se unifica aqui porque `projects/` no importa de `plataforma/`, y forzar esa dependencia para
# tres tuplas seria peor que la repeticion.* **Lo que si se hace es nombrar la distincion en las tres,
# para que quien lea una sepa que existen las otras dos.**
CADENAS_QUE_SE_CAPTURAN = ("carrefour", "dia", "mercadona", "aldi", "alcampo", "lidl")

# *Y esta es la que decide si un precio entra en una comparacion.*
CADENAS = ("alcampo", "aldi", "carrefour", "dia", "mercadona")


def por_que_no_se_compara(cadena: str) -> str | None:
    """El motivo por el que una cadena capturada no entra en las comparaciones.

    *Devuelve `None` si si se compara.* **Existe para que la pantalla pueda decir por que falta una
    cadena, en vez de dejarla simplemente ausente** -- *que es lo que A05 pide con «mantener la
    cobertura parcial visible donde proceda».*
    """
    if cadena in CADENAS:
        return None
    if cadena == "lidl":
        return ("Lidl se captura, pero publica **ofertas semanales parciales**, no el surtido completo: "
                "sus precios no entran en la comparación porque no cubren el catálogo.")
    return f"{cadena} no es una cadena conocida."


if __name__ != "__main__":  # pragma: no cover
    # **Una comprobacion al importar, y es barata**: *la lista comparable tiene que estar DENTRO de la
    # capturable.* *Si alguien anade una cadena a `CADENAS` sin colector, se sabe aqui y no al comparar.*
    _sobran = [c for c in CADENAS if c not in CADENAS_QUE_SE_CAPTURAN]
    if _sobran:  # pragma: no cover
        raise RuntimeError(f"estas cadenas se comparan pero no se capturan: {', '.join(_sobran)}")


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
    # **Autorizacion explicita de sustituir ESTA linea.** Va por linea y no por lista a proposito: se
    # autoriza una sustitucion concreta, no "lo que haga falta" en toda la compra.
    autorizado: bool = False
    # **Que se acepto**, no solo que se acepto: el producto y la cadena que la persona confirmo.
    autorizado_producto: str | None = None
    autorizado_cadena: str | None = None


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
    # **Si esta eleccion puede contar en un total exacto.** Un aviso no es una autorizacion: si no es el
    # producto que se pidio y nadie lo ha autorizado, cuenta cero para el total y se dice por que.
    autorizada: bool = True
    # **La opcion que se puede ofrecer**, cuando esta no es el producto pedido: la mas barata de las que
    # no son exactas, con su motivo. `None` si no hay ninguna. Ofrecerla es lo que evita el callejon sin
    # salida: se dice que no cuenta, y se dice que se puede pedir en su lugar.
    alternativa: dict | None = None


def _coste_para(cantidad: int, precio_cent: int, promo_txt: str | None) -> int:
    """Lo que cuesta **la cantidad que se pide** con esa promocion. Es la regla de la eleccion.

    **Por que no basta el precio unitario.** Para dos unidades, un envase de 1,00 EUR con "2a unidad -50%"
    cuesta 150 cent y uno de 0,90 EUR sin promocion cuesta 180: el mas barato por unidad es el **mas caro**
    al pagar. Retener el menor precio unitario antes de mirar la promocion descarta la oferta buena.

    Es una funcion aparte porque es pura: se prueba con numeros, sin base de datos ni peticiones.
    """
    if not promo_txt:
        return cantidad * precio_cent
    return lee_promo(promo_txt).coste(cantidad, precio_cent)


def _prefiere(exacta_nueva: bool, coste_nuevo: int, exacta_actual: bool, coste_actual: int) -> bool:
    """Si la fila nueva sustituye a la que ya estaba en ese hueco.

    **Una exacta gana siempre a una que no lo es**, aunque cueste mas: la regla del encargo es que elegir un
    producto concreto no autoriza a sustituirlo, y para el total la alternativa no cuenta de todas formas,
    asi que preferirla solo servia para perder el producto bueno. Entre dos del mismo tipo, la mas barata.
    """
    if exacta_nueva != exacta_actual:
        return exacta_nueva
    return coste_nuevo < coste_actual


def _llave(peticion: Peticion) -> tuple:
    """La identidad que pide la linea: **el grupo y el producto concreto, si consta**."""
    return (peticion.grupo_id, peticion.producto_id)


def _llave_candidato(dueno, pedida, fuente) -> tuple:
    """**La llave de `mejor`, en un solo sitio.** El que guarda y el que busca pasan por aqui.

    **Sin producto concreto, la llave es la del grupo** -- `(grupo, cadena)` --: una linea que pide el grupo
    tiene por identidad el grupo, y esa es la forma que ya usaba el motor. Con producto concreto la llave lo
    lleva dentro, y ahi esta el arreglo del caso 3: dos articulos del mismo grupo dejan de pisarse.
    """
    if pedida is None:
        return (dueno, fuente)
    return ((dueno, pedida), fuente)


def _tiene_region(con) -> bool:
    """**Si `grupos` trae la zona.** *Y hasta que no la traiga, no se pide.*

    *Esto no es una precaucion de mas: es la forma de que el cambio de B03 **no rompa nada hoy y funcione solo
    el dia que toque**.*

    **El 13 de octubre de 2026 se intento anadir `region` a estas consultas directamente, y rompio seis pruebas
    de tres ficheros** -- *con este error, que lo dijo todo:*

    ```
    _duckdb.BinderException: Referenced column "region" not found in FROM clause!
    Candidate bindings: "precio_cent", "seccion", "nutricion", "precio_unidad_cent", "origen"
    ```

    *Porque `grupos` **no sale de la serie de precios**: sale de `gold/grupos.parquet`, que lo escribe el
    **emparejador** (`projects/cesta/emparejar.py`).* **Y ese fichero no la tiene todavia.**

    *Asi que la columna se pide **si esta**, y el dia que el emparejador la escriba, **llega sola** -- sin tocar
    esta funcion otra vez.*

    *Y `origen` no vale como sustituta*: **es el pais de fabricacion, no la zona del precio.** *Confundirlas
    seria el mismo error que «IAN no es EAN».*
    """
    # *Y con `[]` de parametros, no sin ellos*: `_Conexion.execute` **los pide**, y las conexiones de prueba
    # tambien -- *`TypeError: execute() missing 1 required positional argument: 'params'`, que es lo que salto
    # al poner esta linea sin ellos.*
    columnas = {r[0] for r in con.execute("DESCRIBE SELECT * FROM grupos", []).fetchall()}
    return "region" in columnas


def _candidatos(peticiones: list[Peticion], fecha_tope: str) -> dict:
    """Por cada linea y cadena, el producto mas barato que la resuelve."""
    con = conexion()
    grupos = [p.grupo_id for p in peticiones if p.grupo_id is not None]
    sueltos = [p.producto_id for p in peticiones if p.producto_id]
    # **La zona, AL FINAL del `SELECT` -- y solo si existe.**
    #
    # *Al final a proposito*: los diez campos de antes **no se mueven**, asi que **ningun indice de los que ya
    # se leen cambia de sitio**. *Y se comprobo que esa era la forma correcta: **el error del 13 de octubre no
    # fue de indices**, fue de una columna que no existia.*
    col = ", region" if _tiene_region(con) else ""
    filas = []
    if grupos:
        filas += con.execute(f"""
            SELECT grupo_id, NULL, fuente, fuente || ':' || id_fuente, nombre,
                   precio_cent, precio_unidad_cent, comparacion_fiable, ean, marca{col}
              FROM grupos
             WHERE grupo_id IN ({','.join('?' * len(grupos))}) AND precio_cent > 0
        """, grupos).fetchall()
    if sueltos:
        filas += con.execute(f"""
            SELECT NULL, fuente || ':' || id_fuente, fuente,
                   fuente || ':' || id_fuente, nombre,
                   precio_cent, precio_unidad_cent, comparacion_fiable, ean, marca{col}
              FROM grupos
             WHERE fuente || ':' || id_fuente IN ({','.join('?' * len(sueltos))})
               AND precio_cent > 0
        """, sueltos).fetchall()

    # La promocion vigente de cada producto, del ultimo silver.
    promos = _promos_vigentes({f[3] for f in filas}, fecha_tope)

    # **La cantidad que se pide de cada referencia.** Si la misma apareciera en dos lineas con
    # cantidades distintas, manda la ultima: es una decision, no un descuido.
    # **Las lineas del mismo producto se compran juntas.** La cantidad que decide que oferta
    # conviene es la SUMA de todas sus lineas, no la de la ultima: pedir 2 y 3 es pedir 5.
    cantidades = _cantidades_por_referencia(peticiones)

    # **Que pide cada linea.** El grupo y, si consta, el producto concreto.
    claves: set = {_llave(p) for p in peticiones}

    # La ficha de cada fila por su identificador, para buscar la del producto pedido.
    fichas = {fila[3]: (fila[3], fila[4], fila[8], fila[9]) for fila in filas}

    # **Una referencia por grupo, la misma en todas las cadenas.** Antes la clave incluia la
    # cadena, asi que la referencia se movia con la tienda: el mismo candidato podia salir exacto
    # en una y alternativa en otra, y los veredictos de dos cadenas no eran comparables.
    canonico = _canonico_de(filas)
    for fila in filas:
        # `fila[:10]` por lo mismo que en `_canonico_de`: la consulta lleva una columna mas -- `region` --
        # cuando la tabla la tiene, y el desempaquetado pide diez. Cortar por diez la ignora, este o no.
        gid, pid_suelto, fuente, pid, nombre, _precio, _punit, _fiable, ean, marca = fila[:10]
        clave = (gid if gid is not None else pid_suelto, fuente)
        if clave not in canonico or str(pid) < str(canonico[clave][0]):
            canonico[clave] = (pid, nombre, ean, marca)

    # **Una copia de cada fila por llave que sirva**, despues de la pasada del canonico -- que lee diez
    # campos y la expansion añade uno --. Y **abstencion**: si se pide un producto concreto que no esta entre
    # las filas con precio, su llave no se crea; el canonico no sustituye su identidad.
    por_llave: list = []
    for fila in filas:
        dueno_fila = fila[0] if fila[0] is not None else fila[1]
        # **El emparejamiento, por las dos vias.** `k` es `(grupo, producto)`, y `dueno_fila` es de
        # quien es la fila: el grupo, o el producto cuando no hay grupo. Comparando solo `k[0]`, una
        # peticion de producto sin grupo (`k[0]` es `None`) no casaba nunca: la fila no entraba y
        # `mejor` salia vacio. Es el caso del ESCANER. Medido el 13 de octubre de 2026.
        for pedida in [k[1] for k in claves
                       if k[0] == dueno_fila
                       or (k[1] is not None and k[1] == dueno_fila)]:
            if pedida is not None and pedida not in {f[3] for f in filas}:
                continue
            por_llave.append((*fila, pedida))
    filas = por_llave

    # **Segunda pasada: la eleccion.** Aqui se puede comparar cada fila con el canonico, asi que una
    # variante barata ya no puede tapar a la exacta.
    mejor: dict = {}
    for fila in filas:
        # **Las diez de siempre, y `pedida`, que va la ultima.** La fila lleva ademas `region` cuando la
        # tabla la tiene -- y la 270 la expande con `pedida` detras --, asi que cortar por diez y tomar
        # la ultima deja las once que este bucle espera, con `region` o sin ella.
        (gid, pid_suelto, fuente, pid, nombre, precio, _punit, _fiable, ean, marca,
         pedida) = (*fila[:10], fila[-1])
        dueno = gid if gid is not None else pid_suelto
        clave = _llave_candidato(dueno, pedida, fuente)
        coste = _coste_para(cantidades.get(dueno, 1), precio, promos.get(pid))
        # **La referencia: lo pedido si consta, y si no el canonico del grupo.** Es la misma ficha
        # para todas las cadenas, porque la identidad se compara por GTIN y no por donde este.
        cual = fichas.get(pedida) or canonico[dueno]
        referencia = identidad.Producto(fuente=clave[1], id_fuente=str(cual[0]),
                                        nombre=cual[1], gtin=cual[2], marca=cual[3])
        esta = identidad.Producto(fuente=fuente, id_fuente=str(pid), nombre=nombre, gtin=ean, marca=marca)
        # Sin GTIN ni presentacion que afirmar, el motor se abstiene; y `None` cuenta como "nada que
        # afirmar", que es lo mismo que hacia antes de este cambio.
        veredicto = identidad.decide(referencia, esta)
        exacta = veredicto["estado"] == identidad.EXACTO
        # El canonico se guarda como ficha del motor para que `_resolver` no tenga que reconstruirlo.
        fila = (pid, precio, nombre, promos.get(pid), ean, referencia, marca, coste)
        actual = mejor.get(clave)
        # **Si la linea pidio un producto concreto y esta entre las filas con precio, gana ESE.** El
        # «mas barato del grupo» es la regla de la linea que pide el grupo sin mas; aplicarsela a la que
        # pidio un articulo seria sustituirle lo que pidio sin que nadie lo haya aceptado.
        es_la_pedida = pedida is not None and str(pid) == str(pedida)
        actual_es_la_pedida = (actual is not None and pedida is not None
                               and str(actual[0]) == str(pedida))
        if (actual is None or (es_la_pedida and not actual_es_la_pedida)
                or (es_la_pedida == actual_es_la_pedida
                    and _prefiere(exacta, coste, actual[8], actual[7]))):
            # Campos: identificador, precio, nombre, oferta, GTIN de esta fila, canonico del grupo,
            # marca, coste final y si es exacta.
            mejor[clave] = (*fila, exacta)
        # **La alternativa no se tira.** Si la que se queda no es exacta, o si esta lo es y otra no, se
        # guarda la mas barata de las que no lo son para poder ofrecerla aparte.
        if not exacta:
            alternativa = mejor.get((*clave, "alternativa"))
            if alternativa is None or coste < alternativa[7]:
                mejor[(*clave, "alternativa")] = (*fila, False)
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


def _es_de_fiar(peticion: Peticion, candidata, mejor: dict) -> bool:
    """Si la cantidad de esta linea puede entrar en un grupo al que se le aplica una oferta.

    **Si el candidato es el producto pedido, si. Si es una sustitucion, solo con la confirmacion en la mano.**
    Es la misma regla que `_resolver` usa para decidir si algo cuenta, aqui porque `estimacion` lee `mejor`
    directamente y no pasa por alli.

    Sin esto, la lista aplicaba descuentos a cantidades que esperaban autorizacion: un ahorro que nadie ha
    aceptado, enseñado como si lo estuviera.
    """
    elegida = mejor.get(_llave_candidato(peticion.grupo_id if peticion.grupo_id is not None else peticion.producto_id, peticion.producto_id, candidata[1]))
    if elegida is not None and len(elegida) > 8 and elegida[8]:
        return True
    guardada = mejor.get((*_llave_candidato(peticion.grupo_id if peticion.grupo_id is not None else peticion.producto_id, peticion.producto_id, candidata[1]),
                          "alternativa"))
    if guardada is None:
        return False
    alternativa = {"producto_id": guardada[0], "nombre": guardada[2], "coste_cent": guardada[7],
                   "fuente": candidata[1], "precio_cent": guardada[1], "promo": guardada[3]}
    return _es_la_confirmada(peticion, alternativa)


def _esperada_de(peticion: Peticion) -> tuple:
    """La identidad de una peticion, para agrupar compras: el grupo y el producto concreto, si consta."""
    return _llave_candidato(peticion.grupo_id, peticion.producto_id, None)[0]


def _agrupa_y_reparte(elecciones: list[Eleccion]) -> list[Eleccion]:
    """El coste de una compra se calcula **por grupo** y se reparte entre sus lineas.

    **Agrupar** por producto efectivo y cadena, y **solo con lo autorizado**: un aviso no es un permiso, asi que
    no se aplican descuentos con cantidades pendientes de autorizacion. Dos cadenas no se agrupan nunca.

    **Repartir** el total del grupo conservando la suma exacta: en proporcion a las unidades, parte entera para
    cada linea, y los centimos sobrantes de uno en uno a mayor fraccion -- a igualdad, la que va antes.

    Sin esto la promocion se aplicaba **por linea** y luego se sumaban los costes ya separados: un 3x2 daba 200
    centimos en una linea de tres y 300 en dos lineas de una y dos. La misma compra, dos precios.
    """
    grupos: dict[tuple, list[int]] = {}
    for indice, eleccion in enumerate(elecciones):
        if not eleccion.autorizada or not eleccion.unidades:
            continue
        grupos.setdefault((eleccion.producto_id, eleccion.fuente), []).append(indice)

    repartidas = list(elecciones)
    for indices in grupos.values():
        if len(indices) < 2:
            continue
        primera = elecciones[indices[0]]
        unidades = sum(elecciones[i].unidades for i in indices)
        unitario = primera.coste_sin_oferta_cent // primera.unidades
        total = lee_promo(primera.promo_txt).coste(unidades, unitario)
        partes = [(total * elecciones[i].unidades) // unidades for i in indices]
        resto = total - sum(partes)
        orden = sorted(range(len(indices)),
                       key=lambda k: (-((total * elecciones[indices[k]].unidades) % unidades), k))
        for k in orden[:resto]:
            partes[k] += 1
        for k, indice in enumerate(indices):
            repartidas[indice] = replace(elecciones[indice], coste_cent=partes[k])
    return repartidas


def _total_autorizado(elecciones: list[Eleccion]) -> dict:
    """El total de lo autorizado, y **lo que falta** con su motivo.

    Un total que esconde lo que no pudo contar es peor que un total mas bajo: el primero miente y el
    segundo se puede explicar. Por eso devuelve las dos cosas juntas y no solo la suma.

    Las que no cuentan no se tiran: van en `pendientes`, que es de donde sale la propuesta de alternativas
    que quien compra puede aceptar linea a linea.
    """
    cuenta = [e for e in elecciones if e.autorizada]
    pendientes = [e for e in elecciones if not e.autorizada]
    return {
        "total_cent": sum(e.coste_cent for e in cuenta),
        "lineas_contadas": len(cuenta),
        "pendientes": [{"linea_id": e.linea_id, "fuente": e.fuente, "nombre": e.nombre,
                        "coste_cent": e.coste_cent, "identidad": e.identidad, "motivo": e.motivo}
                       for e in pendientes],
        "completo": not pendientes,
    }


def _resolver(peticion: Peticion, fuente: str, mejor: dict) -> Eleccion | None:
    clave = _llave_candidato(*_llave(peticion), fuente)
    hallado = mejor.get(clave)
    if hallado is None:
        return None
    pid, precio, nombre, promo_txt, ean, referencia, marca, _coste_elegido = [*hallado, None, None, None, None][:8]
    # **El veredicto, antes de proponer nada.** Si no es el mismo producto, el coste que sigue es el
    # de una alternativa, y eso tiene que viajar en la respuesta para que nadie lo sustituya callando.
    veredicto = None
    if referencia is not None:
        propuesto = identidad.Producto(fuente=fuente, id_fuente=str(pid), nombre=nombre,
                                      gtin=ean, marca=marca)
        veredicto = identidad.decide(referencia, propuesto)
    # **La alternativa, si la hay.** Se lee la que ya eligio `_candidatos`: recalcularla aqui seria tener
    # dos sitios donde se decide lo mismo.
    guardada = mejor.get((*clave, "alternativa"))
    alternativa = None
    if guardada is not None:
        # **Con su precio unitario y su oferta**, no solo con el coste del grupo: es lo que hace falta
        # para poder devolverla y cobrarla como efectiva.
        alternativa = {"producto_id": guardada[0], "nombre": guardada[2],
                       "coste_cent": guardada[7], "fuente": fuente,
                       "precio_cent": guardada[1], "promo": guardada[3]}
    # **La eleccion efectiva, antes de cobrar.** Si hay sustitucion confirmada, lo que se devuelve y se cobra
    # es ESA alternativa -- su producto, su nombre, su precio y su oferta --, no el canonico que el motor
    # propone hoy. Con la confirmacion validada y la eleccion tomada de `hallado`, lo aceptado y lo cobrado
    # eran dos productos distintos: el fallo que reprodujo el dueno (`confirmado=dia:B; elegido=dia:A`).
    confirmada = _es_la_confirmada(peticion, alternativa)
    if confirmada and alternativa is not None:
        pid = alternativa["producto_id"]
        nombre = alternativa["nombre"]
        precio = alternativa["precio_cent"]
        promo_txt = alternativa.get("promo")

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
    # **Cuenta si es el producto pedido, si no hay nada que afirmar, o si se autorizo.** Cualquier otra
    # cosa -- alternativa, cuarentena, abtencion -- no suma: se enseña, se explica y se ofrece aparte.
    # **Un si de ayer no vale para la sustitucion de hoy.** El motor elige la alternativa
    # cada vez, con los precios de hoy: si propone otro producto, o el mismo en otra cadena,
    # la confirmacion no cuenta para esta y se pide nueva. Es lo que impide dar por aceptado
    # un cambio que nadie acepto.
    autorizada = (veredicto is None or veredicto["estado"] == identidad.EXACTO
                  or confirmada)
    # **El estado de la eleccion, dicho.** Si la confirmacion manda, lo que hay no es «una alternativa
    # propuesta» sino **una sustitucion aceptada**: el producto devuelto ya es el de la persona, y la etiqueta
    # tiene que decir eso y no lo que el motor proponia antes de que nadie aceptara nada.
    estado = "confirmada" if (confirmada and alternativa is not None) else (
        veredicto["estado"] if veredicto else None)
    return Eleccion(pid, nombre, fuente, peticion.cantidad, coste, sin_oferta,
                    promo_txt if mecanica.util else None, sugerencia,
                    linea_id=peticion.id,
                    identidad=estado,
                    motivo="; ".join(veredicto["motivos"]) if veredicto else None,
                    autorizada=autorizada, alternativa=alternativa)


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
        resueltas = _agrupa_y_reparte([e for e in elecciones if e])
        # **`por_cadena` se queda SIN agrupar, y es a proposito.** *Aqui se agrupo para `una_tienda`
        # --que es una tienda entera--, pero el reparto no puede usar esas partes: la parte de una
        # linea solo existe si todas las lineas van a esa tienda.* **El reparto agrupa el suyo, con el
        # conjunto que de verdad va a cada tienda** (`_mejor_reparto`). *Escribirlas aqui fue el arreglo
        # de la ronda anterior y era a medias: quito la incoherencia entre los dos numeros y dejo la
        # parte circular, que es lo que encontro el oraculo.*
        faltan = [p.nombre for p, e in zip(peticiones, elecciones, strict=True) if not e]
        if not resueltas:
            continue
        # **Solo cuenta lo autorizado.** Lo resuelto pero no autorizado -- alternativa, cuarentena,
        # abtencion -- se sigue enseñando con su precio, pero no suma: un aviso no es un permiso.
        total = _total_autorizado(resueltas)
        una_tienda.append({
            "cadena": fuente,
            "total_cent": total["total_cent"],
            "total_sin_ofertas_cent": sum(e.coste_sin_oferta_cent for e in resueltas if e.autorizada),
            "encontrados": len(resueltas),
            "contadas": total["lineas_contadas"],
            "sin_autorizar": len(total["pendientes"]),
            "pendientes": total["pendientes"],
            "faltan": faltan,          # por su nombre, no como un numero
            "productos": [_serializa(e) for e in resueltas],
        })
    # Primero las que lo tienen todo, y dentro de esas la mas barata. **`sin_autorizar` entra en el
    # orden a proposito:** una cadena que resuelve todas las lineas pero no autoriza ninguna no puede
    # colocarse por delante de una que si las tiene exactas, que es lo que pasaba ordenando solo por
    # `faltan`.
    una_tienda.sort(key=lambda x: (len(x["faltan"]), x["sin_autorizar"], x["total_cent"]))

    repartido = _mejor_reparto(peticiones, por_cadena, max_t, una_tienda)
    return {"una_tienda": una_tienda, "repartido": repartido, "lineas": len(peticiones)}


# **Cuanto se enumera antes de rendirse.** El producto cartesiano crece con las lineas -- 6 cadenas y
# 8 lineas son 1,7 millones --, asi que la exploracion exhaustiva de verdad no cabe para una lista de
# la compra de verdad. *Por debajo del limite se enumera y el resultado es el optimo; por encima se usa
# la heuristica, y la respuesta lo dice.*
_LIMITE_EXHAUSTIVO = 200_000
# *** Lo que se estima que cuesta ir a una segunda tienda, en centimos. ***
# *No es un gasto medido: es una estimacion de tiempo y viaje, y se llama asi para que quien la
# lea sepa que no es una cuenta.* *Estaba escrita dentro de una comparacion (`>= 150`), sin
# nombre y sin salir nunca al que la pantalla pudiera leer.*
VIAJE_CENT = 150


def _coste_con_lo_agrupado(elecciones: list[Eleccion]) -> int:
    """**Lo que cuesta un conjunto que se compra junto.**

    *Se agrupa por producto y se suman las partes: es la misma cuenta que `una_tienda` hace para una
    tienda entera, aplicada al conjunto de verdad que va a esa tienda.*
    """
    return sum(e.coste_cent for e in _agrupa_y_reparte(list(elecciones)))


def _asignaciones(peticiones, por_cadena, cadenas, max_tiendas):
    """**Las asignaciones que se van a puntuar**: todas si caben, y las de la heuristica si no.

    *Cuando caben se devuelve el optimo y `exhaustivo` es cierto. Cuando no, se recorren los conjuntos
    de tiendas y se manda cada linea a la mas barata **dentro de ese conjunto** -- la heuristica de
    siempre --, que es una respuesta peor y se dice.*
    """
    if len(cadenas) ** len(peticiones) <= _LIMITE_EXHAUSTIVO:
        for combinacion in product(cadenas, repeat=len(peticiones)):
            if len(set(combinacion)) <= max_tiendas:
                yield combinacion
        return

    for combo in combinations(cadenas, min(max_tiendas, len(cadenas))):
        yield tuple(
            min((c for c in combo if por_cadena[c][i]),
                key=lambda c: por_cadena[c][i].coste_cent, default=combo[0])
            for i in range(len(peticiones)))


def _mejor_reparto(peticiones, por_cadena, max_tiendas, una_tienda) -> dict | None:
    """La mejor combinacion de hasta `max_tiendas`, si gana a ir a una sola.

    **Cada asignacion se puntua con el conjunto que de verdad va a cada tienda.** *Antes se repartia con
    la «parte» que a cada linea le tocaba **suponiendo que todas las lineas iban a esa tienda**, y esa
    parte solo existe si la linea se queda: el motor mandaba una linea a la tienda donde su parte era
    menor, con una parte que salia de un grupo que se deshacia al mandarla alli.*

    *Es la frase de F06 al pie de la letra* -- **«no elegir partes de un descuento calculado sobre una
    cesta que al final no se compra en esa tienda»** --, y estaba medido: **9 discrepancias en 176
    escenarios** contra el oraculo exhaustivo `core/oraculo_reparto.py`. *Caso minimo: `l1`(2u)→aldi,
    `l2`(3u) y `l3`(1u) en alcampo a 1,20 con 3x2; la parte de `l3` en alcampo era 90 frente a 100 en
    aldi, pero salia de un grupo de cuatro unidades que solo se forma si `l3` se queda. El motor decia
    **435** y el optimo es **415**.*

    **Y se dice si la respuesta es exhaustiva o heuristica**: `exhaustivo` viaja en el resultado.
    *Heuristica se llama heuristica.*

    Garantia y limites
    ------------------
    **Garantia.** Con **200.000 asignaciones o menos** (`_LIMITE_EXHAUSTIVO`), el reparto devuelto es
    **el optimo** entre las asignaciones de como mucho `max_tiendas` tiendas, puntuando cada una con
    **el conjunto que de verdad va a cada tienda**. *Medido contra el oraculo independiente
    `core/oraculo_reparto.py`: **cero discrepancias en 200 escenarios al azar** con semilla fija
    (`tests/test_fase2_f06_oraculo_asignaciones.py`).*

    **Limites, dichos:**

    1. **Por encima de 200.000 asignaciones no se promete el optimo**, y la respuesta lo dice con
       `exhaustivo: False`. *Es una heuristica y se llama heuristica.*
    2. **El limite es un numero de asignaciones, no de tiempo.** *Si alguna vez se mide que 200.000
       tardan demasiado, el numero tendra que bajar y habra que decirlo.*
    3. **`umbral` se aplica por producto, y los folletos lo escriben por marca.** Medido el 13 de
       octubre de 2026 sobre los **236** textos distintos de oferta del silver: **3** son de umbral y
       los tres nombran una marca o una familia --

           "5 EUR DTO COMPRANDO 15 EUR PRODUCTOS PASCUAL"
           "5 EUR dto. comprando 20 EUR en Nestle Cafes. Exclusivo Online."
           "5 EUR dto. comprando 15 EUR en PepsiCo. Exclusivo Online."

       *No es el ticket entero, como supondria leerlo como compra global, y **no es un producto**, que
       es lo que hace el motor.* **Dos de los tres son `solo_online` y no restan**, asi que la
       exposicion viva es **1 texto de 236**. *La lectura del motor **subestima** el descuento -- cobra
       de mas --, que es el lado conservador del error; cerrarlo pide un concepto de marca o familia
       que el motor no tiene, y por eso queda publicado como limite en vez de disimulado.*
    4. **`acumulable` y `solo_online` no restan nada**: se ensenan, pero ese dinero no baja el ticket
       --*va a la tarjeta, o solo existe comprando por internet*--. *Un comparador que los reste miente
       sobre lo que se paga hoy.*
    """
    if max_tiendas < 2 or len(por_cadena) < 2:
        return None
    # **Completa de verdad**: sin lineas sin resolver y sin lineas resueltas pero no autorizadas. Si no,
    # el ahorro se mediria contra un total que no se puede comprar.
    completas = [x for x in una_tienda if not x["faltan"] and not x["sin_autorizar"]]
    referencia = completas[0]["total_cent"] if completas else None

    cadenas = sorted(por_cadena)
    exhaustivo = len(cadenas) ** len(peticiones) <= _LIMITE_EXHAUSTIVO

    mejor = None
    for combinacion in _asignaciones(peticiones, por_cadena, cadenas, max_tiendas):
        usadas = sorted(set(combinacion))
        if len(usadas) < 2:
            continue                       # no es un reparto, es una tienda

        por_tienda: dict[str, list[Eleccion]] = {}
        faltan: list[str] = []
        sin_autorizar: list[dict] = []
        for i, p in enumerate(peticiones):
            e = por_cadena[combinacion[i]][i] if combinacion[i] in por_cadena else None
            if e is None:
                faltan.append(p.nombre)
                continue
            # **Solo se elige entre lo autorizado.** Lo resuelto pero no autorizado no compite: se
            # propone aparte, con su motivo, y no suma.
            if not e.autorizada:
                sin_autorizar.append({"linea": p.nombre, "cadena": e.fuente,
                                      "coste_cent": e.coste_cent, "identidad": e.identidad,
                                      "motivo": e.motivo})
                continue
            por_tienda.setdefault(combinacion[i], []).append(e)

        if not por_tienda:
            continue
        eleccion = [e for es in por_tienda.values() for e in es]
        # **La cuenta de verdad**: cada tienda agrupa **lo que de verdad se lleva**.
        total = sum(_coste_con_lo_agrupado(es) for es in por_tienda.values())
        usadas = sorted(por_tienda)
        if len(usadas) < 2:
            continue
        # `sin_autorizar` entra en la comparacion: un reparto que resuelve todo sin autorizar nada no
        # puede ganar a uno que lo tiene exacto.
        if mejor is None or (len(faltan), len(sin_autorizar), total) < (
                len(mejor["faltan"]), len(mejor["sin_autorizar"]), mejor["total_cent"]):
            mejor = {"cadenas": usadas, "total_cent": total, "faltan": faltan,
                     "sin_autorizar": sin_autorizar,
                     "productos": [_serializa(e) for e in eleccion],
                     "reparto": {c: len(es) for c, es in sorted(por_tienda.items())},
                     "exhaustivo": exhaustivo}
    if mejor is None:
        return None
    if referencia is not None:
        mejor["ahorro_cent"] = referencia - mejor["total_cent"]
        # *** EL COSTE DE VIAJE, POR SEPARADO Y CON NOMBRE. ***
        # *La especificacion pide «mostrar ahorro bruto y coste de viaje opcional por
        # separado» (M06).* *Hasta hoy el coste existia como un **150 escrito dentro de una
        # comparacion** -- `ahorro_cent >= 150` -- que solo servia para poner un booleano:*
        # **el numero no salia nunca**, asi que la pantalla podia decir «no merece la pena»
        # sin decir cuanto cuesta la pena ni cuanto se ahorra.*
        #
        # *Ahora viajan las tres cifras: lo que se ahorra (**bruto**), lo que cuesta ir, y lo
        # que queda.* *El booleano se sigue dando, porque hay pantallas que solo necesitan eso,
        # pero se calcula con el numero de arriba y no con un literal suelto.*
        #
        # *150 centimos es una **estimacion de tiempo y viaje**, no un dato medido: por eso se
        # llama `VIAJE_CENT` y no se presenta como un gasto real. Quien lo pinte puede decir de
        # donde sale.*
        mejor["viaje_cent"] = VIAJE_CENT
        mejor["neto_cent"] = mejor["ahorro_cent"] - VIAJE_CENT
        mejor["merece_la_pena"] = mejor["ahorro_cent"] >= VIAJE_CENT
    return mejor


def _reparte_filas(filas: list[dict]) -> list[dict]:
    """Reparte el coste de una sublista entre sus lineas, por producto efectivo.

    **Una sublista ya es una tienda**, asi que dentro de ella el grupo de compra es el producto: dos lineas del
    mismo producto comparten la oferta. Y a tiendas distintas no se agrupa nunca, porque no hay donde.

    Misma regla de redondeo que en el resto: parte entera para cada linea, y los centimos sobrantes de uno en uno
    a mayor fraccion -- a igualdad, la que va antes --, para que la suma sea siempre el total del grupo.
    """
    grupos: dict[str, list[int]] = {}
    for indice, fila in enumerate(filas):
        if fila.get("coste_cent") is None or not fila.get("cantidad"):
            continue
        grupos.setdefault(str(fila.get("producto_id")), []).append(indice)
    repartidas = [dict(f) for f in filas]
    for indices in grupos.values():
        if len(indices) < 2:
            continue
        primera = filas[indices[0]]
        unidades = sum(filas[i]["cantidad"] for i in indices)
        unitario = primera["coste_sin_oferta_cent"] // primera["cantidad"]
        total_grupo = lee_promo(primera.get("promo")).coste(unidades, unitario)
        partes = [(total_grupo * filas[i]["cantidad"]) // unidades for i in indices]
        resto = total_grupo - sum(partes)
        orden = sorted(range(len(indices)),
                       key=lambda k: (-((total_grupo * filas[indices[k]]["cantidad"]) % unidades), k))
        for k in orden[:resto]:
            partes[k] += 1
        for k, i in enumerate(indices):
            repartidas[i]["coste_cent"] = partes[k]
    return repartidas


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
        # **El coste, repartido por grupo de compra dentro de la sublista.** Su docstring ya prometia «con
        # las ofertas aplicadas»: esto es lo que la cumple. El ahorro se recalcula sobre lo repartido, para
        # que la explicacion no contradiga al precio.
        filas = _reparte_filas(filas)
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
    # **El total de la lista, la suma de las sublistas.** Con el reparto hecho, sumar las lineas por separado
    # daria otro numero; y el total tiene que ser lo que de verdad se va a pagar.
    total = sum(x["total_cent"] for x in salida)

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
            "opciones": _opciones(hay),
            # **Lo que la persona ya decidio sobre esta linea**, que la peticion trae y aqui se
            # perdia: sin esto, la pantalla que ense?a la alternativa no puede saber si esta
            # aceptada, y el boton de consentir no tiene donde mirar. Medido el 13 de octubre de
            # 2026. Va por linea y no por lista: *autoriza una sustitucion concreta, no "lo que
            # haga falta" en toda la compra*.
            "autorizado": peticion.autorizado,
            "autorizado_producto": peticion.autorizado_producto,
            "autorizado_cadena": peticion.autorizado_cadena}


def _serializa(e: Eleccion) -> dict:
    return {"producto_id": e.producto_id, "nombre": e.nombre, "cadena": e.fuente,
            "unidades": e.unidades, "coste_cent": e.coste_cent,
            "coste_sin_oferta_cent": e.coste_sin_oferta_cent,
            "promo": e.promo_txt, "sugerencia": e.sugerencia,
            "linea_id": e.linea_id,
            # **El veredicto y lo que se ofrece.** Sin esto, todo el trabajo de identidad y de
            # autorizacion se quedaba dentro del servidor y la pantalla no podia decir nada.
            "identidad": e.identidad,
            "motivo": e.motivo,
            "autorizada": e.autorizada,
            "alternativa": e.alternativa}


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
    # **Y lo que la linea dice que se confirmo.** Sin esto, la comparacion de la sustitucion ve `None`
    # y no cuenta ninguna confirmacion: el dato estaba guardado y se quedaba a medio camino.
    peticiones = [Peticion(x.get("grupo_id"), x.get("producto_id"),
                           x.get("cantidad", 1), x.get("nombre_visto", ""),
                           autorizado=bool(x.get("autorizado")),
                           autorizado_producto=x.get("autorizado_producto"),
                           autorizado_cadena=x.get("autorizado_cadena")) for x in lineas]
    mejor = _candidatos(peticiones, _fecha_de_hoy())
    # **El candidato de cada linea.** El mas barato, que es el modelo de esta cuenta.
    candidatas: list = []
    for linea, peticion in zip(lineas, peticiones, strict=True):
        if linea.get("producto_movido"):
            candidatas.append(None)
            continue
        esperada = _llave_candidato(peticion.grupo_id if peticion.grupo_id is not None else peticion.producto_id, peticion.producto_id, None)[0]
        opciones = [(v[1], k[1], v[3]) for k, v in mejor.items()
                    if k[0] == esperada and k[-1] != "alternativa"]
        # *** SI LA PERSONA ELIGIO TIENDA, SE CUENTA ESA -- *no la mas barata*. ***
        # *El cierre (`coste_por_linea`) ya lo hacia, y lo dice su docstring: «guardar la mas
        # barata cuando alguien decidio comprarlo en DIA apuntaria un precio que no se pago».
        # **La estimacion no lo miraba**: se quedaba con `min(opciones)`, que es el mas barato
        # de cualquier cadena.*
        #
        # *Medido el 18/10/2026 con una linea de DIA a 100 y Aldi a 90: la lista decia **90**,
        # el recibo guardaba **100**. Diez centimos por linea, y una por cada cosa que se compre
        # en una tienda que no sea la mas barata -- en una lista de treinta, el total que se mira
        # mientras se anade no es el que se va a pagar.*
        #
        # *Se copia el patron del cierre (`cesta.py`, `elegida = linea.get("cadena_elegida")`):
        # si la cadena elegida tiene candidato, se usa **ese**; si no lo tiene, se sigue cogiendo
        # el mas barato, que es lo unico honesto cuando la tienda elegida no vende el producto.*
        elegida = linea.get("cadena_elegida")
        suya = next((op for op in opciones if op[1] == elegida), None) if elegida else None
        candidatas.append(suya or (min(opciones) if opciones else None))
    # **Agrupar por producto efectivo Y cadena, y repartir.** Dos lineas a la misma tienda comparten la
    # oferta; a tiendas distintas no se agrupan, porque seria inventarle un descuento a una compra que no
    # existe. La suma de las lineas es siempre el total del grupo.
    grupos: dict[tuple, list[int]] = {}
    for indice, (_linea, peticion, candidata) in enumerate(
            zip(lineas, peticiones, candidatas, strict=True)):
        if candidata is None or not peticion.cantidad:
            continue
        # **Solo lo exacto o lo confirmado entra en el grupo de la oferta.** Una cantidad
        # pendiente de autorizacion no lleva descuento: nadie ha aceptado esa sustitucion.
        if not _es_de_fiar(peticion, candidata, mejor):
            continue
        grupos.setdefault((candidata[1], _esperada_de(peticion)), []).append(indice)
    reparto: dict[int, int] = {}
    for indices in grupos.values():
        # **Una linea sola con tres unidades ES un 3x2.** Antes se saltaban los grupos de una sola
        # linea, con un comentario que decia *"entera si va sola, que es el mismo numero"*: era falso
        # en cuanto la oferta depende de la cantidad. Medido el 13 de octubre de 2026.
        primera = candidatas[indices[0]]
        unidades = sum(peticiones[i].cantidad for i in indices)
        total_grupo = lee_promo(primera[2]).coste(unidades, primera[0])
        partes = [(total_grupo * peticiones[i].cantidad) // unidades for i in indices]
        resto = total_grupo - sum(partes)
        orden = sorted(range(len(indices)),
                       key=lambda k: (-((total_grupo * peticiones[indices[k]].cantidad) % unidades), k))
        for k in orden[:resto]:
            partes[k] += 1
        for k, indice in enumerate(indices):
            reparto[indice] = partes[k]
    total = en_carro = sin_precio = 0
    for indice, (linea, peticion) in enumerate(zip(lineas, peticiones, strict=True)):
        # **Una linea que apunta a otro producto no se cuenta.** El `grupo_id` es un
        # ordinal que se renumera en cada pasada, asi que esta linea puede estar
        # apuntando a un pintalabios cuando dice «leche entera»: sumarle su precio
        # seria meter un numero falso en el total. Cuenta como «sin precio», que ya
        # es una cara que la pantalla sabe enseñar. Ver `catalogo.lineas_movidas`.
        if linea.get("producto_movido"):
            sin_precio += 1
            continue
        # **Por la llave del motor, no por el grupo.** La llave lleva el producto concreto cuando la linea
        # lo pide, y comparar contra el grupo dejaba esas lineas en «sin precio»: en silencio, y en la
        # pantalla de la lista. `_llave_candidato(...)[0]` no depende de la cadena.
        candidata = candidatas[indice]
        if candidata is None:
            sin_precio += 1
            continue
        # Del reparto si su grupo tiene mas de una linea; entera si va sola, que es el mismo numero.
        # **Sin oferta si la cantidad no es de fiar, ni agrupada ni sola.** Una sustitucion pendiente de
        # confirmacion se cobra a precio de catalogo: aplicar su 3x2 seria enseñar un ahorro que nadie ha
        # aceptado.
        if not _es_de_fiar(peticion, candidata, mejor):
            coste = peticion.cantidad * candidata[0]
        else:
            coste = reparto.get(
                indice, lee_promo(candidata[2]).coste(peticion.cantidad, candidata[0]))
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

    Devuelve `{linea_id: {"cadena", "precio_cent", "promo", "producto_id"}}`, mas `coste_cent` cuando
    hay precio y cantidad, que es la parte repartida de la promocion. `precio_cent` es **None** cuando
    no hay precio que dar: la linea apunta a otro producto (`producto_movido`, el caso de
    `catalogo.lineas_movidas`) o el producto no esta en el catalogo. Quien lo guarde lo cuenta aparte --
    un cero ahi seria afirmar que salio gratis.

    **`promo` y `producto_id` se anadieron el 13 de octubre de 2026 (fase 2, F01)**, y son lo que el
    cierre necesita para guardar **el producto efectivo**: *sin `producto_id`, una linea que pide solo
    grupo se archivaba **sin identidad** -- no se sabia que producto le habia puesto el precio; y sin
    `promo`, el reparto de la oferta la adivinaba buscando en `mejor` un candidato de esa cadena con
    ese precio exacto, que se equivoca con dos productos al mismo precio y **no encontraba nada cuando
    el precio venia de una alternativa aceptada**.*
    """
    salida: dict[str, dict] = {}
    if not lineas:
        return salida
    # **Y lo que la linea dice que se confirmo.** Sin esto, la comparacion de la sustitucion ve `None`
    # y no cuenta ninguna confirmacion: el dato estaba guardado y se quedaba a medio camino.
    peticiones = [Peticion(x.get("grupo_id"), x.get("producto_id"),
                           x.get("cantidad", 1), x.get("nombre_visto", ""),
                           autorizado=bool(x.get("autorizado")),
                           autorizado_producto=x.get("autorizado_producto"),
                           autorizado_cadena=x.get("autorizado_cadena")) for x in lineas]
    mejor = _candidatos(peticiones, _fecha_de_hoy())
    for linea, peticion in zip(lineas, peticiones, strict=True):
        cadena = precio = promo = efectivo = None
        if not linea.get("producto_movido"):
            # **Por la llave del motor**, no por el grupo: la llave lleva el producto concreto cuando la
            # linea lo pide, y comparar contra el grupo dejaba esas lineas guardandose **sin precio**.
            esperada = _llave_candidato(peticion.grupo_id if peticion.grupo_id is not None else peticion.producto_id, peticion.producto_id, None)[0]
            # **La sustitucion aceptada manda aqui igual que en la estimacion.** Hasta el 13 de octubre
            # de 2026 no se miraba: se filtraba `k[-1] != "alternativa"` y se guardaba **el producto del
            # grupo** con su precio, mientras la estimacion cobraba la alternativa aceptada. Medido con
            # el escenario del encargo -- A de 300 c pedido, B de 250 c con 3x2 aceptado, tres unidades:
            # **la estimacion cobraba 500 y el cierre guardaba 900.** Cuatrocientos centimos, y un
            # producto que nadie compro. *Y lo que se guarda al cerrar no se recalcula nunca: un error
            # aqui miente para siempre.*
            aceptada = None
            for k, v in mejor.items():
                if k[0] != esperada or k[-1] != "alternativa":
                    continue
                candidata = {"producto_id": v[0], "precio_cent": v[1], "promo": v[3], "fuente": k[1]}
                if _es_la_confirmada(peticion, candidata):
                    aceptada = candidata
            if aceptada is not None:
                cadena = aceptada["fuente"]
                precio = aceptada["precio_cent"]
                promo = aceptada["promo"]
                efectivo = aceptada["producto_id"]
            else:
                # **Sin sustitucion confirmada, el producto que el grupo es hoy**, con la tienda
                # decidida mandando sobre el mas barato. *Es lo que hacia antes y sigue estando bien:
                # una linea que no acepto nada no puede cobrarse como si hubiera aceptado.*
                suyos = [(k[1], v[1], v[3], v[0]) for k, v in mejor.items()
                         if k[0] == esperada and k[-1] != "alternativa"]
                elegida = linea.get("cadena_elegida")
                if elegida and any(f == elegida for f, *_ in suyos):
                    cadena, precio, promo, efectivo = next(x for x in suyos if x[0] == elegida)
                elif suyos:
                    cadena, precio, promo, efectivo = min(suyos, key=lambda par: par[1])
        salida[str(linea.get("id"))] = {"cadena": cadena, "precio_cent": precio,
                                        "promo": promo, "producto_id": efectivo}

    # **Y la parte de cada linea, repartida.** La promocion se decide **aqui**, que es donde se conoce: el
    # cierre solo tiene que escribir el numero. Se agrupa por producto efectivo y cadena elegida -- dos lineas
    # a la misma tienda comparten oferta, a tiendas distintas no -- y el total del grupo se reparte
    # conservando la suma exacta: parte entera, y los centimos sobrantes de uno en uno a mayor fraccion.
    grupos: dict[tuple, list[str]] = {}
    for linea, peticion in zip(lineas, peticiones, strict=True):
        suyo = salida.get(str(linea.get("id"))) or {}
        if suyo.get("precio_cent") is None or not peticion.cantidad:
            continue
        esperada = _llave_candidato(peticion.grupo_id if peticion.grupo_id is not None else peticion.producto_id, peticion.producto_id, None)[0]
        grupos.setdefault((esperada, suyo.get("cadena")), []).append(str(linea.get("id")))
    for indices in grupos.values():
        primera = salida[indices[0]]
        unidades = sum(int(next(x["cantidad"] for x in lineas if str(x.get("id")) == i))
                       for i in indices)
        unitario = primera["precio_cent"]
        # **La oferta de la propia linea, no una busqueda por parecido.** Antes se rebuscaba en `mejor`
        # un candidato de esa cadena con ese precio exacto: se equivocaba con dos productos al mismo
        # precio en la misma tienda y, sobre todo, **no encontraba nada cuando el precio venia de una
        # alternativa aceptada**, porque la alternativa no estaba entre los candidatos que miraba.
        promo = primera.get("promo")
        total_grupo = lee_promo(promo).coste(unidades, unitario)
        cantidades = [int(next(x["cantidad"] for x in lineas if str(x.get("id")) == i)) for i in indices]
        partes = [(total_grupo * c) // unidades for c in cantidades]
        resto = total_grupo - sum(partes)
        orden = sorted(range(len(indices)),
                       key=lambda k: (-((total_grupo * cantidades[k]) % unidades), k))
        for k in orden[:resto]:
            partes[k] += 1
        for k, i in enumerate(indices):
            salida[i]["coste_cent"] = partes[k]
    return salida



def _cantidades_por_referencia(peticiones: list[Peticion]) -> dict:
    """Cuantas unidades se compran de cada referencia, **sumando todas sus lineas**.

    Dos lineas del mismo producto no son dos compras: son una compra de mas unidades, y las ofertas que
    dependen de la cantidad se aplican a lo que se lleva. Quedarse con la ultima -- que es lo que hacia antes,
    con un comentario que lo llamaba decision -- elige el candidato con un numero que no es el que se paga.
    """
    cantidades: dict = {}
    for peticion in peticiones:
        referencia = peticion.grupo_id if peticion.grupo_id is not None else peticion.producto_id
        if referencia is not None:
            cantidades[referencia] = cantidades.get(referencia, 0) + max(1, int(peticion.cantidad))
    return cantidades


def _es_la_confirmada(peticion: Peticion, alternativa) -> bool:
    """Si la sustitucion que confirmo la persona **es la que el motor propone ahora**.

    Tres cosas tienen que darse, y ninguna sobra:

      - que haya un si;
      - que conste **que** se acepto -- un si sin producto no se puede honrar, y la base lo
        rechaza desde la migracion 012 --;
      - y que coincida con la alternativa de ahora, en **producto y cadena**.

    Si el motor propone otra cosa, esto devuelve `False` y la linea vuelve a pedir confirmacion:
    es una sustitucion distinta, aunque se parezca.
    """
    if not peticion.autorizado or alternativa is None:
        return False
    if not peticion.autorizado_producto:
        return False

    def campo(cosa, nombre):
        """La alternativa puede llegar como diccionario o como objeto: se lee sin suponer cual."""
        if isinstance(cosa, dict):
            return cosa.get(nombre)
        return getattr(cosa, nombre, None)

    if str(campo(alternativa, "producto_id")) != str(peticion.autorizado_producto):
        return False
    # **La cadena, con los dos nombres.** La alternativa la llama `fuente` -- es la cadena de
    # la que sale el precio -- y leer solo `cadena` fue mi error: la comparacion salia siempre
    # falsa y no contaba ninguna confirmacion, ni la buena.
    confirmada_cadena = campo(alternativa, "cadena") or campo(alternativa, "fuente")
    if confirmada_cadena is None or peticion.autorizado_cadena is None:
        return False
    return str(confirmada_cadena) == str(peticion.autorizado_cadena)


def _canonico_de(filas) -> dict:
    """El producto de referencia de cada grupo: **uno por grupo**, no uno por grupo y cadena.

    Es el de identificador mas bajo, y no el primero que devuelva el SQL, para que la referencia sea
    la misma entre ejecuciones. Y es el mismo en todas las cadenas a proposito: la referencia no puede
    depender de donde este el candidato, o el mismo producto saldria exacto en una tienda y alternativa
    en otra, y los veredictos de dos cadenas no se podrian comparar.
    """
    canonico: dict = {}
    # **`fila[:10]`, y no `in filas` directo.** La consulta que alimenta esto lleva una columna mas
    # -- `region` -- cuando la tabla la tiene, y **anadirla rompio este desempaquetado**: el
    # desempaquetado pide diez y llegaban once, con un `ValueError` que la suite caza. Va al final,
    # asi que cortar por diez deja las diez de siempre y **ignora la que sobre**, este o no.
    for fila in filas:
        gid, pid_suelto, _fuente, pid, nombre, _precio, _punit, _fiable, ean, marca = fila[:10]
        clave = gid if gid is not None else pid_suelto
        if clave not in canonico or str(pid) < str(canonico[clave][0]):
            canonico[clave] = (pid, nombre, ean, marca)
    return canonico