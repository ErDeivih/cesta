# PLAN — Interfaz nueva + matching automático de productos entre cadenas

> Documento maestro del encargo. Lo escribió una sesión de trabajo que ya había
> consumido su contexto, para que **otra sesión nueva** lo ejecute con todo el
> contexto posible. Léelo entero antes de tocar nada.
> Fecha: 2026-09-22 · Raíz del proyecto: `F:\aprendizaje\scrap`

---

## 0. Cómo usar este documento

1. Lee **⚠️ primero** estos documentos del propio repo (son decisiones ya tomadas
   por el dueño; no se contradicen sin avisar):
   `docs/MODELO.md`, `docs/DATOS.md`, `docs/COMPETENCIA.md`, `docs/CADENAS.md`,
   `docs/PARIDAD.md`, `docs/PARIDAD-CAMPOS.md`, `docs/PANTALLAS.md`,
   `docs/USABILIDAD.md`, `docs/UX-MOVIL.md`, `docs/DASHBOARD.md`, `docs/CIFRAS.md`,
   `docs/PRECIO-POR-UNIDAD.md`, `docs/API.md`, `docs/APP.md`, `docs/BACKLOG.md`
   (54 KB), `docs/AUDITORIA.md`, `docs/OPERACION.md`, `docs/FASES.md`.
   Si algo de este plan choca con ellos, **ganan ellos** y se avisa al dueño.
2. Este documento define el **qué** y el **porqué**. El código manda en el **cómo**.
3. El trabajo se hace por fases (§8), cada una con criterio de aceptación medible.

---

## 1. El encargo (palabras del dueño, resumidas)

- Migrar la interfaz a algo **más especializado** (no HTML pelado).
- **Rehacer/repensar la UI**: funcionalidades, datos y gráficas que se muestran
  de los productos, tipos de filtros, y **combinación de productos entre cadenas**:
  elegir un producto general y ver las alternativas de cada cadena, con **pesos**.
- **El matching está mal**: muchos productos están asociados incorrectamente.
- **Nadie va a validar a mano**: el matching debe ser **automático** (programa o
  algoritmo). Se pide investigar y aplicar **algoritmos complejos** que además
  sirvan para aprender.
- El orden da igual: **hay que hacer todo**.

---

## 2. Estado de partida (reconocimiento hecho)

```
F:\aprendizaje\scrap\
  README.md                 qué es: fábrica de datos; producto 1 = "cesta" (comparador)
  pyproject.toml · uv.lock  se gestiona con uv  ->  usar `uv run`
  ejecutar.bat              tarea diaria de Windows ("Cesta diaria", 06:00)  ¡NO ROMPER!
  COMANDOS.md               comandos útiles
  core/                     librería común: fetch, normalize, state, storage,
                            derive, off (Open Food Facts), runlog, schemas, config
  projects/cesta/
    collectors/             mercadona, aldi, alcampo, dia, carrefour
    pipeline.py             bronze -> silver -> gold
    run.py                  orquestador;  search.py = buscador CLI
  data/                     FUERA DE GIT — 64.493 ficheros, 10,9 GB
      warehouse.duckdb      almacén de consulta (DuckDB)
      raw/ bronze/ silver/ gold/
  plataforma/
      api/main.py           23,9 KB — backend FastAPI
      web/index.html        6,5 KB — TODA la interfaz actual (HTML/JS pelado)
      docker-compose.yml · .env · LEEME.md
  docs/                     45 documentos (el conocimiento del proyecto)
  extension/ · notebooks/ · tests/ (74) · projects/ (53)
```

Puntos de partida concretos para leer el código:
`plataforma/api/main.py`, `plataforma/web/index.html`,
`projects/cesta/pipeline.py`, `core/normalize.py`, `core/schemas.py`,
`core/derive.py`, y lo que haya de *matching* (busca: `match`, `equivalen`,
`paridad`, `competencia`, `splink`, `embedding`).

Reglas del proyecto que **no** se tocan (README §Reglas):
crudo inmutable · `fetch`/`parse`/`load` separados · `parse` puro y testeable sin
red · idempotencia (reejecutar el mismo día no duplica) · escalera de acceso
(API interna → httpx → curl_cffi → Patchright → pagar) · ritmo conservador ·
cero datos personales · **ningún campo vacío** (nativo, derivado, externo o inferido).

