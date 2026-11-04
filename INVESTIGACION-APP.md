# Investigación — qué hacen las apps del sector y qué copiamos con criterio

**Fecha de consulta de todas las fuentes: 2026-11-04.** Encargo: `ALCANCE-APP.md` §2. Autor: `investigador-app`.
Objetivo: decidir las funciones de la app de consumo con referencias leídas de verdad, no de memoria.

---

## 1. Qué se ha mirado

| Referente | Enlace consultado | Fecha | ¿Legible? | Qué se ha podido ver |
|---|---|---|---|---|
| Soysuper | https://apps.apple.com/es/app/soysuper/id985951382 | 2026-11-04 | Ficha sí; web no | Funciones y cadenas en la ficha; `soysuper.com` solo devuelve «Cargando…» (JS); su `sitemap.xml` lista 17 ficheros de productos. |
| Idealo | https://apps.apple.com/es/app/idealo-app-de-compras-online/id454415640 | 2026-11-04 | Solo la ficha | Web bloqueada: `idealo.es` e `idealo.co.uk` devuelven **HTTP 403** anti-bot. **No se ha podido ver una ficha de producto ni su precio por kg/l.** |
| CamelCamelCamel | https://camelcamelcamel.com/features · https://de.camelcamelcamel.com/THQ-21217-Oben/product/B0027BOXK8 | 2026-11-04 | Sí | Funciones y una ficha real con tabla mínimo/máximo/actual/media. |
| Lidl Plus | https://apps.apple.com/es/app/lidl-plus/id1238611143 · https://www.lidl.com/c/lidl-plus-faqs/s10097623 | 2026-11-04 | Sí (fichas) | Funciones en la ficha ES; funcionamiento en la FAQ (versión EE. UU.). `lidl.es` corta tras el menú. |
| Mercadona | https://apps.apple.com/es/app/mercadona/id1368037685 · https://ayuda.tienda.mercadona.es/hc/en-us/articles/360000841132-Purchasing-from-your-mobile-device | 2026-11-04 | Sí | Funciones de la ficha y ayuda oficial de compra desde el móvil. |
| Yuka | https://help.yuka.io/l/es/article/ijzgfvi1jq · https://yuka.io/es/aplicacion/ | 2026-11-04 | Sí | Método de puntuación (60/30/10) y funciones de la app. |
| MyRealFood | https://apps.apple.com/es/app/myrealfood-recetas-y-plan/id1458031749 | 2026-11-04 | Sí | Nota 0–10, alternativas, menú semanal, kcal/macros, lista por pasillos. |
| BOE (contexto legal) | https://www.boe.es/diario_boe/txt.php?id=BOE-A-2000-24118 | 2026-11-04 | Sí | Obligación de indicar el precio por unidad de medida y su definición. |
| OCU (contexto) | https://www.ocu.org/consumo-familia/supermercados/calculadora/comparar-precios-supermercados | 2026-11-04 | Portada sí; fondo no | Comparador de cesta por perfil familiar reservado a socios (muro de pago). |

Las fichas de Google Play devolvieron contenido vacío; las de App Store sí son servibles. No se ha copiado texto ni capturas: todo va resumido con palabras propias.

---

## 2. Por función del alcance

### 2.1 Comparar mi cesta

Referentes: Soysuper (ficha), OCU (portada del comparador).

**Qué hace.** Soysuper compara la lista de tu supermercado habitual entre Mercadona, Carrefour, Eroski, Alcampo, El Corte Inglés, Hipercor, DIA, Condis y Caprabo, con «más de 130.000 productos con fotos». La lista se dicta por voz, se puede escanear el código de barras para «ver el precio y la oferta que tiene cada supermercado» y existe una «lista rápida». OCU hace el mismo ejercicio por perfil familiar, tras muro de pago.

**Qué funciona.** La lista es el objeto central, no un buscador suelto. El escaneo resuelve la pregunta real en tienda. El precio se ata a un producto concreto, no a una categoría.

**Qué no funciona.** Su ficha marca **2,4/5 con 63 valoraciones**: fricción de uso (dato público, no medición mía). Y si una cadena no tiene un producto o no se ha capturado, su total parece mejor de lo que es.

**Qué copiamos.** Cesta persistente como pantalla principal; total por cadena; columna «qué falta en esta cadena»; entrada por búsqueda y escaneo; contador «N de M productos comparados».

