# El precio por unidad, y cuando no se puede comparar

Escrito el 17 de septiembre de 2026, despues de descubrir que la app anunciaba
ahorros del **102.896 %**.

Este documento explica las tres reglas que deciden si dos precios se pueden
restar. Son la pieza central de la app: sin ellas, "donde sale mas barato" es
una loteria.

---

## 0. Por donde salio todo

La comprobacion fue esta: coger los enlaces que unen productos con **el mismo
codigo de barras** -- o sea, los que son el mismo producto sin discusion -- y
mirar cuanto se llevan sus precios por unidad.

    enlaces con el mismo EAN                    2.680
      de ellos con el precio/unidad >1,2x         415  (15,5 %)
      de ellos con el precio/unidad   >2x         180  ( 6,7 %)
      de ellos con el precio/unidad  >10x          92  ( 3,4 %)

El mismo producto, con el mismo codigo de barras, con precios por unidad que se
llevan diez veces. Noventa y dos veces. Ese numero es el que hay que vigilar
cuando se toque cualquiera de las tres reglas de abajo.

---

## 1. Un grupo, una unidad

**El problema.** 231 de los 6.448 grupos comparables (3,7 %) tenian productos
medidos en unidades distintas. Ejemplo real, la manzanilla Hornimans de 25
bolsitas a 2,15 EUR en las tres cadenas:

    alcampo     25 ud    0,04 EUR/ud
    dia         25 ud    0,09 EUR/ud
    carrefour      kg   61,43 EUR/kg     <- el peso de la hierba, no las bolsitas

Los tres precios son correctos. Restar el de Carrefour de los otros da un ahorro
del **153.475 %**. Y esos 231 grupos eran el **67 % de todos los que anunciaban
mas de 10x**.

**La regla.** Se elige **una unidad por grupo**: la que comparten mas cadenas, y
a igualdad la que tiene mas productos. Solo se compara dentro de ella. Los
productos en otra unidad siguen en el grupo y salen en la ficha; lo que no hacen
es decidir el ahorro.

Esta en `plataforma/api/catalogo.py`, en los CTE `unidades` / `manda` /
`comparables`. Pruebas: `tests/test_catalogo_filtros.py`.

---

## 2. Un atributo se cumple producto a producto, no por grupo

**El problema.** La busqueda entra por grupos: basta con que un miembro case con
el texto para que el grupo entre, y eso es correcto (si buscas "leche", el grupo
es de leche aunque un miembro se llame "L.R. Desnatada"). Pero luego se
reconstruia el grupo **entero** y se ensenaba el mas barato. Con el filtro **sin
gluten** puesto, "galletas" devolvia unas Cuetara normales: estaban en el mismo
grupo que unas sin gluten y eran mas baratas.

Para alguien celiaco eso no es un resultado flojo. Es un resultado peligroso.

**La regla.** El **texto** se puede cumplir a nivel de grupo. Un **atributo**
(sello, conservacion, marca blanca, oferta) tiene que cumplirlo **cada producto
que se ensena**. Los filtros se aplican dos veces: al buscar y al reconstruir.

---

## 3. Si nuestro precio y el de la cadena se contradicen, no se compara

**El problema.** Cada cadena publica su propio precio por unidad en la etiqueta
del lineal. Nosotros calculamos el nuestro a partir del formato. Cuando los dos
hablan de la misma unidad y se llevan un factor de dos o mas, uno esta mal.

Revisadas las 220 filas del 17 de septiembre una a una, hay errores **en las dos
direcciones**:

| quien se equivoca | caso | que pasa |
|---|---|---|
| nosotros | Conchitas Jumpers 95 g | DIA publica `0,095 g` en su ficha (se comieron el kilo). Salia a 15.263 EUR/kg; su etiqueta dice 15,26 |
| nosotros | Platano de Canarias 850 g | cantidad leida 0,001 kg -> 2.540 EUR/kg |
| **la cadena** | Barrita proteica, pack 3 x 40 g, 3,49 EUR | Aldi dice **0,03 EUR/kg**. Con eso el pack costaria 0,004 EUR. La misma barrita suelta, en Aldi, dice 31,25 |
| **la cadena** | Hierbas provenzales 20 g, 0,77 EUR | Aldi dice 481,30 EUR/kg; lo correcto es 38,50 |
| **la cadena** | Panuelos, pack de 30, 2,95 EUR | Aldi dice 0,01 EUR/unidad |

Se intento decidir por plausibilidad (que la cantidad implicita sea un tamano de
envase creible) y **no se sostiene**: un tarro de azafran de 0,4 g es tan raro
como un error, y sale igual de "implausible" que el fallo de Aldi.

