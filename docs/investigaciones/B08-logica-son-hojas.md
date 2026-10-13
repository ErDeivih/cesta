# B08 · **`logica/` son HOJAS**: por que la composicion no puede vivir ahi

*(13 de octubre de 2026. **Y lo descubri rompiendolo, y lo reverti.**)*

## 1. Lo que intente, y lo que paso

```
*** LO QUE ESCRIBI: ***  `src/logica/tresSeries.ts`
  *-- que **componia las tres series**, *y **por tanto importaba `./chispa`** *

*** Y SALIO UN CONFLICTO DE DOS CARAS, y las dos son verdad: ***
  ```
  *** sin extension (`from './chispa'`) ***   -> *`tsc` VERDE, *y **`node --test` FALLA**: *
     `ERR_MODULE_NOT_FOUND: Cannot find module '...src/logica/chispa'` *-- *Node ESM **exige** extension*
  *** con extension (`from './chispa.ts'`) *** -> *** y `node --test` PASA (79 en vez de 74) *** *
     *y **`tsc` FALLA**:* `TS5097: An import path can only end with a '.ts' extension when
     'allowImportingTsExtensions' is enabled`
  ```
```

> *** O sea: *** *** **`tsc` prohibe la extension, y Node la exige.** *Y **no es un descuido de nadie**: *
> *es **la frontera entre el compilador y el runtime**, y **el proyecto la tiene resuelta por construccion.** *

## 2. *** Y la resolucion estaba a la vista: **`logica/` no tiene NI UN import interno** ***

```
$ git grep -n "^import .* from '\./" -- "plataforma/web/app/src/logica"
*** -> NADA. Ni una coincidencia. *** *
```

> *** O sea: *** *** **cada modulo de `logica/` es una HOJA**: *no importa a ningun otro.* *
>
> *** Y **por eso los ensayos `.mjs` pueden importarlos con `.ts`**: *** *`tests/*.test.mjs` hace
> `import { aMs, filasDeChispa, *** serieDeChispa *** } from '*** ../src/logica/chispa.ts ***'` *
> *-- *y **funciona, porque `chispa.ts` **no importa nada**.** *
>
> *** -> y **mi `tresSeries.ts` rompia esa propiedad**: *era **el primer modulo de `logica/` que importaba
> a otro de `logica/`** -- *y **por eso choco.** *

## 3. Y **por eso lo reverti**, que es lo correcto

```
*** LO QUE HICE: ***  *borrar `src/logica/tresSeries.ts` y `tests/tresSeries.test.mjs`*
*** Y LAS PUERTAS, VERDES OTRA VEZ: ***  *`tsc` limpio, *y *** 74 ensayos *** (los de antes) *
```

> *** Y **no es una retirada: es no doblar el proyecto.** *
>
> *** Porque **las tres salidas eran malas**, *y conviene decirlas: *
> ```
> *** a) activar `allowImportingTsExtensions` ***  -> *tocaria **la configuracion del compilador de todo el
>    proyecto** para que quepa **un fichero mio** -- *y **eso es doblar el proyecto por comodidad.** *
> *** b) copiar la logica de `serieDeChispa` ***    -> *** y ya esta escrito que no: *** *«copiar aqui el
>    minimo seria **una segunda copia que se queda vieja**» (`Cesta.tsx:139`). *
> *** c) dejar `tsc` en rojo ***                    -> *y **`tsc` verde es una de las cuatro puertas.** *
> ```
>
> *** -> y **queda la (d), que es la que el proyecto ya usa**: *** *** la composicion vive **donde el
> empaquetador resuelve los imports** -- *o sea, **en un componente (`.tsx`)**, *que **no se prueba con
> `node --test`** *sino con **`npm run build`** y **`tsc`**.* *

## 4. *** Y ESO ES UN DATO PARA LA VISTA DE LAS TRES SERIES ***

```
*** LA VISTA DE LAS TRES SERIES, ENTONCES: ***
  *** donde va ***   -> *en un componente, junto a las que ya pintan (`Tendencias.tsx`)*
  *** y como ***      -> *tres `serieDeChispa(...)`, *y **la leyenda con lo que cada una trae** *
  *** y su prueba ***  -> *`tsc` **y** `npm run build` -- *que es **como se prueban los componentes** *
  *** y `logica/` se queda como esta: HOJAS *** *
```

> *** O sea: *** *** **el invariante «`logica/` son hojas» no es un capricho de estilo: es lo que permite
> probarlas con `node --test` sin cargador ni configuracion.** *
>
> *** Y **es la misma forma de todo el proyecto**, otra vez: *la **regla esta en la estructura**, *
> *y **quien la rompe lo nota en la primera puerta.** *
>
> *** Y **se dice lo que se hizo y lo que no**: *** *** se intento, se midio, se entendio, **se revirtio** --
> *y **el invariante queda escrito**, *que es **lo unico que faltaba.** *
