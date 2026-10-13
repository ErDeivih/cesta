# B10 · **El fallo del propietario, documentado en el codigo con su arreglo** -- y las dos reglas opuestas

*(13 de octubre de 2026. **Sexta ronda de B10. Y esta es la respuesta literal a la restriccion del propietario.**)*

## 1. El docstring, literal (`plataforma/api/almacen.py:415`)

```python
    """...
    `momento` es la hora del MOVIL, no la de llegada: tachar sin cobertura a las
    18:04 y subirlo a las 18:20 cuenta como las 18:04, **que si no el orden de los
    hechos se lo inventa el servidor.**
    """
    cuando = momento or datetime.now(timezone.utc)

    if tachado is True:
        trozos.append("en_carrito = true")
        # COALESCE: si ya estaba tachado, se respeta el primero.
        trozos.append("tachado_en = LEAST(COALESCE(tachado_en, %s), %s)")

    if cantidad is not None:
        # **Gana el MAS NUEVO, no el que llega ultimo.** *Esto era `cantidad = %s` con el come[ntario]
        # «el ultimo, a proposito», y ese «ultimo» era **el ultimo que llega** -- asi que dos p[ersonas]
        # cambiando la cantidad sin cobertura se pisaban, y **ganaba la de las 17:50 que llego [a las]
        # 18:31**. El orden de los hechos se lo inventaba el servidor.*
        #
        # *La regla vive en la migracion `019`, que trae `cantidad_en`*: **la cantidad no se e[scribe si]
        # llega una mas vieja que la que ya consta.** *`COALESCE(cantidad_en, 'epoch')` deja g[anar a]
        # cualquier cambio con hora frente a una linea que nunca cambio de cantidad* -- *y ahi [el epoch]
        # significa «no consta», no «cambio en el origen de los tiempos».*
        #
        # **Y es `GREATEST`, al contrario que el tachado**, que usa `LEAST`. *No es una incohere[ncia]:
        # tachar es «yo lo hice primero» y **gana el primero**; la cantidad es «este es el val[or de]
        # ahora» y **gana el mas nuevo**. *Dos reglas opuestas, cada una con su motivo.*
        trozos.append(
            "cantidad = CASE WHEN %s >= COALESCE(cantidad_en, TIMESTAMPTZ 'epoch') "
            "THEN %s ELSE cantidad END")
        trozos.append("cantidad_en = GREATEST(COALESCE(cantidad_en, %s), %s)")
```

## 2. Y el fallo del propietario **esta escrito ahi, con el numero de linea**

> *** La restriccion decia: *** *«el fallo de que 300 g necesarios terminan como **una unidad y una nota de 100 g**,
> **descartando la segunda receta como repetida**.»*
>
> *** Y el codigo dice: ***
>
> ```
> «Esto era `cantidad = %s` con el comentario **"el ultimo, a proposito"**,
>  y ese "ultimo" era EL ULTIMO QUE LLEGA --
>  asi que dos personas cambiando la cantidad sin cobertura SE PISABAN,
>  y GANABA LA DE LAS 17:50 QUE LLEGO A LAS 18:31.»
> ```
>
> *** O sea: **el defecto es exactamente «gana el que llega despues»** *** -- *y **el propietario lo describio como
> «descartando la segunda receta como repetida»**: *la segunda receta **llegaba despues** **y se descartaba**, *o
> **llegaba antes y la pisaba la primera**.*
>
> *** Y **la correccion esta hecha, y dice como**: ***
>
> ```
> ANTES:  cantidad = %s                          <- «el ultimo» = el ultimo que LLEGA    *** EL FALLO ***
> AHORA:  cantidad_en = GREATEST(...)             <- gana el MAS NUEVO *por el reloj del movil*
>         tachado_en  = LEAST(...)                <- y el tachado, el PRIMERO
> ```

## 3. Y las tres frases que hay que subrayar

### a) «`momento` es la hora del MOVIL, no la de llegada»

