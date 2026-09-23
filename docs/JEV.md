# Jev — dos sitios donde encaja, y ninguno es juzgar pares

> Estudio del modelo `jev-1.13.0` (TypeSafe AI) y de los dos únicos huecos de este
> proyecto donde su documentación y la nuestra dicen lo mismo. **No hay una línea
> de integración escrita**: todo lo de aquí se mide y se decide cuando haya
> acceso, que es lista de espera.
>
> Fecha del estudio: **2026-09-23** · Raíz: `F:\aprendizaje\scrap`

**De dónde sale esto.** Los dos sitios que se proponen abajo —los ejes de
atributo y las categorías sin pasillo— **los identificó primero la revisión
paralela** (`Claude outputs/JEV.md`), y este documento es su versión canónica en
`docs/`, donde la ven `verificar_docs` y el traspaso. Lo que **corrige** de
aquélla, medido: los ejes de `core/atributos.py` no son cinco, son **doce** (§4);
el coste de la pasada entera no es 0,09 $ sino **~0,29 $** con los doce ejes
(§4.3); y el ejemplo de categorías sin mapear de aquel informe (`navidad/bodega`,
10 productos) **no es el de hoy**: hoy son **9 claves y 6 dicen «A MANO»** (§5).
Lo que **añade**: la medida de sobre-disparo de las listas (§4.1) y los 881
mapeos que sirven de banco (§5).

## Cómo se reproduce lo medido aquí

```powershell
uv run python -m projects.cesta.auditar_secciones        # las 9 categorias sin pasillo
uv run -m projects.cesta.emparejar --medir                # el 65 % de la barra
uv run pytest tests/test_atributos.py -q                  # los ejes a mano
uv run python -m projects.cesta.verificar_docs            # las cifras de los docs
```

Y las cuentas del §4 y del §5 salen de leer `data/gold/grupos.parquet` (52.567
filas) con `core.atributos.valores()` y `core.secciones.clave_de()`, en dos
consultas que están escritas al pie de cada tabla.

---

## 1. Qué es Jev, verificado

| | |
|---|---|
| Modelo | `jev-1.13.0`, alias `jev-latest` y `jev-preview` (hoy los dos al mismo) |
| Quién | TypeSafe AI (San Francisco), Diogo Almeida (coautor de RLHF/InstructGPT, cuatro años en OpenAI), Erik Gafni y Sasha Sheng; ~40 M$ de semilla |
| Entrada | un `state`: texto, objeto JSON o lista de textos. **Solo texto**: nada de imagen, audio ni vídeo |
| Salida | `choice` (+ `probabilities` + `confidence`), `score` (+ `legend`), `noul` (0–1, **sin** `confidence`) |
| Tope | `choice` hasta **255 opciones**; por encima, dos etapas |
| Precio | **$0,042 / Mtok de entrada** ($42/billón). La salida es gratis pero **se contabiliza** (`usage.output_tokens`) |
| Límites | 64k de contexto (32k para `state` + la pregunta más larga); 1.200 req/min; 250.000 tok/s; `429`/`529` con backoff |
| API | `POST https://api.typesafe.ai/v1/systemone`; SDK `typesafe-sdk` (Python ≥ 3.10, que es el `requires-python` de este repo) |
| Acceso | **early access, lista de espera**; claves en `console.typesafe.ai/keys` |

**Lo que no se puede verificar, y por tanto no cuenta.** La tabla de evaluación
que circula por blogs de terceros (con GPT-5.6 Luna, DeepSeek V4 Flash, GPT-6 Sol)
**no es del blog oficial**: el post del 15 de septiembre compara contra
**GPT-5.6 Terra, GPT-6 Astra y Fable 5.1**, y a DeepSeek lo deja sin versión.
Los nombres de terceros además se contradicen entre sí (unos dicen `GPT-5.6 Sol`,
otros `GPT-6 Sol`). Cifras de acierto atadas a nombres inventados no son una
medida, y este proyecto no acepta esa clase de dato. Lo que sí queda del material
propio: dentro de 3 puntos de los modelos frontera **en su propia batería**, y
entre 100 y 400 veces más barato y rápido en tareas con forma de decisión. La
latencia de 70–500 ms y la factura **no tienen medición independiente**: el
modelo no es descargable y no hay paper de arquitectura ni recuento de
parámetros.

