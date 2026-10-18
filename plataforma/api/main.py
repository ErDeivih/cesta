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

import hashlib
import json
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import psycopg
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from core import gasto, traspaso

from . import (
    alertas,
    almacen,
    analisis,
    catalogo,
    cesta,
    cocina,
    despensa,
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
app.include_router(despensa.rutas)
app.include_router(cocina.rutas)
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
           usuario: dict | None = Depends(usuario_opcional),
           desplazamiento: int = Query(0, ge=0)):
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
                               sin_alcohol, seccion, desplazamiento=desplazamiento)

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


def _version_del_catalogo() -> str | None:
    """La version publicada, leida del puntero.

    Sin importar core.publicacion: ese modulo trae polars -- publica DataFrames -- y la imagen de la API no
    lo lleva, que es una restriccion con prueba propia. Leer un JSON pequeno no justifica arrastrar una
    libreria de datos entera.
    """
    try:
        return json.loads((AJUSTES.gold / "actual.json").read_text(encoding="utf-8"))["version"]
    except (OSError, KeyError, ValueError):
        return None


@app.get("/api/estado")
def estado():
    """De que dia es cada cadena y que falta.

    La interfaz la pide al abrir: con ella sabe que precios puede dar por
    buenos. Es lo que sostiene la regla de que un precio viejo se ensena con su
    fecha pero no decide en que tienda comprar.
    """
    con = catalogo.conexion()
    filas = con.execute("""
        WITH ultimas AS (
            SELECT fuente, max(fecha) AS fecha FROM diario GROUP BY fuente
        )
        SELECT d.fuente, count(DISTINCT d.id_fuente) AS productos,
               u.fecha::VARCHAR AS ultimo_dia
          FROM diario d JOIN ultimas u ON d.fuente = u.fuente AND d.fecha = u.fecha
         GROUP BY d.fuente, u.fecha ORDER BY d.fuente
    """).fetchall()
    hoy = catalogo.fecha_de_gold()

    # **Y la cobertura, cuando una cadena la declara.** *Y hoy solo la declara Lidl, y no es casualidad: es
    # la unica cuyo catalogo es **parcial**.*
    #
    # *El problema que esto resuelve, medido el 13 de octubre de 2026*: **`/api/estado` daba, por cadena,
    # `productos` y nada mas** --
    #
    #     alcampo    22816
    #     lidl          77
    #
    # **-- y esos dos numeros no son la misma clase de numero.** *22 816 es un catalogo; **77 son las fichas
    # de una campana semanal**.* **Y `productos` no lo distingue**, asi que un 77 se lee como «Lidl tiene 77
    # productos» -- *que es falso, y es justo lo que el plan prohibe*: «sin presentar ausencias de captura
    # como indisponibilidad».
    #
    # *Asi que se lee el fichero que **el propio colector ya escribe** para esto* (`data/cobertura/
    # {fuente}-{fecha}.json`), **y se pone al lado del numero.** *Un `77` con
    # `ofertas_semanales_parcial` y `con_precio 77 de 79` al lado es un dato; un `77` solo es un catalogo
    # pequeno.
    #
    # **Y aqui habia una cita POR NUMERO DE LINEA** -- *`collectors/lidl.py:273`* --, *y **se ha quitado**:
    # *el numero **ya no apuntaba a donde se escribe la cobertura**, y **no puede apuntar bien**, porque
    # **cualquier cambio por encima lo mueve.** *El fichero lo escribe **`lidl.main`**, despues de
    # `write_parquet`, bajo **`config.DATA / "cobertura"`** -- *y eso **si** se puede citar, porque **el
    # nombre de la funcion no se mueve cuando se anade una linea.** *
    #
    # *Lo que si se puede citar de un fichero ajeno es **lo que no cambia de sitio**: un nombre de funcion,
    # una constante, o la RUTA del fichero que produce. *Una linea, no.**
    #
    # **Y si el fichero no esta, no se inventa nada**: la cadena sale sin `cobertura`, *que es lo correcto
    # para las cinco que si catalogan entero.*
    def _cobertura(fuente: str, dia: str | None) -> dict | None:
        if not dia:
            return None
        # **La raiz es la del CATALOGO, no `config.DATA`.** *Y esto costo una comprobacion*: en el
        # contenedor, `config.DATA` vale `/app/data` -- **que no es donde estan los datos** --, mientras
        # que el catalogo lee `/datos/gold`.* **Medido el 13 de octubre de 2026:**
        #
        #     host   config.DATA = F:\aprendizaje\scrap\data
        #     docker config.DATA = /app/data        <- y los datos en /datos
        #
        # *Asi que la cobertura se busca al lado del gold, que es la raiz que **si** apunta a los datos:*
        # **el fichero existe en los dos sitios, pero solo uno es el que el contenedor ve.**
        fichero = AJUSTES.gold.parent / "cobertura" / f"{fuente}-{dia}.json"
        if not fichero.is_file():
            return None
        try:
            return json.loads(fichero.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            # *Un fichero ilegible no puede tumbar el estado*: se dice que no se pudo leer, en vez de
            # callarlo y que la cadena parezca completa.
            return {"cobertura": "no_se_pudo_leer", "aviso": f"no se pudo leer {fichero.name}"}

    return {
        "fecha_datos": hoy,
        # **De que catalogo salen esos precios.** `fecha_datos` dice el dia; esto dice la version, que es
        # lo que permite atar un precio a su origen y distinguir dos respuestas del mismo dia.
        "version_catalogo": _version_del_catalogo(),
        "vigencia_precio": _vigencia_del_catalogo(),
        "dias_precio_valido": AJUSTES.dias_precio_valido,
        "cadenas": [{**{"cadena": f[0], "productos": f[1], "ultimo_dia": f[2], "al_dia": f[2] == hoy},
                     # *Y la cobertura, cuando la hay.* **Va aparte y no dentro de `productos`**, porque
                     # `productos` sigue queriendo decir lo que decia.
                     **({"cobertura": cub} if (cub := _cobertura(f[0], f[2])) else {})}
                    for f in filas],
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
    # **Una lista de casa por persona, y la base lo impone** (`lista_de_casa_por_dueno`). La regla
    # es la correcta -- la lista de casa es el eje de la aplicacion: alimenta el contador del menu,
    # el puente de la compra y las alertas --, pero **la respuesta era mentira**: crear la segunda
    # salia como **500 «Internal Server Error»**, que manda a mirar los registros de la API por algo
    # que el usuario puede entender y resolver. Medido el 11 de octubre de 2026 contra la API viva:
    # `UniqueViolation: duplicate key value violates unique constraint "lista_de_casa_por_dueno"`.
    # Es la misma clase de defecto que el 422 de las lineas: **la restriccion hacia su trabajo y el
    # mensaje culpaba al servidor**.
    try:
        return almacen.crea_lista(usuario["id"], datos.nombre, datos.es_de_casa)
    except psycopg.errors.UniqueViolation as choque:
        raise HTTPException(
            409, "Ya tienes una lista de casa, y solo puede haber una. "
                 "Anade lo que quieras a esa, o cambia el nombre de esta.") from choque


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
    # **Lo autorizado se lee de la base, no del cuerpo de la peticion.** Es lo que hace que una
    # confirmacion sobreviva a recargar la pantalla, y lo que impide que el total cuente una
    # sustitucion que nadie ha confirmado.
    lineas = _con_autorizacion(lineas, lista_id)
    # **Las lineas que apuntan a otro producto no tienen precio, y hay que quitarselo aqui.**
    # Sin esto, la compra guardaba el precio del grupo al que apunta la linea -- que hoy puede
    # ser un pintalabios en una linea que dice «leche entera» -- y el total mentia. Es el mismo
    # filtro que hace `ver_lista` antes de pintar, y tiene que estar en los dos sitios: lo que
    # se guarda no puede ser menos honesto que lo que se enseña.
    movidas = catalogo.lineas_movidas(lineas)
    lineas = [_linea_movida(ln) if str(ln.get("id")) in movidas else ln for ln in lineas]
    en_el_carro = [ln for ln in lineas if ln.get("en_carrito")]
    if not en_el_carro:
        # DOS PESTANAS CERRANDO A LA VEZ: SE DISTINGUE DE UN CARRO VACIO.
        # Antes, la segunda pestana recibia 'no hay nada en el carro, marca lo que te llevas'
        # -- y eso es falso: SI habia algo, y otra pestana acaba de cerrarlo.
        # El conflicto se detectaba (409, y sin compra duplicada), pero el mensaje mandaba a
        # buscar un problema donde no estaba.
        # La compra que acaba de cerrarse esta en compras_de con su cerrada_en: si es de hace
        # menos de dos minutos, es eso y se dice.
        _recientes = almacen.compras_de(lista_id, limite=1)
        if _recientes:
            from datetime import datetime as _dt
            from datetime import timezone as _tz
        
            _cuando = _dt.fromisoformat(_recientes[0]['cerrada_en'])
            if (_dt.now(_tz.utc) - _cuando).total_seconds() < 120:
                raise HTTPException(
                    409,
                    'Otra pestana acaba de cerrar esta compra. Abre la lista otra vez para ver'
                    ' lo que quedo: no se ha perdido nada.',
                )
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


@app.get("/api/listas/{lista_id}/gasto")
def ver_gasto(lista_id: str, periodo: str = "mes", usuario: dict = Depends(usuario_actual)):
    """**Cuanto se ha pagado, y cuanto de eso no se sabe.**

    G05 lo pide en Compra: *«gasto pagado semanal/mensual a partir de compras guardadas e importes
    conocidos. Separar fechas de compra y de precios. **Cobertura de importes historicos `NULL`
    visible**»*.

    Se agrupa por **la fecha en que se cerro cada compra** -- *no por la del precio* -- y cada fila
    lleva su total **y su cobertura**: cuantas compras entraron y cuantas no tienen importe conocido.
    **Un periodo sin ninguna compra con total tiene `total_cent = None`, no `0`**: *no es que se
    gastara cero, es que no se sabe*. Y `completo` es `False` en cuanto una compra tenga lineas sin
    precio, aunque su total venga puesto.

    *La regla vive en `core/gasto.py`, que es puro y tiene sus pruebas; aqui solo se sirve.*
    """
    _acceso(lista_id, usuario)
    if periodo not in (gasto.MES, gasto.SEMANA):
        raise HTTPException(422, "El gasto se agrupa por `mes` o por `semana`.")
    # Un limite generoso: el gasto mira el historico entero, no las ultimas doce.
    compras = almacen.compras_de(lista_id, limite=1000)
    return {
        "periodo": periodo,
        "filas": gasto.gasto_de_compras(compras, periodo),
        "compras": len(compras),
        "fecha_datos": catalogo.fecha_de_gold(),
    }


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
    # **Lo autorizado se lee de la base, no del cuerpo de la peticion.** Es lo que hace que una
    # confirmacion sobreviva a recargar la pantalla, y lo que impide que el total cuente una
    # sustitucion que nadie ha confirmado.
    lineas = _con_autorizacion(lineas, lista_id)
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
    # **Un nombre en blanco se corta aqui, con 422.** La restriccion de la base
    # (`linea_con_nombre`) tambien lo rechaza, pero dejarlo llegar al INSERT sale como **500** «el
    # servidor ha fallado», que es mentira y manda a mirar los registros. Es la misma comprobacion
    # que habia antes con el destino, puesta donde ahora hace falta.
    if not linea.nombre.strip():
        raise HTTPException(422, "Una linea necesita un nombre: es lo unico que se puede leer de ella.")
    # **Aqui se exigia grupo o producto, y ya no.** La comprobacion existia porque la base tenia
    # `linea_con_destino`: sin ella, una linea sin destino llegaba al INSERT y salia como **500**
    # «el servidor ha fallado», que es mentira y manda a mirar los registros. Tenia razon en lo que
    # protegia -- una linea sin destino no se puede comparar con nada --, pero **convertia en
    # imposible apuntar «papel de cocina» o «lo que sea del mercado»**, que es la mitad de una lista
    # de la compra. La migracion 014 cambia la restriccion por **una que exige el nombre**:
    # *la linea existe, se lee y se identifica despues*. Lo que ya no se exige es el destino **al
    # apuntarla**. Y lo que NO cambia: mientras no lo tenga se presenta como **«Pendiente de
    # identificar»**, **no entra en ninguna comparacion** y **no se le inventa precio ni
    # equivalencia** -- sus importes se quedan NULL, que es la verdad.
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
    # **Se admite cualquier cadena CAPTURADA, no solo las comparables.** *Y esto es un cambio del 13 de
    # octubre de 2026, con su motivo.*
    #
    # *Antes la puerta era `cesta.CADENAS` -- las cinco comparables --, asi que **`lidl` se rechazaba con un
    # 422**: no se podia decir «esta linea la compro en Lidl» **ni aunque su precio estuviera capturado y
    # fuera valido**.*
    #
    # **Y eso era el veto global que B03 pide quitar**, pero **quitarlo no es anadir `lidl` a `CADENAS`**:
    # *esa lista significa «puede cerrar una cesta», y Lidl **no puede**, porque publica ofertas semanales
    # parciales.* **Son dos preguntas distintas y hay dos listas para ellas:**
    #
    #   - **`CADENAS_QUE_SE_CAPTURAN`**: de las que hay dato. *Aqui si entra Lidl.*
    #   - **`CADENAS`**: de las que se puede **cerrar una cesta**. *Aqui no, y con su motivo dicho.*
    #
    # *Asi que la puerta es la primera, y la segunda decide **quien gana una cesta*** -- *que es la regla
    # fina que el plan pide: **«Lidl no gana una cesta completa si faltan lineas; si puede ofrecer una linea
    # exacta con precio valido»**.*
    if datos.cadena is not None and datos.cadena not in cesta.CADENAS_QUE_SE_CAPTURAN:
        raise HTTPException(422, f"'{datos.cadena}' no es una de las cadenas capturadas: "
                                 f"{', '.join(cesta.CADENAS_QUE_SE_CAPTURAN)}")
    # **Y si la cadena no puede cerrar una cesta, se dice al elegirla** -- *no se calla.* *Es el mismo
    # patron de siempre: la pantalla tiene que poder explicar por que faltara esa tienda en el reparto, en
    # vez de que aparezca ausente sin motivo.*
    aviso = cesta.por_que_no_se_compara(datos.cadena) if datos.cadena else None
    if datos.borrar:
        if datos.cadena is None:
            raise HTTPException(422, "Para borrar una sublista hace falta decir de que tienda.")
        cuantas = almacen.borra_lineas_de_tienda(lista_id, datos.cadena, usuario["id"])
        return {"borradas": cuantas, "cadena": datos.cadena, "aviso": aviso}
    if datos.lineas:
        cuantas = almacen.pon_tienda(lista_id, datos.cadena, usuario["id"], datos.lineas)
        return {"puestas": cuantas, "cadena": datos.cadena, "aviso": aviso}
    # Sin `lineas`: toda la lista, que es el boton de «todo en DIA».
    todas = [x["id"] for x in almacen.lineas_de(lista_id) if x["tachado_en"] is None]
    return {"puestas": almacen.pon_tienda(lista_id, datos.cadena, usuario["id"], todas),
            "cadena": datos.cadena, "aviso": aviso}


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
    # **Idempotente: lo que ya esta en la lista no se vuelve a poner.** Pulsar dos veces el
    # mismo favorito no puede dejar dos lineas, y la respuesta dice que ha hecho -- `anadidos` y
    # `ya_estaban` --, que es la mitad de una vista previa: la otra mitad es decirlo antes.
    ya_en_la_lista = {(x.get("grupo_id"), x.get("producto_id"))
                     for x in almacen.lineas_de(lista_id)}
    puestos = 0
    ya_estaban = 0
    for grupo_id in datos.grupo_ids:
        if (grupo_id, None) in ya_en_la_lista:
            ya_estaban += 1
            continue
        # El nombre que se guarda en la linea es **el del producto**, no el numero
        # del grupo: `nombre_visto` se pinta tal cual en la lista y "Favorito 4821"
        # no le sirve a nadie de pie en el supermercado. Si el grupo ya no esta en
        # gold (lo rehizo el emparejador), se guarda lo que se sepa y la linea sigue
        # siendo valida: el grupo es la referencia, el nombre es una comodidad.
        g = catalogo.grupo(grupo_id) or {}
        nombre = g.get("nombre") or f"Producto {grupo_id}"
        # **Y el miembro que se enseno**, no solo el grupo. La ficha muestra el mas barato por
        # unidad y el motor compara contra el de identificador mas bajo: son productos distintos
        # en cuanto los precios no acompanan. Guardar el mostrado es lo que hace que la referencia
        # sea **lo que se pidio**, y el motor ya lo honra desde la ronda 77.
        mostrado = (g.get("productos") or [{}])[0]
        producto_id = (f"{mostrado['fuente']}:{mostrado['id_fuente']}"
                       if mostrado.get("fuente") and mostrado.get("id_fuente") else None)
        almacen.anade_linea(lista_id, usuario["id"], str(uuid.uuid4()),
                            nombre, grupo_id, producto_id, 1, None)
        puestos += 1
    for producto_id in datos.producto_ids:
        # **El orden de la tupla, que estaba CAMBIADO.** *Arriba se construye
        # `(grupo_id, producto_id)`, asi que una linea con **producto y sin grupo** guarda
        # `(None, producto_id)`. *Y aqui se buscaba `(producto_id, None)`, que **no coincide con nada**.*
        #
        # *O sea: la comprobacion de «ya esta» **no encontraba nunca un producto**, y el mismo producto
        # se podia anadir dos veces -- *justo lo que el comentario de arriba promete que no pasa*:
        # **«pulsar dos veces el mismo favorito no puede dejar dos lineas».** *
        if (None, producto_id) in ya_en_la_lista:
            ya_estaban += 1
            continue
        p = catalogo.producto(producto_id) or {}
        almacen.anade_linea(lista_id, usuario["id"], str(uuid.uuid4()),
                            p.get("nombre") or producto_id, None, producto_id, 1, None)
        puestos += 1
    return {"anadidos": puestos, "ya_estaban": ya_estaban}


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
    # **Lo autorizado se lee de la base, no del cuerpo de la peticion.** Es lo que hace que una
    # confirmacion sobreviva a recargar la pantalla, y lo que impide que el total cuente una
    # sustitucion que nadie ha confirmado.
    lineas = _con_autorizacion(lineas, lista_id)
    # Las que apuntan a otro producto no se reparten: se estaria decidiendo la tienda
    # de un producto que no es el que dice la linea. Se quedan fuera del reparto y la
    # pantalla las señala en la lista (`producto_movido`).
    movidas = catalogo.lineas_movidas(lineas)
    lineas = [x for x in lineas if str(x["id"]) not in movidas]
    # **Y lo que la linea dice que se confirmo, que aqui se perdia.** `estimacion` y
    # `coste_por_linea` ya lo pasan -- esta escrito alli desde el trabajo de coste -- y este sitio
    # no: asi que la sustitucion aceptada no llegaba al reparto, que es **la pantalla donde se
    # acepta**. Medido el 13 de octubre de 2026: el POST devolvia `autorizado: true` y el reparto
    # seguia diciendo `false`.
    peticiones = [cesta.Peticion(x["grupo_id"], x["producto_id"], x["cantidad"],
                                 x["nombre_visto"], x["id"],
                                 autorizado=bool(x.get("autorizado")),
                                 autorizado_producto=x.get("autorizado_producto"),
                                 autorizado_cadena=x.get("autorizado_cadena")) for x in lineas]
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
    # **Lo autorizado se lee de la base, no del cuerpo de la peticion.** Es lo que hace que una
    # confirmacion sobreviva a recargar la pantalla, y lo que impide que el total cuente una
    # sustitucion que nadie ha confirmado.


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
    # **Lo autorizado se lee de la base, no del cuerpo de la peticion.** Es lo que hace que una
    # confirmacion sobreviva a recargar la pantalla, y lo que impide que el total cuente una
    # sustitucion que nadie ha confirmado.
    lineas = _con_autorizacion(lineas, lista_id)
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


def _vigencia(fecha_precio: str, publicado_en: str) -> dict:
    """Si la fecha del precio **pertenece** a esa publicacion. Pura: se prueba con texto.

    Compara solo el **dia**: el catalogo se publica a una hora, y los precios son de dias. Un precio del mismo
    dia que la publicacion es coherente; uno posterior, no.
    """
    if not fecha_precio or not publicado_en:
        return {"comprobable": False, "motivo": "falta la fecha del precio o la de publicacion"}
    dia_publicacion = publicado_en[:10]
    coherente = fecha_precio <= dia_publicacion
    return {
        "comprobable": True,
        "coherente": coherente,
        "fecha_datos": fecha_precio,
        "publicado_en": dia_publicacion,
        "motivo": ("la fecha del precio pertenece a esta publicacion" if coherente
                   else "el precio es POSTERIOR a la publicacion del catalogo: o el puntero esta viejo, o "
                        "gold se escribio por detras"),
    }


def _vigencia_del_catalogo() -> dict:
    """Los valores de verdad: el dia de los precios y el momento de la publicacion.

    Se lee el puntero a mano, como `_version_del_catalogo`, por la misma razon: importar `core.publicacion`
    arrastraria polars, y la imagen de la API no lo lleva.
    """
    try:
        puntero = json.loads((AJUSTES.gold / "actual.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"comprobable": False, "motivo": "no hay catalogo publicado"}
    dicho = _vigencia(catalogo.fecha_de_gold(), str(puntero.get("publicado_en") or ""))
    # **Y una cosa mas, que es barata y evita una conclusion falsa.** *Que las fechas cuadren **no
    # prueba** que el contenido sea el que se publico.* El 12 de octubre de 2026 se midio una version
    # llamada `20261007-103000` cuyo `precio_diario.parquet` era del 11 -- *y las fechas lo delataron,
    # pero solo porque el dia del precio iba por delante. Al reves no se habria notado.*
    #
    # *Por eso se dice **si el puntero trae huellas**, que es lo que permite comprobarlo de verdad.*
    # **No se calculan aqui**: son 30 MB y esto se pide en cada pantalla. *La comprobacion profunda
    # tiene su propia ruta* (`/api/estado/publicacion`).
    dicho["huellas_en_el_puntero"] = len(puntero.get("huellas") or {})
    return dicho


def _comprueba_publicacion() -> dict:
    """**El contenido, byte a byte, contra lo que el puntero dice que se publico.**

    Es la comprobacion que `/api/estado` **no** puede hacer sin arruinar cada carga: *leer y resumir los
    seis parquet son ~30 MB.* Aqui vive aparte, para que la pida quien de verdad necesita saberlo.

    **Y usa `hashlib`, no `core.publicacion`**, por la razon de siempre: *la imagen de la API no lleva
    polars.* *Lo unico que se necesita es resumir ficheros, y eso es de la biblioteca estandar.*

    Devuelve, por fichero, uno de cuatro estados -- *y **`sin_huella` no es `bien`***: es «no se puede
    saber», que es distinto y hay que decirlo.
    """
    carpeta = AJUSTES.gold
    try:
        puntero = json.loads((carpeta / "actual.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"comprobable": False, "motivo": "no hay catalogo publicado"}
    version = str(puntero.get("version") or "")
    guardadas = dict(puntero.get("huellas") or {})
    declarados = list(puntero.get("ficheros") or [])
    if not version or not declarados:
        return {"comprobable": False, "motivo": "el puntero no dice que version ni que ficheros"}

    estado: dict[str, str] = {}
    for nombre in declarados:
        camino = carpeta / f"v{version}" / nombre
        if not camino.exists():
            estado[nombre] = "ausente"
            continue
        esperada = guardadas.get(nombre)
        if not esperada:
            estado[nombre] = "sin_huella"       # *no se puede saber, y no es lo mismo que estar bien*
            continue
        resumen = hashlib.sha256()
        with camino.open("rb") as f:
            for trozo in iter(lambda: f.read(1 << 20), b""):
                resumen.update(trozo)
        estado[nombre] = "bien" if resumen.hexdigest() == esperada else "cambiado"

    malos = sorted(n for n, e in estado.items() if e in ("cambiado", "ausente"))
    return {
        "comprobable": True,
        "version": version,
        "publicado_en": str(puntero.get("publicado_en") or ""),
        "por_fichero": estado,
        # *Y el veredicto en una palabra, para que nadie tenga que interpretar el diccionario.*
        # **`None` cuando no se puede saber** -- *ni bien ni mal.*
        "coherente": None if any(e == "sin_huella" for e in estado.values()) else not malos,
        "no_cuadran": malos,
    }


@app.get("/api/estado/publicacion")
def estado_publicacion() -> dict:
    """Si el catalogo servido es **de verdad** el que se publico. *Lee ~30 MB: no es para cada carga.*"""
    return _comprueba_publicacion()



# ------------------------------------------------------------- autorizar una sustitucion ---

@app.post("/api/listas/{lista_id}/lineas/{linea_id}/autorizar")
def autorizar_linea(lista_id: str, linea_id: str, autorizado: bool = Query(default=True),
                    producto: str | None = Query(default=None),
                    cadena: str | None = Query(default=None),
                    usuario: dict = Depends(usuario_actual)) -> dict:
    """Confirmar (o retirar) la sustitucion propuesta para **una** linea de la lista.

    **Por que existe.** La alternativa la propone el motor, y hasta ahora la confirmacion viajaba en el cuerpo
    de la peticion: al recargar se perdia y habia que volver a decidir. Una decision que hay que tomar dos
    veces es una decision que el sistema no se cree.

    **Por que `hace_falta_escribir=True`.** Autorizar cambia la lista para todos los que la comparten, asi que
    no basta con poder mirarla: se pide la misma puerta que para cualquier escritura, con su papel.

    **Por que se guarda por linea y no por peticion.** La decision es sobre **ese producto en esa lista**.
    Guardarla en la peticion la ata a la pantalla; por lista, al dia entero. La linea es lo unico que no cambia
    de significado.

    **Y se guarda QUE alternativa se acepto**: el producto y la cadena que llegan en la peticion. Antes
    solo se guardaba el si, y el motor podia proponer otro producto manana manteniendo la autorizacion.
    """
    _acceso(lista_id, usuario, hace_falta_escribir=True)
    try:
        tocada = almacen.autoriza_linea(lista_id, linea_id, usuario["id"], autorizado,
            producto=producto, cadena=cadena)
    except ValueError as fallo:
        raise HTTPException(status_code=400, detail=str(fallo)) from fallo
    if tocada is None:
        # 404 y no 403: una linea que no existe y una de otra lista se contestan **igual**, para no decir
        # cuales existen. Es la regla de siempre.
        raise HTTPException(status_code=404, detail="esa linea no esta en esa lista")
    return {"linea_id": tocada, "autorizado": autorizado}


def _con_autorizacion(lineas: list[dict], lista_id: str) -> list[dict]:
    """Las lineas, cada una con **lo que se confirmo** para ella.

    Un solo sitio para esto, usado por todos los que calculan precios. Antes eran cinco copias del
    mismo cruce, y una copia que se queda atras es exactamente el fallo que tuvo `mejor`: dos
    lectores que dejaron de coincidir con lo que leian.

    Las lineas historicas no aparecen autorizadas: la columna nace en falso y **no consta** que
    nadie autorizara nada, que es distinto de que se rechazara.
    """
    confirmado = almacen.autorizacion_de(lista_id)
    salida = []
    for linea in lineas:
        suyo = confirmado.get(str(linea.get("id"))) or {}
        salida.append({**linea,
                        "autorizado": bool(suyo.get("autorizado")),
                        "autorizado_producto": suyo.get("producto"),
                        "autorizado_cadena": suyo.get("cadena")})
    return salida


# ------------------------------------------------------------- el puente del plan ---

def _ruta_recetas():
    """Donde vive el recetario. Se pregunta al modulo de recetas, no se adivina la ruta."""
    from .recetas import ruta_base as _ruta

    return _ruta()


@app.get("/api/listas/{lista_id}/desde-el-plan")
def previa_del_plan(lista_id: str, desde: str = Query(...), hasta: str = Query(...),
                    usuario: dict = Depends(usuario_actual),
                    # **Y va DESPUES de `usuario`, no antes.** *Ponerlo delante desplaza el cuarto
                    # argumento posicional, y las pruebas que llaman a esta funcion a mano -- sin pasar
                    # por FastAPI -- empezaron a fallar con `'Depends' object is not subscriptable`.*
                    # **Un parametro nuevo no puede mover los que ya habia.** *Lo dijo la suite.*
                    descontar_despensa: bool = Query(False)) -> dict:
    """**La vista previa**: que ingredientes del plan entrarian en la lista, sin tocar la lista.

    Cada ingrediente viene de **la version que el plan guardo**, no de la ultima: si la receta cambio
    despues, el plan sigue diciendo lo que se planifico, y la lista tiene que recibir eso.

    Los que **ya estan** se dicen aparte, con su nombre. Es lo que hace falta para que pulsar dos veces
    no duplique: el puente tiene que ser idempotente, y para eso hay que saber que hay puesto.
    """
    _acceso(lista_id, usuario, hace_falta_escribir=False)
    # **Y el tercer valor, la `Previa` entera.** *`sin_cantidad` y `sin_consolidar` son informacion que
    # antes se tiraba, y que el criterio de B04 pide*: *un ingrediente sin cantidad no se puede comprar, y
    # el mismo producto en unidades incompatibles no se puede sumar.* **Decirlo es la regla de la casa.**
    planificadas, ya_en_la_lista, calculada = _del_plan(lista_id, usuario["id"], desde, hasta)
    # **Lo que entra, y lo que entra PENDIENTE.** *Un ingrediente sin producto y sin grupo **si puede
    # entrar**: se apunta con su nombre y queda **«pendiente de identificar»**, y esta previa lo dice en
    # `sin_destino` en vez de esconderlo.*
    #
    # *Antes esta previa lo filtraba, «porque la tabla lo prohibe (`linea_con_destino`)» -- y **eso dejo
    # de ser cierto** cuando la migracion `014_la_linea_sin_destino.sql` quito la restriccion. *Prometer
    # de menos es mentir igual que prometer de mas: **el POST apuntaba la linea y la previa decia 0.***
    #
    # *Y ahora son `LineaDeCompra`, no diccionarios*: `ln.texto`, `ln.producto_id`, `ln.grupo_id`.
    # **Lo que hay en casa, por nombre.** *Se lee la despensa de quien pregunta y solo la suya.*
    # *La comparacion es por texto en minusculas*, que es lo que la despensa guarda: **no se empareja por
    # identidad de producto, y se dice** -- *un `grupo_id` no esta en esa tabla.*
    # **Y si la despensa no se puede leer, se dice «no se sabe» y NO «no lo tienes».** *La diferencia
    # importa y es la regla de toda esta fase*: `False` afirmaria que no esta, **y no haber podido
    # preguntar no es lo mismo que saber que no hay.** *Por eso el marcador es `None` cuando no se pudo
    # leer* -- y `descontar_despensa` tampoco descuenta nada, porque no hay nada de lo que fiarse.
    #
    # *Y esto no es una precaucion teorica*: al anadirlo se cayeron SIETE pruebas que llaman a la previa
    # con mocks, sin base de datos. *El fallo fue mio y lo dijo la suite* -- **que es para lo que esta.**
    en_casa: set[str] | None
    try:
        with almacen.cursor() as cur:
            cur.execute("SELECT texto FROM despensa WHERE usuario_id = %s", (usuario["id"],))
            en_casa = {str(f["texto"]).strip().lower() for f in cur.fetchall() if f["texto"]}
    except Exception:  # noqa: BLE001  <- a proposito: *sin base no se puede saber, y se dice.*
        en_casa = None

    # *Y se marca cada ingrediente, haya o no descuento*: **saber que lo tienes es la mitad del valor, y
    # la persona puede querer comprarlo igual** -- *porque lo que hay en la despensa no consta que siga
    # habiendo: se compro, y puede haberse acabado.*
    # *`None` cuando no se pudo leer*, y `True`/`False` solo cuando se pudo.
    for ln in planificadas:
        ln.en_la_despensa = (  # type: ignore[attr-defined]
            None if en_casa is None else ln.texto.strip().lower() in en_casa)

    pueden = [ln for ln in planificadas
              if not _ya_estaba(ya_en_la_lista, (ln.grupo_id, ln.producto_id), ln.texto)
              # **Y el filtro del destino YA NO VA AQUI.** *Exigia producto o grupo «porque la tabla lo
              # prohibe (`linea_con_destino`)», y **la tabla ya no lo prohibe**: *la migracion
              # `014_la_linea_sin_destino.sql` quito la restriccion, y su motivo es justo este caso --
              # *«quien no encontraba el producto en el catalogo **no podia apuntarlo, y acababa
              # apuntandolo en otro sitio»*.*
              #
              # *Asi que una linea sin destino **entra**, y **se dice que va pendiente**: `sin_destino`
              # la nombra -- para que la pantalla la enseñe como **«Pendiente de identificar»** y
              # **los totales la dejen fuera**, que es distinto de contarla como cero.*
              # **Y aqui esta «la persona lo elige»**: con el parametro en falso -- que es por defecto --
              # *esto no quita nada.*
              and not (descontar_despensa and getattr(ln, "en_la_despensa", False))]
    sin_destino = sorted(ln.texto for ln in planificadas
                         if not _ya_estaba(ya_en_la_lista, (ln.grupo_id, ln.producto_id), ln.texto)
                         and ln.producto_id is None and ln.grupo_id is None)
    # **El adaptador: `LineaDeCompra` por dentro, y la MISMA forma de JSON que antes por fuera.**
    #
    # *Esto no es un detalle de estilo*: la interfaz lee `nombre`, `cantidad` y `unidad` -- *medido en
    # `Grupo.tsx` y en las pantallas del plan* --, y **un refactor interno que cambie lo que ve la
    # interfaz sin decirlo es una rotura de contrato disfrazada de mejora.**
    #
    # *Asi que la forma de fuera se mantiene, y se le ANADE lo que ahora se sabe*: **los envases**, **el
    # sobrante** y **de que recetas viene**. *Lo que la interfaz no lea hoy lo puede leer mañana, y
    # mientras no estorba.*
    def _como_antes(ln) -> dict:
        return {"nombre": ln.texto, "cantidad": ln.cantidad, "unidad": ln.unidad,
                "producto_id": ln.producto_id, "grupo_id": ln.grupo_id,
                "clave": ln.clave, "recetas": list(ln.recetas),
                # *Y `receta`, en singular, que es lo que leia la previa de antes*: **el primer
                # nombre.** *Se mantiene por compatibilidad, y porque una linea que viene de una
                # sola receta se lee mejor asi.*
                "receta": (ln.recetas[0] if ln.recetas else None),
                # *Y los envases y el sobrante, que antes no existian en la previa del plan.*
                "envases": ln.envases, "sobrante": ln.sobrante,
                "en_la_despensa": getattr(ln, "en_la_despensa", None),
                "unidad_envase": ln.unidad_envase}

    pueden = [_como_antes(ln) for ln in pueden]
    sin_destino = list(sin_destino)
    return {"entrarian": pueden, "ya_estaban": sorted(
        ln.texto for ln in planificadas
        if _ya_estaba(ya_en_la_lista, (ln.grupo_id, ln.producto_id), ln.texto)),
        # **Y lo que no se puede comprar, dicho por su nombre.** *Un ingrediente sin cantidad no se
        # compra, y el mismo producto en unidades incompatibles no se suma: las dos cosas salen de
        # `previa_compra` y las dos se dicen, en vez de desaparecer.*
        "sin_cantidad": list(calculada.sin_cantidad),
        "sin_consolidar": list(calculada.sin_consolidar),
        # **Y lo que no se puede, se dice.** Es la regla de la casa: un cero callado no; una lista
        # de lo que falta, si.
        "sin_catalogo": sin_destino,
        "total": len(pueden), "desde": desde, "hasta": hasta}


def _del_plan(lista_id: str, propietario: str, desde: str, hasta: str) -> tuple[list[dict], set[str]]:
    """Los ingredientes que el plan pide en esas fechas, y los nombres que ya estan en la lista.

    **Un solo sitio para el calculo.** La vista previa y la accion que escriba tienen que decir lo mismo,
    y la unica forma de garantizarlo es que sea el mismo codigo: separarlos es como se acaba con una previa
    que miente.

    **Y dos cosas que este calculo hacia mal, medidas el 13 de octubre de 2026** con
    `scripts/auditar_puente_plan_20261013.py`:

      1. **NO ESCALABA POR COMENSALES.** *El plan guarda para cuantas personas se cocina y la receta
         declara para cuantas raciones esta escrita, y la cantidad se usaba tal cual.* **Medido**: *dos
         recetas de 100 g con `raciones: 2`, una planificada para **4 comensales** y otra para 2, daban
         **100 y 100** -- cuando lo que hay que comprar son **200 y 100: 300 g**.*
      2. **NO CONSOLIDABA: DESCARTABA.** *Dos recetas con el mismo ingrediente tienen que dejar **una**
         linea, y eso es correcto* -- **pero la segunda contribucion se tiraba en vez de sumarse.**
         *Medido*: **una sola linea con nota «100 g», y los otros 100 g perdidos.**

    **Lo que se suma es lo que se va a comprar, y por eso se consolida por `(nombre, unidad)`**: *la misma
    harina en gramos y en kilos son dos cosas distintas y sumarlas daria un numero que no es de nadie.*
    """
    from core import recetas as _recetas

    # **La identidad, no el nombre.** *Antes esto era `{nombre_visto.lower()}`, y comparar por texto hace
    # que **dos marcas distintas con el mismo nombre se pisen** -- *y que una linea ya puesta se vuelva a
    # prometer.* *Lo que identifica una linea de la lista es **su destino**: `(grupo_id, producto_id)`,
    # que es lo que la tabla guarda y lo que el motor usa.*
    #
    # *Y queda dicho lo que **no** se puede comprobar hoy*: *la lista **no guarda la unidad** de la linea,
    # asi que la identidad es el destino y no `(destino, unidad)` -- *que es lo que el docstring de arriba
    # pide para **consolidar**, y que `previa_compra` si cumple por dentro con su `clave`.*
    # *** Y `ya` SOLO cuenta lo de ESTA operacion. *** *
    #
    # *Antes eran **todas las lineas de la lista**, *y con eso **el tomate de la semana pasada**
    # impedia que entrara **el de esta** *-- *en vez de sumarse.* *Y **dentro de una operacion**
    # se sigue consolidando por identidad, *que es lo que pide el encargo: *dos recetas con el mismo
    # ingrediente dejan **una** linea.* *
    #
    # *Y **la operacion es la semana** *(-- `desde|hasta` --)*, *que es la misma que lleva el `id`
    # de la linea: *asi **el mismo id** y **el mismo `ya`** cuentan **lo mismo.*** *
    #
    # *** Y `NULL` TAMBIEN CUENTA. *** *Una linea **puesta a mano** no viene de ninguna operacion, *
    # *y **esta ahi**: *saltarla haria que **el puente la duplicara** *-- *y eso **no es acumular**,
    # *es repetir lo que ya hay.* *Lo cazo `test_lo_que_ya_esta_se_dice_aparte_y_no_entra`, *
    # *que la pone **directamente**, *sin operacion* *-- *y **tenia razon.*** *
    esta_operacion = f"{desde}|{hasta}"
    ya = {((x.get("grupo_id"), x.get("producto_id")),
           str(x.get("nombre_visto") or "").strip().lower())
          for x in almacen.lineas_de(lista_id)
          if x.get("operacion") in (None, esta_operacion)}
    recetario = _recetas.conecta(_ruta_recetas())
    # **Los ingredientes de TODO el plan, escalados y con su receta.** *Se juntan primero y se consolidan
    # despues, que es el unico orden en el que dos recetas con el mismo ingrediente suman.*
    todos: list[dict] = []
    try:
        plan = _recetas.plan(recetario, propietario, desde, hasta)
        for linea in plan:
            receta = _recetas.leer(recetario, propietario, linea["receta_id"],
                                   version=linea.get("version"))
            if receta is None:
                continue
            # **El factor de escalado.** *Si la receta no declara raciones, no se inventa: se deja la
            # cantidad como esta* -- *porque multiplicar por un numero que no consta seria peor que no
            # escalar, y **no escalar se ve**, mientras que un factor inventado no.*
            raciones = receta.get("raciones")
            comensales = linea.get("comensales")
            factor = None
            if raciones and comensales and float(raciones) > 0:
                factor = float(comensales) / float(raciones)
            for uno in receta["ingredientes"]:
                suyo = dict(uno)
                if suyo.get("cantidad") is not None and factor is not None:
                    suyo["cantidad"] = suyo["cantidad"] * factor
                # *La receta, para que la nota pueda decir de donde viene cada aportacion.*
                suyo["_receta"] = receta["nombre"]
                # *** Y EL TAMANO DEL ENVASE, QUE FALTABA AQUI. *** *
                #
                # **Y era el fallo entero, medido**: *un plan con **3.800 g** de un articulo cuyo envase
                # son **1.000 g** acababa en la lista con *** `cantidad = 1` *** y los 3.800 g **solo en la
                # nota** -- *que es exactamente lo que denuncio el propietario.* *
                #
                # *La causa no era el calculo*: *`previa_compra` **cuenta los envases enteros** y
                # `envases_enteros` **tiene la regla con su ejemplo** («1,4 kg con envases de 1 kg son dos
                # envases y 0,6 kg sobrantes»). *La causa era que **a `previa_compra` le llegaban los
                # ingredientes sin `tamano_envase`**: *lo pone `recetas._con_precios` -- *que es de la API
                # de recetas* --, *y **este camino no pasa por ahi.** *
                #
                # *Y por eso salia `envases=None`, y por eso la linea quedaba en `1`: *sin tamaño no se
                # puede saber cuantos envases hacen falta, *y **el `1` afirmaba una unidad que nadie habia
                # calculado.*** *
                #
                # **El dato sale de donde tiene que salir**: *de **la ficha del articulo elegido**, que es
                # quien lo publica -- *igual que en `recetas._con_precios`.* *Y si el ingrediente **no tiene
                # articulo**, no se inventa nada: *se queda sin tamaño, *`envases` sale `None`, *y **la nota
                # lo dice.** *
                ficha = (catalogo.producto(str(suyo["producto_id"]))
                         if suyo.get("producto_id") else None)
                if ficha:
                    suyo["tamano_envase"] = ficha.get("cantidad")
                    suyo["unidad_envase"] = ficha.get("unidad")
                todos.append(suyo)
    finally:
        recetario.close()

    # **Y AQUI ESTA LA CONSOLIDACION, QUE ES LA MISMA QUE LA DEL OTRO PUENTE.** *`traspaso` la llama para
    # receta->lista; esto la llama para plan->lista.* **Un solo sitio para el calculo, que es lo que el
    # docstring de arriba pedia desde el principio y no cumplia.**
    #
    # *Antes habia dos implementaciones, y por eso mentian las dos a la vez y cada una a su manera*: *aqui
    # no se escalaba y se descartaba la segunda receta; alli se contaban los gramos como unidades.*
    #
    # **Y no se pierde nada por el camino**: `previa_compra` agrupa por `clave` -- *producto + unidad* --,
    # **cuenta los envases enteros**, **calcula el sobrante** y **recoge de que recetas viene**.
    from core import previa_compra as _previa

    calculada = _previa.previa_de_compra(todos)
    return list(calculada.lineas), ya, calculada



def _ya_estaba(ya: set, destino: tuple, nombre: str | None) -> bool:
    """**Si esa linea ya esta en la lista** -- y con que se compara, que es lo que importaba.

    *Comparar **solo por nombre** era el defecto*: **dos marcas distintas con el mismo texto se pisaban**,
    *y una linea ya puesta **se volvia a prometer**. *Asi que la identidad es **el destino** -- `(grupo_id,
    producto_id)`, que es lo que la tabla guarda y lo que el motor usa.*

    **Pero una linea PENDIENTE no tiene destino** -- *es «pendiente de identificar», y ese es su estado* --
    *y con ella **el nombre es lo unico que queda**.* *Negar que esta seria **prometer una linea que el
    usuario ya ve en su lista**, asi que **con una pendiente si se compara por nombre**.*

    *Y lo que **no** se hace, que es la mitad que importa:* **entre dos lineas CON destino no se mira el
    nombre.** *Dos marcas distintas con el mismo texto **son dos compras distintas**, y fundirlas era
    exactamente el fallo que esto arregla.*
    """
    mio = str(nombre or "").strip().lower()
    for otro_destino, otro_nombre in ya:
        if destino != (None, None) and otro_destino == destino:
            return True
        # *El nombre, **solo si alguno de los dos es una pendiente sin destino**.*
        if (destino == (None, None) or otro_destino == (None, None)) and otro_nombre == mio:
            return True
    return False


@app.post("/api/listas/{lista_id}/desde-el-plan", status_code=201)
def traer_del_plan(lista_id: str, desde: str = Query(...), hasta: str = Query(...),
                   usuario: dict = Depends(usuario_actual)) -> dict:
    """**La accion**: mete en la lista lo que la vista previa dijo que entraria.

    Comparte el calculo con la previa a proposito: si fueran dos codigos, uno de los dos mentiria.

    **La cantidad del campo `cantidad` son LOS ENVASES, no los gramos ni una unidad fija.** La lista
    cuenta envases de un producto y la receta habla en gramos: poner `400` diria «400 envases». *Y por eso
    la respuesta no es `400` **ni `1`**: es **el numero de envases que la previa ya calcula** -- *«cuenta
    los envases enteros»* --, *asi que 1,4 kg de un producto en envase de 1 kg guardan **dos**.*
    *Y los gramos, el sobrante y de que recetas viene van a la nota, que es donde se leen.*

    *Y cuando el tamano del envase no se conoce, la cantidad se queda en `1` -- la columna es
    `NOT NULL` --, **pero la nota lo dice**, para que ese `1` no se lea como «un envase basta».*
    """
    _acceso(lista_id, usuario, hace_falta_escribir=True)
    planificadas, ya, _calculada = _del_plan(lista_id, usuario["id"], desde, hasta)
    # *** Y la operacion, *que es la misma que usa `_del_plan` para su `ya` y para el id. *** *
    #
    # *Va **aqui y no dentro de `_del_plan`** porque es **esta funcion** la que **escribe**: *
    # *`_del_plan` **calcula** y devuelve el `ya` que le corresponde, *y **la ruta lo usa para
    # decidir y para escribir.** *Y la cadena tiene que ser *** la misma *** en los dos sitios, *
    # o **el `ya` contaria una operacion y el id guardaria otra.** *
    esta_operacion = f"{desde}|{hasta}"
    anadidos = 0
    ya_estaban: list[str] = []
    sin_destino: list[str] = []
    for uno in planificadas:
        nombre = uno.texto
        # **Y la identidad, no el nombre.** *`ya` son los **destinos** que ya estan en la lista, asi que
        # comparar por texto haria que **dos marcas con el mismo nombre se pisen** -- *y que una linea ya
        # puesta **se vuelva a prometer**, que es lo que el complemento del 14/10 senala.*
        if _ya_estaba(ya, (uno.grupo_id, uno.producto_id), nombre):
            ya_estaban.append(nombre)
            continue
        # **Lo que no tiene destino SE APUNTA IGUAL, como «pendiente de identificar».** *Antes esta linea
        # hacia `continue` -- y su motivo era cierto cuando se escribio: `linea_con_destino` obligaba a
        # grupo o producto y **la base lo rechazaba con un 500**. Pero **ese suelo cambio**: la migracion
        # `014_la_linea_sin_destino.sql` quito la restriccion, y dice por que -- *«la restriccion
        # protegia la comparacion y **prohibia la lista**: quien no encontraba el producto en el catalogo
        # **no podia apuntarlo, y acababa apuntandolo en otro sitio**»*.*
        #
        # *Y lo que la sustituye es lo que este puente tiene que hacer: la linea **existe y se lee** -- se
        # presenta como **«Pendiente de identificar»**, no como un producto --, **no entra en ninguna
        # comparacion de precios ni de nutricion**, *y **no se le inventa precio ni equivalencia**:
        # `precio_cent` e `importe_cent` se quedan NULL, que es la verdad. *Y **los totales la dejan
        # fuera**, que es distinto de contarla como cero.*
        pendiente = uno.producto_id is None and uno.grupo_id is None
        if pendiente:
            sin_destino.append(nombre)
        # **La nota dice TODAS las recetas que aportan**, y el total ya sumado. *Antes decía solo la
        # primera* -- *«del plan: Receta 1 (100 g)» -- **y los otros 100 g no aparecian por ningun
        # lado**, asi que la nota no solo callaba una receta: callaba la mitad de lo que hay que
        # comprar.*
        #
        # *Y la cantidad que se escribe es **la suma**, no la de la primera: es la respuesta a «cuanto
        # hay que comprar», que es la unica pregunta que esta nota contesta.*
        nombres = uno.recetas or ([uno.texto] if uno.texto else [])
        detalle = "del plan: " + " + ".join(nombres) if nombres else "del plan"
        if uno.cantidad is not None:
            detalle += f" ({uno.cantidad:g} {uno.unidad or ''})".rstrip()
        # **Y los envases y el sobrante, que ahora SI se calculan.** *Antes el puente del plan no los
        # tenia* -- *no pasaba por `previa_compra`* --, **y el de la receta los tenia y los tiraba.**
        # *Son la respuesta a «cuantos paquetes compro», que es la segunda pregunta de una lista.*
        if uno.envases:
            detalle += f" · {uno.envases} envase{'s' if uno.envases != 1 else ''}"
            if uno.sobrante:
                detalle += f", sobran {uno.sobrante:g} {uno.unidad_envase or uno.unidad}"
        else:
            # **Y cuando el tamano del envase no se conoce, se DICE.** *Antes se callaba, y el silencio
            # se leia como «un envase basta» -- que es justo lo que no se sabe.*
            detalle += " · no se sabe el tamano del envase"
        if pendiente:
            # **Y si no tiene destino, tambien se dice.** *«Pendiente de identificar» es lo que la
            # pantalla enseña, y `sin_catalogo` lo que devuelve esta llamada: **la misma verdad en los dos
            # sitios**, que es lo que evita que una linea apuntada a medias parezca un producto.*
            detalle += " · pendiente de identificar (sin catalogo)"
        # *El id, determinista por la clave*: **repetir la operacion no duplica.**
        #
        # **Y la cantidad que se persiste son LOS ENVASES, no los gramos.** *El comentario de arriba
        # tenia razon en el problema -- poner 400 diria «400 envases» -- y se equivocaba en la salida:
        # **escribir 1 tampoco es la respuesta**, porque cuando la previa calcula **dos envases** la
        # cantidad que se guarda tiene que ser **dos**. *Y la unidad correcta ya existia, dicha en
        # `previa_compra`: **«cuenta los envases enteros»**.*
        #
        # *Y cuando no hay envases calculados, queda `1` -- porque `lista_linea.cantidad` es
        # `integer NOT NULL` y **«no se sabe» no cabe en la columna** --, pero **la nota ya lo dice**, asi
        # que el `1` no afirma nada.*
        # *** Y LA CLAVE LLEVA LA OPERACION, *que es lo que hace que dos operaciones distintas
        # **se acumulen** en vez de pisarse. *** *
        #
        # *Antes esto era `uuid5(lista_id|uno.clave)`, *y `uno.clave` es *** producto + unidad ***
        # *-- *o sea: *«200 g de tomate» --, *que **no dice de donde viene.** *Asi que
        # **traer el plan de una semana** y **traerlo de otra** daban **el mismo id**, *
        # *y `anade_linea` **actualizaba en vez de anadir** *-- *y **la segunda operacion se perdia
        # sin decirlo.** *
        #
        # *Y **la operacion es la semana** *(-- `desde|hasta` --)*: *
        #   *-- *traer **la misma semana dos veces** -> **el mismo id** -> *idempotente ✓
        #   *-- *traer **semanas distintas** -> **ids distintos** -> *se acumulan ✓
        #
        # *Y **no se inventa la formula**: *se usa *** `traspaso.id_de_linea` ***, *que es **la misma
        # cuenta** *y **vive en su modulo por un motivo escrito alli**: *«*Es una funcion y no dos
        # lineas dentro del endpoint *** a proposito ***: *asi se puede probar que [es] determinista
        # **sin base de datos ni servidor**, *que es lo unico que este proyecto no puede permitirse
        # no probar de un id.»* *
        #
        # *Y **dentro de una misma pasada** se sigue consolidando por identidad* *(-- *lo hace `ya`,
        # unas lineas mas abajo --)*, *que es lo que pide el encargo.* *
        almacen.anade_linea(lista_id, usuario["id"],
                            traspaso.id_de_linea(lista_id, f"{uno.clave}|{esta_operacion}"), nombre,
                            uno.grupo_id, uno.producto_id, uno.envases or 1, detalle,
                            operacion=esta_operacion)
        # **Y al conjunto de lo que ya hay**: dos recetas de la semana con el mismo ingrediente no pueden
        # dejar dos lineas, y eso se decide dentro de esta misma pasada.
        # **Y al conjunto de lo que ya hay, por IDENTIDAD.** *Antes se anadia el nombre en minusculas:
        # dos marcas distintas con el mismo texto quedaban como «ya estaba» y **la segunda no entraba**.*
        ya.add(((uno.grupo_id, uno.producto_id), nombre.strip().lower()))
        anadidos += 1
    return {"anadidos": anadidos, "ya_estaban": ya_estaban,
            "sin_catalogo": sorted(sin_destino)}

@app.get("/api/listas/{lista_id}/desde-la-compra")
def previa_de_la_compra(lista_id: str, compra_id: str | None = None,
                        usuario: dict = Depends(usuario_actual)) -> dict:
    """**La vista previa de consumir**: que lineas de la ultima compra se podrian anotar y con que datos.

    No escribe nada: el diario rechaza el tipo `compra` a proposito -- comprar no es comer --, asi que esto
    **propone** y la persona confirma.

    **Y dice la cobertura**, que es lo que hace que esto no mienta: las lineas cuyo producto **no** declara
    nutricion en el catalogo se devuelven aparte, con su nombre. Anotar las que se puede y callar las demas
    convertiria un dato que falta en una comida que parece completa.
    """
    _acceso(lista_id, usuario, hace_falta_escribir=False)
    compras = almacen.compras_de(lista_id, limite=1)
    if not compras:
        return {"compra_id": None, "anotarian": [], "sin_dato": [], "cobertura": {"con_dato": 0, "total": 0}}
    la_compra = compra_id or str(compras[0]["compra_id"])
    lineas = almacen.lineas_de_compra(la_compra)
    anotarian: list[dict] = []
    sin_dato: list[str] = []
    for linea in lineas:
        ficha = catalogo.producto(linea["producto_id"]) if linea.get("producto_id") else None
        nutricion = (ficha or {}).get("nutricion")
        if nutricion:
            anotarian.append({"linea_id": str(linea["linea_id"]), "nombre": linea["nombre"],
                              "producto_id": linea["producto_id"], "fuente_dato": "catalogo"})
        else:
            sin_dato.append(linea["nombre"])
    return {"compra_id": la_compra, "anotarian": anotarian, "sin_dato": sin_dato,
            "cobertura": {"con_dato": len(anotarian), "total": len(lineas)}}


class DesdeLaCompra(BaseModel):
    """Lo que la persona confirma que se comio, de su ultima compra."""

    fecha: str
    comida: str
    lineas: list[str] = []


@app.post("/api/listas/{lista_id}/desde-la-compra", status_code=201)
def anotar_de_la_compra(datos: DesdeLaCompra, lista_id: str,
                        usuario: dict = Depends(usuario_actual)) -> dict:
    """Anota en el diario **lo que la persona confirma** de su ultima compra.

    El diario rechaza el tipo `compra` a proposito -- comprar no es comer --, asi que esto anota `alimento` y
    solo lo que se pide: la compra propone, la persona decide.

    **La referencia es el identificador de la linea de compra**, y por eso anotar dos veces la misma linea no
    deja dos entradas: se mira antes si esa referencia ya esta en ese dia.

    **No se inventan calorias.** La nutricion del catalogo se guarda como texto y sacar los numeros de ahi es
    otra pieza; la entrada se anota sin ellas y el diario dice «sin dato», que es la verdad.
    """
    from core import diario as _diario

    from .diario import ruta_base as _ruta_diario

    _acceso(lista_id, usuario, hace_falta_escribir=False)
    compras = almacen.compras_de(lista_id, limite=1)
    if not compras:
        raise HTTPException(404, "Esta lista no tiene ninguna compra cerrada.")
    lineas = {str(x["linea_id"]): x for x in almacen.lineas_de_compra(str(compras[0]["compra_id"]))}
    pedidas = [str(x) for x in datos.lineas] or list(lineas)
    ajenas = [x for x in pedidas if x not in lineas]

    con = _diario.conecta(_ruta_diario())
    try:
        ya = {str(x.get("referencia")) for x in _diario.dia(con, usuario["id"], datos.fecha)["entradas"]}
        anotadas = 0
        ya_estaban: list[str] = []
        sin_nutricion: list[str] = []
        for linea_id in pedidas:
            if linea_id not in lineas:
                continue
            nombre = lineas[linea_id]["nombre"]
            if linea_id in ya:
                ya_estaban.append(nombre)
                continue
            _diario.apunta(con, usuario["id"], datos.fecha, datos.comida, tipo=_diario.ALIMENTO,
                           referencia=linea_id, nota=f"de la compra: {nombre}")
            anotadas += 1
            # **Y se dice que va sin dato, que era la mitad que faltaba.** El puente anota la
            # linea **sin nutricion**: el catalogo la tiene, pero leerla y escalarla por la
            # cantidad es trabajo que aqui aun no esta hecho. Asi que **todas** las que entran van
            # sin dato, y callarlo convertiria un dato que falta en una comida que parece
            # completa. Es la regla que este mismo endpoint escribe en su docstring: *no se
            # inventan calorias; la entrada se anota sin ellas y el diario dice «sin dato», que es
            # la verdad*. Medido el 11 de octubre de 2026: `sin_nutricion` se declaraba y se
            # devolvia siempre vacia mientras la entrada anotada no llevaba un solo nutriente.
            # Cuando el puente sepa leer la ficha del producto, esta lista se estrechara a las que
            # de verdad no la declaren.
            sin_nutricion.append(nombre)
    finally:
        con.close()
    return {"anotadas": anotadas, "ya_estaban": ya_estaban, "ajenas": ajenas,
            "sin_nutricion": sin_nutricion}
