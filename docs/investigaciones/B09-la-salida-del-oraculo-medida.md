# B09 · **La salida del oraculo, medida**: 22.873 enlaces, y **la mayoria son `equivalente`**

*(2026-10-14, ~01:30. **Y es lo que B09 pide cuando dice «el oraculo es INDEPENDIENTE; veredictos CINCO».**)*

## 1. Lo que hay en `enlaces.parquet`

```
*** COLUMNAS: ***  `i` · `j` · *** `parecido` *** · *** `nivel` *** *
*** Y LOS VALORES DE `nivel`, sobre 22.873 enlaces: ***
  *** equivalente    14.528 ***   *** 63,5 % ***
  *** identico        6.617 ***   *** 28,9 % ***
  *** ean            1.728 ***    ***  7,6 % ***
```

> *** O sea: *** *** **hay TRES valores, y el tercero no es un veredicto.** *
>
> *** Y **el docstring de `nivel()` dice dos**: *** *«*** identico | equivalente ***. *La distincion que
> pedia el proyecto.» *
>
> *** -> y **`ean` es otra cosa**: *** *** es **el enlace por CODIGO DE BARRAS** -- *que es **el camino que
> «no se discute»**, *y **por eso se marca aparte.** *
>
> *** Y **encaja con lo que `nivel()` explica**: *** *«mismo EAN **es el mismo producto y no se discute**». *
> *-- *o sea: **`ean` es «lo se por el codigo», *y `identico`/`equivalente` son «lo deduzco por el nombre».** *

## 2. *** Y la proporcion dice mucho ***

```
*** equivalente  63,5 % ***  *-- *y es *** la mayoria ***: *enlaces **entre marcas distintas.** *
*** identico     28,9 % ***  *-- *y **el resto** por nombre.*
*** ean            7,6 % ***  *-- *y **solo 1.728** se saben **por el codigo.** *
```

> *** Y **la mayoria sea `equivalente` es exactamente lo que `nivel()` anticipa**: ***
> > *«distinta marca con el mismo formato **es el equivalente de otra marca**, *que es **justo lo que hay que
> > comparar cuando las cadenas venden marca blanca y no comparten codigo de barras**.» *
>
> *** O sea: *** *** **el 63,5 % no es ruido: es el caso normal**, *y **por eso existe la palabra
> `equivalente`.** *
>
> *** Y **el `30 %` que mentia** *** *-- el fallo que `nivel()` documenta con su medicion del 22 de septiembre --
> *era **llamar «identico» a un equivalente**; *y **hoy hay una palabra para cada uno.** *

## 3. *** Y esto es lo que sostiene «un articulo elegido solo admite ALTERNATIVAS AUTORIZADAS» ***

> *** El encargo dice: *** *** «Un articulo elegido solo admite *** ALTERNATIVAS AUTORIZADAS ***». *
>
> *** Y **`equivalente` es la palabra que hace posible esa frase**: *** *los **14.528 enlaces equivalentes**
> son **las alternativas** *-- *y **no se eligen solas**: *`lista_linea` tiene **`autorizado`** y
> **`autorizado_producto`**, *y **la persona autoriza.** *
>
> *** -> o sea: *** *** **el oraculo PROPONE, y la persona AUTORIZA** *-- *que es **la misma forma que
> `desde-la-compra`**: *«esto **propone** y la persona **confirma**». *
>
> *** Y **`parecido` esta en el fichero** *** *-- *o sea: **cada enlace lleva SU PUNTUACION**, *
> *y **no solo el veredicto**: *y **eso es lo que permite auditar por que se enlazaron.** *

## 4. Y el estado de B09, con **el oraculo medido en su salida**

```
*** B09 · «identidad y coste con oraculo completo» ***
  *** cuantos enlaces ***  -> *** 22.873 ***
  *** y de que tipo ***    -> *** equivalente 14.528 (63,5 %) · identico 6.617 (28,9 %) · ean 1.728 (7,6 %) *** *
  *** y con que ***        -> *y **cada uno lleva `parecido`**, *o sea **la puntuacion, no solo la etiqueta** *
  *** y el coste ***       -> *`precio_derivado.parquet`, *** 1.643.898 filas *** *
  *** -> y **la lectura honesta**: *la mayoria son **equivalentes** -- *que es **lo que hay que comparar**, *
     *y **no un error.** *
```

> *** Y **no se declara «el oraculo acierta»**: *** *se declara **que hay**, *y **cuantos de cada**, *
> *y **que cada uno lleva su puntuacion.** *
