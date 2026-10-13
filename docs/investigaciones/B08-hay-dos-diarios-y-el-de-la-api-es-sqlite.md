# B08 · **Hay DOS diarios, y el de la API es SQLite**: la ruta del objetivo es una decision, no un tramite

*(13 de octubre de 2026. **Y evita el error de meter una escritura de Postgres en el fichero del diario de SQLite.**)*

## 1. El hallazgo, literal

```
`plataforma/api/diario.py`
l17   from core import *** diario ***
l34   def _con():
l35       return *** diario.conecta(_ruta_base) ***      *<- y `core.diario.conecta` abre SQLite*
l27   """Donde vive el fichero del diario. Se puede fijar para que las pruebas NO TOQUEN EL DE VERDAD."""

*** Y `plataforma/api/almacen.py` ***  *-- donde estan `preferencias_de` (l1030) y `guarda_preferencia` (l1036) --*
   *usa `cur.execute("... %s ...")`, *que es *** POSTGRES ***: *`preferencia` es una tabla de Postgres.*
```

> *** O sea: *** *** **el fichero de la API que se llama `diario` NO toca Postgres**: *abre el **diario de
> SQLite** (`data/diario.sqlite`) *con `core.diario.conecta`.* *
>
> *** Y **`preferencia` vive en Postgres**, *y se lee y se escribe con `almacen`.* *
>
> *** -> y por tanto **poner la ruta del objetivo en `api/diario.py`** *mezclaria **dos almacenes** en un
> fichero que hoy tiene uno solo.* ⚠️

## 2. *** Y hay DOS diarios de verdad, y conviene decirlo entero ***

```
*** 1) EL DIARIO DE SQLITE ***  (`data/diario.sqlite`, y `core/diario.py`)
   *-- *y es **el que ve la web**: *`Diario.tsx` llama a **`/api/diario/...`**, *y ese router abre SQLite*
   *-- y **es el que tiene** `apunta`, `de_ficha`, `dia`, `rango`, `borrar` *-- *y **las 11 entradas** de casa*
   *** -> y `resumen(filas)`, que la prevision usa, es **de aqui.** *

*** 2) Y LAS PREFERENCIAS, EN POSTGRES ***  *(`preferencia`, y `almacen.py`)*
   *-- `preferencias_de(usuario_id)` y `guarda_preferencia(usuario_id, clave, valor)`*
   *** -> y `usuario_id` es un `uuid` de Postgres, con FK a `usuario(id)` *** *
```

> *** O sea: *** *** **las dos cosas existen, y en sitios distintos, y con motivos distintos**: *
> *el diario **es de la persona y vive en su fichero** (SQLite, en `data/`), *y **las preferencias son de la
> cuenta y viven en la base de la casa** (Postgres). *
>
> *** Y **el objetivo es «por persona y fecha»** *** -- *o sea: **es una preferencia**, *y **va en `preferencia`.** *
> *** -> pero **su ruta no puede vivir en `api/diario.py` sin decirlo.** *

## 3. Y **la decision, con sus dos salidas y su coste**

```
*** A) LA RUTA VA CON LAS PREFERENCIAS, EN SU PROPIO SITIO ***
   *-- un router nuevo (`api/objetivos.py`), *o **una ruta en `main.py`** junto a las demas de Postgres*
   *** -> y el fichero dice lo que toca: *Postgres, y preferencias.* *
   *** -> y es lo coherente con el resto: *`almacen` es Postgres, *y **`api/diario.py` es SQLite.** *

*** B) LA RUTA VA EN `api/diario.py`, IMPORTANDO `almacen` ***
   *-- y **funcionaria**, *porque `almacen` se puede importar desde cualquier sitio*
   *** -> y mezclaria los dos almacenes en un fichero, *y **el dia que alguien lea `_con()`** *creera que
   **todo** ese fichero es SQLite.* ⚠️
```

> *** Y **la (A) es la que el proyecto elegiria**, *y se puede decir por que: *`main.py:62-66` monta
> **seis routers**, *y cada uno **tiene su almacen**: *`panel`, `recetas`, `despensa`, `cocina`, `diario`.* *
> *Y **la ruta del objetivo es de Postgres**, *asi que **va con las de Postgres.** *
>
> *** Y **una consecuencia practica**: *** *** el objetivo **no necesita `_ruta_base`** *(que es el truco de
> `api/diario.py` para que las pruebas no toquen el diario de verdad), *porque **`preferencia` es de Postgres
> y ya se prueba contra la base de pruebas.** *

## 4. Y el estado, con la ruta del objetivo **localizada y con su decision tomada**

```
*** B08 · lo que queda: ***
  *** a) LA RUTA DEL OBJETIVO *** -> *** y su sitio es el de las preferencias (Postgres), NO `api/diario.py` *** *
     *`GET` -> `preferencias_de(usuario_id)`, *y **filtrar las claves `"objetivo:<fecha>"`** *
     *`POST` -> `guarda_preferencia(usuario_id, *** f"objetivo:{fecha}" ***, *** {"kcal": N} ***)` *
     *** -> y si no hay objetivo, NO SE DEVUELVE UNO: la grafica tiene DOS series, y se dice. *** *
  *** b) LA VISTA DE LAS TRES SERIES *** -> *y `chispa.ts` ya tiene las reglas*
  *** c) y el paso 3 del enlace *** -> *`cesta.py:184`: la columna la escribe `emparejar.py`*
```

> *** Y **esto no es un detalle de organizacion**: *** *** es **la misma leccion de `nivel()`** *-- *que
> **la etiqueta no diga mas de lo que el dato sostiene** -- *aplicada a **un fichero**: *si `api/diario.py`
> empezara a escribir en Postgres, **su nombre mentiria.** *
