---
seccion: Análisis y decisión
resumen: Tres intentos medidos y descartados, con su número y su motivo.
en_una_frase: Tres modelos probados y descartados con su número: aquí el machine learning no aporta, y es la medición la que lo dice.
---

# 10 · Cuándo NO usar machine learning (tres intentos medidos y descartados)

Este capítulo es el que más valor tiene en un portfolio y el que casi nadie escribe: **tres
técnicas de machine learning que se probaron aquí, se midieron con datos y no se adoptaron**.
Saber decir que no —con números— es más difícil y más útil que saber decir que sí.

Ninguna de las tres se descartó «porque no me gusta»: cada una tiene su medida, su coste y el
motivo escrito en el código.

## 1. El canal de vectores: funcionaba, y rompía la garantía

**Qué se probó.** Calcular un embedding por producto (un vector de 384 números que representa el
nombre) y usarlo como **tercer canal** de candidatos para emparejar entre cadenas:
`data/gold/embedding.parquet`, 52.567 productos, 190 MB.

**Lo que se ganó, medido sobre el mismo catálogo** (`docs/DIAGNOSTICO-MATCHING.md`,
`emparejar.py`):

    metrica                    sin vectores   con vectores   diferencia
    enlaces                          22.705         26.703   +3.998 (+18 %)
    grupos comparables                7.992          8.394     +402 (+5 %)
    productos comparables            22.693         24.823   +2.130 (+9,4 %)
    recall de --medir                 65 %           73 %       +8 puntos

**Y lo que se rompió, medido igual:**

    conflictos de asignacion              0            861
    peor caso (un producto con varios
      productos de la MISMA cadena)        2              3

**Por qué pasa, y es lo interesante.** El emparejador respeta el 1-a-1 **dentro de cada canal**:
cada canal hace su propio reparto húngaro con su propio juego de «ocupados». Los dos canales del
nombre nunca produjeron un conflicto; el tercero sí, porque entra después y puede asignar un
producto a algo que el otro canal ya había ocupado de otra manera. El resultado son 861
productos emparejados con **tres** productos de la misma cadena: la garantía del encargo
(*cero conflictos de asignación*) rota.

**La decisión**: el canal está **apagado** (`USAR_VECTORES = False`), y la condición para
encenderlo está escrita: que sus candidatos pasen **por el mismo reparto y los mismos `ocupados`**
que los otros dos. Y se vuelve a medir entero —recall **y** conflictos— antes de encenderlo.

> **La lección, en una frase:** un canal que sube el recall rompiendo la asignación no es una
> mejora, es otro emparejador. Un +8 % de recall no compensa perder la única garantía
> estructural del sistema.

Y un detalle de ingeniería que también enseña: el coste, que era el otro obstáculo, se resolvió
leyendo los vectores **en SQL** en vez de traerlos a Python (239,9 s y 270 MB), así que hoy el
motivo del apagado no es el coste.

## 2. El medoide: la idea era buena, el umbral no se pudo calibrar

**Qué se probó.** Como **segunda red** (no en lugar de la invariante): para cada grupo, calcular
el **medoide** (el miembro con mayor parecido medio a los demás) y expulsar a quien esté por
debajo de un umbral. La invariante caza lo que se funde **entre** cadenas; el medoide cazaría lo
que se funde **dentro** de un grupo legítimo.

**Cómo se calibró.** Contra el banco de pares: se quiere el umbral que **no expulse ningún par
cierto con EAN compartido**.

**Lo que se midió** (`docs/BACKLOG.md`, `projects/cesta/cohesion.py`):

    cohesion minima de un grupo MALO (el que había que cazar)     0,719
    cohesion minima del BANCO de pares ciertos                    0,511

Es decir: **los pares ciertos tienen cohesión más baja que el grupo malo**. La separación va al
revés de lo que la idea necesitaba, así que un umbral que expulse al grupo malo expulsa antes a
pares que son ciertos. La métrica no separa las dos clases, y ninguna calibración arregla eso.

**La decisión**: no se adopta, y queda escrito con sus dos números (que es lo que permite
revisarlo si algún día cambia el banco o la similitud). *«El umbral se calibra contra el banco de
pares, no se elige a ojo»* — y al calibrarlo, la respuesta fue que no hay umbral.

> **La lección:** calibrar contra un banco no es un trámite: es el experimento. Y su resultado
> puede ser «esta señal no distingue», que también es un resultado.

## 3. Los modelos de decisión (Jev y Laya): el cuello de botella no era el juicio

**Qué se probó.** Meter un modelo de salida forzada («system 1»: devuelve una opción entre varias
con su probabilidad, sin generar texto) para **clasificar los ejes de atributo** de los nombres
de producto: *entera / semidesnatada / desnatada*, *virgen extra / virgen / orujo*… Son doce ejes
escritos a mano en `core/atributos.py` (28 valores, 71 patrones de subcadena), y cada eje nuevo
es trabajo manual.

**Por qué parecía buen sitio.** El `state` es el nombre (veinte palabras), las opciones son los
valores del eje más «no lo dice», y la regla de la casa —*el que calla no bloquea*— se implementa
con la probabilidad que el modelo devuelve. Y hay **banco de pruebas gratis**: las listas a mano
son la verdad de referencia.

