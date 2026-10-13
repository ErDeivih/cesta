# G09 · **La contradiccion, RESUELTA por medicion**: Lidl SI corre a las 06:00, y la frase vieja se corrige

*(2026-10-14, ~02:15. **Y es la decimoquinta correccion, y la primera que es a un comentario del proyecto y no a mi.**)*

## 1. La cadena, medida entera

```
*** `registrar-tarea.ps1` ***
  l7   *** «Se dispara a las 06:00 todos los dias, AL ENCENDER el ordenador» *** *
  l28  `New-ScheduledTaskAction -Execute $bat -WorkingDirectory $car[...]`  *-- la tarea llama a `ejecutar.bat`*
*** `ejecutar.bat` ***
  l57  *** `uv run python -m projects.cesta.run >> "data\ejecuciones.log" 2>&1` *** *
*** `projects/cesta/run.py` ***
  l40  *** `ORDEN = ["carrefour", "dia", "mercadona", "aldi", "alcampo", *** "lidl" ***]` *** *
  l234 *** `fuentes = args.solo or *** ORDEN ***` *** ***  <- *** y `ORDEN` ES LA LISTA DE FUENTES *** *
  l119 *** «`ORDEN` --, *y su `main` exige `--html` o `--w[eb]» *** *-- *o sea: **`run.py` ya sabe que
       Lidl esta en `ORDEN`**, *y **documenta como lo llama.** *
```

> *** O sea: *** *** **la tarea de las 06:00 -> `ejecutar.bat` -> `run.py` -> `ORDEN`, y Lidl esta en `ORDEN`.** *
>
> *** -> *** *** LIDL SI CORRE A LAS 06:00. *** *Y **`lidl.py:22` era un resto desactualizado.** *

## 2. *** Y la contradiccion se resolvio MIDIENDO, no suponiendo ***

```
*** LO QUE YO ESCRIBI EN LA RONDA ANTERIOR: ***
  «*las dos son posibles*: *a) el docstring esta viejo... *b) o `ORDEN` no es la tarea de las 06:00...
  *** y NO SE PUEDE SUPONER CUAL. ***»

*** Y LO QUE SE HIZO: *** *** seguir la cadena, eslabon por eslabon *** *
  `registrar-tarea.ps1` (06:00) -> `ejecutar.bat:57` -> `run.py:234` -> `ORDEN:40`
  *** -> y la respuesta no admite las dos: `ORDEN` SI es la lista de fuentes, y Lidl SI esta. *** *
```

> *** Y **es la misma disciplina de las otras dos veces**: *** *«**no existe nada**» (con el WAF delante) y
> «**y nada mas**» (con `runlog` delante) *-- *y las tres se cayeron **al seguir la cadena un eslabon mas.** *
>
> *** Y **esta vez, ademas, se corrigio**: *** *** porque **el resto desactualizado estaba en el fichero**,
> *y **`run.py:119` ya lo citaba al reves.** *

## 3. *** Y el cambio, que sustituye una proteccion por otra ***

```
*** LO QUE DECIA (y era verdad entonces): ***
  *** «**No esta en la tarea de las 06:00, a proposito.** *La ampliacion lo pide asi: "pasar una captura
  acotada antes de anadirlo a la tarea diaria". *** Se ejecuta a mano y no puede romper la pasada diaria. ***» *

*** Y LO QUE DICE AHORA: ***
  *** «**Si esta en la tarea de las 06:00, y esto es un cambio de criterio.** *...* *** Y ya no:
  `run.py:40` lo tiene en `ORDEN`, y `run.py:234` usa `ORDEN` como la lista de fuentes de la pasada diaria
  -- *asi que **si corre a las 06:00**, y **lo que lo protege ya no es la ausencia, sino el PRESUPUESTO**:
  `LIMITE_POR_EJECUCION` en `fichas_lidl.py`, y el `--limite` del lanzador.» *** *
```

> *** Y **esa es la forma del proyecto, y esta escrita en el comentario nuevo**: *** *** **una proteccion que
> se quita se sustituye por otra, Y LA FRASE QUE LA DESCRIBIA SE CORRIGE EN EL MISMO CAMBIO.** *
>
> *** -> y **es la leccion del dia**: *el docstring **no era un error de nadie**; *era **una frase que fue
> verdad**, *y **que dejo de serlo cuando Lidl entro en `ORDEN`** *-- *y **nadie la quito.** *

## 4. Y el estado, con **la prediccion de B02 confirmada en su mecanismo**

```
*** B02 · la prediccion ***
  *** lo que predijo ***  -> *«despues de la proxima pasada de las 06:00, `runs.csv` tendra una fila de `lidl`»*
  *** y AHORA SE SABE QUE EL MECANISMO ESTA ***  ***  -> *** *** `registrar-tarea.ps1` -> `ejecutar.bat`
     -> `run.py:234` -> `ORDEN` con Lidl *** *
  *** -> o sea: **la prediccion no depende de una esperanza: depende de una cadena, y la cadena esta.** *
  *** y lo que falta ***  -> *** la pasada, que es a las 06:00 *** *-- *y **en unas cuatro horas.** *
```
