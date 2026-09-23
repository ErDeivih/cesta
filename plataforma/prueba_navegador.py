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
# Y la segunda cuenta, la que **abre el enlace de invitacion**: tiene que ser otra persona,
# porque el caso que manda es el de quien recibe el enlace y no estaba dentro.
USUARIO_INVITADA = "prueba-invitada"


def _carga(pagina, ruta: str = "/") -> None:
    """Abre una ruta y espera a que la pantalla deje de pedir cosas."""
    pagina.goto(f"{BASE}{ruta}", wait_until="domcontentloaded")
    pagina.wait_for_load_state("networkidle")


def _entra(pagina, usuario: str, clave: str, nombre: str, comprueba=None, *,
           puerta: str = "Entra para ver tu lista") -> str:
    """Entra con una cuenta **fija** en la pantalla que ya esta abierta, y solo si la
    cuenta no existe la crea.

    Devuelve `"entrado"`, `"creado"` o `"sin-sesion"` (no ha podido entrar).

    Entra **donde la pantalla este**, y eso es lo que permite usarlo tambien en
    `/unirme/<codigo>`: esa pantalla no se puede recargar, porque el codigo de la invitacion
    vive en la barra de direcciones y `Unirse.tsx` navega solo, y solo cuando se aplica.
    `puerta` es la frase con la que cada pantalla dice que no hay sesion; la cesta y la
    invitacion no dicen lo mismo.

    La cuenta es fija y no nueva en cada pasada porque la API limita cuantas se crean por
    hora (`ALTAS_POR_HORA`, `main.py:114`): una prueba que se corre diez veces agotaba el
    limite y la sexta pasada se quedaba sin cuenta, con todo lo que depende de la sesion en
    rojo y por un motivo que no tiene nada que ver con la interfaz.
    """
    if puerta not in pagina.inner_text("body"):
        return "entrado"
    campos = pagina.locator("form input")
    if campos.count() < 2:
        return "sin-sesion"
    campos.nth(0).fill(usuario)
    campos.nth(1).fill(clave)
    pagina.get_by_role("button", name="Entrar").click()
    pagina.wait_for_timeout(2500)
    if puerta not in pagina.inner_text("body"):
        return "entrado"
    pagina.get_by_role("button", name="Créala").click()
    pagina.wait_for_timeout(300)
    campos = pagina.locator("form input")
    if comprueba is not None:
        comprueba(campos.count() == 3,
                  f"el alta de {usuario} pide nombre, usuario y clave ({campos.count()})")
    if campos.count() < 3:
        return "sin-sesion"
    campos.nth(0).fill(nombre)
    campos.nth(1).fill(usuario)
    campos.nth(2).fill(clave)
    pagina.get_by_role("button", name="Crear cuenta").click()
    pagina.wait_for_timeout(2500)
    return "sin-sesion" if puerta in pagina.inner_text("body") else "creado"


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


# El contraste, medido ya pintado: color de texto, fondo real (subiendo por los padres,
# porque casi nunca es el del propio elemento) y el minimo de WCAG segun el tamano.
#
# **Sin una sola barra invertida a proposito.** La primera version llevaba el regex
# `rgba?\(...\)` escrito a mano, se perdio al pasar el texto de Python al navegador, y la
# medida decia "0 textos malos" **sin haber mirado ninguno**. Por eso el JS de aqui no usa
# regex con escapes, y por eso al final de la puerta hay una trampa: un texto ilegible
# puesto a mano que TIENE que salir.
_CONTRASTE = """() => {
  const lum = (c) => {
    const v = c.map(x => { x /= 255; return x <= 0.03928 ? x / 12.92
                                                : Math.pow((x + 0.055) / 1.055, 2.4); });
    return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2];
  };
  const parse = (s) => {
    if (!s || s.indexOf('rgb') !== 0) return null;
    const p = s.replace(/[^0-9.]+/g, ' ').trim().split(' ').map(Number);
    if (p.length < 3) return null;
    return {rgb: p.slice(0, 3), a: p.length > 3 ? p[3] : 1};
  };
  const fondo = (el) => {
    let n = el;
    while (n) {
      const c = parse(getComputedStyle(n).backgroundColor);
      if (c && c.a > 0.9) return c.rgb;
      n = n.parentElement;
    }
    return [255, 255, 255];
  };
  const ratio = (a, b) => {
    const l1 = lum(a), l2 = lum(b);
    const hi = l1 > l2 ? l1 : l2, lo = l1 > l2 ? l2 : l1;
    return (hi + 0.05) / (lo + 0.05);
  };
  const salida = [];
  const nodos = document.querySelectorAll(
    'p, span, a, button, h1, h2, h3, h4, li, td, th, dd, dt, summary, label, strong');
  for (const el of nodos) {
    let propio = false;
    for (const n of el.childNodes) {
      if (n.nodeType === 3 && n.textContent.trim().length > 1) { propio = true; break; }
    }
    if (!propio) continue;
    const r = el.getBoundingClientRect();
    const s = getComputedStyle(el);
    if (r.width < 1 || r.height < 1 || s.visibility === 'hidden' || s.display === 'none'
        || parseFloat(s.opacity) < 0.6) continue;
    const fg = parse(s.color);
    if (!fg) continue;
    const cr = ratio(fg.rgb, fondo(el));
    const px = parseFloat(s.fontSize);
    const negrita = parseInt(s.fontWeight, 10) >= 700;
    const grande = px >= 24 || (px >= 18.66 && negrita);
    const minimo = grande ? 3 : 4.5;
    if (cr < minimo) {
      salida.push({texto: el.innerText.trim().split('\\n').join(' ').slice(0, 40),
                   cr: Math.round(cr * 100) / 100, minimo: minimo, px: px,
                   color: s.color, fondo: fondo(el).join(',')});
    }
  }
  return salida;
}"""

