# Decisiones de interfaz — 9 de noviembre de 2026

Para David. Tres cosas de la [revisión de interfaz](revision-interfaz.md) que **sí** necesitan
tu decisión. El resto se aplica en esta sesión sin preguntar: los «0,00 €» de portada y de
comparar la cesta (§4.1 y §4.2), el tiempo dentro del coste de la receta (§4.7), las tildes
(§4.10), el buscador del recetario (§4.8), el título cruzado al importar (§4.5), la etiqueta de
Ajustes (§4.9) y la cabecera (§4.4).

Cada decisión lleva: problema → opciones → **coste** (esfuerzo y riesgo) y **qué gana** cada
una → recomendación en dos líneas. Escala de esfuerzo: **S** = media sesión, **M** = una
sesión, **L** = más de una.

**Resumen de las recomendaciones**

1. Duplicado de Carrefour → **B ahora** (colapsar en pantalla) y **A** en el siguiente pase del
   emparejador. C, no.
2. Porcentajes → **A**: una sola base, la más barata, dicha en la frase; el ahorro, en euros.
3. «Faltan precios de…» → **B**: contador con ancla a «Ingredientes».

## Cómo está comprobado (y qué es supuesto)

- **La API no está levantada.** Los datos del caso salen del gold del repo: `data/gold/actual.json`
  dice versión `20261109-113939`, **el mismo catálogo de la revisión**. Consultas hechas con
  DuckDB sobre `data/gold/grupos.parquet` (53.182 filas, 40.257 grupos).
- Capturas y textos crudos: `data/revision-ui-2026-11-09/` (fuera de git; los `.txt` de `textos/`
  son lo que se leyó en pantalla).
- Líneas de código: **árbol de trabajo de hoy** (commit `8d59f65` más los cambios sin commitear
  de §4.1, §4.2 y §4.7). En `Portada.tsx`, `CompararCesta.tsx` y `RecetaDetalle.tsx` esas líneas
  se mueven mientras se escribe esto; el resto de ficheros citados está sin tocar.
- Supuestos, dichos como tales: el «−43 %» de la portada (§4.6) **no sale en la captura 01**
  (esa captura es el estado de los 0,00 €) y no lo he podido reproducir; lo que consta es la
  fórmula que lo pinta.

---

## 1. El mismo producto de Carrefour sale dos veces

**Problema.** En `/compra/comparar/10645` (captura `04-comparar-grupo-movil.png`) la tarjeta de
Carrefour tiene **dos bloques idénticos**: «Leche semidesnatada Carrefour brik 1 l. · 0,83 € ·
0,83 €/l · +5,1 % · nota 87,8» (textos/04, líneas 57-69 y 79-91). La cabecera dice
«**6 productos · 5 cadenas**» (textos/04:15). En la ficha del producto pasa lo mismo: «En otras
cadenas · mismo artículo» lista las dos filas iguales (captura `03-ficha-producto-movil.png`,
textos/03:36-43). Y hay una consecuencia que no se ve a simple vista: el duplicado **calla el
histórico** de Carrefour, porque la chispa se bloquea cuando la cadena tiene más de un producto
en el grupo (`Grupo.tsx:507`, `chispaBloqueada={lista.length > 1}`; el texto se lee en
textos/04:74 y 96).

**Lo verificado en el gold (no es un fallo de la pantalla, es una ficha duplicada del catálogo):**

| | id 530014571 | id 521007071 |
|---|---|---|
| Cadena | carrefour | carrefour |
| Nombre | Leche semidesnatada Carrefour brik 1 l. | Leche semidesnatada Carrefour brik 1 l. |
| EAN | **8431876100785** | **8431876100785** (mismo, GTIN-13 válido) |
| Precio / €/l | 0,83 € · 0,83 €/l | 0,83 € · 0,83 €/l |
| Ficha de origen | `…/R-530014571/p` | `…/R-521007071/p` |

Mismo EAN válido y misma presentación = **identidad exacta** según el contrato escrito en
`core/identidad.py:12-21` (`normaliza_gtin` en `:58-74`): dos fichas del mismo artículo, no dos
productos parecidos. Y no es un caso único: en el gold hay **40 grupos** con un duplicado de la
misma cadena y el mismo EAN (53 filas sobrantes; 0,1 % de los 40.257 grupos), **20 de Carrefour y
20 de Mercadona**, y en los 40 el EAN es válido.

**Lo enseña:** capturas `04-comparar-grupo-movil.png` y `03-ficha-producto-movil.png`.

