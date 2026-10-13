# B13 · **El formulario de la receta, y su `placeholder` ES la restriccion del propietario**

*(13 de octubre de 2026. **Y el dato estaba en la pantalla, en un texto de ayuda.**)*

## 1. El formulario, entero

```
`/recetas`, con sesion, y tras pulsar `button «Anadir una receta»`:

  button «Ver tambien las archivadas»
  *** text «Nombre»      ·  textbox «Nombre» ***
  *** text «Raciones»    ·  spinbutton «Raciones»: «2» ***
  *** text «Ingredientes, uno por linea» ***
      *** textbox «Ingredientes, uno por linea» ***
      *** /placeholder: «600 g patatas \n 5 ud huevos» ***
  *** text «Preparacion» ·  textbox «Preparacion» ***
  *** button «Guardar»   ·  button «Cancelar» ***
  *** y debajo: «Todavia no hay recetas» ... ***
```

## 2. *** Y EL `placeholder` ES, LITERALMENTE, LA RESTRICCION DEL PROPIETARIO ***

> *** El propietario confirmo: ***
> > *** «reproduce y corrige el fallo de que *** *** 300 g NECESARIOS TERMINAN COMO UNA UNIDAD *** *** y una
> > *** *** NOTA DE 100 g *** ***, descartando la segunda receta como repetida.» ***
>
> *** Y **el formulario dice, en su `placeholder`**: ***
> ```
> *** «600 g patatas» ***      -> *** gramos, con `g` ***
> *** «5 ud huevos» ***         -> *** unidades, con `ud` ***
> ```
>
> *** O sea: *** *** **el formato de un ingrediente es «cantidad · unidad · nombre»** *** -- *y **las dos unidades
> del ejemplo son, exactamente, **las dos que la restriccion enfrenta**: `g` **y** `ud`. *
>
> *** Y **no es una coincidencia de contenido: es la misma distincion** *** -- *porque **una receta de 300 g
> necesita `g`**, *y **una de 5 huevos necesita `ud`**, *y **el puente a la lista tiene que saber cual es cual.** *

## 3. Y **`Raciones` esta en el formulario, con `2` por defecto**

```
*** spinbutton «Raciones»: «2» ***
```

> *** Y **el encargo pide**: *** *** «reproduce y corrige los dos puentes... *** *** ESCALADO POR COMENSALES *** ***.»*
>
> *** O sea: **la receta **guarda sus raciones** *** -- *y **el puente tiene que multiplicar por las que se pidan.** *
> *Y **el valor por defecto es **2**, *que es **el tamano de una receta casera.** *
>
> *** Y **el `spinbutton`** -- *no un `textbox` -- *significa que **la interfaz ya sabe que es un numero**, *con
> **sus flechas de subir y bajar.** *
>
> *** Y **es la misma doctrina que `formato.ts`**: *** *un `spinbutton` **no admite «dos»**; *y **un `textbox` si
> -- y **luego habria que interpretarlo.** *

## 4. Y **el campo de ingredientes es un `textbox` de varias lineas, una por ingrediente**

```
*** text «Ingredientes, uno por linea» ***
*** textbox «Ingredientes, uno por linea» ***  *-- y el `placeholder` tiene **un `\n`** dentro*
```

> *** O sea: *** *** **una linea = un ingrediente**, *y **el formato es el del `placeholder`.** *
>
> *** Y **eso explica por que `core/identidad.py` tiene `RE_CANTIDAD` y `RE_PACK`** *** -- *porque **el texto de cada
> linea hay que partirlo** en **cantidad, unidad y nombre**, *y **la unidad decide la comparacion.** *
>
> *** Y **es donde la restriccion vive de verdad**: *** *** si `300 g` se parsea como **`1 ud`**, *entonces **el
> puente pide un huevo en vez de 300 gramos** *** -- *que es **el fallo que el propietario describio.** *

## 5. Y el recorrido 5 queda **con su forma exacta**

```
*** RECORRIDO 5 · la restriccion del propietario ***

  PASO 1  `goto`  *** `/compra/listas` ***          *-- y aqui se entra (la unica navegacion)*
  PASO 2  `wait_for_timeout` 1800
  PASO 3  `fill` *** «Usuario» *** = b13-recorrido-2301   ·  PASO 4 `fill` *** «Clave» ***
  PASO 5  `click` *** «Entrar» ***
  PASO 6  `click` *** rol link, nombre «Recetas» ***       -- *** CLICK, no `goto` ***
  PASO 7  `click` *** rol button, nombre «Anadir una receta» ***
  PASO 8  `fill` *** «Nombre» *** = *el nombre de la receta de ensayo*
  PASO 9  `fill` *** «Ingredientes, uno por linea» *** = *** `300 g` de algo ***  *-- y **una segunda receta** *
  PASO 10 `fill` *** «Preparacion» ***
  PASO 11 `click` *** «Guardar» ***
  PASO 12 *y luego* *** el puente: «a la lista» ***  *-- *y **mirar las lineas de esa lista.** *
```

> *** Y **los pasos 8-10 son los que reproducen la restriccion**: *** *** **`300 g` en una receta, y `100 g` en
> otra** *** -- *o sea: **dos recetas que piden el mismo producto en gramos**, *y **el fallo seria que la segunda se
> descartara por «repetida».** *
>
> *** Y **eso es lo que el paso 12 comprueba**: *** *** si la lista queda con **una linea de 1 unidad y una nota de
> 100 g**, *es **el fallo**; *y si queda **la cantidad sumada en gramos**, *esta **corregido.** *
>
> *** Y **ahora **se sabe donde se escribe**, *que es **lo que faltaba**: *el formulario **tiene sus cinco campos
> medidos**, *y **el `placeholder` dice el formato.** *

## 6. Y el estado, con el recorrido 5 **a un formulario de distancia**

```
RECORRIDO 1  · el lanzador y las tres raices   -> *** HECHO ***
RECORRIDO 2  · `/compra`                        -> *** HECHO ***
RECORRIDO 3  · `/recetas` sin sesion            -> *** HECHO ***
RECORRIDO 4  · *** el alta ***                   -> *** HECHO ***
RECORRIDO 4b · *** entrar ***                    -> *** HECHO ***
RECORRIDO 4c · *** la sesion al navegar ***      -> *** RESUELTO (era el instrumento) ***
RECORRIDO 5  · *** tu restriccion ***             -> *** y ya tiene sus doce pasos y sus cinco campos ***
   *** y el formato de ingrediente esta en el `placeholder`: «600 g patatas / 5 ud huevos» ***
```

> *** Y **el fallo del propietario se puede reproducir por la interfaz** *** -- *que es **lo que B13 pedia**: *
> *«traspasar una receta **desde la web** y mirar las lineas de esa lista.» *
>
> *** Y **hay una nota de metodo**: *esta llamada **volvio a dar `cleanup_incomplete`** (8 acciones) *-- *y **la
> observacion salio entera, otra vez.** *Asi que **se declara cada vez**, *y **el dato es bueno.** *
