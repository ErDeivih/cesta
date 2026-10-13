# B08 · **El inventario final**: faltan DOS hooks y el componente -- y nada mas

*(13 de octubre de 2026. **Y con esto, lo que queda de B08 esta contado entero.**)*

## 1. Los hooks que ya existen

```
`plataforma/web/app/src/api/diario.ts:178`   *** useRango(desde, hasta) ***   *-- EL REGISTRADO* ✓
`plataforma/web/app/src/api/recetas.ts:131`  *** usePlan(desde, hasta) ***     *-- y EL PLAN* ✓
`plataforma/web/app/src/api/consultas.ts:86` *** useEstado() ***               *-- el estado*
```

> *** Y **`usePlan` es el que mas cerca esta**, *porque **la prevision vive en la misma ruta base**: *
> *`/api/recetas/plan` y `/api/recetas/plan/prevision`.* *
>
> *** -> o sea: **el hook que falta es un hermano de `usePlan`**, *y **con su mismo patron.** *

## 2. *** Y lo que NO existe, y es TODO lo que falta ***

```
*** 1) `usePrevision(desde, hasta)` ***  *-- para `/api/recetas/plan/prevision`*    ⚠️
*** 2) `useYo()` ***                       *-- para `/api/yo`*                        ⚠️
*** 3) y ampliar `paginas/Tendencias.tsx` *** con las tres series y su leyenda          ⚠️

$ git grep -ln "prevision\|api/yo" -- "plataforma/web/app/src"
*** -> NADA. *** *Cero referencias en TODO el frontend.* *
```

> *** O sea: *** *** **la vista de las tres series no esta empezada por el lado del cliente**, *y **lo
> que falta son **tres cosas**, *y **las tres tienen su patron escrito**: *
> ```
> *** los dos hooks *** -> *`useRango` y `usePlan` son el molde: *~8 lineas cada uno, con `useQuery`*
> *** y el componente *** -> *`Tendencias.tsx` ya pinta una serie, *y **su docstring ya tiene la doctrina** *
> ```
>
> *** Y **nada de eso decide nada**: *la ruta existe (`prevision`), *la otra existe (`/api/yo`), *
> *la funcion existe (`serieDeChispa`), *y **el sitio existe (`Tendencias.tsx`).** *

## 3. *** Y esto es TODO lo que queda de B08, y del encargo ***

```
*** B00-B07 · B09-B12 ***  -> *cerrados o contestados*
*** B13 ***                 -> *5 de 5 recorridos · la restriccion medida por los DOS puentes · la aceptacion*
*** B14 ***                 -> *5 de 5 · y el volumen APLICADO*
*** B15 ***                 -> *medido*
*** B16 ***                 -> *dictamen escrito*

*** B08 ***  -> *** y esto es lo unico que queda: *** *
  *** 1) `usePrevision(desde, hasta)` ***  *-- ~8 lineas, con el molde de `usePlan` (recetas.ts:131)*
  *** 2) `useYo()` ***                       *-- ~8 lineas, con el molde de `useRango` (diario.ts:178)*
  *** 3) y `Tendencias.tsx` ***              *-- tres `serieDeChispa`, la leyenda, y la tabla accesible*
  *** y su prueba ***                        -> *`tsc` y `npm run build`, *que es como se prueban los componentes*
```

> *** Y **se puede decir sin exagerar ni quedarse corto**: *** *** **el trabajo que queda son **dos hooks de
> ocho lineas y una ampliacion de un componente que ya pinta una de las tres series**.** *
>
> *** Y **lo que NO queda** *** *-- *y es **lo que ha costado estas rondas** --: *
> ```
> *** no falta ni un dato ***      -> *los tres se leen (rango, prevision, /api/yo)*
> *** no falta ni una regla ***    -> *«un dia sin dato no es un dia de cero», y sus hermanas*
> *** no falta ni una funcion ***  -> *`serieDeChispa`, generica y con cobertura*
> *** no falta ni una tabla ***    -> *`preferencia`, con la fecha en la clave*
> *** no falta ni una migracion *** -> *y no hay que tocar el esquema*
> *** y no falta ni una decision *** -> *salvo la que el propio encargo deja a la persona: **el valor del objetivo***
> ```
