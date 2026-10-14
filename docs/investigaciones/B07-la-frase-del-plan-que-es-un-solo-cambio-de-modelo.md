# B07 · **la frase del plan que no son tres cosas, sino una**

*El plan dice, en B07: *** «*Plan con *** varias comidas por día ***, *** repetir/duplicar semana *** y
*** raciones por ocurrencia ***».** *Y **parecen tres features.** *No lo son: *son **una carencia de
modelo**, *y se ve **leyendo la clave primaria de la tabla.** *

---

## 1. *** La tabla, que es la que decide ***

```
*** `core/recetas.py:49-55` *** *
   *** `CREATE TABLE IF NOT EXISTS plan (` *** *
   *** `    fecha      TEXT NOT NULL,` *** *
   *** `    receta_id  INTEGER NOT NULL REFERENCES receta(id),` *** *
   *** `    version    INTEGER NOT NULL,` *** *
   *** `    comensales INTEGER NOT NULL,` *** *
   *** `    PRIMARY KEY (fecha, receta_id)` *** *
   *** `);` *** *
```

## 2. *** Y con esa clave, **las tres frases del plan** ***

```
*** 1) «VARIAS COMIDAS POR DIA» ***  *** -> NO ESTA *** ⚠️ *
   *-- *no hay columna **`comida`** *(-- desayuno / almuerzo / cena --)* *
   *-- *y **`(fecha, receta_id)`** no distingue **en cual de las comidas** va ✓
*** 2) «REPETIR / DUPLICAR SEMANA» ***  *** -> NO ESTA *** ⚠️ *
   *-- *medido **leyendo la lista entera de rutas**: *no hay operacion que copie una semana*
   *-- *y **tampoco se puede escribir encima de esta clave**: *copiar exige **saber que copiar**, *
      *y **con `(fecha, receta_id)`** no se distingue **una ocurrencia de otra** ✓
*** 3) «RACIONES POR OCURRENCIA» ***  *** -> NO ESTA *** ⚠️ *
   *-- *hay *** `comensales` ***, *que es *** cuantos comen ***, *
   *-- *y **no** *cuantas raciones *** se cocinan en esa ocurrencia *** *-- *que **es otra cosa** ✓
*** -> y **lo que SI esta**: *** `comensales`, `NOT NULL` *** *
   *-- *que es **exactamente** lo que el encargo pedia con «escalado por comensales» ✓✓✓
```

## 3. *** Y el motivo comun, que es lo que cambia el diagnostico ***

```
*** LA CLAVE ES *** `(fecha, receta_id)` ***, *y eso significa: *
   *-- *** la misma receta NO puede estar dos veces el mismo dia *** *(-- *choca con la clave --)* ⚠️
   *-- *** no se puede decir en que comida va *** ⚠️
   *-- *** no se puede decir cuantas raciones se cocinan ahi *** ⚠️
   *-- *** y no se puede copiar una semana ***, *porque **copiar exige saber que copiar**, *
      *y **hoy una ocurrencia no se distingue de otra** ⚠️
*** -> o sea: **lo que falta es que LA OCURRENCIA TENGA IDENTIDAD PROPIA** *
   *-- *p. ej. **`(fecha, comida, receta_id)`** *-- *o un `id` de ocurrencia --* ✓
*** -> y **entonces las tres frases del plan salen juntas**, *y **no como tres parches** ✓✓✓
```

## 4. *** Y por que eso importa para no hacer el arreglo tonto ***

```
*** SI SE HICIERA «DUPLICAR SEMANA» COMO OPERACION SUELTA *** ⚠️ *
   *-- *habria que **decidir que copiar** *-- *y **con la clave actual no hay nada que nombrar**: *
      *si una receta esta **dos veces el mismo dia**, *son **la misma fila** *(-- *no se puede --)*; *
      *si esta **en dos comidas**, *son **la misma fila** *(-- *idem --)* ⚠️
   *-- *asi que **la operacion no tendria sobre que actuar** *
   *** -> seria EXACTAMENTE el tipo de arreglo que PARECE y NO ES *** *
      *-- *como **la guarda del SSRF que escribi y no interceptaba** *(-- *que parecia proteger --), *
      *-- *como **el `findstr /i running`** *(-- *que parecia comprobar --), *
      *-- *como **el `len() > 40`** *(-- *que parecia una regla --)* ⚠️✓✓✓
*** -> y **por eso el orden correcto es**: *** primero la identidad de la ocurrencia ***, *
   *** y despues las tres cosas *** ✓
```

## 5. *** Y lo que hay que decidir, que **si es una decision de producto** ***

```
*** (a) LA COMIDA COMO PARTE DE LA CLAVE ***  *-- `PRIMARY KEY (fecha, comida, receta_id)` *
   *-- *ventaja: **dice donde va** *y **permite dos comidas el mismo dia** ✓
   *-- *inconveniente: *hay que **decidir el vocabulario** *(-- *desayuno/almuerzo/comida/cena? --)*, *
      *y **una receta no puede ir dos veces a la misma comida** ⚠️
*** (b) UN `id` DE OCURRENCIA ***  *-- *y la comida y las raciones **como columnas** *
   *-- *ventaja: **una ocurrencia se puede nombrar**, *y **copiar** *y **borrar** *una sola ✓
   *-- *inconveniente: *una **clave sustituta** *(-- *y hay que **decidir si se puede repetir** --)* ⚠️
*** y **las `raciones` de la ocurrencia** *** son **una columna nueva** en cualquiera de las dos *
   *-- *y **su valor por defecto** seria *** las de la receta ***, *que es **un dato que ya existe** ✓
*** -> y **eso es lo que hay que decidir antes de escribir**, *no despues* ✓
```

## 6. Y el estado de la frase, con las tres categorias

```
*** IMPLEMENTADO ***: *** `comensales` *** *(-- *el escalado por comensales, *que pedia el encargo --)* ✓
*** HUECO DEL PROYECTO, *MEDIDO, *Y MAS GRANDE DE LO QUE DIJE *** ⚠️: *
   *** «varias comidas por dia» · «repetir/duplicar semana» · «raciones por ocurrencia» *** *
   *-- *las tres, **por la misma causa**: *la ocurrencia **no tiene identidad** ✓
   *-- *y **una operacion suelta encima no las resuelve** ✓✓✓
*** y **el siguiente comando, concreto**: *
   ```
   git grep -n "INSERT INTO plan\|UPDATE plan\|DELETE FROM plan" -- core plataforma
   *-- *para ver TODOS los sitios que escriben el plan, y saber que tocaria el cambio de clave*
   ```
```
