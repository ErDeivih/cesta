# Scrapling: que es, y que haria falta para que nos sirviera

Repositorio: `github.com/D4Vinci/Scrapling`. Mirado y **probado** el 18 de
septiembre de 2026 (v0.4.15, BSD-3, Python >= 3.10).

## Que es

Un marco de trabajo de scraping en Python que junta tres capas que normalmente
se montan por separado:

    Fetcher            peticiones HTTP con huella TLS suplantada
    StealthyFetcher    navegador endurecido, con bypass de Cloudflare Turnstile
    DynamicFetcher     Playwright entero
    FetcherSession     sesiones reutilizables, y sus variantes Async*

y encima un parser con **selectores adaptativos**: guarda como era el elemento y,
si la web se rediseña, lo vuelve a encontrar por parecido.

## El dato que cambia la conversacion

Sus dependencias, leidas de los metadatos del paquete:

    curl_cffi>=0.16.1        ; extra == "fetchers"
    playwright>=1.62.0       ; extra == "fetchers"
    patchright>=1.62.1       ; extra == "fetchers"
    browserforge>=1.2.4      ; extra == "fetchers"
    protego>=0.6.2           ; extra == "fetchers"

**curl_cffi y patchright son exactamente las dos piezas que ya usamos.**
`core/fetch.py` es curl_cffi; la renovacion de la cookie del WAF de Alcampo es
Patchright. Scrapling no trae una tecnologia distinta de la nuestra: trae **la
nuestra envuelta**, mas generacion de huellas (browserforge) y una API comun.

Eso no lo hace malo -- la envoltura tiene valor --, pero cambia la pregunta. No es
"¿esto nos da algo que no tenemos?", es "¿compensa poner nuestra parte mas medida
detras de la API de otro?".

## Lo unico que si es nuevo para nosotros: el selector adaptativo

Probado de verdad, no leido:

```python
viejo = '<article class="card"><h2 class="nombre">Leche entera 1 L</h2></article>'
nuevo = '<section class="producto-item"><h3 class="title-product">Leche entera 1 L</h3></section>'

Selector(viejo, adaptive=True, url=...).css(".nombre", auto_save=True)
Selector(nuevo, adaptive=True, url=...).css(".nombre", adaptive=True)
# -> ['Leche entera 1 L']
```

Cambiada la clase **y** la etiqueta, lo encuentra igual. Funciona.

Ahora, cuanto nos sirve: de nuestras cinco cadenas, **cuatro entregan JSON**
(Alcampo y Mercadona por API, Aldi por API, Carrefour por `__INITIAL_STATE__`
dentro del HTML). Solo DIA se parsea como HTML de verdad. Un selector que se cura
solo arregla un problema que tenemos **en una cadena de cinco**.

Y para ese problema ya tenemos otra respuesta, que ademas cubre las cinco:
`core/cobertura.py` no arregla el selector roto, pero **se entera** de que una
rama entera ha desaparecido y se niega a escribir el bronze. Un parser que se cura
solo y se equivoca en silencio es peor que uno que se rompe y lo dice.

## Lo que NO vamos a usar, y conviene dejarlo escrito

Su titular es **evadir Cloudflare Turnstile**, y para Akamai, DataDome y Kasada
remite a servicios de pago que resuelven el reto.

Las dos cosas quedan fuera:

- Resolver o automatizar una verificacion anti-bot es una linea que este proyecto
  no cruza. Es la misma razon por la que **Eroski queda descartada** (su web
  responde con reCAPTCHA) y por la que el reto del WAF de Alcampo se resuelve
  abriendo un navegador visible y esperando, no simulandolo.
- Servicios de pago: va contra la regla de no meter infraestructura de pago.

Ademas, y esto es lo que mas importa: **nuestro problema con Carrefour no es un
Turnstile**. Son 403 por reputacion y ritmo -- 373 categorias el 18 de septiembre,
levantadas solas a los veinte minutos --, y lo que lo arreglo, medido, fue esperar
**una vez por tanda** en el bucle de rescate en vez de una vez por peticion. La
evasion no habria cambiado nada.

## Lo que si merece una prueba, acotada

**Una sola**: cambiar `StealthyFetcher` por Patchright en la renovacion de la
cookie del WAF de Alcampo. Es un cambio contenido -- una funcion, `_fetcher()`, que
devuelve cookies y User-Agent -- y tiene un numero que lo decide:

    hoy: 8 renovaciones de cookie en una pasada de 3.770 s

Si con `StealthyFetcher` la pasada necesita **menos renovaciones** o tarda menos,
se queda. Si no, se descarta y se apunta el numero. Sin bypass de Turnstile
activado: solo el navegador endurecido.

De su lista de dependencias nos llevamos ademas una idea gratis: **`protego`**, un
analizador de `robots.txt`. Hoy leemos los `robots.txt` a mano y los citamos en los
documentos; que el colector los compruebe solo seria mejor que la buena voluntad.

## Lo que NO se ha podido probar

Nada contra los supermercados de verdad: esta sesion no tiene red hacia esos
dominios. Todo lo de arriba es lectura del paquete instalado y una prueba del
parser en local. **La prueba de la cookie de Alcampo hay que hacerla en el PC.**

## Veredicto

No es un reemplazo de `core/fetch.py`. Ese fichero tiene propiedades medidas esta
semana -- sin reintento del 403, ritmo por dominio, cache del crudo para reanudar
-- que costaria volver a ganar detras de la API de otro, y a cambio de una capa de
red que por dentro es la misma que ya tenemos.

Si es un candidato para **una** pieza concreta, la del WAF de Alcampo, con una
medicion que decide. Y es una buena fuente de ideas: el selector adaptativo y el
`robots.txt` comprobado por codigo son dos cosas que valen aunque no adoptemos la
libreria.
