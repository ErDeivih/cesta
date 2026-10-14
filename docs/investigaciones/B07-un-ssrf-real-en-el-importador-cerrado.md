# B07 · **un SSRF real, en el importador de recetas** -- medido, y **cerrado**

*El objetivo pide: *** «*Reabre criterios cerrados por lectura *** y trabaja en implementacion y
evidencia»** *—* *y la fila del control decia: *** «B07 · cerrado como lectura».** *

---

## 1. *** Lo que habia: **la ruta no tenia ni un ensayo** ***

```
*** `tests/test_fase2_f09_fuente_permitida.py` *** *** 19 ENSAYOS ***, *y **todos prueban EL MODULO** *
   *-- *`comprueba_fuente` · `lee_json_ld` · `borrador` ✓
*** Y NINGUNO PASA POR EL ENDPOINT *** ⚠️
   *-- *y **el endpoint es donde viven cuatro guardas**: *la **fuente**, *el **tiempo**
      (`urlopen(..., timeout=10)`), *el **tamaño** (`r.read(2_000_000)`) *
      *y *** las redirecciones *** ⚠️
*** -> *y de las cuatro: *tres estaban, *y *** la cuarta no *** ✓
```

## 2. *** Y el SSRF, medido ***

```
*** `core/recetas.py` / `plataforma/api/recetas.py` ***: *`importar` valida **la URL de entrada**
   *con `comprueba_fuente` **antes de leer nada*** ✓
*** y **despues** *** `urllib.request.urlopen(datos.url, timeout=10)` *** *
   *-- *** `urlopen` SIGUE LAS REDIRECCIONES POR DEFECTO *** *(-- hasta diez --)*
   *-- *y *** el destino no se comprueba *** ⚠️
*** -> asi que **una fuente DECLARADA puede redirigir a un host que nadie declaro**, *
   *y el importador **lo lee** ⚠️
```

**Y medido con un servidor de fixture local:**

```
*** la fuente declarada redirige a *** `localhost` *** (OTRO nombre, *NO declarado)*
*** -> el importador *** sigue la redireccion *** *y **da `422`** *(-- *leyo el destino, *y ahi no
   habia receta --)* ⚠️
```

## 3. *** Y **el arreglo**, reutilizando una guarda que ya estaba ***

```
*** `core/importar_receta.abre_con_guarda(url, timeout=10)` *** *
   *-- *un `HTTPRedirectHandler` que *** valida el destino con `comprueba_fuente` ANTES de ir *** ✓
   *-- *** y no despues ***, *porque **comprobar despues no sirve**: *la peticion al host no
      declarado **ya se hizo** *(-- DNS, conexion, cabeceras --), *y **eso es lo que un SSRF consigue** ✓
*** y **la ruta lo usa**, *traduciendo el `HTTPError` de la guarda a *** `400` con su motivo *** ✓
*** -> **medido despues**: *** da `400` *** ✓✓✓
*** -> y **la guarda no es nueva**: *es *** `comprueba_fuente` ***, *que **ya existia** *
   *-- *con sus **cuatro motivos**, *y **contemplando `file://`** *(-- «no tiene host» --)* ✓
```

## 4. *** Y los cinco ensayos de la ruta, que no existian ***

```
*** FUENTE NO DECLARADA ***      *** 400 *** *con su motivo, *y **sin leer nada** ✓
*** PAGINA SIN `ld+json` ***     *** 422 ***, *y **distinto del 400** ✓
*** LA RED FALLA ***             *** 502 *** *y lo dice ✓
*** EL CAMINO BUENO ***          *borrador con **`fuente`** *y *** `guardada: False` *** ✓
*** LA REDIRECCION A OTRO HOST *** *** 400 *** *** -> el SSRF, cerrado *** ✓✓✓
```

## 5. *** Y **mi propio error de medicion**, que estuvo a punto de enterrar el arreglo ***

```
*** PRIMERA VERSION DEL ENSAYO ***  *redirigia a *** `http://127.0.0.1:OTRO_PUERTO` *** ⚠️
   *** y eso NO es un SSRF ***: *`comprueba_fuente` mira `urlparse(url).hostname`, *
   *** y `hostname` NO lleva el puerto *** -> *el destino *** es la misma fuente declarada**, *
   *y **seguirla es correcto** ✓
   *-- *por eso daba `422` *y **parecia que la guarda fallaba** ⚠️
*** -> **el arreglo ya lo habia intentado**, *y **lo reverti** *porque **el ensayo decia 422** ⚠️
*** -> y **con otro nombre (`localhost`)** el arreglo **se ve**: *** `400` *** ✓✓✓
*** -> *** la sexta vez hoy *** que **el que media mal era yo** *y **no el codigo** ✓
```

> *** Y **por eso el `xfail` fue **estricto**: *
> ```
> *** mientras el hueco estaba ***: *`xfail` *-- *suite verde, *y **el hueco documentado con su motivo** ✓
> *** y **al arreglarse***: *** `XPASS(strict)` *** *-> el ensayo **fallo**, *y **aviso de que habia
>    que quitar la marca** ✓✓✓
> *** -> *** nada de esto se habria sabido sin el ensayo ***: *ni el hueco, *ni el arreglo, *
>    *ni **el fallo de mi medicion** ✓
> ```

## 6. Y el estado, con esto cerrado

```
*** LAS CINCO PUERTAS ***  *** verdes ***: *`ruff` · *** 2.061 passed · 0 failed · 0 xfailed *** ·
   *`81` del frontend · *`tsc` · *`build` ✓
*** y **el recorrido E2E** ***  *** «== TODO BIEN» *** ✓
*** B07 ***  *** de «cerrado por lectura» a **un SSRF cerrado**, *con **su guarda** y **cinco ensayos** ✓✓✓
*** y **lo que queda de B05, B06 y B07** ***: *cosas **medibles una a una** *
   *-- *la **causa** de cada hueco nutricional · *los **historicos de ficha** · *
   *la **foto propia** · *el **duplicar semana** · *los **temporizadores** · *
   *y las cinco de B05 (conflicto por contenido, concurrencia, caida a mitad, dos pestañas,
   destino distinto)* ✓
```
