# B02/B03 · **La prueba, medida en el fichero**: 226 pasadas de cinco cadenas, y **Lidl ni una**

*(13 de octubre de 2026. **Ya no es una inferencia: esta en `data/runs.csv`.**)*

## 1. Lo que hay en el registro

```
data/runs.csv -- 13558 bytes · 226 filas
columnas: ts · fuente · filas · errores · segundos · ok

  alcampo      48 pasadas registradas
  aldi         44
  carrefour    41
  dia          45
  mercadona    48

  LIDL         *** NI UNA SOLA ***
```

> **El registro existe. Tiene **226 pasadas**. **Cinco cadenas aparecen.** **Y Lidl, ni una vez.***
>
> *Y `ok` es la columna que decidio `completa = not detener and errores == 0` -- *la que `check_drift` usa para
> saber **cual fue la ultima vez que salio bien**.*

## 2. Y esto es lo que convierte la octava correccion en un hecho, no en una deduccion

**Lo que se habia medido**: *«`lidl.py` no contiene `log_run`» -- **una ausencia en el codigo**.*
**Lo que se ha medido ahora**: *«`data/runs.csv` tiene 226 pasadas y **ninguna de Lidl**» -- **una ausencia en los
datos**.*

> ***Y son dos cosas distintas***: *la primera se puede deber a mil motivos; **la segunda es el efecto, y no admite
> interpretacion.***
>
> *Asi que **el cierre de B03 esta incompleto, y ahora se puede decir con el fichero delante***: *Lidl **corre** en
> la pasada diaria -- lo vi en el pipeline -- **pero su pasada NO QUEDA REGISTRADA**, y por tanto **no sirve de
> referencia para `check_drift`, ni cuenta como «la ultima vez que salio bien»**.*
>
> ***Es el unico de los seis, y es el que yo cerre.***

## 3. Y lo que esto cambia, con precision

```
B03, CRITERIO DEL PLAN:  «entrada diaria con cobertura por campo» y «contador visible»
   -> la cobertura por campo:  HECHO (data/cobertura/lidl-2026-10-13.json, 13 campos)
   -> el contador de la pasada:  *** NO *** (log_run nunca se llama)
   -> Y el plan pide «observabilidad». **Lidl es el unico sin registro.**

EL DAÑO CONCRETO, QUE NO ES ABSTRACTO:
   `check_drift` compara contra «la ultima vez que salio bien». Sin registro de Lidl,
   **no hay referencia** -- asi que **una caida de Lidl no se detecta**.
   Y las otras cinco SI la detectan.
```

> *Que es, exactamente, **la clase de fallo que B02 existe para evitar**: **una cadena que deja de capturar y nadie
> se entera.*** *Cinco lo detectarian; **Lidl no**.*

## 4. Y el cambio, ahora con todo medido

```python
# core/runlog.py:10    LOG = config.DATA / "runs.csv"    (se AÑADE, con encabezado si esta vacio)
# y las columnas son:   ts · fuente · filas · errores · segundos · ok

# Asi que en lidl.py:
from core.runlog import log_run
import time

def main(argv=None) -> int:
    t0 = time.monotonic()
    errores = 0
    ...
    # cada salida de fracaso:
        log_run(FUENTE, 0, 1, time.monotonic() - t0)
    # y el exito, con el juicio:
        completa = bool(resumen.get("precios_con_vigencia_comprobada")) and errores == 0
        log_run(FUENTE, len(filas), errores, time.monotonic() - t0, completa)
```

> **Y despues, la comprobacion que cierra el circulo y que **no** es «pasa la suite»**:*
>
> **`data/runs.csv` tiene que pasar de 226 a 227 -- con `lidl` entre las filas.** *Que es **observable**, y es la
> forma de comprobar que un registro funciona: **no que el codigo lo llame, sino que la fila aparezca**.*
>
> ***Es la misma distincion que esta ronda acaba de hacer: la ausencia en el codigo era una sospecha; la ausencia
> en el fichero es un hecho.*** *Y la prueba del arreglo sera **la fila que aparece**.*
