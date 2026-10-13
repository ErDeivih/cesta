# B13 · **El formulario de alta, medido entero** -- y sus cuatro localizadores son **otros cuatro**

*(13 de octubre de 2026. **Y una llamada de cinco acciones los da todos: 3,0 s, limpia.**)*

## 1. Lo que hace `button «Créala»`, y lo que aparece

```
ANTES (formulario de ENTRAR):   textbox «Usuario» · textbox «Clave» · button «Entrar» · button «Créala»

*** Y AL PULSAR «Créala», APARECE ESTO: ***
  *** heading «Crea tu cuenta» [level=2] ***
  *** paragraph: ***
    *** «La cuenta es lo que hace que la lista tenga dueño: sin ella no se guarda ni se puede compartir. ***
    *** Se queda en casa, en esta Cesta, y al crearla YA ENTRAS.» ***
  *** text «Tu nombre»   ·  textbox «Tu nombre»   ·  placeholder «Como quieres que te vean» ***
  *** text «Usuario»     ·  textbox «Usuario»     ·  placeholder «sin tildes ni espacios» ***
  *** text «Contraseña»  ·  textbox «Contraseña»  ·  placeholder «ocho caracteres o más» ***
  *** button «Crear cuenta» ***
  *** text «¿Ya tienes cuenta?»  ·  button «Entra» ***
```

## 2. Y **los dos nombres que yo habria usado mal**, ahora medidos

```
*** LOS CUATRO LOCALIZADORES DEL ALTA: ***
  *** rol `textbox`, nombre «Tu nombre» ***
  *** rol `textbox`, nombre «Usuario» ***
  *** rol `textbox`, nombre «Contraseña» ***   <- *** ¡NO «Clave»! ***
  *** rol `button`,  nombre «Crear cuenta» ***  <- *** ¡NO «Créala»! ***
```

> *** O sea: **la llamada B que yo iba a hacer **habria fallado dos veces** *** -- *porque **el boton no se llama
> «Créala»** (se llama **«Crear cuenta»**) *y **el campo no se llama «Clave»** (se llama **«Contraseña»**). *
>
> *** Y **es exactamente el motivo de partir la llamada**: *** *si hubiera ido directo a los doce pasos, *habria
> **fallado en el paso 7**, *y **sin saber por que.** *
>
> *** Y **el reparto en dos llamadas no es una precaucion: es lo que dio el dato.** *

## 3. Y los dos formularios son **dos componentes distintos**, y lo dice el texto

```
ENTRAR  ->  heading «*** Entra para ver tu lista ***»  ·  «Usuario» · «Clave»  ·  «Entrar» · «Créala»
ALTA    ->  heading «*** Crea tu cuenta ***»           ·  «Tu nombre» · «Usuario» · «Contraseña»  ·  «Crear cuenta»

*** Y CADA UNO TIENE SU BOTON DE CAMBIO AL OTRO: ***
  *en ENTRAR:* *** button «Créala» ***       -> *y da la vuelta al ALTA*
  *en ALTA:*   *** button «Entra» ***        -> *y da la vuelta al ENTRAR*
```

> *** Y **son simetricos, con nombres que se contestan**: *** *«¿No tienes cuenta? **Créala**»* · *«¿**Ya tienes
> cuenta**? **Entra**»* -- *y **los dos dicen lo que va a pasar.** *
>
> *** Y **`textbox «Contraseña»` vs `textbox «Clave»`** *** -- *o sea: **el mismo dato se llama de dos maneras en las
> dos pantallas.** *Y eso **no es un fallo**: *«**Clave**» es **el nombre corto de entrar**; *y «**Contraseña**» es
> **el nombre completo de crear**, *donde **se esta eligiendo** y **el `placeholder` dice la regla**. *
> *** Y **la regla esta en el `placeholder`, y no en el codigo**: *** *** «ocho caracteres o más» *** -- *y
> `Cesta.tsx:136-139` dice **por que**: *la verdad **la dice `api/registro.py`**, *y **copiarla seria una segunda
> copia que se queda vieja.** *

## 4. Y **la frase del alta es la mejor de las cuatro**, y contesta el encargo

> *** «La cuenta es lo que hace que **la lista tenga dueño**: sin ella **no se guarda ni se puede compartir**. ***
> *** Se queda en casa, en esta Cesta, *** *** Y AL CREARLA YA ENTRAS. ***» *
>
> *** Y son **cuatro cosas**, y **las cuatro son del encargo**: ***
> ```
> *** «la lista tenga dueño» ***   -> *y **por eso hay que entrar** (B13: «una lista sin dueño no se puede
>                                    compartir ni recuperar»)*
> *** «no se guarda» ***            -> *la persistencia: *lo que se hace **se queda** *
> *** «ni se puede compartir» ***   -> *`lista_acceso`*
> *** «SE QUEDA EN CASA, EN ESTA CESTA» *** -> *** y esta es la del encargo: «no despliegues publicamente» ***
> *** «y al crearla YA ENTRAS» ***  -> *y **por eso `registrarse` devuelve la cookie** (`main.py:105`)*
> ```
>
> *** O sea: **la pantalla dice, en tres lineas, TODO lo que B13 y el encargo piden de una cuenta** *** -- *y **lo
> dice al usuario**, *no **al programador.** *

## 5. Y la llamada B queda **con sus cinco acciones y sus nombres exactos**

```
*** LLAMADA B · el alta, con los cuatro localizadores medidos: ***

  1. `goto`  *** `/compra/listas` ***
  2. `fill`  *** rol textbox, nombre «Tu nombre» ***   = Ensayo B13
  3. `fill`  *** rol textbox, nombre «Usuario» ***     = b13-recorrido-2291
  4. `fill`  *** rol textbox, nombre «Contraseña» ***  = ensayo-b13-2291
  5. `click` *** rol button,  nombre «Crear cuenta» ***
  *** -- y `capture.at_end: [url]`, para ver a donde va ***
```

> *** Y **ocho caracteres o mas**: *`ensayo-b13-2291` tiene **15**, *asi que **pasa la regla del `placeholder`** --
> *y **la del API se vera en su 422 o en su 201.** *
>
> *** Y **NO hace falta pulsar «Créala» antes**: *** *`/compra/listas` **abre en ENTRAR**, *pero **la llamada B puede
> empezar por el alta** si **se navega al estado de alta**... *y **si no hay URL directa**, *entonces **si**:* *un
> `click` en «Créala» primero, *y **seran seis acciones.** *
>
> *** Y **eso es un dato que la llamada A **no** contesta**: *habria que ver **si `/compra/listas` recuerda el
> estado** -- *y **no se sabe**, *y **se dice.** *
