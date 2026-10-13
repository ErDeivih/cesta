# B02 · **`RITMO`, con el motivo de cada cadena** -- y el comentario que es la mejor pieza del proyecto

*(13 de octubre de 2026. **Y el punto 189 queda cerrado con su codigo delante.**)*

## 1. La tabla, literal (`core/config.py:55`)

```python
RITMO = {
    "mercadona": 2.0,
    "aldi": 2.0,
    # AWS WAF: una cada 4 s evitaba el corte que se veia a 1/s, pero el 8 sep el
    # reto escalo a pedir un clic humano tras siete cortes. Menos presion es la
    # unica palanca que queda del lado del codigo: a una cada 6,7 s el recorrido
    # entero pasa de unos 27 a unos 45 minutos de trabajo real, que en una tarea
    # nocturna no le importa a nadie.
    "alcampo": 0.15,
    "dia": 1.0,          # Akamai: sin prisa
    "carrefour": 1.0,    # el Crawl-delay 60 de robots.txt solo es para TwengaBot,
    # **Lidl estaba sin declarar.** `ficha_lidl.descarga` usaba `RITMO.get("lidl", 1.0)`,
    # asi que su ritmo era un valor por defecto que nadie habia elegido ni podia revisar.
    # Declarado con el mismo 1.0 que se estaba aplicando: **no cambia lo que pasa, cambia
    # que se pueda ver y discutir.**
    "lidl": 1.0,
}
```

## 2. Y **cada cadena tiene su motivo escrito**, que es lo que la hace una tabla y no una lista

```
"mercadona": 2.0     · "aldi": 2.0
*** "alcampo": 0.15 *** -- *con el parrafo del WAF:*
    *** «el 8 sep el reto escalo a PEDIR UN CLIC HUMANO tras siete cortes. *** *** MENOS PRESION ES LA
    UNICA PALANCA QUE QUEDA DEL LADO DEL CODIGO: *** *a una cada 6,7 s el recorrido entero pasa de unos **27 a
    unos 45 minutos** de trabajo real, *** que en una tarea nocturna NO LE IMPORTa A NADIE. ***» *
    -> *o sea: **la lentitud se justifica con el reloj de la tarea** -- *y **«45 minutos de noche» no es un
    coste**, *porque **nadie esta esperando.** *
*** "dia": 1.0 ***        -- *** «Akamai: sin prisa» ***
*** "carrefour": 1.0 ***  -- *** «el Crawl-delay 60 de robots.txt SOLO ES PARA TwengaBot» ***
    -> *o sea: **leyo el `robots.txt`, y supo A QUIEN se aplica la regla** -- *y **por eso no la obedece a ciegas.** *
*** "lidl": 1.0 ***       -- *y su comentario, que es el de la pieza (2) del punto 189*
```

> *** Y las tres razones son **de tres clases distintas, y las tres son buenas**: ***
>
> ```
> alcampo   -> *** LA PRESION: *** *menos peticiones, para no provocar el reto -- y se mide en minutos de noche*
> dia       -> *** LA FUENTE: *** *«Akamai: sin prisa» -- la CDN no lo pide, y no hay motivo para correr*
> carrefour -> *** LA REGLA: *** *el `Crawl-delay` es de `robots.txt`, y **es para TwengaBot** -- leer la norma
>               incluye leer **a quien obliga***
> ```
>
> *** Y la de **carrefour** es **la mas fina de las seis**: *** *no es «obedecer» ni «desobedecer» -- *es **leer la
> regla y saber a quien se aplica.** *
>
> *** Que es **lo que este proyecto hace en todas partes**: *** *`_de_quien` (B07) · `ESQUEMAS` (B07) · y **un
> `Crawl-delay` que se lee antes de acatarlo.** *

## 3. Y el comentario de Lidl, **literal, es lo que el documento decia**

```
*** «**Lidl estaba sin declarar.** `ficha_lidl.descarga` usaba `RITMO.get("lidl", 1.0)`, asi que su ritmo era
UN VALOR POR DEFECTO QUE NADIE HABIA ELEGIDO NI PODIA REVISAR. Declarado con el mismo 1.0 que se estaba
aplicando: *** NO CAMBIA LO QUE PASA, CAMBIA QUE SE PUEDA VER Y DISCUTIR. ***» ***
```

> *** Y **coincide palabra por palabra con lo que `SUPERAPP-EJECUCION.md:923-925` decia** *** -- *o sea: **el
> documento y el codigo dicen lo mismo**, *y **el comentario esta donde tiene que estar: al lado del valor.** *
>
> *** Y **hay un detalle que vale**: *** *`fichas_lidl.py:114` **todavia** tiene `ritmo = config.RITMO.get("lidl",
> 1.0)` -- *o sea: **el `1.0` de reserva sigue ahi**, *y **ahora es una red de seguridad y no una decision
> escondida**, *porque **el valor de verdad esta declarado en `config.RITMO`.** *
>
> *** Y **eso es lo correcto, y no una contradiccion**: *** *un `get` con defecto **sobre un valor declarado** es
> **defensa**; *el mismo `get` **sin nada declarado** era **la decision invisible.** *

## 4. Y el punto 189 queda **cerrado con el codigo delante**

```
(1) *** Lidl esta en `ORDEN` ***        `run.py:40  ORDEN = [..., "lidl"]`
(2) *** Su ritmo esta DECLARADO ***      *** `core/config.py:70  "lidl": 1.0,` -- con su comentario l66-69 ***
(3) *** Y con presupuesto ***            *** `LIMITE_POR_EJECUCION` en `fichas_lidl.py` (y `fichas_carrefour.py`) ***
                                         *-- contra `--limite = 3`, que daban 1.676 ejecuciones y CUATRO AÑOS Y MEDIO*
```

> *** Y **las tres, con su linea.** *** *Que es **todo lo que B02 necesitaba**, y **esta medido y no contado.** *
>
> *** Y **la frase del comentario es la que hay que llevarse**: ***
>
> > *** «No cambia lo que pasa, cambia que se pueda ver y discutir.» ***
>
> *** Es **la definicion de declarar**, *y **es aplicable a `fuente_dato`, a `FUENTES`, a `ABSTIENE` y a este
> `1.0`**: *el valor **no cambia**; *lo que cambia es **que ya no esta escondido.** *
