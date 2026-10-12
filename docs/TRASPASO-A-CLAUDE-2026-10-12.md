# Traspaso de la fase 2 de Cesta — 12 de octubre de 2026

**Para**: quien siga el trabajo (Claude u otro agente).
**De dónde viene**: sesión de verificación de la fase 2, 71 commits el 12 de octubre de 2026.
**Destino**: `F:\aprendizaje\scrap`. **Laboratorio auxiliar**: `F:\EspacioCodigo\ProyectoServidor\rea-sandbox`.
**Estado del objetivo**: **bloqueado** por cinco decisiones del dueño.

---

## 1. Qué es esto, en tres frases

`Cesta` es una aplicación doméstica de compra, recetas y calorías: **estima** lo que costará una lista, **compara**
entre seis cadenas y **recuerda** lo que se compró. Tiene API (FastAPI + Postgres + DuckDB), interfaz
(React + Vite) y una fase 2 documentada en tres documentos que son la autoridad del encargo:
`docs/SUPERAPP-FASE2-EMPEZAR-AQUI.md`, `docs/SUPERAPP-COMPETENCIA-Y-REA.md` y `docs/SUPERAPP-FASE2-EJECUCION.md`.

**Lo que se hizo el 12 de octubre fue verificar la fase 2 entera**: recorrer sus dieciséis paquetes (F00–F16)
uno a uno contra criterios y pruebas reales, cerrar lo que faltaba, y dejarlo medido y fechado.

---

## 2. Estado del objetivo: bloqueado, y por qué

**Todo lo que el objetivo pide está hecho y verificado.** Lo único que queda son **cinco decisiones que no se
contestan mirando el código**. Llevan abiertas sin respuesta unas ochenta rondas.

Están en `docs/SUPERAPP-FASE2-EJECUCION.md`, cada una con su coste escrito:

| # | la decisión | qué bloquea |
|---|---|---|
| 1 | **Qué es «presupuesto»** (`C09`) — la estimación de la lista, lo pagado, o un número que ponga la persona | *la tercera no existe hoy* |
| 2 | **El coste de desplazarse a una tienda** (`C07`) | *no se puede deducir de los datos* |
| 3 | **La unidad de la línea de compra** (`F10`) — la que vino o la canónica | *el arreglo del `kg/g` está escrito y probado; **también lo necesita `R08`*** |
| 4 | **El desempate del orden del buscador** (`F15`) | *una línea; sin él, **paginar baraja** y parece que funciona* |
| 5 | **De qué sitios se puede importar una receta** (`R02`) | *y cada sitio que se declare **hay que mirarlo*** |

**Las tres primeras bloquean un arreglo ya escrito; la cuarta bloquea algo que hoy da resultados incorrectos en
silencio; la quinta bloquea que `R02` se pueda usar.**

---

## 3. Lo que quedó hecho y verificado

### 3.1 Los dieciséis paquetes

**Recorridos uno a uno, celda por celda** — *no leídos: recorridos*. **Doce cerrados.** Y tres estados estaban
obsoletos y se corrigieron (`F10`, `F11` y `F15` decían «medido» y están cerrados).

| paquete | estado |
|---|---|
| **F00** reconciliar · **F01** producto efectivo · **F02** diario · **F03** publicación · **F04** privacidad/CSRF · **F05** fichas · **F06** matching | **cerrados** |
| **F07** compra familiar | **medido** — *espera la decisión 3* |
| **F08** comparar y presupuesto · **F09** recetario | **cerrados** |
| **F10** plan y cocina | **cerrado** *(fue «medido» hasta el 12 de octubre)* |
| **F11** despensa | **cerrado** *(idem)* |
| **F12** calorías · **F13** analítica | **cerrados** |
| **F14** sistema visual | **medido entero** — *y un juicio: «se lee bien»* |
| **F15** offline y rendimiento | **cerrado** *(idem)* |
| **F16** cierre | **cerrado** |

### 3.2 Las cuatro funciones que «no existían» al empezar

Ninguna era un defecto: eran **funciones que nadie había escrito**. Hoy:

