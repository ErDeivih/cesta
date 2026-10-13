# B01/B02 · **El `ejecucion.lock` y los ocho procesos**: lo que hay, y lo que **no** se concluye

*(13 de octubre de 2026. **La verificacion que el encargo pide primero. Y con el cuidado de siempre.**)*

## 1. Lo que hay, medido

```
data/ejecucion.lock:   escrito 09/07/2026 12:19:06   <- HACE 36 DIAS (52098 minutos)
                       contenido: "0"                 <- 1 byte, el literal «0»

procesos python:  8, y por parejas (4 MB + uno grande):
   pid 11348  15:27:14   4 MB        pid 34100  15:27:14  118 MB
   pid 24196  16:15:21   4 MB        pid 45748  16:15:21  324 MB
   pid 11512  16:29:58   4 MB        pid 41332  16:29:58   15 MB
   pid 36580  16:30:03   4 MB        pid 21712  16:30:03  285 MB

tarea programada:  Cesta diaria   ·   estado Ready   ·   proxima 10/14/2026 06:00
version publicada: v20261013-155356  (la mas nueva de tres de hoy)
```

## 2. Y lo que **NO** se concluye, que es lo importante

**El candado tiene 36 dias y contiene `"0"`.** *Y hay **dos lecturas**, y **son contrarias**:*

```
LECTURA A:  el candado esta TOMADO desde el 7 de septiembre -> la ingesta lleva 36 dias
            sin poder arrancar. *** Seria grave: la captura diaria no habria corrido. ***

LECTURA B:  `"0"` es el valor de «LIBRE» -> el candado esta SUELTO, y la fecha es de la
            ultima vez que se solto. *** Y entonces no hay nada roto. ***
```

> *** Y no se elige ninguna de las dos sin leer `core/runlock.py`. ***
>
> *Y hay un dato que apunta a B: la **version publicada es de hoy a las 15:53** (`v20261013-155356`), **y las otras dos tambien son de hoy** (13:43 y 13:55).*
>
> *** Si la ingesta no hubiera podido arrancar en 36 dias, no habria tres versiones publicadas hoy. ***
>
> *Pero **eso es un indicio, no una prueba**: las versiones se pueden publicar a mano. **Asi que se dice el
> indicio, y se dice que es un indicio.***

## 3. Y los ocho procesos: lo que parecen, y por que

**Van por parejas, con segundos de diferencia, y tres arranques (15:27, 16:15, 16:29/16:30).** *Y uno de cada
pareja ocupa 4 MB.*

> **Eso se parece mucho a `uv run` + el interprete real** *-- **que es exactamente lo que lanza cada `pytest` y cada
> `uv run python` que he ejecutado esta tarde**.*
>
> *Y **cuadra con las horas**: a las 15:27 y 16:15 y 16:29 he corrido la suite y los ensayos de Lidl.*
>
> *** O sea: los ocho procesos son MIOS, no de la ingesta. *** *Y eso **tambien es un indicio**: no hay ningun
> proceso con pinta de captura larga (que dura minutos y ocupa cientos de MB **durante mucho tiempo**).*
>
> **Y no se concluye mas.** *No se matan: no son mios para matar sin saberlo, y **el encargo dice preservar**.*

## 4. Y el estado operativo, que si se puede afirmar

```
AFIRMADO, con su fuente:
  - la tarea programada EXISTE, esta Ready, y su proxima es manana a las 06:00
  - hay TRES versiones publicadas de hoy, y la mas nueva es de las 15:53
  - el fichero de cobertura de Lidl es de hoy
  - data/runs.csv tiene 226 pasadas de cinco cadenas, la ultima de hoy a las 10:48 (alcampo)

SIN CONCLUIR, y se deja escrito:
  - si `ejecucion.lock` con "0" significa TOMADO o LIBRE   <- se lee en core/runlock.py
  - si los 8 procesos son mios o de una captura            <- se mira con su linea de comandos
```

> *** Que es exactamente la regla: lo que se ha medido se afirma, y lo que no, se dice que no. *** *Y las dos cosas
> que no se concluyen **se pueden averiguar en una ronda**: leyendo `core/runlock.py` y mirando la linea de
> comandos de un proceso.* **No suponiendo.**
