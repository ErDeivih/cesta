# B13 · **«Entrar» NO funciono**: `/recetas` es **byte por byte** la pantalla sin sesion

*(13 de octubre de 2026. **Y la prueba es un hash, no una impresion.**)*

## 1. Lo que se hizo, y lo que salio

```
LA LLAMADA · 6 acciones · 5,2 s · cleanup: terminated-owned-process · completeness: complete

  1. `goto`  `/compra/listas`
  2. `fill`  *** rol textbox «Usuario» ***  = `b13-recorrido-2301`   *-- tardo **865 ms***
  3. `fill`  *** rol textbox «Clave» ***    = `ensayo-b13-2301`       *-- tardo **160 ms***
  4. `click` *** rol button «Entrar» ***                              *-- tardo **130 ms***
  5. `goto`  `/recetas`
  6. `wait_for_timeout` 3 s  -- *y captura*

*** Y EL RESULTADO: ***  *`/recetas` **dice lo mismo que sin sesion**:*
  link «Ver tambien las archivadas»  ·  link «Anadir una receta»  ·  *** paragraph: «Hay que entrar primero.» ***
```

> *** Y **la prueba no es una impresion: es un hash.** *
>
> ```
> RONDA 220 (SIN sesion):  accesibilidad de `/recetas` -> sha256 *** 260662eb141a12ae... ***
> RONDA 231 (con «Entrar»): accesibilidad de `/recetas` -> sha256 *** 260662eb141a12ae... ***
> *** IDENTICOS. ***  *-- y tambien **los mismos 854 bytes.** *
> ```
>
> *** O sea: **no es que se parezca: es que **es la misma pantalla**, *y **la misma respuesta.** *
>
> *** Y **eso es lo que hace el hash**: *** *no hay **que fiarse de «parece que no entro»**; *las dos capturas
> **coinciden byte a byte**, *y **eso es un hecho, no una lectura.** *

## 2. Y **la cuenta SI existe**, asi que el fallo no es de la cuenta

```
$ docker exec cesta-db-1 psql -U cesta -d cesta -tAc "select usuario, nombre from usuario where usuario like 'b13-%'"
*** b13-recorrido-2301 | Ensayo B13 ***      *-- *verificado en la ronda 230, y **sigue ahi.** *
```

> *** O sea: **el usuario esta, y la clave deberia ser `ensayo-b13-2301`** *** -- *porque **es la que se mando al
> crear la cuenta**, *y **`crea_usuario` guarda `_hasher.hash(clave)`.** *
>
> *** Y **si la cuenta existe y la clave es la que se uso**, *entonces **el fallo esta en el trayecto**: *o **el `fill`
> no llego**, *o **el `click` no disparo**, *o **la respuesta no se aplico.** *

## 3. Y hay **un dato que apunta a `fill`**, y es de tiempo

```
EN EL ALTA (ronda 230, y FUNCIONO):   `fill` «Tu nombre» *** 15 ms *** · `fill` «Usuario» *** 19 ms *** · `fill` «Contraseña» *** 14 ms ***
EN EL ENTRAR (ronda 231, y NO):       `fill` «Usuario» *** 865 ms *** · `fill` «Clave» *** 160 ms ***
```

> *** O sea: **en el alta los `fill` fueron instantaneos** *** -- *porque **el formulario ya estaba montado**
> (se **acababa de pulsar «Créala»**, *y **el `click` espero**). *
>
> *** Y **en el entrar, el primero tardo 865 ms** *** -- *que es **lo que tarda Playwright en encontrar el campo**: *o
> sea: **la pagina todavia se estaba montando.** *
>
> *** Y **si el campo no estaba**, *`fill` **espera**, *y **escribe cuando aparece** -- *y **entonces `Usuario` y
> `Clave` se rellenan, *pero **React puede haber remontado el formulario entre los dos**, *y **el segundo `fill`
> escribe en un campo que ya no es el que el estado lee.** *
>
> *** Y **es lo mismo que paso en la ronda 225** *** -- *«faltaba `nombre`» y **la guarda no mando nada** -- *o sea:
> **la misma clase de fallo: el formulario no manda si cree que falta algo.** *
>
> *** Y **NO SE ELIGE**: se dice **que el `fill` de 865 ms es el sospechoso**, *y **que hay una prueba que lo
> decide.** *

## 4. Y **la prueba que lo decide**, concreta

```
*** LA MISMA LLAMADA, CON UN `wait_for_timeout` ANTES DE RELLENAR: ***
  1. `goto`  `/compra/listas`
  2. *** `wait_for_timeout` 1500  ***   <- *** y esto es lo unico que cambia ***
  3. `fill` «Usuario»   · 4. `fill` «Clave»   · 5. `click` «Entrar»
  6. `goto` `/recetas`  · 7. `wait_for_timeout` 3000
  *** -> y si AHORA entra, entonces era el montaje; y si NO entra, es la clave o la respuesta.** *
```

> *** Y **hay una segunda prueba, mas rapida y sin navegador**: *** *** `POST /api/entrar` a mano, por stdin, con
> las mismas credenciales** *-- *y **su codigo dice si la clave vale.** *
> ```bash
> curl -s -o /tmp/e.txt -w "HTTP %{http_code}\n" -X POST http://cesta-api-1:8000/api/entrar \
>   -H "content-type: application/json" -d '{"usuario":"b13-recorrido-2301","clave":"ensayo-b13-2301"}'
> ```
> *** *** y esa separa las dos mitades: *** *si **el API entra**, *el fallo es **del navegador**; *y si **no**,
> *es **de la clave.** *

## 5. Y el estado, sin adornos

```
RECORRIDO 4 · *** el alta ***            -> *** HECHO ***  *-- la cuenta se creo y la pantalla lo demostro*
RECORRIDO 4b · *** volver a entrar ***    -> *** NO FUNCIONO ***  *-- y `/recetas` es byte-identico a sin sesion*
   *** y la causa esta entre tres, y las tres se separan con dos pruebas dichas. ***
RECORRIDO 5 · *** tu restriccion ***      -> *detras de poder entrar de nuevo*
```

> *** Y **una nota que importa para el propietario**: *** *** el alta **funciona** (probado y verificado en la base),
> *y **volver a entrar es lo que no.** *-- *y **si eso se confirma**, *es **un fallo de verdad**: *una cuenta que se
> crea y **no se puede volver a usar** *no sirve de nada.* *
>
> *** Y **NO se declara**: *se declara **medido con un hash**, *y **con las dos pruebas que lo deciden escritas.** *
