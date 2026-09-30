# Cesta — la competencia, funcionalidad a funcionalidad, listo para implementar

`docs/COMPETENCIA.md` dice **qué hacen** las otras apps y qué nos llevamos.
`docs/FUNCIONALIDADES.md` da el **veredicto** de cada idea. Este documento es el
paso que faltaba: **el detalle y el "cómo", para poder implementarlo sin volver a
investigar**.

No repite lo que ya está. Cuando una idea ya está contada en su sitio, la cita en
una línea y sigue.

    docs/COMPETENCIA.md             611 lineas   que hacen las otras apps
    docs/FUNCIONALIDADES.md         270 lineas   el veredicto, A hacerlo ya ... G descartado
    docs/CADENAS.md                 272 lineas   que publica de verdad cada cadena
    docs/BACKLOG.md               4.155 lineas   el trabajo pendiente, por tareas
    docs/COMPETENCIA-IMPLANTABLE.md  este        detalle por funcionalidad y a implementar

**Actualización del 30 de septiembre de 2026 — de qué dependía cada fila.** Este documento se
escribió el 24, y la columna que decide dice en varias filas «si, **con la tarea 10**» o
«necesita la **tarea 10** cerrada antes». **La tarea 10 está hecha** (cerrar la compra, el 30 de
septiembre), así que esas filas **ya no están bloqueadas por ella**: lo que queda es el trabajo
propio de cada una.

Y el estado del resto de tareas que este documento cita, para no volver a leerlo entero:

    tarea 1   agrupar la lista por pasillos            HECHO (27 sep)
    tarea 3   la voz del buscador                      HECHO (30 sep)
    tarea 5   notas de la linea y el aviso legal        HECHO (30 sep)
    tarea 8   el escaner, tambien desde el buscador     HECHO (30 sep)
    tarea 10  cerrar la compra                          HECHO (30 sep), con dos desvios:
              `GET /listas/{id}/compras` en vez de `/api/compras`, y sin `cadena_elegida`
              (la cadena que se guarda es la del precio) -- detalle en `docs/API.md`
    tarea 9   la nota 0-100                             PENDIENTE, y pendiente de una
              decision, no de codigo: `docs/API.md` tiene la forma y **los numeros medidos**
              (el 74,2 % de los productos no tiene ningun dato con el que calcularla)

Los numeros de lineas de arriba estaban viejos (`FUNCIONALIDADES.md` decia 255 y son 270;
`BACKLOG.md` decia 1.540 y son 4.155) y se han contado otra vez hoy. Un recuento sin fecha es
una promesa que el documento no puede cumplir.

---

## 0. Como se ha hecho, y que garantiza cada numero

**Lo propio está medido, no citado.** Todo dato sobre nuestro sistema sale de una
consulta sobre `data/gold` con fecha de datos **2026-09-22**, o de un fichero del
repositorio con su línea. Cuando algo no se ha podido comprobar, lo dice: escribe
**"no comprobado"** en vez de afirmarlo.

**Lo de fuera está citado con su URL y su fecha.** Las apps cambian: `COMPETENCIA.md`
es del 17 y 18 de septiembre y varias fichas ya no dicen lo mismo. Las
correcciones van marcadas como tales.

**La columna que decide es "Se puede hacer aquí?", y la decide el dato.** Si
depende de un campo que las cadenas no publican, va el motivo y la línea de
`docs/CADENAS.md`. Si depende de algo que ya está en gold, va el número medido.

Leyenda del coste, la misma de `docs/FUNCIONALIDADES.md:10-16`:

    XS   menos de media jornada
    S    una jornada
    M    dos o tres jornadas
    L    una semana
    XL   mas de una semana

Comprobación antes de tocar nada (`COMANDOS.md`):

    uv run pytest -q                   662 pasan, 0 fallan, 1 saltada
    uv run ruff check .

### Las consultas, para poder repetirlas

**Las nueve cifras que el proyecto ya comprueba cada día** salen de
`projects/cesta/verificar_docs.py:51-75` (`COMPROBACIONES`), y ese control **pasa
hoy**:

    uv run python -m projects.cesta.verificar_docs

    productos del catalogo               52.567   SELECT count(*) FROM g
    grupos comparables                    7.992   count(*) de los grupo_id con count(DISTINCT fuente) >= 2
    productos con codigo de barras       25.517   SELECT count(ean) FROM g
    productos con Nutri-Score             8.450   SELECT count(nutriscore) FROM g
    productos comparables por kg/l/m     42.353   SELECT count(*) FROM g WHERE comparacion_fiable
    productos con algun sello            11.823   SELECT count(sellos) FROM g
    productos con certificado               730   SELECT count(certificados) FROM g
    productos con tabla nutricional       3.841   SELECT count(nutricion) FROM g
    productos con envase                  9.120   SELECT count(envase) FROM g

**Dos parejas se confunden solas, y por eso van las dos escritas.** `g` es
`read_parquet('data/gold/grupos.parquet')`:

    codigos de barras distintos          23.759   SELECT count(DISTINCT ean) FROM g WHERE ean <> ''

    -> 23.759 es cuantas veces aparece un codigo distinto: es la cifra del
       escaner, porque dos productos de dos cadenas comparten el mismo codigo de
       fabricante. 25.517 es cuantos productos lo traen, y es la que usa
       `verificar_docs`.

    con Nutri-Score o ingredientes       11.944   SELECT count(*) FROM g
                                                  WHERE nutriscore IS NOT NULL
                                                     OR (ingredientes IS NOT NULL
                                                         AND ingredientes <> '')

    -> son **tres columnas distintas** y ninguna sustituye a otra.
       `nutricion` (3.841) es la tabla de la etiqueta y **solo la publica DIA**;
       `nutriscore` (8.450) viene de Open Food Facts; `ingredientes` (7.052) es
       texto de etiqueta. La nota de la ficha 9 se apoya en `nutriscore` e
       `ingredientes`, **no en `nutricion`**.

**El resto de cifras propias**, que no están en `COMPROBACIONES`, con su consulta:

    seccion                              52.446   count(*) WHERE seccion IS NOT NULL AND seccion <> ''
    imagen                               52.567   count(*) WHERE imagen IS NOT NULL AND imagen <> ''
    ingredientes                          7.052   count(*) WHERE ingredientes IS NOT NULL AND ingredientes <> ''
    alergenos                             3.885   count(*) WHERE alergenos IS NOT NULL AND alergenos <> ''
    conservacion                          7.964   count(*) WHERE conservacion IS NOT NULL
    origen                                1.749   count(*) WHERE origen IS NOT NULL
    dias_caducidad                        4.382   count(*) WHERE dias_caducidad IS NOT NULL   (todos de DIA)
    promo                                 7.207   count(*) WHERE promo
    promo_club                            1.899   count(*) WHERE promo_club
    promo_solo_online                       398   count(*) WHERE promo_solo_online
    es_recall                                 0   count(*) WHERE es_recall
    EAN que llegan a 2 o mas cadenas     11.613   count(DISTINCT ean) de los grupos con >= 2 cadenas

**Y en `precio_derivado.parquet`, cuidado con cinco columnas que son
booleanas**: una booleana **nunca es NULL**, así que `WHERE promo_empieza IS NOT
NULL` casa con las **763.042** filas y un `count(DISTINCT producto_id)` sobre eso
devuelve los **72.802** productos del catálogo, que no dice **nada** de
promociones. Lo que se cuenta es **el valor verdadero**, y lo que sale son
**filas (un par producto × día)**, no productos:

    filas de precio_derivado            763.042   17 fechas, del 2026-09-06 al 2026-09-22
    ha_bajado                       8.752 filas   (8.124 productos)
    promo_empieza                   4.854 filas   (4.808 productos)
    promo_acaba                     1.571 filas   (1.569 productos)
    promo_inferida                 23.335 filas   (4.808 productos)
    descuento_real                 407.678 filas
    oferta_sospechosa                   0 filas   dormida: compara con shift(45)

    (para el dato de un solo dia, anadir
     AND fecha = (SELECT max(fecha) FROM precio_derivado)  ->  promo_empieza 92, promo_acaba 56)

---

## 1. La tabla completa de funcionalidades

Una fila por funcionalidad de la competencia. **"La tenemos?"** vale `si`,
`a medias` o `no`, con el número del BACKLOG cuando lo hay.

### 1.1 Listas de la compra

| Funcionalidad | De quién es (app) | Cómo lo hace ella | La tenemos? | Se puede hacer aquí? | Coste |
|---|---|---|---|---|---|
| Lista compartida en vivo entre dos móviles | QueFalta, Bring!, AnyList, Cozi, FamilyWall | varios miembros; al tachar uno, al otro se le tacha | **si** (`API.md:206` `personas` y `novedades`) | si: `lista_acceso` y `POST /listas/{id}/sincronizar` ya existen (`plataforma/sql/001_esquema.sql:71`, `API.md:242`) | — |
| Papel por persona: dueño / escribe / mira | QueFalta | "miembros con avatar y papel" | **si** (`API.md:203`) | si: `lista_acceso.papel` con `CHECK` (`plataforma/sql/001_esquema.sql:74`) | — |
| Invitación por enlace que caduca | QueFalta, Bring! | enlace o `@usuario` | **si** (`API.md:267-274`) | si: `invitacion` con usos y caducidad (`plataforma/sql/002_invitaciones.sql:9-18`) | — |
| Amigos por `@usuario` | QueFalta | buscador de personas | no | **no**: sois dos (`FUNCIONALIDADES.md:236`) | — |
| Varios carritos con uno activo | QueFalta | "varios carritos y uno activo que se elige" | no | **no**: descartado (`FUNCIONALIDADES.md:237`) | — |
| Orden por los pasillos del supermercado | QueFalta ("ordenada por las categorías del supermercado"), Bring! ("based on the aisles"), Listonic, AnyList ("reorganizar para que se adapten al diseño de tu tienda") | la lista se reordena sola al recorrer la tienda | **si**: `seccion` está en gold y **la lista se agrupa por pasillos desde el 27 de septiembre de 2026** (`porPasillo` en `Cesta.tsx`, con el encabezado pegado arriba) | hecho | — |
| Mosaico de lo habitual, a un toque | Bring! ("tiles"), Listonic ("suggestions from shopping history"), Soysuper ("Minisúper") | cuadrícula con lo que compras siempre, sin escribir | **si**: `Mosaico.tsx` y `GET /api/habituales`, con `origen` en cada tarjeta, desde el 23 de septiembre de 2026 | hecho | — |
| Añadir por voz | Listonic ("Voice input"), Soysuper ("Dicta tu lista"), EROSKI, OkLista | dictas y se rellena la lista | **en el buscador**: `componentes/Microfono.tsx` desde el 30 de septiembre de 2026 (rellena el campo, y **sin soporte del navegador no se dibuja**). Dictar y que se llene **la lista** no está | si, el resto es encadenar el micro con el alta de la línea | XS |
| Sugerencias del historial de compra | Listonic ("based on shopping history"), Soysuper | propone lo que compras cada cierto tiempo | no (**tarea 3.3**, `BACKLOG.md:563-566`) | si, pero **necesita 30 días de listas hechas** (`BACKLOG.md:573`) | S |
| Total estimado en vivo / presupuesto | QueFalta ("Total estimado en vivo"), Listonic ("Budget control"), AnyList (precios con total acumulado) | el total sube mientras añades | **si** (`API.md:211` `estimacion`) | si | — |
| Presupuesto con límites por categoría | FamilyWall (Premium) | topes de gasto por tipo de producto | no | si, con las secciones ya en gold y el cierre de compra | S |
| Notas por línea | Bring!, Listonic, AnyList ("marca, cantidad o una foto") | "la de cristal", "si hay del grande" | **si**: se apuntan, se leen y se quitan debajo de la línea desde el 30 de septiembre de 2026 (`UnaLinea` en `Cesta.tsx`) | hecho | — |
| Foto en la línea | Bring!, Listonic, AnyList | una foto del producto exacto | **a medias**: `imagen` está en **52.567 de 52.567** (medido) | si, es pintar `imagen` en la línea | XS |
| Etiquetas de urgencia | Bring!, OurGroceries ("a star might indicate... urgently needed") | marca de prioridad en el artículo | no | si: una columna y un color | XS |
| Categorías automáticas al escribir | Listonic | clasifica sola lo que tecleas | **a medias**: `seccion` ya está en gold y es heredable por grupo (`BACKLOG.md:479-480`) | si | S |
| Cantidad por línea | todas | "leche x6" | **si** (`cantidad` con `CHECK` en `plataforma/sql/001_esquema.sql:91`) | si | — |
| Tachar y subir lo hecho sin cobertura | QueFalta, Cozi ("saves your lists locally... sync automatically once you reconnect"), Go2Market | se tacha sin red y se sube al recuperarla | **a medias**: la API sí (`API.md:242`), la cola local del front nuevo no (`BACKLOG.md:120-124`) | si: `momento` con la hora del móvil ya está en el contrato | M |
| Lista ya hecha, curada y ordenada por supermercado | GoCoCo (*"listas de la compra elaboradas por expertos, con productos saludables verificados y organizadas por los supermercados más populares"*; en el plan de pago, para tus súpers favoritos) | no montas la lista: eliges una hecha | no | **no**, y a propósito: una lista elegida por otros no sabe qué tienes en casa ni qué te gusta. Lo que sí tenemos es el orden por pasillos de **sección** (`seccion` en 52.446 de 52.567 productos, medido) | — |
| Reusar una lista anterior | OurGroceries, AnyList | repetir la compra del mes pasado | no | si: `lista.archivada_en` ya existe (`plataforma/sql/001_esquema.sql:64`) | XS |
| Widget en la pantalla de inicio | Listonic, AnyList, Bring! | acceso desde el escritorio del móvil | no | **no por ahora**: pide app nativa (`FUNCIONALIDADES.md:224`) | XL |
| Compartir la lista fuera de la app (WhatsApp, imprimir) | OurGroceries (imprimir, exportar XLSX/JSON), Cozi (email), AnyList, Samsung Food | manda la lista a quien no tiene la app | no | si: es texto, y el enlace de invitación ya existe | XS |
| Integración con Alexa / Google / Siri | AnyList ("añade artículos con tu voz usando Alexa"), Bring!, OurGroceries, sinGLU10 | dictas al asistente de casa | no | **no**: exige nube y cuenta de terceros; choca con "los datos se quedan en casa" (`APP.md:56-76`) | XL |
| Recetas a lista | Bring!, AnyList, Samsung Food, Cozi, FamilyWall | se importa la receta y sus ingredientes van a la lista | no (**F1**, `FUNCIONALIDADES.md:198-204`) | si, pero el casado de ingredientes es el problema del emparejador otra vez | XL |
| Modo sin conexión de la lista | Cozi, Listonic, Go2Market | la lista se lee y se edita sin red | **a medias**: la lista se lleva entera (`APP.md:87-93`), escribir sin red no | si | M |
| Castellano y catalán | QueFalta (ES + CA) | dos idiomas | no | si: es texto | S |

### 1.2 Comparación de precios

