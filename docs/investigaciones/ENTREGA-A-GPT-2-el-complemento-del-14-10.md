# ENTREGA A GPT · **2ª parte: el complemento del 14/10** (rondas 322–353)

*Y **la primera parte** esta en [ENTREGA-A-GPT-resumen-de-la-sesion.md](ENTREGA-A-GPT-resumen-de-la-sesion.md),
que cubre hasta la ronda 322. Esto es lo que vino despues: **el propietario reviso el cierre, corrigio
cuatro puntos, y aqui esta lo que se hizo con ellos.***

---

## 0. Lo que el propietario corrigio, y por que tenia razon

*Su revision (`docs/SUPERAPP-REANUDAR-DEEPSEEK-2026-10-14.md`, 155 lineas) dice cuatro cosas, **y las
cuatro eran ciertas**:*

```
*** 1) «se calculan dos envases y se persiste cantidad 1, y "dos envases" queda solo en la nota» *** *
   *** -> CIERTO ***: *`main.py:1669` pasaba `1` fijo, y `recetas.py:379` igual*
*** 2) «el ingrediente sin catalogo se queda FUERA de la lista, asi que `sin_catalogo` prueba rechazo,
      no conservacion» *** *** -> CIERTO ***: *habia un `continue` que lo tiraba*
*** 3) «Lidl puede fallar sin fila en `runs.csv`» *** *** -> CIERTO ***: *y eran TRES caminos mudos, no uno*
*** 4) «restaurar en una base NUEVA y desechable esta contemplado, y no necesita sobrescribir ninguna
      existente» *** *** -> CIERTO ***: *yo lo habia declarado bloqueado por el encargo, y no lo estaba*
*** y una quinta, que es la que mas importa: *** *
*** «las siete pruebas actuales de ambos puentes pasan, pero NO DETECTAN el fallo de los dos envases» *** *
   *** -> CIERTO, y peor ***: *dos de ellas **afirmaban que la cantidad correcta es `1`***
```

---

## 1. *** Los seis puntos, con su evidencia ***

### (1) Los envases

```
*** DONDE ***      `main.py` (plan->lista) y `recetas.py` (receta->lista) -- *** `1` fijo *** *
*** EL ARREGLO *** *** `uno.envases or 1` *** y *** `ln.envases or 1` *** *
*** Y POR QUE `1` PARECIA BIEN *** *`main.py:1631` lo decia por escrito: *«poner 400 en `cantidad` diria
   «400 envases»… se anade UNA unidad»*. *** El problema era cierto; la salida, falsa *** *
   *-- *y **la unidad correcta ya estaba en el sistema**: *`previa_compra` *** «cuenta los envases enteros» *** *
*** Y CUANDO NO SE SABE *** *`lista_linea.cantidad` es *** `integer NOT NULL` ***, asi que «no se sabe» no
   cabe: queda `1` -- *** pero la nota lo dice *** («no se sabe el tamano del envase»), *y asi ese `1`
   **no afirma nada** *
*** LAS REGRESIONES *** *** 7 -> 12 ensayos ***, y *** revertido el arreglo: 6 FALLAN *** *
   1,4 kg en envase de 1 kg -> *** DOS *** · 2,4 kg -> *** TRES *** · tamano desconocido -> la nota lo dice,
   *en los DOS puentes* · y la asercion de cantidad que **faltaba** en el ensayo que ya tenia el caso montado
```

### (2) El ingrediente sin catalogo

```
*** DONDE ***  `main.py`, el `continue` que lo tiraba *
*** SU MOTIVO, ESCRITO ***  *«la base lo rechazaba con un 500»* *** -- y dejo de ser cierto *** *
   *-- *la migracion *** `014_la_linea_sin_destino.sql` *** quito la restriccion `linea_con_destino`, y
   *dice por que*: *** «la restriccion protegia la comparacion y PROHIBIA LA LISTA: quien no encontraba el
   producto en el catalogo no podia apuntarlo, y acababa apuntandolo en otro sitio» *** *
*** EL ARREGLO ***  *`pendiente = ...` y **la linea ENTRA**, con su nombre y su cantidad, y la nota dice
   *** «pendiente de identificar (sin catalogo)» *** *
*** Y LA PREVIA, QUE MENTIA AL REVES ***  *filtraba por «la tabla lo prohibe (`linea_con_destino`)» y
   contaba *** `total: 0` *** mientras el POST apuntaba 1* *** -> prometer de menos es mentir igual que
   prometer de mas *** -- *y ahora **los dos numeros dicen 1***
*** Y EL ENSAYO ***  *** `test_un_ingrediente_escrito_a_mano_no_entra_y_se_dice` -> INVERTIDO *** *
   *-- *decia «**Medido el 13 de octubre de 2026**… la tabla exige `linea_con_destino`»* *-- *y **su ejemplo
   era la sal**, que es **literalmente el caso que el complemento nombra** *
```

