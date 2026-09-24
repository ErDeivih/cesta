---
seccion: Investigación y anexos
resumen: La investigacion sobre emparejamiento, entera y con sus fuentes.
---

# Entity resolution / record linkage / product matching: estado del arte (2024-2026) aplicado a un comparador de precios de supermercados

> Contexto de referencia: pipeline Python + DuckDB + Parquet, 5 cadenas españolas, bloqueo por marca/categoría, similitud Dice ponderada por IDF + trigramas, reparto húngaro 1-a-1 por par de cadenas, unión por componentes conexas. Banco de verdad = 1.799 pares con el mismo EAN; recall actual 1.161/1.799 = 65 %.

## 1. El marco clásico

El modelo de Fellegi-Sunter (1969) plantea el enlace como un contraste de verosimilitudes: para cada campo se estiman las probabilidades *m* (coincide siendo el mismo producto) y *u* (coincide siendo distinto), se combinan en un peso logarítmico y se fijan dos umbrales que separan enlace / duda / no enlace, con estimación de errores bajo independencia condicional. La línea moderna reformula esto como modelos de mezcla (clases latentes) con dependencia entre campos y estimación bayesiana, sin necesidad de verdad de referencia ([A Review of Modern Multinomial-Derived and Partition-Based Record-Linkage Methods](https://wires.onlinelibrary.wiley.com/doi/pdf/10.1002/wics.70015); [Method: Fellegi-Sunter and Jaro Approach to Record Linkage](https://ec.europa.eu/eurostat/cros/system/files/Micro-Fusion-07-M-Fellegi-Sunter%20and%20Jaro%20Approach%20v1.0_0.pdf)). Los pasos canónicos son bloqueo → comparación por pares (vector de similitudes) → clasificación → clustering; la literatura reciente los trata como una cadena de configuración donde cada etapa tiene sus propios hiperparámetros ([Auto-Configuring Entity Resolution Pipelines](https://arxiv.org/abs/2503.13226)). Una panorámica reciente del aprendizaje profundo para ER es [A Comprehensive Survey of Deep Learning for Entity Resolution](https://dlnext.acm.org/doi/epdf/10.1145/3828660).

**En este proyecto:** el banco EAN permite estimar *m* y *u* empíricamente por campo (marca, categoría, tokens de tamaño, trigramas) en lugar de fijar pesos a mano, y sustituir el umbral único del húngaro por dos umbrales (enlace / duda).

## 2. Blocking moderno y su coste

El bloqueo agrupa registros en cubos para no comparar todos los pares posibles; su calidad se mide con *pair completeness* (recall de pares verdaderos co-ubicados) y *reduction ratio* (pares evitados), y **el recall del bloqueo es el techo del recall final**: un par que nunca cae en el mismo bloque nunca se enlaza ([Blocking and Filtering Techniques for Entity Resolution: A Survey](https://dlnext.acm.org/doi/fullHtml/10.1145/3377455); [Blocking Techniques for Large-Scale Entity Resolution](https://raw.githubusercontent.com/imvladikon/imvladikon/master/articles/entity_resolution_blocking_survey.pdf)). Las familias clásicas son claves deterministas, *sorted neighborhood*, *canopy clustering* y LSH/MinHash; las aprendidas inducen las claves desde etiquetas ([Learning Blocking Schemes for Record Linkage](https://auld.aaai.org/Papers/AAAI/2006/AAAI06-070.pdf); [Adaptive Blocking](https://dl.acm.org/doi/abs/10.1109/ICDM.2006.13)). Hoy se usa mucho bloqueo denso/ANN: [BlockingPy](https://arxiv.org/abs/2504.04266) hace blocking con vecinos aproximados (CPU/GPU), [Towards Universal Dense Blocking for Entity Resolution](https://arxiv.org/abs/2404.14831) pre-entrena un blocker denso de dominio abierto, y [Neural Locality Sensitive Hashing for Entity Blocking](https://arxiv.org/abs/2401.18064) aprende funciones hash para métricas personalizadas. Los componentes conexos se han usado incluso para escalar bloqueo con orden parcial a miles de millones de entidades ([Connected Components for Scaling Partial-order Blocking to Billion Entities](https://dl.acm.org/doi/10.1145/3646553)).

**En este proyecto:** antes de tocar el matcher, medir la *pair completeness* del bloqueo marca+categoría sobre los 1.799 pares EAN. Si muchos pares no comparten bloque, el 65 % es un techo estructural y ningún modelo lo sube. Candidatas: clave compuesta marca + tamaño normalizado + categoría, y blocking ANN sobre el texto sin el número de envase.

## 3. Matchers modernos

Las similitudes de string siguen siendo baseline: Jaro-Winkler para cadenas cortas (marcas), Levenshtein para typos, y métricas por tokens (Jaccard/Dice/cosine) para títulos reordenados o incompletos; el survey de redes neuronales para matching resume el salto a representaciones aprendidas ([Neural Networks for Entity Matching: A Survey](https://arxiv.org/abs/2010.11075)). Del lado aprendido, DeepMatcher fue el hito de deep learning para EM ([Deep Learning for Entity Matching](https://dl.acm.org/doi/10.1145/3183713.3196926)) y Ditto (transformer fine-tuned como clasificación de pares) reporta mejoras de **hasta +29 % de F1** sobre el SOTA previo, +9,8 % con sus optimizaciones (resaltado de campos, resumen de strings, aumento de datos) y **96,5 % F1** en un caso real de 789 K vs 412 K registros, además de alcanzar resultados previos con la mitad de etiquetas ([Ditto](https://arxiv.org/abs/2004.00584)). El benchmark WDC Products muestra que **todos los matchers actuales (Ditto, HierGAT, R-SupCon) empeoran al generalizar a entidades no vistas** y que el aprendizaje contrastivo es más eficiente en etiquetas que los cross-encoders ([WDC Products](https://arxiv.org/abs/2301.09521)); una evaluación experimental reciente concluye que los **bi-encoders afinados dominan en datos de producto y cross-dominio** ([The impact of fine-tuning on entity resolution: An experimental evaluation](https://www.sciencedirect.com/science/article/pii/S095070512600170X)). Para producto concreto, hay pipelines de dos etapas (filtro grueso + filtro fino con GNN sobre atributos y relaciones) en [Cross-platform Product Matching … RAEA](https://arxiv.org/abs/2512.07232) y matching con atención jerárquica de producto en [HierGAT](https://dl.acm.org/doi/pdf/10.1145/3514221.3517872).

**En este proyecto:** el reparto húngaro fuerza 1-a-1 por par de cadenas; con recall bajo eso crea enlaces falsos por eliminación. Antes de cambiar de modelo, conviene sustituirlo por umbral + verificación, y reservar el húngaro para desambiguar cuando hay varios candidatos fuertes.

## 4. Búsqueda vectorial: complemento, no sustituto

Los embeddings de frases permiten blocking denso y recuperación semántica (SBERT afinado con triplet loss supera a TF-IDF y a SBERT sin afinar en 3-19 % según [TriBERTa](https://arxiv.org/abs/2411.10629)); con HNSW/FAISS el coste por consulta es sublineal. El límite documentado es numérico: **13 modelos de embeddings ampliamente usados tienen dificultades para codificar detalles numéricos** ([Revealing the Numeracy Gap: An Empirical Investigation of Text Embedding Models](https://arxiv.org/abs/2509.05691), versión ACL en [Findings of EACL 2026](https://aclanthology.org/2026.findings-eacl.289/)). Es exactamente el caso `1,75 cl` vs `175 ml` vs `1,5 l`: el embedding ve títulos casi iguales y el único rasgo discriminante es el número.

**En este proyecto:** extraer el tamaño/pack a campos estructurados, normalizarlos (cl → ml, `pack 6 x 1,5 l` → 9.000 ml) y **quitar el número del texto que se vectoriza**; luego comparar tamaño con tolerancia. No he verificado en esta sesión cifras publicadas de recall de HNSW/FAISS/pgvector/Qdrant frente a búsqueda exacta: **no lo sé**.

## 5. Entity resolution con LLM

Lo publicado en 2023-2026 va en tres direcciones: prompting, uso del LLM como **verificador** de pares dudosos, y ajuste/planificación con conciencia de coste. El resultado más citado para producto es que ChatGPT alcanza **82,35 % F1 zero-shot** en una tarea difícil donde RoBERTa necesita 2.000 ejemplos para un rendimiento similar; añadir demostraciones in-context seleccionadas por similitud sube hasta **+7,85 % F1** (y 10 ejemplos fijos, +4,92 %), y añadir reglas de matching da ganancias parecidas, con un **coste de 0,10-0,14 céntimos de dólar por par** (gpt-3.5-turbo-0301) frente a 1,29-1,36 céntimos con davinci-002 ([Using ChatGPT for Entity Matching](https://arxiv.org/abs/2305.03423)). Se publica también razonamiento multi-paso y debate para robustez ([Structured Multi-Step Reasoning for Entity Matching](https://arxiv.org/abs/2511.22832)), controladores de coste con RL ([CaRL-EM](https://arxiv.org/abs/2609.01195)), presupuesto entre dominios ([BEACON](https://arxiv.org/abs/2603.11391)) y grafos que combinan propagación barata con consultas LLM caras bajo presupuesto ([Alper](https://arxiv.org/abs/2605.25814)). La advertencia publicada es de **calibración**: la confianza de los LLM como matchers no está bien calibrada ([Confidence Calibration in Large Language Model-Based Entity Matching](https://aclanthology.org/2025.uncertainlp-main.12/)).

**En este proyecto:** usar LLM solo como verificador de la banda ambigua (0,4-0,7 de similitud). Extrapolando el coste publicado: 50.000 pares dudosos × 0,001 $ ≈ 50 $ por pasada, asumible si se muestrea y se cachea.

## 6. Clustering después del matching

Unir por componentes conexas impone transitividad dura: un solo falso positivo puede fusionar dos clusters enteros (efecto puente), y Alper critica explícitamente que el paradigma secuencial produce un grafo disperso con aristas perdidas y ruidosas y que la "transitividad rígida" propaga errores ([Alper](https://arxiv.org/abs/2605.25814)). La alternativa formal es el clustering con restricciones (must-link / cannot-link), que se aborda como clustering correlacional —NP-duro, con aproximaciones y reparación de subconjuntos— ([CKR Partitions and Lower Bounds for Constrained Correlation Clustering](https://arxiv.org/abs/2608.08291); [Clustering with Noisy Queries](https://arxiv.org/abs/1706.07510); [Uncertainty-Aware Probabilistic Constrained Clustering](https://arxiv.org/abs/2608.12027)).

**En este proyecto:** A~B y B~C no implica A~C. Ya tienes dos restricciones fuertes y baratas: **mismo EAN = must-link** y **EAN distinto y no vacío = cannot-link**. Aplicarlas como corte sobre las componentes conexas evita fusiones absurdas a coste casi nulo.

## 7. Métricas y evaluación

Las métricas pair-wise (precisión/recall/F1 sobre pares) y las de cluster (B-cubed, pairwise, cluster F1) **no ordenan igual a los sistemas**: Menestrina et al. mostraron que los rankings a menudo entran en conflicto, y el pair-wise recall se puede mantener alto mientras los clusters son inservibles ([A Practitioner's Guide to Evaluating Entity Resolution Results](https://arxiv.org/abs/1509.04238); [Evaluating entity resolution results](https://dl.acm.org/doi/10.14778/1920841.1920871)). B-cubed (Bagga y Baldwin, 1998) evalúa a nivel de mención con precisión y recall por registro, lo que penaliza los clusters grandes y erróneos (definición verificada en [este documento](https://ar5iv.labs.arxiv.org/html/2504.19606)). Sobre fugas: si el banco son pares con el mismo EAN, ningún campo derivado del EAN puede ser feature, y la evaluación debe separar productos/categorías/cadenas no vistos — precisamente la dimensión que WDC Products añade y donde todos los matchers caen ([WDC Products](https://arxiv.org/abs/2301.09521)); ese benchmark advierte además de que sus etiquetas provienen de un clustering automático de ofertas, es decir, verdad aproximada.

**En este proyecto:** reportar siempre dos cifras: recall pair-wise sobre el banco EAN (techo = pair completeness del bloqueo) y B-cubed F1 sobre clusters de productos. El 65 % pair-wise puede convivir con clusters mal formados.

## 8. Errores típicos y trampas publicadas

La dominancia de un atributo está documentada: en [Using ChatGPT for Entity Matching](https://arxiv.org/abs/2305.03423) añadir el **precio** (sin normalizar formato/moneda) **reduce** el F1, mientras la marca lo sube hasta 1 punto. Los casos esquina (packs, tamaños, negativos difíciles) son los que hunden a los matchers fuera de muestra ([WDC Products](https://arxiv.org/abs/2301.09521)). Sobre sobre-bloqueo por marca blanca en supermercados españoles no he encontrado literatura específica: **no lo sé**; por teoría de blocking, una clave basada en una marca ausente o compartida (marca blanca) es un bloque gigante (poca reducción) o un bloque vacío (pérdida total de recall). Para auditar desacuerdos, el enfoque de explicaciones y equidad en ER ayuda a inspeccionar por qué se enlaza o no ([Fairness and Explanations in Entity Resolution: An Overview](https://ieeexplore.ieee.org/document/11129015)), y el análisis experimental de heterogeneidad entre datasets recuerda que el rendimiento no se transfiere entre dominios sin medirlo ([Heterogeneity in entity matching: A survey and experimental analysis](https://www.sciencedirect.com/science/article/pii/S0169023X26000224)).

**En este proyecto:** clasificar cada par perdido en dos causas — *fallo de bloqueo* (no co-ubicado) o *fallo de matching* (co-ubicado y no enlazado). Es el diagnóstico de mayor valor por euro invertido.

## Tabla de decisión

| técnica | coste | qué mejoraría aquí | riesgo | cómo medirlo |
|---|---|---|---|---|
| Calcular *pair completeness* del bloqueo actual con el banco EAN | Muy bajo | Revela si 65 % es techo estructural | Ninguno | PC global y por cadena/categoría |
| Normalizador de unidades y packs (`1,75 cl`→`175 ml`, `6 x 1,5 l`→`9.000 ml`) | Bajo (reglas + tests) | Ataca los pares separados por formato | Fusionar formatos distintos mal parseados | Recall en subconjunto del banco con formatos divergentes |
| Clave de bloqueo compuesta marca + tamaño normalizado + categoría | Bajo | Sube la *pair completeness* | Marca blanca/vacía; tamaño mal parseado | PC y tamaño medio de bloque |
| Blocking ANN / MinHash sobre texto sin el número de envase | Medio (infra) | Recupera typos y reordenaciones | Recall aproximado < 1 y confusión numérica | recall@k contra el banco EAN |
| Bi-encoder afinado con triplet loss sobre positivos EAN | Medio | Generaliza a abreviaturas y typos | Fuga si test y train comparten producto; dominancia de marca | Recall/precisión en holdout por producto no visto |
| Cross-encoder (Ditto/RoBERTa) como verificador de banda dudosa | Medio-alto | Precisión en pares difíciles | Necesita miles de etiquetas; sobreajuste a entidades vistas | F1 en pares de productos no vistos |
| Verificador LLM solo en banda ambigua (≈0,1 ¢/par) | Bajo-medio | Casos de pack/formato raros | Calibración dudosa, inconsistencia, coste creciente | Precisión y ECE sobre muestra etiquetada a mano |
| Etiquetado asistido por LLM para ampliar el banco | Medio | Más datos de entrenamiento | Ruido en etiquetas y circularidad | Kappa/ acuerdo con etiquetas humanas |
| Sustituir húngaro 1-a-1 por umbral + restricciones (must-link/cannot-link por EAN) | Bajo | Evita enlaces forzados con recall bajo | Clusters que crecen por transitividad | B-cubed F1 y distribución de tamaños de cluster |
| Reparación de grafo / clustering correlacional aproximado | Medio | Evita fusiones masivas por un puente falso | Romper pares buenos (caída de recall) | Precisión de cluster + revisión de merges |
| Deduplicación intra-cadena por EAN antes de comparar | Muy bajo | Limpia el grafo de entrada | EAN ausente en parte del catálogo | Nº de aristas intra-cluster espurias |
| Auditoría dirigida de 200 desacuerdos (bloqueo vs matching) | Humano | Prioriza el siguiente cambio a hacer | Sesgo de muestreo | Distribución de causas de fallo |

## Qué NO merece la pena (y por qué)

- **Fine-tuning completo de un cross-encoder tipo Ditto con 1.799 pares.** Pocos datos: el propio Ditto reporta necesitar muchas etiquetas, y la evidencia reciente dice que los bi-encoders contrastivos son más eficientes en etiquetas y dominan en datos de producto.
- **Usar el LLM para bloquear o para decidir todos los pares.** El coste es lineal en el número de pares y la calibración está cuestionada; su sitio es la banda ambigua.
- **Resolver correlation clustering de forma exacta.** Es NP-duro; a esta escala basta reparación local o umbrales con restricciones.
- **Añadir el precio entre cadenas como atributo de comparación.** Evidencia publicada de caída de F1 cuando el atributo numérico no está normalizado.
- **Usar embeddings como sustituto del bloqueo.** La brecha numérica documentada hace que confundan envases que solo difieren en el número; van como complemento.
- **Perseguir el mejor modelo antes de arreglar normalización de unidades y bloqueo.** Con bloqueo al 65 % de techo, la mejora del matcher está limitada por arriba.

## Lo que no he podido verificar

- Números concretos de recall frente a latencia de HNSW/IVF con FAISS, pgvector o Qdrant.
- Literatura específica sobre sobre-bloqueo por marca blanca en supermercados españoles.
- Benchmarks públicos de product matching de supermercados españoles con EAN.
