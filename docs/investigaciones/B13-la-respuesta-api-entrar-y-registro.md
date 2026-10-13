# B13 · **La respuesta: `POST /api/entrar`, y una ruta que crea la cuenta y entra en un solo paso**

*(13 de octubre de 2026. **Y es exactamente lo que el propietario eligio en B13.**)*

## 1. Las dos puertas, literales (`plataforma/api/main.py`)

```
l79   # --------------------------------------------------------------- *** entrar *** ---
l87   *** @app.post("/api/entrar") ***
l88   def entrar(c: Credenciales, respuesta: Response):
l91       raise HTTPException(401, "*** Usuario o contrasena incorrectos. ***")

l107  """*** Crear una cuenta y entrar con ella, en un solo paso. ***"""
l132      raise HTTPException(500, "La cuenta se creo pero no se pudo entrar.")
```

> *** O sea: **hay DOS caminos**, y **los dos devuelven la cookie de sesion**: ***
> 1. *** `POST /api/entrar` *** -- *con `Credenciales` (usuario y clave), *y **401 con su motivo** si no cuadran;*
> 2. *** *** `POST /api/registrarse` (201) *** *** -- *con `Alta`, *y **«crea una cuenta Y ENTRA CON ELLA, EN UN SOLO
>    PASO»**; *y **su 500 dice que la cuenta se creo y no se pudo entrar**, *que es **la doctrina otra vez**:
>    *distingue **«no se creo»** de **«se creo y fallo el paso siguiente».** *
>
> *** Y **la razon del registro esta escrita, y es de UX**: ***
> > *** «Entra sola A PROPOSITO: *** *hacer que alguien rellene un formulario, le digan **"cuenta creada"** y tenga
> > que **escribir lo mismo otra vez** en la pantalla de [entrar]...» *
>
> *** O sea: **el registro entra solo para no pedir dos veces lo mismo** *** -- *y **es la misma clase de decision que
> `Suite.tsx` y que `ABSTIENE`: **quitarle al usuario un paso que no aporta nada.** *

## 2. Y **es la decision del propietario**, tomada en B13 hace muchas rondas

> *** B13 pregunto: *** *** ¿usar los usuarios de prueba que ya existen, o crear nuevos? ***
>
> *** Y **el propietario eligio**, literal: *** *** «CREAR USUARIOS DE PRUEBA NUEVOS en cesta-db-1 (Recomendado)» ***
> -- *y **anadio**: «de forma aditiva, sin tocar su cuenta». *
>
> *** O sea: **la ruta del registro es exactamente lo que pidio** *** -- *«crear una cuenta **y entrar con ella**, en
> un solo paso»: *crea **y** entra, *y **no toca nada de nadie.** *
>
> *** Y **por eso los dos recorridos que quedan ya tienen camino**: *** *** no hay que **adivinar una clave**; *hay
> que **crear una cuenta de ensayo**, *y **el navegador se queda con su cookie.** *

## 3. Y **el navegador puede hacerlo solo**, porque el proveedor tiene `fill` y `click`

```
`capture_browser_scenario` admite, entre otras acciones:
  *** `fill` ***   -- *locator + value*      -> *rellenar el usuario y la clave*
  *** `click` ***  -- *locator*              -> *pulsar «Crear cuenta» o «Entrar»*
  *** `wait_for` *** -- *locator + state*     -> *esperar a que aparezca lo que solo se ve CON sesion*
  *** y `locator` admite `role`, `test_id` y `css` ***
```

> *** O sea: **el recorrido 4 y el 5 se pueden hacer enteros**, *y **sin que nadie toque nada**: *
> ```
> 1) `goto`  -> `/ajustes`  (que es «Cuenta y preferencias», el enlace del menu)
> 2) `fill`  -> el usuario   (elegido por el agente, y NO uno del propietario)
> 3) `fill`  -> la clave     (inventada, y no secreta: es una cuenta de ensayo)
> 4) `click` -> crear cuenta
> 5) `wait_for` -> algo que SOLO se ve con sesion -- *y ahi esta la prueba de que entro*
> 6) `goto`  -> `/calorias`  y `/recetas`, ya con sesion
> ```
>
> *** Y **el paso 5 es el que convierte el recorrido en una prueba**: *** *si aparece **algo que solo se ve con
> sesion**, *entonces **entro**; *y si **sigue diciendo «Hay que entrar primero»**, *entonces **no entro** -- *y
> **eso tambien es un dato.** *

## 4. Y **una advertencia, que es del encargo**: la cuenta se crea, y **en la base de casa**

```
*** LA RUTA CREA LA CUENTA EN LA BASE A LA QUE APUNTE LA API *** -- *y la API es `cesta-api-1`. *
   -> *y su DSN es **el de casa** (5432), **porque es el contenedor de casa.** *
   *** -> o sea: **el recorrido 4/5 ESCRIBE EN LA BASE DE CASA**, *que es **lo que B13 ya decidio**: *
      «crear usuarios de prueba nuevos **en cesta-db-1**» -- *y **de forma aditiva.** *
```

> *** Y **por eso el nombre del usuario lleva prefijo y marca de tiempo** *** -- *que es **la convencion que ya hay**
> (B13: *`a09`/`c01b`/`f07` + sello*, **38 usuarios**). *
>
> *** Y **NO se toca nada del propietario**: *** *la fila nueva **es nueva**, *y **`crea_usuario` solo hace un
> `INSERT`** (B13, leido: *«una sola linea: `INSERT INTO usuario (usuario, nombre, clave_hash)`»*). *
>
> *** Y **el recorrido 5** (traspasar una receta) *si **escribe mas** -- *y **ahi hay que elegir**: *
> *** una receta y una lista **de la cuenta de ensayo**, *que es **lo mismo que hacen los ensayos `f07`** (B10: los
> usuarios de prueba y sus listas). *
