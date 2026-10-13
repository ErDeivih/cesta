# B00 · **La guarda, el estado publicado y los contenedores**, verificados al final

*(2026-10-14, ~00:45. **Y es la primera verificacion que el objetivo pide, re-hecha al final.**)*

## 1. Lo que se midio, y es lo que el encargo pide primero

```
*** EL RUNLOCK ***  *`core/runlock.py`*
  l12  *** def ejecucion_exclusiva(path: Path | None = None): *** *
  l25      msvcrt.locking(fh.fileno(), *** msvcrt.LK_NBLCK ***, 1)      *-- Windows*
  l32      fcntl.flock(fh.fileno(), *** fcntl.LOCK_EX | fcntl.LOCK_NB ***)  *-- y POSIX*
  *** -> y `NB` quiere decir NON-BLOCKING: *** *si ya hay una ejecucion, **no espera: sale.** *

*** EL ESTADO PUBLICADO ***  *** `data/gold/v20261013-155356` *** *
  *-- *y es **el mismo que el dictamen de B16 nombra**, *y **el ultimo publicado** (antes, `v20261013-135533`)*

*** LOS CONTENEDORES ***
  `cesta-api-1`  *** Up 39 minutes (healthy) ***   *-- recreada por el cambio del volumen, y **sana** *
  `cesta-db-1`   *Up 12 hours (healthy)*
  `cesta-web-1`  *Up 12 hours*

*** Y LAS SEIS FUENTES ***  *`data/runs.csv`, las ultimas pasadas: *
  *2026-10-13T08:57*  *** aldi ***       2683   0 err   97,9 s
  *2026-10-13T08:57*  *** mercadona ***  4213   0 err   114,0 s
  *2026-10-13T09:08*  *** dia ***        5773   0 err   721,3 s
  *2026-10-13T10:31*  *** carrefour ***  16149  *** 1 err ***  5713,2 s
  *2026-10-13T10:48*  *** alcampo ***    22828  0 err   6732,8 s
  *** y `lidl`: NO APARECE *** *-- porque **el cambio de `ORDEN` es de hoy**, y su primera ocasion es
  la pasada de las 06:00 del 14.*
```

> *** O sea: *** *** **la guarda funciona, el estado publicado es el que el dictamen dice, y los cuatro
> contenedores estan sanos.** *
>
> *** Y **falta Lidl, con su motivo**: *no **porque falle**, *sino **porque todavia no ha corrido.** *
>
> *** Y **carrefour tiene 1 error**, *y **se dice**: *`ok=True` *-- o sea: **la cadena termino bien y anoto un
> error**, *que es **lo que el log existe para contar.** *

## 2. Y el estado del encargo, con lo que queda **y por que no es trabajo**

```
*** LO QUE ESTA, Y ESTA VERIFICADO ***
  B00 *Docker, las cuatro puertas y la guarda* · B01 *las seis fuentes* · B03 · B04 (27/27)
  B05 · B06 · B07 *cerrados como lectura* · *** B08 HECHO y comprobado sobre la SEMANA ENTERA ***
  B09 5 de 5 · B10 7 de 7 · B11 · B12 *contestados*
  *** B13 5 de 5 recorridos · la restriccion medida por los DOS puentes · la aceptacion completa ***
  *** B14 5 de 5 · y el volumen APLICADO *** · *** B15 medido, con el capitulo que le faltaba ***
  *** B16 dictamen escrito y ajustado a la verdad ***

*** Y LO QUE QUEDA, y ninguna de las dos es trabajo de un agente: ***
  *** B02 ***  -> *** una prediccion FECHADA: la pasada de las 06:00 del 14 *** *
     *** -> y vence en unas CINCO HORAS, y se comprueba con UNA linea. *** *
     *** -> y NO se lanza a mano: eso seria tocar el ciclo que el encargo manda verificar. *** *
  *** la restauracion ***  -> *** y restaurar sobre las bases de casa LO PROHIBE EL ENCARGO *** *
     *** -> la copia esta documentada y el volumen aplicado; *lo que falta es **el acto de restaurar**, *
     *** y ese acto el encargo no lo permite. *** *
```

> *** Y **por eso el objetivo sigue ACTIVO y no se marca cumplido**: *** *** **queda una verificacion
> pendiente, y es la unica cosa del encargo que un agente no puede adelantar.** *
>
> *** Y **tampoco se marca bloqueado**: *** *no hay **ningun obstaculo**; *hay **un reloj**, *y **una
> prohibicion que el propio encargo escribio.** *
