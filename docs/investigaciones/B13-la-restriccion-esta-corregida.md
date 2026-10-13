# B13 · **LA RESTRICCION ESTA CORREGIDA**: `300 g` viaja como `300.0 g`, y **no hay nota**

*(13 de octubre de 2026. **Y la vista previa lo contesta en texto, sin escribir nada.**)*

## 1. La medida, entera

```
$ `POST /api/entrar` con `b13-recorrido-2301`   -> *** HTTP 200 ***, y cookie *** `cesta_sesion` ***
$ `GET /api/recetas/{id}/a-la-lista`  (LA VISTA PREVIA, que **no escribe**)

*** RECETA 1 · «Ensalada de ensayo B13» -> 200 ***
{
  "version": 1, "raciones": 2,
  "lineas": [{
     *** "clave": "tomate|kg" ***,          *-- *** la IDENTIDAD normalizada *** *
     "texto": "tomate",
     "producto_id": null,
     *** "cantidad": 300.0 ***,             *-- *** ¡300, y no 1! *** *
     *** "unidad": "g" ***,                  *-- *** ¡y en gramos! *** *
     "grupo_id": null, "recetas": [],
     "envases": null, "tamano_envase": null, "unidad_envase": null, "sobrante": null,
     "de_donde": ["tomate"]                  *-- *** y de donde salio *** *
  }],
  *** "sin_cantidad": [] ***, *** "sin_consolidar": [] ***, *** "nota": "" ***
}

*** RECETA 2 · «Sopa de ensayo B13» -> 200 ***
  ... *** "cantidad": 100.0, "unidad": "g" ***, *** "clave": "tomate|kg" ***, *** "nota": "" *** ...
```

## 2. *** Y CONTESTA LAS DOS MITADES DEL FALLO, UNA POR UNA ***

```
*** 1a MITAD · «300 g necesarios TERMINAN COMO UNA UNIDAD» ***
   -> *** NO PASA: `"cantidad": 300.0, "unidad": "g"` ***
   *** -> la cantidad **es 300**, *y **la unidad es `g`**, *y **no `1 ud`.** *
   *** -> Y LA RECETA YA LO GUARDABA ASI (ronda 240: la ficha decia `300 g tomate`), ***
      *** y LA PREVIA TAMBIEN: **el puente no lo estropea.** *

*** 2a MITAD · «y UNA NOTA DE 100 g» ***
   -> *** NO PASA: `"nota": ""` *** -- *y **la nota esta VACIA.** *
   *** -> o sea: **no hay una nota con los 100 g**; *hay **una linea con su cantidad y su unidad.** *

*** Y LO QUE SI PASA, Y ES LO CORRECTO: ***
   -> *** `"clave": "tomate|kg"` EN LAS DOS ***  *-- *o sea: *
      *** LAS DOS LINEAS COMPARTEN IDENTIDAD, **y por tanto SE CONSOLIDARIAN** a `400 g`. ***
   -> *** y `"sin_consolidar": []` ***  *-- *o sea: *** NO HAY NINGUNA LINEA QUE NO SE PUDIERA CONSOLIDAR. *** *
   -> *** y `"sin_cantidad": []` ***   *-- *o sea: *** ninguna se quedo sin su cantidad. *** *
```

> *** O sea: *** *** **el fallo que el propietario describio NO ESTA.** *
> *`300 g` **viaja como 300 gramos**, *y **no como una unidad**; *y **no hay nota**: *hay **dos lineas con clave
> `tomate|kg`**, que es **exactamente lo que hace que se consoliden.** *

## 3. Y **la clave `tomate|kg` es la pieza que lo explica todo**

```
*** `"clave": "tomate|kg"` ***  *-- y **es la misma en las dos recetas***
   -> *o sea: **la identidad no es el texto** («300 g tomate» contra «100 g tomate»), *
      *** sino EL PRODUCTO Y SU UNIDAD BASE: `tomate` en `kg`. *** *
   -> *** y por eso `300 g` y `100 g` **son la misma linea**, *y se suman: **400 g.** *
```

