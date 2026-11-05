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

---

# Parte II — Ampliación del 2026-11-05 (`ALCANCE-APP.md` §5, puntos 3–7)

**Fecha de consulta de todas las fuentes de esta parte: 2026-11-05.** Autor: `investigador-app2`. Método: `web_search`/`web_fetch` reales; se distingue **leído** de **no accesible** y no se rellena ningún hueco con memoria. Nada de esta parte pide credenciales de supermercados ni documenta cómo saltarse un login.

## 7. Cuentas de las apps de los supermercados

### 7.1 Qué se ha leído (y qué no)

| Cadena | Leído el 2026-11-05 | ¿Legible? | Qué permite de verdad |
|---|---|---|---|
| Carrefour | [El Club Carrefour](https://www.carrefour.es/clubcarrefour/) · [App Mi Carrefour](https://www.carrefour.es/clubcarrefour/app-mi-carrefour/) | Sí | Mis listas, cupones personalizados, ChequeAhorro, ticket digital, lector de precios, pago QR. Su política de privacidad **no se ha leído** (solo localicé PDFs de otras sociedades; no se usan). |
| Lidl | [Nota de prensa «Puntos Lidl» (01.07.2026)](https://empresa.lidl.es/sala-de-prensa/actualidad-lidl/lidl-lanza-puntos-lidl-una-nueva-funcionalidad-de-su-app-dirigida-al-ahorro-de-sus-clientes-a-traves-de-recompensas-personalizables) | Sí | Ticket digital, Lidl Pay, lista, recetas, cupones, Puntos Lidl. **Privacidad de Lidl Plus: HTTP 404**, no accesible. |
| Mercadona | [Política de privacidad (rev. 20.07.2026)](https://tienda.mercadona.es/legal/privacy/en/) · [Ficha de app](https://apps.apple.com/es/app/mercadona/id1368037685) | Sí | Compras anteriores, «productos habituales sin necesidad de listas», nutrición vía imagen con zoom. Login con Google/Apple. |
| DIA | [Ficha de app](https://apps.apple.com/es/app/dia-supermercado-online-y-club/id660175630) · [web](https://www.dia.es/) | Sí | Tickets físicos y online, cupones Club activados en caja, tarjeta digital, repetir compra, escáner de alérgenos. **`/politica-de-privacidad` devuelve la portada**: no accesible. |
| Alcampo | [Política de privacidad Club Alcampo (rev. feb. 2025)](https://www.compraonline.alcampo.es/content/politica-privacidad-club-alcampo) · [App](https://www.compraonline.alcampo.es/content/app-alcampo) | Sí | Favoritos, Compra rápida, Productos recurrentes, Mis listas, editar pedidos, cupones. |
| Aldi | [Ficha de app](https://apps.apple.com/es/app/aldi-supermercados/id669956906) | Sí | Folleto, varias listas, alertas de favoritos, recordatorios de ofertas, ingredientes y sellos. Sin programa de fidelización en app/web. |

**API pública: no existe para consumidor en ninguna de las seis.** Lo único documentado que aparece es la API de *marketplace* de Carrefour (Mirakl), que un integrador documenta para **vendedores** ([Channable](https://helpcenter.channable.com/list-advertise/list-and-advertise-es/vende-en-marketplaces/marketplaces-mirakl/como-a-configurar-un-canal-de-carrefour-spain), leído): sirve para publicar catálogo, no para leer tickets ni cuentas. Hay paquetes no oficiales de terceros que dicen leer catálogos de súper (p. ej. uno en PyPI para Mercadona), pero PyPI bloqueó la lectura y, aunque existieran, no son API pública ni traen condiciones que permitan reutilizarlas. **La app no puede prometer «conecta tu cuenta».**

**Exportación RGPD.** La [AEPD](https://www.aepd.es/preguntas-frecuentes/1-tus-derechos/2-tus-derechos-de-proteccion-de-datos/FAQ-0113-que-es-el-derecho-a-la-portabilidad-de-los-datos) (leído) define la portabilidad como recibir los datos en formato estructurado, de uso común y lectura mecánica, y transmitirlos a otro responsable cuando sea técnicamente posible; aplica cuando el tratamiento se basa en consentimiento o contrato y es automatizado. En las políticas que sí se han leído: **Alcampo** la reconoce y se ejerce por correo al DPO (`dpoare@alcampo.es`) o por escrito con DNI; **Mercadona** reconoce «request the transfer of your information» por correo postal o formulario con certificado digital (DPO `dpo@mercadona.es`). Ninguna documenta exportación autoservicio. Conclusión: la vía legítima realista es **que la persona pida su exportación y nos la entregue**, o que pegue su ticket/lista a mano.

El login con Google/Apple de Mercadona es el login de la persona **en Mercadona**, no una puerta para nosotros: no se toca.

### 7.2 Qué copiamos con criterio
Importación manual como camino principal («trae tu historial»: pegar texto o subir el CSV/JSON de la exportación RGPD). «Repetir compra» y «compras anteriores» como fuente de lo comprado cuando la persona lo aporte. En la interfaz, cero lenguaje de conectar cuentas.

### 7.3 Qué no copiamos
Guardar credenciales, tokens o sesiones. Automatizar el login (navegador con su sesión, cookies, scraping autenticado), ni «con su permiso». Pedir DNI o certificado y tramitar la solicitud RGPD en su nombre: somos un tercero, no su representante. Prometer sincronización en tiempo real.

### 7.4 Qué dato necesita
Nada nuevo del backend para el primer corte. Para que la importación sea útil: un formato de entrada (nombre, cantidad, precio, fecha, cadena), mapeo de texto libre a `grupo_id` (el problema del emparejador) y marca de origen («importado por ti el …») que no se mezcle con la captura diaria.

## 8. Ofertas con detalle y dónde conviene comprar

### 8.1 Qué se ha leído
- **Regla legal del precio anterior** — [Consumo Responde](https://www.consumoresponde.es/actualidad/noticias/rebajas-deben-realizarse-sobre-menor-precio-producto-establecimiento-30-dias) (leído): la rebaja se anuncia sobre el **menor precio de los 30 días anteriores**; cita la Directiva (UE) 2019/2161 y una sentencia del TJUE sobre falsas rebajas. Es la norma que hace honesto o deshonesto cualquier «-30 %».
- **Club Carrefour** (leído): 1 % de la compra de alimentación acumulado, 15 % en «Mi Día de El Club», IVA de frescos y BIO con tarjetas +65/Superfamilias/Joven, **ChequeAhorro cada dos meses**, 20+ *partners*. Es ahorro **diferido**, no precio de estantería.
- **Lidl Puntos** (leído): 1 punto por euro en tienda, canje por 400+ recompensas, validez 24 meses, 25 puntos de bienvenida, sumado a cupones y ofertas semanales.
- **DIA** (ficha, leída): cupones personalizados que se activan en caja y tarjeta digital del Club. **Aldi**: sin fidelización; ofertas de folleto con fecha. **Mercadona**: sin club; sus bajadas son precio directo ([titular de prensa](https://www.economiadigital.es/sociedad/mercadona-descarta-tarjeta-fidelizacion-si-ofrecen-consum-lidl.html) leído; cuerpo no).
- **Comparadores**: Idealo devolvió **HTTP 403** hoy otra vez (`idealo.es/ofertas/que-es-idealo` y `idealo.co.uk/magazine/faqs`); Soysuper sigue en «Cargando…» (aplicación JS); OCU, muro de pago (ya documentado en la parte I). **No se ha podido leer cómo tratan las ofertas condicionadas**: no se les atribuye nada.

Lo que ya tenemos: `core/promos.py` reconoce cinco mecánicas (precio fijo, porcentaje, umbral, enésima, nxm) y marca los descuentos de tarjeta como `acumulable` **sin restarlos** (`docs/OFERTAS-Y-ML.md`). Esa decisión es la correcta; esta sección la respalda con fuentes.

### 8.2 Taxonomía y qué exige cada tipo para recomendar sin mentir

| Tipo | Ejemplo real | Qué dato exige | Error típico |
|---|---|---|---|
| Descuento % | «-30 % Días Locos» | Precio base + mínimo de 30 días + fecha fin | Calcular el % sobre un precio inflado |
| Precio fijo | «Todo a 1 €» | Que el producto entre en el saco; comparar €/kg después | Venderlo como rebaja del producto |
| Enésima (2ª unidad -50 %) | Club Alcampo / Carrefour | Cuántas unidades pide la lista | Restarlo al precio de **una** unidad |
| NxM (3x2, 2x1) | «3x2» | Unidades y que la persona pueda usar la extra | Aplicarlo con 1 unidad |
| Precio club inmediato | Cupón en caja | Pertenencia + activación | Enseñarlo como precio de todos |
| Precio club diferido | ChequeAhorro, Puntos, «acum en tu tarjeta» | Modelarlo como monedero aparte | Restarlo del total |
| Umbral | «5 € dto. comprando 20 €» | Cesta mínima de la marca | Darlo por hecho sin llegar al umbral |
| Pack | Pack 6 | Cantidad total y €/kg del pack | No comparar con 6 sueltos |

**Regla de oro:** si falta el dato de la condición, la oferta no se recomienda; se enseña el precio base y «hay promoción, sin detalle». Mejor no recomendar que recomendar mal.

### 8.3 Qué copiamos
La mecánica traducida y la fecha de fin (no una etiqueta roja). Tres cifras separadas: precio de hoy, ahorro inmediato aplicable a **mi cantidad**, y ahorro acumulable con su condición. Chip «solo socios» cuando exige club. El reparto entre tiendas con la mecánica aplicada y el número de paradas.

### 8.4 Qué no copiamos
Restar ChequeAhorro o Puntos del total. Etiquetar como oferta una subida previa (para eso está `oferta_sospechosa`, a partir de 45 días). Ordenar por «% de descuento» sin €/kg.

### 8.5 Qué dato necesita
`tipo_mecanica` normalizado (ya), más `exige_club` (booleano), `es_diferido` (booleano), `condicion` (unidades o importe mínimo), `fecha_fin` y **el nombre del club** (Carrefour, DIA, Alcampo, Lidl) para no meterlos en el mismo saco. Hoy vive en texto libre: hay que estructurarlo antes de que la app lo pinte.

## 9. Aprender de las listas

### 9.1 Qué se ha leído
- **Instacart**, centro de ayuda (leído): dos objetos, «Shopping list» (personal, semanal) y «Saved lists» (reutilizables, privadas o públicas; las privadas no son buscables y admiten una sola tienda). Alta por **foto** (lista manuscrita, receta impresa, captura), **pegando texto** (hasta 200 ítems) o buscando; cuenta familiar con iniciales de quién añadió; «Suggested», «Buy it again», favoritos; «añadir todo al carrito».
- **Bring!** (leído): listas compartidas con cambios en tiempo real, orden por pasillos, etiquetas de urgencia, **guardar recetas de internet** y pasar ingredientes a la lista, tarjetas de fidelización y folletos con ofertas a la lista.
- **Mercadona** (leído): revisar compras anteriores y comprar «productos habituales sin necesidad de listas».
- **DIA** (leído): repetir un pedido con un clic y **repetir online una compra hecha en tienda**; sección «Pedidos y listas».
- **Alcampo** (leído): «Productos recurrentes», «Compra rápida», Favoritos, Mis listas. **Carrefour**: Mis listas, Mis compras. **Aldi**: varias listas y alertas de favoritos.
- **Amazon Fresh** (`Repeat Items`): **muro de login**, no leído.

### 9.2 Qué copiamos
Separar **favorito** (producto), **lista** (intención) y **compra** (hecho): mezclarlos es el error de casi todas. «Rellenar sola» como **sugerencia revisable** en la lista de casa (los N que más se repiten en compras e importaciones, con «añadir todos» y «quitar»), nunca añadiendo a escondidas. Aprender cantidades solo cuando son estables; si varían mucho, no sugerir cantidad. «Sugerir otra tienda» con la lógica de `docs/LISTAS.md` §6bis (total, desglose y coste de la segunda parada). Quién añadió qué, ya en el modelo.

### 9.3 Qué no copiamos
Listas públicas y descubribles (exponen hábitos y no aportan). Convertir la sugerencia en suscripción o reposición automática. Marketing dentro de la lista. Y el «rellenar sola» fingido: sin historial importado no hay aprendizaje, y se dice.

### 9.4 Privacidad y consentimiento
Base de contrato/consentimiento y minimización: solo lo necesario para rellenar y comparar, sin perfil comercial ni cesión. **Opt-in explícito** para «aprender de mis compras», apagable, con borrado real del historial importado. Explicación corta y visible: «para rellenar tu lista usamos tus últimas compras; puedes borrarlas». Nada de datos de terceros.

### 9.5 Qué dato necesita
Historial de líneas con fecha, `grupo_id`, cantidad y cadena; marca «importado vs capturado»; y las tablas de lista que ya existen. **Nota de coherencia:** `docs/LISTAS.md` §7 descartaba «plantillas y listas recurrentes». La ampliación las pide como **sugerencia**, no como plantilla: se implementa «rellenar sola» sobre la lista de casa sin crear un sistema de plantillas.

## 10. Calculadora de calorías diarias con pautas de salud

### 10.1 Qué se ha leído
- **WHO, «Healthy diet»** ([26.01.2026](https://www.who.int/news-room/fact-sheets/detail/healthy-diet), leído): principios de adecuación, **equilibrio entre ingesta y gasto**, moderación y diversidad; rangos de referencia (45–75 % hidratos, 15–30 % grasas, 10–15 % proteína) y el ejemplo de que con 2000 kcal los azúcares libres bajo el 10 % son unos 50 g.
- **EFSA** ([nota de prensa 10.01.2013](https://www.efsa.europa.eu/es/press/news/130110), leída; [opinión científica](https://efsa.onlinelibrary.wiley.com/doi/10.2903/j.efsa.2013.3005) enlazada, no leída): ingestas medias de referencia con estilo moderadamente activo (PAL 1,60) y BMI asumido 22, ajustables si el BMI es distinto. Mujeres/hombres 30–39: 2.000–2.600 kcal; 50–59: 2.000–2.500; 70–79: 1.800–2.300. Embarazo: +70/+260/+500 kcal por trimestre; lactancia: +500 kcal.
- **FAO/WHO/UNU**, [Informe 2004](https://www.fao.org/4/y5686e/y5686e00.htm) (leído el índice y la estructura): requisitos de energía, ecuaciones de gasto basal (Anexo 3) y niveles de actividad.
- **AESAN**, [«Recomendaciones dietéticas saludables y sostenibles…» (2022, NIPO 069220082)](https://cpage.mpr.gob.es/publicacion/recomendaciones-dieteticas-saludables-y-sostenibles-complementadas-con-recomendaciones-de-actividad-fisica-para-la-poblacion-espanola-2022-069220082-0001/) (ficha leída). **El PDF no se ha leído.**
- **Mifflin-St Jeor (1990)** — [resumen indexado](https://europepmc.org/article/MED/2305711) (leído): REE = 10·peso(kg) + 6,25·altura(cm) − 5·edad + 5 (hombres) / −161 (mujeres); el mismo trabajo señala que Harris-Benedict (1919) sobreestimaba el gasto ~5 %. **Harris-Benedict no se ha leído en su fuente original**, solo a través de este resumen.

### 10.2 Qué copiamos
Dos capas separadas: **lo que registras** (kcal de lo comprado y de las recetas, con «N de M productos con dato») y **la referencia** (tabla EFSA por edad, sexo y actividad; Mifflin como estimación individual declarada). Rango, no número: la estimación tiene error y se dice. Sin prescribir: ni objetivo automático, ni déficit, ni «deberías». La fuente y la fecha en el «por qué», en llano y sin fórmulas en pantalla.

### 10.3 Qué no copiamos
Fijar un objetivo calórico al abrir la app o al registrar el peso. Diagnósticos, IMC como juicio, «quema esto», planes de adelgazamiento. Rellenar kcal que no tenemos (23,08 % de grupos; **0 en Alcampo, Aldi y Lidl**): el hueco se dice. Presentar Mifflin como «tu gasto real».

### 10.4 El límite, por escrito
La app no es un dispositivo médico ni sustituye a un profesional. No hay recomendación individualizada de salud; si el registro sugiere algo clínico, se remite a un profesional. Texto breve en pantalla, sin letra pequeña.

### 10.5 Qué dato necesita
Tabla nutricional estructurada (kcal/100 g y por ración) —medida: 23,08 %, 0 en Alcampo/Aldi/Lidl—, ración por producto y un registro **opcional y local** del usuario (peso, altura, edad, actividad) para Mifflin. Sin nutrición estructurada, la calculadora solo puede enseñar la referencia, no el registro.

## 11. Recetas establecidas y creadas por el usuario

### 11.1 Qué se ha leído
- **Cookpad**, [condiciones](https://cookpad.com/es/terminos) (leído): el contenido es de quien lo publica, pero al subirlo concede licencia mundial, gratuita, transferible a terceros y sin compensación; Cookpad no revisa las recetas ni responde de su seguridad; hay cláusulas específicas para España. **No se copian recetas de Cookpad.**
- **MyRealFood** ([web](https://www.myrealfood.app/es), leída): recetas con tiempo y **kcal por receta**, ordenadas por popularidad, con plan de pago. El recetario es suyo.
- **Alcampo**, [«La cocina de Alcampo»](https://www.compraonline.alcampo.es/recipes) (leída): recetario **editorial de marca** (Chicote, verdura, carne, pescado, postres, Rik&Rok) integrado en la tienda; no es contenido de usuarios. **DIA** tiene sección de recetas propia.
- **Bring!** (leído): «guardar recetas de internet» y pasar ingredientes a la lista. **Instacart** (leído): añadir a la lista fotografiando una receta impresa o una captura.
- **Recetas Gratis: no se ha podido leer** sus condiciones; no se le atribuye nada.

### 11.2 Qué copiamos
**Recetas propias primero**: recetario editorial de Cesta con licencia nuestra más recetas del usuario (suyas, con permiso de uso dentro de la app). Importación **manual** desde texto pegado (un ingrediente por línea) y, más adelante, desde URL **con revisión**: se guarda enlace, ingredientes normalizados y cantidades que confirme la persona, no el texto de la receta. Porciones que escalan cantidades y coste. Alérgenos como campo de la receta propia y como **aviso**, no como garantía: la obligación de declarar los 14 alérgenos es del etiquetado del producto (Reglamento UE 1169/2011); la ficha de AESAN sobre sustancias alergénicas **no se ha podido leer completa** en esta sesión y se cita como pendiente.

### 11.3 Qué no copiamos
Copiar recetarios de terceros (Cookpad, MyRealFood, webs de recetas): licencia y riesgo. Scrapear recetas ajenas y republicarlas. Prometer «sin alérgenos»: solo «según los ingredientes que has puesto».

### 11.4 Qué dato necesita
Recetario propio o con licencia; ingredientes mapeados a `grupo_id` (hoy 4/473 y ninguno válido); cantidades y unidades; nº de raciones; kcal por ración cuando exista; campo de alérgenos en recetas propias. Sin recetario licenciado, **solo recetas propias y del usuario** en el primer corte.

## 12. Favoritos, lista y continuidad de producto

### 12.1 Lo que tratan bien y copiamos
**Sin sesión:** Bring! exige cuenta para compartir e Instacart la pide al final, pero la lista se puede empezar; copiamos lista utilizable sin cuenta y sincronización opcional al entrar. **Vacío:** sugerir «compra otra vez» o favoritos en vez de una pantalla en blanco (Instacart «Suggested», Alcampo «Productos recurrentes», DIA «repetir»). **Offline:** `docs/LISTAS.md` §4 ya lo resuelve mejor que las apps leídas (uuid en el móvil, hora del móvil, lista entera en caché, aviso «sin conexión con casa»). **Continuidad:** cuando el producto desaparece o cambia de nombre entre capturas, la línea conserva su `grupo_id`, muestra «no lo encuentro hoy» y ofrece alternativa del mismo grupo. DIA y Carrefour lo resuelven dentro de su catálogo; nosotros, **entre cadenas**.

### 12.2 Lo que tratan mal y no copiamos
Listas públicas y «descubre listas» (Instacart). Perder la lista al cerrar sesión o cambiar de dispositivo. Pedir cuenta antes de dejar usar la lista.

### 12.3 Qué dato necesita
Favoritos por `grupo_id` (no por `producto_id`, para sobrevivir al cambio de catálogo); el estado de línea (sin decidir/decidida/comprada) que ya define `LISTAS.md`; y una regla de «producto desaparecido» con fecha de última vez visto.

## 13. Decisiones propuestas para el 5/11

**Entra primero, en este orden:**
1. **Favoritos + lista de casa, con «rellenar sola» revisable.** Es lo que ya tiene modelo y offline resuelto; sin historial importado se queda en «compra otra vez» con lo que haya.
2. **Ofertas con tipo y club, en la lista y en el reparto.** Ya existe `promos.py`; falta estructurar `exige_club`, `es_diferido`, `condicion` y `fecha_fin` para que la pantalla no adivine.
3. **Calculadora con referencias y sin prescribir.** Referencia (EFSA/WHO/AESAN) + estimación declarada (Mifflin) + registro de lo comprado donde hay kcal. Sin objetivos.
4. **Recetas propias y del usuario**, con importación manual de texto; coste por ración solo cuando haya mapeo y precio.

**Se limita:**
- **Cuentas de supers: solo exportación RGPD que pide la persona e importación manual.** Sin credenciales, sin login automatizado, sin pedir DNI. La app nunca dice «conecta tu cuenta».
- **Ofertas de club: se enseñan, no se restan.** ChequeAhorro, Puntos Lidl y cupones personalizados van a un apartado «acumulas» con su condición.
- **Calorías:** se enseña el dato donde existe (23,08 % de grupos; 0 en Alcampo/Aldi/Lidl) y se dice el hueco; nunca se estima.
- **Recetas de terceros:** no se copian; si se importan, se guardan enlace e ingredientes, no el texto.

**Se descarta:**
- API de supermercados (no hay pública de consumidor; la documentada es de *marketplace* para vendedores).
- Scraping con sesión, cookies o credenciales; cualquier automatización de cuentas de terceros.
- Listas públicas, compartidas con desconocidos y «descubrir listas».
- OCR de tickets en el primer corte: primero pegar texto o CSV.
- Objetivos de salud, déficit calórico, IMC como juicio y planes de adelgazamiento.
- Predicción de precios y recomendador de productos (ya descartado en la parte I; sigue vigente).

## 14. Fuentes de la ampliación (todas consultadas el 2026-11-05)

Todas las fuentes **leídas** están enlazadas en su sección (§7–§12); aquí solo se consolidan las no accesibles.

**No accesibles (se dice, no se rellena):** Idealo (`idealo.es/ofertas/que-es-idealo`, `idealo.co.uk/magazine/faqs` → HTTP 403) · Soysuper (`soysuper.com` → «Cargando…», JS) · OCU (muro de pago, ya en la parte I) · Lidl Plus, privacidad (`lidl.es/es/asset/…Lidl-Plus-1.pdf` → HTTP 404) · DIA, privacidad (`dia.es/politica-de-privacidad` → portada) · Carrefour, privacidad (no leída) · Amazon Fresh «Repeat Items» (muro de login) · opinión EFSA 2013 en Wiley (referenciada, no leída) · PDF de AESAN 2022 (no leído) · Reglamento UE 1169/2011 (ficha europea con error 404; obligación citada, texto no leído) · Recetas Gratis (condiciones no leídas) · paquete PyPI de Mercadona (bloqueado).
