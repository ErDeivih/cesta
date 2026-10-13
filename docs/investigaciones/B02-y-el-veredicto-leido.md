# B02 · **Y el veredicto, leido**: `completa = not detener and errores == 0`

*(13 de octubre de 2026. **La ultima pieza. Y confirma, palabra por palabra, lo que avisaba el docstring.**)*

## 1. Lo que hay, literal

```python
alcampo.py:717:  t0, errores, filas, truncadas = time.monotonic(), 0, [], 0
alcampo.py:950:  completa = not detener and errores == 0
alcampo.py:974:  guardar = completa
```

> **Y ahi esta todo:**
>
>   - **`t0, errores, ... = time.monotonic(), 0, ...`** *-- el reloj y el contador, al principio;*
>   - **`completa = not detener and errores == 0`** *-- ***el veredicto NO es `errores == 0`***: es
>     **`not detener` Y `errores == 0`**.* *Y `detener` es **el circuit breaker** -- *la bandera que se levanta
>     cuando el WAF nos tiene fichados.*
>   - **`guardar = completa`** *-- ***y el veredicto decide si se guarda***.*

## 2. Y esto confirma, palabra por palabra, lo que el docstring avisaba

```
log_run:  «La columna `ok` decide dos cosas: si esta captura sirve de referencia para `check_drift`
           y si cuenta como "la ultima vez que salio bien". DURANTE DIECINUEVE EJECUCIONES se
           calculo aqui dentro como `errores == 0`, QUE NO ES LO QUE EL COLECTOR ENTIENDE POR BUENA.»
```

> **Y el colector entiende por buena `not detener and errores == 0`.** *O sea: **una pasada en la que el WAF no
> nos corto y no hubo errores**.*
>
> ***`detener` es el juicio del colector*** -- *y es exactamente el trozo que **no se puede deducir de los
> numeros**: *que el WAF te haya cortado **no es un error contado**, es **una decision de parar**.*
>
> **Y por eso el veredicto es del colector.** *Que es lo que el docstring decia, y ahora esta **leido**.*

## 3. Y `guardar = completa` es la pieza que explica por que todo esto importa

**El veredicto no es decorativo: decide si se guarda.** *O sea: **una pasada en la que el WAF nos corto NO se
guarda** -- y por tanto **no se sobrescribe la referencia** -- y `check_drift` **sigue comparando contra la ultima
buena**.*

> *Y eso, mirado del derecho, es **exactamente lo que B03 hizo con Lidl sin llamarlo asi**:* **`AVANCE_MINIMO`, y
> «se deja para manana; lo descargado queda en cache».**
>
> ***Los dos colectores estan diciendo lo mismo con dos mecanismos distintos*** -- *y **el de Alcampo esta mejor
> porque queda escrito en el registro**, no solo en la pantalla.*

## 4. Y B02, con esto, no tiene NADA por leer

```
PARA LIDL -- especificado entero:
  t0, errores, filas = time.monotonic(), 0, []      (el molde: alcampo.py:717)
  en cada salida de fracaso:  log_run(FUENTE, 0, 1, time.monotonic() - t0)
  en la salida de exito:      log_run(FUENTE, len(filas), errores, segundos, completa)
  y `completa` = (lo que Lidl entienda por buena) -- Y NO ES `errores == 0`:
      es el juicio del colector, y Lidl no tiene `detener`, asi que el suyo es otro

PARA CARREFOUR Y ALCAMPO:
  el fichero de cobertura por dia -- las 5 lineas de lidl.py:278-285

Y ADEMAS:
  los fixtures en tests/fixtures/ · y la decision del navegador (del propietario)
```

> **Y `completa` para Lidl sale de su propio fracaso leido**: *su salida dice «**no hay precios regionales con
> vigencia comprobada**».* **Asi que su veredicto es algo como «leidas las ofertas, con region acreditada y
> precios vigentes»** -- *y **los datos ya estan en su `resumen`**.*
>
> *Se deja escrito y **no se decide**: porque **el veredicto es de Lidl** -- y esto es, despues de nueve rondas,
> **la unica cosa de B02 que pide un juicio en vez de una lectura**.*
