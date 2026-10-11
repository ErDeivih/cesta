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
