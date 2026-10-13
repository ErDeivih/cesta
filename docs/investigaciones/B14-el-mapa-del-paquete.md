# B14 (y B15) · **El mapa** -- y las dos traen frases que son el encargo, refinado

*(13 de octubre de 2026. **Lo siguiente por el plan, y son los dos paquetes de cierre.**)*

## 1. B14, literal (`plan:348`)

> **B14 · Seguridad, copias y operacion**
>
> *«Revisar *** CSRF con sesion real de ensayo ***, *** origen permitido/rechazado *** y *** misma-site distinto
> origen ***; *** CORS no sustituye autorizacion de mutacion ***. *** Auditar GET sin cambios ***,
> Origin/Referer/Fetch Metadata o token *** segun contrato *** y *** pruebas negativas ***. *** Copias de PostgreSQL,
> SQLite privados y metadatos; restauracion de los TRES, hashes, retencion y verificacion ***. Programacion local
> solo con guardas; *** destino externo requiere decision concreta, no subir datos a una nube elegida por el agente ***.
> *** Logs crecientes con rotacion, metricas y secretos ausentes ***; TLS/registro/ratelimits *** en matriz distinta de
> uso local ***. *** No declarar defensa completa por 401 sin cookie. ***»*

## 2. Y desglosado, son cinco bloques -- y **cuatro traen una frase que corrige una confusion**

```
1) CSRF CON SESION REAL        -- «origen permitido/RECHAZADO» · «misma-site DISTINTO ORIGEN»
   *** «CORS no sustituye autorizacion de mutacion» ***   <- *una cabecera permisiva NO es un permiso*
2) AUDITAR LOS GET             -- *** «auditar GET sin cambios» ***: *un GET **no puede** cambiar nada*
                                y el contrato (Origin/Referer/Fetch Metadata o token) **segun contrato**, con
                                *** pruebas NEGATIVAS ***
3) LAS COPIAS Y LA VUELTA      -- *** «copias de PostgreSQL, SQLite privados y metadatos; restauracion de
                                LOS TRES, hashes, retencion y verificacion» ***
                                *** y «destino externo requiere decision concreta, NO SUBIR DATOS A UNA NUBE
                                ELEGIDA POR EL AGENTE» ***
4) LOGS Y METRICAS             -- *** «crecientes con rotacion, metricas y SECRETOS AUSENTES» ***
                                y TLS/registro/ratelimits *** «en matriz DISTINTA de uso local» ***
5) Y LA REGLA QUE CIERRA       -- *** «NO DECLARAR DEFENSA COMPLETA POR 401 SIN COOKIE» ***
```

> *** Y las cinco son **correcciones de una confusion comoda**, y las cinco van en la misma direccion: ***
>
> ```
> «CORS permisivo»          NO es «autorizacion de mutacion»
> «el GET no rompio nada»    NO es «el GET no cambia nada»   -> hay que AUDITARLO
> «hay copia»                NO es «se puede volver»          -> hay que RESTAURAR LOS TRES
> «hay logs»                 NO es «no hay secretos dentro»   -> hay que comprobarlo
> «sin cookie da 401»        NO es «la defensa esta completa»
> ```
>
> *** O sea: **el paquete de seguridad no pide anadir defensas: pide COMPROBAR las que se creen tener.** ***
> *Y es **la misma disciplina** que los trece paquetes anteriores: **no dar por bueno lo que no se ha medido.** *
>
> *** Y la (3) es **la que mas importa para el propietario**: *** *** «no subir datos a una nube elegida por el
> agente» *** -- *que es **su «no despliegues publicamente»**, *dicho **del lado del destino de las copias.** *
> *** O sea: **ni publico, ni a un tercero.** *

## 3. B15, literal (`plan:359`)

> **B15 · Aprendizaje reproducible**
>
> *«Actualizar *** `docs/aprende` ***: *** fuente->raw->bronze->silver->gold->API ***, fichas versus precios,
> Parquet/DuckDB/SQLite/PostgreSQL, entidades, unidades, matching, costes y promociones, evaluacion del algoritmo,
> linaje, nutricion y casos de errores reales. *** DBT/Dagster: documentar que esta realmente instalado/usado; no
> introducirlos para decorar el stack ***. *** Cada capitulo con ejemplo, comando seguro, salida esperada y test ***.»*

> *** Y trae **dos reglas que valen por todo el paquete**: ***
>
>   - *** «documentar que esta **realmente** instalado/usado; **no introducirlos para decorar el stack**» *** -- *que
>     es **el encargo**: «no consideres terminado lo que solo abrio una pantalla vacia», *aplicado **a una
>     herramienta**: **no la metas para que la lista parezca mejor.** *
>   - *** «cada capitulo con **ejemplo, comando seguro, salida esperada y test**» *** -- *o sea: **un documento de
>     aprendizaje tiene que poder **repetirse**, *y **«comando seguro» quiere decir que no rompe nada.** *
>
> *** Y **`docs/aprende` existe** *** -- *y **no se ha mirado**: *es **la zona de B15**, *y **la unica del plan que
> no ha aparecido todavia.** *

## 4. Y el orden, con lo que queda

```
B13   *** AVERIGUADO ENTERO ***  -- *y lo que falta es **ejecutar los cinco recorridos** (necesita navegador)
B14   *POR MIRAR* -- y sus cinco bloques **se pueden comprobar**: hay sesion, hay copias, hay logs
B15   *POR MIRAR* -- y su zona es *** `docs/aprende` ***, que **existe y no se ha abierto**
B16   *el dictamen final*  -- **«dictamen por capacidad y puertas finales»**
```

> *** Y **B14 y B15 son, casi enteros, comprobables sin navegador** *** -- *a diferencia de B13:*
>
>   - **B14**: *«CSRF con sesion real de ensayo»* -> **los ensayos ya existen** (`test_fase2_f07_dos_sesiones.py`,
>     y `test_publicacion.py`); *«copias»* -> **hay que ver si hay guion de copia**; *«logs crecientes con
>     rotacion»* -> **`data/runs.csv` es un log que crece**, *y **se puede mirar si rota.** *
>   - **B15**: *`docs/aprende`* -> **es un directorio, y se lee.** *
>
> *** O sea: **de los cuatro paquetes que quedan, tres se pueden trabajar leyendo** *** -- *y **solo B13 necesita el
> navegador.** *
