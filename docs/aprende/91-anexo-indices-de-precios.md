# Índice de precios con datos de escáner: teoría, práctica oficial y auditoría del proyecto

**Alcance.** Reviso la metodología publicada y la contrasto con lo que hace este repositorio: `plataforma/api/analisis.py` (índice), `core/derive.py` ("precio de siempre"), `core/promos.py` (mecánicas de oferta) y `core/comparacion.py` (ventanas). Lo que afirmo del proyecto sale de leer su código, no de medir sus datos.

**Aviso previo.** El encargo describe un recorte de relativos fuera de **0,5x–2x**, pero el código usa **1/3–3** (`RECORTE_MIN = 1.0/3`, `RECORTE_MAX = 3.0`). Conviene decidir la política y dejarla escrita en un solo sitio.

## 1. Fórmulas de índice y agregados elementales

Laspeyres fija la cesta base `L = Σp_t·q_0 / Σp_0·q_0` y exagera la subida al no admitir sustitución; Paasche usa la corriente `P = Σp_t·q_t / Σp_0·q_t` y se queda corto; Fisher `F = √(L·P)` y Törnqvist `T = Π (p_t/p_0)^((s_0+s_t)/2)`, con `s` la cuota de gasto, son superlativos; Törnqvist es el estándar con datos de escáner porque necesita cantidades. En el nivel elemental, Carli (media aritmética de relativos), Dutot (cociente de medias) y Jevons (media geométrica de relativos): el manual del IPC de OIT/FMI/OCDE/CEPE/Banco Mundial recomienda **Jevons**, porque Carli tiene sesgo al alza y Dutot depende de la dispersión de precios.

