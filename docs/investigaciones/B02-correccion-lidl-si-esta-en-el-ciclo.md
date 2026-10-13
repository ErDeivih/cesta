# B02 · **CORRECCION**: el `REM` estaba desactualizado -- **Lidl SI esta en el ciclo diario**

*(13 de octubre de 2026. **La decima correccion a mi mismo. Y esta vez, la hizo la comprobacion que yo mismo puse.**)*

## 1. Lo que acabo de medir

```
`projects/cesta/run.py`  (504 lineas)

  l35-38:  *** «**Lidl entra aqui, y por eso**: tiene colector (`collectors/lidl.py`), descubrimiento
               (`collectors.<nombre>`), asi que anadirlo es una palabra; y va **AL FINAL** porque [...]» ***
  l112:    mod = importlib.import_module(f"projects.cesta.collectors.{nombre}")
```

> *** O sea: **Lidl esta en la lista de fuentes de `run.py`**, *con **un comentario que explica por que**, *y
> **`importlib` importa el colector por nombre.** *
>
> *** Y *** *** la lista de cadenas **no esta en `ejecutar.bat`: esta en `run.py`** *** -- *y el `REM` de
> `ejecutar.bat` («las cinco cadenas») **es un comentario que se quedo viejo cuando Lidl entro.** *

## 2. Y la correccion es exacta: **lo que yo dije era falso, y lo dijo mi propia advertencia**

> *** Lo que escribi en el documento anterior: ***
>
> > *«`ejecutar.bat` nombra CINCO, y **Lidl no esta.**»*
> > *«Lidl **no esta en el ciclo diario**; su crudo existe porque se ejecuto a mano.»*
>
> *** Y **la frase que salvo el error fue esta**, escrita en el mismo documento: ***
>
> > *** «Y NO SE DICE QUE FALTE HASTA ENTONCES: la comprobacion es una sola -- leer `projects/cesta/run.py` y ver si
> > la lista de fuentes esta escrita o se descubre.» ***
>
> *** *** Y la lista ESTA escrita... en `run.py`. *** *** Y Lidl esta dentro. *** *
>
> *** O sea: **el paso que me salvo fue el que me puse antes de concluir** *** -- *y **es la decima vez en esta sesion
> que una conclusion se cae al comprobarla.** *

## 3. Y queda **un dato que sigue sin explicacion**, y hay que decir cual

```
SIGUE SIN EXPLICAR:  *** `data/runs.csv` NO tiene NINGUNA pasada de lidl ***
   y sin embargo:     *** `data/raw/fuente=lidl` SI existe ***
   y `lidl.py` registra con `log_run` *** dentro del bloque `--escribir` ***
```

> *** Y **las explicaciones posibles, ahora, son otras**: ***
> 1. *** Lidl corre **sin `--escribir`** *** -- *y entonces **no registra por diseno** (el arreglo `5039b9c`);*
> 2. *** o corre con `--escribir` y **sale por uno de los dos caminos de fallo** *** -- *y entonces **registraria
>    `0,1`**, *y **tampoco hay fila** -- *asi que **esta se descarta.** *
> 3. *** o `run.py` **no le pasa `--escribir` a Lidl** *** -- *y **esto es lo que hay que mirar**, porque **las
>    otras cinco si registran.** *
>
> *** Y **la (3) es la mas probable** *** -- *porque **el comentario de `run.py:123` dice «y solo se le pasan a quien
> los espera»**: *o sea: **los argumentos se pasan por colector**, *y **puede que a Lidl no se le pase `--escribir`.** *
> *** Y **NO SE DICE QUE SEA ESO**: se dice que **es lo que hay que mirar, y donde.** *

## 4. Y lo que **NO cambia** de todo lo medido

```
*** NO CAMBIA: *** `data/runs.csv` no tiene pasadas de lidl   -- *es un HECHO*
*** NO CAMBIA: *** `data/raw/fuente=lidl` existe               -- *es un HECHO*
*** NO CAMBIA: *** `lidl.py` registra dentro del `--escribir`  -- *es CODIGO leido*
*** NO CAMBIA: *** y el dictamen dice «limitado», y sigue bien -- *lo que cambia es **por que***
*** Y CAMBIA: *** ~~«Lidl no esta en el ciclo diario»~~  ->  *** «Lidl SI esta; su pasada no se registra.» ***
```

> *** O sea: **la casilla del dictamen sigue en «limitado»**, *y **su razon se afina otra vez**: *no es **el ciclo**;
> es **el registro** -- *y **el registro esta dentro del `--escribir`**, *que es **donde yo lo puse a proposito.** *
>
> *** Y hay **una ironia que conviene dejar escrita**: *** *** **arregle un log fantasma, y el efecto colateral es que
> una cadena puede correr sin dejar rastro.** *** *Y **las dos cosas son correctas a la vez** -- *lo que **falta** es
> **que Lidl escriba**, *y **que su escritura quede registrada.** *

## 5. Y la leccion, que ya es la decima

```
RONDA 105 (B02):   «no existe nada»                     -> FALSO: `RetoWAF` (13 usos)
RONDA 112 (B02):   «y nada mas»                          -> FALSO: `runlog`, `peticiones`
RONDA 116 (B02):   «el tiempo no se mide»                 -> FALSO: `time.monotonic()`
RONDA 150 (B08):   «previsto no aparece»                  -> *y NO se concluyo: se probaron SIETE palabras*
RONDA 190 (B13):   «las siete listas del puente estan»     -> *y NO se concluyo: se midieron y NO estan en casa*
*** RONDA 205 (B02):  «Lidl no esta en el ciclo diario»  -> FALSO: `run.py:35` lo tiene, y LO EXPLICA ***
```

> *** Y las dos ultimas **no fueron errores**: fueron **afirmaciones con la comprobacion escrita al lado** *** -- *y
> **una se confirmo** (las listas) *y **la otra se cayo** (Lidl). *
>
> *** Que es **la diferencia que esta sesion ha producido**: *** *** no «no equivocarse», sino **poner la comprobacion
> donde se pueda hacer.** *
