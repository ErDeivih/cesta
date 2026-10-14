"""La API de recetas: **personal, y con la sesion delante de todo**.

Cada endpoint depende de `usuario_actual`, y el propietario sale **solo de la sesion**: nunca del cuerpo
de la peticion. Cuando algo no es tuyo se responde **404 y no 403**, porque un 403 confirmaria que ese
identificador existe y es de otra persona.

Los manejadores no usan `Depends` para la conexion, para poder llamarse directamente desde una prueba;
la sesion, en cambio, **si** es una dependencia, y por eso la prueba del anonimo recibe 401 de verdad.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from core import diario, importar_receta, recetas

from . import catalogo
from .sesion import usuario_actual

rutas = APIRouter(prefix="/api/recetas", tags=["recetas"])

_ruta_base: Path | None = None


def ruta_base(ruta: Path | str | None = None) -> Path | None:
    """Donde vive el fichero de recetas. Se puede fijar para que las pruebas no toquen el de verdad."""
    global _ruta_base
    if ruta is not None:
        _ruta_base = Path(ruta)
    return _ruta_base


def _con():
    return recetas.conecta(_ruta_base)


class ALaLista(BaseModel):
    """**Lo unico que manda el cliente.** *El propietario y la semana los pone el servidor.*"""
    lista_id: str


class IngredienteIn(BaseModel):
    texto: str = Field(min_length=1)
    cantidad: float | None = None
    unidad: str | None = None
    producto_id: str | None = None
    grupo_id: int | None = None
    fuente: str | None = None


class RecetaIn(BaseModel):
    nombre: str = Field(min_length=1)
    raciones: int = Field(default=2, ge=1)
    preparacion: str = ""
    ingredientes: list[IngredienteIn] = []
    minutos: int | None = Field(default=None, ge=0)
    etiquetas: str = ""


class CambioIn(BaseModel):
    """Todo opcional: lo que no se manda se hereda de la version anterior, **copiado**."""
    nombre: str | None = None
    raciones: int | None = Field(default=None, ge=1)
    preparacion: str | None = None
    ingredientes: list[IngredienteIn] | None = None
    minutos: int | None = Field(default=None, ge=0)
    etiquetas: str | None = None


class PlanIn(BaseModel):
    fecha: str
    receta_id: int
    comensales: int = Field(default=2, ge=1)
    version: int | None = None


def _como_filas(ingredientes: list[IngredienteIn] | None) -> list[dict] | None:
    if ingredientes is None:
        return None
    return [i.model_dump(exclude_none=True) for i in ingredientes]


@rutas.get("")
def listar(incluir_archivadas: bool = False,
           usuario: dict = Depends(usuario_actual)) -> dict:
    con = _con()
    try:
        return {"recetas": recetas.listar(con, usuario["id"], incluir_archivadas=incluir_archivadas)}
    finally:
        con.close()


@rutas.post("", status_code=201)
def crear(datos: RecetaIn, usuario: dict = Depends(usuario_actual)) -> dict:
    con = _con()
    try:
        rid = recetas.crear(con, usuario["id"], datos.nombre, raciones=datos.raciones,
                            preparacion=datos.preparacion,
                            ingredientes=_como_filas(datos.ingredientes),
                            minutos=datos.minutos, etiquetas=datos.etiquetas)
        return {"id": rid, "receta": recetas.leer(con, usuario["id"], rid)}
    finally:
        con.close()


@rutas.get("/plan")
def plan(desde: str = Query(...), hasta: str = Query(...),
         usuario: dict = Depends(usuario_actual)) -> dict:
    """Va **antes** que `/{receta_id}`: si no, FastAPI leeria "plan" como un identificador."""
    con = _con()
    try:
        return {"plan": recetas.plan(con, usuario["id"], desde, hasta)}
    finally:
        con.close()


@rutas.post("/plan", status_code=201)
def planificar(datos: PlanIn, usuario: dict = Depends(usuario_actual)) -> dict:
    con = _con()
    try:
        recetas.planificar(con, usuario["id"], datos.fecha, datos.receta_id,
                           comensales=datos.comensales, version=datos.version)
        return {"plan": recetas.plan(con, usuario["id"], datos.fecha, datos.fecha)}
    except ValueError as fallo:
        raise HTTPException(status_code=404, detail=str(fallo)) from fallo
    finally:
        con.close()


_GRAMOS_POR_UNIDAD = {"g": 1.0, "kg": 1000.0}


def _gramos_de(ingrediente: dict) -> float | None:
    """Los gramos de un ingrediente, **si la unidad es de peso**. Y `None` si no.

    *Solo hay dos unidades de peso aqui (`g` y `kg`), y no se anade ninguna mas sin motivo:*

    - `ml` **no se convierte a gramos**: haria falta la **densidad**, y *el encargo prohibe inventarla*.
    - `ud` **tampoco**: una unidad no pesa lo mismo en dos productos, *y el peso de una unidad no esta en
      el dato.*

    Y si no se puede, la linea va a `sin_cantidad` -- *que es un resultado, no un fallo.*
    """
    cantidad, unidad = ingrediente.get("cantidad"), ingrediente.get("unidad")
    if cantidad is None or unidad is None:
        return None
    factor = _GRAMOS_POR_UNIDAD.get(str(unidad).strip().lower())
    return None if factor is None else cantidad * factor


@rutas.get("/plan/prevision")
def prevision_del_plan(desde: str = Query(...), hasta: str = Query(...),
                       usuario: dict = Depends(usuario_actual)) -> dict:
    """**La nutricion PREVISTA del plan**, con su cobertura. *No escribe nada, y no adivina.*

    **Compra no es consumo**: esto mira lo que **se va** a comer, y el diario lo que **se comio**. Por eso
    no anota nada: *solo suma lo que ya esta enlazado.*

    Y **lo que falta se dice, no se rellena.** Un ingrediente **sin `producto_id`** entra en `sin_dato`
    **con su nombre**, porque *buscarle un producto por el texto seria atribuirle la nutricion de otro* --
    y el propio `cesta.py` ya avisa de que la columna que lo trae **«llega sola»** el dia que el emparejador
    la escriba. Un ingrediente con producto pero **sin cantidad en peso** entra en `sin_cantidad`.

    **Y la cobertura es por nutriente**, que es lo que hace que esto no mienta: un producto puede traer
    energia y no proteinas, y `diario.de_ficha` **ya devuelve `None` en lo que no sabe** en vez de un cero.
    *El subtotal se llama `conocido` y no `total`, y sale de `diario.resumen`, la MISMA aritmetica que usa
    el diario: si cada uno sumara a su manera, los dos numeros no serian comparables.*
    """
    con = _con()
    try:
        comidas: list[dict] = []
        sin_dato: list[str] = []
        sin_cantidad: list[str] = []
        for entrada in recetas.plan(con, usuario["id"], desde, hasta):
            receta = recetas.leer(con, usuario["id"], entrada["receta_id"],
                                  version=entrada["version"], raciones=entrada["comensales"])
            if receta is None:
                continue
            lineas: list[dict] = []
            conocidos: list[dict] = []
            for ingrediente in receta.get("ingredientes") or []:
                texto = ingrediente.get("texto")
                producto_id = ingrediente.get("producto_id")
                ficha = catalogo.producto(producto_id) if producto_id else None
                gramos = _gramos_de(ingrediente)
                if ficha is None:
                    motivo = "sin_catalogo"
                    sin_dato.append(texto)
                elif gramos is None:
                    motivo = "sin_cantidad"
                    sin_cantidad.append(texto)
                else:
                    motivo = None
                    nutrientes = diario.de_ficha(ficha, gramos)
                    conocidos.append(nutrientes)
                    lineas.append({"texto": texto, "producto_id": producto_id,
                                   "nutrientes": nutrientes, "motivo": None})
                    continue
                lineas.append({"texto": texto, "producto_id": producto_id,
                               "nutrientes": None, "motivo": motivo})
            comidas.append({
                "fecha": entrada["fecha"], "receta_id": entrada["receta_id"],
                "nombre": entrada.get("nombre"), "version": entrada["version"],
                "comensales": entrada["comensales"], "lineas": lineas,
                # **La misma aritmetica que el diario.** Y sobre las lineas que SI tienen nutrientes:
                # las que no, ya estan dichas en `sin_dato` y en `sin_cantidad`.
                **diario.resumen(conocidos),
            })
        return {"desde": desde, "hasta": hasta, "comidas": comidas,
                "sin_dato": sin_dato, "sin_cantidad": sin_cantidad}
    finally:
        con.close()


@rutas.get("/{receta_id}")
def leer(receta_id: int, version: int | None = None,
         raciones: int | None = Query(default=None, ge=1),
         usuario: dict = Depends(usuario_actual)) -> dict:
    con = _con()
    try:
        hallada = recetas.leer(con, usuario["id"], receta_id, version=version, raciones=raciones)
    finally:
        con.close()
    if hallada is None:
        raise HTTPException(status_code=404, detail=f"no hay receta {receta_id}"
                            + (f" en la version {version}" if version else ""))
    _con_precios(hallada)
    return hallada


def _con_precios(hallada: dict) -> None:
    """Pone a cada ingrediente **con producto elegido** el precio del catalogo.

    **G12, punto 222**: *«nutricion/coste por racion con cobertura y procedencia. **Separar coste de
    ingredientes usados del desembolso por envases**»*.

    **El dato ya estaba.** `core/recetas.py` guarda `producto_id`, `grupo_id` y `fuente` por
    ingrediente desde antes -- *opcionales los tres, para que un ingrediente generico siga siendo
    generico* --. **Lo que faltaba era el cable**: la pantalla recibia el ingrediente sin precio y
    `logica/costeReceta.ts` decia «no se puede calcular todavia» en **todas** las lineas, incluidas
    las que si tenian producto.

    *Y se hace aqui y no en la pantalla a proposito*: el precio sale del catalogo, que la API ya
    tiene; **que la pantalla pidiera el precio ingrediente a ingrediente serian N peticiones por
    receta para un dato que ya esta a mano.**

    **Sin `producto_id` no se pone precio**, ni se busca por nombre: *un nombre parecido no demuestra
    que sea el mismo producto, y es la regla que `cocina.ts` escribe: «no fusionar por parecido de
    nombre».* **Lo que no se sabe sigue sin saberse.**
    """
    from . import catalogo

    for ing in hallada.get("ingredientes") or []:
        pid = ing.get("producto_id")
        if not pid:
            continue
        try:
            producto = catalogo.producto(str(pid))
        except Exception:  # noqa: BLE001  (un catalogo ilegible no tumba la receta)
            producto = None
        if not producto:
            continue
        # Los tres que el coste necesita, con los nombres que ya usa `costeReceta.ts`.
        ing["precio_cent"] = producto.get("precio_cent")
        ing["precio_unidad_cent"] = producto.get("precio_unidad_cent")
        ing["unidad_canon"] = producto.get("unidad_canon")
        # **Y el cuarto: el tamano neto del envase, que es lo que A08 pide.**
        #
        # *Es «el tamano neto publicado del articulo elegido», y aqui esta a mano*: `producto["cantidad"]`
        # y `producto["unidad"]` **son** el tamano de un envase -- *1 kg, 1 l, 6 ud*.
        #
        # **Sin esto, `_envases_de` no tenia por donde calcular**: `cantidad` del ingrediente es **cuanto
        # se necesita**, no **cuanto trae un envase**, y confundirlas daria un pedido de un solo envase
        # siempre. *La regla estaba escrita y probada; **lo que faltaba era rellenar el dato**, y esa
        # linea es esta.*
        #
        # *Y la unidad va aparte de la del ingrediente*: una receta pide `200 g` de algo que se vende en
        # `1 l`, y ahi **no hay conversion** -- `envases_enteros` lo dice en vez de inventar un numero.
        ing["tamano_envase"] = producto.get("cantidad")
        ing["unidad_envase"] = producto.get("unidad")


@rutas.get("/{receta_id}/a-la-lista")
def previa(receta_id: int, version: int | None = None,
           usuario: dict = Depends(usuario_actual)) -> dict:
    """**Que se compraria, sin comprar nada.** *Es la previa del 221, y no escribe.*

    *Y hace falta que exista*: el `POST` escribe, asi que **enseñar la previa antes de decidir exige
    un sitio que la calcule y no toque nada.** *La consolidacion y los envases son logica de servidor
    (Python), no de pantalla, asi que no se duplica en el cliente.*

    **Y devuelve tambien lo que NO se puede comprar** -- *lo que no tiene cantidad y lo que no se pudo
    consolidar -- con su motivo.* *Es la mitad del valor de una previa: saber que la sal no se compra
    porque no se sabe cuanto, en vez de ver una lista sin sal y no entender por que.*
    """
    from dataclasses import asdict

    from core import previa_compra

    con = _con()
    try:
        hallada = recetas.leer(con, usuario["id"], receta_id, version=version)
    finally:
        con.close()
    if hallada is None:
        raise HTTPException(status_code=404, detail=f"no hay receta {receta_id}")
    _con_precios(hallada)
    previa = previa_compra.previa_de_compra(hallada.get("ingredientes") or [])
    return {
        "version": hallada.get("version"),
        "raciones": hallada.get("raciones"),
        "lineas": [asdict(ln) for ln in previa.lineas],
        "sin_cantidad": previa.sin_cantidad,
        "sin_consolidar": previa.sin_consolidar,
        "nota": previa.nota,
    }


@rutas.post("/{receta_id}/a-la-lista", status_code=201)
def a_la_lista(receta_id: int, datos: ALaLista,
               usuario: dict = Depends(usuario_actual)) -> dict:
    """**G12, punto 221: pasar una receta a la lista, y repetir no duplica.**

    *El cuerpo trae `lista_id` y nada mas*: **ni el propietario ni la semana**, porque los dos los pone
    el servidor -- *el propietario es `usuario["id"]` y la semana la calcula `traspaso.semana_de()`*.
    **Si los mandara el cliente, dos pestañas con fechas distintas escribirian dos veces la misma
    compra**, y es la regla que G12 pide en su 223 y G13 en su 227: *no confiar en lo que manda el
    cliente como identidad ni como propietario.*

    **Y el id de cada linea es determinista** -- `uuid5` de la clave de la operacion y del ingrediente
    -- asi que **la idempotencia esta dos veces**: `traspaso` impide la segunda operacion, y
    `almacen.anade_linea` **ya es un upsert** (*«el id lo trae el movil; si llega dos veces, no se
    duplica: se actualiza»*), que es la segunda red por si algo se cuela.
    """
    from core import traspaso

    from . import almacen

    # **La lista tiene que ser suya.** *No se importa `_acceso` de `main.py` -- seria circular -- y
    # se comprueba con lo que ya existe: `listas_de` devuelve las listas de quien pregunta.*
    from . import almacen as _almacen

    suyas = {str(lst["id"]) for lst in _almacen.listas_de(usuario["id"])}
    if datos.lista_id not in suyas:
        raise HTTPException(status_code=404, detail="no hay lista " + datos.lista_id)

    def insertar(lineas) -> str:
        for ln in lineas:
            # **El id sale de la clave**: repetir la operacion produce los mismos ids, y el upsert
            # los actualiza en vez de anadir. *Y con `grupo_id`/`producto_id` cuando el ingrediente
            # los tenia: sin ellos la linea queda «Pendiente de identificar», que es la verdad.*
            #
            # **Y LA CANTIDAD VA A LA NOTA, NO AL CAMPO DE CANTIDAD.** *Esto estaba mal, y es el mismo
            # defecto del puente del plan por el otro lado* -- *medido el 13 de octubre de 2026*:
            #
            #     round(ln.cantidad) or 1     -> 300 g de harina se escribian como **300 UNIDADES**
            #
            # *O sea «300 envases de harina», que es lo contrario de lo que dice la receta.* **Y con
            # `None` de nota no quedaba ni rastro de los gramos**: quien leyera la lista no podia saber
            # que eran 300 g.
            #
            # El campo `cantidad` de una linea de lista **cuenta unidades de un producto** -- *lo dijo la
            # base cuando A09 intento escribir `None`: es NOT NULL, porque apuntar es decidir cuanto* --,
            # y la receta habla en gramos. **Se anade UNA unidad y el detalle va donde se lee**, que es lo
            # mismo que hace el puente del plan.
            #
            # *Y `previa_compra` ya trae lo que hace falta para decirlo bien*: **la unidad**, **los
            # envases enteros** y **el sobrante**. *Tirarlos era quedarse con la peor mitad del calculo.*
            # *Y `de_donde` dice que ingredientes la formaron*, que es la trazabilidad que el encargo pide.
            detalle = f"de la receta: {ln.texto} ({ln.cantidad:g} {ln.unidad})".rstrip()
            if ln.envases:
                detalle += f" · {ln.envases} envase{'s' if ln.envases != 1 else ''}"
                if ln.sobrante:
                    detalle += f", sobran {ln.sobrante:g} {ln.unidad_envase or ln.unidad}"
            else:
                # **Y cuando el tamano del envase no se conoce, se DICE.** *Callarlo se leia como «un
                # envase basta», que es justo lo que no se sabe.*
                detalle += " · no se sabe el tamano del envase"
            if ln.de_donde:
                detalle += " · " + " + ".join(ln.de_donde)
            # **Y la cantidad son LOS ENVASES.** *Era `1` fijo, y con eso **«dos envases» solo existia en
            # la nota**: la linea decia 1, y el coste, el cierre y el historico leian 1.*
            # *Y cuando no hay envases calculados queda `1`, porque la columna es `NOT NULL` -- pero
            # **la nota ya dice que no se sabe**, asi que ese `1` no afirma nada.*
            almacen.anade_linea(
                datos.lista_id, usuario["id"], traspaso.id_de_linea(datos.lista_id, ln.clave),
                ln.texto,
                # *El grupo, que estaba clavado en `None`.* **Un ingrediente identificado solo por
                # grupo llegaba a la lista sin destino** -- y la tabla exige `linea_con_destino`:
                # producto **o** grupo.
                ln.grupo_id,
                # **Y el `producto_id` SE PASA TAL CUAL, porque es TEXTO.**
                #
                # *Aqui habia `int(ln.producto_id) if (ln.producto_id or "").isdigit() else None`, y con
                # eso **el articulo elegido se perdia SIEMPRE**: *los identificadores del catalogo son
                # **`fuente:id`** -- `dia:1234`, `carrefour:5678` --, y **ninguno es `isdigit()`**, asi
                # que la linea salia con `producto_id = None` **siempre**.*
                #
                # *Y `lista_linea.producto_id` es **`text`**, no un entero: *el `int()` no era una
                # conversion necesaria, era **una perdida**.* *La columna de al lado, `grupo_id`, si es
                # `bigint`, y ahi el entero es lo correcto.*
                #
                # *Y es justo lo que el complemento del 14/10 senala: «un grupo puede evitar el rechazo,
                # **pero no preservar el articulo elegido**» -- *porque un grupo es una **familia**, y la
                # persona **eligio un articulo**.*
                ln.producto_id,
                ln.envases or 1, detalle, None)
        return datos.lista_id

    con = _con()
    try:
        # *** Y `enriquece=_con_precios`, QUE ES LO QUE HACE QUE HAYA ENVASES. *** *
        #
        # *Es la pieza que ya existia y que solo se usaba **al leer** una receta* (`l229`): *pone en cada
        # ingrediente con articulo elegido el tamaño del envase de su ficha.*
        #
        # *Y sin esto, pasar una receta de **1.400 g** de un articulo de **1.000 g** dejaba la linea con
        # `cantidad = 1` y los gramos **solo en la nota** -- *medido, y es el fallo del propietario.* *
        # *Porque `traspaso` es `core` y **no puede leer el catalogo**: *el catalogo vive aqui.* *
        return traspaso.pasar_a_lista(con, usuario["id"], receta_id, insertar=insertar,
                                      enriquece=_con_precios)
    except ValueError as fallo:
        # *Receta de otro, o version que no existe: **404**, no un 500 con el motivo dentro.*
        raise HTTPException(status_code=404, detail=str(fallo)) from fallo
    finally:
        con.close()


@rutas.get("/{receta_id}/versiones")
def versiones(receta_id: int, usuario: dict = Depends(usuario_actual)) -> dict:
    """Las versiones de una receta tuya. De una que no lo es, **404 y no una lista vacia**: una lista
    vacia diria "existe y no tiene versiones", que es informacion que no te toca."""
    con = _con()
    try:
        if recetas.leer(con, usuario["id"], receta_id) is None:
            raise HTTPException(status_code=404, detail=f"no hay receta {receta_id}")
        return {"versiones": recetas.versiones(con, usuario["id"], receta_id)}
    finally:
        con.close()


@rutas.put("/{receta_id}")
def cambiar(receta_id: int, datos: CambioIn, usuario: dict = Depends(usuario_actual)) -> dict:
    con = _con()
    try:
        numero = recetas.actualizar(con, usuario["id"], receta_id, nombre=datos.nombre,
                                    raciones=datos.raciones, preparacion=datos.preparacion,
                                    ingredientes=_como_filas(datos.ingredientes),
                                    minutos=datos.minutos, etiquetas=datos.etiquetas)
        return {"version": numero,
                "receta": recetas.leer(con, usuario["id"], receta_id, version=numero)}
    except ValueError as fallo:
        raise HTTPException(status_code=404, detail=str(fallo)) from fallo
    finally:
        con.close()


@rutas.post("/{receta_id}/archivar")
def archivar(receta_id: int, archivada: bool = True,
             usuario: dict = Depends(usuario_actual)) -> dict:
    con = _con()
    try:
        if not recetas.archivar(con, usuario["id"], receta_id, archivada=archivada):
            raise HTTPException(status_code=404, detail=f"no hay receta {receta_id}")
        return {"id": receta_id, "archivada": archivada}
    finally:
        con.close()


@rutas.delete("/plan")
def quitar_plan(fecha: str = Query(...), receta_id: int = Query(...),
                usuario: dict = Depends(usuario_actual)) -> dict:
    """Quitar una receta de un dia. **Va al final a proposito y no puede chocar**: no hay ninguna otra ruta
    DELETE en este router, asi que la trampa del orden de rutas no aplica aqui.

    Responde 404 si no habia nada que quitar, que es lo mismo que hace el resto: no se dice "hecho" cuando no
    se ha hecho nada.
    """
    con = _con()
    try:
        if not recetas.quitar_del_plan(con, usuario["id"], fecha, receta_id):
            raise HTTPException(status_code=404, detail="ese dia no tiene esa receta planificada")
        return {"quitada": receta_id, "fecha": fecha}
    except ValueError as fallo:
        raise HTTPException(status_code=400, detail=str(fallo)) from fallo
    finally:
        con.close()


# ---------------------------------------------------------------------------------------------
# R02: importar una receta -- **la previa, que no escribe**
# ---------------------------------------------------------------------------------------------


class ImportarIn(BaseModel):
    """**Lo unico que manda el cliente es de donde.** *Nada mas: lo demas lo lee el servidor.*"""

    url: str = Field(min_length=1)


@rutas.post("/importar")
def importar(datos: ImportarIn, usuario: dict = Depends(usuario_actual)) -> dict:
    """**Lee una receta de una fuente permitida y devuelve el borrador.** *No guarda nada.*

    **Y el orden de las comprobaciones es la decision**, no un detalle:

    1. **Primero, la fuente.** *Si no esta declarada, **no se lee nada** -- *ni siquiera se intenta* --, y se
       devuelve **el motivo**: «la fuente no esta declarada: recetas.example.com». *Eso es lo que permite decir
       **«no puedo importar de ahi»** en vez de «no he encontrado ninguna receta en esa pagina», **que son dos
       cosas muy distintas*** y solo una es verdad.
    2. **Y despues, el formato**: *se lee **`application/ld+json` con `@type: Recipe`**, que es **el estandar que
       las webs de recetas publican*** -- *no un raspador a medida.* **Un sitio que no lo publique no se puede
       leer sin escribirlo a mano, y eso es scraping**: *por eso «fuente permitida» y «formato» son la misma
       decision.*
    3. **Y si hay receta, sale el borrador con su `fuente` dentro** -- *que es lo que permite **volver a
       comprobarla** dentro de un ano.* **Y no se guarda**: *`crear` escribe, y esto es la previa.*

    **Y cuando no se puede, se dice cual de las tres cosas ha pasado** -- *la fuente no vale, no hay receta, o
    hay receta y le faltan cosas* --, **porque son problemas distintos y se arreglan distinto.**
    """
    permiso = importar_receta.comprueba_fuente(datos.url)
    if not permiso.permitida:
        # **404 y no 403**, como en todo lo demas, pero aqui ademas **no tiene sentido leer**: no se ha leido.
        raise HTTPException(400, f"No se puede importar de esa direccion: {permiso.motivo}.")

    # *Se baja el HTML.* **Con tope de tiempo y de tamano**: una pagina que no contesta no puede colgar la
    # peticion, y una que pese 40 MB no es una receta.
    import urllib.request

    try:
        with urllib.request.urlopen(datos.url, timeout=10) as r:
            html = r.read(2_000_000).decode("utf-8", errors="replace")
    except Exception as e:
        raise HTTPException(502, f"No se pudo traer la pagina: {e}.") from e

    campos = importar_receta.lee_json_ld(html)
    if campos is None:
        # **Y esto se dice distinto que «la fuente no vale».** *Aqui la fuente SI vale, y la pagina **no trae una
        # receta legible** -- que puede ser que no sea una receta, o que ese sitio no publique el estandar.*
        raise HTTPException(422, "Esa pagina no trae una receta con datos estructurados "
                                 "(application/ld+json con @type: Recipe).")

    permiso2, b = importar_receta.borrador(datos.url, campos)
    if b is None:
        raise HTTPException(422, f"La receta no se puede previsualizar: {permiso2.motivo}.")

    # **El borrador, tal cual -- y `faltantes` viaja, para que la pantalla pueda decirlo.**
    return {
        "nombre": b.nombre, "raciones": b.raciones, "minutos": b.minutos,
        "preparacion": b.preparacion, "ingredientes": b.ingredientes,
        "fuente": b.fuente, "faltantes": b.faltantes,
        # **Y el aviso de que esto NO esta guardado**, para que nadie lo confunda con una receta.
        "guardada": False,
    }
