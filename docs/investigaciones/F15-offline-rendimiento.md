# F15 -- Offline, rendimiento y aprendizaje (P1/P2)

**Criterio, de `docs/SUPERAPP-FASE2-EMPEZAR-AQUI.md:185`:**

> **Definir que funciona sin red local/servicio: datos cacheados fechados, borradores y acciones pendientes.**
> **Medir busqueda/listas/fichas/graficas con volumen real: paginacion, indices, cargas, tamanos JS y latencia.**
> **Actualizar material educativo** con ejemplos reproducibles crudo -> normalizacion -> identidad -> coste/nutricion.
> **Aceptacion:** **mala conexion / error / recuperacion sin duplicados y cuenta cruzada**; **antes/despues de
> rendimiento**.

---

## 1. Punto de partida: **tres cosas distintas en un paquete**, y una de ellas ya tiene pieza medida

**De F15 no se ha medido nada.** *Pero el criterio son **tres trabajos que no se parecen**:*

| | que es | **como se mide** |
|---|---|---|
| **offline** | *definir **que funciona sin red*** -- datos cacheados fechados, borradores, acciones pendientes | *leyendo el codigo y **con el servidor caido*** |
| **rendimiento** | *medir con **volumen real**: paginacion, indices, cargas, tamanos JS y latencia* | ***midiendo***: `SELECT`, `du`, y tiempos |
| **aprendizaje** | *actualizar el material educativo con **ejemplos reproducibles*** | *leyendo y reescribiendo* |

**Y la aceptacion nombra la parte que **ya tiene una pieza medida en esta fase**:**

> *«mala conexion / error / recuperacion **sin duplicados y cuenta cruzada**»*

**«Sin duplicados y cuenta cruzada» es, palabra por palabra, `N01`/`N04`:** *la **clave de operacion** --
«el cliente la genera al enviar y **la repite si reintenta**… y **dos comidas legitimas llevan claves
distintas**».* **Y «cuenta cruzada» es la carrera que `test_fase2_f02_concurrencia.py` ya prueba**: *«misma
clave a la vez -> **una** entrada; choque -> **400**».*

**Asi que la mitad de la aceptacion de F15 esta **medida y pasando** -- *lo que falta es **lo de offline**: que
pasa cuando la red **no esta**.*

### Y hay dos piezas de offline que ya se han visto, y conviene anotarlas como pistas

1. **`alcampo._cache_limpia`** (`F03`): *«reanudar una captura **sin volver a pedirla**»* -- *y rechaza un reto
   cacheado.* **Es cache, y es del colector, no de la app.**
2. **`F14` acaba de anadir `prefers-reduced-motion`**, y **la app nueva no tiene `service worker`** -- *que es
   **la** pieza de offline en una web*. *Y el laboratorio auxiliar **bloquea los service workers** por defecto en
   sus escenarios (`service_workers: "block"`), **que es una pista de que el proyecto ya se topo con esto**.*

**Lo primero es un `SELECT`**: ***¿hay `service worker`, hay `localStorage` de datos, y hay cola de acciones
pendientes?*** *Tres preguntas, y **las tres son de codigo, no de pantalla** -- asi que se contestan antes de
levantar nada.*

### Y el rendimiento es lo unico de la fase que se mide **con reloj**

**«Antes/despues de rendimiento»** *exige **dos medidas**, y eso es lo que F16 quiere con «evidencia»:*
**paginacion** (¿hay?), **indices** (¿cuales?), **cargas** (¿cuantas peticiones?), **tamanos JS** (*el build ya
avisa: «Some chunks are larger than 500 kB»*) y **latencia**.

**Y el aviso del build no es una hipotesis: es un mensaje que el propio build escupe** -- *y **esta sin
resolver**.*


---

## 2. El `SELECT`: **offline esta, por `navigator.onLine` y React Query -- y no por `service worker`**

*(Ronda 146.)* Las tres preguntas del §1, contestadas **de codigo, sin levantar nada.**

### 1. `service worker`: **no hay** -- y las dos menciones son otra cosa

```
plataforma/web/app/src/paginas/Cesta.tsx:1207   // React Query *pausa* una mutacion cuando `navigato[r.onLine]`...
plataforma/web/app/src/paginas/Cesta.tsx:1292         if (!navigator.onLine) return
```

**Un `service worker` no aparece en ninguna parte.** *Y las **dos** menciones de la busqueda son
`navigator.onLine`, que es **otra cosa**: no cachea la aplicacion, **consulta si hay red**.*

