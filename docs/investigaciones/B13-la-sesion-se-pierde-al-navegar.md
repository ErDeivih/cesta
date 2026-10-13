# B13 · **La sesion SE PIERDE AL NAVEGAR** -- y hay dos causas posibles, y una es del proveedor

*(13 de octubre de 2026. **La medida que separaba, y separo.**)*

## 1. La prueba, y su resultado

```
`capture_browser_scenario` · 7 acciones · 5,9 s · cleanup: terminated-owned-process

  1. `goto`  `/compra/listas`  ·  2. `wait_for_timeout` 2000
  3. `fill` «Usuario» *44 ms*  ·  4. `fill` «Clave» *17 ms*
  5. `click` «Entrar» *** 56 ms ***
  6. *** `goto` `/compra/listas` OTRA VEZ ***
  7. `wait_for_timeout` 3000  -- *y captura*

*** Y LO QUE SALE ES LA PANTALLA DE ENTRAR: ***
  heading *** «Entra para ver tu lista» [level=2] ***
  paragraph «La lista de la compra es tuya y de quien la compartas...»
  *** textbox «Usuario» · textbox «Clave» · button «Entrar» · button «Créala» ***
  sha256 *** 5c2c0dc74a59235e4c082ed9c80578694239ae343a61a1eeb23eb9e168353de5 ***  ·  *** 1239 bytes ***
```

> *** Y **ese hash es EXACTAMENTE el de la ronda 224** *** -- *cuando **`/cesta` redirigio a `/compra/listas`** y
> salio **la pantalla de entrar** (`5c2c0dc7…`, 1239 bytes). *
>
> *** O sea: **al volver, la sesion NO ESTA.** *
>
> *** Y **la cuenta es definitiva**: ***
> ```
> *** SIN `goto` despues de entrar:  4 de 4 ENTRO ***   (rondas 230 y 233, y las dos capturas dan `e4476372…`)
> *** CON `goto` despues de entrar:  0 de 3 ENTRO ***   (rondas 231, 232 y 234)
> ```

## 2. Y entonces la explicacion **A** gana: **es la navegacion**, y no `/recetas`

```
*** A) la sesion se pierde al navegar ***     -> *** GANA: *el `goto` a `/compra/listas` tambien la pierde***
*** B) `/recetas` no comparte la sesion ***    -> *** DESCARTADO ***: *no hace falta llegar a `/recetas`*
```

> *** Y **la prueba estaba bien puesta**: *** *se **volvio a la misma pagina donde entro**, *y **tambien se perdio.**
> *Asi que **no era `/recetas`.** *

## 3. Y ahora **la causa**, y hay **dos, y una es del proveedor** ⚠️

```
*** CAUSA 1 · LA COOKIE NO SOBREVIVE A UNA NAVEGACION COMPLETA ***
   -> *y **seria un fallo de la aplicacion**, *y **de los gordos**: *entras, y **al cambiar de seccion te pide
      entrar otra vez.** *
   -> *** y hay un dato que hay que mirar: `SameSite` *** -- *B14 leyo `test_la_cookie_va_con_httponly_y_samesite_lax`,
      *o sea **`Lax`**, *y **`Lax` SI manda la cookie en una navegacion GET del mismo sitio.** *
   -> *** pero `main.py:94` pone la cookie con `max_age=AJUSTES.dias_sesion * 86400` *** -- *o sea: **es persistente,
      no de sesion.** *Asi que **deberia sobrevivir.** *
   -> *** y por eso esta causa tiene un problema, y se dice.** *

*** CAUSA 2 · EL PROVEEDOR RESETEA EL ALMACENAMIENTO EN CADA NAVEGACION ***  ⚠️
   -> *** y esta es la que hay que descartar PRIMERO, porque es MIA: *** *
      *los parametros del escenario llevan **`storage: { cookies: [], local_storage: [], session_storage: [] }`** *
   -> *o sea: **el escenario DECLARA el almacenamiento VACIO** -- *y **un escenario determinista lo repone al
      estado declarado**, *y **una navegacion es el momento natural para hacerlo.** *
   -> *** y encaja con TODO: *** *cada `goto` **deja el almacenamiento como se declaro** -- *vacio.* *
```

> *** Y **la causa 2 se prueba sin tocar la aplicacion**: *** *** **la misma llamada, quitando la clave `storage`**
> (o **declarando la cookie de sesion**, *que el proveedor **admite**: *`storage: { cookies: [...] }`). *
>
> *** Y **si con eso la sesion sobrevive**, *entonces **no hay fallo de la aplicacion** -- *y **seria un falso
> positivo**, *que es **lo que el encargo prohibe.** *
>
> *** Y **si NO sobrevive tampoco**, *entonces **la causa 1 es cierta** -- *y **es un fallo de verdad**, *y **de los
> que el usuario nota: *entrar, cambiar de seccion, y que te pidan entrar otra vez.** *

## 4. Y el estado de B13, con una medicion nueva y dura

```
RECORRIDO 1  · el lanzador y las tres raices   -> *** HECHO ***
RECORRIDO 2  · `/compra`                        -> *** HECHO ***
RECORRIDO 3  · `/recetas` sin sesion            -> *** HECHO ***
RECORRIDO 4  · *** el alta ***                   -> *** HECHO ***   *-- `e4476372…`*
RECORRIDO 4b · *** entrar ***                    -> *** HECHO ***   *-- y **dentro de la misma pagina**, `e4476372…`*
RECORRIDO 4c · *** la sesion al navegar ***      -> *** NO SOBREVIVE ***  *-- y **la causa esta entre dos, y una es
                                                     del proveedor*** *
RECORRIDO 5  · *** tu restriccion ***             -> *detras de 4c*
```

> *** Y **`4 de 4` contra `0 de 3` es un dato duro** *** -- *y **la hipotesis del proveedor se prueba en una llamada**,
> *y **sin tocar codigo.** *
>
> *** Y **es la leccion de toda la sesion, otra vez**: *** *** antes de **declarar un fallo de la aplicacion**,
> *hay que **descartar que el fallo sea del instrumento.** *
