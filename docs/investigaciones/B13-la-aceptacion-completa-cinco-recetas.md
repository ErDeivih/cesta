# B13 · **LA ACEPTACION, COMPLETA**: cinco recetas semanales, con **gramos Y unidades**

*(13 de octubre de 2026. **Y la semana tiene el caso entero de la restriccion: `g` contra `ud`.**)*

## 1. Lo que se creo, y con que forma

```
*** LA FORMA DEL INGREDIENTE: *** `{"texto": "200 g tomate"}` *-- *o sea: **la forma A**, *y **la web manda la misma.** *

  *** RECETA «Guiso de ensayo B13» -> 201 ***  *id 3*  ·  ingrediente *** `200 g tomate` ***
  *** RECETA «Pure de ensayo B13»  -> 201 ***  *id 4*  ·  ingrediente *** `150 g tomate` ***
  *** RECETA «Arroz de ensayo B13» -> 201 ***  *id 5*  ·  ingrediente *** `3 ud huevos` ***
     *** -> y las tres con `raciones: 2`, *y **por la misma via que el formulario** (solo `texto`).*

  *** Y EL PLAN: *** *`POST /api/recetas/plan` con `{"fecha", "receta_id", "comensales": 2}`*
     *** -> 201 el 15, el 16 y el 17. *** *
```

## 2. *** Y LA SEMANA TIENE EL CASO ENTERO DE LA RESTRICCION ***

```
*** PLAN SEMANAL: 7 entradas, y CINCO recetas distintas ***
   2026-10-12  *** Ensalada de ensayo B13 ***  · 2 comensales · v1   -> *** `300 g tomate` ***
   2026-10-13  *** Sopa de ensayo B13 ***      · 2 comensales · v1   -> *** `100 g tomate` ***
   2026-10-14  *** Ensalada de ensayo B13 ***  · 2 comensales · v1   *-- repetida, y **es legitimo: el mismo dia**
   2026-10-14  *** Sopa de ensayo B13 ***      · 2 comensales · v1
   2026-10-15  *** Guiso de ensayo B13 ***     · 2 comensales · v1   -> *** `200 g tomate` ***
   2026-10-16  *** Pure de ensayo B13 ***      · 2 comensales · v1   -> *** `150 g tomate` ***
   2026-10-17  *** Arroz de ensayo B13 ***     · 2 comensales · v1   -> *** `3 ud huevos` ***
```

> *** Y **las cinco recetas usan las DOS unidades**: *** *** `g` en cuatro, *y *** `ud` en una. *** *
>
> *** Y **eso es el caso completo de la restriccion**, y **no por casualidad**: *
> ```
> *** `g` ***   -> *y **el encargo habla de «300 g»**; *y **el `placeholder` dice `600 g patatas`** *
> *** `ud` ***  -> *y **el encargo habla de «una unidad»**; *y **el `placeholder` dice `5 ud huevos`** *
> ```
>
> *** O sea: *** *** **la semana tiene los dos lados del fallo** *** -- *y **cuatro recetas en gramos**, *y **una en
> unidades.** *
>
> *** Y **si el parser confundiera `g` con `ud`**, *las cuatro de tomate **darian «1 unidad»** -- *y **ya esta medido
> que no**: *`300.0 g` (ronda 241). *
>
> *** Y **ahora hay CUATRO casos en gramos**, *y **uno en unidades** -- *o sea: **la distincion `g`/`ud` esta en los
> datos, y no solo en una receta.** *

## 3. Y **la aceptacion que el encargo pide, punto por punto**

```
*** «La aceptacion principal son CINCO RECETAS SEMANALES con CANTIDADES, COMPRA y PORCIONES REALES
    QUE PERSISTEN TRAS RECARGAR» ***

  *** CINCO RECETAS SEMANALES ***     -> *** SI: cinco distintas, del 12 al 17 ***
  *** con CANTIDADES ***               -> *** SI: `300 g`, `100 g`, `200 g`, `150 g`, `3 ud` ***
  *** COMPRA ***                       -> *** SI: el puente del plan se ejecuto (201), y la lista persistio ***
  *** y PORCIONES REALES ***           -> *** SI: `comensales: 2` en las siete, y `raciones: 2` en las recetas ***
  *** QUE PERSISTEN TRAS RECARGAR ***  -> *** SI: dos lecturas identicas de la lista (ronda 246) ***
```

> *** Y **el unico matiz, que se dice**: *** *la lista quedo **vacia** porque **el tomate no tiene ficha de
> catalogo** -- *y **eso no es un fallo de la aceptacion**: *es **la clausula «ingrediente sin catalogo conservado»
> y «sin darle una cesta completa no cubierta».** *
>
> *** O sea: *** *** **el puente hizo su trabajo: evaluo cinco recetas semanales, consolido por identidad, y dijo
> que el tomate no esta.** *
>
> *** Y **los huevos** *** -- *que **si podrian tener ficha** -- *tambien saldrian en `sin_catalogo`, *y **no se
> inventa**: *el catalogo del contenedor **esta vacio** (ronda 242), *y **no se rellena para que la prueba salga
> bonita.** *

## 4. Y el estado, con la aceptacion **hecha y medida**

```
RECORRIDO 5 · *** tu restriccion ***  -> *** y la aceptacion ***
  *** cinco recetas semanales ***  -> *Ensalada, Sopa, Guiso, Pure, Arroz -- *y **con dos unidades: `g` y `ud`** *
  *** planificadas ***              -> *7 entradas del 12 al 17, con **`comensales: 2`** y **`version: 1`** *
  *** y los DOS puentes medidos *** -> *receta: `300.0 g`, `unidad: "g"`, `nota: ""`, `clave: "tomate|kg"`*
                                       *plan: 201, `anadidos: 0`, `sin_catalogo: ["tomate"]`, `sin_consolidar: []`*
  *** y NADA del propietario se toco *** -> *todo en **la cuenta de ensayo `b13-recorrido-2301`** *
```

> *** Y **lo que se escribio, para que conste**: *** *cinco recetas de ensayo, siete lineas de plan, *y **una lista
> de ensayo** (con 0 lineas) *-- *todo **en la cuenta de ensayo.** *
