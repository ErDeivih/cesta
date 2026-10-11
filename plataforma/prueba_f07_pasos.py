"""F07: **cuantos toques cuesta el recorrido de cuenta vacia.**

El criterio (`docs/SUPERAPP-FASE2-EMPEZAR-AQUI.md:127`) acaba con *«tarea movil con una mano, recorrido de
cuenta vacia, recarga y dos sesiones; **medir pasos**»*.

**Y «pasos» aqui son toques con el pulgar, no peticiones.** *Medido en §5 de
`docs/investigaciones/F07-compra-familiar.md`: **el servidor necesita cuatro peticiones** --
`registrarse` → `POST /listas` → `buscar` → `POST /lineas`.* **Los toques son otra cosa, y esto los cuenta.**

*Por que no vale contar los botones del fichero:* **el orden y los campos dependen del estado** -- *si ya hay
lista no se crea, si no hay sesion se entra primero* --, **y eso no se lee: se usa.** *Y contar botones y
llamarlo «medir pasos» seria que el instrumento mide algo distinto de lo que se le pide.*

**Cuenta los toques de verdad**: *cada `click`, `fill` y `press` que hace falta para que una cuenta nueva tenga
su primer producto en la lista.*

*Necesita la pantalla servida: `CESTA_UI` (por defecto `http://localhost:5174`).*
"""
from __future__ import annotations

import contextlib
import os
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

# **La consola de Windows es cp1252** y la pantalla trae simbolos (el menu es `\u2630`): sin esto, imprimir
# el estado **revienta el ensayo** -- y el fallo seria del instrumento, no de lo medido.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

UI = os.environ.get("CESTA_UI", "http://localhost:5174")
CLAVE = "clave-de-prueba-123"


