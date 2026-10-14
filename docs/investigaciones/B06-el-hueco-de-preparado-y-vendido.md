# B06 · **el unico hueco que he encontrado**: «preparado / vendido»

*Despues de **cuatro cosas de B06 que si estaban** *(-- *y que la fila del control no contaba --), *
*esta es **la primera que no**, *y **la digo con el metodo nuevo**: *buscada **con las palabras del plan**
*y **con las del esquema.** *

---

## 1. *** Lo que el plan pide ***

```
*** B06, literal ***: *
   *** «*Nutricion por 100 g/100 ml/racion *** *y *** preparado / vendido ***.» *** *
```

*Y **la diferencia es real y no es cosmetica**: *100 g de **arroz crudo** *y **100 g de arroz cocido**
*no tienen las mismas kcal* *(-- *el cocido lleva agua --), *y **el mismo producto** puede publicarse
**como se vende** (seco, crudo) *o **como se come** (preparado).* *Mezclarlos es **inventar** *(-- *y el
encargo prohibe inventar calorias --).* *

## 2. *** Y lo que hay ***

```
*** `core/schemas.py:75-77` *** *
   *** `"nutricion": pl.Utf8,          # JSON: kcal, grasas, saturadas, hidratos,` *** *
   *** `#   azucares, fibra, proteinas, sal` *** *
   *** `"nutricion_por": pl.Utf8,      # "100g" | "100ml" | "porcion"` *** *
*** -> **la base de la etiqueta SI esta**, *y con **tres valores** ✓
*** -> **y NO hay** columna -- *ni valor -- que diga **si el dato es del producto que se vende**
   *o **del plato preparado** ⚠️
```

## 3. *** Y como lo he buscado, que es lo que cambia ***

```
*** CON LAS PALABRAS DEL PLAN ***: *** `preparado` *** · *** `vendido` *** ✓
*** Y CON LAS QUE USARIA UN ESQUEMA ***: *** `tal_cual` · `en_seco` · `cocido` · `crudo` ·
   `as_sold` · `estado` *** ✓
*** y en `core/schemas.py`, *en `core/`, *y **en los 23 ficheros de ensayo de fichas e inventario** *
*** -> y **solo aparecen comentarios sobre `auditar_crudo.py`**, *y **categorias de tienda**
   (`preparados`, *que es **otra cosa**: *una seccion, *no una base nutricional)* ⚠️
*** -> *** asi que no es «no lo he buscado»: *es «no esta» *** ✓✓✓
```

## 4. *** Y las dos formas de hacerlo, que son **una decision de diseño** ***

```
*** (a) UN VALOR MAS EN `nutricion_por` ***  *-- *`"100g" | "100ml" | "porcion" | "preparado"` *
   *-- *ventaja: **una columna menos**, *y **el dato ya viaja en el mismo sitio** ✓
   *-- *inconveniente: *`nutricion_por` dice **la base de la medida**, *y «preparado» es **otra
      dimension** *(-- *un producto puede estar **por 100 g Y preparado** --)*, *asi que **se
      mezclarian dos cosas en un campo** ⚠️
*** (b) UNA COLUMNA APARTE ***  *-- *p. ej. `nutricion_estado = "vendido" | "preparado"` *
   *-- *ventaja: **son dos dimensiones independientes**, *y **cada una dice una cosa** ✓
   *-- *inconveniente: *una columna mas, *y **hay que decidir el valor por defecto** *(-- *y si
      «no consta» es un tercer valor --)* ⚠️
*** -> y **`nutricion_por` ya tiene `porcion`**, *que **tampoco es una unidad de masa** *-- *
   *asi que **el campo ya mezcla un poco** *(-- *y eso **inclina hacia (b)**, *pero **no lo decide** --)* ⚠️
```

## 5. *** Y lo que NO toco, y por que ***

```
*** NO LO IMPLEMENTO EN ESTA RONDA ***, *y **digo el motivo**: *
   *-- *es **un cambio de esquema** *(-- *y el catalogo es Parquet, *con sus 51.631 filas y su
      `alcance.yml` --), *y **hacerlo sin contexto** es **como el arreglo del SSRF que reverti** ⚠️
   *-- *y **las dos formas son defendibles**: *elegir **sin medir cuantas fichas traerian el dato**
      *seria **inventar la decision** ⚠️
*** LO QUE SI HAGO ***: *
   *** dejarlo ESCRITO, *con las dos opciones y sus contras** *** ✓
   *** y **en la fila del control**, *que es **lo que lee el siguiente** *** ✓
*** Y **el comando siguiente, si se decide hacerlo**: *
   ```
   git grep -n "nutricion_por" -- core plataforma tests
   *-- *para ver **cuantos sitios leen ese campo** *antes de anadir un valor o una columna* ✓
   ```
```

*** Y **esto cierra B06 con un balance honesto**: *cinco cosas **medidas y presentes**, *una
**buscada y ausente**, *y una **declarada desconocida** *(-- *la causa concreta de cada hueco --).*
*Que es **exactamente** la distincion que el objetivo pide: *** demostrado / hipotesis / desconocido. *** *