**Qué no copiamos.** El «ahorro» único sin desglose; que el orden lo decida una comisión de afiliación; su diseño propietario.

**Qué dato necesita.** Precios del mismo día por cadena, cesta del usuario y la regla de comparables de `docs/PRECIO-POR-UNIDAD.md` (una unidad por grupo, atributos producto a producto). Y distinguir «no está» de «no lo hemos capturado».

### 2.2 Comparación por kg/litro

Referentes: BOE, RD 3423/2000. De Idealo **no se puede afirmar nada**: web bloqueada y su ficha no menciona precio por unidad.

**Qué hace la norma.** Obliga a indicar el precio de venta y el **precio por unidad de medida** (kg, litro, metro, m², m³ o unidad), «inequívoco, fácilmente identificable y claramente legible», en el mismo campo visual y también en publicidad. Fija excepciones (menos de 50 g/ml) y unidades especiales (docena en huevos, 100 g/ml en complementos y cosméticos).

**Qué funciona.** Es la única base honesta cuando cambian los tamaños y está respaldada por normativa. Una unidad por categoría evita mezclar peras con manzanas.

**Qué no funciona.** Mezclar unidades en un grupo produce ahorros absurdos: `docs/PRECIO-POR-UNIDAD.md` documenta el mismo producto con el mismo código de barras con precios por unidad que se llevaban diez veces.

**Qué copiamos.** €/kg o €/l como cifra principal; precio del envase como secundario; unidad siempre visible; si el grupo mezcla unidades, no comparar y decirlo.

**Qué no copiamos.** Ordenar por precio absoluto del envase y llamarlo «más barato»; esconder la unidad en letra pequeña.

**Qué dato necesita.** Cantidad y unidad normalizadas por producto, unidad dominante del grupo y precio por unidad calculado (la regla existe; la cobertura, en §4).

### 2.3 Historial de precio y «caro o barato»

Referentes: CamelCamelCamel (funciones y ficha real), Idealo (ficha de app).

**Qué hace.** CamelCamelCamel se define por sus **alertas por umbral de precio** y sus **gráficas de historial** con máximo, mínimo y media; su ficha enseña «Lowest Ever», «Highest Ever», «Current» y «Average» por tipo de precio, con rangos de 1 mes a todo el histórico. Idealo describe historial en gráfica, «Precio Ideal» (alarma al alcanzar el precio deseado) y favoritos con semáforo: amarillo si sube, naranja si no cambia, verde si baja.

**Qué funciona.** Mínimo y máximo van con **fecha** y el rango temporal se declara; la media sin periodo no significa nada y no la usan así. El semáforo de Idealo solo es útil porque hay una cifra detrás.

**Qué no funciona.** Un «mínimo histórico» con pocos días es falso aunque el cálculo sea correcto. Mezclar promoción con precio normal deforma el mínimo. Un semáforo sin cifras es una caja negra.

**Qué copiamos.** Mínimo, máximo y media **con periodo y número de observaciones**; «caro/barato» como percentil con frase en llano («hoy 1,29 €/kg; más barato que el 80 % de los días registrados»); promociones marcadas y separadas del precio base; fecha de última captura.

**Qué no copiamos.** Predicciones o «precio ideal» como promesa de cuándo comprar; semáforos sin números; gráficas que interpolan días sin dato.

**Qué dato necesita.** Serie diaria por producto y cadena, días acumulados, distinción oferta/base y fecha de la última captura. Con serie corta, la pantalla dirá «sin histórico suficiente» en vez de inventar un mínimo.

### 2.4 Alternativas más baratas del mismo grupo

Referentes: Yuka y MyRealFood (alternativas), Idealo («Gangas»: mayores caídas del día, no alternativas).

**Qué hace.** Yuka, al escanear un producto «mediocre o malo», recomienda «productos similares y mejores para la salud»; MyRealFood ofrece «alternativas más sanas» en la ficha. Ninguna de las revisadas ofrece un bloque de **alternativa más barata del mismo grupo comparable**; eso se diseña aquí con nuestras reglas.

**Qué funciona.** La alternativa se ofrece en contexto, dentro de la ficha, y «similar» se define por categoría, no por ocurrencia.

