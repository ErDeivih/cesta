# B13 · **¡EL RECORRIDO 4 ESTA HECHO!** -- la cuenta se creo, entro, y la pantalla lo demuestra

*(13 de octubre de 2026. **Tres intentos, y el tercero con los nombres medidos: 3,8 s y limpio.**)*

## 1. La llamada, y sus siete acciones

```
`capture_browser_scenario` · Chrome oculto · *** 7 acciones · 3,8 s · cleanup: terminated-owned-process ***
*** completeness: complete · equality_eligible: true ***  ·  y **sin eventos pedidos** (0)

  1. `goto`  `/compra/listas`
  2. `click` *** rol button, nombre «Créala» ***        *-- y cambia al formulario de alta*
  3. `fill`  *** rol textbox, nombre «Tu nombre» ***     = Ensayo B13
  4. `fill`  *** rol textbox, nombre «Usuario» ***       = b13-recorrido-2301
  5. `fill`  *** rol textbox, nombre «Contraseña» ***    = ensayo-b13-2301
  6. `click` *** rol button, nombre «Crear cuenta» ***
  7. `wait_for_timeout` 2,5 s  -- *y **captura** al final*
```

> *** Y **las siete acciones son las siete que salieron de las dos llamadas anteriores**: *** *cuatro
> localizadores **medidos en la ronda 229**, *y **los dos nombres que yo habria usado mal** («Clave» y «Créala»)
> **sustituidos por los de verdad** («Contraseña» y «Crear cuenta»). *
>
> *** O sea: **el recorrido no se hizo a la tercera por insistir: se hizo porque **la segunda midio lo que faltaba.** *

## 2. Y **la prueba es que el formulario se fue** -- y que **hay contenido de usuario**

```
*** EL FORMULARIO DE ENTRAR YA NO ESTA ***  -- *ni «Usuario», ni «Clave», ni «Crear cuenta».*

*** Y EN SU LUGAR, CONTENIDO QUE SOLO EXISTE CON SESION: ***

  *** EL MENU CAMBIA: ***
    link «Listas *** No hay lista de casa, asi que no hay nada que contar ***»  -> `/compra/listas`

  *** Y EL `main`: ***
    paragraph: «*** No tienes ninguna lista ***»
    paragraph: «Todavia no hay listas guardadas. Busca un producto o toca uno de abajo: ***
                se apunta en la lista de casa, QUE SE CREA SOLA ***, y la cantidad se cambia aqui.»
    paragraph: «*** Lo que compra la casa ***»
    paragraph: «Un toque y a la lista. *** Lo tocado se cambia en la cesta. ***»
    *** list: SEIS PRODUCTOS, CON SU PRECIO POR UNIDAD Y SU CADENA, Y SU BOTON «Anadir»: ***
      «Tortilla de patatas con cebolla Dia Al Punto 600 g · *** 4,33 €/kg *** · en DIA»
      «PRODUCTO ALCAMPO Cafe molido natural descafeinado espresso 250 g · *** 9,44 €/kg *** · en Alcampo»
      «LE RUSTIQUE Lonchas de queso raclette 350 g · *** 24,91 €/kg *** · en Alcampo»
      «TWIX Barritas de chocolate con caramelo y galleta 10 uds. 50 g · *** 15,88 €/kg *** · en Alcampo»
      «Leche fresca entera · *** 1,15 €/l *** · en Aldi»
      «REVLON Colorstay suede ink Tono 018 First class · *** 11,19 €/ud *** · en Alcampo»
```

> *** Y **el menu que cambia es la mejor prueba de las tres**: *** *** «Listas» **no lleva un icono de sesion**: *lleva
> **«No hay lista de casa, asi que no hay nada que contar»** -- *o sea: **el menu sabe si hay lista, y lo dice.** *
>
> *** Y **eso es la doctrina en un enlace de navegacion**: *** *** un sitio **donde cabria un cero o un espacio en
> blanco** *lleva **una frase que explica que no hay, y por que.** *