| Opción | Coste (esfuerzo) | Qué gana | Riesgo |
|---|---|---|---|
| **A. Deduplicar en el catálogo (identidad) y colapsar en pantalla** | **M**: elegir cuál de las dos fichas es la canónica y guardar el alias, tocar el armado de miembros (`catalogo.py:1011`) y la serie (`catalogo.py:1030-1035`, que se pide por `fuente:id_fuente`), regenerar gold y revisar los 40 grupos. Sin API nueva. | Desaparece en todas partes a la vez (comparar, ficha, «6 productos», «precios de hoy», chispa) y **no vuelve** si Carrefour recaptura la ficha que sobra. El catálogo queda con una ficha por artículo y los recuentos dejan de mentir. | Cambia el censo de 40 grupos; si el canónico se elige por precio y no por frescura se puede perder la serie buena de la otra ficha. Tocar gold obliga a comparar cifras antes/después y a revisar pruebas de la API. |
| **B. Colapsar solo en pantalla** | **S**: un helper puro que agrupe por `(cadena, ean)` y se use en los dos sitios donde se ven (`Grupo.tsx:493-511` y `Producto.tsx:552-553`), con un contador «2 fichas iguales»; pruebas nuevas (`Grupo` no tiene prueba de página) y revisar `Producto.test.tsx`, que monta la ficha con la respuesta real. | Quita el ruido ya, sin tocar datos ni gold, y **devuelve la chispa de Carrefour** (`chispaBloqueada` deja de bloquearse). Es el arreglo que menos se puede romper. | La cabecera sigue diciendo «6 productos» (`Grupo.tsx:282`) y la API sigue mandando dos fichas: el duplicado sigue en el gold y habría que hacer A algún día. |
| **C. No tocar** | **0**. | Nada nuevo. | La pantalla que existe para comparar precios enseña dos filas idénticas y oculta un histórico; se lee como fallo de la app aunque sea del catálogo. |

**Recomendación.** B ahora y A en el siguiente pase del emparejador: B es media sesión, quita el
ruido en las dos pantallas donde se ve y devuelve la chispa, mientras que A es el arreglo bueno
(los 40 casos comparten EAN válido, así que la identidad ya sabe decidirlo) pero pide tocar gold y
elegir canónico, y no corre prisa para 40 grupos de 40.257. C, no.

---

## 2. Los porcentajes no dicen su base (y cada pantalla usa una)

**Problema.** Tres pantallas enseñan diferencias de precio con dos bases distintas y sin decir
cuál es:

- **Comparar un grupo** (captura 04): «DIFERENCIA ENTRE LA MÁS CARA Y LA MÁS BARATA: **130,4 %** ·
  1,03 € por unidad» (textos/04:25-26; `Grupo.tsx:364-367`). Base = €/l más barato (0,79 €/l
  frente a 1,82 €/l del grupo): «la más cara cuesta un 130,4 % más».
- **Buscar** (captura 02): «**hasta un 61,7 %** en el grupo» en cada fila (textos/02:37;
  `componentes/Etiquetas.tsx:157-172`, el texto en `:169`; también
  `componentes/TablaResultados.tsx:175` y `:194`). Base = la más barata (`catalogo.py:435-451`,
  el cálculo en `:449`).
- **Portada**: una píldora «**−43 %**» que cuenta el ahorro contra la **más cara** y **sobre los
  totales de la cesta**, no sobre un grupo (`Portada.tsx:264-268` y `:283-287`). §4.6 la cita; la
  captura 01 enseña en realidad el estado de los 0,00 €, así que lo verificado es la fórmula.

No es la misma cuenta —una compara €/l dentro de un grupo, otra totales de cesta—, pero
comparten el defecto: **un porcentaje sin base no se puede comprobar**, y encima cada pantalla
elige un extremo distinto. Y la base no es cosmética: con el par documentado 0,79/1,82 €/l el
sobreprecio es **130,4 %** con base barata y **56,6 %** con base cara; el 61,7 % de Buscar sería
**38,2 %** con la otra base. En la prueba de la portada (408 € y 794 €, `Portada.test.tsx:78-87`)
el «−48,6 %» es «+94,6 %» si se cambia la base (`Portada.test.tsx:232`).

Lo importante para decidir: **la app ya calcula con base = la más barata** en el grupo
(`catalogo.py:1136`) y en el buscador (`catalogo.py:449`). La portada es la única que calcula
aparte, y la frase más leída ya habla así («Cuesta un X % más que en CADENA», `logica/frase.ts:108-109`;
«te ahorras N € frente a la más cara», `:102-103`).

**Lo enseña:** capturas `04-comparar-grupo-movil.png`, `02-buscar-movil.png` y
`01-portada-movil.png` (esta última, el estado con precios no está en la captura).