**Qué no funciona.** Proponer un producto más barato sin decir en qué se diferencia (tamaño, unidad, marca blanca, sello) es sustituir a ciegas. Sin grupo fiable, la «alternativa» es otro producto.

**Qué copiamos.** Bloque «más barato en el mismo grupo» en la ficha, con diferencia en € y €/kg y una línea de «en qué se diferencia», solo dentro de la unidad dominante.

**Qué no copiamos.** Ranking global de «lo más barato» sin comparabilidad; sustitución silenciosa en la cesta.

**Qué dato necesita.** Grupos comparables, unidad dominante, precio por unidad y atributos (nutrición, sellos) para no proponer algo no equivalente.

### 2.5 Etiquetado: Nutri-Score, sellos, certificados y aditivos

Referentes: Yuka (método y app), MyRealFood (ficha), Mercadona (ficha).

**Qué hace.** Yuka explica su método: **60 % calidad nutricional** sobre Nutri-Score «suavizado»; **30 % aditivos**, con cuatro niveles de riesgo (sin riesgo, limitado, moderado, de riesgo) y una regla dura —un aditivo rojo limita la nota a 49/100—; **10 % orgánico** por certificado ecológico. El riesgo de cada aditivo y sus fuentes se muestran en la app. Su ficha añade ficha detallada, historial de escaneos con colores, recomendaciones de similares mejores, búsqueda (premium), modo offline y preferencias (palma, gluten, lactosa). MyRealFood da una nota 0–10 con «lo bueno, lo malo» y alternativas. Mercadona ofrece nutrición, ingredientes y alérgenos **con zoom sobre la imagen del producto**: una foto de la etiqueta, no un dato filtrable.

**Qué funciona.** Una nota única ordena y el desglose explica; el color va con palabra y explicación; la fuente se consulta; las preferencias se aplican como filtro persistente.

**Qué no funciona.** La nota sin explicación es una caja negra. Nutri-Score no cubre procesamiento ni aditivos. Una etiqueta en imagen no se puede buscar ni filtrar.

**Qué copiamos.** Nutri-Score como letra + color + palabra; aditivos como lista con nombre, nivel de riesgo y fuente; sellos y certificados como chips filtrables; un «por qué» a un toque; filtros de preferencias.

**Qué no copiamos.** Una nota propia de salud; mezclar salud y precio en un índice; replicar la escala de Yuka (es su método).

**Qué dato necesita.** Nutri-Score, ingredientes y aditivos estructurados, sellos, certificados y alérgenos. §4 decide si entra completa o solo con sellos.

### 2.6 Recetas con coste real

Referentes: MyRealFood (ficha), Lidl (folleto y recetas enlazadas desde su web).

**Qué hace.** MyRealFood ofrece plan con menú semanal, kcal y macros, «miles de recetas» —también con lo que hay en la nevera— y **lista de la compra generada desde el menú, ordenada por pasillos**. Lidl enlaza recetas desde su web, sin coste. Ninguna de las revisadas muestra el coste con precios reales de supermercado: el coste es diferenciador, no copia.

**Qué funciona.** Receta → ingredientes → lista, y kcal por ración. «Con lo que tienes en la nevera» es un gancho real.

**Qué no funciona.** Una receta sin coste no responde a «cuánto me cuesta comer esto». El coste por ración exige precio comparable y cantidad exacta; muchas recetas usan «al gusto» o ingredientes fuera de catálogo.

**Qué copiamos.** Receta con ingredientes enlazados al catálogo; coste por ración con **rango** entre cadenas y fecha del precio; aviso «3 de 7 ingredientes con precio»; la lista se genera desde la receta.

**Qué no copiamos.** Un coste único sin cadena ni fecha; recetas con ingredientes que no se pueden comprar.

**Qué dato necesita.** Recetario propio o con licencia, cantidades, mapeo ingrediente→producto, precios del día y kcal. Sin recetario licenciado, no entra.

### 2.7 Calorías

Referentes: MyRealFood (kcal y macros), Yuka (nutrición), Mercadona (tabla como imagen).

**Qué hace.** MyRealFood integra kcal y macros en el plan; Yuka usa la calidad nutricional en la nota; Mercadona deja consultar la tabla nutricional con zoom a la foto.

**Qué funciona.** kcal por 100 g y por ración; el total de una receta o de una cesta.

**Qué no funciona.** kcal por envase sin decir si es peso escurrido; estimar cuando falta el dato; una tabla en imagen que no se puede sumar.