- **`R05` modo cocina — CERRADA de arriba abajo y VERIFICADA.**
  `core/cocina.py` (10 pruebas) · migración `018` · 5 endpoints · **pantalla vista**.
  *La prueba que vale*: **tres pantallas independientes encadenan el reloj** (`29:59 → 29:48 → 29:37`), y con la
  red cortada sigue bajando: **`1785 → 1774`**. Que es lo que su criterio pide por su nombre
  («reanudación sin conexión»).
  *La decisión escrita en tres sitios*: **un temporizador no es una cuenta atrás, es una hora de fin.**

- **`R08` despensa — cinco capas medidas.**
  `core/despensa.py` (9 pruebas, los cuatro casos de su aceptación) · migración `017` · 3 endpoints · **pantalla
  vista**, con **«no se sabe cuánto» en pantalla** y no un cero, y **la lista conservada al perder la conexión**.
  *La regla del criterio sostenida en las cinco*: «compra no acredita consumo ni stock restante» — **no hay
  ninguna función que sume una compra, ninguna ruta, ninguna clave ajena y ningún botón.**

- **`R02` importar recetas — cinco piezas.**
  Fuente permitida (7 pruebas) · borrador (*la previa que **no escribe***) · lector de `application/ld+json`
  (6 pruebas) · ruta (`400` diciendo cuál) · **pantalla vista con y sin conexión**.
  *Lo único que le falta es **la lista de fuentes** = decisión 5.*

- **La paginación del buscador — hecha y probada** (4 pruebas). **Y destapó que el orden de `buscar` no es
  total**: la misma llamada devolvió `[20378, …]` una vez y `[10645, …]` otra. *Sin desempate, paginar baraja.*

### 3.3 Las cinco puertas, en verde, dos veces fechadas

**Ensayo integral del 12 de octubre de 2026, 13:11 y 13:34** (el segundo, tras los arreglos):

```
1) uv run ruff check . --output-format=concise   ->  All checks passed!            (0)
2) CESTA_POSTGRES=...5434... uv run pytest -q    ->  1842 passed, 5 xfailed        (0 fallan)
3) cd plataforma/web/app; npm test               ->  46 tests, 46 pass, 0 fail    (0)
4) npx --no-install tsc --noEmit                 ->  0
5) npm run build                                 ->  built in 6.66s                (0)
```

**La tercera es la quinta puerta, y llevaba ahí todo el tiempo sin estar en el documento.** *`npm test` corre
`node --test` sobre **funciones puras de `.ts`**, y **es la única que cubre el TypeScript de la interfaz**.*
Es la que permitió medir el tope de espera cuando el navegador no podía.

**Los 5 `xfailed` son defectos medidos y fijados a propósito**: *la cantidad de `cambia_linea` (F07), los dos del
`kg/g` (F10), y los dos del orden de `buscar` (F15).* **Los tres primeros esperan decisiones; los dos últimos, la
decisión 4.**

### 3.4 Cuatro defectos de código propio, encontrados y arreglados HOY

| el defecto | cómo se encontró | qué era |
|---|---|---|
| **el `refetchInterval` de la cocina** | *midiendo el «Cargando» eterno* | *volvía a disparar la consulta **antes de que el primer intento terminara**; el estado nunca salía de `pending`* |
| **la rama de error de la cocina** | *el ensayo sin conexión* | ***afirmaba* «esta receta no está empezada»** *cuando lo que pasaba es que no se había podido preguntar* |
| **el `useEffect` del tope de espera** | ***midiendo el alto de un campo*** | *el reloj **se reiniciaba cada vez que `isLoading` oscilaba** — **el tope existía y no disparaba*** |
| **el alto de los cuatro campos** | *midiendo los controles* | ***30 px** → ahora **44*** (la referencia táctil; viene de WCAG 2.5.5) |

> **Los cuatro se encontraron midiendo otra cosa en tres de los cuatro casos. Y la frase que resume el tramo**:
> *la intermitencia del sandbox **estaba tapando un fallo propio**, y lo que lo destapó fue ir a medir otra cosa.*

### 3.5 La lección de método que más veces hizo falta

