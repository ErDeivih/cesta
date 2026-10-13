# B08 · **Las promociones, medidas**: duran **5 a 8 dias** de mediana, y hay **8.884** observadas

*(2026-10-14, ~01:20. **Y el fichero que parecia vacio era un RESUMEN.**)*

## 1. La confusion, y lo que era

```
*** LO QUE PARECIA: ***  `promos_por_cadena.parquet`  *** 0,0 MB *** *-- y parecia **vacio.** *
*** LO QUE ES: ***       *** 5 filas *** *-- *una **por cadena**, *y con **cuatro columnas**: *
  `fuente` · *** `duracion_mediana` *** · *** `duracion_p90` *** · *** `promos_observadas` *** *
```

> *** O sea: *** *** **no es un listado de promociones: es un RESUMEN por cadena**, *y **por eso pesa cero.** *
>
> *** Y **las promociones de verdad estan en `grupos.parquet`**: *** *** 5.732 productos con `promo_txt`
> no vacio.** *

## 2. *** Y las cinco filas, que son el dato ***

```
  fuente        mediana        p90   observadas
  *** alcampo        8,0       10,0 ***     *** 6.397 ***
  *** carrefour      5,0       13,0 ***     *** 1.330 ***
  *** dia            7,0       15,0 ***       *** 811 ***
  *** mercadona      8,0       14,0 ***       *** 177 ***
  *** aldi           6,0       11,0 ***       *** 169 ***
  *** y total de promociones observadas: 8.884 *** *
```

> *** Y **se puede leer, y las dos lecturas son utiles**: *
> ```
> *** alcampo ***    -> *** la mediana MAS ALTA (8) y el p90 MAS BAJO (10) ***, *y **6.397 promociones**: *
>    *o sea, *** muchas y regulares *** -- *lo que **se corresponde con su catalogo (22.828 productos).** *
> *** carrefour ***  -> *** la mediana mas baja (5) y un p90 de 13 ***: *o sea, *** cortas pero con cola *** -- *
>    *y **1.330 observadas.** *
> *** dia ***        -> *7 de mediana y **el p90 mas alto (15)**: *y **811.** *
> *** mercadona ***  -> *8 y 14, *y **177.** *
> *** aldi ***       -> *6 y 11, *y **169.** *
> *** y lidl ***     -> *** NO APARECE *** *-- *y **es coherente**: *79 productos, cero nutricion, *
>    *y **cero promociones observadas.** *
> ```

## 3. *** Y esto es lo que hace que un precio se pueda comparar sin mentir ***

> *** El encargo dice: *** *** «Permite comparar precios validos de articulos observados *** *** SIN PRESENTAR
> AUSENCIAS DE CAPTURA COMO INDISPONIBILIDAD *** ***». *
>
> *** Y **la duracion de una promocion es justo eso**: *** *si **no se sabe cuanto dura**, *una bajada
> **puede ser una promocion de tres dias** *o **el precio nuevo** -- *y **confundirlos seria atribuirle al
> catalogo algo que era temporal.** *
>
> *** Y **por eso el proyecto mide `duracion_mediana` y `duracion_p90` POR CADENA** *** -- *porque *
> *la duracion **no es la misma en Alcampo (8/10) que en Dia (7/15)**, *y **una regla unica mentiria en una
> de las dos.** *
>
> *** Y **es la misma forma de todo el proyecto**: *** *** **una media sola no vale; hacen falta la mediana,
> el p90 y cuantas se observaron.** *

## 4. Y el estado de B08, con **las promociones ya no siendo un fichero «vacio»**

```
*** B08 · «promociones y anomalias» ***
  *** cuantas ***        -> *** 8.884 promociones observadas ***, *y **5.732 productos con `promo_txt`** *
  *** cuanto duran ***   -> *** mediana 5-8 dias, y p90 10-15 ***, *por cadena*
  *** y quien ***        -> *** alcampo 6.397 · carrefour 1.330 · dia 811 · mercadona 177 · aldi 169 ***,
                            *** y lidl: ninguna observada *** *
  *** -> y el fichero que parecia vacio era un resumen, y **su contenido es el dato.** *
```

> *** Y **no se declara «las promociones funcionan»**: *** *se declara **lo que hay**: *8.884 observadas, *
> *y **su duracion medida, por cadena.** *
> *-- *y **lo que NO hay** (Lidl) *-- *tambien.* *
