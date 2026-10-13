# B14 · **La recomendacion de las copias**, con su diff -- y **por que NO se aplica sola**

*(13 de octubre de 2026. **Y es el ultimo cabo, y es una decision que el propietario delego: «lo que mejor consideres».**)*

## 1. El problema, medido en tres piezas

```
*** 1) `OPERACION.md:459` ***  *«Copia de seguridad, cuando haya algo que perder: *** EL CRUDO ES LO UNICO
   IRRECUPERABLE. *** *Un `robocopy` semanal de `data\raw` a un disco externo **cubre el riesgo entero**.» *
   *** -> y el criterio es BUENO: *lo derivado (bronce, plata, oro) **se recalcula**; *lo observado **no.** *

*** 2) Y **le faltan DOS datos que tampoco se recalculan**, y **no son crudo**: ***
   `data/recetas.sqlite` (42 recetas, 42 del plan, 43 versiones, 7 traspasos) -- *escrito a mano o importado*
   `data/diario.sqlite` (11 entradas) -- *lo que una persona comio, y **solo ella lo sabe***

*** 3) *** Y ADEMAS: `/app/data` NO TIENE MONTAJE NI VOLUMEN NOMBRADO *** *** (`docker-compose.yml`)
   -> *o sea: **el `recetas.sqlite` que la API ESCRIBE vive en la capa del contenedor**, *
      *y **no esta en el host en absoluto.** *
```

> *** O sea: *** *** **hay TRES sitios donde vive algo irreemplazable**, *y **la copia documentada cubre uno**
> *(el crudo). *
> ```
> *** `data/raw` ***            -> *y **SI se copia** (el `robocopy` documentado)*
> *** `data/*.sqlite` privados *** -> *** y NO se copian ***  *(estan en `data/`, y el `robocopy` es de `data\raw`)*
> *** `/app/data` del contenedor *** -> *** y NO ESTA EN EL HOST: no se puede copiar porque no se ve *** *
> ```

## 2. Y la recomendacion, que son **dos cosas y no una**

```
*** A) QUE LA COPIA LLEVE LOS TRES: ***
   robocopy "F:\aprendizaje\scrap\data\raw"  "E:\cesta\raw"      /MIR /R:2 /W:5
   robocopy "F:\aprendizaje\scrap\data"      "E:\cesta\privado"  diario.sqlite recetas.sqlite /R:2 /W:5
   *** -> y el criterio del manual, aplicado con rigor, YA LOS INCLUIA: *solo que su frase solo nombra el crudo.* *

*** B) Y QUE `/app/data` DEJE DE SER INVISIBLE: ***  *** <- y esto es un cambio de `docker-compose.yml` *** *
```

> *** Y **la (B) es la que importa**, *y la que **descubri en esta sesion**: *si **alguien usa la web**,
> *sus recetas **van a `/app/data`**, *y **no al `data/` que se copia.** *
>
> *** Y **el diff es pequeño**, *y **esta en el bloque de `cesta-api`**: *
> ```yaml
>   cesta-api:
>     volumes:
>       - ${CESTA_DATOS:-../data}:/datos:ro          # el crudo y el oro, en solo lectura
> +     - datos_api:/app/data                         # y el estado propio, en un volumen NOMBRADO
> ...
> volumes:
>   datos_db:
>   datos_caddy:
> + datos_api:
> ```
>
> *** Y **se elige un volumen NOMBRADO y no un `bind`**, *y por un motivo: *el `data/` del host esta montado
> **`ro`** a proposito, *y **un `bind` de escritura a `data/`** *tendria **dos escritores** (el host y el
> contenedor) *sobre **el mismo fichero** -- *y eso **es la clase de cosa que el `ro` esta evitando.** *
>
> *** Y **alternativa, si se prefiere verlo en el host**: *** *un `bind` a **otra carpeta**, *por ejemplo
> `${CESTA_DATOS:-../data}/privado:/app/data` -- *y **entonces si se copia con el `robocopy` de la (A)**, *
> *sin **dos escritores** sobre el mismo fichero.* *

## 3. *** Y POR QUE NO SE APLICA SOLA *** -- y es la parte del encargo

```
*** APLICARLA SIGNIFICA `docker compose up -d cesta-api` ***
   -> *y eso *** RECREA EL CONTENEDOR *** -- *y **el `recetas.sqlite` que hoy vive en su capa**,
      *segun como se haga, **puede quedar fuera de alcance.** *
   *** -> o sea: **aplicarlo SIN COPIAR ANTES el `/app/data` actual** *seria **destruir lo que se quiere
   proteger.** *
   *** Y el encargo dice: *** *** «no restaures sobre bases existentes» *** *y **«preserva cambios ajenos»**. *
```

> *** O sea: *** *** **el orden importa, y es este**: ***
> ```
> *** 1) PRIMERO, sacar el `/app/data` actual del contenedor ***  *(docker cp, o el volumen nuevo tras recrear)*
> *** 2) DESPUES, cambiar el compose ***
> *** 3) y DESPUES, `docker compose up -d` ***
> ```
>
> *** Y **el paso 1 no se puede saltar**, *porque **el fichero que hay que salvar esta dentro de lo que se
> recrea.** *
>
> *** Y **por eso NO se aplica**: *** *** no porque **no se deba**, *sino porque **hacerlo mal borra lo que se
> protege** -- *y **el encargo prohibe las acciones destructivas.** *

## 4. Y **lo que SI se puede hacer sin riesgo**, y se dice

```
*** Y es una lectura, y es lo que la (A) necesita saber: ***
  *** CUANTO HAY EN EL `/app/data` DEL CONTENEDOR ***
     *`recetas.sqlite` -> **5 recetas** (las de ensayo) *· y **el `diario.sqlite`**, si existe*
  *** -> y si **solo tiene las de ensayo**, *entonces **aplicar la (B) hoy no pierde nada** *
  *** -> y si **tuviera recetas de verdad**, *entonces **hay que sacarlas primero**, *y **eso decide el orden.** *
```

> *** Y **es la comprobacion que convierte la recomendacion en una decision tomada**: ***
> *si **el contenedor solo tiene ensayo**, *la (B) **se puede aplicar ya**; *y **si tiene algo real**,
> *primero **se saca.** *
>
> *** Y **B13 ya midio una mitad**: *** *el contenedor tiene **5 recetas**, *y **las cinco son de ensayo**
> *(`Ensalada`, `Sopa`, `Guiso`, `Pure`, `Arroz de ensayo B13`). *
> *** -> o sea: **hoy, la (B) no perderia nada.** *Pero **el `diario.sqlite` del contenedor no se ha mirado**, *
> *y **se dice.** *
