# Jev, verificado contra las fuentes primarias

Escrito el 23 de septiembre de 2026. Se verificó cada dato contra la
documentación oficial (`typesafe.ai`, `docs.typesafe.ai`), la Wikipedia y la
prensa técnica, y se cruzó con los números medidos de este proyecto.

**Veredicto:** Jev existe, está bien diseñado para lo suyo, y aquí cuesta
céntimos. Pero **el cuello de botella de Cesta no es el juicio semántico**, y la
propia documentación de Jev descarta por escrito los dos usos que más falta nos
hacen. Hay un sitio donde sí encaja, y no es el que proponía ninguno de los dos
informes anteriores.

---

## 1. Qué es, confirmado

| | |
|---|---|
| Quién | TypeSafe AI, San Francisco, fundada en 2024 por **Diogo Almeida, Erik Gafni y Sasha Sheng**. Almeida estuvo cuatro años en OpenAI (ChatGPT y GPT-4) |
| Cuándo | **15 de septiembre de 2026**, acceso anticipado limitado. Versión estable `jev-1.13.0` |
| Qué hace | Devuelve **valores tipados con probabilidad y confianza**, no texto. Tres primitivas: `Choice` (elegir entre opciones), `Score` (puntuar en niveles), `Noul` (0–1) |
| Salida | `Choice` y `Score` devuelven **`confidence`**; `Noul` **no** — sólo el número |
| Contexto | **64k** por petición; **32k** para el `state` más la pregunta más larga |
| Límites | **1.200 peticiones/min**, **250.000 tok/s**. La documentación avisa de que «los límites se ajustan dinámicamente» y pueden cambiar sin aviso |
| Precio | **$0,042 / Mtok** de entrada; salida gratis («demasiado barata para medirla») |
| Arquitectura | Transformer entrenado **sólo con datos sintéticos**, con RLCD (*Reinforcement Learning for Calibrated Decisions*). **No hay artículo, ni pesos, ni recuento de parámetros publicados** |
| Cardinalidad | máximo **255** opciones en una sola etapa |
| Imágenes | no, sólo texto y JSON |

El nombre viene de la **paradoja de Jevons**: si decidir sale casi gratis, se
decide mucho más. Eso es también su apuesta de negocio, y conviene saberlo.

---

## 2. Lo que corrijo del informe anterior

El informe que se pasó es, en lo técnico, **correcto casi en todo**: precio,
primitivas, cardinalidad de 255, límites, que `Noul` no trae confianza, que la
frase «no puede alucinar» es **estructural y no factual**, y que las webs
`jevtypesafeai.com` y `jevai.org` no son oficiales. Todo eso se confirma.

**Lo que está mal, y no es menor:**

> «Eval propia: Jev 76,0 % vs **GPT-5.6 Luna** 76,1 %, **DeepSeek V4 Flash**
> 76,8 %, **GPT-6 Sol** 79,1 %»

Esos tres nombres no existen. El blog oficial compara contra **GPT-5.6 Terra**,
**GPT-6 Astra** y **Fable 5.1**. Una tabla con cifras de acierto atadas a modelos
inventados es justo la clase de dato que este proyecto no acepta: **si los
nombres son falsos, las cifras no se pueden comprobar**, y entonces no son una
medida, son una impresión. Hasta que alguien las reproduzca contra la fuente, la
línea de «76,0 % vs 79,1 %» no debería usarse para decidir nada.

**Lo que sí estaba bien y conviene subrayar**, porque es la advertencia que más
pesa aquí, y está verificada palabra por palabra en `docs.typesafe.ai/models`:

> «English is the primary training language and where accuracy is currently best.
> Other languages, including CJK scripts, are handled but not equally well. Test
> on your own content before relying on Jev for a non-English workload, and pay
> close attention to Confidence when routing.»

Todo el corpus de este proyecto está en castellano.

Y la crítica de *The Register* también se confirma: la comparación «sin
alucinaciones» no es justa porque Jev no genera texto; no hay verificación
independiente de la latencia ni del precio; y el «238× más barato» **asume que la
demanda de tokens se sostiene**.

---

## 3. Lo que la propia documentación dice que hace mal

De `docs.typesafe.ai/model-jaggedness/jev-1.13`, citado:

- **«does not count reliably»** — caracteres, ocurrencias, **elementos de una
  lista larga**.
