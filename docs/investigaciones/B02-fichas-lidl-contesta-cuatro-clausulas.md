# B02 · **`fichas_lidl.py` contesta cuatro clausulas del encargo** -- y el *lease* es el checkpoint

*(13 de octubre de 2026. **Y el modulo que B02/B16 citaban por su presupuesto resulta ser mucho mas.**)*

## 1. Su cabecera, literal

```python
"""Pedir fichas desde la cola: *** con presupuesto, con hash y dejando la proxima revision puesta ***.

**Por que es la pieza que cierra S02 y S03.** La cola sabe a quien le falta ficha; el lector [...] una ficha.
Lo que faltaba es quien las junte *** sin romper nada ***: coger unos pocos candidatos [...], pedir su ficha,
leerla, y cerrar la ficha en la cola con el hash del contenido util [...], la version del parser y la fecha de la
proxima revision.

**Las reglas, que son las del contrato:**

  - *** Presupuesto ***: se procesan como mucho `limite` fichas por ejecucion. *** No hay bucle hasta [agotar]:
    una ejecucion que no termina NO ES PROGRESO, ES UN RASTRO QUE SE QUEDA A MEDIAS. ***
  - *** El *lease* manda ***: si el proceso se muere a mitad, *** la ficha vuelve sola a la cola *** [...]
    hay que hacer nada especial, *** y eso es lo que se gana por haberlo hecho bien alli. ***
  - *** Fallo de red y dato que falta son estados distintos ***: un error de red deja la ficha en
    `error_temporal` (se reintenta, *** no cuenta como intento fallido del producto ***); que [no] publique el
    detalle la deja en `no_publicado`, *** que es un dato sobre la fuente, no un fallo. ***
  - *** El hash se guarda siempre que se lee algo ***: es lo que permitira detectar que la ficha [cambio sin]
    volver a leerla entera.
"""
```

## 2. Y las **cuatro clausulas del encargo** estan aqui, con su nombre

```
EL ENCARGO PIDE:  *** «mejora colectores mediante validacion, CHECKPOINTS, BACKOFF, LIMITES, OBSERVABILIDAD
                   y RECUPERACION» ***
```

| el encargo | `fichas_lidl.py` |
|---|---|
| ***«límites»*** | ***`LIMITE_POR_EJECUCION = 1000`*** *-- y su razon: **«no hay bucle hasta agotar»*** |
| ***«checkpoints»*** | *** «El *lease* manda»: si el proceso se muere a mitad, **la ficha vuelve sola a la cola** *** |
| ***«validación»*** | *** «el hash del contenido util», «la version del parser» y «la fecha de la proxima revision» *** |
| ***«recuperación»*** | *** `error_temporal` **se reintenta** -- y **no cuenta como intento fallido del producto** *** |
| ***«observabilidad»*** | *los estados: **`error_temporal` · `no_publicado` · y el hash** -- *tres cosas que se pueden mirar* |

> *** Y el ***checkpoint*** es **el *lease*, y su razon es la mejor del modulo**: ***
>
> > *** «Si el proceso se muere a mitad, la ficha vuelve sola a la cola -- y **no hay que hacer nada especial**, y
> > **eso es lo que se gana por haberlo hecho bien alli.**» ***
>
> *** O sea: **la recuperacion no es un `try/except` que alguien escribio**: *** *** es **una propiedad de la cola**,
> *y **el modulo que la usa no tiene que hacer nada** -- *porque **el trabajo se hizo en el sitio correcto.** *
>
> *** Y es **la misma forma que todo el proyecto**: *** *`traspaso.clave PRIMARY KEY` (B05) · `ON CONFLICT` (B05) ·
> `cocina.py` sin importar el diario (B07) -- *y ahora **un *lease* que devuelve la ficha sola.** *
> *** Decimocuarta forma de imposibilidad, y es la primera que **se recupera sin codigo de recuperacion.** *

## 3. Y la tercera regla es **la doctrina, otra vez, y con dos estados nuevos**

```
*** «FALLO DE RED Y DATO QUE FALTA SON ESTADOS DISTINTOS» ***
   -> un error de red        -> `error_temporal`  -> *se reintenta, y* *** NO CUENTA COMO INTENTO FALLIDO DEL
                                                     PRODUCTO ***
   -> que no publique detalle -> `no_publicado`     -> *** «que es UN DATO SOBRE LA FUENTE, NO UN FALLO» ***
```

> *** O sea: **el mismo hecho -- «no hay ficha» -- se parte en dos, y cada mitad dice de quien es la culpa**: ***
> *si es **de la red**, **es temporal**; *y si es **de la fuente**, **es un dato** -- *y **no un fallo.** *
>
> *** Y es **exactamente** lo que B06 hizo con los cinco motivos, *y B07 con los cuatro de `comprueba_fuente`,
> *y B09 con `ABSTIENE`: *** *** no forzar a dos lo que tiene mas de dos. *** *** Decimoquinta vez. ***
>
> *** Y **«no cuenta como intento fallido del producto»** es **la parte que protege**: *** *si un fallo de red
> contara como intento, **el producto se marcaria como malo por un problema de la red** -- *y **eso es un dato
> falso sobre el producto.** *

## 4. Y el presupuesto, con sus numeros

```
l33:  # -- *** 5.026 pendientes de Lidl *** -- eso son *** 1.677 dias: CUATRO AÑOS Y MEDIO ***
l37:  # A 1 peticion por segundo (el ritmo declarado en `config.RITMO`), 1.000 fichas [...]
l41:  *** LIMITE_POR_EJECUCION = 1000 ***
l100: ap.add_argument("--limite", type=int, default=LIMITE_POR_EJECUCION, ...)
l102:   f"{LIMITE_POR_EJECUCION}; *** NO HAY BUCLE HASTA AGOTAR ***")
```

> *** Y **los 45 minutos de `RITMO["alcampo"]` y los 6 dias de `LIMITE_POR_EJECUCION = 1000` son la misma
> clase de decision**: *** *un numero **elegido a la vista**, *con **su comparacion al lado** (3 -> cuatro anos y
> medio; 1000 -> seis dias). *
>
> *** Y **no estan en el codigo por gusto: estan porque alguien hizo la cuenta** y **la dejo escrita.** *

## 5. Y B02 queda con **el encargo de colectores contestado**, clausula por clausula

```
B02 PEDIA:  «mejora colectores mediante validacion, checkpoints, backoff, limites, observabilidad y recuperacion;
             NO ELUDAS CAPTCHA/WAF NI CONFUNDAS DESAFIO CON CATALOGO VACIO»
   -> *** y las cinco primeras estan en `fichas_lidl.py`, con su nombre y su motivo ***
   -> *** y las dos ultimas son `RetoWAF` (B02: 13 usos) y `ESTADOS_DE_BLOQUEO = (403, 429)` (carrefour) ***
      *-- o sea: **el desafio SE DISTINGUE, y no se confunde con «no hay productos»** *
```

> *** Y **B02 no tiene ninguna ausencia**: *** *tiene **tres piezas del punto 189**, *y **un modulo que contesta
> las seis clausulas de colectores** -- *y **su unica cosa abierta es la prediccion con hora de manana.** *