| Funcionalidad | De quién es (app) | Cómo lo hace ella | La tenemos? | Se puede hacer aquí? | Coste |
|---|---|---|---|---|---|
| El mismo producto en varias cadenas, con precio por kg/l | Soysuper (9 cadenas, *"más de 150.000 productos... en más de 4.700 códigos postales"*), RadarSuper, Precios del Super, Findit (6–8), **CestIA (16 cadenas)**, **SuperPrecios (10)**, **Ahorramercado**, OkLista | una fila por producto y el precio en cada cadena | **si**: **7.992 grupos** con 2 o más cadenas, de 37.823 grupos (medido) | si | — |
| Comparar la cesta entera: todo en una tienda o repartida | Soysuper, Precios del Super ("Mi Carrito"), Findit ("Mi Cesta"), **CestIA** (el **reparto entre dos supermercados** va en su plan de pago, **3,99 €/mes**) | suma la lista en cada cadena y elige | **si** (`API.md:249` `donde`) | **si, y gratis**: lo que CestIA cobra a 3,99 €/mes lo tenemos en `merece_la_pena` y el reparto a dos tiendas (`API.md:249-265`) | — |
| Sugerir equivalentes cuando no hay coincidencia exacta | Soysuper, **SuperPrecios** (*"productos equivalentes en otros supermercados"*) | "sugerencias de productos equivalentes" | **si**: nivel `equivalente` en `gold/enlaces.parquet`, **22.705 pares** (medido) | si | — |
| Cesta tipo de N básicos para comparar cadenas | RadarSuper (**23 básicos**, mediana del €/kg, solo precios de los últimos 7 días, y una cadena solo puntúa con **3 productos reales suyos** con precio fresco); **el estudio anual de la OCU** usa **cuatro cestas**: la Cesta OCU (**241 productos**), la **cesta fresca**, la **cesta de marcas** (*"productos idénticos en todas las tiendas"*) y la **cesta económica** (89 productos), en **183 ciudades**, con un índice por establecimiento | ranking semanal de "qué supermercado es más barato" | **a medias**: `/api/panel/cadenas` da quién es más barato y la dispersión, sin cesta tipo declarada | si: tenemos 17 días de serie y `precio_unidad_cent` en **52.365** productos (medido) | S |
| Detección de reduflación (el envase encoge, el precio no) | RadarSuper (solo cuenta si el tamaño baja **≥ 2 %** y filtra cambios **> 40 %**; las bandejas de peso variable no valen) | cruza precio total con precio por unidad y lo registra como evento | no | **si, y es lo que ya calculamos a medias**: `cantidad` + `precio_unidad_cent` dan el envase, y `precio_ref_canon_cent` de la propia cadena confirma el cálculo | M |
| Comparar con el IPC alimentación del INE | RadarSuper (usa IPC general, IPC alimentación, salario medio bruto y SMI) | publica su inflación al lado de la oficial y dice cuándo divergen | no | **no**: descartado a propósito (`APP.md:404`, "es otro proyecto") | — |
| Inflación por categoría, con la mediana y no la media | RadarSuper (mediana de la variación del €/unidad a 12 meses) | una cifra por categoría | **a medias**: `/api/pulso` cuenta cuántos precios toca cada cadena, pero no hay inflación por sección | si: `seccion` en el 99,8 % del catálogo (medido) y `precio_diario` con 17 fechas | S |
| Histórico y curva de precios por producto | **Ahorramercado** (pestañas **30 días / 90 días / 1 año / todo**, y llega hasta **enero de 2023: más de 3 años**), **SuperPrecios** (histórico *"y en qué fechas estuvo de oferta"*), **CestIA** (histórico solo en el plan de pago), RadarSuper (declara *"hasta tres años de profundidad"* en PostgreSQL y **el histórico completo es función de pago**), Precios del Super, supermarket-tracker (**abandonado**), PrecioReal (pero **de tiendas online**, no de supermercado) | gráfica del precio en el tiempo | **si**: `precio_diario` con **763.042 filas y 17 fechas** (medido); la serie va dentro de `GET /api/grupo` (`API.md:146`) | si | — |
| Distinguir una **bajada estructural** de una **oferta puntual** | **Ahorramercado**, que las separa en dos secciones: *"🏷️ Ofertas — promoción puntual con precio anterior, puede acabar pronto"* frente a *"📉 Bajadas de precio — caída estructural, **no es una oferta puntual**"* | no te dice "ha bajado": te dice **por qué** ha bajado | no | **si, y los campos ya están**: `ha_bajado`, `precio_base_cent` (mediana móvil), `promo_empieza` y `promo_acaba` en `precio_derivado.parquet` (medidos). Es una consulta, no un cálculo nuevo | S |
| Saber **en qué fechas** un producto estuvo en oferta | **SuperPrecios** (*"histórico de precios y en qué fechas estuvo de oferta"*), **Ahorramercado** (estado **Normal \| Oferta** en la curva) | la curva marca los tramos de promoción | no | **si**: `promo_empieza` (**4.854**) y `promo_acaba` (**1.571**) ya están calculados en `precio_derivado.parquet` (medido) | S |
| Índice de precios propio y "IPC de tu cesta" | RadarSuper (**cesta básica nacional** de 12 productos, cada mes con *forward-fill* del último precio conocido; hoy **29,40 €** frente a **24,36 €** de feb 2024, **+20,7 %**), Precios del Super (`/ipc`) | una cifra de inflación propia, por categoría | **hecho el 24 sep 2026**: `GET /api/indice` y la pestaña **Índice** del panel, con la frase (quién ha bajado y quién ha subido) antes que el dibujo y la tabla con capturas y productos | si: hay `seccion` en el 99,8 % y `precio_diario` con 17 fechas | XS |
| Alerta de precio y herramientas **de pago** | RadarSuper (Plus **3,99 €/mes**: alertas ilimitadas, histórico completo, **simulador de sueldo y cesta**; Pro **9,99 €/mes**: + chat IA, análisis nutricional, API básica) — pero **el cobro no está operativo**: *"Stripe (próximamente)"*. CestIA Pro **3,99 €/mes** (histórico + reparto entre dos súpers). SuperPrecios Premium **0,99 €/mes**. OkLista **1,79 €/mes** | parte de la función detrás del pago | **a medias**: los avisos de precio están hechos y sin pantalla en el front nuevo (ver arriba) | **si, y gratis**: lo que ellos cobran entre 0,99 y 3,99 €/mes ya está en la API y en `alerta` (`plataforma/sql/001_esquema.sql:126-133`) | S |
| La curva dentro de la web de la cadena (extensión de navegador) | supermarket-tracker (**abandonada**: su extensión solo se inyecta en Mercadona, es la 0.1.0 del 4 feb 2023), **PrecioReal** (extensión de Chrome **y addon de Firefox**, sobre tiendas online) | dibuja el histórico encima de la web del supermercado | **si** (`extension/`), y la nuestra cubre **las cinco cadenas** | si | — |
| "Bajadas de esta semana" | Precios del Super (`/bajadas` y `/subidas`), Comparaloo ("Bajadas de precio"), RadarSuper ("qué ha bajado y subido esta semana") | compara con la captura anterior | **si**: `GET /api/bajadas` (`plataforma/api/main.py:205`) y pestana en el panel | si | — |
| Verificador de ofertas: ¿el descuento es real? | PrecioReal ("evita falsas rebajas"), Comparaloo ("detector de falsas rebajas": *"un −50 % sobre un precio inventado es el precio de siempre"*, con la curva diaria y un ejemplo de tres pasos: precio habitual 30 días / subido hace 3 días / "rebajado" hoy), RadarSuper ("qué ofertas del folleto son de verdad"), **Ahorramercado** (por la vía de separar oferta puntual de bajada estructural) | guarda el precio día a día y enseña la curva antes de comprar | **hecho el 24 sep 2026**: `GET /api/ofertas-dudosas` y la pestaña **Ofertas dudosas**, con la frase del servidor (`por_que`) antes que el precio y la regla de 90 días. Y con un filtro que ninguno de ellos tiene: **solo se acusa a las ofertas que son un descuento sobre el precio de esa unidad** (un 3x2 no baja el precio de una: eran 3.658 de 5.488), y lo que no se puede juzgar se cuenta y se dice | **si, hoy**: es una pantalla sobre un endpoint que ya responde | S |
| Alerta cuando un producto baja de precio | idealo ("**Precio Ideal**: activa una alarma de precios"), Comparaloo (aviso por correo **sin registro**, confirmado con un código de seis dígitos), PrecioReal ("alertas con precio objetivo"), **CestIA** ("alertas de bajada en favoritos"), **SuperPrecios** | te avisa al alcanzar el precio que buscas | **a medias**: tabla `alerta` con tres tipos (`plataforma/sql/001_esquema.sql:126-133`) y `/api/alertas` (`plataforma/api/main.py:549`); **el front nuevo no las usa** (`BACKLOG.md:128-132`) | **si, hoy**: la API funciona y el `app.js` viejo la usaba (`app.js:742, 1066`) | S |
| Enseñar **de cuándo es el dato** | **CestIA** (*"muestra la antigüedad del dato"*); Precios del Super publica la hora de cada cambio; RadarSuper se niega a puntuar una cadena sin **3 productos con precio de menos de 7 días** | el número va con su fecha o no se enseña | **si, y es una ley del proyecto**: cada precio lleva su fecha pegado al número y uno de más de tres días **no decide** en qué tienda comprar (`APP.md:147-163`) | si | — |
| Alerta de que un producto **de tu lista** está en oferta | Bring! ("Passende Angebote"), Tiendeo ("alertas sobre las promos de tus productos favoritos") | cruza tu lista con las ofertas del folleto | no | si: `core/promos.py` ya está hecho y probado (10 pruebas), y `promo` está en **7.207** productos (medido) | S |
| Cupones verificados contra el feed de la tienda | Comparaloo ("el mejor código de cada tienda, comprobado contra el feed de su programa y retirado en cuanto caduca"), Flipp (cupones cargados a la tarjeta de fidelidad) | lista de códigos vivos | no | **no**: hay que ser la cadena o tener su acuerdo de afiliación | — |
| Comparar marca blanca contra marca | Soysuper/OCU | | **si**: `GET /api/panel/marcas`, con un `aviso` obligatorio (`API.md:297-299`) | si | — |
| Filtrar por las cadenas que tengo cerca | Findit ("modo mapa"), OCU Market ("te decimos el supermercado más cercano a tu ubicación"), Tiendeo (geolocalización precisa) | solo enseña tiendas a tu alcance | **hecho el 24 sep 2026**: el panel tiene su filtro de cadenas y **arranca en las que tienes puestas** (`preferencia.cadenas_cerca`, `API.md:283`), diciendo de dónde sale el filtro; antes ninguna pestaña la leía y las cinco pesaban lo mismo | si: es un filtro que ya viaja en `GET /api/buscar` | XS |
| Mapa de tiendas y gasolineras | Findit ("modo mapa... gasolineras y supermercados"), Tiendeo | mapa con las tiendas alrededor | no | **no**: no tenemos ni una columna de tienda ni de dirección (medido: 53 columnas en `grupos.parquet`, ninguna de tienda) | — |
| Precio por unidad de medida coherente entre cadenas | Findit lo intenta y **le sale mal**: *"las unidades de medida, en algunos productos da el precio por quilo, en otros por unidad y es confuso"* (reseña del 7 ago 2025) | | **si, y es nuestra ventaja**: `unidad_canon`, `precio_unidad_cent` y `comparacion_fiable` (`docs/MODELO.md:42-45`); `comparacion_fiable` en **42.353** productos (medido) | si | — |
| "¿Merece la pena ir a dos tiendas?" | Soysuper | | **si**: `merece_la_pena` con umbral de 1,50 EUR (`API.md:264`) | si | — |
| Índice de precios: cuánto ha subido la cesta | RadarSuper ("cesta básica nacional" de 12 productos, con marca más vendida por cadena), Precios del Super ("IPC") | una cifra de evolución | **hecho el 24 sep 2026**: `GET /api/indice` y la pestaña **Índice** del panel | si | XS |
| Precios abiertos de contraste | Open Prices (Open Food Facts) | base colaborativa con API y búsqueda por EAN | no | **a medias**: se puede leer para contrastar, no mezclar — licencia ODbL (`COMPETENCIA.md:418-429`) | — |
| API pública de precios para terceros | Comparaloo (**API pública y gratis**: 1,2 M de productos, 60 peticiones/minuto). **Ojo con el detalle**: esa API **excluye justo el supermercado** — *"no incluye los productos de supermercado y mascotas... no se pueden servir aquí"*. RadarSuper la anuncia en su plan Pro de 9,99 €/mes | otros programas consumen sus datos | **a medias**: la API existe pero es de casa, por Tailscale (`APP.md:343`) | si, el día que se decida abrir | S |
| Presupuesto y **gasto por tienda** | SuperPrecios (lista con total estimado **y gasto por tienda**), FamilyWall (límites por categoría), OkLista (presupuesto) | cuánto llevas y cuánto en cada sitio | **a medias**: `estimacion` da los tres totales de la lista (`API.md:211`) y **no hay acumulado en el tiempo**, porque falta el cierre de compra | si, con la **tarea 10** (`BACKLOG.md:802-823`) | S |

### 1.3 Escáner de código de barras y nutrición

| Funcionalidad | De quién es (app) | Cómo lo hace ella | La tenemos? | Se puede hacer aquí? | Coste |
|---|---|---|---|---|---|
| Escanear y ver el precio en varias tiendas a la vez | **nadie lo hace bien junto**: Soysuper ("escanea el código de barras para ver el precio y la oferta de cada supermercado"), Findit, OCU Market (precio medio por cadena), **CestIA** (comparación *"emparejada por su código de barras"*). **idealo tiene lector de código de barras pero compara comercio online, no supermercados**: su categoría "Alimentación" es en la práctica bebidas, whisky y vinos. **Yuka no puede hacerlo y lo dice**: *"por razones de independencia no podemos indicar dónde comprar los artículos"* | escaneas y sale el precio en cada cadena | **si** (`src/paginas/Escaner.tsx`, `GET /api/ean/{codigo}`, `plataforma/api/main.py:270`) | si, y es nuestra función diferencial: **25.517 productos traen código de barras**, de los que salen **23.759 códigos distintos**, y **11.613** llegan a 2 o más cadenas (medido; las tres consultas están en el punto 0). La app de referencia del sector **renuncia explícitamente** a esto | — |
| Nota del producto de 0 a 100, **absoluta** | Yuka: **60 %** calidad nutricional (metodología Nutri-Score, "suavizado... según la tabla de correspondencia"), **30 %** aditivos, **10 %** ecológico | una cifra por producto, igual en cualquier tienda | **a medias**: la letra A/B/C de hoy es una posición **dentro del grupo** y el 76,9 % de las letras son el precio disfrazado (`FUNCIONALIDADES.md:138-140`) | **si**: hay **11.944** productos con Nutri-Score o ingredientes (medido). El contrato `nota` ya está escrito en `API.md:390-405` | M |
| Tope de la nota si hay un aditivo de riesgo | Yuka: *"al contener un aditivo que consideramos de riesgo (pastilla roja), la puntuación máxima del producto se ha fijado en 49/100"* | un solo aditivo malo hunde la nota | no | si: `calidad_nota` ya guarda las señales y `core/calidad.py` ya cuenta los aditivos | S |
| Aditivos con color de riesgo | Yuka (4 pastillas: verde, amarillo, naranja, rojo), OCU Market (**código de cuatro colores** + si el aditivo es alergénico + **ingesta diaria admisible** + si se puede usar en ecológico), **AddiCheck** (más de **400 aditivos**, con perfil de salud propio), CodeCheck (semáforo propio, **pero solo en Alemania, Suiza, Austria y Países Bajos**) | cada aditivo con su nivel y su explicación | **a medias**: `core/calidad.py` los cuenta exigiendo "E" + tres o cuatro dígitos — **2 falsos positivos en 400 productos** (`BACKLOG.md:785-788`) — pero el color no existe | si: falta la tabla de riesgo por aditivo, que es un fichero escrito a mano | S |
| Nutri-Score visible | Yuka, GoCoCo (aunque **rechaza el Nutri-Score** y usa su propia escala), OCU Market, Open Food Facts app (que es de donde sale el dato). **CodeCheck no lo usa** | letra A–E | **si**: **8.450** productos con Nutri-Score (medido) | si | — |
| NOVA / ultraprocesados | GoCoCo, OCU Market, Open Food Facts app. **Yuka no lo usa en su fórmula publicada** y **CodeCheck tampoco** | grupo 1–4 | **si**: **7.797** productos con NOVA (medido) | si | — |
| Puntuación propia 0–10 con fórmula publicada | GoCoCo: OMS (modelo de perfil de nutrientes, 17 categorías) **+** NOVA **+** sistema de alerta chileno (calorías, azúcares añadidos, grasas saturadas, sal); regla 4/5/6/10 puntos y **−1 punto por cada sello de advertencia**, hasta −4. **CodeCheck** publica también sus pesos: *"50 % de la evaluación de los nutrientes y 50 % de la evaluación de los ingredientes"* | burbuja roja, amarilla o verde | no | **a medias**: sin `categories_tags` de OFF no hay las 17 categorías de la OMS; con ellas, sí | M |
| Bonus ecológico | Yuka (10 %): *"una bonificación que se otorga a los productos considerados orgánicos, es decir, aquellos con un certificado ecológico oficial nacional o internacional"* | sube la nota si lleva certificado | **a medias**: `certificados` en **730** productos y `sellos` en **11.823** (medido). El sello `ecologico` lo tienen **1.963** (medido) | si: la columna existe y solo hay que mirarla | XS |
| Alternativas más sanas al escanear | Yuka, GoCoCo ("si escaneas un producto con mala puntuación, te sugerimos alternativas mejores al instante") | propone otro producto mejor | no | **no hoy**: la OCU le achaca proponer productos de otra categoría (`COMPETENCIA.md:131-137`) y nuestros grupos son anchos (`COMPETENCIA.md:226-242`) | — |
| "Hay uno mejor **y** más barato", dentro del mismo grupo | idea propia, de la crítica de la OCU a Yuka | | no (**B1**) | **no hoy**: lo cumplen **168 grupos** (medido, `comparacion_fiable`), pero mirando el grupo 92 — "*Cerveza sin alcohol*", **84 productos de las 5 cadenas, de 84,85 a 509,09 céntimos por litro" (medido) — se ve que la cifra mide la anchura del grupo, no el ahorro | — |
| Avisos según tu dieta | Yuka Premium: vegetariana/vegana, sin aceite de palma, sin gluten, sin lactosa, sin cerdo, sin soja, sin sulfitos; **y las recomendaciones también los tienen en cuenta** | marca los productos que no encajan contigo | **a medias**: `GET /api/buscar?sellos=` con 8 sellos (`API.md:449-452`) | si: los sellos ya están y el escáner solo tiene que mirarlos | XS |
| Alertas de alérgenos | Open Food Facts app (**14 alérgenos**, con el aviso *"compruébelo usted mismo siempre con el embalaje"*), **AlerScan** (avalada por **ADILAC** el 9 jul 2026: *"APTO / NO APTO / A REVISAR"*, y cubre alimento, bebida, cosmético, higiene **y fármaco**; *"sin registro, sin correo, sin pagos"*), **IntOut** (65.000 productos, **18 alergias**, foto al plato o a la etiqueta; 14,99 €/año), **Escáner Alergia Alimentaria** (sobre Open Food Facts, avisos de trazas, gratis sin anuncios), **AlergiGuard** (cartas de restaurante por foto + tarjeta médica SOS en 7 idiomas), **Qcomo?** (fructosa y polioles), **ALLiCANEAT** (FODMAP, histamina), OCU Market (si el aditivo es alergénico). **Ojo a lo que NO existe**: ni AESAN ni la SEAIC tienen app de consumo para escanear alérgenos — la de la SEAIC es para alergólogos socios | avisa antes de comprar | **a medias**: `alergenos` en **3.885** productos (medido) y `sellos` sin gluten / sin lactosa filtrables | si, **con la cobertura dicha en pantalla**: `CADENAS.md:33` da alérgenos 0 % en Alcampo, Aldi y Carrefour. **Y hay una limitación que no se puede tapar**: en una alergia, un falso negativo hace daño, así que el aviso va siempre con la frase de "compruébalo en el envase" | S |
| Producto verificado por una asociación de pacientes | **CELIGUIA** (la app de **FACE**, antes FACEMÓVIL; renombrada el 24 abr 2026 *"por motivos legales, derechos de registro de marca"*): lector de código de barras sobre *"los 16.000 productos incluidos en la Lista digital de alimentos sin gluten de FACE"*, y **5.000 establecimientos asesorados**. **sinGLU10** (ACySG Madrid, circuito **independiente** de FACE): +23.000 productos contrastados *"tras consultar al fabricante y revisar los certificados"*, clasifica en *"contiene, no contiene o **puede contener**"*, y **avisa si un producto de tus favoritos cambia** | el aval no es un algoritmo: es una asociación | no | **no**: eso no lo da ninguna cadena; es otro trabajo de datos y no lo vamos a hacer. **Y su propio límite es la prueba de por qué**: FACE reconoce que *"la inclusión en la Lista digital de alimentos es **voluntaria para las empresas**, por lo que no disponemos de la información de todos los productos sin gluten"*, y las reseñas lo confirman (*"2 de cada 3 productos no los tiene"*). CELIGUIA además es **exclusiva para socios** y tiene **1,9★ en Play** | — |
| Tabla nutricional completa (kcal, grasas, azúcares, sal) | Yuka, CodeCheck, OCU Market (con sistema de colores), Open Food Facts app | los números por 100 g o 100 ml | **a medias**: `nutricion` en **3.841** productos y **los 3.841 son de DIA** (medido) | **si**: OFF trae **11.723** (`BACKLOG.md:625`). `nutriments` está pedido en `core/off.py:44`, pero **no comprobado** que llegue a gold | S |
| Historial de escaneos | Yuka ("historial de lo escaneado con código de color"), OCU Market (lo piden sus reseñas), Open Food Facts app ("puede exportar su historial de escaneo") | lo escaneado queda guardado | no | si: es una tabla y una pantalla | XS |
| Buscar sin escanear | Yuka Premium ("barra de búsqueda avanzada"), Open Food Facts app | buscar por nombre en vez de escanear | **si** (`GET /api/buscar`) | si | — |
| Escanear sin conexión | Yuka Premium ("modo sin conexión"), GoCoCo Plus (*"escanea incluso sin señal, por ejemplo dentro de supermercados grandes, y tus resultados se guardan solos en el historial al volver la conexión"*; en el plan gratis, **5 escaneos por semana**), Open Food Facts app ("puede agregar nuevos productos, incluso con mala o nula conexión") | la base viaja en el móvil y lo escaneado se sube luego | no | **no**: descartado llevar el catálogo al móvil (`APP.md:56-76`) | — |
| Ficha completa al escanear: ingredientes, proveedor, origen, conservación | QueFalta ("ingredientes, alérgenos, proveedor y origen, conservación"), OCU Market | todo lo de la etiqueta | **a medias**: ingredientes **7.052**, conservación **7.964**, origen **1.749** (medido); `origen` solo lo publica Mercadona y en el 30 % (`CADENAS.md:36`) | si, con la procedencia dicha en pantalla (`API.md:491-494`) | S |
| Escanear y comparar varios códigos a la vez | OCU Market (lo pide una reseña: *"estar bien la posibilidad de escanear más de un código de barras de una vez de modo que se muestre una comparativa"*) | comparar el lineal entero de una vez | no | si: es una lista y la ficha de grupo ya existe | S |

### 1.4 Histórico, avisos y ofertas

