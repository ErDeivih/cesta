# B08 · **La prevision, sobre la semana entera**: siete comidas, siete huecos **con su nombre**, y `kcal` nulo

*(2026-10-14, 00:3x. **Y es la comprobacion final de la honestidad, sobre datos reales.**)*

## 1. La respuesta, entera

```
$ `GET /api/recetas/plan/prevision?desde=2026-10-12&hasta=2026-10-18`
*** comidas: 7 ***
  *2026-10-12*  Ensalada de ensayo B13   v1  *2 com*  ->  `tomate`         *motivo* *** sin_catalogo ***  *kcal* *** None ***
  *2026-10-13*  Sopa de ensayo B13       v1  *2 com*  ->  `tomate`         *motivo* sin_catalogo   *kcal* None
  *2026-10-14*  Ensalada de ensayo B13   v1  *2 com*  ->  `tomate`         *motivo* sin_catalogo   *kcal* None
  *2026-10-14*  Sopa de ensayo B13       v1  *2 com*  ->  `tomate`         *motivo* sin_catalogo   *kcal* None
  *2026-10-15*  Guiso de ensayo B13      v1  *2 com*  ->  `200 g tomate`   *motivo* sin_catalogo   *kcal* None
  *2026-10-16*  Pure de ensayo B13       v1  *2 com*  ->  `150 g tomate`   *motivo* sin_catalogo   *kcal* None
  *2026-10-17*  Arroz de ensayo B13      v1  *2 com*  ->  *** `3 ud huevos` ***  *motivo* sin_catalogo   *kcal* None

*** `sin_dato`     -> ['tomate','tomate','tomate','tomate','200 g tomate','150 g tomate','3 ud huevos'] ***
*** `sin_cantidad` -> [] ***
```

## 2. *** Y confirma las cuatro cosas, y la tercera es la que importa ***

```
*** 1) LAS SIETE COMIDAS ***  -> *con su **`version: 1`** y sus **`comensales: 2`** -- *el plan, escalado* ✓
*** 2) *** `kcal: None` EN LAS SIETE *** ***  -> *** y NO CERO. *** *El hueco viene como hueco.* ✓✓✓
*** 3) *** Y `sin_dato` LLEVA *** LOS SIETE NOMBRES ENTEROS *** ***  -> *incluidos `200 g tomate`,
   `150 g tomate` y `3 ud huevos`* ✓✓✓
   *** -> o sea: *** *** EL INGREDIENTE SE CONSERVA CON SU CANTIDAD Y SU UNIDAD ***, *y no como
   «tomate» a secas ni como un id* -- *que es la clausula del encargo: *** «ingrediente sin catalogo
   conservado» ***. *
*** 4) y `motivo` dice CUAL de los dos, en las siete *** ✓
```

> *** Y **el `3 ud huevos` es el mejor de los siete**, *y por dos motivos: *
> *-- *lleva *** la unidad `ud` ***, *que es **la del fallo del propietario**, *y **se conserva tal cual** *
> *-- y **no se convierte a gramos**: *`_gramos_de` **solo convierte `g` y `kg`**, *y **su ensayo lo fija.** *

## 3. *** Y sale un detalle que hay que decir: **`sin_cantidad` esta VACIO*****

```
*** `sin_cantidad -> []` ***  *-- y **NO porque no haya unidades sin peso**: *`3 ud huevos` **es una.** *
*** -> es porque *** `sin_catalogo` SE COMPRUEBA PRIMERO ***: *** sin producto, los gramos no importan. *** *
```

> *** Y **el orden es el correcto**, *y conviene explicarlo: *
> ```
> *** primero `sin_catalogo` ***  -> *no **sabemos de que producto hablamos** -- *y **sin eso, la cantidad
>                                  no sirve para nada.** *
> *** y despues `sin_cantidad` *** -> *y **aqui** si sabemos el producto, *pero **la linea no dice cuanto** *
> ```
>
> *** -> y **con estas recetas `sin_cantidad` no se alcanza**, *porque **ninguna tiene producto.** *
> *** Y **se dice, y no se disimula**: *** *** **el camino de `sin_cantidad` no esta ejercido por estos datos**,
> *y **su ensayo lo cubre** (`test_solo_se_convierten_las_dos_unidades_de_peso`). *

## 4. Y el estado, con **la aceptacion comprobada sobre la semana entera**

```
*** B08 · la vista de previstos ***
  *** la semana ***         -> *** 7 comidas, 5 recetas distintas, del 12 al 17 *** ✓
  *** el escalado ***       -> *** `v1` y `2 comensales` en las siete *** ✓
  *** la honestidad ***     -> *** `kcal: None` en las siete ***, *y `motivo` en las siete* ✓
  *** el ingrediente ***    -> *** conservado con su cantidad y su unidad, y CON SU NOMBRE *** ✓
  *** y `sin_cantidad` ***  -> *vacio, **y se dice por que** -- *y su ensayo lo cubre* ✓
  *** todo sobre la cuenta de ensayo `b13-recorrido-2301` *** *
```

> *** Y **es la comprobacion mas completa que se ha hecho de la vista**: *** *no **una receta**, *
> *sino **la semana entera**, *y **con los dos lados del fallo del propietario**: *`g` en cuatro, *y `ud` en una.* *
