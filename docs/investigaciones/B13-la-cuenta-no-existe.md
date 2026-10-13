# B13 · **La cuenta no existe**: el fallo del recorrido 4 **no fue «usuario repetido»**

*(13 de octubre de 2026. **Y una consulta de lectura deja tres motivos en pie y descarta uno.**)*

## 1. La comprobacion, y su resultado

```
$ docker exec cesta-db-1 psql -U cesta -d cesta -tAc \
    "select usuario, nombre from usuario where usuario like 'b13-recorrido-%'"
*** (sin filas) ***
```

> *** Y **la consulta **funciono** *** -- *no dio error, *y devolvio **cero filas.** *
>
> *** O sea: *** *** `b13-recorrido-2251` NO SE CREO. *** *
>
> *** Y **eso descarta el motivo (c)** *** -- *el de **«la cuenta ya existia»**: *si **el registro hubiera fallado
> por nombre repetido**, *habria **una** fila con ese nombre (de un intento anterior), *y **no hay ninguna.** *
>
> *** Y **ademas** lo descarta por el otro lado: *** *si **el registro hubiera funcionado**, *habria **una fila**; *y
> **tampoco la hay.** *Asi que **la peticion o no salio, o salio y no creo nada.** *

## 2. Y los motivos que quedan, **de cuatro a tres**

```
(a) *** el registro fallo ***               -> *sigue en pie*, *y **ahora se sabe que fallo SIN crear la fila**
(b) *** el `click` no llego a disparar ***    -> *sigue en pie*: **44 ms es el `dispatch`, no la respuesta**
(c) ~~la cuenta ya existia~~                  -> *** DESCARTADO: no hay ninguna fila ***
(d) *** `fill` no disparo el evento ***       -> *sigue en pie*
```

> *** Y **los tres que quedan se distinguen con UNA medida**: *** *** la consola y los errores de pagina
> (`events: ["console", "page-errors"]`). *
>
> ```
>   (b) el click no disparo    -> *** y no habria NINGUNA peticion ni error ***: la consola estaria limpia
>   (a) el registro fallo      -> *** habria un error, o un 4xx/5xx *** -- *y si el API contesta, **algo**
>                                 *aparece*
>   (d) fill no disparo         -> *y **el formulario se quejaria de campos vacios*** -- *o **no haria nada**,
>                                 *que es **lo mismo que (b)** por fuera, *y **se distingue por `console`** *
> ```
>
> *** O sea: **la consola separa (b) de (a)**, *y **esa es la medida que falta.** *

## 3. Y **hay una cuarta comprobacion**, que no necesita el navegador

> *** Si **el API funciona**, *se puede comprobar **sin navegador**: *** *** `POST /api/registrarse` a mano, *desde
> dentro de la red de Docker (la API **no esta publicada al host**, B16), *y **mirar el codigo de respuesta.** *
>
> ```bash
> docker exec cesta-web-1 sh -c 'curl -s -o /dev/null -w "%{http_code}\n" \
>   -X POST http://cesta-api-1:8000/api/registrarse \
>   -H "content-type: application/json" \
>   -d "{\"usuario\":\"b13-sonda-1\",\"clave\":\"sonda-b13-1\"}"'
> ```
>
> *** Y **eso separa las dos mitades del problema**: ***
> ```
> *** si responde 201 ***  -> *el API **crea cuentas**, *y **el fallo esta en el navegador** (b) o (d)*
> *** si responde 4xx/5xx *** -> *el API **no las crea con esos campos**, *y **el fallo esta en lo que se manda** (a)*
> ```
>
> *** Y **NO se ha hecho todavia**, *y **se dice**: *es **una sonda** que **crea una cuenta** (`b13-sonda-1`), *y
> **escribir en la base de casa es lo que B13 ya decidio** -- *pero **se hace cuando se sepa que hace falta**, *no
> **a ciegas.** *

## 4. Y el estado, sin adornos

```
RECORRIDO 4 · `/calorias`  -> *** INTENTADO · NO PASO ***
   *** y ahora se sabe MAS que antes, y las dos cosas por medicion: ***
     1. *** los localizadores por `role`+`name` SON correctos *** -- *los dos `fill` funcionaron (392 y 33 ms)*
     2. *** la cuenta NO se creo *** -- *0 filas, y por tanto **el fallo no fue «repetido»***
   *** y lo que falta es UNA medida: la consola y los errores de pagina. ***
```

> *** Y **la proxima ronda tiene tres caminos, y el orden importa**: ***
> 1. *** repetir el recorrido pidiendo `console` y `page-errors` *** -- *y **con nombre nuevo**, para no mezclar;*
> 2. *** y si la consola no dice nada, la sonda a `POST /api/registrarse` *** -- *que **separa el API del navegador**;*
> 3. *y **NO se declara limitado**: *se declara **intentado, medido en parte, y con la medida que falta dicha.** *
