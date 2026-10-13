# B08 · **LA ESPECIFICACION de la vista de previstos** -- para escribirla sin decidir nada nuevo

*(13 de octubre de 2026. **Y es el siguiente paso, con sus entradas, sus piezas y su salida ya fijadas.**)*

## 1. Por que una especificacion y no codigo, dicho claro

> *** Los **seis pasos** de la prevision **existen** (medido en las rondas 262-268), *y **lo que falta es
> encadenarlos y darles salida.** *
>
> *** Y **encadenar** toca **el nucleo del emparejador y la API**, *y **una version escrita a medias seria peor
> que ninguna**: *un encadenamiento que decida mal *mete **un numero equivocado** en una prevision, *y **eso es
> exactamente lo que el encargo prohibe** («no inventes calorias», *«**lo que no se sabe sigue sin saberse**»). *
>
> *** Asi que **lo que se fija aqui es la forma**, *con **cada pieza citada por su fichero y su linea**, *
> *para que **escribirla no exija decidir nada nuevo.** *

## 2. La funcion, y sus entradas

```
*** NOMBRE: ***  `prevision(con, propietario, desde, hasta, *, cadena=None)`
*** DONDE: ***   `plataforma/api/` -- *y **junto a las rutas del plan** (`recetas.py` tiene `/plan`)*

*** ENTRADAS: ***
  `propietario`  -> *el dueno del plan (la sesion ya lo da: `usuario_actual`)*
  `desde`,`hasta` -> *** y son OBLIGATORIOS *** *-- *como en `desde-el-plan` (422 sin ellos, medido)*
  `cadena`       -> *** y es la decision de la persona *** *-- *y si no viene, **no se adivina**:
                    *se usa la de la lista (`lista_linea.cadena_elegida`), *y **si tampoco hay, `ABSTIENE`** *
```

## 3. *** Y el algoritmo, con cada pieza citada ***

```
*** 1) EL PLAN ***             `GET /api/recetas/plan?desde=&hasta=`   (`recetas.py:107`)
     -> *da, por entrada: `fecha`, `receta_id`, `*** version ***`, `*** comensales ***`, `nombre`*

*** 2) LA RECETA, ESCALADA ***   `core/recetas.py:134 escala(ingredientes, de_raciones, a_raciones)`
     -> *y `recetas.py:173-182` ya devuelve *** «las dos cifras» ***: `raciones` y `raciones_receta`,
        *y `*** escalada ***`*
     *** -> o sea: se pide `raciones = comensales`, y el escalado sale de ahi, sin calcularlo a mano. ***

*** 3) DE LA LINEA AL PRODUCTO ***  `plataforma/api/cesta.py:98` y `:200`
     -> *** «que producto concreto resuelve una linea en una CADENA DADA» *** *
     -> *y `cesta.py:184`: *** «la columna se pide si esta, y el dia que el emparejador la escriba, llega sola» *** *
     *** -> y si NO hay producto: *** *** `ABSTIENE` *** *-- *y **la linea va a `sin_dato` CON SU NOMBRE.** *

*** 4) DEL PRODUCTO A NUTRIENTES ***  `plataforma/api/catalogo.py` (`producto(id)`) + `core/diario.py:235`
     -> *** `de_ficha(producto, gramos)` *** *-- *y **toma `gramos` directamente.** *

*** 5) LA CANTIDAD ***  *de la linea (`cantidad`, `unidad`) -- *y el puente **ya la lee** (`sin_cantidad`)*

*** 6) LA SUMA, CON COBERTURA ***  `core/diario.py:287` y `:307`
     -> *** `_cobertura(filas, columna, total)` *** *-> `{con_dato, total, completa}`* *** POR NUTRIENTE *** *
     -> *y el subtotal se llama *** `conocido` *** y **no `total`** *-- *y **`suma()` devuelve `None`, no 0.** *
```

## 4. La salida, y su forma

