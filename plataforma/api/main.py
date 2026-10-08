"""Cesta: la API. La unica puerta a los datos.

Responde JSON y nunca HTML: la interfaz se sirve aparte. Dos mitades detras:

    catalogo.py   DuckDB sobre los parquet de gold. Solo lee. Cambia una vez
                  al dia, cuando el pipeline termina.
    almacen.py    PostgreSQL. Cuentas, listas y favoritos. Lo que escribis.

El registro esta abierto: cualquiera que llegue a la pagina puede crearse una
cuenta, y hoy a esa pagina solo se llega desde Tailscale. Se cierra con
`CESTA_REGISTRO=cerrado`. Ver `registro.py`, que explica cuando hay que hacerlo.
"""
from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import (
    alertas,
    almacen,
    analisis,
    catalogo,
    cesta,
    diario,
    habituales,
    movimientos,
    panel,
    recetas,
    registro,
    vigilante,
)
from .ajustes import AJUSTES



@asynccontextmanager
async def ciclo(app: FastAPI):
    almacen.arranca()
    catalogo.conexion()          # que falle al arrancar y no en la primera visita
    # El vigilante de las alertas: las mira cuando cambia gold, sin esperar a que
    # nadie abra la pantalla. Va en un hilo aparte y no puede tumbar la API (ver
    # `api/vigilante.py`).
    vigilante.arranca()
    yield
    vigilante.para()
    almacen.para()


app = FastAPI(title="Cesta", version="1.0", lifespan=ciclo,
              docs_url="/api/docs", openapi_url="/api/openapi.json")
