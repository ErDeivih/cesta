# B13 · **La tabla `traspaso`, medida**: la clave **es** la operacion, y en la base hay **siete recetas en una semana**

*(13 de octubre de 2026. **Octava ronda de B13. Y la aceptacion tiene su prueba en los datos, no en un informe.**)*

## 1. El esquema, literal

```sql
CREATE TABLE traspaso (
    clave       TEXT PRIMARY KEY,      <- *** LA CLAVE ES LA IDENTIDAD DE LA OPERACION ***
    propietario TEXT NOT NULL,
    receta_id   INTEGER NOT NULL,
    version     INTEGER NOT NULL,       <- *** y LA VERSION ***
    semana      TEXT NOT NULL,          <- *** y LA SEMANA ***
    lista_id    TEXT,
    lineas      INTEGER NOT NULL,
    creado      ...
)
```

## 2. Y las siete filas, medidas

```
clave = «propietario|receta_id|version|semana»     <- *** exactamente lo que `traspaso.clave()` describia ***

  …|8|1|2026-10-12    ·  …|13|1|2026-10-12   ·  …|18|1|2026-10-12
  …|28|1|2026-10-12   ·  …|23|1|2026-10-12   ·  …|35|1|2026-10-12   ·  …|3|1|2026-10-12

  *** LAS SIETE en la MISMA semana (2026-10-12) · las siete con `version = 1` ·
      y SIETE RECETAS DISTINTAS (8, 13, 18, 28, 23, 35, 3) · cada una con SU `lista_id` ***
```

## 3. Y contesta **la clausula (2) de B05** -- y **la aceptacion del encargo**

### a) La idempotencia esta **en la base**, no en Python

> *** `clave TEXT PRIMARY KEY` *** -- *o sea: **«la misma operacion no se duplica» no lo decide un `if`: lo impide la
> base.** *
>
> *** Y es **la novena forma de imposibilidad** de la sesion: *** *las otras ocho eran `id uuid PRIMARY KEY` (la
> linea), `fuente_dato NOT NULL`, `FUENTES` vacia, `ON CONFLICT`, la despensa sin clave ajena, `cocina.py` sin
> importar el diario, `UsuarioRepetido`, y `RE_PACK`… *y **esta es la que el `docstring` de `traspaso` ya decia**:
> *** «la identidad tiene que ser de la OPERACION, no del resultado». ***
>
> *** Y **`propietario` esta DENTRO de la clave** *** -- *o sea: **dos personas pueden traspasar la misma receta la
> misma semana sin pisarse**, *porque **la clave las distingue.** *

### b) Y la aceptacion -- «cinco recetas semanales» -- **esta superada en los datos**

```
LA ACEPTACION PIDE:  «cinco recetas semanales con cantidades, compra y porciones reales
                      que persisten tras recargar»

Y EN LA BASE HAY:    *** SIETE traspasos, todos de la semana 2026-10-12 ***
                     -> siete recetas distintas (8, 13, 18, 28, 23, 35, 3)
                     -> cada una con su `lista_id` (siete listas)
                     -> y `lineas` por traspaso (la columna esta, y **no se ha leido su valor**)
```

> *** O sea: *** *** **la aceptacion no hay que imaginarla: hay siete operaciones de traspaso, de siete recetas, en
> una sola semana, y con su lista cada una.** ***
>
> *** Y **no se dice que la aceptacion este cumplida** ***: *se dice que **el dato que la aceptacion describe**
> **existe**, *y que **lo que falta es **recorrerlo** y **comprobar que persiste tras recargar** -- *que es
> **exactamente lo que el paso 4 pide.** *
>
> *** Y **`version = 1` en las siete** *** *dice algo mas: **ninguna de esas recetas se edito despues de traspasarla**
> -- *y **`version: 43` con `receta: 42`** dice que **una receta si tiene dos versiones**, *o sea: **el versionado
> esta probado por otro lado.** *

## 4. Y un dato que cierra la restriccion del propietario, del lado de los datos

> *** La restriccion decia: *** *«el fallo de que 300 g necesarios terminan como **una unidad y una nota de 100 g**,
> **descartando la segunda receta como repetida**.»*
>
> *** Y **`traspaso` tiene 7 filas de 7 recetas distintas en la misma semana** *** -- *o sea: *** *** **siete recetas
> distintas NO se descartaron como repetidas.** ***
>
> *** Y eso es **la mitad de la restriccion, comprobada en los datos**: *** *«descartar la segunda receta como
> repetida» **no ha pasado** en las siete operaciones que hay -- *porque **la clave las distingue por `receta_id`**,
> y no por «lo mismo». *
>
> *** Y la otra mitad --«300 g terminan como una unidad y una nota de 100 g»-- **es de las lineas de la lista**, ***
> *y para verla hay que mirar **`lista_linea` en Postgres** -- *que es **el siguiente sitio**, y **no se ha mirado.** *

## 5. Y B13 queda con **todo lo averiguable, averiguado**

```
  1) RUTAS Y COMPONENTES       HECHO
  PASO 1 (usuarios)            HECHO -- 38, convencion, y el aviso de «Madre»
  PASO 2 (crea_usuario)         HECHO Y CONCLUYENTE
  PASO 3 (elegir)              RESUELTO -- `prueba` / `prueba-invitada`
  PASO 4 (por donde)           HECHO -- http://127.0.0.1:8080 (200)
  PASO 4 (los datos)           *** HECHO: 42 recetas · 42 del plan · 43 versiones · 7 traspasos · 11 entradas ***
                               *** y los 7 traspasos son de UNA semana: la aceptacion tiene su dato ***
  PASO 5 (capturas)            con las guardas: sin «Madre», y sin los dos `.sqlite`
  *** Y LA OTRA MITAD DE LA RESTRICCION: `lista_linea` en Postgres -- POR MIRAR ***
```

> *** Y el paso que queda **no es del navegador**: *** *es **una consulta a `lista_linea`** para ver **con que unidad y
> con que cantidad** entraron esas siete recetas -- *o sea: **si los 300 g entraron como 300 g, o como «1 unidad» y
> una nota.** *
>
> *** Que es **la restriccion del propietario, del lado de los datos**, *y **se puede mirar sin abrir el navegador.** *
