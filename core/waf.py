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

# Cuando hay que abrir ventana, se abre **fuera de la vista del escritorio**.
#
# El dueno lo dijo dos dias seguidos: *"a veces salta el navegador"*. Con el reintento con
# la misma sesion y el modo oculto primero, el 26 de septiembre de 2026 se abrio 4 veces en
# toda la manana en vez de 10-13, pero **se abrio**, y una ventana de Chrome en medio del
# escritorio mientras trabajas es exactamente lo que no se quiere.
#
# El reto de AWS WAF necesita **un navegador de verdad**, no un navegador que se vea: los
# mismos retos pasan con la ventana colocada fuera del area visible, y el sistema la sigue
# tratando como una ventana normal (no es `headless`, que es lo que el WAF detecta mas).
#
# **Y una posicion fija no vale, medido el 26 de septiembre de 2026 con la ventana delante.**
# El primer arreglo ponia `-2400,-2400` a mano, y en este ordenador eso **no** esta fuera de
# la vista: su escritorio virtual empieza en x=-1.920 (hay un monitor a la izquierda del
# principal, 3.840 px de ancho en total), asi que una ventana de 1.382 px colocada en -2.400
# ocupa de -2.400 a -1.018 y **sus ultimos 900 px caen en el monitor de la izquierda**. La
# medicion, con la ventana abierta de verdad:
#
#     fuera       x=-2400 y=-2400 1382x1034  Pasteleria - Categorias - Alcampo superm...
#     escritorio virtual: x de -1.920 a 1.920 (3.840 x 1.083)
#
# O sea que el dueno seguia viendola, y con razon. Ahora la posicion se **calcula** a partir
# del escritorio de verdad (`SM_XVIRTUALSCREEN` y compania) y se coloca la ventana entera
# arriba a la izquierda de todo el escritorio: en este ordenador, `-2870,-750`, que con
# 900x700 ocupa de -2.870 a -1.970 y de -750 a -50, fuera del area de cualquier monitor.
TAMANO_VENTANA = (900, 700)
# Si no se pueden leer las metricas (otra plataforma, o ctypes capado), un valor que queda
# fuera de cualquier escritorio razonable.
POSICION_DE_EMERGENCIA = (-10_000, -10_000)


def escritorio() -> tuple[int, int, int, int]:
    """(x, y, ancho, alto) de TODO el escritorio virtual, sumando los monitores.

    En este ordenador devuelve `(-1920, 0, 3840, 1083)`: hay un monitor a la izquierda del
    principal. Si no se puede preguntar, devuelve un rectangulo de emergencia.
    """
    try:
        import ctypes
        u = ctypes.windll.user32
        # 76..79: SM_XVIRTUALSCREEN, SM_YVIRTUALSCREEN, SM_CXVIRTUALSCREEN, SM_CYVIRTUALSCREEN
        x, y = u.GetSystemMetrics(76), u.GetSystemMetrics(77)
        ancho, alto = u.GetSystemMetrics(78), u.GetSystemMetrics(79)
        if ancho and alto:
            return (x, y, ancho, alto)
    except Exception:  # noqa: BLE001
        pass
    return (-10_000, -10_000, 20_000, 20_000)


def posicion_fuera(escritorio_: tuple[int, int, int, int],
                   ancho: int, alto: int) -> tuple[int, int]:
    """Donde poner la ventana para que quede **entera** fuera de ese escritorio.

    **El margen no es el tamaño que pedimos, es el del escritorio**, y eso es una medicion:
    Chromium no hace caso de `--window-size` cuando el perfil ya tiene su tamaño guardado (el
    perfil se reutiliza a proposito, ver `obtener`). Medido el 26 de septiembre de 2026: se
    pidieron 900x700 y la ventana salio de **1.382x1.034**, asi que 50 px de margen dejaban
    asomar un trozo de 432x284 por el monitor de la izquierda. Contando con una ventana tan
    grande como el escritorio entero, no asoma ni maximizada.

    Es una funcion pura para poder comprobarla con escritorios de mentira (uno solo, dos en
    fila, dos en cruz) sin abrir ningun navegador.
    """
    x, y, ancho_esc, alto_esc = escritorio_
    return x - max(ancho, ancho_esc) - 100, y - max(alto, alto_esc) - 100


def fuera_de_la_vista(ancho: int | None = None, alto: int | None = None) -> list[str]:
    """Los argumentos que dejan la ventana **entera** fuera del escritorio virtual.

    Se calcula y no se escribe a mano porque el escritorio no es siempre 0,0-1920,1080: con
    dos monitores, el area visible puede empezar en x negativo, y una posicion fija que
    parece lejisimos puede caer dentro. Ver la medicion de arriba.
    """
    ancho = ancho or TAMANO_VENTANA[0]
    alto = alto or TAMANO_VENTANA[1]
    x, y = posicion_fuera(escritorio(), ancho, alto)
    return [f"--window-position={x},{y}", f"--window-size={ancho},{alto}"]


# El nombre se mantiene: es el que usan la configuracion del navegador y las pruebas.
ARGS_FUERA_DE_LA_VISTA = fuera_de_la_vista()


def _fichero(dominio: str) -> Path:
    return COOKIES / f"{dominio}.json"


def es_reto(html: str) -> bool:
    """Reconoce la pagina de reto de AWS WAF."""
    return "gokuProps" in html or "awsWafCookieDomainList" in html


