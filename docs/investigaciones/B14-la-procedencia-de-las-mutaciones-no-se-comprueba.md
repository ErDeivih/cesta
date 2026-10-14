# B14 · **La procedencia de las mutaciones: NO se comprueba** -- medido, no supuesto

*14/10/2026. **Sale de leer el plan entero**, *que es lo que el encargo pide: *** «Completa B00–B16».** *
*Y `docs/SUPERAPP-PLAN-DEEPSEEK-2026-10-13.md:348` (B14) pide, ademas de las copias:*

> *** «Revisar CSRF con sesion real de ensayo, *** origen permitido/rechazado *** y *** misma-site distinto
> origen ***; *** CORS no sustituye autorizacion de mutacion ***. *Auditar GET sin cambios,
> Origin/Referer/Fetch Metadata o token segun contrato *** y pruebas negativas***.» ***

*Yo habia dado B14 por cubierto **mirando solo la mitad** -- *copias y restauracion* --, *y **esta es la otra.** *

---

## 1. *** Lo que hay hoy en el codigo ***

```
*** `plataforma/api/main.py:67` ***  *** `app.add_middleware(CORSMiddleware, allow_origins=list(AJUSTES.origenes))` *** *
   *** -> lo unico que mira el origen es CORS *** *
*** `plataforma/api/main.py:93` y `:134` ***  *** `set_cookie(COOKIE, token, httponly=True, samesite="lax")` *** *
*** y `git grep` de `Origin|CSRF|SameSite` en `plataforma/api` ***  *** -> no hay ninguna comprobacion
   de `Origin` en las rutas de mutacion *** *
```

## 2. *** Y la prueba negativa que el plan pide, hecha ***

*Con **sesion real de ensayo**, *y **tres mutaciones** de crear linea, *cambiando solo el `Origin`:*

```
*** `Origin` permitido (`localhost:8080`) ***              *** `201` ***  *** -> crea la linea *** ✓
*** `Origin: http://localhost:9999` *** *** (MISMO SITIO, DISTINTO ORIGEN) ***  *** `201` *** *** -> crea la linea *** ⚠️
*** `Origin: https://sitio-ajeno.example` *** *** (OTRO SITIO) ***          *** `201` *** *** -> crea la linea *** ⚠️
*** Y COMPROBADO EN LA LISTA, no en la respuesta ***: *
  *** `PRUEBA-CSRF-14-10-ok` · `PRUEBA-CSRF-14-10-ajeno` · `PRUEBA-CSRF-14-10-web` *** *** -> LAS TRES ESTAN *** ⚠️⚠️
```

> *** Las tres **persistieron.** *O sea: **no hay control de procedencia en las mutaciones.** *
>
> *** Y **`SameSite=lax` NO cubre el caso que el plan nombra**: *`localhost:9999` y `localhost:8080` son
> *** el mismo sitio *** *(-- «same-site» es el dominio registrable, *y **el puerto no cuenta** --), *asi que
> **la cookie viaja**, *y **sin mirar el `Origin`, la escritura pasa.** *
>
> *** Y **CORS no lo impide**, *que es **literalmente lo que el plan advierte**: *CORS **no deja leer la
> respuesta** *(-- y por eso el navegador bloquea la lectura --), *pero **la peticion ya se hizo y el
> servidor ya escribio.** *

## 3. *** Y por que NO lo arreglo yo ***

```
*** un control de `Origin` es una DECISION DE DISENO, y tiene tres preguntas dentro *** *
  *** 1) ¿QUE ORIGENES SE PERMITEN? ***  *-- *`AJUSTES.origenes` existe, *y hoy solo alimenta CORS*
  *** 2) ¿QUE SE HACE CON UNA PETICION SIN `Origin`? ***  *-- *y esto es lo importante: *
     *un cliente que **no es un navegador** *(-- el **movil**, **curl**, *el propio `prueba_e2e.py` --)
     *puede **no mandar `Origin`**, *y **rechazarlo seria romper el uso legitimo***
     *-- *o sea: *«sin `Origin` -> no pasa» **rompe la app**; *«sin `Origin` -> pasa» **deja el hueco
     abierto** para quien lo omita a proposito*
  *** 3) ¿SE RECHAZA, O SE EXIGE UN TOKEN? ***  *-- *y un token por operacion es **mas codigo y mas
     superficie**, *no una linea*
*** -> ninguna de las tres la puedo contestar yo: *son **del propietario**, *y elegir mal **rompe el
   movil** o **deja el hueco.** *
```

## 4. *** Y lo que B14 tiene ya cubierto, para no confundir el balance ***

```
*** COPIAS ***           *** PostgreSQL + el recetario + el diario *** ✓
  *-- *y **los metadatos**: *el `plan` de recetas esta **dentro** del recetario, *y las listas/compra/
  permisos **dentro** del volcado -- *o sea: *los tres destinos que B14 nombra **estan cubiertos***
*** RESTAURACION DE LOS TRES ***  *** hecha ***, *en base nueva y desechable, *con **las tres patas
  dentro del ensayo** ✓✓✓
*** HASHES · RETENCION · VERIFICACION ***  *** hechos ***: *sello de tiempo · 30 dias para los dos tipos ·
  *y **verificacion por contenido** (`346/73/257/97/272` y `integrity_check`) ✓
*** Y LO QUE FALTA ***  *** procedencia de las mutaciones *** *(-- esto --)*,
  *y **los GET sin cambios** *(-- que es **la otra mitad de la misma frase del plan --)** ⚠️
```

## 5. Y **las tres lineas de prueba siguen en la lista de ensayo**

*Y **a proposito**: *son **la evidencia** de que la comprobacion se hizo de verdad, *y estan **en una lista
mia** *(-- «Ensayo envases 14/10» --), *no en ninguna del propietario.* *Cuando se cierre el hueco,
**el ensayo que lo cierre las usara** *-- *y entonces ya no haran falta.*
