# B13 · **Las dos recetas estan**: `300 g tomate` y `100 g tomate`, y la segunda **no se descarto**

*(13 de octubre de 2026. **Y el escenario de la restriccion ya esta montado.**)*

## 1. La segunda receta, y su resultado

```
`capture_browser_scenario` · *** 11 acciones · 6,1 s *** · cleanup: terminated-owned-process · complete

  `goto` · esperar 1,8 s · `fill` «Usuario» *46 ms* · `fill` «Clave» *25 ms* · `click` «Entrar» *64 ms*
  `click` link «Recetas» *69 ms* · `click` «Anadir una receta» *136 ms*
  `fill` *** «Nombre» *** = «Sopa de ensayo B13» *16 ms*
  `fill` *** «Ingredientes, uno por linea» *** = *** «100 g tomate» *** *11 ms*
  `click` «Guardar» *154 ms* · esperar 2,5 s  --  y capturar

*** Y LA LISTA, CON LAS DOS: ***
  searchbox «Buscar recetas por nombre»
  button «Ver tambien las archivadas» · button «Anadir una receta»
  *** list: ***
    listitem: *** «Ensalada de ensayo B13» ***  ·  *** «2 raciones · version 1» ***  ·  button «Archivar»
    listitem: *** «Sopa de ensayo B13» ***      ·  *** «2 raciones · version 1» ***  ·  button «Archivar»
```

> *** O sea: *** *** **la segunda receta se creo, y se ve** *** -- *y **no se descarto como repetida.** *
>
> *** Y **es un dato, pero **hay que decir cual es y cual no**: ***
> ```
> *** LO QUE ESTA PROBADO: *** *dos recetas **con el mismo ingrediente en gramos** (`tomate`) **conviven** *
>    *-- o sea: **la biblioteca de recetas NO las funde ni descarta.** *
> *** LO QUE NO ESTA PROBADO TODAVIA: *** *** EL PUENTE *** *-- *o sea: *al **traspasarlas a la lista**, *
>    *** es donde el propietario vio «300 g como una unidad y una nota de 100 g» *** *
> ```
>
> *** Y **es la distincion que importa**: *** *el fallo que el propietario describio **no es al crear la receta**:
> *es **al pasar a la lista**, *que es **donde hay consolidacion por identidad y unidad.** *

## 2. Y el escenario de la restriccion **ya esta montado**, y con sus numeros

```
RECETA 1 · *** «Ensalada de ensayo B13» ***  ·  *** 2 raciones ***  ·  version 1  ·  ingrediente: *** «300 g tomate» ***
RECETA 2 · *** «Sopa de ensayo B13» ***      ·  *** 2 raciones ***  ·  version 1  ·  ingrediente: *** «100 g tomate» ***
PROPIETARIO: *** `b13-recorrido-2301` ***  *-- una cuenta de ensayo, y **nada del propietario se toco** *
```

> *** Y **son exactamente los dos numeros del propietario**: *** *** «300 g necesarios» *** y *** «una nota de 100 g» ***. *
>
> *** Y **el producto es el mismo en las dos** (`tomate`) *** -- *que es **lo que hace que la consolidacion tenga
> algo que consolidar.** *
>
> *** Y **las dos tienen `2 raciones`** *** -- *asi que **el escalado por comensales tambien tiene su caso**:
> *si se piden **4 comensales**, *las dos deberian **doblar**; *y **el fallo seria que una doblara y la otra no.** *

## 3. Y **lo que falta es UNA accion**: el puente

```
*** PASO 12 · el puente ***  *-- y hay que encontrar su boton*

  *** Y `recetas.py` tiene las dos rutas, y B13 las leyo: ***
    `l199  @rutas.get("/{receta_id}/a-la-lista")  def previa`    *** <- *** LA VISTA PREVIA, que NO escribe *** ***
    `l235  @rutas.post(...)                       def a_la_lista` *** <- *** Y LA ACCION *** ***
    *y `l247`: «la idempotencia esta **DOS VECES**: `traspaso` impide la segunda operacion, *
              *`almacen.anade_linea` **ya es un upsert**»*
    *y `main.py:1466`: «*** La vista previa ***: que ingredientes del plan entrarian en la lista, **sin tocar la
     lista**» -- *y `main.py:1608`: «*** Y AQUI ESTA LA CONSOLIDACION ***, que es **la misma que la del otro puente**»*
```

> *** O sea: **el boton tiene que estar en la receta**, *y **se llega pulsando su `button «Ensalada de ensayo B13»`**
> (que es **el enlace a la ficha**, *y **la ficha tiene el boton de «a la lista»**). *
>
> *** Y **B13 ya sabe que existe la VISTA PREVIA** *** -- *que es **la que dice «que ingredientes entrarian», sin
> tocar nada.** *Y **es el sitio perfecto para la comprobacion**: *se puede **mirar la previa** *antes de **escribir
> nada.** *
>
> *** Y **eso respeta el encargo** *** -- *«no restaures sobre bases existentes» y **«no dupliques capturas»**:
> *la previa **no escribe.** *

## 4. Y los cinco recorridos, con el 5 **a una accion**

```
RECORRIDO 1  · el lanzador y las tres raices   -> *** HECHO ***
RECORRIDO 2  · `/compra`                        -> *** HECHO ***
RECORRIDO 3  · `/recetas` sin sesion            -> *** HECHO ***
RECORRIDO 4  · *** el alta ***                   -> *** HECHO ***
RECORRIDO 4b · *** entrar ***                    -> *** HECHO ***
RECORRIDO 4c · *** la sesion al navegar ***      -> *** RESUELTO (era el instrumento) ***
RECORRIDO 5  · *** tu restriccion ***             -> *** y ya tiene sus DOS recetas y sus numeros ***
   *** y le falta: *** *** abrir una receta, mirar la VISTA PREVIA «a la lista», y traspasarla. *** *
   *** y despues: mirar las lineas de la lista, y ver si `300 g` y `100 g` se suman o se pisotean. *** *
```

> *** Y **la comprobacion final es la que el propietario pidio** *** -- *«**traspasar una receta desde la web y mirar
> las lineas de esa lista**» -- *y **ahora esta al alcance: las recetas estan, la sesion esta, y el boton esta en
> la ficha.** *
