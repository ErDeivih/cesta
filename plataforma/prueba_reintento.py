"""F02: **el reintento del diario, en un navegador de verdad.**

Por que existe
--------------
F02 lo pide con estas palabras: *«Mantener la operacion pendiente y su payload hasta recibir resultado
inequivoco o cancelacion explicita. **Simular servidor que guarda pero pierde la respuesta; pulsar otra
vez no duplica.**»* **Y la revision avisa de lo que no vale**: *«la prueba de mismo UUID por HTTP no
cubre la UX»*.

Asi que esto no prueba el modulo: prueba **lo que pasa en la pantalla**. Se intercepta la respuesta del
alta despues de que el servidor la haya procesado -- con `route.fetch()` la peticion **llega** y la
entrada **se guarda**; con `route.abort()` el navegador **ve un fallo** -- y despues se pulsa otra vez.

**Lo que se mide, y son tres cosas distintas:**

1. que el primer envio **si guardo** (la respuesta es lo que se perdio, no la entrada);
2. que los dos envios llevan **la misma clave de operacion** -- *que es el mecanismo*;
3. que el dia acaba con **una entrada, no dos** -- *que es lo que la persona ve*.

Como se corre
-------------
Necesita la API y la interfaz levantadas, y **la interfaz sirviendo el codigo de hoy**:

    docker run --rm -d --name cesta-prueba-db -e POSTGRES_PASSWORD=prueba \\
        -e POSTGRES_USER=cesta -e POSTGRES_DB=cesta -p 127.0.0.1:5434:5432 postgres:16-alpine
    $env:CESTA_POSTGRES='postgresql://cesta:prueba@127.0.0.1:5434/cesta'
    uv run uvicorn plataforma.api.main:app --host 127.0.0.1 --port 8099
    cd plataforma/web/app; $env:CESTA_API='http://127.0.0.1:8099'; npm run dev
    uv run python -m plataforma.prueba_reintento

*Los datos son de la base desechable y de una cuenta de prueba.* **No toca el diario de casa.**
"""
from __future__ import annotations

import contextlib
import json
import os
import re
import sys
import time
from datetime import date

from patchright.sync_api import sync_playwright

BASE = os.environ.get("CESTA_UI", "http://localhost:5173")
CLAVE = "clave-de-prueba-123"
FALLOS: list[str] = []


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    def comprueba(condicion: bool, queja: str) -> None:
        if condicion:
            print(f"  ok    {queja}")
        else:
            print(f"  FALLA {queja}")
            FALLOS.append(queja)

    with sync_playwright() as pw:
        navegador = pw.chromium.launch(headless=True)
        contexto = navegador.new_context(
            viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True, locale="es-ES",
        )
        pagina = contexto.new_page()

        # --- la cuenta, por la API y con la sesion del propio contexto -----------------------
        usuario = "prueba-navegador"
        r = contexto.request.post(f"{BASE}/api/entrar", data={"usuario": usuario, "clave": CLAVE})
        if not r.ok:
            usuario = f"reintento{int(time.time() * 1000) % 100000000}"
            r = contexto.request.post(f"{BASE}/api/registrarse",
                                      data={"nombre": "Prueba reintento", "usuario": usuario,
                                            "clave": CLAVE})
        comprueba(r.ok, f"hay sesion con {usuario} ({r.status})")
        if not r.ok:
            return 1

        hoy = date.today().isoformat()

        def cuantas() -> int:
            """Las entradas del dia, **por la API y con la sesion del navegador**."""
            respuesta = contexto.request.get(f"{BASE}/api/diario/{hoy}")
            if not respuesta.ok:
                return -1
            return len(respuesta.json().get("entradas") or [])

        # --- la pantalla del diario ---------------------------------------------------------
        pagina.goto(f"{BASE}/calorias", wait_until="domcontentloaded")
        pagina.wait_for_selector("text=Que has comido", timeout=25000)
        # **`exact=True` no es cosmetico**: «Ver que se puede **anotar**» tambien contiene «anotar», y
        # la coincidencia por defecto es por subcadena -- el localizador resolvia a dos botones.
        boton = pagina.get_by_role("button", name="Anotar", exact=True)
        print("\n== el diario, en un navegador de verdad")

        # **Los cuerpos de las peticiones**, para poder comparar las claves.
        claves: list[str | None] = []

        def apunta(peticion) -> None:
            if peticion.method == "POST" and peticion.url.split("?")[0].endswith("/api/diario"):
                with contextlib.suppress(Exception):
                    claves.append((json.loads(peticion.post_data or "{}")
                                   or {}).get("clave_operacion"))

        pagina.on("request", apunta)

        antes = cuantas()
        comprueba(antes >= 0, f"se lee el dia ({antes} entradas antes)")

        # **Una comida que se distingue**, para no confundirla con lo que ya hubiera.
        nombre = f"Prueba de reintento {int(time.time()) % 100000}"
        pagina.get_by_label(re.compile("Que has comido")).fill(nombre)
        pagina.get_by_label(re.compile("kcal")).fill("111")

        # --- el servidor que guarda y pierde la respuesta ------------------------------------
        perdidas = {"n": 0}

        def pierde_la_respuesta(route) -> None:
            # `fetch()` manda la peticion AL SERVIDOR: la entrada se guarda.
            route.fetch()
            perdidas["n"] += 1
            # Y `abort()` hace que el navegador vea un fallo: la respuesta se ha perdido.
            route.abort()

        pagina.route("**/api/diario", pierde_la_respuesta)
        boton.click()
        # Se espera a que la mutacion termine: el boton vuelve a decir «Anotar».
        with contextlib.suppress(Exception):
            pagina.wait_for_function(
                "() => [...document.querySelectorAll('button')]"
                ".some(b => b.textContent.trim() === 'Anotar')", timeout=20000)
        time.sleep(1.0)

        durante = cuantas()
        comprueba(perdidas["n"] == 1, "se interrumpio una respuesta, ni mas ni menos")
        comprueba(durante == antes + 1,
                  f"**el primer envio SI guardo** (la respuesta es lo que se perdio): "
                  f"{antes} -> {durante}")

        # **Y el reintento**, ya sin interceptar: la respuesta llega.
        pagina.unroute("**/api/diario")
        comprueba(boton.is_enabled(),
                  "el boton vuelve a estar activo: el reintento es posible")
        boton.click()
        with contextlib.suppress(Exception):
            pagina.wait_for_function(
                "() => [...document.querySelectorAll('button')]"
                ".some(b => b.textContent.trim() === 'Anotar')", timeout=20000)
        time.sleep(1.5)
        despues = cuantas()

        # --- las tres comprobaciones --------------------------------------------------------
        print("\n== lo que se ha medido")
        comprueba(len(claves) >= 2, f"hubo dos envios del alta ({len(claves)})")
        if len(claves) >= 2:
            comprueba(bool(claves[0]), "la clave no viaja vacia")
            comprueba(claves[0] == claves[1],
                      "**los dos envios llevan la MISMA clave**: el reintento es la misma operacion")
        comprueba(despues == antes + 1,
                  f"**y el dia acaba con UNA entrada, no dos**: {antes} -> {despues}")

        cuerpo = pagina.inner_text("body")
        comprueba(nombre in cuerpo, "y la comida se ve en la pantalla del dia")

        contexto.close()
        navegador.close()

    print()
    if FALLOS:
        print(f"  {len(FALLOS)} fallo(s):")
        for f in FALLOS:
            print(f"   - {f}")
        return 1
    print("  el reintento del diario: la misma clave, y una sola entrada.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