### (2b) El orden del tuple -- *** que salio al seguir la pista ***

```
*** `main.py`, al anadir favoritos *** *
  `ya_en_la_lista = {(x.get("grupo_id"), x.get("producto_id")) ...}`  *-- el orden es `(grupo, producto)`*
  `if (grupo_id, None) in ya_en_la_lista:`      *** -> CORRECTO *** ✓
  `if (producto_id, None) in ya_en_la_lista:`   *** -> ¡EL ORDEN CAMBIADO! *** ⚠️
     *-- *una linea con producto y sin grupo guarda *** `(None, producto_id)` ***, *y se buscaba
     `(producto_id, None)`* *** -> NO COINCIDE CON NADA *** *
*** -> la comprobacion de «ya esta» NO ENCONTRABA NUNCA UN PRODUCTO, y el mismo se podia anadir DOS VECES *** *
*** y el comentario de tres lineas mas arriba promete: *** *** «pulsar dos veces el mismo favorito NO PUEDE
   dejar dos lineas» *** *
*** Y LA REGRESION: ***  *y **la puse primero en la ruta que no era** (`desde-favoritos` tiene **su propio**
   dedupe y **no pasa por `_del_plan`**), *asi que **pasaba con y sin el arreglo**; *movida a
   `test_la_previa_del_plan.py`, *** ahi SI falla sin el arreglo *** *
```

### (3) El `dedupe` por nombre

```
*** DONDE ***  `_del_plan`: *** `ya = {str(x.get("nombre_visto") or "").lower() ...}` *** *
*** Y SU DOCSTRING DECIA OTRA COSA ***  *«se consolida por *** `(nombre, unidad)` ***»* -- *y guardaba
   **el nombre, sin la unidad** *
*** EL ARREGLO ***  *** `_ya_estaba(ya, destino, nombre)` ***, con la regla que **salio de los ensayos**: *
  *** se compara por DESTINO *** *-- `(grupo_id, producto_id)`*
  *** y por NOMBRE *** *** solo si alguno de los dos es una pendiente sin destino *** *
     *-- *una pendiente **no tiene mas identidad que su nombre**, *y negar que esta seria **prometer una
     linea que el usuario ya ve***
  *** y entre dos lineas CON destino NO se mira el nombre *** *
     *-- *dos marcas distintas **son dos compras distintas**, *y fundirlas era el fallo*
*** Y UN PROBLEMA QUE INTRODUJE Y CACE ***  *`(None, None)` es la identidad de **todas** las pendientes, *asi
   que **dos pendientes colisionaban**; *los tres fallos de la primera pasada me lo dijeron, y de ahi salio
   el respaldo por nombre*
*** Y EL ENSAYO DE CONTRATO ***  *** cambia de nombres a identidad ***, *y su docstring decia por que el
   fallo **parecia imposible**: *** «el nombre ERA el mecanismo» *** *
```

### (4) La identidad de la receta -- *** y era PEOR ***

```
*** DONDE ***  `recetas.py`: *** `int(ln.producto_id) if (ln.producto_id or "").isdigit() else None` *** *
*** LO QUE EL COMPLEMENTO DECIA ***  *«`dia:fixture` queda `None`… no degradar exacto a familia»*
*** LO QUE SE MIDIO ***  *** NO ES «dia:fixture»: ES TODOS *** *
   *-- *los ids del catalogo son *** `fuente:id` *** -- `dia:1234`, `carrefour:5678` --, y *** ninguno es
   `isdigit()` ***, *asi que la linea salia con `producto_id = None` *** SIEMPRE *** *
   *-- *y `lista_linea.producto_id` es *** `text` ***: *el `int()` **no era una conversion, era una perdida**.
   *(Y la columna de al lado, `grupo_id`, **si** es `bigint`: ahi el entero es lo correcto.)*
*** -> el puente de receta NO GUARDABA EL ARTICULO ELEGIDO NUNCA ***; *solo el grupo, *y **una familia no es
   lo que la persona eligio** *
*** LA REGRESION ***  *producto exacto **sin** grupo, y **con** grupo: los dos conservan `"dia:fixture"`*
   *-- *y *** FALLA sin el arreglo *** (comprobado poniendo el `int()` a mano)*
```