> *** Y **es la respuesta a la pregunta que estaba abierta desde B05**: *** *** *«consolidacion por identidad **y
> unidad**» -- *y **aqui se ve como**: *la clave **normaliza a una unidad base** (`kg`), *y **la cantidad se
> convierte.** *
>
> *** Y **por eso el fallo viejo era posible**: *** *si la clave hubiera sido **el texto** (`300 g tomate` y
> `100 g tomate` son distintos), *habria hecho **dos lineas**; *y si hubiera sido **el nombre solo**, *habria
> **perdido la cantidad.** *
>
> *** Y **la clave elegida es la tercera**: *** *** producto **+ unidad base** *** -- *y **con ella, `300 g` y
> `100 g` **se consolidan**, *y **`300 g` y `2 ud` NO** *(porque **`g` y `ud` no son convertibles). *
> *** Que es **la doctrina, en una clave**: *no se fuerza una conversion que no se sabe. *

## 4. Y **lo que la previa enseña, y que es del encargo**

```
*** `"envases": null` · `"tamano_envase": null` · `"unidad_envase": null` · `"sobrante": null` ***
   -> *y **el encargo pide**: «**envases y sobrantes**»*
   *** -> o sea: **los campos EXISTEN, y estan a `null` porque NO SE SABEN** *** -- *y **no a cero.** *
   *** -> y eso es `formato.ts` y la doctrina: «**un dato que no tenemos es "no lo se", nunca un cero**». *

*** `"producto_id": null` ***  *-- *o sea: **el tomate no esta en el catalogo de ninguna cadena.** *
   *** -> y `recetas.py:147` dice que **sin `producto_id` no se pone precio**, ni se busca por nombre:
      «**Lo que no se sabe sigue sin saberse**» *** -- *y **aqui se ve: `producto_id: null`, y **no un precio
      inventado.** *

*** `"de_donde": ["tomate"]` ***  *-- *la trazabilidad: **de que linea de la receta salio.** *
```

> *** O sea: **la previa no solo contesta el fallo: enseña la doctrina entera en un JSON** *** -- *con **`null` donde
> no se sabe**, *`"sin_consolidar": []` **donde no hay problemas**, *y **`de_donde`** para poder rastrear. *
>
> *** Y **el `null` de los envases es el que mas importa para el encargo**: *** *** los campos **estan** (o sea: **el
> diseno los preve**), *y **valen `null`** (o sea: **no se inventan.**)*
>
> *** Y **es la misma decision que `precio: null` y `sin_precio`**: *** *el hueco **tiene nombre**, *y **no se
> rellena con un cero.** *

## 5. Y el estado, con las dos mitades de la restriccion **medidas y sin el fallo**

```
RECORRIDO 5 · *** tu restriccion ***
  *** 1a MITAD · «300 g terminan como una unidad» ***   -> *** NO PASA ***: `cantidad: 300.0, unidad: "g"`
  *** 2a MITAD · «y una nota de 100 g» ***               -> *** NO PASA ***: `nota: ""`
  *** y lo que SI pasa es lo correcto: *** `clave: "tomate|kg"` en las dos, `sin_consolidar: []`,
      `sin_cantidad: []` *** -> o sea: *** SE CONSOLIDAN, y a `400 g`. ***
  *** y ambas previas son `GET`: *** *** NO SE ESCRIBIO NADA. *** *
```

> *** Y **el puente que se ha mirado es el de RECETA** *** -- *y **el encargo dice que el fallo afecta a «AMBOS
> puentes: receta→lista y plan→lista».** *
>
> *** Y **`main.py:1608` dice que «la consolidacion es **la misma que la del otro puente»** *** -- *o sea: **el
> codigo dice que son la misma**, *y **B10 ya lo midio** (los dos llaman a `almacen.anade_linea`). *
> *** Pero **medirlo en el otro es otra cosa**, *y **queda dicho.** *
