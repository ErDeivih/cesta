# La publicación del catálogo — 12 de octubre de 2026

**Qué se hizo.** *Se publicó una versión nueva del catálogo, adoptando el gold suelto, y **el puntero
lleva huellas por primera vez**.*

```
antes:  version 20261007-103000 · publicado_en 2026-10-07T10:30:00 · huellas en el puntero: 0
despues: version 20261012-162023 · 6 huellas

/api/estado             -> version 20261012-162023 · fecha_datos 2026-10-11
                           vigencia_precio.coherente = TRUE · huellas_en_el_puntero = 6
/api/estado/publicacion -> coherente = TRUE · no_cuadran = []
```

**Y esto es la primera condición del [veredicto](../SUPERAPP-VEREDICTO-DOMESTICO.md)**, *que decía:*
*«Publicar el catálogo, y que `coherente` deje de ser `None`».*

---

## 1. Por qué se pudo hacer ahora y no antes

**`publicar()` adoptaba el catálogo con `os.link`, y eso hacía que una versión publicada **no fuera
inmutable**.** *Se midió el 12 de octubre:* `fsutil hardlink list` devolvía **tres nombres para un solo
fichero** -- *el suelto, `v20261007-103000` y `v20261011-124542`* -- **y el enlace seguía intacto**, *lo
que prueba que el pipeline **reescribe los parquet in situ**.*

> **Consecuencia**: *`v20261007-103000` se llama 7 de octubre y su contenido era del 11.* **Y publicar
> otra vez con el mismo mecanismo habría propagado el defecto a la versión nueva.**

**A01 lo cambió a `shutil.copy2`, y se comprobó al publicar:**

```
fsutil hardlink list data\gold\v20261012-162023\precio_diario.parquet
    \aprendizaje\scrap\data\gold\v20261012-162023\precio_diario.parquet
```

**Un solo nombre.** *La versión nueva **está aislada**: si mañana el pipeline reescribe el gold suelto,
esta versión no cambia.*

---

## 2. **Y el daño histórico sigue ahí, y no se disimula**

```
fsutil hardlink list data\gold\v20261007-103000\precio_diario.parquet
    \aprendizaje\scrap\data\gold\v20261007-103000\precio_diario.parquet
    \aprendizaje\scrap\data\gold\v20261011-124542\precio_diario.parquet
    \aprendizaje\scrap\data\gold\precio_diario.parquet
```

**Las dos versiones viejas siguen compartiendo inodo con el gold suelto.** *Publicar una versión nueva
**no arregla las anteriores** -- y no se puede arreglar hacia atrás.*

> **Lo que significa, dicho claro**: *si mañana el pipeline reescribe el gold suelto, **`v20261007-103000`
> y `v20261011-124542` volverán a cambiar su contenido**.* **El arreglo protege a las versiones que se
> publiquen de ahora en adelante; no a las tres que ya existían.**
>
> *Y no se han «republicado» para arreglarlas, a propósito*: **republicar una versión vieja con el
> contenido de hoy sería mentir sobre lo que se publicó aquel día**, que es justo el defecto que se está
> arreglando. **Es más honesto que una versión vieja esté contaminada y se sepa, que una versión vieja
> falsificada y limpia.**

---

## 3. Qué dice ahora la aplicación, y por qué es mejor que antes

**Antes de publicar:**

```
/api/estado             -> coherente = false      (por fechas: 11 > 7)
/api/estado/publicacion -> coherente = None       (no hay huellas con que comprobarlo)
```

**Después:**

```
/api/estado             -> coherente = true
/api/estado/publicacion -> coherente = true  ·  no_cuadran = []
```

> **Y la diferencia entre las dos rutas sigue siendo la que importa**: *`/api/estado` compara **fechas**,
> así que sólo delata un desajuste cuando el día del precio va por delante.* **`/api/estado/publicacion`
> compara **huellas**, así que delata cualquier cambio del contenido** -- *y es lo que hace que
> `coherente` sea una afirmación y no una coincidencia.*