| Funcionalidad | De quién es (app) | Cómo lo hace ella | La tenemos? | Se puede hacer aquí? | Coste |
|---|---|---|---|---|---|
| Ver la oferta mientras añades a la lista | Tiendeo, Bring! (desde el 17 jun 2026: *"añadir ofertas desde folletos digitales directamente a la lista con un solo toque"*), Flipp ("recorta la oferta a tu lista") | la promo aparece al añadir el producto | **a medias**: `core/promos.py` está hecho y con 10 pruebas en verde (`BACKLOG.md:584`); el texto de la mecánica no se enseña (**tarea 4**) | **si, hoy**: falta traducir la mecánica y pintarla | S |
| La mecánica dicha, no la etiqueta | Tiendeo (peor: solo dice "hay promo") | "llevando dos, 1,50 EUR menos por unidad" | no | **si**: `unidades_optimas` y `Mecanica.util` ya existen (`BACKLOG.md:591-593`) | S |
| Avisar de que el descuento es de tarjeta y **no baja el ticket** | (propio, y es una ventaja) | | **si**: `promo_club` en **1.899** productos y `promo_solo_online` en **398** (medido); `MOVIMIENTOS.md:87-120` | si | — |
| Historial de cambios de precio, con fecha | Precios del Super ("últimos cambios de precio", con hora), Comparaloo | una lista cronológica de qué se movió | **si**: `/api/panel/movidos` y `GET /api/pulso` (`plataforma/api/main.py:193`) | si | — |
| "Novedades desde tu última visita" | (propio) | | **si** (`API.md:206`) | si | — |
| Productos retirados del catálogo | Precios del Super (sección **"Retirados"**) | dice qué ha dejado de venderse | **a medias**: `disponible` está en el 100 % de las cinco cadenas (`CADENAS.md:22`), pero no hay pantalla de retirados | si: es un `WHERE disponible = false` comparado con el día anterior | S |
| Evaluación avalada por expertos independientes **nombrados** | CodeCheck (Producto Check GmbH, Berlín; 4,2★, 5 M+ descargas): sus valoraciones salen de *"expertos independientes, entre ellos la Asociación Alemana de Alergia y Asma (DAAB), el Centro del Consumidor de Hamburgo (VZHH), Greenpeace (Suiza) y WWF"*, con datos de la **Comisión Europea**, el **California Department of Public Health**, el **BUND** (microplásticos) y **GS1** para saber qué organización emitió el código de barras. **sinGLU10** hace lo mismo con el aval de la **ACySG** | la nota no la firma un algoritmo anónimo | **a medias, y por el camino bueno**: `calidad_origen` y `sellos_origen` ya dicen de dónde sale cada dato (`API.md:491-494`), y el prefijo del código se enseña con su nombre — **"marca registrada en España"**, no "producto español" (`APP.md:271-283`) | S |
| Aviso de retirada de producto por seguridad | **ninguna app de la competencia avisa dentro de tu lista**; lo más cerca que está alguien es la sección **"Alertas"** de la OCU, que publica las retiradas como noticia (por ejemplo, *"retirada de adelgazantes con sibutramina"*), no enganchadas a lo que compras. La fuente buena es **AESAN** | avisa si algo de tu lista está retirado | no (**N10**, `BACKLOG.md:1160-1189`) | **si**: una página HTML al día, sin RSS ni API (`COMPETENCIA.md:433-449`). `es_recall` existe en gold y está a **0** (medido) | M |
| Folletos de las tiendas de tu ciudad | Tiendeo (folletos de Mercadona, Lidl, Carrefour, Alcampo, Aldi, DIA, Eroski + 40 países), Ofertia, Flipp, RadarSuper (boletín por WhatsApp) | los catálogos de la semana | no | **no**: no bajamos folletos y son imágenes; para leer un folleto hay que hacer reconocimiento sobre un PDF | — |
| Folletos consultables sin conexión | Tiendeo ("consulta los catálogos disponibles incluso sin conexión") | | no | no: sin folletos, no hay nada que guardar | — |
| Aviso semanal de folletos nuevos | Tiendeo ("una notificación cada semana con los nuevos folletos") | push semanal | no | **no**: push pide servidor siempre accesible (`FUNCIONALIDADES.md:253`) | — |
| Tarjetas de fidelización guardadas | Bring! (**Bring! Wallet**), Tiendeo (novedad: escanearlas y llevarlas siempre), Flipp, la app de la cadena | se enseñan en caja | no | **no**: son datos personales y algunas dan acceso a saldo (`FUNCIONALIDADES.md:239`) | — |
| Devolución en efectivo por el ticket (cashback) | **Woolsocks**, **Gelt** (5 M+ descargas), **PROMOS** (acepta tickets de *"cualquier supermercado en España"*), **La Cuponera** (**operada por P&G**, la mejor valorada: 4,69 con 16.632 reseñas). Ninguno llega a cuenta bancaria desde el programa de la cadena: pagan ellos, con el margen de la marca | fotografías el ticket, escaneas el producto y te devuelven el dinero | no | **no**: hay que pagar de verdad — cobrar, validar el ticket y transferir — y tener acuerdos con las marcas que financian la promoción. Es un negocio de pagos, no una función. **Y el ticket es justo el dato que decidimos no leer** (`FUNCIONALIDADES.md:243-247`) | — |
| Puntos y recompensas personalizadas | Lidl Plus (**"Puntos Lidl"** desde el 1 jul 2026: *"un punto por cada euro gastado en tiendas físicas"*, más de **400 recompensas**, validez 24 meses, **10 millones de usuarios en España**), Club Alcampo (saldo en € + puntos), Mi Carrefour (**ChequeAhorro** cada dos meses y Tarjeta PASS al **1 %**), BM ("Ahorrando mes a mes"), EROSKI club, Club Dia, BonpreuEsclat (1 %) | acumulas y canjeas | no | **no**: hay que ser la cadena y tener su programa. **Y las dos cadenas más grandes no lo tienen**: Mercadona no tiene tarjeta ni puntos (lo confirma la empresa) y **ALDI lo rechaza por política**. No es un hueco que nosotros podamos llenar | — |
| Cupones y descuentos personalizados | Mi Carrefour (cupones personalizados), Lidl Plus, DIA, Tiendeo ("cupones y descuentos exclusivos") | la cadena te calcula el descuento sobre tu historial | no | **no**: la cadena los calcula sobre tu ticket y no los publica en ningún sitio | — |
| ChequeAhorro: en qué has ahorrado | Mi Carrefour | suma lo ahorrado con cupones | no | **no**: requiere el ticket | — |
| Control de gasto en el tiempo | Your Food ("guarda lo que pagaste y mira cómo se acumulan tus gastos"), BM ("Ahorrando mes a mes"), FamilyWall (presupuesto Premium) | gráfica de lo gastado | no | **si**, con el cierre de compra de la **tarea 10** (`BACKLOG.md:802-823`) | S |
| Estadísticas de la casa | QueFalta Plus ("estadísticas") | números de tu compra | no | si, con el cierre de compra | S |

### 1.5 Despensa, caducidades y desperdicio

| Funcionalidad | De quién es (app) | Cómo lo hace ella | La tenemos? | Se puede hacer aquí? | Coste |
|---|---|---|---|---|---|
| Inventario separado por nevera / congelador / despensa | NoWaste (*"listas de inventario para el congelador, el frigorífico y la despensa"*), KitchenPal, CozZo, FridgeBuddy, Smantry | tres listas separadas | no | **no a mano**: descartado a propósito (`FUNCIONALIDADES.md:241`); la versión deducida es mejor | — |
| Despensa **deducida** de la compra | la idea es de NoWaste; la versión sin teclear nada es nuestra | | no (**D1**, `FUNCIONALIDADES.md:156-171`) | **si**, pero necesita la **tarea 10** cerrada antes y meses de uso | M |
| Aviso de caducidad | NoWaste ("dos recordatorios por producto", "escanear la fecha de caducidad"), KitchenPal ("recibe alertas antes de caducar"), Mi despensa (color según caducidad + email), FridgeBuddy, CozZo (distinguía **"Best By"** de **"Use By"**), Smantry (distingue consumo preferente de caducidad) | te avisa antes de que se pase | no (**D3**, `FUNCIONALIDADES.md:178-182`) | **a medias, y hay que decir la cobertura**: `dias_caducidad` solo lo publica DIA — **4.382 productos de 52.567, el 8,3 %** (medido); `COLECTORES.md:47` lo dice: *"Nadie más publica esto"* | M |
| Escanear para añadir al inventario | NoWaste, KitchenPal (5 M de productos), CozZo (500 M) | escaneas y entra | **a medias**: el escáner está hecho y el inventario no | si, cuando exista la despensa | S |
| Reconocimiento por foto de tickets y alimentos | NoWaste ("photo recognition"), KitchenPal, CozZo ("Receipt Reader"), FridgeBuddy (foto + Siri + tickets PDF), FridgeTrack (foto del ticket), **Woolsocks** (*"escanea el ticket... el cashback se añadirá automáticamente en 48 horas"*, y rechaza los recibos *"cortados o doblados"*) | una foto y entra todo | no | **no**: descartado (`FUNCIONALIDADES.md:243`). Si algún día hace falta, la puerta es el **ticket digital**, no la foto | — |
| Mover artículos entre listas | NoWaste ("mueva artículos entre listas"), Out of Milk ("mover o copiar entre la lista y la despensa") | nevera → congelador | no | si, cuando exista la despensa deducida | S |
| Marcar "repuesto" al comprar | NoWaste, Mi despensa (**umbral de cantidad mínima y reposición automática**) | lo que se acaba vuelve a la lista | no | si: es una columna en la despensa y una línea en la lista | XS |
| Recetas con lo que tienes | KitchenPal (*"no disponible en ninguna otra app"*), CozZo, FridgeTrack, Encantado de Comerte | propone recetas con el inventario | no | **no hoy**: por el casado de ingredientes, el mismo problema del emparejador | XL |
| Estadísticas de comida tirada | NoWaste ("My numbers"), CozZo (Journal), FridgeBuddy (consumido contra tirado) | cuánto se tira | no | si, con el cierre de compra y `dias_caducidad` | M |
| Sincronizar la despensa en familia | KitchenPal ("comparte y sincroniza con tu familia"), CozZo (hasta 10 personas), FridgeBuddy (iCloud), NoWaste | | **a medias**: las listas ya se comparten | si | XS |
| Packs de excedente de comercios a mitad de precio | Too Good To Go (**8 millones de usuarios y 20.000 negocios en España**, packs sorpresa + Caja Despensa), Phenix (Francia, Bélgica, España y Portugal), Coometas (Madrid, País Vasco, Aragón, La Rioja y Galicia), Karma | marketplace de dos lados | no | **no**: cada comercio tiene que publicar su excedente, hay que captarlo puerta a puerta, cobrar y pagar. Es otro negocio | XL |
| Compartir excedente con vecinos | OLIO ("comunidad global de 7 millones de usuarios") | regalo entre vecinos | no | **no**: es una comunidad, no un dato. Y **no hay evidencia de operación activa en España** | XL |

### 1.6 Compra online y pago

| Funcionalidad | De quién es (app) | Cómo lo hace ella | La tenemos? | Se puede hacer aquí? | Coste |
|---|---|---|---|---|---|
| Comprar online con entrega | apps de las cadenas (Mundo Consum, Alcampo Online, BM, EROSKI por redirección), Soysuper ("compra") | carrito y reparto | no | **no**: cambia el producto entero (`COMPETENCIA.md:400-402`); somos una app para **ir a la tienda** | — |
| Incluir los gastos de envío en la comparación | Soysuper (`COMPETENCIA.md:80`) | suma el reparto al total | no | **no**: `grupos.parquet` tiene **53 columnas y ninguna de envío** (medido), y no compramos online | — |
| Escanear y pagar sin pasar por caja | **Club Alcampo, AutoScan** (escanear y pagar por QR, ~40 tiendas desde 2026) | escaneas mientras llenas el carro y pagas al salir | no | **no**: hace falta ser la cadena y tener su TPV | — |
| Pago con QR o con el móvil | Mi Carrefour, El Corte Inglés (solo consta en prensa de feb-2023, **no en las fichas de sept-2026**) | | no | **no**: hay que ser la cadena (`FUNCIONALIDADES.md:242`) | — |
| Canje en caja por NFC | Mundo Consum (**solo Android**, según fuente oficial propia; no en iOS) | se acerca el móvil y aplica el cupón | no | no | — |
| Seguimiento del pedido | BM, cadenas | estado del reparto | no | no | — |
| Enviar la cesta al supermercado | Soysuper ("enviar al supermercado") | traspasa la cesta a su web | no | **no**: automatizar una compra en nombre del usuario (`FUNCIONALIDADES.md:248`) | — |
| Lista creada desde el folleto | Mi Carrefour ("crear listas desde los folletos") | | no | no: sin folletos no hay de dónde | — |

### 1.7 Apps de las cadenas

| Funcionalidad | De quién es (app) | Cómo lo hace ella | La tenemos? | Se puede hacer aquí? | Coste |
|---|---|---|---|---|---|
| Lector de precios en tienda | Mi Carrefour (*"escanea con la app los productos en tienda"*), Club Alcampo (AutoScan), idealo (desde **cualquier** tienda física) | escaneas y ves el precio | **si, y mejor**: el nuestro compara **las cinco cadenas** y no solo la tienda donde estás (`src/paginas/Escaner.tsx`) | si | — |
| Ticket digital guardado | Mi Carrefour ("Papel Cero"), Mercadona (por WhatsApp), BM (descargable; **54 % de sus usuarios de app lo usan**), DIA, Lidl Plus, EROSKI (no en tiendas CHÁRTER) | el ticket vive en la app | no | **no**: el ticket lo emite la cadena y no hay API pública. La app **no guarda datos de pago** (`API.md:427`) | — |
| Lista de la compra dentro de la app | Mercadona, Mi Carrefour, Alcampo Online, EROSKI (con **escáner de código de barras y voz**), BM (listas de ida y vuelta con la tienda online) | | **si** | si | — |
| Ofertas y folletos digitales | todas | sección de promos | **a medias**: `promo` en **7.207** y `promo_txt` en los que la publican (medido; `CADENAS.md:41-44` da 0 % en Mercadona y Carrefour) | si | — |
| Información nutricional y alérgenos del producto | EROSKI y BM los ofrecen en su app | | **a medias**: Nutri-Score **8.450**, alérgenos **3.885** (medido) | si | — |
| Valoraciones de clientes | EROSKI las publica en el listado (`EROSKI.md`), y de las cinco nuestras **ninguna** | estrellas y opiniones | no | **a medias**: el dato existe pero solo en Eroski, que **no está bajada**; `grupos.parquet` no tiene ninguna columna de valoración (medido) | L |
| Compra online y recogida | todas | | no | no | — |

### 1.8 Otros

| Funcionalidad | De quién es (app) | Cómo lo hace ella | La tenemos? | Se puede hacer aquí? | Coste |
|---|---|---|---|---|---|
| Escala saludable con valoración **propia** de aditivos | OCU Market (**0 a 100**, con nutrientes, Nutri-Score, NOVA, **aromas** y valoración de aditivos por la OCU) | nota con aval de una organización de consumidores | no | si: es la nota de la ficha 9 con una tabla de aditivos escrita a mano | M |
| Comparar tu cesta con el IPC oficial | RadarSuper (contrasta su cifra con el IPC alimentación del INE y **señala cuándo divergen**), Precios del Super (sección "IPC") | inflación oficial al lado de la real | no | **no**: descartado a propósito (`APP.md:404`, "es otro proyecto") | — |
| Filtro de "producto nacional" | lo pediste tú, no lo tiene ninguna app | | no | **no**: techo realista de **1.900 de 51.781, el 3,7 %** (`CADENAS.md:95`, `BACKLOG.md:639-642`) | — |
| Nota con la procedencia del dato a la vista | Open Food Facts app, RadarSuper ("te la enseñamos producto a producto para que la compruebes tú") | dice de dónde sale cada número | **si**: `sellos_origen` vale `certificado`, `etiqueta`, `nombre` o `mixto` y la interfaz lo dice (`API.md:491-494`); reparto medido: etiqueta **10.178**, nombre **795**, mixto **508**, certificado **342** | si | — |
| Publicidad y patrocinio | Bring!, Listonic (gratis con anuncios), Flipp ("contiene anuncios"), Phenix ("contiene anuncios"), Out of Milk ("contains ads") | financiación por publicidad | no | **no, y nunca**: `PANTALLAS.md:323-324` | — |
| Pantalla de actividad familiar | Cozi, FamilyWall, Dommuss | quién hizo qué y cuándo | no | **no**: descartado (`PANTALLAS.md:318-319`) | — |
| Tutorial o pantalla de bienvenida | casi todas | | no | **no**: descartado (`PANTALLAS.md:316`) | — |
| Modo oscuro | QueFalta, Listonic, Bring! | | **si** | si | — |
| Idiomas más allá del castellano | QueFalta (ES + CA), Listonic (38 idiomas) | | no | si: es texto | S |
| Asistente que aprende tu compra y la planifica | OurGroceries (integración **MCP** con Claude y ChatGPT), AnyList (planificador de comidas), Samsung Food | | no | **no por ahora**: un planificador de comidas sin recetas casadas no dice nada útil | XL |

---

## 2. Ficha por funcionalidad

Solo las que **no están hechas** y **se pueden hacer**. Las que están hechas no
llevan ficha: no hay nada que implementar.

### Ficha 1 · Ordenar la lista por pasillos

**Que es.** Agrupar las líneas de la lista en el orden en que se recorre la
tienda, dentro de "Por coger".

**Quien lo hace y como.** QueFalta promete *"ordenada por las categorías del
supermercado"*; Bring! lo llama *"sort your list... based on the aisles in your
supermarket"*; AnyList deja *"reorganizar las categorías para que se adapten al
diseño de tu tienda"*. Se usa así: se abre la lista en la puerta de la tienda y
las líneas aparecen ya en el orden del recorrido, sin que nadie las ordene.

**El dato que hace falta.** `seccion`, que **ya está en gold**: 52.446 de 52.567
productos (medido). El orden de recorrido ya existe en `core/secciones.ORDEN`
(`BACKLOG.md:470-483`). El fichero de equivalencias es `core/datos/secciones.yml`,
849 claves, con el 97 % propuesto automáticamente (`COMPETENCIA.md:329-331`).
**No hace falta nada nuevo.**

**Diseno aqui.**

- Sin ruta nueva. Se agrupa en el cliente con lo que ya devuelve
  `GET /api/listas/{id}`.
- `plataforma/api/catalogo.py`: `secciones()` (línea 365) ya devuelve el orden;
  hay que devolver también `seccion` en cada línea de la lista, que hoy no viaja.
- Front: `plataforma/web/app/src/paginas/Cesta.tsx`. Las líneas se agrupan por
  `seccion` bajo encabezados, usando `RespuestaSecciones` (`src/tipos.ts:173`).
- Lo que no tenga sección va al final, bajo **"otros"**, y no desaparece
  (`BACKLOG.md:484-485`).

**La regla que la gobierna.** *"Lo que no tenga sección va al final, bajo 'otros':
no se inventa una sección para que no quede feo"* (`BACKLOG.md:484`). Y la ley 6
del `README.md:57` — ningún campo vacío: o tiene sección, o va a "otros" dicho.

**Como se sabe que esta bien.**

    uv run pytest tests/test_secciones.py           13 pruebas en verde
    uv run python -m projects.cesta.auditar_secciones

- La lista del móvil se agrupa y el orden es el de recorrer la tienda.
- `seccion` llega a cada línea con **cobertura ≥ 99 %** (hoy hay 99,8 % en gold:
  52.446 de 52.567, medido).
- Un producto sin sección sale bajo "otros", al final, y se puede tachar.
- **Las cinco cadenas siguen dando el mismo total**: agrupar no cambia
  `estimacion.total_cent`.

