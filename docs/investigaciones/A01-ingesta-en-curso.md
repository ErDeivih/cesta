# El ensayo de la ingesta de las dos cadenas que faltan — en curso

*(12 de octubre de 2026. **Se deja escrito lo que se midió, que es poco, y por qué es poco.**)*

## Qué se lanzó

```
uv run python -m projects.cesta.run --solo carrefour alcampo
```

*En segundo plano, porque una pasada de las dos son horas.*

## Lo que se midió a los quince minutos

```
bronze:                  IDENTICO a antes -- alcampo y carrefour siguen con dato de 10-11
data/inventario.sqlite:  10-11 22:25, sin tocar
ficheros escritos en los ultimos 40 minutos:  NINGUNO
```

**O sea: el trabajo corre y no ha escrito nada todavía.**

## Y no es un fallo: es lo que tarda

**Carrefour tiene 16 195 filas y Alcampo 23 128.** *Y Alcampo va a **una petición cada 6,7 segundos*** --
*que es su ritmo declarado, y su comentario dice por qué: el WAF de AWS escaló a pedir un clic humano, y
menos presión es la única palanca del lado del código.*

> **Una pasada completa de las dos son horas, no minutos.** *Y bronze puede escribirse **al final** y no
> durante, así que la ausencia de ficheros nuevos **no distingue «va bien» de «no ha llegado»**.*

## Y eso es un límite del instrumento, no del trabajo

**No se puede decir si avanza**, porque la única señal que hay -- el fichero de bronze -- se escribe tarde
**y porque mi propio comando la esconde**: *le puse `Select-Object -Last 40`, que **bufferiza toda la salida
hasta el final**.* *Así que ni el log sirve para verlo avanzar.*

> *Es el mismo tipo de error que el de las claves del cursor y el del formato del descuento, y el más
> tonto de los siete*: **no me dejé mirar, y luego me quejé de no ver.** *Si se vuelve a lanzar, va **sin**
> el `Select-Object` y con la salida a un fichero.*

## Lo que se puede afirmar, y lo que no

**Se puede afirmar**: *el catálogo publicado es **coherente** -- `coherente: true`, con seis huellas --, y
**lo que le falta es dato nuevo de dos cadenas**.*

**No se puede afirmar**: *que el ensayo vaya bien, ni cuándo termina.*

**Si termina**: *se republica, y el catálogo queda al día.*

**Si Alcampo se queda en el reto del WAF** -- *que pide un clic humano --*: *quedará dicho **cuál de las dos
falta y por qué**, que es el límite que la fuente pone.*
