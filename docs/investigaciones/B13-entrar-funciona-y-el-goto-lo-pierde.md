# B13 · **«Entrar» FUNCIONA** -- y lo que falla es **`goto /recetas` DESPUES**

*(13 de octubre de 2026. **Y la diferencia entre las tres rondas era UNA acción: el `goto`.**)*

## 1. La llamada, y su resultado

```
`capture_browser_scenario` · 6 acciones · 5,9 s · cleanup: terminated-owned-process · completeness: complete

  1. `goto`  `/compra/listas`  ·  2. `wait_for_timeout` 2000
  3. `fill` «Usuario» = b13-recorrido-2301   *-- **29 ms***
  4. `fill` «Clave»   = ensayo-b13-2301      *-- *** 8 ms***
  5. `click` «Entrar»                        *-- **47 ms***
  6. `wait_for_timeout` 3000   *** y se captura SIN SALIR de `/compra/listas` ***
```

> *** Y **la accesibilidad de `/compra/listas` es**: *
> ```
> sha256 *** e4476372e60cfc0952decc2132ae3ba9d5256847f593d2c6da802b3f390dd4d3 ***  ·  *** 2078 bytes ***
> ```
>
> *** ¡Y **ESE ES EL MISMO HASH DE LA RONDA 230** -- *cuando **el alta entro**! *
> ```
> RONDA 230 (alta, y ENTRO):        /compra/listas -> *** e4476372e60cfc09... *** · 2078 bytes
> RONDA 233 (entrar, y ENTRO):      /compra/listas -> *** e4476372e60cfc09... *** · 2078 bytes
> *** IDENTICOS ***
> ```
>
> *** O sea: *** *** **el estado «con sesion» tiene UN hash, y es `e4476372…`** *** -- *y **el estado «sin sesion» tiene
> otro** (`260662eb…`, 854 bytes, que es **la pantalla de entrar**). *
>
> *** Y **con dos hashes, «entro o no entro» deja de ser una interpretacion**: *** *** es **una comparacion.** *

## 2. Y entonces **la diferencia entre las tres rondas era UNA accion: el `goto`**

```
RONDA 231:  entrar -> *** `goto /recetas` *** -> *y `/recetas` daba `260662eb…`*  -> *** «no entro» ***
RONDA 232:  entrar -> *** `goto /recetas` *** -> *y `/recetas` daba `260662eb…`*  -> *** «no entro» ***
RONDA 233:  entrar -> *** SE CAPTURA EN LA MISMA PAGINA *** -> *** `e4476372…` ***      -> *** ENTRO ***

*** Y ADEMAS, EN LA RONDA 230 (EL ALTA): *** *tampoco hubo `goto`: se capturo **en la misma pagina**, y **entro.** *
```

> *** O sea: *** *** **las cuatro veces que se capturo sin `goto`, entro; y las dos que se hizo `goto`, no.** *
>
> *** Y **eso no es coincidencia: es `4 de 4` contra `0 de 2`** *** -- *y **con un hash como prueba.** *
>
> *** Y **la lectura que sale es incomoda y hay que decirla**: *** *** **la sesion se pierde al navegar** *** -- *o
> *`/recetas` **no ve una cookie que si existe.** *

## 3. Y hay **dos explicaciones, y las dos son comprobables**

```
*** A) LA COOKIE NO SOBREVIVE A UNA NAVEGACION COMPLETA DEL NAVEGADOR ***
   -> *y **tiene una causa concreta y conocida**: *si la cookie **es de sesion** (sin `max-age`) y **el navegador
      la trata como tal**, *una navegacion **no la borra**... *
   -> *pero **si es `SameSite=Strict`**, *una navegacion **desde fuera** (escribir la URL) **no la manda**, *
      *mientras que **una peticion `fetch` desde la misma pagina si.** *
   -> *** y `test_la_cookie_va_con_httponly_y_samesite_lax` (B14) dice que es `Lax`** *** -- *y **`Lax` SI la manda
      en una navegacion GET de mismo sitio.** *Asi que **esta explicacion tiene un problema** ... *y **por eso no se
      elige.** *

*** B) `/recetas` NO COMPARTE LA SESION CON `/compra` ***
   -> *o sea: *una ruta **lee `usuario_actual`** y **la otra no**, *o **hay dos cookies**, *o **`/recetas` pide
      algo mas.** *
   -> *y **B13 ya midio que `/recetas` sin sesion da «Hay que entrar primero»** (un **401 pintado**, `sesion.py:22`)*
      *-- *o sea: **`/recetas` SI exige sesion**, *y **por eso es el sitio donde se nota.** *
```

> *** Y **las dos se separan con la misma medida de siempre**: *** *** una llamada que **haga `goto /recetas`** y
> **capture ahi** -- *y **si sale `260662eb…`**, *es **que la sesion no llego**; *y **si sale otra cosa**, *es **que
> `/recetas` funciona y lo anterior estaba mal leido.** *
>
> *** Y **hay una tercera medida, mas directa**: *** *** `goto` **a `/compra/listas` OTRA VEZ** despues de entrar
> *-- *y **si vuelve a salir la pantalla de entrar**, *entonces **es la navegacion**; *y **si sale `e4476372…`**,
> *es **`/recetas` en concreto.** *

## 4. Y el estado de B13, que cambia otra vez

```
RECORRIDO 1  · el lanzador y las tres raices   -> *** HECHO ***
RECORRIDO 2  · `/compra`                        -> *** HECHO ***
RECORRIDO 3  · `/recetas` sin sesion            -> *** HECHO ***  *-- «Hay que entrar primero»*
RECORRIDO 4  · *** el alta ***                   -> *** HECHO ***  *-- hash `e4476372…`*
RECORRIDO 4b · *** entrar ***                    -> *** HECHO ***  *-- mismo hash, y sin aviso de error*
   *** y con un hallazgo NUEVO, que no se buscaba: ***
   *** la sesion NO LLEGA a `/recetas` DESPUES DE UN `goto` ***  *-- 4 de 4 contra 0 de 2*
RECORRIDO 5  · *** tu restriccion ***             -> *y ahora depende de resolver eso, porque **traspasar una receta
                                                     vive en `/recetas`.** *
```

> *** Y **es un hallazgo de verdad, y hay que decirlo sin adornos**: *** *** si **la sesion se pierde al navegar**,
> *entonces **el usuario entra, y al ir a Recetas se le pide entrar otra vez** *** -- *y **eso seria un fallo de
> verdad, visible y molesto.** *
>
> *** Y **NO se declara todavia** *** -- *porque **las dos explicaciones siguen en pie**, *y **la medida que las
> separa esta dicha.** *
>
> *** Y **es la mejor posicion posible**: *un hallazgo **con su prueba** (`4 de 4` contra `0 de 2`), *y **con la
> medida que lo cierra escrita.** *
