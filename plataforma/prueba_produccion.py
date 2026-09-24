"""La interfaz **servida de verdad por Caddy**, en el 8080, despues de desplegar.

Por que existe, y en que se diferencia de `prueba_navegador.py`
--------------------------------------------------------------
`plataforma/prueba_navegador.py` mide la interfaz en el **servidor de desarrollo**
(`localhost:5173`, con el proxy de Vite) y contra un PostgreSQL de pruebas. Eso
comprueba la aplicacion; **no comprueba lo que se sirve**. Lo que se sirve es otra cosa:

    el paquete compilado (`web/dist`), no el codigo fuente
    las cabeceras de Caddy, incluido el **CSP** (`script-src 'self'`, `style-src 'self'`),
      que en el servidor de desarrollo no existe
    el proxy `/api` de Caddy, no el de Vite
    la base de datos de casa, no una de pruebas

El 24 de septiembre de 2026, el dia que se cambio el montaje a `web/dist`, esta
diferencia se pago dos veces: la API del contenedor contesto **500** a `/api/ofertas-dudosas`
porque un import perezoso de `core.derive` si se llamaba (y polars no esta en su imagen), y
el navegador de la puerta no lo vio porque corria contra el uvicorn del PC, donde polars si
esta. Un `TODO BIEN` en desarrollo con la produccion rota es exactamente lo que esta prueba
existe para no volver a firmar.

Como se corre
-------------
Con la plataforma levantada (`docker compose up -d`) y **despues** de desplegar:

    uv run python -m plataforma.prueba_produccion

Crea una cuenta de prueba (`prueba-produccion`), recorre lo que hay que mirar y **la borra
al final** con `DELETE /api/yo`: la base de casa no se queda con basura de una prueba. Si
una pasada se corta a medias, la siguiente entra en vez de crearla.

Lo que NO hace: no sustituye a la puerta del navegador (esa mide las cuatro preguntas, los
44 px, el contraste y la cola sin cobertura, pantalla a pantalla) ni a `docs/PRUEBA-15-SEGUNDOS.md`
(que es una persona con un movil).
"""
from __future__ import annotations

import contextlib
import os
import sys

BASE = os.environ.get("CESTA_PRODUCCION", "http://127.0.0.1:8080")
USUARIO = "prueba-produccion"
CLAVE = "clave-de-prueba-123"

FALLOS: list[str] = []


def comprueba(condicion: bool, queja: str) -> None:
    print(("   ok    " if condicion else "   FALLO ") + queja)
    if not condicion:
        FALLOS.append(queja)


