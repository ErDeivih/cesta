# B08 · **Los cinco veredictos, y su frase**: «se abstiene -- que es un resultado **valido** y no un fallo»

*(13 de octubre de 2026. **Y es lo que hace que el paso 1 de B08 se pueda escribir sin inventar vocabulario.**)*

## 1. El vocabulario, literal (`core/identidad.py`)

```
l8   *** «puede decidir, SE ABSTIENE -- que es un resultado VALIDO y no un fal[lo]» *** *
l33  *** EXACTO ***       = "exacto"
l34  *** PROBABLE ***     = "probable"
l35  *** ALTERNATIVA ***  = "alternativa"
l36  *** CUARENTENA ***   = "cuarentena"
l37  *** ABSTIENE ***     = "abstiene"
```

> *** Y **la frase de `l8` es la que lo explica todo**: *** *** «puede decidir, **se abstiene** -- *que es
> **un resultado valido** *y **no un fallo**.» *
>
> *** Y **es la misma doctrina, otra vez, y en el sitio donde mas importa**: *** *en **el que decide si dos
> productos son el mismo.** *Porque **el error caro no es abstenerse**: *es **decidir mal** -- *y **decidir mal
> aqui** significa **sumar la nutricion de dos cosas distintas**, *o **comparar dos precios que no lo son.** *
>
> *** Y **los cinco estados dicen mucho**: ***
> ```
> *** `EXACTO` ***       -> *y **se puede afirmar** *
> *** `PROBABLE` ***     -> *y **se puede afirmar, diciendo que es probable** *
> *** `ALTERNATIVA` ***  -> *** y aqui entra el encargo: «un articulo elegido SOLO ADMITE ALTERNATIVAS
>                            AUTORIZADAS» *** -- *o sea: **hay alternativa, y la autoriza la persona** *
> *** `CUARENTENA` ***   -> *y **se aparta** (y `cobertura.py:142`: «un bronze malo se **aparta, no se borra**»)*
> *** `ABSTIENE` ***     -> *** y no se decide, y es valido *** *
> ```

## 2. *** Y por eso el paso 1 de B08 **no necesita vocabulario nuevo** ***

```
*** LO QUE B08 NECESITA POR INGREDIENTE, y ya tiene nombre: ***
  *** `EXACTO` / `PROBABLE` ***  -> *hay `producto_id` -> **hay nutricion** -> *suma, y cuenta en `con_dato`*
  *** `ALTERNATIVA` ***           -> *y **se ofrece**, y **la persona autoriza** (`lista_linea.autorizado`)*
  *** `CUARENTENA` ***            -> *y **se aparta con su motivo** *
  *** `ABSTIENE` ***              -> *** y entra en `sin_dato` CON SU NOMBRE *** -- *como `desde-la-compra`*
  *** y sin cantidad ***           -> *y **el puente ya lo dice**: `sin_cantidad`*
```

> *** O sea: *** *** **la prevision tiene el vocabulario entero, y solo le falta el encadenamiento.** *
> *Y **la respuesta a «¿y si no lo se?» ya esta escrita en el proyecto, y con estas palabras: ***
> *** «es un resultado valido y no un fallo». *** *

## 3. Y **el estado del paso 1**, cerrado en su diagnostico

```
*** EL PASO 1 DE B08: resolver el `producto_id` de cada ingrediente ***
  *** lo que hay ***      -> *`tokens`, `trigramas`, `parecido` (con pesos), `decide`, `nivel`, *
                             *`candidatos_por_gtin`, `candidatos_por_bloque`, `ampliar_grupo`, `precio_imposible`*
  *** lo que falta ***    -> *** el que las encadena ***: *nombre -> candidatos -> veredicto*
  *** y el vocabulario *** -> *** los CINCO veredictos, incluido `ABSTIENE` *** *
  *** y el sitio ***       -> *`lista_linea`: `cadena_elegida`, `autorizado`, `autorizado_producto`*
  *** y el patron de la cobertura *** -> *`desde-la-compra`: `{con_dato, total}` y `sin_dato` con nombres*
```

> *** Y **no se escribe codigo en esta ronda**, *y se dice por que: *el encadenamiento **toca el nucleo del
> emparejador**, *y **una version a medias seria peor que ninguna** -- *porque **un resolutor que decide mal**
> *mete **un numero equivocado** en una prevision, *y **eso es exactamente lo que el encargo prohibe**: *
> *«no inventes calorias», *y *«lo que no se sabe sigue sin saberse». *
>
> *** Y **lo que si queda hecho es el trabajo previo, y no es poco**: *** *** el hueco **localizado en dos
> pasos**, *las **piezas inventariadas con sus nombres y sus lineas**, *y **el vocabulario de la respuesta
> encontrado** -- *que es **lo que hace que el paso 1 sea escribible sin decidir nada nuevo.** *
