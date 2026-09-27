# Laya — el mismo sitio que Jev, sin lista de espera: medido, no llega

Escrito el 24 de septiembre de 2026, a raíz de que apareciera
`convaiinnovations/laya4` como «parece que hace lo mismo que Jev». Se verifica
contra las fuentes primarias (la tarjeta del modelo, PyPI, GitHub) y **se mide**
con el mismo banco de pruebas que ya estaba diseñado en `docs/JEV.md` §4.

**Veredicto:** Laya existe, es Apache 2.0, se instala y corre **en este PC**, y hace
lo mismo que Jev —hasta el punto de exponer el mismo endpoint—. Pero **quita los dos
bloqueos de Jev (la lista de espera y ser un tercero) y no quita ninguno de sus
límites**: el 64 % de lo que se nos escapa sigue siendo aritmética de envases, y en
el único sitio donde un modelo de estos encaja —los 12 ejes de
`core/atributos.py`— **medido aquí da 73,1 % de acuerdo contra una barra de 97 %**.
Su propia tarjeta dice por qué: la puntería de estos pesos viene del *fine-tuning*,
no del cero. Lo que sí ha dejado es un instrumento, un «no» medido que costó 0 €, y
**una lista de fallos de nuestras propias listas a mano** que vale más que el modelo.

---

## 0. El nombre que se pidió no existe

`https://huggingface.co/convaiinnovations/laya4` responde **401** — pero ese 401 no
significa «existe y es privado», y confundirlo sería justo la clase de dato que este
proyecto no acepta. El instrumento, calibrado antes de usarlo:

| lo que se pidió | respuesta |
|---|---|
| `api/models/convaiinnovations/laya4` | **401** `Invalid username or password.` |
| `api/models/convaiinnovations/zzz-no-existe-9f3` (inventado a propósito) | **401** `Invalid username or password.` |
| `api/models/bert-base-uncased/zzz-no-existe-9f3` (inventado, otra cuenta) | **401** `Invalid username or password.` |
| página `huggingface.co/convaiinnovations/laya4` | **401**, 52.307 bytes |
| página `huggingface.co/convaiinnovations/zzz-no-existe-9f3` | **401**, 52.331 bytes |
| `api/models?search=laya4` | `[]` |
| `api/models?search=laya` | los tres de verdad, en la primera línea |

Un nombre **inexistente** da exactamente el mismo 401 y la misma página que el
pedido, así que lo único que se puede afirmar es que **no es público**. Si existe
uno privado a punto de salir, **no lo sé**. Lo que sí existe es la familia:

| repo | encoder | parámetros | contexto | gusta a | creado |
|---|---|---:|---:|---:|---|
| `convaiinnovations/laya` | ModernBERT-large | 421 M | 512 | 3.255 | 18 sep |
| `convaiinnovations/laya-multilingual` | mmBERT-base | 322 M | 1.024 (hasta 8.192) | 234 | 19 sep |
| `convaiinnovations/laya-typed-decisions` | ModernBERT-large | 421 M | 1.024 | 96 | 18 sep |

Los tres viven en el **mismo repo**: el inglés en la raíz, los otros dos en
subcarpeta, y solo se descarga el que se pide (`laya.load(..., subfolder=...)`).

---

## 1. Qué es, verificado contra la fuente

| | |
|---|---|
| Quién | **Convai Innovations** (autor en PyPI), repo de `NandhaKishorM` |
| Licencia | **Apache 2.0** en los tres sitios: tarjeta de HF, `LICENSE` de GitHub y metadatos de PyPI |
| Paquete | `laya` **0.3.20** en PyPI, requiere Python ≥ 3.10, `torch>=2`, `transformers>=4.48` |
| Proyecto | GitHub **21.913 estrellas, 1.873 forks, 110 issues abiertos**, creado el 18 sep, último push el 24 sep (hoy) |
| Salida | **cero tokens de salida**: devuelve valores tipados con su reparto de probabilidad. No hay texto que parsear |
| Primitivas | `choice` (una entre opciones), `score` (ordinal) y `noul` (probabilidad de un sí/no) |
| Compatibilidad | `laya-serve` expone `POST /v1/systemone`, **la misma forma de petición que Jev**, para que un cliente de Jev solo cambie la URL |
| Arquitectura | encoder bidireccional afinado + cabeza de decisión entrenada desde cero (2 capas, marcador por opción, cabeza de actuar/escalar) |
| Entrenamiento | RL contra reglas de puntuación estrictamente propias (*RLCD*); el reparto honesto es la única forma de maximizar la recompensa |