---

## 3. Decisiones ya tomadas (por el dueño, en esta conversación)

| Tema | Decisión |
|---|---|
| Interfaz | **Migrar** a un stack especializado (React + Vite + TypeScript). Mantener FastAPI como cerebro. |
| Validación humana del matching | **Ninguna.** Todo automático, con métricas y explicabilidad. |
| Algoritmos | Aplicar técnicas **avanzadas** (las de §5) y dejar el sistema **aprendiendo** con cada ejecución. |
| Orden | Da igual: se hace **todo**. Se recomienda el orden de §8 por dependencias. |
| Idioma | Documentación y UI **en español** (así está todo el repo). |

---

## 4. Diagnóstico: por qué están mal asociados (hipótesis a confirmar)

Antes de reescribir nada, **medir**. Hipótesis, por orden de probabilidad:

1. **Emparejamiento por nombre y a lo bruto**: comparar cadenas de texto sin
   normalizar (acentos, mayúsculas, "pack", "ud", "x2", abreviaturas, formato de
   tamaño) → falsos positivos entre productos parecidos y falsos negativos entre
   el mismo producto escrito distinto.
2. **Sin restricción de unidad/cantidad**: se compara un bote de 500 g con uno de
   1 kg como si fueran el mismo. `core/normalize.py` ya resuelve cantidad+unidad:
   **usarlo como puerta dura** (bloqueo), no como un detalle.
3. **Ignorar el código de barras (EAN)**: cuando dos cadenas traen EAN del mismo
   producto, ese par es **oro** (verdad de referencia). Si no se está usando, es
   el mayor error del sistema.
4. **Asignación no exclusiva**: un producto de Mercadona asociado a dos de Lidl, y
   otro a ninguno (emparejamiento voraz/greedy, sin resolver la asignación global).
5. **Sin control de categoría**: comparar "aceite de oliva" con "aceite de girasol"
   por parecido de texto.
