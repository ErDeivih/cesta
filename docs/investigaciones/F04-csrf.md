# F04 · CSRF: lo medido, y lo que falta

Estado: **medido en el código; sin ensayo empírico**. Fecha: 13 de octubre de 2026.
Origen: hallazgo #10 de la revisión de fase 2 -- *el único de los diez que seguía sin tocar*.

> *«Informe lo posterga y dice que **mismo origen lo hace irrelevante**. → **No aceptar esa inferencia**:
> comprobar solicitudes cross-origin, cookies y mutaciones de la app local; **mismo origen normal no prueba
> defensa**.»*

---

## 1. Y el informe tenía razón en una cosa: **la inferencia no es la defensa**

Lo que hay, medido en el código:

```
plataforma/api/main.py:62   app.add_middleware(CORSMiddleware,
                                allow_origins=list(AJUSTES.origenes),     # CESTA_ORIGENES
                                allow_credentials=True, allow_methods=["*"])
plataforma/api/main.py:88   respuesta.set_cookie(COOKIE, token,
                                httponly=True, samesite="lax", ...)
plataforma/api/main.py:129  (igual, en el otro punto donde se emite)
```

**Así que la defensa no es «el mismo origen»: es la política de la cookie.**

- **`SameSite=Lax`**: *el navegador **no manda** la cookie en un POST, PUT, PATCH o DELETE cross-site.*
  Esa es la barrera real contra el CSRF clásico.
- **`HttpOnly`**: *el JavaScript de la página no puede leer el token.*
- **CORS con lista fija y `allow_credentials=True`**: *una página de otro origen no puede **leer** las
  respuestas.*

*Y conviene decir lo que CORS **no** hace, porque es el error habitual*: **CORS no impide enviar la
petición**, sólo leer la respuesta. *Quien defiende del CSRF es `SameSite`, no CORS.*

## 2. Y el hueco que `Lax` deja, comprobado

**`SameSite=Lax` sí manda la cookie en un GET de navegación de nivel superior.** *Así que un endpoint que
**mute** por GET sería vulnerable a un enlace: `<a href="https://cesta/api/...">`.*

**Busqué endpoints GET que muten**, con una heurística sobre el cuerpo de la función:

```
rutas GET registradas: 26
mutantes registrados (post/put/patch/delete): 26
GET que parecían mutar según la heurística: 2
    linea 1311  /api/listas/{lista_id}/desde-el-plan
    linea 1418  /api/listas/{lista_id}/desde-la-compra
```

**Y el primero, leído entero, es una lectura que lo declara:**

```
1311  @app.get("/api/listas/{lista_id}/desde-el-plan")
1314      """**La vista previa**: que ingredientes del plan entrarian en la lista,
             **sin tocar la lista**."""
1322      _acceso(lista_id, usuario, hace_falta_escribir=False)     <- lo declara
```

**`hace_falta_escribir=False`**: *el endpoint dice que no necesita escribir, y el acceso se comprueba en
consecuencia.* **Es un diseño auditable, no una casualidad** -- *y el docstring del ayudante `_del_plan`
explica por qué la previa y la acción comparten cálculo: «separarlos es como se acaba con una previa que
miente».*

## 3. Lo que NO se ha hecho, y no se da por hecho

1. **La segunda mitad**: `/api/listas/{lista_id}/desde-la-compra` (línea 1418) **tiene la misma heurística
   y la misma pinta -- «desde-la-compra» es la pareja simétrica -- pero NO se ha leído.** *Darlo por bueno
   por simetría es exactamente lo que el informe hacía y esta fase existe para no repetir.*
2. **Ningún ensayo empírico.** *No se ha lanzado una petición cross-origin real contra la API, ni se ha
   comprobado con el navegador que la cookie no viaja.* **El hallazgo pedía «comprobar solicitudes
   cross-origin, cookies y mutaciones», y de eso sólo está hecho lo de las mutaciones.**
3. **`CESTA_ORIGENES` por defecto es `http://localhost:8080`**, y *la app de ensayo corre en el 5173*:
   **no se ha comprobado qué lista de orígenes tiene el despliegue real**, y si el 5173 está en ella, CORS
   lo permite por configuración, no por diseño.

## 4. Lo que se puede afirmar hoy, sin adornos

**Hay defensa, y no es la que el informe decía.** *`SameSite=Lax` + `HttpOnly` bloquean el CSRF clásico, y
los 26 endpoints que mutan son POST/PUT/PATCH/DELETE, no GET.* **Eso es más de lo que el informe había
comprobado.**

**Y no está demostrado.** *Falta leer el segundo endpoint, y falta el ensayo real con una petición
cross-origin.* **F04 sigue abierto, con dos pasos concretos en vez de una inferencia.**


---

## 5. Y el ensayo, hecho -- con su limite dicho

*(Ronda 39.)* `tests/test_fase2_f04_csrf.py`, **cinco pruebas**, dos de ellas con un `Origin` de verdad
pasando por el middleware:

| prueba | que fija |
|---|---|
| un origen ajeno no recibe permiso | **`https://malo.example` no obtiene `access-control-allow-origin`**, y tampoco un comodin |
| un origen configurado si lo recibe | *la otra mitad*: **sin esto, un `allow_origins` vacio tambien pasaria la de arriba** |
| el preflight de un origen ajeno tampoco | *un POST con `Content-Type: application/json` dispara preflight: si no autoriza, el navegador no manda la peticion* |
| la cookie va con `HttpOnly` y `SameSite=Lax` | **las dos emisiones**, leidas de la fuente |
| ninguna ruta que muta es un GET | **y el defecto de `_acceso` sigue siendo leer** |

### El segundo endpoint, leido

`/api/listas/{lista_id}/desde-la-compra` (linea 1418): **tambien es una lectura y tambien lo declara** --
*«No escribe nada: el diario rechaza el tipo `compra` a proposito -- comprar no es comer --, asi que
**propone** y la persona confirma»*, y `_acceso(..., hace_falta_escribir=False)`.

**Asi que ningun GET muta**, y las dos que lo parecian **son vistas previas que lo declaran en la firma del
acceso.**

### Y dos cosas que hay que decir de estas pruebas, para que no se lean como mas de lo que son

1. **Las dos del CORS no usan la app real.** *Montan un `Starlette` con **los mismos parametros** que
   `main.py` -- leidos de alli -- y comprueban el comportamiento del middleware.* **Eso fija que la
   politica de Starlette defiende con esos parametros, no que la app los tenga hoy**: *si alguien cambiara
   `allow_origins` en `main.py`, estas dos pruebas seguirian pasando.* **Para cerrarlo hay que usar
   `TestClient` contra la app de verdad, y eso necesita la base.**
2. **Ninguna prueba mira el navegador.** *Lo que se ha comprobado es la **configuracion**, no el
   comportamiento real de un navegador mandando o no la cookie.* *Un ensayo con `patchright` -- mandar un
   `POST` cross-origin y ver que no viaja la cookie -- seria la prueba que cierra F04, y no se ha hecho.*

### Y un error mio, que es el de esta fase otra vez

**La primera version de la ultima prueba tenia la condicion al reves**: marcaba las rutas GET que llaman a
`_acceso` **sin** el argumento, y fallo con **cinco rutas de lectura**. *El codigo estaba bien:*
`def _acceso(..., hace_falta_escribir: bool = False)` -- **el defecto ya significa leer**. *Corregido: lo
que hay que vetar es una GET que **exija** escribir, y que el defecto siga siendo `False`.*