**Qué copiamos.** kcal/100 g y kcal por ración; total de la cesta con «N de M productos con dato nutricional», sin estimar el resto.

**Qué no copiamos.** Estimar calorías sin tabla; semáforos calóricos moralistas.

**Qué dato necesita.** Tabla nutricional estructurada (no imagen) y porción/ración. Si solo hay imagen, no hay función.

### 2.8 Avisos de bajada

Referentes: CamelCamelCamel (alertas), Idealo («Precio Ideal»), Lidl Plus (notificaciones y cupones).

**Qué hace.** CamelCamelCamel basa el producto en alertas por correo con **umbral que pone el usuario** y registro opcional. Idealo ofrece alarma al alcanzar el precio deseado. Lidl Plus envía notificaciones de promociones y aplica las ofertas de socio al escanear la app en caja.

**Qué funciona.** El umbral lo pone el usuario, no la app; el aviso lleva precio anterior y actual y enlace a la ficha; se puede usar sin cuenta.

**Qué no funciona.** Mezclar promoción con bajada real hace que se ignoren los avisos; sin control de frecuencia, el canal se quema.

**Qué copiamos.** Aviso **solo de productos de mi lista**; umbral por producto o «baja más del X %»; un resumen al día; enlace a la ficha con histórico; registro opcional. Primer corte in-app; push después.

**Qué no copiamos.** Push promocional; promesas de «precio ideal»; avisos sin cifra.

**Qué dato necesita.** Serie de precios, lista del usuario, canal (in-app/email/push) y preferencias. Sin serie fiable no hay aviso honesto.

### 2.9 Despensa y lista automática

Referentes: MyRealFood (lista desde el menú, por pasillos), Lidl Plus (lista de la compra), Soysuper (lista rápida).

**Qué hace.** MyRealFood genera la lista desde el menú semanal y la ordena por pasillos; Lidl Plus y Soysuper mantienen una lista de la compra.

**Qué funciona.** La lista generada ahorra tecleo; el orden por pasillos se nota en la tienda; marcar «ya lo tengo» sin borrar evita rehacer.

**Qué no funciona.** La despensa automática exige consumo, caducidad y stock; el inventario manual cansa y se abandona. Ninguna referencia documenta una despensa que se actualice sola.

**Qué copiamos.** Lista desde receta o menú, agrupada por sección de tienda, con «ya lo tengo» y persistencia.

**Qué no copiamos.** Despensa con caducidades en el primer corte: pide historial de compra que no tenemos y fricción alta.

**Qué dato necesita.** Receta o menú, productos y secciones de tienda. La despensa completa pediría historial de compra personal, hoy inexistente.

---

## 3. Patrones de interfaz para móvil de supermercado

De pie, con una mano, a 400 px. Lo que se deduce de lo leído y de `DOCTRINA-CALIDAD.md` §2:

- **Navegación.** Barra inferior con cuatro destinos como máximo (Cesta, Buscar, Producto/Historial, Recetas) y búsqueda arriba. Acción principal en la mitad inferior, al alcance del pulgar. Nada de gestos que haya que aprender.
- **Densidad.** Fila de producto de dos líneas: nombre y €/kg grandes; precio del envase y cadena pequeños. Dos acciones visibles por fila como máximo.
- **Comparación sin mentir.** Tabla de 3–6 cadenas con la mejor primera, marcada con icono **y** texto, nunca solo con color; «no disponible» cuando falte; total con «N de M comparados» y fecha; si la unidad del grupo no coincide, se dice y no se compara.
- **Histórico sin mentir.** Banda mínimo–máximo, puntos de captura y rango temporal visible, con leyenda «captura diaria; puede faltar algún día». No interpolar ni pintar promociones como precio base.
- **«Caro o barato» con datos.** Primero número y periodo, después color: «1,29 €/kg · más barato que el 80 % de los últimos 59 días». Con pocos días, «sin histórico suficiente».
- **Etiquetado legible.** Nutri-Score como letra + color + palabra; aditivos con nombre y nivel de riesgo, no solo el código E; «por qué» a un toque y con fuente.
- **Accesibilidad.** Contraste AA calculado, información nunca solo por color, objetivos de 44×44, texto escalable y `prefers-reduced-motion`. Cada pantalla con vacío, cargando, error y sin permiso (ubicación o notificaciones), explicando qué se pierde.