**Lo que se midió.** Con Jev (API en lista de espera) el experimento estaba bloqueado. Con **Laya**
(pesos abiertos Apache 2.0, corre en CPU en este PC) se pudo hacer, y se hizo
(`docs/LAYA.md`, `projects/cesta/laya_ejes.py`):

    215 nombres, 316 declaraciones de las listas a mano, los 12 ejes
    acuerdo 231 (73,1 %)      la barra pide 97 %
    se abstiene 48 · declara otro valor 37 · declara donde la lista calla 1.230 de 2.264 (54 %)

Dos fallos sistemáticos, no ruido: **11 veces contesta `sin grasa`** donde el nombre dice entera o
semidesnatada, y **6 veces `natural`** donde dice descafeinado. Y el 54 % de declaraciones donde el
nombre no dice nada es el número más peligroso, porque con la regla «el que calla no bloquea» esas
declaraciones **cortarían comparaciones legítimas** si entraran como guarda.

**Y la parte que se ganó sin querer.** Auditar los 85 desacuerdos uno a uno encontró **27 fallos
de nuestras propias listas**: `leche` declarando «bebida vegetal» en cualquier cosa con arroz o
avena, `cafe` declarando «soluble` con «instantáneo», `integral` disparando en «vino blanco»,
`azucar` disparando dentro de una negación. Es decir: **el experimento con un modelo sirvió para
encontrar bugs en el código propio**, que se arreglan sin ningún modelo.

**La decisión**: no se integra en la cadena diaria, y el motivo es el mismo que el de Jev, ahora
con número: el 64 % de lo que el nombre no encuentra son **números** (formato, unidad, cantidad),
y su propia tarjeta dice que la puntería de estos pesos viene del *fine-tuning*, no del cero. Las
dos rutas siguientes están escritas y ordenadas: arreglar las listas (barato) y, si alguien
quiere gastar una GPU, afinar con nuestras etiquetas.

> **La lección:** antes de meter un modelo, comprueba **cuál es el cuello de botella**. Aquí no
> era el juicio semántico: era aritmética de envases y datos mal leídos.

## 4. La calibración: cuando el modelo dice «0,9» y no significa 0,9

Una cosa es acertar y otra **saber cuánto acierta**. Un modelo está *calibrado* si cuando dice
«0,9» acierta el 90 % de las veces. Se mide con el **ECE** (*Expected Calibration Error*): se
agrupan las predicciones por confianza y se compara la confianza media con la tasa de acierto.

Y esto importa aquí porque **la regla del proyecto depende de la confianza**: «el que calla no
bloquea» se implementa con un umbral (`confianza < 0,9 → no lo dice`), así que si la confianza no
significa lo que dice, la regla entera se sostiene en el aire.

Lo medido, de las dos fuentes que se probaron:

    Laya   "ships over-confident": recalibrar una temperatura por (tipo de pregunta, numero de
           opciones) mueve el ECE de 0,466 a 0,081 -- o sea, antes de recalibrar sus
           probabilidades no se pueden tomar al pie de la letra
    Jev    ECE publicado 0,246; y su propio `Score` documenta que no se puede reconstruir el
           numero exacto interpolando entre niveles

Y una advertencia publicada sobre la otra vía: **la confianza de un LLM como verificador tampoco
está bien calibrada** ([Confidence Calibration in LLM-Based Entity Matching](https://aclanthology.org/2025.uncertainlp-main.12/)),
así que «usar la confianza para decidir» no es gratis en ningún caso: hay que medirla en tus
propios datos.

> **La lección:** antes de automatizar una decisión con un umbral de confianza, comprueba con
> datos propios que la confianza significa algo. Un modelo sin calibrar y un umbral son dos
> errores que se multiplican.

## 5. El patrón que comparten los tres

    intento                    lo que prometia        lo que se midio            decision
    canal de vectores          +8 puntos de recall    861 conflictos de           apagado, con la
                                                      asignacion                 condicion escrita
    medoide como 2a red        cazar fusiones         no separa: 0,511 contra    no adoptado, con
                                                      0,719                      sus dos numeros
    modelo de decision (Laya)  clasificar ejes        73,1 % frente a 97 %, y    no integrado; dejo
                                                      54 % sin prueba            27 bugs propios

Los tres tienen tres cosas en común, y son la lección del capítulo:

1. **Se midieron contra un banco que ya existía** (pares con EAN, listas a mano, invariantes).
   Sin banco no hay decisión, hay opinión.
2. **Se midió también lo que se rompía**, no solo lo que se ganaba: los conflictos, la separación
   de clases, las declaraciones sin prueba.
3. **Se dejó escrito el camino de vuelta**: qué habría que arreglar para encenderlos. Un «no» sin
   condiciones es tan malo como un «sí» sin medida.

## 6. Lo que se aprende en este capítulo

- Un modelo no arregla un problema de datos: **mide el cuello de botella antes** (aquí: 64 % de
  aritmética de envases).
- Una mejora que rompe una garantía estructural **no es una mejora** (+8 puntos de recall con 861
  conflictos).
- Calibrar contra un banco puede terminar en «esta señal no separa», y eso es un resultado, no un
  fracaso.
- Auditar los desacuerdos de un modelo es una de las mejores formas de **encontrar bugs propios**
  (27 listas mal escritas aparecieron así).
- Deja siempre escrito **por qué no** y **qué haría falta para que sí**.
- Y si vas a decidir con un umbral de confianza, **mide la calibración** en tus datos antes: un
  modelo sobre-confiado y un umbral son dos errores que se multiplican.
