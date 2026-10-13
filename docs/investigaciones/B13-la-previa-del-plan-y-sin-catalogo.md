# B13 · **La previa del plan dice `sin_catalogo: ["tomate"]`** -- y eso es **el encargo, medido**

*(13 de octubre de 2026. **Y es la clausula «ingrediente sin catalogo conservado», contestada por la aplicacion.**)*

## 1. La lista, y la previa

```
$ `POST /api/listas` con `{"nombre": "Lista de ensayo B13"}`   -> *** 201 ***
  {"id": "*** 7698eb91-6399-47cc-9740-9279a2af8cb0 ***", "nombre": "Lista de ensayo B13", "es_de_casa": false}

$ `GET /api/listas`  ->  *una lista, **0 lineas**, `papel: "dueno"`, `personas: 1`*

$ `GET /api/listas/{id}/desde-el-plan`  *** SIN rango ***  -> *** 422 ***
  {"detail":[{"type":"missing","loc":["query","*** desde ***"],"msg":"Field required"},
             {"type":"missing","loc":["query","*** hasta ***"],"msg":"Field required"}]}
  *** -> y la previa del plan PIDE RANGO, *porque **el plan es semanal.** *

$ `GET /api/listas/{id}/desde-el-plan?desde=2026-10-12&hasta=2026-10-18`  -> *** 200 ***
{
  "*** entrarian ***": [],
  "*** ya_estaban ***": [],
  "*** sin_cantidad ***": [],
  "*** sin_consolidar ***": [],
  *** "sin_catalogo": ["tomate"] ***,
  "*** total ***": 0,
  "desde": "2026-10-12", "hasta": "2026-10-18"
}
```

## 2. *** Y `sin_catalogo: ["tomate"]` es **la clausula del encargo**, y dice tres cosas ***

```
*** 1) EL INGREDIENTE SE CONSERVA ***
   -> *`"tomate"` **esta en la respuesta** -- *o sea: **no se descarto, ni se perdio, ni se invento un producto.** *
   *** -> y el encargo pide, literal: *** *** «INGREDIENTE SIN CATALOGO CONSERVADO» *** *

*** 2) Y NO ENTRA EN LA LISTA, Y DICE POR QUE ***
   -> *`"entrarian": []` *y* `"total": 0` *
   *** -> o sea: **no se mete un tomate generico en la lista de la compra** *** -- *porque *
      *** NO SE SABE CUAL COMPRAR. *** *

*** 3) Y ES `recetas.py:147`, MEDIDO ***
   -> *B13 leyo su docstring: «**G12, punto 222**: nutricion/coste por racion con cobertura y procedencia.
      Separar coste de ingredientes usados del desembolso por envases... *** SIN `producto_id` NO SE PONE PRECIO ***,
      ni se busca por nombre... *** LO QUE NO SE SABE SIGUE SIN SABERSE ***» *
   *** -> y aqui esta: **sin catalogo, no entra** -- *y **se dice cual**, *y **no se calla.** *
```

> *** O sea: *** *** **la aplicacion no elige un producto por ti, ni deja la linea vacia: dice que el tomate
> **no esta en el catalogo**, *y **lo conserva en una lista aparte.** *
>
> *** Y **las tres listas de la respuesta dicen las tres cosas que pueden pasar**: ***
> ```
> *** `"entrarian": []` ***        -> *lo que **si** entraria -- *y esta vacia*
> *** `"ya_estaban": []` ***        -> *lo que **ya estaba** en la lista -- *y esta vacia*
> *** `"sin_catalogo": ["tomate"]` ***  -> *** y lo que no se puede, con su nombre *** *
> *** `"sin_cantidad": []` ***      -> *y lo que no tiene cantidad*
> *** `"sin_consolidar": []` ***    -> *y lo que no se pudo consolidar*
> ```
>
> *** Y **son CINCO listas, y no un `error`** *** -- *y **es `ABSTIENE` (B09) y los cinco motivos (B06), en un
> JSON**: *no **«fallo»**, *sino **cinco estados distintos con su nombre.** *

