# Jev — dos sitios donde encaja, y ninguno es juzgar pares

> Estudio del modelo `jev-1.13.0` (TypeSafe AI) y de los dos únicos huecos de este
> proyecto donde su documentación y la nuestra dicen lo mismo. **No hay una línea
> de integración escrita**: todo lo de aquí se mide y se decide cuando haya
> acceso, que es lista de espera.
>
> Fecha del estudio: **2026-09-23** · Raíz: `F:\aprendizaje\scrap`

> **Actualización del 24 de septiembre de 2026 — el bloqueo del acceso ya no existe.**
> Los pesos abiertos de **Laya** (Apache 2.0, `convaiinnovations/laya`) hacen el mismo
> trabajo, se instalan y corren **en este PC**, y el experimento del §4 **se ha hecho
> con ellos**: **73,1 % de acuerdo contra la barra de 97 %**, con dos fallos
> sistemáticos que su propia tarjeta documenta. Todo el detalle, con la receta
> reproducible, está en **`docs/LAYA.md`**. Lo que sigue valiendo de aquí, palabra por
> palabra, es el §2 (lo que estos modelos no saben hacer) y el §7. Este documento se
> deja como estaba: es el registro de lo que se midió el 23.

> **Actualización del 29 de septiembre de 2026 — el navegador que decide, y una
> corrección de hecho.** Circula un vídeo muy visto que propone **Jev + Playwright**
> para scrapear («un LLM planifica, Jev decide, Playwright ejecuta»). El **§9** lo mira
> con lo medido aquí y con lo que han medido otros, y la conclusión es que **no mejora
> la calidad de este trabajo**: las cinco cadenas leen JSON o el HTML del propio sitio
> y **ninguna necesita elegir un elemento**; en la pasada de hoy, a las 11:00, el
> navegador se ha abierto **4 veces** para 12 retos del WAF, y la tabla de estados de
> esa herramienta llama a ese caso
> `blocked` —lo informa, no lo resuelve—; y el único susto real que ha tenido este
> proyecto con un dato falso (**1.292 productos de Alcampo a 1,00 €**, §N31 del
> `BACKLOG`) **no lo habría cazado**, porque un precio de 1,00 € es perfectamente
> plausible: lo cazó la aritmética sobre el tiempo, que ya está en casa.
> Y una corrección: el §1 y el §8 dicen **«lista de espera», y eso caducó el 21 de
> septiembre** —el acceso es abierto, con 5 $ de regalo (~120 M tokens) y tres caminos
> independientes—. La tabla del §1 se deja como estaba, por la misma razón que la del
> 23: es el registro de lo que se sabía ese día.

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

---

## 9. El vídeo: Jev con Playwright. El navegador que decide, y por qué aquí no hay hueco

Revisado el **29 de septiembre de 2026**, sobre el material que circula estos días
(«un LLM planifica, Jev decide, Playwright ejecuta»).

### 9.1 Qué propone, verificado

| | `jev-browser` | `jev-ultrafast` |
|---|---|---|
| quién | Ying-Kai Liao (uno) | Browser Use × TypeSafe |
| repositorio | 91 estrellas, creado el **16/09**, último envío **hoy 29/09**, 5 incidencias abiertas, MIT | 21.257 estrellas, creado el **16/09**, último envío el 25/09, **165 incidencias**, MIT |
| paquete | npm `jev-browser` **0.1.1**, publicado el 17/09 (no se ha republicado) | `uv sync`, con Chrome por depuración remota |
| cómo | un LLM dice el objetivo, de uno en uno; cada ronda **una** petición de ~300 ms pregunta a la vez qué elemento, qué acción, qué valor, y si está hecho / hay error / está bloqueado / es irreversible; Playwright ejecuta | una petición por paso con las preguntas de operación y de objetivo; un LLM pequeño escribe texto **sólo** si la operación es escribir |
| lo que mide su propio banco | 42 tareas: **40 correctas, 0 «hecho» falsos**, 202 llamadas, 286 ms de media, 2.800-2.900 tokens de entrada por llamada, ~5 s por tarea | Zúrich→Londres en Google Flights en 7,1 s |

