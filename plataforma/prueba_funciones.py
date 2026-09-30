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

Y mide tambien **que lo que se despliega se note que se despliega**: los diez desplegables de la
aplicacion llevan su flecha y gira al abrirse. Eso no lo encontro leer el codigo, lo encontro
mirar una captura (ver `Resumen` en `componentes/ui.tsx`).

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

# **Cuantas comprobaciones hace una pasada que va bien.** Es el numero que se cita en
# `docs/OPERACION.md` y en `.stitch/DESIGN.md`, y la pasada lo comprueba al final: si alguien
# anade o quita una, la puerta lo dice en vez de dejar los documentos mintiendo. Las ramas que
# solo se corren cuando algo va mal (`no hay boton de deshacer`...) cuentan tambien, pero esas
# pasadas ya salen con FALLO y el numero es lo de menos.
COMPROBACIONES = 92


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
        # **Una pasada cortada a mitad deja la cuenta viva, y da igual como la deje.** El 30 de
        # septiembre de 2026 esta condicion se quedo corta: pedia «tiene lista **con lineas**»,
        # y una pasada que se cayo despues de vaciar la lista dejaba la cuenta ahi -- el alta no
        # volvia a pasar (la pantalla ya no ofrecia «Créala»), la lista nueva salia con un
        # «(1)» detras porque el nombre estaba cogido, y dos comprobaciones se pusieron rojas
        # por la basura de la pasada anterior y no por el codigo. La cuenta de esta puerta es
        # desechable: **si hay sesion, se borra**.
        if pagina.get_by_label("Clave").count() == 0:
            borrado = pagina.evaluate(
                "async () => (await fetch('/api/yo', {method: 'DELETE',"
                " credentials: 'same-origin'})).status")
            print(f"   (la cuenta de la pasada anterior seguia ahi: se ha borrado, {borrado})")
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
        # La cantidad, **en los dos sentidos**: `+` sube a 2 y `−` la devuelve a 1. Solo se
        # medía el `+`, y bajar la cantidad es la mitad de «cambiar la cantidad» -- ademas de
        # ser el boton que se queda apagado en 1 (la API acepta 1..99 y un 422 por pulsar de
        # mas no es una forma de enterarse).
        def cantidad_de_la_primera() -> str:
            return pagina.locator("button[aria-label^='Más ']").first.locator(
                "xpath=..").inner_text()

        mas = pagina.locator("button[aria-label^='Más ']").first
        if mas.count():
            mas.click()
            comprueba(espera(lambda: "2" in cantidad_de_la_primera()),
                      "el boton de mas sube la cantidad")
            menos = pagina.locator("button[aria-label^='Menos ']").first
            if menos.count():
                menos.click()
                comprueba(espera(lambda: "1" in cantidad_de_la_primera()),
                          "y el de menos la baja (vuelve a 1)")
                comprueba(menos.is_disabled(),
                          "y en 1 se queda apagado, en vez de mandar un 422")
            else:
                comprueba(False, "no encuentro el boton de bajar la cantidad")
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

        # -------------------------------------- cerrar la compra (tarea 10) -----------------
        # **La mitad que le faltaba al bucle**: la lista sabia lo que falta y no lo que se
        # compro, asi que cada semana se empezaba de cero. Lo del carro se guarda como compra
        # (con su precio) y sale de la lista; **lo que no se cogio se queda**, que es lo que
        # hace que el boton sirva -- quien no encuentra el pan no quiere volver a apuntarlo.
        #
        # Se comprueba el viaje entero con dos cosas: una marcada (va al carro) y otra sin
        # marcar (se queda). Y se mira **lo que queda en la lista**, que es donde este boton no
        # puede fallar.
        # Se siembra **una linea marcada** (la que va al carro) y se deja la que ya habia **sin
        # marcar**, que es justo el caso que hay que comprobar: lo que no se cogio no se va.
        carga("/cesta")
        antes = lineas()
        sembrada = pagina.evaluate("""async () => {
          const listas = (await (await fetch('/api/listas', {credentials:'same-origin'})).json()).listas;
          const casa = listas.find((l) => l.es_de_casa) || listas[0];
          if (!casa) return null;
          const r = await fetch(`/api/listas/${casa.id}/lineas`, {method:'POST',
            credentials:'same-origin', headers:{'Content-Type':'application/json'},
            body: JSON.stringify({id: crypto.randomUUID(), nombre: 'PAN QUE SI ME LLEVO',
                                  grupo_id: null, producto_id: 'dia:74397'})});
          return r.ok ? casa.id : null;
        }""")
        carga("/cesta")
        comprueba(espera(lambda: lineas() == antes + 1),
                  f"la puerta deja dos cosas en la lista para poder cerrar ({antes} -> {lineas()})")
        casilla = pagina.get_by_role("checkbox", name=re.compile("PAN QUE SI ME LLEVO"))
        comprueba(casilla.count() == 1,
                  "y la sembrada se anuncia con su nombre (se puede marcar sin adivinar)")
        if casilla.count():
            casilla.first.click()
            comprueba(espera(lambda: pagina.locator("input[type=checkbox]:checked").count() == 1),
                      "se marca la que se lleva, y la otra se queda sin marcar")
        cerrar = pagina.get_by_role("button", name="He terminado la compra")
        comprueba(cerrar.count() == 1,
                  "y con algo en el carro sale el boton de cerrar la compra")
        if cerrar.count():
            cerrar.first.click()
            comprueba(espera(lambda: "¿Terminada?" in texto()),
                      "cerrar pregunta antes, y dice cuantas cosas van a salir")
            comprueba("No, déjalo" in texto(), "y se puede decir que no")
            no = pagina.get_by_role("button", name="No, déjalo")
            if no.count():
                no.first.click()
                comprueba(espera(lambda: "¿Terminada?" not in texto()),
                          "«No, déjalo» no cierra la compra, vuelve a dejar el boton")
            cerrar.first.click()
            pagina.get_by_role("button", name="Sí, he terminado").first.click()
            comprueba(espera(lambda: "Compra guardada" in texto()),
                      "cerrar la compra dice lo que ha pasado "
                      f"({[ln for ln in texto().splitlines() if 'Compra guardada' in ln][:1]})")
            comprueba(espera(lambda: lineas() == antes),
                      f"las del carro salen y lo demas se queda ({antes + 1} -> {lineas()})")
            comprueba(espera(lambda: "PAN QUE SI ME LLEVO" not in texto()),
                      "y la que iba en el carro ya no esta en la lista")
        # Y se deja la lista como estaba: fuera la linea sembrada, que ya salio al cerrar.
        if sembrada:
            pagina.evaluate("""async (lista) => {
              const detalle = await (await fetch(`/api/listas/${lista}`,
                {credentials:'same-origin'})).json();
              for (const ln of (detalle.lineas || []).filter((l) => l.nombre_visto.startsWith('PAN QUE SI'))) {
                await fetch(`/api/listas/${lista}/lineas/${ln.id}`, {method:'DELETE',
                  credentials:'same-origin'});
              }
            }""", sembrada)

        # ------------------------------------------- una linea que apunta a otro ---------
        # **El fallo mas caro de la aplicacion, y el mas silencioso.** El emparejador numera los
        # grupos en el orden en que aparecen los productos, asi que una pasada puede renumerarlos
        # y una linea guardada acaba apuntando a otra cosa: medido el 28 de septiembre de 2026,
        # **43 de las 54 lineas** de la lista de la cuenta de pruebas estaban asi, la leche salia
        # en el pasillo «Higiene y belleza» y la estimacion decia 298,71 EUR cuando lo contable
        # eran 10,56 (el resto era un pintalabios a 10,66 EUR/ud por linea). Aqui se siembra el
        # caso a mano -- una linea con el nombre de una cosa y el grupo de otra -- y se comprueba
        # que la pantalla **no la pinta con el pasillo ni con el precio de otro**.
        sembrada = pagina.evaluate("""async () => {
          const listas = (await (await fetch('/api/listas', {credentials: 'same-origin'})).json())
            .listas;
          const casa = listas.find((l) => l.es_de_casa) || listas[0];
          if (!casa) return null;
          const detalle = await (await fetch(`/api/listas/${casa.id}`,
            {credentials: 'same-origin'})).json();
          const mia = (detalle.lineas || []).find((l) => l.grupo_id != null);
          if (!mia) return null;
          const id = crypto.randomUUID();
          const r = await fetch(`/api/listas/${casa.id}/lineas`, {
            method: 'POST', credentials: 'same-origin',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({id, nombre: 'PINTALABIOS QUE NO ES DE ESTE GRUPO',
                                  grupo_id: mia.grupo_id, cantidad: 1})});
          return r.status === 201 ? id : null;
        }""")
        if sembrada:
            carga("/cesta")
            comprueba("ya no es el mismo en el catálogo" in texto(),
                      "una linea que apunta a otro producto lo dice, en vez de ponerle su "
                      "pasillo y su precio")
            comprueba("De " in texto() and "no tengo precio" in texto(),
                      "y no entra en la cuenta de lo que cuesta la lista")
            pagina.evaluate("""async (id) => {
              const listas = (await (await fetch('/api/listas',
                {credentials: 'same-origin'})).json()).listas;
              const casa = listas.find((l) => l.es_de_casa) || listas[0];
              await fetch(`/api/listas/${casa.id}/lineas/${id}`, {
                method: 'PATCH', credentials: 'same-origin',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({borrado: true})});
            }""", sembrada)
            pagina.wait_for_timeout(1500)
            carga("/cesta")
            comprueba("ya no es el mismo en el catálogo" not in texto(),
                      "y al quitarla la lista vuelve a estar como estaba")
        else:
            comprueba(False, "no he podido sembrar una linea con el grupo de otro producto")

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

        # ------------------------------------------- con el teclado y con lector --------
        print("\n== con el teclado, y lo que anuncia una casilla")
        # **Lo que no medía nadie.** Las puertas miden el dedo (44 px, contraste, que nada se
        # deslice) y el teclado no lo miraba ninguna: la aplicacion se usa tambien en el
        # ordenador -- desde el 28 de septiembre de 2026 la puerta de produccion mide la
        # pantalla ancha --, y un control al que no se llega con el tabulador no existe para
        # quien no usa el raton. Medido con `data/debug/teclado.py` antes de escribir esto: el
        # foco recorre los seis destinos, el desplegable y las lineas, y **se ve donde esta**.
        carga("/cesta")
        alcanzados = []
        for _ in range(24):
            pagina.keyboard.press("Tab")
            quien = pagina.evaluate("""() => {
              const a = document.activeElement;
              if (!a || a === document.body) return null;
              const e = getComputedStyle(a);
              return {etiqueta: a.tagName.toLowerCase(),
                      nombre: (a.getAttribute('aria-label') || a.innerText || '').trim(),
                      foco: (e.outlineStyle !== 'none' && e.outlineWidth !== '0px')
                            || e.boxShadow !== 'none'};
            }""")
            if quien:
                alcanzados.append(quien)
        sin_foco_visible = [a["nombre"][:30] for a in alcanzados if not a["foco"]]
        comprueba(len(alcanzados) >= 8 and not sin_foco_visible,
                  f"{len(alcanzados)} controles alcanzados con el tabulador, y todos dicen "
                  f"donde esta el foco (sin marca: {sin_foco_visible})")
        comprueba(any(a["etiqueta"] == "input" for a in alcanzados),
                  "y la casilla de una linea se alcanza con el tabulador")
        # **Lo que oye un lector de pantalla al llegar a la casilla.** Un `input` sin nombre se
        # anuncia «casilla, activada» y quien no ve la pantalla no sabe que esta tachando. El
        # nombre sale del `<label>` (`Casilla`), asi que se mira el nombre **accesible**, no el
        # `value` del input (que es «on» en todas).
        nombres = pagina.evaluate("""() => [...document.querySelectorAll('input[type=checkbox]')]
          .slice(0, 3).map((i) => (i.labels && i.labels[0] ? i.labels[0].innerText.trim() : ''))""")
        comprueba(bool(nombres) and all(len(n) > 2 for n in nombres),
                  f"cada casilla se anuncia con el nombre de su linea ({nombres})")
        # Y la tarea de verdad, sin dedo: se tacha con la barra espaciadora.
        antes_de_tachar = pagina.locator("input[type=checkbox]:checked").count()
        casilla = pagina.locator("input[type=checkbox]").first
        casilla.focus()
        pagina.keyboard.press("Space")
        comprueba(espera(lambda: pagina.locator(
            "input[type=checkbox]:checked").count() == antes_de_tachar + 1),
            "y una linea se tacha con la barra espaciadora")
        pagina.locator("input[type=checkbox]:checked").first.focus()
        pagina.keyboard.press("Space")
        espera(lambda: pagina.locator(
            "input[type=checkbox]:checked").count() == antes_de_tachar)

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
        comprueba("No sigues ningún producto" not in texto(),
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
            comprueba("No sigues ningún producto" in texto(),
                      "quitar el favorito deja la pantalla vacia")
        else:
            comprueba(False, "no hay boton de quitar el favorito")

        # ------------------------------- pasarlos TODOS de golpe --------------------------
        # **El boton que existe para montar la compra de la semana** («Añadir los N a la
        # lista», del 25 de septiembre de 2026: *"que sea facil anadir a una lista productos
        # que ya estan en favoritos"*) no lo pulsaba ninguna puerta. Hacen falta **dos**
        # favoritos, y se marcan desde la ficha de dos grupos distintos que salen de una
        # busqueda, que es el camino que hace una persona.
        carga("/buscar?q=leche+entera")
        grupos = pagina.evaluate("""() => [...document.querySelectorAll("main a[href^='/grupo/']")]
          .map((a) => a.getAttribute('href')).filter((h, i, t) => t.indexOf(h) === i).slice(0, 2)""")
        for ruta in grupos or []:
            carga(ruta)
            corazon = pagina.get_by_role("button", name="Guardar")
            if corazon.count():
                corazon.first.click()
                pagina.wait_for_timeout(1500)
        carga("/favoritos")
        todos = pagina.get_by_role("button", name=re.compile(r"^Añadir los \d+ a la lista$"))
        comprueba(todos.count() == 1 and len(grupos or []) == 2,
                  f"con {len(grupos or [])} favoritos sale el boton de pasarlos todos")
        if todos.count():
            carga("/cesta")
            antes_todos = lineas()
            carga("/favoritos")
            cuantos = int(re.search(r"(\d+)", todos.first.inner_text()).group(1))
            todos.first.click()
            comprueba(espera(lambda: "Añadidos" in texto() or "Añadido" in texto()),
                      "pasarlos todos lo dice")
            carga("/cesta")
            comprueba(lineas() == antes_todos + cuantos,
                      f"y quedan apuntados los {cuantos} ({antes_todos} -> {lineas()} lineas)")
        # ------------------- el orden, que es lo que la pantalla promete desde el primer dia ---
        # **Y no lo hacia.** El 30 de septiembre de 2026, leyendo el codigo contra su propia
        # documentacion: la pantalla decia «primero lo que ha cambiado» y la API devolvia los
        # favoritos en el orden en que se anadieron, con el precio de hoy y sin decir si habia
        # cambiado. Ahora el cambio lo mide `movimientos.cambios_de_grupos`.
        #
        # Se comprueba lo que promete **sin depender de que hoy haya bajado algo**: el sentido
        # de cada tarjeta esta en el DOM (`data-cambio`) y el orden tiene que ser bajadas,
        # subidas, igual; lo que no se puede comparar va despues, con su motivo.
        # Se marcan **uno que ha bajado y uno que ha subido**, y los elige la API en el momento
        # (hoy son unos productos y manana otros): sin eso, con dos favoritos que no se han
        # movido, la comprobacion del orden pasaria sin comprobar nada.
        elegidos = pagina.evaluate("""async () => {
            const coge = async (u) => (await (await fetch(u)).json()).resultados?.[0]?.grupo_id;
            const baja = await coge('/api/bajadas?dias=7&limite=1');
            const sube = await coge('/api/bajadas?dias=7&limite=1&subidas=true');
            for (const g of [baja, sube]) {
                if (g != null) await fetch('/api/favoritos', {
                    method: 'POST', headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({grupo_id: g})});
            }
            return {baja, sube};
        }""")
        print(f"   (marcados para el orden: ha bajado {elegidos.get('baja')}, "
              f"ha subido {elegidos.get('sube')})")
        carga("/favoritos")
        cuantos_favs = int((re.search(r"Añadir los (\d+) a la lista", texto()) or [0, 0])[1])
        sentidos = pagina.evaluate(
            "() => [...document.querySelectorAll('[data-cambio]')]"
            ".map((e) => e.getAttribute('data-cambio'))")
        rango = {"baja": 0, "sube": 1, "igual": 2}
        comprueba(sentidos == sorted(sentidos, key=lambda s: rango.get(s, 3))
                  and (bool(sentidos) or cuantos_favs == 0),
                  f"los favoritos van por lo que se han movido ({sentidos} de {cuantos_favs})")
        comprueba(elegidos.get("baja") is None or elegidos.get("sube") is None
                  or sentidos.index("baja") < sentidos.index("sube"),
                  f"y el que ha bajado va antes que el que ha subido ({sentidos})")
        dicen = sentidos + [t for t in pagina.locator("main").inner_text().split("\n")
                            if t.strip() in ("sin comparar", "ya no está")]
        comprueba(len(dicen) >= cuantos_favs,
                  f"cada favorito dice su cambio o por que no se puede "
                  f"({len(dicen)} de {cuantos_favs})")
        # Y la ventana: se puede cambiar, y cambiar se dice con palabras (no con una flecha).
        treinta = pagina.get_by_role("button", name="30 días")
        if treinta.count():
            treinta.first.click()
            comprueba(espera(lambda: "Ventana activa: 30 días" in texto()),
                      "cambiar la ventana se dice con palabras")
            pagina.get_by_role("button", name="7 días").first.click()
            comprueba(espera(lambda: "Ventana activa: 7 días" in texto()),
                      "y volver a siete dias, tambien")
        else:
            comprueba(False, "no encuentro el selector de ventana de los favoritos")

        # Y se dejan los favoritos como estaban: una pasada no puede dejar basura que la
        # siguiente tenga que adivinar.
        carga("/favoritos")
        for _ in range(6):
            quitar = pagina.get_by_role("button", name="Quitar")
            if not quitar.count():
                break
            quitar.first.click()
            pagina.wait_for_timeout(1500)
        carga("/favoritos")
        comprueba("No sigues ningún producto" in texto(),
                  "y quitarlos deja la pantalla de favoritos vacia")

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

        # --------------------------------------------------------- compartir -------------
        print("\n== compartir la lista: por su usuario, con sus dos caras")
        # **La otra via de compartir, la que no pasa por el enlace.** El enlace lo mide la
        # puerta del navegador con una segunda persona de verdad; esto es la tarjeta de
        # «Compartir con quien ya tiene cuenta», que hasta hoy no tocaba nadie.
        carga("/cesta")
        campo_usuario = pagina.get_by_label("Su usuario")
        comprueba(campo_usuario.count() == 1,
                  "quien creo la lista puede meter a alguien por su usuario")
        if campo_usuario.count():
            # Cara 1: un usuario que no existe. Un nombre de usuario se escribe mal con una
            # facilidad pasmosa, y callarse seria dejar creyendo que se ha compartido.
            campo_usuario.fill("no-existe-esta-persona-9271")
            pagina.get_by_role("button", name="Compartir").first.click()
            comprueba(espera(lambda: "No he podido compartirla" in texto()),
                      "un usuario que no existe lo dice, en vez de callarse")
            # Cara 2: uno que existe. **Se usa la propia cuenta de la prueba**: compartir con
            # un desconocido de verdad le meteria una lista ajena a alguien, y una puerta no
            # puede tocarle la compra a nadie.
            #
            # **Y esto encontro un fallo de verdad el 28 de septiembre de 2026**: compartir
            # contigo mismo te cambiaba el papel a `escribe`, la lista dejaba de ser tuya (403
            # al invitar y al borrarla) y la tarjeta de Compartir desaparecia de la pantalla --
            # sin forma de volver. Ahora la base no deja bajar al dueno de su papel, y la
            # pantalla dice que no hacia falta compartirla.
            campo_usuario.fill(USUARIO)
            pagina.get_by_role("button", name="Compartir").first.click()
            comprueba(espera(lambda: "ya es tuya" in texto()),
                      "compartir contigo mismo dice que la lista ya es tuya")
            captura("compartir-contigo-mismo")
            carga("/cesta")
            comprueba(pagina.get_by_label("Su usuario").count() == 1
                      and "Compartir" in texto(),
                      "y la lista sigue siendo tuya: la tarjeta de compartir sigue ahi")
            comprueba("Quién está dentro" in texto(),
                      "y la lista de quien esta dentro sigue ahi, con su papel")

        # ------------------------------------------------------------ el buscador -----
        print("\n== el buscador: filtros, orden, vistas guardadas, recientes")
        carga("/buscar?q=leche+entera")
        # **El orden, que no lo media nadie.** El control dice en que orden esta puesto, y
        # pulsar el que ya esta puesto le da la vuelta. Se comprueba lo unico que no se puede
        # fingir: que la lista cambia de orden, y que el sentido que dice es el que hace.
        def orden_de_los_resultados() -> list[str]:
            return pagina.evaluate(
                "() => [...document.querySelectorAll(\"main a[href^='/grupo/']\")]"
                ".map((a) => a.getAttribute('href'))")

        def precios_visibles() -> list[int]:
            """Los precios de los resultados, **en el orden en que se ven**, en centimos.

            Se leen del DOM, que es donde se juzga un numero. En 390 px cada resultado es una
            tarjeta y el precio vive en un `span.cifra` que **no** esta dentro del enlace del
            nombre -- esta en la otra columna de la tarjeta --, asi que se leen todos en orden
            de documento, que es el orden de las tarjetas. Se descartan «ahorras un 74 %» y los
            €/kg, que llevan la misma clase: medido el 29 de septiembre de 2026, en `main` hay
            117 elementos con la clase `cifra` y solo uno por tarjeta es un precio de venta.
            """
            dichos = pagina.evaluate(
                "() => [...document.querySelectorAll('main span.cifra')]"
                ".map((e) => e.innerText || '')")
            salida = []
            for dicho in dichos:
                m = re.fullmatch(r"\s*(\d+),(\d{2})\s*€\s*", dicho.replace("\xa0", " "))
                if m:
                    salida.append(int(m.group(1)) * 100 + int(m.group(2)))
            return salida

        if pagina.get_by_role("button", name="Ordenar por").count() or pagina.get_by_text(
                "Ordenar por").count():
            antes_del_orden = orden_de_los_resultados()

            def abre_el_orden() -> None:
                """Abre el desplegable **solo si esta cerrado**.

                Pulsar el resumen cuando ya esta abierto lo **cierra**: la segunda vuelta del
                orden se quedo esperando un boton que acababa de esconder, y la pasada se corto
                ahi (28 de septiembre de 2026).
                """
                if pagina.get_by_role("button", name=re.compile(r"^Precio")).count() == 0:
                    pagina.get_by_text("Ordenar por").first.click()
                    pagina.wait_for_timeout(800)

            abre_el_orden()
            precio = pagina.get_by_role("button", name=re.compile(r"^Precio"))
            if precio.count():
                precio.first.click()
                pagina.wait_for_timeout(2500)
                arriba = orden_de_los_resultados()
                precios_arriba = precios_visibles()
                resumen = texto()
                comprueba(arriba and arriba != antes_del_orden,
                          "ordenar por precio cambia el orden de los resultados")
                comprueba("de menor a mayor" in resumen,
                          "y el control dice el sentido con palabras, no con una flecha")
                # Volver a pulsarlo le da la vuelta (el desplegable sigue abierto).
                abre_el_orden()
                pagina.get_by_role("button", name=re.compile(r"^Precio")).first.click()
                pagina.wait_for_timeout(2500)
                abajo = orden_de_los_resultados()
                precios_abajo = precios_visibles()
                comprueba("de mayor a menor" in texto(),
                          "pulsarlo otra vez le da la vuelta al sentido")
                # **Y el orden es de verdad**: el primero de uno es el ultimo del otro.
                #
                # Se comparan **los precios**, no los identificadores, y esto tiene fecha:
                # el 29 de septiembre de 2026 esta comprobacion salio roja con la aplicacion
                # bien. El precio mas bajo de «leche entera» eran 94 centimos y lo tenian
                # **dos** grupos (15692 y 23164), asi que el de menor a mayor empezaba por
                # uno y el de mayor a menor terminaba por el otro. Con un minimo empatado,
                # pedir el mismo id es pedir un orden que no existe; lo que si se promete en
                # pantalla es que el primero de un sentido y el ultimo del otro cuestan lo
                # mismo, y que ese es el precio mas bajo de los que se ven.
                #
                # Y se exige que haya **un precio por resultado**: si la pantalla se dejara
                # alguno sin pintar, los dos extremos podrian coincidir por casualidad.
                cuadran = (len(precios_arriba) == len(arriba) == len(abajo) == len(precios_abajo))
                comprueba(bool(precios_arriba and precios_abajo) and cuadran
                          and precios_arriba[0] == precios_abajo[-1]
                          and precios_arriba[0] == min(precios_arriba),
                          f"el mas barato encabeza un orden y cierra el otro "
                          f"({precios_arriba[0] if precios_arriba else '?'} centimos arriba / "
                          f"{precios_abajo[-1] if precios_abajo else '?'} centimos abajo, "
                          f"el mas bajo de {len(precios_arriba)}; "
                          f"precios {len(precios_arriba)}/{len(arriba)} y "
                          f"{len(precios_abajo)}/{len(abajo)} resultados)")
            else:
                comprueba(False, "no encuentro el boton de ordenar por precio")
        else:
            comprueba(False, "no encuentro el control de ordenar")
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
        # Y quitarlas todas de una vez: el boton **solo sale cuando hay alguna marcada**, asi
        # que este es el momento de medirlo (y si el de arriba no ha marcado nada, no se mide
        # y se dice, en vez de dar por bueno un boton que no estaba).
        quitar_todas = pagina.get_by_role("button", name="Quitar todas")
        if quitar_todas.count():
            quitar_todas.first.click()
            pagina.wait_for_timeout(2500)
            carga("/ajustes")
            marcadas = pagina.locator("button[aria-pressed='true']").count()
            comprueba(marcadas == 0 and "Quitar todas" not in texto(),
                      f"«Quitar todas» deja las cadenas sin marcar ({marcadas})")
        else:
            print("   (no hay cadenas marcadas: «Quitar todas» no se pinta, y eso es correcto)")
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

        # ---------------------------------------------------- el panel entero ------------
        print("\n== el panel entero: las diez pestanas, una por una")
        # **Faltaban seis.** Las puertas median `bajadas`, `indice`, `posicion` y `dudosas`;
        # `hoy`, `donde`, `cadenas`, `marcas`, `historico` y `movidos` no los abria nadie --
        # seis pantallas que existen y que nadie habia visto contestar con el navegador.
        # Se pulsan **las pestanas**, no se navega por la direccion: es lo que hace una
        # persona, y de paso se mide que la barra de pestanas lleve a donde dice.
        PESTANAS = (
            ("Hoy", "La ingesta de hoy"),
            ("Dónde comprar", "Dónde hacer la compra"),
            ("Cadenas", "Quién gana y cuánto se mueve"),
            ("Marcas", "Marca propia contra marca"),
            ("Histórico", "guardado"),
            ("Movidos", "Lo que se ha movido hoy"),
            ("Bajadas", "bajado"),
            ("Índice", "El nivel de precios de cada cadena"),
            ("Posición", "En qué es cara cada cadena"),
            ("Ofertas dudosas", "conviene mirar dos veces"),
        )
        carga("/panel")
        for nombre, tiene_que_decir in PESTANAS:
            pestana = pagina.get_by_role("tab", name=nombre, exact=True)
            if not pestana.count():
                comprueba(False, f"no encuentro la pestana «{nombre}» del panel")
                continue
            pestana.first.click()
            # Se espera al texto y no a un tiempo fijo: estos paneles piden a la API y pintan
            # cientos de filas, asi que leer antes del final mide «Cargando…».
            visto = espera(lambda que=tiene_que_decir: que in texto(), 20.0)
            comprueba(visto and "No he podido" not in texto(),
                      f"la pestana «{nombre}» contesta ({tiene_que_decir!r})")
        captura("panel-hoy")

        # **Un dato que viajaba y no lo pintaba nadie.** `dias_del_salto` viene en `/api/indice`
        # desde el primer dia (los dias que cubre cada eslabon del indice encadenado) y la pantalla
        # no lo decia: el dibujo hacia como si hubiera visto todos los dias. Medido el 28 de
        # septiembre de 2026: **cinco eslabones** de 2 y 3 dias (Alcampo el 13 y el 23, Carrefour
        # el 13, el 19 y el 23). La comprobacion **compara la pantalla con la API**, que es lo
        # unico que no se puede fingir: si la API tiene saltos, la pantalla lo dice; y si no los
        # tiene, no se inventa un aviso.
        saltos = pagina.evaluate("""async () => {
          const d = await (await fetch('/api/indice', {credentials: 'same-origin'})).json();
          return (d.series || []).flatMap((s) => s.puntos || [])
            .filter((p) => (p.dias_del_salto || 1) > 1).length;
        }""")
        carga("/panel?pestana=indice")
        # **Se espera al texto, no a un tiempo fijo.** Esta pestana pide `/api/indice`, que
        # recorre el historico: la primera peticion despues de arrancar el contenedor tarda
        # segundos (hay que montar la copia de gold), y leer antes daba un FALLO con la pantalla
        # bien -- paso el 28 de septiembre de 2026, con «5 eslabones en la API y la pantalla no
        # lo dice». Solo se espera si hay algo que esperar.
        if saltos:
            espera(lambda: "más de un día" in texto(), 25.0)
        lo_dice = "más de un día" in texto()
        comprueba((saltos == 0 and not lo_dice) or (saltos > 0 and lo_dice),
                  f"el indice dice los eslabones que cubren mas de un dia ({saltos} en la API, "
                  f"y la pantalla {'lo dice' if lo_dice else 'no lo dice'})")
        captura("panel-indice")

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

        # ------------------------------------------------- lo que se despliega --------
        print("\n== lo que se despliega: que se note que se despliega")
        # **Esto lo encontro mirar una captura, no leer el codigo.** El marcador nativo del
        # `<summary>` desaparece en cuanto se le pone `display: flex` (que hace falta para que
        # mida 44 px), asi que los diez desplegables de la aplicacion eran texto suelto: en la
        # cabecera, «Estado de las cadenas» parecia un encabezado sin nada debajo, y la caja de
        # filtros del buscador parecia un segundo campo de texto. Ahora todos usan `Resumen`
        # (`componentes/ui.tsx`) y llevan su flecha, que gira al abrirse.
        F = """() => [...document.querySelectorAll('summary')].map((s) => {
          const f = s.querySelector('.flecha')
          return {
            texto: (s.innerText || '').slice(0, 40),
            flecha: f ? getComputedStyle(f).transform : null,
            abierto: s.parentElement.open,
            alto: Math.round(s.getBoundingClientRect().height),
          }
        })"""
        for ruta in ("/", "/buscar?q=leche%20entera", "/panel/matching"):
            carga(ruta)
            resumenes = pagina.evaluate(F)
            sin_flecha = [r["texto"] for r in resumenes if r["flecha"] is None]
            bajos = [r["texto"] for r in resumenes if r["alto"] < 44]
            comprueba(bool(resumenes) and not sin_flecha and not bajos,
                      f"{ruta}: los {len(resumenes)} desplegables llevan su flecha y miden 44 px "
                      f"(sin flecha: {sin_flecha}, bajos: {bajos})")
        # Y la flecha dice en que estado esta: cerrada, sin girar; abierta, girada.
        carga("/")
        cerrada = pagina.evaluate(F)
        pagina.locator("summary").first.click()
        pagina.wait_for_timeout(1200)
        abierta = pagina.evaluate(F)
        giro = abierta[0]["flecha"] if abierta else None
        comprueba(cerrada and cerrada[0]["flecha"] not in (None, giro)
                  and abierta and abierta[0]["abierto"],
                  f"la flecha gira al abrirse ({cerrada[0]['flecha'] if cerrada else '?'} -> {giro})")
        captura("desplegable-abierto")

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

        # ------------------------------------------- la baja, desde la pantalla ---------
        print("\n== darme de baja, desde la pantalla")
        # **La unica operacion que no se puede deshacer, y la unica que se hacia por detras.**
        # Hasta hoy esta puerta borraba su cuenta con un `fetch` a `DELETE /api/yo`: medía la
        # API, no la pantalla. Y la pantalla tiene una decision que hay que medir -- no basta
        # con un «¿seguro?», hay que **escribir tu propio usuario** --, que es justo lo que
        # este proyecto cambio respecto a la interfaz vieja (`app.js:1571-1603`).
        carga("/ajustes")
        abrir_baja = pagina.get_by_role("button", name="Quiero darme de baja")
        comprueba(abrir_baja.count() == 1, "los ajustes tienen la puerta de salida")
        if abrir_baja.count():
            abrir_baja.first.click()
            pagina.wait_for_timeout(1200)
            confirmar = pagina.get_by_role("button", name="Darme de baja")
            comprueba(confirmar.count() == 1 and confirmar.first.is_disabled(),
                      "sin escribir tu usuario, el boton de la baja esta apagado")
            campo_baja = pagina.get_by_label(f"Escribe {USUARIO} para confirmarlo")
            comprueba(campo_baja.count() == 1,
                      "y la confirmacion pide escribir tu propio usuario, no un «si»")
            if campo_baja.count():
                campo_baja.fill("otra-cosa")
                pagina.wait_for_timeout(800)
                comprueba(pagina.get_by_role(
                    "button", name="Darme de baja").first.is_disabled(),
                    "con otro nombre sigue apagado")
                # Y se puede uno arrepentir antes de escribirlo.
                dejalo = pagina.get_by_role("button", name="No, déjalo")
                if dejalo.count():
                    dejalo.first.click()
                    pagina.wait_for_timeout(1000)
                    comprueba(pagina.get_by_role(
                        "button", name="Quiero darme de baja").count() == 1,
                        "«No, déjalo» vuelve a dejarlo como estaba")
                    pagina.get_by_role("button", name="Quiero darme de baja").first.click()
                    pagina.wait_for_timeout(1200)
                campo_baja = pagina.get_by_label(f"Escribe {USUARIO} para confirmarlo")
                campo_baja.fill(USUARIO)
                pagina.wait_for_timeout(800)
                comprueba(not pagina.get_by_role(
                    "button", name="Darme de baja").first.is_disabled(),
                    "con el tuyo se enciende")
                pagina.get_by_role("button", name="Darme de baja").first.click()
                with contextlib.suppress(Exception):
                    pagina.get_by_label("Clave").first.wait_for(timeout=25000)
                carga("/cesta")
                comprueba(pagina.get_by_label("Clave").count() == 1,
                          "la baja deja la aplicacion pidiendo entrar")
                quedan = pagina.evaluate(
                    "async () => (await (await fetch('/api/yo',"
                    " {credentials: 'same-origin'})).json()).usuario")
                comprueba(quedan is None,
                          f"y la cuenta no esta: la API ya no la conoce ({quedan!r})")
        # Red de seguridad: si la pantalla no ha podido (o el paso de arriba ha fallado a
        # medias), la cuenta se borra igual. La base de casa no se queda con basura de una
        # prueba, y una pasada cortada dejaria la cuenta para la siguiente.
        if pagina.evaluate(
                "async () => (await (await fetch('/api/yo',"
                " {credentials: 'same-origin'})).json()).usuario") is not None:
            borrado = pagina.evaluate(
                "async () => (await fetch('/api/yo', {method: 'DELETE',"
                " credentials: 'same-origin'})).status")
            print(f"   (la baja por la pantalla no la dejo limpia: se borra por la API, {borrado})")

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
        if HECHAS != COMPROBACIONES:
            # No es un fallo de la aplicacion: es que este numero se cita en los documentos.
            print(f"\n   La pasada ha hecho **{HECHAS}** comprobaciones y lo escrito son "
                  f"{COMPROBACIONES}.\n   Actualiza `COMPROBACIONES` aqui, `docs/OPERACION.md` "
                  f"y `.stitch/DESIGN.md`\n   en el mismo cambio: si no, los documentos dicen "
                  f"una cosa y la puerta hace otra.")
            return 1
        print("\n   TODAS LAS FUNCIONES CONTESTAN.")
        ctx.close()
        navegador.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