# Un texto que no se lee, puesto a mano. Si la medida no lo ve, la medida no sirve.
_TRAMPA = """() => {
  const malo = document.createElement('p');
  malo.style.color = 'rgb(238, 238, 238)';
  malo.style.backgroundColor = 'rgb(255, 255, 255)';
  malo.textContent = 'Este texto no se lee';
  document.querySelector('main').prepend(malo);
}"""


def _contraste_flojo(pagina) -> list[dict]:
    """Los textos que no llegan al minimo de contraste, ya pintados."""
    return pagina.evaluate(_CONTRASTE)


def _toques_pequenos(pagina) -> list[dict]:
    """Lo que se puede pulsar y mide menos de 44 px de verdad, ya pintado.

    §3.3 del encargo: *"lo que se toca con el carro en marcha va abajo y grande. Las siete
    zonas por debajo de 44 px que estan medidas son solo el minimo legal"*. Las pruebas de
    codigo comprueban que la clase esta escrita; **esto mide lo que el navegador pinta**,
    que es otra cosa: un elemento con la clase puede quedar comprimido por su contenedor, y
    otro sin clase puede medir 16 px sin que nadie lo note. Medido el 23 de septiembre de
    2026 en un movil de 390 x 844, esto encontro tres: el desplegable «Estado de las
    cadenas» (358 x 24), los «Por que esta en esta posicion» de la ficha (306 x 16) y el
    enlace «Cesta» de la cabecera (**43** px de ancho, un pixel por debajo).

    Dos cosas que la medida tiene que tener en cuenta para no mentir:

      - **Un `input` dentro de un `<label>` no es el objetivo**: el objetivo es el label, que
        es lo que se pulsa. Los cinco filtros del buscador salen como `input` de 16 px, y su
        etiqueta mide los 44 que manda el diseno.
      - **Un enlace dentro de una frase no es un control**: «...buscalo en la cesta» son
        palabras, no un boton, y agrandarlas romperia el texto. Se marcan y se dejan estar.
    """
    return pagina.evaluate("""() => {
      const caja = (n) => {
        const r = n.getBoundingClientRect();
        return {w: Math.round(r.width), h: Math.round(r.height)};
      };
      return [...document.querySelectorAll(
          'button, a, select, summary, [role=button], input[type=checkbox]')]
        .filter(n => {
          const r = n.getBoundingClientRect();
          const s = getComputedStyle(n);
          return r.width > 0 && r.height > 0 && s.display !== 'none'
                 && s.visibility !== 'hidden';
        })
        .map(n => {
          const objetivo = (n.tagName === 'INPUT' && n.closest('label')) || n;
          const c = caja(objetivo);
          return {
            texto: (n.innerText || n.getAttribute('aria-label') || n.value || '')
                     .trim().slice(0, 34).replace(/\\n/g, ' '),
            w: c.w, h: c.h, rol: n.tagName.toLowerCase(),
            enFrase: n.tagName === 'A' && n.closest('p') !== null,
          };
        })
        .filter(t => t.w < 44 || t.h < 44);
    }""")


