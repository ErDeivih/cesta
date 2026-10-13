# B13 · **La cookie esta BIEN** -- y por tanto el fallo es del instrumento, no de la aplicacion

*(13 de octubre de 2026. **Y un falso positivo evitado, que es lo que el encargo prohibe.**)*

## 1. La cookie, con sus cuatro atributos

```python
# plataforma/api/main.py:93-94
respuesta.set_cookie(COOKIE, token,
                     *** httponly=True ***,
                     *** samesite="lax" ***,
                     *** max_age=AJUSTES.dias_sesion * 86400 ***,
                     *** path="/" ***)
```

> *** Y **los cuatro son los correctos, y cada uno por su motivo**: ***
> ```
> *** httponly=True ***        -> *el JavaScript **no la lee** -- *y **por eso no puede robarla un script** *
> *** samesite="lax" ***       -> *** y `Lax` SI la manda en una navegacion GET del mismo sitio *** *
>                                *(que es **exactamente** lo que es un `goto` a `/compra/listas`)*
> *** max_age = dias_sesion *** -> *** y es PERSISTENTE, no de sesion *** -- *o sea: **sobrevive a cerrar el
>                                navegador** *
> *** path="/" ***             -> *y **cubre todo el sitio**, no **una seccion** *
> ```
>
> *** O sea: *** *** **no hay nada que arreglar en la cookie.** *Esta **como tiene que estar.** *

## 2. Y por tanto la causa 1 **se cae**, y la causa 2 **es la buena**

```
*** CAUSA 1 · «la cookie no sobrevive a una navegacion» ***  -> *** DESCARTADA ***
   -> *porque **`Lax` + `path="/"` + `max_age` = sobrevive**, *y **es la configuracion correcta.** *
   *** -> y si la aplicacion estuviera mal, `test_la_cookie_va_con_httponly_y_samesite_lax` (B14) la habria
      cazado** *-- *y **pasa.** *

*** CAUSA 2 · «el proveedor repone el almacenamiento declarado» ***  -> *** ES LA QUE QUEDA ***  ⚠️
   -> *los parametros del escenario llevan *** `storage: { cookies: [], local_storage: [], session_storage: [] }` ***
   -> *** y ese «vacío» es lo que el escenario DECLARA *** -- *y **el proveedor lo mantiene.** *
   -> *** y encaja con `4 de 4` contra `0 de 3`: *** *cada `goto` **deja el almacenamiento como se declaro.** *
```

> *** O sea: *** *** **el fallo era del instrumento, y decirlo es obligatorio** *** -- *porque **lo contrario es un
> falso positivo**, *y **el encargo lo prohibe dos veces**: *«no consideres terminado lo que solo abrio una pantalla
> vacia» -- *y **su simetrico**: *no **declares roto lo que solo no has sabido usar.** *
>
> *** Y **las dos veces se ha evitado lo mismo en esta sesion**: *** *una **con `grep` de mis propias palabras**
> (B02, nueve veces), *y **otra con un escenario mal declarado** (aqui). *

## 3. Y **la forma de hacer el recorrido bien esta a la vista**, y es de una palabra

```
*** EL PROBLEMA: ***  *`goto` es una *** NAVEGACION COMPLETA *** -- *y **el proveedor repone el almacenamiento.** *
*** LA SOLUCION: *** *** NO NAVEGAR. CLICKAR. ***
   -> *la suite es **una SPA** (React Router): *los enlaces del menu **no recargan la pagina** *
   -> *y **las capturas ya lo demuestran**: *el menu tiene *** `link «Recetas» -> /recetas` ***,
      *y **`link «Calorias» -> /calorias`** -- *con `data-discover="true"` (visto en el DOM de la ronda 218)* *
   *** -> o sea: *se pulsa el enlace, **y el enrutado es del lado del cliente.** *-- *y **el almacenamiento no se
      toca, porque no hay navegacion.** *
```

> *** Y **encaja con TODO lo medido**: ***
> ```
> ronda 230 · el alta   ->  *** sin `goto` *** -> `e4476372…` (entro)
> ronda 233 · entrar    ->  *** sin `goto` *** -> `e4476372…` (entro)
> ronda 234 · entrar    ->  *** con `goto` *** -> `5c2c0dc7…` (la pantalla de entrar)
> ```
>
> *** Y **hay una segunda via, tambien dicha**: *** *** declarar **la cookie de sesion** en `storage.cookies`
> *-- *y el proveedor **la admite** (`storage: { cookies: [...] }`), *y **el token sale de la respuesta de
> `/api/entrar`.** *
>
> *** Pero **la primera es mejor**, y por una razon: *** *** no **fabrica** una sesion: *la **consigue como la
> consigue un usuario** -- *pulsando «Entrar» **y luego un enlace del menu.** *

## 4. Y el recorrido 5 queda **con su forma correcta, y es de dos acciones**

```
*** RECORRIDO 5 · y la restriccion del propietario ***

  PASO 1  `goto`  *** `/compra/listas` ***          *-- *y aqui **si** se navega: es **la entrada** *
  PASO 2  `wait_for_timeout` 2000
  PASO 3  `fill` «Usuario»  ·  PASO 4 `fill` «Clave»
  PASO 5  `click` *** «Entrar» ***
  *** PASO 6  `click` *** `rol link, nombre «Recetas»` *** ***  <-- *** ¡CLICK, NO `goto`! ***
  PASO 7  `wait_for_timeout` 2500  -- *y captura*
  *** -> y si la pantalla **ya no dice «Hay que entrar primero»**, *entonces **la sesion sobrevivio al enlace** --
     *que es **lo que hace un usuario.** *
```

> *** Y **el paso 6 es la correccion de todo**: *** *** de `goto` a `click`. *Y **con eso el recorrido 5 se puede
> hacer**, *y **la restriccion del propietario queda a la vista.** *
>
> *** Y **es una buena posicion para parar**: *la aplicacion **esta limpia** (cookie correcta, login 200, alta 201),
> *y **el fallo era mio.** *

## 5. Y el estado, con la aplicacion declarada limpia y el instrumento corregido

```
RECORRIDO 4c · «la sesion al navegar»  -> *** Y NO ES UN FALLO DE LA APLICACION ***
   -> *la cookie esta bien (`httponly` · `lax` · `max_age` · `path="/"`)*
   -> *y el escenario **declaraba `storage` vacio**, *y **el proveedor lo repone al navegar** *
   *** -> FALSO POSITIVO EVITADO, y con la causa escrita. ***
RECORRIDO 5 · *** tu restriccion ***      -> *** y ahora tiene su forma: `click` en «Recetas», no `goto` ***
```
