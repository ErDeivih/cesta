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

        def busca(texto: str) -> None:
            """Busca **como se busca desde el 27 de septiembre de 2026**.

            La pantalla de entrada (`/`) es ahora Inicio, y el buscador vive dentro: se
            escribe ahi y se manda con Enter, que es lo que hace una persona. Los resultados
            siguen en `/buscar`, que es donde estaba antes el buscador, asi que las
            comprobaciones de despues (pulsar el primer `/grupo/`) no cambian.
            """
            carga("/")
            campo = pagina.get_by_placeholder("leche entera, atún, papel de cocina…")
            campo.fill(texto)
            campo.press("Enter")
            with contextlib.suppress(Exception):
                pagina.wait_for_url("**/buscar**", timeout=15000)
            with contextlib.suppress(Exception):
                pagina.locator("a[href^='/grupo/']").first.wait_for(timeout=20000)

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
        busca("leche entera")
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
        # **Lo que se pulsa en el material, que no lo media nadie.** El boton de copiar lo pone
        # un script (`copiar.js`, en fichero porque el CSP prohibe los incrustados), asi que si
        # el script no corre no hay boton **y ninguna prueba de codigo se entera**: el HTML que
        # genera `aprende.py` no lo lleva. Y las tarjetas de anterior/siguiente son la forma de
        # recorrer el curso, que es para lo que existe el sitio.
        cuantos_pre = pagina.locator("article pre").count()
        copiar = pagina.locator("article pre .copiar")
        comprueba(copiar.count() == cuantos_pre,
                  f"cada bloque de codigo tiene su boton de copiar ({copiar.count()} de "
                  f"{cuantos_pre})")
        if copiar.count():
            copiar.first.click()
            with contextlib.suppress(Exception):
                pagina.wait_for_function(
                    "() => { const b = document.querySelector('article pre .copiar');"
                    " return b && b.textContent !== 'Copiar'; }", timeout=8000)
            dicho = copiar.first.inner_text()
            # Los dos finales valen, **y el segundo es el normal por http**: el portapapeles
            # necesita contexto seguro y el material se sirve por http. Lo que no vale es
            # callarse, que es lo que hacia hasta el 28 de septiembre de 2026: decia «No puedo»
            # y ahi se acababa, con el comando delante y sin nada seleccionado.
            comprueba(dicho in ("Copiado", "Cópialo a mano"),
                      f"y al pulsarlo contesta ({dicho!r})")
            if dicho == "Cópialo a mano":
                elegido = pagina.evaluate("() => window.getSelection().toString().length")
                comprueba(elegido > 10,
                          f"y deja el codigo seleccionado para copiarlo a mano ({elegido} "
                          "caracteres)")
        migas = pagina.locator("nav.migas a")
        comprueba(migas.count() >= 2 and "Material" in pagina.locator("nav.migas").inner_text(),
                  "el capitulo dice de donde viene (migas de pan)")
        siguiente = pagina.locator("nav.paso a.paso-caja.despues").first
        if siguiente.count():
            destino = siguiente.get_attribute("href")
            titulo = siguiente.inner_text()
            siguiente.click()
            with contextlib.suppress(Exception):
                pagina.wait_for_url(f"**/aprende/{destino}", timeout=15000)
            comprueba(f"/aprende/{destino}" in pagina.url and pagina.locator("main h1").count() == 1,
                      f"y «siguiente» lleva al capitulo que anuncia ({titulo[:30]!r})")
        else:
            comprueba(False, "el capitulo no tiene tarjeta de «siguiente»")
        # El indice de la pagina (la columna de la derecha) apunta a los apartados. Se miro en
        # `aside.lateral` hasta el 24 de septiembre de 2026, y ahi no hay anclas: el lateral
        # enlaza paginas. El indice del capitulo vive en `aside.toc`.
        comprueba(pagina.locator("aside.toc a[href^='#']").count() >= 3,
                  "con su indice de apartados")
        # **Un solo `h1` por pagina, tambien en el material.** Los documentos del proyecto son
        # notas de trabajo y algunos llevan varios `#`: el de operacion tenia tres, y salia una
        # pagina con tres titulos del mismo nivel (medido el 27 de septiembre de 2026 con
        # `data/debug/accesibilidad.py`). El generador deja el primero y baja los demas a `h2`.
        for ruta in ("/aprende/", "/aprende/04-emparejar-productos.html",
                     "/aprende/93-las-formulas.html", "/aprende/OPERACION.html"):
            carga(ruta)
            cuantos = pagina.locator("main h1").count()
            comprueba(cuantos == 1,
                      f"{ruta} tiene un solo titulo de pagina ({cuantos})")
        # **Y la cara rota del material: un documento que ya no esta.** Caddy contestaba la
        # portada con un `200` (`try_files … /index.html`), asi que un enlace viejo -- un
        # documento renombrado, un marcador -- parecia funcionar y no: quien lo pulsaba veia el
        # temario y no podia saber que su enlace estaba roto. Medido el 27 de septiembre de 2026
        # con `data/debug/cuatrocientos.py`. Ahora contesta 404 con la pagina que lo dice.
        respuesta = pagina.request.get(f"{BASE}/aprende/documento-que-no-existe.html")
        comprueba(respuesta.status == 404,
                  f"un documento que no esta contesta 404 ({respuesta.status})")
        comprueba("Ese documento no está" in respuesta.text(),
                  "y con la pagina que lo dice, no con la portada")
        comprueba(pagina.request.get(f"{BASE}/aprende/").status == 200,
                  "y la portada sigue contestando 200")
        # **Y ninguna pagina del material se sale de la pantalla.** Medido el 27 de septiembre de
        # 2026 con `data/debug/quien_desborda.py`: dos documentos de la referencia medían **486 y
        # 420 px en una ventana de 390** -- una ruta, una URL y una lista entre llaves no se
        # parten solas y empujaban la pagina entera. Son los dos documentos mas largos del
        # proyecto, y se leen desde el movil como todo lo demas.
        for ruta in ("/aprende/", "/aprende/04-emparejar-productos.html",
                     "/aprende/93-las-formulas.html", "/aprende/COMPETENCIA.html",
                     "/aprende/COMPETENCIA-IMPLANTABLE.html", "/aprende/BACKLOG.html"):
            carga(ruta)
            ancho, scroll = pagina.evaluate(
                "() => [document.documentElement.clientWidth,"
                " document.documentElement.scrollWidth]")
            comprueba(scroll <= ancho + 1,
                      f"{ruta} no se sale de la pantalla ({scroll} > {ancho})")
        # **Y el capitulo empieza en la primera pantalla del movil.** Medido el 27 de septiembre
        # de 2026: el `<details>` del indice lateral sale abierto y, a 390x844, la primera
        # pantalla era el indice entero -- catorce capitulos y ni una linea del capitulo. Se
        # mira la posicion del titulo, que es lo que ve quien abre la pagina.
        caja_h1 = pagina.locator("main h1").first.bounding_box()
        comprueba(caja_h1 is not None and caja_h1["y"] < 780,
                  f"y en un movil el capitulo empieza en la primera pantalla "
                  f"(el titulo esta a {None if caja_h1 is None else round(caja_h1['y'])} px)")

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
        # **Y si la cuenta quedo a medias, se borra aqui.** Esta parte de la puerta pide una
        # cuenta **nueva**, y hasta el 27 de septiembre de 2026 daba por hecho que la de la
        # pasada anterior se habia borrado al final: una pasada cortada a mitad (por ejemplo,
        # matando el comando por tiempo) dejaba la cuenta con su lista, y la siguiente pasada
        # fallaba en tres comprobaciones -- «una cuenta nueva llega a la pantalla de la primera
        # vez» -- por el estado que dejo ella misma, no por la aplicacion. Se vio asi: el
        # timeout de un comando dejo `prueba-produccion` con una lista en la base.
        if pagina.locator("input[type=checkbox]").count() > 0 or \
                "No tienes ninguna lista" not in pagina.inner_text("main"):
            borrado = pagina.evaluate(
                "async () => { const r = await fetch('/api/yo', {method: 'DELETE',"
                " credentials: 'same-origin'}); return r.status; }")
            print(f"   (quedaba una cuenta a medias: se ha borrado, {borrado})")
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
        # Y la primera pantalla, con la cuenta recien creada y sin nada apuntado, tiene que
        # decir por donde se empieza. Antes decia «Lo que te falta: 0 cosas» y un enlace a una
        # lista vacia: medido en un movil el 27 de septiembre de 2026, y se vio en una captura.
        carga("/")
        texto = pagina.inner_text("main")
        comprueba("Todavía no tienes lista" in texto,
                  "la primera pantalla, sin lista, dice por donde se empieza")
        comprueba("0 cosas" not in texto,
                  "y no contesta con un cero, que es un hueco con forma de respuesta")
        # Y los avisos, con la misma cuenta nueva: sin ningun aviso pedido, la pantalla decia
        # «Esperando · Todavia no se ha cumplido. Te aviso yo.» encima de la caja que decia
        # «No sigues ningun producto» -- dos cabeceras para un estado, y la primera
        # contradiciendo a la segunda. Medido en una captura el 27 de septiembre de 2026.
        carga("/avisos")
        texto = pagina.inner_text("main")
        comprueba("No sigues ningún producto" in texto,
                  "los avisos, con una cuenta nueva, dicen que no sigues nada")
        comprueba("Esperando" not in texto,
                  "y no titulan «Esperando» cuando no se espera nada")
        comprueba(pagina.get_by_role("link", name="Buscar un producto").count() == 1,
                  "con por donde empezar, en vez de un callejon sin salida")
        # Y los favoritos, con la misma cuenta nueva: mismo caso y mismo arreglo. La pantalla
        # decia donde se anaden («desde la ficha de un producto, con el corazon») y no daba
        # forma de llegar, en la pantalla que esta a un toque de la barra de abajo.
        carga("/favoritos")
        texto = pagina.inner_text("main")
        comprueba("Todavía no tienes favoritos" in texto,
                  "los favoritos, con una cuenta nueva, dicen que no hay ninguno")
        comprueba(pagina.get_by_role("link", name="Buscar un producto").count() == 1,
                  "y dan por donde empezar, en vez de un callejon sin salida")
        # Las cadenas se llaman como se llaman: el identificador viene en minusculas (`dia`) y
        # se veia «dia» y «alcampo» en las cinco pantallas con pastillas, mientras la ficha del
        # grupo decia «Aldi». DIA va con las tres letras en mayuscula.
        carga("/ajustes")
        texto = pagina.inner_text("main")
        comprueba("DIA" in texto and " dia" not in texto,
                  "y las cadenas se llaman como se llaman (DIA, no «dia»)")
        carga("/cesta")
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
        busca("leche entera")
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

        # **La pantalla de Inicio, que es la que contesta las cuatro preguntas** (27 de
        # septiembre de 2026). Antes habia que entrar en Cesta para saber que faltaba y en
        # Avisos para saber que habia bajado; ahora las cuatro se contestan desde `/`. Esto
        # comprueba lo que se puede comprobar desde aqui: que el resumen **esta en la primera
        # pantalla y con datos**, no que se entienda a la primera, que es la barra (a) y la
        # cierra una persona.
        print("\n== la primera pantalla contesta las cuatro preguntas (27 sep 2026)")
        carga("/")
        texto = pagina.inner_text("main")
        comprueba("Lo que te falta" in texto,
                  "el resumen dice lo que falta sin entrar en la lista (preguntas 1 y 3)")
        comprueba("Ha bajado de lo tuyo" in texto,
                  "y lo que ha bajado de lo tuyo, tambien en la primera pantalla (pregunta 4)")
        comprueba(pagina.get_by_placeholder("leche entera, atún, papel de cocina…").count() == 1,
                  "con el buscador arriba, que es la pregunta 2")
        comprueba(pagina.locator("nav[aria-label='Secciones'] a[href='/']").count() >= 1,
                  "y la barra lleva a Inicio")

        print("\n== sin cuenta, la primera pantalla no promete «lo tuyo» (27 sep 2026)")
        # **El fallo que esto vigila, y se vio en una captura, no en una prueba.** La API
        # contesta `solo_mios: false` cuando no hay sesion -- no puede saber que es "lo mio" --
        # y la pantalla ponia el titulo fijo «Ha bajado de lo tuyo» encima de las sesenta
        # mayores bajadas del catalogo. Se mira con un contexto **sin cookies**, que es el
        # unico sitio donde esto se ve: la sesion de la puerta ya esta abierta.
        suelta_ctx = navegador.new_context(viewport={"width": 390, "height": 844},
                                           has_touch=True, is_mobile=True)
        suelta = suelta_ctx.new_page()
        with contextlib.suppress(Exception):
            suelta.goto(f"{BASE}/", wait_until="domcontentloaded", timeout=30000)
        suelta.wait_for_timeout(2500)
        limpio = suelta.inner_text("main")
        comprueba("Lo que más ha bajado" in limpio,
                  "sin cuenta, la tarjeta dice «Lo que más ha bajado»")
        # El titulo exacto, no la idea: «qué ha bajado de lo tuyo» tambien sale en la tarjeta
        # que invita a entrar, y esa frase es correcta. Lo que no puede salir es el **titulo**
        # de la tarjeta cuando el servidor ha dicho que no ha filtrado.
        comprueba("Ha bajado de lo tuyo" not in limpio,
                  "y no titula «Ha bajado de lo tuyo» encima de las bajadas del catalogo")
        comprueba("entra o crea una cuenta" in limpio,
                  "y dice por donde se entra, en vez de dejarlo sin salida")
        # **Y las pantallas que piden sesion, sin sesion: que no se queden cargando.** Aqui
        # estaba el fallo mas serio de esta cara: `useAlertas` tiene `enabled: hay usuario`, asi
        # que sin sesion la consulta no se lanza nunca y se queda en `pending` para siempre --
        # quien no habia entrado y tocaba «Avisos» en la barra de abajo se quedaba mirando un
        # esqueleto **eterno**. Medido con `data/debug/texto.py /avisos --sin-sesion`.
        for ruta, tiene_que_decir in (("/avisos", "Entra para ver tus avisos"),
                                      ("/cesta", "Entra para ver tu lista"),
                                      ("/favoritos", "Entra para ver tus favoritos"),
                                      ("/ajustes", "Entra para cambiar tus ajustes")):
            with contextlib.suppress(Exception):
                suelta.goto(f"{BASE}{ruta}", wait_until="domcontentloaded", timeout=30000)
            suelta.wait_for_timeout(2500)
            texto = suelta.inner_text("main")
            comprueba(tiene_que_decir in texto,
                      f"sin cuenta, {ruta} dice por donde se entra")
            comprueba("Cargando" not in texto,
                      f"y {ruta} no se queda cargando para siempre ({texto[:40]!r})")
        suelta_ctx.close()

        print("\n== pregunta 3: tachar, y las dos secciones (barra c)")
        # **Se deja la lista con algo de los dos lados**, en vez de suponer como la dejo la
        # pasada anterior: si hay menos de dos lineas se anade otra, y si no hay nada tachado
        # se tacha una. La version anterior pulsaba la primera casilla y la cuenta podia
        # venir con lineas ya tachadas -- pulsarla entonces *destacha*, y la comprobacion
        # fallaba con la aplicacion bien (medido el 24 de septiembre de 2026).
        carga("/cesta")
        if pagina.locator("input[type=checkbox]").count() < 2:
            busca("leche entera")
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

        # ------------------------------------------------------------- en escritorio -----
        print("\n== y en una pantalla de escritorio, que no la medía nadie")
        # **Todo lo de arriba es un movil de 390 x 844, y la aplicacion tambien se usa en el
        # ordenador del salon.** Hasta el 28 de septiembre de 2026 la unica mirada a lo ancho era
        # una captura (`data/debug/captura.py --entero`) y el contraste, o sea que dos cosas que
        # solo existen en pantalla grande -- la barra de secciones de arriba y las tablas **con
        # sus columnas** en vez de apiladas -- no las comprobaba ninguna puerta. Se abre un
        # contexto nuevo a 1440 x 900, se mira eso y que nada se deslice de lado.
        ancho_ctx = navegador.new_context(viewport={"width": 1440, "height": 900},
                                          locale="es-ES")
        ancho = ancho_ctx.new_page()
        ancho.on("pageerror", lambda e: consola.append(f"[escritorio] pageerror: {e}"))
        for ruta, que in (("/", "la primera pantalla"), ("/buscar?q=leche%20entera",
                                                         "los resultados"),
                          ("/cesta", "la lista"), ("/panel?pestana=donde", "el panel"),
                          ("/aprende/04-emparejar-productos.html", "un capitulo del material")):
            ancho.goto(f"{BASE}{ruta}", wait_until="domcontentloaded")
            with contextlib.suppress(Exception):
                ancho.wait_for_load_state("networkidle", timeout=8000)
            ancho.wait_for_timeout(900)
            desliza = ancho.evaluate(
                "() => document.documentElement.scrollWidth - window.innerWidth")
            comprueba(desliza <= 1,
                      f"{que}, a 1440 px, no se desliza de lado ({desliza} px)")
        ancho.goto(f"{BASE}/buscar?q=leche%20entera", wait_until="domcontentloaded")
        with contextlib.suppress(Exception):
            ancho.wait_for_load_state("networkidle", timeout=8000)
        ancho.wait_for_timeout(1200)
        # La barra de secciones de arriba: en el movil esta abajo (`lg:hidden`), y aqui tiene que
        # estar y llevar a los mismos sitios.
        nav_ancho = ancho.locator("header nav[aria-label='Secciones'] a")
        comprueba(nav_ancho.count() >= 5,
                  f"en escritorio sale la barra de secciones de arriba ({nav_ancho.count()} "
                  "destinos)")
        comprueba(ancho.locator("body > div > nav[aria-label='Secciones']").count() == 0
                  or not ancho.locator("body > div > nav[aria-label='Secciones']").first.is_visible(),
                  "y la barra de abajo del movil no se pinta dos veces")
        # Y la tabla, con sus columnas: en el movil se apila (una fila por linea) y en escritorio
        # tiene que volver a ser una tabla, con su cabecera.
        cabecera = ancho.locator("main thead th")
        comprueba(cabecera.count() >= 3 and cabecera.first.is_visible(),
                  f"y los resultados vuelven a ser una tabla con columnas "
                  f"({cabecera.count()} cabeceras)")
        # El material, a lo ancho: el indice lateral tiene que estar (en el movil se pliega).
        ancho.goto(f"{BASE}/aprende/04-emparejar-productos.html", wait_until="domcontentloaded")
        ancho.wait_for_timeout(900)
        lateral = ancho.locator("aside.lateral")
        comprueba(lateral.count() == 1 and lateral.first.is_visible(),
                  "el indice lateral del material se ve en pantalla ancha")
        # **Y el teclado del material, que tampoco lo miraba nadie.** El buscador del sitio tiene
        # un atajo (`/`, `buscar.js`) para no tener que ir al raton, la lista de resultados se
        # cierra con `Escape`, y lo que no encuentra lo dice («Nada con esas palabras»), que es
        # la cara vacia que aqui no habia medido nadie. Y el indice lateral esta plegado en el
        # movil a proposito: en el escritorio es al reves.
        ancho.goto(f"{BASE}/aprende/04-emparejar-productos.html", wait_until="domcontentloaded")
        ancho.wait_for_timeout(900)
        ancho.keyboard.press("/")
        ancho.wait_for_timeout(400)
        foco = ancho.evaluate("() => document.activeElement && document.activeElement.id")
        comprueba(foco == "buscar",
                  f"en el material, «/» lleva el foco al buscador ({foco!r})")
        ancho.locator("#buscar").fill("zzz-no-existe-zzz")
        ancho.wait_for_timeout(600)
        comprueba("Nada con esas palabras" in ancho.locator("#resultados").inner_text(),
                  "y una busqueda sin resultados lo dice, en vez de quedarse vacia")
        ancho.keyboard.press("Escape")
        ancho.wait_for_timeout(400)
        comprueba(ancho.locator("#resultados").is_hidden(),
                  "y «Escape» cierra la lista de resultados")
        # El indice lateral: plegado en el movil (el `<details>` no lleva `open`), abierto en
        # escritorio (el CSS esconde el `<summary>`), que es lo que `GUION_LATERAL` decide.
        comprueba(ancho.locator(".lateral details").first.get_attribute("open") is not None,
                  "en escritorio el indice lateral esta desplegado de salida")
        ancho_ctx.close()

        movil_lateral = navegador.new_context(viewport={"width": 390, "height": 844},
                                             is_mobile=True, has_touch=True, locale="es-ES")
        estrecho = movil_lateral.new_page()
        estrecho.goto(f"{BASE}/aprende/04-emparejar-productos.html", wait_until="domcontentloaded")
        estrecho.wait_for_timeout(1200)
        comprueba(estrecho.locator(".lateral details").first.get_attribute("open") is None,
                  "y en el movil se pliega, para que la primera pantalla sea el capitulo")
        movil_lateral.close()

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
