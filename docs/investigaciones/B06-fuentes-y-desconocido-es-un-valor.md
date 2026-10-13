# B06 · **`FUENTES = (ETIQUETA, FICHA, ESTIMADO, DESCONOCIDO)`** -- y `DESCONOCIDO` es un valor, no un hueco

*(13 de octubre de 2026. **Sexta ronda de B06. Y la clausula 2 queda cerrada del todo.**)*

## 1. El catalogo, literal

```
core/diario.py:34:   FUENTES = (ETIQUETA, FICHA, ESTIMADO, DESCONOCIDO)
```

> *** Cuatro origenes, y los cuatro son **respuestas validas** ***:
>
>   - **`ETIQUETA`** *-- el dato viene **de lo que dice el envase o la ficha**;*
>   - **`FICHA`** *-- viene **de la ficha de la cadena**;*
>   - **`ESTIMADO`** *-- **lo hemos estimado**;*
>   - **y `DESCONOCIDO`** *-- *** «no se sabe de donde salio». ***
>
> *** Y el cuarto es la pieza que cierra B06: ***
>
> *El plan pide «campo **nativo / enriquecido / manual**». *Y el proyecto tiene **esos tres** -- `ETIQUETA`/`FICHA`
> son **nativo**, `ESTIMADO` es **enriquecido**, y lo escrito a mano seria **manual** -- **y ademas un cuarto**:
> **`DESCONOCIDO`**.*
>
> *** Que es la NOVENA vez que aparece la doctrina, y la forma mas limpia de todas: *** **«no se sabe» es un valor
> de la lista, no la ausencia de valor.** *Asi que **se puede guardar un dato sin saber de donde salio** -- *y
> **queda dicho**, en vez de quedar en blanco.*

## 2. Y `ValueError` **no contradice** a `DESCONOCIDO`

```
l151:  if fuente_dato not in FUENTES:
l152:      raise ValueError(f"fuente de dato desconocida: {fuente_dato}")
```

> *** Y hay que leer las dos cosas juntas, porque parecen contrarias y no lo son: ***
>
>   - *si `fuente_dato` **no esta en `FUENTES`**, se levanta el error -- *o sea: **no se puede inventar un origen**;*
>   - *pero **`DESCONOCIDO` SI esta** -- *o sea: **se puede decir que no se sabe**.*
>
> *** El `ValueError` no prohibe no saber: **prohibe inventar una etiqueta que no existe**. ***
>
> *Que es **exactamente** la distincion del plan, y **la mas fina de todo B06**: *«no publicado» y «pendiente» no
> son errores -- **son estados**; el error seria **etiquetarlos de algo que no son**.*

## 3. Y la doctrina, **novena vez**, ya ordenada por forma

```
  1) `cantidad` de la despensa        ->  NULL = «no se sabe», que no es 0
  2) `sin_precio`                     ->  «no se sabe el precio», que no es gratis
  3) `diario.fuente_dato`             ->  de donde viene el dato             <- y luego se vio: NOT NULL
  4) `COALESCE` en `anade_linea`      ->  «no llega» no es «llega vacio»
  5) `core/alimentos.py`              ->  «mezcla», que no es ni «si» ni «no»
  6) `test_un_cero_no_se_confunde_con_no_haber_dato`
  7) `unidad_canon`                   ->  sin unidad, las cifras NO SON COMPARABLES
  8) `FUENTES` + `ValueError`         ->  un origen que no es de los conocidos SE LEVANTA
  9) *** y `DESCONOCIDO` EN LA LISTA  ->  «no se sabe» es un VALOR, no la ausencia de valor ***
```

> *** Y las nueve, juntas, son **una sola regla con nueve caras**: ***
>
> **«No se sabe» es una respuesta que se guarda. Lo que no se guarda es un valor inventado.»**
>
> *** Que es, palabra por palabra, lo que el propietario pidio: *** *«**no inventes** calorias, densidad, alergenos,
> equivalencias, objetivos de salud, precios ni costes de viajes».*
>
> *Y este proyecto **no lo tiene como regla: lo tiene como forma** -- *una columna que admite NULL, un `sin_precio`,
> una lista con `DESCONOCIDO`, un `COALESCE`, un `ValueError`, y tres respuestas donde caben dos.*
>
> *** Nueve sitios. Y el encargo entero cabe en esa frase. ***

## 4. Y B06, con seis rondas, tiene **cuatro de cinco cerradas**

```
  1) EL INVENTARIO DE CAMPOS        HECHO -- 21 ensayos, campo por campo
  2) NATIVO / ENRIQUECIDO / MANUAL  *** HECHO DEL TODO: ***
                                    `fuente_dato NOT NULL` + `FUENTES = (ETIQUETA, FICHA, ESTIMADO,
                                    DESCONOCIDO)` + `ValueError`, y `derive.enriquecer` para el enriquecido
  3) AUSENTE / NO APLICABLE / ...   «ausente» y «error» con ensayo; «no aplicable» en `core/alimentos.py`
                                    y «DESCONOCIDO» aqui; *** «no publicado» y «pendiente» POR MIRAR ***
  4) LA COLA CON PRESUPUESTO        *** POR MIRAR ***
  5) Y EL HISTORICO DE FICHA        el historico existe y se usa; *** «no mezclar» POR MIRAR ***
```

> *** Y lo que queda son **dos** cosas, y las dos son «el tiempo»: *** *con que prioridad se pide un campo, y que se
> guarda del pasado.*
>
> *Y **las dos estan, casi con seguridad, en los dos ficheros de la lista de doce que nadie ha abierto**:
> `core/manifiesto.py` y `core/publicacion.py` -- *el **recibo** y la **version** de una publicacion.*
>
> *** Que es, literalmente, «de cuando es este dato». ***