```
{
  "desde": ..., "hasta": ...,
  "*** dias ***": [
    { "fecha": "...",
      "*** comidas ***": [
        { "*** receta_id ***": 1, "*** version ***": 1, "*** comensales ***": 2,
          "*** lineas ***": [
            { "texto": "tomate", "cantidad": 300.0, "unidad": "g",
              "*** veredicto ***": "*** abstiene ***",       <- *los cinco de `identidad.py:33-37`*
              "producto_id": null, "cadena": null,
              "*** nutrientes ***": {"kcal": null, "proteinas_g": null, ...} } ] } ],
      "*** conocido ***": {"kcal": ..., "proteinas_g": ..., "grasas_g": ..., "hidratos_g": ...},
      "*** cobertura ***": {"kcal": {"con_dato": 0, "total": 3, "completa": false}, ...},
      "*** completo ***": false } ],
  "*** sin_dato ***": ["tomate"],          <- *** con su nombre, como `desde-la-compra` ***
  "*** sin_cantidad ***": []
}
```

> *** Y **tres cosas de la forma son obligatorias, y las tres vienen del proyecto**: *
> ```
> *** `conocido` y NO `total` ***          -> *`diario.py:296`: «a proposito»*
> *** `cobertura` POR NUTRIENTE ***        -> *`diario.py:288`: «la cobertura es por nutriente»*
> *** y `sin_dato` CON SU NOMBRE ***       -> *`main.py:1687`: «anotar las que se puede y callar las demas
>                                            convertiria un dato que falta en una comida que parece completa»*
> ```

## 5. *** Y el ensayo, con los numeros del plan ***

```
*** EL CRITERIO DEL PLAN (B08): ***  *«Aceptar *** R1=270, media=135 ***, ausencia de energia con proteina
conocida, idempotencia, recarga y aislamiento A/B» *

*** EL ENSAYO, y sus casos: ***
  1. *** una receta con producto resuelto ***  -> *da `kcal` conocida, *y `con_dato == total` -> **`completa`** *
  2. *** una receta con un ingrediente sin resolver *** -> *** y la energia queda `None` ***, *
     *y **la proteina SI se suma** *si su producto la tiene -- *y **`completa` es false SOLO para `kcal`** *
     *** -> y ESE es el caso «ausencia de energia con proteina conocida» que el plan pide *** ✓✓✓
  3. *** y una receta sin ningun producto *** -> *** `conocido.kcal is None` *** *-- *y **NO 0** *
  4. *** y jamás un total de un dia `completo == false` ***
```

> *** Y **el caso 2 es exactamente el del plan** *** -- *«ausencia de energia con proteina conocida» -- *
> *y **es el que obliga a que la cobertura sea **por nutriente***, *y **no una sola por dia.** *
>
> *** Y **eso ya esta resuelto en `diario.py`** *** *-- *«sin esto, una entrada con proteina y sin energia
> perderia su proteina en el subtotal, *o peor: **se leeria como que el dia esta cubierto**». *
>
> *** O sea: *** *** **el ensayo de B08 se escribe encima de piezas que ya existen, y su caso mas dificil
> ya tiene codigo y motivo.** *

## 6. Y el estado, para que no se confunda la especificacion con el trabajo

```
*** B08 · la vista de previstos ***
  *** ESPECIFICADA ***  -> *esta ronda: nombre, entradas, seis pasos citados, salida y ensayo*
  *** y NO IMPLEMENTADA ***  -> *y por eso **sigue abierta.** *
  *** y las piezas ***  -> *** las seis existen ***, *y cada una con su fichero y su linea*
  *** y el limite del paso 3 *** -> *`cesta.py:184`: la columna la escribe `emparejar.py`, *
                                    *y «ese fichero no la tiene todavia»*
```

> *** Y **una especificacion no es una pantalla** *** -- *y **el encargo prohibe cerrar por tenerla**:
> «**no consideres terminado lo que solo abrio una pantalla vacia**». *Y esto **ni es una pantalla.** *
> *** -> **B08 sigue abierta**, *y **el siguiente paso es escribirla y verla.** *