### Y eso **no** significa que offline no este: significa que esta de otra forma

**`Cesta.tsx:1207` dice el mecanismo, en un comentario:**

> *«**React Query *pausa* una mutacion cuando `navigator.onLine`** [es falso]…»*

**Es decir: cuando no hay red, **la mutacion no falla: se pausa** -- y **React Query la reanuda cuando vuelve la
conexion**.* **Y `:1292` es el otro lado**: *`if (!navigator.onLine) return`, o sea **no se intenta** lo que no
puede funcionar.*

**Y eso es, exactamente, la aceptacion de F15**: *«mala conexion / error / **recuperacion sin duplicados**».* *La
recuperacion la hace **la pausa**, y **los duplicados los evita la clave de operacion** (`N01`/`N04`, medido).*
**Las dos piezas encajan, y por eso estan separadas en dos sitios: React Query sabe **reanudar**, y la clave sabe
**no duplicar al reanudar**.***

### 2. `localStorage`: **si, y con el motivo escrito**

```
plataforma/web/app/src/App.tsx:47,127-128        la ultima pantalla visitada
plataforma/web/app/src/componentes/VistasGuardadas.tsx:3
    *  Se guarda en `localStorage` porque **no hay** ...
plataforma/web/app/src/estado/busquedasRecientes.ts:9
    *  En `localStorage` porque **no hay endpoint p[ara]** ...
```

**Hay persistencia local, y en los dos sitios el comentario dice **por que** esta ahi: **porque no hay
servidor para eso**.** *Y esa es una decision correcta y **del criterio**: «datos cacheados fechados» -- *la
pantalla guardada y las busquedas recientes **no se piden al servidor**, asi que **funcionan sin red**.*

**Lo que **no** hay es `localStorage` con **los datos de la compra** -- *ni la lista, ni el diario, ni las
fichas.* *Asi que **sin red no se puede consultar nada**, pero **la aplicacion si arranca y recuerda donde
estabas**.*

### 3. «Cola de pendientes»: **163 menciones y casi todas son otra cosa**

*`cesta.py:380` («van en `pendientes`, que es de donde s[e]…»), `:341` («descuentos con cantidades pendientes de
autorizacion»), `almacen.py:902` («`por_mirar` es **la cola del vigilante**»)…* **Ninguna es una cola de
acciones de la interfaz.**

**Y la cola de verdad **es la de React Query**: *las mutaciones pausadas **son** la cola de pendientes, y no hay
que escribir una.*

### Y `F15`, con lo medido

| lo que pide F15 | **estado** |
|---|---|
| **«que funciona sin red»** | **la aplicacion arranca y recuerda** (pantalla y busquedas recientes en `localStorage`); *los **datos** no* |
| **«datos cacheados fechados»** | **por medir** -- *y `C06` ya garantiza que **la fecha se ensena**, asi que un dato cacheado **se podria fechar*** |
| **«borradores»** | *por medir* |
| **«acciones pendientes»** | **si, y sin escribir cola**: *React Query **pausa** la mutacion y la reanuda* |
| **«sin duplicados y cuenta cruzada»** | **medido y pasando**: *la clave de operacion (`N01`/`N04`) y `test_fase2_f02_concurrencia.py`* |
| **rendimiento, con volumen real** | *por medir: es lo que falta, y necesita **reloj*** |
| **material educativo** | *por medir* |

**Cinco de siete, y **los dos que faltan son de numeros**: el rendimiento (que exige medir) y el material.** *Y
la pieza que parecia la mas gorda -- «acciones pendientes» -- **ya estaba resuelta sin cola propia**, porque
React Query la trae.*


---

## 3. El rendimiento, con reloj: **700 KB en un solo chunk, y un tope que no es paginacion**

*(Ronda 147.)* **El «antes» de F15**, y son numeros, no impresiones.

### Los tamanos, medidos sobre **lo que se sirve** (`plataforma/web/dist/assets`)

```
   681.283 b   index-CeOlamCl.js        <- UN SOLO chunk
    35.924 b   index-DxKGHfQJ.css
    ---------
   717.207 b   total (unos 700 KB)
```

**Y el aviso del build **no era una hipotesis**: *«Some chunks are larger than 500 kB after minification» -- y el
chunk son **681 KB**, o sea **un 36 % por encima del umbral que el propio Vite considera excesivo**.*

