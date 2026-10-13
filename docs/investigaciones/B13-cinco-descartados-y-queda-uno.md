# B13 · **Cinco sospechosos descartados, y queda uno**: la guarda del `onSubmit`

*(13 de octubre de 2026. **Y la eliminacion esta escrita, con su medida cada una.**)*

## 1. Y el (B) se cae, y con una linea al lado

```
`plataforma/web/app/src/api/cesta.ts`

  l5   *  «`pide()` tal cual: *** hace falta mandar `credentials` *** en las peticiones que [...]»
  l21  export async function *** entrar ***(usuario, clave, ...)
  l24      method: 'POST',
  *** l26      credentials: 'same-origin' ***        <- *** LO TIENE ***
  l45  *  «... *** igual -- mismo `credentials`, mismo trato del error, mismo `detail` *** -- po[rque]...»
  l53  export async function *** registrarse ***(usuario, nombre, clave, ...)
  l56      method: 'POST',
  *** l58      credentials: 'same-origin' ***        <- *** Y TAMBIEN ***
```

> *** O sea: *** *** **las dos funciones mandan `credentials: 'same-origin'`** *** -- *y **ademas el fichero lo dice
> en un comentario**: *«**igual -- mismo `credentials`, mismo trato del error, mismo `detail`**». *
>
> *** Y **eso descarta el (B)**, *que era **el que explicaba el 200 sin sesion** *** -- *y **lo descarta con dos
> lineas contiguas, que es **la mejor forma de descartar.** *
>
> *** Y **el comentario de `l45` es la prueba de que **alguien ya se preocupo de que fueran iguales** *** -- *o sea:
> *la coherencia **no es casualidad: esta escrita.** *

## 2. Y la lista de sospechosos queda **con uno**, y con **cinco descartes medidos**

```
RECORRIDO 4b · «volver a entrar»  -> *** NO ***     y **los cinco, uno a uno: ***

  1. ~~la cuenta~~            -> *** DESCARTADO ***  *-- `b13-recorrido-2301 | Ensayo B13` esta en la base*
  2. ~~la clave~~             -> *** DESCARTADO ***  *-- `POST /api/entrar` da **200**, con el usuario entero*
  3. ~~el montaje~~           -> *** DESCARTADO ***  *-- con 2 s de espera, `fill` baja a **52 ms** y sigue igual*
  4. ~~el click / el submit~~ -> *** DESCARTADO ***  *-- `Cesta.tsx:111`: **es `type="submit"`***
  5. ~~`credentials`~~        -> *** DESCARTADO ***  *-- `cesta.ts:26` y `:58`: **los dos lo mandan**, y `l45` lo dice*

  *** -> QUEDA UNO: ***
  *** 6. LA GUARDA DEL `onSubmit` DE `FormularioEntrar` ***  *-- `Cesta.tsx:71`*
     *y **el boton NO la lleva en el `disabled`** (l111: solo `isPending`), *asi que **si existe, esta en el
     `onSubmit`.** *
```

> *** Y **cinco descartes, cada uno con su evidencia** *** -- *y **dos de ellos con un numero** (200, 52 ms), *y
> **tres con una linea de codigo** (l111, l26, l58). *
>
> *** Y **el sexto es el unico que queda, y esta en un fichero que ya se abrio** *** -- *o sea: **la ronda que viene
> es una lectura, y no un experimento.** *
>
> *** Y **no es casualidad que sea el unico que queda**: *** *es **el mismo sitio donde estaba el fallo de la ronda
> 225** -- *la guarda del `onSubmit` del alta -- *y **por eso se sospecha de el primero... y por eso se dejo para el
> final**, *cuando **los otros cinco ya no podian ser.** *
>
> *** Que es **el orden correcto**: *** *** se descarta lo que se puede medir, *y **lo que queda es lo que se lee.** *

## 3. Y si la guarda **no** es el fallo, entonces **el fallo no esta en el frontend**

```
*** Y ESO HAY QUE DECIRLO ANTES DE LEERLO, para no forzar la conclusion: ***
  *si el `onSubmit` de `FormularioEntrar` **resulta correcto** -- *guarda que se cumple, `preventDefault`, `mutate` --
  *entonces **el fallo esta mas alla del frontend**: *
    -> *o **en el `pide()`**, *que es **el ayudante comun** (y `registrarse` **tambien lo usa**, *y funciona)*
    -> *o **en `alEntrar`**, *que es **la funcion que se llama al entrar** -- *y **si el alta la llama igual**, *
       *y **el alta funciona**, *entonces **tampoco.** *
    -> *o **en que las dos llamadas NO son iguales** *-- *y **`l45` dice que si**, *pero **`l45` es un comentario**:
       *y **un comentario puede estar desactualizado.** *
```

> *** O sea: **la lectura del `onSubmit` decide entre «esta en el frontend» y «esta mas alla»** *** -- *y **las dos
> salidas son utiles**, *y **ninguna se descarta antes de leer.** *
