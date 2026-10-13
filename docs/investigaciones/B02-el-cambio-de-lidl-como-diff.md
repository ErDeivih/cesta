# B02 · **El cambio de Lidl, escrito como diff** -- seis partes, y ninguna es una suposicion

*(13 de octubre de 2026. **Lo unico que falta de B02 para Lidl, con las lineas exactas.**)*

## 1. Lo que Lidl NO tiene, medido

```
lidl.py:  import time         NO
lidl.py:  t0                  NO  (el grep conto una coincidencia dentro de otra palabra)
lidl.py:  errores             NO
lidl.py:  completa            NO
lidl.py:  log_run             NO
```

*Y lo que **si** tiene: `FUENTE`, `len(filas)`, y **`resumen`** -- *con `fichas_leidas`, `productos_padre`,
`guardados`, `fuera_de_alcance`, `en_revision`, `con_precio`, `precios_con_vigencia_comprobada`, `region`.*

## 2. Y el cambio, en seis partes

```python
# 1) IMPORTAR (junto a los otros de core, linea 38)
from core import alcance, config, peticiones
from core.runlog import log_run            # <- NUEVO
import time                                 # <- NUEVO (o `from time import monotonic`)

# 2) ARRANCAR EL RELOJ Y EL CONTADOR (al principio de main, antes de parsear)
def main(argv=None) -> int:
    t0 = time.monotonic()                   # <- NUEVO
    errores = 0                             # <- NUEVO

# 3) CADA SALIDA DE FRACASO -- y hay DOS identificadas:
    if not _robots_permite(f):
        print("  la politica publicada de la web no permite esa ruta: no se pide")
        log_run(FUENTE, 0, 1, time.monotonic() - t0)      # <- NUEVO
        return 1

    print("  no se publica: no hay precios regionales con vigencia comprobada")
    log_run(FUENTE, 0, 1, time.monotonic() - t0)          # <- NUEVO
    return 1

# 4) EL VEREDICTO -- que es lo unico que pide un juicio
    # `completa` NO ES `errores == 0`: en Alcampo es `not detener and errores == 0`.
    # Para Lidl, sus datos estan en `resumen`; y su unico fracaso leido dice
    # «no hay precios regionales con vigencia comprobada». Asi que el juicio es del tipo:
    completa = bool(resumen.get("precios_con_vigencia_comprobada")) and errores == 0
    # ^ Y ESTA ES LA UNICA LINEA QUE HAY QUE PENSAR, no copiar.

# 5) LA SALIDA DE EXITO (donde ya se escribe el bronze y la cobertura)
    log_run(FUENTE, len(filas), errores, time.monotonic() - t0, completa)   # <- NUEVO

# 6) Y LA COBERTURA, QUE YA ESCRIBE -- sin tocar
```

## 3. Y lo que hay que comprobar despues, que no es «pasa la suite»

```
1) que la suite siga en 2025 pasando (los ensayos de Lidl: test_lidl_colector.py)
2) que `log_run` ACEPTE que se le llame dos veces en el mismo proceso -- porque hay
   dos salidas de fracaso y una de exito, y solo una se ejecuta
3) y que el registro salga en el fichero que `log_run` use -- MIRARLO, no suponerlo
4) `ruff check .` limpio
```

> **Y la 3 es la que no se puede suponer**: *`log_run` «apunta la ejecucion» -- **y no se ha mirado donde**.*
> *Puede ser un json, un parquet o una tabla; **y hay que verlo** antes de decir que Lidl «ya registra».*
>
> *Que es, exactamente, la regla de las nueve rondas: **no decir «ya esta» sin haber mirado donde cae**.*

## 4. Y lo que este documento NO hace, y por que

**No se aplica el diff.** *Tiene seis partes en un fichero, **y con el contexto que queda no se puede verificar
como es debido** -- *y un cambio a medias en un colector **deja la captura diaria con un registro que miente**.*

> *Que es peor que no tener registro.* **Un `log_run` que se llama en el fracaso y no en el exito dice que Lidl
> nunca acierta.**
>
> *Asi que se deja escrito, **con sus lineas**, para que se aplique entero y se verifique entero.* **Que es lo que
> estas nueve rondas han estado haciendo: no empezar lo que no se puede terminar bien.**