---

## 4. Datos que ya tenemos

Fuente: `docs/DATOS-APP-2026-11-04.md` (medición propia sobre el gold publicado `20261104-144138`, sin red ni base de casa). 40.082 grupos comparables, 52.982 productos, 59 fechas de precio (2026-09-06 → 2026-11-04).

| Función | Dato que exige | ¿Lo tenemos? | Cobertura medida | Decisión |
|---|---|---|---|---|
| Comparar mi cesta | precios same-day por cadena + disponibilidad | Sí, precios; **no** stock | 39.837 grupos pintables (99,4 %); **8.851** con precio hoy en 2+ cadenas (`precio_comparable`); **8.066** comparables de verdad (unidad dominante + fiable, **20,1 %**) | **hacer**, sin prometer comparación universal |
| Precio por kg/litro | cantidad y unidad normalizadas + unidad por grupo | Sí | 52.780/52.982 (99,62 %) con precio por unidad; 43.090 (81,33 %) con unidad comparable; 8.066 grupos con ≥2 cadenas | **hacer** |
| Historial y «caro/barato» | serie diaria + días + oferta/base | Sí | 39.906 grupos (99,56 %) con serie; **35.736 (89,16 %) con ≥30 días**; solo 1.941 con los 59; 407 con algún hueco >7 días | **hacer**, con la ventana real (59 días), nunca «90 días» |
| Alternativas más baratas | grupos comparables + unidad + atributos | Sí | **8.066 grupos** (2.803 con ≥3 cadenas); ahorro mediano **13,45 %** (p75 46,05 %) | **hacer** |
| Etiquetado | Nutri-Score, **aditivos**, sellos, certificados, alérgenos | Parcial: **no hay aditivos** | Nutri-Score 6.945 grupos (17,33 %); sellos 9.673 (24,13 %); certificados 995 (2,48 %); completo 1.264 (3,15 %) | **limitada**: Nutri-Score/sellos/certificados sí; aditivos, no (sin nueva ingesta) |
| Recetas con coste | recetario real + ingrediente→producto | **No** | `recetas.sqlite` = 242 recetas de prueba; **0/242 con coste**; 4/473 ingredientes con `producto_id` (y no existen en el catálogo) | **no en el primer corte**: primero recetario y mapeo |
| Calorías | tabla nutricional estructurada | Parcial | kcal en 9.252 grupos (23,08 %); **0 en alcampo, aldi y lidl** (no publican EAN) | **limitada**: se enseña donde hay dato, no se estima |
| Avisos | serie + lista + canal | Sí (backend entero) | 86 grupos con bajada real en la última captura; 15.945 en mínimo; 1.988 con <30 días (frase «90 días» a corregir) | **hacer** in-app primero |
| Despensa y lista | despensa + receta/menú + secciones | Despensa sí; lista desde recetas no | API de despensa completa; lista desde plan/compra/favoritos existe; desde recetas, 0/242 | **limitada**: despensa y lista desde plan/compra, sí |

**Lectura honesta que la app no puede saltarse.** De los 40.082 grupos, **31.207 (77,9 %) solo tienen una cadena** y 809 tienen 2+ pero no son comparables (unidad `ud` o mezcladas). El techo de comparación entre supermercados es **8.066 grupos (20,1 %)**. Las cifras «8.851/8.829» que se ven en el panel y en `metricas-cesta.json` son «precio hoy en 2+ cadenas»; «comparable de verdad» (misma unidad dominante y comparación fiable) son 8.066. La app dirá cuál está enseñando.

**Otros huecos medidos:** sin stock; sin EAN en Alcampo/Aldi/Lidl (por eso no hay Nutri-Score ni kcal ahí); sin precios por provincia ni de cadenas fuera de las 6; sin histórico anterior al 6/9; el 1 % de filas de Alcampo con precio nulo. Detalle y comandos en `docs/DATOS-APP-2026-11-04.md` §13.

---

## 5. Decisiones propuestas (ajustadas con §4)

**Primer corte, en este orden (lo que tiene dato denso y backend ya hecho):**

