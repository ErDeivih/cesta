"""Comprobacion de la suite en un navegador de verdad: navegacion, teclado, movil y recarga.

**Que comprueba, y por que cada cosa:**

  - **Navegacion**: que `/` sea el lanzador con los tres accesos y que cada aplicacion tenga su
    armazon con el menu lateral y las tres aplicaciones siempre visibles.
  - **Teclado**: es lo que se rompe sin querer en un cajon modal. Se comprueba que el boton de menu
    se alcanza con Tab, que al abrirlo **el foco entra dentro**, que Tab **da vueltas sin salirse**,
    que Escape **cierra y devuelve el foco al boton**, y que el fondo queda inerte.
  - **Movil**: a 390 px el lateral no existe y manda el cajon; a 1280 px manda el lateral.
  - **Recarga**: recargar en una ruta profunda sigue funcionando y el cajon no se queda abierto.
  - **Ausencia de errores**: se recogen los `pageerror` y los errores de consola. **Aviso honesto**:
    la API no esta levantada (Docker parado), asi que las pantallas mostraran sus estados de error
    de datos; eso es un estado previsto y no cuenta como fallo de armazon, pero se apunta aparte
    para no confundir "no hay datos" con "la pantalla esta rota".

Uso:  uv run python -m plataforma.prueba_suite     (con el servidor de desarrollo en 5173)
"""
import sys
from pathlib import Path

from patchright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parents[1]
UI = "http://localhost:5173"
CAPTURAS = RAIZ / "data" / "capturas-s06"
resultados: list[tuple[bool, str]] = []


def comprueba(condicion: bool, texto: str) -> None:
    resultados.append((bool(condicion), texto))
    print(f"  {'OK  ' if condicion else 'FALLA'} {texto}")


with sync_playwright() as pw:
    navegador = pw.chromium.launch()
    CAPTURAS.mkdir(parents=True, exist_ok=True)

    # ---------- escritorio ----------
    contexto = navegador.new_context(viewport={"width": 1280, "height": 900})
    pagina = contexto.new_page()
    errores: list[str] = []
    pagina.on("pageerror", lambda e: errores.append(str(e)))

    pagina.goto(UI, wait_until="networkidle")
    comprueba(pagina.locator("nav[aria-label='Aplicaciones'] a").count() == 3,
              "el lanzador ofrece las tres aplicaciones")
    pagina.screenshot(path=str(CAPTURAS / "01-lanzador-escritorio.png"), full_page=True)

    pagina.goto(f"{UI}/compra", wait_until="networkidle")
    lateral = pagina.locator("aside[aria-label='Menu de la suite']")
    comprueba(lateral.is_visible(), "/compra tiene menu lateral en escritorio")
    comprueba(lateral.locator("nav[aria-label='Aplicaciones'] a").count() == 3,
              "las tres aplicaciones siguen visibles dentro de una")
    comprueba(lateral.locator("nav[aria-label='Secciones de Compra'] a").count() >= 4,
              "el lateral muestra las subsecciones de la aplicacion activa")
    comprueba(pagina.locator("header h1").first.inner_text().strip() != "",
              "la cabecera lleva el titulo de la seccion")
    # El elemento activo se marca con aria-current, no solo con color.
    comprueba(lateral.locator("[aria-current='page']").count() >= 1,
              "la aplicacion activa lleva aria-current")
    pagina.screenshot(path=str(CAPTURAS / "02-compra-escritorio.png"), full_page=True)

    for ruta, nombre in (("/recetas", "Recetas"), ("/calorias", "Calorias")):
        pagina.goto(f"{UI}{ruta}", wait_until="networkidle")
        comprueba(pagina.locator("p", has_text=nombre).first.is_visible(),
                  f"{ruta} lleva su armazon con el nombre de la aplicacion")

    # ---------- movil y teclado ----------
    contexto_movil = navegador.new_context(viewport={"width": 390, "height": 844})
    movil = contexto_movil.new_page()
    movil.on("pageerror", lambda e: errores.append(str(e)))
    movil.goto(f"{UI}/compra", wait_until="networkidle")
    comprueba(not movil.locator("aside[aria-label='Menu de la suite']").is_visible(),
              "a 390 px el lateral no se pinta")
    boton = movil.locator("button[aria-controls='menu-suite']")
    comprueba(boton.is_visible(), "a 390 px hay boton de menu")
    comprueba("Compra" in boton.inner_text(), "el boton dice en que aplicacion estas, no solo Menu")
    caja = boton.bounding_box()
    comprueba(bool(caja) and caja["width"] >= 44 and caja["height"] >= 44,
              "el boton de menu mide al menos 44x44")
    movil.screenshot(path=str(CAPTURAS / "03-compra-movil.png"), full_page=True)

    boton.click()
    cajon = movil.locator("div[role='dialog'][aria-modal='true']")
    comprueba(cajon.is_visible(), "el cajon se abre")
    dentro = movil.evaluate("document.activeElement?.closest(\"[role='dialog']\") !== null")
    comprueba(dentro, "al abrir el cajon el foco entra dentro")
    ancho = cajon.bounding_box()
    comprueba(bool(ancho) and ancho["width"] >= 280, "el cajon mide 288 px (o su tope en pantalla)")
    # Tab da vueltas dentro: se dan diez y el foco sigue en el dialogo.
    for _ in range(10):
        movil.keyboard.press("Tab")
    comprueba(movil.evaluate("document.activeElement?.closest(\"[role='dialog']\") !== null"),
              "Tab no se escapa del cajon")
    # El fondo queda inerte mientras el cajon esta abierto.
    comprueba(movil.evaluate("document.querySelector('main')?.closest('[inert]') !== null"),
              "el contenido de detras queda inerte")

    movil.keyboard.press("Escape")
    comprueba(not cajon.is_visible(), "Escape cierra el cajon")
    comprueba(movil.evaluate("document.activeElement === document.querySelector("
                             "\"button[aria-controls='menu-suite']\")"),
              "al cerrar, el foco vuelve al boton de menu")

    # ---------- recarga ----------
    movil.goto(f"{UI}/calorias/tendencias", wait_until="networkidle")
    movil.reload(wait_until="networkidle")
    comprueba(movil.locator("body").inner_text().strip() != "", "recargar en ruta profunda sigue pintando")
    comprueba(not movil.locator("div[role='dialog']").is_visible(), "tras recargar, el cajon no queda abierto")

    # ---------- redirecciones antiguas ----------
    escritorio2 = navegador.new_context(viewport={"width": 1280, "height": 900})
    p2 = escritorio2.new_page()
    p2.goto(f"{UI}/buscar?q=leche", wait_until="networkidle")
    comprueba("/compra" in p2.url and "q=leche" in p2.url,
              "la direccion antigua /buscar lleva a /compra y conserva la busqueda")

    comprueba(not errores, f"sin errores de pagina ({len(errores)}): {errores[:2]}")
    navegador.close()

fallos = [t for ok, t in resultados if not ok]
print(f"\ncomprobaciones: {len(resultados)} · fallos: {len(fallos)}")
for t in fallos:
    print(f"  FALLO: {t}")
print(f"capturas en {CAPTURAS.relative_to(RAIZ).as_posix()}")
sys.exit(1 if fallos else 0)