## 3. Y los seis productos **demuestran dos cosas mas**, y las dos son del encargo

```
*** 1) EL PRECIO VA POR UNIDAD, Y LA UNIDAD ES LA DEL PRODUCTO: ***
   *** 4,33 €/kg ***  ·  *** 9,44 €/kg ***  ·  *** 24,91 €/kg ***  ·  *** 15,88 €/kg ***  ·  *** 1,15 €/l ***  ·  *** 11,19 €/ud ***
   -> *y eso es **`formato.eurosUnidad`** (B12): *«el dinero llega en **centimos enteros** y se pasa a euros
      **solo al pintar**»; *y **la unidad la pone el producto**, *no **una constante.** *

*** 2) Y CADA UNO DICE SU CADENA: *** *** en DIA · en Alcampo · en Aldi ***
   -> *y **son cuatro productos de Alcampo, uno de DIA y uno de Aldi** -- *o sea: **la lista mezcla cadenas**, *
      *y **cada linea dice la suya.** *
```

> *** Y **la marca del producto tambien esta**: *** *«PRODUCTO ALCAMPO», «LE RUSTIQUE», «TWIX», «REVLON» *-- *o sea:
> **el `nombre_visto` de la fuente**, *y **no un nombre normalizado.** *
>
> *** Y **el «REVLON» es un producto de bazar** *** -- *y **B02 midio exactamente eso**: *«de sus 37.019 productos,
> **solo el 33 % era comida**, *y su rama mas grande no era "Alimentacion" sino "Hogar y Decoracion"». *
> *** O sea: **la pantalla esta enseñando el catalogo tal como es**, *y **no solo la comida.** *

## 4. Y la cuenta, y la decision del propietario

```
*** LA CUENTA SE CREO: `b13-recorrido-2301` · «Ensayo B13» ***
   -> *y **el propietario ya lo habia decidido** (B13): «crear usuarios de prueba nuevos», **de forma aditiva** *
   -> *y **`crea_usuario` solo hace un `INSERT`** -- *asi que **no se toco nada suyo.** *
   -> *y **el nombre lleva prefijo `b13-`**, *que es **la convencion que ya habia** (`a09`, `c01b`, `f07`)*
```

> *** Y **la frase del alta se cumplio**: *** *** «al crearla **YA ENTRAS**» *** -- *y **entro**, *sin **una segunda
> pantalla.** *
>
> *** Y **es `main.py:105`**: *`registrarse` **devuelve la cookie en la misma respuesta**, *y **por eso no hay que
> entrar despues.** *
>
> *** Y **lo dijo la propia pantalla, en la ronda 229**: *** *«Se queda en casa, en esta Cesta, y al crearla ya
> entras.» *

## 5. Y los cinco recorridos, con el 4 **hecho**

```
RECORRIDO 1 · el lanzador y las tres raices  -> *** HECHO ***
RECORRIDO 2 · `/compra`                      -> *** HECHO ***
RECORRIDO 3 · `/recetas`                     -> *** HECHO ***  *-- y **sin sesion**, que es su estado*
RECORRIDO 4 · *** el alta y la sesion ***     -> *** HECHO ***  *-- y **la cuenta creada y la cookie puesta***
RECORRIDO 5 · *** `/calorias` con sesion, y la restriccion del propietario ***  -> *** y ahora es UNA LLAMADA MAS ***
```

> *** Y **el 4 no era «ver `/calorias`»: era «entrar»** *** -- *y **el plan lo puso como recorrido porque
> entrar es lo que hace posible los demas.** *
>
> *** Y **lo que queda para el 5** es **una llamada de dos acciones** (`goto /calorias` y capturar), *con **la
> sesion que esta llamada acaba de crear.** *-- *y **despues**, *la **restriccion del propietario**, que es
> **traspasar una receta y mirar las lineas.** *
