"""La puerta de las funciones: cada accion del usuario, hecha de verdad en un navegador.

**Por que existe.** Las otras dos puertas del navegador miran lo que el encargo pide: las cuatro
preguntas y su medicion (`prueba_navegador`) y lo que se sirve en produccion
(`prueba_produccion`). Entre las dos se recorren las pantallas, pero **no se ejercita todo lo
que la aplicacion sabe hacer**: quedaban sin tocar el alta y la baja, varias listas, cambiar el
nombre de una, los favoritos, las vistas guardadas, las busquedas recientes, las preferencias de
cadenas, los pesos del «que te importa», elegir tienda por linea, y salir y volver a entrar.

Esto no mide si algo se entiende -- eso es la barra (a), y la cierra el dueño -- ni si esta bien
puesto: mide **que funciona**. Cada comprobacion hace la accion como la hace una persona (tocar
el boton, escribir en el campo) y mira el resultado en la pantalla.

La cuenta es desechable: se crea al empezar y se borra al terminar, y si una pasada anterior se
corto a mitad, se borra antes de empezar (una pasada cortada dejaba la cuenta con su lista y la
siguiente fallaba por el estado que habia dejado ella misma).

    uv run python -m plataforma.prueba_funciones
    uv run python -m plataforma.prueba_funciones --guardar-capturas
"""
from __future__ import annotations

import argparse
import contextlib
import os
import pathlib
import re
import sys

BASE = os.environ.get("CESTA_UI", "http://127.0.0.1:8080")
USUARIO = "prueba-funciones"
CLAVE = "clave-de-prueba-123"
CAPTURAS = pathlib.Path("data/debug/capturas/funciones")

FALLOS: list[str] = []
HECHAS = 0


def comprueba(condicion: bool, queja: str) -> None:
    """Apunta una comprobacion. El numero lo pone este contador, no la queja.

    Antes cada queja traia su numero escrito a mano y al anadir comprobaciones se repitieron
    (dos «13.», cuatro «35.»), de forma que «FALLO 13» no senalaba nada. Ahora la queja dice que
    se miro y el contador dice cual es.
    """
    global HECHAS
    HECHAS += 1
    marca = "   ok    " if condicion else "   FALLO "
    print(f"{marca}{HECHAS:>3}. {queja}")
    if not condicion:
        FALLOS.append(f"{HECHAS}. {queja}")