### (5) La telemetria de Lidl -- *** tres caminos mudos, no uno ***

```
*** l265  la region sin acreditar ***  *-- *el que el complemento nombra: *imprimia la causa y `return 1`
   SIN tocar `runs.csv`*
*** l298  la PETICION ***  *-- *`f.get(URL)` + `save_raw` + `decode`: *una excepcion de red salia por el
   `traceback` sin fila*
*** l311  el PARSEO ***  *-- *`captura(...)`: *una pagina que cambia de forma se llevaba la fila por delante*
*** -> las tres registran ya `log_run(FUENTE, 0, 1, ..., completa=False)` *** *
*** Y DONDE VA LA CAUSA ***  *`log_run(fuente, filas, errores, segundos, completa)` y el CSV tiene SEIS
   columnas: *** no hay sitio para un motivo *** -- *pero **si sale por stdout**, que va a
   `data/ejecuciones.log`* *** -> el CSV dice QUE HUBO INTENTO, y el log dice POR QUE FALLO *** *
*** LAS REGRESIONES ***  *region sin acreditar y excepcion de red: **las dos dejan UNA fila** (0 filas,
   1 error) *y **NO escriben bronze*** *-- *y *** las dos FALLAN sin el arreglo *** *
```

---

## 2. *** Los extras, que no estaban en el complemento y salieron ***

### (6) La clase de las citas por linea, *** eliminada ***

```
*** las tres que habia ESTABAN LAS TRES MAL *** *
  `main.py` -> `collectors/lidl.py:273`      *-- *en 273 esta **la salida de la region**, no la cobertura*
  `despensa.py` -> `diario.py:154`           *-- *en 154 esta *** `borrar` *** (un 404)* *** desplazada 73 lineas ***
  `despensa.py` -> `diario.py:140`           *-- *en 140 esta *** `dia` *** (la ruta del dia)* *** desplazada 4 ***
*** -> y ahora se cita lo que NO CAMBIA DE SITIO: *** *** un nombre de funcion, una constante, o la RUTA del
   fichero que produce. Una linea, no. *** *
*** y no queda NINGUNA cita por linea viva en la API *** *
```

### (7) *** EL RESPALDO, QUE NO EXISTIA ***

```
*** `respaldar.bat` FALLABA SIEMPRE ***, y su comprobacion era: *
  `docker compose ps db 2>nul | findstr /i "running" >nul`  *** -> exit=1 *** *
  *y Docker contesta: *** «Up 22 hours (healthy)» *** *** -> NO DICE «running» *** *
  *** -> Docker Compose cambio el formato de `ps`, y el guion abortaba con «La base de datos no esta
  levantada» CON LA BASE LEVANTADA Y SANA *** *
*** y `data\respaldos` NO EXISTIA ***  *-- *la carpeta la crea el guion* *** -> nunca se ejecuto con exito *** *
*** Y LO QUE ESO SIGNIFICABA, con las palabras del propio guion: *** *
  *** «las cuentas, las listas y los favoritos solo existen aqui: si se pierde este volumen, se pierde todo
  lo que habeis escrito vosotros» *** *
*** Y NO CUBRIA LAS DOS SQLITE ***  *-- *y lo dice `docker-compose.yml:60-66`: *
  *** «El `recetas.sqlite` y el `diario.sqlite` NO SON CRUDO NI SE RECALCULAN -- SON LO QUE LA CASA HA
  ESCRITO… y `robocopy data\raw` NO LOS VE» *** *
*** EL ARREGLO ***  *** las tres cosas que no se regeneran ***: *PostgreSQL (con `--status running -q` en
   vez del `findstr`), el recetario y el diario -- **del VOLUMEN** (no el fichero del host: no son el mismo),
   **con `VACUUM INTO`** (una SQLite abierta copiada a mano puede salir a medias) y **con sello de tiempo**
   (con nombre fijo, la copia de hoy pisaria la de ayer)* *
*** Y SI EL FICHERO NO EXISTE, SE DICE Y NO SE INVENTA ***  *-- *el diario se crea al primer apunte*
```