| Opción | Coste (esfuerzo) | Qué gana | Riesgo |
|---|---|---|---|
| **A. Una sola base, la más barata, y nombrarla** | **S**: textos en `Grupo.tsx:366`, `Etiquetas.tsx:169` y `TablaResultados.tsx:175`; en la portada la píldora pasa a euros («ahorras 3,86 €» en el caso de la prueba, que no depende de la base) y hay que reescribir `Portada.test.tsx:232`. **No se toca la API**: ya calcula en barata. | Una sola convención, la que ya está en los datos: cualquier % se lee «X % más que la más barata», se puede comprobar y no cambia de significado al cambiar de pantalla. El dinero ahorrado se sigue diciendo en euros, como ya se hace en `frase.ts:102-103` y `CompararCesta.tsx:466-469`. | El número cambia de magnitud y hasta de signo al cambiar la base (el 130,4 % de comparar es un «−56,6 %» si se cuenta como ahorro; un 43 % de ahorro es un 75,4 % de sobreprecio), así que quien recuerde la cifra vieja creerá que el precio cambió. Quitar el % de la portada es un cambio visible en la pantalla de entrada; se compensa con los euros. |
| **B. Dos bases, pero siempre dichas** | **S**: solo textos (`Grupo.tsx:366`, `Etiquetas.tsx:169`, píldora de `Portada.tsx:283-287`); los números no se tocan; pruebas de texto. | Conserva el gancho «ahorras %» en la portada y la magnitud «el doble» en comparar, y cada cifra dice contra qué se mide. Es el cambio mínimo para que nada parezca contradecirse. | Conviven dos marcos (sobreprecio frente a ahorro): quien lea 61,7 % y 43 % sin la coletilla seguirá pensando que se contradicen, y hay que vigilar que ningún % nuevo vuelva a salir desnudo. |
| **C. Base = la más cara en toda la app** | **M–L**: cambiar `catalogo.py:1136` y `:449` y todo lo que lee `ahorro_pct` (el propio catálogo cuenta cinco pantallas, `catalogo.py:1093-1096`), más pruebas y documentación. | Todo se lee como «lo que te ahorras», que es la pregunta literal del usuario. | Los porcentajes se encogen casi a la mitad (130,4→56,6; 61,7→38,2) y se pierde «cuánto más caro es el otro»; se toca la API y varias pantallas de golpe, y el campo se seguiría llamando `ahorro_pct`. |

**Recomendación.** A: porcentaje = sobreprecio contra la más barata, y decirlo; ahorro = euros,
que es como ya habla la frase más leída (`frase.ts:108-109`) y como ya calcula la API. En la
portada, «ahorras 3,86 €» dice más que «−48,6 %» y no necesita base.

---

## 3. (Opcional) El aviso «Faltan precios de…» de la receta: lista o contador

**Problema.** En `/recetas/245` (captura `10-receta-movil.png`) el aviso es **un párrafo de 258
caracteres con cuatro nombres dentro de la tarjeta verde del coste**: «Faltan precios de Patatas
para freir 2 Kg Carrefour, Media tortilla…, AUCHAN… y PRODUCTO ALCAMPO Aceite de orujo… 1 l..»
(textos/10:22; se genera en `RecetaDetalle.tsx:208-221` y se pinta en `:291-298`). §4.7 lo llama
«seis nombres»: en la captura son **cuatro** (los cuatro ingredientes sin coste), y el problema es
el mismo. De propina, `enEspanol` (`:201-205`) deja «…Producto Alcampo. y … 1 l..» con punto y
seguido y punto final.

Ya hay una versión mecánica en el árbol de trabajo: con más de tres ingredientes, un contador
(«Faltan precios de 4 ingredientes: los marcados como «sin coste» aquí abajo», `:219`). Lo que
falta por decidir es si esa versión se queda o se cambia por la lista desplegable.

**Lo enseña:** captura `10-receta-movil.png` y textos/10:17-22.

| Opción | Coste (esfuerzo) | Qué gana | Riesgo |
|---|---|---|---|
| **A. Lista desplegable, una línea por ingrediente con enlace al buscador/ficha** | **M**: `sinPrecio` son nombres ya formateados (`RecetaDetalle.tsx:159-198`), no identificadores; para enlazar hay que llevar el id desde el coste y rehacer la prueba de `RecetaDetalle.test.tsx`. | El aviso se vuelve accionable: se busca el ingrediente y se le pone precio, que es lo que hace que el dato se rellene. Deja de ser un muro. | Un desplegable dentro de la tarjeta del coste tapa el dato que se viene a ver, y **duplica** lo que ya está dos secciones más abajo en «Ingredientes», donde cada línea sin precio dice «sin coste» (`:358`). |
| **B. Resumen con contador, y el detalle en «Ingredientes»** | **S**: texto y contador (ya está en el árbol); opcionalmente un ancla a `#ingredientes` (`:327` y `:335`). | Cabe en una línea, no repite una lista que ya está en la misma pantalla y el nombre de cada ingrediente se sigue leyendo justo debajo. | No lleva al buscador; si se quiere acción, hay que enlazar los «sin coste» de la lista de ingredientes. |

**Recomendación.** B, con el ancla a «Ingredientes»: el detalle ya está en la pantalla y un
desplegable dentro de la tarjeta del coste tapa justo lo que se viene a ver. Si luego se quiere
acción, el enlace va en cada línea de ingrediente sin coste (un solo sitio), no en el aviso.

---

## Anexo: qué NO se te pide decidir

Se aplica en esta sesión porque no depende de una decisión de producto: los ceros que parecen
precios (§4.1 y §4.2), el tiempo dentro de la tarjeta de coste (§4.7), las tildes (§4.10), el
buscador del recetario (§4.8), el título de «Importar una receta» (§4.5), la etiqueta «Cadenas
que tienes cerca» (§4.9) y la cabecera con un solo título (§4.4).
