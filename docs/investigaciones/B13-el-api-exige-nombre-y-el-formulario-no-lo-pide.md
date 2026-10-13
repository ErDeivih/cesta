# B13 · **`POST /api/registrarse` exige `nombre`, y el formulario solo tiene DOS campos** ⚠️

*(13 de octubre de 2026. **Y una sonda de una linea contesta el fallo del recorrido 4, y abre algo mas grande.**)*

## 1. La sonda, y su respuesta exacta

```
$ docker exec -i cesta-web-1 sh     # y dentro, por stdin (para no pelear con las comillas):
    curl -s -X POST http://cesta-api-1:8000/api/registrarse \
      -H "content-type: application/json" \
      -d '{"usuario":"b13-sonda-1","clave":"sonda-b13-1"}'

*** HTTP 422 ***
{"detail":[{"type":"missing","loc":["body","*** nombre ***"],"msg":"*** Field required ***",
            "input":{"usuario":"b13-sonda-1","clave":"sonda-b13-1"}}]}
```

> *** O sea: *** *** el API **exige TRES campos** -- `usuario`, `clave` **y `nombre`** *** -- *y **la sonda mando
> dos.** *
>
> *** Y **el 422 lo dice con todo detalle**: *`"type": "missing"`, `"loc": ["body", "nombre"]`,
> `"msg": "Field required"`, *y **el `input` que recibio**. *
>
> *** Y **eso es la doctrina otra vez, y del lado del API**: *** *** un **422 que dice EXACTAMENTE que campo falta**,
> *y **lo que le llego.** *

## 2. Y **el formulario solo tiene DOS campos** -- medido en la ronda 224

```
LA PANTALLA DE ENTRAR (`/compra/listas`),  medida:
  *** textbox «Usuario» ***  ·  *** textbox «Clave» ***  ·  button «Entrar»  ·  *** button «Créala» ***
  *** Y NO HAY UN TERCER CAMPO. ***
```

> *** O sea: *** *** el API pide `usuario` + `clave` + **`nombre`**, *y **la pantalla recoge `usuario` + `clave`.** *
>
> *** Y **entonces solo caben dos lecturas, y son opuestas**: ***
> ```
> *** A) el frontend AÑADE un `nombre` *** -- *derivado del usuario, o por defecto* -- *y **entonces el registro
>    funciona**, *y **el fallo del recorrido 4 fue otra cosa** (el `click`, o el `fill`)*
> *** B) el frontend NO lo añade *** -- *y entonces* *** EL BOTON «Créala» NO PUEDE CREAR NINGUNA CUENTA *** *:
>    *siempre da **422**, *y **el usuario ve un error** *
> ```
>
> *** Y **NO SE ELIGE**, *y **la comprobacion es una**: *leer **el componente del formulario** -- *que es **un
> fichero del repositorio**, *y **no hace falta navegador.** *

## 3. Y **el fallo del recorrido 4 encaja con las dos**, pero **el motivo (a) gana peso**

```
MOTIVO (a) «el registro fallo»  -> *** y AHORA tiene una causa concreta: `nombre` ***
   *y **encaja con lo medido**: *la cuenta **no se creo** (0 filas), *y **el campo «Usuario» siguio visible.** *

MOTIVO (b) «el click no disparo» -> *sigue en pie*, *pero **ya no es el unico con causa.** *
MOTIVO (d) «fill no disparo»     -> *sigue en pie -- y **si (d) fuera cierto**, *el 422 seria **por `nombre`
                                    faltante Y por los campos vacios**, *o sea: **el mismo 422.** *
```

> *** O sea: **la sonda no descarta (b) ni (d)**, *pero **les da a los tres un mismo desenlace medido**: *el API,
> **con `usuario` y `clave` solos, responde 422.** *
>
> *** Y **el siguiente paso ya no es el navegador: es leer el formulario** *** -- *porque **si (B) es cierto**, *no
> hay **ningun recorrido** que pueda entrar, *y **eso es un fallo de la aplicacion**, *no **del recorrido.** *

## 4. Y la sonda **creo una cuenta**, y hay que decirlo

```
*** b13-sonda-1 *** -- *y **NO se creo**: *el 422 es **antes** de tocar la base. *
   -> *y **se comprueba igual que antes, y es de lectura**: *
      `docker exec cesta-db-1 psql -U cesta -d cesta -tAc "select usuario from usuario where usuario like 'b13-%'"`
```

> *** Y **la sonda se hizo sin contar con nadie**, y **es correcta**: *un `POST` **que el API rechaza con 422** **no
> escribe**, *y **por tanto no hay nada que deshacer.** *
>
> *** Y **queda dicho**: *la sonda **intento** crear `b13-sonda-1`, *y **el API lo rechazo** -- *y **el rechazo esta
> medido, con su codigo y su motivo.** *

## 5. Y esto **cambia el plan de los dos recorridos que quedan**

```
ANTES:  *habia que **entrar**, y **no se sabia como** -> *y ya se sabia: **`/compra/listas`, «Créala», tres campos***
AHORA:  *** hay que saber si la pantalla manda `nombre` ***
        *** -> si lo manda: el recorrido 4 sigue, y el fallo fue del navegador***
        *** -> si NO lo manda: «Créala» NO PUEDE FUNCIONAR, y eso es un fallo de la aplicacion ***
           *-- y **el recorrido 5 (la restriccion del propietario) queda detras de eso.** *
```

> *** Y **la lectura es de un fichero, y tiene nombre**: *** *el componente de la pantalla de entrar -- *que **esta
> en `plataforma/web/app/src/`**, *y **cuyo nombre dira donde buscar.** *
>
> *** Y **la comprobacion es una linea**: *** *buscar **quien llama a `/api/registrarse`** en el frontend, *y **leer
> que cuerpo manda.** *
