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
