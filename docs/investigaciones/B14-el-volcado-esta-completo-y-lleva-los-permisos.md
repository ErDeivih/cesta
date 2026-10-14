# B14 · **El volcado esta completo, y los permisos van dentro** -- verificado sin restaurar

*2026-10-14. **Y con una falsa alarma mia de por medio, que es la parte que hay que contar.** *

## 1. Lo que el complemento pide

> *** «La prueba debe incluir *** PostgreSQL, recetas/diario SQLite Y PERMISOS/SNAPSHOTS ***, no solo una
> tabla vacia.» ***

*Y la prueba **completa** necesita un destino nuevo (bloqueado por Docker).* **Pero las tres patas se pueden
verificar SIN restaurar**: *el volcado de PostgreSQL **es un fichero de texto** -- *se lee* --, *y el del
recetario **ya se copio y se comprobo** con `integrity_check`.* *

## 2. *** Y el volcado, contado bien, tiene todo ***

```
`data/respaldos/cesta_2026-10-14_1123.sql.gz` *** 432.930 bytes descomprimidos · 3.297 lineas *** *

*** filas por tabla: ***
  *** `sesion`        1020 ***  ·  *** `lista_linea`   346 *** *** <- las MISMAS que casa ***
  *** `lista_acceso`   272 *** *** <- LOS PERMISOS ***  ·  *** `lista`         257 ***
  *** `compra_linea`   137 ***  ·  *** `compra`         97 ***
  *** `usuario`         73 *** *** <- los MISMOS que casa ***  ·  *** `invitacion`     71 ***
  *** `visita`          28 ***  ·  *** `alerta`          6 ***  ·  *** `favorito`       4 ***
  *** `preferencia`      1 *** *** <- el objetivo del 14 ***  ·  *`cocina` 0 · `despensa` 0*

*** TOTAL: 2.312 filas de datos, en 14 tablas *** *
```

> *** Y **coincide con casa**: *`lista_linea` **346 = 346**, *`usuario` **73 = 73** -- *las dos cifras que se
> midieron en la ronda 339 leyendo la base de casa.* *
>
> *** Y **`lista_acceso` tiene 272 filas**: *es **la tabla que acredita quien puede que** sobre cada lista,
> *y **es la tercera pata que el complemento pedia** -- *y **va dentro del volcado.** *

## 3. *** Y la falsa alarma, que es lo que hay que contar ***

```
*** MI PRIMERA MEDICION DIJO: ***  *`usuario` 0 filas · `lista` 0 filas · `lista_linea` 0 filas* ⚠️
*** y era FALSO ***: *mi regex era `COPY ... \([^)]*\)`, *y **`[^)]*` se corta en el primer `)`** -- *
*y **`numeric(10,2)` lo tiene dentro*** -> *la lista de columnas no casaba **nunca**, *y contaba cero **en todas**. *
*** y lo detecte por un detalle que NO cuadraba ***: *
  *** un volcado vacio serian ~15 KB, y el fichero son 432.930 bytes *** *
  *** -> eso me dijo que **el error era mio ANTES de creerme el cero** *** *
```

> *** Y **la leccion es la del proyecto, otra vez, y ahora contra mi**: *** *** **no es lo mismo que la
> sentencia `COPY` ESTE que que TENGA FILAS.** *** *
>
> *** -> *es **la misma forma** que el `findstr /i running` que dejo a Cesta sin respaldo: *comprobar **una
> parte** y leerla como si fuera el todo.* *-- *y esta vez **me la hice a mi mismo, y me la cace midiendo
> otra cosa.** *
>
> *** Y **la version correcta es por lineas**: *buscar `COPY`, *contar hasta la linea `\.`, *y **no intentar
> adivinar la forma de la lista de columnas.** *

## 4. Y el estado de las tres patas

```
*** PostgreSQL ***  *** 2.312 filas en 14 tablas ***, *y **coincide con casa** en las dos cifras comprobables* ✓
*** PERMISOS ***    *** `lista_acceso`: 272 filas *** *** -> van en el volcado *** ✓
*** SQLite ***      *** el recetario: `VACUUM INTO` + `integrity_check: ok` *** ✓
                    *** y el diario: se dice que no existe, y NO se inventa *** ✓
*** -> y lo que sigue faltando es el RECORRIDO en un destino nuevo *** *-- *que necesita que Docker responda*
```
