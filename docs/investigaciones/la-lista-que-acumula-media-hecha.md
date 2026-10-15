# La decisión 3 · **«la lista acumula»** -- media hecha, y la otra media medida

*El propietario contesto el 14/10/2026: *** «las cuatro, de acuerdo con lo recomendado»** *, *y la
tercera era: *** la lista ACUMULA ***.* *Y **eso ha resultado ser un cambio en TRES sitios**, *no en uno. *

---

## 1. *** Por que son tres, *y no uno ***

```
*** EL TRASPASO (receta -> lista) ***  *ya lo hacia bien, *y **por eso no se notaba**: *
   *-- *usa *** `traspaso.id_de_linea` *** *(-- una funcion, *no la formula a mano --)* ✓
   *-- *y tiene *** la tabla `traspaso` ***, *cuya `clave` es **`PRIMARY KEY`** *
   *-- *y **su docstring lo dice**: *«*La tabla de operaciones. *Con la clave unica: *** es ella la
      que impide el duplicado ***» ✓✓✓
*** EL PUENTE DEL PLAN ***  *** NO tenia nada de eso *** ⚠️
   *-- *hacia `uuid5(lista_id|uno.clave)` **a mano**, *y `uno.clave` es *** producto + unidad *** *
      *-- *o sea: *«200 g de tomate» --, *que **no dice de donde viene** ⚠️
   *-- *asi que **dos operaciones distintas** daban **el mismo id**, *
      *y `anade_linea` **actualizaba en vez de anadir** ✓
```

## 2. *** Lo que YA esta hecho ***

```
*** EL ID DE LA LINEA LLEVA LA OPERACION ***  *** HECHO *** ✓ *
   *** `main.py:1818` ***: *** `traspaso.id_de_linea(lista_id, f"{uno.clave}|{desde}|{hasta}")` *** *
   *-- *y **se usa la funcion del proyecto** en vez de la formula a mano ✓
   *-- *y **la operacion es la semana** *(-- `desde|hasta` --)*: *
      *traer **la misma semana dos veces** -> **el mismo id** -> *idempotente ✓
      *traer **semanas distintas** -> **ids distintos** -> *se acumulan ✓
*** Y MEDIDO POR EL RECORRIDO ***: *
   *** «traer la misma semana otra vez no anade nada: siguen 15 lineas» *** ✓✓✓
```

## 3. *** Y lo que FALTA, *con la causa medida ***

```
*** EL CONJUNTO `ya` NO SABE LA OPERACION *** ⚠️ *
   *** `main.py` ***: *** `ya = {((grupo_id, producto_id), nombre.lower()) for x in
   almacen.lineas_de(lista_id)}` *** *
   *-- *se construye con *** TODAS las lineas de la lista ***, *y **salta** todo ingrediente que
      ya este ⚠️
   *-- *y **eso es CORRECTO dentro de una operacion** *(-- dos recetas con el mismo ingrediente
      dejan **una** linea, *que es la **consolidacion por identidad** que pide el encargo --)* ✓
   *-- *y **es INCORRECTO entre operaciones**: *si la lista ya tiene **200 g de tomate**, *
      *y traigo **otra semana que tambien pide tomate**, *** se queda en 200 *** ⚠️
*** Y MEDIDO POR EL RECORRIDO ***: *
   *** «FALLO: traer OTRA semana con plan deberia anadir lineas, y anadio 0» *** ⚠️✓✓✓
```

## 4. *** Y por que **no se puede arreglar leyendo el id** ***

```
*** `traspaso.id_de_linea` DEVUELVE *** `str(uuid.uuid5(uuid.NAMESPACE_URL, f"{lista_id}|{clave}"))` *** *
*** -> *** `uuid5` es un HASH ***: *de `id_de_linea(lista_id, "tomate|2026-11-02|2026-11-08")` *
   *** NO SE PUEDE RECUPERAR la operacion *** ⚠️✓✓✓
*** -> *asi que *** la opcion «leerla del id» NO EXISTE ***, *y **eso lo decide `uuid5`**, *
   *no una preferencia ✓
*** -> y **por eso `traspaso` NO lee la operacion del id**: *la tiene *** en columnas *** *
   *(-- `receta_id`, `version`, `semana` --)* ✓✓✓
```

## 5. *** El cambio que falta, *medido y con sus sitios ***

```
*** 1) LA MIGRACION ***  *** `plataforma/sql/020_la_operacion_de_la_linea.sql` *** *
   *-- *el patron esta en las numeradas: *la ultima es *** `019_la_cantidad_que_gana.sql` *** ✓
   ```sql
   ALTER TABLE lista_linea ADD COLUMN IF NOT EXISTS operacion text;
   -- *NULL quiere decir «no viene de una operacion»* -- *una linea escrita a mano, por ejemplo.
   ```
*** 2) `anade_linea` ***  *(-- `almacen.py:368` --)* *** recibe y guarda `operacion` *** *
   *-- *y **su `INSERT ... ON CONFLICT (id) DO UPDATE`** *sigue igual: *el id ya distingue ✓
   *-- *y en el `DO UPDATE` **no se toca** *(-- *una linea es de la operacion que la trajo --)* ✓
*** 3) `ya` ***  *(-- `main.py`, *donde se construye --)* *** se filtra por la operacion *** *
   *-- *hoy: *`for x in almacen.lineas_de(lista_id)` *
   *-- *y tiene que ser: *solo **las de esta operacion** *(-- `x["operacion"] == f"{desde}|{hasta}"` --)* ✓
   *-- *y **`lineas_de` tiene que devolver la columna** ✓
*** 4) Y EL ENSAYO ***, *que **ya esta escrito en el recorrido** *(-- *y hoy falla --)*: *
   *-- *la **misma** semana dos veces -> **no duplica** *(-- hoy: ✓ 15 -> 15 --)* *
   *-- *otra semana -> **acumula** *(-- hoy: ✗ 0 anadidas --)* ✓✓✓
*** -> y **el comando siguiente**: *
   ```
   uv run pytest -q tests/ -k "lista or puente or del_plan"
   *-- *despues de tocar `lineas_de`, que lo usan varias rutas*
   ```
```

## 6. *** Y el estado, sin adornos ***

```
*** LO QUE ESTA ***  *** el id lleva la operacion, *y la idempotencia funciona *** ✓
   *-- *medido: *** 15 -> 15 *** ✓✓✓
*** LO QUE FALTA ***  *** la columna, *`anade_linea`, *`lineas_de`, *y `ya` *** ⚠️
*** Y **EL RECORRIDO TIENE 1 FALLO** ***, *que es *** el hallazgo ***, *no una regresion ✓
   *-- *y **esta escrito con numeros**: *«y anadio 0» ✓✓✓
```

*** Y **esto es lo que ha valido el recorrido**: *el arreglo del `id` **parecia la respuesta entera**, *
*los **ensayos unitarios pasaban**, *y **el recorrido ha dicho que falta la otra mitad** *--* *y que la
otra mitad **no es un `if`, *es saber de donde viene cada linea.*** *