- **No sabe juzgar si dos números están cerca.** Funciona mejor con
  representaciones semánticas que con números crudos (su ejemplo: nombres de
  color mejor que códigos hex).
- **«reads dates as text, not as ordered quantities»** — comparar fechas o
  ventanas no es de fiar.
- **`Score` está mal calibrado numéricamente**: no se puede reconstruir el número
  exacto interpolando entre niveles.
- **La precisión cae cuando el `state` crece con contenido que no hace falta.**
- Lee literalmente: negaciones, condiciones implícitas y dobles negaciones fallan.

Esas cuatro primeras líneas **deciden el caso en Cesta**, y conviene verlo junto
a lo que ya está medido aquí:

```
de los 784 pares ciertos que el nombre no encuentra:
  287  formato ilegible        <- numeros
  172  unidad distinta         <- numeros
   45  cantidad distinta       <- numeros
  ---
  504  (64 %)  no son juicio semantico: son dato numerico
  122  (16 %)  asignacion      <- lo arregla el hungaro, ya hecho
  158  (20 %)  puntuacion      <- aqui, y solo aqui, cabria un juez
```

**El 64 % de nuestro problema es exactamente lo que Jev dice por escrito que no
sabe hacer.** No es una sospecha: es su documentación contra nuestra medición.

Y hay más evidencia en casa que apunta igual: la Fase 9 probó un LLM local
(gemma-3-4b con JSON forzado) sobre el banco de pares y con enunciado estricto
acertó **20/20 negativos y falló 19/20 positivos**. El texto *sí* lleva señal; lo
que mató a gemma fue devolver un binario sin confianza. Jev devuelve
distribución y `confidence`, así que ese agujero concreto sí lo tapa — pero tapa
el 20 %, no el 64 %.

---

## 4. Dónde sí encajaría, y esto es lo que aporto

Los dos informes anteriores proponen usarlo como **juez de pares** (decidir si
dos productos son el mismo). Es el uso más obvio y el menos rentable: es el 20 %
del problema, va detrás del canal de vectores, y compite con algo que ya
funciona.

Hay dos sitios mejores, y los dos son **clasificación pura sobre texto en
volumen**, que es literalmente para lo que está hecho:

### 4.1 Los ejes de atributo — el mejor encaje del proyecto

Hoy `core/atributos.py` tiene listas escritas a mano: *entera / semidesnatada /
desnatada*, *virgen extra / virgen / suave / orujo*, *con gas / sin gas*, *natural
/ descafeinado*, *con alcohol / 0,0*. Cinco categorías cubiertas de las decenas
que tiene un supermercado, y cada una nueva es trabajo manual — y ya dio un fallo
clásico (`desnatad` casando dentro de `semidesnatad`).

Eso es **un `Choice` de manual**: el `state` es el nombre del producto (veinte
palabras, no 32k), las opciones son los valores del eje más «no lo dice», y la
regla del proyecto —*el que calla no bloquea*— se implementa con el `confidence`
que Jev ya devuelve: por debajo del umbral, «no lo dice».

- No hay números de por medio, que es donde Jev falla.
- El `state` es minúsculo, así que no aplica lo de «la precisión cae con contexto
  irrelevante».
- 52.567 productos × ~40 tokens ≈ **2,1 Mtok ≈ 0,09 $ la pasada entera**.
- Y **es verificable contra lo que ya tenemos**: las listas a mano son la verdad
  de referencia para las cinco categorías cubiertas. Si Jev no reproduce lo que
  ya sabemos, no se usa para lo que no sabemos.

Ésa última frase es la clave: **hay banco de pruebas gratis**, y sin banco de
pruebas no se mete nada en este proyecto.

### 4.2 Las secciones sin mapear — lo único que hoy dice «a mano»

La auditoría diaria termina con esto, todos los días:

```
=== categorias nuevas, sin mapear todavia: 1
    10  dia  navidad/bodega   -> A MANO: su rama no es clara
```

Es el **único** paso de toda la cadena diaria que pide una persona, y choca con
la ley del encargo. Y es un `Choice` de 19 opciones (los pasillos), con el nombre
de la categoría y sus productos como `state`. Cardinalidad 19, muy por debajo de
255. Coste: despreciable, son unidades al día.

### 4.3 Lo que NO le daría

