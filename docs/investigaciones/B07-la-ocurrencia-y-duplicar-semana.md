# B07 · **la ocurrencia del plan, y «duplicar semana»** -- hecho, en orden, y con su prueba

*El plan pedia, en B07: *** «*Plan con *** varias comidas por día ***, *** repetir/duplicar semana *** y
*** raciones por ocurrencia ***».** *Y **parecian tres features.** *No lo eran: *eran **una carencia de
modelo**, *y eso se vio **leyendo la clave primaria.** *

---

## 1. *** El diagnostico, que salio de una linea ***

```
*** `core/recetas.py:49-55`, ANTES *** *
   *** `CREATE TABLE IF NOT EXISTS plan (fecha, receta_id, version, comensales,`
   *** `                                 PRIMARY KEY (fecha, receta_id));` *** *
*** -> y con esa clave **no se podia**: *
   *-- *poner la misma receta **dos veces el mismo dia** *(-- choca con la clave --)* ⚠️
   *-- *decir **en cual de las comidas** va ⚠️
   *-- *decir **cuantas raciones** se cocinan ahi ⚠️
   *-- *ni **copiar una semana**, *porque **copiar exige saber que copiar** ⚠️
*** -> o sea: **el plan modelaba bien** «esta receta, este dia, para esta gente», *
   *** y no modelaba la ocurrencia *** ✓✓✓
```

## 2. *** Y lo que se hizo, **en este orden** ***

```
*** 1) LA IDENTIDAD ***  *** `(fecha, receta_id)` -> `(fecha, comida, receta_id)` *** ✓
   *-- *y **el vocabulario NO se invento**: *son los valores de *** `diario.COMIDAS` ***, *
      *que **ya existia** *(-- desayuno, media manana, comida, merienda, cena, otras --)* ✓✓✓
*** 2) LA MIGRACION ***  *** en `_migra()`, *con los datos dentro *** *
   *-- *SQLite **no permite `ALTER TABLE` sobre una clave primaria**: *hay que **rehacer la tabla** ✓
   *-- *y va **en `_migra` y no en el esquema**, *por **el motivo que ya esta escrito alli**: *
      *en una base antigua la columna **no existe**, *y un `INSERT` sobre ella **reventaria antes**
      *de que la funcion pudiera arreglarlo ✓
   *-- *y **conserva**: *fila vieja -> `comida='comida'` *(-- lo que significaba --), *
      *`raciones=NULL` *(-- las de la receta, *que es lo que se cocinaba --)* ✓✓✓
*** 3) LAS RACIONES ***  *** columna PROPIA de la ocurrencia *** *
   *-- *`NULL` = «las de la receta», *y *** NO se copian ***: *si se copiaran, *una receta que cambie
      *cambiaria *** lo que ya se cocino *** ✓✓✓
*** 4) LAS TRES FUNCIONES ***  *-- `planificar` · `plan` · `quitar_del_plan` ✓
*** 5) LAS TRES RUTAS ***  *-- `POST /plan` *y `DELETE /plan` aceptan la ocurrencia; *
   *`GET /plan` **ya la devolvia** ✓
*** 6) LA PREVIA ***  *-- `GET /plan/prevision` **lleva `comida` y `raciones`** ✓
*** 7) LA PRUEBA ***  *** 9 ensayos *** ✓✓✓
*** 8) Y *** DUPLICAR SEMANA ***, *que **es la consecuencia**, *y **va al final por eso** ✓✓✓
```

## 3. *** «Duplicar semana», y la decision que **contestó B05** ***

```
*** B05, ya escrito ***: *** «*misma clave con contenido distinto produce *** CONFLICTO, *no exito
   ficticio ***» *** ✓
*** -> por eso *** NO usa `INSERT OR REPLACE` *** *
   *-- *que es lo que usan las demas, *y *** alli reemplazar es correcto ***: *el usuario esta
      diciendo «pon esta receta aqui» ✓
   *-- *aqui *** `INSERT OR IGNORE` ***, *y **devuelve el recibo**: *
      *** `{"creadas": n, "ya_estaban": m}` *** ✓✓✓
   *-- *porque **decir «duplicado» cuando no se duplico nada** es *** exactamente *** el exito
      ficticio que B05 prohibe ✓
*** y **la ruta** *** `POST /plan/semana` ***, *con **dos fechas y nada mas**: *
   *** lo que se copia lo lee el servidor *** ✓
```

## 4. *** Y los 9 ensayos ***

```
*** DE LA IDENTIDAD (5) *** *
   *la misma receta dos veces el mismo dia son **dos ocurrencias** · *
   *las raciones son **de la ocurrencia**, *y **la receta puede cambiar sin tocar lo cocinado** · *
   *la comida **se valida** contra `diario.COMIDAS` · *
   *quitar **con y sin** comida · *
   *y **una base con la clave vieja se migra sin perder lo planeado** ✓✓✓
*** DE DUPLICAR (4) *** *
   *copia **con comida y raciones** · *
   *** NO pisa lo que ya hay, *y lo dice en el recibo *** *(-- la tortilla **no se toca** con sus 9
   comensales y 9 raciones, *y **la ensalada si se copia** --)* · *
   *duplicar sobre la misma semana **es un error dicho** · *
   *y **no toca el plan de otro** ✓✓✓
```

## 5. *** Y lo que queda **dicho sin adornos** ***

```
*** EL CORE TIENE 9 ENSAYOS; *** LA RUTA `POST /plan/semana` NO TIENE NINGUNO *** ⚠️ *
   *-- *la ruta es **fina** *(-- *valida, *llama, *traduce el `ValueError` a 422 --)*, *
      *y **lo que decide esta probado en `core`** ✓
   *-- *pero **eso es lo que yo mismo dije de B07 al principio** *(-- «los 19 ensayos prueban el
      modulo, *no la ruta» --), *y **seria incoherente no decirlo ahora de mi propio cambio** ⚠️✓
   *** -> y **el siguiente comando, nombrado**: *
   ```
   uv run pytest -q tests/test_b07_la_ruta_de_importar_y_sus_guardas.py
   *-- *que es el fichero donde deberia ir, porque ya tiene el cliente y el patron*
   ```
*** Y **los errores mios de esta tanda**, *que fueron **seis**: *
   *13 lineas de comentario de Python **dentro del esquema** *(-- `ruff` no lo vio, *los ensayos si --)* ·
   *`ingredientes` como cadenas *(-- el codigo lo dijo claro --)* ·
   *un parentesis de mas · *un triple apice mal cerrado · *
   *una sangria de **doce** espacios donde habia **ocho** · *
   *y **dos ensayos mal planteados** *(-- la Ensalada en el destino, *y pedirle a `otro` que no
   tuviera plan --)* ⚠️
*** -> y **todos menos el primero los cazo un instrumento**: *`ruff`, *los propios ensayos, *
   *o **el `assert` que va antes de escribir** ✓✓✓
```

## 6. Y el estado, verificado

```
*** `ruff` ***  *** All checks passed! *** ✓
*** `pytest -q` ***  *** 2.070 passed · 0 failed · 17 skipped *** ✓✓✓
*** `python -m plataforma.prueba_e2e` ***  *** «== TODO BIEN» *** ✓✓✓
*** y **los scripts de un solo uso**, *borrados* ✓
```