**Qué cambiaría.** El Jevons encadenado está bien elegido, pero es **sin ponderar**: un producto de 0,09 € pesa lo mismo que uno de 30 €. Las cantidades ya se deducen en `plataforma/api/movimientos.py` (`precio_cent / precio_unidad_cent`), así que se puede publicar un Törnqvist junto al Jevons. [Manual del IPC 2020](https://www.dev.ilo.org/sites/default/files/wcmsp5/groups/public/%40dgreports/%40stat/documents/publication/wcms_761444.pdf) · [Consumer Price Index Manual (FMI)](https://data.imf.org/-/media/iData/External-Storage/Documents/094CFD9697F645FBA6B4F720A062A35D/en/Consumer-Price-Index-Manual.pdf).

## 2. Encadenamiento y *chain drift*

Si un precio rebota (100 → 50 → 100 por una promoción), el índice encadenado puede acabar por debajo de 100: imposible comparando el mismo producto consigo mismo. Ivancic, Diewert y Fox documentaron ese *drift*, y la respuesta estándar hoy son los índices **multilaterales** —GEKS-Törnqvist sobre ventana rodante, con empalme para no reescribir la historia—, práctica habitual con datos de escáner según Eurostat. Los bilaterales se usan, sabiendo que el *drift* crece con la longitud de la cadena y la frecuencia de promociones.

**Qué cambiaría.** El índice encadena capturas **diarias** contra la anterior de la misma cadena: el escenario exacto del *drift*. Comprobación barata antes de reescribir nada: recalcular con las capturas en orden inverso y medir cuánto se separa del original. [Ivancic, Diewert y Fox](https://users.nber.org/~confer/2009/SI2009/PRB/Ivancic_Diewert_Fox.pdf) · [Multilateral Methods in the HICP (Eurostat/CEPE 2024)](https://unece.org/sites/default/files/2024-09/Multilateral%20Methods%20in%20the%20HICP_final.pdf).

## 3. Productos que aparecen y desaparecen

Un índice emparejado sólo mide lo que está en las dos capturas: los productos nuevos y los que salen no existen para el cálculo, y ahí vive la sustitución. La guía práctica de Eurostat sobre datos de supermercado distingue enfoque "estático" (imita la muestra fija, tratando los relanzamientos como productos nuevos) y "dinámico", recomienda un **filtro de bajas ventas** y usa hedónicos multilaterales para relanzamientos con EAN nuevo. El ajuste por tamaño de envase es en rigor un reescalado de cantidad, no un ajuste de calidad.

**Qué cambiaría.** El proyecto no imputa ni enlaza —es el enfoque estático— pero debería declararlo y **publicar la cobertura del eslabón** (`n` frente al catálogo de esa cadena ese día) como métrica de calidad del número. [Practical Guide to Supermarket Scanner Data](https://circabc.europa.eu/sd/a/8e1333df-ca16-40fc-bc6a-1ce1be37247c/Practical-Guide-Supermarket) · [Using multilateral hedonic methods to capture product relaunches (CEPE 2023)](https://unece.org/sites/default/files/2023-05/1a.3%20Using%20multilateral%20hedonic%20methods%20to%20capture%20product%20relaunches.pdf).

## 4. Promociones y precios temporales

Las rebajas temporales son frecuentes y cuantitativamente relevantes. La regla estándar es doble: entra el precio rebajado **si está disponible para cualquier comprador**, y queda fuera si es condicional (tarjeta, cupón, sólo online). Las promociones de varias unidades (3x2, 2ª unidad -50%) no cambian el precio de la unidad suelta pero sí el coste por unidad, y por eso el proyecto las modela aparte. **No lo sé**: no he encontrado una regla oficial explícita sobre cómo debe entrar una promoción de lote en el índice.

**Qué cambiaría.** Excluir `acumulable` y `solo_online` con `util` está alineado con "disponible para todos": bien. Falta escribir la decisión ya tomada de facto: el índice usa `precio_cent`, precio de **una** unidad, sin promociones de lote. [Alternative data aggregates in consumer prices (ONS)](https://cy.ons.gov.uk/economy/inflationandpriceindices/methodologies/alternativedataaggregatesinconsumerprices/pdf) · [Reglamento (UE) 2020/1148 (IPCA)](https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:02020R1148-20240711).

## 5. Precio por unidad de medida

La [Directiva 98/6/CE](https://eur-lex.europa.eu/legal-content/ES/TXT/PDF/?uri=CELEX:01998L0006-20220528) obliga a indicar el precio por unidad de medida (€/kg, €/l, €/m) para que dos envases distintos se puedan comparar: comparar €/kg con €/ud no produce una diferencia, produce un disparate. La *shrinkflation* —menos gramos al mismo precio— se mide precisamente con €/kg, y un tamaño mal leído (400 g que eran 400 mg, un pack de 30 leído como 1) contamina todo lo que se calcule sobre el precio unitario.

**Qué cambiaría.** Aquí el proyecto va por delante de la media: `unidad_canon`, unidad dominante por grupo comparable, ventanas particionadas por producto **y** unidad, y precio por unidad recalculado en casa en vez de fiarse del campo nativo de la cadena. Añadiría un control de plausibilidad **por sección** (€/kg fuera del percentil 0,1–99,9 → no comparable), porque hoy la única barrera global es el factor 30. [Polidoro y otros, *Shrinkflation* (Ottawa Group)](https://stats.unece.org/ottawagroup/download/Polidoro_and_others_on_shrinkflation.pdf) · [Ajuste por tamaño de envase (dspace.vsb.cz)](https://dspace.vsb.cz/bitstream/handle/10084/137827/KSGQ17015ENN.en.pdf).

## 6. Qué estadístico usar para "el precio normal"

Con cola larga —0,09 €/ud y 6.875 €/kg en el mismo catálogo— la media es inservible: un extremo la desplaza. La mediana tiene punto de ruptura del 50 % y la media recortada o winsorizada es el compromiso entre robustez y eficiencia; el manual del IPC usa el algoritmo de **Tukey** para validar series con muchos ceros de variación, que es el caso de un precio quieto 25 de cada 30 días.

**Qué cambiaría.** Hoy es una mediana móvil de 30 observaciones con `min_samples=7`: siete puntos son pocos para una mediana robusta, y "30 observaciones" no es "30 días" si hay huecos (el propio proyecto documenta días sin captura). Subiría `min_samples` a ~15, publicaría cuántas observaciones sostienen cada mediana y, si se quiere más eficiencia, usaría recorte al 10 %. [Manual del IPC 2020, §5.132 y §4.89](https://www.dev.ilo.org/sites/default/files/wcmsp5/groups/public/%40dgreports/%40stat/documents/publication/wcms_761444.pdf).

## 7. Cauciones estadísticas

Un índice arrastra dos errores: el de **muestreo** —se observa una muestra, no el universo, y por eso los institutos publican varianzas— y el ajeno al muestreo, donde el **error de cobertura** suele pesar más con datos de escáner. Un catálogo que cambia de tamaño cada día mezcla ambos: si el eslabón pasa de 260.000 a 240.000 productos, parte de la variación es composición, no precio. Sobre mínimos por celda, **no lo sé** con precisión: Eurostat documenta un filtro de códigos de bajas ventas, pero no he encontrado una cifra oficial de observaciones mínimas por agregado.

**Qué cambiaría.** Publicar un intervalo aproximado —`exp(avg(ln rel) ± 1,96·sd/√n)`, inmediato porque el índice ya es `exp(avg(ln(rel)))`—, fijar un mínimo de productos por eslabón (en `posicion` ya hay 15, en el índice ninguno) y separar en la interfaz "cambió el precio" de "cambió el conjunto comparado". [BLS, Variance Estimates for the CPI](https://www.bls.gov/cpi/tables/variance-estimates/home.htm) · [Practical Guide to Producing CPI (UN Statistics)](https://unstats.un.org/wiki/download/attachments/101354122/Practical_Guide_to_Producing_CPI.pdf).

## 8. Aplicaciones que se pueden construir

Con índice por cadena, "precio de siempre" y posición en 90 días salen: la **inflación personal de una cesta** (como el [calculador de la ONS](https://www.ons.gov.uk/visualisations/dvc1833/calculator/index.html)), la **comparación de la subida por cadena y categoría**, el "**cuánto ha subido lo que yo compro**" con el histórico propio, y la **detección de subidas antes de una promoción**, donde la norma da vara externa: la [Directiva (UE) 2019/2161](https://www.legislation.gov.uk/eudr/2019/2161/article/2/adopted) obliga a anunciar como precio anterior el **más bajo de los 30 días previos**, así que `oferta_sospechosa` (base un 8 % por encima de la de hace 45 días) es una versión propia y comprobable de una exigencia legal. Su valor en un portfolio: no es un comparador, es un instrumento de medida con `n`, salto y recortes declarados. **No lo sé**: no he encontrado series públicas españolas de precios por cadena con las que validar el índice externamente. [Banca d'Italia, QEF 883/2024](https://www.bancaditalia.it/pubblicazioni/qef/2024-0883/QEF_883_24.pdf) · [ONS, How multilateral index methods help us understand grocery scanner data](https://www.ons.gov.uk/economy/inflationandpriceindices/methodologies/howmultilateralindexmethodshelpusunderstandgroceryscannerdata/pdf).

## Tabla de auditoría

| Práctica | Qué dice la fuente oficial | Qué hace el proyecto | Veredicto | Cómo comprobarlo |
|---|---|---|---|---|
| Fórmula elemental | Jevons sin ponderaciones; con escáner hay cantidades (manual IPC; ONS) | Jevons encadenado sobre relativos emparejados | **Mejorable**: sin ponderación por gasto | Calcular Törnqvist con cuotas y comparar series |
| Encadenamiento | Los bilaterales encadenados sufren *drift*; se propone GEKS-Törnqvist | Encadena captura a captura, base 100 la primera | **Mejorable**: sin control de *drift* | Recalcular en orden inverso y medir la vuelta a 100 |
| Entradas y salidas | Enfoque estático o dinámico, filtro de bajas ventas, hedónicos | Matched model puro, sin imputar ni enlazar | **Mejorable**: cobertura del eslabón no declarada | Publicar `n` frente al catálogo de la cadena y fecha |
| Recorte de relativos | Validación con algoritmo de Tukey (manual IPC §5.132) | Recorte fijo `[1/3, 3]`, contado y mostrado | **Mejorable**: fijo y discrepante de lo documentado | Comparar recorte fijo contra Tukey |
| Precio usado y descuentos | El precio observado; el rebajado sólo si es para todos; fuera tarjeta, cupón y sólo-online | Precio de venta de una unidad; `acumulable` y `solo_online` fuera de `util` | **Bien** (evita errores de formato), sin declarar el efecto del lote | Listar las mecánicas excluidas y recalcular con `Mecanica.coste` |
| Promociones de lote | Recogidas por los datos de escáner; regla del índice: **no lo sé** | Modeladas aparte, no entran en `precio_cent` | **Mejorable**: decisión correcta pero implícita | Documentarla y probar sensibilidad del índice |
| Unidad de medida | Directiva 98/6/CE; el tamaño es cantidad, no calidad | Unidad canónica, dominante por grupo, ventanas por unidad | **Bien** | `test_derive`/`test_comparacion`: 2.239 productos con dos unidades |
| Tamaño mal leído | Vigilancia de €/kg fuera de rango (*shrinkflation*) | Factor global 30 y factor llamativo 3 | **Mejorable**: falta control por sección | Percentil 0,1–99,9 de €/kg por sección |
| Precio normal | Mediana robusta; Tukey con muchos ceros | Mediana móvil 30 obs, `min_samples=7` | **Mejorable**: 7 obs es poco; "30 obs" ≠ "30 días" | Distribución de obs por ventana; probar `min_samples=15` |
| Error del índice | Error de muestreo y de cobertura; se publica varianza | Publica `n`, salto y recortes, sin intervalo | **Mejorable**: falta intervalo | `exp(avg ± 1,96·sd/√n)` sobre `ln(rel)` |
| Mínimo por celda | Filtro de bajas ventas (Eurostat); mínimo oficial: **no lo sé** | 15 en `posicion`; ninguno en el índice | **Mejorable** por asimetría | Añadir umbral y ver qué celdas desaparecen |
| Subida antes de promo | Directiva 2019/2161: precio anterior = mínimo de 30 días | `oferta_sospechosa`: base > base de hace 45 días × 1,08 | **Bien** como criterio propio, sin citar la norma | Contar marcadas y contrastar con el mínimo de 30 días |