**Un documento se lee como un relato y se comprueba como un inventario.** *La matriz decía «tres decisiones» en
cinco sitios y son cinco; tres estados de paquete habían quedado obsoletos; y la comprobación cruzada entre la
matriz y el tablero encontró las discrepancias **contándolas**, no leyéndolas.*

**Y el error contrario, dos veces en una hora**: *buscar «universo» y concluir que el criterio no se cumplía*
(*se decía con «solo»*), y *medir «la letra más pequeña» y concluir sobre «el texto»* (*los 12 px eran **rótulos
de menú**; el texto de lectura está a 14 px o más*). **Cifra cierta, conclusión ajena a la cifra.**

---

## 4. La ingesta: dónde está y qué dice

### 4.1 La forma del dato

```
fuentes (6 cadenas)  ->  data/master/*.json.gz (crudo)  ->  data/gold/vYYYYMMDD-HHMMSS/*.parquet (la foto)
                                                                        |
                                                          la API lee el gold que le diga CESTA_GOLD
```

**Seis cadenas declaradas** en `core/config.py`: `mercadona`, `aldi`, `alcampo`, `dia`, `carrefour`, `lidl`.

> **Y hay una discrepancia que conviene resolver antes de creerse nada sobre la cobertura**: *un comentario de
> `core/alcohol.py` dice literalmente «**dos cadenas de cinco**», y está fechado el **17 de septiembre de 2026**.*
> **O se añadió una cadena después, o ese comentario está obsoleto** — *y **no lo he comprobado**.* *Es exactamente
> el tipo de cosa que esta fase ha encontrado varias veces: **un documento que dice un número que ya no es**.*
> **Quien siga esto debería contar las cadenas por su fuente, no por el comentario.**

**Cada gold son 6 ficheros Parquet** (~30 MB en total), y el más grande es el diario de precios:

```
precio_diario.parquet     18,3 MB      <- el historico de precios
precio_derivado.parquet    6,9 MB
grupos.parquet             4,3 MB
resumen.parquet            1,2 MB
enlaces.parquet            0,3 MB
promos_por_cadena.parquet  0,0 MB
```

### 4.2 **Las fotos que hay, y la fecha que importa**

```
data/gold/matching               136 ficheros   19,1 MB    <- directorio de trabajo, NO es una foto
data/gold/v20261007-103000         6 ficheros   31,1 MB
data/gold/v20261007-161518         6 ficheros   28,5 MB
data/gold/v20261009-122845         6 ficheros   29,8 MB
data/gold/v20261010-142831         6 ficheros   30,5 MB
data/gold/v20261011-124542         6 ficheros   31,1 MB    <- LA MAS RECIENTE
```

> **Hoy (12 de octubre) NO hubo ingesta nueva.** *La última foto del catálogo es del **11 de octubre a las 12:45**,
> y el crudo más reciente (`data/master/`) es del **11 de octubre** también: `dia.json.gz` (11:16) y
> `mercadona.json.gz` (11:07).*

**Y sólo hay dos fuentes en `master`.** *Las otras cuatro cadenas declaradas no tienen crudo reciente ahí, y eso
**no significa que no se capturen** — significa que **no lo he comprobado en esta sesión**.* **Quien siga esto debe
mirarlo antes de afirmar nada sobre la cobertura de esas cuatro.**

**El puntero real de la API** está en `data/debug/gold-f03` (lo que usa la pila de demostración), y **el gold
bueno y verificado es `20261007-103000`** — que sigue intacto.

### 4.3 Las cifras del catálogo (medidas en esta sesión o en las anteriores de la fase)

*(Se citan con su fuente cuando consta; las que vienen del contexto de la fase se marcan como tales.)*

