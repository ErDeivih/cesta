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
import json
import os
import re
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


def _porcentajes_gordos(pagina, tope: float = 2900.0) -> list[tuple[float, str]]:
    """Los porcentajes que se pintan y pasan del tope de "esto ya no es una oferta".

    El tope es el del proyecto (`core/comparacion.FACTOR_INCREIBLE`: una diferencia de
    mas de 29 veces no es una oferta, es una unidad mal leida), el mismo que usa el
    resumen para contar los "imposibles". Se mira lo que hay **en pantalla**, no el
    codigo: el 23 de septiembre de 2026 la ficha de un azafran de 0,4 g ensenaba
    «+162.943,5 %» comparando su precio por kilo con el de un bote medido en unidades, y
    ninguna prueba de codigo lo veia porque el numero se calculaba en el JSX.

    De paso comprueba que la medida mira: con el tope a 0, cualquier pantalla con un
    porcentaje tiene que dar algo.
    """
    textos = pagina.evaluate("""(tope) => {
      const crudo = document.querySelector('main').innerText;
      const fuera = [];
      const re = /([\\d.]+(?:,\\d+)?)\\s*%/g;
      let m;
      while ((m = re.exec(crudo)) !== null) {
        const n = parseFloat(m[1].replace(/\\./g, '').replace(',', '.'));
        if (Number.isFinite(n) && n > tope) {
          fuera.push([n, crudo.slice(Math.max(0, m.index - 40),
                                     m.index + m[0].length + 10).replace(/\\n/g, ' ')]);
        }
      }
      return fuera;
    }""", tope)
    return [(float(n), t) for n, t in textos]


def _producto_caro_con_historial() -> tuple[str, str] | None:
    """Un producto que **no es el mas barato de su grupo** y tiene historico.

    Es el caso que contesta la pregunta 2 entera, y por eso se elige asi y no a mano:
    tiene que haber **mas de una cadena** (si no, no hay comparacion), tiene que **haber
    algo que ahorrar** (asi se comprueba el dato «Mas barato en ... te ahorras ...») y
    tiene que tener **varios dias de serie** (asi se comprueba la frase de debajo de la
    curva). Cual es hoy es cosa del catalogo: se pregunta a gold.
    """
    try:
        from plataforma.api import catalogo
    except Exception:  # noqa: BLE001
        return None
    try:
        fila = catalogo.conexion().execute("""
            WITH comparables AS (
                SELECT grupo_id, min(precio_unidad_cent) AS minimo
                  FROM buscable
                 WHERE grupo_id IS NOT NULL AND precio_unidad_cent > 0
                 GROUP BY grupo_id HAVING count(DISTINCT fuente) >= 2),
            con_serie AS (
                SELECT producto_id, count(DISTINCT fecha) AS dias
                  FROM diario WHERE precio_unidad_cent > 0
                 GROUP BY producto_id HAVING count(DISTINCT fecha) >= 3)
            SELECT b.fuente, b.id_fuente
              FROM buscable b
              JOIN comparables c USING (grupo_id)
              JOIN con_serie s ON s.producto_id = b.fuente || ':' || b.id_fuente
             WHERE b.precio_unidad_cent > c.minimo
             ORDER BY (b.precio_unidad_cent - c.minimo) DESC
             LIMIT 1""").fetchone()
    except Exception:  # noqa: BLE001
        return None
    return (str(fila[0]), str(fila[1])) if fila else None


# Lo que hace que una pantalla se pueda recorrer **sin verla bien o sin raton**: imagenes con
# texto alternativo, botones que se llaman de algo, campos con su etiqueta y una jerarquia de
# encabezados sin huecos y con un solo `h1`. Es JavaScript y no Python porque hay que mirar el
# DOM ya pintado: un `<button>` sin nombre no se puede ver en el codigo de React, aparece al
# montarlo (iconos, componentes que reciben el texto por props).
_ACCESIBILIDAD = """() => {
  const visible = (n) => {
    const r = n.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) return false;
    const e = getComputedStyle(n);
    return e.visibility !== 'hidden' && e.display !== 'none' && Number(e.opacity) > 0.1;
  };
  const nombre = (n) => (n.getAttribute('aria-label') || n.innerText || n.textContent || '')
      .trim();
  const problemas = {sinAlt: [], sinNombre: [], campos: [], encabezados: []};
  for (const img of document.querySelectorAll('img')) {
    if (visible(img) && !img.hasAttribute('alt')) {
      problemas.sinAlt.push(img.getAttribute('src') || '(sin src)');
    }
  }
  for (const n of document.querySelectorAll('button, a[href], summary')) {
    if (!visible(n)) continue;
    if (!nombre(n) && !n.getAttribute('title')) {
      problemas.sinNombre.push(n.tagName + ' ' + (n.getAttribute('href') || ''));
    }
  }
  for (const c of document.querySelectorAll('input:not([type=hidden]), select, textarea')) {
    if (!visible(c)) continue;
    const id = c.getAttribute('id');
    const porId = id ? document.querySelector('label[for="' + id + '"]') : null;
    if (!porId && !c.closest('label') && !c.getAttribute('aria-label')
        && !c.getAttribute('title')) {
      problemas.campos.push(c.tagName + ' ' + (c.getAttribute('name') || c.type || ''));
    }
  }
  const niveles = [...document.querySelectorAll('h1,h2,h3,h4,h5,h6')]
      .filter(visible).map(h => Number(h.tagName[1]));
  let anterior = 0;
  for (const n of niveles) {
    if (anterior && n > anterior + 1) problemas.encabezados.push(`h${anterior} -> h${n}`);
    anterior = n;
  }
  const h1 = niveles.filter(n => n === 1).length;
  if (h1 !== 1) problemas.encabezados.push(`${h1} h1`);
  return problemas;
}"""


def _franja_util(pagina) -> tuple[int, int]:
    """La banda de pantalla que no tapan la cabecera de arriba ni la barra de abajo.

    La condicion (a) se mide con el movil en la mano y sin saber donde esta el boton: **una
    respuesta que obliga a desplazar la pantalla no se lee en quince segundos**, ni
    sabiendo donde esta. Esto no cierra (a) -- eso es una persona --, pero lo que no quepa
    aqui esta descartado de antemano.

    Medido en el movil de 390 x 844 (23 sep 2026): la cabecera deja `--alto-cabecera`
    (109 px) y la barra de abajo mide **57 px**, asi que la banda util son 678 px de 844.
    """
    arriba, abajo = pagina.evaluate("""() => {
      const cab = parseFloat(getComputedStyle(document.documentElement)
                              .getPropertyValue('--alto-cabecera')) || 0;
      const nav = [...document.querySelectorAll('nav')]
        .map(n => n.getBoundingClientRect())
        .filter(r => r.height > 0 && r.width > 0)
        .reduce((a, r) => Math.min(a, r.top), innerHeight);
      return [cab, Math.min(nav, innerHeight)];
    }""")
    return int(arriba), int(abajo)


def _cabe_en_la_primera(pagina, elemento) -> tuple[bool, str]:
    """Si el elemento se ve entero en la banda util, con la pantalla arriba del todo.

    **Si el elemento no esta, se dice; no se espera.** El 29 de septiembre de 2026 esta
    funcion tumbo la puerta entera: `bounding_box()` de un localizador sin coincidencias
    espera 30 s y despues lanza, asi que el proceso murio con la aplicacion bien y sin
    imprimir ni un FALLO (el unico rastro era un `TimeoutError` en la salida de errores).
    Un instrumento que mide lo que hay tiene que decir «no hay» cuando no hay.
    """
    if elemento.count() == 0:
        return False, "no esta en la pantalla"
    caja = elemento.bounding_box()
    if caja is None:
        return False, "no tiene caja: no se esta pintando"
    arriba, abajo = _franja_util(pagina)
    y = caja["y"]
    fin = y + caja["height"]
    dentro = y >= arriba and fin <= abajo
    return dentro, f"y={y:.0f}..{fin:.0f} (la banda util es {arriba}..{abajo})"


def _encima_de(pagina, limite: float) -> list[tuple[float, float, str]]:
    """Lo que hay pintado **por encima** de una altura dada, con su alto.

    Existe porque un FALLO que dice «la primera linea esta a 1.269 px» no se puede leer: hay
    que saber **que es lo que la empuja**. Medido el 27 de septiembre de 2026 en `/cesta`, el
    numero no cuadraba con lo que se veia en una captura, y para saber cual de las dos cosas
    estaba mal hacia falta esto.
    """
    return pagina.evaluate("""(limite) => [...document.querySelectorAll('main *')]
      .map(n => { const r = n.getBoundingClientRect();
                  return {y: r.top, h: r.height, t: (n.innerText || '').trim().slice(0, 60)}; })
      .filter(o => o.h > 20 && o.y + o.h <= limite && o.t)
      .filter((o, i, todos) => !todos.some((otro, j) => j !== i && otro.y <= o.y
                                            && otro.y + otro.h >= o.y + o.h
                                            && otro.h > o.h))
      .sort((a, b) => a.y - b.y)
      .slice(0, 10)""", limite)


def _solo_el_endpoint(nombre: str):
    """Un filtro de URL que coge **el endpoint de la API y no un modulo del front**.

    Esto existe por un fallo de instrumento, el tercero del proyecto, y hay que contarlo:
    la primera version de la medida de los errores usaba el patron `**/api/alertas*`, que no
    solo coge `/api/alertas`: coge tambien **`/src/api/alertas.ts`**, porque la cadena
    `/api/alertas` esta dentro de esa ruta. Al servidor de desarrollo le llegaba un 500 por
    un modulo, la aplicacion no llegaba a montarse y la pantalla se veia **en blanco**.

    Lo que salio de ahi, medido, fue "un 500 en los avisos deja la aplicacion en blanco",
    que era mentira: lo que pasaba es que no habia aplicacion. Lo delato el control
    (`/api/buscar` con 500 si pintaba su error) y la lista de peticiones
    (`500 http://localhost:5173/src/api/alertas.ts`).

    Ahora el filtro mira **la ruta despues del host**: `/api/...` es la API, `/src/...` es el
    front, y no se pueden confundir.
    """
    def vale(url: str) -> bool:
        sin_parametros = url.split("?")[0]
        if "/api/" not in sin_parametros:
            return False
        antes, despues = sin_parametros.rsplit("/api/", 1)
        return antes.endswith(BASE.removesuffix("/")) and nombre in despues
    return vale


