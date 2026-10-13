# B13 · **«Entrar» SÍ es `type="submit"`** -- y entonces el sospechoso pasa al `onSubmit` y a la cookie

*(13 de octubre de 2026. **Y una lectura de tres lineas estrecha el cerco otra vez.**)*

## 1. Lo que dice el codigo

```
`plataforma/web/app/src/paginas/Cesta.tsx`

  l71   function *** FormularioEntrar({ alEntrar }) ***
  l111  <Boton *** type="submit" *** disabled={entrar_.isPending}>
  l230  : <FormularioEntrar alEntrar={alEntrar} />      *-- *y su hermano `FormularioAlta` es la otra rama*

  *** Y COMPARADO CON OTRO SITIO DEL MISMO FICHERO: ***
  l1044 <Boton type="submit" disabled={*** !usuario.trim() || comparte.isPending ***}>
```

> *** O sea: *** *** **«Entrar» ES un `type="submit"`** *** -- *y **por tanto el boton SI envia el formulario.**
> *Asi que **el sospechoso 4 («el click no dispara») se cae tambien, en su forma simple.** *
>
> *** Y **el `l1044` da el contraste que hacía falta**: *** *en **otro** formulario del mismo fichero, el boton **si
> lleva la guarda en el `disabled`** (`!usuario.trim()`); *y **el de entrar NO**: *solo `isPending`. *
>
> *** O sea: **el boton de entrar **nunca esta deshabilitado por campos vacios** -- *y **eso significa que la guarda,
> si existe, esta en el `onSubmit`.** *

## 2. Y entonces los sospechosos son **dos, y los dos tienen linea**

```
*** A) EL `onSubmit` DE `FormularioEntrar` TIENE UNA GUARDA QUE NO SE CUMPLE ***
   -> *y **seria igual que el alta**: *`if (usuario.trim() && clave) entrar_.mutate()`*
   -> *** y entonces la pregunta es: **por que `usuario` y `clave` (el estado de React) estan vacios,
      si los `fill` funcionaron en el alta?** *
   -> *** Y HAY UNA RESPUESTA POSIBLE, Y ES BUENA: *** *** en el alta, **los dos campos se rellenaron DESPUES
      de montar la pantalla, y la pantalla no volvio a montarse**; *y **en el entrar, la pantalla se monto al
      cargar la pagina** -- *y **si el componente se re-monta (por un `key`, o por el ternario de l230)**,
      *los campos **vuelven a `''`.** *

*** B) LA PETICION NO MANDA `credentials` ***
   -> *si el `fetch` de `entrar` **no lleva `credentials: 'include'`** (o `same-origin`), *
      *** LA COOKIE NO SE GUARDA *** -- *y **entonces el API responde 200 y la sesion NO existe.** *
   -> *** y esto encaja PERFECTAMENTE con lo medido: *** *el API **SI** da 200 (ronda 231), *y **la pantalla
      no cambia** (el hash sigue igual).*
```

> *** Y **el (B) explica **todo** lo observado, y el (A) explica **casi** todo** *** -- *asi que **se miran los dos,
> y en este orden: primero el `onSubmit` (que esta en `Cesta.tsx`, ya abierto), y despues el `fetch` (que esta en
> `cesta.ts`). *
>
> *** Y **hay un detalle que **favorece al (B)**: *** *** el ALTA **si** dejo sesion (la pantalla cambio y el menu
> dijo «no hay lista de casa»), *asi que **`registrarse` **si** guarda la cookie.** *
>
> *** Y **si `registrarse` la guarda y `entrar` no**, *entonces **son dos `fetch` distintos, con opciones
> distintas** -- *y **eso es un dato que `cesta.ts` tiene en dos lineas.** *
>
> *** Y **`cesta.ts:53-56`** es donde vive `registrarse` (ya leido), *y **`entrar` esta al lado** -- *o sea: **la
> comparacion es de dos bloques contiguos.** *

## 3. Y el estado, con los cuatro sospechosos y sus medidas

```
RECORRIDO 4b · *** volver a entrar ***  -> *** NO ***  ·  y **los cuatro sospechosos, uno a uno: ***
   1. ~~la cuenta~~          -> *** DESCARTADO *** *-- existe en la base*
   2. ~~la clave~~           -> *** DESCARTADO *** *-- `POST /api/entrar` da **200***
   3. ~~el montaje~~         -> *** DESCARTADO *** *-- con 2 s, los `fill` bajan a 52 ms **y sigue sin entrar***
   4. ~~el click/el submit~~ -> *** DESCARTADO *** *-- `l111`: **es `type="submit"`***
   *** -> y quedan DOS, y los dos tienen linea: ***
        *** A) la guarda del `onSubmit` ***   *-- `Cesta.tsx:71` en adelante*
        *** B) `credentials` en el `fetch` *** *-- `cesta.ts`, junto a `registrarse` (l53)*
      *** y (B) es el que explica **el 200 sin sesion**, que es **lo que se midio.** *
```

> *** Y **lo que importa de esta ronda no es el fallo: es que **se descarto con un numero** *** -- *865 -> 52 ms,
> *y **el mismo hash.**
>
> *** Y **es el metodo entero de la sesion, en una ronda**: *** *una hipotesis, **una medida que la pone a prueba**,
> *y **el descarte escrito.** *
