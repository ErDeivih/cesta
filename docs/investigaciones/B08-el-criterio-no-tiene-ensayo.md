# B08 · **`R1=270` y `media=135` no estan en ningun ensayo** -- y eso confirma la ausencia

*(13 de octubre de 2026. **Y cierra la comprobacion: el criterio de B08 no tiene ensayo, porque la funcion no esta.**)*

## 1. Lo que se busco, y lo que salio

```
*** EL CRITERIO DE B08 DICE: ***  *«Aceptar *** R1=270, media=135 ***, ausencia de energia con proteina
conocida, idempotencia, recarga y aislamiento A/B»*

$ git grep -ln "270" -- tests/          -> *** `test_movimientos.py` · `test_pipeline.py` *** *
$ git grep -ln "270" -- core/ plataforma/ -> *** `cesta.py` · `aprende.py` *** *
```

> *** Y **los dos ficheros de ensayo se leyeron, y no son eso**: *
> ```
> *** `test_movimientos.py` ***  -> *** son MOVIMIENTOS DE PRECIO ***: *«una bajada de verdad sale», *
>    *«un cambio de formato no es una bajada», *«el ruido de redondeo no es una bajada»... *
>    *** y su unico `270` es un PRECIO dentro de una serie: *** *
>    *`gold(_serie("dia", "23", [("2026-09-27", 300, 300...` -- *o sea: **coincidencia.** *
> *** `test_pipeline.py` ***      -> *y el suyo, **de otra cosa.** *
> ```

## 2. *** Y eso confirma la ausencia por una cuarta via, y la mas directa ***

```
*** 1) LOS SIETE NOMBRES ***   -> *«previsto» y «objetivo» no aparecen*
*** 2) EL FRONTEND (73) ***     -> *y ninguna es del plan*
*** 3) EL API Y EL NUCLEO ***   -> *** `previst`/`prevision` dan CERO *** *
*** 4) *** Y LOS ENSAYOS *** ***        -> *** y el criterio de B08 (`R1=270`, `media=135`) NO TIENE ENSAYO *** *
```

> *** O sea: *** *** **el plan da numeros de aceptacion para una funcion que no existe**, *y **no hay ningun
> ensayo que los use** -- *porque **no hay nada que ensayar.** *
>
> *** Y **es la confirmacion mas limpia de las cuatro** *** -- *porque **un criterio de aceptacion con numeros
> concretos (`270`, `135`) deja rastro en los ensayos** *si **la funcion existe**; *y **no hay ninguno.** *
>
> *** Y **es tambien la mas util para el que retome**: *** *** los numeros **ya estan escritos en el plan**, *
> *asi que **la funcion se puede construir contra ellos** -- *y **sabremos si esta bien cuando un ensayo los use.** *

## 3. Y el estado, con la ausencia **confirmada por cuatro vias**

```
*** B08 · y NO es 4 de 5 ***
  *** lo que esta: *** *receta versionada, raciones, cobertura, recibo de consumo, «sin totalizar un dia
     incompleto», «sin colorear diagnosticos», y «compra nunca genera consumo por si sola»*
  *** lo que falta: *** *** la VISTA DE PREVISTOS · el OBJETIVO opcional · y las GRAFICAS de los tres ***
  *** y la ausencia esta confirmada por CUATRO vias: *** *
     *los siete nombres · el frontend (73) · el API y el nucleo (cero) · *** y los ensayos (el criterio no tiene ninguno) *** *
  *** y la materia prima esta, y el patron de la cobertura tambien (`desde-la-compra`). *** *
```

> *** Y **el objetivo sigue activo**, *y **el siguiente paso es concreto**: *** *** construir **la vista de
> previstos** *-- *sumar `costeReceta` sobre las recetas del plan, **con su cobertura**, *y **con los numeros del
> plan como criterio.** *
>
> *** Y **se puede hacer sin inventar nada**: *** *la materia prima (plan con `comensales` y `version`, receta
> con `raciones`, `costeReceta` por racion) **esta**, *y **el patron de la cobertura** (`{con_dato, total}` y
> `sin_dato` con nombres) **tambien.** *