- **Comparar cantidades o formatos** (`1,75 cl` frente a `175 ml`): lo dice su
  documentación.
- **Contar unidades de un pack**: «does not count reliably».
- **Ventanas de fechas de promoción**: lee fechas como texto.
- **Sacar el número de una oferta** («2ª unidad −50 %»): el número lo saca la
  expresión regular que ya existe; como mucho Jev clasificaría *el tipo de
  mecánica* cuando `promos.py` cae en `SIN_REGLA`.
- **Nada dentro de la ejecución de las 06:00** hasta que esté medido y tenga
  camino de vuelta.

---

## 5. Lo que hay que resolver antes de escribir una línea

1. **Acceso.** Es lista de espera (`console.typesafe.ai/keys`). Sin clave no hay
   experimento, así que es lo primero y no depende de nosotros.
2. **El castellano no está medido**, y su documentación pide expresamente
   probarlo con contenido propio. El banco de 4.1 sirve justo para eso.
3. **El precio puede no sostenerse.** Lo dicen ellos y lo subraya *The Register*.
   Todo lo que se construya encima tiene que poder apagarse sin romper nada.
4. **Es un tercero en un proyecto que vive en casa.** Los catálogos son públicos
   y no llevan datos personales, así que el riesgo es bajo — pero si esto entra
   en la cadena diaria, la cadena diaria pasa a depender de una API externa en
   acceso anticipado. Eso contradice la arquitectura salvo que sea opcional y
   degradable.
5. **No devuelve motivo.** La respuesta es `{choice, probabilities, confidence,
   usage}`. Si hace falta el porqué —y aquí hace falta, porque la explicabilidad
   del emparejamiento ya existe— hay que modelarlo como opciones del propio
   `Choice`.

---

## 6. El experimento, con su barra

Antes de integrar nada, y sin tocar `core/` ni el pipeline:

```
projects/cesta/jev_ejes.py      solo lectura sobre gold, offline
```

- Se le pide el eje de atributo de **los productos de las cinco categorías que ya
  tenemos escritas a mano**.
- Se compara contra `core/atributos.py`, que es la verdad de referencia.
- **Barra:** ≥ 97 % de acuerdo en los casos donde la lista a mano sí sabe, y
  ≤ 1 % de casos donde Jev afirma un valor con confianza alta y la lista dice
  otro. Las dos a la vez.
- Si no las cumple **en castellano**, no entra, y queda escrito que se midió.
- Si las cumple, el segundo paso es 4.2 (las secciones sin mapear), que es el
  único sitio donde hoy hay trabajo manual.

Coste de todo el experimento: **menos de un euro**.

---

## 7. Sobre el otro proyecto

Del encaje en WorldPulse (GDELT) no opino: no lo he mirado. Lo que sí se puede
decir desde aquí es que «clasificar y puntuar en volumen, con presión de coste y
sin necesidad de justificación en texto» es la forma exacta del problema para el
que Jev está construido — mucho más que el emparejamiento de productos, donde el
64 % del fallo es aritmética de envases.

---

## Fuentes

- [Introducing System One Models & Jev — TypeSafe AI](https://typesafe.ai/blog/introducing-system-one-models-and-jev)
- [Models — docs.typesafe.ai](https://docs.typesafe.ai/models)
- [Jev 1.13 jaggedness — docs.typesafe.ai](https://docs.typesafe.ai/model-jaggedness/jev-1.13.md)
- [Jev (AI model) — Wikipedia](https://en.wikipedia.org/wiki/Jev_(AI_model))
- [TypeSafe AI debuts model for machines that plays Doom — The Register](https://www.theregister.com/ai-and-ml/2026/09/16/typesafe-ai-debuts-model-for-machines-that-plays-doom/5296711)
- [TypeSafe AI's Jev offers an alternative to LLMs — Tom's Hardware](https://www.tomshardware.com/tech-industry/artificial-intelligence/typesafe-ais-jev-offers-an-alternative-to-llms-that-claims-to-be-193x-faster-and-445x-cheaper-system-one-type-model-is-bespoke-for-probabilistic-decision-making)
- [ChatGPT pioneer launches Jev model for programmatic logic — AI News](https://www.artificialintelligence-news.com/news/chatgpt-pioneer-launches-jev-model-for-programmatic-logic/)