Y el aviso que deshace el titular: **ese vídeo habla de visión, y Jev no ve**. Su
documentación, leída hoy: *«Input: Text only. String, JSON object, or array of text
values. **No image, audio, or video input**»*. Lo que Jev mira es una **descripción en
texto de la página** que escribe el código que envuelve al navegador (etiquetas, roles,
estado, texto visible). Quien mira píxeles, si alguien mira píxeles, es otro modelo:
Jev sólo elige entre opciones que ya le han escrito. Ponerle el cartel de «visión» a
esto es lo que hace que suene a magia y no a lo que es.

Contexto: Jev salió el **15/09** (su hilo de Hacker News pasó de 1.900 puntos, según
[el repaso de Zyte](https://dev.to/extractdata/jev-the-model-that-cannot-write-a-word-and-where-it-fits-in-web-scraping-does-it-45jb))
y **los dos repositorios del vídeo se crearon el 16/09**. Trece días.

### 9.2 Por qué no encaja aquí: cinco medidas, ninguna opinión

**1. Ninguna de las cinco cadenas necesita elegir un elemento.** Lo medido hoy mismo,
en `data/ejecuciones.log` y en los colectores: Aldi **2.126 productos en 90 s**,
Mercadona **4.335 en 100 s**, DIA **5.723 en 511 páginas y 652 s**, los tres con **0
errores**; ayer Carrefour **16.560 en 2.099 páginas** y Alcampo **23.929**. Todo eso
sale de `core/fetch.py`, `selectolax` y `js_object` sobre URLs sacadas del sitemap, con
el nombre y el precio en un campo con nombre. La pregunta «¿en qué elemento pulso?» no
se hace ni una vez al día, y elegir el elemento es exactamente lo que estas herramientas
venden.

**2. El navegador, hoy, se abre cuatro veces, y para lo que él no resuelve.** Lo contado
desde la marca de la pasada de hoy (`############ 2026-09-29 10:26:40`), a las 11:00 y con
la pasada todavía en marcha: **12 avisos de WAF**, **4 renovaciones de sesión** (navegador
de verdad) y 8 reintentos sin navegador. La pasada entera de ayer: **30 y 10**. Y el
registro completo (26 pasadas, 4.629 líneas): **279 avisos de WAF y 37 renovaciones de
sesión**. Ése es todo el trabajo de navegador de un mes, y para él no hay nada que
decidir: hay que **esperar**. Y la tabla de
estados de `jev-browser` tiene una fila que se llama **`blocked` — «captcha, access
denied, error page»**: nuestro problema exacto, devuelto como estado, no resuelto. Lo que
sí lo resuelve, y funciona, es `core/waf.py`: abrir el Chrome de verdad, esperar a que el
reto de AWS WAF se resuelva solo (`es_reto()` lo reconoce por dos cadenas del HTML) y
guardar la cookie.

**3. Jev declara que no sabe comparar números** (§2: *«not a calculator… does not count
reliably»*), y el **64 %** de nuestro problema de emparejamiento es numérico (§3). El
navegador no toca el emparejamiento. Y la segunda cosa que peor se le da a
`jev-browser`, según sus propias notas, es *«juzgar si esta tabla está ordenada o si ha
cambiado exactamente una cosa»* — que es, literalmente, lo que hacen nuestras puertas.

**4. El único dato falso que nos ha dado la vida real, no lo caza.** El **27 de
septiembre** (§N31 del `BACKLOG`) aparecieron **1.292 productos de Alcampo a 1,00 €**,
con un escalón de un día para otro (160-176 al día → 1.233 el 14 de septiembre), escalón
que sigue ahí. Alcampo **publica** ese precio: `"price": {"amount": "1.00"}`, con su
`unitPrice` coherente (0,18 €/100 ml = 1,00 €/560 ml), `available: true` y ninguna
promoción declarada. Pasa todos nuestros filtros estrictos. Un juez de plausibilidad
preguntado «¿esto parece un precio de verdad?» contesta que **sí**, con confianza alta:
1,00 € es el precio más plausible del mundo. Lo que lo encontró fue **aritmética sobre el
tiempo**, gratis y determinista. Ése es el reparto de papeles que hay medido aquí.

**5. Dentro de una puerta, un modelo empeora la puerta.** `prueba_navegador` y
`prueba_funciones` no son demostraciones: son **instrumentos**, y su valor es que dos
ejecuciones dan lo mismo y que una diferencia se puede señalar. Cambiar un selector por
un modelo que acierta «casi siempre» convierte una comprobación reproducible en una
probabilística, y la barra que el dueño firmó (que la comprobación esté **en las
puertas**) deja de significar lo que dice. Es la misma razón por la que la captura de
390 px no decide un número: se juzga en el DOM.

### 9.3 El único sitio de scraping que alguien ha medido de verdad, y no es el navegador

**Zyte** —que vive de scrapear— lo probó el 21 y el 22 de septiembre y publicó las dos
mitades: [dónde encaja Jev en un scraping](https://dev.to/extractdata/jev-the-model-that-cannot-write-a-word-and-where-it-fits-in-web-scraping-does-it-45jb)
y [cómo lo usó para parar un rastreo cuando los datos dejan de parecer reales](https://www.zyte.com/blog/stopping-a-crawl-when-fields-stop-looking-real/).
Su filtro, que es el nuestro, palabra por palabra:

> *«if a regular expression, a status code, or a CSS class can answer the question, do
> not ask a model»*.

Y su conclusión sobre el uso bueno: **no extraer, sino juzgar lo ya extraído**. Construyó
`scrapy-jev`, una puerta de calidad: una pregunta de puntuación por campo («¿esto sigue
pareciendo un nombre, un precio, un SKU real?»), **20 registros de muestra**, un campo
vacío cuenta como suspenso, y si la tasa de aprobados baja, se para el rastreador. Lo
medido por ellos:

| | |
|---|---|
| lo que caza | un `sku` que devuelve el título del producto (**0,08-0,35**) y un `name` que llega vacío |
| lo que **no** caza | un selector que apunta a **otro producto** pero devuelve algo con forma de nombre y de precio; y renombrar la clase del precio no disparó nada *«y correctamente»*, porque la extracción era una expresión regular |
| coste real | 570 tokens de entrada = **0,000024 $ por registro**; muestrear 20 en vez de todos es una fracción de céntimo |
| el argumento de muestrear | no es el dinero —$30 por millón de registros es trivial— sino que puntuar todo significa que **cada registro espera a una llamada externa**: un millón de llamadas que tienen que salir bien en vez de veinte |
| y la confianza no avisa | en una corrida mayor etiquetó una página de categoría como *poetry* con **confianza 1,00**; hay que poner a mano la opción «ninguna de las anteriores» |

Traducido a este proyecto: **la mitad estructural de esa puerta ya está en casa**, y es
gratis y determinista — `core/cobertura.py`, `core/runlog.check_drift`, `verificar_ingesta.py`
y el escalón de los 1,00 € del §N31 se cazan con cuentas, no con juicios. Lo que la puerta
de Zyte añadiría es una clase que hoy no vemos: **el valor plausible pero equivocado**. Es
una clase real. También es, según su propia medida, una clase **estrecha**, y la forma de
saber si aquí existe es un experimento de **sólo lectura sobre `gold` ya construido** —como
`banco_de_pares.py` o `laya_ejes.py`—, fuera de la cadena de las 06:00 y sin que la cadena
dependa de un tercero. Eso no hace falta decidirlo hoy.

### 9.4 Lo que sigue abierto de Jev, que no es esto

- **El bloqueo del §8 ya no existe**: el acceso es **abierto desde el 21 de septiembre**,
  sin lista de espera y con **5 $ de regalo (~120 M tokens)**, y se llega por tres caminos
  independientes —`api.typesafe.ai`, la [pasarela de Vercel](https://vercel.com/ai-gateway)
  (`typesafe-ai/jev`, comprobado hoy en su lista de modelos) y el endpoint alfa de
  OpenRouter, que es el que usa Zyte—. El precio sigue siendo **0,042 $/Mtok de entrada,
  salida gratis**, 64k de contexto (32k para el `state`) y 1.200 peticiones/minuto. Lo que
  no ha cambiado: **el castellano sigue sin medir** (su aviso es literal: *«test on your
  own content before relying on Jev for a non-English workload»*), y `jev-browser`
  afirma que funciona en interfaces no inglesas, cosa que **nadie ha medido**: el único
  número en castellano que existe aquí es el de Laya, **73,1 %**.
- **El §4 ya se hizo, con un hermano abierto, y no llegó**: Laya dio **73,1 % contra la
  barra de 97 %** (`docs/LAYA.md`). La carga de la prueba está ahora en Jev, no en
  nosotros.
- **Lo que sí es nuevo y encaja con nuestro hueco**: el proveedor tiene recetario propio
  para **justo la forma del §5** — [clasificación jerárquica](https://docs.typesafe.ai/cookbooks/hierarchical_classification)
  de productos de *retail* con búsqueda en haz sobre las probabilidades de `Choice`, y
  [clasificación usando la confianza](https://docs.typesafe.ai/cookbooks/classification_using_confidence)
  con reserva a la división superior cuando la confianza baja, que es exactamente nuestro
  «sin pasillo». Y [extracción con candidatos ya mordidos](https://docs.typesafe.ai/cookbooks/pre_parsed_value_extraction):
  la expresión regular propone, el modelo elige el trozo. Las tres son **texto, sin
  navegador**.

### 9.5 Cómo se comprueba lo de aquí

```powershell
# solo la pasada en curso: desde su marca de fecha hasta el final del registro
$t = Get-Content data/ejecuciones.log
$i = ($t | Select-String -Pattern '^#{5,} \d{4}-\d{2}-\d{2}' | Select-Object -Last 1).LineNumber
$hoy = $t[($i-1)..($t.Count-1)]
($hoy | Select-String -SimpleMatch 'el WAF ha saltado').Count      # 12 hoy
($hoy | Select-String -SimpleMatch 'sesion renovada').Count        #  4 hoy (navegador de verdad)
# quien abre un navegador y quien no, en los colectores
Select-String -Path projects/cesta/collectors/*.py, core/waf.py -Pattern 'patchright|playwright'
uv run pytest tests/test_waf_alcampo.py -q
```

Lo de fuera se cita con enlace y con fecha, porque no se reproduce en este PC:
[documentación de TypeSafe](https://docs.typesafe.ai/models) (solo texto, precio,
lengua), [`jev-browser`](https://github.com/Ying-Kai-Liao/jev-browser) y sus
[resultados](https://github.com/Ying-Kai-Liao/jev-browser/blob/main/RESULTS.md) y
[notas de diseño](https://github.com/Ying-Kai-Liao/jev-browser/blob/main/NOTES.md),
[`jev-ultrafast`](https://github.com/browser-use/jev-ultrafast),
[`awesome-jev`](https://github.com/ckaraca/awesome-jev) (que es de donde sale que ya no
hay lista de espera), los dos artículos de Zyte y
[la apertura total del 21/09](https://eu.36kr.com/en/p/3992394169613316).

**Veredicto.** El vídeo **no mejora la calidad de este trabajo**: resuelve —elegir el
elemento, pulsar, esperar a que la página se asiente— un problema que aquí no se plantea
ni una vez al día, y no resuelve el que sí se plantea (que las cinco cadenas sigan
entrando y que los números del catálogo sean verdad). Lo que de verdad ha mejorado la
calidad de este scraping en septiembre no ha sido un modelo: ha sido la herencia del
número de grupo (`core/grupos_ids.py`), la guarda de cobertura, el rescate de Carrefour y
las puertas. Lo que queda abierto de Jev es lo que este documento ya decía —el §5, las
claves sin pasillo— y **eso no lleva navegador**.