def main() -> int:
    from patchright.sync_api import sync_playwright

    with sync_playwright() as p:
        navegador = p.chromium.launch()
        # El mismo movil que la puerta: esto se usa de pie y con una mano.
        ctx = navegador.new_context(viewport={"width": 390, "height": 844},
                                    has_touch=True, is_mobile=True, device_scale_factor=2)
        pagina = ctx.new_page()
        consola: list[str] = []
        pagina.on("console", lambda m: consola.append(f"{m.type}: {m.text}"))
        pagina.on("pageerror", lambda e: consola.append(f"pageerror: {e}"))

        def carga(ruta: str) -> None:
            pagina.goto(f"{BASE}{ruta}", wait_until="domcontentloaded")
            # **`networkidle` con tope, no a secas.** La pestaña de ofertas dudosas carga 60
            # fotos desde los CDN de las cadenas: si uno tarda, la espera a que la red se
            # quede quieta revienta con un `TimeoutError` de 30 s y la comprobacion muere a
            # mitad (paso el 24 de septiembre de 2026, con la pagina bien). Se espera lo que
            # se pueda y se sigue: lo que se comprueba despues es el contenido, no la red.
            with contextlib.suppress(Exception):
                pagina.wait_for_load_state("networkidle", timeout=8000)
            pagina.wait_for_timeout(800)

        print(f"== la aplicacion monta en {BASE}, y el CSP de Caddy la deja")
        carga("/")
        texto = pagina.inner_text("body")
        comprueba(len(texto) > 80 and pagina.get_by_placeholder(
            "leche entera, atún, papel de cocina…").count() == 1,
            f"la pagina no sale en blanco (empieza: {texto[:40]!r})")
        comprueba(pagina.locator("#raiz > *").count() > 0, "React ha montado algo en #raiz")
        bloqueado = [c for c in consola if "Content Security Policy" in c or "Refused to" in c]
        comprueba(not bloqueado, f"el CSP no bloquea nada ({bloqueado[:3]})")
        errores = [c for c in consola if c.startswith("pageerror")]
        comprueba(not errores, f"sin excepciones de JavaScript ({errores[:3]})")

        print("\n== pregunta 2: «¿esto que tengo en la mano esta caro?»")
        carga("/")
        pagina.get_by_placeholder("leche entera, atún, papel de cocina…").fill("leche entera")
        with contextlib.suppress(Exception):
            pagina.locator("a[href^='/grupo/']").first.wait_for(timeout=20000)
        comprueba(pagina.locator("a[href^='/grupo/']").count() > 0,
                  "el buscador encuentra (la ruta mas nueva de la API responde)")
        pagina.locator("a[href^='/grupo/']").first.click()
        pagina.wait_for_url("**/grupo/**", timeout=20000)
        pagina.wait_for_load_state("networkidle")
        pagina.wait_for_timeout(1200)
        frase = pagina.locator("main p.font-semibold").first
        # **Se espera a que la frase tenga texto**, no a que la pagina este quieta. La version
        # anterior esperaba `networkidle` y 1,2 s, y el 24 de septiembre de 2026 fallo una vez
        # con la frase ya escrita: el párrafo existia, pero se leyo **antes** de que se
        # rellenara, asi que `inner_text()` devolvio vacio. Es la misma mentira de instrumento
        # que documenta el capitulo 12 -- leer antes del estado final --, y se arregla
        # esperando a la condicion que se va a comprobar.
        with contextlib.suppress(Exception):
            pagina.wait_for_function(
                "() => { const p = document.querySelector('main p.font-semibold');"
                " return !!p && p.innerText.trim().length > 10; }", timeout=15000)
        comprueba(frase.count() > 0 and len(frase.inner_text()) > 10,
                  f"y la ficha contesta con una frase: {frase.inner_text()[:64]!r}")

        print("\n== las tres pantallas del panel, en el sitio que se sirve")
        for pestana, tiene_que_decir in (
                ("indice", "El nivel de precios de cada cadena"),
                ("posicion", "En qué es cara cada cadena"),
                ("dudosas", "conviene mirar dos veces")):
            # **Se espera al texto, no a un tiempo fijo.** Estos paneles piden a la API y
            # pintan cientos de filas: con una espera fija, la comprobacion falla con la
            # aplicacion bien (paso el 24 de septiembre de 2026). Se espera a que aparezca lo
            # que se va a comprobar, con tope.
            #
            # Y **se intenta dos veces**, porque el 24 de septiembre de 2026 esta misma
            # comprobacion fallo una vez y paso en la siguiente, con el codigo sin tocar: el
            # panel tarda, la primera carga se queda sin el texto y el fallo era del reloj,
            # no del panel. Un reintento con recarga no baja el liston (si tampoco aparece a
            # la segunda, sigue siendo un fallo); lo que evita es que una puerta que miente
            # una vez de cada veinte deje de mirarse.
            for _intento in (1, 2):
                carga(f"/panel?pestana={pestana}")
                with contextlib.suppress(Exception):
                    pagina.get_by_text(tiene_que_decir, exact=False).first.wait_for(timeout=20000)
                if tiene_que_decir in pagina.inner_text("main"):
                    break
            comprueba(tiene_que_decir in pagina.inner_text("main"),
                      f"el panel de {pestana} contesta")
        comprueba("no se juzgan aquí" in pagina.inner_text("main"),
                  "y la de ofertas dice cuantas no se juzgan (el campo nuevo de la API)")

        print("\n== el material de aprendizaje, servido")
        carga("/aprende/")
        texto = pagina.inner_text("main")
        comprueba("Aprender datos con un proyecto de verdad" in texto,
                  f"el temario se sirve en /aprende/ (lei: {texto[:40]!r})")
        comprueba(pagina.locator("#buscar").count() == 1, "y trae su buscador")
        # La portada lista el temario por secciones en tarjetas (`ul.tarjetas`). La comprobacion
        # miro `ol.temario` hasta el 24 de septiembre de 2026: era la portada vieja, y desde que
        # el sitio tiene indice por secciones daba **0** con el sitio perfecto. Una comprobacion
        # que suspende lo que se sirve cuando esta bien es peor que no tenerla.
        tarjetas = pagina.locator("section.bloque ul.tarjetas li").count()
        comprueba(tarjetas >= 15, f"con los capitulos del curso ({tarjetas} tarjetas)")
        comprueba(pagina.locator("nav.nav-lateral a[href$='.html']").count() >= 15,
                  "y el indice lateral con las secciones y sus capitulos")
        # **Y el buscador funciona de verdad**, no solo existe. El 24 de septiembre de 2026
        # estaba muerto en produccion y no daba ningun error visible: el CSP de Caddy prohibe
        # los scripts en linea (`script-src 'self'`), y el indice iba dentro de uno. Se caza
        # escribiendo: si el JavaScript no corre, no aparece ningun resultado.
        pagina.locator("#buscar").fill("emparejar")
        pagina.wait_for_timeout(600)
        resultados = pagina.locator("#resultados li").count()
        comprueba(resultados >= 1,
                  f"y el buscador responde bajo el CSP ({resultados} resultados para "
                  f"«emparejar»)")
        carga("/aprende/04-emparejar-productos.html")
        comprueba(pagina.locator("article table").count() >= 1,
                  "un capitulo se lee: pintan las tablas")
        comprueba(pagina.locator("article pre").count() >= 2,
                  "y los bloques de codigo")
        comprueba(pagina.locator("article aside.frase").count() == 1,
                  "y el capitulo abre con su «en una frase»")
        # El indice de la pagina (la columna de la derecha) apunta a los apartados. Se miro en
        # `aside.lateral` hasta el 24 de septiembre de 2026, y ahi no hay anclas: el lateral
        # enlaza paginas. El indice del capitulo vive en `aside.toc`.
        comprueba(pagina.locator("aside.toc a[href^='#']").count() >= 3,
                  "con su indice de apartados")

        print("\n== la primera vez, con una cuenta de verdad (barra b)")
        carga("/cesta")
        # La cuenta puede quedar de una pasada anterior que se cortara: se intenta
        # **entrar** primero, y si no esta, se crea. Los dos caminos se miran.
        if pagina.get_by_label("Clave").count():
            pagina.get_by_label("Usuario").fill(USUARIO)
            pagina.get_by_label("Clave").fill(CLAVE)
            pagina.get_by_role("button", name="Entrar").first.click()
            pagina.wait_for_timeout(2500)
            carga("/cesta")
        if pagina.get_by_role("button", name="Créala").count():
            pagina.get_by_role("button", name="Créala").first.click()
            pagina.get_by_label("Tu nombre").fill("Prueba de produccion")
            pagina.get_by_label("Usuario").fill(USUARIO)
            pagina.get_by_label("Contraseña").fill(CLAVE)
            pagina.get_by_role("button", name="Crear cuenta").first.click()
            with contextlib.suppress(Exception):
                pagina.get_by_role("button", name="Añadir").first.wait_for(timeout=25000)
            carga("/cesta")
        texto = pagina.inner_text("main")
        comprueba("No tienes ninguna lista" in texto,
                  "una cuenta nueva llega a la pantalla de la primera vez")
        comprueba(pagina.get_by_role("button", name="Añadir").count() >= 4,
                  f"y ve la aplicacion con datos reales que tocar "
                  f"({pagina.get_by_role('button', name='Añadir').count()} productos)")
        pagina.get_by_role("button", name="Añadir").first.click()
        with contextlib.suppress(Exception):
            pagina.get_by_role("checkbox").first.wait_for(timeout=25000)
        pagina.wait_for_timeout(1200)
        # La segunda linea entra por donde entra de verdad: buscar, abrir la ficha y
        # anadir alli. Y hacen falta **dos**, porque los encabezados de las dos
        # secciones solo salen cuando hay algo en los dos lados (`Cesta.tsx:1187`).
        carga("/")
        pagina.get_by_placeholder("leche entera, atún, papel de cocina…").fill("leche entera")
        with contextlib.suppress(Exception):
            pagina.locator("a[href^='/grupo/']").first.wait_for(timeout=20000)
        pagina.locator("a[href^='/grupo/']").first.click()
        pagina.wait_for_url("**/grupo/**", timeout=20000)
        with contextlib.suppress(Exception):
            pagina.get_by_role("button", name="Añadir a la cesta").first.wait_for(timeout=20000)
        pagina.get_by_role("button", name="Añadir a la cesta").first.click()
        pagina.wait_for_timeout(2500)
        carga("/cesta")
        texto = pagina.inner_text("main")
        comprueba("Casa" in texto, "al tocar se crea la lista de casa sola")
        comprueba(pagina.get_by_role("checkbox").count() == 2,
                  f"y hay dos lineas apuntadas ({pagina.get_by_role('checkbox').count()})")
        comprueba("No he podido" not in texto, "sin un error rojo al leer")

        print("\n== pregunta 3: tachar, y las dos secciones (barra c)")
        # **Se deja la lista con algo de los dos lados**, en vez de suponer como la dejo la
        # pasada anterior: si hay menos de dos lineas se anade otra, y si no hay nada tachado
        # se tacha una. La version anterior pulsaba la primera casilla y la cuenta podia
        # venir con lineas ya tachadas -- pulsarla entonces *destacha*, y la comprobacion
        # fallaba con la aplicacion bien (medido el 24 de septiembre de 2026).
        carga("/cesta")
        if pagina.locator("input[type=checkbox]").count() < 2:
            carga("/")
            pagina.get_by_placeholder("leche entera, atún, papel de cocina…").fill("leche entera")
            with contextlib.suppress(Exception):
                pagina.locator("a[href^='/grupo/']").first.wait_for(timeout=20000)
            pagina.locator("a[href^='/grupo/']").first.click()
            pagina.wait_for_url("**/grupo/**", timeout=20000)
            with contextlib.suppress(Exception):
                pagina.get_by_role("button", name="Añadir a la cesta").first.wait_for(
                    timeout=20000)
            pagina.get_by_role("button", name="Añadir a la cesta").first.click()
            pagina.wait_for_timeout(2500)
            carga("/cesta")
        if pagina.locator("input[type=checkbox]:checked").count() == 0:
            pagina.locator("input[type=checkbox]:not(:checked)").first.click()
            pagina.wait_for_timeout(2500)
            carga("/cesta")
        por_coger = pagina.locator("input[type=checkbox]:not(:checked)")
        en_el_carro = pagina.locator("input[type=checkbox]:checked")
        comprueba(por_coger.count() >= 1 and en_el_carro.count() >= 1,
                  f"la lista tiene lineas de los dos lados "
                  f"({por_coger.count()} por coger, {en_el_carro.count()} en el carro)")
        texto = pagina.inner_text("main")
        comprueba("En el carro" in texto, "y salen las dos secciones, «En el carro»")
        comprueba("Por coger" in texto, "y «Por coger», que es la otra mitad")
        # El numero de la barra: la respuesta 3 sin abrir nada. Se lee la **chapa** (el
        # `span` con `aria-hidden` y solo digitos) y no el texto del enlace, porque
        # `innerText` pega la cifra a la etiqueta y no se distingue un 1 de un 11.
        en_la_barra = pagina.evaluate("""() => {
          const a = [...document.querySelectorAll('nav a')]
            .find(x => x.getAttribute('href') === '/cesta');
          if (!a) return -1;
          const chapa = [...a.querySelectorAll('span[aria-hidden="true"]')]
            .map(s => (s.innerText || '').trim())
            .find(t => /^\\d+$/.test(t));
          return chapa ? Number(chapa) : 0;
        }""")
        comprueba(en_la_barra == por_coger.count(),
                  f"y la barra dice las que quedan por coger ({en_la_barra} contra "
                  f"{por_coger.count()})")

        print("\n== y la cuenta de prueba se borra")
        carga("/ajustes")
        comprueba("Darme de baja" in texto or "Darme de baja" in pagina.inner_text("main"),
                  "los ajustes tienen la baja")
        # Por la API y con la sesion del navegador: la pantalla pide escribir tu propio
        # usuario a proposito, y aqui lo que se quiere es no dejar basura en la base.
        borrado = pagina.evaluate(
            "async () => { const r = await fetch('/api/yo', {method: 'DELETE',"
            " credentials: 'same-origin'}); return r.status; }")
        comprueba(borrado in (200, 204), f"la cuenta de prueba se ha borrado ({borrado})")

        print("\n== el resultado")
        print(f"   consola: {len(consola)} mensajes")
        for c in consola[:6]:
            print("     ", c[:150])
        # Los 401 de la consola son **como se pregunta si hay sesion**: no son fallos.
        print(f"\n   {'TODO BIEN' if not FALLOS else 'FALLOS: ' + str(len(FALLOS))}")
        ctx.close()
        navegador.close()
    return 1 if FALLOS else 0


if __name__ == "__main__":
    sys.exit(main())