### (8) *** El volcado verificado SIN restaurar ***

```
`data/respaldos/cesta_2026-10-14_1123.sql.gz`  *** 432.930 bytes · 3.297 lineas · 2.312 filas en 14 tablas *** *

  *** `lista_linea` 346 *** *** <- LAS MISMAS que casa *** · *** `usuario` 73 *** *** <- LOS MISMOS ***
  *** `lista_acceso` 272 *** *** <- LOS PERMISOS: la tercera pata que el complemento pide ***
  `lista` 257 · `sesion` 1020 · `compra` 97 · `compra_linea` 137 · `invitacion` 71 · `visita` 28 ·
  `alerta` 6 · `favorito` 4 · *** `preferencia` 1 *** *(el objetivo del 14)* · `cocina` 0 · `despensa` 0
```

### (9) Las guardas del ensayo de restauracion

```
`scripts/ensayo_de_restauracion.py`  *-- *** 19 ensayos, todos SIN Docker y SIN bases *** *
*** 1) LOS PUERTOS, POR NUMERO ***  *5432 (casa) · 5433 (facylf) · 5434 (pruebas)*, *y `puerto_libre()`
   **no confia**: *el sistema no sabe que 5432 es casa, asi que **comprueba en el bucle***
*** 2) LOS NOMBRES de esos contenedores *** *** 3) un nombre sin el prefijo propio *** *
*** 4) EL DSN ***  *no loopback · sin base · sin puerto (que PostgreSQL resolveria a **5432**)*
*** 5) LA BASE VACIA ***  *`information_schema.tables` filtrando por `public`*
*** 6) LA LIMPIEZA ***  *borra **solo** lo que lleva **la etiqueta**, *y con `-v`*
*** Y LA AUDITORIA PREVIA DEL GUION VIEJO ***  *-- *el complemento manda «no ejecutar el guion actual a
   ciegas: auditar sus eliminaciones y subprocesos primero»*, *y la auditoria encontro que **no sirve para
   esto**: *esta cableado a `db` (**casa**) y **su primer acto es `DROP SCHEMA public CASCADE`***
```

---

## 3. *** LOS ERRORES MIOS, y el patron que comparten ***

```
*** 1) Puse la regresion del tuple EN LA RUTA QUE NO ERA ***  *-- *pasaba con y sin el arreglo*
*** 2) Di un «EXITO» FALSO en el respaldo ***  *-- *anclas mal indentadas: solo cambio la cabecera, el guion
   dijo `exit=0`, *y **no copio ninguna SQLite***
*** 3) Declare una guarda que SOLO ESTABA ESCRITA ***  *-- *«la base tiene que estar vacia» era un docstring;
   *lo dije **en el mismo commit** en que lo declaraba, *y lo cace al verificarlo*
*** 4) El `git checkout HEAD` me BORRO el arreglo de `recetas.py` ***  *-- *por no haberlo commiteado antes*
*** 5) Un `ruff B023` ***  *-- *la clausura del bucle no ligaba la variable, *y **las dos vueltas habrian
   compartido la ultima**: *el ensayo habria pasado **probando una sola cosa dos veces***
*** 6) Conte MAL el volcado ***  *-- *regex `[^)]*` cortada por `numeric(10,2)`: *decia **0 filas en todas**;
   *lo detecte porque **un volcado vacio serian ~15 KB y el fichero son 432.930 bytes***
*** 7) Reconstrui la API con el demonio ya raro ***  *-- *25+ minutos, y despues el demonio saturado;
   *debi parar **cuando el primer `inspect` se colgo***
*** 8) Sonde la API por el host ***  *-- *dieciseis rondas despues de haber medido yo mismo que **el 8000
   no se publica al host***
*** 9/10/11) Tres hipotesis sobre la lentitud de la suite, las tres caidas MIDIENDOLAS *** *
```

