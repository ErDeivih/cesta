# B14 · **HECHO: el volumen `datos_api:/app/data`** -- con permiso, y sin perder nada

*(13 de octubre de 2026. **Y era el ultimo cabo del encargo, y se cerro con el propietario.**)*

## 1. El permiso, y la respuesta

> *** Se pregunto: *** *** «`/app/data` no tiene montaje ni volumen, asi que las recetas que la web escribe
> viven en la capa del contenedor y no estan en el host. Tu copia es `robocopy data\raw`, y no las cubrira.
> ¿Añado el volumen `datos_api:/app/data`? *** *** Eso recrea `cesta-api`, y por eso te lo pregunto y no lo hago
> solo.» ***
>
> *** Y **el propietario respondio**: *** *** «Si, añade el volumen.» *** *

## 2. Y se hizo **en el orden que se midio**, y ese orden es el que evito perder el dato

```
*** PASO 1 · SACAR EL `/app/data` ACTUAL ***  *-- y no se puede saltar*
   $ docker cp cesta-api-1:/app/data data\debug\app_data_antes_20261013
   *** -> y salio: `recetas.sqlite`, 32768 bytes *** *

*** PASO 2 · EL COMPOSE, CON SU MOTIVO Y A LA VISTA ***
   ```yaml
   cesta-api:
     volumes:
       - ${CESTA_DATOS:-../data}:/datos:ro        # el crudo y el oro, en solo lectura
   +   # **Y AQUI VA EL ESTADO PROPIO, Y ESE SI SE ESCRIBE.** ... sin este volumen vivian **en la capa del
   +   # contenedor**, donde `docker compose down` se los lleva y **`robocopy data\raw` no los ve**.
   +   # *No es un `bind` a `../data` a proposito: ahi ya escribe el pipeline, y dos escritores sobre el
   +   # mismo fichero es justo lo que el `ro` de arriba evita.*
   +   - datos_api:/app/data
   ...
   volumes:
     datos_db:
     datos_caddy:
   + datos_api:
   ```

*** PASO 3 · RECREAR, Y DEVOLVER EL DATO ***  *-- porque **el volumen nace VACIO***
   $ docker compose up -d *** api ***       *-- y NO `cesta-api`: **el servicio se llama `api`** *
   $ docker cp ...app_data_antes_20261013\. cesta-api-1:/app/data
```

> *** Y **hay un detalle que costo un intento y se dice**: *** *** el contenedor es **`cesta-api-1`**, *y el
> **servicio** es *** `api` *** -- *y `docker compose up -d cesta-api` **contesta `no such service`.** *
>
> *** Y **no paso nada malo por eso**: *el primer intento **no recreo**, *y **el `cp` fue al contenedor de
> siempre** -- *asi que **el paso se repitio con el nombre correcto.** *

## 3. Y el resultado, verificado por los dos lados

```
*** EL MONTAJE ***  `docker inspect cesta-api-1 --format "{{json .Mounts}}"`
  [{"Type":"bind","Source":"F:\\aprendizaje\\scrap\\data","Destination":"/datos","Mode":"ro","RW":false},
   *** {"Type":"volume","Name":"cesta_datos_api",
       "Source":"/var/lib/docker/volumes/cesta_datos_api/_data",
       "Destination":"/app/data","Driver":"local","*** RW":true ***}] ***
   *** -> y el `bind` de `/datos` sigue **`ro`**: *no se toco nada de lo que ya estaba bien.* *

*** Y LA APLICACION, VIVA ***
  `recetas: 5`                                       <- *el fichero tiene las cinco*
  *** `ENTRAR tras recrear -> 200` ***                *-- la sesion funciona*
  *** `RECETAS por la API: 5` ***  ['Arroz', 'Ensalada', 'Guiso', 'Pure', 'Sopa' de ensayo B13]
  *** y la web: `HTTP 200` ***
```

> *** O sea: *** *** **el estado propio de la web ya vive en un volumen**, *y **el volumen tiene nombre**
> (`cesta_datos_api`), *y **se puede copiar** sin entrar al contenedor: *
> ```
> docker run --rm -v cesta_datos_api:/de -v "E:\cesta\privado":/a alpine cp -a /de/. /a/
> ```
>
> *** Y **con eso, la copia documentada ya puede cubrir los TRES sitios**: ***
> ```
> *** `data\raw` ***          -> *el `robocopy` que ya estaba*
> *** los dos `.sqlite` del host *** -> *y hay que añadirlos al `robocopy` (no estaban)*
> *** y AHORA el del contenedor ***  -> *** y ahora SE VE, porque esta en un volumen con nombre *** *
> ```

## 4. Y el encargo, con **los dos cabos de B14 cerrados**

```
*** B14 · 4 de 5 ***  -> *y el quinto era **el permiso**, y ya esta:*
  *** el CSRF ***        -> *5 ensayos*
  *** los GET ***        -> *`test_ninguna_ruta_que_muta_es_un_get`*
  *** los LOGS ***       -> *`runs.csv` + *** `CAPAS_INTOCABLES = ("bronze", "gold")` *** *
  *** LAS COPIAS ***     -> *** el volumen aplicado, y los tres sitios ya son copiables *** *
  *** y lo que queda *** -> *** añadir los dos `.sqlite` del host al `robocopy` semanal *** *-- *y eso es
     una linea de un guion que el propietario ejecuta, no una accion de la maquina.* *
```

> *** Y **el cambio esta commiteado**, *con **su motivo escrito en el compose** y **en la voz del proyecto**:
> *«sin este volumen vivian en la capa del contenedor, **donde `docker compose down` se los lleva** y
> **`robocopy data\raw` no los ve`». *
>
> *** Y **queda dicho lo que se hizo y lo que se toco**: *** *un `docker cp` de salida, *una linea en el
> `docker-compose.yml`, *un `docker cp` de vuelta, *y **un contenedor recreado.** *Y **nada del propietario
> se perdio, y esta medido: las 5 recetas siguen, y la web responde 200.** *
