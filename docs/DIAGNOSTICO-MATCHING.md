# DIAGNÓSTICO DEL MATCHING — Fase 0

> Informe de la Fase 0 de `docs/PLAN-UI-MATCHING.md`. **Solo mide: no cambia
> nada.** Todos los números salen del catálogo de gold del **21 de septiembre de
> 2026** (52.661 productos) y se reproducen con dos comandos.
>
> Fecha del informe: 2026-09-22 · Raíz: `F:\aprendizaje\scrap`

## Cómo se reproduce

```powershell
uv run python -m projects.cesta.diagnostico_matching --json   # el informe
uv run python -m projects.cesta.emparejar --medir             # el 57 %
uv run pytest tests/test_diagnostico_matching.py -q           # 11 pruebas
uv run python -m projects.cesta.verificar_docs
```

Lo primero escribe `data/gold/diagnostico_matching.json` además de imprimirlo. Lo
segundo es la medición que ya existía en el proyecto (esconde el EAN y empareja
por nombre). Nada más se escribe.

Estado de aceptación del proyecto tras esta fase: **11 pruebas en verde, `ruff`
limpio, `verificar_docs` en verde y `--medir` = 57 %**, que es exactamente el
listón que `docs/FASES.md:518-521` y `docs/BACKLOG.md:141` fijan como mínimo que
no se puede bajar.

---

## 0. Resumen para decidir

Cinco frases, y el resto del documento son las pruebas.

1. **El matching no falla donde el plan cree.** De los 784 pares que sabemos
   ciertos por código de barras y el nombre no encuentra, **504 (64 %) se caen
   antes de que el algoritmo opine**: el formato es ilegible (287) o las dos
   cadenas lo venden en otra unidad (172) o en otra cantidad (45). Solo 158
   (20 %) son de puntuación y **122 (16 %) son de asignación**, que es justo lo
   que arregla el algoritmo húngaro. El clasificador es lo último, no lo primero.
2. **Los dos vetos duros del plan borrarían aciertos y ningún error.** De los 266
   enlaces con unidad distinta, **los 266 son el mismo producto** (mismo EAN). El
   problema es el dato de unidad, no el emparejamiento. Y el proyecto **ya había
   decidido esto**: `docs/MODELO.md:42-45` y `docs/PRECIO-POR-UNIDAD.md:29-49`
   dicen que en un grupo manda **una** unidad pero los productos de otra unidad
   **se quedan dentro**.
3. **El umbral de precio del plan (60 %) es 18 veces más estricto que el del
   proyecto.** `core/comparacion.py:28` marca `dudoso` a partir de
   `FACTOR_INCREIBLE = 30` (30×) porque hay ahorros reales de 28×. Con el 60 %
   saldrían 3.191 enlaces sospechosos; con el criterio del proyecto, **13**.
4. **El plan se contradice con documentos del dueño, y el plan dice que ganan
   ellos.** `docs/APP.md:320-331` decide *"nada de framework pesado… sin
   framework… gráfica SVG a mano"* y `docs/API.md:336` decide que FastAPI
   **"no sirve HTML. Eso es Caddy"**. El §7 del plan hace exactamente lo
   contrario en las dos cosas. Hay que decidir antes de escribir una línea de
   React.
5. **No hay control de versiones.** `F:\aprendizaje\scrap` **no tiene `.git`**
   (comprobado; `docs/AUDITORIA.md:36` ya lo dejaba escrito). Antes de tocar el
   emparejador y migrar el front, esto es la decisión número uno.

---

## 1. Qué hay hoy

| | |
|---|---:|
| productos en el catálogo | **52.661** |
| grupos | **39.149** |
| grupos de un solo producto | 32.693 |
| grupos con ≥2 cadenas (**comparables**) | **6.431** |
| productos dentro de un grupo comparable | **19.902** (37,8 % del catálogo) |
| productos sin cantidad o sin unidad ("bloque `?`") | 8.494 |

Reparto de cadenas por grupo: 2 cadenas **4.109**, 3 cadenas **1.452**,
4 cadenas **602**, 5 cadenas **268**.

Dos detalles pequeños que ensucian las cuentas:

- **1.320 grupos comparables** tienen a la misma cadena repetida dentro. O son
  dos variantes que no se debían juntar, o el grupo está de más.
- **25 grupos** tienen varios productos y **una sola cadena**: comparan cero.

El grupo más grande tiene 52 productos; hay 110 grupos de más de 10.

Coincide con `docs/CIFRAS.md` (52.661 / 6.431) y con `verificar_docs`, que da
verde: las dos fuentes están de acuerdo.

---

## 2. El tope alcanzable

### 2.1 El tope del EAN no sirve para medir el objetivo

| | |
|---|---:|
| productos con código de barras | 25.544 (48,5 %) |
| EAN distintos presentes en ≥2 cadenas | 1.610 |
| **pares entre cadenas con el mismo EAN** | **1.821** |
| de esos, hoy en el mismo grupo | 1.821 (**100 %**) |
| de esos, unidos por un enlace directo | 1.802 (99 %) |

Por par de cadenas: carrefour/dia 1.449 · dia/mercadona 208 ·
carrefour/mercadona 164. **Alcampo y Aldi no aportan ni un par con EAN
compartido**, que es lo que ya avisaba `docs/PARIDAD-CAMPOS.md:90-100`.

Dos consecuencias:

1. El "100 % del tope EAN" **no es un logro, es una tautología**: el emparejador
   enlaza por EAN con parecido `1.0` (`core/matching.py:247-255`), así que esos
   pares acaban siempre en el mismo grupo. Ese tope **no mide recall**.
2. El EAN sirve para lo que sí es oro: **esconderlo y comprobar si el nombre
   encuentra el par** (§4), y como **sonda de precisión** (§3).

### 2.2 El tope que sí importa: el bloque canónico

El proyecto existe para comparar la marca blanca de una cadena con la de otra, y
eso no tiene EAN común. El techo real se mide agrupando por la clave de bloqueo
que propone el plan — **(sección, unidad canónica, cantidad)** — y contando
cuántos productos caben en un bloque con ≥2 cadenas:

| | |
|---|---:|
| bloques con ≥2 cadenas | **1.584** |
| productos que caben en alguno (techo alto) | **40.183** (76,3 %) |
| pares 1-a-1 máximos que se podrían formar | **30.725** |
| productos comparables **hoy**, dentro de grupos | **19.902** = **50 % del techo** |

Es un **techo optimista**: compartir sección, unidad y cantidad no garantiza que
sean el mismo producto (un bloque como `despensa/kg/1.0` mete cientos de cosas
distintas; la asignación 1-a-1 dentro del bloque es la que decide). Pero es la
referencia honesta: **hoy estamos a la mitad, y el otro 50 % no se pierde por el
clasificador, se pierde por el bloqueo y por la asignación.**

---

## 3. Lo que está mal hoy, con números

El emparejador aceptó **18.129 enlaces** (6.034 `identico`, 12.095
`equivalente`). Medidos contra las señales duras:

| señal | enlaces | % del total |
|---|---:|---:|
| mismo EAN (acierto demostrable) | 2.807 | 15,5 % |
| EAN distinto en los dos lados | 3.432 | 18,9 % |
| con EAN en los dos lados | 6.239 | 34,4 % |
| unidad canónica distinta | 266 | 1,5 % |
| precio por unidad difiere **>60 %** | 3.191 | 17,6 % |
| sección distinta | 4.330 | 23,9 % |
| misma marca y dos EAN distintos | 373 | 2,1 % |

**El "precio/unidad difiere >60 %" del plan no es una señal de error.** La misma
medición con el criterio que el proyecto ya usa (`FACTOR_INCREIBLE = 30`,
`core/comparacion.py:28`), sobre los 17.789 enlaces con precio comparable en los
dos lados y la misma unidad:

| umbral | enlaces | % |
|---|---:|---:|
| >1,6× (el del plan: "más de un 60 %") | **3.191** | 17,9 % |
| >3× | 520 | 2,9 % |
| >10× | 60 | 0,3 % |
| >30× (el del proyecto) | **13** | 0,1 % |