6. **Marca y variedad ignoradas** ("Hacendado leche entera" vs "Hacendado leche
   desnatada").

Entregable del diagnóstico (Fase 0): un informe con **números**, no opiniones:
cuántos grupos hay, cuántos con ≥2 cadenas, cuántos pares con EAN coincidente
(tope de calidad alcanzable), cuántos pares con diferencia de precio por unidad
absurda (>60 %), y 20 ejemplos malos.

---

## 5. Matching automático: investigación de algoritmos y recomendación

**Planteamiento**: el problema es *entity resolution* / *product matching* de
registros (dos catálogos de la misma realidad, con ruido). La arquitectura
correcta tiene **5 etapas**; casi todo el error real viene de las etapas 1 y 5,
no del clasificador.

### Etapa 1 — Bloqueo (candidate generation)
No se comparan todos contra todos (64 k productos = 2·10⁹ pares). Se generan
candidatos:
- **Bloqueo por clave canónica**: `categoría + marca_normalizada + cantidad+unidad`
  (usar `core/normalize.py`). Reduce el espacio sin perder recall útil.
- **EAN exacto** (si existe): par de máxima confianza, se acepta directamente.
- **Bloqueo difuso**: TF-IDF de n-gramas de caracteres (robusto a erratas y
  abreviaturas) y/o **LSH/MinHash** para near-duplicates.
- **Vecinos por embedding (ANN)**: embeddings multilingües de nombre+marca
  (`paraphrase-multilingual-MiniLM-L12-v2`, `intfloat/multilingual-e5-small` o
  `BAAI/bge-m3`) + índice **FAISS/hnswlib**; k vecinos por producto.
  *Por qué*: "aceite oliva virgen extra 1l" y "AOVE 1 L" se parecen poco como
  texto y mucho como significado.
- **Biblioteca que resuelve esto de serie**: **Splink** (`moj-analytical-services/splink`)
  implementa *Fellegi–Sunter* con DuckDB como motor (¡ya usáis DuckDB!), incluye
  bloqueo, comparadores, TF ajustado y **estimación no supervisada por EM**:
  **no necesita etiquetas humanas**. Es la pieza central recomendada.

### Etapa 2 — Comparadores / características del par
Calcular *features* por par candidato y guardarlas (auditables y reutilizables):
- EAN igual (0/1) · marca igual (ratio) · categoría igual (0/1)
- cantidad+unidad iguales (0/1) y su **ratio** (0,5 kg vs 1 kg = 0,5)
- **ratio de precio por unidad** (¡pista fuerte! mismo producto ⇒ mismo orden de
  magnitud) y su log-diferencia
- similitud léxica: `rapidfuzz` (ratio, token_set_ratio), Jaro-Winkler, Levenshtein
  normalizada
- similitud semántica: coseno de embeddings
- similitud de tokens raros (IDF): coincidir en "Hacendado" aporta poco; en
  "aove" o "0,0" aporta mucho (esto es exactamente el *TF ajustado* de Splink)
- distancia en el árbol de categorías (2 niveles)

### Etapa 3 — Puntuación (probabilidad de ser el mismo producto)
- **Recomendado (sin etiquetas)**: **Splink / Fellegi–Sunter con EM** → cada par
  sale con una probabilidad calibrada y **descomposición por comparador**
  (explicable: "se aceptó por EAN + marca + tamaño, penalizado por precio").
- **Cuando haya etiquetas** (ver Etapa 6): **LightGBM/XGBoost** sobre las features
  de la etapa 2. Suele batir a las reglas y da importancia de variables.
- **Caso residual ambiguo**: un modelo local vía **Ollama** (ya instalado) con
  **salida estructurada forzada** — **Outlines** o **Guidance** — devolviendo un
  JSON estricto `{mismo_producto: bool, motivo: str, confianza: 0..1}`. Es la
  respuesta correcta a "modelos pequeños que alucinan": se les obliga al esquema.
  Usarlo **solo** para unos pocos miles de pares dudosos, no para todo.

### Etapa 4 — Asignación y agrupación (aquí está el mayor salto de calidad)
- Dentro de cada bloque canónico, y **por cada par de cadenas**, resolver la
  asignación **1-a-1 óptima** con el **algoritmo húngaro**
  (`scipy.optimize.linear_sum_assignment`) maximizando la suma de probabilidades,
  con umbral mínimo. Evita que un producto de Mercadona "robe" el par de otro.
- **Agrupar** los pares aceptados en "productos generales" con *union-find* /
  componentes conexas, con **correlación-clustering** si aparecen conflictos
  (un producto no puede estar en dos grupos por transitividad contradictoria).
- Elegir el **representante** del grupo (nombre y categoría canónicos) y guardar
  el **origen** de cada miembro y su peso.

### Etapa 5 — Control de calidad automático (sin humanos)
- **Métricas de pares**: precisión/recall estimados por muestreo estratificado,
  F1, y *AUC* usando el subconjunto con EAN como verdad de referencia.
- **Métricas de negocio**: % de grupos con ≥2 cadenas; coherencia de precio
  (desviación por unidad dentro del grupo); nº de conflictos de asignación;
  estabilidad entre ejecuciones (¿cambian los grupos de un día para otro?).
- **Reglas de veto automáticas** (defensa en profundidad): nunca aceptar un par
  si la unidad canónica difiere; si el precio por unidad difiere > X %; si la
  categoría de nivel 1 difiere. Se guardan como "vetos" con su motivo.
- **Explicabilidad**: cada par aceptado guarda sus features y la contribución de
  cada una → un panel lo puede auditar sin que nadie valide a mano.

### Etapa 6 — Aprendizaje continuo (lo que el dueño quiere "para aprender")
- **Auto-etiquetado**: los pares con EAN coincidente y los pares de altísima
  probabilidad (>0,99) = positivos; los pares con la misma categoría y EAN
  distintos, o con precio por unidad muy lejano = negativos. Así se construye un
  conjunto de entrenamiento **sin intervención humana**.
- **Entrenar** el clasificador (LightGBM) con ese conjunto, compararlo con Splink
  y quedarse el mejor por métrica. Guardar modelo + métricas versionadas.
- **Metric learning**: afinar los embeddings con pares positivos (contrastive /
  triplet loss) usando `sentence-transformers`. Es la pieza "compleja" y muy
  didáctica; hacerla **después** de tener las métricas base funcionando.
- **Otras técnicas para estudiar/aplicar** (todas encajan aquí):
  *active learning* autogestionado (elegir para etiquetar los pares de máxima
  incertidumbre, pero etiquetados por las reglas de oro, no por personas),
  *self-training* iterativo, *graph embeddings* (node2vec sobre el grafo de
  equivalencias) y *blocking adaptativo* (aprender qué claves de bloqueo rinden).

### Resumen de la pila recomendada (orden de implementación)
1. **Splink + DuckDB** (Fellegi–Sunter, EM, no supervisado) ← columna vertebral.
2. **rapidfuzz + embeddings multilingües (ANN con FAISS)** ← features y candidatos.
3. **Hungarian + union-find/correlación-clustering** ← asignación y grupos.
4. **LightGBM** entrenado con auto-etiquetas ← mejora incremental.
5. **Ollama + Outlines/Guidance** ← solo los casos ambiguos, con JSON forzado.
6. **sentence-transformers con triplet loss** ← afinado, al final.

---

## 6. Modelo de datos propuesto (mínimo, en DuckDB/Parquet)

```
producto            (id, cadena, nombre, marca, categoria_l1, categoria_l2,
                     cantidad, unidad, ean, precio_actual, precio_ud, url, ...)
precio_historico    (producto_id, fecha, precio, precio_ud, disponible)
equivalencia        (id, grupo_id, producto_id, peso, metodo, confianza,
                     features JSON, version, creada, ejecucion_id)
grupo_producto      (grupo_id, nombre_canonico, categoria_l1, categoria_l2,
                     cantidad, unidad, n_cadenas, precio_ud_medio, dispersion)
matching_ejecucion  (ejecucion_id, fecha, version_modelo, metricas JSON)
matching_metrica    (ejecucion_id, metrica, valor)
```

Reglas: **nunca** sobreescribir: cada ejecución **versiona** (permite comparar y
volver atrás). Todo par guarda `features` y `metodo` (`ean`, `splink`, `modelo`,
`llm`, `regla`) para poder explicarlo y medir qué método acierta más.

---

## 7. Interfaz nueva (arquitectura y pantallas)

**Stack recomendado** (el dueño pidió "algo más especializado"):
- **Vite + React + TypeScript** en `plataforma/web/` (build servido como estático
  por FastAPI; sin infra nueva, sin Node en producción).
- **Tailwind CSS** + componentes **shadcn/ui** (Radix) ← limpio y moderno, al
  estilo de las referencias aportadas (VibeUI / Refero / designmd).
- **TanStack Query** (datos/servidor) + **TanStack Table** (filtros, orden,
  agrupación, columnas virtualizadas) — encaja justo con la petición de "tipos de
  filtros".
- **Gráficas**: **uPlot** (rapidísimo, ideal para series de precio) o **Recharts**
  si se prefiere comodidad; sparkline de histórico en cada fila.
- **"Generative UI" sin Node**: el patrón que piden las referencias (Vercel AI SDK)
  se puede hacer íntegro con FastAPI devolviendo **vistas tipadas**:
  `{"tipo":"tabla_comparativa","datos":...}` y un **renderizador** en React que
  mapea cada `tipo` a un componente. Las respuestas del modelo local pasan por
  **Outlines** para garantizar el esquema. Mantiene la complejidad fuera de la vista.
- **Móvil**: hay `docs/UX-MOVIL.md`; la UI nueva debe ser responsive desde el
  principio (rejilla + tablas con scroll horizontal controlado).

**Pantallas mínimas**:
1. **Grupo de producto (la clave del encargo)**: eliges un producto general y ves
   en columnas las alternativas de cada cadena, con su precio por unidad, su peso,
   su histórico (sparkline) y **la diferencia % contra el mejor**. Botón para
   cambiar el peso y ver cómo se reordena.
2. **Explorador / filtros**: por cadena, categoría, marca, rango de precio,
   precio por unidad, "con alternativas en ≥N cadenas", "ha subido/bajado",
   disponibilidad. Guardar filtros como vistas.
3. **Ficha de producto**: histórico, mínimo/máximo, media, evolución, y su grupo
   de equivalencias con la **explicación del emparejamiento**.
4. **Panel de matching (auditoría, no validación)**: métricas de la última
   ejecución, métodos y su acierto, conflictos, vetos, y buscador de pares
   dudosos con sus features. Sin botones de "aceptar/rechazar".
5. **Cesta**: la lista de la compra del dueño (ya existe `config.yml`) comparada
   entre cadenas, con el total y el ahorro.

---

## 8. Fases, con criterio de aceptación

| Fase | Qué | Aceptación |
|---|---|---|
| **0** | Diagnóstico con números + informe de por qué falla el matching actual (+ leer los 18 docs clave) | Informe con métricas actuales y 20 ejemplos malos documentados |
| **1** | Modelo de datos de equivalencias versionado + migración de lo que ya haya | Tablas creadas, idempotentes, con tests |
| **2** | Pipeline de matching: bloqueo (canónico+EAN+ANN) → features → **Splink/EM** | Métricas automáticas publicadas por ejecución; mejora medible frente al actual |
| **3** | Asignación húngara + agrupación + vetos + explicabilidad | 0 conflictos de asignación; todo par con motivo y features |
| **4** | Auto-etiquetado + **LightGBM** + comparación contra Splink | El mejor modelo queda versionado y elegido por métrica |
| **5** | API nueva para la UI (grupos, filtros, históricos, métricas) + tests | Contrato documentado en `docs/API.md` |
| **6** | Front nuevo (Vite+React+TS+Tailwind+shadcn+TanStack+uPlot), pantallas §7 | Funciona en escritorio y móvil; el viejo `index.html` deja de usarse |
| **7** | LLM local con Outlines para pares ambiguos (opcional si mejora) | Mejora medible en el subconjunto ambiguo, con JSON forzado |
| **8** | Aprendizaje continuo (triplet loss, blocking adaptativo, graph embeddings) | Métricas versionadas que mejoran o se justifican |

En cada fase: **tests** (pytest, `parse` sin red), actualizar **`docs/`** y el
**BACKLOG**, y no romper la **"Cesta diaria"** (`ejecutar.bat`, schtasks 06:00).

---

## 9. Métricas de éxito (para no engañarse)

- **Matching**: precisión ≥ 0,97 en pares aceptados; recall ≥ 0,85 sobre el tope
  alcanzable definido por EAN; ≥ 90 % de grupos con ≥2 cadenas; dispersión media
  de precio por unidad dentro del grupo razonable (< 35 %).
- **Estabilidad**: < 2 % de grupos cambian de composición entre ejecuciones
  seguidas sin motivo (cambio real de catálogo).
- **Producto**: el dueño puede, en < 10 s, ver un producto general con sus
  alternativas por cadena, el mejor precio y el histórico. Filtros combinables y
  guardables. Sin pantallas que necesiten explicación.
- **Rendimiento**: la página del grupo responde < 300 ms; el matching completo
  corre en minutos, no horas.

---

## 10. Riesgos y trampas

- **Tocar `data/`**: es el crudo inmutable (10,9 GB). Solo lectura. Reprocesar
  debe costar minutos (regla 1 del README).
- **Romper la tarea diaria** de Windows y las reglas de ritmo/educación de los
  sitios. Nada de cambios en `core/fetch.py` sin cuidado.
- **Sobreajustar el umbral** para que los números luzcan: el tope lo marca el EAN.
- **Embeddings con modelos enormes** en un PC con 6 GB de VRAM: usar modelos
  pequeños (MiniLM/e5-small) en CPU o GPU compartida; ojo, en este equipo hay
  otros proyectos que usan la GPU (hay un cerrojo compartido en `%TEMP%`).
- **Cambiar el contrato de la API** sin actualizar `docs/API.md` y sin avisar.
- **Duplicar trabajo**: leer el BACKLOG antes de implementar (puede haber
  decisiones o tareas ya planificadas para esto).

---

## 11. Qué NO hacer

- No introducir validación humana ni pantallas de "aprobar/rechazar".
- No comparar todos contra todos ni usar solo similitud de cadenas de texto.
- No aceptar un par sin guardar **por qué** se aceptó.
- No migrar el front sin dejar el build servido por FastAPI (nada de segundo
  servidor en producción).
- No tocar la voz/audiolibros: eso es otro proyecto (`E:\Libros\VozStudio`), aquí
  no se mezcla.