Y una trampa que conviene dejar escrita: buscando "Jev" salen
`jevtypesafeai.com` y `jevai.org`, que se declaran **no afiliados** y reparten
claves y un SDK que no existe (`client.decide(...)`; el real es
`TypeSafeClient().system_one(...)`). Lo oficial es `console.typesafe.ai`,
`docs.typesafe.ai` y `api.typesafe.ai`.

---

## 2. Lo que su documentación dice que no sabe hacer, contra lo que aquí está medido

**Aviso de idioma, textual en `docs.typesafe.ai/models`:** *"English is the
primary training language… Other languages are handled but not equally well.
Test on your own content before relying on Jev for a non-English workload."*
Nuestro corpus es castellano entero, así que esto no es un detalle: es la primera
medida del experimento, no una nota al pie.

**Y los defectos que declara él mismo**, en su página oficial de *jaggedness*
(`docs.typesafe.ai/model-jaggedness/jev-1.13`, revisada el 2026-09-16): ocho
modos de fallo, y **tres de ellos deciden el caso aquí** —

| modo | qué dice, textual | qué parte del proyecto toca |
|---|---|---|
| Math and Numbers | *«Jev is not a calculator… does not count reliably»*; con números crudos no sabe juzgar si dos valores están cerca | formato, cantidad y unidad: **504 de los 784** pares que se escapan |
| Date and time comparison | *«reads dates as text, not as ordered quantities»* | ventanas de promoción (`promo_hasta`) |
| Large state full of irrelevant detail | *«accuracy falls as the state grows with content unrelated to the decision»*, y lo llama **context rot** | el diseño del `state`: sólo lo que la pregunta necesita |

Y los otros cinco (lectura literal, indirección, contenido adversarial,
instrucciones contradictorias, generación) son avisos de diseño que se aplican
escribiendo bien el enunciado, no bloqueos.

Puesto junto a lo medido en `docs/DIAGNOSTICO-MATCHING.md` §4:

| motivo por el que se escapan los 784 pares ciertos | pares | % |
|---|---:|---:|
| formato ilegible | 287 | 37 % |
| la otra cadena lo vende en otra unidad | 172 | 22 % |
| pack frente a unidad | 45 | 6 % |
| **subtotal: dato numérico** | **504** | **64 %** |
| puntuó por encima y perdió la elección mutua | 122 | 16 % |
| misma forma y por debajo del umbral | 158 | 20 % |

**El 64 % de nuestro problema es justo lo que Jev dice por escrito que no sabe
hacer.** Eso solo descarta un sitio —juzgar pares— y deja libres los dos que
siguen, que no tienen números por medio.

---

## 3. Por qué NO juzga pares

No es una opinión: es lo que ya está medido.

- §20: el LLM local (`gemma-3-4b` por Ollama con JSON forzado) se midió y se
  descartó. Estricto: **20/20 negativos y 1/20 positivos** (es un escéptico, se
  llevaría el recall por delante). Amplio: 78 %, que no aporta nada.
- §21: **no hay nada que aprender** de las características del par. Misma marca y
  código distinto son, por construcción, casi idénticos en el texto; el único
  separador es el código de barras, que es la verdad con la que se mide.
- La cola es el **canal de vectores**, ya medido (recall 65 % → 73 %) y apagado
  porque rompe la asignación (861 conflictos): ponerlo con el reparto compartido
  es lo siguiente que hay que hacer con el matching, y va antes que cualquier
  modelo de juicio.

---

## 4. Sitio 1: los ejes de `core/atributos.py` — el clasificador de atributos

