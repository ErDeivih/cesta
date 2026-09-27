---
seccion: Algoritmos y evaluación
resumen: Resolución de entidades: bloqueo, similitud, reparto húngaro y los ejes del nombre.
en_una_frase: Decidir que dos ofertas son el mismo producto no lo resuelve una regla: se bloquea, se puntúa y se reparte uno a uno.
---

# 04 · Emparejar productos: el método

El problema central del proyecto, y el que más enseña: **decidir cuándo dos fichas de dos
cadenas distintas son el mismo producto**. En la literatura esto se llama *entity resolution*
o *record linkage*, y es un problema viejo (Fellegi y Sunter, 1969) con una industria entera
detrás (deduplicar clientes, unir catálogos, fusionar registros médicos).

    "Leche entera MILSANI 1 l"          Alcampo,  1,09 EUR
    "Leche entera Hacendado 1 l"        Mercadona, 1,05 EUR
    "Leche entera LAUKI 6 x 1 l"        DIA,       6,30 EUR

El tercero es el mismo producto **en otro formato**, y ahí está la trampa: sin darse cuenta,
un emparejador ingenuo compararía 1,09 €/l con 1,05 €/l (correcto) y con 1,05 €/l del pack de
6 (mal, si no normaliza). Comparar mal aquí no da un error pequeño: da «te ahorras 5,25 €» en
la ficha de la leche.

Este capítulo cuenta **qué decide** cada paso. Las fórmulas --Dice, el IDF, la mezcla con los
trigramas, la ganancia del reparto húngaro y los cuatro frenos-- están una a una en el
**anexo 93**, con sus símbolos y el número que dan sobre este catálogo.

## 1. La teoría, en cuatro pasos

Todo sistema de *entity resolution* serio tiene las mismas cuatro etapas, y conviene
reconocerlas porque cada una tiene su propia métrica y sus propios errores:

1. **Bloqueo**: no se comparan todos los pares posibles (con 57.000 productos serían 1.600
   millones), sino solo los que comparten algo (marca, categoría, primeras letras). El bloqueo
   decide **el techo del recall**: un par que nunca cae en el mismo bloque es imposible de
   encontrar, por muy bueno que sea el matcher. Sus dos métricas son *pair completeness*
   (cuántos pares verdaderos quedan juntos) y *reduction ratio* (cuántos pares te ahorras).
   ([Blocking and Filtering Techniques for Entity Resolution: A Survey](https://dlnext.acm.org/doi/fullHtml/10.1145/3377455))
2. **Comparación**: para cada par candidato se calcula una similitud. Las clásicas son de
   cadena (Jaro-Winkler para nombres cortos, Levenshtein para erratas, Jaccard/Dice por
   tokens para títulos reordenados) y las modernas son aprendidas (transformers que leen los
   dos registros juntos).
   ([Neural Networks for Entity Matching: A Survey](https://arxiv.org/abs/2010.11075))
3. **Clasificación**: se decide enlace, no enlace o duda, con un umbral. El marco de
   Fellegi-Sunter estima, por campo, la probabilidad de que coincida *siendo* el mismo
   registro (*m*) y *sin serlo* (*u*), y combina los pesos en un logaritmo de verosimilitud.
4. **Agrupación**: los enlaces se convierten en grupos (clusters) y aquí aparece el problema
   de la **transitividad**: si A≈B y B≈C, ¿A≈C? Con componentes conexas, sí por construcción
   — y por eso **un solo falso positivo puede fusionar dos grupos enteros**. La alternativa
   formal (clustering correlacional con restricciones *must-link* / *cannot-link*) es
   NP-dura, así que en la práctica se usan umbrales y reparaciones locales.

## 2. Lo que hace este proyecto

El reparto de tareas, en el código:

    bloqueo        (unidad_canonica, round(cantidad, 3)) -- el formato, o ("?") si falta
    similitud      Dice ponderada por IDF sobre tokens, mas trigramas para erratas
    asignacion     reparto hungaro 1-a-1 POR CADA PAR DE CADENAS
    agrupacion     componentes conexas, con una segunda red que rechaza contradicciones

El bloqueo real es **el formato** —misma unidad canónica y misma cantidad redondeada a tres
decimales—, y el capítulo 93 lo tiene con su cuenta completa: sin él habría que comparar 52.824
productos entre sí (1.395 millones de pares), y deja 14,9 millones dentro del bloque, de los que el
emparejador puntúa 3,5 millones. Un bloqueo por marca o por categoría sería **peor aquí**: la marca
blanca de una cadena no se llama como la de la otra, y la categoría de Alcampo no es la de DIA, así
que bloquear por ahí dejaría fuera justo los pares que este proyecto busca. Está en la lista de
trabajo futuro del capítulo, con el coste dicho.

Tres decisiones merecen explicación, porque no son las obvias:

**IDF: no todas las palabras pesan igual.** «Leche» aparece en miles de fichas y no
distingue nada; «MILSANI» aparece en unas pocas y distingue mucho. Ponderar cada token por su
frecuencia inversa (IDF) es lo que hace que dos fichas que comparten la marca rara se parezcan
mucho y dos que comparten «leche entera» no. Es la misma idea que usan los buscadores.

**El húngaro, y por qué 1-a-1.** Entre Alcampo y DIA se comparan miles de productos; si se
enlazara cada uno con su candidato más parecido sin más, dos productos de Alcampo podrían
acabar enlazados al mismo de DIA. El **algoritmo húngaro** resuelve la asignación óptima
uno-a-uno entre dos conjuntos con un coste, y aquí se aplica **por cada par de cadenas** (10
pares con 5 cadenas). Consecuencia práctica que descubrió este proyecto: los enlaces son
1-a-1 por par, pero los grupos se forman uniendo esos enlaces, así que un grupo **puede**
acabar con dos productos de la misma cadena sin que ningún enlace individual esté mal. Eso se
llamó «la invariante del reparto» y se mide aparte (capítulo 05).

**La segunda red: el eje que el nombre declara.** Un grupo puede mezclar «leche entera» con
«leche desnatada» si el camino pasa por «leche semidesnatada». Lo que corta no es el margen de
precio (eso borraría ahorros reales de 28×, que es justo lo que la aplicación busca), sino lo
que **el nombre declara**: `core/atributos.py` tiene doce ejes (grasa, aceite, gas, alcohol,
cafeína, azúcar, integral, lactosa, gluten, formato, café, leche) con sus valores, y una regla
que es la clave de todo el proyecto:

> **el que calla no bloquea.** Un producto que no dice si es entera o desnatada no está
> afirmando que sea igual: es que no lo sabemos.

Resultado medido el 24 de septiembre de 2026 (`uv run python -m projects.cesta.ejes`):

    grupos con algun eje contradictorio        0   (venian de 49)
    grupos de 11 o mas productos               0   (venian de 74)
    con la misma cadena repetida sin EAN       0   (venian de 1.385)

## 3. La verdad de referencia: el código de barras

Para saber si el emparejador acierta hace falta saber cuál es la respuesta correcta, y eso es
caro... salvo que tengas el **EAN**. Cuando dos fichas de dos cadenas comparten código de
barras, son el mismo producto **sin discusión**: es un banco de pares ciertos, gratis, y sin
él este proyecto no tendría forma de medir nada.

    banco de pares ciertos (mismo EAN en dos cadenas)     1.799
    pares que el emparejador encuentra de esos            1.161   (65 %)
    tiempo de una pasada de --medir                       498 s

(cifras de la última pasada: `uv run python -m projects.cesta.emparejar --medir`)

Ese 65 % es el número más importante del proyecto. Y hay tres cosas que decir sobre él, que
valen más que el número:

1. **Es un techo estructural, no una nota del modelo.** Si un par no cae nunca en el mismo
   bloque, no se puede encontrar. La primera medición que hay que hacer antes de tocar el
   matcher es la *pair completeness* del bloqueo: cuántos de esos 1.799 pares comparten
   bloque. Si son el 65 %, mejorar el matcher no sirve de nada.
2. **El banco está sesgado a favor de las marcas conocidas.** Los productos con EAN son los
   de marca (el 50 % del catálogo no lo tiene), así que medir solo ahí mide lo fácil. Los
   números de este proyecto se dan siempre por separado para marca y marca blanca.
3. **El EAN es también una restricción gratuita.** Dos fichas con el mismo EAN **son** el
   mismo producto (*must-link*) y dos con EAN distinto y no vacío **no** lo son
   (*cannot-link*). Son las restricciones que en la literatura se piden a un clustering con
   restricciones, y aquí salen gratis del dato.
   ([A Practitioner's Guide to Evaluating Entity Resolution Results](https://arxiv.org/abs/1509.04238))

## 4. Las trampas, con el caso que las enseñó

Cada una de estas se descubrió **midiendo**, y están todas en el registro del proyecto
(`docs/DIAGNOSTICO-MATCHING.md` es el informe entero):

| Trampa | Qué pasó |
|---|---|
| Packs contra unidades | «Agua 1,5 l» y «pack 6 × 1,5 l» se emparejan bien, pero el precio por unidad engaña si el pack no se declara |
| Formatos ilegibles | `1,75 cl` contra `175 ml`: el mismo líquido con el número en otra unidad |
| El número manda | Añadir un atributo numérico sin normalizar **empeora** un matcher: la evidencia publicada coincide ([Using ChatGPT for Entity Matching](https://arxiv.org/abs/2305.03423)) |
| Embeddings y números | 13 modelos de embeddings evaluados tienen dificultades documentadas para representar detalles numéricos: dos envases que solo difieren en el número salen casi idénticos ([Revealing the Numeracy Gap](https://arxiv.org/abs/2509.05691)) |
| Falso positivo puente | Con componentes conexas, un enlace malo puede fusionar dos grupos legítimos enteros |
| Sobre-bloqueo por marca blanca | Si la marca es «Hacendado» o está vacía, el bloque es gigantesco (no reduces nada) o vacío (pierdes el par) |

## 5. Lo que se puede probar, en orden de coste

Esto es la cola de trabajo que sale de la investigación de septiembre de 2026, ordenada por
coste (el detalle con fuentes, en el **anexo 90**):

    coste casi nulo    medir la pair completeness del bloqueo (antes de tocar nada)
                       aplicar must-link/cannot-link por EAN como corte
                       normalizar unidades y packs (cl -> ml, "6 x 1,5 l" -> 9.000 ml)
    coste bajo         clave de bloqueo marca + tamano normalizado + categoria
                       auditoria de 200 desacuerdos: ¿fallo de bloqueo o de matching?
    coste medio        bi-encoder afinado con triplet loss sobre los positivos EAN
                       verificador LLM solo en la banda dudosa (~0,1 centimo por par)
    coste alto         cross-encoder tipo Ditto (necesita miles de etiquetas; hay 1.809 pares)
                       reparacion de grafo / clustering correlacional aproximado

Y lo que **no** merece la pena, que también es una conclusión: con 1.809 pares no se afina un
cross-encoder grande; el LLM no se usa para bloquear ni para decidir todo (coste lineal y
calibración discutida: [Confidence Calibration in LLM-Based Entity Matching](https://aclanthology.org/2025.uncertainlp-main.12/));
y no se persigue un modelo mejor antes de arreglar el bloqueo y las unidades.

## 6. Lo que se aprende en este capítulo

- El *entity resolution* es un problema con cuatro etapas, y **cada etapa tiene su métrica**.
  Confundirlas es lo que hace que la gente cambie de modelo cuando el problema era el bloqueo.
- Un banco de verdad barato (el EAN) vale más que cualquier técnica: sin él no hay medida.
- Las restricciones gratuitas del dato (*must-link* / *cannot-link*) son el mejor retorno por
  línea de código escrita.
- La regla «el que calla no bloquea» es ingeniería de datos disfrazada de sentido común: sin
  ella, un dato ausente se convierte en una afirmación falsa.
