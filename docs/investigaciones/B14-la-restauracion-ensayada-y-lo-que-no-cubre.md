# B14 · **La restauracion, ensayada en una base nueva y desechable** -- y lo que aun NO cubre

*14/10/2026. **Primera vez que se ejerce**, y el complemento decia de ella: *** «se ensaya en bases NUEVAS
desechables con guardas: nunca casa 5432, facylf 5433 ni pruebas compartidas 5434. **No pidas autorizacion
para sobrescribirlas porque no es necesario ni esta permitido**.» *** *

---

## 1. *** Y corre entera, con las guardas delante ***

```
*** destino ***   *`cesta-restauro-ee9912c20f1b`, puerto **52679** (libre), etiqueta `cesta.ensayo=restauracion`*
*** y NO se toca ***  *** 5432, 5433, 5434 *** *
*** guardas, en este orden *** *
   *-- *nombre con prefijo propio · puerto **por numero** y no por confianza · DSN comprobado*
   *-- *** `arranco: Up Less than a second` ***  *** -> la guarda del `Up` (un id de `docker run -d` no es
      un contenedor corriendo)*
   *-- *** `la base esta vacia: se puede restaurar aqui` ***  *-> `information_schema.tables` filtrando por `public`*
*** el restaurado ***  *`cesta_2026-10-14_1123.sql.gz` -> **432.937 bytes** descomprimidos* ✓
*** Y EL CONTENIDO, VERIFICADO ***  *** `lista_linea 346 · usuario 73 · lista 257 · compra 97` *** *
   *** -> EXACTAMENTE los mismos numeros que se contaron en el fichero *** ✓✓✓
*** y se limpia solo ***  *`limpiado (era suyo)` -- *porque **lleva la etiqueta*** ✓
*** y despues: ***  *`docker ps -a --filter label=…` -> **vacio*** ✓
```

## 2. *** Y el cuarto fallo que el propio ensayo se encontro a si mismo ***

```
*** el contenedor dijo ***  *** `Up Less than a second` ***  *-- *o sea **arrancado***
*** y `psycopg.connect` revento ***  *** «server closed the connection unexpectedly» *** ⚠️
*** -> porque *** *** `Up` es el CONTENEDOR y no la BASE *** *
   *-- *PostgreSQL **tarda un poco mas** en aceptar conexiones, *y en ese hueco **la puerta esta abierta
   y nadie atiende***
*** -> y el arreglo: *** *** `_conecta` espera a la BASE ***, *reintentando **la conexion** -- *
   *no un `SELECT` posterior, que es lo que hacia*
```

> *** Y van **cuatro fallos que este ensayo destapa en si mismo**: *el `Created` que no se comprobaba, *el
> `docker rm -f` que se bloquea, *el `Up` que no se miraba, *y ahora **la conexion antes de que la base
> atienda.** *Todos del mismo tipo: **mirar una cosa y creer que es otra.** *

## 3. *** Y LO QUE AUN NO CUBRE, que hay que decir ***

```
*** el complemento pide: ***  *** «PostgreSQL, recetas/diario SQLite Y PERMISOS/SNAPSHOTS, no solo una
   tabla vacia» *** *
*** LO QUE ESTE ENSAYO HACE ***  *** PostgreSQL *** ✓  *-- *14 tablas, y con los recuentos comparados*
*** LO QUE **NO** HACE TODAVIA *** ⚠️ *
   *** 1) LAS DOS SQLITE ***  *-- *se **respaldan** (con `VACUUM INTO` e `integrity_check: ok`), *
      *pero **no se restauran** en el ensayo: *el ensayo solo crea un contenedor `postgres`*
      *-- *y `recetas.sqlite` vive en **otro volumen** (`datos_api`, que monta la API)*
   *** 2) LOS PERMISOS ***  *-- *van **dentro del volcado** (`lista_acceso`, 272 filas, verificado), *
      *pero el ensayo **no comprueba que se puedan ejercer** despues de restaurar*
*** -> o sea: **dos de las tres patas estan RESPALDADAS y verificadas en el fichero, pero no RESTAURADAS
   y ejercidas** *** ⚠️ *-- *y decirlo es parte del resultado*
```

## 4. Y lo que haria falta para cerrarlas

```
*** LA SQLITE ***  *-- *el ensayo tendria que **crear tambien un volumen desechable**, *
   *copiar ahi `recetas_<sello>.sqlite`, *y **abrirlo y comparar** (`receta`, `version`, `plan`)*
   *-- *y el diario: *si no existe, **se dice** -- *no se inventa*
*** LOS PERMISOS ***  *-- *despues de restaurar, **preguntar por `lista_acceso`** y comprobar que una
   cuenta **sin papel** recibe **404** y **con papel** recibe **200*** *
   *-- *que es la medicion que ya se hizo **en vivo** contra la app (`401 sin sesion · 404 ajena · 200
   la mia`), *pero **no dentro del ensayo de restauracion***
```

## 5. Y el resto del complemento, para que esto no se lea solo

```
*** (1) LOS ENVASES ***      *** hecho en los dos puentes ***, *medido en vivo: plan 3.800 g -> `cantidad = 4`
                             · receta 2.800 g -> `cantidad = 3`* ✓✓
*** (2) EL SIN CATALOGO ***   *entra como pendiente, `envases=None`, *y la nota lo dice* ✓
*** (3) LIDL ***             *las tres salidas mudas registran; *y el ciclo real: **79 filas · 0 errores ·
                             ok=True** · `LastTaskResult: 0`* ✓
*** (4) LA RESTAURACION ***  *** PostgreSQL hecho y verificado ***; *las SQLite y los permisos, **pendientes
                             de ejercer** -- *el respaldo y los permisos **si** estan en la copia* ✓
*** la ingesta ***           *viva, sin duplicar, y terminada* ✓
```
