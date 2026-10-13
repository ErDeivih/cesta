# B13 · **El puente del plan tiene sus DOS rutas** -- y para mirarlo hacen falta **una lista y algo planeado**

*(13 de octubre de 2026. **Y sale una diferencia entre el fichero del contenedor y el del host, que hay que decir.**)*

## 1. Y los dos puentes tienen cuatro rutas, no dos

```
`plataforma/api/main.py`:

  l1458  *** @app.get("/api/listas/{lista_id}/desde-el-plan") ***             *** <- LA VISTA PREVIA DEL PLAN ***
  l1624  *** @app.post("/api/listas/{lista_id}/desde-el-plan", 201) ***        *-- y la accion*
  l1679  @app.get("/api/listas/{lista_id}/*** desde-la-compra ***")            *-- y **un tercero**: desde la compra*
  l1719  @app.post("/api/listas/{lista_id}/desde-la-compra", 201)
  y `recetas.py:199/235`: *** `/api/recetas/{receta_id}/a-la-lista` ***        *-- **el puente de la receta***
```

> *** O sea: **el «puente plan→lista» es de la LISTA, y no del plan** *** -- *toma **`lista_id`**, *y **el plan
> entra en ella.** *
>
> *** Y **hay **tres** puentes, no dos** *** -- *receta, plan, y **`desde-la-compra`** -- *y **el encargo nombra
> dos**, *y **el tercero esta ahi.** *
>
> *** Y **el de la receta tambien es de la lista por dentro** *** -- *`recetas.py:235` **resuelve la lista** y luego
> **llama a lo mismo.** *

## 2. Y para mirar la previa del plan **hacen falta dos cosas que la cuenta no tiene**

```
$ `GET /api/listas`   -> *** {"listas": []} ***      *-- la cuenta **no tiene listas** *
$ `select receta_id, fecha from plan`  -> *** [] ***  *-- y **el plan esta VACIO** *
```

> *** O sea: *** *** la previa del plan **no se puede mirar todavia**, *y **no por un fallo: por falta de datos.** *
>
> *** Y **`/compra/listas` ya lo decia**: *** *«**No tienes ninguna lista** ... se apunta en la lista de casa,
> **que se crea sola**»* (ronda 233). *O sea: **la lista existe cuando hay algo que meter.** *
>
> *** Y **el plan** *** -- *`core/recetas.py:253 planificar` y `l267 plan(desde, hasta)` *-- *y **para que tenga
> filas, hay que planificar una receta en una fecha.** *
>
> *** Y **entonces la previa del plan necesita, por orden**: *** *** (1) planificar las recetas, *(2) **la lista**,
> *(3) **y la previa.** *

## 3. Y sale **una diferencia que hay que decir, sin conclusion**

```
*** EL HOST: *** `data/recetas.sqlite` -- *y **B13 lo midio con 42 recetas y 42 filas de plan** *
*** EL CONTENEDOR: *** `/app/data/recetas.sqlite` -- *y **ahora tiene 2 recetas (las mias) y 0 de plan** *
```

> *** Y **hay tres explicaciones, y ninguna se elige**: ***
> ```
> a) *** el contenedor NO monta el `data/` del host *** -- *y tiene **su propia copia** *
> b) *** monta otro `data/` *** -- *por ejemplo, **uno creado al arrancar** *
> c) *** o el fichero del host que yo medi es otro *** *-- *y **el del contenedor esta montado, pero en otra ruta** *
> ```
>
> *** Y **lo que SI se puede decir, medido**: ***
> ```
> *** `docker exec cesta-api-1 ls -la /app/data/*.sqlite` ***  -> *`recetas.sqlite ... Oct 13 21:08`*
>    *-- *o sea: **el fichero del contenedor ES el que se escribio** (mi receta, a las 21:08)*
> *** y el host tiene `data/recetas.sqlite` con 42 recetas ***  *-- *medido en B13, **y sigue ahi** *
> ```
>
> *** O sea: **los dos existen, y **el contenedor no ve las 42** *** -- *y **eso significa que **el servicio
> sirve 2 recetas donde el host tiene 42.** *
>
> *** *** Y ESO ES UN HALLAZGO DE VERDAD, Y NO SE DECLARA COMO FALLO TODAVIA *** *** -- *porque **falta la
> comprobacion que lo decide**, *y es **una**: *mirar **los `volumes` del contenedor** *
> ```
> docker inspect cesta-api-1 --format '{{json .Mounts}}'
> ```
> *** -> y con eso se sabe **si monta `data/` del host, o uno suyo.** *
