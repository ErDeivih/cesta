# B13 · **El recorrido 4, segundo intento: la llamada expiro** -- y deja ocho navegadores

*(13 de octubre de 2026. **Y el fallo es de otra clase: no del recorrido, sino de su tamano.**)*

## 1. Lo que paso

```
LA LLAMADA:  `capture_browser_scenario` con *** DOCE acciones *** (y tres esperas de 1,2 s · 2,5 s · 15 s)
RESULTADO:   *** «Error: Request timed out» ***  -- *y **sin observacion**: no hay `evidence_id`, ni parcial.*

Y DESPUES, medido:
  *** la cuenta NO se creo ***  -> `select usuario from usuario where usuario like 'b13-%'` da *** 0 filas ***
  *** y los navegadores: 16 -> 24 ***  -> *** 8 procesos NUEVOS, del intento que expiro ***
```

> *** O sea: **el segundo intento no llego a nada** *** -- *y **lo que dejo fue **ocho navegadores colgados**, *que es
> **lo contrario de lo que se buscaba.** *
>
> *** Y **la causa es clara, y es de tamano**: *** *** **doce acciones, tres esperas y dos `fill` de mas** *** *--
> *y **el proveedor tiene un tope de tiempo**, *y **al llegar, corta.** *
>
> *** Y **es la tercera vez que el tamano de la observacion muerde, y las tres distinto**: ***
> ```
> RONDA 218: *** pedi 18 eventos de red ***  -> *la **limpieza** quedo incompleta* (1000 ms)
> RONDA 225: *** no pedi consola ***          -> *y **el fallo no se pudo explicar** por esa via*
> RONDA 228: *** pedi 12 acciones ***         -> *** y la llamada entera expiro ***
> ```
>
> *** Y **las tres veces la leccion es la misma, y ya esta escrita dos veces en esta sesion**: *** *** **pide lo
> justo, y en tandas cortas.** *

## 2. Y lo que **hay que hacer distinto**, que es concreto

```
*** EL RECORRIDO, EN DOS LLAMADAS, Y CADA UNA CORTA: ***

  LLAMADA A · *** el alta ***  (y cinco acciones, no doce):
    1. `goto`  `/compra/listas`
    2. `fill`  rol textbox «Usuario»
    3. `fill`  rol textbox «Clave»
    4. `click` rol button «Créala»          *-- cambia al formulario de alta*
    5. *** `capture.at_end: [url, accessibility]` ***   *-- y **aqui se VE el formulario de alta**,
       *con **sus campos y su boton**, *y **sin adivinar nada** *

  *** Y CON ESO SE SABE: *** *si el alta **conserva** «Usuario» y «Clave», *y **como se llama su boton.** *

  LLAMADA B · *** el resto ***  -- *ya con los nombres medidos, y **en cinco acciones**: *
    fill «Tu nombre» · fill «Usuario» · fill «Clave» · click <el boton> · goto `/calorias`
    *** -- y la prueba (`wait_for` el textbox «Usuario» hidden) se deja para una TERCERA, **si hace falta.** *
```

> *** Y **la clave del reparto**: *** *** la **llamada A** no pretende entrar: *pretende **ver el formulario de
> alta**, *que es **el dato que falta.** *
>
> *** Y **es lo mismo que se hizo bien en las rondas 220-224**: *** *una captura por pregunta, y **cada una con su
> respuesta.** *

## 3. Y **los ocho navegadores: ahora SI se pueden distinguir**, y se dice como

```
ANTES (ronda 218): *** no se podian distinguir ***  -- *los 16 estaban repartidos (21:05, 22:34, 22:42)*
AHORA:             *** SI *** -- *porque **se sabe que eran 16**, *y **los 8 nuevos empezaron despues.** *
```

> *** Y **aun asi NO se matan**, y el motivo sigue siendo el mismo: ***
> ```
> *** los 16 primeros siguen sin identificar *** -- *y **puede haber uno del propietario entre ellos** *
> *** -> y matar «los de mas de X minutos» **cerraria su navegador** si el suyo es viejo ***
> ```
>
> *** Y **la comprobacion, que la decide el**: ***
> ```powershell
> Get-Process chrome | Sort-Object StartTime | Select-Object Id, StartTime, MainWindowTitle
> ```
> *** -- *los de **ventana vacia y hora reciente** son **del recorrido**; *y los demas, **no lo son por eso solo.** *
>
> *** Y **queda dicho como lo que es**: *** *** **ocho procesos que deje yo**, *y **no los limpio porque no puedo
> distinguirlos con seguridad.** *Y **es un coste real de haber pedido una observacion demasiado grande.** *

## 4. Y el estado del recorrido 4, sin adornos

```
RECORRIDO 4 · `/calorias`  -> *** DOS INTENTOS ***
   *** 1o (ronda 225): fallo, y EXPLICADO -- faltaba el campo «Tu nombre» ***
   *** 2o (ronda 228): no llego a correr -- la llamada expiro por tamano ***
   *** y la cuenta NO existe todavia (0 filas con `b13-`) ***
*** Y LO QUE FALTA NO ES CONOCIMIENTO: *** *es **partir el recorrido en dos llamadas cortas.** *
   *-- y **el dato que se busca (el formulario de alta) sale en la primera, con CINCO acciones.** *
```