**Lo que se descarta.** Un clasificador de texto para los restos sin sección. Si
al final quedan claves sueltas, se miran y se añaden al fichero
(`BACKLOG.md:494-496`).

---

### Ficha 2 · El mosaico de lo de siempre

**Que es.** Una cuadrícula con lo que esa persona más ha añadido, a un toque,
cuando el buscador está vacío.

**Quien lo hace y como.** Bring! lo llama *"tiles"* y Listonic *"personalized
product suggestions based on shopping history"*; Soysuper lo llama "Minisúper"
(`COMPETENCIA.md:392-396`). Se usa así: abres Buscar, no escribes nada, y ahí
está lo de siempre con su foto; un toque y ya está en la lista.

**El dato que hace falta.** `lista_linea.anadido_por` y `anadido_en` **ya
existen** (`plataforma/sql/001_esquema.sql:93-94`), y `imagen` está en **52.567
de 52.567** productos (medido). Nada nuevo.

**Diseno aqui.**

    GET /api/habituales?limite=24          (contrato ya escrito en API.md:380-388)

    sale  {"fecha_datos",
           "habituales": [{"grupo_id", "nombre", "imagen",
                           "precio_cent", "veces", "ultima_vez"}]}

- Implementación en `plataforma/api/main.py`, junto a `/api/buscar`
  (línea 144). La consulta sale de `almacen.py` (PostgreSQL) y el precio de
  `catalogo.py` (gold), igual que `GET /api/favoritos` (`main.py:585`).
- Front: `plataforma/web/app/src/paginas/Buscar.tsx`, cuando
  `consultaUtil(f)` es falso (`src/api/consultas.ts:65-67` ya sabe detectar el
  buscador vacío). Nuevo componente `src/componentes/Mosaico.tsx`.
- **Lista vacía si no hay historial, y la interfaz no pinta nada.** No se
  rellena con "populares" (`API.md:388`).

**La regla que la gobierna.** Nada de campos vacíos ni datos inventados: sin
historial no hay mosaico, y no se sustituye por lo más vendido del catálogo, que
no es lo mismo (`API.md:388`). Área de pulsar de 44 px o más (`UX-MOVIL.md:138`).

**Como se sabe que esta bien.**

- Con el buscador vacío y **con** historial, se ve el mosaico, y añadir algo desde
  ahí son **dos toques** (el producto y ya).
- Con el buscador vacío y **sin** historial, no se pinta nada, y la pantalla sigue
  diciendo qué se puede buscar.
- Los 24 que salen son los que ese usuario añadió más veces en 90 días: se
  comprueba contra `SELECT grupo_id, count(*) FROM lista_linea WHERE
  anadido_por = ... AND anadido_en > now() - interval '90 days' GROUP BY 1`.
- `uv run pytest tests/test_cesta_api.py` en verde, con una prueba que pide
  `/api/habituales` sin sesión y espera **401**.

**Lo que se descarta.** El mosaico de iconos de Bring! hecho a mano (un catálogo
de iconos por producto). Con la foto real que ya está en gold se ve mejor y no
hay nada que mantener.

---

### Ficha 3 · Voz en el buscador

**Que es.** Un botón de micrófono que rellena el campo de búsqueda.

**Quien lo hace y como.** Listonic (*"voice input — add items hands-free"*),
Soysuper (*"dicta tu lista de la compra"*), EROSKI y OkLista también. No es un
asistente: dices "dos litros de leche entera" y aparece escrito en el campo.

**El dato que hace falta.** Ninguno. Es del navegador (`SpeechRecognition`).

**Diseno aqui.**

- Sin ruta nueva. Front: `plataforma/web/app/src/paginas/Buscar.tsx` y
  `src/componentes/FiltrosBusqueda.tsx`.
- **Si el navegador no lo soporta, el botón no se dibuja** (`FUNCIONALIDADES.md:49`).
  En iOS solo va en Safari y pide permiso (`BACKLOG.md:560-561`).
- Si el texto trae cantidad ("dos litros"), se propone como `cantidad` de la
  línea, pero **no se añade sola**.

**La regla que la gobierna.** Un botón que se dibuja y falla es peor que no tener
botón (`BACKLOG.md:561`, y la misma regla ya aplicada en `Escaner.tsx:57-60` con
`BarcodeDetector`). Y no es un asistente: no se le pide nada más.

**Como se sabe que esta bien.**

- En un navegador sin `SpeechRecognition`, **el botón no existe en el DOM**: se
  comprueba que no hay ningún elemento con `data-voz` en el árbol.
- "dos litros de leche entera" deja el campo con "leche entera" y propone
  cantidad 2, sin haber añadido nada a la lista.
- Decir "leche" y no tocar nada no rompe la búsqueda por texto, que sigue
  funcionando igual.
- `uv run pytest tests/test_interfaz.py` en verde.

**Lo que se descarta.** Un asistente conversacional. Con nueve días de histórico
y un buscador que ya funciona, es una promesa que no se puede cumplir en el
pasillo con una mano.

---

### Ficha 4 · Notas por línea, en la interfaz nueva

**Que es.** Poder escribir "la de cristal" en una línea de la lista.

**Quien lo hace y como.** Bring! (*"notas y fotos por producto"*), Listonic,
AnyList (*"agrega notas sobre la marca, la cantidad o incluso una foto"*).
Un toque largo sobre la línea y un campo de texto.

**El dato que hace falta.** **Ya existe**: `lista_linea.nota`
(`plataforma/sql/001_esquema.sql:92`). La API lo acepta desde el principio
(`POST /api/listas/{id}/lineas`, `API.md:218`, con `"nota": "la de cristal"`), y
**la interfaz no lo usa** (`BACKLOG.md:609`).

**Diseno aqui.**

- Sin ruta nueva: `nota` va en `POST /listas/{id}/lineas` y en
  `PATCH /listas/{id}/lineas/{linea_id}` (`plataforma/api/main.py:402` y `:419`).
- Front: `plataforma/web/app/src/paginas/Cesta.tsx`, en la línea de la lista.
- Ojo: `src/tipos.ts:414` tiene `nombre_visto` y **hoy no se pinta ningún fichero
  de `app/src`** (`BACKLOG.md:97-100`). Al pintar la línea, esto se arregla de
  paso.

**La regla que la gobierna.** El campo ya está en el contrato: no se añade una
ruta nueva para algo que ya viaja. Y una nota vacía es `null`, no cadena vacía
(`API.md:37`).

**Como se sabe que esta bien.**

- Se escribe una nota, se recarga la pantalla y sigue ahí.
- La otra persona la ve al sincronizar.
- Una línea **sin** nota no enseña un hueco: no enseña nada.
- `uv run pytest tests/test_lineas_api.py` en verde, con un caso que manda
  `nota` de 500 caracteres y espera que se corte o se rechace, no que reviente.

**Lo que se descarta.** Fotos por línea. La `imagen` del grupo ya se pinta y una
foto propia del usuario sería almacenamiento que hay que respaldar.

---

### Ficha 5 · La mecánica de la oferta, al añadir y en la lista

**Que es.** No decir "hay promo", sino **qué hay que hacer** para aprovecharla:
"llevando dos, 1,50 EUR menos por unidad".

**Quien lo hace y como.** Tiendeo solo dice que hay promoción
(`COMPETENCIA.md:96-98`); Bring! desde el 17 de junio de 2026 añade la oferta del
folleto a la lista con un toque. Nosotros podemos hacerlo mejor porque sabemos
el precio **y la mecánica** (`BACKLOG.md:577-585`).

**El dato que hace falta.** **Ya está hecho**: `core/promos.py`, con 10 pruebas en
verde, y `unidades_optimas` calculado (`BACKLOG.md:584, 591-593`). El texto de la
oferta está en `promo_txt` y el sí/no en `promo` — **7.207 productos con `promo`**
(medido). `CADENAS.md:41-44` avisa de que Carrefour y Mercadona no publican texto
de promoción.

**Diseno aqui.**

- Sin ruta nueva. `GET /api/buscar` ya devuelve `con_oferta` (`API.md:119`): hay
  que añadir `mecanica` y `unidades_optimas` a esa fila.
- Front: `src/componentes/TablaResultados.tsx` (el sello de oferta) y
  `src/paginas/Cesta.tsx` (la línea pequeña debajo de la línea de la lista).
- En la lista: *"llevando 3 en vez de 2, la tercera sale gratis"*.

**La regla que la gobierna.** *"Una oferta es una regla, no un precio"*
(`BACKLOG.md:435-437`): "2ª unidad −50 %" no abarata el producto, abarata el par.
Y **los descuentos de tarjeta no bajan el total**: no se descuentan en caja. Por
eso `Mecanica.util` los excluye, y `promo_club` está puesto en **1.899**
productos (medido).

**Como se sabe que esta bien.**

    uv run pytest tests/test_promos.py              10 pruebas en verde

- Un producto con "3x2" enseña la sugerencia cuando llevas 2.
- Un producto con "Club Alcampo … acum en tu tarjeta" **no la enseña**
  (`BACKLOG.md:598-600`).
- El total de la lista baja al subir de 2 a 3 unidades en un 3x2.
- Un producto de Mercadona (que no publica `promo_txt`) no enseña una mecánica
  inventada.

**Lo que se descarta.** Leer los folletos de Lidl y Aldi para sacar sus ofertas.
Sus folletos son imágenes y no traen precio por unidad; RadarSuper, que sí lo
intenta, reconoce que de ellas *"solo vigilamos folletos y novedades"*
(radarsuper.com/metodologia). Es lo mismo que concluyó `LIDL.md`.

---

### Ficha 6 · La pantalla del verificador de ofertas

**Que es.** *"Esta oferta no lo es"*: la lista de promociones anunciadas que el
histórico no sostiene.