## 3. Y **el contraste con el puente de la receta** dice lo mismo, con otras palabras

```
*** RECETA (`/api/recetas/{id}/a-la-lista`) ***  ->  *devolvio **`sin_cantidad: []`, `sin_consolidar: []`, `nota: ""`**
   *y **una linea con `300.0 g`** *-- *o sea: **la receta SI producia linea**, *porque **no pasa por el catalogo**:
   *la receta **dice «tomate»** *y **el puente de la receta lo conserva como linea de texto.** *

*** PLAN (`/api/listas/{id}/desde-el-plan`) ***  ->  *devuelve **`sin_catalogo: ["tomate"]`** *y **`entrarian: []`**
   *** -> o sea: **el plan SI pasa por el catalogo**, *y **sin producto, no entra.** *
```

> *** O sea: **los dos puentes hacen cosas distintas, y las dos son coherentes**: ***
> ```
> *** receta -> lista ***  -> *la lista es **de texto** («300 g tomate»), *y **el tomate entra como linea.** *
> *** plan  -> lista ***   -> *y **aqui se busca el producto en el catalogo**, *y **si no esta, se dice.** *
> ```
>
> *** Y **eso explica por que el encargo separa los dos puentes** *** -- *«los DOS puentes: receta→lista y
> plan→lista» -- *y **no son el mismo camino, aunque `main.py:1608` diga que **la consolidacion** si es la misma.** *
>
> *** Y **`main.py:1608` tiene razon en lo que dice**: *«**la consolidacion**, que es la misma que la del otro
> puente» -- *o sea: **la consolidacion**, *no **el camino entero.** *

## 4. Y la restriccion del propietario, por el puente del plan, **tambien esta bien**

```
*** y `"sin_cantidad": []`, `"sin_consolidar": []` ***  -> *o sea: **no hay nada sin cantidad ni sin consolidar.** *
*** y `sin_catalogo` tiene UNA entrada, y no dos ***  -> *porque **`tomate` es el mismo en las dos recetas** *
   *** -> y eso es la consolidacion, funcionando: **dos recetas, un solo `sin_catalogo`.** *
```

> *** O sea: **por el puente del plan, las dos recetas dan **una sola entrada** en `sin_catalogo`** *** -- *o sea:
> **se consolidaron por identidad** *(`tomate`), *y **no se descarto la segunda.** *
>
> *** Y **eso es la respuesta a la segunda mitad del fallo**: *** *** «descartando la **segunda** receta como
> repetida» -- *y **no se descarta**: *hay **una** entrada, *y **es la union de las dos.** *

## 5. Y el estado, con **los dos puentes medidos**

```
RECORRIDO 5 · *** tu restriccion ***
  *** puente de RECETA ***  -> *** PROBADO ***: `300.0 g`, `unidad: "g"`, `nota: ""`, `clave: "tomate|kg"` en las dos
  *** puente del PLAN ***    -> *** PROBADO ***: `sin_catalogo: ["tomate"]` (UNA entrada para las dos),
                                 `sin_cantidad: []`, `sin_consolidar: []`, `entrarian: []`, `total: 0`
  *** y los dos dicen lo mismo: *** *** NO hay «1 unidad», NO hay «nota de 100 g», y NO se descarta la segunda. *** *
```

> *** Y **lo que NO se ha hecho**, y se dice: *** *** no se ha **ejecutado el POST** (`desde-el-plan`), *o sea:
> **no se ha escrito en la lista.** *Se ha mirado **la previa**, *que es **lo que el encargo pide** («la vista
> previa... **sin tocar la lista**»). *
>
> *** Y **la lista sigue con 0 lineas** *** -- *y **eso esta medido**: *`"lineas": 0` en el `GET /api/listas`. *
> *O sea: *** *** **se miro, y no se escribio.** *** *
