# B08 · **La unidad `g`/`ud` es una regla del sistema** -- y `chispa.ts` la hereda con sus palabras

*(13 de octubre de 2026. **Y es la misma regla que la restriccion del propietario, ya escrita en tres sitios.**)*

## 1. Las dos interfaces, y la pieza que cierra el circulo

```ts
// plataforma/web/app/src/logica/chispa.ts
l19  export interface PuntoChispa {
l20    fecha: string
l21    *** valor: number | null ***                 *-- y el hueco es `null`, no 0*
l22    /** *** La unidad con la que se midio ESE dia. *** La API puede no mandarla. */
l23    *** unidad?: string | null ***
l24  }

l26  export interface SerieDeChispa {
l28    xs: number[]
l29    *** ys: (number | null)[] ***                *-- y `ys` lleva los `null` dentro*
l31    total: number
l33    *** dibujados ***: number                   *-- «un hueco CUENTA COMO PUNTO»*
l35    *** sinFecha ***: number                    *-- «no se colocan en el eje»*
l37    *** dibujable ***: boolean                  *-- «No significa «un solo dia»»*
l39    *** unidades ***: string[]
l40-44 *** /** **Por que no se dibuja, cuando es por la unidad.** Mismo criterio y mismas palabras que
       `logica/curva.ts`: *«tres dias en `kg` y uno en `ud` *** SON DOS SERIES PEGADAS, *** y el minimo de
       las dos juntas *** no es el minimo de nada ***»*. Y `api/alertas.py` ya dice lo mismo: *«*** si la
       unidad cambio, no es una bajada ***»*. *** LA CHISPA ERA LA UNICA PIEZA DEL SISTEMA QUE LO IGNORABA. *** */ ***
l44    *** motivoUnidad: string | null ***
l45  }
```

## 2. *** Y eso es **la restriccion del propietario**, dicha por el proyecto ***

> *** La restriccion, del propietario: ***
> > *** «300 g necesarios terminan como **una unidad** y una nota de 100 g» *** *
>
> *** Y **la regla del proyecto**, en tres sitios: ***
> ```
> *** `logica/curva.ts` ***  -> *«tres dias en `kg` y uno en `ud` *** son dos series pegadas ***, *
>                            *y el minimo de las dos juntas *** no es el minimo de nada ***»*
> *** `api/alertas.py` ***   -> *«*** si la unidad cambio, no es una bajada ***»*
> *** `logica/chispa.ts` *** -> *y **la hereda**, *y **dice que era la unica pieza que lo ignoraba** *
> ```
>
> *** O sea: *** *** **«300 g» y «3 ud» no son la misma cosa, y el proyecto lo tiene escrito en tres sitios**,
> *con el mismo criterio: *mezclar unidades **fabrica un numero que no existe.** *
>
> *** Y **es exactamente el fallo que el propietario describio**: *«300 g» convertidos en **«una unidad»** *
> *-- *o sea: **una unidad que cambio, presentada como si fuera la misma serie.** *
>
> *** Y **por eso el parser (`identidad.RE_CANTIDAD`) importa tanto**: *** *si lee `300 g` como `1 ud`,
> *fabrica **un numero que no existe** -- *y **`chispa.ts` dice, con sus palabras, que eso es **pegar dos
> series**.** *

## 3. Y **`SerieDeChispa` es todo lo que la vista de las tres series necesita**

```
*** POR CADA SERIE (registrado, previsto, objetivo): ***
  *** `xs` / `ys` ***      -> *lo que se dibuja, *y **`null` donde no hubo observacion** *
  *** `dibujados` ***       -> *** y un hueco CUENTA COMO PUNTO *** *-- o sea: se ve*
  *** `sinFecha` ***        -> *y lo descartado **se cuenta** *
  *** `dibujable` ***       -> *** y `false` significa «no hay serie», NO «un solo dia» *** *
  *** `unidades` ***        -> *y si hay mas de una, se sabe*
  *** `motivoUnidad` ***    -> *** y si no se dibuja por la unidad, viene el motivo *** *
```

> *** O sea: *** *** **la funcion devuelve, para cada serie, TODO lo que hace falta para no mentir al
> pintarla**: *lo que se dibuja, *lo que se descarta y por que, *y si hay serie o no.* *
>
> *** Y **las tres series son tres llamadas**, *y **la leyenda se compone de los tres resultados** *** -- *
> *y **si el objetivo no existe**, *su `dibujable` es **`false`**, *y **la leyenda dice «no hay serie»**
> *en vez de **dibujar una linea por el cero.** *

## 4. Y el estado, con **la ultima pieza de B08 ya sin incognitas**

```
*** B08 · la vista de las tres series ***
  *** los tres datos ***    -> *`/api/diario/rango`, `/api/recetas/plan/prevision`, `/api/yo`* ✓
  *** las tres reglas ***   -> *`chispa.ts`, y con sus palabras* ✓
  *** y la funcion ***      -> *** `serieDeChispa(puntos) -> SerieDeChispa` ***, *generica, *y **con
                               `dibujable`, `dibujados`, `sinFecha`, `unidades` y `motivoUnidad`** *
  *** y la tabla accesible *** -> *y `chispa.ts:93` **ya la reclama**: «la aceptacion de G05 pide
                               *** «tabla accesible de los mismos datos» ***»*
  *** -> y NO queda ni una incognita: *** *es **componer tres llamadas**, *y **pintar la leyenda y la tabla**
     *con lo que **cada `SerieDeChispa` ya trae.** *
```

> *** Y **esto es lo que hace que la vista sea corta**: *** *** la parte dificil -- **decidir que se dibuja
> y que no, y decirlo** -- *esta **resuelta, probada y con `tsc` verde**, *y **a la vista solo le queda
> **componer.** *
