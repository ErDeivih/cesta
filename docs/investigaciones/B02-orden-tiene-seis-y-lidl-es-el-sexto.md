# B02 · **`ORDEN` tiene seis, y Lidl es el sexto** -- y el codigo documenta el fallo que lo hacia invisible

*(13 de octubre de 2026. **Y esta es la respuesta entera, con el defecto escrito al lado.**)*

## 1. Lo que hay, literal (`projects/cesta/run.py`)

```python
# Orden a proposito para el modo en fila: primero los lentos. En paralelo el orden
# solo decide quien arranca antes, pero se conserva porque tambien es el orden en
# que se leen los resultados.
# **Lidl entra aqui, y por eso**: tiene colector (`collectors/lidl.py`), descubrimiento
# (`descubrir_lidl.py`), cola de fichas y parser, y `ORDEN` no lo incluia -- que es la
# primera mitad del punto 189 de G09. *`_en_paralelo` resuelve por nombre de modulo
# (`collectors.<nombre>`), asi que anadirlo es una palabra; y va **al final** porque
# `ORDEN` tambien es el orden de lectura de los resultados.*
ORDEN = ["carrefour", "dia", "mercadona", "aldi", "alcampo", "lidl"]

# **Los que tienen CLI propia, y con que argumentos se les llama en la pasada diaria.**
#
# *Solo Lidl, y por un motivo que ya costo una busqueda*: **su `main` exige `--html` o `--web`
# (`required=True`), *y aqui se llamaba `main()` a secas* -- *asi que `argparse` salia con [error]*.
# **el dia seguia sin Lidl, con un aviso en el log que parecia una precaucion**.
#
# **`--escribir` va con `--web` a proposito**: *es lo que convierte la captura en bronze, y [...]
```

## 2. Y contesta **todo**, y con el defecto escrito

```
`ORDEN = ["carrefour", "dia", "mercadona", "aldi", "alcampo", *** "lidl" ***]`
   -> *** LIDL ES EL SEXTO. *** *Y **va al final** -- y **el comentario dice por que**: *«`ORDEN` tambien es el
   orden de LECTURA de los resultados.» *

*** Y el defecto que hacia invisible su ausencia, escrito por quien lo arreglo: ***
   *** «su `main` exige `--html` o `--web` (`required=True`), y aqui se llamaba `main()` a secas -- asi que
       `argparse` salia con [error]. *** *** EL DIA SEGUIA SIN LIDL, CON UN AVISO EN EL LOG QUE PARECIA UNA
       PRECAUCION. ***» ***
```

> *** Y esa ultima frase es **la mejor descripcion de un fallo silencioso que hay en todo el proyecto**: ***
> *Lidl **no corría**, *y **el log decía algo que parecía prudencia** -- *o sea: **el sintoma se disfrazaba de
> virtud.** *
>
> *** Y **es la misma familia que B02 encontro nueve veces en esta sesion**: *** *«no existe nada» cuando el WAF
> estaba ahi; «y nada más» cuando `runlog` estaba ahi; y ahora **«un aviso que parecía una precaución»** cuando
> **faltaba una cadena entera.** *
>
> *** Y **la leccion, que el codigo deja escrita**: *** *** un fallo que se registra como aviso **se lee como
> cuidado**, y **por eso tarda en encontrarse.** *

## 3. Y `--escribir` va con `--web` a proposito

```
*** «`--escribir` va con `--web` a proposito: es lo que convierte la captura en bronze» ***
```

> *** O sea: *** *** Lidl **si escribe** en el ciclo diario *** -- *y **`--escribir` es lo que pasa de captura a
> bronze.** *
>
> *** Y **por eso el `log_run` dentro del `--escribir` (arreglo `5039b9c`) **si se ejecuta** en la pasada diaria** ***
> -- *o sea: **Lidl debería tener filas en `runs.csv`.** *
>
> *** Y **no las tiene.** *** *** Y eso ya no es una explicacion: es **la siguiente pregunta**, y es distinta de la
> anterior.** *

## 4. Y la pregunta que queda, ahora **precisa**

```
MEDIDO:      `ORDEN` incluye lidl · `--escribir` va con `--web` · y `lidl.py` registra dentro del `--escribir`
MEDIDO:      `data/raw/fuente=lidl` existe
MEDIDO:      *** `data/runs.csv` NO tiene ninguna pasada de lidl ***
Y LA PISTA:  *** «la PRIMERA MITAD del punto 189 de G09» *** -- *o sea: **hay una SEGUNDA mitad.** *
```

> *** Asi que **lo que falta no es el ciclo: es averiguar por que su pasada no deja fila**, *** *y **hay dos
> sospechosos, y ninguno se elige**:*
> 1. *** el arreglo `5039b9c` es **posterior a la ultima pasada de Lidl** *** -- *o sea: **Lidl no ha corrido desde
>    que se arreglo el registro**, y **por eso no hay fila** (y es lo mas simple);*
> 2. *** o **«la segunda mitad del punto 189 de G09»** es justamente esto, y esta pendiente.** *
>
> *** Y **la (1) se puede comprobar con una fecha**: *** *`runs.csv` tiene un `ts` por fila, *y **`5039b9c` tiene su
> fecha.** *Si el commit es **posterior a la ultima pasada de cualquier cadena**, *entonces **ninguna ha corrido
> desde el arreglo** -- *y **Lidl sin fila es lo esperado.** *

## 5. Y la correccion, con su numero

```
RONDA 205:  «Lidl NO esta en el ciclo diario; su crudo existe porque se ejecuto a mano»
            *** FALSO *** -- *`run.py:40` lo tiene, y **el comentario explica por que y desde cuando.** *

RONDA 206:  *** «Lidl SI esta en el ciclo (`ORDEN`, sexto); y `--escribir` va con `--web` a proposito.» ***
            *** y lo que queda por explicar es SOLO su fila en `runs.csv` *** -- *y la explicacion mas simple es
            que **no ha corrido desde el arreglo del registro.** *
```

> *** Decima correccion, y **la mas limpia**: *** *la hizo **la comprobacion que escribi antes de concluir**, *en la
> ronda siguiente, *y **dejo una pregunta mejor que la que habia.** *
