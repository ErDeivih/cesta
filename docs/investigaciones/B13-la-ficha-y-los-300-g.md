# B13 · **`300 g tomate` se guarda como `300 g tomate`** -- y no como una unidad

*(13 de octubre de 2026. **Y la ficha de la receta lo enseña, con su version y sus raciones.**)*

## 1. La ficha, abierta

```
`click` *** rol button, nombre «Ensalada de ensayo B13» ***  *237 ms*  -- *y la ficha se despliega **dentro de la lista***

  *** heading «Ensalada de ensayo B13» [level=2] ***
  button «*** Cerrar ***»
  *** text «Version»  ·  combobox «Version»: option «*** 1 (ultima) ***» [selected] ***
  *** text «2 raciones» ***
  *** list: ***
    *** listitem: «300 g tomate» ***
```

> *** O sea: *** *** **el ingrediente esta guardado como `300 g tomate`** *** -- *con **su cantidad y su unidad.**
> *
>
> *** Y **NO como «1 unidad»** *** -- *que es **la primera mitad del fallo que el propietario describio**:
> *«**300 g necesarios terminan como una unidad**». *
>
> *** *** Y ESO ES UN DATO MEDIDO, Y HAY QUE DECIR SU ALCANCE: *** *** *lo que se ha medido es **que la receta lo
> guarda bien.** *Y **lo que el propietario vio** pasa **al traspasarlo a la lista** -- *que es **donde hay
> consolidacion por identidad y unidad.** *
>
> *** O sea: **este paso esta bien, y el siguiente es el que se prueba.** *

## 2. Y el `combobox «Version»` con `«1 (ultima)»` es **el versionado, en vivo**

```
*** combobox «Version»:  option «1 (ultima)» [selected] ***
```

> *** Y **es un `combobox`, no un texto** *** -- *o sea: **se puede cambiar de version**, *y **la ficha
> reconstruiria con la que se elija.** *
>
> *** Y **el texto de la opcion es `«1 (ultima)»`** *** -- *y **las dos partes dicen cosas distintas**: *
> `1` es **el numero**, *y `(ultima)` es **el aviso de cual es la vigente.** *
>
> *** Y **es la doctrina en un `option`**: *** *** no dice **«v1»** a secas *-- *dice **que es la ultima**, *porque
> **una receta puede tener varias, y hay que saber cual se esta mirando.** *
>
> *** Y **B13 midio que `version` tiene 43 filas para 42 recetas** *** -- *o sea: **una receta tiene dos versiones.**
> *Asi que **el `combobox` no es decorativo: tiene casos.** *

## 3. Y **el boton del puente NO se ve todavia**, y hay que decirlo

```
*** LO QUE HAY EN LA FICHA: *** *heading · «Cerrar» · el `combobox` de version · «2 raciones» · la lista de ingredientes*
*** LO QUE NO SE VE: *** *** el boton de «a la lista» ***  ⚠️
```

> *** Y **no se concluye que no exista** *** -- *hay **tres explicaciones, y ninguna se elige**: *
> ```
> a) esta **mas abajo**, y la captura de accesibilidad **no lo alcanza** *-- *pero **no**: la accesibilidad
>    **no depende del scroll** *
> b) *** hay que abrir la RECETA ENTERA ***, *y esto es **solo la ficha desplegada de la lista** *
> c) *** el puente vive en `/recetas/plan` *** *-- *o sea: **en el PLAN SEMANAL**, *y **no en la receta.** *
> ```
>
> *** Y **la (c) tiene un apoyo fuerte**: *** *** el encargo dice «los DOS puentes: **receta→lista** y
> **plan→lista**» *** -- *o sea: **hay un puente por receta Y otro por plan**, *y **B13 ya sabe que `/recetas/plan`
> existe** (esta en el menu: *`link «Plan semanal» -> /recetas/plan`). *
>
> *** Y **`main.py:1466` lo dice tambien**: *** *«la vista previa: **que ingredientes del plan entrarian en la
> lista**» -- *o sea: **la previa es DEL PLAN.** *
>
> *** *** Y por tanto el puente de RECETA tambien tiene que estar, y esta en `recetas.py:199` (`/{receta_id}/a-la-lista`). ***
> *Asi que **el boton existe, y esta en algun sitio de la ficha que no se ha capturado.** *

## 4. Y el estado, con una mitad de la restriccion **medida y bien**

```
RECORRIDO 5 · *** tu restriccion ***
  *** 1a MITAD · «300 g terminan como una unidad» ***  -> *** NO en la receta: guarda `300 g tomate` ***
  *** 2a MITAD · «y una nota de 100 g» ***              -> *y **el puente** es donde hay que mirarlo*
  *** y las dos recetas estan, con sus numeros, y con `2 raciones` cada una. ***
```

> *** Y **la ficha trae tres cosas que el encargo pide, todas juntas**: ***
> ```
> *** `300 g tomate` ***  -> *la cantidad **con su unidad** (y no «1 ud»)*
> *** `combobox «Version»: «1 (ultima)»` ***  -> *y **la version**, que el encargo pide para el diario:
>    «el diario solo registra las porciones confirmadas... **con receta/version/snapshot** y cobertura»*
> *** `2 raciones` ***  -> *y **las raciones**, que son **lo que el puente escala por comensales.** *
> ```
>
> *** O sea: **la ficha de una receta tiene exactamente los tres datos que los dos puentes necesitan** *** --
> *y **los tres estan visibles.** *