**Quien lo hace y como.** PrecioReal by Chollometro (extensión de Safari,
*"evita falsas rebajas"*), Comparaloo (*"detector de falsas rebajas: un −50 %
sobre un precio inventado es el precio de siempre"*, y enseña "precio habitual
30 días / subido hace 3 días / rebajado hoy"), RadarSuper (*"qué ofertas del
folleto son de verdad"*). Se usa así: miras la oferta que tienes delante y
compruebas si el precio de hoy está por debajo de lo que ese producto cuesta
normalmente.

**El dato que hace falta.** **Ya está calculado y ya hay endpoint.** `GET
/api/ofertas-dudosas` existe (`plataforma/api/main.py:225`) y cruza `promo_txt`
con `precio_base_cent` y `posicion_90d` de `precio_derivado.parquet`
(`plataforma/api/movimientos.py:142-207`). **No hay nada que calcular.**

Aviso importante y medido: `oferta_sospechosa`, que es la regla más exigente
(subir el precio justo antes de anunciar la oferta), compara con `shift(45)` y
**hoy sale `False` en las 763.042 filas** (medido; `BACKLOG.md:835-837` dice
"necesita 45 días → 20 de octubre"). **No está roto: está esperando.**

**Diseno aqui.**

    GET /api/ofertas-dudosas?limite=60&cadenas=alcampo     ya existe

- Front: nueva pestaña en `plataforma/web/app/src/paginas/Panel.tsx`, en la lista
  de pestañas de la línea 30-35. El `app.js` viejo la tenía (`app.js:1110-1156`)
  y se perdió en la migración (`BACKLOG.md:133-137`).
- Cada fila enseña `por_que`, que ya lo devuelve la API
  (`movimientos.py:206`).

**La regla que la gobierna.** Se enseña el motivo, no un veredicto: `por_que` ya
existe y la pantalla no decide por nadie. Y **la pantalla no puede decir que una
oferta es falsa si lo que pasa es que no sabemos** — cuando `precio_base_cent` es
`null`, la fila no entra (`movimientos.py:189`).

**Como se sabe que esta bien.**

    uv run pytest tests/test_movimientos.py         en verde

- La pestaña sale y responde con datos sobre el gold de hoy.
- **La pantalla dice cuántos días de histórico tiene** y, si son menos de 45,
  explica que el control del "precio subido antes de la oferta" está dormido y
  cuándo despierta (`MOVIMIENTOS.md:77-83`).
- Ninguna fila lleva el distintivo de tarjeta: `solo_con_tarjeta` ya viene
  (`movimientos.py:205`).

**Lo que se descarta.** Basar la pantalla en `oferta_sospechosa`. Enseñaría una
pantalla vacía durante seis semanas sin que nadie supiera por qué
(`MOVIMIENTOS.md:82-83`).

---

### Ficha 7 · Los avisos de precio, en la interfaz nueva

**Que es.** Que un producto vigilado avise cuando baja de verdad, al abrir la app.

**Quien lo hace y como.** idealo (*"Precio Ideal: activa una alarma de precios y
te avisaremos cuando el artículo alcance el precio deseado"*), Comparaloo (aviso
por correo **sin registro**, confirmado con un código de seis dígitos), PrecioReal
(*"alertas de bajada"*), Tiendeo (alertas de promos de tus favoritos). Son
**pasivas**: la app te lo enseña cuando la abres, no te manda nada.

**El dato que hace falta.** **Ya está**: tabla `alerta` con tres tipos —
`baja_de`, `minimo_90d`, `cualquier_bajada` — y umbral
(`plataforma/sql/001_esquema.sql:126-133`), y cuatro rutas vivas
(`plataforma/api/main.py:549, 563, 573, 579`). El `app.js` viejo las usaba
(`app.js:742, 1066, 1493, 1505`) y **el front nuevo tiene cero coincidencias de
`alertas` en `app/src`** (`BACKLOG.md:128-132`).

**Diseno aqui.**

    GET    /api/alertas              con `saltan`, que ya las explica
    POST   /api/alertas              {"grupo_id", "tipo", "umbral_cent"}
    DELETE /api/alertas/{alerta_id}
    POST   /api/alertas/vistas       {"ids": [...]}

- Front: `src/paginas/Favoritos.tsx` (crear y ver) y
  `src/componentes/BotonFavorito.tsx` (el mismo sitio donde ya se guarda un
  favorito). Nuevo `src/api/alertas.ts`.
- Marcar como vistas es **otra llamada**, a propósito: abrir la pantalla en el
  autobús no es haberlas leído (`main.py:551-556`).

**La regla que la gobierna.** *"Las alertas son pasivas: la app te lo enseña
cuando la abres, no te manda nada"* (`APP.md:249-251`), porque el push pide un
servidor siempre accesible y **el PC se apaga** (`FUNCIONALIDADES.md:253`).

**Como se sabe que esta bien.**

- Crear una alerta de tipo `minimo_90d` sobre un favorito y ver que aparece.
- Una alerta que salta se enseña con su frase; **no se marca como vista sola**.
- Borrar una alerta que no es tuya da **404**, no 403 (`API.md:52-56`).
- `uv run pytest tests/test_alertas.py` en verde.

**Lo que se descarta.** Notificaciones push y avisos por correo. Comparaloo puede
mandar correo porque tiene servidores; nosotros no, y el correo además saca de
casa el dato de qué vigilas.

---

### Ficha 8 · Índice de precios y posición por sección

**Que es.** Dos pantallas del panel que ya tienen endpoint y no tienen pantalla:
cuánto se ha movido el índice, y dónde está cada cadena dentro de cada pasillo.

**Quien lo hace y como.** RadarSuper publica "qué supermercado es más barato esta
semana" con una **cesta tipo de 23 básicos**, la mediana del €/kg o €/l, solo
precios de los últimos 7 días, y **una cadena solo puntúa si tiene 3 productos
reales suyos con precio fresco**; si no llega, se queda fuera del ranking en vez
de aparecer con datos viejos. Precios del Super tiene sección "IPC".

**El dato que hace falta.** **Ya está**: `GET /api/indice`
(`plataforma/api/main.py:187`), `GET /api/posicion` (`:199`) y `GET /api/pulso`
(`:193`), sobre `analisis.py`. La sección está en el 99,8 % del catálogo (medido)
y `precio_diario` tiene **763.042 filas en 17 fechas** (medido).

**Diseno aqui.**

- Front: dos pestañas nuevas en `src/paginas/Panel.tsx`. El `app.js` viejo las
  tenía (`app.js:796-920` y `:925-996`) y se perdieron (`BACKLOG.md:133-135`).
- De paso, el **filtro del panel por cadenas cercanas**: `Panel.tsx:488` llama
  `useBajadas(dias, subidas, [])` con la lista vacía y ninguna pestaña lee
  `cadenas_cerca` (`BACKLOG.md:135-137`).

**La regla que la gobierna.** Cada número dice sobre cuántos productos está
calculado, o no se enseña (`panel.py`, citado en `Panel.tsx:3`). Un ranking con
pocos días de histórico se declara como tal, no se disfraza.

**Como se sabe que esta bien.**

- Con menos de 7 días de serie, el índice **avisa** de que la ventana es corta en
  vez de dar una cifra firme.
- Pulsar cualquiera de las dos no cambia ni un fichero (`test_el_panel_solo_lee`,
  citada en `API.md:340-343`).
- `uv run pytest tests/test_analisis.py` en verde.

**Lo que se descarta.** La cesta tipo de 23 básicos de RadarSuper como pantalla
propia. Es una selección fija y discutible, y nosotros podemos enseñar el
**conjunto entero** de grupos comparables, que son **7.992** (medido), sin
elegir por nadie.

---

### Ficha 9 · La nota absoluta del producto y el color de riesgo de los aditivos

**Que es.** Cambiar la letra A/B/C de hoy por una **nota de 0 a 100 absoluta**:
60 % nutrición, 30 % aditivos, 10 % ecológico, con tope en 49 si hay un aditivo
de riesgo alto.

**Quien lo hace y como.** Es la fórmula de Yuka, **publicada en su centro de
ayuda** (*"la calidad nutricional representa el 60 % de la nota... la presencia de
aditivos representa el 30 %... la dimensión orgánica representa el 10 %"*, y
*"al contener un aditivo que consideramos de riesgo (pastilla roja), la
puntuación máxima del producto se ha fijado en 49/100"*). Cada aditivo lleva una
pastilla de color: verde sin riesgo, amarillo limitado, naranja moderado, rojo de
riesgo. **OCU Market** hace lo mismo con cuatro colores y añade **si el aditivo es
alergénico, la ingesta diaria admisible y si se puede usar en ecológico**; su
escala es de 0 a 100 e incluye los **aromas** en la valoración. **GoCoCo** usa
otra fórmula, también publicada: OMS + NOVA + sistema de alerta chileno.

**El dato que hace falta.**

    Nutri-Score           8.450 productos   (medido; count(nutriscore))
    ingredientes          7.052 productos   (medido; count(*) WHERE ingredientes IS NOT NULL AND <> '')
    Nutri-Score o ingredientes  11.944, el 22,7 %   (medido; count(*) WHERE nutriscore IS NOT NULL
                                                     OR (ingredientes IS NOT NULL AND ingredientes <> ''))
    sellos                11.823 productos  (medido), de ellos ecologico 1.963
    aditivos              core/calidad.py los cuenta hoy

**Cuidado con la union de las tres**: `nutricion` (3.841) es **otra columna** --
la tabla de la etiqueta, que solo publica DIA -- y no entra en esa cuenta. La
nota se calcula con `nutriscore` e `ingredientes`. Las consultas estan en el
punto 0.

Falta **una tabla de riesgo por aditivo**, y esa **no se puede bajar de ninguna
cadena**: es un fichero escrito a mano. Es el mismo tipo de trabajo que
`core/datos/secciones.yml` (849 claves escritas en una tarde,
`COMPETENCIA.md:325-327`). Los aditivos que aparecen de verdad en el catálogo
son un número corto, no los miles del reglamento.

**Aviso de honestidad, medido:** `nutricion` en gold son **3.841 productos y
todos de DIA** (medido). Los nutrientes de OFF están pedidos en
`core/off.py:44`, pero **no comprobado** que lleguen a gold. Si la nota va a
depender de ellos, hay que hacer antes la ficha 10.

**Diseno aqui.**

    no es una ruta aparte: se anade a cada producto de /api/grupo y /api/ean
    (contrato ya escrito en API.md:390-405)

    "nota": {"valor": 72, "de_que": ["nutriscore", "aditivos"],
             "aditivos": 3, "aditivos_riesgo": 0, "ecologico": false,
             "tope_por_aditivo": false}

    "nota": null    cuando no hay con que calcularla (el 77,3 % de los casos)

- Cálculo en `core/calidad.py`, que ya produce `calidad`, `calidad_origen` y
  `calidad_nota`. La tabla nueva va en `core/datos/`.
- Front: `src/paginas/Grupo.tsx` y `src/paginas/Escaner.tsx` — este último ya
  tiene el hueco pintado (`Escaner.tsx:330-339`).

**La regla que la gobierna.** Cuatro leyes, y las cuatro están escritas:

1. **Un dato que no tenemos es "no lo sé", nunca un cero**
   (`API.md:403-405`). `nota: null` es una respuesta, no un fallo.
2. **`calidad` no es `gama`**: se devuelve `calidad` si sale de ingredientes y
   `gama` si sale del precio, **nunca las dos** (`API.md:184-185`). La nota nueva
   es absoluta, así que no puede confundirse con el precio — que es justo el
   problema que arregla (`FUNCIONALIDADES.md:138-146`).
3. **La procedencia se conserva**: `de_que` dice en qué se ha basado
   (`API.md:396`). Y no es un adorno: **Yuka admite por escrito que sus datos
   pueden estar mal** — *"puede haber errores de composición o detección,
   especialmente si la composición de un producto cambia y no se actualiza"*
   (help.yuka.io). Lo que nos separa de ella es que nosotros decimos de dónde
   sale cada número y ella no.
4. **Nuestro contador de aditivos exige "E" + tres o cuatro dígitos**, así que
   **no cuenta los aromas como aditivos** — que es justo el error que la OCU
   documenta en Yuka y MyRealFood. Comprobado: 2 falsos positivos en 400
   productos (`BACKLOG.md:785-789`). **Si se toca `core/calidad.py`, hay que
   volver a comprobarlo.**

**Como se sabe que esta bien.**

- Un producto sin Nutri-Score ni ingredientes devuelve `nota: null` y la app pone
  **"no lo sé"**, nunca un número ni un cero.
- Un producto con un aditivo de riesgo alto **no pasa de 49**.
- **La nota no cambia al cambiar de grupo** — es absoluta: esa es toda la gracia.
- Se conserva `gama` para ordenar dentro de un grupo, y se sigue llamando `gama`.
- El contador de aditivos sigue dando **2 falsos positivos en 400 productos**
  revisados: ni uno más.

**Lo que se descarta.** Copiar la fórmula de GoCoCo (OMS + NOVA + alertas
chilenas). Necesita las **17 categorías del modelo de perfil de nutrientes de la
OMS**, que salen de `categories_tags` de OFF, y hoy no está comprobado que
lleguen a gold. La de Yuka solo necesita lo que ya tenemos.

---

### Ficha 10 · Los nutrientes y los sellos de Open Food Facts hasta gold

**Que es.** Traer de OFF los nutrientes completos y los sellos, que se piden
pero no llegan a la tabla que consulta la app.

**Quien lo hace y como.** No es una app de la competencia: es el dato que sostiene
la nota de la ficha 9 y los filtros. El efecto visible es de apps que sí lo
tienen: Open Food Facts (*"nutrientes, contenido de grasa, ácidos grasos
saturados, hidratos, azúcares, fibra, proteínas y sal"*), OCU Market (sistema de
colores con grasas saturadas, azúcares y sal por 100 g), CodeCheck.

**El dato que hace falta.** Medido, y aquí está el problema:

    sellos               11.823 en gold   -> esto SI funciona
    nutricion             3.841 en gold   -> y los 3.841 son de DIA (medido)
    pedido en el codigo   core/off.py:44 y ss. pide "nutriments"
    no comprobado         si "nutriments" llega a gold

Lo que OFF tiene para dar, según `BACKLOG.md:625-630`: **11.723** con nutrientes
completos, **10.209** con categorías y **8.055** con sellos, de nuestros 12.835
productos que cruzan por código de barras.

**Diseno aqui.**

- `core/off.py`, diccionario `CAMPOS` (línea 33): `nutriments`,
  `categories_tags` y `labels_tags` ya están pedidos. Lo que falta es el mapeo a
  la columna `nutricion` de `core/schemas.py:53`.
- La columna `nutricion` es un JSON con `energia_kcal`, `grasas`, `saturadas`,
  `hidratos`, `azucares`, `fibra`, `proteinas`, `sal`, y `nutricion_por` vale
  `100g` o `100ml` (medido: no hay otros valores).

**La regla que la gobierna.** El origen del dato se dice: `nutricion` de DIA es
**de etiqueta** y lo de OFF es **externo**, y la interfaz ya sabe decirlo porque
lo hace con `sellos_origen` (`API.md:491-494`). Nunca se mezclan sin decir de
dónde viene cada uno.

**Como se sabe que esta bien.**

    uv run pytest tests/test_off.py                  en verde

- `nutricion` en gold pasa de **3.841** a más de **11.000** productos.
- **Los 3.841 de DIA siguen ahí y sin cambios**: traer OFF no puede pisar un dato
  de etiqueta.
- Una prueba comprueba que `nutricion_por` solo vale `100g` o `100ml`: si aparece
  un valor nuevo, sale en rojo en vez de colarse.
- El filtro `con_nutricion` de `/api/buscar` sube de cobertura y **dice cuántos
  se quedaron fuera por no tener el dato**, no por ser malos (`CADENAS.md:74-79`).

**Lo que se descarta.** Mezclar Open Prices en gold. Su licencia es **ODbL**
(*share-alike*): si se mezcla y se publica, hay que publicar la base combinada
como datos abiertos (`COMPETENCIA.md:418-429`). Se puede leer para contrastar un
precio puntual y no se mezcla.

---

### Ficha 11 · El aviso legal y el encabezado de cobertura del escáner

**Que es.** Dos frases obligatorias: la de QueFalta, y la que dice cuántos
códigos reconocemos de verdad.

**Quien lo hace y como.** QueFalta las pone tal cual y son correctas:
*"Los precios son orientativos y pueden variar"* y *"no está afiliada, asociada
ni patrocinada por ninguno de estos supermercados"* (`COMPETENCIA.md:35-37`).
RadarSuper lo dice en su web con las mismas palabras. Y las dos apps de escáner
más serias ponen la misma advertencia sobre la etiqueta: Open Food Facts app
(*"tenga cuidado porque la información puede no ser 100 % precisa... compruébelo
usted mismo siempre con el embalaje"*) y **Yuka** (*"no sustituye la información
presente en el envase del producto... consulta siempre la información que figura
en la etiqueta, incluso si utilizas la función de 'Preferencias alimentarias'"*).
Que las dos lo digan es la mejor prueba de que hay que decirlo.

**El dato que hace falta.** Ninguno, es texto. Pero los números que acompañan a
la segunda frase están medidos:

    productos con codigo de barras        25.517   count(ean)
    de esos, codigos distintos            23.759   count(DISTINCT ean)
    ... que llegan a 2 o mas cadenas      11.613   (48,9 % de los codigos distintos)
    ... cuyo grupo trae nutricion         12.008   count(DISTINCT ean)
    Alcampo y Aldi no publican EAN        el 50 % del catalogo (CADENAS.md:54-56)

Las tres cifras de codigos van en la misma unidad -- **codigos distintos**, no
productos -- y salen de la misma consulta con filtros distintos. Las condiciones
exactas estan en el punto 0.

**Diseno aqui.**

- Front: `src/paginas/Ajustes.tsx` y una línea pequeña bajo el total de la lista
  en `src/paginas/Cesta.tsx`. El texto exacto ya está redactado en
  `PANTALLAS.md:304-307`, con una frase más que ya estaba pensada: *"Los datos
  viven en el ordenador de casa y no salen de ahí"* y *"Información nutricional de
  Open Food Facts, bajo licencia ODbL"*.
- En el escáner: la frase de cobertura va **antes** del resultado, no en letra
  pequeña debajo (`Escaner.tsx:189-199` ya tiene el hueco del aviso de
  `BarcodeDetector`).

**La regla que la gobierna.** *"Una app de precios que muestra precios viejos sin
decirlo es peor que no tener app"* (`APP.md:162-163`). Aquí es lo mismo con la
cobertura: **decir "no lo sé" cuatro de cada cinco veces no es un fallo, es el
dato** (`COMPETENCIA.md:144-146`), y taparlo sería vender una precisión que no
tenemos.

**Como se sabe que esta bien.**

- El aviso legal se ve en Ajustes y bajo el total de la lista.
- El escáner dice, antes de buscar, que la marca propia de Alcampo y Aldi no
  tiene código de barras y no la va a encontrar (`CADENAS.md:54-63`).
- `uv run pytest tests/test_interfaz.py` en verde.

**Lo que se descarta.** Un aviso de cookies, un banner de consentimiento y un
"acepto" al abrir. Aquí no hay cookies de terceros ni analítica: un banner sería
mentira (`PANTALLAS.md:314-324`).

---

### Ficha 12 · Historial de escaneos

**Que es.** Lo que has escaneado, en orden, para volver a ello.

**Quien lo hace y como.** Yuka (*"historial de lo escaneado con código de color"*),
Open Food Facts app (*"puede exportar su historial de escaneo"*). OCU Market lo
tiene pedido por sus usuarios: *"otra mejora sería que conservase el historial de
los productos escaneados"*.

**El dato que hace falta.** Ninguno nuevo: hace falta guardar qué se ha escaneado.
Es una tabla en PostgreSQL, la mitad de escritura del sistema
(`MODELO.md:57-70`).

**Diseno aqui.**

- Tabla nueva, con la misma forma que `favorito`
  (`plataforma/sql/001_esquema.sql:114-118`):

      escaneo      usuario_id, grupo_id, producto_id, ean, escaneado_en

- Ruta: `GET /api/escaneos?limite=50`. Se escribe desde `GET /api/ean/{codigo}`
  **solo si hay sesión**: un escaneo anónimo no se puede guardar.
- Front: una sección en `src/paginas/Escaner.tsx`, debajo del resultado.

**La regla que la gobierna.** Sin sesión no se guarda nada, y la pantalla **no
promete** un historial que no va a existir. Cero datos personales más allá de
quién escaneó qué en su propio PC (`README.md:56`).

**Como se sabe que esta bien.**

- Escanear con sesión y volver a la pantalla: el producto está en la lista.
- Escanear **sin** sesión: no se guarda nada y no se pide que entres.
- `uv run pytest tests/test_cesta_api.py` en verde, con un caso que pida
  `/api/escaneos` sin sesión y espere **401**.

**Lo que se descarta.** Exportar el historial, como hace Open Food Facts. Es un
fichero que hay que mantener y nadie lo va a abrir.

---

### Ficha 13 · Cerrar la compra

**Que es.** Un botón "he terminado la compra" que guarda lo que iba en el carro.

**Ya está en el BACKLOG como tarea 10** (`BACKLOG.md:802-823`). La ficha no la
repite: añade por qué va **antes** de lo que parece, y de qué depende.

**Quien lo hace y como.** No lo hace ninguna app de lista; lo que sí existe es el
**ticket digital** de las cadenas (Mi Carrefour "Papel Cero", Mercadona por
WhatsApp, BM con el 54 % de sus usuarios de app usándolo). Esto es la versión que
sí podemos hacer: no leer el ticket, sino **acordarse de lo que se cogió**.

**El dato que hace falta.** `lista_linea.en_carrito`
(`plataforma/sql/002_invitaciones.sql:35`) y `tachado_en`. Nada nuevo que bajar.
Lo que sale de aquí **alimenta cuatro fichas de este documento**: la despensa
deducida, el aviso de caducidad, el control de gasto y las estadísticas de la
casa. Sin ella, en diciembre no habrá historial que mirar (`BACKLOG.md:804-807`).

**Diseno aqui.**

    POST /api/listas/{id}/cerrar    contrato en API.md:409-417
    GET  /api/compras
    GET  /api/compras/{id}

    compra        id, lista_id, cerrada_por, cerrada_en, cadena_elegida,
                  total_estimado_cent
    compra_linea  compra_id, grupo_id, producto_id, cantidad, precio_cent

- Front: botón en `src/paginas/Cesta.tsx`.

**La regla que la gobierna.** **Idempotente por lista y minuto**: pulsar dos veces
no crea dos compras (`API.md:417`). Y el precio se guarda **como estaba ese día**:
si mañana cambia, la compra de ayer no cambia — igual que la regla de que cada
precio lleva su fecha (`APP.md:147-163`).

**Como se sabe que esta bien.**

- Cerrar una compra vacía la parte "en el carro" y deja "por coger".
- Cerrar dos veces seguidas no duplica.
- El historial queda consultable en `/api/compras`.
- `uv run pytest tests/test_lineas_api.py` en verde.

**Lo que se descarta.** Deducir la compra sola sin pulsar nada, cuando la lista
lleva días sin tocarse. Adivinar mal es peor que preguntar: una compra inventada
envenena todo el historial que sale de aquí.

---

### Ficha 14 · La despensa deducida

**Que es.** Saber qué hay en casa **sin que nadie teclee un inventario**: se
deduce de lo que se cerró en cada compra.

**Quien lo hace y como.** NoWaste, KitchenPal, CozZo y FridgeBuddy piden el
inventario a mano. La idea de deducirlo no la hace nadie
(`COMPETENCIA.md:244-248`). El problema real de la categoría está medido: **NoWaste,
la más citada, tiene 2,8★ en Google Play**, y KitchenPal movió la adición manual
de productos detrás del pago. Las apps de despensa se abandonan porque meter el
inventario es trabajo.

**El dato que hace falta.** La **ficha 13**, y unos meses de uso. Nada más.

**Diseno aqui.**

- Sin ruta nueva al principio: la despensa es una consulta sobre `compra_linea`
  agrupada por `grupo_id`, con la fecha de la última vez.
- Cuando pida tabla propia, la forma es la misma que `favorito`: `usuario_id o
  casa`, `grupo_id`, `cantidad_estimada`, `visto_en`.
- Front: `src/paginas/Cesta.tsx` (lo que ya tienes en casa, marcado en la lista)
  y una pantalla nueva cuando haya algo que enseñar.

**La regla que la gobierna.** *"Un dato que no tenemos es 'no lo sé'"*: si no hay
compras cerradas, **no hay despensa**, y la pantalla no la inventa a partir de
los favoritos ni de "lo que suele comprar la gente".

**Como se sabe que esta bien.**

- Cerrada una compra con 5 líneas, la despensa tiene 5 líneas y sus fechas.
- Con **cero** compras cerradas, la despensa está vacía y **la pantalla no
  aparece** en vez de salir en blanco.
- La despensa **no** cambia al cambiar un precio: es "qué hay", no "cuánto vale".
- `uv run pytest` en verde y una prueba nueva que verifica las dos primeras.

**Lo que se descarta.** Pedir el inventario a mano, aunque sea "un poco". Es lo
que hace que estas apps se abandonen (`FUNCIONALIDADES.md:241`), y el 20 % que
deducimos solos aporta el 80 % del valor (`COMPETENCIA.md:244-248`).

---

### Ficha 15 · Aviso de caducidad

**Que es.** "Se compró hace 12 días, dura 15, se acaba el viernes."

**Quien lo hace y como.** NoWaste (*"ordene sus alimentos por fecha de caducidad"*,
con hasta dos recordatorios por producto), KitchenPal (*"recibe alertas antes de
la fecha de caducidad"*), Mi despensa (el artículo cambia de color según su
fecha), CozZo, que **distinguía "Best By" de "Use By"** — y Smantry lo distingue
también. Esa distinción no es un detalle: **la ley española separa fecha de
consumo preferente y fecha de caducidad**, y casi ninguna app lo hace.

**El dato que hace falta, y aquí está el límite.** `dias_caducidad` **solo lo
publica DIA**: **4.382 productos de 52.567, el 8,3 %** (medido). El proyecto ya lo
sabía y lo escribió: *"`dias_caducidad` entero. **Nadie más publica esto**"*
(`COLECTORES.md:47`), y *"es el único campo del proyecto que ninguna otra app
tiene"* (`COLECTORES.md:55-62`).

**Es decir: el aviso solo puede funcionar en uno de cada doce productos.** Eso
no lo descalifica, pero **se dice en pantalla**, igual que el escáner dice su
cobertura.

**Diseno aqui.**

- Sin ruta nueva: el aviso es una resta — `compra_linea.cerrada_en` + `dias_caducidad`
  del grupo.
- Front: en `src/paginas/Cesta.tsx`, una etiqueta discreta en las líneas que lo
  tengan. En la despensa, ordenado por lo que caduca antes.
- **Lo que no tenga `dias_caducidad` no lleva etiqueta**, y no se estima por
  sección ("los lácteos duran 7 días" es un dato inventado).

**La regla que la gobierna.** Nada de campos vacíos **ni de campos rellenados a
ojo**: `README.md:57` pide que ningún campo quede vacío, pero la ley que manda
aquí es la de `API.md:37` — lo que no sabemos es `null`, y la interfaz dice "no lo
sé". Estimar una caducidad por categoría sería exactamente el dato inventado que
el proyecto prohíbe.

**Como se sabe que esta bien.**

- Un producto de DIA cerrado hace 12 días con `dias_caducidad = 15` avisa.
- Un producto de Mercadona **no avisa**, y en su ficha se lee por qué: *"solo DIA
  publica los días de caducidad"*.
- **La cobertura está en pantalla**: se dice sobre cuántas líneas se puede avisar.
- `uv run pytest tests/test_dia_nutricion.py` y `tests/test_colectores.py` en verde.

**Lo que se descarta.** Que el usuario escriba la fecha de caducidad a mano.
Es convertir la función en trabajo, y es justo lo que hace que las apps de
despensa se abandonen. También se descarta el **escaneo de la fecha** que hace
NoWaste: es reconocimiento óptico sobre un troquelado, el peor texto posible.

---

### Ficha 16 · Control de gasto

**Que es.** Cuánto llevas gastado este mes en la compra, con el detalle por
compra.

**Quien lo hace y como.** Your Food (*"guarda lo que pagaste y mira cómo se
acumulan tus gastos... gráficos por semana, mes o año"*), BM (*"Ahorrando mes a
mes"*), FamilyWall (presupuesto con límites por categoría, de pago), Listonic
(*"budget control — total cost calculator"*), Mi Carrefour (ChequeAhorro, con
cupones).

**El dato que hace falta.** La **ficha 13**. La tabla `compra` que hay que crear
lleva `total_estimado_cent` y `compra_linea` lleva `precio_cent`
(`BACKLOG.md:809-813`).

**Diseno aqui.**

- `GET /api/compras?desde=&hasta=` devuelve las compras con su total; la suma la
  hace el cliente.
- Front: una tarjeta en `src/paginas/Cesta.tsx` y, cuando haya meses de datos,
  una pantalla propia.

**La regla que la gobierna.** El total de una compra pasada es **lo que se estimó
ese día**, no lo que costaría hoy. Se enseña con su fecha, como todo precio
(`APP.md:147-163`). Y **no se llama "ahorro"**: no sabemos lo que habrías gastado
en otra tienda, así que no se inventa una cifra de ahorro.

**Como se sabe que esta bien.**

- Dos compras suman bien y el total es la suma de sus `total_estimado_cent`.
- El total de una compra **no cambia** cuando cambian los precios de hoy: se
  comprueba cerrando una compra, forzando un precio distinto en gold y volviendo
  a mirar.
- La pantalla dice en cuántas compras se basa el número.
- `uv run pytest tests/test_cesta_api.py` en verde.

**Lo que se descarta.** La calculadora "cuánto puedes ahorrar al año" de CozZo.
Es una proyección sobre datos que no tenemos, y la OCU ya critica ese tipo de
cifra cuando no se puede sostener.

---

### Ficha 17 · Una bajada estructural no es una oferta

**Que es.** Al decir "ha bajado", decir **por qué**: si es una promoción puntual
que puede acabar el domingo, o si el producto **ha bajado de verdad** y se queda
ahí.

**Quien lo hace y como.** **Ahorramercado** es el único que lo separa, y lo hace
en dos secciones con nombre propio: *"🏷️ Ofertas — promoción puntual con precio
anterior, puede acabar pronto"* frente a *"📉 Bajadas de precio — caída
estructural... no es una oferta puntual"*. **SuperPrecios** va por la otra mitad:
en su curva marca *"en qué fechas estuvo de oferta"*, con el estado **Normal |
Oferta** por tramo. Se usa así: miras el producto, ves que ha bajado un 20 %, y
lo que quieres saber es si esperas al sábado o lo compras hoy.

**El dato que hace falta.** **Ya está calculado, en `precio_derivado.parquet`**
(medido). Las cuatro primeras son **booleanas**, así que se cuenta el valor
verdadero y lo que sale son **filas (producto × día)**, entre paréntesis los
productos distintos:

    ha_bajado              8.752 filas   (8.124 productos)
    promo_empieza          4.854 filas   (4.808 productos)
    promo_acaba            1.571 filas   (1.569 productos)
    promo_inferida        23.335 filas   (4.808 productos)
    descuento_real         407.678 filas
    precio_base_cent       la mediana movil: el "precio de siempre"
    posicion_90d           donde esta hoy dentro de los ultimos 90 dias

Las consultas exactas estan en el punto 0. **Ojo**: `WHERE promo_empieza IS NOT
NULL` casa con las 763.042 filas, porque una booleana nunca es NULL.

No hace falta bajar nada nuevo ni calcular nada nuevo: **es cruzar dos columnas
que ya existen y nadie ha puesto una al lado de la otra** — exactamente el mismo
patrón que `MOVIMIENTOS.md:8-12` describe para las bajadas.

**Diseno aqui.**

- Sin ruta nueva al principio: `GET /api/bajadas` y `GET /api/ofertas-dudosas`
  (`plataforma/api/main.py:205` y `:225`) ya leen `precio_derivado` en
  `movimientos.py`. Basta con añadir a cada fila un campo `motivo_de_la_bajada`.
- La regla, escrita antes de programarla:

      estructural   precio_unidad_cent < precio_base_cent  Y  posicion_90d baja
                    Y  NO hay promo_txt ni promo_hasta vivo
      puntual       precio_unidad_cent < precio_base_cent  Y  promo vivo
                    (promo_hasta en el futuro, o promo_empieza reciente)
      dudosa        precio_unidad_cent >= precio_base_cent  Y  promo_txt existe
                    -> es lo que ya devuelve /api/ofertas-dudosas

- Front: `src/paginas/Panel.tsx` (pestaña Bajadas) y `src/paginas/Grupo.tsx`
  (la serie de la ficha), que ya pinta la chispa del histórico.

**La regla que la gobierna.** **Una oferta es una regla, no un precio**
(`BACKLOG.md:435-437`), y **los descuentos de tarjeta no bajan el ticket**: por eso
`promo_club` (**1.899** productos, medido) tiene que excluir la fila de
"puntual", no contarla. Y una bajada **solo lo es** si la unidad es la misma, la
cantidad es la misma y el precio de venta se movió en el mismo sentido — las tres
condiciones que `MOVIMIENTOS.md:40-51` ya tuvo que poner porque, sin ellas, salían
ocho productos de Alcampo a exactamente **−96,7 %** que no habían bajado nada.

**Como se sabe que esta bien.**

    uv run pytest tests/test_movimientos.py tests/test_resumen.py    en verde

- Un producto con **3x2** vivo y precio igual al de siempre **no** sale como
  bajada estructural: sale como oferta puntual.
- Un producto que bajó y lleva dos semanas bajo, sin promoción, sale como
  **estructural**.
- Un producto con "Club Alcampo … acum en tu tarjeta" **no** cuenta como bajada.
- **Ninguna fila sale con las dos etiquetas a la vez**, y ninguna sale sin
  etiqueta cuando `ha_bajado` es verdadero.
- El caso de los **−96,7 %** no reaparece: la variación que cambia es de más de
  30 veces y se descarta.

**Lo que se descarta.** Enseñar la curva con los tramos de promoción pintados,
como SuperPrecios. Es bonito, pero con los días de histórico que tenemos la
curva cabe en un dedo, y `promo_empieza`/`promo_acaba` dan la misma información
en una frase.

---

## 3. Lo que la competencia hace y aquí **no se puede** hacer

Esta es la sección que sirve para no volver a discutirlo. Cada línea lleva el
motivo y **la medida**.

### 3.1 No se puede porque el dato no existe

**Gastos de envío en la comparación** (Soysuper). *Motivo*: no compramos online y
la comparación es entre lineales de tienda. *Medida*: `grupos.parquet` tiene **53
columnas y ninguna de envío** (medido); y `COMPETENCIA.md:400-402` ya decidió que
somos una app para **ir a la tienda**.

**Cupones y descuentos personalizados** (Mi Carrefour, Lidl Plus, DIA, Tiendeo).
*Motivo*: la cadena los calcula sobre tu ticket y **no los publica en ningún
sitio**. *Medida*: ninguna de las cinco cadenas expone un campo de descuento
personalizado; lo que sí publican es el texto de la promo, que está en `promo_txt`
y solo en Alcampo (12 %) y Aldi (8 %) (`CADENAS.md:42`).

**ChequeAhorro: en qué has ahorrado** (Mi Carrefour). *Motivo*: se calcula sobre
el ticket, que no tenemos.

**Ticket digital guardado** (Mi Carrefour, Mercadona, BM, DIA, EROSKI). *Motivo*:
lo emite la cadena y no hay API pública. *Medida*: **`API.md:427`** — *"no guarda
datos de pago ni direcciones"*. La puerta, si algún día se abre, es el ticket
digital de la cadena y no una foto (`FUNCIONALIDADES.md:243-247`).

**Escaneo de tickets por foto** (NoWaste, KitchenPal, CozZo, FridgeBuddy,
FridgeTrack, Woolsocks). *Motivo*: es reconocimiento óptico sobre papel arrugado,
con un formato distinto por cadena, y **se rompe cada vez que alguien cambia el
diseño del ticket** (`FUNCIONALIDADES.md:243-247`).

**Reconocimiento por foto de alimentos** (NoWaste, KitchenPal, FridgeTrack).
*Motivo*: mismo problema, y encima hay que casar el resultado con el catálogo,
que es el problema del emparejador otra vez.

**Folletos digitales y catálogos** (Tiendeo, Ofertia, Flipp, RadarSuper). *Motivo*:
son **imágenes en PDF**, no datos. Leerlos es reconocimiento óptico, con el mismo
problema que el ticket. *Medida*: no hay ningún colector de folletos y `data/raw`
solo tiene las cinco cadenas. RadarSuper, que **sí** los usa, reconoce que de Aldi
y Lidl *"solo vigilamos folletos y novedades"* porque no publican precios online
(radarsuper.com/metodologia) — exactamente lo que comprobó `LIDL.md`.

**Mapa de tiendas, horarios y geolocalización de la tienda más cercana** (Findit,
Tiendeo, OCU Market). *Motivo*: no tenemos **ni una columna de tienda ni de
dirección**. *Medida*: las 53 columnas de `grupos.parquet`, ninguna de tienda
(medido). Es un catálogo de tiendas físicas, otro trabajo de datos entero.

**Valoraciones de clientes** (EROSKI las publica; `EROSKI.md`). *Motivo*: el dato
existe **en una sola cadena** y esa cadena no está bajada. *Medida*: cero columnas
de valoración en `grupos.parquet` (medido).

**Comparar con el IPC oficial** (RadarSuper, Precios del Super). *Motivo*:
descartado a propósito: *"interesante, pero es otro proyecto"* (`APP.md:404`).

**Filtro de "producto nacional"** (lo pediste tú; no lo tiene ninguna app).
*Motivo*: el techo realista es **1.900 de 51.781, el 3,7 %** (`CADENAS.md:95`).
BEDCA no lo arregla: describe alimentos genéricos, no productos con código de
barras (`BACKLOG.md:639-642`).

**Escáner de la marca propia de Alcampo y Aldi** (ninguna app puede). *Motivo*:
**no publican código de barras**. *Medida*: `CADENAS.md:31` da EAN **0 % en
Alcampo y 0 % en Aldi**, y son **25.638 de 51.781 productos, el 50 % del
catálogo** (`CADENAS.md:54-56`). Y a diferencia de un producto de fabricante,
aquí no hay ninguna otra cadena donde casar el código.

**Comparar un producto que solo está en una cadena.** *Motivo*: no hay con qué.
*Medida*: **32.486 de 51.781 productos, el 63 %, no tienen con quién compararse**
(`APP.md:122-124`). La app **no debe inventarse una comparación**
(`APP.md:123`).

**"Hay uno mejor y además más barato".** *Motivo*: los grupos son demasiado
anchos, y sacarlo antes sería peor que no sacarlo. *Medida propia, de hoy*: lo
cumplen **168 grupos** (`comparacion_fiable`), y mirando el grupo **92** —
"*Cerveza sin alcohol*", **84 productos de las 5 cadenas, de 84,85 a 509,09
céntimos por litro** — se ve que la cifra mide la anchura del grupo y no el
ahorro. Hay **259 grupos con dispersión mayor de 3×** entre su miembro más barato
y el más caro (medido). Es el bloqueo número uno y sigue siéndolo
(`BACKLOG.md:409-411`).

### 3.2 No se puede porque hay que ser la cadena

**Pago con QR y pago móvil** (Mi Carrefour; en El Corte Inglés solo consta en
prensa de feb-2023). **Escáner y pago sin pasar por caja** (Club Alcampo,
**AutoScan**, ~40 tiendas). **Canje en caja por NFC** (Mundo Consum, y **solo
Android**). *Motivo*: hace falta su TPV y su sistema de caja
(`FUNCIONALIDADES.md:242`).

**Puntos y recompensas personalizadas** (Lidl Plus, Club Alcampo, BM).
**Tarjetas de fidelización guardadas** (Bring!, Tiendeo, Flipp).
**Devolución en efectivo por el ticket** (Woolsocks, Gelt, PROMOS, La Cuponera).
*Motivo*: hay que tener el programa de fidelización, o los datos personales de
otro; y en el caso del cashback, **pagar de verdad**: cobrar, validar el ticket y
transferir, con acuerdos de marca detrás. *Medida y motivo escrito*: son datos
personales, algunas dan acceso a saldo, y solo ahorran abrir la cartera
(`FUNCIONALIDADES.md:239`).

**Seguimiento de pedido, lista desde el folleto** (BM, Mi Carrefour). *Motivo*:
dependen del pedido, y no compramos online.

### 3.3 No se puede porque necesita otra cosa que no somos

**Comprar online con entrega.** *Motivo*: *"cambia el producto entero"*
(`COMPETENCIA.md:400-402`).

**"Enviar al supermercado"** (Soysuper). *Motivo*: automatizar una compra en la
web de la cadena en nombre del usuario. *Medida*: no hay API ni sesión del
usuario en la cadena, y automatizarla sería automatizar un login ajeno
(`FUNCIONALIDADES.md:248-249`).

**Cupones verificados contra el feed de la tienda** (Comparaloo, Flipp).
*Motivo*: exige un acuerdo de afiliación con cada comercio. Comparaloo lo dice:
sus precios de tiendas de afiliación entran *"por su propio feed"*.

**Packs de excedente de comercios** (Too Good To Go, Phenix, Coometas).
*Motivo*: es un marketplace de dos lados: sin comercio que publique, no hay
oferta. Too Good To Go capta **puerta a puerta** y tiene **20.000 negocios en
España**; eso no se programa, se vende. Además exige cobro y pago.

**Comunidad de intercambio entre vecinos** (OLIO). *Motivo*: es una red social,
no un dato. Y **no hay evidencia de operación activa en España** (OLIO funciona
globalmente y tiene la interfaz en español, pero la única alianza documentada es
británica).

**Recomendaciones de "productos mejores" de otra categoría** (Yuka, GoCoCo).
*Motivo*: es exactamente lo que la **OCU le critica a Yuka**: proponer productos
de otra categoría en vez de comparables (`COMPETENCIA.md:131-137`). Nosotros solo
podemos proponer **dentro del grupo**, y eso está bloqueado por los grupos anchos.

**Producto verificado por una asociación de pacientes** (sinGLU10, ACySG: 19.000
productos contrastados *"tras consultar al fabricante y revisar los certificados"*).
*Motivo*: eso no lo da ninguna cadena. Es otro trabajo de datos, con llamadas a
fabricantes, y no lo vamos a hacer.

**Planificador de comidas e IA que aprende tu compra** (AnyList, OurGroceries con
**MCP**, Samsung Food, CozZo). *Motivo*: sin recetas casadas con el catálogo, un
planificador no dice nada útil, y ese casado es el problema del emparejador.

**Asistencia por voz de casa (Alexa, Google, Siri)** (AnyList, Bring!,
OurGroceries, sinGLU10). *Motivo*: necesita nube y cuenta de terceros, y choca
con la decisión central de que **los datos se quedan en casa** (`APP.md:56-76`).

**Notificaciones push y avisos por correo.** *Motivo*: *"necesitan servidor
siempre accesible y el PC se apaga"* (`FUNCIONALIDADES.md:253`). Comparaloo puede
mandar correo porque tiene servidores; nosotros no, y además el correo saca de
casa qué vigilas.

**Widget nativo y app nativa** (Listonic, AnyList, Bring!). *Motivo*: hoy somos
una web servida por Caddy; un widget pide app nativa y eso es otro proyecto
(`FUNCIONALIDADES.md:224-228`).

**Modo sin conexión completo.** *Motivo*: descartado a propósito, con tres
razones escritas (7 MB al día, listas sin compartir, el panel no cabe)
(`APP.md:56-76`).

**Publicidad y patrocinio.** *Motivo*: *"ni ahora ni nunca: el día que un producto
suba en la lista por dinero, la app deja de servir para lo que se hizo"*
(`PANTALLAS.md:323-324`).

**API pública de precios para terceros** (Comparaloo la tiene). *Motivo hoy*: la
API solo se sirve por Tailscale y **no está abierta** (`APP.md:343`).
*Condición*: el día que se publique, hay que resolver antes la licencia de Open
Food Facts (ODbL, hay que citarla), las condiciones de uso de las cadenas y la
protección de datos (`APP.md:406-408`).

### 3.4 Correcciones a `docs/COMPETENCIA.md`, porque las apps cambian

Esto no es "no se puede hacer": es **lo que ya no es verdad** en el documento del
18 de septiembre, y conviene saberlo antes de citarlo.

| Lo que dice `COMPETENCIA.md` | Lo que hay hoy | Fuente |
|---|---|---|
| FindItApp: *"Fuerte en Levante y Cataluña, con Consum, BonPreu y Caprabo"* (`COMPETENCIA.md:408-411`) | Su ficha de Play dice: **Mercadona, Carrefour, Consum, DIA, Masymas, Hiperber, BM y Eroski**, más gasolineras. En su web solo hay **6** (`/supermercado/{mercadona,carrefour,alcampo,consum,dia,caprabo}`). Sus pantallas son "**Para ti**", "**Reporte de Precios**", "**Findit IA**", "Categorías" y "Gasolineras". 3,7★, 10 mil+ descargas, última actualización **11 sept 2025**. **No tiene app de iOS** (0 resultados en la App Store española) | `play.google.com` `com.finditapp` + fichas de iTunes con `country=es` |
| Precios del Super: *"10 cadenas"* (`COMPETENCIA.md:518`) | Su portada dice **8 supermercados** y "+120K productos"; su `/comparador` dice **9**. Sus pantallas reales están en el sitemap: `/cambios`, `/subidas`, `/bajadas`, `/nuevos`, **`/descatalogados`**, `/escanear`, `/ipc`, `/comparador`. **Su app es solo de Android**, con **100+ descargas**, y la web solo invita a Android | preciosdelsuper.es, `sitemap-static.xml` |
| RadarSuper cubre Lidl (dudado en `COMPETENCIA.md:509-514`) | **Confirmado por ellos mismos**: de Aldi y Lidl *"solo vigilamos folletos y novedades"* porque **no publican precios online**. Nuestra decisión de `LIDL.md` queda ratificada por un tercero. Y su metodología declara **hasta tres años de histórico** en PostgreSQL | radarsuper.com/radar y /metodologia |
| RadarSuper, planes de pago | Los tres planes están **anunciados pero el cobro no está operativo**: *"Pago seguro mediante Stripe (próximamente)"*. Free 0 €, Plus 3,99 €/mes (alertas ilimitadas, histórico completo, simulador de sueldo y cesta, exportar listas), Pro 9,99 €/mes (+ chat IA, análisis nutricional, API básica). **Solo web: no tiene app** | radarsuper.com/planes |
| Soysuper es "el comparador de cesta español" | **La web sigue viva y mantenida** (9 cadenas, *"más de 150.000 productos... en más de 4.700 códigos postales"*, blog activo en julio de 2026, y negocio B2B de datos). **Sus apps están degradadas**: la de iOS es la 5.1.5 del **14/04/2025** con **2,5★/60**, y la de Android no se toca desde el **23 nov 2023** y tiene **2,3★/430**. Las reseñas de agosto y septiembre de 2026 dicen literalmente **"NO FUNCIONA"**. **No documenta curva de histórico** | blog.soysuper.com + fichas de ambas tiendas |
| PrecioReal (precioreal.com) es "verificador de ofertas e histórico" **de supermercado** | **No es de supermercado**: es un verificador de **tiendas online** (eje Amazon), y su web lo dice: *"para comprobar precios y comparar ofertas de productos de tiendas online"*. **Amazon le ha exigido retirar sus gráficas de historial de precios.** Tiene **extensión de Chrome y addon de Firefox** — que es lo que a nosotros nos interesa de él | precioreal.com `llms.txt` + su bundle JS |
| PreciRadar (`COMPETENCIA.md:545-548`, "se apunta y ya") | **Ha muerto.** El dominio **expiró**: el DNS apunta a un *lander* de parking y la respuesta es *"Domain registration has expired."* Última captura con 200: **16 may 2026**. **Cuidado: los buscadores siguen devolviendo sus URLs con títulos correctos**, son entradas obsoletas del índice | DNS + Wayback Machine |
| supermarket-tracker: *"Mercadona, Carrefour y Consum... y una extensión de Chrome"* (`COMPETENCIA.md:550-564`) | El scraper sí era de 3 cadenas, pero **su extensión solo se inyecta en Mercadona**: `"matches": ["https://tienda.mercadona.es/*"]`, y su ficha de la Chrome Web Store lo confirma (*"Actualmente solo funciona con Mercadona. Próximamente Consum y Carrefour"*). **El repositorio está abandonado desde el 3 feb 2023** y la extensión es la 0.1.0 del 4 feb 2023 | API de GitHub + `extension/manifest.json` |
| Ofertia (comparador de folletos) | **`ofertia.com` redirige a `tiendeo.com`**: Ofertia fue absorbida por Tiendeo (Shopfully). Y **ojo**: `ofertia.es` es un sitio **distinto y sin relación**, de captación de luz y gas | redirección comprobada en vivo |
| Yuka: fórmula del 60/30/10 | **Confirmada y ampliada**: hay cuatro niveles de riesgo por aditivo (verde, amarillo, naranja, rojo) y **tope de 49/100** con uno rojo. Premium añade búsqueda avanzada, modo sin conexión y **avisos por dieta** (vegetariana, sin palma, sin gluten, sin lactosa, sin cerdo, sin soja, sin sulfitos) | help.yuka.io |
| El CoCo | Hoy es **GoCoCo** y ha girado a **diabetes tipo 2 y pérdida de peso**. Puntuación 0–10 con fórmula publicada: OMS + NOVA + alerta chilena | gococo.app/es/puntuacion-gococo |
| NoWaste y KitchenPal | Siguen vivas. **NoWaste tiene 2,8★ en Play**: es la prueba de que la categoría se abandona. **CozZo, que tenía todas las funciones, cerró** el 30 dic 2025 por depender de su propia nube | play.google.com Play + aviso de fin de vida de CozZo |
| MyRealFood es una app de análisis de comida | Hoy vende otra cosa: **escáner con IA**, un **"Real Score"** semanal, plan nutricional, +160.000 recetas, entrenamientos con Synergym, comunidad y **una tienda propia dentro de la app** ("Tienda Realfooding"). 4,4★, 1 M+ descargas, actualizada el **31 ago 2026** | `play.google.com/store/apps/details?id=es.myrealfood.myrealfood` |
| Carritus (comparador de supermercados "nº1") | **Muerto.** Sin registro DNS desde hace años; su última web real en Wayback es del **30 nov 2020**, y su última captura con 200 también. Era de 9 cadenas y decía *"fotos del 99 % de los productos"* | DNS + Wayback Machine |
| Yuka, sobre sus propios datos | **Lo admite ella misma**: *"los datos presentados dependen de la información disponible en el envase... añadidos por contribuyentes o fabricantes. A pesar de las verificaciones... **puede haber errores de composición o detección**, especialmente si la composición de un producto cambia y no se actualiza"*. Y añade: *"consulta siempre la información que figura en la etiqueta"* | help.yuka.io, "¿Cuáles son las limitaciones de Yuka?" |
| Yuka, cuando no hay alternativa buena | **No inventa una**: *"si no se ofrece ninguna recomendación para un producto calificado como mediocre o malo, es que lamentablemente no hemos logrado encontrar ninguna alternativa que sea buena"* | help.yuka.io, "¿Por qué algunos productos no tienen recomendaciones?" |
| Flipp (nueva, folletos) | **No está disponible en España**, confirmado por ellos: *"Flipp is available in Canada & the United States"* | help.flipp.com |
| Samsung Food / Whisk (nueva, recetas) | Sus **supermercados integrados son Australia, Alemania, Reino Unido y Estados Unidos. España no está** | artículo oficial "Integrated Stores" |
| *"Mi DIA"* y *"MiBM"* | No existen con esos nombres. Son **"Supermercados Dia"** (`es.dia`) y **"BM Supermercados"** (`com.uvesco.bm`) | búsqueda negativa en Play y App Store ES |
| Ahorramas, Froiz | **Ninguna de las dos tiene app de cliente.** Ahorramas solo tiene `com.ahorramas.intranet`, que es de empleados (23 nov 2023) | búsqueda negativa en dos tiendas + su web |
| Shopmium (cashback por ticket) | **No opera en España**, contra lo que parece al ver su ficha de Play traducida. `shopmium.com/es` da **404** y **nunca existió** (0 capturas en Wayback); su centro de ayuda en español tiene **cero artículos**; dice *"más de 9 millones de personas en el **Reino Unido, Francia y Bélgica**"*; y **no tiene ficha en la App Store española**, mientras es la primera en Reino Unido, Francia y Bélgica. Quien ocupa ese hueco aquí: **Woolsocks, Gelt, PROMOS y La Cuponera** | `shopmium.com` + API de iTunes con `country=es` |
| CodeCheck (aditivos) | **No está en España** y **no usa Nutri-Score ni NOVA**. Su ficha de la App Store española da **404**; la búsqueda de iTunes devuelve **cero resultados** en `es`, `fr`, `gb`, `us` e `it`, y sí en `de`, `ch`, `at` y `nl`. Su nota es un **"Bewertungskreis"** propio con pesos publicados: *"50 % de la evaluación de los nutrientes y 50 % de la evaluación de los ingredientes"* | API de iTunes por país + codecheck.info/info/bewertungskreis |
| *"FACEMÓVIL"* (la app de los celíacos) | **Se llama CELIGUIA** desde el 24 abr 2026. FACE lo explica: *"cambiamos el nombre de la app **por motivos legales**, básicamente, derechos de registro de marca. El cambio es solo de nombre"*. Lector de código de barras sobre los **16.000 productos** de su Lista digital, y **5.000 establecimientos**. Es **exclusiva para socios** y tiene **1,9★ en Play** | celiacos.org + ficha de Play `com.face.facemovil` |
| Google Shopping como comparador | **Su app cerró en 2021** (ficha de Play 404) y **no hay fuente sólida** de que compare alimentación o cesta en España: es un servicio de comparación que exige el *feed* de cada comerciante, y las cadenas sin precios online no pueden alimentarlo | support.google.com/merchants + ficha de Play |
| PriceRunner, Buycott (comparadores de escáner) | **PriceRunner no opera en España** (paquete `com.pricerunner` → 404; es nórdico). **Buycott** no compara precios, es de pago (1,99 €), solo iOS y fuera de Google Play. **RadaRprice** parece muerto (el dominio no resuelve) | fichas de tienda + búsqueda negativa |

---

## 4. El orden propuesto

Ordenado por **valor partido por coste**, y diciendo qué desbloquea cada paso.

**Nada de esta lista arregla el bloqueo número uno.** Los grupos demasiado anchos
(`BACKLOG.md:409-411`) siguen siendo lo primero, y bloquean tres cosas de aquí:
la pantalla de secciones del panel, el análisis por sección y el "hay uno mejor y
más barato". Eso no lo arregla ninguna funcionalidad de la competencia.

### Los seis primeros, por valor partido por coste

**1. `XS` · Notas por línea, y el aviso legal (fichas 4 y 11).**
*Qué desbloquea*: nada técnico, y por eso va primero: **la columna, el contrato y
las frases ya existen** y solo falta pintarlas. El aviso legal, además, **hay que
tenerlo antes de que esto lo use alguien más**.

**2. `S` · Añadir sin escribir: el mosaico y la voz (fichas 2 y 3).**
*Qué desbloquea*: quita el escribir, que es lo que más se hace con una mano
ocupada. Las dos juntas son una jornada y **el dato ya está en `lista_linea`**.

**3. `S` · La mecánica de la oferta, al añadir y en la lista (ficha 5).**
*Qué desbloquea*: **la pieza difícil ya está hecha y probada** (`core/promos.py`,
10 pruebas). Es la única cosa que Tiendeo insinúa y nosotros podemos hacer mejor,
porque sabemos la mecánica y no solo que "hay promo".

**4. `S` · Las cuatro funciones que ya tienen API y no tienen pantalla
(fichas 6, 7, 8 y 12).**
*Qué desbloquea*: el verificador de ofertas, los avisos de precio, el índice y la
posición por sección son **cuatro pantallas sobre endpoints que ya responden**.
**Y hay que hacerlo antes de servir `web/dist`**: hoy cambiar de interfaz **quita
funciones** (`BACKLOG.md:55-60`), y estas cuatro son exactamente las que se
quedaron en el `app.js`.

**5. `S` · Una bajada estructural no es una oferta (ficha 17).**
*Qué desbloquea*: es lo que separa "ha bajado" de "está de oferta hasta el
domingo", que es la diferencia entre comprar hoy y esperar. **El cálculo ya está
hecho** en `precio_derivado.parquet` (`promo_empieza`, `promo_acaba`,
`precio_base_cent`) y **solo Ahorramercado lo distingue** de toda la competencia.

**6. `S` · Ordenar la lista por pasillos (ficha 1).**
*Qué desbloquea*: **Explorar** y el análisis por sección, porque `seccion` ya
está en gold al **99,8 %** (medido) y el orden de recorrido ya existe. Es la
mejora que más se nota en la tienda.

**7. `S` · Nutrientes y sellos de OFF hasta gold (ficha 10).**
*Qué desbloquea*: **es el requisito de la ficha 9** (los nutrientes de la nota) y
sube los filtros de dieta. Va antes que la nota aunque valga menos: sin él, la
nota se calcula sobre el 22,7 % del catálogo.

### Después

**8. `M` · La nota absoluta del producto y el color de riesgo de los aditivos
(ficha 9).** *Qué desbloquea*: arregla un problema de raíz — hoy la letra A/B/C es
una posición dentro del grupo y **el 76,9 % son el precio disfrazado**. Es el de
más valor de la lista y por eso no va el primero: cuesta `M` y necesita la ficha
10 hecha. Necesita además **una tabla de riesgo por aditivo escrita a mano**,
como `secciones.yml`.

**9. `S` · Cerrar la compra (ficha 13, ya es la tarea 10 del BACKLOG).**
*Qué desbloquea*: **cuatro cosas de este documento** — la despensa deducida, el
aviso de caducidad, el control de gasto y las estadísticas. Va aquí y no más
abajo porque **es barato ahora e imposible de recuperar después**: sin ella, en
diciembre no habrá historial que mirar (`BACKLOG.md:804-807`).

**10. `M` · La despensa deducida (ficha 14).**
*Qué desbloquea*: el 80 % del valor de una app de despensa sin el trabajo que
hace que se abandonen. **Depende de la 9.**

**11. `S` · Control de gasto (ficha 16).** **Depende de la 9.**

**12. `M` · Aviso de caducidad (ficha 15).** **Depende de la 9**, y solo puede
avisar sobre el **8,3 %** del catálogo: `dias_caducidad` es de DIA y de nadie más.

**13. `M` · Avisos de retirada de producto con AESAN (N10, ya en el BACKLOG).**
*Qué desbloquea*: es **lo único de toda la lista que ninguna app de la
competencia tiene** (`COMPETENCIA.md:445-447`). `es_recall` existe en gold y está
a **0** (medido). No está en las fichas porque **no tiene app de referencia**, y
esa es la razón de que valga la pena.

### Lo que no hay que hacer todavía

La **detección de reduflación** (RadarSuper). Es una idea buena y **el dato que
hace falta ya lo tenemos** — `cantidad`, `precio_unidad_cent` y
`precio_ref_canon_cent` — pero no antes de los grupos anchos: hoy el 6 % de los
grupos tiene una dispersión de más de 3× (259 de 7.992, medido), y una detección
de reduflación sobre grupos malos daría falsos positivos en cadena.

---

## 5. Lo que habría que añadir al BACKLOG

Tareas **nuevas**, en el formato del BACKLOG, listas para pegar. Lo que ya está
allí (tareas 1, 3, 4, 5, 9 y 10) **no se repite**: cuando una ficha de aquí
apunta a una tarea existente, lo dice. La numeración sigue a `N28`.

---

## N29. Ordenar la lista por pasillos, en la interfaz nueva · **HECHO el 27 de septiembre de 2026**

**Por que.** `seccion` ya está en gold al **99,8 %** (52.446 de 52.567 productos,
medido) y `core.secciones.ORDEN` ya está en el orden en que se recorre una tienda.
La tarea 1 dejó hecho el dato y la mitad de la pantalla; **lo que faltaba era agrupar, y se hizo
ese mismo día** (`porPasillo` en `Cesta.tsx`, con el encabezado pegado arriba mientras dura su
tanda; lo mide `prueba_navegador`). Es la mejora que más se nota andando por el supermercado, y
**desbloquea "Explorar" y el análisis por sección**.

**Que hay que hacer.**

1. `plataforma/api/catalogo.py`: devolver `seccion` en cada línea de
   `GET /api/listas/{id}`. El orden ya lo da `secciones()` (línea 365).
2. `plataforma/web/app/src/paginas/Cesta.tsx`: agrupar las líneas por `seccion`
   **dentro de "Por coger"**, con el orden de `core.secciones.ORDEN`.
3. Lo que no tenga sección va al final, bajo **"otros"**, y **no desaparece**.
4. **La barra de abajo no se toca** (`USABILIDAD.md:89-107`).

**Donde.** `plataforma/api/catalogo.py`, `plataforma/web/app/src/paginas/Cesta.tsx`.

**Como se sabe que esta bien.**

    uv run pytest tests/test_secciones.py           13 en verde
    uv run python -m projects.cesta.auditar_secciones

- La lista se agrupa y el orden es el del recorrido de la tienda.
- `seccion` llega en **≥ 99 %** de las líneas.
- Un producto sin sección sale bajo "otros", al final, y se puede tachar.
- **`estimacion.total_cent` no cambia** al agrupar: agrupar no es recalcular.

---

## N30. Las cuatro funciones de la competencia que se quedaron en el `app.js`

> **CERRADO el 24 de septiembre de 2026, y esta seccion se deja como estaba porque es el
> registro de lo que se midio ese dia.** Las cuatro funciones estan ya en la interfaz nueva
> -- los avisos de precio (campana y `/avisos`), el indice, la posicion y las ofertas dudosas
> (las tres ultimas pestañas del panel, ver `docs/BACKLOG.md` §0) -- y `web/dist` **es lo que
> se sirve** desde esa tarde. El bloqueo que describe aqui, `/api/ofertas-dudosas`
> (`app.js:1110-1156`), existe y esta medido. Lo de abajo es la historia.

**Por que.** Cuatro cosas que **ya tienen endpoint y ya tenian pantalla en la
interfaz vieja**, y que la nueva no tenia: **avisos de precio**
(`BACKLOG.md:128-132`), **índice de precios** (`app.js:796-920`), **posición por
sección** (`app.js:925-996`) y **ofertas dudosas** (`app.js:1110-1156`). Las
cuatro salen de la competencia (`COMPETENCIA.md:599-606`). **Era el bloqueo para
servir `web/dist`**: entonces, cambiar de interfaz quitaba funciones
(`BACKLOG.md:55-60`).

**Que hay que hacer.**

1. **Avisos de precio**: `src/api/alertas.ts` nuevo sobre
   `GET/POST/DELETE /api/alertas` y `POST /api/alertas/vistas`
   (`plataforma/api/main.py:549, 563, 573, 579`). Se crean y se ven en
   `src/paginas/Favoritos.tsx`, y se crea desde `src/componentes/BotonFavorito.tsx`.
   **Marcar como vistas es otra llamada**: abrir la pantalla en el autobús no es
   haberlas leído.
2. **Índice y posición**: dos pestañas nuevas en `src/paginas/Panel.tsx`, en la
   lista de la línea 30-35, sobre `GET /api/indice` y `GET /api/posicion`.
3. **Ofertas dudosas**: una pestaña sobre `GET /api/ofertas-dudosas`, con
   `por_que` en cada fila (lo devuelve `movimientos.py:206`).
4. **El filtro del panel por cadenas cercanas**: `Panel.tsx:488` llama
   `useBajadas(dias, subidas, [])` con la lista vacía. Debe leer `cadenas_cerca`,
   como hace `GET /api/buscar` (`plataforma/api/main.py:159-163`).

**Donde.** `plataforma/web/app/src/api/alertas.ts` (nuevo),
`src/paginas/Panel.tsx`, `src/paginas/Favoritos.tsx`,
`src/componentes/BotonFavorito.tsx`.

**Como se sabe que esta bien.**

- Crear una alerta de `minimo_90d` sobre un favorito y verla aparecer.
- **Una alerta que salta no se marca como vista sola.**
- La pestaña de ofertas dudosas **dice cuántos días de histórico hay** y, si son
  menos de 45, explica que el control del "precio subido antes de la oferta" está
  dormido (`MOVIMIENTOS.md:77-83`).
- `uv run pytest tests/test_analisis.py tests/test_alertas.py tests/test_movimientos.py`
  en verde.
- **Ninguna de las cuatro pantallas cambia un fichero** al abrirse
  (`test_el_panel_solo_lee`, `API.md:340-343`).

---

## N31. Añadir sin escribir: el mosaico y la voz

**Por que.** Las tareas 3.1 y 3.2 del BACKLOG están escritas **para el `app.js`
viejo** (`BACKLOG.md:551-552` apuntan a `plataforma/web/app.js`). Hay que
apuntarlas al front nuevo. El dato ya está: `lista_linea.anadido_por` y
`anadido_en` (`plataforma/sql/001_esquema.sql:93-94`) e `imagen` en los **52.567**
productos (medido).

**Que hay que hacer.**

1. `GET /api/habituales?limite=24` en `plataforma/api/main.py`, junto a
   `/api/buscar`. Contrato en `API.md:380-388`. **Lista vacía si no hay
   historial, y la interfaz no pinta nada.**
2. `src/componentes/Mosaico.tsx` (nuevo), que se pinta en
   `src/paginas/Buscar.tsx` cuando `consultaUtil(f)` es falso
   (`src/api/consultas.ts:65-67` ya sabe detectarlo).
3. El botón de voz en `src/paginas/Buscar.tsx`, con `SpeechRecognition`.
   **Si el navegador no lo soporta, el botón no se dibuja**: la misma regla que
   ya usa `Escaner.tsx:57-60` con `BarcodeDetector`.
4. Si el dictado trae cantidad ("dos litros"), **se propone**, no se añade sola.

**Donde.** `plataforma/api/main.py`, `plataforma/web/app/src/paginas/Buscar.tsx`,
`src/componentes/Mosaico.tsx` (nuevo).

**Como se sabe que esta bien.**

- Con historial: se ve el mosaico y añadir son **dos toques**.
- **Sin** historial: no se pinta nada, y **nunca** se rellena con "populares"
  (`API.md:388`).
- Sin `SpeechRecognition`, **no hay botón en el DOM**.
- `/api/habituales` sin sesión da **401**.
- Área de pulsar **≥ 44 px** (`UX-MOVIL.md:138`).
- `uv run pytest tests/test_cesta_api.py tests/test_interfaz.py` en verde.

---

## N32. La mecánica de la oferta, en el resultado y en la lista

**Por que.** La tarea 4 del BACKLOG está apuntada al `app.js` viejo y **la pieza
difícil ya está hecha** (`core/promos.py`, 10 pruebas en verde). Sabemos el precio
**y la mecánica**: no "hay promo", sino "llevando dos, 1,50 EUR menos por unidad".

**Que hay que hacer.**

1. `GET /api/buscar`: añadir `mecanica` y `unidades_optimas` a cada fila, que
   `core/promos.py` ya calcula.
2. `src/componentes/TablaResultados.tsx`: el sello de oferta lleva su mecánica
   traducida ("3x2", "2ª unidad −50 %").
3. `src/paginas/Cesta.tsx`: si una línea tiene oferta aprovechable y llevas
   menos unidades de las que compensan, una línea pequeña debajo: *"llevando 3
   en vez de 2, la tercera sale gratis"*.

**Donde.** `plataforma/api/catalogo.py` (`buscar`, línea 155),
`plataforma/web/app/src/componentes/TablaResultados.tsx`,
`src/paginas/Cesta.tsx`.

**Como se sabe que esta bien.**

- Un producto con "3x2" enseña la sugerencia cuando llevas 2.
- Un producto con "Club Alcampo … acum en tu tarjeta" **no la enseña**, porque
  ese dinero no se descuenta en caja (`BACKLOG.md:598-600`).
- El total de la lista **baja** al subir de 2 a 3 unidades en un 3x2.
- Un producto de Mercadona, que **no publica `promo_txt`** (`CADENAS.md:42`), no
  enseña una mecánica inventada.
- `uv run pytest tests/test_promos.py` en verde.

---

## N33. Notas por línea y el aviso legal, en la interfaz nueva

**Por que.** Las dos cosas más baratas de toda la lista. `nota` existe en
`plataforma/sql/001_esquema.sql:92` y **la interfaz no lo usa**
(`BACKLOG.md:609`); el aviso legal de QueFalta está redactado desde el 17 de
septiembre y **hay que tenerlo antes de que esto lo use alguien más**
(`FUNCIONALIDADES.md:82-88`).

**Que hay que hacer.**

1. `src/paginas/Cesta.tsx`: campo de nota en la línea. Ojo: las líneas **hoy no
   se pintan** — `Cesta.tsx:213-217` solo usa `lineas.length` (`BACKLOG.md:97-100`).
   Al pintarlas, usar `nombre_visto` (`src/tipos.ts:414`), que ya viaja y no
   renderiza ningún fichero de `app/src`.
2. El aviso legal en `src/paginas/Ajustes.tsx` y bajo el total de la lista. El
   texto está redactado en `PANTALLAS.md:304-307`, incluidas las tres frases que
   ya estaban pensadas: la de precios orientativos, la de no afiliación y la de
   que los datos viven en casa.

**Donde.** `plataforma/web/app/src/paginas/Cesta.tsx`,
`plataforma/web/app/src/paginas/Ajustes.tsx`.

**Como se sabe que esta bien.**

- Se escribe una nota, se recarga y sigue ahí; la otra persona la ve al
  sincronizar.
- Una línea **sin** nota no enseña un hueco vacío: no enseña nada.
- **Las líneas se ven.** Hoy no se ven, y ese es el arreglo de verdad de esta
  tarea.
- El aviso legal sale en Ajustes y bajo el total.
- `uv run pytest tests/test_lineas_api.py tests/test_interfaz.py` en verde.

---

## N34. La nota absoluta del producto y el color de riesgo de los aditivos

**Por que.** La tarea 9 del BACKLOG ya describe el problema y la fórmula; esto
añade **lo que le falta para implementarla**. Hoy la letra A/B/C es una posición
**dentro del grupo** y **el 76,9 % de las letras son el precio disfrazado**
(`FUNCIONALIDADES.md:138-140`). La fórmula de Yuka es **absoluta**, está publicada
(60 % nutrición, 30 % aditivos, 10 % ecológico; **tope 49/100** con un aditivo de
riesgo rojo), y no se puede confundir con el precio. Eso es todo el arreglo.

**Que hay que hacer.**

1. **Una tabla de riesgo por aditivo, escrita a mano**, en `core/datos/`. No se
   baja de ninguna cadena: es trabajo de escribir, como `secciones.yml` (849
   claves en una tarde, `COMPETENCIA.md:325-327`). Con cuatro niveles, como Yuka
   (verde, amarillo, naranja, rojo) y el aviso de si es alergénico, como OCU
   Market. **Los aditivos que aparecen de verdad en el catálogo son pocos.**
2. `core/calidad.py`: calcular la nota. **No tocar el contador de aditivos**: hoy
   exige "E" + tres o cuatro dígitos y **no cuenta los aromas**, que es justo el
   error que la OCU documenta en Yuka y MyRealFood (2 falsos positivos en 400
   productos, `BACKLOG.md:785-789`).
3. Añadir `nota` a cada producto de `GET /api/grupo` y `GET /api/ean`. **El
   contrato ya está escrito en `API.md:390-405`.**
4. `src/paginas/Grupo.tsx` y `src/paginas/Escaner.tsx`: el hueco ya está pintado
   (`Escaner.tsx:330-339`).

**Donde.** `core/calidad.py`, `core/datos/` (nuevo), `plataforma/api/catalogo.py`,
`plataforma/web/app/src/paginas/Grupo.tsx`, `src/paginas/Escaner.tsx`.

**Como se sabe que esta bien.**

- Un producto sin Nutri-Score ni ingredientes devuelve **`nota: null`** y la app
  pone **"no lo sé"**, nunca un cero ni un número (`API.md:403-405`).
- Un producto con un aditivo de riesgo alto **no pasa de 49**.
- **La nota no cambia al cambiar de grupo.** Es absoluta: esa es toda la gracia.
- Se conserva `gama` para ordenar dentro de un grupo, y **se sigue llamando
  `gama`**: `calidad` y `gama` **nunca vienen las dos** (`API.md:184-185`).
- El contador de aditivos sigue dando **2 falsos positivos en 400 productos**
  revisados. Si sale otro número, hay que mirarlo antes de seguir.
- `uv run pytest tests/test_calidad.py` en verde.

---

## N35. Los nutrientes y los sellos de Open Food Facts, hasta gold

**Por que.** La tarea 6 pide tres campos en `CAMPOS` y **dos ya están pedidos**
(`core/off.py:38, 44`). Los **sellos llegan** — 11.823 productos en gold, medido
— y **los nutrientes no**: `nutricion` en gold son **3.841 productos y todos de
DIA** (medido). **Es el requisito de N34**: sin nutrientes, la nota se calcula
sobre el 22,7 % del catálogo (11.944 de 52.567, medido).

**Que hay que hacer.**

1. Comprobar primero **si `nutriments` llega a silver**: en gold no está. Si no
   llega, cerrar el mapeo a la columna `nutricion` de `core/schemas.py:53`.
2. El JSON de `nutricion` lleva `energia_kcal`, `grasas`, `saturadas`,
   `hidratos`, `azucares`, `fibra`, `proteinas` y `sal`, con `nutricion_por`
   valiendo **`100g` o `100ml`** y nada más (medido).
3. **El dato de etiqueta manda sobre el externo**: donde DIA ya publica su tabla,
   **no se pisa**.

**Donde.** `core/off.py`, `core/schemas.py`, `projects/cesta/pipeline.py`.

**Como se sabe que esta bien.**

    uv run pytest tests/test_off.py tests/test_dia_nutricion.py    en verde

- `nutricion` en gold pasa de **3.841** a **más de 11.000**.
- **Los 3.841 de DIA siguen idénticos**, uno a uno: traer OFF no puede pisar un
  dato de etiqueta.
- Una prueba comprueba que `nutricion_por` solo vale `100g` o `100ml`: un valor
  nuevo sale en rojo en vez de colarse.
- El filtro `con_nutricion` de `/api/buscar` **dice cuántos se quedaron fuera por
  no tener el dato**, no por ser malos (`CADENAS.md:74-79`).

---

## N36. Historial de escaneos

**Por que.** Yuka lo tiene gratis, Open Food Facts app lo exporta y **OCU Market
lo tiene pedido por sus usuarios** ("otra mejora sería que conservase el historial
de los productos escaneados"). Es barato y el escáner ya está hecho.

**Que hay que hacer.**

1. Tabla nueva en PostgreSQL, con la forma de `favorito`
   (`plataforma/sql/001_esquema.sql:114-118`):

       escaneo    usuario_id, grupo_id, producto_id, ean, escaneado_en

2. Se escribe desde `GET /api/ean/{codigo}` **solo si hay sesión**.
3. `GET /api/escaneos?limite=50`.
4. Una sección en `src/paginas/Escaner.tsx`, debajo del resultado.

**Donde.** `plataforma/sql/006_escaneos.sql` (nuevo), `plataforma/api/main.py`,
`plataforma/web/app/src/paginas/Escaner.tsx`.

**Como se sabe que esta bien.**

- Escanear con sesión y volver: el producto está en la lista.
- Escanear **sin** sesión: **no se guarda nada y no se pide que entres**. Un
  escaneo anónimo no se puede guardar ni deshacer.
- `GET /api/escaneos` sin sesión da **401**.
- `uv run pytest tests/test_cesta_api.py` en verde.

---

## N37. Aviso de caducidad, con la cobertura en pantalla

**Por que.** Es la única función de las apps de despensa que **podemos hacer sin
pedir trabajo a nadie**, porque `dias_caducidad` ya está en gold y se combina con
la fecha de la compra cerrada (tarea 10). **Y hay que decir el límite**: ese campo
solo lo publica DIA y son **4.382 de 52.567 productos, el 8,3 %** (medido).
`COLECTORES.md:47` ya lo avisa: *"Nadie más publica esto"*.

**Que hay que hacer.**

1. Sin ruta nueva: es una resta entre `compra_linea.cerrada_en` y el
   `dias_caducidad` del grupo.
2. Etiqueta discreta en las líneas que lo tengan, en `src/paginas/Cesta.tsx`, y
   orden por lo que caduca antes en la despensa.
3. **Un producto sin `dias_caducidad` no lleva etiqueta y no se estima nada.** No
   se pone "los lácteos duran 7 días": eso es un dato inventado.
4. La pantalla dice **sobre cuántas líneas puede avisar**.

**Donde.** `plataforma/web/app/src/paginas/Cesta.tsx`, y el cálculo en
`plataforma/api/cesta.py`.

**Como se sabe que esta bien.**

- Un producto de DIA cerrado hace 12 días con `dias_caducidad = 15` avisa.
- Un producto de Mercadona **no avisa**, y en la ficha se lee por qué.
- **La cobertura está en pantalla.**
- **Depende de la tarea 10**: con cero compras cerradas no hay nada que avisar y
  la pantalla no aparece en blanco.
- `uv run pytest tests/test_dia_nutricion.py` en verde.

---

## N38. Control de gasto de la compra cerrada

**Por que.** Lo tienen Your Food (con gráficos por semana, mes o año), BM
("Ahorrando mes a mes"), FamilyWall y Listonic, y **a nosotros nos sale casi
gratis**: `compra.total_estimado_cent` ya está en el contrato de la tarea 10
(`API.md:411`).

**Que hay que hacer.**

1. `GET /api/compras?desde=&hasta=` con las compras y su total.
2. Una tarjeta en `src/paginas/Cesta.tsx` con lo gastado este mes y en cuántas
   compras se basa.
3. **No se llama "ahorro".** No sabemos lo que habrías gastado en otra tienda, así
   que no se inventa esa cifra.

**Donde.** `plataforma/api/main.py`, `plataforma/web/app/src/paginas/Cesta.tsx`.

**Como se sabe que esta bien.**

- Dos compras suman bien: el total es la suma de sus `total_estimado_cent`.
- **El total de una compra pasada no cambia** cuando cambian los precios de hoy.
- La pantalla dice en cuántas compras se basa.
- **Depende de la tarea 10.**
- `uv run pytest tests/test_cesta_api.py` en verde.

---

## N39. Una bajada estructural no es una oferta

**Por que.** Cuando la app dice "ha bajado", no dice **por qué**. **Ahorramercado**
es el único de la competencia que lo separa, y lo hace con dos secciones con
nombre: *"Ofertas — promoción puntual con precio anterior, puede acabar pronto"*
frente a *"Bajadas de precio — caída **estructural**, no es una oferta puntual"*.
**SuperPrecios** cubre la otra mitad, marcando *"en qué fechas estuvo de oferta"*.
Es la diferencia entre esperar al sábado y comprar hoy.

**Y no hay que calcular nada**: `precio_derivado.parquet` ya trae `ha_bajado`
(**8.752** filas; 8.124 productos), `promo_empieza` (**4.854** filas; 4.808
productos), `promo_acaba` (**1.571** filas; 1.569 productos), `precio_base_cent`
(la mediana móvil) y `posicion_90d` (medidos). **Son columnas booleanas: las
cifras son de filas (producto × día), no de productos, y lo que se cuenta es el
valor verdadero** — `IS NOT NULL` casaría con las 763.042 filas. Las consultas
están en el punto 0. Es el mismo
patrón que `MOVIMIENTOS.md:8-12` describe para las bajadas: **cruzar dos columnas
que ya estaban y que nadie había puesto una al lado de la otra**.

**Que hay que hacer.**

1. En `plataforma/api/movimientos.py`, añadir un campo `motivo` a cada fila de
   `bajadas()` y de `ofertas_dudosas()`, con la regla escrita antes de programarla:

       estructural   precio_unidad_cent < precio_base_cent
                     Y posicion_90d baja
                     Y NO hay promo_txt ni promo_hasta vivo
       puntual       precio_unidad_cent < precio_base_cent  Y  promo vivo
       dudosa        precio_unidad_cent >= precio_base_cent  Y  promo_txt existe

2. `src/paginas/Panel.tsx` (pestaña Bajadas) y `src/paginas/Grupo.tsx`: enseñar el
   motivo con la frase, no con un color.
3. **`promo_club` fuera de "puntual"**: un descuento de tarjeta no baja el ticket.

**Donde.** `plataforma/api/movimientos.py`, `plataforma/web/app/src/paginas/Panel.tsx`,
`plataforma/web/app/src/paginas/Grupo.tsx`.

**Como se sabe que esta bien.**

    uv run pytest tests/test_movimientos.py tests/test_resumen.py    en verde

- Un producto con **3x2** vivo y precio igual al de siempre sale como **puntual**,
  no como estructural.
- Un producto que bajó y lleva dos semanas bajo, sin promoción, sale como
  **estructural**.
- Un producto con "Club Alcampo … acum en tu tarjeta" **no** cuenta como bajada.
- **Ninguna fila sale con dos motivos a la vez**, y ninguna sale sin motivo cuando
  `ha_bajado` es verdadero.
- **El caso de los −96,7 %** de `MOVIMIENTOS.md:23-36` no reaparece.

---

## Anexo. Lo que no se ha podido comprobar

Va escrito para que nadie lo dé por bueno sin mirarlo.

**De nuestro sistema.**

- **Si `nutriments` de Open Food Facts llega a silver.** Está pedido en
  `core/off.py:44` y en gold `nutricion` solo tiene 3.841 filas, todas de DIA
  (medido). Si silver lo tiene, N35 es más corta de lo que parece.
- **Si el precio de Ahorramas viene en el HTML.** `COMPETENCIA.md:572` lo dejó
  como "falta comprobar" y sigue sin comprobarse.
- **El botón de cámara del escáner no está probado en un móvil real**
  (`BACKLOG.md:192-193`). Lo verificado es que se esconde solo cuando no hay
  `BarcodeDetector`.

**De la competencia.**

- **CodeCheck**: **comprobada, y con dos correcciones a lo que se suele decir**.
  Es de **Producto Check GmbH** (Berlín), 4,2★, 5 M+ descargas, ficha actualizada
  el 20 ago 2026. **No está en España**: su ficha de la App Store española da 404 y
  la búsqueda de iTunes devuelve **cero resultados** para `es`, `fr`, `gb`, `us` e
  `it`, y sí para `de`, `ch`, `at` y `nl`. Y **no usa Nutri-Score ni NOVA**: tiene
  un **"Bewertungskreis"** propio con los pesos publicados — *"50 % de la
  evaluación de los nutrientes y 50 % de la evaluación de los ingredientes"*. Sí
  limita a **5 escaneos por semana** en la versión gratis. Se cita aquí como
  referencia de **cómo se avala una nota con expertos nombrados**, no como
  competidor en España.
- **Shopmium**: **no opera en España**, y esto corrige lo que se deduce de su
  ficha de Play traducida. Siete comprobaciones convergentes: su selector de
  países solo lista Reino Unido, Francia, Estados Unidos y Bélgica; `shopmium.com/es`
  da 404 y **nunca existió** (0 capturas en Wayback); su centro de ayuda en
  español devuelve **cero artículos**; dice *"más de 9 millones de personas en el
  Reino Unido, Francia y Bélgica"*; y **la App Store española no tiene su ficha**,
  mientras sí aparece la primera en Reino Unido, Francia y Bélgica. Tiene reseñas
  en español, que prueban uso, pero **no un catálogo válido en supermercados
  españoles**. Quien ocupa ese hueco aquí son **Woolsocks, Gelt, PROMOS y La
  Cuponera**.
- **Google Shopping**: **su aplicación cerró en 2021** (la ficha de Play da 404) y
  **no hay ninguna fuente sólida** de que compare alimentación o cesta en España.
- **PriceRunner**: **no opera en España** (su paquete `com.pricerunner` da 404);
  es nórdico.
- **Buycott**: no compara precios, es de pago (1,99 €), solo iOS y fuera de Google
  Play. Una prueba oficial de la Verbraucherzentrale alemana lo despacha con un
  *"Bitte sparen Sie sich diesen Download!"*.
- **Open Prices**: su API declara **315.070 precios** (medido el 22 sep 2026), y se
  alimenta de **fotos de etiquetas de precio leídas por IA**. **Su cobertura de
  España no se ha podido comprobar**, y la licencia ODbL ya obliga a no mezclarla
  (`COMPETENCIA.md:418-429`).
- **MyRealFood**: comprobado qué hace hoy (escáner, "Real Score", planes, recetas,
  entrenamientos, comunidad y tienda propia; 4,4★, 1 M+, 31 ago 2026), pero **no
  se ha podido leer su fórmula de puntuación**, así que no se afirma nada sobre
  cómo calcula el "Real Score".
- **OLIO en España**: el sitio y la app están en español, pero **no hay ninguna
  evidencia de operación activa** — ni ciudades, ni cifras, ni alianzas. La única
  alianza documentada es británica (Lidl GB).
- **Bring! en España**: **no publica qué supermercados cubre**. Dice que "varían
  según la ubicación" y sus ejemplos son alemanes (Lidl, Aldi, Edeka). No se
  puede afirmar su cobertura española.
- **QuéFalta Plus**: cuesta dinero y **su precio no está publicado en ningún
  sitio** (`/plus` y `/precios` dan 404). Lo mismo con la matriz de pago de
  **Listonic**: no existe página oficial de precios.
- **Precio de Bring! (13,99 €/año) y de Listonic**: vienen de una reseña de
  prensa, **no de fuente oficial**. Marcados como tal.
- **El Corte Inglés**: "ticket digital", "escaneo de productos" y "pago con el
  móvil" **solo constan en prensa de febrero de 2023**, no en sus fichas de
  septiembre de 2026. Dato a verificar antes de citarlo.
- **Flipp está en las tiendas españolas** con ficha traducida, y **su propio
  centro de ayuda dice que solo está en Canadá y Estados Unidos**. La ficha
  traducida no significa que funcione aquí.
- **Shopmium**: **no opera en España** (ver arriba). Su ficha de Play traducida
  describe supermercados **británicos** y sus importes van en libras: una ficha
  traducida no es un mercado.
- **Karma**: se ha reconvertido a **TPV para restaurantes** (agosto de 2025) y su
  app de consumidor es solo de Suecia hoy. **No hay evidencia de que haya operado
  nunca en España.** Además hay colisión de nombre con una app de criptomonedas.
- **Encantado de Comerte**: `encantadodecomerte.es` sirve hoy el sitio de
  **Coometas**, con giro hacia **bonos digitales de ayuda alimentaria**.
- **CozZo está cerrada** (soporte hasta el 30 de diciembre de 2025). Se cita solo
  como referencia de qué tenía la categoría.
- **Tres dominios del encargo no existen tal cual**: `cozzoapp.com` y
  `kitchenpal.com` no resuelven, y `olioex.com` falla el TLS (el sitio es
  `olioapp.com`).
