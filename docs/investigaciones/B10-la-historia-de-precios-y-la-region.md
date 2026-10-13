# B10 · **La historia de precios**: 38 dias, **1.643.898 filas**, y **`region` es una columna**

*(2026-10-14, ~01:40. **Y `region` es exactamente lo que el propietario pidio para Lidl.**)*

## 1. Lo que hay, literal

```
*** `data/gold/v20261013-155356/precio_diario.parquet` ***  *-- 20,5 MB*
*** COLUMNAS: ***
  `fuente` · `id_fuente` · *** `precio_cent` *** · *** `precio_unidad_cent` *** · *** `unidad_canon` *** ·
  *** `region` *** · *** `fecha` *** · `producto_id`

*** Y EL RANGO: *** *** 2026-09-06 *** a *** 2026-10-13 *** *
*** 38 DIAS DISTINTOS *** · *** 1.643.898 FILAS *** *
```

> *** Y **`1.643.898 / 38` son unas 43.250 filas por dia** *** *-- *y **encaja con los 51.725 productos
> observados**: *no **todos** los productos se ven **todos** los dias, *y **eso es lo que la cobertura dice.** *
>
> *** Y **las tres columnas que hacen posible comparar** *** *estan: *
> ```
> *** `precio_cent` ***         -> *el precio*
> *** `precio_unidad_cent` ***  -> *** y el precio POR UNIDAD ***, *que es **el unico comparable** *
> *** `unidad_canon` ***        -> *** y la unidad canonica ***, *para saber **si dos precios se pueden comparar** *
> ```

## 2. *** Y `region` es la respuesta a lo que el propietario pidio ***

> *** El propietario dijo: *** *** «que dependa de *** LA REGION *** que elija el usuario, o en la UE se
> encuentre en ese momento. *** Verifica si esto le pasa a mas supermercados so solo a lidl para mejorar la
> experiencia del usuario» *** *
>
> *** Y **la columna `region` YA ESTA en la historia de precios** *** *-- *o sea: **el dato no hay que
> inventarlo: **hay un sitio donde vive la region de cada observacion.** *
>
> *** Y **lo que NO se ha comprobado todavia**, y se dice: *** *** **que valores toma `region`** -- *
> *si esta vacia, si es una sola, o si de verdad separa. *-- *y **eso es UNA consulta, y la siguiente.** *

## 3. *** Y los 38 dias, que es el dato que sostiene toda comparacion ***

```
*** 38 dias *** *-- *del **6 de septiembre al 13 de octubre de 2026.** *
  *** -> y son los que hacen posible: ***
     *** «una bajada de verdad sale» ***        *-- *hacen falta **dos fechas**, *y hay 38*
     *** «el ruido de redondeo no es una bajada» *** *-- *y **una serie** para distinguirlo*
     *** «una oferta que no baja el precio se denuncia» *** *-- *y **`promo_txt`** al lado (`grupos.parquet`)*
     *** y las promociones: *** *mediana **5-8 dias**, p90 **10-15** (`promos_por_cadena.parquet`)*
  *** -> o sea: LA VENTANA ES SUFICIENTE para lo que el sistema afirma. *** *
```

> *** Y **no se declara «38 dias bastan»** *** *como juicio: *se declara **que hay 38**, *y **que las
> duraciones medidas (5-8 de mediana) caben dentro.** *
>
> *** Y **el `precio_derivado.parquet` (1.643.898 filas)** *** *-- *o sea: **las mismas filas que
> `precio_diario`**, *y **con lo derivado** *-- *y **su tamano (7 MB frente a 20,5) dice que deriva del diario
> sin anadir filas.** *

## 4. Y el estado, con **la base de los precios medida**

```
*** B10 · «compra profesional para familias» ***
  *** cuanta historia ***  -> *** 38 dias *** (2026-09-06 a 2026-10-13)
  *** cuantas filas ***     -> *** 1.643.898 *** en `precio_diario`, *y otras **1.643.898** en `precio_derivado`*
  *** y con que ***         -> *** `precio_cent` · `precio_unidad_cent` · `unidad_canon` · `region` · `fecha` *** *
  *** y las promociones *** -> *8.884 observadas, *con **mediana 5-8 dias y p90 10-15**, *por cadena*
  *** -> y **la region ya esta en el dato**, *que es **lo que el propietario pidio.** *
  *** -> y **queda UNA consulta**: *que valores toma `region`.* *
```

> *** Y **esto cierra el circulo del propietario sobre Lidl**: *** *pidio **que dependa de la region**, *
> *y **se puede decir que el sitio existe** -- *y **si esta poblado o vacio, es lo siguiente que hay que
> mirar.** *
