# B14 · **El CSRF, medido**: cinco ensayos, y **cubren cuatro de las cinco frases de B14**

*(13 de octubre de 2026. **Tercera ronda de B14. Y la clausula de seguridad tiene su contrato escrito.**)*

## 1. Lo que hay: `tests/test_fase2_f04_csrf.py`, cinco ensayos

```
test_un_origen_ajeno_no_recibe_permiso
test_un_origen_configurado_si_recibe_permiso
*** test_el_preflight_de_un_origen_ajeno_tampoco_lo_autoriza ***
test_la_cookie_va_con_httponly_y_samesite_lax
*** test_ninguna_ruta_que_muta_es_un_get ***
```

## 2. Y contra el criterio, **frase por frase**

```
B14 PIDE                                          EL ENSAYO
  «CSRF CON SESION REAL DE ENSAYO»                  `test_un_origen_ajeno_no_recibe_permiso`
                                                    `test_un_origen_configurado_si_recibe_permiso`
  «ORIGEN PERMITIDO / RECHAZADO»                    los dos de arriba -- *** y son un par: uno niega y otro concede ***
  *** «CORS NO SUSTITUYE AUTORIZACION DE MUTACION» ***  *** `test_el_preflight_de_un_origen_ajeno_tampoco_lo_autoriza` ***
  «MISMA-SITE DISTINTO ORIGEN»                       `test_la_cookie_va_con_httponly_y_samesite_lax`
  *** «AUDITAR GET SIN CAMBIOS» ***                  *** `test_ninguna_ruta_que_muta_es_un_get` ***
  «PRUEBAS NEGATIVAS»                                *el primero de todos: «un origen ajeno NO recibe permiso»*
```

> *** Y las dos que mas valen son **la tercera y la quinta**, y por razones distintas: ***
>
> *** a) `test_el_preflight_de_un_origen_ajeno_tampoco_lo_autoriza` ***
>    *** es **«CORS no sustituye autorizacion de mutacion», comprobado**: *** *el preflight -- que es **la parte que
>    CORS controla** -- **tampoco autoriza**. *O sea: **el proyecto probo que la cabecera permisiva no es un
>    permiso**, *que es **exactamente la confusion que B14 nombra.** *
>
> *** b) `test_ninguna_ruta_que_muta_es_un_get` ***
>    *** es **«auditar GET sin cambios», hecho de la unica forma que no se puede burlar**: *** *no se auditan los GET
>    uno a uno -- **se prohibe que una ruta que muta sea un GET.** *
>    *Que es **otra vez la forma fuerte**: *no **una promesa** («los GET no cambian nada»), *sino **una
>    invariante** que se comprueba sobre **todas** las rutas.* *
>
> *** Undecima forma de imposibilidad, y es la primera que **abarca el conjunto entero de rutas.** *

## 3. Y las cinco frases de B14, con lo que queda

```
1) CSRF CON SESION REAL      *** HECHO *** -- dos ensayos, uno que niega y otro que concede
2) ORIGEN PERMITIDO/RECHAZADO *** HECHO ***
3) CORS != AUTORIZACION      *** HECHO *** -- y de la forma mas directa: el preflight ajeno no autoriza
4) MISMA-SITE DISTINTO ORIGEN `test_la_cookie_va_con_httponly_y_samesite_lax` -- *** y `Lax` es la respuesta: ***
                             *la cookie **no viaja** en una peticion cruzada de mutacion, *que es **lo que
                             `SameSite=Lax` significa.* *
5) AUDITAR GET SIN CAMBIOS   *** HECHO *** -- `test_ninguna_ruta_que_muta_es_un_get`
6) Y LA REGLA                «no declarar defensa completa por 401 sin cookie»  *** POR MIRAR ***
```

> *** Y **la (6) es una advertencia, no una tarea**: *** *«no declarar defensa completa por 401 sin cookie» -- *o
> sea: **que una peticion sin cookie devuelva 401 NO demuestra que la defensa este completa**, *porque **el 401 puede
> venir de que falta la sesion, y no de que el origen este mal.** *
> *** Y **la forma de no caer en eso es lo que el fichero ya hace**: *** *probar **el origen** -- *que es **la
> variable** -- *y no **la ausencia de cookie**, que es **una consecuencia.** *

## 4. Y B14 queda con **tres de cinco bloques hechos, y los tres medidos**

```
1) CSRF CON SESION REAL      *** HECHO *** -- `test_fase2_f04_csrf.py`, cinco ensayos
2) AUDITAR LOS GET           *** HECHO *** -- `test_ninguna_ruta_que_muta_es_un_get`
3) LAS COPIAS Y LA VUELTA    *** MEDIDO: *** `robocopy` semanal de `data\raw` a disco externo;
                             *** y la pregunta abierta: `diario.sqlite` y `recetas.sqlite` son irreemplazables
                             y NO son crudo ***
4) LOGS Y METRICAS           *** MEDIDO EN PARTE: *** `data/runs.csv`, 6 columnas, sin sitio para un secreto;
                             *** y la rotacion NO se ha visto ***
5) Y LA REGLA                «401 sin cookie no es defensa completa»  *** y el fichero ya evita esa trampa ***
```

> *** Y de los cinco, **dos estan contestados enteros con nombre de ensayo**, *y **los otros tres son preguntas
> concretas** -- *una **para el dueño** (que se copia al disco externo), *y dos **por mirar** (la rotacion del log, y
> si hay guion de copia en otro sitio). *
>
> *** Que es **el mismo patron de B13**: *** *lo que se puede averiguar, averiguado; y lo que queda, **dicho con
> nombre.** *
