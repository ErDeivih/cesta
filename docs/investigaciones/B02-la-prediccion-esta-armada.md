# B02 · **La prediccion esta armada**: la tarea corre manana a las 06:00, y el arreglo entro despues de la de hoy

*(13 de octubre de 2026. **Octava ronda de B02 en este tramo. Y la prediccion queda verificada en sus dos extremos.**)*

## 1. La tarea, medida

```
$ schtasks /query /tn "Cesta diaria"

  Nombre de tarea   *** Hora proxima ejecucion   Estado ***
  Cesta diaria      *** 14/10/2026 6:00:00 ***   *** Listo ***
```

> *** Y **coincide con lo que B01 dejo anotado**: «tarea Ready (**14/10 06:00**)». *
>
> *** O sea: **la tarea existe, esta lista, y su proxima ejecucion es manana a las seis.** *

## 2. Y la cronologia del dia encaja **entera**, sin forzar nada

```
*** 06:00 (hoy, 13/10)  *** la tarea corre `ejecutar.bat` -- *y corre las SEIS, con Lidl incluido*
*** 09:08  dia        *** 5773 filas · 0 err · ok=True
*** 10:31  carrefour  *** 16149 filas · 1 err · ok=True
*** 10:48  alcampo    *** 22828 filas · 0 err · ok=True      <- *** la ultima pasada registrada ***
*** 16:15  `5039b9c`  *** el arreglo: `log_run` entra en el `--escribir`   *** <-- DESPUES de la pasada ***
*** manana 06:00     *** *** la PRIMERA pasada con el arreglo puesto ***
```

> *** Y **la cronologia explica las tres cosas a la vez**: ***
>
>   1. **por que `runs.csv` no tiene Lidl** *-> porque **su registro cambió a las 16:15**, *y la pasada fue a las 09-11;*
>   2. **por que el arreglo es correcto** *-> porque **`log_run` dentro del `--escribir`** evita el **fantasma de un
>      ensayo**, *que fue **el fallo que la ronda 123 encontro**;*
>   3. *** y por que manana es la prueba *** -> *porque **es la primera vez que las dos cosas coinciden**: *Lidl
>      **en el ciclo** (`ORDEN`), *y **el registro puesto** (`5039b9c`). *
>
> *** O sea: **no hay nada que arreglar, y hay una cosa que comprobar** *** -- *y **la comprobacion tiene hora.** *

## 3. Y la prediccion, con sus dos resultados posibles

```
*** MANANA 14/10 A LAS 06:00, `ejecutar.bat` corre las seis ***
   la comprobacion (una linea):
      Get-Content data\runs.csv -Tail 8 | Select-String lidl

   *** SI SALE una fila de lidl ***  -> *el arreglo funciona, y **Lidl queda verificado en el ciclo***.
       Y hay que mirar `filas` y `ok`: *si `ok=True` y `filas` es un numero de verdad, **la sexta fuente
       esta en el ciclo, con su pasada registrada.** *

   *** SI NO SALE ***  -> *** entonces SI hay un fallo ***, *y **las dos cosas a mirar son**:
       a) *** si `run.py` pasa `--escribir` a Lidl *** -- *y **el comentario l.44-48 dice que va con `--web`
          a proposito**, asi que **se le pasa**;*
       b) *** «la segunda mitad del punto 189 de G09» *** -- *que **esta nombrada en el comentario y no se ha
          leido**, y **es la unica pieza que queda sin explicar.** *
```

## 4. Y lo que esto deja, como cierre de B02

```
LO QUE B02 PEDIA Y ESTA:
  *** «Lidl en el MISMO ciclo diario» ***   -> `ORDEN = [..., "lidl"]` (run.py:40), y el comentario lo explica
  *** «y en API/UI» ***                      -> B03: superficie, columna `region`, cobertura por zona
  *** «no lo declares completo por un sitemap» ***  -> *y **el alcance esta DICHO**, y **su limite tambien**
  *** «mejora colectores: validacion, checkpoints, backoff, limites, observabilidad y recuperacion» ***
      -> **y el defecto que costaba una busqueda esta ESCRITO**, con su sintoma:
         *** «el dia seguia sin Lidl, con un aviso en el log que PARECIA UNA PRECAUCION» ***

LO QUE QUEDA, Y NO SE ESCONDE:
  *** una prediccion con hora: manana 06:00 *** -- *y **la linea que la comprueba.** *
  *** y «la segunda mitad del punto 189 de G09» *** -- *nombrada, **y sin decir que falte**, porque NO SE HA LEIDO.*
```

> *** Y **es el mejor estado posible para un paquete que no se puede terminar hoy**: *** *** todo lo que se puede
> averiguar, averiguado; **una prediccion con hora**; *y **el nombre exacto de la unica pieza que queda**, *en el
> comentario de quien lo arreglo.* *
