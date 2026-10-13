# B02 · **Correccion de la ronda 105**: Alcampo SI tiene maquinaria de resistencia, con otras palabras

*(13 de octubre de 2026. **La medida de la ronda 105 era demasiado fuerte, y se corrige antes de sacar consecuencia.**)*

## 1. Lo que se dijo, y por que estaba mal

*En la ronda 105 quedo escrito, y era la conclusion del documento:*

> *«Asi que **B02 no es «mejorar lo que hay»: es construir lo que no hay**.»*

**Y eso se dedujo de un `grep` solo:**

```
$ git grep -rn "desafio|captcha|Retry-After|retry_after|429|503|backoff|requiere_interaccion" \
      -- projects/cesta/collectors/
projects/cesta/collectors/carrefour.py:69:ESTADOS_DE_BLOQUEO = (403, 429)
```

> **Y el error es el de siempre: se busco con LAS PALABRAS QUE YO ESPERABA** -- *`backoff`, `429`, `503`,
> `Retry-After`* -- **en vez de buscar la IDEA.** *Y Alcampo la tiene, **con otros nombres**.*

## 2. Lo que si hay, y estaba a un `grep` de distancia

```
alcampo.py:743:  sin_estado, renovaciones, reintentos, detener = [], 0, 0, False
alcampo.py:792:  if (renovaciones >= CORTES_PARA_RENDIRSE and anterior
alcampo.py:795:  print(f"  {renovaciones} cortes y solo {len(filas)} productos "
```

> **«Cortes», «renovaciones», «reintentos», y una constante con nombre: `CORTES_PARA_RENDIRSE`.** *O sea:*
>
>   - **hay un contador de cortes** *-- lo que el plan llama «corte a mitad»*;
>   - **hay renovaciones y reintentos** *-- la resistencia*;
>   - **y hay un limite con nombre** *-- `CORTES_PARA_RENDIRSE` --, que es **exactamente** el «backoff con
>     limite» que el plan pide, **dicho de otra forma**;
>   - **y hay un `detener`** *-- que es lo que el plan llama **circuit breaker**.*
>
> **Y ademas, `alcampo.py:165` tiene un comentario que dice:** *«fichero vacio, **indistinguible** de un fichero
> que no se pudo escribir.»* **Que es el problema de B02, escrito en el codigo hace quien sabe cuanto.**

## 3. Y entonces la conclusion de B02 cambia, y hay que decirla

**NO es «construir lo que no hay».** *Es:*

  - **lo que hay esta en Alcampo y no en Carrefour** *-- y el plan pide los dos*;
  - **y esta con nombres propios del dominio** *-- cortes, renovaciones, rendirse -- que **no son los del plan**
    *(`Retry-After`, `backoff`, `circuit breaker`)*, **y por eso un `grep` con las palabras del plan no lo ve**;
  - **y lo que falta de verdad es** *la distincion **desafio vs cero valido**, que esa si que no aparece por
    ningun nombre.* *Y **medir**, que es lo que el plan pide cuatro veces.*

> **O sea: B02 es «comparar dos colectores, igualar el que esta peor, y anadir la distincion que falta»** --
> *mucho mas pequeño que «construirlo entero», y **mucho mas facil de hacer bien**.*

## 4. Y el error, dicho para que sirva

**Es el mismo de la ronda 68** -- *cuando se midio `estabiliza` con un caso y se le puso un nombre sin contrastar
-- y **el mismo de la ronda 105**: **una medida con las palabras equivocadas es peor que ninguna**, porque viene
con un `grep` delante y **parece comprobada**.*

> **Lo que lo caza es lo mismo de siempre: no buscar con las palabras propias, sino con las del codigo.** *Y eso
> no se sabe de antemano: **se averigua mirando el fichero entero**, que es lo que la ronda 105 no hizo.*
>
> *Un `grep` responde a la pregunta que le haces. **Y si la pregunta esta mal, la respuesta tambien** -- con el
> agravante de que **parece un dato**.*

## 5. Y el siguiente comando, ahora si el correcto

```
  leer projects/cesta/collectors/alcampo.py alrededor de 740-800
    -> que cuenta como «corte», que es una «renovacion», y cuando se «rinde»
  y leer projects/cesta/collectors/carrefour.py alrededor de 69
    -> que hace con ESTADOS_DE_BLOQUEO, que es lo unico que tiene
```

*Y **despues** decidir que se iguala y que se anade.* **Sin volver a `grep`ear con mis palabras.**
