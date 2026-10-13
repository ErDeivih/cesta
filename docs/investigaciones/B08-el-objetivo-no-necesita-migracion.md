# B08 · **El objetivo opcional NO necesita migracion**: `preferencia` ya lo admite, con la fecha en la clave

*(13 de octubre de 2026. **Y resuelve la ultima pieza que B08 pedia sin tocar el esquema.**)*

## 1. La tabla, literal (medida en `cesta-prueba-db`)

```
Table "public.preferencia"
       Column   | Type  | Nullable | Default
    ------------+-------+----------+---------
  *** usuario_id | uuid  | not null | ***
  *** clave      | text  | not null | ***
  *** valor      | jsonb | not null | ***
    Indexes:
        "preferencia_pkey" PRIMARY KEY, btree (*** usuario_id, clave ***)
    Foreign-key constraints:
        "preferencia_usuario_id_fkey" FOREIGN KEY (usuario_id) REFERENCES usuario(id) *** ON DELETE CASCADE ***
```

> *** Y **el encargo pide**: *** *** «*** OBJETIVO OPCIONAL POR PERSONA Y FECHA ***» *** -- *y **la tabla tiene
> justo eso**: *
> ```
> *** `usuario_id` ***  -> *** la PERSONA *** *-- y con `ON DELETE CASCADE`, al borrar la cuenta se va.*
> *** `clave` ***        -> *** y la FECHA cabe en la clave ***: *`"objetivo:2026-10-14"` *
> *** `valor` (jsonb) *** -> *** y el valor lo pone la persona ***: *`{"kcal": 2000}` *
> *** PK `(usuario_id, clave)` *** -> *** un objetivo por persona y fecha, y no dos *** *
> ```
>
> *** O sea: *** *** **la clave primaria compuesta ES la regla del encargo**, *y **el `jsonb` deja el valor
> abierto** *-- *y **el `ON DELETE CASCADE` hace la limpieza sola.** *
>
> *** Y **NO HACE FALTA MIGRACION**, *ni **una tabla nueva**, *ni **un `ALTER TABLE`.** *

## 2. *** Y el valor no se inventa: lo pone la persona ***

```
*** LO QUE EL ENCARGO PROHIBE: ***  *** «no inventes... OBJETIVOS DE SALUD» *** *
*** Y LO QUE ESTA TABLA PERMITE: ***  *guardar **el que la persona escriba**, *y **no calcularlo.** *
```

> *** O sea: *** *** **la estructura se puede hacer, y el valor no.** *Y **eso no es una limitacion del
> diseno: es el diseno.** *
>
> *** Y **la forma de guardarlo ya existe en el proyecto**: *** *`preferencia` **se usa** desde
> `core/despensa.py`, `plataforma/api/almacen.py` y `plataforma/api/main.py` *-- *o sea: **hay funciones de
> leer y escribir preferencias**, *y **el objetivo es una preferencia mas.** *

## 3. Y **las tres cosas de B08 que quedaban, con su estado real**

```
*** B08 pedia: ***
  *** 1. la vista de previstos ***      -> *** HECHA *** *(ronda 274)*
  *** 2. el ensayo ***                  -> *** HECHO *** *(ronda 276: 8 ensayos, y de 2025 a 2033)*
  *** 3. *** EL OBJETIVO OPCIONAL *** ***    -> *** y NO necesita migracion: `preferencia` lo admite *** *
     *`usuario_id` + `clave` (`"objetivo:<fecha>"`) + `valor` jsonb + PK compuesta + CASCADE*
  *** 4. *** LAS GRAFICAS DE LOS TRES *** ***  -> *y `logica/chispa.ts` **ya tiene sus tres reglas**: *
     *«lo que no se observo **no se puede dibujar como si se hubiera observado**»*
  *** y el criterio ***                 -> *`R1=270`, `media=135`, y «ausencia de energia con proteina conocida»*
```

> *** O sea: *** *** **de las cuatro cosas de B08, dos estan hechas y dos tienen su sitio ya localizado.** *
> *Y **ninguna exige inventar un dato.** *
>
> *** Y **lo que falta por escribir** *** *-- *el **almacen del objetivo** y **la vista de las tres series**
> -- *es trabajo de encadenamiento, *y **no de decision**: *la tabla, la PK, el `jsonb`, la grafica y sus
> reglas **ya existen.** *

## 4. Y una nota de metodo, porque esto se midio y no se supuso

> *** Lo que se hizo fue **leer la tabla**, *y **no** «mirar si habria que migrar». *
> *Y **el resultado cambio el trabajo**: *si **no** hubiera encajado, *habria que **decidir una tabla nueva**;
> *y **como encaja**, *lo que queda es **usarla.** *
>
> *** Y **la medicion se hizo en `cesta-prueba-db`** (`127.0.0.1:5434`), *que es **la base de pruebas
> compartida**, *y **solo se describio la tabla** -- *ninguna escritura, *y **nada del propietario.** *
