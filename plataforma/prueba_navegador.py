"""La interfaz, en un navegador de verdad: las cuatro preguntas, medidas y comprobadas.

Por que existe
--------------
La condicion (a) de la barra -- *"las cuatro preguntas contestadas en menos de quince
segundos con el movil y sin saber donde esta el boton"* -- **no la puede cerrar quien
escribe el codigo**: se juzga contra la madre del dueno. Pero si que se puede comprobar
**todo lo que hace falta para que sea posible**: que la pantalla cargue, que la busqueda
responda, que la ficha diga la frase, que la lista tenga las dos secciones y el pasillo,
que tachar funcione sin cobertura y que suba solo. Un boton que no existe no se pulsa en
quince segundos, y eso es un fallo de codigo, no de usabilidad.

Esto es la puerta mecanica de (a): lo que este script no pase, no se le puede pedir a una
persona. Lo que este script pase **no** quiere decir que (a) este cumplida -- eso lo dice
`docs/PRUEBA-15-SEGUNDOS.md`, con alguien que no haya escrito estas pantallas.

Como se corre
-------------
Necesita la API y la interfaz levantadas, y **la interfaz tiene que hablar con la API
nueva** (la imagen que corre en el 8080 puede ser mas vieja):

    docker run --rm -d --name cesta-prueba-db -e POSTGRES_PASSWORD=prueba \
        -e POSTGRES_USER=cesta -e POSTGRES_DB=cesta -p 127.0.0.1:5434:5432 postgres:16-alpine
    $env:CESTA_POSTGRES='postgresql://cesta:prueba@127.0.0.1:5434/cesta'
    uv run uvicorn plataforma.api.main:app --host 127.0.0.1 --port 8099
    cd plataforma/web/app; $env:CESTA_API='http://127.0.0.1:8099'; npm run dev
    uv run python -m plataforma.prueba_navegador

El navegador es el de `patchright`, que ya esta instalado para los colectores. Se usa un
movil de 390 x 844 con `has_touch`, que es como se usa esto de verdad: de pie y con una
mano.
"""
from __future__ import annotations

import contextlib
import os
import sys
import time

BASE = os.environ.get("CESTA_UI", "http://localhost:5173")
CLAVE = "clave-de-prueba-123"
# **Fija, no nueva en cada pasada**: la API limita las altas por hora (`ALTAS_POR_HORA`).
USUARIO = "prueba-navegador"


def _grupo_de_una_cadena() -> int | None:
    """Un grupo que este en **una sola cadena**, preguntandole a gold.

    Es el caso que el encargo llama «sin comparacion»: no hay dos precios que restar, asi
    que la frase no se puede decir sin inventarsela, y la pantalla tiene que callarse y
    decir por que.

    **No se busca por el buscador**, y esto es lo que se aprendio al intentarlo: en los
    primeros cuarenta resultados de cinco busquedas **no salio ninguno de una sola cadena**
    -- los productos sin pareja no aparecen ahi --, asi que la unica forma de comprobar
    esta regla es ir a un grupo concreto. Cual es hoy es cosa del catalogo, no del codigo:
    se pregunta a gold.
    """
    try:
        from plataforma.api import catalogo
    except Exception:  # noqa: BLE001
        return None
    try:
        fila = catalogo.conexion().execute("""
            SELECT grupo_id FROM buscable
             WHERE grupo_id IS NOT NULL AND precio_unidad_cent > 0
             GROUP BY grupo_id HAVING count(DISTINCT fuente) = 1
             ORDER BY grupo_id LIMIT 1""").fetchone()
    except Exception:  # noqa: BLE001
        return None
    return int(fila[0]) if fila else None


