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

from . import alertas, almacen, analisis, catalogo, cesta, movimientos, panel, registro
from .ajustes import AJUSTES

COOKIE = "cesta_sesion"


@asynccontextmanager
async def ciclo(app: FastAPI):
    almacen.arranca()
    catalogo.conexion()          # que falle al arrancar y no en la primera visita
    yield
    almacen.para()


app = FastAPI(title="Cesta", version="1.0", lifespan=ciclo,
              docs_url="/api/docs", openapi_url="/api/openapi.json")
app.include_router(panel.rutas)
app.add_middleware(CORSMiddleware, allow_origins=list(AJUSTES.origenes),
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


# ------------------------------------------------------------ quien llama ---

def usuario_actual(peticion: Request) -> dict:
    yo = almacen.quien(peticion.cookies.get(COOKIE))
    if yo is None:
        raise HTTPException(401, "Hay que entrar primero.")
    return yo


def usuario_opcional(peticion: Request) -> dict | None:
    return almacen.quien(peticion.cookies.get(COOKIE))


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
    """
    lista = [c.strip() for c in cadenas.split(",")] if cadenas else None
    filtros = [s.strip() for s in sellos.split(",")] if sellos else None
    if lista is None and usuario:
        # Si no tiene Aldi cerca, sus resultados no deberian ensenarselo.
        cercanas = almacen.preferencias_de(usuario["id"]).get("cadenas_cerca")
        if cercanas:
            lista = list(cercanas)
    return {"fecha_datos": catalogo.fecha_de_gold(),
            "resultados": catalogo.buscar(q, lista, limite, comparables, con_nutricion,
                                          filtros, conservacion, marca_propia, ofertas,
                                          sin_alcohol, seccion)}


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
            subidas: bool = False,
            usuario: dict | None = Depends(usuario_opcional)):
    """Lo que mas ha cambiado de precio esta semana.

    `dias` se acota a la ventana que el historico puede sostener: pedir 365 dias
    con trece en disco no da un error, da una respuesta vacia que parece un fallo.
    """
    dias = max(1, min(dias, 90))
    lista = [c.strip() for c in cadenas.split(",")] if cadenas else None
    if lista is None and usuario:
        cercanas = almacen.preferencias_de(usuario["id"]).get("cadenas_cerca")
        if cercanas:
            lista = list(cercanas)
    return {"fecha_datos": catalogo.fecha_de_gold(), "dias": dias,
            "sentido": "subidas" if subidas else "bajadas",
            "resultados": movimientos.bajadas(dias, lista, limite, subidas)}


@app.get("/api/ofertas-dudosas")
def ofertas_dudosas(limite: int = 60, cadenas: str | None = None,
                    usuario: dict | None = Depends(usuario_opcional)):
    """Ofertas anunciadas que el historico no sostiene."""
    lista = [c.strip() for c in cadenas.split(",")] if cadenas else None
    if lista is None and usuario:
        cercanas = almacen.preferencias_de(usuario["id"]).get("cadenas_cerca")
        if cercanas:
            lista = list(cercanas)
    return {"fecha_datos": catalogo.fecha_de_gold(),
            "resultados": movimientos.ofertas_dudosas(limite, lista)}


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


class CambioLinea(BaseModel):
    tachado: bool | None = None
    en_carrito: bool | None = None
    cantidad: int | None = Field(default=None, ge=1, le=99)
    nota: str | None = None
    borrado: bool | None = None
    momento: datetime | None = None       # la hora del movil, no la de llegada


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


@app.get("/api/listas/{lista_id}")
def ver_lista(lista_id: str, usuario: dict = Depends(usuario_actual)):
    papel = _acceso(lista_id, usuario)
    lineas = almacen.lineas_de(lista_id)
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
    return almacen.anade_linea(lista_id, usuario["id"], linea.id, linea.nombre,
                               linea.grupo_id, linea.producto_id,
                               linea.cantidad, linea.nota)


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
                                     nota=cambio.nota, borrado=cambio.borrado,
                                     en_carrito=cambio.en_carrito, momento=momento)
    if resultado is None:
        raise HTTPException(404, "Esa linea ya no esta en la lista. Puede que la haya quitado la otra persona.")
    return resultado


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
                                    c.get("cantidad", 1), c.get("nota"))
            else:
                momento = c.get("momento")
                almacen.cambia_linea(
                    lista_id, c["id"], usuario["id"],
                    tachado=c.get("tachado"), cantidad=c.get("cantidad"),
                    nota=c.get("nota"), borrado=c.get("borrado"),
                    en_carrito=c.get("en_carrito"),
                    momento=datetime.fromisoformat(momento) if momento else None)
            hechos += 1
        # Un cambio malo no puede impedir que suban los demas: el movil manda lo
        # que tenga guardado, y alguno puede referirse a una linea que la otra
        # persona ya borro.
        except Exception as exc:  # noqa: BLE001
            fallidos.append({"id": c.get("id"), "motivo": type(exc).__name__})
    return {"aplicados": hechos, "fallidos": fallidos,
            "lineas": almacen.lineas_de(lista_id)}


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
    """
    mias = almacen.alertas_de(usuario["id"])
    return {"fecha_datos": catalogo.fecha_de_gold(),
            "alertas": mias,
            "saltan": alertas.evalua([a for a in mias if not a["vista_en"]])}


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


@app.get("/api/favoritos")
def ver_favoritos(usuario: dict = Depends(usuario_actual)):
    """Con el estado de hoy de cada uno, ordenados por lo que ha cambiado y no
    alfabeticamente: lo que ha bajado arriba, lo que ha subido debajo, lo quieto
    al final."""
    favs = almacen.favoritos_de(usuario["id"])
    salida = []
    for f in favs:
        if f["grupo_id"] is not None:
            g = catalogo.grupo(f["grupo_id"])
            if g:
                salida.append({"grupo_id": f["grupo_id"], "nombre": g["nombre"],
                               "precio_unidad_cent": g["productos"][0]["precio_unidad_cent"],
                               "cadena": g["productos"][0]["fuente"],
                               "unidad": g["unidad"], "ahorro_pct": g["ahorro_pct"]})
        elif p := catalogo.producto(f["producto_id"]):
            salida.append(p)
    return {"favoritos": salida, "fecha_datos": catalogo.fecha_de_gold()}


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
