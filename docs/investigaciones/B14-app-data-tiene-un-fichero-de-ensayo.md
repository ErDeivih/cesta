# B14 · **`/app/data` tiene UN fichero, y es de ensayo**: la decision se puede tomar hoy sin perder nada

*(13 de octubre de 2026. **Y es la comprobacion que convierte la recomendacion en algo aplicable.**)*

## 1. Lo que hay, medido

```
$ docker exec cesta-api-1 ls -la /app/data/
total 40
drwxr-xr-x 2 cesta cesta  4096 Oct 13 21:18 .
drwxr-xr-x 1 cesta root   4096 Oct 13 21:07 ..
-rw-r--r-- 1 cesta cesta *** 32768 *** Oct 13 21:18 *** recetas.sqlite ***
```

> *** O sea: ***
> ```
> *** UN SOLO FICHERO: `recetas.sqlite`, 32 KB, y escrito a las 21:18 ***  *-- o sea: **por mi, hoy.** *
> *** Y NO HAY `diario.sqlite` ***  ⚠️ *
> ```

## 2. Y las dos consecuencias, y las dos importan

```
*** 1) EL CONTENEDOR NO TIENE NINGUN DATO REAL ***
   -> *`recetas.sqlite` tiene **5 recetas**, *y **las cinco son de ensayo** (`Ensalada`, `Sopa`, `Guiso`,
      `Pure`, `Arroz` de ensayo B13) -- *y **las cree yo en esta sesion.** *
   *** -> o sea: **aplicar la recomendacion (B) HOY no pierde nada.** *

*** 2) Y NO HAY `diario.sqlite` ***  ⚠️
   -> *y `core/diario.py:23` dice `BASE = RAIZ/"data"/"diario.sqlite"`, *y dentro del contenedor `RAIZ` seria `/app` *
   -> *** -> o sea: **el diario del contenedor NUNCA SE HA ESCRITO.** *Nadie ha usado la web para anotar comidas. *
   -> *y **eso es coherente con `/app/data` teniendo una sola cosa, y con que la tuviera yo.** *
```

> *** O sea: *** *** **hoy, `/app/data` es solo mi material de ensayo.** *
>
> *** Y **eso hace la decision facil de tomar y de justificar**: *la recomendacion (B) **no borra nada real**, *
> *porque **no hay nada real.** *
>
> *** *** Y EL DIA QUE ALGUIEN USE LA WEB, SI *** *** -- *y **entonces sus recetas irian ahi**, *y
> **`docker compose down` las borraria.** *

## 3. Y la decision, entonces, **con su razon y su orden**

```
*** LO QUE RECOMIENDO, y por que: ***

  *** A) LA COPIA LLEVA TRES COSAS: ***  *`data\raw` (lo observado), *y **los dos `.sqlite` privados** *
     *(porque **tampoco se recalculan**, *y **el criterio del manual ya los incluia.**)*

  *** B) Y `/app/data` DEJA DE SER INVISIBLE: ***  *un volumen nombrado (`datos_api:/app/data`), *
     *o un `bind` a **otra carpeta** (`.../data/privado:/app/data`), *para que **el estado propio viva
     donde se copia**, *y **sin dos escritores** sobre el mismo fichero.*

  *** Y EL ORDEN, si se aplica: ***
     1. *sacar **el `/app/data` actual** del contenedor*  *(hoy: **sin valor**, pero **el paso se hace igual**)*
     2. *cambiar el `docker-compose.yml`*
     3. *`docker compose up -d cesta-api`*  *** y recrear es lo que hace falta, y por eso el orden manda. *** *
```

> *** Y **no se aplica**, y el motivo es de metodo: *** *** el cambio **recrea un contenedor**, *y **el encargo
> dice «preserva cambios ajenos» y «no restaures sobre bases existentes».** *
>
> *** Y **la parte que si se puede hacer sola ya esta hecha**: *** *** medir **que hay dentro** -- *y **son 5
> recetas de ensayo y ningun diario.** *
>
> *** O sea: **la recomendacion queda con su diff, su orden, y la medida de lo que hay** *** -- *y **lo unico que
> falta es que el propietario diga «adelante», porque recrear un contenedor es suyo.** *

## 4. Y el estado de B14, con las copias cerradas en todo lo que no es una decision

```
*** B14 · 3 de 5 · y la copia DECIDIDA ***
  *** el CSRF ***        -> *** 5 ensayos, medidos *** (`test_fase2_f04_csrf.py`)
  *** los GET ***        -> *** `test_ninguna_ruta_que_muta_es_un_get` ***
  *** los LOGS ***       -> *`data/runs.csv`, 6 columnas, **sin sitio para un secreto**; *y **la rotacion no se ha visto***
  *** LAS COPIAS ***     -> *** y ahora con las TRES piezas medidas: ***
     *`data\raw` (copiado) · los dos `.sqlite` del host (no copiados) · y `/app/data` del contenedor (invisible)*
     *** + el diff, el orden, y la medida de lo que hay dentro (5 recetas de ensayo, y ningun diario) *** *
  *** y lo que queda *** -> *** una palabra del propietario, porque recrear un contenedor es suyo. *** *
```

> *** Y **es el mejor estado posible para una decision delegada pero no ejecutable**: *** *** la recomendacion
> **esta escrita, con su diff, su orden y su riesgo**, *y **lo unico que falta no es informacion: es permiso.** *
