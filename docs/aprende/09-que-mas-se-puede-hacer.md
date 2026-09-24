# 09 · Qué más se puede hacer con estos datos (y qué no)

Un proyecto de datos se juzga también por saber **dónde está su frontera**. Este capítulo es el
catálogo de análisis que se pueden hacer con lo que hay aquí, con una columna que casi nunca
aparece en un portfolio: **lo que estos datos no permiten concluir**. Lo que sigue sale de una
revisión de fuentes (2020-2026) hecha el 24 de septiembre de 2026; las fuentes van citadas y
los detalles, en los anexos 90 (emparejamiento), 91 (índices de precios) y en este capítulo.

## 1. La tabla, que es el capítulo

| Análisis | Datos que necesita | ¿Se puede aquí? | Qué conclusión permitiría | Riesgo de conclusión falsa |
|---|---|---|---|---|
| Dispersión de precios del mismo producto entre cadenas | Catálogo emparejado + precio diario | **Sí** | Cuánto más caro es lo mismo en cada cadena | Leer dispersión como «poder de mercado» |
| Auditoría del precio anterior (¿la oferta es real?) | Serie diaria por producto | **Sí** (parcial) | Si el precio subió antes de la bajada | Afirmar incumplimiento sin la ventana legal completa |
| Detección de anomalías y escalones de precio | Serie diaria por producto | **Sí** | Errores de captura y cambios de nivel | Etiquetar una promoción legítima como error |
| Índice de precios por cadena | Relativos emparejados | **Sí** | A qué ritmo se mueve cada cadena | Llamarlo inflación; confundir composición con precio |
| Inflación personal de una cesta | Listas de usuario + precios | **Sí** (parcial) | Cuánto ha subido *tu* cesta | Sin cantidades no hay ponderación por gasto |
| Clustering de categorías por dinámica | Precios + categoría | **Sí** | Qué categorías son volátiles o promocionadas | Elegir k a ojo y no validar estabilidad |
| Co-ocurrencia en listas de la compra | Listas de usuario | **Parcial** | Qué se planifica junto | Confundir intención con cesta real |
| Previsión del índice agregado | Serie del índice (1-7 días) | **Parcial** | Tendencia a corto plazo, con intervalos | Extrapolar 19 días a «inflación anual» |
| Reglas de asociación (Apriori/FP-Growth) | Miles de tickets completos | **No** | — | Reglas espurias con lift alto presentadas como hallazgos |
| Elasticidad de la demanda | Cantidades vendidas o cuotas | **No** | — | Publicar correlaciones precio-cantidad como elasticidades |
| Cuota de mercado por cadena | Ventas o unidades | **No** | — | Inferir cuota desde precios o catálogo |
| Estacionalidad anual | ≥1 año de histórico | **No** | — | Inventar patrones «de verano» con 19 días |
| Sustitución / canibalización entre marcas | Ventas por marca y periodo | **No** | — | Confundir correlación de precios con sustitución |

## 2. Por qué las tres «No» son «No»