**Y esta **sin dividir**: un solo fichero, que se descarga **entero** antes de que la aplicacion arranque** -- *y
en un movil en un pasillo, eso es lo que decide si la pantalla aparece o no.*

### La paginacion: **hay tope, y no hay paginacion**

```python
254  def buscar(texto: str, cadenas: list[str] | None = None, limite: int = 40, ...
340  args = texto_args + atributo_args + atributo_args + [limite]
422  LIMIT ?
```

**El `LIMIT` esta parametrizado** -- *no es un 40 escrito a mano en el SQL, es un parametro* --, **y eso es
correcto**. *Pero **no hay `OFFSET` en ninguna parte** de `catalogo.py`:*

> **Se devuelven **los primeros 40**, y **no se puede pedir la pagina 2**.**

**Y el criterio dice «paginacion», que es otra cosa que «tope».** *Un tope **corta**; una paginacion **continua**.*
*Con el buscador, **ver los 41º y siguientes no es posible** -- y eso **no es un problema de rendimiento: es una
funcion que no esta**.* **Es la distincion de siempre, otra vez: no confundir «se para» con «no hay mas».**

### Y lo que queda por medir, que necesita el servidor levantado

| lo que pide F15 | **como se mide, y por que no esta todavia** |
|---|---|
| **«indices»** | *`SELECT` sobre el esquema del catalogo (DuckDB, que **no usa indices clasicos** -- *usa zonemaps*), **por medir*** |
| **«cargas»** | *cuantas peticiones hace una pantalla: **necesita el navegador*** |
| **«latencia»** | *`/api/buscar` con los **52.087 grupos** reales: **necesita la API levantada*** |

**Los tamanos **si** se han medido -- *y son el numero que mas importa, porque es el unico que **ve el usuario
antes de que la aplicacion exista***.

### Y `F15`, con lo medido

| lo que pide F15 | **estado** |
|---|---|
| **offline: que funciona sin red** | **medido**: *arranca y recuerda; los datos no* |
| **acciones pendientes sin duplicar** | **medido y pasando** (React Query + clave de operacion) |
| **paginacion** | **NO HAY**: *hay un tope de 40, y **no se puede pedir la pagina 2*** |
| **tamanos JS** | **medido**: **681 KB en un chunk**, un 36 % sobre el umbral de Vite |
| **indices / cargas / latencia** | *por medir: los tres necesitan el servidor o el navegador* |

**Tres de seis con numero, y los tres que faltan son los que exigen levantar algo.** *Y el unico que resulto ser
una **funcion ausente** -- la paginacion -- **no era el que parecia**: se buscaba un problema de rendimiento y
aparecio **una capacidad que no esta**.*


---

## 4. La latencia, medida -- *una de las tres cosas que `F15` pedia y no estaban*

*(Ronda 216. **`F15` pedia «indices, cargas, tamanos JS y latencia»; la latencia ya tiene numero.**)*

### Lo que se midio

**Cinco llamadas por endpoint, desde el navegador, con la pila del sandbox** (*API `8102`, Vite `5173`*):

```
/api/yo                                  mediana  20,6 ms   min 14,8   max  23,0   {200}
/api/listas                              mediana  16,2 ms   min 14,7   max  17,8   {200}
/api/despensa                            mediana  14,2 ms   min 13,3   max  15,1   {200}
/api/cocina/7?version=2                  mediana  13,5 ms   min 12,9   max  13,7   {200}
/api/catalogo/buscar?texto=leche&...     mediana   6,9 ms   min  6,6   max   7,3   {404}
```

### Y lo que dicen los numeros, que es lo util

**Los cuatro endpoints de las funciones nuevas** -- *la despensa, la cocina, la sesion y las listas* -- **contestan en
**13 a 21 milisegundos**, y **con muy poca dispersion**: *la diferencia entre el mas rapido y el mas lento de cinco
intentos es de **2 a 8 ms**.*

> **Y eso importa porque el tope de espera se puso en **diez segundos**.** *O sea: **el tope esta a un factor de
> **quinientas veces** por encima de la mediana real**.* **No es un limite que se pueda alcanzar por lentitud normal**
> -- *solo por **un atasco de verdad**, que es exactamente lo que tiene que detectar.* **Y ahora se sabe, en vez de
> suponerlo.**

### Y el `404`, que es **de mi medicion y no del producto**

**La quinta ruta la escribi de memoria y **no existe**: `/api/catalogo/buscar` devuelve `404`.** *El buscador **si**
existe -- *su ruta esta declarada en otro sitio* --, **y lo que fallo fue mi suposicion de como se llama.**