`docs/PRECIO-POR-UNIDAD.md:114-141` lo dejó medido: **por debajo de 30× los
ahorros son reales** (hay 28× comprobados). Marcar como sospechoso todo lo que
pase de 1,6× convertiría en "error" el 17,9 % de los aciertos, o sea justo la
mitad del valor del comparador. Además hay que respetar `precio_comparable`
(223 filas en `false`).

A nivel de grupo:

| | grupos |
|---|---:|
| grupos con dos EAN distintos dentro | 2.233 (todos comparables) |
| de esos, con la **misma marca** | **316** (1.096 productos) |
| grupos comparables con unidad mixta | 238 |
| grupos comparables con sección mixta | 2.039 (1.744 sin pasillos transversales) |

### 3.1 Grupos demasiado anchos (el bloqueo nº 1 del BACKLOG)

El BACKLOG §2 dejó escrito que había **405 grupos con más del 200 % de
dispersión**. Hoy, contando solo grupos donde comparar precios significa algo
(kg/l/m) y con ≥2 precios:

| el más caro cuesta… | grupos |
|---|---:|
| más del 200 % que el más barato | **364** |
| entre 100 % y 200 % | 592 |
| entre 50 % y 100 % | 792 |
| menos del 50 % | 3.957 |
| **total con precio comparable** | **5.705** |

Han bajado de 405 a 364, pero siguen siendo **1 de cada 16 grupos**. El criterio
del BACKLOG pide llegar a menos de 150 sin bajar del 57 % de aciertos.

### 3.2 La etiqueta `identico` miente en el 30 % de los casos comprobables

`nivel()` (`core/matching.py:352`) llama `identico` a un par cuando comparten
**marca**, aunque los códigos de barras sean distintos. Medido con
`emparejar --medir`:

```
de los enlaces marcados 'identico' con EAN en ambos lados,
1033 de 1475 comparten codigo (70 %)
```

De 1.475 enlaces que el propio código etiqueta como "el mismo producto" y donde
los dos traen código de barras, **442 no lo comparten**. No es un problema de
datos: es un fallo de la definición. Un código de barras distinto es otro
producto.

---

## 4. Por qué falla: los 784 pares ciertos que el nombre no encuentra

Escondiendo el EAN, el emparejador por nombre encuentra **1.037 de 1.821 (57 %)**
— justo el 57 % que el BACKLOG §2 fijó como listón que no se puede bajar. Los
784 que se le escapan fallan por una de estas cinco razones, y **cada una se
arregla en un sitio distinto del plan**:

| motivo del fallo | pares | % |
|---|---:|---:|
| **formato ilegible** en alguno de los dos | **287** | 37 % |
| **una cadena lo vende en otra unidad** | **172** | 22 % |
| mismo formato y por debajo del umbral | 158 | 20 % |
| **puntuó por encima del umbral y perdió la elección mutua** | **122** | 16 % |
| misma unidad, cantidad distinta (pack frente a unidad) | 45 | 6 % |

De los que fallan por umbral, el parecido mediano es **0,48** (máximo 0,55,
mínimo 0,08): bajarlo de 0,55 a 0,48 recuperaría unos pocos y metería el ruido
de "aceite de oliva" contra "aceite de coco", que es justo lo que el umbral está
evitando.

**Lectura: 504 de los 784 fallos (64 %) no son del clasificador.** Son de
bloqueo y de dato (287 + 172 + 45), y otros **122 (16 %) son de asignación**:
pares que puntúan por encima del umbral y pierden porque un tercer producto se
lleva al candidato. Ese es literalmente el problema que resuelve el **algoritmo
húngaro**. Solo 158 (20 %) son de puntuación, que es donde el plan pone todo el
peso (Splink, LightGBM, embeddings).

Orden que se deduce: **asignación y dato primero, clasificador después.**

---

## 5. Dos hallazgos que cambian el plan (y dos decisiones que ya existían)

El plan (§5, etapas 1 y 5) propone dos **vetos duros**: no comparar nunca cosas
de distinta unidad canónica, y no aceptar un par si la categoría de nivel 1
difiere. Medido hoy, **los dos borrarían aciertos y ningún error**:

```text
enlaces con unidad distinta:  266,  de ellos con el MISMO EAN:  266  (100 %)
enlaces con seccion distinta: 4330, de ellos con el MISMO EAN:  667
```

**Los 266 enlaces con unidad distinta son, los 266, el mismo producto.** No hay
uno solo que sea un falso positivo. Lo que está mal es el dato de unidad:

| A | B | qué pasa |
|---|---|---|
| Desodorante roll-on Dry Comfort Nivea 50 ml [carrefour] → `1.0 ud` | el mismo, EAN `4005900388513` [dia] → `0.05 l` | Carrefour declara "1 unidad" de un bote de 50 ml |
| Snack dental Frolic Smiley Sticks 175 g [carrefour] → `? ud` | el mismo, EAN `5998749121092` [dia] → `0.175 kg` | Carrefour no trae formato |
| Vino Viña Albali 75 cl [carrefour] → `? ud` | el mismo, EAN `8410702000017` [dia] → `0.75 l` | ídem |

Lo mismo con la sección: 667 enlaces que sabemos ciertos por código de barras
tienen secciones distintas, y mirando los casos se ve por qué — **la sección es
el pasillo de cada cadena, no una taxonomía del producto**:

```text
Pizza carbonara Casa Tarradellas 400 g   [carrefour] despensa   <-> [dia] preparados
Mezcla para sofrito Verleal 400 g        [carrefour] congelados <-> [dia] frutas-verduras
Levadura de panadería Maizena            [carrefour] despensa   <-> [dia] panaderia
Azúcar blanco en azucaritos Azucarera    [carrefour] desayuno   <-> [dia] panaderia
Filetes de melva en aceite Ubago 85 g    [carrefour] despensa   <-> [dia] pescaderia
```

Mismo producto, mismo nombre, mismo formato, dos pasillos distintos.

### 5.1 Esto no es una opinión mía: el proyecto ya lo decidió

| documento | lo que ya está decidido |
|---|---|
| `docs/MODELO.md:42-45` | en un grupo manda **una** unidad; los productos en otra unidad **siguen dentro del grupo** |
| `docs/PRECIO-POR-UNIDAD.md:29-49` | `comparacion_fiable` es "el campo más importante": `ud` no se compara entre cadenas, pero **no se expulsa** a nadie del grupo |
| `docs/PRECIO-POR-UNIDAD.md:114-141` | hasta 30× (`FACTOR_INCREIBLE`) el ahorro es **real**; por encima, el grupo se marca `dudoso` y **no se da cifra**, no se rompe |
| `docs/PRECIO-POR-UNIDAD.md:18-25` | de 2.680 enlaces con el mismo EAN, **92 (3,4 %) tienen precios por unidad a más de 10×**: el precio es una pista **débil**, no una verdad |
| `docs/PRECIO-POR-UNIDAD.md:147-159` | medido y **descartado**: el `envase` (38 % de discrepancia) y `tipo_producto` no sirven para bloquear |

**Conclusión:** el veto tiene que ser **condicional**, no duro. Unidad y sección
sirven para *puntuar* y para *sospechar*; para descartar hacen falta tres cosas:
que el formato sea **fiable** (lo publica la cadena, no se dedujo del nombre), que
la contradicción sea **grande** (mucho más de 1,6×) y que el precio sea
`precio_comparable`. Como está escrito en el plan, el veto se lleva por delante
266 aciertos y 0 errores.

---

## 6. El dato de formato no aguanta el peso que el plan le quiere dar

Si la clave de bloqueo es `(sección, unidad, cantidad)`, el bloqueo vale lo que
valga `cantidad`. Medido cadena a cadena:

| cadena | productos | sin cantidad | en `ud` | `ud` = 1 | cantidad imposible |
|---|---:|---:|---:|---:|---:|
| alcampo | 23.776 | **4.527** | 814 | 85 | 2 |
| carrefour | 16.560 | **3.921** | 3.146 | **2.076** | 3 |
| dia | 5.808 | 0 | 590 | 147 | 35 |
| mercadona | 4.327 | 38 | 547 | 428 | 2 |
| aldi | 2.190 | 8 | 476 | 276 | 7 |

"cantidad imposible" = kg>25, l>25, ud>250, m>200 en un supermercado online.

- **8.494 productos (16 %) no tienen formato** y caen al bloque `("?",)`, que el
  emparejador **no recorre** (`core/matching.py:266`): solo pueden entrar por la
  segunda pasada, con el listón alto de 0,82. De ahí buena parte de los 287
  fallos por "formato ilegible".
- **Carrefour declara `1 ud` en 2.076 productos** cuyo tamaño real está en el
  nombre (el desodorante de 50 ml). Ese `1 ud` es **peor que no tener el dato**:
  bloquea contra lo que no debe.
- Hay cantidades absurdas que **envenenan el precio por unidad**, que es la señal
  que el plan quiere usar como pista fuerte:

| producto | lo que dice el catálogo | lo que es |
|---|---|---|
| POTE Azafrán molido 0,40 g [alcampo] | `0.4 kg` | 0,0004 kg → su precio por unidad sale **1.030 veces** más barato que el de DIA |
| Suavizante Flor 63 lavados [dia] | **`63.0 l`** | "63 lavados" leído como 63 litros |
| Filetes de dorada 300 g [dia] | `0.001 kg` | 1 gramo |
| Cartílago de tiburón 100 cápsulas [alcampo] | `0.055 kg` | el peso del bote, no del contenido |
| FLOR Suavizante 87 lavados [alcampo] | `1.392 l` | no es el contenido |

Cuando `cantidad` está mal, el **precio por unidad** está mal, y entonces la
señal "precio por unidad parecido ⇒ mismo producto" **miente**. Antes de apoyar
el clasificador en el precio hay que arreglar el formato. Y esto encaja con lo
que `docs/BACKLOG.md:730-733` ya vivió con los packs de Mercadona: "nuestra
deducción acertaba 169 y fallaba 1.087".

---

## 7. Qué hace hoy el matching

| pieza | dónde |
|---|---|
| algoritmo | `core/matching.py` → `enlaces()`, `agrupar()`, `Union`, `tokens`, `trigramas`, `bloque`, `nivel` |
| orquestación y escritura de gold | `projects/cesta/emparejar.py` → `main()`, `catalogo_actual()`, `_completa_cantidad()`, `medir()` |
| medición | `uv run python -m projects.cesta.emparejar --medir` |
| salidas | `data/gold/enlaces.parquet` (18.129 pares), `data/gold/grupos.parquet` (52.661 filas + `grupo_id`) |
| caché | `data/gold/enlaces_huella.json`: firma de la secuencia `(fuente, id_fuente)` del catálogo |

**Cómo funciona, en cinco líneas.** Trocea los nombres en palabras (con raíz,
sin ruido, con IDF) y en trigramas; el parecido de un par es el mejor de los dos
(dice ponderado por IDF, con los trigramas descontados un 15 %). Solo compara
dentro del mismo bloque `(unidad, cantidad)`. Exige **elección mutua**: `j` tiene
que ser el mejor candidato de `i` en su cadena y al revés. Los pares con el mismo
EAN se enlazan directamente con parecido 1,0. Los enlaces se juntan en grupos con
**union-find** (componentes conexas). Hay una segunda pasada sin bloque, solo
para productos que comparten una palabra rara (IDF ≥ 4), con listón 0,82.

**Decisiones ya documentadas en el propio código** (no son fallos, son frenos
medidos, y **no hay que deshacerlos sin medir**):

- `UMBRAL = 0.55` — bajarlo a 0,50 daba 55 % de acierto pero juntaba cosas que
  solo se parecen de nombre.
- Elección mutua en vez de componentes conexas — "con componentes conexas la
  precisión caía por debajo del 1 %" (`core/matching.py:204-208`).
- Dos elecciones separadas (una con marca, otra sin) — quitarlo bajaba el
  acierto del 53 % al 43 %.
- `CAMPOS_PARA_EMPAREJAR` reducido a seis columnas: pasar de 17 a 34 columnas
  llevó el emparejador de 79 s a más de 115 s (`docs/PRECIO-POR-UNIDAD.md:163-178`).
- Los enlaces son **pares de posiciones**, no de identificadores: por eso existe
  la huella. Es una fragilidad conocida (`docs/OPERACION.md:412-426`) que el
  modelo nuevo debe eliminar.

**Por qué falla, en una frase:** porque el 64 % de los pares que se le escapan se
caen antes de que el algoritmo opine (formato ilegible o unidad distinta), un 16 %
más se pierde en una asignación que no es global, y la etiqueta `identico` no
exige compartir código de barras.

---

## 8. Propuesta de modelo de datos (§6 del plan, ajustado a lo medido)

El plan propone cuatro tablas nuevas. Antes de crearlas hay que resolver un
choque real: `docs/MODELO.md:57-71` fija que **PostgreSQL son siete tablas y no
van a ser más**, que **no hay tabla de productos ni de precios**, y que
`grupo_id` es una referencia a gold **sin integridad referencial, a propósito**,
para poder migrar las listas si se rehace el emparejador. Y
`docs/API.md:334-335` fija que la plataforma **no escribe** en `data/gold`.

Con eso, lo propuesto vive **en gold (Parquet), no en Postgres**:

```text
producto            (producto_id PK, fuente, id_fuente, nombre, marca,
                     seccion, categoria_l1, categoria_l2,
                     cantidad, unidad_canon, cantidad_fiable BOOL,  -- NUEVO
                     ean, precio_cent, precio_unidad_cent, precio_comparable, ...)
                     UNIQUE (fuente, id_fuente)

precio_historico    (producto_id, fecha, precio_cent, precio_unidad_cent, disponible)

-- Un par, con todo lo necesario para explicarlo y reproducirlo.
equivalencia        (equivalencia_id, producto_a, producto_b,       -- a<b, canónico
                     metodo, confianza, peso, features JSON,
                     vetos JSON, ejecucion_id, creada)
                     UNIQUE (producto_a, producto_b, ejecucion_id)

grupo_producto      (grupo_id, nombre_canonico, seccion, cantidad, unidad_canon,
                     n_cadenas, n_productos, unidad_fiable BOOL,
                     precio_unidad_medio, dispersion, ejecucion_id)

matching_ejecucion  (ejecucion_id, fecha, version_modelo, version_codigo, umbral,
                     n_candidatos, duracion_s, metricas JSON)
matching_metrica    (ejecucion_id, metrica, valor, objetivo, cumple BOOL)
bloqueo_ejecucion   (ejecucion_id, clave, n_productos, n_cadenas, metodo)
```

Correcciones respecto al §6 del plan, todas obligadas por lo medido:

1. **`producto_id` estable, nunca posiciones.** `equivalencia` referencia
   `producto_id`, no índices. Es la lección de `_huella()` en `emparejar.py`.
2. **`cantidad_fiable BOOL`.** El bloqueo depende de un campo que a veces está
   mal (§6). Marcarlo es lo que permite que el veto de unidad sea condicional.
3. **No hay `categoria_canon`**: no existe en el proyecto
   (`docs/MODELO.md:49-53`). Lo único que hay es `seccion` (20 valores, 99,9 % de
   cobertura). El "árbol de categorías de 2 niveles" del plan §5 no tiene datos
   detrás.
4. **`matching_ejecucion` no duplica `core/runlog.py`** (`data/runs.csv`): aquel
   registra la ingesta por cadena; este, la pasada de matching. Se enlazan, no se
   solapan.
5. **`peso` y `confianza` son campos nuevos de verdad**: hoy en gold solo hay
   `parecido` (0-1) y `nivel`. El "peso" del plan (por miembro y ajustable por el
   usuario en la UI) **no existe en ningún documento del repo**: hay que
   definirlo, no heredarlo.

---

