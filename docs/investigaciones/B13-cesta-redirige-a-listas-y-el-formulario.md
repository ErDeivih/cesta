# B13 · **`/cesta` redirige a `/compra/listas`**, y el formulario tiene sus localizadores -- y su motivo

*(13 de octubre de 2026. **Y la ultima pieza que faltaba para los dos recorridos.**)*

## 1. Lo que se observo, y esta limpio

```
cleanup: «terminated-owned-process» · completeness: «complete» · 3,6 s

*** `/cesta` REDIRIGE A `/compra/listas` ***  (after_url: http://127.0.0.1:8080/compra/listas)

  banner:  «Compra»  ·  heading «Listas» [level=1]
  *** main: ***
    heading «Lista» [level=1]
    *** heading «Entra para ver tu lista» [level=2] ***
    *** paragraph: ***
      *** «La lista de la compra es tuya y de quien la compartas. Por eso hay que entrar: ***
      *** UNA LISTA SIN DUEÑO NO SE PUEDE COMPARTIR NI RECUPERAR.» ***
    text «Usuario»   ·  *** textbox «Usuario» ***
    text «Clave»     ·  *** textbox «Clave» ***
    *** button «Entrar» ***
    text «¿No tienes cuenta?»  ·  *** button «Créala» ***
```

## 2. Y **los localizadores estan aqui**, y son de `role` y `name`

```
*** rol `textbox`, nombre «Usuario » ***   -> *el campo del usuario*
*** rol `textbox`, nombre «Clave » ***     -> *el campo de la clave*
*** rol `button`, nombre «Entrar » ***     -> *la puerta de `POST /api/entrar`*
*** rol `button`, nombre «Créala » ***     -> *** y esta es la del registro (`POST /api/registrarse`, 201) ***
```

> *** O sea: **las dos rutas del API tienen su boton en la pantalla** *** -- *«Entrar» y «Créala». *Y **el segundo
> nombre es un imperativo**: *«**Créala**», *no «Registrarse» **-- *habla de **la cuenta**, *y **le dice al usuario
> lo que va a pasar.** *
>
> *** Y **los cuatro son de `role` + `name`** *** -- *que es **el localizador mas estable de los tres** (`role`,
> `test_id`, `css`), *porque **viene de la accesibilidad**, *y **no del marcado.** *
>
> *** Y **por eso se puede escribir el recorrido sin mirar el HTML** *** -- *y **sin inventar un selector.** *

## 3. Y **el motivo del «hay que entrar» es el mejor del proyecto**

> *** «La lista de la compra es tuya y de quien la compartas. *** *** POR ESO HAY QUE ENTRAR: *** *** UNA LISTA
> SIN DUEÑO NO SE PUEDE COMPARTIR NI RECUPERAR.» ***
>
> *** Y **son las dos cosas que el encargo pide, dichas como motivo**: ***
> ```
> *** «COMPARTIR» ***   -> *`lista_acceso` (B13: la tabla que **da acceso a otra persona**)*
> *** «RECUPERAR» ***    -> *y **la idempotencia**: *`traspaso.clave PRIMARY KEY` (B05) y `sesion` (B13)*
> ```
>
> *** O sea: **la sesion no esta por costumbre** *** -- *esta porque **sin dueño, la lista no se puede compartir
> (no hay a quien) ni recuperar (no hay de quien).** *
>
> *** Y **es la doctrina en su forma mas economica**: *** *** una frase, **sin «por seguridad»**, *y **con los dos
> motivos concretos.** *

## 4. Y **`/cesta` no es una pagina de entrar: es la lista, y redirige a ella**

```
`/cesta`  ->  *** `/compra/listas` ***
   -> *o sea: **la entrada no es una pantalla aparte**: *es **la lista**, *que **es lo primero que necesita saber
      quien eres.** *
   -> *y **por eso el menu no tiene «Entrar»**: *no hay **una pagina de entrar**; *hay **una lista que, si no sabe
      quien eres, te lo pregunta.** *
```

> *** Y **eso explica el nombre**: *** *el proyecto se llama **Cesta**, *y **`/cesta` es **la lista de la compra**. *
> *O sea: **la aplicacion se llama como su objeto**, *y **la puerta es la lista misma.** *

## 5. Y los dos recorridos que quedan tienen **ya sus seis pasos, con los nombres exactos**

```
RECORRIDO 4 · `/calorias`, con sesion

  PASO 1  `goto` *** `/compra/listas` ***          *-- o `/cesta`, que redirige aqui*
  PASO 2  `fill`  *** rol textbox, nombre «Usuario» ***   <- *un usuario de ensayo, con prefijo y sello*
  PASO 3  `fill`  *** rol textbox, nombre «Clave» ***     <- *una clave inventada: la cuenta es de ensayo*
  PASO 4  `click` *** rol button, nombre «Créala» ***     <- *** y este crea Y ENTRA, en un solo paso ***
  PASO 5  *** `wait_for` -> algo que SOLO se ve con sesion ***   *-- y `main` ya no dira «Entra para ver tu lista»*
  PASO 6  `goto` *** `/calorias` ***                      *-- ya con cookie*

RECORRIDO 5 · *** la restriccion del propietario ***     *-- despues del 4, y con la misma sesion*
```

> *** Y **el paso 5 es la prueba, y tiene una frase exacta que buscar**: *** *** si `main` **ya no dice** «Entra para
> ver tu lista», *entonces **entro**. *Y **si lo sigue diciendo**, *no. *
>
> *** Y **es mejor que buscar un elemento cualquiera**: *** *la frase **«Entra para ver tu lista»** *es **el estado
> sin sesion**, *y **su ausencia es el estado con sesion.** *
