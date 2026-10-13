# B13 · **Los DOS almacenes, medidos por su lista de tablas** -- y el reparto no es casual

*(13 de octubre de 2026. **Septima ronda de B13. Y una medicion cierra lo que B05, B08 y B10 decian por partes.**)*

## 1. Las tablas del PostgreSQL de casa, medidas

```
$ docker exec cesta-db-1 psql -U cesta -d cesta -tAc \
    "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename;"

  alerta · cocina · compra · compra_linea · despensa · favorito · invitacion · lista
  lista_acceso · lista_linea · preferencia · sesion · usuario · visita

  *** y NO hay `receta`, ni `entrada`, ni `plan` ***
     (comprobado: `SELECT ... FROM receta` y `FROM entrada` -> «relation does not exist»)
```

## 2. Y el reparto es **el titulo de B05, literal**

```
B05:  «idempotencia y consistencia *** ENTRE ALMACENES ***»
```

> *** Y los dos almacenes son, medidos: ***
>
> ```
> POSTGRESQL  (casa, 127.0.0.1:5432)   -- *** EL LADO DE LA COMPRA ***
>   usuario · sesion · invitacion · lista · lista_acceso · lista_linea
>   compra · compra_linea · despensa · favorito · cocina · alerta · preferencia · visita
>
> SQLITE      (`data/diario.sqlite`)    -- *** `entrada` ***       (B08: `core/diario.py:23`)
> SQLITE      (recetas)                 -- *** `receta` ***        (B08/B07: `core/recetas.py` usa `sqlite3`)
> ```
>
> *** O sea: *** *** **la compra vive en PostgreSQL y lo personal vive en SQLite.** ***
>
> *** Y **eso explica las tres cosas que esta sesion encontro por separado**: ***
>
>   - **B05**: *«idempotencia **entre almacenes**» -- *y hay **dos**, con **dos formas de no duplicar**: `ON CONFLICT
>     (id) DO UPDATE` + `LEAST`/`GREATEST` en Postgres, y `_el_mismo_reintento` en SQLite (B08);*
>   - **B08**: *`core/diario.py:23 BASE = data/diario.sqlite` -- *y **no es una eleccion suelta**: *es **el lado
>     personal**;*
>   - **B10**: *`cambia_linea` con `LEAST`/`GREATEST` -- *y es **Postgres**, porque **la lista es de casa y se toca
>     desde dos moviles.** *
>
> *** Y el criterio del reparto se puede decir: *** *** lo que **se comparte** (la lista, la compra) **va a la base
> con concurrencia**; y lo que **es de una persona** (su diario, sus recetas) **va a un fichero suyo.** *
>
> *** Y **`Ajustes.tsx` lo dice al usuario** (B08): *** *** «los datos viven en el ordenador de casa y no salen de
> ahi» *** -- *y **el `.sqlite` es literalmente eso: un fichero en `data/`.** *

## 3. Y hay **seis tablas que esta sesion no habia nombrado**, y hay que decirlo

```
NOMBRADAS YA:  usuario (B13) · lista · lista_linea (B05/B10) · compra (B06) · despensa (B06) · cocina (B07)
*** NUEVAS:   alerta · compra_linea · favorito · invitacion · lista_acceso · preferencia · sesion · visita ***
```

> *** Y no se dice que sean un hueco ni que esten sin hacer: *** *se dice que **aparecen en la lista y no se han
> leido** -- *y que **`ALERTA_TIPOS = ("baja_de", "minimo_90d", "cualquier_bajada")` si se leyo** (ronda 169), *o
> sea: **`alerta` tiene contenido conocido.** *
>
> *** Y **`preferencia` y `visita`** suenan a **lo que B13 pide** («temas y zoom», «evidencia referenciable»): *
> *una preferencia por persona, y un registro de visitas.* *** No se supone: se dice que suenan a eso. ***

## 4. Y B13 queda con **la precondicion medida, y no la que se esperaba**

```
PASO 4 PIDE:  «recorrer cinco recetas, compra y diario»
   y lo medido es:
     - *** la COMPRA esta en Postgres, con 14 tablas ***
     - *** y las RECETAS y el DIARIO estan en SQLite *** -> *o sea: **no se pueden contar con un `SELECT` a Postgres***
       *-- y **contarlas pide abrir el `.sqlite`**, que es **el fichero que B13 pide NO commitear**. *
```

> *** Y **no se ha contado cuantas recetas hay** *** -- *porque **la pregunta era de Postgres y la respuesta esta en
> otro sitio**, *y **decirlo es mejor que inventar un numero.** *
>
> *** Y **lo que si queda claro es una guarda del paso 5**: *** *el `.sqlite` **tiene el diario y las recetas** -- *o
> sea: **es el fichero que no se puede adjuntar a una captura**, *y **el que hay que excluir del manifiesto.** *
>
> *** Que es **exactamente** lo que B13 pide: *** *** «guardar evidencia referenciable sin commitear nutricion
> personal». ***