Hoy son **listas a mano**. Y no cinco: **doce ejes**, contados en el fichero
(`grasa`, `aceite`, `gas`, `alcohol`, `cafeina`, `azucar`, `integral`, `lactosa`,
`gluten`, `formato`, `cafe`, `leche`). Cada eje es una lista de
`(valor, patrones)` y **el orden es el algoritmo**: lo específico antes que lo
general, porque `desnatad` casa dentro de `semidesnatad` (el fallo que la
auditoría del 17 de septiembre encontró, ya arreglado por orden y fijado con una
prueba).

### 4.1 El banco de pruebas es gratis, y tiene una trampa que conviene medir

La verdad de referencia son las propias listas, aplicadas al catálogo de hoy
(`data/gold/grupos.parquet`, 52.567 productos → **16.605 declaraciones**):

| eje | valor | productos |
|---|---|---:|
| gluten | sin gluten | 3.022 |
| leche | bebida vegetal | 2.032 |
| azucar | sin azucar | 1.836 |
| cafeina | natural | 1.598 |
| integral | blanco | 1.155 |
| lactosa | sin lactosa | 913 |
| … | (19 valores más, hasta 9) | … |

**La trampa, medida**: parte de esas declaraciones cae en productos donde el eje
no significa nada, porque los patrones son subcadenas sueltas aplicadas a todo el
catálogo. **Solo en los tres casos de abajo hay 935 declaraciones fuera de
sitio**, y son las peores de cada eje:

| eje · valor | n | pasillos distintos | dónde vive de verdad |
|---|---:|---:|---|
| `cafeina · natural` | 1.598 | **19** | el mayor es **lacteos-huevos (411)**: es "yogur natural", no café |
| `integral · blanco` | 1.155 | **20** | el mayor es **bebidas (508)**: es "vino blanco" |
| `aceite · orujo` | 32 | 4 | **bebidas (16) por delante de despensa (12)**: es orujo *de hierbas* |

Consecuencia para el experimento: el banco **no** se usa entero. Se usa lo que
declara un eje coherente con su pasillo (o con su rama), y **los desacuerdos se
auditan uno a uno** — ahí no hay ruido, hay listas que sobre-disparan, que es
justo el trabajo manual que se quiere retirar. Un eje que se da por bueno con
16 productos en 20 pasillos no es una verdad de referencia: es una corazonada con
formato.

### 4.2 El diseño (no hay nada que inventar: es un `Choice` de manual)

```
state        el nombre del producto, tal cual (minúsculo, 15 tokens)
questions    12, una por eje, cada una un Choice
             criteria = los valores del eje en EJES + "no lo dice"
confianza    la devuelve el modelo; el umbral vive en NUESTRO código
regla        "el que calla no bloquea": value == "no lo dice"  ->  eje ausente
```

Lo importante: **`confidence` no decide, decide el código**. La regla de la
cabecera de `core/atributos.py:17-19` («un eje donde uno declara y otro calla no
bloquea») se implementa con `confidence < 0,9 → sin valor`: eso es **ausencia de
prueba**, que es lo que la regla pide, y no una tolerancia. Y el `Choice` devuelve
todo el reparto, así que un eje con la masa partida entre `virgen` y
`virgen extra` no elige: se marca para la vista.

La opción «no lo dice» no es un invento de este diseño: su propio recetario de
extracción de fechas recomienda lo mismo —*«it gives you somewhere to put an
explicit "not stated" option so a missing part is reported rather than guessed»*—
que es la misma idea que ya está escrita en la cabecera de `core/atributos.py`.

Lo que Jev aporta aquí de verdad, y es lo que las listas **no pueden** hacer: no
tiene el fallo de subcadenas. Un lector no confunde `desnatada` con
`semidesnatada` ni `champu` con `champan`; una lista de patrones, sí — y ya lo ha
hecho dos veces.

### 4.3 Coste (supuesto explícito, y cómo se comprueba)

Supuesto: ~130 tokens por producto con los 12 ejes (nombre ~10 + 12 enunciados
de ~10), que **hay que confirmar con `usage.input_tokens` en la primera llamada
real**; a $0,042/Mtok sale **~$0,29 el catálogo entero** (52.567), o **~$0,09 la
pasada de validación** sobre los 16.605 declarados.