## 9. Orden de implementación propuesto

El plan propone EAN → bloqueo → Splink → húngaro → LightGBM. Los números del §4
dicen que **el dato de formato y la asignación valen más que el clasificador**,
así que se suben los dos. Y hay dos frenos escritos que respetan ese orden:

- `docs/AUDITORIA.md:73-78`: *"no introducir embeddings hasta tener varios
  cientos de pares EAN Mercadona-DIA como conjunto de validación"*.
- `docs/BACKLOG.md:462-464`: *"TF-IDF y regresión logística; ni se te ocurra una
  red neuronal con ese volumen"*.

Con 1.821 pares EAN y 1.610 EAN multicadena, **el conjunto de validación ya
existe** (la mitad Mercadona-DIA: 208), así que el freno de AUDITORIA se puede
levantar con números, no con ganas.

| # | Fase | Qué exactamente | Criterio de aceptación medido |
|---|---|---|---|
| 0 | Diagnóstico | este informe + `diagnostico_matching.py` + 11 tests | **hecho** |
| 1 | Modelo | tablas del §8, migrar los 18.129 enlaces y 6.431 grupos a `producto_id`, idempotente | reejecutar no duplica; los grupos actuales se reproducen |
| **2** | **Arreglo del dato de formato** | `cantidad_fiable`, deducir el formato del nombre donde falta (los 8.494), corregir los absurdos, quitar los `1 ud` falsos de Carrefour | sin formato: 8.494 → <2.000; enlaces con precio/unidad >3× : 520 → menos de la mitad; `--medir` **≥ 57 %** |
| 3 | Bloqueo | clave canónica + EAN + TF-IDF de n-gramas + ANN con embeddings pequeños (FAISS; GTX 1660 de 6 GB, compartida) | recall del bloqueo ≥ 95 % sobre el tope EAN; ≤ 200 candidatos por producto |
| 4 | **Asignación** | **húngaro** por par de cadenas dentro de cada bloque, con umbral; union-find + correlación-clustering | **0 conflictos** (hoy 1.320 grupos con la cadena repetida); se recuperan parte de los 122 pares que hoy pierden la elección mutua |
| 5 | Puntuación | Splink/Fellegi–Sunter con EM sobre DuckDB; features del plan (EAN, marca, sección **como débil**, cantidad, rapidfuzz, coseno, ratio de precio) | probabilidad calibrada por par + descomposición; `--medir` **sube** del 57 % |
| 6 | Grupos y representante | nombre canónico, peso por miembro, origen, `unidad_fiable` | ≥ 90 % de los grupos comparables con representante legible; grupos >200 % de dispersión: **364 → <150** (criterio del BACKLOG §2) |
| 7 | Métricas y versionado | `matching_ejecucion` / `matching_metrica` en cada pasada, contra la anterior | toda pasada publica precisión, recall, dispersión y estabilidad |
| 8 | Aprendizaje | auto-etiquetado (EAN y >0,99 = positivos; **no** usar el precio como etiqueta negativa, §5.1) → LightGBM; después triplet loss | el modelo elegido gana a Splink **por métrica medida**, no por opinión |
| 9 | LLM local | Ollama + Outlines con JSON forzado, **solo** los pares ambiguos | mejora medible en el subconjunto ambiguo; si no mejora, no entra |
| 10 | Front nuevo | **bloqueado**: hay que resolver el choque del §0.4 y del §12 antes | — |
| 11 | API nueva | **solo lo que falte**: ampliar `/api/buscar` y `/api/grupo/{id}` en vez de duplicarlos | contrato actualizado en `docs/API.md` |

Entorno verificado hoy para la fase 3 y la 9: `node v24.19.0`, `npm 11.2.0`,
`pnpm` y `npx` instalados; **Ollama 0.34.2 respondiendo** en `127.0.0.1:11434`; el
cerrojo de GPU compartida (`%TEMP%\vozstudio_motor.lock`) **no** está cogido;
Docker disponible. Ninguno de los dos frenos por GPU está activo ahora mismo.

Las fases 2 y 4 son las que más mueven la aguja y las más baratas; la 5 y la 8
son las que el encargo llama "algoritmos complejos".

---

## 10. Lo que necesito que decidas

1. **Control de versiones.** La carpeta **no tiene `.git`** (comprobado; ya estaba
   escrito en `docs/AUDITORIA.md:36`). Voy a tocar el emparejador, migrar el
   modelo de grupos y (si se aprueba) rehacer el front. **¿Hago `git init` y un
   primer commit del estado actual antes de empezar?** Sin esto, cualquier paso
   atrás se hace a mano. Es la decisión que más barata es ahora y más cara
   después.
2. **El front choca con dos decisiones tuyas.** `docs/APP.md:320-331` dice *"nada
   de framework pesado… sin framework… gráfica SVG a mano"* y
   `docs/API.md:336` dice que FastAPI *"no sirve HTML. Eso es Caddy"*. El plan
   nuevo pide Vite+React+TS+Tailwind+shadcn+TanStack+uPlot servido por FastAPI.
   *El plan mismo dice que, si choca, ganan los documentos.* **¿Cuál de los dos
   vale?** Si la respuesta es "el front nuevo", hay que **actualizar `APP.md` y
   `API.md` en el mismo commit**, no dejarlos contradiciendo al código.
   (Dato que ayuda a decidir: el front actual **no son 6,5 KB de HTML pelado**,
   como dice el §2 del plan: son `index.html` 6.663 B **+ `app.js` 79.656 B +
   `estilo.css` 29.063 B**. Los propios documentos citan `web/app.js`.)
3. **Tocar el dato de formato en el pipeline diario.** La Fase 2 corrige
   `cantidad`/`unidad_canon` en silver, que es lo que alimenta la tarea de las
   06:00. Es la palanca nº 1 (287 + 172 de los 784 fallos, y los precios por
   unidad absurdos), pero toca el camino crítico. **¿Adelante, con tests y sin
   cambiar el contrato de columnas?**
4. **Vetos condicionales en vez de duros.** Los datos dicen que el veto duro de
   unidad borraría 266 pares correctos y el de sección al menos 667 (§5), y que
   `docs/MODELO.md` y `docs/PRECIO-POR-UNIDAD.md` **ya decidieron** que no se
   expulsa a nadie por la unidad. **¿Confirmas el veto condicional** (formato
   fiable + contradicción grande + `precio_comparable`) **y el umbral de 30× en
   vez del 60 % del plan?**
5. **Cambiar el tope de referencia.** El plan pide "recall ≥ 0,85 sobre el tope
   del EAN", pero ese tope son 1.821 pares y hoy ya sale 100 % por construcción
   (§2.1). Propongo publicar siempre **dos** métricas: precisión contra el EAN
   (sonda) y recall contra el tope del bloque canónico (40.183 productos /
   30.725 pares). **¿De acuerdo con la redefinición?**
