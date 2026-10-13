# B08 · **El objetivo YA ESTA EN LA CACHE**: no hace falta `useYo`

*(13 de octubre de 2026. **Y de las tres piezas que quedaban, una se cae.**)*

## 1. Lo que hay, y no habia que escribirlo

```ts
// plataforma/web/app/src/api/cuenta.ts
l15  *** import { yo } from './cesta' ***              *-- y `yo` es la funcion que pide `/api/yo`*
l22  export function useClaveDeCuenta(): string {
l23      const { data } = useQuery({ queryKey: *** ['yo'] ***, queryFn: *** yo ***, staleTime: 60_000 })
l24      return data === undefined ? 'sin-sesion' : JSON.stringify(data)
l25  }
```

> *** O sea: *** *** **la respuesta de `/api/yo` -- que trae `preferencias`, y por tanto `objetivo:<fecha>` --
> YA ESTA EN LA CACHE de React Query, bajo la clave `['yo']`.** *
>
> *** Y **se pide para calcular la clave de cuenta** *** *-- *o sea: **se pide siempre**, *y **su resultado
> queda guardado.** *
>
> *** -> y **la vista de las tres series lo puede leer con la misma consulta**, *sin escribir un hook nuevo: *
> *`useQuery({ queryKey: ['yo'], queryFn: yo })` **es la que ya existe.** *

## 2. *** Y `l8-10` dice algo que hay que leer DOS veces ***

> *** «**Y por que ademas se pone el usuario en las claves nuevas.** *** *** Porque son miAS y son CUATRO, ***
> *** y asi dos cuentas no comparten entrada de cache ni aunque el vaciado fallara. *** *** Defensa en
> profundidad: la primera capa es la que protege, la segunda es la que aguanta si la primera se rompe. ***» *
>
> *** Y **`l3-6` explica la primera capa**: *** *«hay **95 claves de consulta** en la aplicacion. *Poner el
> usuario en las 95 **a mano no es viable**, *y **basta olvidar una** para que al cambiar de cuenta aparezca
> durante un instante **el diario, el recetario o la lista de la compra de la otra persona**. *
> *** VACIAR NO SE PUEDE OLVIDAR. ***» *
>
> *** Y **entonces `usePrevision` -- la que escribi en la ronda 293 -- lleva el usuario en su clave**: ***
> *`queryKey: ['prevision', *** cuenta ***, desde, hasta]` *-- *y **eso no es un adorno: es la segunda capa**,
> *y **el fichero dice por que.** *

## 3. Y **lo que queda de B08, corregido: DOS piezas y no tres**

```
*** 1) `usePrevision(desde, hasta)` ***  -> *** HECHA *** (commit `0a7f602`)
*** 2) `useYo()` ***                       -> *** NO HACE FALTA: `['yo']` ya se consulta, y `yo` esta exportada *** ✓
*** 3) y `Tendencias.tsx` ***              -> *tres `serieDeChispa`, la leyenda, y la tabla accesible*
*** y su prueba ***                        -> *`tsc` y `npm run build`*
```

> *** O sea: *** *** **la vista de las tres series tiene sus TRES datos disponibles con DOS consultas que ya
> existen** (`useRango` para el registrado, `['yo']` para el objetivo) *y **una que acabo de escribir**
> (`usePrevision`). *
>
> *** Y **queda UNA cosa**: *** *** **el componente.** *Y su sitio es `Tendencias.tsx`, *que **ya pinta una de
> las tres series** *y **cuyo docstring ya tiene la doctrina.** *

## 4. Y una nota de metodo, porque esto se descubrio leyendo y no suponiendo

> *** Iba a escribir `useYo` *** *-- *y **lo primero fue **leer el fichero donde iria**, *que es
> `api/cuenta.ts`.* *
>
> *** Y **en su linea 15 estaba `import { yo } from './cesta'`** *** *-- *o sea: **la funcion ya existia**, *
> *y **la consulta tambien.** *
>
> *** -> y **haberlo escrito sin leer** habria dejado **dos consultas a la misma ruta**, *con claves distintas,
> y **dos peticiones por carga** -- *o peor: **una clave nueva sin el usuario**, *que es exactamente **el fallo
> que `l3-10` describe.** *
>
> *** Y **es la misma leccion de siempre, y van quince**: *** *** **leer la linea antes de escribir la
> siguiente.** *
