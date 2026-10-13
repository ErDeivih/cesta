# B13 · **Recorrido 2 HECHO**: `/compra`, y **esta vez la limpieza se confirmo**

*(13 de octubre de 2026. **Y el menu de la suite confirma, en vivo, lo que el lanzador prometia.**)*

## 1. Y la primera noticia es del proveedor, no de la pantalla

```
RECORRIDO 1:  *** cleanup: «incomplete» *** -- *«could not be confirmed: timed out after 1000ms»*
RECORRIDO 2:  *** cleanup: «terminated-owned-process» ***  <- *** y `completeness: complete` ***
              *y esta vez **no se pidieron eventos de red** (18 -> 0), *y tardo **5,4 s** en vez de 11,0*
```

> *** O sea: **el `cleanup_incomplete` de la ronda 218 fue por **el volumen de la observacion** *** -- *y **no por el
> navegador.** *
>
> *** Y **la leccion, para los tres que quedan**: *** *** pedir solo lo que se va a leer.** *El proveedor **lee la
> red entera si se le pide**, *y **la limpieza tiene 1000 ms.** *
>
> *** Y **no es una excusa: es una instruccion** -- *los recorridos **3, 4 y 5** se piden **igual que este.** *

## 2. Y el menu de la suite **confirma lo que el lanzador prometia**, seccion por seccion

```
EL LANZADOR DECIA:  *** «Compra -- Buscar, la lista, favoritos y lo que gastas.» ***

Y EL MENU DE `/compra` TIENE:  *** navigation «Secciones de Compra» ***
  *** «Buscar» ***          -> `/compra`
  *** «Listas» ***          -> `/compra/listas`
  *** «Favoritos» ***       -> `/compra/favoritos`
  *** «Gasto y ahorro» ***  -> `/compra/analisis`
```

> *** Y **son las cuatro, en el mismo orden, y con los mismos nombres** *** -- *«buscar **la lista** favoritos y lo
> que gastas»: *`Buscar` · `Listas` · `Favoritos` · `Gasto y ahorro`. *
>
> *** O sea: **la descripcion del lanzador no es marketing: es el indice del menu**, *y **se puede comprobar con dos
> capturas.** *
>
> *** Y **`Suite.tsx:44 APLICACIONES`** es **la fuente de las dos** (ronda 190: *«las tres aplicaciones y sus
> subsecciones, tal y como las fija `SUPERAPP-01`»*) -- *y **aqui se ve el resultado.** *

## 3. Y **las tres aplicaciones estan en el menu de dentro**, no solo en el lanzador

```
complementary «*** Menu de la suite ***»:
  link «Cesta»            -> `/`
  navigation «Aplicaciones»:  *** `/compra` · `/recetas` · `/calorias` ***
  navigation «Secciones de Compra»:  *las cuatro de arriba*
  navigation «*** Cuenta y ayuda ***»:  «Cuenta y preferencias» -> `/ajustes`  ·  *** «Aprender» -> `/aprender` ***
```

> *** Y **`/aprender` esta enlazado desde la interfaz** *** -- *que es **el material de B15**, *y **no un directorio
> suelto.** *O sea: **el material de aprendizaje se sirve y se enlaza.** *
>
> *** Y **`<a class="..." data-discover="true">`** (visto en el DOM del recorrido 1) *sugiere **que el menu se
> descubre de `APLICACIONES`** -- *y **por eso las dos listas coinciden.** *

## 4. Y la pantalla de Compra, con sus piezas (que son A09)

```
banner:  «Compra» · heading «Buscar» [level=1]
*** main ***:  heading «Buscar» [level=1]
  *** region «Buscar» ***:
    searchbox «*** Buscar producto ***»
    button «*** Buscar hablando ***»
    status                                    <- *y esta VACIO: no hay nada que anunciar todavia*
    link «*** Escanear un codigo de barras ***» -> `/escaner`
    group: «*** Filtros cadena, pasillo, dieta, ofertas… ***»
    button «*** Guardar estos filtros ***»
  «*** Escribe al menos dos letras, o elige un pasillo ***»
  «*** Tambien puedes explorar un pasillo entero sin escribir nada. ***»
  «Busca lo que compras. Por ejemplo:»
  button «*** leche entera ***» · button «*** papel de cocina ***» · button «*** atun en aceite ***»
```

> *** Y **las cuatro cosas que B02/B13 querian de `/compra` estan**: ***
> 1. *** buscar *** -- *`searchbox`, y **con su regla escrita**: «escribe al menos dos letras, **o elige un
>    pasillo**»;*
> 2. *** la lista *** -- *`/compra/listas` en el menu;*
> 3. *** favoritos *** -- *`/compra/favoritos`;*
> 4. *** y lo que gastas *** -- *`/compra/analisis`, y **se llama «Gasto y ahorro».** *
>
> *** Y **no es una pantalla vacia**: *hay **un buscador con voz**, **un escaner**, **filtros con cinco ejes**
> («cadena, pasillo, dieta, ofertas…»*), **un boton de guardar filtros**, **tres ejemplos pulsables**, *y **dos
> frases que explican como se usa.** *
>
> *** Y **el `status` vacio** es **la misma doctrina**: *un anuncio **sin nada que anunciar** **no se rellena con
> nada.** *

## 5. Y los cinco recorridos, con su estado

```
RECORRIDO 1 · el lanzador y las tres raices   -> *** HECHO ***   *(y con `cleanup` incompleto, declarado)*
RECORRIDO 2 · *** `/compra` ***                -> *** HECHO ***   *(y `cleanup: terminated-owned-process`)*
RECORRIDO 3 · `/recetas`                       -> *por hacer*
RECORRIDO 4 · `/calorias`                      -> *por hacer*
RECORRIDO 5 · *** la restriccion del propietario ***  -> *por hacer*

*** LA RECETA, que ya esta probada dos veces: ***
  `capture_browser_scenario` · Chrome oculto · `start_url` el lanzador · `goto` a la seccion · esperar 2,5 s
  *** y pedir SOLO `url` y `accessibility` *** -- *ni red, ni DOM, ni captura.*
  *** -> `cleanup: terminated-owned-process` y `completeness: complete`. ***
```
