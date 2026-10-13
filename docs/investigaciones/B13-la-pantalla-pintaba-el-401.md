# B13 · **La pantalla no estaba vacia: estaba pintando el mensaje del 401**

*(13 de octubre de 2026. **Y la frase del recorrido 3 esta, palabra por palabra, en `sesion.py`.**)*

## 1. La linea, literal

```python
# plataforma/api/sesion.py:22
raise HTTPException(401, "Hay que entrar primero.")
```

> *** Y **la pantalla del recorrido 3 decia, literal**: *** *** `paragraph: «Hay que entrar primero.»` ***
>
> *** O sea: **no es un texto de la interfaz: es EL MENSAJE DEL 401, PINTADO.** *
>
> *** Y **eso cambia la lectura del recorrido 3 entero**: *** *la pantalla **no estaba vacia** -- *estaba **diciendo
> lo que la API le contesto**, *y **lo dijo con las palabras de la API.** *
>
> *** Y **es la doctrina en su forma mas literal**: *** *** el «no» viaja con su motivo, **desde la base hasta el
> parrafo de la pantalla**, *sin que nadie lo reescriba por el camino. *

## 2. Y contesta **la regla de B14**, que parecia una advertencia suelta

> *** B14 pide: *** *** «NO DECLARAR DEFENSA COMPLETA POR 401 SIN COOKIE.» ***
>
> *** Y **aqui esta el caso, medido**: ***
> ```
> el navegador NO tiene cookie  ->  `/api/...` responde *** 401 ***  ->  y la pantalla **lo dice**
> *** y eso NO significa que la defensa este completa *** -- *significa **que no hay sesion**, y nada mas.*
> ```
>
> *** O sea: **el 401 es **la ausencia de sesion**, y no **un veredicto sobre el origen** *** -- *y por eso **B14
> avisa de no confundirlos**: *y **aqui se ven los dos por separado**, *porque **el origen se probo en
> `test_fase2_f04_csrf.py`, y la sesion se ve en esta pantalla.** *

## 3. Y **la sesion vive en `sesion.py`**, con su cookie

```
`plataforma/api/main.py:73`  *** «La sesion vive en `sesion.py` y se reexporta aqui por dos razones: [...]» ***
`main.py:77`   from .sesion import *** COOKIE, usuario_actual, usuario_opcional ***
```

> *** Y **`usuario_opcional`** es **la pieza que distingue los dos casos**: *** *una ruta **con `usuario_actual`**
> **exige** sesion (y da **401**); *y **con `usuario_opcional`** *«solo se aplica cuando hay sesion»* (main.py:112). *
>
> *** O sea: **el proyecto **tiene dos puertas**, y **cada ruta elige la suya** *** -- *y **eso explica los tres
> recorridos**:*
> ```
> RECORRIDO 1 · el lanzador  -> *** publico ***            -> 200, y sin sesion
> RECORRIDO 2 · /compra       -> *** el buscador se dibuja *** -> 200 en la pantalla, y el buscador funciona
> RECORRIDO 3 · /recetas      -> *** usuario_actual ***     -> *** 401, y la pantalla lo dice ***
> ```

## 4. Y lo que falta, ahora, es **una sola cosa: la clave**

```
*** Y NO SE PUEDE FABRICAR LEYENDO LA BASE: *** `almacen.crea_usuario` guarda `_hasher.hash(clave)`.
   -> *o sea: **hash**, y por tanto **la clave no esta en ningun fichero.** *
*** Y LA RESPUESTA ESTA EN LOS ENSAYOS *** -- *que **entran solos, y por tanto saben como**:*
   `tests/test_aislamiento.py` · `tests/test_b04_los_dos_puentes.py` · `tests/test_cesta_api.py` ·
   `tests/test_cifras.py` · y **mas** (el `git grep` de «entrar/login/sesion» da **seis ficheros o mas**)
```

> *** Y **hay un tercer camino que no necesita clave, y hay que nombrarlo**: *** *** la cookie de sesion *** -- *si
> los ensayos **fabrican una cookie** (o **insertan una fila en `sesion`**), *entonces **el recorrido puede llevar
> esa cookie en `storage.cookies`**, *y **el proveedor de navegador lo admite**: *`storage: { cookies: [...] }`. *
>
> *** Y **eso seria la via limpia**: *** *no **adivinar** una clave, *sino **usar la sesion que el proyecto ya sabe
> crear** -- *que es **lo que hacen sus propias pruebas.** *
>
> *** Y **la comprobacion, para la proxima ronda, es una**: *** *leer **como `test_cesta_api.py` (o
> `test_aislamiento.py`) consigue una sesion**, *y **si lo hace con cookie, `capture_browser_scenario` la acepta.***