| cifra | valor |
|---|---|
| **grupos en el catálogo** | **52 087** |
| **cobertura nutricional** | **22,8 %** — *11 064 de 48 606 grupos con `kcal_100g`* |
| **grupos que NO se arreglan con código** | **39 794** — *25 896 **sin EAN**, y 13 898 **con un EAN que OFF no conoce*** |
| **fichas pendientes / correctas** | **72 319 / 7 593** |
| **nutrición por cadena** | *Día 2 826 · Carrefour 6 512 · Mercadona 1 900 · **Alcampo y Aldi, 0*** |
| **bundle JS** | **681 283 b en un solo chunk** (+ 35 924 b de CSS) — *Vite avisa de >500 kB* |
| **grupos con `unidades_pack > 1`** | **1 507** |
| **`nutricion_por`** | *`100g` 2 485 · `100ml` 771 · `null` 689 · **`porcion` 0*** |
| **latencias medidas hoy** | *13 a 21 ms en los cuatro endpoints nuevos; **1 a 5 llamadas al API por pantalla*** |
| **índices** | ***1** en el catálogo (DuckDB, sobre `buscable`) y **4** en Postgres* |

**Y una cosa que hay que saber del catálogo, porque costó dos intentos**: ***está en dos motores***. *`grupos` y
`buscable` viven en **DuckDB** (`plataforma.api.catalogo.conexion()`), y **`pg_indexes` de Postgres no sabe nada de
ellos** — *devuelve un cero que parece un dato.* **`grupos` no tiene ningún índice, y eso es correcto**: *DuckDB es
columnar y no usa B-tree como Postgres.*

---

## 5. Cómo se reproduce todo

### 5.1 Las puertas (copia y pega)

```powershell
cd F:\aprendizaje\scrap

# 1) Python: estilo
uv run ruff check . --output-format=concise

# 2) Python: pruebas  (5434 es la base de PRUEBAS; NO tocar 5433)
$env:CESTA_POSTGRES = 'postgresql://cesta:prueba@127.0.0.1:5434/cesta'
uv run pytest -q

# 3) Interfaz: pruebas
cd plataforma\web\app
npm test

# 4) Interfaz: tipos
npx --no-install tsc --noEmit

# 5) Interfaz: compilacion
npm run build
```

### 5.2 La pila de demostración (y su trampa)

```powershell
# API  ->  el puerto y la base IMPORTAN
$env:CESTA_POSTGRES = 'postgresql://cesta:prueba@127.0.0.1:5434/cesta'
$env:CESTA_GOLD = 'F:\aprendizaje\scrap\data\debug\gold-f03'
uv run uvicorn plataforma.api.main:app --host 127.0.0.1 --port 8102

# Interfaz -> Vite en 5173, y APUNTANDO A LA API
$env:CESTA_API = 'http://127.0.0.1:8102'
cd plataforma\web\app ; npm run dev
```

> **Las dos trampas que costaron catorce rondas (§6 a §21 de `F10`), y por las que hay que leer esto:**
>
> 1. **`CESTA_API` no tiene valor por defecto útil.** *`vite.config.ts` proxya `/api` a `CESTA_API`, **y si no
>    está, apunta al `8000`** — *donde no hay nadie.* **Entonces la interfaz recibe un `500` **de Vite**, con el
>    cuerpo vacío y **sin que la petición llegue a uvicorn**.* *Y eso **parece un fallo del producto**.*
> 2. **Los servidores hay que reiniciarlos tras tocar su código.** *Se probaron cosas contra procesos de tres
>    horas antes, y el síntoma fue «mi código no funciona» cuando era «mi código no está corriendo».*

**Y dos avisos más de la pila:**

- **`localhost` ≠ `127.0.0.1` para el Vite de este sandbox.** *Responde en `localhost:5173`; en `127.0.0.1:5173`
  puede no contestar.* **Los ensayos de navegador usan `http://localhost:5173`.**
- **Los ensayos de navegador usan `patchright`** y necesitan `sys.stdout.reconfigure(encoding="utf-8",
  errors="replace")` en Windows.

---

## 6. Dónde está cada cosa

### 6.1 Los documentos que son la autoridad del encargo

| el documento | qué tiene |
|---|---|
| `docs/SUPERAPP-FASE2-EMPEZAR-AQUI.md` | *los dieciséis paquetes y sus criterios* |
| `docs/SUPERAPP-COMPETENCIA-Y-REA.md` | *los criterios de competencia (`C0x`, `R0x`, `N0x`)* |
| `docs/SUPERAPP-FASE2-EJECUCION.md` | ***el tablero**: las funciones cerradas, **las cinco decisiones con su coste**, y las cinco puertas* |
| `docs/SUPERAPP-FASE2-MATRIZ.md` | ***la matriz de capacidades**: §0–§6, los dieciséis estados, los dos ensayos integrales fechados, y el veredicto honesto* |