> *** Y **las once son la misma forma**: *** *** **una afirmacion que sobrevive al codigo que la describia.**
> *** *
> ```
> *«no esta en la tarea de las 06:00»* (y estaba) · *«la base lo rechazaba con un 500»* (y la migracion lo
> quito) · *«la tabla lo prohibe»* (y no) · *«pulsar dos veces no duplica»* (y no lo cumplia) · *«consolida
> por `(nombre, unidad)`»* (y guardaba el nombre) · *`isdigit()`* (y ningun id lo es) · *«es lo UNICO que hay
> que respaldar»* (y no) · *«la tabla exige `linea_con_destino`… medido el 13 de octubre»* (y ya no) ·
> *`findstr /i running`* (y Docker ya no lo dice) · *las tres citas por linea* · *y **mis once**.*
> ```

---

## 4. *** LO QUE BLOQUEA, medido ***

```
*** `docker ps` *** *** -> se cuelga *** *(5 y 30 minutos, en dos intentos separados por media hora)*
*** `docker rm -f` *** *** -> se cuelga *** *sobre `cesta-restauro-82294a5bd651`, que quedo en *** `Created` *** *
*** `docker inspect` *** *** -> se cuelga *** *
*** LO QUE SI FUNCIONA ***  *los tres puertos **abiertos** (5432 · 5433 · 5434) -- los contenedores **siguen
   corriendo**; *`ruff` pasa; *y **la ingesta sigue viva** (`Cesta diaria` Running desde las 10:11, 267009)*
*** Y ESO PARA TRES COSAS *** *
  *** (a) LA PRUEBA DE RESTAURACION ***  *-- *guardas hechas, recorrido no*
  *** (b) LA ACEPTACION CONTRA EL CODIGO DE HOY ***  *-- *la imagen de la API es *** de ayer a las 23:48 ***,
     *asi que **NADA de lo hecho hoy es visible para la app**; *la aceptacion **ya se corrio** y dio el
     resultado viejo (`anadidos=0`, `sin_catalogo=['tomate']`, la lista a 0) -- *** que es la confirmacion de
     que el defecto era real *** *
  *** (c) LA SUITE COMPLETA ***  *-- *no termina (30+ min cuando tarda 5)*
*** y ademas, UNA DECISION DE PRODUCTO: ***  *hoy `uuid5(lista_id|clave)` con `ON CONFLICT DO UPDATE`
   *** REEMPLAZA *** -- *¿dos operaciones legitimas del mismo producto **suman** (800 g de dos semanas)
   o **sustituyen** (lo de la ultima)?*
```

## 5. Y lo que **no se sabe**, y no se inventa

```
*** por que la API sale `unhealthy` ***  *-- *responde `200` a todo **desde dentro***
*** por que la suite tarda 30+ min ***  *-- *tres hipotesis caidas, ninguna causa*
*** que region es `'28'` de Lidl ***  *-- *el `regionPriceId` capturado; *su nombre no se ha buscado*
*** si la restauracion funciona ***  *-- *nunca se ha ejercido: *no habia copias, *y ahora **si**, *pero el
   recorrido esta pendiente*
```

## 6. Los commits de esta parte

```
6667991  los DOS puentes persisten los envases
60e6ff0  la regresion de las dos marcas, EN LA RUTA QUE TOCA
156aa07  la receta preserva el articulo elegido
6fe7d34  el dedupe por nombre, sustituido por identidad
a89811f  la telemetria de Lidl en todas sus salidas
8ca7dc8  la regresion de la telemetria
a71fbbb  las dos citas por linea de despensa.py, que estaban las dos mal
e25da91  el respaldo no existia: el `findstr /i running`
6b078c8  el respaldo de las dos SQLite, con VACUUM INTO
1193a28  respaldar.bat respalda las tres cosas
59b837c  la primera linea de la cabecera, que tambien era corta
2cea612  el inventario NO se respalda, y es correcto
3415636  el volcado esta completo y lleva los permisos
4dd2069 / 5f7ab7f  las guardas del ensayo de restauracion, y la quinta que solo estaba escrita
```

> *** Y **el estado de las puertas, lo ultimo que se pudo medir**: *`ruff` **All checks passed**;
> *`pytest -q` **no termino** (30+ min); *y **2.062 ensayos recolectados en 6,5 s** -- *que son **29 mas**
> que los 2.033 de la primera parte.* *