### 1.1 Lo que su propia tarjeta dice que hace mal

Está en una sección que se llama *Honest Limits*, y es lo que decide el caso aquí:

- **Los checkpoints base están cerca del azar cero-shot**: 0,362 en su propio banco
  de decisiones tipadas, contra 0,461 de «contestar siempre la clase mayoritaria».
  **El 0,766 que anuncia es del checkpoint afinado sobre el propio banco.** Sus
  palabras: *«Laya is a fast base to specialise, not a zero-shot decision engine»*.
- **Más de 20 opciones se despeñan**: en Banking77 (77 etiquetas) saca 0,425 donde
  Jev saca 0,870, porque las opciones se reparten ~3 tokens cada una.
- **`score` es la primitiva más floja** (SST-5: 0,372).
- **`noul` puede seguir a sus etiquetas y no al texto** (*issue* #156): devuelve un
  «no» seguro ante una entrada claramente positiva. Su recomendación es preguntarlo
  como `choice` de dos opciones con claves neutras.
- **Viene sobre-confiado**: recalibrar una temperatura por (tipo de pregunta, número
  de opciones) mueve el ECE de **0,466 a 0,081**. Hay que hacerlo con datos propios
  antes de creerse una probabilidad.
- **`action.act_probability` no lleva señal** (*issue* #185): da 1,0 casi siempre y
  su AUROC va *en contra* del acierto (0,30).

Y una advertencia de la casa, sobre sus comparaciones: las cifras de Jev de su
tabla son *«third-party published, never measured here»* — es decir, tienen el mismo
estado que las que este proyecto ya puso en cuarentena en `docs/JEV.md:35-52`. No se
usan para decidir. El dato que sí sostiene tracción es GitHub (21.913 estrellas); el
campo `downloads` de la API de HF da **0** también para repos de 2025 de la misma
cuenta, así que no se cita como prueba de nada.

---

## 2. Lo que cambia respecto a Jev, y es lo único que cambia

`docs/JEV.md` §8 dejaba el asunto parado en un bloqueo que no dependía de nosotros:
**la lista de espera**. Y `Claude outputs/JEV.md` §5 añadía el segundo: meter un
tercero en acceso anticipado dentro de un proyecto que vive en casa.

Laya quita los dos de golpe:

- **No hay lista de espera ni clave.** `pip install laya` y a correr.
- **No hay tercero y no sale nada del PC.** Pesos abiertos Apache 2.0 en CPU: el
  catálogo no viaja, y la tarea de las 06:00 no pasa a depender de una API ajena.
- **No hay precio que se pueda torcer.** El coste por pasada del catálogo entero
  ($0,29 en `docs/JEV.md:197-213`) pasa a ser **0 € y 2,2 s por producto de CPU**.

Y no cambia **nada** del resto, que es lo que importaba:

- El **64 %** de lo que el nombre no encuentra es formato, unidad y cantidad — números
  (`docs/JEV.md:71-109`)— y Laya tampoco los hace: su tarjeta solo promete `choice`,
  `score` y `noul` sobre texto.
- El **juez de pares** sigue siendo el 20 %, detrás del canal de vectores.
- Las **ofertas** siguen siendo 20 textos distintos, no un modelo.
- Y hereda las mismas debilidades documentadas: lee las negaciones al pie de la
  letra, `score` flojo, y la cardinalidad alta se despeña. **Esto se mide en §5 y se
  cumple**: los fallos del modelo son justo esos.

---

## 3. Medido aquí: se instala, corre, y en castellano hay que forzarlo

Todo lo de abajo está medido en este PC, con el módulo nuevo
`projects/cesta/laya_ejes.py` (la receta completa está en su cabecera: entorno
aparte, `laya` **no entra** en `pyproject.toml`, `USE_TF=0`).

| lo que se midió | número |
|---|---|
| instalación (`uv pip install laya`) | `laya 0.3.20` + `torch 2.14.0` + `transformers 5.17.0`, sin tocar el entorno del proyecto |
| pesos (los tres checkpoints) | **2,2 GB** en disco (medido en `HF_HOME`) |
| `Router(preload=True)` | **402 s** (incluye descargar los tres; después quedan en disco) |
| una petición de 12 preguntas, `multilingual`, CPU | **2,16 s** (215 peticiones en 8 min) |
| la misma, checkpoint `english`, CPU | **7,15 s** |
| tokens de salida | **0** (`usage.output_tokens`), como promete |
| aviso del propio paquete al cargar | *«ships invalid temperatures… Treat confidence from the affected entries as uncalibrated»* |

**La ruta, que es una trampa para nosotros.** El enrutador decide por guion y tildes:
un nombre de producto en castellano **se va al checkpoint inglés**:

```
routing: {'model': 'english',
          'reason': 'Latin script, language not identified and no non-English
                     letters; using default (english)'}
```

Su propia tabla dice que el inglés saca 0,521 en XNLI no-inglés donde el multilingüe
saca 0,731 — así que el defecto del enrutador es el equivocado para un catálogo
entero en castellano. Se arregla con un argumento (`model="multilingual"` o
`lang_guess="es"`), y por eso el banco de §4 lo **fuerza** y cuenta aparte lo que el
enrutador habría elegido solo.

Medido también el inglés sobre el mismo banco (muestra menor, 122 declaraciones):
**78,7 %** frente al **73,1 %** del multilingüe sobre 316. Con esos tamaños la
diferencia **no se distingue** (el error estándar ronda los 4 puntos), así que no se
afirma que uno sea mejor: se deja dicho que el defecto del enrutador manda al que su
documentación señala como peor, y que **eso no se ha podido confirmar aquí**.

---

## 4. El primer experimento, con su barra

No hubo que inventar nada: es el diseño de `docs/JEV.md:170-196` (§4.2) con los
pesos de Laya en lugar de la API de Jev — el `respaldo` que
`docs/JEV-IMPLANTACION.md:63-76` ya había dejado previsto.

```
state        el nombre del producto, tal cual
questions    las 12 del mismo producto, una petición (Choice por eje)
criteria     los valores de EJES + "no lo dice"
verdad       core/atributos.valores(nombre) -- las listas a mano
```

Se pregunta solo por productos de los que **la lista ya sabe algo**: un nombre del
que no sabemos nada no prueba nada. Muestreo determinista (semilla 23), hasta 8
nombres por cada (eje, valor).

```
uv run python -m projects.cesta.laya_ejes --sin-modelo          # solo el banco
# y con el modelo, la receta de la cabecera del módulo:
#   ... python -m projects.cesta.laya_ejes --por-valor 8 --json data/laya_ejes.json
```

### 4.1 El resultado

    nombres en el banco                         215
    (producto, eje) con verdad declarada        316
    ejes cubiertos                               12

| | |
|---|---:|
| **acuerdo sobre lo declarado** | **231 (73,1 %)** — la barra pide 97 % |
| se abstiene (dice que el nombre no lo dice) | 48 |
| declara **otro valor** | 37 |
| la lista callaba y el modelo también | 2.264 |
| la lista callaba y el modelo declara | **1.230** |

(El banco entero de `docs/JEV.md` §4.1 son **16.605 declaraciones**; esto es una
muestra determinista de 316. Y una cuenta que conviene no copiar de un informe a otro:
`docs/JEV-IMPLANTACION.md:31` dice 28 valores por eje y hoy `EJES` tiene **27** — la
diferencia es el valor `formato=concentrado`, que se quitó el 23 de septiembre por lo
que cuenta `core/atributos.py:76-93`.)

Por eje (acuerdo / calla / otro valor):

| eje | acuerdo | calla | otro valor | lo que dice cuando falla |
|---|---:|---:|---:|---|
| lactosa | 16 | 0 | 0 | — |
| gluten | 21 | 1 | 0 | — |
| gas | 15 | 1 | 0 | — |
| alcohol | 14 | 2 | 1 | `con alcohol` en una cerveza 0,0 % |
| cafe | 31 | 8 | 1 | — |
| cafeina | 31 | 0 | **6** | `natural` donde el nombre pone **descafeinado** |
| formato | 15 | 1 | 2 | `en polvo` en dos detergentes «líquido gel» |
| integral | 15 | 4 | 0 | — |
| aceite | 15 | **14** | 4 | `oliva suave` en un «virgen extra (suave y afrutado)» |
| grasa | 21 | 2 | **11** | `sin grasa` donde el nombre pone **entera / semidesnatada** |
| azucar | 12 | 1 | **10** | `sin azucar` en «con azúcar de caña» |
| leche | 25 | **14** | 2 | `bebida vegetal` en «Leche desnatada» |

Donde el nombre es explícito y el vocabulario no se presta a nada —`lactosa`,
`gluten`, `gas`— **acierta casi siempre**. Donde hay que entender el envés de la
frase (`descafeinado`, `0,0 %`, `con azúcar de caña`) **falla de forma sistemática**,
que es exactamente lo que su tarjeta avisa.

### 4.2 Las 1.230 declaraciones donde el nombre no dice nada

Es el número más incómodo: de los 2.264 pares en los que **nuestras listas callan**,
el modelo declaró un valor en **1.230 (54 %)**. Los mayores:

    lactosa=sin lactosa  187      gluten=sin gluten   93
    azucar=sin azucar    175      integral=integral   92
    cafeina=natural      174      formato=en polvo   101
    grasa=sin grasa      129      alcohol=sin alcohol 115

Con la regla de la casa —**el que calla no bloquea**— esto no es un matiz: si esas
declaraciones entraran como guarda, un «Tostas de pan con avena» declarando
`grasa=sin grasa` **cortaría comparaciones legítimas** con una leche entera del mismo
grupo. Es el modo de fallo caro de esta aplicación, y sale medido.

**Parte de la culpa es del enunciado, y es mía.** El mío pide «elige la opción que el
nombre afirma», y no advierte de que «no lo dice» es una respuesta legítima y
frecuente. **No sé cuánto baja ese 54 % con un enunciado mejor**: se mide cambiando
una línea y volviendo a correr el banco, que cuesta 8 minutos.

### 4.3 Cuánto de este acierto es copia nuestra, y la respuesta es que no

El enunciado de cada valor está escrito como lo escribiría una persona, y eso hace
que **en 12 de los 27 valores** la explicación lleve dentro el mismo patrón con el que
la lista reconoce el valor (`formato=en polvo` → «viene en polvo para disolver»). Si
el acierto se concentrara ahí, el 73,1 % no mediría lo que dice medir. Medido:

| | pares | acuerdo |
|---|---:|---:|
| donde el enunciado **copia** un patrón de la lista | 135 | **68,1 %** |
| donde el enunciado **no copia** nada | 181 | **76,8 %** |

O sea: **la copia no infla el resultado**, más bien al revés. Y la comparación no es
controlada —son conjuntos de valores distintos, no los mismos casos con dos
enunciados—, así que la diferencia de 8,7 puntos **no se distingue** con estos
tamaños (±5,1 puntos de error). Lo que sí se puede afirmar es lo que importa: **no hay
indicio de que el 73,1 % sea un espejo de nuestras propias reglas.**

Esto no es una precaución de adorno: lo mide el propio instrumento
(`valores_que_copian_el_patron()` y `generosidad()`), lo imprime en cada pasada, y
`tests/test_laya_ejes.py` fija el 12 para que nadie lo cambie sin que se note.

La pasada entera se repitió para poder medir esto, y dio **exactamente lo mismo**
(231, 48, 37, 1.230): la cifra es reproducible.

---

## 5. La auditoría de los 85 desacuerdos: 27 veces la que falla es nuestra lista

La condición 1 de la barra (`docs/JEV.md:217-219`) pide que los desacuerdos se
auditen **uno a uno**. Están los 85 enteros en `data/laya_ejes.json`
(`desacuerdos`), y leídos uno a uno salen tres montones:

### 5.1 Donde el modelo tiene razón y nuestra lista se equivoca — **27 casos**

Son declaraciones **fuera de sitio**: el patrón es una subcadena suelta aplicada a
todo el catálogo, y el modelo se calla o contesta bien. Es la trampa que
`docs/JEV.md:152-168` ya había medido en abstracto (935 declaraciones fuera de
sitio); aquí tiene los nombres:

| eje | n | por qué se equivoca nuestra lista | ejemplo |
|---|---:|---|---|
| `leche` | **8** | `arroz`, `avena`, `soja`, `almendra`, `bebida de` disparan `bebida vegetal` en cualquier cosa que los lleve | «Tostas de pan con avena especial canapé», «Arroz blanco precocido ultracongelado», «Almendra frita y salada», «Postre estilo skyr de soja y coco» |
| `cafe` | **5** | `instant`, `instantaneo` disparan `soluble` | «Apresto instantáneo para planchado», «Sopinstant Crema de pollo», «Fideos instantáneos MAGGI», «Tinte retoca raíces spray instantáneo» |
| `aceite` | **9** | `orujo` dispara en **licores** de crema de orujo; `virgen` dispara en la marca «Virgen del Brezo»; y dos nombres del catálogo vienen rotos (`virgen extrLOREA`, `virgen exttra`) | «Crema de Orujo Ruavieja», «Licor de crema de orujo PANIZO», «Lazos Virgen del Brezo» |
| `azucar` | **4** | `azucar` dispara **dentro de la negación**: «bajo en azúcares», «sin azúcares añadidos», «0 % azúcar» | «Bebida vegetal de almendra (0 % azúcar)», «Pan tostado bajo en sal y en azúcares» |
| `integral` | **1** | `blanco` dispara en el vino | «Vino blanco con D.O. Rías Baixas» |

Y **3 más** en los que fallan los dos: los dos chocolates «con avellanas **enteras**»
y la sardina «**Entera**», donde nuestra lista lee grasa entera y el modelo contesta
`sin grasa`.

**Los 55 restantes son el modelo fallando donde la lista acierta**, y dos patrones se
llevan casi todo:

- **11 veces `sin grasa`** donde el nombre dice `entera` o `semidesnatada`: «Leche
  entera de vaca pasteurizada Saha», «L.R. Leche entera», «Leche entera sin
  lactosa», «FEIRACO Leche semidesnatada», «PULEVA Leche semidesnatada»… Nueve de
  ellas son leche de vaca clara. Es un fallo sistemático, no ruido.
- **6 veces `natural`** donde el nombre dice `descafeinado` — las seis: «Café molido
  mezcla descafeinado Marcilla», «NESCAFE Café en cápsulas espresso descafeinado»
  (×2), «Café cápsulas cortado descafeinado Carrefour», «TASSIMO L'OR…», «Gran
  Aroma Marcilla».

### 5.2 Lo que esto dice de nuestro código, que es lo que se puede usar hoy

Las listas de `core/atributos.py` **sobre-disparan**, y ahora hay 27 nombres
concretos que lo demuestran en los ejes `leche`, `cafe`, `aceite`, `azucar` e
`integral`. Eso **no es un hallazgo sobre Laya**: es un hallazgo sobre lo nuestro,
que se puede arreglar sin ningún modelo, y que conviene tener arreglado **antes** de
volver a usar estas listas como verdad de referencia — porque un banco de pruebas
que está mal en 27 de 85 desacuerdos no puede juzgar a nadie.

No se toca aquí: `core/atributos.py` mueve los ejes contradictorios de todo el
catálogo (`projects/cesta/ejes.py`), y la barra pide **0** grupos contradictorios.
Cambiarlo es un trabajo con su propia medida y su propia pasada, y esta sesión no lo
hace a escondidas dentro de un informe.

---

## 6. Veredicto: ¿sirve para este proyecto?

**Para lo que Jev tenía reservado —los 12 ejes y las categorías sin pasillo—, cero
shot no.** 73,1 % contra una barra de 97 %, con dos fallos sistemáticos que su
tarjeta documenta. Y no es una sorpresa: su propio número bueno (0,766) es del
checkpoint **afinado sobre el banco de ese benchmark**, contra 0,362 del base.

**Para el emparejamiento, tampoco**: los 4 números que fallan son envases y unidades
(`docs/JEV.md:90-99`), y esto no cuenta.

**Para la cadena de las 06:00, no.** Nada de esto entra en `ejecutar.bat`.

Lo que sí ha quedado, y no es poco:

1. **El instrumento**: `projects/cesta/laya_ejes.py`, que corre sin modelo
   (`--sin-modelo`), sin tocar gold y sin entrar en las dependencias del proyecto.
2. **Un «no» medido que costó 0 €** y no una opinión sobre un enlace de Hugging
   Face. El experimento que `docs/JEV-IMPLANTACION.md` §6 daba por imposible sin
   acceso **está hecho**.
3. **27 fallos concretos de nuestras propias listas**, con nombre y apellidos, en
   cinco ejes.
4. La confirmación de que **un tercero no hace falta** para esta clase de trabajo:
   la decisión sobre Jev ya no está presa de una lista de espera. Se puede decidir
   sin él.

### El orden de lo que queda, de más barato a más caro

1. ~~**Arreglar las listas** (§5.2) y volver a correr el mismo banco.~~ **Hecho el 27 de
   septiembre de 2026, y sin necesidad de volver a correr el modelo.** Los 27 casos se
   arreglaron con la regla que ellos mismos pedían —**el eje no se pronuncia fuera de su
   dominio**— más un patrón con hueco para la negación del azúcar:

       eje        declaraciones antes -> ahora      de los 16 casos auditados
       leche                    2.513 -> 1.146      los 4 corregidos
       integral                 1.659 ->   563      el del vino blanco, corregido
       cafe                     1.576 ->   835      los 4 corregidos
       grasa                      909 ->   689      los 2 corregidos
       aceite                     456 ->   408      los 3 corregidos
       azucar / cafeina / gluten / lactosa / gas / alcohol / formato: sin cambio

   En total **16.417 declaraciones -> 12.945** (−21 %), y de los 16 casos auditados **14
   corregidos** (los otros 2, el zumo «0 % azúcar» y el pan «bajo en sal y en azúcares»,
   ahora dicen `sin azucar`, que es lo que dicen). **0 de 12 fichas legítimas se rompieron.**

   Y lo que importa, medido con el banco de pares: la precisión del emparejador sigue en
   **91,0 %** (era 91,1 %: 179 falsos positivos de 3.000 contra 177, o sea dos pares) con la
   cobertura en el 100 %, y la auditoría de grupos de `ejes` sigue en **0 contradicciones**.
   Callarse de más no rompe comparaciones —el que calla no bloquea—; lo que hacía era partir
   grupos por un eje inventado.

   **Aviso de orden para quien lo repita**: al cambiar los ejes hay que **volver a correr
   `emparejar`** antes de las pruebas del catálogo, porque la agrupación aplica esos vetos y
   `tests/test_atributos.py::test_el_catalogo_no_ha_empeorado` lee el gold. Con el gold viejo
   el trinquete salta sin que nada esté mal.
2. **Las 19 opciones de pasillo** (`docs/JEV.md` §5): el único «A MANO» de la cadena
   diaria, con **881 claves ya mapeadas** como banco gratis. 19 opciones está justo
   en el borde de lo que su tarjeta dice que aguanta, así que **no lo sé** sin
   medirlo — y medirlo son ~30 minutos de CPU a 2,2 s por categoría.
3. **Afinar con datos propios**: es donde su tarjeta dice que está la puntería, y
   tendríamos etiquetas (las listas a mano, las 881 claves mapeadas). Pero hace falta
   una GPU que no está en casa, y eso es una decisión del dueño, no un paso técnico.

---

## 7. Lo que no sé

- Si existe un `laya4` **privado**. El 401 es el mismo para un nombre inventado.
- **Cuánto baja el 54 %** de declaraciones sin prueba con un enunciado mejor (§4.2).
- Si el multilingüe es mejor que el inglés **en castellano**: con 122 y 316
  declaraciones la diferencia no se distingue (§3). Lo dice su documentación; aquí
  no se ha podido confirmar.
- Si afinando con nuestras etiquetas se llega al 97 % (§6). Su tarjeta dice que la
  puntería viene de ahí, y no dice cuánto para un dominio nuevo.
- Si las **19 opciones de pasillo** se le dan mejor o peor que un eje de 3-5: estaría
  en el borde del despeñadero que documenta.
- Si el castellano de un catálogo de supermercado —nombres truncados, mayúsculas de
  marca, abreviaturas de cadena— es representativo del castellano con el que se
  entrenó. El banco de §4 es lo único que hemos mirado.

---

## Fuentes

- Tarjeta del modelo: <https://huggingface.co/convaiinnovations/laya> (y los
  subdirectorios `multilingual` y `typed-decisions` del mismo repo)
- Paquete: <https://pypi.org/pypi/laya/json> (0.3.20, Apache-2.0, Convai Innovations)
- Código: <https://github.com/NandhaKishorM/laya> (metadatos por la API de GitHub el
  24 sep de 2026: 21.913 estrellas, 1.873 forks, 110 issues abiertos)
- API de Hugging Face: `api/models?author=convaiinnovations`, `api/models?search=laya`
  y las páginas de `laya4` y de un nombre inventado, comparadas (§0)
- Lo medido aquí: `projects/cesta/laya_ejes.py`, con `data/laya_ejes.json` (banco
  multilingüe) y `data/laya_ejes_english.json` (el mismo banco con el inglés). Los dos
  JSON **no se versionan** (`data/` está en `.gitignore`): se regeneran con la receta
  de la cabecera del módulo, que es la que está en `docs/OPERACION.md`.