def _ean_con_comparacion() -> str | None:
    """Un codigo de barras de verdad que este en tres cadenas o mas.

    Es como empieza la pregunta 2 de verdad: **escaneando lo que tienes en la mano**. Un
    codigo que solo exista en una cadena no puede contestar «¿esto esta caro?», asi que no
    sirve para esta prueba. Cual es hoy es cosa del catalogo: se pregunta a gold.
    """
    try:
        from plataforma.api import catalogo
    except Exception:  # noqa: BLE001
        return None
    try:
        fila = catalogo.conexion().execute("""
            SELECT ean FROM buscable
             WHERE ean IS NOT NULL AND ean <> '' AND precio_unidad_cent > 0
             GROUP BY ean HAVING count(DISTINCT fuente) >= 3
             ORDER BY count(DISTINCT fuente) DESC, ean LIMIT 1""").fetchone()
    except Exception:  # noqa: BLE001
        return None
    return str(fila[0]) if fila else None


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
            _carga(pagina, ruta)

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
        print("\n== entrar (como alguien que ya tiene cuenta)")
        carga("/cesta")
        comprueba(pagina.get_by_text("Entra para ver tu lista").count() >= 1,
                  "sin sesion la lista pide entrar, y lo explica")
        estado = _entra(pagina, USUARIO, CLAVE, "Madre", comprueba)
        if estado == "creado":
            print(f"   (la cuenta {USUARIO} no existia: se ha creado, una vez)")
        carga("/cesta")
        cuerpo_entrada = pagina.inner_text("body")
        comprueba(estado != "sin-sesion" and "Entra para ver tu lista" not in cuerpo_entrada,
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

        # ------------------------------- y lo que se pulsa, medido de verdad (§3.3) -------
        # Un objetivo que no se acierta es un boton que no existe: la condicion (a) dice
        # "sin saber donde esta el boton", y 16 px de alto no se aciertan ni mirando.
        print("\n== lo que se pulsa, medido ya pintado")
        rutas = ["/", "/cesta"]
        if solo_uno is not None:
            rutas.append(f"/grupo/{solo_uno}")
        rutas += ["/avisos", "/panel", "/ajustes"]
        for ruta in rutas:
            carga(ruta)
            pagina.wait_for_timeout(800)
            pequenos = _toques_pequenos(pagina)
            graves = [t for t in pequenos if not t["enFrase"]]
            for t in pequenos:
                print(f"   {'(frase)' if t['enFrase'] else 'FALLO '} {t['w']:4d} x"
                      f"{t['h']:3d}  {t['rol']:8s} {t['texto']!r}")
            resumen = ", ".join(
                "{}x{} {}".format(t["w"], t["h"], t["texto"]) for t in graves)
            comprueba(not graves,
                      f"en {ruta} no hay nada que pulsar por debajo de 44 px ({resumen})")

        # -------------------------- el enlace de invitacion, abierto por otra persona ----
        # Que la lista sea de quien la creo **y de quien entre** lleva escrito desde el
        # primer dia (`docs/AMIGOS.md`), y no lo habia abierto un navegador nunca: se probaba
        # el endpoint, no el enlace. Aqui se hace el viaje entero y con dos personas: la de
        # siempre manda el enlace desde su cesta, y la segunda -- otra sesion, otro aparato,
        # sin nada en comun -- lo abre tal como lo abre quien lo recibe: en el movil y sin
        # cuenta todavia.
        print("\n== el enlace de invitacion, abierto por otra persona")
        carga("/cesta")
        # **Se anulan antes los que haya**, y no es adorno: la API admite tres enlaces
        # vivos por lista (`MAX_INVITACIONES_VIVAS`, `almacen.py:645`) y contesta 409 al
        # cuarto. Una prueba que crea uno en cada pasada dejaba la lista sin poder invitar a
        # nadie en la cuarta vuelta -- y fallaba ella, no la aplicacion. Anulando primero se
        # mide ademas el otro camino, el de apagar un enlace que ya no vale.
        anular = pagina.get_by_role("button", name="Anular los enlaces que haya dado")
        comprueba(anular.count() == 1, "quien creo la lista puede anular los enlaces")
        if anular.count():
            anular.first.click()
            with contextlib.suppress(Exception):
                pagina.get_by_text("Anulad", exact=False).first.wait_for(timeout=15000)
            dicho = pagina.inner_text("main")
            comprueba("Anulados" in dicho or "No había ninguno" in dicho,
                      "y la pantalla dice cuantos ha anulado (o que no habia ninguno)")
            comprueba("A quien ya entró no le afecta" in dicho,
                      "y avisa de que anular no echa a quien ya esta dentro")
        crear = pagina.get_by_role("button", name="Crear un enlace")
        comprueba(crear.count() >= 1,
                  "quien creo la lista manda el enlace desde la pantalla (no por API)")
        enlace = ""
        if crear.count():
            crear.first.click()
            campo_enlace = pagina.get_by_label("Enlace de invitación")
            with contextlib.suppress(Exception):
                campo_enlace.wait_for(timeout=20000)
            if campo_enlace.count():
                enlace = campo_enlace.input_value()
            comprueba("/unirme/" in enlace,
                      f"el enlace sale escrito entero, con su codigo ({enlace[-14:]})")
            caduca = pagina.inner_text("main")
            comprueba("Caduca" in caduca and "personas que lo abran" in caduca,
                      "y dice cuando caduca y para cuantas personas vale")
        if not enlace:
            print("   (sin enlace no se puede seguir: la invitacion se queda sin comprobar)")
        else:
            ruta = enlace[len(BASE):] if enlace.startswith(BASE) else enlace
            # Otra sesion de verdad: contexto nuevo, sin cookies ni almacenamiento.
            contexto2 = navegador.new_context(
                viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True,
                locale="es-ES")
            otra = contexto2.new_page()
            otra.on("pageerror", lambda e: errores.append(f"[invitada] {e}"))
            _carga(otra, ruta)
            invitacion = otra.inner_text("body")
            comprueba("Te han invitado a una lista" in invitacion,
                      "quien abre el enlace sin cuenta ve que le han invitado, no un error")
            comprueba("barra de direcciones" in invitacion,
                      "y le dicen que el codigo no se pierde al entrar")
            # Se entra **aqui**, sin salir de la ruta: el codigo vive en la barra de
            # direcciones, y una pantalla que navegara antes de aplicar la invitacion lo
            # perderia (`Unirse.tsx:14`).
            estado2 = _entra(otra, USUARIO_INVITADA, CLAVE, "Invitada", comprueba,
                             puerta="Te han invitado a una lista")
            print(f"   (la invitada: {estado2})")
            # **Llegar a la cesta es la prueba**: la pantalla del enlace navega sola, y
            # solo cuando la invitacion se aplica (`Unirse.tsx:52`). Si sigue en `/unirme`,
            # o no ha entrado o la API ha dicho 429 (demasiadas altas en la ultima hora).
            with contextlib.suppress(Exception):
                otra.wait_for_url("**/cesta", timeout=20000)
            otra.wait_for_load_state("networkidle")
            traida = otra.inner_text("body")
            comprueba("/cesta" in otra.url and "unirme" not in otra.url,
                      f"al aplicarse lleva a la cesta, y no deja el enlace a mano ({otra.url})")
            # **Los dos estados valen, a proposito.** La cuenta es la misma en cada pasada:
            # la primera vez entra, y a partir de la segunda la API dice que ya estaba
            # dentro (y no gasta un uso del enlace, `almacen.py:493`). Una prueba que solo
            # acepte el primer estado obliga a crear una cuenta nueva cada vez, y las altas
            # estan limitadas por hora.
            recien = "Ya estás en" in traida
            ya_estaba = "Ya estabas en" in traida
            comprueba(recien or ya_estaba,
                      "y dice a que lista ha entrado, con el nombre que le puso quien la creo")
            comprueba(not recien or "quien te la mandó te ha dejado" in traida,
                      "y con que papel: escribir o solo mirar, dicho en castellano")
            # **Lo que se ve dentro**: la lista que abrio la otra persona es la misma, con
            # la linea que hay dentro. Sin esto, "te meto en la lista" seria solo una frase.
            with contextlib.suppress(Exception):
                otra.locator("input[type=checkbox]").first.wait_for(timeout=20000)
            comprueba(otra.locator("input[type=checkbox]").count() >= 1,
                      "la invitada ve las lineas que ya estaban puestas")
            # Y quien no creo la lista **no puede invitar**: la API contesta 403 y la
            # pantalla no ensena el boton, en vez de ensenar uno que no puede funcionar.
            comprueba(otra.get_by_role("button", name="Crear un enlace").count() == 0,
                      "y no le sale el boton de invitar, porque la lista no es suya")
            # Y de vuelta en la lista de quien invito: la otra persona **aparece**.
            carga("/cesta")
            dentro = pagina.inner_text("body")
            comprueba("Invitada" in dentro or USUARIO_INVITADA in dentro,
                      "quien invito ve a la otra persona en «Quién está dentro»")
            contexto2.close()

        # ------------------------------- el contraste del texto, pintado y en los dos temas --
        # §1 del encargo: *"el contraste y los limites de los campos, con las formulas dentro
        # de las pruebas. Eso es accesibilidad de verdad y esta medida"*. `tests/test_contraste.py`
        # mide los **tokens** del CSS; esto mide el texto **pintado**, resolviendo el fondo
        # real de cada uno (que casi nunca es el del propio elemento) y **en los dos temas**:
        # un `dark:` que falte no se ve en los tokens y si se ve aqui.
        print("\n== el contraste del texto, ya pintado (§1)")
        for tema in ("light", "dark"):
            pagina.emulate_media(color_scheme=tema)
            for ruta in ("/", "/cesta", "/avisos"):
                carga(ruta)
                pagina.wait_for_timeout(600)
                malos = _contraste_flojo(pagina)
                detalle = "; ".join(
                    "{:.2f}<{} {}px {!r}".format(m["cr"], m["minimo"], m["px"], m["texto"])
                    for m in malos[:4])
                comprueba(not malos,
                          f"en {ruta} con el tema {tema} todo el texto se lee ({detalle})")
        # **Y la prueba de que la medida mira**: un texto ilegible puesto a mano tiene que
        # salir. Sin esto, un `0` puede significar "todo bien" o "no he mirado nada".
        pagina.emulate_media(color_scheme="light")
        carga("/")
        pagina.evaluate(_TRAMPA)
        vistos = _contraste_flojo(pagina)
        comprueba(any("no se lee" in m["texto"] for m in vistos),
                  "la medida del contraste ve un texto ilegible puesto a mano")

        # --------------------------------- el escaner: la pregunta 2 de verdad, en la tienda --
        # §3 del encargo: la lista y la ficha se usan **de pie y con una mano**, y lo que
        # se tiene en la mano se escanea. Hasta hoy la pantalla del escaner no la habia
        # abierto un navegador: se probaba el endpoint, no la pantalla. Aqui se teclea un
        # codigo de verdad -- el camino manual, que es el que funciona cuando la camara no
        # esta o no hay permiso -- y se comprueba que contesta.
        print("\n== el escaner, con un codigo de verdad")
        ean = _ean_con_comparacion()
        if ean is None:
            print("   (no he encontrado un codigo con comparacion: no se puede comprobar)")
        else:
            carga("/escaner")
            comprueba(pagina.locator("#ean").count() == 1,
                      "el escaner deja escribir el codigo a mano (sin camara tambien vale)")
            t0 = time.monotonic()
            pagina.locator("#ean").fill(ean)
            pagina.get_by_role("button", name="Buscar").first.click()
            with contextlib.suppress(Exception):
                pagina.get_by_text("€", exact=False).first.wait_for(timeout=20000)
            pagina.wait_for_timeout(800)
            tiempos.append(("escanear un codigo", time.monotonic() - t0))
            texto_ean = pagina.inner_text("main")
            comprueba(ean in texto_ean or "€/" in texto_ean,
                      f"el codigo {ean} contesta con el producto y su precio")
            comprueba("No conozco" not in texto_ean and "no lo sé" not in texto_ean.lower(),
                      "y no dice que no lo conoce, porque lo conoce")
            # Y un codigo que no existe: tiene que decir que no lo sabe, no romperse.
            pagina.locator("#ean").fill("0000000000000")
            pagina.get_by_role("button", name="Buscar").first.click()
            pagina.wait_for_timeout(2500)
            texto_malo = pagina.inner_text("main")
            comprueba("no lo" in texto_malo.lower() or "no conozco" in texto_malo.lower()
                      or "desconocido" in texto_malo.lower(),
                      "un codigo que no esta dice que no lo sabe, en vez de callarse")
            comprueba(not errores, f"y la pantalla no se rompe ({errores[:2]})")

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
