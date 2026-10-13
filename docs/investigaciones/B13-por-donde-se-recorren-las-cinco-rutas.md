# B13 · **Por donde se recorren las cinco rutas**: `127.0.0.1:8080`, y **la API no esta publicada**

*(13 de octubre de 2026. **Sexta ronda de B13. Y el paso 4 ya tiene direccion.**)*

## 1. Lo que hay, medido

```
$ docker ps --format "{{.Names}}|{{.Ports}}"

  cesta-api-1      | 8000/tcp                       <- *** NO PUBLICADO: solo en la RED INTERNA de Docker ***
  cesta-db-1       | 127.0.0.1:5432->5432/tcp        <- la base de casa, SOLO LOOPBACK
  *** cesta-web-1  | 127.0.0.1:8080->8080/tcp ***     <- *** LA WEB: POR AQUI VAN LOS CINCO RECORRIDOS ***
  cesta-prueba-db  | 127.0.0.1:5434->5432/tcp        <- la de pruebas, loopback
  facylf-postgres  | (ajeno)

$ docker inspect cesta-api-1 --format '{{json .Config.Healthcheck}}'
  "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8000/api/salud').read()\""
```

## 2. Y contesta el paso 4, y confirma una restriccion del encargo

```
PASO 4 (los cinco recorridos):  *** http://127.0.0.1:8080 ***  -- la WEB
  y la API se alcanza **desde dentro** (`cesta-api-1:8000`, red de Docker), NO desde el host.
  y `/api/salud` es la ruta de salud.
```

> *** Y las dos cosas juntas son **la forma correcta**, y confirman el encargo: ***
>
>   - *** «**No despliegues publicamente ni abras puertos**» *** *-> y **lo unico publicado son CUATRO puertos de
>     LOOPBACK** (`127.0.0.1:5432`, `:5434`, `:8080` y nada mas);*
>   - *** y **la API no esta publicada en absoluto** *** -> *solo **la web**, que es **la que una persona usa.** *
>
> *** O sea: **la superficie expuesta es un puerto de loopback con la interfaz web**, *y **la API y las dos bases
> quedan dentro.** *
>
> *** Y es **el mismo criterio que `Ajustes.tsx` escribe al usuario** (B08): *** *** «los datos viven en el ordenador
> de casa y no salen de ahi» *** -- *y **la topologia de puertos lo cumple.** *

## 3. Y los cinco recorridos, con su punto de entrada

```
  1) receta -> lista       *** `http://127.0.0.1:8080` -> /recetas -> (receta) -> a la lista ***
  2) plan -> lista         *** -> /recetas -> /plan -> traer del plan ***
  3) receta -> consumo     *** -> /recetas -> /calorias -> (anotar) ***
  4) compra                *** -> /compra -> (lista) -> cerrar compra ***
  5) diario                *** -> /calorias -> (dia) ***
     *** y las tres raices son las de `Suite.tsx`: `/compra` · `/recetas` · `/calorias` ***
```

> *** Y **las tres raices del recorrido son las tres de `APLICACIONES`** *** -- *o sea: **el inventario de B13 (las
> rutas) y el inventario de `Suite.tsx` (las aplicaciones) **coinciden**, y **por eso el aviso de `Nav` importaba**:
> *si el recorrido se hubiera hecho sobre `Nav`, **no habria pasado por las tres raices de verdad.** *
>
> *** Que es **la primera clausula de B13 haciendo su trabajo tres rondas despues**: *** *«inventariar rutas y
> componentes montados» -- *y **el inventario sirve para saber donde se recorre.** *

## 4. Y el estado de B13, con el paso 4 listo

```
  1) RUTAS Y COMPONENTES      *** HECHO *** -- `Suite` se sirve · `/compra`·`/recetas`·`/calorias`
  PASO 1 (ver usuarios)       *** HECHO *** -- 38 usuarios; y el aviso de «Madre»
  PASO 2 (leer `crea_usuario`) *** HECHO Y CONCLUYENTE *** -- un solo `INSERT` en `usuario`
  PASO 3 (elegir usuarios)    *** RESUELTO *** -- `prueba` / `prueba-invitada`
  *** PASO 4 (POR DONDE)       HECHO: `http://127.0.0.1:8080`, y la API NO se publica ***
  PASO 5 (capturas + manifiesto)  *y con las dos guardas: sin el nombre «Madre», y sin nutricion personal*
```

> *** Y **lo que queda del paso 4 no es una medicion: es abrir la web y recorrer.** ***
>
> *** Que es **el limite que esta sesion declaro en B13 y mantiene**: *** *todo lo que se puede **averiguar** antes de
> recorrer, **ya esta** -- *la direccion, las tres raices, los dos usuarios, la guarda del nombre, y **la
> comprobacion de que crear usuarios no hace daño.** *
>
> *** Lo que falta **no se lee: se hace.** ***