def main() -> int:
    from patchright.sync_api import sync_playwright

    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--guardar-capturas", action="store_true",
                    help="deja una captura de las pantallas clave en data/debug/capturas/funciones")
    args = ap.parse_args()
    if args.guardar_capturas:
        CAPTURAS.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        navegador = p.chromium.launch()
        ctx = navegador.new_context(viewport={"width": 390, "height": 844},
                                    has_touch=True, is_mobile=True)
        pagina = ctx.new_page()
        consola: list[str] = []
        pagina.on("pageerror", lambda e: consola.append(f"pageerror: {e}"))
        pagina.on("console", lambda m: consola.append(f"{m.type}: {m.text[:120]}")
                 if m.type == "error" else None)

        def carga(ruta: str) -> None:
            pagina.goto(f"{BASE}{ruta}", wait_until="domcontentloaded")
            with contextlib.suppress(Exception):
                pagina.wait_for_load_state("networkidle", timeout=8000)
            pagina.wait_for_timeout(900)

        def captura(nombre: str) -> None:
            if args.guardar_capturas:
                pagina.screenshot(path=str(CAPTURAS / f"{nombre}.png"))

        def texto() -> str:
            return pagina.inner_text("main")

        def lineas() -> int:
            return pagina.locator("input[type=checkbox]").count()

        def espera(condicion, segundos: float = 12.0) -> bool:
            """Espera a que algo sea verdad. Devuelve si lo fue."""
            import time
            fin = time.monotonic() + segundos
            while time.monotonic() < fin:
                with contextlib.suppress(Exception):
                    if condicion():
                        return True
                pagina.wait_for_timeout(250)
            with contextlib.suppress(Exception):
                return bool(condicion())
            return False

        def entrar_o_crear() -> None:
            carga("/cesta")
            if pagina.get_by_label("Clave").count():
                pagina.get_by_label("Usuario").fill(USUARIO)
                pagina.get_by_label("Clave").fill(CLAVE)
                pagina.get_by_role("button", name="Entrar").first.click()
                pagina.wait_for_timeout(2500)
                carga("/cesta")

        # ---------------------------------------------------------------- la cuenta ---
        print("\n== la cuenta, de cero")
        entrar_o_crear()
        if "No tienes ninguna lista" not in texto() and pagina.locator(
                "input[type=checkbox]").count() > 0:
            # Una pasada cortada a mitad deja la cuenta con su lista: se borra y se empieza.
            borrado = pagina.evaluate(
                "async () => (await fetch('/api/yo', {method: 'DELETE',"
                " credentials: 'same-origin'})).status")
            print(f"   (quedaba una cuenta a medias: se ha borrado, {borrado})")
            carga("/cesta")
        if pagina.get_by_role("button", name="Créala").count():
            pagina.get_by_role("button", name="Créala").first.click()
            pagina.get_by_label("Tu nombre").fill("Prueba de funciones")
            pagina.get_by_label("Usuario").fill(USUARIO)
            pagina.get_by_label("Contraseña").fill(CLAVE)
            pagina.get_by_role("button", name="Crear cuenta").first.click()
            with contextlib.suppress(Exception):
                pagina.get_by_role("button", name="Añadir").first.wait_for(timeout=25000)
            carga("/cesta")
        comprueba("No tienes ninguna lista" in texto(),
                  "el alta deja la cuenta en la pantalla de la primera vez")

        # --------------------------------------------------------- apuntar cosas -------
        print("\n== apuntar, cambiar, tachar, quitar")
        pagina.get_by_role("button", name="Añadir").first.click()
        espera(lambda: lineas() >= 1)
        comprueba(lineas() == 1, f"añadir desde el mosaico apunta una linea ({lineas()})")
        primera = pagina.locator("input[type=checkbox]").first
        # La cantidad: `+` sube a 2.
        mas = pagina.locator("button[aria-label^='Más ']").first
        if mas.count():
            mas.click()
            comprueba(espera(lambda: "2" in pagina.locator(
                "button[aria-label^='Más ']").first.locator("xpath=..").inner_text()),
                "el boton de mas sube la cantidad")
        else:
            comprueba(False, "no encuentro el boton de subir la cantidad")
        # Tachar: la linea se va a «En el carro».
        primera.click()
        comprueba(espera(lambda: pagina.locator("input[type=checkbox]:checked").count() == 1),
                  "tachar manda la linea al carro")
        pagina.locator("input[type=checkbox]:checked").first.click()
        comprueba(espera(lambda: pagina.locator("input[type=checkbox]:checked").count() == 0),
                  "y destacharla la devuelve a «Por coger»")
        # Quitar, y deshacer.
        quitar = pagina.locator("button[aria-label^='Quitar '][aria-label$=' de la lista']")
        quitar.first.click()
        comprueba(espera(lambda: "Has quitado" in texto()), "quitar una linea lo dice")
        deshacer = pagina.get_by_role("button", name="Deshacer")
        if deshacer.count():
            deshacer.first.click()
            comprueba(espera(lambda: lineas() == 1), "y «Deshacer» la trae de vuelta")
        else:
            comprueba(False, "no hay boton de deshacer")

        # ------------------------------------------------------------ varias listas ----
        print("\n== varias listas: crear, cambiar de nombre, borrar")
        nueva = pagina.get_by_role("button", name="Lista nueva")
        comprueba(nueva.count() == 1, "hay boton de lista nueva")
        if nueva.count():
            nueva.first.click()
            with contextlib.suppress(Exception):
                pagina.get_by_role("textbox").first.wait_for(timeout=8000)
            caja = pagina.get_by_role("textbox").first
            caja.fill("Navidad")
            pagina.get_by_role("button", name="Crear").first.click()
            comprueba(espera(lambda: "Navidad" in pagina.inner_text("body")),
                      "crear la lista nueva la deja seleccionada")
        # Volver a la de casa y renombrarla. **Se mira el desplegable de listas**, que es donde
        # se ve el nombre de verdad: buscar el nombre en el texto de la pagina entera daba por
        # bueno un nombre que estaba de opcion en un desplegable cerrado.
        carga("/cesta")
        selector_listas = pagina.locator("select[aria-label='Lista']")
        comprueba(selector_listas.count() == 1, "esta el desplegable de listas")
        opciones = selector_listas.first.locator("option").all_inner_texts()
        casa = next((o for o in opciones if o.startswith("Casa")), None)
        comprueba(casa is not None, f"la lista de casa esta en el desplegable ({opciones})")
        if casa:
            selector_listas.first.select_option(label=casa)
            espera(lambda: lineas() == 1)
            comprueba(lineas() == 1, f"cambiar de lista trae sus lineas ({lineas()})")
        cambiar = pagina.get_by_role("button", name="Cambiar el nombre")
        if cambiar.count():
            cambiar.first.click()
            caja = pagina.get_by_role("textbox").first
            caja.fill("La de casa")
            pagina.get_by_role("button", name="Guardar").first.click()
            comprueba(espera(lambda: any(
                o.startswith("La de casa")
                for o in pagina.locator("select[aria-label='Lista'] option").all_inner_texts())),
                "cambiar el nombre se ve en el desplegable")
        else:
            comprueba(False, "no encuentro «Cambiar el nombre»")
        # Borrar la otra (la que cree al principio y esta vacia).
        carga("/cesta")
        antes_de_borrar = pagina.locator("select[aria-label='Lista'] option").all_inner_texts()
        otra = next((o for o in antes_de_borrar if o.startswith("Navidad")), None)
        if otra:
            selector_listas.first.select_option(label=otra)
            pagina.wait_for_timeout(2000)
            pagina.get_by_role("button", name="Quitar la lista").first.click()
            with contextlib.suppress(Exception):
                pagina.get_by_role("button", name="Sí, quitar esta lista").first.click()
            pagina.wait_for_timeout(2500)
            # **Se recarga antes de mirar el desplegable.** Justo despues de borrar, la lista de
            # listas se esta volviendo a pedir y el desplegable pasa por un momento sin
            # opciones: medido con `data/debug/borrar_lista.py`, la API ya tenia la lista
            # correcta (`[('Casa', 1)]`) mientras la pantalla enseñaba `[]`. Mirar en ese hueco
            # daba un FALLO que no era de la aplicacion.
            carga("/cesta")
            despues_de_borrar = pagina.locator(
                "select[aria-label='Lista'] option").all_inner_texts()
            comprueba(len(despues_de_borrar) == len(antes_de_borrar) - 1
                      and not any(o.startswith("Navidad") for o in despues_de_borrar),
                      "quitar una lista la quita del desplegable "
                      f"({antes_de_borrar} -> {despues_de_borrar})")
        else:
            comprueba(False, f"no encuentro la lista «Navidad» que cree antes "
                             f"({antes_de_borrar})")

        # ------------------------------------------------------------- favoritos -------
        print("\n== favoritos: marcar, ver, pasar a la lista, quitar")
        # **Antes hay que tener una lista**, y esto costo un FALLO falso: sin ninguna lista,
        # `ElegirLista` enseña un enlace a la cesta («Crea una lista para poder añadir») y los
        # botones salen apagados **a proposito**. La puerta los daba por rotos.
        carga("/cesta")
        if lineas() == 0:
            pagina.get_by_role("button", name="Añadir").first.click()
            espera(lambda: lineas() >= 1)
        carga("/grupo/526")
        corazon = pagina.get_by_role("button", name="Guardar")
        if corazon.count():
            corazon.first.click()
            pagina.wait_for_timeout(2000)
        carga("/favoritos")
        comprueba("Todavía no tienes favoritos" not in texto(),
                  "marcar un favorito lo deja en la pantalla de favoritos")
        comprueba(pagina.locator("select").count() == 1,
                  "con una lista, el desplegable de destino esta")
        # **La cuenta de lineas se mide en la lista**, no en favoritos: alli no hay casillas, y
        # comparar el numero de una pantalla con el de otra daba un FALLO falso.
        carga("/cesta")
        antes = lineas()
        carga("/favoritos")
        a_lista = pagina.get_by_role("button", name=re.compile(r"^A la lista$"))
        if a_lista.count():
            a_lista.first.click()
            comprueba(espera(lambda: "Añadido a la lista" in texto()),
                      "pasar un favorito a la lista lo dice")
            carga("/cesta")
            comprueba(lineas() == antes + 1,
                      f"y queda apuntado ({antes} -> {lineas()} lineas)")
        else:
            comprueba(False, "no hay boton de pasar el favorito a la lista")
        carga("/favoritos")
        quitar_fav = pagina.get_by_role("button", name="Quitar")
        if quitar_fav.count():
            quitar_fav.first.click()
            pagina.wait_for_timeout(2000)
            carga("/favoritos")
            comprueba("Todavía no tienes favoritos" in texto(),
                      "quitar el favorito deja la pantalla vacia")
        else:
            comprueba(False, "no hay boton de quitar el favorito")

        # ----------------------------------------------------------------- avisos ------
        print("\n== avisos: pedirlo desde la ficha")
        carga("/grupo/526")
        campana = pagina.get_by_role("button", name="Avisarme si baja")
        if campana.count():
            campana.first.click()
            pagina.wait_for_timeout(2500)
        carga("/avisos")
        comprueba("No sigues ningún producto" not in texto(),
                  "el aviso pedido en la ficha sale en la pantalla de avisos")

        # ------------------------------------------------- elegir tienda por linea -----
        print("\n== el reparto: elegir tienda")
        carga("/cesta")
        selector = pagina.locator("select").first
        if selector.count():
            antes = texto()[:200]
            with contextlib.suppress(Exception):
                selector.select_option(index=1)
            pagina.wait_for_timeout(2500)
            comprueba(texto() != antes or "decidid" in texto().lower(),
                      "elegir tienda en el reparto cambia la pantalla")
        else:
            print("   (no hay selector de tienda: la lista no tiene reparto que decidir)")

        # ------------------------------------------------------------ el buscador -----
        print("\n== el buscador: filtros, orden, vistas guardadas, recientes")
        carga("/buscar?q=leche+entera")
        chip = pagina.locator("[aria-label='Cadena de los resultados'] button").first
        if chip.count():
            chip.click()
            pagina.wait_for_timeout(2500)
            comprueba(pagina.locator(
                "[aria-label='Cadena de los resultados'] button[aria-pressed='true']"
            ).count() == 1, "el filtro de cadena se marca")
        cargar_vista = pagina.get_by_text("Guardar estos filtros")
        comprueba(cargar_vista.count() == 1, "hay donde guardar los filtros")
        if cargar_vista.count():
            cargar_vista.first.click()
            caja = pagina.get_by_role("textbox").first
            caja.fill("Mi vista")
            with contextlib.suppress(Exception):
                pagina.get_by_role("button", name="Guardar").first.click()
            pagina.wait_for_timeout(1200)
            comprueba("Mi vista" in pagina.inner_text("body"),
                      "la vista guardada aparece con su nombre")
        # Las busquedas recientes: dos busquedas y volver. **El rotulo se pinta en
        # mayusculas por CSS**, asi que el texto leido pone «LO QUE HAS BUSCADO»: buscarlo tal
        # cual daba un FALLO falso.
        for que in ("aceite de oliva", "papel de cocina"):
            carga("/")
            campo = pagina.get_by_placeholder("leche entera, atún, papel de cocina…")
            campo.fill(que)
            campo.press("Enter")
            with contextlib.suppress(Exception):
                pagina.wait_for_url("**/buscar**", timeout=15000)
            pagina.wait_for_timeout(2500)
        carga("/buscar")
        recientes = pagina.inner_text("body").upper()
        guardadas = pagina.evaluate(
            "() => localStorage.getItem('cesta.busquedas.v1') || ''")
        comprueba("LO QUE HAS BUSCADO" in recientes and "ACEITE DE OLIVA" in recientes,
                  f"las busquedas recientes salen como chips ({guardadas[:60]})")

        # ---------------------------------------------------------------- ajustes ------
        print("\n== ajustes: cadenas cercanas, salir y volver a entrar")
        carga("/ajustes")
        chip_cadena = pagina.get_by_role("button", name="Aldi")
        if chip_cadena.count():
            antes = chip_cadena.first.get_attribute("aria-pressed")
            chip_cadena.first.click()
            pagina.wait_for_timeout(2000)
            carga("/ajustes")
            despues = pagina.get_by_role("button", name="Aldi").first.get_attribute(
                "aria-pressed")
            # **Se marca lo que se quiere mirar**: pulsar la pastilla la mete (o la saca) de
            # «tengo cerca», y lo que se comprueba es que el cambio **se guarda**, no el
            # sentido: mirarlo al reves daba otro FALLO falso.
            comprueba(despues != antes,
                      f"marcar una cadena cercana se guarda ({antes} -> {despues})")
        else:
            comprueba(False, "no encuentro las pastillas de cadenas en ajustes")
        salir = pagina.get_by_role("button", name="Salir").first
        if salir.count():
            salir.click()
            pagina.wait_for_timeout(2500)
            carga("/cesta")
            comprueba(pagina.get_by_label("Clave").count() == 1,
                      "«Salir» deja la pantalla pidiendo entrar")
        else:
            comprueba(False, "no encuentro el boton de salir")
        entrar_o_crear()
        carga("/cesta")
        comprueba(lineas() >= 1, f"volver a entrar deja la lista donde estaba "
                                 f"({lineas()} lineas)")
        captura("cesta-con-la-lista")

        # ------------------------------------------------------------------ panel ------
        print("\n== el panel: la ventana, las subidas y lo mio")
        carga("/panel?pestana=bajadas")
        comprueba("en 7 días" in texto(), "el panel abre en la ventana de 7 dias")
        ventana = pagina.locator("select").first
        if ventana.count():
            with contextlib.suppress(Exception):
                ventana.select_option("30")
            pagina.wait_for_timeout(2500)
            comprueba("en 30 días" in texto(), "cambiar la ventana a 30 dias se ve")
        subidas = pagina.get_by_role("button", name="Ver las subidas")
        if subidas.count():
            subidas.first.click()
            pagina.wait_for_timeout(2500)
            comprueba("subido" in texto(), "«Ver las subidas» cambia el sentido")
        mio = pagina.get_by_role("button", name="Solo lo mío")
        if mio.count():
            mio.first.click()
            pagina.wait_for_timeout(3000)
            comprueba("Lo tuyo" in texto() or "Nada de lo tuyo" in texto(),
                      "«Solo lo mío» contesta lo tuyo")
        captura("panel-bajadas")

        # ------------------------------------------------------------------ grupo ------
        print("\n== la ficha del grupo: los pesos")
        carga("/grupo/526")
        pesos = pagina.locator("input[type=range]")
        comprueba(pesos.count() >= 3, f"la ficha del grupo tiene sus pesos ({pesos.count()})")
        if pesos.count():
            antes = texto()
            with contextlib.suppress(Exception):
                pesos.first.fill("100")
            pagina.wait_for_timeout(2000)
            comprueba(texto() != antes, "mover un peso cambia el orden de las alternativas")
        captura("grupo")

        # ---------------------------------------------------------------- escaner ------
        print("\n== el escaner")
        carga("/escaner")
        pagina.get_by_label("Código de barras").fill("4005808221950")
        pagina.get_by_role("button", name="Buscar").first.click()
        with contextlib.suppress(Exception):
            pagina.get_by_text("Añadir a la cesta").first.wait_for(timeout=20000)
        comprueba("No tengo ese código" not in texto(),
                  "un codigo conocido contesta con el producto")
        carga("/escaner")
        pagina.get_by_label("Código de barras").fill("1234567890123")
        pagina.get_by_role("button", name="Buscar").first.click()
        pagina.wait_for_timeout(3000)
        # El texto es **«No tengo ese código»**, tal cual: buscar «No tengo este» daba un FALLO
        # falso con la pantalla diciendolo bien.
        comprueba("No tengo ese código" in texto(),
                  "un codigo que no esta lo dice, en vez de callarse")
        captura("escaner")

        # ------------------------------------------------------------ sin sesion -------
        print("\n== la cara sin sesion")
        suelta_ctx = navegador.new_context(viewport={"width": 390, "height": 844},
                                           has_touch=True, is_mobile=True)
        suelta = suelta_ctx.new_page()
        for ruta, tiene_que_decir in (("/cesta", "Entra para ver tu lista"),
                                      ("/avisos", "Entra para ver tus avisos"),
                                      ("/favoritos", "Entra para ver tus favoritos"),
                                      ("/ajustes", "Entra para cambiar tus ajustes")):
            with contextlib.suppress(Exception):
                suelta.goto(f"{BASE}{ruta}", wait_until="domcontentloaded", timeout=30000)
            suelta.wait_for_timeout(2000)
            visto = suelta.inner_text("main")
            comprueba(tiene_que_decir in visto and "Cargando" not in visto,
                      f"sin sesion, {ruta} pide entrar y no se queda cargando")
        suelta_ctx.close()

        # ------------------------------------------------------- la cuenta se borra ----
        print("\n== y la cuenta de prueba se borra")
        carga("/ajustes")
        borrado = pagina.evaluate(
            "async () => (await fetch('/api/yo', {method: 'DELETE',"
            " credentials: 'same-origin'})).status")
        comprueba(borrado == 200, f"la cuenta de prueba se borra ({borrado})")

        errores = [c for c in consola if "pageerror" in c or "Failed to fetch" in c]
        print(f"\n== el resultado\n   consola: {len(consola)} mensajes"
              + (f"\n      {consola[0]}" if consola else ""))
        comprueba(not errores, f"sin excepciones de JavaScript ({errores[:2]})")
        print(f"\n   {HECHAS - len(FALLOS)} de {HECHAS} comprobaciones bien")
        if FALLOS:
            print("   FALLOS:")
            for f in FALLOS:
                print(f"     - {f}")
            print("\n   Lo que no funcione aqui, no funciona para nadie.")
            return 1
        print("\n   TODAS LAS FUNCIONES CONTESTAN.")
        ctx.close()
        navegador.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
