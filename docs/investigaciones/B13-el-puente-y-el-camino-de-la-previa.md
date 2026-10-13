# B13 · **El puente tiene DOS funciones en el frontend, y una frase que es la idempotencia**

*(13 de octubre de 2026. **Y sale un camino mejor que el navegador para la prueba final.**)*

## 1. Lo que hay en `api/recetas.ts`

```
l177:  `/api/recetas/${recetaId}/*** a-la-lista ***`  ...      *-- *** la VISTA PREVIA *** (GET)*
l184:  *** «**Pasa la receta a la lista.** *Repetir no [duplica]...» ***
l193:  conCuerpo(`/recetas/${recetaId}/*** a-la-lista ***`, ...)   *-- *** y la ACCION *** (POST)*
```

> *** O sea: **el frontend tiene las dos llamadas**, *y **la segunda lleva su frase**: *** *** «**Pasa la receta a la
> lista**. *** *** Repetir no duplica. ***» *
>
> *** Y **esa frase es la idempotencia, escrita en el sitio donde se usa** *** -- *y **coincide con `recetas.py:247`**
> (B13): *«la idempotencia esta **DOS VECES**: `traspaso` impide la segunda operacion, *y `almacen.anade_linea`
> **ya es un upsert**». *
>
> *** O sea: **lo dice la API, lo dice el frontend, y lo dice el esquema** *** -- *y **las tres veces con las mismas
> palabras: repetir no duplica.** *

## 2. *** Y sale un camino MEJOR que el navegador para la prueba final ***

```
*** LO QUE SE PERSIGUE: *** *ver **que pasa al pasar `300 g` y `100 g` a la lista.** *

*** EL CAMINO DEL NAVEGADOR: *** *12 acciones, *y **hay que encontrar el boton** *-- *y **la captura de la ficha
   NO lo enseño.** *

*** EL CAMINO DE LA API, que es el que conviene ahora: ***
   1. `POST /api/entrar` con `b13-recorrido-2301` *** -> y la respuesta trae `Set-Cookie` ***
   2. y con esa cookie, *** `GET /api/recetas/{id}/a-la-lista` *** -> *** LA VISTA PREVIA, que NO ESCRIBE ***
      *** -> y la previa dice «que ingredientes entrarian», *y **con que cantidad y que unidad.** *
```

> *** Y **este camino es mejor por tres razones, y las tres son del encargo**: ***
> ```
> *** 1) NO ESCRIBE ***  -> *la previa **no toca la lista** (`main.py:1466`), *y el encargo dice
>    «no restaures sobre bases existentes» y «no dupliques capturas»*
> *** 2) ES TEXTO ***    -> *la respuesta **es JSON**, *y se puede **leer linea por linea** -- *y la pregunta
>    («300 g como unidad o como gramos») **se contesta leyendo un campo**, *no **interpretando una pantalla.** *
> *** 3) ES CORTO ***     -> *dos comandos, *y **sin navegador**, *y **sin los `cleanup_incomplete`** que ya han
>    aparecido cuatro veces. *
> ```

## 3. Y **la previa es la que dice si el fallo existe**, sin escribir nada

> *** Y **la pregunta es exacta**: *** *** si la previa de una receta con `300 g tomate` dice
> ***`cantidad: 300, unidad: "g"`***, *entonces **esta bien**; *y si dice ***`cantidad: 1, unidad: "ud"`***,
> *entonces **es el fallo del propietario, medido.** *
>
> *** Y **con las dos recetas**, *la pregunta es **la segunda mitad**: *si se traspasan **las dos**, *¿la linea
> queda con **`400 g`** (sumadas), *o con **`300 g` y una nota de `100 g`** (que es **el fallo**)? *
>
> *** Y **eso es exactamente lo que el propietario describio** *** -- *y **ahora se puede medir sin escribir.** *

## 4. Y el estado, con un cambio de instrumento justificado

```
RECORRIDO 5 · *** tu restriccion ***
  *** la 1a mitad esta MEDIDA: *** *la receta guarda `300 g tomate`, *y no «1 ud»*
  *** y la 2a («y una nota de 100 g») es del PUENTE ***
  *** -> y el puente se puede mirar por la API, con la VISTA PREVIA, que NO ESCRIBE ***
     *y el camino es: `POST /api/entrar` (cookie) + `GET /api/recetas/{id}/a-la-lista`*
```

> *** Y **el cambio de instrumento no es un atajo: es una eleccion mejor** *** -- *porque **la pregunta es sobre
> datos**, *y **la API los da en texto.** *
>
> *** Y **el navegador sigue siendo necesario para los cinco recorridos** *** -- *que ya estan hechos *-- *y
> **para lo que es de interfaz**: *«no consideres terminado lo que solo abrio una pantalla vacia». *Y **aqui la
> pantalla **ya se abrio, y se leyo**: *hay **recetas, fichas, version, raciones e ingredientes.** *
