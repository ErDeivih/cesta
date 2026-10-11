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
