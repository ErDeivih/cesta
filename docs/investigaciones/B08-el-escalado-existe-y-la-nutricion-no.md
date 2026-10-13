# B08 · **Dos cosas de `core/recetas.py`**: el escalado **existe con sus dos cifras**, y **la nutricion no esta**

*(13 de octubre de 2026. **Y la primera es una pieza del encargo; la segunda, la que falta para la prevision.**)*

## 1. *** El escalado por comensales **YA EXISTE**, y con la forma correcta ***

```python
# core/recetas.py
l39   raciones INTEGER NOT NULL
l134  *** def escala(ingredientes: list[dict], de_raciones: int, a_raciones: int) -> list[dict]: ***
l135      """Los ingredientes para `a_raciones` en vez de para `de_raciones`. [...]
l144      if de_raciones < 1 or a_raciones < 1: raise ValueError("las raciones son al menos una")
l146      *** factor = a_raciones / de_raciones ***
l173      # *** **Las dos cifras.** *** Si se piden otras raciones, se devuelven los ingredientes escalados
          # y *** las dos *** [cifras]
l181      "raciones": pedidas,  "*** raciones_receta ***": fila["raciones"],
l182      "*** escalada ***": pedidas != fila["raciones"],
```

> *** O sea: ***
> ```
> *** `escala(...)` ***            -> *** y el factor es `a_raciones / de_raciones` *** *
> *** `raciones` ***                -> *las **pedidas** *
> *** `raciones_receta` ***         -> *** y las **que la receta declara** *** -- *** «las dos cifras» *** *
> *** `escalada` ***                -> *** y un booleano que dice si se escalo *** *
> *** y `ValueError` si alguna es < 1 *** -> *«las raciones son al menos una»*
> ```
>
> *** Y **es exactamente lo que el encargo pide**: *** *** «los dos puentes: *** ESCALADO POR COMENSALES ***». *
> *Y **esta hecho, en el nucleo, y con «las dos cifras»** -- *o sea: **nunca se pierde de donde salio.** *
>
> *** Y **«las dos cifras» es la misma doctrina** *** *que `Diario.tsx:3` («las dos cifras van juntas»),
> *y que `cobertura: {con_dato, total}`: *** *** no dar **un numero** sin **el contexto que lo hace legible.** *

## 2. *** Y la nutricion **no esta** en `core/recetas.py`: ni una linea ***

```
32 coincidencias de `nutricion|kcal|energia|porcion|racion`
*** y NINGUNA es `nutricion`, `kcal` ni `energia`. *** *
   -> *las 32 son de **`raciones`**, **`escala`**, **`version`** y **`propietario`** *
```

> *** O sea: *** *** **el nucleo de recetas sabe de raciones, versiones y escalado, y NO SABE NADA de nutricion.** *
>
> *** Y **es coherente con el resto**: *** *la nutricion vive **en el catalogo** (`Producto.tsx`, `tipos.ts`) *
> *y **en el diario** (`diario.ts`), *y **la receta solo tiene `raciones` e ingredientes.** *
>
> *** Y **por eso la prevision hay que construirla**: *** *** el camino es *ingrediente -> `producto_id` ->
> nutricion del producto -> escalar por cantidad y por comensales -> sumar con cobertura*, *
> *y **ese camino NO existe** -- *y **`producto_id` suele ser `null`** (el tomate, medido). *
>
> *** Y **de ahi sale la conclusion mas util**: *** *** **la prevision sera, casi siempre, `sin_dato`** --
> *porque **los ingredientes de una receta escrita a mano no tienen `producto_id`.** *
> *** Y **eso NO es un obstaculo: es el resultado** -- *y **lo que hay que hacer es DECIRLO con la cobertura**,
> *que es **lo que `desde-la-compra` ya hace.** *

## 3. Y **el estado de la prevision**, con su forma exacta

```
*** LO QUE HACE FALTA, paso a paso: ***
  1. *** las recetas del plan ***           -> *`GET /api/recetas/plan?desde=&hasta=` da `comensales` y `version`*
  2. *** y por cada una, sus ingredientes *** -> *`recetas.leer(con, propietario, rid)` los da, **escalados***
  3. *** y por cada ingrediente, su producto *** -> *** y aqui esta el hueco: `producto_id` suele ser `null` *** *
  4. *** y con producto, su nutricion ***     -> *`catalogo.producto(id)` la tiene*
  5. *** y escalar por cantidad y comensales *** -> *y `escala` **ya sabe** hacer la parte de comensales*
  6. *** y sumar CON COBERTURA ***              -> *** y el patron esta en `desde-la-compra` *** *

*** Y LOS NUMEROS DEL PLAN SON EL CRITERIO: *** *«R1=270, media=135, ausencia de energia con proteina conocida»*
```

> *** Y **el paso 3 es el que decide**, *y **no se puede saltar ni inventar**: *si **el ingrediente no tiene
> producto**, *entra en **`sin_dato`** -- *con **su nombre**, *como **`desde-la-compra`** hace.* *
>
> *** Y **`R1=270` y **`media=135`** *** *-- *y **ya se sabe de donde saldran**: *de **un ensayo con recetas que
> SI tengan `producto_id`»**, *que es **lo que hoy no hay en la base del contenedor.** *
