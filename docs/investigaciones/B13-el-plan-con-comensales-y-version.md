# B13 · **El plan tiene `comensales` y `version` por receta** -- y ya esta montado

*(13 de octubre de 2026. **Y `comensales` es lo que el escalado necesita.**)*

## 1. La ruta, y su resultado

```
`plataforma/api/recetas.py`
  l107  @rutas.get("/plan")            def plan(desde, hasta, ...)          *-- *y **pide el rango***
  l118  *** @rutas.post("/plan", status_code=201) ***   def planificar(datos: PlanIn, usuario = Depends(*** usuario_actual ***))
  l122      recetas.planificar(con, usuario["id"], datos.fecha, datos.receta_id, ...)
  l355  @rutas.delete("/plan")

*** Y LA LLAMADA: *** `POST /api/recetas/plan` con `{"fecha": "2026-10-14", "receta_id": 1|2}`

  *** PLANIFICAR Ensalada -> 201 ***
  *** PLANIFICAR Sopa     -> 201 ***

*** Y EL PLAN, LEIDO: ***  `GET /api/recetas/plan?desde=2026-10-12&hasta=2026-10-18`
{
  "plan": [
    {"fecha": "2026-10-14", *** "comensales": 2 ***, *** "version": 1 ***, "receta_id": 1, "nombre": "Ensalada de ensayo B13"},
    {"fecha": "2026-10-14", *** "comensales": 2 ***, *** "version": 1 ***, "receta_id": 2, "nombre": "Sopa de ensayo B13"}
  ]
}
```

## 2. *** Y `comensales` es **la pieza del escalado**, y estaba en el plan desde el principio**

```
*** `"comensales": 2` ***  *-- *y **no viene de la receta**: *la receta tiene **`raciones: 2`** *
   -> *o sea: **son dos numeros distintos, y el plan guarda el suyo.** *
   *** -> y por eso el escalado es posible: *la receta tiene **su tamano** (2 raciones), *
      *y el plan dice **para cuantos** (2 comensales) -- *y **el puente multiplica.** *
```

> *** Y **es exactamente lo que el encargo pide**: *** *** «los dos puentes: escalado **por comensales**» *** --
> *y **el dato esta en el plan, con su nombre, y **no hay que calcularlo.** *
>
> *** Y **`"version": 1` tambien** *** -- *o sea: **el plan apunta a **una version concreta** de la receta.** *
> *Y **eso es lo que el encargo pide para el diario**: *«con **receta/version/snapshot** y cobertura» -- *y **el
> plan ya lo lleva.** *
>
> *** O sea: **`comensales` y `version` en la misma linea** *** -- *y **son las dos cosas que un puente necesita
> saber para no inventarse nada.** *

## 3. Y **el plan esta montado con las dos recetas del fallo**

```
*** 2026-10-14 ***  ·  *** Ensalada de ensayo B13 ***  ·  *** 2 comensales ***  ·  v1  ·  *** `300 g tomate` ***
*** 2026-10-14 ***  ·  *** Sopa de ensayo B13 ***      ·  *** 2 comensales ***  ·  v1  ·  *** `100 g tomate` ***
```

> *** O sea: **el escenario de la restriccion esta completo por el lado del plan** *** -- *las dos recetas, **el
> mismo dia**, *y **el mismo producto.** *
>
> *** Y **falta el lado de la lista**: *** *`GET /api/listas` dio **`{"listas": []}`**, *y **el puente del plan es
> `GET /api/listas/{lista_id}/desde-el-plan`** -- *o sea: *** *** **necesita una `lista_id`, y no hay ninguna.** *** *
>
> *** Y **la lista «se crea sola»** *** *(`/compra/listas` lo dice) -- *o sea: **al anadir el primer producto.** *
> *Y **`@app.post("/api/listas", 201)`** (main.py:576) **la crea a mano.** *

## 4. Y el estado, con el escenario completo y una lista de distancia

```
RECORRIDO 5 · *** tu restriccion ***
  *** el puente de RECETA ***   -> *** PROBADO Y CORREGIDO ***  *`300.0 g`, `unidad: "g"`, `nota: ""`, `clave: tomate|kg`*
  *** el escenario del PLAN *** -> *** MONTADO ***  *las dos recetas, el mismo dia, con `comensales: 2` y `version: 1`*
  *** y falta: *** *** UNA LISTA *** -- *y `POST /api/listas` la crea (main.py:576)*
     *** -> y despues, `GET /api/listas/{id}/desde-el-plan`, que es la VISTA PREVIA y NO ESCRIBE *** *
```

> *** Y **todo lo que se ha hecho en esta ronda son `POST` y `GET` normales de la aplicacion** *** -- *ninguna
> restauracion, *ninguna base tocada a mano, *y **todo en la base del contenedor:** *la de ensayo.* *
>
> *** Y **el planificado creo DOS filas** *** -- *y **hay que decirlo**, porque **es una escritura**: *`plan` paso de
> **0 a 2 filas**, *en **la cuenta de ensayo `b13-recorrido-2301`**, *y **con recetas de ensayo.** *
>
> *** Y **nada del propietario se toco**: *** *su cuenta no se uso, *y **el plan es de la cuenta de ensayo.** *