1. **Comparar mi cesta, con €/kg como base.** La que engancha. Total por cadena, «qué falta», «N de M comparados» y fecha; y decir si se está comparando el conjunto completo o solo los 8.066 comparables de verdad.
2. **Historial de precio y «caro/barato».** La que da confianza. Mínimo/máximo/media **con periodo y número de observaciones**; percentil en texto; la ventana real es de 59 días, así que nunca se dirá «90 días».
3. **Alternativas más baratas del mismo grupo.** Dato fuerte (8.066 grupos, ahorro mediano 13,45 %) y se ofrece dentro de la ficha, no como ranking global.
4. **Avisos de bajada in-app.** El backend existe entero; se limita a la lista de la persona y a las bajadas «de verdad» (86 grupos hoy en todo el catálogo: la pantalla no puede prometer una cascada).
5. **Etiquetado, en versión limitada.** Nutri-Score, sellos y certificados con filtros; **aditivos fuera** hasta que exista ingesta (no hay columna; solo se pueden contar E-xxx en texto en el 31 % de las listas).

**Limitadas por dato (se enseñan donde lo hay, sin estimar):** calorías (23,08 % de grupos; 0 en alcampo/aldi/lidl) y despensa (la despensa y la lista desde plan/compra/favoritos ya existen; la lista desde recetas, no).

**No entran en el primer corte:** recetas con coste real (0/242 recetas costeables: falta recetario de verdad y mapeo ingrediente→producto), despensa con caducidades/inventario automático, «Yuka» de aditivos, predicción de precios o «precio ideal», push promocional, comparación con cadenas que no se capturan.

---

## 6. Fuentes y método

**Método.** `web_search` y `web_fetch` el 2026-11-04, con lectura directa de fichas de tienda y páginas de ayuda oficiales. Resumen con palabras propias; sin copiar texto ni capturas de las apps.

**Limitaciones y qué se ha hecho.**
- **Idealo: inaccesible.** `https://www.idealo.es/`, `https://www.idealo.es/ofertas/que-es-idealo` e `https://www.idealo.co.uk/compare/6621217/arctic-mx-4-45g.html` devuelven HTTP 403 anti-bot. Solo se ha leído su ficha de App Store, que **no menciona el precio por unidad**; por eso §2.2 no le atribuye ningún comportamiento sobre kg/litro.
- **Soysuper: web no legible.** `soysuper.com` y `/como-funciona` devuelven una aplicación JS («Cargando…»); se usan ficha y `sitemap.xml`.
- **Lidl España: contenido tras el menú.** `lidl.es/c/lidl-plus/s10089100` y `/puntos-lidl-plus/s10096382` cortan; se usan ficha ES y FAQ de Lidl (versión EE. UU., indicada como tal).
- **Google Play: fichas vacías**; se sustituyen por la App Store.
- **OCU: muro de pago** en su comparador por perfil familiar.
- **PDF de accesibilidad de la ONCE**: la herramienta no lee `application/pdf`; no se han usado.

**Fuentes citadas (todas el 2026-11-04):**

- Soysuper, ficha: https://apps.apple.com/es/app/soysuper/id985951382
- Soysuper, sitemap: https://soysuper.com/sitemap.xml
- Idealo, ficha: https://apps.apple.com/es/app/idealo-app-de-compras-online/id454415640
- CamelCamelCamel, funciones: https://camelcamelcamel.com/features
- CamelCamelCamel, ficha de producto: https://de.camelcamelcamel.com/THQ-21217-Oben/product/B0027BOXK8
- Lidl Plus, ficha: https://apps.apple.com/es/app/lidl-plus/id1238611143
- Lidl Plus, FAQ: https://www.lidl.com/c/lidl-plus-faqs/s10097623
- Mercadona, ficha: https://apps.apple.com/es/app/mercadona/id1368037685
- Mercadona, ayuda móvil: https://ayuda.tienda.mercadona.es/hc/en-us/articles/360000841132-Purchasing-from-your-mobile-device
- Yuka, método: https://help.yuka.io/l/es/article/ijzgfvi1jq
- Yuka, funciones: https://yuka.io/es/aplicacion/
- MyRealFood, ficha: https://apps.apple.com/es/app/myrealfood-recetas-y-plan/id1458031749
- BOE, RD 3423/2000: https://www.boe.es/diario_boe/txt.php?id=BOE-A-2000-24118
- OCU, comparador (muro de pago): https://www.ocu.org/consumo-familia/supermercados/calculadora/comparar-precios-supermercados
