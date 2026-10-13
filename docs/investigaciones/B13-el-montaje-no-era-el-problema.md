# B13 · **El montaje NO era el problema**: con `fill` de 52 ms, «Entrar» sigue sin entrar

*(13 de octubre de 2026. **Y el sospechoso se cae, y queda otro.**)*

## 1. La prueba, y su resultado

```
LA LLAMADA · 7 acciones · 6,2 s · cleanup: terminated-owned-process · completeness: complete
*** y lo UNICO que cambio respecto a la ronda 231 fue un `wait_for_timeout` de 2000 ms antes de rellenar. ***

  fill «Usuario» *** 52 ms ***   *-- vs **865 ms** en la ronda 231*
  fill «Clave»   *** 19 ms ***   *-- vs **160 ms***
  click «Entrar» *** 73 ms ***   *-- vs **130 ms***

*** Y EL RESULTADO: ***
  accesibilidad de `/recetas` -> sha256 *** 260662eb141a12ae... *** · *** 854 bytes ***
  *** EL MISMO HASH. ***  *-- o sea: **la misma pantalla, y sin sesion.** *
```

> *** O sea: *** *** **la espera hizo su trabajo** -- *los `fill` bajaron de **865 a 52 ms**, *y de **160 a 19** -- *o
> sea: **el formulario YA estaba montado.** *
>
> *** Y **aun asi no entro.** *
>
> *** Y **eso descarta el sospechoso 1**, *y de la forma mas limpia: **se midio la hipotesis, y no se cumplio.** *

## 2. Y entonces quedan **dos**, y **el `fill` tambien se cae**

```
*** SOSPECHOSO 1 · «la pagina se estaba montando» ***  -> *** DESCARTADO ***: *los `fill` fueron instantaneos.*

*** SOSPECHOSO 3 · «el `fill` no propaga el evento a React» ***  -> *** CASI DESCARTADO ***, *y por el alta: *
   *en la ronda 230 **los mismos `fill`** (15, 19 y 14 ms) **si funcionaron** -- *y **la cuenta se creo.**
   -> *o sea: **`fill` SI llega al estado de React**, *y **esta probado con un 201.** *

*** SOSPECHOSO 4 · «el `click` en "Entrar" no dispara el alta» ***  -> *** ES EL QUE QUEDA. ***
```

> *** O sea: **el unico que queda es el `click`** *** -- *y **hay una razon concreta por la que puede no disparar**, *y
> **no es una teoria: es una diferencia entre los dos botones.** *
>
> ```
> EN EL ALTA:  se pulso *** «Créala» *** (para abrir) *y luego* *** «Crear cuenta» *** (para enviar) -- *** Y FUNCIONO. ***
> EN EL ENTRAR: se pulso *** «Entrar» *** -- *** y no hizo nada. ***
> ```
>
> *** Y **los dos son `button`, y los dos salen en la accesibilidad** *** -- *o sea: **los dos existen y son
> pulsables.** *
>
> *** Y **entonces: **o «Entrar» no es el boton que envia**, *o **envia y la respuesta no se aplica.** *

## 3. Y **la comprobacion es de lectura, y es una**: el `FormularioEntrar`

```
*** Y EL SITIO ES CONOCIDO: *** `Cesta.tsx` -- *donde esta `FormularioAlta` (l141), *y **donde tiene que estar
`FormularioEntrar`.** *

*** LO QUE HAY QUE MIRAR, Y SON TRES COSAS: ***
  a) *** si «Entrar» es `<button type="submit">` *** -- *o **un `type="button"` con `onClick`***
  b) *** y si su `onSubmit` tiene `e.preventDefault()` *** -- *como **el del alta (l153-154)***
  c) *** y si su guarda es como la del alta *** -- *`if (usuario.trim() && clave)`, *o **distinta***

*** Y CON ESO SE SABE: *** *si **el boton no envia**, *o **si envia y el fallo esta mas alla.** *
```

> *** Y **`FormularioAlta` tiene `type="submit"` implicito y `onSubmit` con `preventDefault`** *** (l151-156, leido).
> *Asi que **el patron esta en el fichero**, *y **el de entrar deberia seguirlo.** *
>
> *** Y **si lo sigue**, *entonces **el fallo esta en otro sitio** -- *y **el siguiente en la lista es **la
> respuesta**: *si el `fetch` **no manda `credentials`**, *la cookie **no se guarda**, *y **la sesion no existe
> aunque el API diga 200.** *
>
> *** Y **eso es `cesta.ts`**, *y **es la tercera cosa a leer.** *

## 4. Y el estado, con tres medidas y un descarte

```
RECORRIDO 4 · *** el alta ***          -> *** HECHO ***  *-- y con los MISMOS `fill`*
RECORRIDO 4b · *** volver a entrar ***  -> *** NO ***  ·  y **ya se sabe que NO es: ***
   1. *** no es la cuenta ***    -- *existe (verificado en la base)*
   2. *** no es la clave ***      -- *`POST /api/entrar` responde **200** con el usuario entero*
   3. *** no es el montaje ***    -- *con 2 s de espera, los `fill` bajan a 52 ms **y sigue sin entrar***
   4. *** y casi seguro que no es el `fill` *** -- *los mismos `fill` crearon una cuenta (201)*
   *** -> queda el `click`/submit, o la cookie ***
```

> *** Y **las cuatro se han ido cayendo una a una, y cada una con su medida** *** -- *que es **como se llega a un
> fallo**: *no **adivinando**, *sino **descartando con numeros.** *
>
> *** Y **lo que queda son DOS lecturas de `Cesta.tsx` y `cesta.ts`** *** -- *y **ninguna necesita navegador.** *
