# B13 · **RESUELTO: era el instrumento.** Con `click`, la sesion sobrevive -- y `/recetas` ya no pide entrar

*(13 de octubre de 2026. **Y el hash lo confirma en los dos sentidos.**)*

## 1. La llamada, y su resultado

```
7 acciones · 6,3 s · cleanup: terminated-owned-process · completeness: complete

  `goto` `/compra/listas` · esperar 2 s · `fill` «Usuario» *42 ms* · `fill` «Clave» *15 ms*
  `click` «Entrar» *49 ms*  ·  *** `click` rol link, nombre «Recetas» ***  *67 ms*
  esperar 3 s  --  y capturar

*** URL: `http://127.0.0.1:8080/recetas` ***    *-- o sea: **el enlace navego**, y **sin recargar la pagina***

*** Y EL `main` YA NO DICE «HAY QUE ENTRAR PRIMERO»: ***
  button «Ver tambien las archivadas»  ·  button «Anadir una receta»
  *** paragraph: «Todavia no hay recetas» ***
  *** paragraph: «Anade la primera y aparecera aqui, con sus ingredientes y sus raciones.» ***

sha256 *** 2d263a18573fbfc4ad70aad2ddadb533fbb001087e3cd584247d2183e80ed75d ***  ·  *** 942 bytes ***
```

## 2. Y **los tres hashes** contestan la pregunta entera

```
*** SIN sesion, en `/recetas`: ***      `260662eb…`  ·  *** 854 bytes ***  *-- «Hay que entrar primero»*
*** CON sesion, y con `goto`: ***        `5c2c0dc7…`  ·  1239 bytes  *-- **la pantalla de entrar de `/compra/listas`***
*** CON sesion, y con `click`: ***       *** `2d263a18…`  ·  942 bytes ***  *-- *** y NO dice que hay que entrar *** *
```

> *** O sea: *** *** **tres estados, tres hashes, y ninguno se confunde.** *
>
> *** Y **el tercero es el que importa**: *942 bytes, *y **un `main` con contenido de usuario** -- *«**Todavia no hay
> recetas**»* -- *que **es lo que dice una cuenta nueva, y no una que no ha entrado.** *

## 3. Y por tanto **la causa 2 era la buena**: era el `goto`

```
*** LA CUENTA: ***  *la cookie esta bien* (`httponly` · `lax` · `max_age` · `path="/"`, `main.py:93-94`)
*** EL INSTRUMENTO: ***  *el escenario **declaraba `storage` vacio**, *y **el proveedor lo repone en una
   navegacion completa** (`goto`), *y **no en un `click`** -- *porque **un `click` no navega: enruta.** *
```

> *** Y **el `click` lo demuestra**: *** *`after_url` **cambia a `/recetas`**, *y **la sesion sigue.** *
>
> *** O sea: *** *** **NO HAY FALLO DE LA APLICACION.** *Y **declararlo lo habria sido.** *
>
> *** Y **es el segundo falso positivo evitado en esta sesion** *** -- *el primero fue **un `grep` de mis propias
> palabras** (B02), *y **este un escenario mal declarado.** *Y **las dos veces la salvacion fue la misma: **medir
> antes de concluir.** *

## 4. Y **`/recetas` dice dos cosas que son del encargo**

> *** «Todavia no hay recetas» *** -- *y **no un cero, ni un espacio en blanco** *
>
> *** «Anade la primera y aparecera aqui, *** *** CON SUS INGREDIENTES Y SUS RACIONES. *** ***» *
>
> ```
> *** «CON SUS INGREDIENTES» ***  -> *la receta **tiene ingredientes**, que es lo que **el puente a la lista usa** *
> *** «Y SUS RACIONES» ***        -> *** y las raciones son lo que el encargo pide escalar: ***
>    *«reproduce y corrige los dos puentes... *** ESCALADO POR COMENSALES ***»*
> ```
>
> *** O sea: **la pantalla vacia de `/recetas` dice, en una frase, lo que la receta tiene que tener para que el
> puente funcione** *** -- *y **lo dice antes de que haya ninguna receta.** *

## 5. Y los cinco recorridos, con el 4 **cerrado del todo**

```
RECORRIDO 1  · el lanzador y las tres raices   -> *** HECHO ***
RECORRIDO 2  · `/compra`                        -> *** HECHO ***
RECORRIDO 3  · `/recetas` sin sesion            -> *** HECHO ***
RECORRIDO 4  · *** el alta ***                   -> *** HECHO ***
RECORRIDO 4b · *** entrar ***                    -> *** HECHO ***
RECORRIDO 4c · *** la sesion al navegar ***      -> *** RESUELTO: era el instrumento, y con `click` sobrevive ***
RECORRIDO 5  · *** tu restriccion ***             -> *** y ahora es el unico que queda ***
   *** y su primer paso ya esta hecho: se entra, se pulsa «Recetas», y la sesion esta. ***
   *** y le falta lo suyo: *** *** una receta con ingredientes y raciones, y traspasarla a la lista. *** *
```

> *** Y **la cuenta nueva no tiene recetas** *** -- *y **eso no es un problema: es el punto de partida.** *
> *Y **`button «Anadir una receta»` esta en la pantalla**, *que es **por donde se empieza.** *
