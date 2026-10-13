# B02 · **La prediccion esta armada, y ahora tiene hora**: las 06:00 del 14, en menos de seis horas

*(2026-10-14, 00:25. **Y es la comprobacion que B02 dejo fechada, medida en el momento exacto.**)*

## 1. El estado, medido ahora

```
*** LA HORA ***       2026-10-14 *** 00:25 ***
*** LA ULTIMA PASADA ***  2026-10-13T10:48 *** alcampo *** (22828 filas, 0 errores, 6732,8 s)
*** y LIDL ***        *** NO APARECE EN NINGUNA PASADA DEL FICHERO *** *
```

> *** O sea: ***
> ```
> *** la pasada de las 06:00 del 14 NO HA OCURRIDO TODAVIA *** *-- *son las **00:25***
> *** y la ultima pasada es del 13 a las 10:48 *** *
> *** -> y la PREDICCION vence *** *** EN MENOS DE SEIS HORAS *** *
> ```

## 2. Y **por que Lidl no ha corrido nunca**, que es lo que B02 explico

> *** B02 midio que *** *** Lidl **es el sexto en `run.py:40`** *** -- *y **ese cambio es de esta sesion.** *
>
> *** Y **por eso el fichero no tiene ni una fila suya**: *no es que **Lidl falle**; *es que **todavia no ha
> tenido ocasion de correr**, *porque **hasta hoy no estaba en la lista.** *
>
> *** -> y **entonces la proxima pasada no es «una mas»: es LA PRIMERA** *** *-- *y **es la que decide si la
> prediccion se cumple.** *

## 3. *** Y la prediccion, tal y como quedo escrita *** *

```
*** LO QUE B02 PREDIJO: ***
  *** «despues de la proxima pasada de las 06:00, `data/runs.csv` tendra una fila de `lidl`» *** *
  *-- *y **si no la tiene, hay un defecto de verdad** -- *y **no una precaucion en el log.** *

*** Y LA COMPROBACION ES UNA LINEA: ***
  Get-Content data\runs.csv -Tail 8 | Select-String lidl

*** Y LO QUE HAY QUE MIRAR, si aparece: ***
  *** `filas` ***     -> *que **no sea 0**: *0 filas **no es «Lidl corre», *es «Lidl contesta y no trae nada»*
  *** `errores` ***   -> *y **`ok`**
  *** y `segundos` *** -> *y **el presupuesto**: *`LIMITE_POR_EJECUCION = 1000` en `fichas_lidl.py`, *
     *y **`--limite = 3`** en el lanzador -- *o sea: **la primera pasada debe traer unas pocas fichas y salir**,
     *y **no intentar 5.026.** *
```

> *** Y **lo que NO se puede declarar todavia**: *** *** **ni que funciona, ni que no.** *
> *Porque **la comprobacion es una pasada que no ha corrido** -- *y **declarar cualquiera de las dos cosas ahora
> seria exactamente lo que el encargo prohibe: cerrar por cansancio, o por numero de rondas.** *

## 4. Y el estado de B02, **con la prediccion armada y sin vencer**

```
*** B02 · cerrado con prediccion fechada ***
  *** lo que esta medido y hecho ***  -> *`ORDEN` tiene seis y **Lidl es el sexto**; *su **ritmo** (`RITMO: 1.0`)
     esta declarado **con su motivo**; *y `fichas_lidl.py` **contesta cuatro clausulas**: presupuesto, `lease`,
     «fallo de red y dato que falta son estados distintos», *y hash.*
  *** lo que falta ***                -> *** una sola cosa: la pasada de las 06:00 del 14 ***
     *** -> y vence en menos de seis horas, y se comprueba con UNA linea. *** *
  *** y lo que NO se hace ***         -> *no se lanza la pasada a mano para «ver si funciona»: *
     *** eso seria tocar el ciclo que el encargo manda verificar, y no verificarlo. *** *
```

> *** Y **es el cierre mas limpio de todos los paquetes**: *** *** **no hay nada que decidir, nada que
> escribir, y nada que medir ya** -- *solo **esperar a un reloj**, *y **mirar una linea.** *
