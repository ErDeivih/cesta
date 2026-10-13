# B13 · **La receta se creo**: `«Ensalada de ensayo B13»` · *** `«2 raciones · version 1»` ***

*(13 de octubre de 2026. **Y la lista de recetas enseña las dos cosas que el encargo pide: raciones y version.**)*

## 1. La llamada, y su resultado

```
`capture_browser_scenario` · *** 11 acciones · 5,4 s *** · cleanup: terminated-owned-process · complete

  1. `goto` `/compra/listas` · 2. esperar 1,8 s
  3-4. `fill` «Usuario» *30 ms* · `fill` «Clave» *10 ms*
  5. `click` «Entrar» *42 ms*
  6. *** `click` rol link «Recetas» ***  *60 ms*      -- *** CLICK, no `goto` ***
  7. `click` «Anadir una receta» *77 ms*
  8. `fill` *** «Nombre» *** = «Ensalada de ensayo B13»  *11 ms*
  9. `fill` *** «Ingredientes, uno por linea» *** = *** «300 g tomate» ***  *12 ms*
  10. `click` *** «Guardar» *** *99 ms*
  11. esperar 2,5 s  -- y capturar

*** Y EL `main` DESPUES DE GUARDAR: ***
  *** searchbox «Buscar recetas por nombre» ***        <- *y **el buscador aparece cuando hay recetas** *
  button «Ver tambien las archivadas»  ·  button «Anadir una receta»
  *** list: ***
    listitem:
      *** button «Ensalada de ensayo B13» ***
      *** text: «2 raciones · version 1» ***
      *** button «Archivar» ***
```

> *** O sea: **la receta esta guardada, y la lista la enseña.** *
>
> *** Y **`Preparacion` se dejo vacia a proposito** *** -- *y **la receta se guardo igual**: *o sea: **es opcional.** *
> *Y **eso es un dato mas**: *el formulario **exige lo que necesita** y **no mas.** *

## 2. *** Y el texto de la linea es `«2 raciones · version 1»` *** -- y son **las dos cosas del encargo**

```
*** «2 raciones» ***  -> *y **`Raciones` era un `spinbutton` con `2` por defecto** (ronda 237)*
   *** -> y el encargo pide: «los dos puentes... ESCALADO POR COMENSALES» ***
   -> *o sea: **la receta guarda sus 2 raciones**, *y **el puente tendra que multiplicar por las que se pidan.** *

*** «version 1» ***  -> *y **`core/recetas.py` tiene `versiones` (l189) y `actualizar` (l197)** *
   *** -> y B13 midio que `version` tiene 43 filas para 42 recetas: UNA RECETA TIENE DOS VERSIONES ***
   -> *o sea: **la version se ve en la lista**, *y **es la primera de esta receta.** *
```

> *** Y **las dos juntas, en una linea, con un `·` en medio** *** -- *que es **la misma forma de `«2 raciones · version 1»` que ya se vio en el codigo**: *`Cesta.tsx` **pinta la ficha de la receta con esos dos datos.** *
>
> *** Y **no hay un tercero** *** -- *ni **calorias**, *ni **coste**, *ni **tiempo**: *y **eso es el encargo**: *«no inventes calorias, densidad, alergenos, equivalencias, objetivos de salud, precios ni costes de viajes.» *
> *** O sea: **la lista dice lo que la receta sabe, y nada mas.** *

## 3. Y **el buscador aparece solo cuando hay recetas**

```
SIN recetas:   button «Ver tambien las archivadas» · button «Anadir una receta» · «Todavia no hay recetas»
CON recetas:   *** searchbox «Buscar recetas por nombre» *** · los dos botones · *** y la lista ***
```

> *** O sea: **no hay un buscador vacio sobre una lista vacia** *** -- *hay **un buscador cuando hay algo que buscar.** *
>
> *** Y **es la doctrina otra vez**: *** *** un control **que no sirve para nada** **no se pinta** -- *en vez de
> pintarlo **deshabilitado**, *o **vacio.** *
>
> *** Y **es la misma familia que `status` vacio** (ronda 219: *el buscador de `/compra` tiene un `status` **sin
> contenido**), *y que **`link «Listas No hay lista de casa...»`** (ronda 230: *el menu **dice** que no hay). *
> *** O sea: **cuando no hay nada, se dice; y cuando hay, se enseña -- y no se mezclan.** *

## 4. Y **el estado de la receta de ensayo**, que hay que decir con precision

```
*** RECETA CREADA: ***  «*** Ensalada de ensayo B13 ***»  ·  *** 2 raciones ***  ·  *** version 1 ***
*** INGREDIENTE: ***    *** «300 g tomate» ***  -- *una linea, y en el formato del `placeholder`*
*** PROPIETARIO: ***    `b13-recorrido-2301` (la cuenta de ensayo)
*** y NO se toco nada del propietario: la receta es de una cuenta nueva.** *
```

> *** Y **`«300 g tomate»` es **lo que el propietario describio**: *** *** «300 g necesarios» ***. *Asi que
> **la receta que reproduce la restriccion ya esta** -- *y **falta la segunda mitad**: *una **segunda receta** con
> **`100 g` del mismo producto**, *y **el puente a la lista.** *
>
> *** Y **el «tomate» es a proposito**: *** *es **un producto generico**, *y **el `placeholder` usa «patatas»
> -- o sea: **el proyecto ya usa nombres genericos para los ejemplos**, *y **no invento nada raro.** *
>
> *** Y **queda dicho que es una receta de ENSAYO** *** -- *con «ensayo» **en el nombre**, *que es **la convencion
> que ya hay** (`a09`, `c01b`, `f07`). *

## 5. Y los cinco recorridos, con el 5 **a dos pasos**

```
RECORRIDO 1  · el lanzador y las tres raices   -> *** HECHO ***
RECORRIDO 2  · `/compra`                        -> *** HECHO ***
RECORRIDO 3  · `/recetas` sin sesion            -> *** HECHO ***
RECORRIDO 4  · *** el alta ***                   -> *** HECHO ***
RECORRIDO 4b · *** entrar ***                    -> *** HECHO ***
RECORRIDO 4c · *** la sesion al navegar ***      -> *** RESUELTO (era el instrumento) ***
RECORRIDO 5  · *** tu restriccion ***             -> *** y ya tiene su receta: `«300 g tomate»` ***
   *** y le faltan DOS pasos: ***
     *** 1) la SEGUNDA receta con `100 g` del mismo producto ***  *-- y **B13 ya tiene el camino** *
     *** 2) el puente: «a la lista» ***  *-- *y **mirar las lineas de esa lista** *
```

> *** Y **la restriccion se reproduce con dos recetas, y no con una** *** -- *porque **el fallo era «descartar la
> SEGUNDA receta como repetida»**: *asi que **hacen falta las dos.** *
