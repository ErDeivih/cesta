# B13 · **El recorrido 4 fallo, y el fallo dice que falta una medida** -- no que no se pueda

*(13 de octubre de 2026. **Y es un fallo limpio: el clic se dio, y la prueba no paso.**)*

## 1. Lo que paso, con sus tiempos

```
paso 1 «puerta»   goto `/compra/listas`                     -> completed
paso 2 «usuario»  fill rol textbox «Usuario» = b13-recorrido-2251 -> *** completed, 392 ms ***
paso 3 «clave»    fill rol textbox «Clave»   = ensayo-b13-2251    -> *** completed,  33 ms ***
paso 4 «crear»    click rol button «Créala»                 -> *** completed,  44 ms ***
paso 5 «prueba»   wait_for rol textbox «Usuario» *hidden*   -> *** FAILED: timed out after 15000ms ***
paso 6 «calorias» goto `/calorias`                          -> *cancelled* («not executed after an earlier failure»)
```

> *** O sea: *** *** el clic **se dio** (y en **44 ms**), *y **la prueba no paso**: *el campo **«Usuario» sigue
> visible**, *o sea: *** LA SESION NO SE ABRIO. *** *
>
> *** Y **los `fill` funcionaron** (392 y 33 ms) *** -- *o sea: **los localizadores por `role`+`name` SON
> correctos**, *y **el formulario se relleno.** *
>
> *** Y **la prueba tambien es la correcta**: *** *el campo **desaparece solo si entras**, *y **no desaparecio.** *

## 2. Y **lo que NO se sabe**, que es lo que importa

> *** No se sabe **por que** no entro, *y **hay al menos cuatro motivos, y ninguno se elige**: ***
>
> ```
> a) *** el registro fallo *** -- *el API responde **4xx/5xx**, *y **la pantalla lo dice en algun sitio que no se
>    capturo** (no se pidio `console` ni `dom`)*
> b) *** el `click` no llego a disparar *** -- *y **44 ms es el tiempo del `dispatch`**, no **el de la respuesta**:
>    *una peticion de red **tarda mas**, *y **`click` no espera a que termine.** *
> c) *** la cuenta ya existia *** -- *y entonces el API responde **«Usuario repetido»** (`almacen.UsuarioRepetido`,
>    B13: *«crear dos veces no duplica»*)*
> d) *** `fill` rellena el `value` pero no dispara el evento que el formulario escucha *** -- *y entonces **la
>    pantalla ve los campos vacios**, *y **el boton no manda nada.** *
> ```
>
> *** Y **el (b) y el (c) son los mas probables**, *y **son distintos**: *el (b) se arregla **esperando**; *y el (c)
> se arregla **cambiando el nombre.** *
>
> *** Y **NO SE ELIGE NINGUNO**: *se dice que **los cuatro caben**, *y **cual es se decide midiendo.** *

## 3. Y **falta una medida que si se puede pedir**: la consola y los errores de pagina

```
LA PETICION QUE SE HIZO:   capture: { at_end: [url, accessibility], events: [] }
*** LA QUE HACE FALTA: ***  capture: { at_end: [url, accessibility],
                                       *** events: [\"console\", \"page-errors\"] *** }
```

> *** O sea: **el recorrido se hizo a ciegas** *** -- *y **no por el proveedor, que **ofrece `console` y
> `page-errors`**, *sino **porque no se pidieron.** *
>
> *** Y **eso es lo mismo que paso en la ronda 218** *(-- cuando pedi 18 eventos de red y la limpieza se quedo
> incompleta): *allí **pedi de mas**; *y **aqui, de menos.** *
>
> *** Y **las dos veces la leccion es la misma**: *** *** pedir **lo que se va a leer** -- y **cuando algo falla, lo
> que hay que leer es **el error.** *

## 4. Y el estado de la cuenta `b13-recorrido-2251`, que **hay que decir**

```
*** NO SE SABE SI SE CREO. ***
   -> *si **se creo**, el proximo intento con **el mismo nombre** dara **«Usuario repetido»**
   -> *y si **no se creo**, **el mismo nombre vale** -- *y **reintentar con el no dice nada.**
*** POR ESO EL PROXIMO INTENTO USA UN NOMBRE NUEVO *** -- *con **sello distinto**, *y **asi el (c) queda descartado
   por construccion**: *si **entra con un nombre nuevo**, *entonces **el problema era el nombre**; *y si **no entra
   tampoco**, *entonces **no era el nombre.** *
```

> *** Y **la comprobacion de si existe** es **una linea, y es de lectura**, *y **no toca nada de nadie**: *
> ```
> docker exec cesta-db-1 psql -U cesta -d cesta -c \
>   "select usuario, nombre, creado from usuario where usuario like 'b13-recorrido-%'"
> ```

## 5. Y los cinco recorridos, con el 4 **intentado y no pasado**

```
RECORRIDO 1 · el lanzador y las tres raices  -> *** HECHO ***
RECORRIDO 2 · /compra                        -> *** HECHO ***
RECORRIDO 3 · /recetas                       -> *** HECHO ***
RECORRIDO 4 · /calorias                      -> *** INTENTADO · NO PASO ***
     *** y lo que falta no es permiso ni decision: es UNA MEDIDA -- la consola y los errores de pagina. ***
RECORRIDO 5 · *** la restriccion ***          -> *por hacer, y **necesita el 4.** *
```

> *** Y **no se declara el 4 «limitado»** *** -- *se declara **intentado, con el fallo y sus cuatro motivos
> posibles**, *y **con la medida que lo decide.** *
>
> *** Que es **la unica forma honesta de escribir un intento que falla**: *** *** no «no se pudo», *sino **«esto paso,
> esto se midio, esto no se sabe, y esto es lo que lo decide.»** *