app.include_router(panel.rutas)
app.include_router(recetas.rutas)
app.include_router(diario.rutas)
app.add_middleware(CORSMiddleware, allow_origins=list(AJUSTES.origenes),
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


# ------------------------------------------------------------ quien llama ---

# **La sesion vive en `sesion.py`** y se reexporta aqui por dos razones: los routers no pueden
# importar de `main` sin ciclo, y `main.usuario_actual` tiene que seguir existiendo porque las pruebas
# del proyecto lo usan como punto de sustitucion. Es el mismo objeto, no una copia: si fueran dos, el
# `dependency_overrides` de las pruebas sustituiria una y la aplicacion usaria la otra.
from .sesion import COOKIE, usuario_actual, usuario_opcional  # noqa: E402

# ----------------------------------------------------------------- entrar ---

class Credenciales(BaseModel):
    usuario: str
    clave: str
    dispositivo: str | None = None


@app.post("/api/entrar")
def entrar(c: Credenciales, respuesta: Response):
    resultado = almacen.entra(c.usuario, c.clave, c.dispositivo)
    if resultado is None:
        raise HTTPException(401, "Usuario o contraseña incorrectos.")
    token, yo = resultado
    respuesta.set_cookie(COOKIE, token, httponly=True, samesite="lax",
                         max_age=AJUSTES.dias_sesion * 86400, path="/")
    return {"usuario": yo}


class Alta(BaseModel):
    usuario: str
    nombre: str
    clave: str
    dispositivo: str | None = None


@app.post("/api/registrarse", status_code=201)
def registrarse(a: Alta, respuesta: Response):
    """Crear una cuenta y entrar con ella, en un solo paso.

    Entra sola a proposito: hacer que alguien rellene un formulario, le digan
    "cuenta creada" y tenga que escribir lo mismo otra vez en la pantalla de al
    lado es una pantalla de mas por nada. Y lo que trae aqui a la mayoria es un
    enlace de invitacion a una lista, que solo se aplica cuando hay sesion.
    """
    if not AJUSTES.registro_abierto:
        raise HTTPException(
            403, "El registro está cerrado. Pídele a quien lleva esta Cesta "
                 "que te dé de alta.")
    if problema := registro.revisa(a.usuario, a.nombre, a.clave):
        raise HTTPException(422, problema)
    if almacen.altas_en_la_ultima_hora() >= almacen.ALTAS_POR_HORA:
        raise HTTPException(
            429, "Se han creado demasiadas cuentas en la última hora. Prueba "
                 "dentro de un rato.")
    try:
        almacen.crea_usuario(registro.normaliza(a.usuario),
                             registro.limpia_nombre(a.nombre), a.clave)
    except almacen.UsuarioRepetido:
        raise HTTPException(409, "Ese usuario ya está cogido. Elige otro.") from None

    resultado = almacen.entra(a.usuario, a.clave, a.dispositivo)
    if resultado is None:                 # no deberia pasar nunca
        raise HTTPException(500, "La cuenta se creó pero no se pudo entrar.")
    token, quien = resultado
    respuesta.set_cookie(COOKIE, token, httponly=True, samesite="lax",
                         max_age=AJUSTES.dias_sesion * 86400, path="/")
    return {"usuario": quien}


@app.get("/api/personas")
def quien_hay(_: dict = Depends(usuario_actual)):
    """Quien tiene cuenta en esta Cesta y desde cuando.

    Con el registro abierto es la ventana que hace vigilable la puerta: si un
    dia aparece un nombre que no conoces, se ve aqui. Pide sesion -- quien no ha
    entrado no tiene por que saber quien hay dentro.
    """
    return {"personas": almacen.personas()}


@app.post("/api/salir")
def salir(peticion: Request, respuesta: Response):
    if token := peticion.cookies.get(COOKIE):
        almacen.sale(token)
    respuesta.delete_cookie(COOKIE, path="/")
    return {"hecho": True}


@app.get("/api/yo")
def yo(usuario: dict | None = Depends(usuario_opcional)):
    return {"usuario": usuario, "preferencias":
            almacen.preferencias_de(usuario["id"]) if usuario else {}}


# --------------------------------------------------------------- catalogo ---

@app.get("/api/buscar")
def buscar(q: str = "", cadenas: str | None = None, limite: int = 40,
           comparables: bool = False, con_nutricion: bool = False,
           sellos: str | None = None, conservacion: str | None = None,
           marca_propia: bool = False, ofertas: bool = False,
           sin_alcohol: bool = False, seccion: str | None = None,
           usuario: dict | None = Depends(usuario_opcional)):
    """Buscar por texto, por pasillo, o las dos cosas.

    `q` deja de ser obligatorio: explorar un pasillo es una busqueda sin texto.
    Sin ninguna de las dos, la respuesta es una lista vacia, no un error: es lo
    que hay que contestar cuando no se ha preguntado nada.

    **Y si no encuentra nada, lo intenta con las palabras arregladas.** El encargo pide
    que el buscador *"encuentre con faltas de ortografia"*, y medido el 23 de septiembre
    de 2026 no las encontraba: `lece entera`, `detergnete` y `asucar` devolvian **cero**
    resultados. La correccion es la de `catalogo.corregir` (palabra a palabra contra el
    diccionario del catalogo, mismo tamano, y a igualdad de parecido la palabra que mas
    aparece), y **solo se usa como ultimo recurso**: primero se busca lo que se ha
    escrito, y la correccion solo entra cuando no hay nada.

    `corregido` viaja en la respuesta **solo si la busqueda corregida encuentra algo**.
    Si tampoco encuentra nada, no se anuncia una correccion que no ha servido de nada: lo
    honesto es decir que no hay nada, con lo que se escribio.
    """
    lista = [c.strip() for c in cadenas.split(",")] if cadenas else None
    filtros = [s.strip() for s in sellos.split(",")] if sellos else None
    if lista is None and usuario:
        # Si no tiene Aldi cerca, sus resultados no deberian ensenarselo.
        cercanas = almacen.preferencias_de(usuario["id"]).get("cadenas_cerca")
        if cercanas:
            lista = list(cercanas)

    def busca(que: str) -> list:
        return catalogo.buscar(que, lista, limite, comparables, con_nutricion,
                               filtros, conservacion, marca_propia, ofertas,
                               sin_alcohol, seccion)

    resultados = busca(q)
    corregido = None
    if not resultados and q.strip():
        arreglado = catalogo.corregir(q)
        if arreglado:
            resultados = busca(arreglado)
            if resultados:
                corregido = arreglado
    return {"fecha_datos": catalogo.fecha_de_gold(),
            "resultados": resultados,
            **({"corregido": corregido} if corregido else {})}


@app.get("/api/secciones")
def secciones(cadenas: str | None = None,
              usuario: dict | None = Depends(usuario_opcional)):
    """Los pasillos, en el orden en que se recorre una tienda.

    Vacio mientras el scraper no haya escrito la columna `seccion` en gold. La
    web lo dice en vez de ensenar una pantalla en blanco.
    """
    lista = [c.strip() for c in cadenas.split(",")] if cadenas else None
    if lista is None and usuario:
        cercanas = almacen.preferencias_de(usuario["id"]).get("cadenas_cerca")
        if cercanas:
            lista = list(cercanas)
    return {"fecha_datos": catalogo.fecha_de_gold(),
            "secciones": catalogo.secciones(lista)}


@app.get("/api/indice")
def indice(desde: str | None = None):
    """Índice de precios por cadena. Ver `api/analisis.py` para el método."""
    return analisis.indice(desde)


@app.get("/api/pulso")
def pulso(desde: str | None = None):
    """Cuántos precios toca cada cadena en cada captura, y cuánto."""
    return analisis.pulso(desde)


@app.get("/api/posicion")
def posicion():
    """Dónde está cada cadena dentro de cada sección, sobre lo emparejado."""
    return analisis.posicion()


@app.get("/api/bajadas")
def bajadas(dias: int = 7, cadenas: str | None = None, limite: int = 60,
            subidas: bool = False, solo_mios: bool = False,
            usuario: dict | None = Depends(usuario_opcional)):
    """Lo que mas ha cambiado de precio esta semana.

    `dias` se acota a la ventana que el historico puede sostener: pedir 365 dias
    con trece en disco no da un error, da una respuesta vacia que parece un fallo.

    `solo_mios` contesta a la cuarta de las cuatro preguntas con las que se abre la
    aplicacion: *"¿ha bajado algo de lo mio?"*. Filtra por los grupos de esta persona
    -- sus listas y sus favoritos (`almacen.mis_grupos`) -- **en SQL**, no recortando
    la respuesta: con un limite de 60 por detras, filtrar despues dejaria fuera
    bajadas mias que no estan entre las sesenta mayores del catalogo. Sin sesion,
    `solo_mios` no puede saber que es "lo mio" y se contesta lo del catalogo, que es
    lo honesto: no se inventa un "tuyo" que no existe.
    """
    dias = max(1, min(dias, 90))
    lista = [c.strip() for c in cadenas.split(",")] if cadenas else None
    if lista is None and usuario:
        cercanas = almacen.preferencias_de(usuario["id"]).get("cadenas_cerca")
        if cercanas:
            lista = list(cercanas)
    # `None` es "no me filtres"; una lista vacia es "no tiene nada apuntado", y eso
    # es una respuesta distinta: no hay bajadas suyas porque no hay "suyo".
    grupos = None
    if solo_mios:
        grupos = almacen.mis_grupos(usuario["id"]) if usuario else None
        if grupos is not None and not grupos:
            return {"fecha_datos": catalogo.fecha_de_gold(), "dias": dias,
                    "sentido": "subidas" if subidas else "bajadas",
                    "solo_mios": True, "resultados": []}
    # **`solo_mios` dice si se filtro, no si se pidio.** Es la diferencia entre una
    # respuesta honesta y una que miente: sin sesion no hay "lo mio" (`grupos` se queda
    # en `None`) y se contesta el catalogo, asi que el campo tiene que decir `false`.
    # Poniendo lo que pidio el cliente, la pantalla ensenaria sesenta bajadas del
    # catalogo entero bajo el titulo "Solo lo mio" -- y eso se vio de verdad: lo
    # encontro la verificacion de punta a punta contra un PostgreSQL de verdad, porque
    # la prueba unitaria miraba los grupos que llegaban al SQL y no este campo.
    return {"fecha_datos": catalogo.fecha_de_gold(), "dias": dias,
            "sentido": "subidas" if subidas else "bajadas",
            "solo_mios": grupos is not None,
            "resultados": movimientos.bajadas(dias, lista, limite, subidas, grupos)}


@app.get("/api/ofertas-dudosas")
def ofertas_dudosas(limite: int = 60, cadenas: str | None = None,
                    usuario: dict | None = Depends(usuario_opcional)):
    """Ofertas anunciadas que el historico no sostiene.

    `sin_poder_juzgar` cuenta las que **no se pueden juzgar** con el precio de una
    unidad: las que dependen de cuantas compres (un 3x2 no baja el precio de una),
    las que no anuncian un descuento de precio (un "Stock Fuera" no es una oferta) y
    aquellas cuyo tamaño declarado cambio dentro de la ventana. Va en la respuesta
    porque la pantalla lo dice: es "no lo se", no "no hay ninguna".
    """
    lista = [c.strip() for c in cadenas.split(",")] if cadenas else None
    if lista is None and usuario:
        cercanas = almacen.preferencias_de(usuario["id"]).get("cadenas_cerca")
        if cercanas:
            lista = list(cercanas)
    return {"fecha_datos": catalogo.fecha_de_gold(),
            "resultados": movimientos.ofertas_dudosas(limite, lista),
            "sin_poder_juzgar": movimientos.ofertas_sin_poder_juzgar(lista)}


@app.get("/api/grupo/{grupo_id}")
def ficha(grupo_id: int):
    """El grupo entero, y el por que de que esos productos esten juntos.

    `explicacion` **solo viaja si hay algo que decir**: un grupo de un solo
    producto, o uno sin ningun par directo entre sus miembros, no tiene
    explicacion, y el campo se omite en vez de mandarse vacio. La pantalla sabe
    decir que ahi no hay nada que ensenar; un objeto vacio diria que se emparejo
    por nada, que es distinto de no saberlo.
    """
    g = catalogo.grupo(grupo_id)
    if g is None:
        raise HTTPException(404, "No tengo ese producto. Puede que ya no lo vendan.")
    respuesta = g | {"fecha_datos": catalogo.fecha_de_gold()}
    explicacion = catalogo.explicacion(grupo_id)
    if explicacion:
        respuesta["explicacion"] = explicacion
    return respuesta


@app.get("/api/panel/matching")
def panel_de_matching(limite: int = Query(20, ge=1, le=200)):
    """El panel de auditoria del matching.

    Ensenia las metricas de la ultima pasada, la comparacion con la anterior y
    una muestra de pares con **por que** se aceptaron. **No hay botones de
    aprobar ni rechazar**, y no los va a haber: el encargo dice que no hay
    validacion humana nunca, asi que aqui no hay ningun endpoint de escritura.
    """
    return catalogo.matching(limite)


@app.get("/api/ean/{codigo}")
def por_codigo_de_barras(codigo: str):
    """El escaner: lo que tengo en la mano, por su codigo de barras.

    Acepta el codigo como lo lea el lector (con espacios, con guiones, con ceros
    de mas). Un codigo que no sea un codigo es un 400; un codigo bueno que no
    conocemos es un 200 con `encontrado: false` y una explicacion, porque "no lo
    tengo" y "me lo has dado mal" son cosas distintas.
    """
    limpio = catalogo.normaliza_ean(codigo)
    if limpio is None:
        raise HTTPException(400, "Eso no es un codigo de barras: tienen entre 8 "
                                 "y 14 digitos.")
    return catalogo.por_ean(limpio)


@app.get("/api/producto/{cadena}/{id_fuente}")
def ficha_de_producto(cadena: str, id_fuente: str):
    """Un producto por su identificador **en la cadena**, no por el nuestro.

    Existe para la extension de navegador: lo unico que se puede sacar de la
    URL de un supermercado es su propio id. Devuelve, ademas de la ficha, el
    grupo entero, que es lo que contesta la pregunta que se hace alguien
    delante del estante -- *¿esta mas barato en otro sitio?*.
    """
    p = catalogo.producto(f"{cadena}:{id_fuente}")
    if p is None:
        raise HTTPException(404, "No tengo ese producto.")
    g = catalogo.grupo(p["grupo_id"]) if p.get("grupo_id") else None
    return {"fecha_datos": catalogo.fecha_de_gold(), "producto": p, "grupo": g}


@app.get("/api/estado")
def estado():
    """De que dia es cada cadena y que falta.

    La interfaz la pide al abrir: con ella sabe que precios puede dar por
    buenos. Es lo que sostiene la regla de que un precio viejo se ensena con su
    fecha pero no decide en que tienda comprar.
    """
    con = catalogo.conexion()
    filas = con.execute("""
        SELECT fuente, count(*) AS productos, max(fecha)::VARCHAR AS ultimo_dia
          FROM diario GROUP BY fuente ORDER BY fuente
    """).fetchall()
    hoy = catalogo.fecha_de_gold()
    return {
        "fecha_datos": hoy,
        "dias_precio_valido": AJUSTES.dias_precio_valido,
        "cadenas": [{"cadena": f[0], "productos": f[1], "ultimo_dia": f[2],
                     "al_dia": f[2] == hoy} for f in filas],
    }


# ------------------------------------------------------------- habituales ---

@app.get("/api/habituales")
def ver_habituales(limite: int = Query(24, ge=1, le=60),
                   usuario: dict = Depends(usuario_actual)):
    """El mosaico de lo habitual: lo que esta persona compra una y otra vez.

    Pide sesion, y no por costumbre: esto es **su** historial de compra. Ni el
    recuento de lo que compra la casa dice quien lo compro.

    `origen` dice de donde sale lo que se manda -- `"tuyo"`, `"de todos"` o
    `"basico"` --, porque los tres casos se pintan igual y significan cosas muy
    distintas: la pantalla tiene que poder decir *"todavia no se lo que sueles
    comprar"* en vez de inventarse un habito. El porque de cada uno, en
    `api/habituales.py`.
    """
    return habituales.lista(usuario["id"], limite)


# ----------------------------------------------------------------- listas ---

class NuevaLista(BaseModel):
    nombre: str
    es_de_casa: bool = False


class NuevaLinea(BaseModel):
    # El movil genera el id para poder anadir sin cobertura.
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nombre: str
    grupo_id: int | None = None
    producto_id: str | None = None
    cantidad: int = Field(default=1, ge=1, le=99)
    nota: str | None = None
    cadena_elegida: str | None = None     # se puede anadir ya sabiendo donde se compra


class CambioLinea(BaseModel):
    tachado: bool | None = None
    en_carrito: bool | None = None
    cantidad: int | None = Field(default=None, ge=1, le=99)
    nota: str | None = None
    borrado: bool | None = None
    # La tienda donde se compra esta linea. `None` **puesto a proposito** quita la
    # asignacion; no mandarlo la deja como estaba. La diferencia se resuelve con
    # `model_fields_set`, porque en JSON las dos cosas llegan igual (`null` y
    # ausente) y sin eso no habria forma de deshacer una asignacion.
    cadena_elegida: str | None = None
    momento: datetime | None = None       # la hora del movil, no la de llegada


class NombreLista(BaseModel):
    nombre: str = Field(min_length=1, max_length=80)


class EnTienda(BaseModel):
    """Poner (o quitar) la tienda de un grupo de lineas, o borrar la sublista.

    Tres botones de la pantalla con una sola forma:
      - `cadena` + `lineas`      esas lineas se compran ahi
      - `cadena` sin `lineas`    **toda** la lista se compra ahi
      - `borrar=True` + `cadena` la sublista de esa tienda se borra del tiron
    """
    cadena: str | None = None
    lineas: list[str] | None = None
    borrar: bool = False


class DesdeFavoritos(BaseModel):
    """Pasar favoritos a una lista, de uno en uno o todos de golpe."""
    grupo_ids: list[int] = []
    producto_ids: list[str] = []


class Compartir(BaseModel):
    usuario: str
    papel: str = "escribe"


def _acceso(lista_id: str, usuario: dict, hace_falta_escribir: bool = False) -> str:
    # Un identificador que no es un UUID no es un error del servidor: es una
    # direccion que no existe. Sin esta comprobacion, PostgreSQL rechaza el
    # texto al comparar contra una columna uuid y la peticion sale como 500 con
    # su traza en el log. Se vio al levantar la plataforma por primera vez, el
    # 18 de septiembre de 2026, pidiendo /api/listas/None.
    try:
        uuid.UUID(str(lista_id))
    except (ValueError, AttributeError, TypeError):
        raise HTTPException(404, "Esa lista no existe.") from None
    papel = almacen.papel_en(lista_id, usuario["id"])
    if papel is None:
        raise HTTPException(404, "Esa lista ya no esta. Puede que la haya borrado quien la creo.")
    if hace_falta_escribir and papel == "mira":
        raise HTTPException(403, "En esta lista solo puedes mirar. Pidele a quien la creo que te deje escribir.")
    return papel


@app.get("/api/listas")
def mis_listas(usuario: dict = Depends(usuario_actual)):
    return {"listas": almacen.listas_de(usuario["id"])}


@app.post("/api/listas", status_code=201)
def nueva_lista(datos: NuevaLista, usuario: dict = Depends(usuario_actual)):
    return almacen.crea_lista(usuario["id"], datos.nombre, datos.es_de_casa)


@app.delete("/api/listas/{lista_id}")
def borrar_lista(lista_id: str, usuario: dict = Depends(usuario_actual)):
    """Borra la lista entera. **Se archiva: desaparece y se puede recuperar.**

    Lo pidio el dueno el 25 de septiembre de 2026 (*"poder borrar sublista o lista
    del tiron"*). Archivar y no borrar de verdad porque estas listas se comparten:
    borrarlas de verdad le quita la compra a otra persona de un toque, y deshacerlo
    no puede depender de una copia de seguridad.
    """
    if _acceso(lista_id, usuario) != "dueno":
        raise HTTPException(403, "Solo quien la creo puede borrarla.")
    if not almacen.archiva_lista(lista_id, usuario["id"]):
        raise HTTPException(404, "Esa lista ya no esta.")
    return {"borrada": lista_id}


@app.post("/api/listas/{lista_id}/cerrar")
def cerrar_compra(lista_id: str, usuario: dict = Depends(usuario_actual)):
    """«He terminado la compra»: lo del carro se guarda como compra y sale de la lista.

    Lo pidio el encargo (tarea 10) y es la mitad que le faltaba al bucle: hasta hoy la
    lista sabia lo que **falta** y no lo que **se compro**. Lo que va en el carro son las
    lineas marcadas (`en_carrito`), que son las que se tachan en el pasillo; **lo que no se
    cogio se queda en la lista**, que es lo que hace que esto sirva: quien no encuentra el
    pan no quiere volver a apuntarlo.

    Los precios los pone `cesta.coste_por_linea`, que es quien puede mirar gold: aqui solo
    hay PostgreSQL y el precio vive en los parquet. Se guarda la compra **con sus precios**,
    porque gold se reescribe cada dia y una compra sin su precio no se puede volver a mirar.

    Y si no hay nada en el carro, se dice: pulsar el boton sin haber tachado nada no puede
    inventar una compra vacia. Devuelve cuantas lineas salieron, cuanto costo (con las que
    no tienen precio contadas aparte, que **no** se tiran) y cuantas quedan en la lista.
    """
    _acceso(lista_id, usuario, hace_falta_escribir=True)
    lineas = catalogo.con_pasillos(almacen.lineas_de(lista_id))
    # **Las lineas que apuntan a otro producto no tienen precio, y hay que quitarselo aqui.**
    # Sin esto, la compra guardaba el precio del grupo al que apunta la linea -- que hoy puede
    # ser un pintalabios en una linea que dice «leche entera» -- y el total mentia. Es el mismo
    # filtro que hace `ver_lista` antes de pintar, y tiene que estar en los dos sitios: lo que
    # se guarda no puede ser menos honesto que lo que se enseña.
    movidas = catalogo.lineas_movidas(lineas)
    lineas = [_linea_movida(ln) if str(ln.get("id")) in movidas else ln for ln in lineas]
    en_el_carro = [ln for ln in lineas if ln.get("en_carrito")]
    if not en_el_carro:
        raise HTTPException(409, "No hay nada en el carro: marca lo que te llevas y vuelve.")
    hecho = almacen.cierra_compra(lista_id, usuario["id"], cesta.coste_por_linea(en_el_carro))
    return hecho | {"total_cent": hecho["total_cent"]}


@app.get("/api/listas/{lista_id}/compras")
def ver_compras(lista_id: str, usuario: dict = Depends(usuario_actual)):
    """Las ultimas compras de una lista, con lo que costaron.

    Existe para que el dia que la pantalla lo pida no haya que decidir el modelo otra vez:
    lo que se guarda al cerrar es lo que hace falta para contestar «¿cuanto me gaste la
    ultima vez?». **No** hay `GET /api/compras/{id}` (el detalle linea a linea): la pantalla
    no lo pide todavia y el detalle se puede reconstruir de `compra_linea` cuando haga falta.
    """
    _acceso(lista_id, usuario)
    return {"compras": almacen.compras_de(lista_id),
            "fecha_datos": catalogo.fecha_de_gold()}


@app.patch("/api/listas/{lista_id}")
def renombrar_lista(lista_id: str, datos: NombreLista,
                    usuario: dict = Depends(usuario_actual)):
    _acceso(lista_id, usuario, hace_falta_escribir=True)
    hecho = almacen.renombra_lista(lista_id, datos.nombre, usuario["id"])
    if hecho is None:
        raise HTTPException(404, "Esa lista ya no esta.")
    return hecho


def _linea_movida(linea: dict) -> dict:
    """Una linea cuyo grupo ya no es su producto: se marca y se le quita el pasillo.

    El pasillo vive en el grupo, asi que el de una linea movida es el de **otro
    producto** (medido el 28 de septiembre de 2026: la leche entera salia bajo
    «Higiene y belleza»). Sin pasillo, la pantalla la pinta al final y sin encabezado,
    que es la cara que ya existe para las lineas sin seccion.
    """
    limpia = {k: v for k, v in linea.items()
              if k not in ("seccion", "pasillo", "pasillo_orden")}
    return limpia | {"producto_movido": True}


@app.get("/api/listas/{lista_id}")
def ver_lista(lista_id: str, usuario: dict = Depends(usuario_actual)):
    papel = _acceso(lista_id, usuario)
    # Cada linea con su pasillo: es lo que permite pintar la lista por tandas, con
    # el pasillo delante, que es como se usa de pie en la tienda. Se anade aqui y no
    # en `almacen.lineas_de` porque el pasillo vive en gold (DuckDB) y las lineas en
    # PostgreSQL: son dos almacenes distintos y se juntan en la capa que ya habla
    # con los dos. Y **no se reordena nada aqui**: la pantalla es la que sabe
    # cuantas secciones tiene la lista y en que orden se pintan.
    lineas = catalogo.con_pasillos(almacen.lineas_de(lista_id))
    # **Y si el grupo ya no es el producto que la linea dice, se dice.** El
    # `grupo_id` es un ordinal que el emparejador renumera en cada pasada, asi que
    # una linea puede estar apuntando a otra cosa: sin esta marca, la pantalla
    # pinta el pasillo y el precio del producto equivocado (medido el 28 de
    # septiembre de 2026: «Leche entera» en el pasillo de higiene y belleza, con el
    # precio de una barra de labios). Ver `catalogo.lineas_movidas`.
    #
    # **Y se le quita el pasillo**, porque el pasillo tambien es del grupo: dejarlo
    # seria decir que la leche esta en higiene y belleza, que es justo la mentira que
    # se esta arreglando. Sin pasillo, la pantalla la pinta al final y sin
    # encabezado, que es la cara que ya existe para una linea sin seccion.
    movidas = catalogo.lineas_movidas(lineas)
    lineas = [_linea_movida(ln) if str(ln.get("id")) in movidas else ln for ln in lineas]
    nuevo = almacen.novedades(lista_id, usuario["id"])
    almacen.marca_visita(lista_id, usuario["id"])
    return {
        "papel": papel,
        "lineas": lineas,
        # Lo que va a costar, ahora mismo, en la cadena mas barata de cada cosa.
        # Es lo primero que se mira al ir anadiendo, mucho antes de calcular
        # donde comprarla entera.
        "estimacion": cesta.estimacion(lineas),
        "novedades": nuevo,
        "personas": almacen.quienes_en(lista_id),
        "fecha_datos": catalogo.fecha_de_gold(),
    }


@app.post("/api/listas/{lista_id}/lineas", status_code=201)
def anadir(lista_id: str, linea: NuevaLinea, usuario: dict = Depends(usuario_actual)):
    _acceso(lista_id, usuario, hace_falta_escribir=True)
    # Una linea sin destino no se puede comparar con nada, y la base lo rechaza
    # con una restriccion (`linea_con_destino`). Sin esta comprobacion, ese
    # rechazo llegaba como un **500** "el servidor ha fallado", que es mentira y
    # ademas manda a mirar los registros: es una peticion mal formada, o sea un
    # 422. La interfaz siempre manda uno de los dos, asi que esto no se ve desde
    # la pantalla; se ve desde `curl`, que es donde se prueba una API.
    if linea.grupo_id is None and linea.producto_id is None:
        raise HTTPException(
            422, "Una linea necesita el grupo o el producto al que se refiere.")
    return almacen.anade_linea(lista_id, usuario["id"], linea.id, linea.nombre,
                               linea.grupo_id, linea.producto_id,
                               linea.cantidad, linea.nota, linea.cadena_elegida)


@app.patch("/api/listas/{lista_id}/lineas/{linea_id}")
def cambiar(lista_id: str, linea_id: str, cambio: CambioLinea,
            usuario: dict = Depends(usuario_actual)):
    _acceso(lista_id, usuario, hace_falta_escribir=True)
    momento = cambio.momento
    if momento is not None and momento.tzinfo is None:
        momento = momento.replace(tzinfo=timezone.utc)
    # Nunca en el futuro: un movil con la hora mal no puede ganar siempre.
    ahora = datetime.now(timezone.utc)
    if momento is not None and momento > ahora:
        momento = ahora
    resultado = almacen.cambia_linea(lista_id, linea_id, usuario["id"],
                                     tachado=cambio.tachado, cantidad=cambio.cantidad,
                                     borrado=cambio.borrado,
                                     en_carrito=cambio.en_carrito, momento=momento,
                                     # Ausente = no tocar; `null` = quitarla. Es la misma
                                     # regla que `cadena_elegida`, y aqui importa: la
                                     # pantalla borra la nota mandando `null`.
                                     nota=(cambio.nota
                                           if "nota" in cambio.model_fields_set
                                           else almacen.SIN_CAMBIAR),
                                     cadena_elegida=(cambio.cadena_elegida
                                                     if "cadena_elegida" in cambio.model_fields_set
                                                     else almacen.SIN_CAMBIAR))
    if resultado is None:
        raise HTTPException(404, "Esa linea ya no esta en la lista. Puede que la haya quitado la otra persona.")
    return resultado


@app.post("/api/listas/{lista_id}/tienda")
def en_tienda(lista_id: str, datos: EnTienda, usuario: dict = Depends(usuario_actual)):
    """Elegir tienda: para una linea, para toda la lista o para borrar la sublista.

    Es la operacion que pidio el dueno: *"en la lista poder elegir en que supermercado
    lo quiero comprar... con opciones para eliminar facilmente de la lista cosas,
    poder borrar sublista o lista del tiron"*.
    """
    _acceso(lista_id, usuario, hace_falta_escribir=True)
    if datos.cadena is not None and datos.cadena not in cesta.CADENAS:
        raise HTTPException(422, f"'{datos.cadena}' no es una de las cadenas: "
                                 f"{', '.join(cesta.CADENAS)}")
    if datos.borrar:
        if datos.cadena is None:
            raise HTTPException(422, "Para borrar una sublista hace falta decir de que tienda.")
        cuantas = almacen.borra_lineas_de_tienda(lista_id, datos.cadena, usuario["id"])
        return {"borradas": cuantas, "cadena": datos.cadena}
    if datos.lineas:
        cuantas = almacen.pon_tienda(lista_id, datos.cadena, usuario["id"], datos.lineas)
        return {"puestas": cuantas, "cadena": datos.cadena}
    # Sin `lineas`: toda la lista, que es el boton de «todo en DIA».
    todas = [x["id"] for x in almacen.lineas_de(lista_id) if x["tachado_en"] is None]
    return {"puestas": almacen.pon_tienda(lista_id, datos.cadena, usuario["id"], todas),
            "cadena": datos.cadena}


@app.post("/api/listas/{lista_id}/desde-favoritos", status_code=201)
def desde_favoritos(lista_id: str, datos: DesdeFavoritos,
                    usuario: dict = Depends(usuario_actual)):
    """Pasar favos a la lista sin salir de favoritos.

    *"Que sea facil anadir a una lista productos que ya esta en favoritos, esa seria
    la ventaja de tener favoritos configurado"* (25 de septiembre de 2026). Se hace
    en una peticion y no en veinte: una lista de la compra se monta de golpe, y
    veinte viajes de ida y vuelta desde el movil en la puerta de la tienda no son
    una forma de hacerlo.
    """
    _acceso(lista_id, usuario, hace_falta_escribir=True)
    if not datos.grupo_ids and not datos.producto_ids:
        raise HTTPException(422, "No has dicho que favoritos anadir.")
    puestos = 0
    for grupo_id in datos.grupo_ids:
        # El nombre que se guarda en la linea es **el del producto**, no el numero
        # del grupo: `nombre_visto` se pinta tal cual en la lista y "Favorito 4821"
        # no le sirve a nadie de pie en el supermercado. Si el grupo ya no esta en
        # gold (lo rehizo el emparejador), se guarda lo que se sepa y la linea sigue
        # siendo valida: el grupo es la referencia, el nombre es una comodidad.
        g = catalogo.grupo(grupo_id) or {}
        nombre = g.get("nombre") or f"Producto {grupo_id}"
        almacen.anade_linea(lista_id, usuario["id"], str(uuid.uuid4()),
                            nombre, grupo_id, None, 1, None)
        puestos += 1
    for producto_id in datos.producto_ids:
        p = catalogo.producto(producto_id) or {}
        almacen.anade_linea(lista_id, usuario["id"], str(uuid.uuid4()),
                            p.get("nombre") or producto_id, None, producto_id, 1, None)
        puestos += 1
    return {"anadidos": puestos}


@app.get("/api/listas/{lista_id}/reparto")
def reparto(lista_id: str, cadenas: str | None = None,
            usuario: dict = Depends(usuario_actual)):
    """La lista partida por tiendas: sublistas, totales y lo que queda por decidir.

    Es la pantalla que pidio el dueno el 25 de septiembre de 2026. `donde` contesta
    *«¿donde sale mas barata esta lista?»* y esta contesta *«¿que he decidido, y
    cuanto me cuesta asi?»*: cada linea lleva su `cadena_elegida`, y aquí se agrupa
    por tienda, se aplican las ofertas y se dice el total de cada sublista y el de
    la lista entera.
    """
    _acceso(lista_id, usuario)
    lineas = [x for x in almacen.lineas_de(lista_id) if x["tachado_en"] is None]
    # Las que apuntan a otro producto no se reparten: se estaria decidiendo la tienda
    # de un producto que no es el que dice la linea. Se quedan fuera del reparto y la
    # pantalla las señala en la lista (`producto_movido`).
    movidas = catalogo.lineas_movidas(lineas)
    lineas = [x for x in lineas if str(x["id"]) not in movidas]
    peticiones = [cesta.Peticion(x["grupo_id"], x["producto_id"], x["cantidad"],
                                 x["nombre_visto"], x["id"]) for x in lineas]
    elegidas = [x.get("cadena_elegida") for x in lineas]
    prefs = almacen.preferencias_de(usuario["id"])
    lista_cadenas = ([c.strip() for c in cadenas.split(",")] if cadenas
                     else prefs.get("cadenas_cerca"))
    cuerpo = cesta.reparto_por_tienda(peticiones, elegidas, lista_cadenas)
    return cuerpo | {"fecha_datos": catalogo.fecha_de_gold()}


@app.post("/api/listas/{lista_id}/sincronizar")
def sincronizar(lista_id: str, cambios: list[dict], usuario: dict = Depends(usuario_actual)):
    """Lo que se hizo sin cobertura, todo de golpe.

    Cada cambio lleva su hora del movil. Como anadir y tachar son idempotentes,
    subir dos veces lo mismo no rompe nada: es justo lo que pasa cuando la red
    va y viene en el pasillo del supermercado.
    """
    _acceso(lista_id, usuario, hace_falta_escribir=True)
    hechos, fallidos = 0, []
    for c in cambios:
        try:
            if c.get("tipo") == "anadir":
                almacen.anade_linea(lista_id, usuario["id"], c["id"], c["nombre"],
                                    c.get("grupo_id"), c.get("producto_id"),
                                    c.get("cantidad", 1), c.get("nota"),
                                    c.get("cadena_elegida"))
            else:
                momento = c.get("momento")
                almacen.cambia_linea(
                    lista_id, c["id"], usuario["id"],
                    tachado=c.get("tachado"), cantidad=c.get("cantidad"),
                    borrado=c.get("borrado"),
                    en_carrito=c.get("en_carrito"),
                    # Ausente = no tocar la nota; `null` = quitarla. En la cola sin cobertura
                    # el cambio viaja tal y como se hizo en el movil, asi que la misma regla
                    # que `cadena_elegida`.
                    nota=c.get("nota", almacen.SIN_CAMBIAR),
                    # Elegir tienda sin cobertura en el pasillo es justo uno de los
                    # cambios que hay que poder subir despues, asi que viaja en la cola
                    # como los demas. Ausente = no tocar; `null` = quitar la tienda.
                    cadena_elegida=c.get("cadena_elegida", almacen.SIN_CAMBIAR),
                    momento=datetime.fromisoformat(momento) if momento else None)
            hechos += 1
        # Un cambio malo no puede impedir que suban los demas: el movil manda lo
        # que tenga guardado, y alguno puede referirse a una linea que la otra
        # persona ya borro.
        except Exception as exc:  # noqa: BLE001
            fallidos.append({"id": c.get("id"), "motivo": type(exc).__name__})
    return {"aplicados": hechos, "fallidos": fallidos,
            # Con pasillo, igual que `ver_lista`: las dos devuelven lineas y la
            # pantalla las pinta con el mismo codigo. Que una traiga el pasillo y
            # la otra no seria una lista que cambia de forma segun por donde haya
            # entrado el dato.
            "lineas": catalogo.con_pasillos(almacen.lineas_de(lista_id))}


@app.post("/api/listas/{lista_id}/compartir")
def compartir(lista_id: str, datos: Compartir, usuario: dict = Depends(usuario_actual)):
    if _acceso(lista_id, usuario) != "dueno":
        raise HTTPException(403, "solo quien la creo puede compartirla")
    if datos.papel not in ("escribe", "mira"):
        raise HTTPException(400, "el papel es 'escribe' o 'mira'")
    hecho = almacen.comparte(lista_id, datos.usuario, usuario["id"], datos.papel)
    if hecho is None:
        raise HTTPException(404, "No hay nadie con ese usuario. Comprueba como se escribe, o mandale un enlace de invitacion.")
    return hecho


class Invitacion(BaseModel):
    papel: str = "escribe"
    usos: int = Field(default=1, ge=1, le=10)
    dias: int = Field(default=7, ge=1, le=30)


@app.post("/api/listas/{lista_id}/invitacion", status_code=201)
def invitar(lista_id: str, datos: Invitacion, usuario: dict = Depends(usuario_actual)):
    """Un enlace para mandar por WhatsApp.

    Pedirle a alguien que teclee un nombre de usuario es pedirle que se
    equivoque. El enlace caduca, y se puede revocar.
    """
    if _acceso(lista_id, usuario) != "dueno":
        raise HTTPException(403, "solo quien la creo puede invitar")
    if datos.papel not in ("escribe", "mira"):
        raise HTTPException(400, "el papel es 'escribe' o 'mira'")
    try:
        inv = almacen.crea_invitacion(lista_id, usuario["id"], datos.papel,
                                      datos.usos, datos.dias)
    except ValueError as exc:
        # 409: no es que la peticion este mal, es que hay que resolver algo antes.
        raise HTTPException(409, str(exc)) from exc
    return {"codigo": inv["codigo"], "papel": inv["papel"],
            "expira_en": inv["expira_en"], "ruta": f"/unirme/{inv['codigo']}"}


@app.post("/api/invitacion/{codigo}")
def aceptar_invitacion(codigo: str, usuario: dict = Depends(usuario_actual)):
    hecho = almacen.acepta_invitacion(codigo, usuario["id"])
    if hecho is None:
        raise HTTPException(404, "Ese enlace ya no vale: caduca a los siete dias, y puede que ya lo hayan usado. Pidele otro a quien te lo mando.")
    return hecho


@app.delete("/api/listas/{lista_id}/invitacion")
def revocar_invitaciones(lista_id: str, usuario: dict = Depends(usuario_actual)):
    if _acceso(lista_id, usuario) != "dueno":
        raise HTTPException(403, "solo quien la creo puede hacer esto")
    return {"revocadas": almacen.revoca_invitaciones(lista_id)}


@app.get("/api/listas/{lista_id}/donde")
def donde(lista_id: str, cadenas: str | None = None, max_tiendas: int | None = None,
          usuario: dict = Depends(usuario_actual)):
    """Donde sale mas barata esta lista. Con las ofertas puestas."""
    _acceso(lista_id, usuario)
    lineas = [x for x in almacen.lineas_de(lista_id) if x["tachado_en"] is None]
    # Igual que en el reparto: una linea que apunta a otro producto no se compara, no
    # sea que «donde sale mas barata» conteste con el precio de otra cosa.
    movidas = catalogo.lineas_movidas(lineas)
    lineas = [x for x in lineas if str(x["id"]) not in movidas]
    peticiones = [cesta.Peticion(x["grupo_id"], x["producto_id"],
                                 x["cantidad"], x["nombre_visto"]) for x in lineas]
    prefs = almacen.preferencias_de(usuario["id"])
    lista_cadenas = ([c.strip() for c in cadenas.split(",")] if cadenas
                     else prefs.get("cadenas_cerca"))
    return cesta.donde_comprar(peticiones, lista_cadenas, max_tiendas) | {
        "fecha_datos": catalogo.fecha_de_gold()}


# -------------------------------------------------------------- favoritos ---

class Favorito(BaseModel):
    grupo_id: int | None = None
    producto_id: str | None = None


@app.get("/api/alertas")
def ver_alertas(usuario: dict = Depends(usuario_actual)):
    """Las alertas de esta persona y cuales saltan hoy.

    Las que saltan se devuelven con la frase que las explica; marcarlas como
    vistas es otra llamada, para que no se den por leidas solo por abrir la
    pantalla en el autobus.

    Y **`salto_en` dice cuando se cumplio la condicion, no cuando has entrado a
    mirar**: lo apunta el vigilante (`api/vigilante.py`) en cuanto cambia gold, para
    que un aviso no dependa de que alguien abra la pantalla. Esa es la mitad que
    faltaba del punto 6 del encargo. `vista_en` sigue siendo tuyo.

    Y la otra mitad es que **abrir esto sea instantaneo**: la evaluacion va por
    `alertas.evalua_con_memoria`, que recuerda el veredicto mientras gold no cambie. Se
    midio que sin eso la pantalla tardaba 469 ms con una sola alerta.
    """
    mias = almacen.alertas_de(usuario["id"])
    # Cada alerta con **la tarjeta de su grupo**: sin el nombre, la pantalla solo puede
    # decir "producto", y un aviso que no dice de que producto es no es un aviso. Se
    # pide la tarjeta a gold, que es quien sabe como esta hoy ese grupo; un grupo que ya
    # no esta en el catalogo sale sin tarjeta y la pantalla lo dice.
    tarjetas = catalogo.tarjetas([a["grupo_id"] for a in mias])
    mias = [a | tarjetas.get(a["grupo_id"], {}) for a in mias]
    return {"fecha_datos": catalogo.fecha_de_gold(),
            "alertas": mias,
            "saltan": alertas.evalua_con_memoria([a for a in mias if not a["vista_en"]])}


@app.post("/api/alertas", status_code=201)
def crear_alerta(cuerpo: dict, usuario: dict = Depends(usuario_actual)):
    try:
        return almacen.crea_alerta(
            usuario["id"], int(cuerpo["grupo_id"]), str(cuerpo.get("tipo", "")),
            int(cuerpo["umbral_cent"]) if cuerpo.get("umbral_cent") else None)
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(400, str(exc)) from exc


@app.delete("/api/alertas/{alerta_id}", status_code=204)
def borrar_alerta(alerta_id: str, usuario: dict = Depends(usuario_actual)):
    if not almacen.borra_alerta(usuario["id"], alerta_id):
        raise HTTPException(404, "esa alerta no es tuya o ya no existe")


@app.post("/api/alertas/vistas")
def alertas_vistas(cuerpo: dict, usuario: dict = Depends(usuario_actual)):
    ids = [str(i) for i in (cuerpo.get("ids") or [])]
    return {"marcadas": almacen.marca_alertas_vistas(usuario["id"], ids)}


def _orden_de_favoritos(f: dict) -> tuple:
    """Lo que ha bajado arriba (y lo que más, primero), después lo que ha subido, y al final
    lo que no se ha movido.

    El orden lo decide **el signo de la variación**, no un umbral: un 0,4 % en el precio por
    unidad es un movimiento de verdad (un céntimo en un euro), y llamarlo «igual» sería
    esconder el dato. Lo que no se puede comparar va al final y con su motivo, no con un 0 %.
    """
    if not f.get("comparable"):
        return (3, 0.0, f.get("nombre") or "")
    pct = f.get("variacion_pct") or 0.0
    if pct < 0:
        return (0, pct, f.get("nombre") or "")          # la mayor bajada, primero
    if pct > 0:
        return (1, -pct, f.get("nombre") or "")         # la mayor subida, primero
    return (2, 0.0, f.get("nombre") or "")              # quieto, detrás de los dos


def _favorito_sin_catalogo(f: dict, que: str, dias: int) -> dict:
    """Un favorito que ya no se puede resolver, dicho en vez de borrado.

    Si alguien sigue un producto y ese producto desaparece del catálogo, la pantalla tiene que
    poder decirlo —y dejar quitarlo—, no enseñar una lista más corta sin explicar por qué. Es
    la misma regla que la línea movida de la lista: lo que no se puede enseñar se dice.
    """
    return {
        "grupo_id": f.get("grupo_id"), "producto_id": f.get("producto_id"),
        "nombre": None, "marca": None, "unidad": None, "precio_cent": None,
        "precio_unidad_cent": None, "cadena": None, "imagen": None,
        "ahorro_pct": None, "n_cadenas": 0,
        "desconocido": True, "que": que, "anadido_en": str(f.get("anadido_en") or ""),
        "comparable": False, "motivo": "ya no esta en el catalogo",
        "variacion_pct": None, "precio_unidad_antes_cent": None,
        "dias_medidos": None, "dias": dias,
    }


@app.get("/api/favoritos")
def ver_favoritos(dias: int = 7, usuario: dict = Depends(usuario_actual)):
    """Los que sigues, con su estado de hoy **y ordenados por lo que se han movido**.

    Lo que ha bajado arriba (y lo que más, primero), después lo que ha subido, y al final lo
    que no se ha movido: es una pantalla de vigilancia, no un catálogo, y lo que se viene a
    saber es «¿se ha movido algo de lo que compro siempre?».

    **Esto estaba escrito aquí desde el primer día y no se hacía.** El 30 de septiembre de 2026
    esta función decía «ordenados por lo que ha cambiado y no alfabéticamente: lo que ha bajado
    arriba, lo que ha subido debajo, lo quieto al final» y lo que hacía era devolverlos en el
    orden en que se añadieron: el texto prometía una cosa y el código otra. Ahora el orden y la
    variación salen de `movimientos.cambios_de_grupos`, que además dice lo que **no se puede
    comparar** (`comparable: false` con su `motivo`) en vez de contar un 0 %.

    `dias` es la ventana (7 por defecto). `dias_medidos` dice los días que hay de verdad: un
    producto que lleva tres días en el catálogo dice tres, no siete, y la pantalla lo enseña.

    Y las dos formas de seguir algo -- un grupo (la ficha del grupo) o un producto concreto (la
    ficha del producto) -- salen **con la misma forma**. Antes la de producto devolvía el sobre
    entero de `catalogo.producto` y la pantalla pintaba una tarjeta sin nombre.
    """
    favs = almacen.favoritos_de(usuario["id"])
    grupos = [f["grupo_id"] for f in favs if f["grupo_id"] is not None]
    cambios = movimientos.cambios_de_grupos(grupos, dias)
    sin_medida = {"comparable": False, "motivo": "sin historico", "variacion_pct": None,
                  "precio_unidad_antes_cent": None, "dias_medidos": None, "dias": dias}

    salida = []
    for f in favs:
        if f["grupo_id"] is not None:
            g = catalogo.grupo(f["grupo_id"])
            if not g:
                salida.append(_favorito_sin_catalogo(f, "grupo", dias))
                continue
            p = g["productos"][0]
            item = {
                "grupo_id": f["grupo_id"], "producto_id": p["producto_id"],
                "nombre": p["nombre"], "marca": p["marca"], "unidad": p["unidad"],
                "precio_cent": p["precio_cent"],
                "precio_unidad_cent": p["precio_unidad_cent"],
                "cadena": p["fuente"], "imagen": p["imagen"],
                "ahorro_pct": g["ahorro_pct"], "n_cadenas": len(g["productos"]),
            }
        else:
            p = catalogo.producto(f["producto_id"])
            if not p:
                salida.append(_favorito_sin_catalogo(f, "producto", dias))
                continue
            # `catalogo.producto` devuelve el producto **plano** (no un sobre con
            # `producto` dentro, como `por_ean`): la primera version de esto ultimo
            # buscaba `d["producto"]` y daba un 500 en cuanto un favorito apuntaba a un
            # producto concreto.
            item = {
                "grupo_id": p.get("grupo_id"), "producto_id": p["producto_id"],
                "nombre": p["nombre"], "marca": p["marca"], "unidad": p["unidad"],
                "precio_cent": p["precio_cent"],
                "precio_unidad_cent": p["precio_unidad_cent"],
                "cadena": p["fuente"], "imagen": None,
                "ahorro_pct": None, "n_cadenas": 1,
            }
        # La clave del cambio es `(cadena, id_fuente)`, y el `id_fuente` se saca del
        # `producto_id` («fuente:id_fuente»), que es lo único que tienen las dos formas:
        # `catalogo.grupo` lo trae suelto y `catalogo.producto` no.
        item |= cambios.get(
            (item["cadena"], str(item["producto_id"]).partition(":")[2]), sin_medida)
        salida.append(item)
    salida.sort(key=_orden_de_favoritos)
    return {"favoritos": salida, "dias": dias, "fecha_datos": catalogo.fecha_de_gold()}


@app.post("/api/favoritos", status_code=201)
def anadir_favorito(f: Favorito, usuario: dict = Depends(usuario_actual)):
    if f.grupo_id is None and not f.producto_id:
        raise HTTPException(400, "hace falta un grupo o un producto")
    almacen.anade_favorito(usuario["id"], f.grupo_id, f.producto_id)
    return {"hecho": True}


@app.delete("/api/favoritos")
def quitar_favorito(f: Favorito, usuario: dict = Depends(usuario_actual)):
    almacen.quita_favorito(usuario["id"], f.grupo_id, f.producto_id)
    return {"hecho": True}


class Preferencia(BaseModel):
    clave: str
    valor: object


@app.put("/api/preferencias")
def guardar_preferencia(p: Preferencia, usuario: dict = Depends(usuario_actual)):
    almacen.guarda_preferencia(usuario["id"], p.clave, p.valor)
    return {"hecho": True}


@app.delete("/api/yo")
def borrarme(peticion: Request, respuesta: Response,
             usuario: dict = Depends(usuario_actual)):
    """Darse de baja.

    Quien presta su ordenador para que otros guarden su lista de la compra tiene
    que darles la puerta de salida. Se lleva sus listas propias, sus favoritos y
    sus sesiones; lo que anadio a listas de otros se queda, sin autor, porque
    borrarlo vaciaria la lista de alguien que no ha pedido nada.
    """
    hecho = almacen.borra_usuario(usuario["id"])
    if token := peticion.cookies.get(COOKIE):
        almacen.sale(token)
    respuesta.delete_cookie(COOKIE, path="/")
    return hecho


@app.get("/api/salud")
def salud():
    return {"vivo": True, "fecha_datos": catalogo.fecha_de_gold()}
