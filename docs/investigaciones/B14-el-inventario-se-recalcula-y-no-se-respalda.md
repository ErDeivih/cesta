# B14 · **¿Hay que respaldar `inventario.sqlite`?** No -- y por que se puede decir

*2026-10-14. **Sale de la prueba de restauracion**: el complemento pide cubrir PostgreSQL, recetas/diario
SQLite **y permisos/snapshots**. *Y al mirar que hay en `data/` salen **dos ficheros mas de estado**, y
**27 MB** entre los dos.* *

## 1. Lo que hay en `data/`, y cuanto ocupa

```
*** `inventario.sqlite` ***                    *** 14,41 MB *** *
*** `inventario.sqlite.antes-de-reconciliar` *** *** 13,63 MB *** *
*** `recetas.sqlite` ***                       0,05 MB   *-- *el recetario*
*** `diario.sqlite` ***                        0,02 MB   *-- *el diario*
```

> *** Y **los dos grandes no los respalda nadie** -- *ni `respaldar.bat`, ni el nuevo `respaldar_sqlite.py`,
> que solo copia el recetario y el diario.* *Asi que la pregunta es la de siempre: **¿esto se recalcula, o
> se pierde?** *

## 2. *** Y la respuesta esta escrita en el codigo ***

```
*** `core/inventario.py:202` ***  *** «**Levanta el inventario desde `bronze` historico**: la union de to[das]» *** *
*** `core/storage.py:24` ***       *** `CAPAS_INTOCABLES = ("bronze", "gold")` *** *
```

> *** O sea: *** *** **el inventario se RECALCULA desde `bronze`**, *que es **una capa intocable**.* *
>
> *** Y **eso sigue la politica del propio proyecto**, que esta escrita en `core/storage.py`: ***
> *«**`raw` se puede tirar cuando caduca** -- *ocupa 338 MB»*, *y `comprueba_borrable` **revienta si la ruta
> cae dentro de una capa que no se borra**.* **La regla: **lo que recalcula se puede tirar; lo que no,
> no.** *
>
> *** Y **el inventario recalcula** -- *basta volver a levantar la union de todo el `bronze` historico.* *
> *-- *y `.antes-de-reconciliar` es **un resto de una reconciliacion**: *se puede rehacer tambien, y su
> nombre lo dice.* *

## 3. *** Y por eso el respaldo esta BIEN como esta ***

```
*** LO QUE NO SE REGENERA, y ahora SI se respalda: *** *
  *** PostgreSQL ***      *-- *las cuentas, las listas, la compra, los favoritos **Y los permisos***
  *** `recetas.sqlite` ***  *-- *** el RECETARIO *** *
  *** `diario.sqlite` ***   *-- *** el DIARIO *** *

*** LO QUE SE REGENERA, y por eso NO se respalda: *** *
  *** `inventario.sqlite` (14 MB) ***  *-- *se levanta desde `bronze`*
  *** `.antes-de-reconciliar` (14 MB) ***  *-- *un resto de una reconciliacion*
  *** `gold` ***  *-- *se regenera desde `raw` con `ejecutar.bat`*
  *** `raw` ***   *-- *se vuelve a bajar de las webs*
```

> *** Y **la distincion no es de tamano**: *el `diario.sqlite` ocupa **0,02 MB** y **es lo mas importante de
> la casa**; *el `inventario.sqlite` ocupa **14,41 MB** y **se rehace solo**.* *
>
> *** -> y es **la misma regla que el resto del proyecto**: *** *** **no se respalda por lo que pesa, sino por
> lo que no se puede volver a calcular.** *** *