def contenido(page, intentos: int = 4, espera_ms: int = 800) -> str | None:
    """El HTML de la pagina, aguantando a que deje de navegar. `None` si no se pudo.

    **Por que existe esto.** El 2 de octubre de 2026 el barrido de Alcampo se perdio entero, y
    el 5 y el 6 tampoco trajo nada, por una carrera de una linea:

        page.goto(url_prueba, wait_until="domcontentloaded")   # protegido
        page.wait_for_timeout(3000)                            # "que el reto se resuelva"
        html = page.content()                                  # <-- el reto recarga AQUI

    Cuando el reto de AWS WAF recarga la pagina justo en ese momento, leer el contenido lanza
    `Page.content: Unable to retrieve content because the page is navigating and changing the
    content`; el `except` de arriba solo envolvia el `goto`, asi que la excepcion subia hasta el
    colector, el dia terminaba con `FALLO: Error: Page.content` **y no se escribia ni una
    captura**. Ahora se intenta unas cuantas veces y, si de verdad no se puede, se dice `None` y
    el bucle de fuera vuelve a probar: quedarse sin leer una vez no puede costar el dia.
    """
    for _ in range(intentos):
        try:
            return page.content()
        except Exception:  # noqa: BLE001
            page.wait_for_timeout(espera_ms)
    return None


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
        if not headless:
            # Con ventana, pero fuera de la vista: ver `ARGS_FUERA_DE_LA_VISTA`.
            comun["args"] = list(ARGS_FUERA_DE_LA_VISTA)
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
            html = contenido(page)
            if html and not es_reto(html) and "__INITIAL_STATE__" in html:
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


def ventana_del_navegador(dominio: str, url_prueba: str,
                          segundos: int = 240) -> dict:
    """Abre el navegador como se abre de verdad y **dice donde ha quedado su ventana**.

    Existe porque esto hizo falta dos veces y las dos a mano:

      1. El 25 de septiembre de 2026 el dueno dijo *"a veces salta el navegador"*.
      2. El 26, con la ventana ya colocada en `-2400,-2400`, la medicion enseno que **seguia
         asomando** 432x284 px por el monitor de la izquierda (escritorio virtual de -1.920 a
         1.920) y que Chromium no hace caso de `--window-size` (900x700 pedidos, 1.382x1.034
         reales). De ahi salio `posicion_fuera`.

    Enumerar ventanas es de Windows (`user32`), que es donde corre la tarea. Devuelve las
    ventanas vistas y si la del navegador cae fuera del escritorio, para poder imprimirlo.

        uv run python -m core.waf --comprobar-ventana
    """
    import threading

    ventanas: dict[int, tuple] = {}
    parar = threading.Event()

    def anota() -> None:
        try:
            import ctypes
            import ctypes.wintypes as wt
            user32 = ctypes.windll.user32
            user32.SetProcessDPIAware()
        except Exception:  # noqa: BLE001
            return
        firma = ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)

        def cb(hwnd, _lparam):
            if not user32.IsWindowVisible(hwnd):
                return True
            rect = wt.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(rect))
            ancho, alto = rect.right - rect.left, rect.bottom - rect.top
            if ancho < 200 or alto < 100:          # tooltips y ventanas de 4x4
                return True
            largo = user32.GetWindowTextLengthW(hwnd)
            titulo = ctypes.create_unicode_buffer(largo + 1)
            user32.GetWindowTextW(hwnd, titulo, largo + 1)
            pid = wt.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            ventanas[hwnd] = (rect.left, rect.top, ancho, alto, pid.value, titulo.value[:60])
            return True

        while not parar.is_set():
            user32.EnumWindows(firma(cb), 0)
            time.sleep(0.2)

    esc = escritorio()
    hilo = threading.Thread(target=anota, daemon=True)
    hilo.start()
    resultado: dict = {"escritorio": esc, "posicion": fuera_de_la_vista(), "ventanas": []}
    try:
        resultado["sesion"] = obtener(dominio, url_prueba, headless=False)
    except Exception as exc:  # noqa: BLE001
        resultado["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        parar.set()
        hilo.join(timeout=5)

    for _hwnd, (x, y, ancho, alto, pid, titulo) in sorted(ventanas.items(),
                                                          key=lambda kv: kv[1][0]):
        fuera = (x + ancho <= esc[0] or y + alto <= esc[1]
                 or x >= esc[0] + esc[2] or y >= esc[1] + esc[3])
        resultado["ventanas"].append({"x": x, "y": y, "ancho": ancho, "alto": alto,
                                      "pid": pid, "titulo": titulo, "fuera": fuera})
    resultado["suyas"] = [v for v in resultado["ventanas"] if v["fuera"] or "Alcampo" in v["titulo"]]
    return resultado


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
    ap.add_argument("--comprobar-ventana", action="store_true",
                    help="abre el navegador con ventana y dice donde queda (solo Windows)")
    a = ap.parse_args()
    if a.comprobar_ventana:
        r = ventana_del_navegador(a.dominio, a.url)
        print(f"escritorio virtual: x de {r['escritorio'][0]} a "
              f"{r['escritorio'][0] + r['escritorio'][2]}, "
              f"y de {r['escritorio'][1]} a {r['escritorio'][1] + r['escritorio'][3]}")
        print(f"posicion calculada: {r['posicion']}")
        print(f"sesion: {'obtenida' if 'sesion' in r else r.get('error')}")
        suyas = [v for v in r["ventanas"] if "Alcampo" in v["titulo"]]
        for v in suyas or r["ventanas"][:5]:
            print(f"  {'FUERA DE LA VISTA' if v['fuera'] else 'EN PANTALLA':<16} "
                  f"x={v['x']} y={v['y']} {v['ancho']}x{v['alto']}  {v['titulo']}")
        if not suyas:
            print("  (no se vio la ventana del navegador: no se puede afirmar nada)")
        raise SystemExit(0)
    s = obtener(a.dominio, a.url, headless=a.headless)
    print(f"sesion guardada para {a.dominio}: {len(s['cookies'])} cookies")
    print(f"  {', '.join(sorted(s['cookies']))}")
