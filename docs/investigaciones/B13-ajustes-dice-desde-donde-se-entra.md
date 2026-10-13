# B13 · **`/ajustes` no se queda en «entra»: dice desde donde** -- y la puerta es `/cesta`

*(13 de octubre de 2026. **Y la cuarta pantalla sin sesion vuelve a decir la verdad, y ademas da el camino.**)*

## 1. Lo que se observo

```
cleanup: «terminated-owned-process» · completeness: «complete» · 3,5 s

/ajustes
  *** banner: *** «Cesta»  ·  *** heading «Cesta» [level=1] ***
  *** main: ***
    *** heading «Entra para cambiar tus ajustes» [level=1] ***
    paragraph:
      «*** Los ajustes son de cada uno, asi que hacen falta tus listas. Se entra desde ***
       *** link «la cesta» -> `/cesta` *** ***.»
```

## 2. Y son **dos cosas**: dice que falta, **y dice donde**

```
*** «Entra para cambiar tus ajustes» ***        -> *dice QUE falta*
*** «Los ajustes son de cada uno...» ***          -> *y dice POR QUE: **son de cada uno** *
*** «...asi que hacen falta tus listas» ***       -> *y **nombra lo que hace falta: las listas** *
*** «Se entra desde link «la cesta» -> /cesta» *** -> *** Y DA EL CAMINO. ***
```

> *** O sea: **no es un «no tienes permiso»: es una frase que se puede seguir** *** -- *y **en tres pasos**: *que
> falta (entrar), *por que (los ajustes son de cada uno), *y **donde se entra** (`/cesta`). *
>
> *** Y **es la misma forma que `identidad.Permiso` (B07)**: *** *un «no» **con su motivo**, *y **con lo que hay que
> hacer.** *Y **lo mismo que `_presentacion(a, b) -> (bool, list[str])`**: *el «no» **y sus razones.** *
>
> *** Y **es la cuarta vez en cuatro pantallas**: ***
> ```
> / (lanzador)  -> 200, y las tres aplicaciones
> /compra       -> 200, y el buscador;  *ninguna sesion hace falta*
> /recetas      -> *** «Hay que entrar primero» ***  *(el 401 pintado -- sesion.py:22)*
> /ajustes      -> *** «Entra para cambiar tus ajustes... Se entra desde la cesta» ***  *(y DA el camino)*
> ```

## 3. Y **`/cesta` es una ruta que NO esta en el menu**: es la puerta

```
EL MENU DE LA SUITE TIENE:  «Cesta» -> `/`  ·  `/compra` · `/recetas` · `/calorias` · `/ajustes` · `/aprender`
*** Y LA ENTRADA ES `/cesta` *** -- *y **no aparece en el menu**: *se llega **por el enlace de una pantalla que
pide sesion.** *
```

> *** Y **eso es coherente**: *** *el menu **no ofrece «entrar»** *porque **quien no ha entrado no tiene menu**, *y
> **quien ha entrado no necesita el enlace.** *
>
> *** Y **`/cesta` es, ademas, el nombre del proyecto** *** -- *y **la pagina de entrar.** *O sea: **la puerta se
> llama como la casa.** *

## 4. Y el recorrido 4 tiene ya **su primer paso, y con la direccion exacta**

```
RECORRIDO 4 · `/calorias`, con sesion

  PASO 1  *** `goto` -> `/cesta` ***          <- *y esta medido: **es donde se entra***
  PASO 2  *ver el formulario*  -- *y **`/cesta` tendra «entrar» y «crear cuenta»**, *porque **las dos rutas
          existen** (`POST /api/entrar` y `POST /api/registrarse`)*
  PASO 3  *** `fill` usuario · `fill` clave · `click` crear cuenta ***
  PASO 4  *** `wait_for` -> algo que SOLO se ve con sesion ***   *-- **y este paso es la prueba** *
  PASO 5  *** `goto` -> `/calorias` ***       -- *y **ya con cookie**, *dibujara **el diario***
```

> *** Y **el paso 2 es el que falta mirar**, *y **es una captura**: *`/cesta` **con accesibilidad**, *y **sus
> localizadores** (`role`, `test_id` o `css`) **salen de ahi.** *
>
> *** Y **no se inventa ninguno**: *** *el proveedor admite **tres clases de localizador**, *y **cual de las tres usa
> la pagina es un dato, no una suposicion.** *