---

## 4. Lo que esto **no** arregla, y hay que decirlo

**El catálogo sigue siendo del 11 de octubre.** *La publicación ha hecho que la aplicación **pueda
comprobar** su coherencia; **no ha traído datos nuevos**.*

**Y la ingesta que traería esos datos sigue interrumpida**: *bronze lo prueba -- Aldi 12:26, Mercadona
12:26, DIA 12:37, y **Alcampo y Carrefour con datos del 11**.*

> **Así que el veredicto cambia en una cosa y no en la otra.** *`coherente: true` significa **«lo que hay
> publicado coincide con lo que hay en el gold»** -- no significa «los precios son de hoy».*
> **Y esa distinción es exactamente la que el veredicto mantiene: la aplicación lo dice, y dice la
> verdad.**

**La segunda condición -- los precios al día -- necesita que la ingesta termine**, y eso es otro trabajo.


---

## 5. La ingesta interrumpida, medida cadena por cadena

*(12 de octubre de 2026. **Esto es lo que la revisión del dueño decía, y ahora está medido con la hora de
cada fichero** en vez de con una impresión.)*

```
data/bronze/fuente=alcampo     10-11 12:45     <- AYER
data/bronze/fuente=carrefour   10-11 12:38     <- AYER
data/bronze/fuente=aldi        10-12 12:26     <- HOY
data/bronze/fuente=mercadona   10-12 12:26     <- HOY
data/bronze/fuente=dia         10-12 12:37     <- HOY
```

### Lo que dice, y no es lo que yo había supuesto

**Tres de las cinco cadenas **sí** ingestaron hoy.** *Aldi, Mercadona y DIA, entre las 12:26 y las 12:37.*

**Y las dos que no son Alcampo y Carrefour** -- *las dos con dato de **ayer**, el 11 a las 12:45 y 12:38.*

**Y la tarea `Cesta diaria` corridó a las 12:24:20 y terminó con `3221225786`** --
*`STATUS_CONTROL_C_EXIT`, o sea **un `^C`*** --, *que es exactamente lo que la revisión describía.*

> **Así que la forma de contarlo bien no es «la ingesta no corrió».** *Corrió, hizo tres cadenas, y **la
> mataron antes de hacer las dos que faltaban**.* **Y una de las dos -- Alcampo -- es la única que
> necesita un navegador **visible** para pasar su WAF.**
>
> *Que sea justo la que falta, y justo la que necesita una persona delante, es la clase de coincidencia
> que conviene mirar dos veces antes de llamarla casualidad.*

### Y el orden importa, porque `ORDEN` empieza por Carrefour

```
ORDEN = ["carrefour", "dia", "mercadona", "aldi", "alcampo", "lidl"]
```

**Carrefour es el **primero** de la lista, y su bronze es de ayer.** *DIA, Mercadona y Aldi -- que van
detrás -- sí tienen dato de hoy.* **O sea que no se cortó por la mitad de la lista en orden: Carrefour
falló o se saltó, y el `^C` llegó después.**

*No se ha averiguado por qué*, y **no se inventa**: *lo que consta es que su fichero es de ayer y que la
tarea murió con un `^C`.*

### Lo que se lanzó, y el límite que hay que decir

**Se lanzaron las dos que faltan, sólo esas dos:**

```
uv run python -m projects.cesta.run --solo carrefour alcampo
```

**Y el límite, que es el mismo que el comentario de `config.RITMO` documenta**: *Alcampo va a **una
petición cada 6,7 segundos** porque su WAF -- AWS -- escaló a **pedir un clic humano** tras siete cortes.*
**Si el reto vuelve a pedir ese clic y no hay nadie delante, la cadena no se completa** -- *y eso no es un
fallo del código: es el límite que la fuente pone.*

*Carrefour, en cambio, no necesita navegador.* **Así que si Alcampo se queda a medias, Carrefour debería
completarse igual** -- *y entonces bronze tendría cuatro de cinco al día en lugar de tres.*
