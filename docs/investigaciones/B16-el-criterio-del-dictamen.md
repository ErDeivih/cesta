# B16 · **El criterio del dictamen** -- y su titulo es la condicion del propietario

*(13 de octubre de 2026. **El ultimo paquete del plan. Y lo dice todo en el titulo.**)*

## 1. El criterio, literal (`plan:367`)

> **B16 · Aceptacion final, no cierre por cansancio**
>
> *«Puertas Python/client/lint/tsc/build, ensayos HTTP, sandbox PostgreSQL/SQLite, **cinco recetas completas en
> navegador**, publicacion durante el uso, recuperacion de ingesta y restauracion aislada. *** Cero xfail/skips sin
> explicacion especifica. *** *** Dictamen por capacidad: implementado/verificado/limitado, con version y
> evidencia. *** *** Separar usable en casa de desplegable para publico. *** *** Si una fuente es inaccesible,
> explicar alcance y no fingir que ya son seis catalogos completos. ***»*

## 2. Y el titulo **es la condicion del propietario, dentro del plan**

```
EL PROPIETARIO DIJO:  «no cierres por alcanzar un numero de rondas o pruebas»
B16 SE TITULA:        *** «ACEPTACION FINAL, NO CIERRE POR CANSANCIO» ***
```

> *** La misma frase, con otra palabra: *** *el propietario dice **«un numero de rondas»**; *el plan dice
> **«cansancio»**. *Y **las dos nombran lo mismo**: *cerrar **porque toca**, y no **porque este**. *
>
> *** Y **el encargo lo repite una tercera vez**: *** *** «no consideres terminado lo que solo abrio una pantalla
> vacia» *** -- *y **B13 lo cuarta**: «no "cerrar A09 entero" con vacios unicamente». *
>
> *** Cuatro veces la misma regla, con cuatro palabras: *** **rondas · cansancio · pantalla vacia · vacios.**

## 3. Y las cinco cosas que pide, contra lo que hay medido

```
B16 PIDE                                          LO MEDIDO EN ESTA SESION
  «Puertas Python/client/lint/tsc/build»           *** ruff limpio · 2025 pytest · 74 npm · tsc 0 · build ***
  «ensayos HTTP»                                    *los hay: `test_g01_diario_http.py`, `test_b03_*`, y la
                                                    aceptacion de B04 (27/27 contra la API real)*
  «sandbox PostgreSQL/SQLite»                       *** los DOS almacenes, medidos: Postgres (14 tablas) y
                                                    SQLite (`recetas` · `diario` · `inventario`) ***
  *** «CINCO RECETAS COMPLETAS EN NAVEGADOR» ***     *** NO HECHO *** -- *es B13, y necesita el navegador*
  «publicacion durante el uso»                      *POR MIRAR -- `test_publicacion.py` existe*
  «recuperacion de ingesta»                          *POR MIRAR*
  «restauracion aislada»                             *** y es la pregunta del disco externo (B14) ***
  *** «CERO xfail/skips sin explicacion» ***         *** 0 pasan · 0 fallan · 0 SE SALTAN · y 0 xfail ***
  *** «Dictamen por capacidad: implementado/verificado/limitado, con version y evidencia» ***  *** NO HECHO ***
  *** «Separar usable en casa de desplegable para publico» ***  *** y esta medido: LO PUBLICADO SON CUATRO
                                                    PUERTOS DE LOOPBACK (`:5432`·`:5434`·`:8080`) ***
  *** «no fingir que ya son seis catalogos completos» ***  *** y B02 lo tiene medido: Lidl es la SEXTA, y su
                                                    alcance esta dicho ***
```

> *** Y de las once cosas, **cinco estan hechas o medidas**, **dos son la misma pregunta** (el navegador y los cinco
> recorridos), *y **el dictamen no esta escrito** -- *que es **lo que B16 pide y nadie ha redactado.** *
>
> *** Y **las tres que B16 subraya mas** son **las tres que se pueden decir hoy**: ***
>   - *** «cero skips» *** -> **0 se saltan, y 0 xfail**;
>   - *** «separar casa de publico» *** -> **loopback solamente, y la API ni se publica**;
>   - *** «no fingir seis catalogos completos» *** -> *y **B02 tiene el alcance de Lidl medido**, y **su cobertura
>     por region** (B03: la `region` en los grupos). *

## 4. Y **por que el dictamen no se ha escrito todavia**: porque le falta **una linea**

> *** Un dictamen por capacidad dice, por cada cosa: *** *** «implementado» / «verificado» / «limitado» *** -- *y
> **pide version y evidencia.** *
>
> *** Y **de las capacidades del encargo, todas tienen evidencia menos una**: *** *** «cinco recetas completas en
> navegador» *** -- *y **esa no es una lectura: es un recorrido.** *
>
> *** O sea: **el dictamen se puede escribir hoy con una casilla en «LIMITADO»** *** -- *y **lo honesto es
> escribirla asi**, *en vez de **poner «verificado» en algo que no se ha recorrido.** *
>
> *** Y **es exactamente lo que B16 pide**: *** *** «implementado/verificado/**limitado**» *** -- *tres palabras
> porque **hay tres estados**, *y **no dos** -- *igual que **`ABSTIENE`** (B09) y **los cinco motivos de B06**: *
> *** no forzar a dos lo que tiene tres. ***
>
> *** Decimosegunda vez. ***

## 5. Y el plan termina, y su ultima seccion ya se leyo

```
`docs/SUPERAPP-PLAN-DEEPSEEK-2026-10-13.md`  --  *** 466 lineas ***
  y la seccion 8 («Referencias y uso concreto de REA») es la ULTIMA, y se leyo: *las cuatro referencias son
  DOCUMENTACION, y «no se han descargado ni decompilado las apps comerciales».*
  Y su ultima frase: *** «El estado global incluye otros proyectos: este encargo es Cesta; no desviarse a
  cazador, facylf o CueDigital ni cambiar sus objetivos. *** *** Crear un perfil de Cesta si hace falta,
  CONSERVANDO EL TRABAJO AJENO DEL LABORATORIO. ***» *
```

> *** Y esa ultima frase es **la restriccion del propietario, escrita en el plan**: *** *«preserva cambios ajenos»,
> con **los tres proyectos hermanos por su nombre** y **`facylf` entre ellos.** *
>
> *** O sea: **el plan y el encargo dicen lo mismo en los dos extremos** *** -- *el propietario **al pedirlo**, *y el
> plan **al cerrar.** *
