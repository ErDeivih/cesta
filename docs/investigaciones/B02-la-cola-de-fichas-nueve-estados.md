# B02 · **La cola de fichas: NUEVE estados, un *lease* de 30 minutos, y `tomar()`**

*(13 de octubre de 2026. **Y es la pieza que hacia automatica la recuperacion.**)*

## 1. `core/inventario.py`, por sus nombres

```
BASE = RAIZ / "data" / "inventario.sqlite"        <- *** 14,7 MB: la cola mas grande del proyecto ***

l37  PENDIENTE        l38  EN_CURSO          l39  CORRECTO
l40  PARCIAL          l41  NO_PUBLICADO      l42  BLOQUEADO
l43  ERROR_TEMPORAL   l44  NO_ENCONTRADO     l45  EXCLUIDO
l46  *** FINALES = (CORRECTO, PARCIAL, NO_PUBLICADO, NO_ENCONTRADO, EXCLUIDO) ***

l48  REVISION_DIAS = 30           # revision ordinaria
l49  REVISION_CONFLICTO_DIAS = 7  # cuando hay conflicto o cambio observado
l50  *** LEASE_MINUTOS = 30 ***

l127 *** def tomar(con, limite: int = 50, *, fuentes: list[str] [...]) ***
```

## 2. Y contesta **la clausula del *lease***, que era la pieza que hacia falta para entenderla

> *** `fichas_lidl.py` decia: *** *** «El *lease* manda: si el proceso se muere a mitad, la ficha vuelve sola a la
> cola -- y no hay que hacer nada especial.» ***
>
> *** Y **aqui esta el como**, con sus tres numeros: ***
>
> ```
> *** LEASE_MINUTOS = 30 ***   -> *una ficha tomada y no terminada **vuelve a la cola a los 30 minutos** *
> *** def tomar(con, limite = 50) ***  -> *** y `tomar` es la que la saca *** -- *con **su limite**, y
>                                 **por fuentes** (`fuentes=[...]`)*
> *** EN_CURSO ***             -> *el estado que tiene **mientras esta tomada**; *y **si el proceso muere**, se queda
>                                 ahi **hasta que el lease vence** -- *y **entonces vuelve a `PENDIENTE` sola.** *
> ```
>
> *** O sea: **la recuperacion es **una resta de tiempo** *** -- *t=0 se toma (`EN_CURSO`), *y **a los 30 minutos,
> lo que siga `EN_CURSO` se considera abandonado y vuelve.** *
>
> *** Y **no hace falta un `finally`, ni un `atexit`, ni un vigilante**: *** *el proximo que llame a `tomar(...)`
> **ve la ficha otra vez** -- *porque **el lease caduco mientras nadie miraba.** *
>
> *** Que es **la forma mas limpia de las catorce**: *** *las otras trece impedian algo **en el momento**; *y esta
> **repara sola con el paso del tiempo** -- *sin **una sola linea de codigo de reparacion.** *

## 3. Y los nueve estados son **la doctrina llevada a su maximo**

```
*** NUEVE estados, y CINCO son FINALES ***
  PENDIENTE · EN_CURSO                                        <- *los dos «en marcha»*
  *** CORRECTO · PARCIAL · NO_PUBLICADO · NO_ENCONTRADO · EXCLUIDO ***  <- *** y los CINCO FINALES ***
  BLOQUEADO · ERROR_TEMPORAL                                  <- *y los dos «vuelve»*
```

> *** Y **nueve** es **el numero mas alto de todo el proyecto** *** -- *porque **`FINALLES` son cinco**:*
>
> ```
> CORRECTO       -> *se leyo y esta bien*
> PARCIAL        -> *se leyo, y **falta algo** -- *y **es un final, no un fallo** (B06)*
> NO_PUBLICADO   -> *la fuente **no lo publica** -- *«un DATO sobre la fuente, no un fallo» (fichas_lidl.py)*
> NO_ENCONTRADO  -> *se busco y **no esta***
> EXCLUIDO       -> *se decidio **no pedirla** -- y **es un final** *
> ```
>
> *** O sea: **cinco formas de terminar, y solo una es «bien»** *** -- *y **las otras cuatro son finales
> legitimos**, *no **fallos pendientes de arreglar.** *
>
> *** Y es **`ABSTIENE` (B09), los cinco motivos (B06), los cuatro de `comprueba_fuente` (B07) y `error_temporal`
> vs `no_publicado` (B02)** *** -- *** llevados a **nueve**, que es **el maximo.**
> *** Decimosexta vez, y la mas grande. ***

## 4. Y dos numeros mas, que son politica y no codigo

```
*** REVISION_DIAS = 30 ***           -- *revision ORDINARIA: **una ficha se vuelve a mirar cada 30 dias** *
*** REVISION_CONFLICTO_DIAS = 7 ***   -- *y **cuando hay conflicto o cambio observado, a los 7** *
```

> *** Y **el comentario del codigo dice que «el contrato la quiere co[n...]»** *** -- *o sea: **el numero no es del
> programador: es del contrato**, *y esta citado.* *
>
> *** Y **la distincion es la del proyecto entero**: *** *la revision **ordinaria** es lenta (30); *y **la que
> responde a un conflicto** es rapida (7) -- *porque **un conflicto es una senal, y una senal se mira antes.** *
>
> *** Y **es la misma logica que `ALERTA_TIPOS`** (`baja_de`, `minimo_90d`, `cualquier_bajada`): *tres plazos, y
> **el que dispara decide la prisa.** *

## 5. Y B02 queda cerrado **con la cola delante**, y no con una afirmacion

```
*** Y ESTA ES LA PIEZA QUE FALTABA PARA ENTENDER EL *LEASE* ***:
  `fichas_lidl.py` decia QUE pasa («la ficha vuelve sola»)
  y `core/inventario.py` dice COMO: *** `LEASE_MINUTOS = 30` + `tomar(...)` + `EN_CURSO` ***
  *** -> la recuperacion es UNA RESTA DE TIEMPO, y no hace falta codigo de recuperacion. ***
```

> *** Y **con esto, B02 no tiene nada «por mirar»**: *** *tiene **tres piezas del punto 189**, *y **una cola con
> nueve estados, un lease de 30 minutos y `tomar()`** -- *y **el unico cabo abierto es la prediccion con hora de
> manana.** *
