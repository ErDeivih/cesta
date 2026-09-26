# Patchright — cuando y como

Los dos enlaces que pasaste:

- **Kaliiiiiiiiii-Vinyzu/patchright** — el bueno. 3.600 estrellas, 1.007 commits,
  22 releases, la ultima en junio de 2026, mantenido por Vinyzu. Es el oficial.
- **oyeaono/patchright** — un fork sin actividad: 0 estrellas, 0 forks, 0 watchers.
  No lo uses; es una copia sin mantener del mismo codigo.

## Que es

Playwright parcheado para no ser detectado. Es un reemplazo directo: mismo API, solo
cambia el import.

    pip install patchright
    patchright install chromium

    # antes:  from playwright.sync_api import sync_playwright
    from patchright.sync_api import sync_playwright

## Que parchea exactamente

- **Fuga de `Runtime.enable`**: Playwright usa ese comando CDP y los antibots lo
  detectan. Patchright ejecuta el JS en contextos aislados y no lo usa.
- **Fuga de `Console.enable`**: desactiva la API de consola entera.
- **Flags del navegador**: quita `--enable-automation` y añade
  `--disable-blink-features=AutomationControlled`.
- **Shadow DOM cerrado**: permite interactuar con locators normales.

## Limitaciones

- **Solo Chromium.** Nada de Firefox ni WebKit. Si necesitas Firefox, Camoufox.
- La consola queda desactivada: no puedes depurar con `console.log` desde la pagina.
- Los `init scripts` son detectables por ataques de temporizacion (ningun antibot
  conocido lo comprueba hoy).
- No pasa toda la bateria de tests de Playwright.

## Donde nos hace falta en este proyecto

**En una sola fuente: Lidl.** Su folleto vive en un visor de terceros dentro de un
iframe que no carga hasta aceptar el consentimiento. Es el unico caso donde un
navegador real gana.

Las otras cinco cadenas se resuelven con `curl_cffi`, que cuesta 5 veces menos en
RAM y 10 veces menos en tiempo. **No metas Patchright donde no hace falta**: cada
navegador son ~250 MB y varios segundos por pagina.

Regla: Patchright entra cuando `curl_cffi` devuelve 403 dos dias seguidos, o cuando
el contenido solo existe despues de una interaccion (consentimiento, login, scroll).

## Esqueleto para Lidl

    from patchright.sync_api import sync_playwright

    with sync_playwright() as p:
        b = p.chromium.launch_persistent_context(
            user_data_dir="data/browser/lidl",   # guarda el consentimiento
            channel="chrome", headless=False,    # headless=True es mas detectable
        )
        page = b.new_page()
        capturas = []
        page.on("response", lambda r: capturas.append(r)
                if "leaflets.schwarz" in r.url and "json" in (r.headers.get("content-type") or "")
                else None)
        page.goto(URL_FOLLETO, wait_until="networkidle")
        # el consentimiento se acepta A MANO la primera vez; el perfil persistente
        # lo recuerda y las siguientes ejecuciones ya no lo piden
        for r in capturas:
            guardar(r.json())

El truco importante es `launch_persistent_context`: aceptas la cookie una vez tu, a
mano, y a partir de ahi el scraper semanal corre solo.


## Donde se usa de verdad hoy: Alcampo (no Lidl)

Sorpresa del 6 sep: el primero que ha necesitado navegador no ha sido Lidl, sino
**Alcampo**, que protege su catalogo con AWS WAF.

`core/waf.py` hace el trabajo: abre Patchright con contexto persistente, espera a
que una pagina de categoria llegue CON datos, y guarda cookies + User-Agent en
data/cookies/. A partir de ahi el colector va con curl_cffi como siempre.

Dos cosas que costaron un intento fallido:

1. **Validar por resultado, no por el nombre de la cookie.** El primer intento
   esperaba a que apareciese `aws-waf-token` y se rendia a los 25 s. Lo correcto es
   comprobar que una pagina protegida llega con `__INITIAL_STATE__`: da igual como
   se llame el testigo.
2. **Copiar tambien el User-Agent.** El testigo de AWS WAF va ligado al agente que
   lo obtuvo. Mandarlo desde curl_cffi con otro agente lo invalida.

Y una tercera, aprendida antes: **headless es mas detectable**. El arranque va en
visible por defecto; `--headless` esta disponible para cuando funcione sin ventana.

## La ventana que no se ve: medido, y dos veces

El dueno dijo el 25 de septiembre de 2026: *"a veces salta el navegador"*. Alcampo corta con
el WAF entre 10 y 33 veces al dia y cada corte podia abrir Chrome encima de lo que estuviera
haciendo. Tres cosas, en este orden, y las tres con su numero:

1. **Reintentar con la misma sesion antes de tocar el navegador** (`REINTENTOS_SIN_NAVEGADOR`
   en el colector). Medido el 26 de septiembre, la pasada de Alcampo:

       33 cortes:  22 resueltos reintentando con la misma cookie (0 navegadores)
                   11 necesitaron ventana
        (antes: 13 cortes el dia 24 y 10 el 23, cada uno con su ventana)

2. **Modo oculto primero, ventana solo si el reto no pasa** (`waf.renueva`). El modo oculto
   pasa menos retos, pero cuando pasa no molesta a nadie.
3. **La ventana, fuera de la vista.** Aqui esta lo que costo dos intentos:

   El primer arreglo puso `--window-position=-2400,-2400` a mano. **No estaba fuera de la
   vista**, y se vio midiendo: este ordenador tiene un monitor a la izquierda del principal, o
   sea un escritorio virtual de x=-1.920 a 1.920 (3.840 px). Una ventana de 1.382 px colocada
   en -2.400 ocupa de -2.400 a -1.018, asi que **432 px caian dentro** del monitor de la
   izquierda:

       fuera   x=-2400 y=-2400 1382x1034   Pasteleria - Categorias - Alcampo...
       escritorio virtual: x de -1920 a 1920

   Y ademas Chromium **no hace caso de `--window-size`** cuando el perfil ya tiene el suyo
   (900x700 pedidos, 1.382x1.034 reales), asi que el margen se calcula con el escritorio
   entero y no con lo que pedimos. Ahora la posicion se **calcula** con las metricas del
   sistema (`SM_XVIRTUALSCREEN` y compania) y la ventana queda entera fuera, ni maximizada:

       posicion calculada: ['--window-position=-5860,-1183', '--window-size=900,700']
       FUERA DE LA VISTA x=-5860 y=-1183 1382x1034   Pasteleria - Categorias - Alcampo...

La comprobacion esta en la linea de ordenes, porque hizo falta a mano dos veces y la segunda
fue justamente para descubrir que la primera no bastaba:

    uv run python -m core.waf --comprobar-ventana

Abre el navegador con ventana, enumera las ventanas del escritorio y dice si la suya cae
fuera del area visible. Es de Windows (`user32`), que es donde corre la tarea de las 06:00.