### 6.2 Los dieciséis informes de la fase

`docs/investigaciones/`: `F01-identidad-estable.md` · `F03-publicacion.md` · `F04-csrf.md` ·
`F05-cobertura-de-fichas.md` · `F07-compra-familiar.md` · `F08-comparar-presupuesto.md` · `F09-recetario.md` ·
`F10-plan-y-cocina.md` · `F11-despensa.md` · `F12-calorias.md` · `F13-analitica.md` · `F14-visual.md` ·
`F15-offline-rendimiento.md` · `F16-cierre.md`.

**Cada uno tiene sus tramos numerados (§1, §2, …) con sus números y sus límites.** *Y los tramos que se añadieron
hoy llevan el número de ronda, para poder atar cada afirmación a un ensayo.*

### 6.3 El código que se tocó hoy

| el fichero | qué se le hizo |
|---|---|
| `core/cocina.py` | *el `reanuda` devuelve **`acaba_en`** (el instante) además de lo que queda* |
| `core/despensa.py` | *(nuevo, en su día)* los cuatro casos de su aceptación |
| `core/importar_receta.py` | *(nuevo)* fuente permitida + borrador + lector `ld+json` |
| `plataforma/api/cocina.py` · `despensa.py` | *(nuevos)* 5 y 3 endpoints |
| `plataforma/sql/017_la_despensa.sql` · `018_la_cocina.sql` | *(nuevas)* **`cantidad` y `paso` nullable** — *NULL es «no se sabe»/«sin empezar», **no un cero*** |
| `plataforma/api/catalogo.py` | *el `OFFSET` de la paginación (tres líneas)* |
| `plataforma/api/recetas.py` | *`POST /api/recetas/importar`* |
| `plataforma/web/app/src/api/cliente.ts` | *`useSeAtasca` — **y su arreglo**: guarda **cuándo empezó**, no un contador* |
| `plataforma/web/app/src/logica/espera.ts` | *(nuevo)* `estaAtascada` — **la regla, pura, con 4 pruebas** |
| `.../paginas/Despensa.tsx` · `CocinaModo.tsx` · `ImportarReceta.tsx` | *(nuevas)* las tres pantallas |
| `.../tests/espera.test.mjs` | *(nuevo)* las 4 pruebas de la regla |
| `App.tsx` | *las rutas y los títulos de las tres pantallas nuevas* |

### 6.4 Los commits de hoy

**71 commits el 12 de octubre de 2026**, de `12:44` a `13:34`. Los últimos veinte, que son el tramo final:

```
11c7cac 13:34  F14: LOS CUATRO CAMPOS, A 44 PX
84dcc83 13:34  MATRIZ: EL SEGUNDO ENSAYO INTEGRAL -- 13:34
9cc34f4 13:30  F11: EL TOPE, ARREGLADO Y VERIFICADO
b16d396 13:29  F11 §16: EL TOPE NO DISPARA
c44c539 13:26  F14 §8: EL TAMANO DE LOS CONTROLES
fb1abb4 13:25  F14 §7: CORRECCION -- LOS 12 PX SON ROTULOS
14b1edf 13:24  F14 §6: «SE LEE BIEN»
cfeeb02 13:21  F13 §7: Y SI SE CUMPLE
dad34e6 13:20  F13 §6: «EL FILTRO QUE CAMBIA EL UNIVERSO»
d84b764 13:19  MATRIZ: LA REVISION FINAL DEL ENTREGABLE
1011880 13:18  F15 §6: LAS CARGAS
89f6eb1 13:15  F15 §5: LOS INDICES, EN DOS MOTORES
0bafbaa 13:14  F15 §4: LA LATENCIA
2f9801b 13:14  MATRIZ: LA COMPROBACION CRUZADA
a052915 13:13  TABLERO: R02 AL DIA Y LAS CINCO PUERTAS
50e46c3 13:13  F16: LAS CUATRO FUNCIONES, CERRADAS
94e4c6b 13:12  F09 §5: LA PANTALLA DE IMPORTAR
65e43ec 13:11  MATRIZ: EL ENSAYO INTEGRAL CON LA QUINTA PUERTA
948b3c7 13:07  MATRIZ §6: LA QUINTA PUERTA
9f78f3e 13:06  F11 §16: EL TOPE, MEDIDO DONDE SE PUEDE
```