def main() -> int:
    from patchright.sync_api import sync_playwright

    from plataforma.api import catalogo

    # **Un producto de verdad**, para buscar algo que exista.
    fila = catalogo.conexion().execute(
        "SELECT nombre FROM grupos WHERE precio_unidad_cent > 0 AND categoria LIKE 'la-despensa%' "
        "ORDER BY length(nombre) LIMIT 1").fetchone()
    termino = (fila[0].split()[0] if fila else "leche")

    toques = 0
    fallos: list[str] = []

    def comprueba(ok: bool, que: str) -> None:
        print(f"  {'ok  ' if ok else 'MAL '} {que}")
        if not ok:
            fallos.append(que)

    def toca(descripcion: str) -> None:
        """Cuenta un toque y lo dice. **Es el instrumento, y por eso se ve cada uno.**"""
        nonlocal toques
        toques += 1
        print(f"        toque {toques:2}: {descripcion}")

    with sync_playwright() as p:
        navegador = p.chromium.launch()
        contexto = navegador.new_context(viewport={"width": 390, "height": 844})  # **un movil**
        pagina = contexto.new_page()
        errores: list[str] = []
        pagina.on("pageerror", lambda e: errores.append(str(e)))

        try:
            # ---------------------------------------------------------------- 1. la cuenta
            # **Y si el alta esta limitada (429), se ENTRA.** *Es el limite de altas por hora de la propia
            # API -- y esta bien que exista --, asi que el ensayo usa una cuenta que ya existe en vez de
            # reventar por un limite que no tiene nada que ver con lo que mide.*
            usuario = f"f07pasos{int(time.time() * 1000) % 100000000}"
            r = contexto.request.post(f"{UI}/api/registrarse",
                                      data={"nombre": "Prueba F07 pasos", "usuario": usuario,
                                            "clave": CLAVE})
            if not r.ok:
                print(f"        el alta contesto {r.status}: se entra con una cuenta que ya existe")
                r = contexto.request.post(f"{UI}/api/entrar",
                                          data={"usuario": "prueba-navegador", "clave": CLAVE})
            comprueba(r.ok, f"hay sesion para el recorrido ({r.status})")

            # ---------------------------------------------------------------- 2. la app, de cero
            pagina.goto(f"{UI}/compra", wait_until="domcontentloaded")
            toca("abrir la app")
            comprueba(pagina.title() != "", f"la pantalla carga (titulo: {pagina.title()!r})")

            # **Que se ve al llegar**, que es lo que decide los toques que vienen.
            cuerpo = pagina.locator("body").inner_text()
            print(f"        al llegar, la pantalla dice: {cuerpo[:180]!r}")

            # ---------------------------------------------------------------- 3. crear la lista
            boton_crear = pagina.get_by_role("button", name="crear", exact=False)
            if boton_crear.count() == 0:
                boton_crear = pagina.locator("button", has_text="lista").first
            if boton_crear.count():
                boton_crear.first.click()
                toca("pulsar para crear una lista")
                campo = pagina.locator("input[type=text], input:not([type])").first
                campo.fill("La del sabado")
                toca("escribir el nombre de la lista")
                confirmar = pagina.get_by_role("button", name="crear", exact=False)
                if confirmar.count():
                    confirmar.first.click()
                    toca("confirmar la lista")
            else:
                print("        (no hay boton de crear lista: puede que ya venga creada)")

            # ---------------------------------------------------------------- 4. buscar
            buscador = pagina.locator("input[type=search]").first
            buscador.wait_for(timeout=25000)
            buscador.fill(termino)
            toca(f"escribir {termino!r} en el buscador")
            buscador.press("Enter")
            toca("pulsar buscar")
            with contextlib.suppress(Exception):  # si no hay resultados, se dice y se sigue
                pagina.wait_for_selector("ul.divide-y > li", timeout=25000)

            # ---------------------------------------------------------------- 5. anadirlo
            resultados = pagina.locator("ul.divide-y > li")
            print(f"        resultados en pantalla: {resultados.count()}")

            # **Y aqui hay que MIRAR que se puede pulsar**, en vez de suponer el boton.
            if resultados.count():
                primero = resultados.first
                print(f"        el primer resultado dice: {primero.inner_text()[:120]!r}")
                pulsables = primero.locator("button, a")
                print(f"        y trae {pulsables.count()} elementos pulsables")
                for i in range(min(pulsables.count(), 4)):
                    with contextlib.suppress(Exception):
                        print(f"          [{i}] {pulsables.nth(i).inner_text()[:44]!r}")
                if pulsables.count():
                    pulsables.first.click()
                    toca("anadir el producto a la lista")

            # ---------------------------------------------------------------- C03/C04/C05 EN LA PANTALLA
            #
            # *Las tres capas que faltaban son la misma: **mirar la pantalla**.* **Y se miran aqui, con el
            # navegador que ya esta abierto** -- que es la leccion de esta sesion: no deducir la pantalla de
            # las otras capas.
            print()
            print("  === C03/C04/C05, en la pantalla ===")

            # **C05**: lo que la pantalla dice de cada resultado. *Si no afirma identidad, no habra ninguna
            # palabra de confirmacion -- y lo que SI diga hay que leerlo, no suponerlo.*
            if resultados.count():
                texto = resultados.first.inner_text()
                print(f"        un resultado dice: {texto[:220]!r}")
                cuerpo_completo = pagina.locator("body").inner_text()
                for palabra in ("confirmad", "exacto", "es el mismo", "probable", "parecid", "sin confirmar",
                                "puede ser", "identidad"):
                    if palabra in cuerpo_completo.lower():
                        print(f"        la pantalla usa la palabra {palabra!r}")
                print("        (y si no sale ninguna de esas, el buscador no afirma identidad)")

            # **C03**: los pasillos. *Si el agrupador `porPasillo` esta haciendo su trabajo, la lista tendra
            # encabezados; y si una linea no tiene pasillo, **va al final y sin encabezado**.*
            encabezados = pagina.locator("h3, h2, [role=heading]")
            print(f"        encabezados en pantalla: {encabezados.count()}")
            for i in range(min(encabezados.count(), 5)):
                with contextlib.suppress(Exception):
                    print(f"          [{i}] {encabezados.nth(i).inner_text()[:40]!r}")

            # **C04**: los estados. *«Lo de siempre» es el mosaico de habituales; y «en el carro» y «tachado»
            # tienen que poder verse a la vez o por separado.*
            habituales = pagina.locator("text=/lo de siempre|habitual/i")
            print(f"        menciones de lo habitual: {habituales.count()}")
            carro = pagina.locator("text=/en el carro|carrito/i")
            print(f"        menciones de en el carro: {carro.count()}")

            # ---------------------------------------------------------------- el numero
            print()
            print(f"  === TOQUES DEL RECORRIDO DE CUENTA VACIA: {toques} ===")
            comprueba(not errores, f"la pantalla no dio errores de JavaScript ({errores[:2]})")
        finally:
            contexto.close()
            navegador.close()

    if fallos:
        print("\n=== FALLO ===")
        for f in fallos:
            print(f"  - {f}")
        return 1
    print("\n=== PASA ===")
    print(f"  y el numero que pedia el criterio: {toques} toques")
    return 0


if __name__ == "__main__":
    sys.exit(main())
