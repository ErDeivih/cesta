# B08 · **La AUSENCIA, CERRADA**: tres capas, y **cero apariciones** en el API y en el nucleo

*(13 de octubre de 2026. **Y ya no es «no lo he encontrado»: es un cero, en dos capas, y con la tercera medida.**)*

## 1. La comprobacion que faltaba, y su resultado

```
$ git grep -ln "previst\|prevision" -- "plataforma/api" "core"
*** -> NADA. Ni un fichero. ***  *(exit code 1)*
```

> *** O sea: *** *** **ni `previst` ni `prevision` aparecen en `plataforma/api/` ni en `core/`.** *
>
> *** Y **eso cierra la pregunta por esta via**, *y por las tres capas: *
> ```
> *** 1) LOS SIETE NOMBRES de B08 ***  -> *«previsto» y «objetivo» no aparecen por ninguno*
> *** 2) EL FRONTEND ***                -> *73 coincidencias de `nutricion`/`kcal`, *y **ninguna es del PLAN** *
> *** 3) EL API Y EL NUCLEO ***         -> *** y `previst`/`prevision` dan CERO *** *
> ```

## 2. Y **lo que da la ausencia no es «falta una funcion»: es donde esta la frontera**

```
*** LO QUE HAY, Y EN SU SITIO: ***
  *** el producto ***   -> *`Producto.tsx`, `tipos.ts` (`nutricion`, `kcal_100g`, `energia_kcal`), Open Food Facts*
  *** una receta ***    -> *`logica/costeReceta.ts`: «nutricion por racion y coste estimado»* (G05)
  *** lo registrado *** -> *`diario.ts` (`cobertura`, `sin_nutricion`, `kcal_conocida`), `Diario.tsx`, `Tendencias.tsx`*
  *** y lo local ***     -> *`cocina.ts` / `Cocina.tsx` -- *y **su propio texto dice que no se sincroniza.** *

*** Y LO QUE NO HAY: *** *** LA SUMA SOBRE EL PLAN *** *
   -> *o sea: **la nutricion de lo que se VA a comer**, *y **su cobertura.** *
```

> *** Y **la frontera esta en la palabra PLAN** *** -- *y **es exactamente la que el encargo dibuja**: *
> *** «el PLAN calcula nutricion prevista; *** *** el diario solo registra las porciones confirmadas» *** -- *
> *o sea: **los dos lados**, *y **el segundo existe** (el diario, con su cobertura), *y **el primero no.** *
>
> *** Y **la materia prima esta**: *** *el plan da **`comensales`** y **`version`** por receta (medido hoy), *
> *y **`costeReceta` sabe calcular por racion.** *Asi que **no falta un dato: falta la suma, y su cobertura.** *

## 3. Y **la cobertura es la parte que no se puede saltar**, y el proyecto ya sabe hacerla

```
*** `Diario.tsx:3` ***  -> *** «**Las dos cifras van juntas.** "Conocido: 1.250 kcal" sin decir cuantas entradas
   no traen dato *** es un[a mentira] ***» *
*** `desde-la-compra` ***  -> *y **ya lo resuelve para el consumo**: *`cobertura: {con_dato, total}`, *
   *y **`sin_dato` con sus nombres.** *
*** `formato.ts` ***  -> *«un dato que no tenemos es "no lo se", **nunca un cero**»*
```

> *** O sea: *** *** **el patron de la prevision esta en el proyecto, y esta en `desde-la-compra`.** *
> *Y **lo que falta es aplicarlo al plan**: *sumar **las recetas del plan**, *y **decir cuantas no traen dato.** *
>
> *** Y **si se sumara sin la cobertura**, *daria **un numero menor que la realidad** -- *y **seria la mentira que
> `Diario.tsx:3` nombra**, *y **la que el docstring de `desde-la-compra` nombra**: *«**callar las demas
> convertiria un dato que falta en una comida que parece completa**». *

## 4. Y el estado de B08, con la ausencia **cerrada y con su forma**

```
*** B08 · 4 de 5 · una AUSENCIA medida ***  -> *y ahora la ausencia esta medida **por tres capas**: *
  *** 1) los siete nombres ***      -> *nada*
  *** 2) el frontend (73) ***        -> *nada del plan*
  *** 3) *** `plataforma/api/` y `core/` ***  -> *** CERO apariciones de `previst`/`prevision` *** *
  *** y la forma de la ausencia: *** *** falta LA SUMA SOBRE EL PLAN, y SU COBERTURA *** *
     *-- y **la materia prima esta** (`comensales`, `version`, `costeReceta`), *y **el patron de la cobertura
     tambien** (`desde-la-compra`). *
```

> *** Y **no se declara «no existe»** *** -- *se declara *** *** **que se busco en tres capas, y que dos dan cero, y
> que la tercera tiene las piezas sueltas.** *
>
> *** Y **es mas util que un «no existe»**: *** *dice **donde esta la frontera** (el producto, la receta, lo
> registrado -- y **el plan**), *y **que falta** (la suma y su cobertura), *y **con que se hace** (lo que ya hay). *
