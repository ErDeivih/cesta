# B03 · **EL CAMBIO ESTA INVERTIDO.** La prueba de fuego lo dice, y hay que revertirlo

*(13 de octubre de 2026. **Se acaba de descubrir, midiendo, que la pieza de la ronda 87 hace lo CONTRARIO de lo
que B03 quiere. Se escribe antes que nada mas.**)*

## 1. La medida

*Se dio a `agrupar_enlaces` el caso exacto, hecho a mano*: **el mismo producto, en la misma cadena, en dos
zonas** -- *y un tercero de otra cadena, parecido a los dos.*

```
filas:
  lidl / "Leche entera 1 L" / region 28
  lidl / "Leche entera 1 L" / region 07
  dia  / "Leche entera 1 L" / region None

enlaces:  (0,2) y (1,2), los dos a 0.95
```

**Y el resultado:**

```
SIN zonas (como hoy)   grupos: [0, 1, 0]
  -> los dos de lidl en el mismo grupo: False      <- LO CORRECTO

CON zonas (el cambio)  grupos: [0, 0, 0]
  -> los dos de lidl en el mismo grupo: TRUE       <- *** LO CONTRARIO ***
```

## 2. Y por que, que es lo que hay que entender

**La invariante «un grupo no puede tener dos productos de la misma cadena» NO es una regla de estilo: es lo que
IMPIDE que dos productos de la misma cadena acaben juntos.**

*Y eso es lo que hace que el grupo monstruo no se forme* -- *los 25 de Alcampo, 25 de DIA, 17 de Carrefour que se
fundieron en el grupo 92.*

> **Al relajarla a «misma cadena Y MISMA ZONA», dos precios de la misma cadena en zonas distintas DEJAN DE
> ESTAR PROHIBIDOS -- y por tanto SE JUNTAN.**
>
> **O sea: el cambio hace que las zonas SE MEZCLEN en vez de SEPARARSE.** *Exactamente lo contrario de lo que
> B03 lleva cuarenta rondas buscando.*

## 3. Y el error de razonamiento, que es lo que hay que dejar escrito

*En la ronda 87 se escribio, y era el razonamiento central:*

> *«un producto no puede tener dos parejas en la misma CADENA Y LA MISMA ZONA -- pero SI PUEDE en la misma cadena
> y OTRA ZONA, porque son dos precios distintos.»*

**Y la primera mitad es correcta; la segunda es el error.**

> **«Que sean dos precios distintos» no significa «que puedan ir en el mismo grupo»: significa JUSTO LO CONTRARIO
> -- que NO pueden, porque son dos precios de sitios distintos y un grupo es un conjunto de cosas comparables.**
>
> *Se confundio **«son distintos»** con **«pueden juntarse»**.* **Y son lo contrario: si son distintos, hay que
> separarlos.**

**Y la prueba de las dos zonas, que se escribio en la ronda 83 y pasa, **no lo caza** -- porque comprueba que
`regiones=None` da lo mismo que no pasarlo, *que es verdad*. **Lo que no comprueba es que con zonas haga lo
correcto** -- *y hace lo inverso.*

## 4. Y por que la prueba de fuego no existia antes

**Porque todas las pruebas que se escribieron comprobaban que el cambio NO ROMPIA lo de antes** -- *«sin zonas
nada cambia»* --, **y ninguna comprobaba que hiciera lo que B03 pide.**

> *Es la misma forma que la medida mal interpretada de la ronda 68: **se comprobo lo que era facil de comprobar**
> -- que nada empeoraba -- **en vez de lo que habia que comprobar** -- que mejora.*
>
> **Y la causa es la misma: la prueba se escribio desde el cambio, no desde el objetivo.**

## 5. Lo que hay que hacer, y se dice sin rodeos

  **1. REVERTIR la pieza de la ronda 87** (`dea976a`: `ocupados` por `(producto, cadena, zona)`).
  **2. Y revisar las otras dos que tocan la invariante** -- *`75e625f` (la guarda) y `2ad380c` (los bloques)* --,
     **porque las tres salen del mismo razonamiento invertido.**

> **Y la direccion correcta hay que pensarla desde el objetivo, no desde el mecanismo:**
>
> **un grupo no puede tener DOS PRECIOS DEL MISMO PRODUCTO EN ZONAS DISTINTAS** -- *o sea, la zona **separa**, y
> lo que hay que prohibir es la mezcla.* **Que es lo contrario de lo que se escribio.**
>
> *Y eso no es un cambio en `ocupados`: es una condicion **nueva**, sobre la zona, **en la guarda** -- junto a la
> de la cadena, no en lugar de ella.* **La de la cadena sigue como estaba.**

## 6. Y lo que esto dice de las catorce medidas

**Catorce medidas siguen en pie** -- *todas dicen donde esta cada cosa, y eso es cierto y util.* **Lo que estaba
mal era la CONCLUSION que se saco de ellas:** *«la zona entra en la clave»* -- *que se decidio en la ronda 63 con
la respuesta del propietario delante, y **se aplico al reves**.*

> *El propietario dijo:* **«que dependa de la region que elija el usuario»**. *Y eso significa que **el precio que
> ve es el de SU zona** -- y por tanto **los de otras zonas no pueden estar en el mismo grupo mezclados con
> ellos**.*
>
> **La decision era correcta. La traduccion a codigo, no.** *Y se ha visto **cinco rondas despues**, con una
> prueba de fuego que se hizo **porque quedaba contexto para hacerla**.*
