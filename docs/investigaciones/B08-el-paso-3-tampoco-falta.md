# B08 · **El paso 3 NO falta**: `cesta.py` ya resuelve **«que producto concreto resuelve una linea en una cadena dada»**

*(13 de octubre de 2026. **Y reduce B08 a encadenar, no a construir.**)*

## 1. Lo que hay, literal

```
`plataforma/api/cesta.py`
l98    *** """Que producto concreto resuelve una linea en una cadena dada.""" *** *
l200   *** """Por cada linea y cadena, el producto mas barato que la resuelve.""" *** *
l261      # *** **El emparejamiento, por las dos vias.** *** `k` es `(grupo, producto)`, y `dueno_fila` es de [...]
l364   def _promos_vigentes(producto_ids: set[str], fecha_tope=None) -> dict[str, str]
l594      # *** orden a proposito: *** una cadena que resuelve todas las lineas pero **no autoriza ninguna** no puede [...]
l729      # *** `sin_autorizar` entra en la comparacion: *** un reparto que resuelve todo sin autorizar nada no [...]
l1173  if str(campo(alternativa, "producto_id")) != str(peticion.*** autorizado_producto ***):
```

> *** O sea: *** *** **la resolucion «linea -> producto concreto en una cadena» YA ESTA HECHA**, *y **con sus
> dos variantes**: *el **producto concreto**, *y **el **mas barato** que la resuelve.** *
>
> *** Y **es exactamente el paso 3 de B08** *** -- *y **no hay que construirlo.** *

## 2. *** Y el `l184-186` es el mejor parrafo del asunto: **el proyecto ya espera un dato que no llega** ***

> *** «...emparejador (`projects/cesta/emparejar.py`). *** *** Y ESE FICHERO NO LA TIENE TODAVIA. *** ***
> *** Asi que la columna se pide *** *** SI ESTA *** ***, y el dia que el emparejador la escriba, ***
> *** LLEGA SOLA *** *** -- *sin tocar [nada].» *

```
*** O SEA: ***
  *** hay una COLUMNA que el emparejador todavia no escribe ***
  *** y el consumidor la pide *** «si esta» *** -- *o sea: **sin romperse si falta** *
  *** y el dia que se escriba, *** «llega sola, sin tocar nada» *** *
```

> *** Y **es el mismo patron que `CESTA_ORIGENES` y que el `ro`**: *** *** **el proyecto se prepara para el dato
> que falta, y no para el que tiene.** *
>
> *** Y **es lo contrario de un `TODO`**: *** *un `TODO` **espera a que alguien lo haga**; *y esto **ya
> funciona sin el dato**, *y **mejorara solo cuando llegue.** *
>
> *** Y **por eso `producto_id` salio `null` para el tomate**: *** *** no porque **no haya resolutor**,
> *sino porque **la columna que lo trae no la escribe todavia el emparejador** *-- *y **el codigo lo dijo sin
> romperse.** *

## 3. *** Y ESO CAMBIA EL ESTADO DE B08: de «falta un paso» a «hay que encadenar» ***

```
*** LA PREVISION, paso a paso, y ahora: ***
  1. las recetas del plan          -> *** HECHO ***  (`GET /api/recetas/plan`: `comensales`, `version`)
  2. y sus ingredientes, escalados -> *** HECHO ***  (`core/recetas.py:134 escala` + «las dos cifras»)
  3. *** de la linea a un PRODUCTO *** -> *** HECHO EN `cesta.py:98` Y `:200` *** ✓✓✓
     *«que producto concreto resuelve una linea en una cadena dada»*
     *** y su limite, dicho por el codigo: la columna que lo trae la escribe `emparejar.py`, *
     *** y «ese fichero no la tiene todavia» *** *
  4. y del producto a nutrientes   -> *** HECHO ***  (`catalogo.producto(id)` + `diario.de_ficha(producto, gramos)`)
  5. y escalar por cantidad        -> *** HECHO ***  (`de_ficha` toma `gramos`)
  6. *** y sumar CON COBERTURA ***   -> *** HECHO ***  (`diario.suma()`, `_cobertura()`, `conocido`, `completo`)
  *** -> LOS SEIS PASOS EXISTEN. *** *
```

> *** Y **entonces, ¿que falta?** *** *** **encadenarlos en una vista**, *y **decir la cobertura.** *
>
> *** Y **falta tambien una cosa del paso 3, y hay que decirla**: *** *`cesta.py` resuelve **por cadena**
> («en una cadena dada»), *y **una prevision necesita saber LA CADENA** -- *y **eso es la decision de la
> persona** («un articulo elegido solo admite **alternativas autorizadas**»). *
>
> *** Y **el sitio existe**: *** *`lista_linea` con **`cadena_elegida`**, **`autorizado`** y
> **`autorizado_producto`** *-- *o sea: **la prevision puede usar la cadena que la lista ya tiene.** *

## 4. Y la conclusion, sin exagerar en ninguna direccion

```
*** LO QUE SE PUEDE DECIR, MEDIDO: ***
  *** 1. la vista de previstos NO existe ***  *-- confirmado por cuatro vias (nombres, frontend, API/core, ensayos)*
  *** 2. y sus SEIS pasos SI existen, y cada uno en su sitio, con su nombre y su linea *** *
  *** 3. y el paso 3 tiene un limite escrito por el propio codigo: *** *
        *** la columna que trae el producto la escribe `emparejar.py`, y «ese fichero no la tiene todavia» *** *

*** LO QUE NO SE DECLARA: ***
  *** no se declara «hay que construir la prevision» *** -- *porque **sus piezas estan**; *
  *** ni «ya esta» *** -- *porque **la vista no existe**, *y **el paso 3 depende de una columna que falta.** *
```

> *** Y **la frase que mejor lo resume es del propio proyecto**, *en `cesta.py:184`: ***
> *** «la columna se pide si esta, y el dia que el emparejador la escriba, llega sola -- sin tocar nada.» *** *
