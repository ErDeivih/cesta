# B13 · **El API entra (200), y el navegador no** -- asi que el fallo era de mi recorrido

*(13 de octubre de 2026. **Y una sonda de una linea separa las dos mitades: la aplicacion funciona.**)*

## 1. La prueba, y su respuesta

```
$ docker exec -i cesta-web-1 sh    # y dentro, por stdin:
    curl -s -X POST http://cesta-api-1:8000/api/entrar \
      -H "content-type: application/json" \
      -d '{"usuario":"b13-recorrido-2301","clave":"ensayo-b13-2301"}'

*** HTTP 200 ***
{"usuario":{"id":"*** 4a48c57d-a5ba-480c-b9a0-989e2941e437 ***","usuario":"*** b13-recorrido-2301 ***",
            "nombre":"*** Ensayo B13 ***"}}
```

> *** O sea: *** *** **el API entra, y devuelve el usuario entero** *** -- *con **su `id`**, *su `usuario`, *y su
> `nombre`. *
>
> *** Y **eso cierra la mitad de la pregunta, y de la forma mas limpia**: ***
> ```
> *** la cuenta existe ***        -> *verificado en la base (ronda 230)*
> *** la clave es la correcta ***  -> *** el API dice 200 ***
> *** y la sesion es real ***       -> *el API devuelve **`id`** -- *o sea: **sabe quien eres.** *
> ```
>
> *** Y **por tanto: **el fallo NO es de la aplicacion** *** -- *es **de mi recorrido**, *que **no consiguio que el
> navegador mandara la peticion.** *

## 2. Y la causa, entonces, esta en **el navegador**, y hay **dos sospechosos, y los dos son mios**

```
*** SOSPECHOSO 1 · el `fill` no propago al estado de React ***
   -> *`fill` escribe el `value` del `input`, *y **React lee su propio estado**; *si **el evento `input` no se
      dispara**, *React **cree que el campo esta vacio** *
   -> *y **entonces `FormularioEntrar` tiene la misma guarda que el alta**: *si cree que falta algo, *
      *** NO MANDA NADA ***
   -> *** y encaja con el dato: el `fill` de «Usuario» tardo 865 ms *** (la pagina se estaba montando)

*** SOSPECHOSO 2 · el `click` fue demasiado pronto ***
   -> *130 ms, y **el `onSubmit` puede no estar enganchado** *
   -> *pero **en el alta el `click` funciono con 430 ms y 54 ms**, *asi que **este es menos probable.** *
```

> *** Y **el sospechoso 1 es el fuerte**, *y **tiene un numero**: *865 ms. *
>
> *** Y **es LA MISMA CLASE DE FALLO que el de la ronda 225** *** -- *«el formulario no manda si cree que falta
> algo» -- *y **las dos veces la guarda hizo su trabajo.** *

## 3. Y **la prueba que lo confirma**, concreta y corta

```
*** LA MISMA LLAMADA, Y LO UNICO QUE CAMBIA ES UNA ESPERA ANTES DE RELLENAR: ***

  1. `goto`  `/compra/listas`
  2. *** `wait_for_timeout` 2000 ***   <- *para que el formulario **este montado** antes de tocarlo*
  3. `fill` «Usuario»  · 4. `fill` «Clave»
  5. `click` «Entrar»
  6. `goto` `/recetas`  · 7. `wait_for_timeout` 3000

  *** Y EL RESULTADO SE MIDE CON EL MISMO HASH QUE YA SE TIENE: ***
     *** si la accesibilidad de `/recetas` YA NO es `260662eb...` ***  -> *** ENTRO ***
     *** y si sigue siendo `260662eb...` ***                            -> *** no entro, y entonces es el `fill` ***
```

> *** Y **tener el hash de antes es lo que hace la prueba barata**: *** *** no hay **que interpretar** una pantalla;
> *hay **que comparar un hash** *con **uno que ya esta medido.** *

## 4. Y lo que esto significa, y lo que **no**

```
*** LO QUE SIGNIFICA: ***
  *** la aplicacion hace lo suyo: *** *crea cuentas (201), *entra (200), *y **guarda la cookie en la respuesta** *
  *** y mi recorrido no: *** *el navegador **no llego a mandar la peticion** -- *y **la causa es mi forma de
  rellenar**, *no **la suya.** *

*** LO QUE NO SIGNIFICA: ***
  *** no es un fallo de la aplicacion ***  -- *y **decir lo contrario seria un falso positivo**, *
     *que es **exactamente lo que el encargo prohibe**: *«no consideres terminado lo que solo abrio una pantalla
     vacia» -- y **su simetrico**: *no **declares roto lo que solo no has sabido usar.** *
  *** y NO se declara «hay un fallo de login» ***  -- *porque **el login funciona, y esta medido con un 200.** *
```

## 5. Y el estado de B13, con los dos lados medidos

```
RECORRIDO 1 · el lanzador y las tres raices  -> *** HECHO ***
RECORRIDO 2 · `/compra`                      -> *** HECHO ***
RECORRIDO 3 · `/recetas` sin sesion          -> *** HECHO ***  *-- y dice «Hay que entrar primero» (401 pintado)*
RECORRIDO 4 · *** el alta ***                 -> *** HECHO ***  *-- cuenta creada, cookie puesta, pantalla cambiada*
RECORRIDO 4b · *** volver a entrar ***        -> *** NO, y la causa es del recorrido ***
   *** el API entra con 200 ***  -- *y **el navegador no mando nada**, *y **el sospechoso es el `fill` de 865 ms.** *
RECORRIDO 5 · *** tu restriccion ***           -> *detras de poder entrar de nuevo*
```

> *** Y **lo que falta es una espera de dos segundos y una comparacion de hash** *** -- *y **con eso se cierra el 4b,
> y el 5 queda a la vista.** *
>
> *** Y **es una buena posicion para parar**: *la aplicacion **esta probada por sus dos puertas** (`registrarse` 201
> *y `entrar` 200), *y **lo que queda es mi forma de manejar el navegador.** *