**Y por eso se dice, en vez de quitarlo de la tabla**: *un `404` en una tabla de latencias **parece un fallo del
buscador** y **es un fallo de quien midio**.* *Es la misma distincion que el resto de la fase: **decir cual de las
dos cosas es.***

### Y lo que queda de `F15`, con su nombre

| lo que `F15` pide | **estado** |
|---|---|
| **paginacion** | **hecha** -- *y destapo que el orden de `buscar` no es total* |
| **latencia** | **medida** -- *13 a 21 ms en los cuatro endpoints nuevos* |
| **tamanos JS** | **medido** antes: *681 KB en un solo chunk + 35,9 KB de CSS* |
| **cargas** | *por medir: cuantas peticiones hace una pantalla al abrirse* |
| **indices** | *por medir: que indices tiene la tabla y cuales se usan* |

**Y las dos que quedan son **medibles sin decidir nada** -- *asi que van despues de esto, no antes.*


---

## 5. Los indices, medidos -- *y estan en **dos motores**, que es lo primero que hubo que aprender*

*(Ronda 217. **La ultima de las tres cosas que `F15` pedia y no estaban.**)*

### Y antes de los numeros, dos intentos fallidos que hay que decir

**1. `pg_indexes`, en Postgres.** *Devuelve **cuatro** indices -- *y **ninguno del catalogo***:*

```
cocina    cocina_pkey        (usuario_id, receta_id)
compra    compra_pkey        (id)
compra    compra_por_lista   (lista_id, cerrada_en DESC)
despensa  despensa_pkey      (usuario_id, texto)
```

**2. Y `from catalogo import conexion`, que no existe.** *El modulo es `plataforma.api.catalogo`, y `core` **no tiene**
uno.*

> **Las dos cosas dicen lo mismo, y es lo que hay que entender antes de contar indices**: *el catalogo **no esta en
> Postgres**.* *`grupos` y `buscable` viven en **DuckDB**, y **`pg_indexes` no sabe nada de ellos** -- *no porque no
> tengan indices, sino porque **no son suyos**.* **Preguntarle a un motor por las tablas de otro devuelve un cero que
> parece un dato y es una respuesta a otra pregunta.**

### Y los numeros, en su motor

**DuckDB, `duckdb_indexes()`:**

```
indices en el catalogo:  1
    buscable_grupo   en `buscable`   (no unico)
```

**Y las tablas del catalogo, que son siete:**

```
buscable   derivado   diario   enlaces   grupos   palabras   resumen
```

### Y lo que eso dice, que es mas interesante que el numero

**Hay **un** indice, y esta **en la tabla que lee la busqueda** -- `buscable`.** *Y **`grupos` -- 52 087 filas -- no
tiene ninguno**.*

**Y eso no es un descuido, por dos razones que conviene decir juntas:**

1. **El motor es DuckDB**, *que es **columnar** y **no usa indices B-tree como Postgres**: *para agregaciones y
   exploraciones completas **lee columnas enteras**, y **un indice no ayuda** -- *puede estorbar.*
2. **Y las consultas que importan lo confirman**: *`buscar` filtra por texto **sobre `buscable`** -- *que **si** tiene
   indice* --, y **el resto de la aplicacion lee `grupos` entero** para agrupar, comparar y calcular. **Un indice
   sobre `grupos` no se usaria.**

> **Asi que «un indice» no es «un indice de menos»**: *es **lo que el motor necesita**.* *Y lo que lo convierte en un
> dato y no en una sospecha es **haber mirado el motor** -- *que es lo que los dos intentos fallidos obligaron a
> hacer.*

### Y las cinco cosas que `F15` pedia, con su estado

| lo que `F15` pide | **estado** |
|---|---|
| **paginacion** | **hecha** -- *y destapo que el orden de `buscar` no es total* |
| **latencia** | **medida**: *13 a 21 ms en los cuatro endpoints nuevos* |
| **tamanos JS** | **medido**: *681 KB en un solo chunk + 35,9 KB de CSS* |
| **indices** | **medidos**: ***1** en el catalogo (DuckDB, sobre `buscable`) **y 4** en Postgres* |
| **cargas** | *por medir: cuantas peticiones hace una pantalla al abrirse* |

**Cuatro de cinco.** *Y la que queda -- las **cargas** -- es del navegador y **no depende de ninguna decision**.