6. **Backlog que queda anulado o cambiado.** El **N8** ("el botón *esto no es lo
   mismo*", `docs/BACKLOG.md:738-766`) es validación humana, ahora prohibida, y
   `docs/COMPETENCIA.md:373-390` lo llama "la mejor idea del día". Las "colas de
   revisión a mano" del BACKLOG §2 y de `docs/FASES.md:244-248` también.
   **¿Los marco como obsoletos con una nota que apunte aquí, en vez de
   borrarlos?** (Dejar el registro de por qué se decidió lo contrario vale más
   que un hueco.)

Nada más. El resto del plan (§6, §7, §8) se puede ejecutar tal cual.

---

## 11. Anexo: 20 malas asociaciones concretas

Salen de `diagnostico_matching.py`. Las 6 primeras son **misma marca y dos
códigos de barras distintos**: dos códigos distintos son dos productos distintos,
y el sistema no debería etiquetarlos `identico` sin comprobarlo.

| # | motivo | grupo | A | B |
|---|---|---|---|---|
| 1 | misma marca, 2 EAN | 92 | Cerveza San Miguel **especial sin gluten** 33 cl [carrefour] `8410655002410` | Cerveza San Miguel 33 cl [dia] `8410655000010` |
| 2 | misma marca, 2 EAN | 7284 | Cerveza tostada Amstel **0,0 Radler con limón** 33 cl [carrefour] `8410569520017` | Cerveza **radler** Amstel 33 cl [dia] `8410569615614` |
| 3 | misma marca, 2 EAN | 3039 | Fuze Tea té limón **sin azúcar** lata 33 cl [carrefour] `5449000329943` | Fuze tea de limón 330 ml [dia] `5449000325983` |
| 4 | misma marca, 2 EAN | 2569 | Fanta limón **zero** 330 ml [dia] `5449000120991` | Fanta limón **zero** [mercadona] `5449000114884` |
| 5 | misma marca, 2 EAN | 1858 | Schweppes naranja zero lata 33 cl [carrefour] `8414100382065` | Schweppes de naranja zero 330 ml [dia] `8414100363460` |
| 6 | misma marca, 2 EAN | 1357 | Mahou 5 Estrellas **sin gluten** lata 33 cl [carrefour] `8411327001885` | Mahou 5 Estrellas **sin gluten** 33 cl [dia] `8411327001908` |
| 7 | precio/unidad **×1.030** | 5565 | POTE Azafrán molido 0,40 g [alcampo] → `0.4 kg` | Azafrán molido Pote 0,4 g [dia] → `0.0004 kg` |
| 8 | precio/unidad **×1.030** | 10398 | POTE Azafrán en hebra 0,400 gr [alcampo] → `0.4 kg` | Azafrán en hebras Pote 0,4 g [dia] → `0.0004 kg` |
| 9 | precio/unidad **×920** | 3631 | PIPER-HEIDSIECK Champagne brut 75 cl [alcampo] → `? ud` | Champagne Piper Heidsieck brut 75 cl [carrefour] → `? ud` |
| 10 | precio/unidad **×316** | 32339 | Filetes de dorada Selección de Dia 300 g [dia] → `0.001 kg` | Filetes de dorada [mercadona] → `0.2 kg` |
| 11 | precio/unidad **×88** | 4113 | SANON Cartílago de tiburón **100 cápsulas** [alcampo] → `0.055 kg` | Cartílago de tiburón Sanon **100 ud** [carrefour] → `? kg` |
| 12 | precio/unidad **×67** | 2013 | FLOR Suavizante **87 lavados** [alcampo] → `1.392 l` | Suavizante Flor **63 lavados** [dia] → `63.0 l` |
| 13 | precio/unidad **×45** | 7554 | VERNEL Suavizante cielo azul **55 dosis 1000 ml** [alcampo] → `1.0 l` | Suavizante cielo azul Vernel **55 lavados** [dia] → `55.0 l` |
| 14 | precio/unidad **×38** | 12905 | CARMENCITA Cardamomo **23 g** [alcampo] | Sazonador cardamomo Carmencita **30 g** [carrefour] |
| 15 | unidad distinta (mismo EAN) | 11544 | Desodorante roll-on Dry Comfort Nivea **50 ml** [carrefour] → `1.0 ud` | el mismo, EAN `4005900388513` [dia] → `0.05 l` |
| 16 | unidad distinta (mismo EAN) | 3520 | Desodorante spray mineral protect Sanex **200 ml** [carrefour] → `1.0 ud` | el mismo, EAN `8718951464841` [dia] → `0.2 l` |
| 17 | unidad distinta (mismo EAN) | 23851 | Tinte retoca raíces Magic Retouch L'Oréal **75 ml** [carrefour] → `1.0 ud` | el mismo, EAN `3600524146191` [mercadona] → `0.075 l` |
| 18 | unidad distinta (mismo EAN) | 23852 | Snack dental Frolic Smiley Sticks **175 g** [carrefour] → `? ud` | el mismo, EAN `5998749121092` [dia] → `0.175 kg` |
| 19 | unidad distinta (mismo EAN) | 11975 | Vino Viña Albali D.O. Valdepeñas **75 cl** [carrefour] → `? ud` | el mismo, EAN `8410702000017` [dia] → `0.75 l` |
| 20 | unidad distinta (mismo EAN) | 19298 | Vino Faustino VII D.O.Ca. Rioja **75 cl** [carrefour] → `? ud` | el mismo, EAN `8410441211002` [dia] → `0.75 l` |

**Lectura del anexo.** Los casos 1–6 son un fallo del algoritmo (la etiqueta
`identico` no exige el código). Los casos 7–14 son un fallo de **dato**: cuando la
cantidad está mal, el precio por unidad se dispara y la señal de precio miente.
Los casos 15–20 **no son fallos del emparejamiento**: son el mismo producto, y lo
que está mal es el campo de formato de una de las dos cadenas. De los 20
ejemplos, **6 son del algoritmo, 8 del dato de cantidad y 6 del dato de unidad**:
la misma proporción que el §4, y la razón de que el plan deba empezar por el dato
y por la asignación.

---

## 12. Conflictos con lo ya decidido en el repo

El §0 del plan manda: **si este plan choca con los documentos del proyecto, ganan
ellos y se avisa.** Esto es el aviso.

### 12.1 Decisiones del dueño que el plan contradice

| documento | qué está decidido | qué dice el plan |
|---|---|---|
| `docs/APP.md:320-331` | *"Nada de framework pesado… cliente: una web servida por Caddy. Sin framework… gráfica SVG a mano"* | Vite+React+TS+Tailwind+shadcn+TanStack+uPlot (§7) |
| `docs/API.md:6-8, 336` | la API responde **JSON y nunca HTML**; la interfaz la sirve **Caddy** (existen `plataforma/Caddyfile` y el servicio en `docker-compose.yml`) | el build servido como estático **por FastAPI** (§7, §11) |
| `docs/MODELO.md:57-71` | PostgreSQL = **siete tablas y no van a ser más**; no hay tabla de productos ni de precios; `grupo_id` sin integridad referencial **a propósito** | cuatro tablas nuevas (§6) |
| `docs/MODELO.md:42-45`, `docs/PRECIO-POR-UNIDAD.md:29-49` | una unidad por grupo, y **los productos de otra unidad siguen dentro** | veto duro por unidad (§5, etapa 5) |
| `docs/PRECIO-POR-UNIDAD.md:114-141` | `FACTOR_INCREIBLE = 30`: hasta 30× el ahorro es real | sospechoso por encima del **60 %** |
| `docs/AUDITORIA.md:73-78` | *"no introducir embeddings hasta tener varios cientos de pares EAN Mercadona-DIA como conjunto de validación"* | embeddings + FAISS en la etapa 1 |
| `docs/BACKLOG.md:462-464` | *"TF-IDF y regresión logística; ni se te ocurra una red neuronal con ese volumen"* | embeddings, triplet loss, LightGBM |
| `docs/BACKLOG.md:46-49, 487`, `docs/API.md:143-144` | **calidad ≠ gama**: se devuelve `calidad` si sale de ingredientes y `gama` si sale del precio, **nunca las dos** | el plan no menciona ni una ni otra |
| `docs/BACKLOG.md:109-111` | *"Lo que NO hay que hacer. Un clasificador"* (para la sección) | "distancia en el árbol de categorías" |
| `docs/PRECIO-POR-UNIDAD.md:147-159` | medido y descartado: `envase` y `tipo_producto` no sirven para bloquear | el plan no los usa, pero conviene no reintroducirlos |
| `docs/API.md:33-39` | `fecha_datos` en toda respuesta; **un dato que falta es `null`, nunca cero** | los endpoints nuevos del plan quedan sujetos |
| `docs/APP.md:147-163` | un precio de más de 3 días **no decide** dónde comprar | la pantalla de grupo debe llevar la fecha por cadena |

### 12.2 Duplicaciones y trabajo ya hecho

| dónde | qué |
|---|---|
| `docs/BACKLOG.md:115-146` (tarea 2, "Grupos demasiado anchos") | ya planifica lo mismo que la Fase 2/3 del plan, **con criterios medibles** (≥57 % de aciertos, >200 % de 405 a <150). Hay que citarla, no reinventarla |
| `docs/BACKLOG.md:466-470`, `docs/FASES.md:206-252` (F2, F2.5) | el modelo con "1.748 pares verdaderos gratis (mismo EAN)" ya está planificado, con el sesgo avisado |
| `core/matching.py` | las etapas 1, 2 y parte de la 4 del plan **ya existen** (bloqueo, TF-IDF n-gramas, EAN, union-find, umbral medido). Falta Splink/EM, embeddings, húngaro, LightGBM y LLM |
| `data/gold/grupos.parquet` + `enlaces.parquet` | el modelo de grupos **ya existe**; `equivalencia`/`grupo_producto` lo renombran y añaden `peso`, `confianza`, `metodo`, `features`, `version` |
| `core/runlog.py` (`data/runs.csv`) + `core/cobertura.py` | ya registran ejecuciones; `matching_ejecucion` debe **enlazarse**, no solaparse |
| `docs/PANTALLAS.md:44, 97, 169, 191, 204, 248, 271, 290` | Buscar, Lista, Donde la compro, Favoritos, Ficha, Compartir, Panel y Ajustes están marcadas **[hecho]**: el §7 del plan las propone en parte como nuevas |
| `plataforma/api/main.py` + `panel.py` | 19 rutas vivas (buscar, grupo, producto, estado, bajadas, índice, pulso, posición, panel×5, listas/donde, alertas, favoritos, preferencias). La "Fase 5: API nueva" debe **ampliarlas**, no duplicarlas |
| `docs/MODELO.md:157` | documenta `GET /grupo/{id}/serie?dias=90`, **que no existe**: la curva llega dentro de `/api/grupo/{grupo_id}`. Hay que reconciliar el contrato antes de "documentarlo" |

### 12.3 Riesgos operativos que el plan no menciona

| riesgo | documento |
|---|---|
| **No hay `.git`** — y el plan incluye refactor de matching + migración de front | `docs/AUDITORIA.md:36`, `docs/FASES.md:50-56` |
| La tarea de las **06:00**; `ejecutar.bat` con marca diaria y reintento | `README.md:15-18`, `ejecutar.bat` |
| **`pytest` fue destructivo** hasta el 21-sep: escribir en `data/` bajo pytest ahora lanza `EscrituraDePrueba` | `COMANDOS.md:15-23` |
| Orden obligatorio de recuperación: `rehacer_maestro` → `reprocesar` → `pipeline` → `emparejar` → `verificar_docs` | `docs/OPERACION.md:237-245` |
| **Un dato que no cruza la frontera de gold no existe**: toda columna nueva va a `emparejar.COLUMNAS` | `docs/BACKLOG.md:568-569` |
| Si se añade un campo al contrato, se añade también a la matriz de paridad | `docs/PARIDAD-CAMPOS.md:1-6, 183-186` |
| La plataforma **no escribe** en `data/gold/` (solo lectura) | `docs/API.md:334-335` |
| **Bronze no se borra nunca** (`BorradoProhibido`); y `DATOS.md` (30 días) contradice a `OPERACION.md` ("para siempre") | `docs/OPERACION.md:19-21, 327-359` |
| Rendimiento: `adelgaza()` existe porque 17→34 columnas llevó de 79 s a >115 s | `docs/PRECIO-POR-UNIDAD.md:163-178` |
| DuckDB: una conexión **por hilo**; tolerar gold viejo con `DESCRIBE` previo | `docs/API.md:20-21, 409-415` |
| Criterios de aceptación vigentes: pytest, ruff, **`--medir ≥ 57 %`**, `verificar_docs` | `docs/FASES.md:518-521` |

### 12.4 Lo que el plan da por hecho y **no está en ningún documento del repo**

El cerrojo de GPU en `%TEMP%`, los modelos de embeddings concretos
(MiniLM/e5/bge-m3), **Splink**, FAISS/hnswlib, el algoritmo húngaro, LightGBM,
Ollama y Outlines/Guidance. No es que estén mal: es que **son nuevos**, y por
tanto cada uno hay que justificarlo con una medición antes/después, como pide el
encargo. Ninguna de esas piezas se apoya en una decisión previa del proyecto.

---

## 13. Lo que se arregló el 22 de septiembre, con números

Las decisiones del §10 se tomaron y se ejecutaron. Todo lo de esta tabla está
medido **sobre el mismo bronze** —las cinco cadenas del 21/22 de septiembre—, con
el código de antes y el de después, guardando el `grupos.parquet` de cada versión
y corriendo los dos. No es una comparación entre dos días distintos.

| | antes | después | |
|---|---:|---:|---|
| **aciertos de `emparejar --medir`** | **57 %** | **65 %** | +8 puntos; el listón era 57 % |
| enlaces aceptados | 18.001 | **22.702** | +26 % |
| grupos comparables entre cadenas | 6.439 | **6.589** | |
| **productos comparables** | 19.834 (37,7 %) | **23.049 (43,8 %)** | +16 % |
| grupos con las cinco cadenas | 268 | **271** | |
| pares ciertos encontrados por el nombre (de 1.809) | 1.028 | **1.169** | |
| etiqueta `identico` que dice la verdad | 70 % | **100 %** | ver §3.2 |
| enlaces con unidad canónica distinta | 266 | **132** | |
| grupos comparables con unidad mixta | 239 | **109** | |
| fallos por "una cadena lo vende en otra unidad" | 172 | **39** | −77 % |
| cantidades imposibles en DIA | 35 | **16** | |
| Carrefour con un `1 ud` de relleno | 2.076 | **468** | |
| enlaces con un par de precio imposible (>30×) | — | **0** | veto nuevo |
| **grupos con el más caro a más del 200 %** | 369 (6,5 %) | **443 (7,5 %)** | **empeoró: ver §14** |

### 13.1 Los tres arreglos de dato

1. **La etiqueta de 100 gramos no vale lo mismo en todas las cadenas.** Miles de
   productos traían el precio por unidad mal por un factor de diez. Medido
   producto a producto contra el precio real de cada uno: DIA multiplica por diez
   en **529 de 529**, Aldi en **202 de 223**, y **Mercadona no multiplica en 488
   de 488**. Antes se aplicaba la convención de una cadena a las demás. Ahora la
   convención es de cada cadena, y cuando el propio producto permite comprobarlo,
   manda el producto. La prueba de que hacía falta: un desodorante de 50 ml a
   2,49 EUR trae `4,98` con etiqueta `100ml`, que es exactamente 2,49 / 0,05 × 10.
2. **La cadena que se contradice consigo misma.** DIA publicaba "Detergente
   líquido Dia Super Paco **61 lavados**" con formato `61 l` —61 litros de
   detergente en un bote de tres— y su propia referencia de precio en `lavado`.
   33 productos así, con cantidades de 30 a 69 "litros". El precio lo confirma:
   7,14 / 61 = 0,117 y su etiqueta dice 0,12 € por lavado.
3. **`cantidad_fiable`.** Hay ahora una columna que distingue un `1 ud` que
   declara la cadena de un `1 ud` que pusimos nosotros porque no sabemos el
   tamaño. Los dos valen 1, pero solo el primero sirve para bloquear. Carrefour
   pasa de 2.076 falsos a 468, y 1.608 productos dejan de fingir un formato: se
   quedan con la unidad y el precio por unidad **que sí publica la cadena**.

### 13.2 Los dos arreglos de algoritmo

1. **La etiqueta `identico` ya no miente.** `nivel()` llamaba idéntico a dos
   productos con códigos de barras distintos solo por compartir marca, y medido
   acertaba el 70 %. Ahora, con dos códigos, decide el código. Resultado: **100 %**,
   y la etiqueta pasa a ser utilizable para decidir algo.
2. **La asignación 1-a-1 (algoritmo húngaro).** Cada bloque y cada par de cadenas
   reparten sus parejas maximizando la **ganancia por encima del listón**, no el
   parecido a secas. Escrito a mano en `core/matching.py`: sin numpy ni scipy, que
   son dos dependencias de decenas de megas para noventa líneas de algoritmo.
   - Con el parecido a secas salió **peor**: 23 % más de enlaces y 694 grupos
     comparables menos, porque dos parejas mediocres (0,56 + 0,56) le ganan a una
     buena (0,90). Con la ganancia, un 0,90 vale 0,35 y un 0,56 vale 0,01.
   - Se conservan los dos canales separados (con marca y sin marca) porque el
     proyecto ya había medido que con uno solo el acierto caía del 53 % al 43 %;
     hay una prueba que lo fija.

### 13.3 El veto de precio, condicional

`precio_imposible()`: dos productos cuyo precio por unidad se lleva más de **30
veces** no son el mismo producto. El 30 no es inventado: es `FACTOR_INCREIBLE`
(`core/comparacion.py`), el umbral con el que el proyecto ya marca un grupo como
dudoso. Por debajo hay ahorros **reales** de 28×. Solo actúa con la misma unidad,
con precio en los dos lados, con `precio_comparable`, y **nunca** sobre un par con
el mismo EAN.

Comprobado después: **0 de los 22.702 enlaces** lo viola.

### 13.4 Y un arreglo que no era del emparejador

`projects/cesta/collectors/carrefour.py`: la categoría `cat11729677`
(papelería/colorear) lleva **desde el 8 de septiembre** devolviendo HTTP 500
—comprobado en `data/ejecuciones.log`, donde falla en 10 ejecuciones distintas—.
Con la regla estricta, ese día el recorrido **tiró la captura entera de
Carrefour**: 16.525 productos buenos y 47 minutos de recorrido, por unos cuadernos
de colorear. Ahora está en `ROTAS_EN_ORIGEN`, la lista de categorías que el propio
Carrefour sirve rotas, que el recorrido revisa cada día para avisar cuando alguna
revive.

---

## 14. Lo que queda mal, y ahora se sabe exactamente por qué

**Los grupos anchos siguen ahí: 443 con más del 200 % de dispersión, y la tasa
subió del 6,5 % al 7,5 %.** Pero la causa ya no es una hipótesis:

```text
enlaces que violan el veto de precio (>30x):        0 de 22.702
grupos con el mas caro a mas de 3x el mas barato:   443
los peores:   grupo 30054  x316    3 productos
              grupo 92     x125  329 productos
              grupo 434     x64   83 productos
              grupo 252     x42  145 productos
              grupo 52      x36  208 productos
```

**Ningún par aceptado es imposible: la anchura viene de la transitividad.** A–B es
razonable, B–C es razonable, y A y C están a 125 veces. El union-find los mete en
el mismo grupo porque para él un grupo es "lo que está conectado", no "lo que se
parece". Es exactamente el problema que el BACKLOG ya había escrito al hablar del
botón humano: *"un rechazo parte el grupo, pero el union-find los puede volver a
unir por un tercer producto"*.

Arreglarlo **no** es otro veto de par, porque no hay ningún par que vetar. Es un
freno **a nivel de grupo** —no admitir un miembro si el grupo pasa de una
dispersión máxima— o *correlation clustering* de verdad, aceptando que un grupo
pequeño y coherente vale más que uno grande y falso. Eso, más las fases 5 a 11 del
§9, es lo que queda.

---

## 15. Estado del encargo

| fase | estado |
|---|---|
| 0 · diagnóstico | **hecho** |
| 1 · modelo versionado | **hecho** (§17) |
| 2 · dato de formato | **hecho** (§13.1) |
| 3 · bloqueo | pendiente: el actual aguanta, falta el ANN con embeddings |
| 4 · asignación | **hecha**: húngaro (§13.2) y freno de grupo (§16) |
| 5 a 11 | pendientes |

Lo entregado el 22 de septiembre: `core/normalize.py`, `core/matching.py`,
`projects/cesta/pipeline.py`, `projects/cesta/emparejar.py`,
`projects/cesta/collectors/carrefour.py`,
`projects/cesta/diagnostico_matching.py` y sus pruebas. **545 pruebas en verde,
`ruff` limpio, `verificar_docs` en verde, `--medir` = 65 %** (el listón del
proyecto es 57 %). Y el proyecto ya tiene git.

---

## 16. El freno de grupo, y lo que **no** arregla

Mirando los peores grupos en vez de suponerlos, la causa cambió de sitio otra vez:

```text
grupo  92  329 productos  "Cerveza sin alcohol Dia Ramblers" + "Leffe Brune negra"
                          + "Guinness" + "Gulden Draak"...  -> TODAS las cervezas
grupo 252  145 productos  Cortes, Fuente Primavera, Vichy Catalan -> TODAS las aguas
grupo 434   83 productos  Sanex, Axe, Vichy, Happy -> TODOS los desodorantes
grupo 30054  3 productos  Filetes de dorada: Mercadona 2.250, Carrefour 3.645
                          y DIA **712.000** c/kg -> aqui el roto es el DATO
```

Y sólo 4 de los 329 miembros del grupo 92 están a más de 3× de la mediana: **la
dispersión no era el problema, era el síntoma**. Un freno por precio no lo habría
tocado.

### 16.1 Lo que sí se arregló: el freno de unión

`core.matching.agrupar_enlaces`: los enlaces se recorren de más parecido a menos,
y un enlace por debajo de **0,80** todavía puede meter a un producto suelto en un
grupo, pero **no puede pegar dos grupos que ya existen**. Es la regla que corta el
mecanismo del grupo monstruo, que es la propagación, no el par.

El número salió de medir, no de elegir (`grupo mayor / grupos comparables /
productos comparables / grupos de 5 cadenas / error demostrable / grupos >200 % /
productos con letra de calidad`):

| regla | grupo mayor | comparables | productos | 5 cadenas | error dem. | >200 % | con calidad |
|---|---:|---:|---:|---:|---:|---:|---:|
| sin freno | **329** | 6.589 | 23.049 | 271 | 935 | 7,5 % | 14.610 |
| **A · 0,80** | **97** | **7.925** | 23.047 | 201 | 900 | 6,4 % | **12.996** |
| B · 0,80 | 85 | 8.499 | 20.176 | 69 | **422** | **3,7 %** | **5.546** |

Dos reglas, no una. La A es la de arriba: un enlace flojo puede meter a un
producto suelto, pero no pegar dos grupos. La B es más dura: un enlace flojo
**solo** vale entre dos productos sueltos.

**Se elige la A, y la B se descartó midiendo.** La B es claramente mejor en lo que
se estaba mirando —mitad de error demostrable, mitad de grupos anchos—, pero
**hunde la letra de calidad de 12.996 productos a 5.546**, porque casi todos los
grupos se quedan en pareja y `letras()` pide tres comparables para dar una letra.
La letra de calidad es una función que se usa en la ficha y en la API: no se
cambia por una mejora en un indicador indirecto. La medición queda escrita en
`core/matching.py` por si algún día la letra deja de pedir tres.

Consecuencia de lo elegido: **los productos comparables no bajan (23.047)**, los
grupos comparables suben de 6.589 a **7.925** (+20 %, o sea más productos con
alternativa visible) y el grupo mayor cae de 329 a **97**.

### 16.2 Lo que **no** arregla: las familias temáticas, y por qué

Después del freno siguen habiendo 80 productos de cervezas juntos. La causa se
buscó, se encontró una candidata, **se implementó, se midió y se descartó**.

**La hipótesis.** El IDF se calcula sobre el catálogo entero. De 52.567 productos
unos 600 son cerveza, así que para la fórmula `cerveza` es una palabra **rara**
(`log(52567/601) ≈ 4,4`) y por tanto distintiva, cuando entre cervezas no
distingue absolutamente nada. Arreglo: calcular el peso dentro del pasillo.

**La medición.** Se implementó (`pesos_por_pasillo`, 60 líneas, con sus pruebas) y
se corrió sobre el mismo catálogo, recalibrando el umbral porque la escala cambia:

| | aciertos `--medir` | grupos comparables | productos | grupo mayor | tasa >200 % |
|---|---:|---:|---:|---:|---:|
| IDF global, 0,55 | 65 % | 7.925 | 23.047 | 97 | 6,28 % |
| IDF por pasillo, 0,55 | 62 % | — | — | — | — |
| IDF por pasillo, 0,50 | **66 %** | 8.134 | 23.449 | **80** | 6,38 % |

Cuesta 3 puntos de acierto al mismo umbral y, puesto al umbral que los recupera,
**el grupo mayor baja de 97 a 80 y la tasa de grupos anchos hasta empeora un
poco**. La hipótesis era falsa.

**Por qué era falsa, medido.** De los 137 enlaces internos del grupo mayor, en
**50 manda el trigrama**, y son justo los flojos, los que hacen de puente:

```text
total=0.50   palabra=0.32   trigrama*0.85=0.39
   [alcampo]   AMSTEL CLASICA Cerveza tostada 33 cl.
   [dia]       Cerveza tostada Dia Ramblers 33 cl
total=0.52   palabra=0.33   trigrama*0.85=0.42
   [alcampo]   MAHOU Cerveza tostada 0.0 % alcohol lata 33 cl.
   [carrefour] Cerveza tostada Saer Brau 0,0 sin alcohol lata 33 cl
total=0.52   palabra=0.33   trigrama*0.85=0.42
   [carrefour] Cerveza tostada Saer Brau 0,0 sin alcohol lata 33 cl
   [dia]       Cerveza tostada 0,0% alcohol Mahou 33 cl
```

`parejo()` es `max(palabras, 0,85 × trigramas)`. **Quitarle peso a las palabras no
cierra un puente que abre el trigrama.** El número que gobierna el canal de letras
es `PESO_TRIGRAMAS`, así que se probó a bajarlo… **y tampoco**:

| | aciertos `--medir` | enlaces | tasa >200 % | productos comparables |
|---|---:|---:|---:|---:|
| 0,85 (lo que vale) | **65 %** | 22.702 | 448 | 23.047 |
| 0,80 (probado) | 64 % | 22.679 | 449 | 23.039 |

Un punto de acierto y 23 enlaces, para nada. Y el motivo es aritmético, así que
conviene dejarlo escrito para no repetir el error: con el listón en 0,55, para que
un puente lo sostenga el trigrama su Dice tiene que llegar a `0,55 / 0,85 = 0,647`;
bajando el peso a 0,80 el corte pasa a `0,55 / 0,80 = 0,6875`, así que solo caen
los puentes que están en esa banda estrecha. **Bajar el peso no apaga el canal,
solo lo desplaza un poco**, y de paso se lleva aciertos que sí dependían de él.

Las dos hipótesis sobre la *puntuación* están por tanto medidas y descartadas. Lo
que cierra los puentes es la **asignación y la unión**, que es donde ya se actuó
(§13.2 y §16.1), y lo que queda por hacer es un freno **a nivel de grupo**, no
otro ajuste de la fórmula.

Los dos números (`UMBRAL_UNION` y `PESO_TRIGRAMAS`) se quedan escritos en
`core/matching.py` con estas tablas al lado, para que nadie tenga que volver a
descubrir que no funcionan.

El `0,85` estaba antes como número suelto dentro de la función; ahora es una
constante con nombre y con su medición. Ese es el cambio que se queda de esta
prueba: la fórmula no ha cambiado, pero ya no hay un número mágico.

El código de `pesos_por_pasillo` se queda en `core/matching.py` con sus pruebas y
con este resultado escrito al lado: la idea es buena, el sitio donde falla está
localizado, y no se usa porque la medición dice que no aporta.

### 16.4 Y una cosa que no era un hallazgo, era un fallo: no era reproducible

Persiguiendo lo anterior salió esto: dos ejecuciones del **mismo día con el mismo
código** daban **22.702** y **22.704** enlaces. No es ruido de datos. El reparto
1-a-1 va marcando qué producto queda ocupado, y el orden en que se recorrían los
grupos de candidatos salía de un diccionario cuyas claves llevan texto: eso
depende del *hash seed* del proceso, que Python sortea en cada arranque.

Se recorren ordenados y **mejoró, pero no se cerró**: medido después, con el
`sorted` puesto, dos procesos siguen dando **22.702** y **22.705** (3 de 22.700, un
0,013 %). Ni los grupos ni las métricas cambian (7.923 contra 7.925), así que no se
ha seguido cazando — pero **queda anotado**, porque el plan pide medir la
estabilidad entre ejecuciones («menos del 2 % de grupos cambian de composición») y,
mientras quede baile, esa medida tiene un suelo de ruido que hay que conocer antes
de creerse cualquier mejora pequeña.

Lo que sí se aprendió y se queda: escribir la afirmación «es reproducible» antes de
comprobarlo dos veces es exactamente el error que este proyecto paga caro.

Y el grupo 30054 no es de emparejamiento: DIA publica **1 g** para unos filetes de
dorada de "300 g aprox". Es el mismo tipo de roto que los 33 detergentes "de 61
litros" del §13.1: **el dato de cantidad de los productos que se venden al peso**.
DIA y Mercadona venden pescado fresco así y Mercadona sí lo marca `peso_variable`;
DIA lo publica como si fuera un peso fijo.

### 16.3 El criterio del BACKLOG sigue sin cumplirse

El BACKLOG §2 pide **menos de 150 grupos con más del 200 % de dispersión**. Hoy
hay **448** (6,3 % de los 7.130 grupos con precio comparable, contra el 7,5 % de
antes: la tasa sí mejora). No se cumple, y no se va a cumplir con frenos: hace
falta el IDF por sección del §16.2 y arreglar la cantidad de los productos al
peso. Queda en el BACKLOG como tarea 2, con estas dos pistas en vez de con una
corazonada.

La medida excluye los precios que la propia cadena marca `precio_comparable =
false`: medir el ancho de un grupo con un número que ya sabemos que no vale es
medir el grupo con una regla rota. Quitarlos baja de 458 a 448, así que no eran
el motor del problema, pero la cuenta es más honesta así.

---

## 17. El modelo de equivalencias, versionado (Fase 1)

`core/equivalencias.py`. Dos cosas que el modelo de antes no tenía, y las dos
importan:

1. **`producto_id` estable.** Hasta hoy `enlaces.parquet` guardaba **pares de
   posiciones** en la lista de productos; por eso existía `enlaces_huella.json`,
   que avisa cuando el catálogo cambia. Un par de posiciones no sobrevive a
   reordenar el catálogo, a añadir una cadena ni a que un día falle una captura.
   Ahora un par es `(dia:12345, carrefour:9)`, que significa lo mismo siempre.
2. **Cada pasada escribe su propio directorio y no toca las anteriores**
   (`data/gold/matching/ejecucion=<id>/`), con la huella del catálogo del que
   salió y la versión del modelo. Se puede comparar una pasada con la anterior y
   volver atrás. Es lo que pedía el encargo: nunca sobrescribir.

Y cada par guarda **por qué** se aceptó, en `features`: si el EAN coincide y si
está en los dos lados, si la marca coincide, si coinciden cantidad, unidad y
sección, el parecido y el **ratio de precio por unidad**. Eso es lo que hace
auditable el resultado sin que nadie apruebe nada.

```text
data/gold/matching/ejecucion=20260922-134241/
    equivalencia.parquet   22.702 pares, con metodo, confianza y features
    metrica.parquet        enlaces, identicos, grupos y productos comparables...
    resumen.json           de que catalogo salio, con que codigo y con que umbral
data/gold/matching/ultima.json     cual es la ultima
```

Diez pruebas en `tests/test_equivalencias.py`: que el id no depende de la
posición, que la huella cambia si cambia el orden, que dos pasadas no se pisan,
que las features dicen la verdad y que sin ninguna pasada no revienta.

**Lo que queda de esta fase**: migrar las listas y los favoritos de PostgreSQL,
que hoy apuntan a `grupo_id` (un número que cambia en cada pasada). Con
`producto_id` estable ya se puede; ver `docs/MODELO.md`.
