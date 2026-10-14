# B14 · **El respaldo no cubre las dos SQLite** -- y el proyecto lo dice en dos sitios que se contradicen

*2026-10-14. **Y sale del propio complemento**: «la prueba debe incluir PostgreSQL, **recetas/diario SQLite**
y permisos/snapshots, **no solo una tabla vacia**».*

## 1. Lo que `respaldar.bat` declara

```
`plataforma/respaldar.bat:5-8` *** «**Es lo UNICO que hay que respaldar.** Gold se regenera solo desde raw
con `ejecutar.bat`, y raw se vuelve a bajar de las webs. *** Pero las cuentas, las listas y los favoritos
solo existen aqui ***: si se pierde este volumen, se pierde todo lo que habeis escrito vosotros.» *** *

*** y el guion: *** *** NO MENCIONA `sqlite` NI `recetas` NI `diario` NI `robocopy` *** *** -> SOLO PostgreSQL ***
```

## 2. *** Y lo que el compose dice **del mismo asunto**, y no coincide ***

```
`plataforma/docker-compose.yml:60-66` *** «**Y AQUI VA EL ESTADO PROPIO, Y ESE SI SE ESCRIBE.** El
`recetas.sqlite` y el `diario.sqlite` *** NO SON CRUDO NI SE RECALCULAN *** -- *** SON LO QUE LA CASA HA
ESCRITO *** --, *y sin este volumen vivian en la capa del contenedor, donde `docker compose down` se los
lleva y *** *** `robocopy data\\raw` NO LOS VE *** ***.» *** *
```

> *** Y **los dos ficheros hablan del respaldo y dicen cosas distintas**: *
> ```
> *** `respaldar.bat` ***  -> *«es **lo unico** que hay que respaldar»*  *-- *refiriendose a PostgreSQL*
> *** `docker-compose.yml` ***  -> *«el `recetas.sqlite` y el `diario.sqlite` **no son crudo ni se
>    recalculan**, son **lo que la casa ha escrito**»*  *-- y **`robocopy data\\raw` no los ve** *
> *** -> y son los dos DATOS DEL USUARIO. El compose lo dice; el guion de respaldo, no lo hace. *** *
> ```

## 3. *** Y con un matiz medido, que cambia el arreglo ***

```
*** en el HOST ***  `data/recetas.sqlite` 53.248 bytes · `data/diario.sqlite` 20.480 bytes *
*** y en el CONTENEDOR ***  *los mismos nombres, pero en *** el volumen `datos_api` *** (`/app/data`)*
*** -> y el compose dice por que NO es un `bind` a `../data` ***: *
   *** «ahi ya escribe el pipeline, y dos escritores sobre el mismo fichero es justo lo que el `ro` de
   arriba evita» *** *
*** -> o sea: *** *** NO son el mismo fichero *** *, *y **respaldar el del host no respalda el que la web usa.** *
```

> *** Y **por eso el arreglo no es un `copy`**: *
> ```
> *** 1) HAY QUE RESPALDAR EL VOLUMEN `datos_api`, no el fichero del host. *** *
> *** 2) Y hay que hacerlo CONSISTENTE: *** *una SQLite **abierta y escribiendose** copiada a mano puede
>    salir **a medias**. *Lo correcto es `sqlite3 ... ".backup"` o `VACUUM INTO`, **que dan una copia
>    coherente aunque haya escrituras** -- *y `copy` no.* *
> *** 3) Y `respaldar.bat` tendria que **decirlo**: *** *su cabecera dice «es lo unico», *y **ya no lo es.** *
> *** -> y NO se ha hecho un `copy` a proposito: *** *un respaldo **que parece un respaldo y no lo es**
>    es peor que no tenerlo, *porque **alguien confiaria en el.** *
> ```
