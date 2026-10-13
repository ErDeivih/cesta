# B08 · **La vista de las tres series es llamar TRES VECES a lo que ya existe**

*(13 de octubre de 2026. **Y las tres reglas ya estan escritas y probadas.**)*

## 1. Lo que hay en `chispa.ts`, y por que sirve para las tres series

```
l3-5   *** «Existe porque las TRES REGLAS de esta decision son de G05 y hay que fijarla con un `tsc` verde --
       *** COMPILAR NO ES ACERTAR ***. Las tres salen del mismo principio: *** lo que no se observo no se
       puede dibujar como si se hubiera observado. ***» *
l7-8   *** «**Un hueco es un hueco**: un `null` entre dos [puntos] se conserva como `null`... [no se pueden]
       conectar datos ausentes como si hubiera observaciones».» *
l9-10  *** «**Una fecha ilegible no es 1970**: el punto se descarta y se cuenta.» *
l11-13 *** «**De una serie vacia no se infiere nada**: ... [lo que se] pinta dice que **no hay serie**,
       no que haya un solo dia.» *
l15-17 *** «Y devuelve la COBERTURA, en la forma que el proyecto ya usa (`{valor, faltantes}`): cuantos puntos
       se dibujan y cuantos se quedaron fuera... *** SIN ESO, UN HUECO Y UNA AUSENCIA SE VEN IGUAL. ***» *
```

```ts
l19  *** export interface PuntoChispa ***      *-- y es **generico**: una fecha y un valor*
l26  *** export interface SerieDeChispa ***    *-- y lleva **la cobertura***
l54  *** export function serieDeChispa(puntos: PuntoChispa[]): SerieDeChispa *** *
```

> *** O sea: *** *** **`serieDeChispa` no sabe de precios ni de calorias: recibe puntos y devuelve una serie
> con su cobertura.** *
>
> *** Y **por eso vale para las TRES**: *** *registrado, previsto y objetivo *-- *y **no hay que escribir
> una version por cada una.** *

## 2. *** Y las tres series tienen sus datos YA, y cada una con su forma ***

```
*** REGISTRADO ***  *`GET /api/diario/rango?desde=&hasta=`*
   -> *da, por dia: `kcal_conocida` (o **`null`**) y `entradas` / `con_dato` / `completo`
   *** -> y **`kcal_conocida` es `null` cuando no hay dato** *-- *o sea: **el hueco ya viene como hueco.** *

*** PREVISTO ***  *** `GET /api/recetas/plan/prevision?desde=&hasta=` ***  *(ronda 274)*
   -> *da, por comida: `conocido` (con **`kcal: null`** si no se sabe) *y* *** `cobertura` POR NUTRIENTE *** *

*** OBJETIVO ***  *** `GET /api/yo` ***  *(ronda 283)*
   -> *** `{"objetivo:<fecha>": {"kcal": N}}` *** *-- *y **si no hay, la clave no esta** *
   *** -> o sea: **un dia sin objetivo es un dia sin punto**, *y **NO un cero.** *
```

> *** Y **las tres cumplen la regla sin que haya que arreglarlas**: ***
> ```
> *** registrado *** -> *`kcal_conocida: null` *-- *no **0***
> *** previsto ***    -> *`conocido.kcal: null` *-- *no **0**, *y con **cobertura por nutriente***
> *** objetivo ***    -> *y **la clave no existe** *-- *no **«objetivo: 0 kcal»***
> ```
>
> *** O sea: *** *** **la grafica de los tres no necesita que nadie le diga que hay huecos: los tres datos
> llegan ya diciendo donde no hay.** *
>
> *** Y **es exactamente lo que `chispa.ts:7` exige**: *«un `null` entre dos [puntos] **se conserva como
> `null`**». *

## 3. Y **lo que falta, entonces, es una composicion y una tabla**

```
*** LO QUE HABRIA QUE ESCRIBIR: ***
  *** 1) tres llamadas, y tres `serieDeChispa(...)` ***  *-- *una por serie*
  *** 2) y una TABLA ACCESIBLE con los mismos datos ***  *-- *y **`chispa.ts:93` ya lo pide**: *
     *«la aceptacion de G05 pide *** «tabla accesible de los mismos datos» ***»*
  *** 3) y la leyenda, con **las tres series y la cobertura de cada una** *** *
     *** -> y si el objetivo no existe, LA LEYENDA TIENE DOS SERIES Y LO DICE *** *
```

> *** Y **el punto (3) es el que el encargo protege**: *** *** «**si no hay objetivo, la grafica tiene DOS
> series**» *-- *y **eso no es una carencia: es lo que hay, dicho.** *
>
> *** Y **`chispa.ts:12` ya tiene la regla para el caso extremo**: *** *«de una serie vacia no se infiere
> nada... **no que haya un solo dia**». *Y **el objetivo puede estar vacio entero**, *y **la grafica tiene
> que decir «no hay serie»**, *no **dibujar una linea por el cero.** *

## 4. Y el estado, con **B08 a una composicion de distancia**

```
*** B08 · las cuatro piezas: ***
  *** 1. la vista de previstos ***  -> *** HECHA ***  *(`GET /api/recetas/plan/prevision`, 200)*
  *** 2. su ensayo ***              -> *** HECHO ***  *(8 ensayos: 2025 -> 2033)*
  *** 3. el objetivo ***            -> *** FUNCIONA *** *(`PUT /api/preferencias` + `GET /api/yo`)*
  *** 4. *** LAS TRES SERIES *** ***     -> *y **sus tres datos ya se leen**, *sus **tres reglas ya estan
     escritas y probadas** (`chispa.ts`), *y **`serieDeChispa` es generica** *
     *** -> lo que falta es **una composicion y una tabla accesible**, y **no una decision ni un dato.** *
```

> *** Y **nada de esto se declara hecho**: *** *la **vista de las tres series NO existe** *-- *y **lo que se ha
> hecho es **medir que hay** para escribirla: *los tres datos, las tres reglas, y la funcion generica.* *