**Una petición por producto, no un lote de productos en un `state`.** Es tentador
meter cien nombres en un `state` y hacer cien preguntas para bajar el reloj, pero
es exactamente el modo de fallo nº 5 de su lista: para la pregunta sobre el
producto 37, los otros noventa y nueve nombres son *«content unrelated to the
decision»*, y la precisión cae. Su propia recomendación es *«send only the fields
the question needs»*, y el *fan-out* que documenta es para **varias preguntas
sobre el mismo sujeto** — que es justo el diseño de aquí: los 12 ejes de un mismo
producto, en una petición, en paralelo. El coste no cambia ($0,29); el reloj sí:
52.567 peticiones a 1.200/min son **~44 minutos** en una tanda, y eso cabe en un
trabajo offline, no en la tarea de las 06:00.

### 4.4 Barra de aceptación

1. **Reproducir las listas donde el eje aplica**: alto en la banda de confianza
   alta sobre los valores coherentes con el pasillo. Y los desacuerdos, auditados
   uno a uno: cada desacuerdo es o un fallo del modelo o un fallo de la lista.
2. **Una prueba por eje** que fije el orden específico-antes-de-general (el
   `desnatad`/`semidesnatad`) y el "no lo dice" → eje ausente.
3. **Sustituye a una lista a mano solo si la lista desaparece del código para ese
   eje** y `tests/test_matching.py` (34 pruebas) y `tests/test_atributos.py`
   siguen en verde. Un eje se cambia de uno en uno, nunca los doce de golpe.
4. Si no reproduce en castellano lo que ya sabemos, **no se usa para lo que no
   sabemos**. Eso incluye no añadir ejes nuevos porque "el modelo los vería".

---

## 5. Sitio 2: las categorías sin pasillo — el único «A MANO» de la cadena diaria

`projects/cesta/auditar_secciones.py:444-454`. La propuesta sale de *lo que hace
el resto de su rama*; cuando la rama no es clara, imprime
`A MANO: su rama no es clara` y esa decisión la toma una persona. Medido hoy:

```
=== categorias nuevas, sin mapear todavia: 9
     2  alcampo    Electrodomésticos > Cepillos de dientes eléctricos       -> A MANO
     2  alcampo    Bebé                                                     -> A MANO
     2  dia        navidad/dulces-navidad                                   -> A MANO
     1  alcampo    Juguetes > Los juguetes más vendidos                     -> desayuno-dulces
     1  alcampo    Hogar y Decoración > Cubiertos, vasos, copas y botellas  -> A MANO
     1  alcampo    Bricolaje > Herramienta de mano                          -> hogar
     1  carrefour  congelados/rebozados-.../lasanas-y-canel...              -> A MANO
     1  carrefour  drogueria-y-limpieza/papeleria/colorear                  -> hogar
     1  carrefour  parafarmacia/complementos-alimenticios/digestivo         -> A MANO
```

- **Son 19 opciones**, exactamente `core/secciones.ORDEN` (de `frutas-verduras` a
  `promociones`): cabe en un solo `Choice`, con sitio de sobra bajo el tope de 255.
- **El banco también es gratis**: `core/datos/secciones.yml` tiene **881 claves
  mapeadas** (alcampo 206, aldi 101, carrefour 294, dia 254, mercadona 26). Un
  modelo que reproduzca esas 881 se ha ganado el derecho a decidir las 6 que hoy
  van a mano. Las 6 de hoy son, leyéndolas, de sentido común: «Cepillos de dientes
  eléctricos», «Bebé» (¡y existe el pasillo `bebe`!), «dulces-navidad»,
  «Cubiertos, vasos, copas y botellas», «lasañas y canelones»,
  «complementos-alimenticios/digestivo».
- **Volumen y coste**: 9 claves, 12 productos, ~2.700 tokens al día ≈
  **$0,0001/día**. Aquí el valor no es el coste, es **quitar el último «A MANO»
  de la cadena de las 06:00**.
