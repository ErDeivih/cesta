# B13 · **Recorrido 3 HECHO**: `/recetas`, y la pantalla dice **«Hay que entrar primero»** -- que es lo correcto

*(13 de octubre de 2026. **Y es el recorrido que cambia los dos que quedan.**)*

## 1. Lo que se observo, y esta limpio

```
cleanup: *** «terminated-owned-process» ***  ·  completeness: *** «complete» ***  ·  3,6 s  ·  0 eventos

URL  http://127.0.0.1:8080/recetas

*** MENU DE LA SUITE *** (el mismo, y las tres aplicaciones):
  «Cesta» -> /  ·  Aplicaciones: /compra · /recetas · /calorias
  *** navigation «Secciones de Recetas » ***:  *** «Mi recetario» -> `/recetas` ***  ·  *** «Plan semanal» -> `/recetas/plan` ***
  «Cuenta y ayuda»: /ajustes · /aprender

*** banner: *** «Recetas»  ·  *** heading «Mi recetario» [level=1] ***
*** main: ***
  button «*** Ver tambien las archivadas ***»
  button «*** Anadir una receta ***»
  *** paragraph: «HAY QUE ENTRAR PRIMERO.» ***
```

## 2. Y **«Hay que entrar primero» es la respuesta correcta**, y no una pantalla vacia

> *** Y aqui esta **la diferencia que el encargo pide distinguir**: ***
>
> > *** «no consideres terminado lo que solo abrio UNA PANTALLA VACIA» ***
>
> *** Y esta **no es una pantalla vacia**: *** *es **una pantalla que dice QUE FALTA** -- *y **dice cual es el
> paso**: *entrar. *
>
> *** O sea: **es la doctrina otra vez, y en su forma mas util**: *** *** no se finge que **no hay recetas**; *se
> dice que **falta entrar.** *
>
> *** Y **hay DOS botones que si estan** («Ver tambien las archivadas», «Anadir una receta») *-- *o sea: **la pantalla
> tiene su contenido**, *y **lo que falta es el dato del usuario**, no la interfaz. *

## 3. Y **por que falta**: el navegador es nuevo, y su almacenamiento esta VACIO por diseno

```
parameters.storage:  *** cookies: [] · local_storage: [] · session_storage: [] ***
browser:             *** «launch» · «provider-owned» · perfil TEMPORAL propio ***
```

> *** O sea: **el recorrido 3 corre con un navegador que no tiene ninguna sesion** *** -- *y **por eso las recetas no
> salen.** *Y **`/api/yo`** (que respondio **200** en el recorrido 1) *devuelve **«no hay nadie»**, y **la pantalla lo
> dice.** *
>
> *** Y **no es un fallo del recorrido: es la condicion del recorrido.** *Es **un navegador limpio, como el de
> alguien que llega por primera vez.** *

## 4. Y entonces **los recorridos 3, 4 y 5 necesitan una SESION**, y eso hay que decirlo

```
RECORRIDO 1 · el lanzador             -> *** HECHO ***  *-- y **no necesita sesion** (el lanzador es publico)*
RECORRIDO 2 · /compra                  -> *** HECHO ***  *-- y **tampoco**: el buscador se dibuja sin sesion*
RECORRIDO 3 · /recetas                 -> *** HECHO ***  *-- y **dice «hay que entrar primero»**: **su contenido
                                            SI necesita sesion***
RECORRIDO 4 · /calorias                -> *por hacer*  *-- y **el diario es de una persona**: **necesitara sesion***
RECORRIDO 5 · *** la restriccion ***    -> *por hacer*  *-- **y tambien**: *traspasar una receta **es de alguien***

*** Y LA PREGUNTA, CONCRETA: *** *** ¿como entra un recorrido automatico? *** *
```

> *** Y **hay dos caminos, y ninguno se elige a ciegas**: ***
> 1. *** los usuarios de prueba que ya existen *** (38 en la base de casa, con prefijos `a09`, `c01b`, `f07`,
>    `prueba`, `prueba-invitada`) -- *y **el propietario ya decidio**, en B13: *** «crear usuarios de prueba
>    nuevos» ***; *
> 2. *** y la clave *** -- *y **`almacen.crea_usuario` la guarda con `_hasher.hash(clave)`**: *o sea: **con hash**, y
>    **por tanto no se puede leer del fichero.** *
>
> *** O sea: **la sesion no se puede fabricar leyendo la base** *** -- *hay que **entrar por la puerta**, con una
> clave **que alguien conozca.** *
>
> *** Y **la comprobacion es una sola**: *** *mirar **como entran los ensayos** -- *que son **los que ya lo hacen
> automaticamente**, *y **por tanto los que tienen la respuesta.** *
> ```
> git grep -ln "entrar\|login\|sesion" -- "tests/"   -> *y **leer el ayudante que usen.***
> ```

## 5. Y los cinco recorridos, con su estado y su condicion

```
RECORRIDO 1 · el lanzador y las tres raices   -> *** HECHO ***  ·  cleanup incompleto (declarado)
RECORRIDO 2 · *** /compra ***                  -> *** HECHO ***  ·  limpio
RECORRIDO 3 · *** /recetas ***                 -> *** HECHO ***  ·  limpio
     *** y dice «Hay que entrar primero» -- que es lo correcto, y NO una pantalla vacia ***
RECORRIDO 4 · /calorias                        -> *por hacer*  ·  *** y necesitara sesion ***
RECORRIDO 5 · *** la restriccion del propietario ***  -> *por hacer*  ·  *** y tambien ***

*** Y los dos que quedan necesitan UNA COSA: *** *** una sesion de ensayo, y el modo de entrar. *** *
```

> *** Y **es un buen sitio para parar**, *porque **lo que falta no es esfuerzo: es un dato** -- *y **el dato esta en
> los ensayos**, que **ya entran solos.** *
