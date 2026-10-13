# B13 · **CORRECCION: el catalogo del contenedor NO esta vacio** -- lo que no tiene es «tomate»

*(13 de octubre de 2026. **Y es la duodecima correccion, y es a mis propias palabras.**)*

## 1. Lo que yo escribi, y lo que hay

> *** Lo que yo escribi (rondas 244 y 251): ***
> > *** «el catalogo del contenedor **esta vacio**» ***
> > *** «y **NO se rellena** para que la prueba salga bonita» ***
>
> *** Y **lo que hay, medido hoy**: ***
> ```
> $ docker exec cesta-api-1 sh -c 'ls /datos/'
>   bronze · *** gold *** · cobertura · cookies · copias · avisos.json · ...

> $ *** `GET /api/buscar?q=leche` -> 200 ***
>   {"fecha_datos":"2026-10-13","resultados":[
>     {"*** grupo_id ***":10645,"nombre":"*** Leche semidesnatada Simpl 1 l. ***","marca":"*** SIMPL ***",
>      "*** cadena_mas_barata ***":"*** carrefour ***","*** precio_cent ***":*** 81 ***,
>      "*** precio_unidad_cent ***":*** 81.0 ***, ...}]}
> ```

> *** O sea: *** *** **el catalogo ESTA, y tiene productos, y con precio y cadena.** *
>
> *** Y **mi frase era falsa**, *y **la causa del fallo era otra**: *** *** el catalogo **no tiene «tomate»** --
> *no **esta vacio.** *
>
> *** Y **`/datos/gold` es el que lo da**, *y esta montado **`ro`** *-- *o sea: **la API lo lee, y el pipeline
> del host lo escribe.** *Y **por eso `/datos` es `ro`: la API no lo toca.** *

## 2. Y por que me equivoque, que es lo util

```
*** LO QUE VI: ***  `entrarian: []`  y  `sin_catalogo: ["tomate"]`  (la previa del plan, ronda 244)
*** Y LO QUE CONCLUI: ***  «el catalogo esta vacio»
*** Y LO QUE PASABA: ***  *** el catalogo no tiene `tomate` *** -- *y **`sin_catalogo` dice exactamente eso:
   LA LINEA, no EL CATALOGO.** *
```

> *** Y **es un error de lectura de un campo, y del mismo tipo que los de B02**: *** *** `sin_catalogo: ["tomate"]`
> significa **«esta linea no tiene producto»**, *y **yo lo lei como «no hay catalogo».** *
>
> *** Y **el campo lo decia bien**: *** *`sin_catalogo` **es una lista de nombres de linea**, *y **`entrarian: []`
> es **la consecuencia** *-- *y **las dos juntas significan**: *«**tomate** no tiene producto, y por eso no entra»,
> *y **no** «no hay catalogo». *
>
> *** Y **la leccion es la de siempre**: *** *** un campo **se lee por lo que significa**, *y no **por lo que
> parece** *-- *y **cuando un resultado me extrana, hay que mirar el campo, no el conjunto.** *

## 3. Y **lo que esto cambia para la prevision**, que es lo importante

```
*** ANTES (mi lectura equivocada): ***  «la prevision sera casi siempre `sin_dato` porque el catalogo esta vacio»
*** AHORA (medido): ***  *** el catalogo tiene productos *** -- *y **`leche` esta, con `precio_cent: 81` y
   `cadena_mas_barata: carrefour`** *
   *** -> o sea: **UNA RECETA CON `leche` SI TENDRIA NUTRICION** *** -- *si el ingrediente **resuelve a un
   `producto_id` del catalogo.** *
   *** -> y **el problema no es el catalogo: es EL ENLACE** *** -- *`ingrediente -> producto_id`, *que es
   **donde `tomate` se queda.** *
```

> *** O sea: *** *** **la prevision SI se puede probar, y con datos de verdad** *** -- *porque **el catalogo tiene
> 37.019 productos** (B02: *«de sus 37.019 productos, solo el 33 % era comida»*). *
>
> *** Y **lo que falta no es un catalogo: es **el enlace del ingrediente con el catalogo** *** -- *que es
> **el paso 3** de la ronda 262, *y **el unico que se resiste.** *
>
> *** Y **eso hace la prevision mas prometedora, no menos**: *** *** con **un ingrediente que resuelva**
> (leche, o el tomate escrito **como lo escribe una cadena**), *la suma **tiene de donde salir** *-- *
> *y **con uno que no**, *entra en `sin_dato` **con su nombre.** *

## 4. Y la correccion, con su numero

```
*** RONDA 244: ***  «el catalogo del contenedor esta vacio»
*** RONDA 263: ***  *** FALSO: `GET /api/buscar?q=leche` da 200 con productos, precio y cadena *** *
   *** y lo que pasa es que `sin_catalogo: ["tomate"]` nombra LA LINEA, no el catalogo. *** *
```

> *** Y **DUODECIMA correccion** *** -- *y **la primera que es sobre una lectura de un campo**, *y no sobre una
> ausencia. *
>
> *** Y **no cambia nada de lo demas**: *la restriccion sigue contestada, *la aceptacion sigue completa, *y
> `anadidos: 0` con `sin_catalogo: ["tomate"]` **sigue siendo lo correcto** -- *porque **el tomate, en efecto,
> no tiene producto.** *
