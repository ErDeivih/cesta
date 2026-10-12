---
seccion: Ingeniería de datos
resumen: Lo que NO hay en el catálogo, medido por fuente y por campo, con el universo y la consulta. 81,6 % sin datos de calidad.
en_una_frase: La mitad del catálogo no tiene ni código de barras, y la mayor fuente no aporta ni un ingrediente.
---

# 18 · Lo que no hay: la cobertura, medida

**Por qué este capítulo existe, y por qué es incómodo.**

*Los capítulos anteriores explican lo que el sistema **sabe hacer**.* **Este mide lo que **no sabe**, que es
la mitad que decide si sirve para algo.**

**Y existe porque la revisión del 12 de octubre de 2026 lo pidió con estas palabras:**

> *«Debe completarse con **ejemplos reales de estas carencias, no con una descripción ideal que afirme
> cobertura conseguida**.»*

*Un material que sólo cuenta lo que funciona describe un sistema que no existe.* **Aquí están los números,
y son los de hoy -- no los de un informe anterior.**

---

## El universo, la fecha y la consulta

**Sin esto, un porcentaje no significa nada.** *«22,8 % de nutrición» no dice **de qué**.*

```
universo:     data/gold/v20261007-103000/grupos.parquet     <- la version que sirve la API
filas:        52 087
fecha:        12 de octubre de 2026
```

**Y la consulta, para que se pueda repetir:**

```sql
SELECT count(*) FILTER (WHERE kcal_100g IS NOT NULL) AS con_kcal,
       count(*)                                     AS total
FROM 'data/gold/v20261007-103000/grupos.parquet';
```

> **Y un aviso que vale como lección**: *las cifras que yo tenía apuntadas hablaban de **48 606** filas.*
> **Otra universo.** *Si se copian, se publica un porcentaje que no es de este catálogo* -- *y nadie lo
> notaría, porque los dos son plausibles.*

---

## 1. Los códigos de barras: la mitad

```
ean   con: 25 136  (48,3 %)      sin: 26 951  (51,7 %)
```

**Más de la mitad del catálogo no tiene código de barras.**

**Y eso no es un detalle de calidad del dato: es la puerta de todo lo demás.** *La identidad entre cadenas
(`core/identidad.py`) empieza por el GTIN; **sin él, sólo queda el parecido de nombres*** -- *que es
exactamente el terreno donde `Président` y `Milsani` pueden acabar en el mismo grupo sin serlo.*

**La consecuencia está medida en el capítulo del emparejador**: *de los grupos que no se pueden arreglar,
**25 896 no tienen EAN** -- *la causa mayor, por delante de los que sí lo tienen y Open Food Facts no
conoce (13 898).*

---

## 2. La nutrición: uno de cada cinco

```
kcal_100g        con: 11 238  (21,6 %)
proteinas_100g   con: 11 139  (21,4 %)
nutriscore       con:  8 461  (16,2 %)
ingredientes     con:  7 146  (13,7 %)
nutricion_por    con:  3 256  ( 6,3 %)
```

**Y `nutricion_por` es el más bajo de todos, y es el que más importa.** *Es la columna que dice **por qué**
son esos 21,6 gramos: por 100 g, por 100 ml, o por porción.* **Sin ella, un valor no se puede comparar con
nada** -- *y sólo el 6,3 % lo tiene.*

**La lección de las unidades, otra vez**: *un número sin su unidad no es un dato, es un número.* **Y aquí
está medido cuántas veces falta.**

---

## 3. **Lo que aporta cada tienda, y esto es lo que más dice**

```
FUENTE        filas    con kcal   con ingredientes
alcampo      23 128           0                 0     <- la mayor, y CERO Y CERO
carrefour    16 195       6 512                 0     <- ingredientes CERO
dia           5 783       2 826             4 394
mercadona     4 213       1 900             2 752
aldi          2 768           0                 0     <- CERO Y CERO
```

### Y lo que esto significa, sin adornos

**Alcampo es la fuente más grande del catálogo -- 23 128 filas, el 44 % -- y no aporta ni una caloría ni un
ingrediente.** *Ni uno.* **Y Aldi, igual: 2 768 filas y cero.**

**Carrefour aporta calorías (6 512) y ningún ingrediente.** *O sea que de Carrefour se puede saber cuánta
energía tiene algo, y no de qué está hecho.*

**Sólo DIA y Mercadona traen ingredientes.** *Entre las dos, 7 146 -- **que es el total del catálogo**,
porque la columna `ingredientes` sólo se llena desde ahí.*

> **La conclusión, y es la que el material tiene que dejar clara**: *la cobertura de nutrición **no es una
> propiedad del catálogo: es una propiedad de cuatro de las cinco cadenas***, *y la mayor de ellas no
> aporta nada.* **Cualquier promesa de «cobertura» que se dé sin decir esto está hablando de otro sistema.**

---

## 4. La procedencia del dato: donde nace A06

```
calidad_origen
    sin_datos            42 505   (81,6 %)
    precio                8 588   (16,5 %)
    ingredientes            654   ( 1,3 %)
    ingredientes_off        340   ( 0,7 %)
```

**El 81,6 % del catálogo no tiene ningún dato de calidad** -- *ni ingredientes, ni Nutri-Score, ni nada con
lo que puntuar.*

**Y de lo que sí lo tiene, la mayoría es `precio` (8 588):** *una calidad **deducida** del precio, no leída
de una etiqueta.* **Eso no es un defecto si se dice** -- *y es exactamente lo que A06 arregló: **el sello de
la pantalla decía «leída de ingredientes» para las dos procedencias**, y ahora dice cuál es.*

**Y las dos columnas que importan de verdad suman 994 grupos: el 1,9 %.** *De los que 340 son
`ingredientes_off`* -- *deducidos **por un tercero**, no por la tienda.*

> **Así que el total honesto es éste**: *de 52 087 grupos, **994 (1,9 %) tienen una calidad leída de
> ingredientes**, y de ellos **654 (1,3 %) la leyó la tienda**.*

---

## 5. Lo que NO se ha medido, y se dice

*Este capítulo cubre **lo que hay en `grupos.parquet`**.* **Y hay tres cosas que su criterio pide y aquí no
están:**

- **El «universo de alimentos»**: *qué parte de los 52 087 grupos son **comida** y qué parte son
  droguería, limpieza o mascotas.* **No se ha computado**, y sin él *el 21,6 % de nutrición no se puede
  juzgar*: *si la mitad del catálogo no es comida, la cobertura de la comida es mejor de lo que parece -- y
  si casi todo es comida, es peor.* **Decir un porcentaje sin haberlo mirado sería inventarlo.**
- **El inventario por campo y por cadena**, más allá de las cuatro columnas de arriba.
- **La cola de fichas** (nuevos / cambiados / caducados) con su presupuesto y sus reintentos. *Hay una
  `fichas` con trabajo pendiente, y **no se ha medido aquí con el detalle que su criterio pide**.*

**Y no se dan números de esas tres cosas.** *Es la misma regla de todo el material: **lo que no se sabe se
dice, y no se deja que se confunda con un cero.***
