"""Superar el reto de AWS WAF con un navegador y reutilizar la sesion en HTTP plano.

Alcampo protege su catalogo con AWS WAF. Sin sesion, las paginas de categoria
llegan con un reto de JavaScript (`window.gokuProps`) en vez de datos. El reto lo
resuelve solo un navegador; despues deja cookies que valen durante horas y que si
sirven desde curl_cffi.

Un navegador al dia, no uno por pagina.

Dos detalles que hacen que esto funcione y que costaron un intento fallido:

1. **Se valida por resultado, no por el nombre de la cookie.** Da igual como se
   llame el testigo: lo que se comprueba es que una pagina de categoria de verdad
   llegue con datos. Buscar `aws-waf-token` a ciegas fallaba aunque la sesion ya
   fuese buena.
2. **Se copia tambien el User-Agent del navegador.** El testigo de AWS WAF va
   ligado al agente que lo obtuvo; mandarlo con otro agente lo invalida.

    uv run python -m core.waf                 # visible, la forma fiable
    uv run python -m core.waf --headless      # sin ventana, para el cron
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

from core import config

COOKIES = config.DATA / "cookies"
COOKIES.mkdir(parents=True, exist_ok=True)
VIDA_SEGUNDOS = 6 * 3600

# El navegador se abre VISIBLE por defecto: con ventana pasa retos que sin ella no
# pasa. Eso obliga a que la tarea programada corra con sesion iniciada ("ejecutar
# solo cuando el usuario haya iniciado sesion"). Si algun dia hace falta que corra
# a puerta cerrada, SCRAP_WAF_HEADLESS=1 lo intenta sin ventana, sabiendo que
# entonces el WAF cortara mas a menudo.
HEADLESS_POR_DEFECTO = os.environ.get("SCRAP_WAF_HEADLESS", "") == "1"


def _fichero(dominio: str) -> Path:
    return COOKIES / f"{dominio}.json"


def es_reto(html: str) -> bool:
    """Reconoce la pagina de reto de AWS WAF."""
    return "gokuProps" in html or "awsWafCookieDomainList" in html


def guardada(dominio: str) -> dict:
    """Sesion en cache, si sigue fresca. {} si no hay o ha caducado."""
    f = _fichero(dominio)
    if not f.exists():
        return {}
    datos = json.loads(f.read_text())
    if time.time() - datos.get("ts", 0) > VIDA_SEGUNDOS:
        return {}
    return {"cookies": datos.get("cookies", {}),
            "user_agent": datos.get("user_agent")}


def obtener(dominio: str, url_prueba: str, headless: bool | None = None,
            espera: int = 60) -> dict:
    """Abre un navegador hasta que `url_prueba` llegue con datos, y guarda la sesion.

    `url_prueba` debe ser una pagina que SI este protegida (una categoria), no la
    portada: si se valida contra una pagina libre, se guarda una sesion inutil.
    """
    try:
        from patchright.sync_api import sync_playwright
    except ImportError:
        raise RuntimeError(
            "falta patchright:  uv add patchright  &&  uv run patchright install chromium"
        ) from None

    headless = HEADLESS_POR_DEFECTO if headless is None else headless
    perfil = config.DATA / "navegador" / dominio
    perfil.mkdir(parents=True, exist_ok=True)
    sesion: dict = {}

    with sync_playwright() as p:
        comun = {
            "user_data_dir": str(perfil),
            "headless": headless,
            "locale": "es-ES",
            "timezone_id": "Europe/Madrid",
            "viewport": {"width": 1366, "height": 900},
        }
        try:
            # el Chrome de verdad pasa mas retos que el Chromium empaquetado
            ctx = p.chromium.launch_persistent_context(channel="chrome", **comun)
        except Exception:  # noqa: BLE001
            ctx = p.chromium.launch_persistent_context(**comun)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        # El reloj arranca AQUI, no antes de abrir el navegador. El 12 sep el
        # arranque de Chrome se comio los sesenta segundos enteros y el mensaje
        # de error decia "tras 0 intentos en 60s": se rindio sin haber probado
        # ni una vez. Y se prueba siempre al menos una, pase lo que pase con el
        # reloj, porque un intento que no se hace no puede salir bien.
        limite = time.time() + espera
        intentos = 0
        while intentos == 0 or time.time() < limite:
            intentos += 1
            try:
                page.goto(url_prueba, wait_until="domcontentloaded", timeout=45_000)
            except Exception:  # noqa: BLE001
                page.wait_for_timeout(2000)
                continue
            page.wait_for_timeout(3000)          # que el reto se resuelva y recargue
            html = page.content()
            if not es_reto(html) and "__INITIAL_STATE__" in html:
                sesion = {
                    "cookies": {c["name"]: c["value"] for c in ctx.cookies()},
                    "user_agent": page.evaluate("navigator.userAgent"),
                }
                break
            page.wait_for_timeout(2500)
        ctx.close()

    if not sesion:
        raise RuntimeError(
            f"tras {intentos} intentos en {espera}s, {dominio} sigue devolviendo el "
            f"reto de AWS WAF.\n"
            f"    Prueba en visible:  uv run python -m core.waf\n"
            f"    Si con ventana tampoco pasa, es que pide interaccion humana."
        )

    _fichero(dominio).write_text(json.dumps({"ts": time.time(), **sesion}))
    return sesion


def para(dominio: str, url_prueba: str, headless: bool | None = None) -> dict:
    """Sesion valida: de la cache si sirve, y si no se renueva con el navegador."""
    return guardada(dominio) or obtener(dominio, url_prueba, headless=headless)


def renueva(dominio: str, url_prueba: str) -> dict:
    """Sesion nueva **sin abrir una ventana, si se puede**.

    Lo pidio el dueno el 25 de septiembre de 2026: *"a veces salta el navegador"*.
    Y era verdad y estaba medido: el WAF corta entre 8 y 13 veces al dia en Alcampo
    (13 el 24 de septiembre, 10 el 23), y cada corte llamaba a `obtener()`, que abre
    Chrome **a la vista**. O sea que la tarea de las seis de la manana le robaba el
    foco al ordenador una docena de veces, sin necesidad.

    El orden es: primero sin ventana, y solo si eso no pasa el reto, con ventana.
    Esta en ese orden y no al reves porque **el modo sin ventana pasa menos retos**
    (medido: el WAF corta mas a menudo asi), pero cuando pasa, pasa, y no molesta a
    nadie. Cuando no pasa, se abre la ventana: quedarse sin catalogo por no querer
    abrir una ventana seria cambiar un dato por una comodidad.

    Devuelve la sesion, con `via` dentro para poder medir cual de las dos hizo falta.
    """
    try:
        sesion = obtener(dominio, url_prueba, headless=True)
    except RuntimeError:
        sesion = obtener(dominio, url_prueba, headless=False)
        sesion["via"] = "con_ventana"
        print("      (el reto no se paso sin ventana: se ha abierto el navegador)")
        return sesion
    sesion["via"] = "sin_ventana"
    return sesion


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--dominio", default="compraonline.alcampo.es")
    ap.add_argument(
        "--url",
        default="https://www.compraonline.alcampo.es/categories/frescos/"
                "pasteler%C3%ADa/OC1282",
        help="pagina PROTEGIDA con la que validar (una categoria, no la portada)")
    ap.add_argument("--headless", action="store_true", help="sin ventana")
    a = ap.parse_args()
    s = obtener(a.dominio, a.url, headless=a.headless)
    print(f"sesion guardada para {a.dominio}: {len(s['cookies'])} cookies")
    print(f"  {', '.join(sorted(s['cookies']))}")