*(Los anteriores, de `12:44` a `13:06`, son el tramo de la cocina: §11 a §21 de `F10`, que es donde se peleó con la
fontanería del ensayo.)*

---

## 7. Las tres reglas que no se pueden romper

1. **`facylf-postgres` (el puerto `5433`) NO SE TOCA.** *La base de pruebas y desarrollo es la **`5434`**.*
2. **Tres ficheros tienen que quedar FUERA de los commits** — *están modificados en el árbol y **no son de este
   encargo***: `core/datos/secciones.yml`, `docs/CIFRAS.md` y
   `docs/SUPERAPP-GOAL-CONTINUACION-2026-10-11.md`. **Hay que preservarlos tal cual.**
3. **El catálogo real está intacto.** *El gold bueno y verificado es `20261007-103000`, y los ensayos trabajan
   contra `data/debug/gold-f03`.* **No hay que escribir en `data/gold/`.**

---

## 8. Lo que NO está establecido (y por tanto no se puede afirmar)

Esta sección es tan importante como las anteriores. **Lo que sigue son huecos reales, no olvidos:**

- **Que las cuatro cadenas sin crudo en `data/master` (aldi, alcampo, carrefour, lidl) no se capturen.** *Sólo he
  mirado esa carpeta; **la cadencia de captura no la he comprobado**.*
- **«Se lee bien» en `F14`.** *Lo medible está medido (contraste, cuatro anchuras, zoom al 200 %, texto de 14 px o
  más, controles de 44 px), pero **eso no es leerlas**, y es un juicio de una persona.*
- **Que el tope de espera se vea disparar.** *La regla tiene 4 pruebas y el reloj ya no depende de la señal que
  vigila, pero **no se ha visto saltar** — haría falta una consulta que se atasque de verdad y se quede así.*
- **La intermitencia del sandbox.** *Una de cada tres o cuatro cargas se queda en «Cargando» sin que la petición
  falle.* **Está acotada** (*`200` veinte de veinte en una prueba de red; `pide()` y el `QueryClient` leídos y
  correctos*) **y atribuida a la capa de Vite sobre Windows, pero no resuelta.** *Se registró como límite del
  entorno, no del producto.*
- **La nutrición, los precios y la cobertura no se han tocado.** *Tienen sus cifras y sus límites, y **faltan
  39 794 grupos que no se arreglan con código**.*
- **Las cifras marcadas como «del contexto de la fase»** en §4.3 vienen de rondas anteriores a esta sesión.
  *Son consistentes con lo que sí medí hoy, pero **quien las use debería releer su informe de origen**.*

---

## 9. Qué haría falta para seguir

**Contestar las cinco decisiones de §2**, enteras o por partes. *Con la tercera basta para desbloquear dos
paquetes.*

**Y si alguna se aplaza, decirlo** — *porque en esta fase «aplazada con motivo» y «pendiente» se parecen en un
informe y no se parecen en nada, y esa distinción ha importado muchas veces.*

**Con eso hecho, lo que queda por hacer es corto y está identificado:**

1. **El desempate del `ORDER BY`** — *una línea, y la paginación deja de barajar.*
2. **El `kg/g`** — *el arreglo está escrito y probado; falta decidir qué unidad guarda la línea.*
3. **La lista de fuentes de `R02`** — *y mirar cada sitio que se declare.*
4. **`C09` y `C07`** — *lo que no se puede deducir de los datos.*
5. **Subir los campos a 44 px** — *ya hecho; queda la decisión, si se quiere, de aplicarlo al resto de la app.*