def main() -> int:
    with contextlib.suppress(Exception):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    from patchright.sync_api import sync_playwright

    fallos: list[str] = []
    tiempos: list[tuple[str, float]] = []

    def comprueba(condicion: bool, queja: str) -> None:
        if condicion:
            print(f"   ok    {queja}")
        else:
            print(f"   FALLO {queja}")
            fallos.append(queja)

    with sync_playwright() as p:
        navegador = p.chromium.launch(headless=True)
        contexto = navegador.new_context(
            viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True,
            locale="es-ES")
        pagina = contexto.new_page()
        errores: list[str] = []
        consola: list[str] = []
        pagina.on("pageerror", lambda e: errores.append(str(e)))
        pagina.on("console", lambda m: consola.append(m.text) if m.type == "error" else None)

        def carga(ruta: str = "/") -> None:
            pagina.goto(f"{BASE}{ruta}", wait_until="domcontentloaded")
            pagina.wait_for_load_state("networkidle")

        # ---------------------------------------------- abrir: la fecha y el buscador ---
        print("\n== abrir la aplicacion")
        t0 = time.monotonic()
        carga("/")
        tiempos.append(("abrir la aplicacion", time.monotonic() - t0))
        cuerpo = pagina.inner_text("body")
        comprueba("Datos del" in cuerpo, "la cabecera dice de que dia son los precios")
        comprueba(pagina.get_by_placeholder("leche entera, atún, papel de cocina…").count() == 1,
                  "el buscador se ve y se puede tocar sin buscar el boton")
        comprueba(pagina.get_by_text("Escribe al menos dos letras").count() >= 1,
                  "sin escribir nada hay algo que leer, no una pantalla vacia")
        # **La primera vez, con datos reales y sin visita guiada** (condicion (b) de la
        # barra): sin sesion, el buscador vacio ensena cuatro productos que compra todo el
        # mundo con su diferencia de hoy. Y cada uno tiene que **hablar de lo que se ha
        # buscado**: el 23 sep 2026 buscar "aceite de oliva" devolvia «Picos sin gluten» el
        # primero, y la tarjeta lo pintaba tal cual.
        primera = pagina.inner_text("main")
        comprueba("Esto compara el precio" in primera,
                  "sin sesion sale la tarjeta de la primera vez (no un esqueleto)")
        comprueba("visita guiada" not in primera.lower()
                  and pagina.get_by_role("button", name="Siguiente").count() == 0,
                  "y no es una visita guiada: no hay pasos que pasar")
        lista_ejemplos = pagina.locator("main ul li")
        nombres = [lista_ejemplos.nth(i).inner_text().split("\n")[0]
                   for i in range(lista_ejemplos.count())]
        print(f"   ejemplos: {nombres}")
        comprueba(len(nombres) >= 3, f"la tarjeta ensena ejemplos ({len(nombres)})")
        for buscado, nombre in zip(("leche", "pan", "aceite", "agua"), nombres, strict=False):
            comprueba(buscado in nombre.lower(),
                      f"el ejemplo «{nombre[:32]}» habla de «{buscado}»")

        # ------------------------------------------------------------- una cuenta -------
        # Se hace primero porque la lista y los avisos son de una persona: sin sesion, la
        # ficha ni siquiera ensena el boton de anadir (no hay donde apuntarlo).
        #
        # **La cuenta es fija, no nueva en cada pasada.** La API limita cuantas se crean
        # por hora (`ALTAS_POR_HORA`, `main.py:114`) y una prueba que se corre diez veces
        # agotaba el limite: la sexta pasada se quedaba sin cuenta y fallaba todo lo que
        # depende de la sesion. Se entra con la de siempre, y solo si no existe se crea.
        print("\n== entrar (como alguien que ya tiene cuenta)")
        carga("/cesta")
        comprueba(pagina.get_by_text("Entra para ver tu lista").count() >= 1,
                  "sin sesion la lista pide entrar, y lo explica")
        campos = pagina.locator("form input")
        campos.nth(0).fill(USUARIO)
        campos.nth(1).fill(CLAVE)
        pagina.get_by_role("button", name="Entrar").click()
        pagina.wait_for_timeout(2500)
        if pagina.get_by_text("Entra para ver tu lista").count():
            print("   (la cuenta no existia: se crea, una vez)")
            pagina.get_by_role("button", name="Créala").click()
            pagina.wait_for_timeout(300)
            campos = pagina.locator("form input")
            comprueba(campos.count() == 3, f"el alta pide nombre, usuario y clave ({campos.count()})")
            if campos.count() == 3:
                campos.nth(0).fill("Madre")
                campos.nth(1).fill(USUARIO)
                campos.nth(2).fill(CLAVE)
                pagina.get_by_role("button", name="Crear cuenta").click()
                pagina.wait_for_timeout(2500)
        carga("/cesta")
        cuerpo_entrada = pagina.inner_text("body")
        comprueba("Entra para ver tu lista" not in cuerpo_entrada,
                  f"la cuenta {USUARIO} entra (si dice 429, se han creado demasiadas "
                  f"cuentas en la ultima hora)")

        # -------------------------------------------------- pregunta 2: ¿esto esta caro? --
        print("\n== 'esto que tengo en la mano, esta caro?'")
        carga("/")
        t0 = time.monotonic()
        pagina.get_by_placeholder("leche entera, atún, papel de cocina…").fill("leche entera")
        # Se espera a que el resultado exista de verdad: esperar un numero fijo de
        # milisegundos es como se escriben las pruebas que fallan solas.
        primer = pagina.locator("a[href^='/grupo/']").first
        primer.wait_for(timeout=15000)
        primer.click()
        pagina.wait_for_url("**/grupo/**", timeout=15000)
        pagina.wait_for_load_state("networkidle")
        tiempos.append(("de la entrada a la ficha con la frase", time.monotonic() - t0))
        comprueba("/grupo/" in pagina.url, f"el resultado abre la ficha ({pagina.url})")
        # Se espera al boton, que solo existe cuando el dato ha llegado: leer el texto
        # antes de eso es medir la pagina a medio pintar, y eso no es un fallo de la
        # aplicacion sino de la prisa de quien mira.
        with contextlib.suppress(Exception):
            pagina.get_by_role("button", name="Añadir a la cesta").first.wait_for(timeout=20000)
        ficha = pagina.inner_text("main")
        # **La frase antes que la tabla**: es la condicion (d) de la barra, y hasta ahora
        # solo estaba comprobada con pruebas de codigo, no en un navegador.
        frases = ("Es la mas barata", "Es la más barata", "Cuesta un", "Esta al mismo precio",
                  "Está al mismo precio", "La mas barata esta en", "La más barata está en")
        frase = next((f for f in frases if f in ficha), None)
        comprueba(frase is not None,
                  "la ficha contesta con una FRASE, no solo con una tabla")
        if frase:
            html = pagina.content()
            corte = html.find(frase)
            tabla = html.find("<table")
            comprueba(tabla == -1 or corte < tabla,
                      "la frase va ANTES que la tabla en la pantalla")
            print(f"   la frase: «{frase}…»")
        # Y la campana de los avisos, que es del punto 6. **Vale cualquiera de los dos
        # estados**: la cuenta es la misma en cada pasada, asi que la segunda vez el aviso
        # ya esta pedido y el boton dice «Te aviso». Una prueba que solo acepta el primer
        # estado obliga a crear una cuenta nueva cada vez -- y la API limita las altas.
        ya_pedido = pagina.get_by_text("Te aviso").count() >= 1
        boton_campana = pagina.get_by_role("button", name="Avisarme si baja")
        comprueba(ya_pedido or boton_campana.count() == 1,
                  "la ficha deja pedir el aviso («Avisarme si baja» o «Te aviso»)")

        # ------------------------------------------------------------ pregunta 1 y 3 ----
        print("\n== 'que me falta y donde lo compro' / 'voy tachando bien'")
        anadir = pagina.get_by_role("button", name="Añadir a la cesta")
        comprueba(anadir.count() >= 1, "se puede anadir a la lista desde la ficha")
        if anadir.count():
            anadir.first.click()
            with contextlib.suppress(Exception):
                pagina.get_by_text("En la cesta").first.wait_for(timeout=20000)
            comprueba(pagina.get_by_text("En la cesta").count() >= 1,
                      "el boton dice que ya esta dentro (y no se puede pulsar dos veces)")

        # ------------------------------------------------- el aviso, pedido desde aqui --
        # Punto 6: la campana tiene que poder pedir el aviso, y lo pedido tiene que
        # aparecer despues en `/avisos`. Sin esto, la pantalla de avisos esta vacia para
        # siempre y la mitad de dentro (el vigilante) no se ve nunca.
        campana = pagina.get_by_role("button", name="Avisarme si baja")
        if campana.count():
            campana.first.click()
            with contextlib.suppress(Exception):
                pagina.get_by_text("Te aviso").first.wait_for(timeout=20000)
            comprueba(pagina.get_by_text("Te aviso").count() >= 1,
                      "la campana pide el aviso y dice que si («Te aviso»)")
        t0 = time.monotonic()
        carga("/cesta")
        tiempos.append(("de la ficha a la lista", time.monotonic() - t0))
        lista = pagina.inner_text("body")
        comprueba("Entra para ver tu lista" not in lista, "la lista se abre con la sesion")
        with contextlib.suppress(Exception):
            pagina.locator("input[type=checkbox]").first.wait_for(timeout=20000)
        comprueba(pagina.locator("input[type=checkbox]").count() >= 1,
                  "la linea anadida esta en la lista")
        comprueba("Por coger" in lista or "líneas" in lista, "la lista ensena lo que hay dentro")

        # --------------------------------------------------- el pasillo, pegado arriba --
        cabeceras = pagina.locator("h4")
        if cabeceras.count():
            pegado = pagina.evaluate(
                "() => getComputedStyle(document.querySelector('h4')).position")
            comprueba(pegado == "sticky",
                      f"el encabezado de pasillo se queda pegado (position: {pegado})")
        else:
            print("   (no hay pasillo que comprobar con una sola linea)")

        # ------------------------------------------------------ deshacer, sin preguntar --
        # §3.4 del encargo: *"cada accion destructiva deja un «deshacer» durante unos
        # segundos, y ninguna pide confirmacion"*. Quitar una linea es LA accion
        # destructiva de esta pantalla.
        print("\n== quitar una linea, y deshacerlo")

        def cuantas_casillas() -> int:
            return pagina.locator("input[type=checkbox]").count()

        def espera_a_cuantas(objetivo: int, segundos: float = 10.0) -> int:
            """Espera a que la lista tenga `objetivo` lineas. Devuelve las que hay.

            Hace falta porque **quitar una linea no es instantaneo**: el clic manda el
            PATCH, y la lista se vuelve a pedir. Leer el numero justo despues del clic mide
            la pantalla de antes -- que es como esta prueba se puso roja sola la primera
            vez que la corri con mas de una linea.
            """
            fin = time.monotonic() + segundos
            while time.monotonic() < fin:
                if cuantas_casillas() == objetivo:
                    break
                pagina.wait_for_timeout(250)
            return cuantas_casillas()

        quitar = pagina.get_by_role("button", name="Quitar")
        comprueba(quitar.count() >= 1, "cada linea se puede quitar")
        if quitar.count():
            # **Cuanto habia antes**, no "cero despues": la cuenta es la misma en cada
            # pasada y la lista va creciendo, asi que contar lineas absolutas hace que la
            # prueba se ponga roja sola en la segunda vuelta.
            antes = cuantas_casillas()
            quitar.first.click()
            with contextlib.suppress(Exception):
                pagina.get_by_text("Has quitado").first.wait_for(timeout=15000)
            cuerpo_tras_quitar = pagina.inner_text("body")
            comprueba("Has quitado" in cuerpo_tras_quitar
                      and "Deshacer" in cuerpo_tras_quitar,
                      "al quitar sale «Has quitado … Deshacer», sin preguntar nada")
            despues = espera_a_cuantas(antes - 1)
            comprueba(despues == antes - 1,
                      f"la linea quitada desaparece de la lista ({antes} -> {despues})")
            deshacer = pagina.get_by_role("button", name="Deshacer")
            if deshacer.count():
                deshacer.first.click()
                with contextlib.suppress(Exception):
                    pagina.locator("input[type=checkbox]").first.wait_for(timeout=15000)
                comprueba(pagina.locator("input[type=checkbox]").count() >= 1,
                          "«Deshacer» la trae de vuelta")

        # ------------------------------------------------- sin cobertura: tachar igual ---
        print("\n== tachar sin cobertura")
        casillas = pagina.locator("input[type=checkbox]")
        comprueba(casillas.count() >= 1, "hay lineas que tachar")
        if casillas.count():
            contexto.set_offline(True)
            t0 = time.monotonic()
            casillas.first.click()
            pagina.wait_for_timeout(1200)
            tiempos.append(("tachar sin cobertura", time.monotonic() - t0))
            sin_red = pagina.inner_text("body")
            comprueba("sin cobertura" in sin_red.lower(),
                      "dice que el cambio espera a que vuelva la cobertura")
            comprueba("No he podido guardar el cambio" not in sin_red,
                      "y NO lo pinta como un error")
            # **Y el cambio esta GUARDADO en el aparato**, que es lo que hace que no se
            # pierda al cerrar la pestaña. Se mira el almacenamiento, no la pantalla: es
            # la mitad que no se ve y la que decide si esto sirve de algo.
            cola = pagina.evaluate("() => localStorage.getItem('cesta.cola.v1')")
            comprueba(bool(cola) and "tachado" in (cola or ""),
                      f"el cambio queda guardado en el movil: {str(cola)[:60]}")
            contexto.set_offline(False)
            # Al volver la cobertura tiene que subirlo solo.
            pagina.wait_for_timeout(2500)
            subido = pagina.inner_text("body")
            comprueba("Se ha subido" in subido or "Se han subido" in subido,
                      "al volver la cobertura se sube solo, y lo dice")
            vacia = pagina.evaluate("() => localStorage.getItem('cesta.cola.v1')")
            comprueba(not vacia or vacia == "{}",
                      f"y la cola se vacia cuando el servidor los aplica: {vacia}")

        # -------------------------------------------------------- pregunta 4: los avisos --
        print("\n== 'ha bajado algo de lo mio?'")
        t0 = time.monotonic()
        carga("/avisos")
        tiempos.append(("de la lista a los avisos", time.monotonic() - t0))
        avisos = pagina.inner_text("body")
        comprueba("Avisos" in avisos, "la pantalla de avisos existe y se abre")
        comprueba("Esperando" in avisos, "ensena lo que se esta esperando")
        # El aviso pedido desde la ficha tiene que estar aqui: es la otra mitad del punto
        # 6, y sin esto la pantalla esta vacia para siempre.
        comprueba("Te aviso cuando" in avisos,
                  "el aviso pedido en la ficha aparece aqui, con lo que promete")

        # ------------------------- y un grupo del que NO nos fiamos no da frase (barra d) --
        # La frase no se inventa: si el grupo esta en una sola cadena, no hay comparacion
        # que hacer y la pantalla no puede decir «es la mas barata de las cinco». Se busca
        # ese caso por la API (que es quien sabe cuantos grupos hay de cada tipo) y se abre
        # en el navegador, porque lo que hay que ver es que NO se pinta la frase.
        print("\n== un grupo de una sola cadena, que no da frase")
        solo_uno = _grupo_de_una_cadena()
        if solo_uno is None:
            print("   (no he encontrado ninguno hoy: no se puede comprobar)")
        else:
            carga(f"/grupo/{solo_uno}")
            texto_uno = pagina.inner_text("main")
            frases = ("Es la mas barata", "Es la más barata", "Cuesta un",
                      "Esta al mismo precio", "Está al mismo precio")
            comprueba(not any(f in texto_uno for f in frases),
                      f"el grupo {solo_uno} (una sola cadena) NO lleva frase")
            comprueba("sin comparación" in texto_uno or "una sola cadena" in texto_uno,
                      "y dice por que no la lleva, en vez de callarse")

        # Un `pageerror` es una excepcion de JavaScript: eso si invalida todo lo demas. Un
        # 401 en `/api/yo` es como la aplicacion pregunta "¿hay sesion?" antes de entrar, y
        # sale en la consola sin ser un fallo. Se cuentan por separado a proposito.
        comprueba(not errores, f"sin excepciones de JavaScript ({errores[:2]})")
        if avisos_401 := [e for e in consola if "401" in e]:
            print(f"   (nota: {len(avisos_401)} respuestas 401 en la consola, "
                  f"que es como se pregunta si hay sesion)")
        navegador.close()

    print("\n== tiempos, de un toque al siguiente")
    for que, segundos in tiempos:
        print(f"   {segundos:5.1f} s   {que}")
    print("\n== LA PUERTA MECANICA DE (a)")
    if fallos:
        print(f"   {len(fallos)} FALLO(S):")
        for f in fallos:
            print(f"     - {f}")
        print("   Lo que no pase aqui no se le puede pedir a una persona.")
        return 1
    print("   TODO BIEN: lo que hace falta para contestar las cuatro preguntas esta,")
    print("   responde y no da un solo error de JavaScript.")
    print("   **Esto NO cierra (a)**: eso lo dice docs/PRUEBA-15-SEGUNDOS.md, con alguien")
    print("   que no haya escrito estas pantallas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