**La regla.** No se elige ganador: la fila se **aparta de las comparaciones**
(`proc_precio_unidad = "en_disputa"`, `precio_comparable = False`). Sigue
teniendo su precio total, sigue saliendo en la busqueda y se puede anadir a la
lista; lo que no hace es decidir donde sale mas barato algo, porque para eso hay
que estar seguro. Son **72 filas de 52.575** (0,14 %).

### 3.1 El orden importa

Esta regla va **despues** de `unidades_inferidas`. El caso "1 ud a 14,90 EUR con
etiqueta de 4,97 EUR/ud" son tres recambios dentro del envase, y "el envase trae
tres" es una explicacion mejor que "alguien se equivoco". De las 220 filas, 148
eran exactamente eso, y con el orden al reves se perdian todas.

### 3.2 El sesgo que tenia el primer intento

La primera version usaba `desviacion_ref = |nuestro - suyo| / suyo`. Eso divide
siempre por el de la cadena, asi que cuando el equivocado es el **nuestro** y se
queda mil veces corto, la desviacion se pega al 0,999 y **no pasa de 1** aunque
el error sea de tres ordenes de magnitud. Le paso al azafran de Alcampo. Ahora se
usa un cociente simetrico, `factor_ref = max / min`, que no tiene ese sesgo.

---

## 4. Ningun producto cuesta treinta veces mas en otro supermercado

Aun con las tres reglas anteriores quedan grupos con diferencias absurdas, porque
el error esta en los datos de la cadena y las dos cifras son "coherentes" entre
si. Medido sobre los 6.448 grupos comparables, ya con una sola unidad por grupo,
la frontera es limpia:

| factor | grupos | que son |
|---:|---:|---|
| > 5x | 130 | ahorros reales |
| > 10x | 43 | casi todos reales |
| > 20x | 23 | mezcla |
| **> 30x** | **15** | **todos errores** |

Hasta 30x son los ahorros buenos, los que la app existe para ensenar:
preservativos de marca blanca frente a Durex (28x), cerveza de marca blanca
frente a Estrella Galicia (28x), tampones frente a Tampax (25x).

Por encima de 30x, los 15 casos son errores: el azafran que Alcampo etiqueta
"400g" cuando son 400 mg, un champan comparado por botella contra el mismo por
unidad, un filete de dorada a 7.120 EUR/kg.

**La regla.** Por encima de `FACTOR_INCREIBLE = 30` el grupo se marca `dudoso`:
sale en la busqueda, sigue diciendo donde esta mas barato, y **no pone numero de
ahorro**. En pantalla dice "precios que no cuadran entre cadenas".

Un "ahorra un 102.896 %" se carga la confianza de golpe y para siempre. Decir
"esto no cuadra" cuesta un resultado y la conserva.

---

## 5. Lo que NO sirve para separar grupos

Apuntado para que nadie lo intente otra vez:

**El envase no sirve.** Parecia la senal perfecta -- dos productos con envase
distinto casi nunca son el mismo -- y al medirlo: de los 980 enlaces donde las
dos cadenas publican envase, **372 (38 %) no coinciden**, y mirando los casos son
el mismo producto con distinta palabra. Las mismas barritas Huesitos son "bolsa"
en una cadena y "paquete" en otra; el mismo cepillo es "blister" y "paquete".
`core/envases.py` unifica lo que se puede, pero el vocabulario de las cadenas no
es lo bastante fino para bloquear un emparejamiento.

**`tipo_producto` todavia no se puede usar.** Solo lo publica DIA, asi que hay
**cero** enlaces donde las dos puntas lo tengan. Sera util cuando alguna cadena
mas lo dé; hoy no bloquea nada.

---

## 6. El emparejador y el tamano de las filas

Sin relacion con los precios, pero descubierto en la misma pasada y conviene no
perderlo.

`enlaces()` recorre **16,7 millones de pares candidatos** y en cada uno hace
varias busquedas en el diccionario de las dos filas. Con las 17 columnas que
llegaban a gold tardaba 79 s. Al crecer el contrato a 34 columnas, el mismo
trabajo se fue por encima de 115 s **sin que cambiara ni una linea del
algoritmo**: diccionarios mas grandes, peor localidad de cache.

`core/matching.adelgaza()` se queda con las seis columnas que el emparejador mira
de verdad (`fuente`, `nombre`, `marca`, `cantidad`, `unidad_canon`, `ean`) y
devuelve el tiempo a 80 s. Lo importante no es el 30 %: es que **deja de empeorar
cada vez que se conquista un dato nuevo a una cadena**, que es lo que este
proyecto hace todas las semanas.
