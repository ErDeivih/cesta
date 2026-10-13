# B16 · **El skip, explicado en vivo** -- que es exactamente lo que B16 pide

*(13 de octubre de 2026. **Segunda ronda de B16. Y su propia clausula se cumplio delante de mi.**)*

## 1. Lo que paso, literal

```
$ uv run pytest -q
   *** 2024 passed · 1 skipped *** · 25 warnings

$ $env:CESTA_POSTGRES = 'postgresql://cesta:prueba@127.0.0.1:5434/cesta'
$ uv run pytest -q
   *** 2025 passed · 0 skipped · 0 xfail *** · 26 warnings
```

> *** Y **la diferencia es una variable de entorno** *** -- *`CESTA_POSTGRES`, que apunta **la base de PRUEBAS**
> (5434), *y que **es la puerta documentada** desde la ronda 123 de esta sesion.*
>
> *** O sea: **el skip no era del codigo: era mio** *** -- *olvide la variable, *y **el ensayo que necesita Postgres
> se salto, en vez de fallar.** *
>
> *** Y **se salto en vez de fallar**, *que es **lo correcto**: *un ensayo que **no puede correr** porque **falta la
> base de pruebas** **no es un fallo de la aplicacion.** *

## 2. Y B16 pide **exactamente eso**: «cero xfail/skips SIN EXPLICACION ESPECIFICA»

```
B16:  «... *** CERO xfail/skips SIN EXPLICACION ESPECIFICA. ***»
```

> *** Y la clausula **no prohibe los skips**: *** *prohibe **los skips sin explicar**. *O sea: **un `skip` es
> aceptable si dice por que**; *y **lo que no vale es `1 skipped` a secas.** *
>
> *** Y **es la misma forma que todo el proyecto**: ***
>
> ```
> `importar_receta.Permiso(False, motivo)`     -> *el «no» CON su motivo*
> `_presentacion(a, b) -> (bool, list[str])`   -> *el «no» CON los motivos*
> `identidad.ABSTIENE`                          -> *y un veredicto de «no me pronuncio»*
> `_lo_que_se_paga(...) -> int | None`          -> *«None» en vez de un cero*
> y `skip`                                     -> *** y un salto que dice POR QUE ***
> ```
>
> *** Y aqui **la explicacion es concreta y comprobable**: *** *falta `CESTA_POSTGRES`; *y **con ella, cero skips.** *
>
> *** O sea: **el skip **tenia** explicacion, *y **la comprobacion la dio en dos comandos.** *

## 3. Y deja una nota practica, para quien retome

> *** *** LA SUITE NECESITA `CESTA_POSTGRES` PARA LLEGAR A CERO SKIPS *** ***:
>
> ```powershell
> $env:CESTA_POSTGRES = 'postgresql://cesta:prueba@127.0.0.1:5434/cesta'
> uv run pytest -q
> # *** 2025 passed · 0 skipped *** -- y el contenedor `cesta-prueba-db` tiene que estar levantado.
> ```
>
> *** Y **si el contenedor `cesta-prueba-db` NO esta** *** (nace con `--rm`, `docs/OPERACION.md:13`), *entonces **el
> skip es correcto** -- *y **por eso el ensayo se salta en vez de fallar**: *la falta **no es de la aplicacion.** *

## 4. Y B16 queda con **las tres cosas que subraya, comprobadas hoy**

```
*** «CERO xfail/skips sin explicacion especifica» ***
    -> *** 2025 pasan · 0 fallan · 0 se saltan · 0 xfail *** -- *y el unico skip que aparecio **tenia su razon
       medida**: faltaba la variable.*

*** «Separar usable en casa de desplegable para publico» ***
    -> *** lo publicado son CUATRO puertos de LOOPBACK: `:5432` · `:5434` · `:8080` ***
       *** y la API (`cesta-api-1:8000`) NO se publica al host, y su `/openapi.json` no existe ***
       -> *o sea: **el proyecto esta en «usable en casa», y NO esta desplegado.** *

*** «no fingir que ya son seis catalogos completos» ***
    -> *y **B02 tiene el alcance de Lidl medido**, y **B03 la cobertura por region** (la columna `region`)*
       *** y `data/raw` tiene las CINCO cadenas de rastreo, con `fuente=lidl` entre ellas ***
       -> *mercadona es la sexta y es de API: su crudo **no esta en `data/raw`**, y **no se finge que lo este.** *
```

## 5. Y el dictamen, con lo que le falta

```
DICTAMEN POR CAPACIDAD:  IMPLEMENTADO / VERIFICADO / LIMITADO  -- *con version y evidencia*
  Y de las capacidades del encargo, *** todas tienen evidencia menos UNA ***:
    *** «cinco recetas completas en navegador» *** -- *y esa NO ES UNA LECTURA: ES UN RECORRIDO.*
  -> *** asi que el dictamen se puede escribir HOY, con esa casilla en «LIMITADO». ***
  *** Y escribirlo asi es lo honesto: NO poner «verificado» en algo que no se ha recorrido. ***
```