- **Barra**: `confidence ≥ 0,9` → se aplica sola; por debajo, se imprime como hoy
  y lo mira una persona. Cero «A MANO» es el objetivo; **ninguna asignación
  automática por debajo del umbral** es la condición.

---

## 6. Un tercer sitio que se apuntó, y que la medida cierra: las ofertas sin regla

Se apuntó como candidato («cuando `core/promos.py` cae en `SIN_REGLA`»). Medido
hoy sobre las 7.087 fichas con texto de oferta:

| mecánica que lee `promos.lee()` | fichas |
|---|---:|
| `enesima` | 2.301 |
| `nxm` | 1.327 |
| **`sin_regla`** | **1.260** |
| `porcentaje` · `precio_fijo` · `umbral` · `descuento_fijo` · `lote` | 2.199 |

1.260 fichas (17,8 %) se quedan sin mecánica, y `core/promos.py:20` dice que
entonces se tratan como si no hubiera oferta. Pero **esos 1.260 textos son 20
textos distintos**, y los cuatro primeros suman 977:

```text
  599  Producto en Folleto (10/09/26_23/09/26)
  159  Stock Fuera (Unidades Limitadas)
  115  Super Precio
  104  XXL Ahorro
   74  En pack, más fácil
   55  Novedad Alcampo
   49  Envío Gratis
   34  PROTEÍNA, CALIDAD, SABOR
   ...
   (20 distintos; sólo 4 aparecen una sola vez)
```

**No hay juicio que pedirle a un modelo: hay veinte cadenas que poner en una
lista**, que es literalmente lo que su página de defectos recomienda («si la
unidad la encuentra una expresión regular, el modelo no tiene nada que añadir»).
Y la mitad no son mecánicas de precio en absoluto: *Producto en Folleto*, *Stock
Fuera*, *Novedad*, *Envío Gratis* son insignias de marketing. La pregunta de
verdad —si «Producto en Folleto» debe contar como oferta— es de negocio, no de
modelo. **Sitio cerrado, y sin gastar un céntimo.**

## 7. Lo que NO se toca

- El **camino crítico de las 06:00** no llama a nada que esté fuera de la máquina.
  Si el experimento entra, entra primero **fuera** de la tarea diaria, midiendo.
- El **canal de vectores** y la **invariante de reparto** que ya está escrita en
  `core/matching.py` (un grupo no puede tener dos productos de la misma cadena,
  salvo EAN compartido) van antes: son el 64 % y el 16 % del problema medido.
- **Bronze no se borra**, la plataforma **no escribe en gold**, y un dato que no
  cruza la frontera de gold no existe.
- **Ningún dato personal** sale de aquí; lo que se manda es el nombre de un
  producto de supermercado, que es público. Aun así es un tercero en un proyecto
  *local-first*: va escrito, no implícito.

---

## 8. El bloqueo, y lo que hay que decidir cuando se abra

**El acceso.** Es lista de espera, y sin clave no hay ni una medida: todo lo de
§4.3 es un supuesto con la cuenta a la vista. Y hay tres cosas del proveedor que
hay que vigilar, no creer: el **castellano** (avisa él mismo de que no lo ha
medido), el **precio** (admite que no puede demostrar que no esté subvencionado:
*"we'll need the long-term to prove the sustainability of our pricing"*) y la
**latencia** (sin medición independiente).

**Lo que hay que decidir antes de escribir código**: si el experimento es
`projects/cesta/juez_jev.py` (un módulo aparte, de solo lectura sobre gold, con
su medición y sus pruebas, al estilo de `banco_de_pares.py`) o un *script* de
una tarde que se tira después. El primero encaja con «ninguna pieza nueva sin
medición antes/después»; el segundo es más barato y no deja deuda. **Cuesta menos
de un euro** y no hace falta decidirlo hoy: hace falta la clave.

**Lo que el experimento sí deja aunque Jev no valga**: el banco de los ejes con
sus tres casos de sobre-disparo (`natural`, `blanco`, `orujo`) y la lista de las
6 claves que hoy van a mano. Los dos valen sin Jev.
