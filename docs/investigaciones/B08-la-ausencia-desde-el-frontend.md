# B08 · **La AUSENCIA del eje de la PREVISION, confirmada desde el FRONTEND**

*(13 de octubre de 2026. **Y es la segunda confirmacion, por una via distinta a los siete nombres de B08.**)*

## 1. Lo que se busco, y lo que salio

```
`plataforma/web/app/src`, patron `previst|previsto|prevision|nutricion|kcal`
*** -> 73 coincidencias, y NINGUNA es una vista de nutricion PREVISTA del plan. *** *
```

> *** Y **lo que SI hay**, *y **cada cosa en su sitio**: *
> ```
> *** `estado/cocina.ts` + `paginas/Cocina.tsx` ***  -> *el cuaderno (B07): *
>    *y su propio texto lo dice: *** «Cuaderno de esta pestaña, SIN SINCRONIZACION CON TU CUENTA.
>    SE PIERDE AL RECARGAR o cerrar» *** *
> *** `api/diario.ts` + `paginas/Diario.tsx` ***      -> *** el diario ***: *`cobertura`, `sin_nutricion`,
>    `kcal_conocida`, `fuente_dato` -- *o sea: **lo REGISTRADO** *
> *** `paginas/Tendencias.tsx` ***                    -> *las tendencias, con `kcal_conocida` -- **y lo REGISTRADO** *
> *** `paginas/Producto.tsx` ***                      -> *la nutricion **del producto**, y Open Food Facts*
> *** `logica/costeReceta.ts` ***                     -> *** y este es el mas cercano: *** *
>    *** «G05 lo pide en Recetas: *"nutricion por racion y coste estimado, *** DISTINGUIENDO CANTIDAD USADA DE
>    [ENVASES]" ***» *** -- *y **es de UNA RECETA.** *
> ```

## 2. Y por tanto **la ausencia se confirma por segunda vez, y por otra via**

```
*** B08 (medido antes): *** *«previsto» y «objetivo» NO aparecen por **ninguno de los siete nombres probados** *
*** Y AHORA, desde el FRONTEND: *** *las 73 coincidencias se reparten en **cuatro cosas**, *
   *y **ninguna es la prevision del plan**: *
     - **lo registrado** (diario, tendencias)      -> *el pasado*
     *- **lo local** (cocina)                        -> *y **ni se sincroniza***
     - **el producto** (Producto.tsx, OFF)          -> *el catalogo*
     *- **y una receta** (costeReceta.ts)             -> *y **no el PLAN***
```

> *** O sea: *** *** **hay nutricion de un producto, de una receta, y de lo que se ha comido -- y no hay
> nutricion de lo que se va a comer.** *
>
> *** Y **la frontera esta en la palabra «PLAN»** *** -- *y *`costeReceta.ts` **calcula la de UNA receta**; *
> *y **nadie la suma sobre el plan de la semana.** *
>
> *** Y **eso es exactamente el eje que el encargo nombra**: *** *** «el PLAN calcula NUTRICION PREVISTA; ***
> *** el diario solo registra las porciones confirmadas» *** -- *o sea: **los dos lados**, *y **el segundo existe**
> *(el diario, con su cobertura), *y **el primero NO.** *

## 3. Y **`costeReceta.ts` es la pieza que faltaria encadenar**, y se dice cual

```
*** LO QUE HAY: ***  `logica/costeReceta.ts` -> *«nutricion por racion y coste estimado» de UNA receta *
*** LO QUE FALTARIA: *** *sumar eso **sobre las recetas del plan de la semana** *
   -> *y **la materia prima esta**: *el plan da **`comensales`** y **`version`** por receta (medido hoy), *
      *y `costeReceta` **sabe calcular por racion** *
   *** -> o sea: **no es que falte un dato: falta la SUMA, y su cobertura.** *
```

> *** Y **la cobertura es la parte que no se puede saltar**: *** *si **cuatro de las cinco recetas** del plan
> **no tienen nutricion**, *sumar **las que si** daria **un numero menor que la realidad** *-- *y **es exactamente
> lo que `Diario.tsx:3` dice de las cifras**: *** «las dos cifras van juntas: "Conocido: 1.250 kcal" sin decir
> cuantas entradas no traen dato es un[a mentira]» *** *
>
> *** Y **`desde-la-compra` ya resuelve eso para el consumo** *** -- *`cobertura: {con_dato, total}` y `sin_dato`
> con sus nombres. *Asi que **el patron esta en el proyecto**, *y **la prevision tendria que hacer lo mismo.** *

## 4. Y **no se declara «hay que construirlo»**, y el motivo es la leccion de B02

```
*** LO QUE SE PUEDE DECIR, MEDIDO: ***
  1. en el frontend **no hay** una vista de nutricion del plan (73 coincidencias, y ninguna lo es)
  2. **si hay** nutricion de producto, de receta, y de lo registrado
  3. y **`costeReceta.ts` calcula la de una receta**, y el plan da `comensales` y `version`
  *** -> y por tanto lo que falta es LA SUMA SOBRE EL PLAN, y SU COBERTURA. *** *

*** LO QUE NO SE DECLARA: ***
  *** no se declara «no existe» *** -- *porque **B02 enseño que esa frase se cae**: *«no existe nada» (con el WAF
  ahi), «y nada mas» (con `runlog` ahi). *Y aqui **se ha mirado el FRONTEND**, *y **no se ha mirado el API**
  con estos nombres: *`main.py` **podria tener una ruta de prevision** *que el frontend **no use todavia** *
  *(y **B13 ya vio que hay rutas sin usar**: *`Nav.tsx` **existe y nadie lo importa**). *
```

> *** Y **la comprobacion que lo decidiria** *** -- *y es **una**: *buscar **en `plataforma/api/`** los mismos
> nombres, *y **en `core/`**. *
>
> *** Y **hasta entonces**: *** *** **la ausencia esta medida en el frontend, y el API queda por mirar por esta
> via** *** -- *que es **mas de lo que B08 tenia**, *y **menos que «no existe».** *
