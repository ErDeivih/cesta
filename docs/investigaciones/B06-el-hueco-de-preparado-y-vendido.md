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

---

## 6. *** Y medido despues: **no es un olvido, es una limitacion de la fuente** ***

```
*** BUSCADO EN TODO EL CODIGO ***, *con las palabras del plan y con las del esquema: *
   *** «preparad» ***  *-> *** solo categorias de tienda ***: *`alimentos.py:36`, *`secciones.py:38`,
      *`catalogo.py:621` -- *`"preparados"`*, *que es **una seccion del supermercado**
      *(-- «Comida Preparada > Pizzas» --)*, *** no la base nutricional *** ⚠️
   *** «tal cual» ***  *-> **y son comentarios sobre otra cosa**: *
      *`normalize.py:210`: *«mercadona 488 de 488 ya por kilo/litro -> *** tal cual ***»*
      *(-- o sea: *«**el precio ya viene por kilo**» --), *`dueno.py:10`: *«tal cual… no acepta un UUID»* ✓
   *** «escurrid» ***  *-> `schemas.py:89`: *** `"peso_escurrido_g": pl.Int32` *** *
      *-- *y **con su motivo escrito**: *«En conservas, *comparar por *** peso escurrido *** en vez de
      por peso total *** cambia cual es mas barato ***»* ✓
      *-- *** y es lo mas parecido, *y es sobre PESO, *no sobre nutricion *** ⚠️
*** -> *** NO HAY NINGUNA SEÑAL DE «PREPARADO / VENDIDO» *** ✓✓✓
```

> ***O sea: **el hueco no es un olvido del proyecto** *-- *ninguna de las seis cadenas **publica** ese
> dato* *(-- *nada en el codigo lo lee --)*, *y **la unica distincion parecida** *(-- `peso_escurrido_g` --)*
> **es sobre el peso**, *y **tiene su motivo escrito.*** *
>
> ***→ Asi que «preparado / vendido» es *** una LIMITACION DE LA FUENTE ***, *
> *** no una falta de implementacion *** ✓✓✓ *
>
> ***→ Y **eso es exactamente lo que el objetivo pide declarar**: *
> *** «*Declara cada capacidad *** implementada / verificada / limitada *** con evidencia» *** ✓✓✓ *

## 7. Y B06 queda con las tres categorias, y cada una con su prueba

```
*** IMPLEMENTADO Y VERIFICADO *** (cinco): *
   *densidad (5 sitios, *** 7 ensayos ***) · *cobertura *** por nutriente *** *
   (`{con_dato, total, completa}`) · *inventario con `PENDIENTE`/`NO_PUBLICADO`, columna `estado`, *
   *cola con prioridad *y *** presupuesto por fuente *** (72.319 fichas, *con su motivo) · *
   *nutricion por *** 100g/100ml/porcion *** con selector en la pantalla · *
   *y *** nativo vs enriquecido *** (`precio_ref_nativo_cent`, `ha_bajado_nativo`) ✓✓✓
*** LIMITADO POR LA FUENTE *** (una): *** «preparado / vendido» *** *
   *-- *y **la forma de implementarlo, si algun dia hay dato, ya esta decidida por medicion**: *
      *** columna aparte ***, *porque **lo unico que lee `nutricion_por` es una etiqueta de pantalla**
      *(`app.js:1299`: *`Por ${p.nutricion_por || '100 g'}`)* ✓✓
   *-- *y `ESQUEMA_BRONZE` es **un contrato con ensayo** (`test_colectores.py:150`), *
      *asi que **el cambio se notaria** ✓
*** DESCONOCIDO *** (una): *la *** causa concreta *** de cada hueco nutricional, *
   *que puede estar dentro de `no_publicado` ✓
```

*** Y **esto cierra B06**, *y **con la distincion que faltaba al principio**: *no todo lo que no esta
*** falta ***; *a veces **la fuente no lo da** *--* *y **confundir esas dos cosas** es lo que hace que un
plan se cierre mal: *o **declarando hecho lo que no hay**, *o **prometiendo lo que nadie publica.*** *
