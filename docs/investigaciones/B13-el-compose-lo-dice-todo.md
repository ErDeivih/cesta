# B13 · **El compose lo dice todo**: `/datos` en `ro`, y **`/app/data` sin montaje ni volumen** ⚠️

*(13 de octubre de 2026. **Y la consecuencia importa para B14, y es de las que el propietario nota.**)*

## 1. Los montajes, literales (`plataforma/docker-compose.yml`)

```yaml
l7   # *** «Los datos se quedan en tu PC. *** Lo unico que sale de aqui es lo qu[e...]» ***

l22  volumes:
l23    - *** datos_db ***:/var/lib/postgresql/data          *-- *** un VOLUMEN NOMBRADO *** (Postgres)*

l52  CESTA_GOLD: /datos/gold
l55  volumes:
l59    - *** ${CESTA_DATOS:-../data}:/datos:ro ***           *-- *** el `data/` del host, EN RO *** *

l118   - ./web/dist:/srv:ro
l131   - ./web/aprende:/aprende:ro
l132   - ./Caddyfile:/etc/caddy/Caddyfile:ro
l133   - *** datos_caddy ***:/data                           *-- y otro volumen nombrado*

l135 volumes:
l136   *** datos_db: ***
l137   *** datos_caddy: ***

*** Y NO HAY NINGUNA LINEA QUE MONTE NI DECLARE `/app/data` ***  ⚠️
```

## 2. Y de ahi salen **tres conclusiones**, y las tres medidas

```
*** 1) EL MONTAJE ES DELIBERADO Y CON NOMBRE PROPIO: ***
   `${CESTA_DATOS:-../data}:/datos:ro`
   -> *la **ruta del host es configurable** (`CESTA_DATOS`), *y **por defecto `../data`** *
   -> *** y `ro` esta escrito: el contenedor NO escribe el crudo. *** *
   *** y ese `ro` es LA MISMA FORMA que todo el proyecto: LA REGLA ESTA EN EL CAMINO, no en el cuidado. ***

*** 2) Y POR ESO HAY DOS `recetas.sqlite`: ***
   -> *el del host (***42 recetas, 42 del plan***) esta en *** `/datos` ***, *y **la API lo LEE** *
   -> *y `/app/data/recetas.sqlite` (**2 recetas, 0 del plan**) es *** DENTRO del contenedor *** *
   *** y son ficheros distintos, y eso ya esta medido. ***

*** 3) Y `/app/data` NO TIENE NI MONTAJE NI VOLUMEN NOMBRADO ***  ⚠️
   -> *o sea: *** VIVE EN LA CAPA DE ESCRITURA DEL CONTENEDOR *** *
   -> *** y por tanto: `docker compose down` SIN `-v` lo borra, y `docker compose up` lo deja vacio. *** *
```

## 3. *** Y ESO ES UNA CONSECUENCIA DE VERDAD, Y ES LA PREGUNTA DE B14 ***

> *** B14 pide, literal: *** *** «copias de PostgreSQL, **SQLite privados** y metadatos; *** *** restauracion de
> LOS TRES, hashes, retencion y verificacion» *** -- *y **B14 ya midio** que `OPERACION.md:459` dice:
> *«el crudo es lo unico irrecuperable, *y un `robocopy` semanal de `data\raw` a un disco externo **cubre el riesgo
> entero**». *
>
> *** Y **ahora se sabe donde estan los dos `.sqlite` privados**: ***
> ```
> *** `data/recetas.sqlite` del HOST ***      -> *esta en `data/`, *y **`robocopy data\raw` NO lo copia** *
> *** `data/diario.sqlite` del HOST ***        -> *igual*
> *** Y EL DEL CONTENEDOR (`/app/data`) ***     -> *** y ese no esta en el host EN ABSOLUTO ***  ⚠️
> ```
>
> *** O sea: *** *** **hay un `recetas.sqlite` que vive solo dentro del contenedor**, *y **cuyo contenido**
> *(las 2 recetas de ensayo) **no esta en el host.** *
>
> *** Y **que sea de ensayo da igual** *** -- *lo que importa es **la propiedad**: *si **alguien usa la web**,
> **sus recetas van ahi**, *y **no al `data/` que se copia.** *
>
> *** *** Y ESO ES EXACTAMENTE LO QUE B14 PREGUNTABA, Y AHORA TIENE UNA RESPUESTA MEDIDA: *** *** *la copia
> documentada (`robocopy data\raw`) **no cubre** ni los dos `.sqlite` del host **ni**, desde luego, **el del
> contenedor.** *

## 4. Y **no se declara fallo**, y el motivo esta escrito

```
*** LO QUE SE PUEDE DECIR: ***
  1. el montaje de `/datos` es **`ro` y deliberado** *-- y *«los datos se quedan en tu PC» (l7)*
  2. `/app/data` **no tiene montaje ni volumen nombrado**
  3. *y por tanto **su contenido vive en la capa del contenedor** *

*** LO QUE NO SE DECLARA: ***
  *** no se declara «los datos se pierden» ***  *-- *porque **la comprobacion que lo decidiria es `docker compose
  down`**, *y **eso es una accion destructiva** que **el encargo prohibe**: *«no restaures sobre bases existentes»
  y **«preserva cambios ajenos».** *
  *** y NO se ejecuta: se LEE el compose, y se dice lo que dice. *** *
```

> *** Y **es un buen sitio para parar, y con una pregunta concreta para el propietario**: ***
> *** *** *** «¿las recetas y el diario de la casa deben vivir en el host (y copiarse), o dentro del contenedor?» *** *** *
> *-- *porque **la respuesta cambia**: *si **deben vivir en el host**, *falta **un montaje**; *y si **vale el
> contenedor**, *entonces **la copia tiene que sacarlas de ahi**, *y **`robocopy data\raw` no puede.** *
>
> *** Y **B14 ya tenia esa pregunta abierta** *** -- *«que se copia al disco externo» -- *y **ahora se sabe que hay
> una tercera cosa que copiar, y que no esta en `data\`.** *

## 5. Y el estado de B13, con la restriccion probada y el mapa entero

```
RECORRIDO 5 · *** tu restriccion ***  -> *** el puente de RECETA esta PROBADO, y esta CORREGIDO ***
   *`300.0 g`, `unidad: "g"`, `nota: ""`, `clave: "tomate|kg"` en las dos -> se consolidan a 400 g*
RECORRIDO 5b · *** el puente del PLAN ***  -> *sus dos rutas localizadas; y **la base del contenedor no tiene
   ni lista ni plan**, *asi que **hay que planificar primero.** *
*** y hay un TERCER puente: `/api/listas/{id}/desde-la-compra` ***  *-- y el encargo nombra dos.*
*** Y EL MAPA DE ALMACENES, ENTERO: ***
   *** Postgres *** (`cesta-db-1`, volumen `datos_db`)  -> *listas, usuarios, compras*
   *** `data/` del HOST *** (`/datos:ro`)                -> *crudo, oro, y dos `.sqlite` privados*
   *** `/app/data` del CONTENEDOR *** (sin montaje)       -> *y **el `recetas.sqlite` que la API escribe** *
```
