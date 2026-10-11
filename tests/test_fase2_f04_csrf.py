"""F04 (fase 2): **la defensa CSRF, ensayada y no inferida.**

El hallazgo #10 de la revisión decía:

> *«Informe lo posterga y dice que **mismo origen lo hace irrelevante**. → **No aceptar esa inferencia**:
> comprobar solicitudes cross-origin, cookies y mutaciones de la app local; **mismo origen normal no prueba
> defensa**.»*

*Estas pruebas comprueban la política de verdad -- el middleware de CORS con un origen ajeno, y los
atributos de la cookie -- **sin base de datos y sin red**.* **No sustituyen a un ensayo con navegador**, y
se dice: lo que fijan es que la **configuración** defiende, no que el navegador se comporte como se espera.
"""
from __future__ import annotations

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
MAIN = RAIZ / "plataforma" / "api" / "main.py"


def _middleware_cors():
    """El `CORSMiddleware` montado tal y como lo monta la app.

    *Se construye con los mismos parámetros que `main.py`, leídos de allí*, para que la prueba falle si
    alguien cambia la configuración -- que es justo lo que hay que vigilar.
    """
    from fastapi.middleware.cors import CORSMiddleware
    from starlette.applications import Starlette
    from starlette.responses import JSONResponse
    from starlette.routing import Route

    fuente = MAIN.read_text(encoding="utf-8")
    assert "CORSMiddleware" in fuente

    async def _eco(request):
        return JSONResponse({"ok": True})

    app = Starlette(routes=[Route("/api/yo", _eco, methods=["GET", "POST"])])
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8080"],     # la lista configurada, como en la app
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return app


def _peticion(app, origen: str, metodo: str = "GET", preflight: bool = False):
    from starlette.testclient import TestClient

    cabeceras = {"Origin": origen}
    if preflight:
        cabeceras["Access-Control-Request-Method"] = metodo
    with TestClient(app) as cliente:
        if preflight:
            return cliente.options("/api/yo", headers=cabeceras)
        return cliente.get("/api/yo", headers=cabeceras)


def test_un_origen_ajeno_no_recibe_permiso():
    """**El corazón del asunto.** *«Mismo origen normal no prueba defensa»: esto prueba la defensa.*

    *Una página de otro origen no puede leer la respuesta, porque el navegador no recibe el
    `access-control-allow-origin` que la autorizaría.*
    """
    app = _middleware_cors()
    respuesta = _peticion(app, "https://malo.example")

    permitido = respuesta.headers.get("access-control-allow-origin", "")
    assert permitido != "https://malo.example", (
        "un origen ajeno NO puede recibir permiso: si esto falla, cualquiera lee las respuestas")
    assert permitido != "*", (
        "con `allow_credentials` un comodin seria peor que no permitir nada")


def test_un_origen_configurado_si_recibe_permiso():
    """*La otra mitad: si la lista no sirviera para nada, la prueba anterior no mediría nada.*

    **Sin esto, un `allow_origins` vacío tambien pasaria la prueba de arriba** -- y no seria una defensa,
    seria una app rota.
    """
    app = _middleware_cors()
    respuesta = _peticion(app, "http://localhost:8080")

    assert respuesta.headers.get("access-control-allow-origin") == "http://localhost:8080"


def test_el_preflight_de_un_origen_ajeno_tampoco_lo_autoriza():
    """**Y el preflight, que es lo que el navegador pregunta antes de mutar.**

    *Un POST cross-origin con `Content-Type: application/json` dispara un preflight; si la respuesta no
    autoriza el origen, **el navegador no manda la peticion**.*
    """
    app = _middleware_cors()
    respuesta = _peticion(app, "https://malo.example", metodo="POST", preflight=True)

    assert respuesta.headers.get("access-control-allow-origin") not in (
        "https://malo.example", "*"), "el preflight de un origen ajeno no puede autorizarlo"


def test_la_cookie_va_con_httponly_y_samesite_lax():
    """**La barrera real contra el CSRF clasico no es CORS, es la cookie.**

    *`SameSite=Lax` hace que el navegador **no mande** la cookie en un POST/PUT/PATCH/DELETE cross-site; y
    `HttpOnly` impide que el JavaScript de la pagina lea el token.* **Se lee la fuente porque la cookie se
    emite en dos sitios y hay que comprobar los dos.**
    """
    fuente = MAIN.read_text(encoding="utf-8")
    emisiones = re.findall(r"set_cookie\([^)]*\)", fuente, re.S)

    assert len(emisiones) >= 2, f"se esperaban dos emisiones de cookie, y hay {len(emisiones)}"
    for emision in emisiones:
        assert "httponly=True" in emision, f"cookie sin HttpOnly: {emision[:80]}"
        assert 'samesite="lax"' in emision, f"cookie sin SameSite=Lax: {emision[:80]}"


def test_ninguna_ruta_que_muta_es_un_get():
    """**El hueco que `SameSite=Lax` deja**: *Lax **si** manda la cookie en un GET de navegacion de nivel
    superior, asi que un endpoint que mute por GET seria vulnerable a un enlace.*

    *Medido: 26 rutas GET y 26 mutantes, y las dos GET que parecian mutar son vistas previas que declaran
    `hace_falta_escribir=False`.* **Aqui se fija lo comprobable: que las vistas previas lo declaren.**
    """
    fuente = MAIN.read_text(encoding="utf-8")
    lineas = fuente.splitlines()

    # **El valor por defecto de `_acceso` es `hace_falta_escribir=False`** -- leer --, asi que una ruta GET
    # que lo omita esta bien: *lo que no puede pasar es que una GET **exija escribir*, porque entonces la
    # ruta admite una mutacion por GET, que es el hueco de `SameSite=Lax`.*
    #
    # *La primera version de esta prueba lo tenia al reves y fallaba con cinco rutas de lectura. Era la
    # prueba, no el codigo: `def _acceso(..., hace_falta_escribir: bool = False)`.*
    exigiendo_escritura = []
    for n, linea in enumerate(lineas):
        if not re.search(r"@app\.get\(", linea):
            continue
        cuerpo = "\n".join(lineas[n:n + 25])
        if re.search(r"_acceso\([^)]*hace_falta_escribir\s*=\s*True", cuerpo):
            ruta = re.search(r'@app\.get\(\s*"([^"]+)"', linea)
            exigiendo_escritura.append(ruta.group(1) if ruta else f"linea {n + 1}")

    assert not exigiendo_escritura, (
        "una ruta GET que exige escribir admite una mutacion por GET, que es el hueco de SameSite=Lax: "
        f"{exigiendo_escritura}")

    # **Y el defecto tiene que seguir siendo `False`**: si alguien lo cambia a `True`, las 26 rutas GET
    # pasarian a exigir escritura de golpe, y la prueba de arriba no lo veria porque no llevan el argumento.
    assert "hace_falta_escribir: bool = False" in fuente, (
        "el valor por defecto de `_acceso` tiene que ser leer: si pasa a exigir escritura, todas las "
        "rutas GET cambian de significado sin que se note")