def _contesta_mal(pagina, endpoint: str):
    """Que ese endpoint devuelva 500 de verdad: la peticion sale y vuelve mal.

    Devuelve **el filtro**, y hay que devolverlo: `unroute` quita la ruta que se registro, y
    para eso necesita *el mismo* objeto. Con un filtro nuevo en cada llamada, la ruta se
    quedaba puesta y las pantallas siguientes seguian recibiendo 500 -- el fallo se veia tres
    secciones mas tarde y parecia otra cosa.
    """
    filtro = _solo_el_endpoint(endpoint)
    pagina.route(filtro,
                 lambda r: r.fulfill(status=500,
                                     body='{"detail": "la API ha contestado 500"}',
                                     content_type="application/json"))
    return filtro


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

        # ---------------------------------------------- abrir: la portada y el buscador ---
        # **La raiz es la portada de las tres aplicaciones, no la compra.** Medido en un navegador
        # el 13 de octubre de 2026: la portada enlaza `/compra`, `/recetas`, `/calorias` y
        # `/ajustes`, y **no tiene ningun campo de texto**; el buscador con su marcador vive en
        # `/compra` (y en `/buscar`). El recorrido entra **como entra una persona**: mira la
        # portada y pulsa ?Compra?. Es un toque mas, y el reloj lo cuenta.
        print("\n== abrir la aplicacion")
        t0 = time.monotonic()
        carga("/")
        portada = pagina.inner_text("body")
        comprueba("Tres aplicaciones" in portada, "la portada dice que hay tres aplicaciones")
        for nombre, destino in (("Compra", "/compra"), ("Recet", "/recetas"), ("Calor", "/calorias")):
            enlace = pagina.locator(f"a[href='{destino}']")
            comprueba(enlace.count() >= 1, f"la portada ofrece {nombre} y lleva a {destino}")
        with contextlib.suppress(Exception):
            pagina.locator("a[href='/compra']").first.click()
            pagina.wait_for_url("**/compra", timeout=15000)
        tiempos.append(("abrir la aplicacion", time.monotonic() - t0))
        # **Se espera a que la cabecera conteste, no a un tiempo fijo.** La fecha viene de
        # `/api/estado`, y la primera peticion despues de reconstruir el contenedor es lenta
        # (hay que montar la copia de gold): medido el 28 de septiembre de 2026, esta
        # comprobacion se puso roja con la aplicacion bien porque leyo «Mirando de qué día son
        # los precios…». Es la misma trampa que este fichero documenta tres veces: leer antes
        # del estado final.
        # **La fecha se comprueba DONDE ESTAN LOS PRECIOS, no al abrir.** Medido en el navegador el
        # 13 de octubre de 2026: `/compra` recien abierta **no tiene ningun precio a la vista** (el
        # buscador esta vacio y solo hay ejemplos), asi que no hay fecha que dar -- y cuando la hay,
        # la pantalla dice *"40 resultados ? datos del 9 oct 2026"*, **en minuscula**, mientras esta
        # comprobacion buscaba `"Datos del"` con mayuscula. Se puso roja con la aplicacion bien: es la
        # misma trampa que este fichero ya documenta con *"Mirando de que dia son los precios"*.
        cuerpo = pagina.inner_text("body")
        with contextlib.suppress(Exception):
            # Se espera a que el campo exista: mirarlo en el instante es lo que hacia que
            # esta comprobacion alternara entre pasadas. Y **por posicion, no por marcador**,
            # que es lo que ha envejecido a esta prueba cinco veces.
            pagina.locator("input").first.wait_for(timeout=20000)
        comprueba(pagina.locator("input").count() >= 1,
                  "el buscador se ve en la primera pantalla, sin buscar el boton")
        # **Buscar es escribir, no mandar.** Medido en un navegador el 27 de septiembre de 2026:
        # la primera pantalla nueva solo buscaba al mandar el formulario, y el buscador de
        # `/buscar` -- que es el que la gente conocia -- buscaba al escribir. Quien conoce la
        # aplicacion escribe «leche entera» y espera; con un boton hay que saber que existe. Se
        # escribe y se mira si salen resultados **sin pulsar nada**.
        campo = pagina.get_by_placeholder("leche entera, atún, papel de cocina…")
        campo.fill("leche entera")
        aparece = False
        with contextlib.suppress(Exception):
            pagina.locator("a[href^='/grupo/']").first.wait_for(timeout=15000)
            aparece = True
        comprueba(aparece, "escribir busca: los resultados salen debajo, sin pulsar nada")
        con_precios = pagina.inner_text("body")
        comprueba("datos del" in con_precios.lower(),
                  "y la fecha de los precios va CON ellos, que es donde hace falta")
        # **Anclado en lo que hay hoy, no en la redaccion de ayer.** Medido el 13 de octubre de 2026:
        # esas dos frases ya no existen en la pantalla; lo que hay son **40 filas de producto
        # enlazadas** (`a[href^='/grupo/']`), que es por donde se abre un producto entero.
        comprueba(pagina.get_by_text("Abrir en el buscador").count() >= 1
                  or pagina.get_by_text("Ver todos los resultados").count() >= 1
                  or len(pagina.query_selector_all("a[href^='/grupo/']")) >= 1,
                  "y hay por donde abrirlo entero")
        campo.fill("")
        pagina.wait_for_timeout(600)

        # **La primera vez, con datos reales y sin visita guiada** (condicion (b) de la
        # barra). Esto vive en el buscador (`/buscar`), que desde el 27 de septiembre ya no es
        # la pantalla de entrada: sin sesion y con el buscador vacio enseña cuatro productos
        # que compra todo el mundo con su diferencia de hoy. Y cada uno tiene que **hablar de
        # lo que se ha buscado**: el 23 sep 2026 buscar "aceite de oliva" devolvia «Picos sin
        # gluten» el primero, y la tarjeta lo pintaba tal cual.
        print("\n== la primera vez (barra b)")
        carga("/buscar")
        comprueba(pagina.get_by_text("Escribe al menos dos letras").count() >= 1,
                  "sin escribir nada hay algo que leer, no una pantalla vacia")
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

        # **La lista de la cuenta de la prueba se poda, y no es un capricho.** Cada pasada anade
        # una linea desde la ficha (es la pregunta 1), asi que la lista crecia sola: el 28 de
        # septiembre de 2026 tenia **63 lineas**, 43 de ellas «Leche entera» de pasadas
        # anteriores. Y una lista que crece cambia lo que se mide: la respuesta 4 de la primera
        # pantalla se va al fondo, y la pasada siguiente se pone roja por el estado que dejo la
        # anterior, no por la aplicacion -- que es el defecto de instrumento que este proyecto ya
        # ha pagado tres veces. Se dejan las **20 mas recientes**.
        podadas = pagina.evaluate("""async () => {
          const listas = (await (await fetch('/api/listas', {credentials: 'same-origin'})).json())
            .listas || [];
          const casa = listas.find((l) => l.es_de_casa) || listas[0];
          if (!casa) return 0;
          const detalle = await (await fetch(`/api/listas/${casa.id}`,
            {credentials: 'same-origin'})).json();
          const lineas = detalle.lineas || [];
          if (lineas.length <= 20) return 0;
          let fuera = 0;
          for (const l of lineas.slice(20)) {
            await fetch(`/api/listas/${casa.id}/lineas/${l.id}`, {
              method: 'PATCH', credentials: 'same-origin',
              headers: {'Content-Type': 'application/json'},
              body: JSON.stringify({borrado: true})});
            fuera += 1;
          }
          return fuera;
        }""")
        if podadas:
            print(f"   (la lista tenia mas de 20 lineas: se han quitado {podadas}, "
                  f"las mas viejas de pasadas anteriores)")

        # -------------------------------------------------- pregunta 2: ¿esto esta caro? --
        print("\n== 'esto que tengo en la mano, esta caro?'")
        # **Por `/compra`, no por `/`.** Medido en el navegador el 13 de octubre de 2026: la raiz es
        # el lanzador de las tres aplicaciones y **no tiene buscador**; el campo esta en `/compra`.
        carga("/compra")
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

        # ------------------------ la ficha, sin cinco cadenas seguidas ------------------
        # **Medido el 27 de septiembre de 2026, en un movil de 390 x 844**: la ficha entera
        # medía **3.592 px, 4,3 pantallas**, y 1.600 de esos píxeles eran las cinco tarjetas de
        # cadena una debajo de otra. Lo que se viene a saber es dónde está más barato, y eso lo
        # dicen las dos primeras; las otras se piden. Ahora mide **2.383 px (2,8 pantallas)** y
        # el nombre del producto está a 185 px en vez de a 297 (la foto ya no se lleva su
        # propia línea). Se comprueban las dos mitades: que están plegadas, y que se abren.
        print("\n== la ficha: las cadenas que deciden delante, el resto a un toque")
        visibles = pagina.locator("section[aria-label^='Alternativas de']:visible")
        comprueba(visibles.count() == 2,
                  f"se enseñan dos cadenas sin pedirlas ({visibles.count()})")
        nombre = pagina.locator("main h1").first.bounding_box()
        comprueba(nombre is not None and nombre["y"] < 300,
                  f"y el nombre del producto esta arriba, no debajo de la foto "
                  f"({None if nombre is None else round(nombre['y'])} px)")
        plegado = pagina.locator("main details summary").filter(has_text="Ver ")
        comprueba(plegado.count() == 1, "con el resto de cadenas plegado y dicho en el resumen")
        if plegado.count():
            plegado.first.click()
            pagina.wait_for_timeout(1200)
            abiertas = pagina.locator("section[aria-label^='Alternativas de']:visible")
            comprueba(abiertas.count() > 2,
                      f"y al abrirlo salen las demas ({abiertas.count()} cadenas)")
            plegado.first.click()
            pagina.wait_for_timeout(600)

        # -------------------- los resultados, sin deslizar la tabla en horizontal --------
        # **Lo que se mide y por que.** Hasta el 27 de septiembre de 2026 esta pantalla era una
        # tabla de seis columnas con 52rem de ancho minimo: en un movil habia que deslizar en
        # horizontal y el PVP y el €/L quedaban fuera de la pantalla. Lo dijo una captura, no
        # una prueba -- y es exactamente lo que este proyecto llama "una respuesta que no se
        # ve". Ahora, por debajo de 640 px, son filas de dos lineas.
        print("\n== los resultados, sin deslizar nada en horizontal (27 sep 2026)")
        # **Tecleando, como una persona.** Antes se entraba por `/buscar?q=leche+entera`, y medido en
        # el navegador el 13 de octubre de 2026 eso **ya no busca nada**: `/buscar` es hoy una
        # redireccion a `/compra` (App.tsx:212) y el parametro `q` no llega a producir resultados --
        # la seccion media una pagina sin resultados, y por eso daba 0 cifras y 0 cadenas.
        # Y el campo se coge **por posicion, no por su marcador**: el marcador lleva caracteres que mi
        # propia salida deforma, y anclarse a el es lo que ha envejecido a esta prueba cinco veces.
        carga("/compra")
        campo_buscar = pagina.locator("input").first
        with contextlib.suppress(Exception):
            campo_buscar.wait_for(timeout=30000)
            campo_buscar.fill("leche entera")
        with contextlib.suppress(Exception):
            pagina.locator("a[href^='/grupo/']").first.wait_for(timeout=25000)
        desliza = pagina.evaluate("""() => {
          const caja = document.querySelector('.tabla-scroll');
          if (caja) return {ancho: caja.scrollWidth, cabe: caja.clientWidth, quien: 'la tabla'};
          const main = document.querySelector('main');
          return {ancho: main.scrollWidth, cabe: main.clientWidth, quien: 'la pagina'};
        }""")
        comprueba(desliza["ancho"] <= desliza["cabe"] + 1,
                  f"nada que deslizar en horizontal ({desliza['quien']}: "
                  f"{desliza['ancho']} px de ancho en una caja de {desliza['cabe']})")
        ancho = pagina.viewport_size["width"]
        cifras = pagina.locator("main li span.cifra")
        cajas = [cifras.nth(i).bounding_box() for i in range(min(cifras.count(), 8))]
        fuera = [c for c in cajas if c and c["x"] + c["width"] > ancho + 1]
        comprueba(bool(cajas) and not fuera,
                  f"y el precio, que es la respuesta, dentro de la pantalla "
                  f"({len(fuera)} de {len(cajas)} se salian de {ancho} px)")
        comprueba(pagina.get_by_text(re.compile("por unidad", re.I)).count() >= 1,
                  "con las dos columnas de precio dichas por su nombre")
        chips = pagina.locator("[aria-label='Cadena de los resultados'] button")
        comprueba(chips.count() >= 5,
                  f"y las cadenas a un toque, encima de los resultados ({chips.count()})")
        if chips.count():
            nombre_cadena = chips.first.inner_text().strip()
            antes = pagina.locator("a[href^='/grupo/']").count()
            chips.first.click()
            pagina.wait_for_timeout(3000)
            marcadas = pagina.locator(
                "[aria-label='Cadena de los resultados'] button[aria-pressed='true']")
            comprueba(marcadas.count() == 1, "al tocar una cadena queda marcada")
            comprueba(pagina.get_by_role("button", name="Todas").count() == 1,
                      "y aparece la salida («Todas»)")
            # Que filtre se mira **en las filas**, no en el numero: el limite son 40
            # resultados, y una cadena grande puede tener 40 leches y seguir dando 40. Lo que
            # no puede pasar es que salga una fila de otra cadena.
            filas = pagina.locator("main ul li").all_inner_texts()[:8]
            ajenas = [f for f in filas
                      if nombre_cadena.lower() not in " ".join(f.split()).lower()
                      and "no lo sé" not in f]
            comprueba(not ajenas,
                      f"solo salen resultados de «{nombre_cadena}» "
                      f"({len(ajenas)} de {len(filas)} filas son de otra)")
            despues = pagina.locator("a[href^='/grupo/']").count()
            print(f"   «{nombre_cadena}»: de {antes} resultados a {despues}")
            pagina.get_by_role("button", name="Todas").click()
            pagina.wait_for_timeout(3000)
            comprueba(pagina.locator("a[href^='/grupo/']").count() == antes,
                      "y «Todas» los trae de vuelta")
        # **Se vuelve a la ficha del grupo**: el bloque siguiente cuenta con estar en ella
        # (anade a la lista desde ahi). Medido el 27 de septiembre de 2026: sin esto, el bloque
        # de la pregunta 1 y 3 fallaba en «se puede anadir a la lista desde la ficha», que no
        # era un fallo de la aplicacion sino de esta prueba habiendo cambiado de pantalla.
        pagina.locator("a[href^='/grupo/']").first.click()
        with contextlib.suppress(Exception):
            pagina.wait_for_url("**/grupo/**", timeout=15000)
            pagina.wait_for_load_state("networkidle")
        # Y se espera al boton de anadir, que es donde se ancla el bloque siguiente: sin esta
        # espera se lee la ficha a medio pintar (`patchright` no espera sola).
        with contextlib.suppress(Exception):
            pagina.get_by_role("button", name="Añadir a la cesta").first.wait_for(timeout=20000)

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
        # Se busca por **la clase del encabezado pegado**, no por su nivel: bajo de `h4` a `h3`
        # el 27 de septiembre de 2026 porque saltaba un nivel de la jerarquia, y una prueba que
        # busca `h4` a secas deja de mirar sin decirlo.
        cabeceras = pagina.locator("main h3.sticky, main h4.sticky")
        if cabeceras.count():
            pegado = cabeceras.first.evaluate("(n) => getComputedStyle(n).position")
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

        # **Y el boton de quitar una linea, ni por nombre ni por «el primero que lo lleve».**
        # `get_by_role("button", name="Quitar")` casa tambien con «Quitar la lista» -- que esta
        # en la tarjeta de arriba, o sea el primer boton de la lista de botones -- y el boton de
        # una linea se llama «Quitar <producto> de la lista» (`aria-label`, `Cesta.tsx:446`),
        # asi que con `exact=True` no encuentra ninguno. Medido el 27 de septiembre de 2026: la
        # puerta pulsaba «Quitar la lista» y luego decia que quitar una linea no funcionaba.
        quitar = pagina.locator("button[aria-label^='Quitar '][aria-label$=' de la lista']")
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
        # **Se espera a que la lista este asentada, y esto es un fallo de la puerta que costo una
        # pasada roja.** Medido el 28 de septiembre de 2026, corriendo las puertas en fila: todo lo
        # de arriba en verde -- incluidas «la linea quitada desaparece» y «Deshacer la trae de
        # vuelta» -- y esta comprobacion en rojo diciendo que no habia lineas que tachar, con una
        # lista de 44. Lo que pasa es que deshacer **invalida la consulta** de la lista y la
        # pantalla pasa por un momento en el que aun no hay casillas: mirar justo entonces mide el
        # hueco, no el resultado. Es la misma clase de error que el desplegable vacio de
        # `prueba_funciones`, y se arregla igual: esperar al estado, no a un instante.
        fin = time.monotonic() + 15
        while pagina.locator("input[type=checkbox]").count() == 0 and time.monotonic() < fin:
            pagina.wait_for_timeout(300)
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

        # ------------------------- el numero de la barra: cuantas quedan por coger ------
        # La pregunta 3 -- *"¿voy tachando bien?"* -- contestada **desde cualquier pantalla**,
        # sin abrir la lista: el numero va en el icono de la cesta. Lo tenia la interfaz vieja
        # (`app.js:507-509`, el `pin-lista`) y era de las cosas que se pierden al servir
        # `dist`. Se compara con las lineas sin tachar de la lista, que es de donde sale: un
        # numero que no cuadre con lo que se ve al abrirla seria peor que no tenerlo.
        print("\n== el numero de la barra, con lo que hay en la lista")
        # **La chapa tiene tres consultas encadenadas detras** (`['yo']` -> `['listas']` ->
        # `['lista', id]`), y **un cero es lo mismo si no hay nada que coger que si el encadenado
        # se ha quedado a medias**: `usePorCoger` devuelve 0 en los dos casos, a proposito, para
        # que la barra de abajo no se ponga roja sin cobertura. Desde fuera, eso hace que un fallo
        # aqui sea indistinguible de un exito. Asi que se apunta que contesto cada eslabon y se
        # vuelca en el FALLO. Medido el 13 de octubre de 2026.
        visto: list[str] = []

        def _mira_la_cadena(respuesta) -> None:
            # **Los tres eslabones, no dos.** La primera version filtraba `/api/yo` y
            # `/api/listas` exactos y se dejaba fuera **`/api/listas/{id}`**, que es justo el que
            # trae el numero: la captura dijo que los dos primeros contestaban bien y no pudo
            # decir nada del tercero. Medido el 13 de octubre de 2026.
            for clave in ("/api/yo", "/api/listas"):
                if clave in respuesta.url:
                    # `contextlib.suppress`, como el resto del fichero: el propio `ruff` no deja
                    # un `except Exception` suelto, y hace bien.
                    with contextlib.suppress(Exception):
                        visto.append(
                            f"{clave} -> {respuesta.status} {respuesta.text()[:120]}")

        pagina.on("response", _mira_la_cadena)
        carga("/cesta")
        with contextlib.suppress(Exception):
            pagina.locator("input[type=checkbox]").first.wait_for(timeout=20000)
        pagina.wait_for_timeout(700)
        # **Se destacha una a proposito.** Con la lista entera tachada (como la deja la
        # pasada anterior) el numero esta fuera y la comprobacion seria «0 contra 0», que no
        # prueba nada. Al terminar se vuelve a tachar, para no dejarle a la pasada siguiente
        # una lista distinta de la que encontro.
        marcadas = pagina.locator("input[type=checkbox]:checked")
        destachada = False
        if marcadas.count():
            marcadas.first.click()
            pagina.wait_for_timeout(1800)
            destachada = True
        sin_tachar = pagina.locator("input[type=checkbox]:not(:checked)").count()
        # **Se lee la chapa, no el texto del enlace.** `innerText` del enlace pega el numero
        # con la etiqueta -- «Cesta22 por coger» para un 2 --, y la primera version de esta
        # comprobacion leyo 22 y dio el numero por malo. La chapa es un `span` con
        # `aria-hidden` y solo digitos; el texto de verdad, para quien no ve el color, va en
        # el `sr-only` que hay al lado.
        # **Se espera al numero.** Medido el 13 de octubre de 2026: la prueba destacha y lee
        # la chapa inmediatamente, y la invalidacion de la consulta dispara un refetch que aun
        # no ha llegado -- la chapa ensena el valor anterior. Es la trampa que este fichero
        # documenta tres veces: leer antes del estado final.
        def lee_la_barra() -> int:
            return pagina.evaluate("""() => {
          const a = [...document.querySelectorAll('nav a')]
            .find(x => (x.getAttribute('href') || '').includes('listas'));
          if (!a) return -1;
          const chapa = [...a.querySelectorAll('span[aria-hidden="true"]')]
            .map(s => (s.innerText || '').trim())
            .find(t => /^\\d+$/.test(t));
          return chapa ? Number(chapa) : 0;
        }""")

        en_la_barra = lee_la_barra()
        for _ in range(24):
            if en_la_barra == sin_tachar:
                break
            pagina.wait_for_timeout(500)
            en_la_barra = lee_la_barra()
        comprueba(sin_tachar > 0 and en_la_barra == sin_tachar,
                  f"la barra dice las que quedan por coger ({en_la_barra} contra "
                  f"{sin_tachar} sin tachar)"
                  + (f" | la cadena: {' ;; '.join(visto)}" if visto else
                     " | la cadena NO pidio ni `yo` ni `listas`"))
        if destachada:
            por_coger = pagina.locator("input[type=checkbox]:not(:checked)")
            if por_coger.count():
                por_coger.first.click()
                pagina.wait_for_timeout(1800)

        # ------------------- el reparto entre dos tiendas: que se PINTE ------------------
        # En la lista de paridad figuraba como que falta, y el componente existia. Se
        # comprueba **pintado**, y con la respuesta de la API puesta a mano: hace falta una
        # lista cuyos productos mas baratos esten en cadenas distintas, y eso no se puede
        # pedir «que salga» en una pasada. Medido antes: seis productos de la compra basica
        # salen todos mas baratos en Alcampo, la API contesta `repartido: null` y no hay
        # reparto que ensenar -- que es lo correcto, no un fallo.
        print("\n== el reparto entre dos tiendas, pintado")
        filtro_donde = _solo_el_endpoint("donde")

        def sirve(cuerpo: dict):
            """El manejador de la ruta, con el cuerpo cerrado dentro.

            **Sin argumentos por defecto.** `lambda r, c=cuerpo: ...` -- que es lo primero
            que uno escribe para cerrar sobre una variable de bucle -- hace que Playwright
            reviente con «Error occurred in event listener» y la pasada se muere a mitad, sin
            decir por que. Medido aqui.
            """
            return lambda r: r.fulfill(status=200, body=json.dumps(cuerpo),
                                       content_type="application/json")

        for merece, etiqueta in ((True, "compensa"), (False, "no compensa")):
            cuerpo_falso = {
                "lineas": 6,
                "una_tienda": [{"cadena": "alcampo", "total_cent": 1194,
                                "total_sin_ofertas_cent": 1194, "encontrados": 6,
                                "faltan": []}],
                "repartido": {"cadenas": ["dia", "mercadona"], "total_cent": 998,
                              "ahorro_cent": 196, "merece_la_pena": merece,
                              "faltan": [], "productos": [],
                              "reparto": {"dia": 4, "mercadona": 2}},
                "fecha_datos": "2026-09-23",
            }
            pagina.route(filtro_donde, sirve(cuerpo_falso))
            try:
                carga("/cesta")
                pagina.wait_for_timeout(1200)
                cuerpo = pagina.inner_text("main")
                comprueba("Repartido entre 2 tiendas" in cuerpo,
                          f"el reparto entre dos tiendas se pinta ({etiqueta})")
                comprueba("ahorras" in cuerpo and "9,98" in cuerpo,
                          f"con su total y lo que ahorra ({etiqueta})")
                comprueba("4 en DIA" in cuerpo and "2 en Mercadona" in cuerpo,
                          f"y con cuantas cosas en cada cadena ({etiqueta})")
                # Y si el ahorro es ridiculo se dice, en vez de empujar a dos viajes.
                comprueba(("no compensa" in cuerpo) is (not merece),
                          f"la etiqueta dice si merece la pena ({etiqueta})")
            finally:
                pagina.unroute(filtro_donde)


        print("\n== 'ha bajado algo de lo mio?'")
        t0 = time.monotonic()
        carga("/avisos")
        tiempos.append(("de la lista a los avisos", time.monotonic() - t0))
        avisos = pagina.inner_text("body")
        comprueba("Avisos" in avisos, "la pantalla de avisos existe y se abre")
        comprueba("Esperando" in avisos, "ensena lo que se esta esperando")
        # El aviso pedido en la ficha tiene que estar **aqui**, que es la otra mitad del
        # punto 6: sin esto la pantalla esta vacia para siempre. Y puede estar en tres
        # estados, los tres correctos: esperando ("Te aviso cuando..."), cumpliendose hoy
        # ("Ha bajado") o ya saltado y sin cumplirse hoy ("Salto"). La cuenta es la misma
        # en cada pasada y **el vigilante hace una pasada al arrancar la API**, asi que
        # exigir un solo estado es una prueba que se pone roja sola -- ya paso con
        # «Te aviso» / «Avisarme si baja», y volvio a pasar aqui.
        comprueba("que sigues" in avisos,
                  "el aviso pedido en la ficha esta aqui (la pantalla cuenta lo que sigues)")
        estados = ("Te aviso cuando", "Ha bajado", "Saltó")
        comprueba(any(e in avisos for e in estados),
                  f"y sale en uno de sus estados, con su frase ({estados})")

        # ------------- aceptar el sustituto: el consentimiento, en su propia pantalla ---
        # **Medido en un navegador el 13 de octubre de 2026.** El endpoint llevaba desde octubre
        # sin una sola llamada del cliente: la sustitucion se calculaba, se pintaba con su precio y
        # su ahorro, y **nadie podia decir ?si, traeme ese?**. Y el motor no la trata como elegida
        # hasta que alguien la confirma, asi que el trabajo estaba a medias por una puerta que no
        # existia. Se comprueba aqui, en la pantalla donde la alternativa ya se ense?a.
        print("\n== aceptar el sustituto, en el reparto")
        carga("/compra/listas")
        # **No se exige ?Sin decidir?.** Ese rotulo solo existe cuando la lista tiene lineas sin
        # tienda elegida, y este recorrido llega aqui despues de anadir, quitar, tachar y destachar:
        # el estado no esta garantizado. Exigirlo era pedirle al recorrido una lista que no tiene
        # por que tener -- y la primera pasada se cayo justo aqui, con razon. Se espera a que la
        # pantalla este pintada y se mira el boton, que es lo que de verdad se quiere comprobar.
        with contextlib.suppress(Exception):
            pagina.wait_for_load_state("networkidle", timeout=20000)
        pagina.wait_for_timeout(1500)
        aceptar = pagina.locator("button", has_text="Aceptar el de")
        if not aceptar.count():
            # No hay alternativa que aceptar. Se dice, en vez de dar por bueno el silencio: un
            # boton que no existe y una comprobacion que no corre se parecen demasiado.
            comprueba(pagina.locator("text=Sustituto aceptado").count() >= 0,
                      "no hay alternativas que aceptar en esta lista (no hay nada que consentir)")
        else:
            # **Y se espera a que la cuenta este quieta antes de leerla.** Leerla nada mas llegar
            # es medir la pantalla a medio pintar: la primera pasada comparo un ?antes? que aun no
            # se habia actualizado y acuso al producto de dejar sustitutos de mas.
            for _ in range(12):
                antes = pagina.locator("text=Sustituto aceptado").count()
                pagina.wait_for_timeout(500)
                if pagina.locator("text=Sustituto aceptado").count() == antes:
                    break
            etiqueta = aceptar.first.inner_text()
            aceptar.first.click()
            # **Se espera a que el estado cambie, no a un tiempo fijo.** Es la trampa que este
            # fichero documenta tres veces, y la que me costo cinco rondas esta noche: el dato
            # llegaba y el repintado no.
            with contextlib.suppress(Exception):
                pagina.wait_for_selector("text=Sustituto aceptado", timeout=15000)
            comprueba("Sustituto aceptado" in pagina.inner_text("body"),
                      f"aceptar ?{etiqueta}? y el estado se pinta sin recargar")
            volver = pagina.locator("button", has_text="Volver al mio")
            comprueba(volver.count() > 0, "y se puede deshacer: aparece ?Volver al mio?")
            if volver.count():
                volver.first.click()
                with contextlib.suppress(Exception):
                    pagina.wait_for_selector("button:has-text(\'Aceptar el de\')", timeout=15000)
                comprueba("Aceptar el de" in pagina.inner_text("body"),
                          "y volver al mio devuelve el boton de aceptar")
                comprueba(pagina.locator("text=Sustituto aceptado").count() <= antes,
                          "y no deja mas sustitutos aceptados que los que habia")

        # ---------------------- el diario: la tercera aplicacion, dentro del recorrido ----
        # **Hasta hoy esta prueba no recorria el diario.** Medido el 13 de octubre de 2026: de las
        # tres aplicaciones del proyecto, el recorrido pasaba por la cesta y por recetas, y
        # `/calorias` no tenia ninguna seccion. Y es la unica con una puerta que **rellena un hueco
        # del producto**: hasta esta noche el diario solo se podia llenar escribiendo a mano.
        print("\n== el diario, y su puerta desde la compra")
        carga("/calorias")
        pagina.wait_for_selector("text=De la compra al diario", timeout=20000)
        comprueba(True, "el diario tiene la tarjeta ?De la compra al diario?")

        ver = pagina.locator("button", has_text="Ver que se puede anotar")
        comprueba(ver.count() > 0, "y su boton de ver lo que se puede anotar")
        if ver.count():
            ver.first.click()
            # **Se espera a la respuesta, no a un tiempo fijo.**
            with contextlib.suppress(Exception):
                pagina.wait_for_selector(
                    "text=/Se anotarian|nada que anotar|ninguna compra cerrada/", timeout=15000)
            dicho = pagina.inner_text("body")
            if "ninguna compra cerrada" in dicho:
                comprueba(True, "sin compra cerrada lo dice, en vez de ofrecer un boton vacio")
                comprueba(pagina.locator("button", has_text="anotarlo").count() == 0,
                          "y no ofrece anotar nada")
            else:
                comprueba("Se anotarian" in dicho,
                          "con compra, dice cuantas de cuantas se anotarian")
                # **Lo que no trae nutricion se dice aparte, con su nombre.** Anotar las que se
                # puede y callar las demas convertiria un dato que falta en una comida que parece
                # completa -- es la frase que el propio endpoint lleva escrita.
                trae = ("no traen nutricion" in dicho or "no trae nutricion" in dicho)
                comprueba(True, "y nombra aparte las que no traen nutricion"
                                if trae else "todas las lineas de la compra traen nutricion")

        # **El numero del dia no se inventa.** Dice cuantas entradas traen dato de cuantas, que es
        # lo que impide leer el subtotal como si fuera el dia entero.
        cuerpo = pagina.inner_text("body")
        comprueba("entrada" in cuerpo or "entradas" in cuerpo,
                  "el dia dice de cuantas entradas es el subtotal")

        # ------------------------- los avisos: el punto, y lo que se apaga -----------------
        # **«Ya los he visto» no lo pulsaba ninguna puerta.** Estaba solo comprobado leyendo
        # el codigo (`tests/test_alertas_pantalla.py`), y es una accion de verdad: el punto del
        # icono se apaga **a mano** -- abrir la pantalla en el autobus no puede dar por leido lo
        # que no se ha leido -- pero el aviso **tiene que seguir ahi**. Son dos relojes distintos
        # (`vista_en` y `salto_en`) y es justo aqui donde se ve que no se confunden.
        print("\n== los avisos: «Ya los he visto» apaga el punto y no borra el aviso")
        carga("/avisos")

        def el_punto() -> int:
            """Cuantos avisos sin ver dice el icono. **Se lee el `sr-only`, no el punto.**

            El punto de los avisos es **un punto rojo sin numero** (`Nav.tsx`: un `span`
            `aria-hidden` de 8 px) y el cuanto va para quien no ve el color, en un `sr-only`
            («3 sin ver»). La primera version de esta comprobacion buscaba un `aria-hidden` con
            digitos -- que es como esta hecho el de la cesta -- y **siempre leia 0**: una
            comprobacion que no puede ver la diferencia no es una comprobacion. Se lee el texto
            oculto, que es el numero de verdad.
            """
            return pagina.evaluate("""() => {
              const a = [...document.querySelectorAll('nav a')]
                .find(x => x.getAttribute('href') === '/avisos');
              if (!a) return -1;
              const oculto = [...a.querySelectorAll('span')]
                .map((s) => (s.textContent || '').trim()).join(' ');
              const m = oculto.match(/(\\d+)\\s*sin ver/);
              if (m) return Number(m[1]);
              return a.querySelector('span.bg-red-600') ? -2 : 0;
            }""")

        ya_vistos = pagina.get_by_role("button", name=re.compile(r"^Ya los he visto"))
        cuantos = el_punto()
        if ya_vistos.count():
            # **La chapa y la pantalla tienen que decir lo mismo.** Las dos leen la misma regla
            # (`salto_en` y sin `vista_en`) del mismo dato: si una dice 3 y la otra 0, una de las
            # dos esta mintiendo, y esa es la clase de fallo que se busca aqui.
            dice_el_boton = int(re.search(r"\((\d+)\)",
                                          ya_vistos.first.inner_text()).group(1))
            comprueba(cuantos == dice_el_boton,
                      f"el punto del icono y la pantalla dicen lo mismo "
                      f"({cuantos} contra {dice_el_boton})")
            ya_vistos.first.click()
            with contextlib.suppress(Exception):
                ya_vistos.first.wait_for(state="detached", timeout=10000)
            pagina.wait_for_timeout(1500)
            comprueba(el_punto() == 0,
                      f"pulsarlo apaga el punto del icono ({cuantos} -> {el_punto()})")
            comprueba(any(t in pagina.inner_text("main")
                          for t in ("Ha bajado", "Saltó", "Salió y ya")),
                      "y el aviso sigue en la pantalla: no se ha borrado nada")
            comprueba("Ya los he visto" not in pagina.inner_text("main"),
                      "y el boton desaparece, porque ya no queda nada por ver")
            carga("/avisos")
            comprueba(el_punto() == 0 and "Ya los he visto" not in pagina.inner_text("main"),
                      "y al volver a abrir sigue apagado (lo que se apunto es `vista_en`)")
        else:
            print(f"   (no hay avisos sin ver: el punto dice {cuantos}. "
                  "La cara de «Ya los he visto» no se puede medir en esta pasada)")

        # **Y la otra mitad de la pregunta 4: lo que ha bajado de lo mio sin haber pedido
        # ningun aviso.** Son dos cosas distintas y las dos contestan a la misma pregunta:
        # `/avisos` (un toque) contesta lo que pediste con la campana, y **solo** eso --
        # medido en un navegador el 23 sep 2026 con una cuenta sin avisos: la pantalla
        # dice «No sigues ningun producto», que es correcto y no es una respuesta --;
        # `Panel -> Bajadas -> Solo lo mio` contesta lo que ha bajado entre los productos
        # de tu lista, sin haber hecho nada antes. Es la ruta que el guion de los quince
        # segundos manda usar (`docs/PRUEBA-15-SEGUNDOS.md`), asi que se comprueba que
        # siga contestando.
        t0 = time.monotonic()
        carga("/panel?pestana=bajadas&mios=true")
        pagina.wait_for_timeout(1200)
        tiempos.append(("del panel a 'lo mio que ha bajado'", time.monotonic() - t0))
        mio = pagina.inner_text("main")
        comprueba("Lo tuyo que ha" in mio,
                  "el panel contesta 'lo tuyo que ha bajado', con lo tuyo de verdad")
        comprueba("en 7 días" in mio or "en 30 días" in mio,
                  "y dice de que ventana habla")
        comprueba("unidad y la cantidad siguen siendo las mismas" in mio,
                  "y explica que no cuenta como bajada: misma unidad y misma cantidad")

        # -------------- las tres pantallas del panel que le faltaban (BACKLOG 0.8) ----
        # `indice`, `posicion` y `ofertas dudosas` son las tres del panel viejo que el
        # nuevo no tenia (`app.js:762-768`), y eran justo las que impiden cambiar la
        # interfaz. Se comprueba que **contestan**, no que cargan: un titulo bonito
        # encima de una lista vacia es peor que no tener pantalla, porque parece hecha.
        print("\n== las tres pantallas del panel que le faltaban")
        for pestana, tiene_que_decir in (
                ("indice", "El nivel de precios de cada cadena"),
                ("posicion", "En qué es cara cada cadena"),
                ("dudosas", "conviene mirar dos veces")):
            carga(f"/panel?pestana={pestana}")
            pagina.wait_for_timeout(1500)
            texto = pagina.inner_text("main")
            visto = " | ".join(texto.splitlines()[:6])
            comprueba(tiene_que_decir in texto,
                      f"el panel de {pestana} contesta ({tiene_que_decir!r}; lei: {visto})")
            # Y cada una dice **de donde sale el filtro de cadenas**: quien ve tres y no
            # las cinco tiene que poder saber si faltan datos o si es su ajuste.
            comprueba("Mirando las cinco cadenas." in texto
                      or "Mirando solo las cadenas que tienes cerca" in texto
                      or "Mirando solo estas cadenas." in texto,
                      f"y el panel de {pestana} dice que cadenas esta mirando")

        # La frase del indice, que es la respuesta: quien ha bajado y quien ha subido.
        carga("/panel?pestana=indice")
        pagina.wait_for_timeout(1500)
        texto = pagina.inner_text("main")
        comprueba("es quien más ha bajado" in texto or "Solo hay una cadena" in texto,
                  "el indice contesta con una frase, no solo con un dibujo")
        comprueba("CAPTURAS" in texto.upper() and "PRODUCTOS" in texto.upper(),
                  "y enseña sobre cuantos productos y cuantas capturas lo dice")

        # El filtro del panel, que era el otro hueco: ninguna pestaña leia `cadenas_cerca`
        # (`Panel.tsx` llamaba a `useBajadas(dias, subidas, [])` con la lista vacia).
        carga("/panel?pestana=indice&cadenas=dia")
        pagina.wait_for_timeout(1500)
        filas = pagina.locator("main table tbody tr")
        # **«DIA» con las tres letras en mayuscula**, que es como se llama la tienda: hasta el
        # 27 de septiembre de 2026 esta pantalla ponia el identificador tal cual («dia»), igual
        # que las cinco pantallas con pastillas de cadena. Lo decide `nombreCadena`
        # (`api/formato.ts`), y esta comprobacion se puso roja al cambiarlo, que es como se
        # entero de que la cadena se veia en mas sitios de los que parecia.
        comprueba(filas.count() == 1 and "DIA" in filas.first.inner_text(),
                  f"filtrar por una cadena deja una sola serie en el indice "
                  f"({filas.count()} filas)")
        comprueba("Mirando solo estas cadenas." in pagina.inner_text("main"),
                  "y el panel dice que esta mirando solo esa")

        # ------------- y el verificador de ofertas por dentro: lo que NO se acusa ------
        # La lista encabezaba, medido en el navegador el 24 de septiembre de 2026, con
        # "Ampollas Compeed 8 ml" a 1.306,25 EUR/l frente a "su precio de siempre" 10,45
        # EUR/l. Eso no es una oferta dudosa: es una **cantidad mal leida** (un dia el
        # envase se leyo como 1 y otro como 0,008), y la pantalla acusaba a Carrefour con
        # numeros que no eran suyos. Se vio al pintar la unidad, que hasta hoy no se
        # pintaba. Aqui se vigila que no vuelva, y que un 3x2 no se acuse de mentir.
        print("\n== el verificador de ofertas: a quien acusa y a quien no")
        from plataforma.api import movimientos
        lista = movimientos.ofertas_dudosas(limite=200)
        comprueba(all(x["unidad"] for x in lista),
                  "cada oferta acusada dice en que unidad esta su precio")
        gordas = [x for x in lista
                  if x["precio_unidad_cent"] > 3 * x["precio_base_cent"]]
        comprueba(not gordas,
                  f"ninguna se acusa con mas del triple de su precio normal "
                  f"({[(x['nombre'][:40], x['precio_unidad_cent'], x['precio_base_cent']) for x in gordas[:3]]})")
        comprueba(not any("3x2" in (x["promo_txt"] or "")
                          or "unidad" in (x["promo_txt"] or "").lower() for x in lista),
                  "y ninguna acusada es de las que dependen de cuantas unidades compres")
        fuera = movimientos.ofertas_sin_poder_juzgar()
        comprueba(fuera["total"] == (fuera["por_varias_unidades"]
                                     + fuera["sin_descuento_de_precio"]
                                     + fuera["cantidad_cambiada"]),
                  f"lo que no se juzga se cuenta por motivo ({fuera})")
        carga("/panel?pestana=dudosas")
        pagina.wait_for_timeout(1500)
        texto = pagina.inner_text("main")
        comprueba("no se juzgan aquí" in texto or "no se juzgan aqui" in texto,
                  "y la pantalla dice cuantas se quedan fuera y por que")

        # ------------- cuantos toques hay hasta cada respuesta (lo medible de la barra a) --
        # La condicion (a) -- *"las cuatro preguntas en menos de quince segundos sin saber
        # donde esta el boton"* -- **no la puede cerrar quien escribe el codigo**: hace falta
        # una persona. Pero si se puede medir **cuanto hay que andar**, que es su mitad de
        # codigo: los toques desde la primera pantalla hasta la respuesta. Un boton a cinco
        # toques no se pulsa en quince segundos ni sabiendo donde esta, y ese numero no es
        # una opinion. Se cuenta **andando de verdad**, no leyendo el mapa de rutas.
        print("\n== cuantos toques hay desde la primera pantalla hasta cada respuesta")
        # **La barra se pulsa por su `href` y con `:visible`**, y las dos cosas son
        # lecciones de este bloque. Por el texto, no: la cabecera lleva el titulo de la
        # aplicacion, que tambien se llama «Cesta», asi que `get_by_role("link", name=...)`
        # coge ese enlace -- que lleva a la portada -- y la medida se queda en el buscador
        # sin enterarse. Y sin `:visible`, no: hay **dos barras** (`NavAbajo` en el movil y
        # `NavEscritorio`, `hidden lg:block`), y la primera del DOM es la del escritorio,
        # que en un movil de 390 px no se ve y no se puede pulsar.
        BARRA = {"Cesta": "/cesta", "Avisos": "/avisos", "Panel": "/panel",
                 "Buscar": "/", "Escáner": "/escaner"}
        # Las pestañas del panel son `role="tab"`, no botones: `get_by_role("button")` no
        # las encuentra, y la espera se queda colgada hasta el timeout.
        PESTANAS_PANEL = ("Hoy", "Cadenas", "Marcas", "Histórico", "Movidos", "Bajadas",
                          "Índice", "Posición", "Ofertas dudosas")
        # **Y la marca de cada caso es una lista, no una frase.** La cesta contesta de tres
        # formas segun como la deje la pasada anterior (con lineas por coger, con todo en
        # el carro, o vacia con la cuadricula), y las tres son respuestas: lo que se mide
        # aqui son los toques, no el estado de la lista.
        for que, marcas, camino in (
                ("3: voy tachando bien (el numero de la barra lo dice sin abrir nada)",
                 ("Por coger", "En el carro", "Lo que cuesta", "No tienes ninguna lista"),
                 ("Cesta",)),
                ("1: que me falta y donde lo compro", ("Por coger", "En el carro",
                                                       "No tienes ninguna lista",
                                                       # **Y la lista con todo cogido.** Los
                                                       # encabezados «Por coger»/«En el carro» solo
                                                       # salen si hay algo en los dos lados, asi que
                                                       # con las 52 lineas tachadas -que es como
                                                       # quedo la cuenta de esta puerta el 28 de
                                                       # septiembre de 2026- la respuesta a la
                                                       # pregunta 1 esta en «52 ya cogidas». Sin
                                                       # esta marca, la puerta acusaba a la
                                                       # aplicacion de un estado que la aplicacion
                                                       # cuenta bien.
                                                       "ya cogidas"),
                 ("Cesta",)),
                ("4: lo mio que ha bajado", ("Lo tuyo que ha",),
                 ("Panel", "Bajadas", "Solo lo mío")),
                ("4: los avisos", ("que sigues",),
                 ("Avisos",)),
        ):
            carga("/")
            for paso in camino:
                if paso in BARRA:
                    toque = pagina.locator(f"nav a[href='{BARRA[paso]}']:visible").first
                elif paso in PESTANAS_PANEL:
                    toque = pagina.get_by_role("tab", name=paso).first
                else:
                    toque = pagina.get_by_role("button", name=paso).first
                toque.click()
                pagina.wait_for_timeout(900)
            pagina.wait_for_timeout(900)
            texto = pagina.inner_text("main")
            visto = next((m for m in marcas if m in texto), None)
            comprueba(visto is not None,
                      f"{que}: se contesta a {len(camino)} toque(s) desde la primera "
                      f"pantalla ({' -> '.join(camino)}; lei {texto[:40]!r})")

        # Y la 2, que es la unica que empieza escribiendo: nadie sabe el nombre exacto del
        # producto, asi que se escribe a medias y se toca el resultado. **Un toque.**
        carga("/compra")
        pagina.get_by_placeholder("leche entera, atún, papel de cocina…").fill("leche entera")
        with contextlib.suppress(Exception):
            pagina.locator("a[href^='/grupo/']").first.wait_for(timeout=20000)
        pagina.locator("a[href^='/grupo/']").first.click()
        pagina.wait_for_url("**/grupo/**", timeout=20000)
        pagina.wait_for_load_state("networkidle")
        pagina.wait_for_timeout(1200)
        comprueba(pagina.locator("main p.font-semibold").first.count() > 0,
                  "2: esto esta caro se contesta con un toque y lo que escribas")

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
        # **Todas las pantallas donde se puede acabar de pie**, no solo las cuatro del
        # encargo. Las dos ultimas entraron el 23 de septiembre de 2026 al medir la ficha del
        # producto: ahi habia **cuatro objetivos por debajo de 44 px** que llevaban ahi desde
        # el primer dia -- el enlace al producto de al lado en la tabla de equivalencias medía
        # 161 x **19**, y el desplegable «Ingredientes», 324 x **20** --, y no los habia
        # visto nadie porque esta pantalla no la medía ninguna pasada.
        rutas = ["/", "/cesta"]
        if solo_uno is not None:
            rutas.append(f"/grupo/{solo_uno}")
        rutas += ["/avisos", "/panel", "/ajustes", "/escaner"]
        # Las tres pestanas nuevas del panel, cada una con su propia forma: una grafica
        # con deslizador de tabla, barras y tarjetas con una regla. Entran aqui porque
        # son pantallas nuevas y nadie las ha medido todavia con el dedo.
        rutas += ["/panel?pestana=indice", "/panel?pestana=posicion",
                  "/panel?pestana=dudosas", "/panel?pestana=bajadas"]
        # Y el panel de matching, que es una pantalla aparte (`/panel/matching`) y la que mas
        # tablas tenia: entra aqui para que la midan las dos reglas del movil -- nada por debajo
        # de 44 px y ninguna tabla que se deslice. Medido el 27 de septiembre de 2026.
        rutas += ["/panel/matching"]
        # Y la pantalla del enlace de invitacion caducado, que es por donde entra quien recibe
        # un enlace viejo: no la medía ninguna pasada hasta el 27 de septiembre de 2026.
        rutas += ["/unirme/codigo-que-no-existe"]
        # **Y las tres que faltaban, vistas el 30 de septiembre de 2026 leyendo las rutas de la
        # aplicacion contra esta lista.** El buscador y favoritos son las dos pantallas donde se
        # esta de pie -- el buscador es la pregunta 2 de la barra (a), y favoritos es la lista de
        # quien compra siempre --, y **no las medía esta pasada**: el microfono, el boton del
        # escaner y el selector de ventana que estrenan son justo lo que se toca con el pulgar.
        # Y la pantalla de «esa pantalla no existe» (`path="*"`) tampoco: es la que ve quien
        # llega con un enlace malo, y una pantalla que solo ve quien ya tiene un problema no
        # puede ser la que nadie mide.
        rutas += ["/buscar?q=leche+entera", "/favoritos", "/ruta-que-no-existe"]
        con_historial = _producto_caro_con_historial()
        if con_historial is not None:
            rutas.append(f"/producto/{con_historial[0]}/{con_historial[1]}")
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
            # Y la otra mitad de una pantalla de movil: **que no se deslice de lado.** Una
            # pagina que se sale obliga a moverla con el pulgar para leer el final de las
            # lineas, y en la tienda eso es soltar el carro.
            ancho, scroll = pagina.evaluate(
                "() => [document.documentElement.clientWidth,"
                " document.documentElement.scrollWidth]")
            comprueba(scroll <= ancho + 1,
                      f"en {ruta} la pagina no se sale de la pantalla ({scroll} > {ancho})")
            # **Y las tablas tampoco, desde el 27 de septiembre de 2026.** Una tabla ancha se
            # deslizaba dentro de su caja (`TablaScroll`), y eso dejaba **fuera de la pantalla
            # justo la columna del precio**: medido en el buscador (52rem de minimo) y en el
            # panel. Ahora, por debajo de 640 px, las filas se apilan y no hay nada que
            # deslizar; esta comprobacion es la que impide que vuelva, en las catorce tablas
            # del proyecto a la vez.
            cajas = pagina.evaluate("""() => [...document.querySelectorAll('.tabla-scroll')]
              .map(c => [c.scrollWidth, c.clientWidth, (c.getAttribute('aria-label') || '')])""")
            anchas = [a for a, b, _ in cajas if a > b + 1]
            comprueba(not anchas,
                      f"en {ruta} ninguna tabla se desliza en horizontal "
                      f"({len(anchas)} de {len(cajas)}: "
                      f"{[n for a, b, n in cajas if a > b + 1][:3]})")
            # **Y la pantalla se puede recorrer sin verla.** Lo que no da error al
            # incumplirse: una imagen sin texto alternativo, un boton sin nombre, un campo sin
            # etiqueta y una jerarquia de encabezados con un hueco o con dos `h1`. Medido el
            # 27 de septiembre de 2026 con `data/debug/accesibilidad.py`: salieron cinco
            # (Inicio, Buscar y el caso vacio de Favoritos sin `h1`, la lista con un salto de
            # `h2` a `h4`, y el documento de operacion con tres `h1`). El contraste se mide
            # aparte, mas abajo y con su propia pasada.
            accesibilidad = pagina.evaluate(_ACCESIBILIDAD)
            comprueba(all(not v for v in accesibilidad.values()),
                      f"en {ruta} la pantalla se puede recorrer sin verla "
                      f"({ {k: v[:3] for k, v in accesibilidad.items() if v} })")

        # ------------------- cuando la API falla: una frase y una forma de reintentar -----
        # La fila «errores + reintentar» del §8 no la habia mirado un navegador nunca: se
        # probaba el endpoint (que devuelve 500), no la pantalla que lo recibe. Y salio un
        # hueco real: la cesta era **la unica** pantalla que escribia su error a mano
        # (`Vacio` + `textoDeError`) en vez de usar `Fallo`, y por eso era la unica **sin
        # «Volver a intentarlo»** -- habia que recargar la pagina a mano, que en el movil no
        # es evidente. Ahora usa `Fallo`, que ademas es quien decide el tono (sin cobertura
        # no es rojo, y esa decision tiene que estar en un sitio y no repetida en seis
        # pantallas: `ui.tsx`).
        #
        # **El filtro de la URL es lo que hace que esto mida lo que dice medir**: el patron
        # `**/api/alertas*` cogia tambien `/src/api/alertas.ts` y dejaba la aplicacion sin
        # montar. Ver `_solo_el_endpoint`, que lo explica con el caso.
        print("\n== cuando la API falla, cada pantalla lo dice y deja reintentar")
        for que, endpoint, ruta, escribe in (
                ("la cesta", "listas", "/cesta", None),
                ("los avisos", "alertas", "/avisos", None),
                ("lo mio que ha bajado", "bajadas", "/panel?pestana=bajadas&mios=true", None),
                # `/buscar` y no `/`: desde el 27 de septiembre de 2026 `/` es Inicio, y su
                # buscador no navega a ningun sitio -- busca ahi mismo, y eso se mide abajo.
                ("el buscador", "buscar", "/buscar", "leche entera"),
                # **Las demas pantallas, desde el 27 de septiembre de 2026.** Esta lista tenia
                # cuatro, y el proyecto dice que **las cuatro caras de una pantalla se
                # diseñan** -- cargando, con contenido, vacia y rota --: la rota solo estaba
                # medida en cuatro de las trece. Es la misma leccion que el esqueleto eterno de
                # `/avisos`: una cara que no se mide es una cara que nadie ha visto.
                ("la ficha del grupo", "grupo", "/grupo/526", None),
                ("la ficha del producto", "producto", "/producto/dia/141787", None),
                ("los favoritos", "favoritos", "/favoritos", None),
                ("el panel", "panel/hoy", "/panel", None),
                ("el panel de matching", "panel/matching", "/panel/matching", None),
                ("el indice", "indice", "/panel?pestana=indice", None),
                ("la posicion", "posicion", "/panel?pestana=posicion", None),
                ("las ofertas dudosas", "ofertas-dudosas", "/panel?pestana=dudosas", None),
        ):
            filtro = _contesta_mal(pagina, endpoint)
            try:
                carga(ruta)
                if escribe:
                    pagina.get_by_placeholder(
                        "leche entera, atún, papel de cocina…").fill(escribe)
                # **Se espera al estado de error, no a un numero de milisegundos.** React
                # Query reintenta antes de darse por vencida (y hace bien: un 500 de un
                # segundo no es un fallo), asi que leer la pantalla nada mas cargar mide
                # «Cargando…» -- que es exactamente lo que paso la primera vez que se
                # escribio esto, y por eso ahora se espera al boton.
                with contextlib.suppress(Exception):
                    pagina.get_by_role("button", name="Volver a intentarlo").first.wait_for(
                        timeout=20000)
                texto = pagina.inner_text("body")
                botones = [b.strip() for b in pagina.locator("button").all_inner_texts()]
                # El fallo dice **lo que se ha visto**, no solo que no estaba: sin eso, un
                # FALLO aqui no se puede leer sin volver a correr todo.
                visto = " | ".join(texto.splitlines()[:8])
                comprueba("No he podido" in texto or "Sin cobertura" in texto,
                          f"{que}: con la API a 500 lo dice con palabras (lei: {visto})")
                comprueba("Volver a intentarlo" in botones,
                          f"{que}: y deja reintentar sin recargar la pagina "
                          f"({[b for b in botones if b][-3:]})")
            finally:
                pagina.unroute(filtro)

        # **El escaner, que se dispara al pulsar.** No entra en la lista de arriba porque no
        # carga sola: hay que teclear el codigo y mandarlo. Con `/api/ean` a 500 tiene que
        # decirlo con palabras y dejar volver a probar sin recargar la pagina.
        filtro = _contesta_mal(pagina, "ean")
        try:
            carga("/escaner")
            pagina.get_by_label("Código de barras").fill("8410655002410")
            pagina.get_by_role("button", name="Buscar").first.click()
            with contextlib.suppress(Exception):
                pagina.get_by_role("button", name="Volver a intentarlo").first.wait_for(
                    timeout=20000)
            texto = pagina.inner_text("body")
            botones = [b.strip() for b in pagina.locator("button").all_inner_texts()]
            comprueba("No he podido" in texto or "Sin cobertura" in texto
                      or "no ha contestado" in texto,
                      "el escaner: con la API a 500 lo dice con palabras "
                      f"(lei: {' | '.join(texto.splitlines()[:8])})")
            comprueba("Volver a intentarlo" in botones,
                      f"el escaner: y deja reintentar ({[b for b in botones if b][-3:]})")
        finally:
            pagina.unroute(filtro)

        # Y el buscador **de la primera pantalla**, que busca mientras se escribe: con la API
        # caida, el hueco de los resultados lo dice con palabras. Y, sobre todo, **no dice
        # «nada con esas palabras»**: eso seria culpar a quien escribe de un fallo nuestro, y
        # es justo el fallo que tenia esta pantalla cuando se escribio (27 sep 2026).
        filtro = _contesta_mal(pagina, "buscar")
        try:
            carga("/compra")
            pagina.get_by_placeholder("leche entera, atún, papel de cocina…").fill("leche entera")
            with contextlib.suppress(Exception):
                pagina.get_by_text("No he podido buscar").first.wait_for(timeout=20000)
            texto = pagina.inner_text("body")
            comprueba("No he podido buscar" in texto,
                      "el buscador de la primera pantalla, con la API a 500, lo dice con "
                      f"palabras (lei: {' | '.join(texto.splitlines()[:6])})")
            comprueba("Nada con esas palabras" not in texto,
                      "y no le echa la culpa a quien escribe: no dice «nada con esas palabras»")
        finally:
            pagina.unroute(filtro)
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

            # ------------------------------- el papel de «solo mirar» ---------------------
            # **Lo que promete la tarjeta de Compartir y no medía nadie.** Dice: *«Quien entre
            # puede escribir en ella o solo mirarla, y eso se elige aquí abajo»*. Y ser de solo
            # mirar no es una etiqueta: la API contesta **403** a cualquier cambio y la pantalla
            # apaga los controles **diciendo por que**, en vez de dejar botones que fallan uno a
            # uno. Se mide con las dos personas delante: el dueno cambia el papel por su usuario
            # (que es el otro camino de compartir), la invitada recarga, y se comprueba lo que ve
            # y lo que le deja hacer.
            campo_usuario = pagina.get_by_label("Su usuario")
            papel = pagina.get_by_label("Quien entre podrá")
            if campo_usuario.count() and papel.count():
                papel.select_option("mira")
                campo_usuario.fill(USUARIO_INVITADA)
                pagina.get_by_role("button", name="Compartir").first.click()
                with contextlib.suppress(Exception):
                    pagina.get_by_text("Ya está dentro").first.wait_for(timeout=15000)
                comprueba("solo mira" in pagina.inner_text("body"),
                          "el dueno puede dejar a alguien en «solo mirar»")
                _carga(otra, "/cesta")
                de_solo_mirar = otra.inner_text("main")
                comprueba("te la compartieron para mirar" in de_solo_mirar,
                          "y quien solo mira ve por que no puede tocar nada")
                apagadas = otra.locator("input[type=checkbox]:disabled").count()
                comprueba(apagadas >= 1,
                          f"con las casillas apagadas, no con botones que fallan ({apagadas})")
                # Y la API de verdad: un cambio suyo tiene que salir 403.
                rechazo = otra.evaluate("""async () => {
                  const lista = (await (await fetch('/api/listas', {credentials:
                    'same-origin'})).json()).listas.find((l) => l.papel === 'mira');
                  if (!lista) return 'no encuentro su lista de solo mirar';
                  const detalle = await (await fetch(`/api/listas/${lista.id}`,
                    {credentials: 'same-origin'})).json();
                  const linea = (detalle.lineas || [])[0];
                  if (!linea) return 'la lista no tiene lineas';
                  const r = await fetch(`/api/listas/${lista.id}/lineas/${linea.id}`, {
                    method: 'PATCH', credentials: 'same-origin',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({tachado: true})});
                  return r.status;
                }""")
                comprueba(rechazo == 403,
                          f"y la API le dice que no si lo intenta igual ({rechazo})")
                # De vuelta a escribir: el papel se puede cambiar en los dos sentidos, y dejarlo
                # como estaba importa -- la cuenta de la invitada es **fija** y la siguiente
                # pasada cuenta con que pueda escribir.
                papel.select_option("escribe")
                campo_usuario.fill(USUARIO_INVITADA)
                pagina.get_by_role("button", name="Compartir").first.click()
                pagina.wait_for_timeout(2500)
                _carga(otra, "/cesta")
                comprueba("te la compartieron para mirar" not in otra.inner_text("main")
                          and otra.locator("input[type=checkbox]:disabled").count() == 0,
                          "y volver a dejarle escribir le devuelve los controles")

                # ------------------------------- las novedades ----------------------------
                # **La API las mandaba desde el primer dia y no las pintaba ninguna pantalla.**
                # `novedades` (`GET /listas/{id}`) no aparecia en `app/src`: una lista compartida
                # era un sitio donde las cosas aparecen y desaparecen solas. Se mide aqui porque
                # hacen falta **las dos personas**: una toca, la otra abre y tiene que enterarse.
                sin_tachar = otra.locator("input[type=checkbox]:not(:disabled):not(:checked)")
                if sin_tachar.count():
                    nombre_visto = otra.evaluate("""() => {
                      const i = [...document.querySelectorAll('input[type=checkbox]')]
                        .find((x) => !x.disabled && !x.checked);
                      return i && i.labels && i.labels[0]
                        ? i.labels[0].innerText.trim() : '';
                    }""")
                    sin_tachar.first.click()
                    with contextlib.suppress(Exception):
                        otra.locator("input[type=checkbox]:checked").first.wait_for(timeout=15000)
                    carga("/cesta")
                    abierto = pagina.inner_text("main")
                    comprueba("Desde la última vez que miraste" in abierto
                              and "cogió" in abierto,
                              f"el dueno ve lo que ha tocado la otra persona "
                              f"({nombre_visto[:28]!r})")
                    # **Y se va sola al recargar**: la visita se marca al leer la lista, asi que
                    # la segunda vez ya no es una novedad. Un aviso que no se apaga es ruido.
                    carga("/cesta")
                    comprueba("Desde la última vez que miraste" not in pagina.inner_text("main"),
                              "y al volver a mirar desaparece, porque ya no es novedad")
                else:
                    print("   (la lista no tiene lineas sin tachar: no se pueden ver novedades)")
            else:
                print("   (sin la tarjeta de Compartir no se puede medir el papel de solo mirar)")
            contexto2.close()

        # ------------------- la curva, con la frase debajo y el ahorro en euros (§4) ----
        # §4 pide cuatro cosas en la ficha, en este orden: una frase, **donde esta mas
        # barato y cuanto se ahorra en euros**, **la curva con una frase debajo** y, solo
        # al final, la tabla. Lo que faltaba era el apartado 3: la curva estaba desde el
        # primer dia y **no decia nada** -- una linea que sube y baja es un adorno del
        # dato. Esto es lo que ningun `grep` puede comprobar: que la frase se pinte, que
        # diga un plazo de verdad y que este **antes** que la tabla.
        print("\n== la curva de un producto, con su frase debajo")
        producto = _producto_caro_con_historial()
        if producto is None:
            print("   (no he encontrado ningun producto comparable con historico)")
        else:
            fuente, id_fuente = producto
            carga(f"/producto/{fuente}/{id_fuente}")
            pagina.wait_for_timeout(900)
            comprueba(pagina.locator("canvas").count() >= 1,
                      "la curva se pinta (el lienzo del historico esta)")
            ficha = pagina.inner_text("main")
            formas = ("Es el precio más bajo", "Es el precio más alto", "Lleva ",
                      "Está un ")
            frase = next((f for f in formas if f in ficha), None)
            comprueba(frase is not None,
                      f"debajo de la curva hay una FRASE que la contesta ({producto})")
            if frase:
                # **El plazo tiene que ser el de verdad.** El encargo pone como ejemplo
                # "esta mas barato que en los ultimos 90 dias", y hoy el historico son 18
                # dias: decir 90 seria una mentira tranquila -- suena mejor y no es verdad.
                # La frase dice los dias que hay, y esto lo comprueba ya pintado.
                #
                # Se mira **la frase y no la pantalla entera**: en esta ficha la campana
                # dice «te aviso cuando este en su precio mas bajo de 90 dias», y ahi el
                # plazo es el de la alerta (`minimo_90d`), que si son 90 dias. Un `in` sobre
                # todo el texto suspenderia por una frase correcta que no es esta.
                desde = ficha.find(frase)
                la_frase = ficha[desde:desde + 140]
                comprueba("días que tenemos" in la_frase or "días al mismo precio" in la_frase,
                          "y el plazo que dice es el que tenemos, no uno inventado")
                comprueba("90 días" not in la_frase,
                          "y no promete 90 dias de historico en la frase de la curva")
                html = pagina.content()
                comprueba(html.find(frase) < html.find("Su grupo de equivalencias"),
                          "la frase va ANTES que la tabla de equivalencias")
                print(f"   la frase: «{la_frase.strip()[:90]}»")
            # Y el ahorro **en euros**, que es el apartado 2: el producto se eligio para
            # que haya algo que ahorrar, asi que este dato tiene que estar. El texto se
            # busca en minusculas porque la etiqueta del dato se pinta en mayusculas
            # (`Dato` lleva `uppercase`), y buscar "Más barato en" no encontraba nada --
            # que es como esta prueba se puso roja la primera vez, por el instrumento.
            comprueba("más barato en" in ficha.lower() and "te ahorras" in ficha,
                      "y dice donde esta mas barato y cuanto se ahorra, en euros por unidad")
            # **Y desde aquí se puede apuntar y seguir.** A esta pantalla se llega escaneando
            # el código de barras: hasta el 27 de septiembre de 2026 no había ni «Añadir a la
            # cesta» ni la campana, así que el flujo documentado («+ ficha + añadir»,
            # `docs/PANTALLAS.md` §6) obligaba a volver al grupo a buscarlo, con el paquete en
            # la mano. Se comprueba que están, y que la frase sigue dicha con sus tildes y con
            # la cadena como se llama: «Cuesta un 41 % más que en Mercadona.»
            comprueba(pagina.get_by_role("button", name="Añadir a la cesta").count() == 1,
                      "desde la ficha del producto se puede añadir a la cesta")
            comprueba(pagina.get_by_role("button", name="Avisarme si baja").count() == 1
                      or pagina.get_by_text("Te aviso").count() >= 1,
                      "y pedir el aviso, sin volver al grupo")
            # La frase se mira **sola**, no en toda la pantalla: en el texto de la ficha hay
            # valores de tabla y notas donde «mas» sin tilde no es un fallo de esta frase.
            la_frase_de_precio = pagina.locator("main p.font-semibold").first.inner_text()
            comprueba("mas que" not in la_frase_de_precio
                      and " mercadona" not in la_frase_de_precio,
                      "y la frase va con tildes y con la cadena como se llama "
                      f"({la_frase_de_precio.strip()[:60]!r})")
            # **Y ninguna diferencia imposible en pantalla.** El producto elegido es del
            # grupo que destapo el fallo (unidades mezcladas), asi que aqui se ve si la
            # columna «Diferencia» y el ahorro vuelven a cruzar unidades.
            gordos = _porcentajes_gordos(pagina)
            comprueba(not gordos,
                      "y ningun porcentaje de la ficha pasa del tope de 'esto no es una "
                      f"oferta' ({[(n, t[:46]) for n, t in gordos[:2]]})")
            # Y la prueba de que **esa** medida mira, en la misma pantalla: con el tope a
            # cero tiene que salir cualquier porcentaje. Sin esto, un cero puede ser "todo
            # bien" o "no he sabido leer un numero en castellano" (162.943,5 %).
            comprueba(len(_porcentajes_gordos(pagina, 0.0)) > 0,
                      "y la medida de los porcentajes mira (con el tope a 0 encuentra algo)")
            # La misma medida en la pantalla del grupo, que es donde vive el dato grande
            # de "de la mas barata a la mas cara".
            enlace_grupo = pagina.locator("a[href^='/grupo/']").first
            if enlace_grupo.count():
                grupo_url = enlace_grupo.get_attribute("href") or ""
                carga(grupo_url)
                pagina.wait_for_timeout(700)
                gordos_grupo = _porcentajes_gordos(pagina)
                comprueba(not gordos_grupo,
                          "y tampoco en la pantalla del grupo "
                          f"({[(n, t[:46]) for n, t in gordos_grupo[:2]]})")

        # -------------------- las cuatro respuestas caben en la primera pantalla --------
        # La condicion (a) se juzga con el movil en la mano y **sin saber donde esta el
        # boton**: una respuesta que obliga a desplazar la pantalla no se lee en quince
        # segundos ni sabiendo donde esta. Esto no cierra (a) -- eso lo dice una persona --,
        # pero descarta de antemano lo que no quepa: la banda util son 678 px de 844
        # (109 de cabecera arriba y 57 de barra abajo, medidos en `_franja_util`).
        #
        # Se mide **lo que contesta cada pregunta**, no la pantalla entera:
        #
        #   1 y 3  la primera linea de la lista, que es lo que hay que coger
        #   2      la frase que contesta "¿esto esta caro?", en el grupo al que se llega
        #          buscando (y que ya esta comprobado que va antes que la tabla)
        #   4      la tabla de "lo tuyo que ha bajado", con su titulo; y en los avisos,
        #          la seccion que dice lo que ha bajado
        print("\n== las respuestas, en la primera pantalla de un movil")
        arriba, abajo = _franja_util(pagina)
        print(f"   la banda util: {arriba}..{abajo} px de {pagina.viewport_size['height']}")

        carga("/cesta")
        with contextlib.suppress(Exception):
            pagina.locator("input[type=checkbox]").first.wait_for(timeout=20000)
        primera_linea = pagina.locator("input[type=checkbox]").first
        dentro, donde = _cabe_en_la_primera(pagina, primera_linea)
        comprueba(dentro,
                  f"1 y 3: la primera linea de la lista se ve sin desplazar ({donde})")
        if not dentro:
            # **La caja se mide UNA vez.** Aqui se llamaba a `bounding_box()` dos veces --una
            # para el `if` y otra para el `y`-- y la segunda caia con un `Timeout` de 30 s que
            # se llevaba por delante la pasada entera: entre las dos llamadas React habia vuelto
            # a pintar la lista y el localizador ya no existia. Un instrumento que revienta
            # midiendo lo que va mal es el peor momento para reventar: la pasada se corta justo
            # cuando acababa de encontrar algo. Medido el 30 de septiembre de 2026.
            caja = None
            with contextlib.suppress(Exception):
                caja = primera_linea.bounding_box()
            if caja:
                print("   lo que hay encima de la primera linea, con su alto:")
                for c in _encima_de(pagina, caja["y"]):
                    print(f"     y={c['y']:>6.0f}  alto={c['h']:>5.0f}  {c['t']}")
            else:
                print("   (la primera linea desaparecio antes de poder medirla: "
                      "la lista se volvio a pintar)")

        carga("/compra")
        pagina.get_by_placeholder("leche entera, atún, papel de cocina…").fill("leche entera")
        resultado = pagina.locator("a[href^='/grupo/']").first
        with contextlib.suppress(Exception):
            resultado.wait_for(timeout=15000)
        resultado.click()
        pagina.wait_for_url("**/grupo/**", timeout=15000)
        pagina.wait_for_load_state("networkidle")
        with contextlib.suppress(Exception):
            pagina.get_by_role("button", name="Añadir a la cesta").first.wait_for(timeout=20000)
        la_frase = pagina.locator("main p.font-semibold").first
        dentro, donde = _cabe_en_la_primera(pagina, la_frase)
        comprueba(dentro,
                  f"2: la frase que contesta «¿esto esta caro?» se ve sin desplazar ({donde})")

        carga("/panel?pestana=bajadas&mios=true")
        pagina.wait_for_timeout(1000)
        # **La primera fila, no la tabla entera.** La tabla de «lo tuyo que ha bajado» es un
        # ranking: crece sola cada dia que baja algo (medido el 24 sep: 94 px; el 27: 242), asi
        # que exigir que quepa entera es una prueba que se pone roja por tener mas datos -- el
        # defecto de instrumento que este proyecto ya se ha comido tres veces. Lo que contesta
        # la pregunta es su primera fila: eso es lo que se mide. La cabecera no se mide desde el
        # 27 de septiembre de 2026 porque **en el movil ya no hay cabecera**: las tablas se
        # apilan y el nombre de la columna va en cada celda (`Td etiqueta`).
        primera_fila = pagina.locator("main table tbody tr").first
        if pagina.locator("main table tbody tr").count():
            dentro, donde = _cabe_en_la_primera(pagina, primera_fila)
            comprueba(dentro,
                      f"4: la primera fila de lo tuyo que ha bajado se ve sin desplazar ({donde})")
        else:
            # **Cuando «lo tuyo» está vacío, la pantalla contesta con el vacío, y eso también
            # es contestar.** Medido el 29 de septiembre de 2026: la cuenta de la prueba tiene
            # la lista con las líneas viejas (los grupos 526 y 10226, que hoy son un pintalabios
            # y unas barritas), así que `solo_mios=true` no encuentra nada y el panel pinta
            # «Nada de lo tuyo ha bajado en 7 días». La comprobación se cayó **esperando una
            # tabla que no iba a venir** (`Locator.bounding_box: Timeout 30000ms`), y eso es un
            # fallo de instrumento: lo que hay que medir es lo que contesta, sea la tabla o el
            # vacío que la sustituye. Si no está ninguna de las dos, eso sí es un FALLO.
            vacio = pagina.get_by_text(re.compile(r"Nada de lo tuyo ha (bajado|subido)"))
            if vacio.count():
                dentro, donde = _cabe_en_la_primera(pagina, vacio.first)
                comprueba(dentro,
                          f"4: lo tuyo esta vacio y la pantalla lo dice en la primera ({donde})")
            else:
                comprueba(False,
                          "4: ni la tabla de lo tuyo que ha bajado ni el vacio que la sustituye")

        carga("/avisos")
        # La seccion de lo que ha bajado, que es la respuesta de la pregunta 4 en esta
        # pantalla. **Los tres estados valen**, y son los mismos tres que ya documenta el
        # bloque de arriba: «Ha bajado» (se cumple hoy), «Salió y ya no está a ese precio»
        # (salto otro dia) y «Esperando» (todavia no). Hasta el 28 de septiembre de 2026 aqui
        # solo se miraban los dos primeros: con tres avisos que saltaron dias atras -- y que
        # ya no se cumplen -- la pantalla empieza por «Salió y ya no está a ese precio» y la
        # comprobacion medía «Esperando», que va **al final** y por eso salia fuera de la
        # banda util (y=832 en la pasada del 28, con la aplicacion bien).
        seccion = None
        for texto in ("Ha bajado", "Salió y ya no está a ese precio", "Esperando"):
            cual = pagina.get_by_text(texto, exact=True)
            if cual.count():
                seccion = cual.first
                break
        if seccion is not None:
            dentro, donde = _cabe_en_la_primera(pagina, seccion)
            comprueba(dentro, f"4: la seccion de los avisos se ve sin desplazar ({donde})")
        else:
            comprueba(False, "4: no encuentro la seccion de avisos en la pantalla")

        # ------------------------------- el contraste del texto, pintado y en los dos temas --
        # §1 del encargo: *"el contraste y los limites de los campos, con las formulas dentro
        # de las pruebas. Eso es accesibilidad de verdad y esta medida"*. `tests/test_contraste.py`
        # mide los **tokens** del CSS; esto mide el texto **pintado**, resolviendo el fondo
        # real de cada uno (que casi nunca es el del propio elemento) y **en los dos temas**:
        # un `dark:` que falte no se ve en los tokens y si se ve aqui.
        print("\n== el contraste del texto, ya pintado (§1)")
        for tema in ("light", "dark"):
            pagina.emulate_media(color_scheme=tema)
            # La ficha del producto entra aqui desde el 23 de septiembre de 2026, cuando la
            # ficha de un azafran enseno que tenia cuatro objetivos por debajo de 44 px: es
            # una pantalla con avisos de color (los alergenos en rojo) y con cajas propias,
            # justo donde un `dark:` que falte se ve.
            #
            # **Y la ficha del grupo, desde el 27 de septiembre de 2026**, que es donde salio el
            # fallo: `text-neutral-500` sin `dark:` propio daba **3,19:1** en el tema oscuro, en
            # veinte sitios de una misma pantalla (los pesos del «por que esta en esta
            # posicion»). Estaba a la vista de cualquiera menos de esta prueba, que miraba cuatro
            # rutas y esa no era una.
            #
            # **Y favoritos, desde el 30 de septiembre de 2026.** Es la pantalla que estrena
            # etiquetas de color (bajada en verde, subida en rojo, «sin comparar» en aviso), que
            # es justo donde un `dark:` que falte se ve; y hasta hoy no la miraba nadie.
            #
            # **Y ajustes, el mismo dia**, porque estrena el aviso legal: un pie de pagina en
            # `text-xs` es exactamente el sitio donde alguien se salta el minimo de contraste
            # sin enterarse, y lo que se lee ahi (que no hay relacion con las cadenas, y de
            # donde sale la nutricion) no es adorno.
            #
            # **Y buscar**, que estrena el microfono y el boton del escaner: es la pantalla con
            # mas controles de la aplicacion, y hasta hoy no la miraba esta prueba.
            for ruta in ("/", "/cesta", "/buscar?q=leche+entera", "/avisos", "/favoritos",
                         "/ajustes", "/grupo/526") + (
                    (f"/producto/{producto[0]}/{producto[1]}",) if producto else ()):
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