> *** El reloj que decide **no es el del servidor**: *** *es **el del telefono que hizo el cambio** -- *y el ejemplo
> esta dado: **tachar sin cobertura a las 18:04 y subirlo a las 18:20 cuenta como las 18:04.** *
>
> *** O sea: **la hora viaja con la intencion, no con el mensaje** *** -- *que es **lo que hace que un reintento o un
> cambio offline no mientan sobre cuando ocurrieron.** *

### b) «que si no **el orden de los hechos se lo inventa el servidor**»

> *** Y esto es **la doctrina, otra vez** *** -- *pero **en su forma mas directa**: *si el servidor decide el orden por
> **cuando le llego**, **esta inventando cuando ocurrio.** *
>
> *** Decimonovena vez. Y es **la que el propietario pedia**. ***

### c) «**GREATEST**, al contrario que el tachado, que usa **LEAST** -- dos reglas opuestas, cada una con su motivo»

> *** Y aqui esta **lo mas fino de todo el proyecto**, y **no se puede adivinar**: ***
>
> ```
> TACHAR  (en_carrito)  -> `LEAST`    -> «YO LO HICE PRIMERO»      -> *** GANA EL PRIMERO ***
> CANTIDAD (cantidad)   -> `GREATEST` -> «ESTE ES EL VALOR DE AHORA» -> *** GANA EL MAS NUEVO ***
> ```
>
> *** O sea: **el proyecto NO usa una sola regla de conflicto** *** -- *usa **la que corresponde a lo que la persona
> quiso decir**, y **lo dice**: «**no es una incoherencia**».*
>
> *** Y es **la respuesta a la restriccion del propietario, y mejor que la que yo habria escrito**: *** *el tachado
> **no se puede deshacer por llegar tarde** (gana el primero), y **la cantidad si se puede corregir** (gana el mas
> nuevo) -- *porque **decir «ya lo cogi» es un hecho pasado**, y **decir «son 300 g» es un valor presente.** *

## 4. Y un detalle del `COALESCE` que vale por si solo

> *** «`COALESCE(cantidad_en, 'epoch')` deja ganar a cualquier cambio con hora frente a una linea que **nunca cambio
> de cantidad** -- *y ahi **el epoch significa «no consta»**, no «cambio en el origen de los tiempos».» ***
>
> *** O sea: **el `epoch` (1970) no es una fecha: es un centinela** *** -- *y **el codigo lo dice**, para que nadie
> lo lea como una fecha real.*
>
> *** Y es **la misma familia que `SIN_CAMBIAR = object()`** (B05): **un valor que no significa lo que parece, y
> dicho.** *

## 5. Y B10 queda con **cinco de seis**, y la restriccion del propietario **localizada, con linea**

```
  1) LOS ESTADOS           *** `cambia_linea` LEIDO en su parte que importa *** -- `LEAST`/`GREATEST`,
                           `COALESCE(cantidad_en, 'epoch')`, y «la hora del movil»
  2) LAS LISTAS Y EL ORDEN HECHO -- 15 ensayos
  3) BUSCAR Y FILTRAR      *** POR MIRAR *** -- «marca/formato/EAN y filtros utiles»
  4) LA PAGINACION         MEDIDA -- `limite` con cotas; sin `cursor`/`version`/`offset`
  5) EL GASTO Y EL AHORRO  HECHO -- 17 ensayos
  6) Y LA DUREZA           HECHO -- 5 ensayos, y **la regla esta en `almacen.py:415-448`**
```

> *** Y la restriccion del propietario **no esta pendiente**: esta **implementada y documentada** *** -- *con **el
> defecto escrito** («esto era `cantidad = %s`... y ganaba la de las 17:50 que llego a las 18:31»), **la correccion
> escrita** (`GREATEST` + `cantidad_en`), **la migracion que la trae** (`019`), **los cinco ensayos que la prueban**,
> *y **la razon de que sea `GREATEST` y no `LEAST`.** *
>
> *** Y lo que queda por comprobar **no es si esta**: *** *es **si los DOS puentes la usan** -- *que es **exactamente
> lo que la restriccion añade**: «afecta a **AMBOS** puentes de transferencia (receta->lista y plan->lista)».*
