# B14 · **La copia documentada: `robocopy` de `data\raw`** -- y una pregunta que B14 hace y la copia no cubre

*(13 de octubre de 2026. **Segunda ronda de B14. Y el manual de operacion contesta, y deja un cabo.**)*

## 1. Lo que dice el manual, literal (`docs/OPERACION.md:459`)

> *** «Copia de seguridad, cuando haya algo que perder: *** *** EL CRUDO ES LO UNICO IRRECUPERABLE. *** ***
> Un `robocopy` semanal de `data\raw` a un disco externo **cubre el riesgo entero**.» ***

> *** Y es **la doctrina aplicada a las copias**, y con la razon buena: *** *todo lo demas -- bronce, plata, oro, la
> API -- **se puede volver a calcular desde el crudo**; *y **el crudo son las capturas de las cadenas**, que **si se
> pierden, no se recuperan** (nadie guarda las paginas de ayer).*
>
> *** O sea: **no hay que copiar todo, hay que copiar lo que no se puede rehacer** *** -- *que es **la misma clase de
> decision** que **`_trae_dato`** (B08) y **`ABSTIENE`** (B09): **distinguir lo que se sabe de lo que no.** *
>
> *** Y **el destino es un disco externo**, y **no una nube** *** -- *que es **lo que B14 pide por escrito**:
> *«destino externo requiere decision concreta, **no subir datos a una nube elegida por el agente**». *
> *** Y el manual ya lo dice: **disco externo.** ***

## 2. Y entonces B14 hace una pregunta que **la copia documentada no cubre**

```
B14 PIDE:  «Copias de PostgreSQL, *** SQLITE PRIVADOS *** Y METADATOS;
            restauracion de LOS TRES, hashes, retencion y verificacion.»

Y LA COPIA DOCUMENTADA ES:  *** `robocopy` de `data\raw` *** -- *o sea: **el CRUDO de las cadenas.** *
```

> *** Y hay **dos cosas que NO son crudo y que tampoco se pueden rehacer**: ***
>
> ```
> *** `data/diario.sqlite`  *** -- 11 entradas · *lo que una persona comio. NO es derivable: **nadie lo puede
>                              recalcular** (solo la persona sabe lo que comio).*
> *** `data/recetas.sqlite` *** -- 42 recetas · 42 del plan · 43 versiones · 7 traspasos · *escritas a mano o
>                              importadas. TAMPOCO son derivables.*
> ```
>
> *** O sea: **el manual dice «el crudo es lo unico irrecuperable», y **el diario y las recetas tambien lo son** ***
> -- *y **no estan en `data\raw`**, *asi que **la copia documentada no los incluye.** *
>
> *** Y **es exactamente lo que B14 nombra**: *** *** «copias de PostgreSQL, **SQLite privados** y metadatos» *** --
> *y **los «SQLite privados» son, medidos, `diario.sqlite` y `recetas.sqlite`.** *

## 3. Y **no se dice que no haya copia de esos dos** -- se dice **que la documentada no los cubre**

> *** Lo que se puede decir: ***
>
>   1. **hay una copia documentada**, *y **es concreta**: `robocopy` semanal de `data\raw` a disco externo;*
>   2. ***y su criterio esta escrito***: *«el crudo es lo unico irrecuperable»;*
>   3. ***y `data/diario.sqlite` y `data/recetas.sqlite` son irreemplazables y NO son crudo*** -- *o sea: **el
>      criterio, aplicado con rigor, los incluiria.** *
>
> *** Lo que **no** se puede decir: *** *que **no se copien**. *Puede haber **una copia manual**, o **el disco
> externo puede llevarse `data/` entero** -- *y **el manual habla de `data\raw`, que es una parte.** *
>
> *** Y **la comprobacion que lo decide** ***: *mirar **si hay un disco externo y que se copia a el** -- *que **no se
> puede saber desde el repositorio**, y **es una pregunta para el dueño** (o para la tarea programada de Windows).*

## 4. Y hay **una segunda cosa de B14 que si se puede comprobar aqui**: el log que crece

```
B14 PIDE:  «LOGS CRECIENTES CON ROTACION, METRICAS Y SECRETOS AUSENTES»

Y LO QUE HAY:  `data/runs.csv` -- *** 228 lineas ***, con columnas `ts,fuente,filas,errores,segundos,ok`
               y **se le anaden filas en cada pasada de cada cadena** (B02: *Lidl empezo a registrar*).
```

> *** O sea: **hay un log que crece** *** -- *y **`runs.csv` es, de hecho, la metrica del proyecto**: *`filas`,
> `errores`, `segundos` y `ok` **por fuente y por pasada.** *
>
> *** Y **la rotacion** ***: *`data/runs.csv` **tiene 228 lineas y 6 columnas** -- *o sea: **todavia es pequeno**
> (unas decenas de KB), *y **no se ha visto ningun mecanismo de rotacion.** *
>
> *** Y **«secretos ausentes»** ***: *`runs.csv` guarda **fuente, filas, errores, segundos y ok** -- *o sea:
> **numeros y un nombre de cadena.** *** No hay sitio para un secreto.** *
>
> *** Y **eso es comprobable leyendo la cabecera**, y **ya se leyo** (B02). ***

## 5. Y B14 queda con **dos de cinco bloques empezados, y los dos con medicion**

```
1) CSRF CON SESION REAL        *POR MIRAR* -- y **los ensayos ya existen**: `test_fase2_f07_dos_sesiones.py`,
                               `test_publicacion.py` (B10 lo encontro buscando la concurrencia)
2) AUDITAR LOS GET             *POR MIRAR*
3) LAS COPIAS Y LA VUELTA      *** MEDIDO: *** *`robocopy` semanal de `data\raw` a disco externo* --
                               *** y el criterio: «el crudo es lo unico irrecuperable» ***
                               *** y una pregunta abierta: `diario.sqlite` y `recetas.sqlite` TAMBIEN son
                               irreemplazables, y NO son crudo ***
4) LOGS Y METRICAS             *** MEDIDO EN PARTE: *** *`data/runs.csv` es el log, con 6 columnas y 228 filas;
                               **no hay sitio para un secreto**; y la rotacion **no se ha visto***
5) Y LA REGLA                  «no declarar defensa completa por 401 sin cookie»
```

> *** Y **los dos medidos son los dos que B14 describe con mas detalle**, *y **los dos salen con la misma forma**:
> *** *** **hay algo, esta escrito, y le falta una pieza por comprobar.** *