**Reglas de asociación.** Apriori y FP-Growth buscan conjuntos de productos que aparecen
juntos, y se evalúan con soporte (P(X,Y)), confianza (P(Y|X)), *lift* (confianza / P(Y)) y
*conviction*. Su problema aquí es doble: una lista de la compra **es una intención**, no la
cesta, así que la co-ocurrencia está censurada de origen (nadie apunta la sal, ni lo que ya
tenía en casa); y con pocos usuarios el soporte se vuelve minúsculo y las reglas que
sobreviven son triviales o no significativas.
([Agrawal y Srikant, 1994](http://www.sigmod.org/publications/dblp/db/conf/vldb/vldb94-487.html) ·
[Han et al., 2000](https://dl.acm.org/doi/10.1145/335191.335372) ·
[Significación estadística de reglas de asociación](https://ar5iv.labs.arxiv.org/html/1405.1360))

**Elasticidad.** La vía clásica es una regresión log-log (`log Q = a + b·log P`), y la moderna
son los modelos de elección discreta, incluido el logit de coeficientes aleatorios de Berry,
Levinsohn y Pakes, que estima demanda a partir de **cuotas de mercado agregadas** con
instrumentos de coste. Sin cantidades vendidas no hay demanda que estimar: lo que se puede
medir con rigor es **dispersión de precios** para el mismo producto, que es descriptivo y
valioso, pero no es elasticidad. La trampa clásica es la endogeneidad: el precio se fija
mirando la demanda, así que su correlación con la cantidad mezcla oferta y demanda.
([BLP, 1995](https://pages.stern.nyu.edu/%7Eacollard/BLP.pdf) ·
[Villas-Boas y Winer, *Endogeneity in Brand Choice Models*](https://pubsonline.informs.org/doi/references/10.1287/mnsc.45.10.1324))

**Cuota de mercado.** No hay ventas ni unidades vendidas. El catálogo dice qué se ofrece, no
qué se vende, y una cadena puede tener más productos porque publica más surtido (Alcampo
publica 23.591 fichas; Aldi, 2.100).

## 3. Los cuatro análisis que sí, y por dónde empezar

**1. Auditoría del precio anterior.** Es el análisis con mejor relación valor/riesgo, y tiene
vara externa: la Directiva (UE) 2019/2161 exige que el «precio anterior» anunciado sea **el
más bajo aplicado en los 30 días previos**. Aquí el histórico es de 19 días, así que solo se
pueden marcar **indicios**, y hay que decirlo. Este proyecto ya tiene la pieza propia
(`oferta_sospechosa`: el precio base un 8 % por encima del de hace 45 días) y la versión
pública que sí se puede enseñar hoy: de 5.488 ofertas anunciadas cuyo precio no baja de su
precio de siempre, **3.658 dependen de cuántas unidades compres** (un 3x2 no baja el precio de
una unidad) y **288 no anuncian ningún descuento de precio**; se juzgan 1.538.
([Orientaciones de la Comisión, C(2021) 1229](https://eur-lex.europa.eu/legal-content/ES/TXT/PDF/?uri=CELEX:52021XC1229(06)&from=ES) ·
[UFC-Que Choisir: 9 de cada 10 «precios tachados» son falsas promociones](https://www.quechoisir.org/action-ufc-que-choisir-prix-barres-sur-les-sites-d-e-commerce-pres-de-9-sur-10-sont-de-fausses-promotions-n168388/))

**2. Detección de anomalías y escalones.** Con series cortas y muchísimos productos, la
cascada sensata es: reglas robustas (z-score sobre mediana y MAD, vallas de Tukey sobre el
rango intercuartílico) para picos y errores de captura, y detección de **puntos de ruptura**
(CUSUM, PELT) para escalones de precio. Ni STL ni Isolation Forest: el primero necesita dos
ciclos estacionales completos (aquí no hay ni uno) y el segundo no escala a 57.000 series sin
coste añadido. Y la advertencia que importa: **una bajada brusca suele ser una promoción
legítima**, así que el evento se etiqueta, no se borra.
([PELT con coste lineal](https://ar5iv.labs.arxiv.org/html/1101.1438) ·
[IsolationForest](https://scikit-learn.org/1.6/modules/generated/sklearn.ensemble.IsolationForest.html))

**3. El índice y su intervalo.** El índice encadenado tipo Jevons que ya existe mide el nivel
de precios de cada cadena comparando cada producto consigo mismo. Lo que le falta, según la
metodología oficial, es (a) **un intervalo de error** y (b) declarar la **cobertura del
eslabón** (cuántos productos sostienen el número). El intervalo sale casi gratis, porque el
índice ya es `exp(avg(ln(rel)))`: basta `exp(avg ± 1,96 · sd/√n)`. Y hay un riesgo metodológico
conocido que conviene comprobar: el **chain drift**, que se puede medir sin reescribir nada
recalculando el índice con las capturas en orden inverso y viendo cuánto se separa del
original.([Manual del IPC 2020 (OIT/FMI/OCDE)](https://www.dev.ilo.org/sites/default/files/wcmsp5/groups/public/%40dgreports/%40stat/documents/publication/wcms_761444.pdf) ·
[Chain drift (Ivancic, Diewert y Fox)](https://users.nber.org/~confer/2009/SI2009/PRB/Ivancic_Diewert_Fox.pdf) ·
[Métodos multilaterales en el IPCA (Eurostat/CEPE 2024)](https://unece.org/sites/default/files/2024-09/Multilateral%20Methods%20in%20the%20HICP_final.pdf))

**4. Clustering de categorías por dinámica.** Clusterizar categorías por volatilidad,
frecuencia de cambios de precio, profundidad promocional y tendencia es viable y útil (prioriza
qué mirar). Clusterizar productos con 19 puntos, no. La lección general: **la distancia importa
más que el algoritmo** (para series de precios, correlación o DTW suelen batir a la euclídea),
y sin etiquetas se valida con silueta, *gap statistic* y estabilidad por remuestreo.
([Gap statistic, Tibshirani 2001](https://cir.nii.ac.jp/crid/1571698599987819520) ·
[métricas de clustering](https://scikit-learn.org/1.6/modules/clustering.html#clustering-performance-evaluation))

## 4. Lo que se puede construir mañana (y su coste)

    medida de pair completeness del bloqueo      horas   decide si el 65 % es techo
    intervalo y cobertura del indice              horas   convierte un numero en una medida
    comprobacion de chain drift                   horas   descarta un sesgo conocido
    auditoria del precio anterior (30 dias)       dias    el analisis con mas valor externo
    deteccion de escalones con PELT               dias    errores de captura y subidas reales
    indice personal con la lista del usuario      dias    «cuanto ha subido lo mio»
    clustering de categorias por dinamica         dias    prioriza la monitorizacion

## 5. Lo que se aprende en este capítulo

- El catálogo de análisis posibles **se ordena por lo que los datos permiten**, no por lo que
  suena moderno. Tres de los doce análisis de la tabla son «no» y decirlo es parte del trabajo.
- Un análisis descriptivo bien acotado (dispersión de precios) vale más que uno inferencial mal
  identificado (elasticidad sin cantidades).
- Casi siempre hay una **vara externa** que sube el rigor: una directiva, un manual oficial, un
  índice publicado. Buscarla antes de inventar la propia métrica es lo que separa un análisis
  casero de un instrumento de medida.
