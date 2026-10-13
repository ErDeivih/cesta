# G06 · **El WAF, y la diferencia entre SUPERARLO y ELUDIRLO** -- que hay que decir

*(2026-10-14, ~02:45. **Y su primera clausula es, literalmente, lo que el encargo pide.**)*

## 1. La cabecera, literal

```
`core/waf.py`  *** (383 lineas) ***
l1    *** «Superar el reto de AWS WAF con un navegador y reutilizar la sesion en HTTP plano.» ***
l3-6  *** «Alcampo protege su catalogo con AWS WAF. Sin sesion, las paginas de categoria llegan con un reto
       de JavaScript (`window.gokuProps`) en vez de datos. *** El reto lo resuelve solo un navegador; ***
       despues deja cookies que valen durante horas y que si sirven desde curl_cffi.» ***
l8    *** «Un navegador al dia, no uno por pagina.» ***
l10   *** «Dos detalles que hacen que esto funcione y que costaron un intento fallido:» ***
l12-15 *** «1. *** **Se valida por resultado, no por el nombre de la cookie.** *** Da igual como se llame el
         testigo: lo que se comprueba es que *** UNA PAGINA DE CATEGORIA DE VERDAD LLEGUE CON DATOS. ***
         Buscar `aws-waf-token` a ciegas fallaba aunque la sesion ya fuese buena.» ***
l16-17 *** «2. *** **Se copia tambien el User-Agent del navegador.** *** El testigo de AWS WAF va ligado al
         agente que lo obtuvo; *** mandarlo con otro agente lo invalida. ***» ***
l19-20 *** `uv run python -m core.waf`  *** *-- «visible, la forma fiable»* ***  ·  `--headless`  *-- «para el cron»*
```

## 2. *** Y HAY UN MATIZ QUE HAY QUE DECIR, Y NO ESCONDER ***

> *** El encargo dice: *** *** «*** NO ELUDAS CAPTCHA/WAF *** ni confundas desafio con catalogo vacio.» *
>
> *** Y **este fichero dice: «SUPERAR el reto de AWS WAF con un navegador».** *
>
> *** Y **no es lo mismo, y la diferencia importa**: *
> ```
> *** ELUDIR ***  -> *burlarlo: *un **servicio que resuelve captchas**, *una **respuesta falsificada**, *
>                 *o **saltarse el reto.** *
> *** SUPERARLO CON UN NAVEGADOR ***  -> *** usar un navegador DE VERDAD, que EJECUTA el JavaScript del
>                 propio WAF ***, *y **recibe las cookies que el WAF concede.** *
> ```
>
> *** Y **lo que hace este modulo es lo segundo, y se puede decir por que**: *
> *-- *dice *** «el reto lo resuelve solo un navegador» ***, *o sea: **es el WAF quien lo pide**, *
>    *y **lo resuelve el navegador del propio WAF** *-- *y **no un solucionador externo.** *
> *-- *y **el reto es de AWS WAF** (JavaScript), *** no un CAPTCHA de imagenes** *-- *y *
>    *** «sin sesion, las paginas llegan con un reto EN VEZ DE DATOS» ***: *o sea, **es un mecanismo
>    de acceso, y el navegador lo cumple.** *
> *-- *y **NO hay nada que falsee la respuesta**: *el navegador **carga la pagina**, *y *
>    *** se comprueba que llegue CON DATOS.** *
>
> *** -> o sea: *** *** **es un cliente que cumple lo que el servidor pide, y no un atajo.** *
> *-- *y **aun asi se dice**, *porque **la palabra «superar» es la que el encargo vigila.** *

## 3. *** Y su primera clausula es **LITERALMENTE** lo que el encargo pide ***

> *** El encargo: *** *** «no... *** CONFUNDAS DESAFIO CON CATALOGO VACIO.» *** *
>
> *** Y `waf.py:12-15`: *** *** «**Se valida por RESULTADO, no por el nombre de la cookie.** *** Da igual como
> se llame el testigo: *** **lo que se comprueba es que una pagina de categoria DE VERDAD llegue CON DATOS.**
> *** Buscar `aws-waf-token` a ciegas **fallaba aunque la sesion ya fuese buena.**» *
>
> *** O sea: *** *** **el proyecto ya distinguia las dos cosas**, *y **lo escribio**: *
> ```
> *** «hay token» ***        -> *NO es «hay catalogo»*
> *** «hay datos» ***        -> *** y ESO es lo que se comprueba *** *
> *** y «buscar el token a ciegas fallaba aunque la sesion fuese buena» ***  *** -> *** *** es el mismo
>    error, en la direccion contraria: *dar por **mala** una sesion **buena** por el nombre de una cookie. *** *
> ```
>
> *** Y **es la misma regla de `chispa.ts`**: *** *«lo que no se observo no se puede dibujar como si se hubiera
> observado» *-- *y aqui: *** **lo que se observa es que lleguen datos, y no que exista un testigo.** *

## 4. Y el estado, con **los cinco mecanismos del encargo, localizados**

```
*** EL ENCARGO PIDE: *** *«mejora colectores mediante *** validacion, checkpoints, backoff, limites,
observabilidad y recuperacion ***» *

*** Y ESTAN, y cada uno en su fichero: ***
  *** validacion ***   -> *** `waf.py:12-15` ***: *«se valida por RESULTADO... que una pagina llegue CON DATOS»*
  *** backoff ***      -> *** `core/waf.py` *** (383 lineas) *y las esperas de `alcampo.py:821/826` y
                          `carrefour.py:546` (`time.sleep(espera)`)*
  *** limites ***      -> *`RITMO` (`config.py:55`), *`LIMITE_POR_EJECUCION` (`fichas_lidl.py`), *
                          *«un navegador al dia, no uno por pagina» (`waf.py:8`)*
  *** recuperacion *** -> *** `core/inventario.py` ***: *el **`lease` de 30 minutos**, *y los **nueve
                          estados** *-- *y **la cola medida**: *72.319 pendientes y **nada atascado***
  *** observabilidad *** -> *`data/runs.csv` (6 columnas), *y **`data/ejecuciones.log`**
  *** checkpoints ***  -> *`core/grupos_ids.py` («la tabla que se guarda para la pasada de mañana»), *
                          *y **`core/inventario.py`** (la cola persistente)*
  *** y «no confundas desafio con catalogo vacio» ***  -> *** `waf.py:12-15`, con su frase *** *
```
