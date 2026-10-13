# B08 · **El sitio de las tres series YA EXISTE**: es `Tendencias.tsx`

*(13 de octubre de 2026. **Y su docstring ya dice la doctrina entera de la grafica.**)*

## 1. El fichero, y lo que ya tiene

```
`plataforma/web/app/src/paginas/Tendencias.tsx`
l1-10  *** /** Las tendencias: los ultimos dias, con los huecos donde no hay dato. ***
  *** «**Un dia sin dato no es un dia de cero.** Aqui los dias sin energia no llevan barra: llevan la palabra
  "sin dato". *** Un grafico que dibuja cero donde no hay dato dice que se comio nada, Y ENCIMA HACE PARECER
  QUE LOS DEMAS DIAS ESTAN COMPLETOS. ***» *
  *** «**Y tampoco se inventa una media.** Si ningun dia trae dato, no hay nada que promediar y se dice;
  dibujar un cero seria INVENTARSE UN RESULTADO.» ***
  *** «**La medida se declara:** es lo anotado y lo que se sabe, no "lo que comiste".» *** */ *

l12  import { useState } from 'react'
l14  import { textoDeError } from '../api/cliente'      *-- el trato del error*
l15  *** import { useRango } from '../api/diario' ***       *** <- Y YA TRAE EL REGISTRADO *** *
l16  import { Tarjeta, Vacio } from '../componentes/ui'  *-- y los dos componentes de marco*
```

> *** O sea: *** *** **el sitio de la grafica ya existe, y ya pinta la primera serie** -- *el **registrado**, *
> *con `useRango`.* *
>
> *** Y **su docstring ya tiene las tres reglas que la vista de las tres series necesita**, *y con las
> palabras del proyecto**: *
> ```
> *** «un dia sin dato no es un dia de cero» ***            -> *`kcal_conocida: null` *
> *** «dibujar un cero seria inventarse un resultado» ***    -> *y **el objetivo ausente**, *igual*
> *** «y encima hace parecer que los demas dias estan completos» *** -> *** y eso es LA COBERTURA *** *
> *** «la medida se declara: es lo anotado y lo que se sabe» *** -> *y **la leyenda con `dibujados`/`total`** *
> ```

## 2. *** Y por eso la vista de las tres series NO es un fichero nuevo ***

```
*** LO QUE HABRIA QUE HACER, y es AMPLIAR: ***
  *** 1) el registro ***   -> *** ya esta: `useRango` *** ✓
  *** 2) la prevision ***  -> *una consulta a `*** /api/recetas/plan/prevision ***` (ronda 274), *con su hook*
  *** 3) el objetivo ***   -> *y **`/api/yo`** ya lo trae: *`{"objetivo:<fecha>": {"kcal": N}}`*
  *** 4) y `serieDeChispa` TRES VECES *** -> *y **el import es SIN extension**: *
     `import { serieDeChispa } from '*** ../logica/chispa ***'` *-- *porque **un `.tsx` lo resuelve el
     empaquetador**, *y **`tsc` exige justo eso.** *
  *** 5) y la leyenda, con `dibujados` / `total` / `sinFecha` / `dibujable` / `motivoUnidad` *** *
```

> *** Y **el (4) es la respuesta al conflicto de la ronda 288**: *** *** **`logica/` son hojas** -- *y **por eso
> los `.mjs` los importan con `.ts`**; *y **un `.tsx` importa SIN extension**, *porque **no pasa por
> `node --test`** *sino por **`tsc` y `npm run build`.** *
>
> *** O sea: *** *** **las dos formas de importar no son incoherentes: son los dos mundos**, *y **el proyecto
> usa cada una donde toca.** *

## 3. Y **el nombre del fichero ya dice lo que va a pasar**

```
*** `Tendencias.tsx` ***  *-- *y su docstring empieza con **«las tendencias: los ultimos dias»** *
*** -> y ahora tendra, en los mismos dias: *** *** lo registrado, lo previsto y el objetivo *** *
   *** y la palabra «tendencias» sigue valiendo: *son **tres tendencias comparadas**, *y no tres pantallas.** *
```

> *** Y **es coherente con la navegacion**, *que el encargo pide separada: ***
> ```
> *** Compra ***    -> `/compra`     *-- las listas, los precios, la compra*
> *** Recetas ***   -> `/recetas`    *-- el recetario, el plan, y LA PREVISION (ya hecha)*
> *** Calorias ***  -> `/calorias`   *-- el diario y las tendencias* *** <- y aqui van las tres series *** *
> ```
>
> *** O sea: *** *** **la vista de las tres series va en Calorias**, *que es **donde ya estan el diario y las
> tendencias** -- *y **su fuente de la prevision es cruzar a Recetas**, *por **una ruta que ya existe.** *

## 4. Y el estado de B08, con **el sitio, la forma y el invariante ya escritos**

```
*** B08 · la vista de las tres series ***
  *** donde va ***   -> *** `paginas/Tendencias.tsx` ***, que **ya pinta el registrado** con `useRango`
  *** de donde saca las otras dos *** -> *`/api/recetas/plan/prevision` y `/api/yo`* *-- las dos YA existen*
  *** y con que ***  -> *** `serieDeChispa` TRES VECES ***, *importada **sin extension** (es un `.tsx`)
  *** y su leyenda *** -> *`dibujados` / `total` / `sinFecha` / `dibujable` / `motivoUnidad`*
  *** y su doctrina *** -> *y **ya esta escrita en el propio fichero**: *«un dia sin dato no es un dia de cero»*
  *** y `logica/` se queda como esta: HOJAS *** *
```

> *** Y **lo que queda es escribir, y no decidir**: *** *** el sitio, los tres datos, la funcion, la leyenda
> y la doctrina **estan** -- *y **la unica regla nueva es que el objetivo puede no estar**, *y **su propia
> ausencia ya viene como `dibujable: false`.** *
