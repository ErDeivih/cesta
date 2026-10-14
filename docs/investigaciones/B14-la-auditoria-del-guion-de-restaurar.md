# B14 · **La auditoría del guion de restaurar**, antes de ejecutar nada

*2026-10-14. **Y es el primer paso que el complemento exige**: «no ejecutar el guion actual a ciegas:
auditar sus eliminaciones y subprocesos primero».*

## 1. Lo que hay, y donde

```
*** LOS GUIONES DE COPIA ***  `git grep -ln "pg_dump\|restaurar\|robocopy"` -> *** solo DOS sitios *** :
  `docs/OPERACION.md`  *-- *la documentacion*
  *** `plataforma/respaldar.bat` ***  *-- *** 78 lineas, y **NO hay ningun guion de restaurar aparte** *** *
*** `git grep -ln "pg_restore"` *** *** -> NADA *** *
*** -> o sea: *** *** el modo RESTAURAR vive DENTRO de `respaldar.bat` *** *
```

## 2. *** Y sus eliminaciones, que era lo que habia que auditar ***

```
l33  *** «ATENCION: esto SOBRESCRIBE las listas y cuentas que haya ahora.» *** *
l35  *** `set /p CONFIRMA="Escribe SI para continuar"` *** *** -> TIENE GUARDA: pide confirmacion ***
l42  *** `docker compose exec -T db psql -U cesta -d cesta -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public"` *** *
l43  *** `powershell ... GZipStream ...` *** *-- *descomprime el fichero que se le pasa en `%~2`*
l62  *** `docker compose exec -T db pg_dump -U cesta -d cesta --clean --if-exists > "%FICHERO%"` *** *-- *el modo RESPALDAR*
l65 · l73 · l78  *** `del "%FICHERO%"` *** *-- *borra la copia en tres caminos*
l85  *** `forfiles /p "%DESTINO%" /m *.sql.gz /d -30 /c "cmd /c del @path"` *** *-- *rota las copias de mas de 30 dias*
```

## 3. *** Y a que base apunta ese `db`, que es la pregunta que decide todo ***

```
`plataforma/docker-compose.yml`, servicio *** `db` *** :
  image: postgres:16-alpine
  environment:  POSTGRES_USER: cesta · *** POSTGRES_DB: cesta *** · PGDATA: /var/lib/postgresql/data/pgdata
  volumes:      *** `datos_db:/var/lib/postgresql/data` *** *
  *** y publica `127.0.0.1:5432` *** *
*** -> `db` es *** LA BASE DE CASA *** *** -- *la que el encargo protege con nombre propio*
```

## 4. *** La conclusion, y es la que hace falta ***

> *** El guion **sí tiene guarda** -- pide escribir «SI» --, *y **el `DROP` es deliberado**: *es el modo
> «restaurar», y **sobrescribe casa a proposito.** *
>
> *** Y por eso *** *** **el guion actual NO SIRVE para el ensayo que el complemento pide** *** *: *
> ```
> *** 1) esta CABLEADO a `db` ***  *-- *no acepta otro destino: *`docker compose exec -T db` es literal*
> *** 2) y su primer acto es `DROP SCHEMA public CASCADE` ***  *** -> sobre CASA *** *
> *** 3) y `db` es la base cuyo volumen es `datos_db`, la de casa *** *
> *** -> o sea: **ejecutarlo «para probar» es exactamente la restauracion destructiva que el encargo
>    prohibe**, *y **por eso el complemento manda auditar antes de ejecutar.** *
> ```
>
> *** Y **el ensayo, entonces, no puede ser «correr el guion»**: *tiene que ser *** **un destino nuevo con
> su propio DSN** ***, *construido por el ensayo, *con **nombre unico**, **puerto libre**, **etiqueta de
> propiedad**, *y **verificacion de identidad del destino ANTES de cualquier DDL** -- *que es *palabra por
> palabra* lo que el complemento pide.* *

## 5. Y lo que el ensayo tiene que cubrir, segun el complemento

```
*** «La prueba debe incluir PostgreSQL, recetas/diario SQLite y permisos/snapshots, NO SOLO UNA TABLA VACIA.» *** *
  *** PostgreSQL ***      -> *la copia de `datos_db` (listas, compra, usuarios, preferencias)*
  *** SQLite ***          -> *** `data/recetas.sqlite` Y `data/diario.sqlite` *** *-- *las DOS*
  *** permisos/snapshots *** -> *y **lo que acredita quien puede que**: *los `permiso`/`acceso` de las listas*
*** y «limpiar solo recursos creados y acreditados como propios» ***  *-- *o sea: *el ensayo **borra su
   contenedor y su volumen**, *y **nada mas**; *y **lo que no pueda acreditar como suyo, no lo toca.** *
```
