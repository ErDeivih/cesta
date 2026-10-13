# B02 · **La tercera lectura, y es la que mas cambia el paquete**: ya hay ensayos del WAF y hay `fixtures/`

*(13 de octubre de 2026. **Se miro lo que la ronda 108 dijo que era «lo que mas informa y lo que menos se ha
mirado». Y estaba a un `ls` de distancia.**)*

## 1. Lo que hay

```
tests/  test_alcance_colectores.py        tests/  test_carrefour.py
        test_colectores.py                        test_fase2_f05_ejecutor_carrefour.py
        test_lidl_colector.py                     test_fase2_f05_ficha_carrefour.py
        test_alcampo.py
        test_alcampo_buscador.py          *** test_waf_alcampo.py ***
        test_alcampo_recorrido.py
        test_las_unidades_de_alcampo.py   tests/fixtures/    <- Y HAY CARPETA DE FIXTURES

```

> **Hay un ensayo del WAF -- `test_waf_alcampo.py` -- y hay `tests/fixtures/`.** *O sea que **lo que B02 pide
> probar ya tiene, al menos en parte, donde probarse.***
>
> *Y mi propia frase de la ronda 108 fue:* **«si ya hay fixtures, B02 es ampliarlos; y si no hay ninguno, B02 es
> crearlos, que es otra cosa. Eso no se sabe. Y se puede saber leyendo.»**
>
> **Se sabia a un `ls` de distancia, y llevaba ahi todo el tiempo.** *No hizo falta leer los ficheros: hizo falta
> **mirar que ficheros hay** -- que es la operacion mas barata de todas y la que no se me ocurrio hasta la
> cuarta ronda.*

## 2. Y esto cambia el tamano de B02, que ya es la tercera vez que cambia

```
RONDA 105:  «construir lo que no hay»                    -> FALSO
RONDA 106:  «igualar Carrefour a Alcampo y anadir la distincion»   -> FALSO
RONDA 107:  «leer lo que Alcampo ya hace y llevarlo»     -> mas cerca, pero sin mirar los ensayos
RONDA 108:  «no se sabe si hay fixtures»                 -> FALSO: hay carpeta y hay un ensayo del WAF
```

**Y la conclusion que si se sostiene, con lo leido:**

  - **Alcampo tiene la resistencia entera**: `RetoWAF` (13 usos), `AVANCE_MINIMO`, `CORTES_PARA_RENDIRSE`,
    `MAX_RENOVACIONES`, `detener`, y un mensaje que lo dice.
  - **y tiene su ensayo**: `test_waf_alcampo.py`.
  - **Carrefour tiene `ESTADOS_DE_BLOQUEO` y lo usa** *en un sitio, la 528.*
  - **y hay `tests/fixtures/`** *-- con lo que sea dentro, que **no se ha mirado**.*
  - **los otros cuatro colectores**: *sin mirar.*

> **Asi que B02, con lo que se sabe, no es construir: es *completar*. Y el trabajo concreto que se sostiene sin
> suponer nada es:***
>
>   1. **leer `test_waf_alcampo.py`** *-- que dice **que se considera comportamiento correcto hoy**;*
>   2. **leer `tests/fixtures/`** *-- que dice **que material de prueba hay**;*
>   3. **y solo entonces** decir que le falta a B02. *Que puede ser **mucho menos** que lo que las tres rondas
>      anteriores dijeron.*

## 3. Y la leccion, que ya van cuatro rondas y siempre es la misma

```
ronda 68   una medida con un caso, y un nombre puesto sin contrastar
ronda 105  un grep con las palabras equivocadas
ronda 106  una correccion hecha sin leer el fichero
ronda 107  una lectura de dos lineas y una conclusion de tres
ronda 108  y esta: NO MIRAR QUE FICHEROS HAY
```

> **Las cinco son la misma cosa, y cada una es un paso mas cerca de lo obvio:** *primero busque con mis palabras,
> luego concluí sin abrir, luego abri dos lineas, y **ahora resulta que ni siquiera habia mirado el directorio**.*
>
> **Y lo que las caza no es leer mejor: es empezar por lo mas barato.** *`ls tests/` cuesta menos que cualquier
> `grep`, y **habria contestado a la pregunta de las cinco rondas**: ¿que hay ya?*
>
> ***La pregunta que hay que hacer primero en un paquete no es «que le falta», sino «que hay».*** *Y se contesta
> mirando, no buscando.*
