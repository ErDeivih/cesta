# Auditoría funcional de la app de Cesta — 2026-11-05

**Encargo:** `ALCANCE-APP.md` §5.1 — «primero que funcione todo lo que ya hay, sin errores», y
`DOCTRINA-CALIDAD.md` §8 — «la interfaz no habla de cómo está hecha».

**Naturaleza de este documento:** auditoría de **solo lectura**. No se ha modificado código, ni datos,
ni el stack. No se ha creado ninguna cuenta ni se han probado credenciales. Todo lo que dice «medido»
lleva el comando y el resultado; lo que sale de leer código lleva `archivo:línea`.

**Stack auditado:** web en `http://127.0.0.1:8080` (Caddy sirviendo `plataforma/web/dist`), API en
`/api/*` por el mismo origen. Código: `plataforma/web/app/src` (React 19 + Vite, build del 04/11/2026
18:10, posterior al último `.tsx`, así que **lo servido corresponde al código leído**) y
`plataforma/api` (FastAPI). Postgres en docker `cesta-db-1` **no se ha tocado**.

---

## 0. Cómo se ha medido, y qué NO se ha podido probar

| Instrumento | Qué ha dado |
|---|---|
| 40+ peticiones HTTP a `/api/*` con `urllib` (Python del `.venv`) | **0 respuestas 5xx**. Códigos vistos: 200, 400, 401, 404, 405 y 422, todos coherentes |
| 40 rutas de la web pedidas por HTTP | **todas 200** y todas devuelven el armazón SPA (`dist/index.html`, 1 764 bytes); no hay caídas de Caddy en rutas profundas |
| Latencia | mediana de 2 peticiones por endpoint (tabla §1.2). Rango completo donde hay dispersión |
| `npm run tipos` en `plataforma/web/app` | **exit 0** en 22,4 s (`tsc --noEmit`) |
| `npm test` (tests de la app, `node --test`) | **376 pass / 0 fail** en 1,8 s |
| Lectura de `plataforma/web/app/src/**/*.tsx` (51 ficheros, sin contar los 5 de prueba) | mapa de pantallas, estados, textos y enlaces |

**No probado, y por qué:** todo lo que exige sesión (listas, favoritos, recetas, diario, despensa,
alertas, habituales) contesta **401** sin cookie y no se han usado credenciales. De esas pantallas se
documenta el **contrato** (API + `tipos.ts`) y **lo que la UI hace con cada estado**, leyendo el código;
no se afirma que funcionen de punta a punta porque no se ha visto. Lo mismo con la cámara del escáner
(necesita HTTPS y permiso) y con la ingesta en marcha (no se ha lanzado nada).

---

## 1. Mapa de rutas: qué pasa al abrirlas

### 1.1 Rutas de la web (`App.tsx`, todas 200 por HTTP)

| Ruta | Pantalla | Datos que pide | Qué se ve al abrirla | Estado |
|---|---|---|---|---|
| `/` | Lanzador | ninguno (solo `localStorage['cesta.ultimo']`) | Tres tarjetas (Compra, Recetas, Calorías) y «Continuar donde estaba» si hay historial | Bien |
| `/compra` | Buscar | `/api/estado`, `/api/secciones`, `/api/buscar`, `/api/habituales` | Sin texto: ejemplos, recientes y mosaico «Lo de siempre». Con texto: resultados y filtros | Bien |
| `/compra/listas` | Cesta | `/api/yo`, `/api/listas`, `/api/listas/{id}`, `/api/listas/{id}/donde`, `/api/listas/{id}/reparto` | Sin sesión: formulario de entrada (correcto). Con sesión: lista, totales, reparto, compartir | Bien |
| `/compra/listas/:listaId` | Cesta | ídem | ídem | Bien |
| `/compra/favoritos` | Favoritos | `/api/yo`, `/api/listas`, `/api/favoritos?ventana=` | Sin sesión: «Entra para ver tus favoritos» + enlace. Con sesión: favoritos con variación | Bien |
| `/compra/productos/:fuente/:idFuente` | Producto | `/api/producto/{fuente}/{id}`, `/api/grupo/{grupo}` | Ficha, comparación del grupo, histórico, nutrición, emparejamiento | Lento (§2.2) |
| `/compra/comparar/:grupoId` | Grupo | `/api/grupo/{id}`, `/api/estado` | Comparación entre cadenas, pesos del orden, histórico | Lento (§2.2) |
| `/compra/despensa` | Despensa | `/api/despensa` | **Sin sesión: error técnico** «No he podido traer esto / La API ha contestado 401.» | **Roto sin sesión (P0-1)** |
| `/compra/analisis` | **Panel** (analítica interna) | `/api/panel/*`, `/api/indice`, `/api/ofertas-dudosas` | «Panel» con 10 pestañas de datos del catálogo | **No es lo que dice el menú (P0-2)** |
| `/compra/cocina/:recetaId/:version` | CocinaModo | `/api/cocina/*` | Nada: no hay ni un enlace que lleve aquí | **Inalcanzable (P2-1)** |
| `/compra/importar` | ImportarReceta | `POST /api/recetas/importar` | Nada: no hay ni un enlace que lleve aquí | **Inalcanzable (P2-1)** |
| `/recetas` | Recetario | `/api/recetas` | **Sin sesión: error técnico 401**; con sesión, recetario + alta | **Roto sin sesión (P0-1)** |
| `/recetas/plan` | PlanSemanal | `/api/recetas`, `/api/recetas/plan` | **Sin sesión: error técnico 401** | **Roto sin sesión (P0-1)** |
| `/recetas/:recetaId` | RecetaDetalle | `/api/recetas/{id}`, `/api/listas` | **Sin sesión: error técnico 401**; 404 tiene pantalla propia | **Roto sin sesión (P0-1)** |
| `/calorias` | Diario | `/api/diario/{fecha}`, `/api/listas`, `/api/yo` | **Sin sesión: error técnico 401** | **Roto sin sesión (P0-1)** |
| `/calorias/alimentos` | **Cocina (prototipo en memoria)** | **ninguno** | Cuaderno de la pestaña; se pierde al recargar | **P0-3** |
| `/calorias/tendencias` | Tendencias | `/api/diario/rango` | **Sin sesión: error técnico 401** | **Roto sin sesión (P0-1)** |
| `/avisos` | Avisos | `/api/yo`, `/api/alertas` | Sin sesión: «Entra para ver tus avisos» (correcto) | Bien |
| `/ajustes` | Ajustes | `/api/yo`, `/api/estado`, `PUT /api/preferencias` | Sin sesión: «Entra para cambiar tus ajustes» (correcto) | Bien |
| `/panel` | Panel (analítica interna) | `/api/panel/hoy`… | «Panel», 10 pestañas técnicas, enlace a `/panel/matching` | **Fuera de sitio (P0-2)** |
| `/panel/matching` | PanelMatching | `/api/panel/matching` (200, 982 ms) | Panel del emparejador con JSON crudo, rutas de ficheros y `docker compose` | **Fuera de sitio (P0-4)** |
| `/escaner` | Escáner | `/api/ean/{codigo}` | Campo de código, cámara si el navegador puede, ficha de lo escaneado | Bien (textos §8) |
| `/aprender` | **Marcador de desarrollador** | ninguno | «El material didactico vive en `docs/aprende/`. Aqui llegara el indice navegable; mientras tanto se lee en el repositorio.» | **§8 (P0-5)** |
| `/unirme/:codigo` | Unirse | `POST /api/invitacion/{codigo}` | Sin sesión: la puerta de entrada con la invitación; con sesión: entra en la lista | Bien |
| `/buscar`, `/cesta`, `/favoritos` | redirección | — | Redirigen a `/compra…` conservando la query | Bien |
| `/producto/:fuente/:id`, `/grupo/:id` | redirección | — | Redirigen a `/compra/productos/…` y a `/compra/comparar/…` | Bien |
| `*` | «Esa pantalla no existe» | — | Estado vacío con enlace al inicio | Bien |

### 1.2 API medida (mediana de 2 peticiones; 2026-11-05, 11:30–11:36)

| Endpoint | HTTP | ms | Bytes | Nota |
|---|---:|---:|---:|---|
| `/api/salud` | 200 | 73 | 40 | `{"vivo":true,"fecha_datos":"2026-11-04"}` |
| `/api/estado` | 200 | 808 | 4 809 | cabecera de frescura: `version_catalogo: 20261104-144138`, `vigente: coherente=true`, `huellas_en_el_puntero: 6` |
| `/api/estado/publicacion` | 200 | 3 231 | 314 | **ninguna pantalla lo usa** (grep en `src`): endpoint huérfano |
| `/api/secciones` | 200 | 256 | 2 126 | 19 pasillos; UTF-8 correcto (`Carnicería`) |
| `/api/buscar?q=leche` | 200 | 409 | 20 524 | 40 resultados; `grupo_id 64466` «Leche semidesnatada MILSANI» a 0,83 €/l en aldi |
| `/api/buscar?q=leche&limite=5&desplazamiento=5` | 200 | 363 | 2 608 | **la paginación funciona** (5 resultados, empieza en «AUCHAN Café latte…») |
| `/api/buscar?q=xyzzyqq` | 200 | 782 | 44 | lista vacía, no error |
| `/api/grupo/64466` | 200 | 3 519 | 35 990 | **0,8–6,0 s** en 4 medidas; 5 cadenas, `explicacion` incluida |
| `/api/producto/aldi/80500` | 200 | 5 862 | 35 875 | **1,5–5,9 s** en 4 medidas |
| `/api/ean/8412345678905` | 200 | 940 | 161 | `encontrado:false`, con sugerencia legible |
| `/api/bajadas` | 200 | 1 030 | 25 366 | 7 días; usado por Panel |
| `/api/panel/hoy` | 200 | 96 | 881 | 6 cadenas; Alcampo 23 416 productos, Lidl 91 |
| `/api/panel/donde` | 200 | 187 | 33 425 | |
| `/api/panel/cadenas` | 200 | 52 | 1 018 | |
| `/api/panel/marcas` | 200 | 59 | 1 382 | |
| `/api/panel/historico` | 200 | 12 | 3 825 | |
| `/api/panel/movidos` | 200 | 25 | 11 403 | |
| `/api/panel/matching` | 200 | 982 | 11 298 | última pasada `20261104-144136`, huella de catálogo incluida |
| `/api/indice` | 200 | **18 334** | 31 734 | **18 s**; lo pinta la pestaña «Índice» de `/panel` |
| `/api/pulso` | 200 | **17 463** | 49 973 | **ninguna pantalla lo usa** |
| `/api/ofertas-dudosas` | 200 | **15 494** | 27 961 | **15 s**; lo pinta la pestaña «Ofertas dudosas» de `/panel` |
| `/api/habituales`, `/api/listas`, `/api/recetas`, `/api/despensa`, `/api/diario/…`, `/api/alertas`, `/api/favoritos` | 401 | 7–76 | 36 | sin sesión, cuerpo vacío (correcto) |

**Cuerpos de error comprobados:** `/api/grupo/abc` → 422; `/api/grupo/999999999` → 404;
`/api/producto/nope/1` → 404; `/api/ean/abc` → 400 con `motivo` y `sugerencia` legibles; método
incorrecto → 405. **Ningún 5xx en toda la batería.** `/api/docs` y `/api/openapi.json` contestan
**200 sin sesión** (P2-6).

---

## 2. Defectos priorizados

Prioridad: **P0** rompe el flujo o pierde lo que el usuario ha escrito · **P1** error visible,
contenido equivocado o pantalla que tarda > 3 s · **P2** pulido y limpieza.

### 2.1 P0

**P0-1. Seis pantallas escupen un error técnico a quien no ha entrado** (Despensa, Recetario,
RecetaDetalle, PlanSemanal, Diario, Tendencias).
Estas pantallas piden endpoints que exigen sesión y **no tienen puerta**: no consultan `/api/yo` ni
tienen el estado «sin permiso». Resultado: un visitante nuevo abre «La despensa» o «Recetas» y ve un
aviso rojo con texto de desarrollador.

- Reproducir: `GET /api/despensa` → **401**; `GET /api/recetas` → **401**; `GET /api/diario/2026-11-05` → **401**.
- Código: `paginas/Despensa.tsx:26` (`useDespensa`) y `:83` (`<Fallo error={error} />`);
  `paginas/Recetario.tsx:206` y `:248`; `paginas/RecetaDetalle.tsx:122` y `:141`;
  `paginas/PlanSemanal.tsx:340`; `paginas/Diario.tsx:489`; `paginas/Tendencias.tsx:73`.
- El texto que sale lo pone `api/cliente.ts:71`: «La API ha contestado 401.» (además §8, fila 2 del inventario).
- Contraste: Favoritos (`Favoritos.tsx:214`), Avisos (`Avisos.tsx:111`), Cesta (`Cesta.tsx:1357`) y
  Ajustes (`Ajustes.tsx:57`) sí tienen puerta. La corrección es la misma pieza en las seis.

**P0-2. «Gasto y ahorro» no lleva al gasto: lleva al panel interno de analítica.**
El menú de la aplicación Compra tiene una subsección llamada **«Gasto y ahorro»**
(`componentes/Suite.tsx:85`) que apunta a `/compra/analisis`, y esa ruta monta `Panel`
(`App.tsx:236-238`), que es el cuadro de mando del catálogo: «Hoy», «Dónde comprar», «Cadenas»,
«Marcas», «Histórico», «Movidos», «Bajadas», «Índice», «Posición», «Ofertas dudosas»
(`paginas/Panel.tsx:38-58`, `:100`, `:139-148`). Lo que David pide cuando abre «Gasto y ahorro» es
**lo que ha pagado**; eso existe (`componentes/LoQueHasPagado.tsx`, montado en `Panel.tsx:274`) pero
está enterrado como una tarjeta de la primera pestaña, debajo de «Lo que entró hoy en el catálogo».

**P0-3. «Mis alimentos» (`/calorias/alimentos`) es un prototipo en memoria: lo escrito se pierde.**
`App.tsx:259` monta `<Cocina modo="calorias" />`, y `paginas/Cocina.tsx` guarda todo en
`useState` (`Cocina.tsx:14-15`), sin API. Lo dice la propia pantalla: «Cuaderno de esta pestaña, sin
sincronización con tu cuenta. Se pierde al recargar o cerrar» (`Cocina.tsx:54`) y «Comida anotada en
esta pestaña. No cambia tu lista de compra.» (`Cocina.tsx:91`). Además duplica el concepto del Diario
real (`/calorias` → `Diario.tsx`), que sí escribe en `/api/diario`. Es la única pantalla de la app que
pierde datos del usuario.

**P0-4. El panel de auditoría del emparejador es alcanzable desde la app de consumo.**
`paginas/Panel.tsx:101-106` enlaza «Panel de matching →». La pantalla muestra el `ejecucion_id`, el
umbral, la huella del catálogo, los nombres crudos de las métricas, los rasgos de cada par, y un
`<pre>` con **la respuesta entera en JSON** (`PanelMatching.tsx:279-281`), además de instrucciones con
`docker compose up -d --build api` (`:368`) y rutas de datos `data/gold/matching/` (`:69-71`).

**P0-5. «Aprender» es un marcador de desarrollador dentro del menú.**
`componentes/Suite.tsx:295-296` pone «Aprender» en «Cuenta y ayuda», y la ruta
(`App.tsx-287`) solo dice: «El material didactico vive en `docs/aprende/`. Aqui llegara el indice
navegable; mientras tanto se lee en el repositorio.» Es §8 puro y está a dos toques de la portada.

### 2.2 P1

**P1-1. La ficha de producto y la de grupo tardan entre 1,5 y 6 segundos** — y son las pantallas donde
se decide la compra.
Medido: `/api/grupo/64466` en 1 524 / 3 519 / 5 446 / 5 994 ms; `/api/producto/aldi/80500` en 1 480 /
2 431 / 4 368 / 5 862 ms. `DOCTRINA-CALIDAD.md` §3: «una pantalla que tarda 3 segundos es una pantalla
rota». Las dos pantallas sí enseñan el esqueleto mientras cargan (`Producto.tsx:134`,
`Grupo.tsx:190`) y, pasado el umbral, dicen que no han podido preguntar (`Grupo.tsx:68,186`); lo que no
tienen es forma de que la espera de 3–6 s sea más corta: es el mismo producto que se está mirando en la
mitad de las visitas, con la sensación de que la app no responde.

**P1-2. Pestañas del panel con 15–18 segundos.**
`/api/indice` → **18,3 s** (`paginas/Panel.tsx:967`); `/api/ofertas-dudosas` → **15,5 s**
(`Panel.tsx:405` de `api/consultas.ts`). Con el filtro por cadena la pantalla no cambia: el filtro se
aplica al pintar (`api/consultas.ts:383-385`).

**P1-3. Se puede ver la analítica sin saber de qué día son los datos** en pantallas sueltas.
La cabecera global que enseñaba «Datos del …» (`componentes/Cabecera.tsx`) **no se monta** (ver §3.3),
así que la fecha solo aparece donde cada pantalla se acuerda: Buscar (`Buscar.tsx:308`), Cesta
(`Cesta.tsx:1594`), Grupo (`Grupo.tsx:376`), Producto (`Producto.tsx:581`), Favoritos
(`Favoritos.tsx:284`), Panel (`Panel.tsx:237`), Ajustes. En Avisos, Despensa y Tendencias no hay fecha
de precios. **No es que falte el dato: es que la regla «un precio viejo se enseña con su fecha» depende
de que cada pantalla se acuerde.**

**P1-4. `/aprender` y el panel interno no tienen estado vacío ni de error** porque no piden datos: el
problema es que existen como pantallas de producto (P0-4, P0-5).

**P1-5. El orden del mosaico «Lo de siempre» se cae al catálogo básico sin decirlo.**
`componentes/Mosaico.tsx:70-72`: si la API no da ni una tarjeta, se pinta `LoQueSeCompra`
(cuatro productos fijos, `LoQueSeCompra.tsx:64`). No se distingue «no tienes historial» de «la ruta ha
fallado»: en el primero el título dice «La compra basica» (`Mosaico.tsx:49,80-82`), en el segundo sale
la tarjeta de la primera vez como si nada. Es el mismo patrón que ya se arregló para el contador de la
lista (`consultas.ts:221-266`) y aquí no se ha hecho.

### 2.3 P2

| # | Defecto | Evidencia |
|---|---|---|
| P2-1 | **Dos pantallas implementadas y sin puerta**: `CocinaModo` (`/compra/cocina/:recetaId/:version`, `App.tsx:217`) e `ImportarReceta` (`/compra/importar`, `App.tsx:218`) no están enlazadas desde ningún sitio (grep de `to="/compra/cocina` y `to="/compra/importar` en `src`: 0 resultados) | `App.tsx:217-218` |
| P2-2 | **Código muerto que ocupa 800+ líneas y confunde**: `componentes/Cabecera.tsx`, `componentes/Nav.tsx`, `paginas/Inicio.tsx`. `Suite.tsx:436` lo dice de `Nav.tsx`: «es codigo muerto». `Inicio.tsx` no está importado en `App.tsx` | `Suite.tsx:436`, `Cabecera.tsx:17`, `Nav.tsx:139`, `paginas/Inicio.tsx` |
| P2-3 | **Texto con un glifo roto**: `? de {x.receta}` en el plan semanal (se lee « ? de 3») | `PlanSemanal.tsx:207` |
| P2-4 | **Tildes que faltan en textos visibles**, a veces en la misma pantalla que otros con tildes: «Este dia no esta completo», «Nada anotado este dia», «Anade la primera», «Todavia no hay recetas», «La despensa esta vacia», «Esta receta no esta empezada», «no esta en el catalogo», «Cocina y alimentación · versión inicial» | `Diario.tsx:506,543`; `Recetario.tsx:251-252`; `Despensa.tsx:107`; `CocinaModo.tsx:107`; `PlanSemanal.tsx:182-183,226-227`; `Cocina.tsx:50` |
| P2-5 | **Tamaños de letra inventados por pantalla** (`text-[13px]`, `[14px]`, `[15px]`, `[16px]`, `[19px]`, `[24px]`, `[28px]`), contra `DOCTRINA-CALIDAD.md` §2 | `Tendencias.tsx:52,59,67,84,87,104,114`; `Diario.tsx:122,132,136,193,470,496,551,557`; `Recetario.tsx:146,155,165,175,271`; `Suite.tsx:267,302,414` |
| P2-6 | **La documentación de la API es pública** en producción: `/api/docs` y `/api/openapi.json` contestan 200 sin sesión | `main.py:60-61` |
| P2-7 | **Endpoints huérfanos y lentos**: `/api/pulso` (17,5 s) y `/api/estado/publicacion` (3,2 s) no los usa ninguna pantalla | grep de `pulso`/`publicacion` en `src` |
| P2-8 | **Código de React Query muerto**: `usePorCoger` (`consultas.ts:205`) solo lo usaban `Nav.tsx` (muerto); `Suite` usa `usePorCogerDeCasa` | `consultas.ts:205`, `Suite.tsx:146` |
| P2-9 | **El punto de avisos sin ver no se pinta en el menú**: el contador existe (`useAvisosSinVer`) y `Suite.tsx:288-290` reconoce que «queda pendiente»; hoy no hay señal de avisos en el lateral | `Suite.tsx:288-290`, `consultas.ts:186` |
| P2-10 | **`/api/habituales` sin sesión devuelve 401** y el mosaico no lo distingue de «no hay historial» (ver P1-5) | medido 401 |

### 2.4 Enlaces y botones a rutas muertas

Búsqueda automática de todos los `to="…"`/`to={`…`}` de `src/**/*.tsx` contra las `path=` de
`App.tsx`: **no hay ningún enlace a una ruta inexistente** (los dos «muertos» que salen son plantillas
`/compra/favoritos${search}` y `/compra/listas${search}` de las redirecciones, que existen). Lo que sí
hay es **pantallas a las que no se llega** (P2-1) y **una pantalla de menú que no hace lo que dice**
(P0-2). Los enlaces externos son dos y correctos: Open Food Facts (`Ajustes.tsx:267`) y la ficha de
cada producto en su cadena (`Grupo.tsx:751`, `Producto.tsx:803`).

---

## 3. Inventario de textos de desarrollador visibles (§8)

Criterio aplicado a cada texto: «¿esto le sirve al cliente para decidir o actuar?». **No están en la
lista** los textos que sí sirven (precio, unidad, fecha del dato, «solo con tarjeta: no baja lo que
pagas en caja», «sin dato ≠ 0», avisos de alérgenos, atribución de Open Food Facts) ni los que están
en código muerto (esos van aparte, en §3.3, para que nadie los «arregle»: se borran con el fichero).

### 3.1 Epicentros: pantallas que hay que sacar del producto, no reescribir

- **`/panel/matching` (`paginas/PanelMatching.tsx`)** — es una herramienta de ingeniería de principio
  a fin (§2.1 P0-4). Sale del menú y, si se quiere conservar, se protege o se saca del build de
  producción. 18 filas del inventario son suyas.
- **`/panel` y `/compra/analisis` (`paginas/Panel.tsx`)** — cuadro de mando del catálogo. Puede seguir
  existiendo como pantalla interna, pero **no** como «Gasto y ahorro» del consumidor.
- **`/aprender` (`App.tsx-287`)** — un párrafo que habla del repositorio.
- **`/calorias/alimentos` (`paginas/Cocina.tsx`)** — prototipo; sus textos son notas de estado.

### 3.2 Tabla

Formato: `archivo:línea | texto literal | por qué sobra | qué hacer`.

| # | archivo:línea | texto literal | por qué sobra | qué hacer |
|---:|---|---|---|---|
| 1 | `api/cliente.ts:70` | `El servidor ha fallado. Mira los registros de la API.` | Habla al que programa, no al que compra; pide mirar registros a un cliente | Reescribir: «No he podido completarlo. Vuelve a intentarlo.» |
| 2 | `api/cliente.ts:71` | `La API ha contestado ${estado}.` | Nombre del componente interno + código HTTP; es el texto que ven 6 pantallas sin sesión (P0-1) | Reescribir por estado: 401 «Entra para ver esto», resto «No he podido…» |
| 3 | `api/cliente.ts:75` | `Sin conexion con casa. Esto es lo ultimo que hay en pantalla.` | «lo que hay en pantalla» es jerga de implementación | Reescribir: «Sin conexión. Esto es lo último que tengo.» |
| 4 | `App.tsx:81` | `La compra de casa, las recetas y lo que comes. Tres aplicaciones, una casa.` | Descripción de producto en la portada (pie de producto) | Borrar (o dejar solo «Cesta») |
| 5 | `App.tsx-282` | `El material didactico vive en docs/aprende/. Aqui llegara el indice navegable; mientras tanto se lee en el repositorio.` | Ruta del repositorio + «aquí llegará» (P0-5) | Borrar la pantalla del menú; si se quiere, índice real |
| 6 | `App.tsx` | `La compra de casa, las recetas y lo que comes.` | Misma descripción, en el armazón de carga | Borrar |
| 7 | `paginas/Cesta.tsx:1356` | `tu sesión` (Cargando, sr-only) | «Sesión» es vocabulario técnico | Reescribir: «tu lista» |
| 8 | `paginas/Cesta.tsx:435` | `Pendiente de identificar` | Estado interno de la migración; el cliente no sabe qué se identifica | Reescribir: «Sin producto del catálogo» |
| 9 | `paginas/Cesta.tsx:489-490` | `Este producto ya no es el mismo en el catálogo: no lo cuento ni te digo dónde comprarlo, porque el número al que apunta esta línea es hoy otra cosa.` | Explica la renumeración interna de grupos | Reescribir: «Este producto ha cambiado en el catálogo. Búscalo y vuelve a añadirlo.» |
| 10 | `paginas/Cesta.tsx:1322-1323` | `Se ha subido 1 cambio que hiciste sin cobertura.` / `Se han subido ${aplicados} cambios que hiciste sin cobertura.` | «Subir» cambios es vocabulario de sincronización | Reescribir: «Ya se han guardado los cambios que hiciste sin conexión.» |
| 11 | `paginas/Cesta.tsx:1501-1502` | `1 cambio hecho sin cobertura se subirá al volver la cobertura.` / `${cola.length} cambios hechos sin cobertura se subirán al volver la cobertura.` | Ídem | Reescribir: «1 cambio sin guardar. Se guardará cuando vuelva la conexión.» |
| 12 | `paginas/Cesta.tsx:1518-1521` | `No he podido guardar los cambios sin cobertura` + `El navegador no me deja escribir en este aparato, así que un cambio hecho sin red se perdería. Vuelve a intentarlo cuando tengas cobertura.` | Explica la causa técnica (almacenamiento del navegador) | Reescribir: «No puedo guardar aquí. Este cambio se perderá si cierras.» |
| 13 | `paginas/Cesta.tsx:1533-1534` | `La lista sigue como estaba. Aquí no se pinta un cambio que el servidor no ha aceptado.` | «El servidor» + justificación de implementación | Borrar la segunda frase |
| 14 | `paginas/Cesta.tsx:231` | `La cuenta es lo que hace que la lista tenga dueño: sin ella no se guarda ni se puede compartir. Se queda en casa, en esta Cesta, y al crearla ya entras.` | Párrafo de relleno antes de un formulario | Reescribir a una frase |
| 15 | `paginas/Cesta.tsx:232` | `La lista de la compra es tuya y de quien la compartas. Por eso hay que entrar: una lista sin dueño no se puede compartir ni recuperar.` | Ídem | Reescribir a una frase |
| 16 | `paginas/Despensa.tsx:67` | `No se ha podido preguntar al servidor. Esto no quiere decir que la despensa este vacia.` | «El servidor» | Reescribir: «No he podido mirar la despensa. No quiere decir que esté vacía.» |
| 17 | `paginas/Diario.tsx:558` | `Receta ${e.referencia} (v${e.version})` | Identificador interno + versión: el cliente no sabe qué es «7 (v2)» | Reescribir: el nombre de la receta, sin identificador ni versión |
| 18 | `paginas/Diario.tsx:561` | `· {e.fuente_dato}` | Código de procedencia del dato, sin traducir | Borrar, o «dato de la etiqueta» si se decide enseñarlo |
| 19 | `paginas/Diario.tsx:533-534` | `Todas las entradas anotadas tienen calorías. El subtotal solo incluye lo registrado; comprueba que hayas anotado todas tus comidas.` | Instrucción redundante que no cambia ninguna decisión | Borrar |
| 20 | `paginas/Tendencias.tsx:90` | `media de los ${conDato.length} dias que traen dato, de ${filas.length} con algo anotado` | Explicación del cálculo, con la jerga de la consulta | Borrar la frase; la media ya está arriba |
| 21 | `paginas/Tendencias.tsx:89` | `Ningun dia de los que se anotaron trae energia: no hay media que dar.` | Justificación interna | Reescribir: «Sin dato de calorías en estos días.» |
| 22 | `paginas/Tendencias.tsx:115-116` | `Sin dato de energia en este dia: no se dibuja, porque un cero no es lo mismo que no saber.` | Explica la decisión de diseño | Borrar |
| 23 | `paginas/Cocina.tsx:50` | `Cocina y alimentación · versión inicial` | «Versión inicial» es un aviso de obra | Borrar |
| 24 | `paginas/Cocina.tsx:54` | `Cuaderno de esta pestaña, sin sincronización con tu cuenta. Se pierde al recargar o cerrar: descarga lo que quieras conservar. Los datos nutricionales se introducen desde la etiqueta; aún no se completan desde el catálogo.` | Nota de estado del desarrollo; si se queda, es confesar que la pantalla no sirve (P0-3) | Borrar y arreglar la persistencia |
| 25 | `paginas/Cocina.tsx:46` | `Receta cargada en esta sesión.` | «Sesión» técnico | Reescribir: «Receta cargada.» |
| 26 | `paginas/Cocina.tsx:91` | `Comida anotada en esta pestaña. No cambia tu lista de compra.` | Aviso de limitación interna | Borrar cuando persista |
| 27 | `paginas/Cocina.tsx:99` | `Cálculos orientativos a partir de lo que introduces. No se fijan objetivos de peso ni recomendaciones médicas. La lista descargada aún no se añade a la cesta ni escoge productos automáticamente.` | Hoja de ruta del desarrollo | Dejar solo «Cálculos orientativos…», borrar el resto |
| 28 | `paginas/Cocina.tsx:74` | `Valores por 100, no por envase. Deja vacío lo desconocido. No conviertas peso cocinado en crudo ni gramos en mililitros sin equivalencia.` | Instrucción de tres frases para un formulario | Reescribir a una |
| 29 | `paginas/Escaner.tsx:239` | `El motivo «sin_ean_en_esa_cadena» todavía no se da nunca: necesitaría un parámetro «cadena» que no está implementado.` (la última palabra va entre comillas invertidas en el código) | Nota de desarrollo literal, con nombre de parámetro | Borrar |
| 30 | `paginas/Escaner.tsx:195` | `Este navegador no tiene BarcodeDetector, así que no hay botón de cámara: teclea o pega el número.` | Nombre de una API del navegador | Reescribir: «Este navegador no puede leer códigos con la cámara: escribe el número.» |
| 31 | `paginas/Escaner.tsx:233` | `Motivo: {perdido.motivo}` | Código interno en crudo (`desconocido`) | Reescribir en castellano |
| 32 | `paginas/Escaner.tsx:220-221` | `Un código bueno que no conozcamos contesta otra cosa: «no lo tengo». Aquí el servidor dice que lo que ha llegado no es un código.` | «El servidor» + explicación del contrato | Borrar |
| 33 | `paginas/Escaner.tsx:333-337` | `La nota del producto (dato en crudo)` + `<pre>{JSON.stringify(hallado.nota)}</pre>` | Volcado de datos internos al usuario | Borrar |
| 34 | `paginas/Escaner.tsx:325-327` | `La diferencia se mide contra el precio por unidad más bajo de la comparación, no contra el precio del envase.` | Explicación del cálculo | Reescribir a «Diferencia con el más barato por unidad» |
| 35 | `paginas/Producto.tsx:687-698` | `De la mas barata a la mas cara de este mismo articulo hay X % de diferencia por unidad (Y € por unidad). … Las alternativas -- otro EAN -- no entran en esta cuenta.` | EAN + explicación del cálculo | Reescribir sin «EAN» y sin la última frase |
| 36 | `paginas/Producto.tsx:703` | `Por qué está emparejado con esos` + `ExplicacionEmparejamiento` | Sección de auditoría del emparejador dentro de la ficha | Borrar la tarjeta |
| 37 | `paginas/Producto.tsx:427,431` | `Sin identidad verificada` / `identidad no verificada` | Concepto interno de identidad de producto | Reescribir: «No sé si es exactamente este producto» |
| 38 | `paginas/Producto.tsx:534` | `No pinto la línea, y lo explico` | Primera persona de desarrollo | Borrar |
| 39 | `paginas/Producto.tsx:509` | `Es lo que dice la cadena, no lo que decimos nosotros` | Nota de procedencia en tooltip | Borrar (la atribución ya está en Ajustes) |
| 40 | `componentes/ExplicacionEmparejamiento.tsx:92-94` | `La API no manda la explicación del emparejamiento. El grupo existe y sus miembros están emparejados, pero no viaja el por qué: en /api/grupo no hay ningún campo con el método ni con la puntuación de parecido.` | Nombre de endpoint y de campos | Borrar |
| 41 | `componentes/ExplicacionEmparejamiento.tsx:102-106` | `matching`, `explicacion`, `explicacion_emparejamiento`, `emparejado_por`, `metodo_emparejamiento`, `por_que`, `parecido` (siete `<code>` listados) | Lista de nombres de campo candidatos | Borrar |
| 42 | `componentes/ExplicacionEmparejamiento.tsx:118` | `<Etiqueta>{campo}</Etiqueta>` (pinta `explicacion`) | Pinta el nombre del campo como etiqueta | Borrar |
| 43 | `componentes/ExplicacionEmparejamiento.tsx:124-127` | pares `ejecucion`, `pares`, `nivel`, `metodo`, `confianza_minima`, `confianza_media`, `par_mas_flojo`, `features.parecido`, `features.ean_igual`… | Métricas internas del emparejador | Borrar |
| 44 | `componentes/ExplicacionEmparejamiento.tsx:132-138` | `Ver el dato en crudo` + `<pre>{JSON.stringify(valor)}</pre>` | Volcado JSON | Borrar |
| 45 | `paginas/Grupo.tsx:345-348` | `La diferencia es entre los articulos del grupo, que no tienen por que ser el mismo: mismo envase y misma marca si, pero cada uno con su EAN. No es el ahorro de uno solo.` | EAN y explicación del modelo de grupos | Reescribir: «La diferencia es entre productos parecidos, no entre el mismo producto.» |
| 46 | `paginas/Grupo.tsx:370-374` | `Precios que deciden · {X} de {Y} · los de más de {diasValidos} días no cuentan` | Regla interna de validez del precio | Reescribir: «Precios de hoy: X de Y» |
| 47 | `paginas/Grupo.tsx:381-385` | `Catálogo pendiente de verificar — La versión publicada no coincide con las fechas de sus precios. Se muestran los datos, pero no se recomienda una tienda hasta verificar la publicación.` | Aviso de administración del catálogo | Mover al panel interno |
| 48 | `paginas/Grupo.tsx:389-394` | `Este grupo mezcla unidades — {N} de sus productos se miden en otra unidad (…) y no entran en la comparación: restar euros por kilo de euros por unidad da números enormes y falsos.` | Explica el cálculo | Reescribir: «Algunos productos se miden en otra unidad y no entran en la comparación.» |
| 49 | `paginas/Grupo.tsx:397-401` | `Hay precios que no sé de cuándo son — (…) sin fecha no se puede decir que el precio sea viejo, así que cuenta, pero no lo puedo fechar.` | Razonamiento interno | Reescribir a una frase |
| 50 | `paginas/Grupo.tsx:581-585` | `gama (por precio, no es calidad)` · `calidad (leída de ingredientes)` · `cercanía al mejor` · `promoción` | Jerga del modelo de pesos | Reescribir a etiquetas cortas («Calidad», «Precio») |
| 51 | `paginas/Grupo.tsx:663` | `Su precio por unidad y su precio de venta se contradicen: no puede decidir la comparación` | Diagnóstico de datos | Reescribir: «Precio poco fiable: no entra en la comparación» |
| 52 | `componentes/ControlPesos.tsx:18` | `Cuánto pesa que sea barato. El más barato del grupo se lleva el 100 % de esta parte.` | Fórmula del cálculo | Reescribir: «Cuánto te importa el precio.» |
| 53 | `componentes/ControlPesos.tsx:23-24` | `Cuánto pesa la letra A/B/C. Si sale de leer ingredientes es calidad; si sale de ordenar por precio es gama, y en ese caso la A es el MÁS CARO del grupo. Cada alternativa usa la que traiga y lo dice. Las dos no se suman nunca.` | La explicación de cálculo más larga de la app | Borrar; dejar una etiqueta |
| 54 | `componentes/ControlPesos.tsx:30` | `Cuánto pesa no alejarse del mejor. Vale 1 hasta un 5 % por encima del más barato y baja a 0 cuando llega al 50 % más caro.` | Fórmula | Reescribir: «Cuánto te importa no alejarte del más barato.» |
| 55 | `componentes/ControlPesos.tsx:36` | `Cuánto pesa que haya oferta que baje lo que pagas hoy en caja. Las de tarjeta cuentan la mitad: no bajan el precio, llenan un monedero.` | Fórmula + jerga de fidelización | Reescribir: «Cuánto te importan las ofertas que bajan lo que pagas hoy.» |
| 56 | `componentes/Etiquetas.tsx:120` | `Se acumula en un monedero: no baja lo que pagas en caja` (tooltip) | Jerga interna de promociones | Reescribir a «Solo con tarjeta del supermercado» |
| 57 | `componentes/Etiquetas.tsx:164` | `Sin comparación fiable no hay ahorro que dar` | Justificación interna | Borrar (la etiqueta ya dice «no lo sé») |
| 58 | `componentes/Etiquetas.tsx:172` | `Del mas barato al mas caro del grupo de equivalencias. No son necesariamente el mismo articulo: cada uno con su EAN. No es el ahorro de este.` | EAN + explicación | Borrar |
| 59 | `componentes/Etiquetas.tsx:193` | `Dentro del grupo hay precios que se contradicen por más del doble en la misma unidad. Sigue saliendo, pero no doy un ahorro que no se sostiene.` | Diagnóstico interno | Reescribir: «Comparación poco fiable» |
| 60 | `componentes/Etiquetas.tsx:230-231` | `Deducida por Open Food Facts: la tienda NO publica los ingredientes de este producto. Es una estimación de un tercero, no un dato del supermercado.` · `Leída de la lista de ingredientes que publica la tienda: aditivos, aceite de palma, porcentaje del primero y longitud de la lista` | Segundo tooltip explica el algoritmo de letras | Reescribir corto o borrar |
| 61 | `componentes/Etiquetas.tsx:244` | `Sale de ordenar por precio dentro del grupo, no de leer la etiqueta. Es gama, no calidad. En esta letra la A es el más caro del grupo.` | Explicación del cálculo | Borrar (la etiqueta ya dice «por precio, no es calidad») |
| 62 | `componentes/Etiquetas.tsx:262,268` | `Leída de los ingredientes` · `Por precio dentro del grupo: A es el más caro. No es calidad.` | Ídem, en tabla | Borrar/reducir |
| 63 | `paginas/Buscar.tsx:151-153` | `Catálogo pendiente de verificar — La versión publicada no coincide con las fechas de sus precios. Estos resultados no deben usarse para decidir dónde comprar hasta verificar la publicación.` | Aviso de administración | Mover al panel interno |
| 64 | `paginas/Buscar.tsx:220` | `Con una sola letra no busco: casaría con media tienda y la lista no diría nada.` | Explica la implementación del buscador | Reescribir: «Escribe al menos dos letras.» |
| 65 | `paginas/Buscar.tsx:373-375` | `Los filtros de dieta y de oferta se aplican a cada producto que se enseña, no al grupo entero: si el grupo solo cumple por uno de sus miembros, no sale. Un sello exigente deja la lista en nada en cuanto la palabra es amplia.` | Explicación del algoritmo de filtros | Borrar; dar el botón (ya está) |
| 66 | `paginas/Buscar.tsx-407` | `El orden se aplica a estos {N} resultados, no a todo el catálogo. Las filas sin precio por unidad se van al final cuando ordenas por precio: un dato que no tenemos no se coloca arriba como si fuera el más barato.` | Paginación + regla interna | Borrar |
| 67 | `paginas/Favoritos.tsx:120` | `Este grupo ya no está en el catálogo: puede que sus productos hayan desaparecido o que el emparejador los haya separado.` | «El emparejador» es interno | Reescribir: «Este producto ya no está en el catálogo.» |
| 68 | `paginas/Favoritos.tsx:297` | `Ventana para medir el cambio` (aria-label del grupo de botones) | «Ventana para medir» es jerga | Reescribir: «Periodo» |
| 69 | `componentes/Chispa.tsx:144-145` | `${etiqueta}: ${puntos.length} días de histórico, ${huecos} sin dato` (aria-label) | Métrica de relleno | Reescribir: «Precio por día» |
| 70 | `componentes/Chispa.tsx:153-154` | `Ver los ${puntos.length} días como tabla (${huecos} sin dato)` | Ídem, visible | Reescribir: «Ver la tabla de precios» |
| 71 | `componentes/LeyendaDeSeries.tsx:61-62` | `Dos series: ${dibujables} de 3. No hay objetivo puesto para estas fechas.` / `Tres series: ${dibujables} de 3.` | Métrica de relleno sobre la propia gráfica | Borrar |
| 72 | `componentes/LeyendaDeSeries.tsx:67` | `Lo que se dibuja en cada serie, y lo que se queda fuera` | Explica la tabla accesible | Reescribir: «Datos de la gráfica» |
| 73 | `componentes/TablaResultados.tsx:196-198` | `Del mas barato al mas caro del grupo de equivalencias.` · `con su EAN. No es el ahorro de uno solo.` | EAN + explicación | Borrar |
| 74 | `componentes/TablaResultados.tsx:405` | `Hay promoción que baja lo que pagas hoy en caja` | Útil para decidir, pero explica el criterio interno | Conservar (reformular corto) |
| 75 | `componentes/Suite.tsx:295` | `Aprender` | Menú que lleva a un marcador de desarrollo | Borrar del menú |
| 76 | `componentes/Suite.tsx:162` | `Sin lista de casa` (chapa del menú) | Estado interno del historial de listas | Reescribir: «Sin lista» |
| 77 | `paginas/Panel.tsx:100` | `Panel` | Nombre interno de una pantalla de consumidor | Renombrar la pantalla o sacarla del menú |
| 78 | `paginas/Panel.tsx:105` | `Panel de matching →` | Enlace a herramienta interna (P0-4) | Borrar del panel de consumidor |
| 79 | `paginas/Panel.tsx:251` | `Lo que entró hoy en el catálogo` | Métrica de ingesta | Sacar del alcance del consumidor |
| 80 | `paginas/Panel.tsx:276` | `Sobre cuántos productos se ha contado cada cosa` | Explica la tabla | Ídem |
| 81 | `paginas/Panel.tsx:284-285` | `Con Nutri-Score` · `Con EAN` | Cobertura de datos interna | Ídem |
| 82 | `paginas/Panel.tsx:423` | `Contar pasillos ganados es lo único que se puede comparar entre catálogos distintos` | Explicación del método | Ídem |
| 83 | `paginas/Panel.tsx:539` | `% de veces que gana` | Métrica interna | Ídem |
| 84 | `paginas/Panel.tsx:595` | `Sospechosos (más del triple)` | Jerga de control de calidad | Ídem |
| 85 | `paginas/Panel.tsx:639` | `Solo con letras leídas de una etiqueta de verdad, nunca con las que salen del precio` | Explicación del método | Ídem |
| 86 | `paginas/Panel.tsx:708-720` | `Lo que se desbloquea cuando haya más días` + `<code>{p.que}</code> — {p.para}` + `faltan N de M días` | Hoja de ruta con identificadores | Ídem |
| 87 | `paginas/Panel.tsx:1012` | `Índice encadenado` · `100 en la primera captura de cada cadena · Jevons encadenado sobre el precio de venta del mismo producto` | Método econométrico en el subtítulo | Ídem |
| 88 | `paginas/Panel.tsx:1016` | `La tabla no es un extra: el color de cinco series no se distingue, y el dato no puede depender de verlo bien` | Justificación de diseño | Ídem |
| 89 | `paginas/Panel.tsx:1066-1068` | `«Recortados» son los relativos fuera del rango creíble: el índice no los usa. Si fueran muchos, ese eslabón sería flojo y el índice estaría midiendo otra cosa.` | Explicación del cálculo | Ídem |
| 90 | `paginas/Panel.tsx:1072-1074` | `«Salto» son los días que cubre el eslabón más largo de esa cadena. Donde pasa de 1, la cadena no se rastreó ese día…` | Ídem | Ídem |
| 91 | `paginas/Panel.tsx:1197` | `solo sobre lo emparejado y con la misma unidad` | Jerga de emparejamiento | Ídem |
| 92 | `paginas/PanelMatching.tsx:50` | `Panel de matching` | Herramienta interna | Sacar (P0-4) |
| 93 | `paginas/PanelMatching.tsx:53` | `pasada {d.ultima.ejecucion_id}` | Identificador interno | Ídem |
| 94 | `paginas/PanelMatching.tsx:57-63` | `Esta pantalla no valida nada — No hay botón de aprobar ni de rechazar equivalencias, y no lo va a haber: en este proyecto no hay validación humana. Lo que se puede hacer aquí es auditar por qué el emparejador aceptó un par —su nivel, su método, su confianza y los rasgos que lo sostienen—…` | Explica el proyecto a sí mismo | Ídem |
| 95 | `paginas/PanelMatching.tsx:69-71` | `La API ha contestado bien, pero en data/gold/matching/ no hay ninguna carpeta ejecucion=… Cada pasada del emparejador deja la suya…` | Rutas de datos | Ídem |
| 96 | `paginas/PanelMatching.tsx:85-89` | `Versión {version_modelo} · umbral {0,55}` | Versión del modelo y umbral | Ídem |
| 97 | `paginas/PanelMatching.tsx:92-99` | `Ejecución` · `Productos` · `Umbral` · `Pasadas guardadas` con `ejecucion_id` | Identificadores | Ídem |
| 98 | `paginas/PanelMatching.tsx:103-104` | `Huella del catálogo: {hash}. Dos pasadas con la misma huella se hicieron sobre el mismo catálogo y se pueden comparar.` | Hash + explicación | Ídem |
| 99 | `paginas/PanelMatching.tsx:110-111` | `Métricas de la pasada` · `El nombre de cada métrica es el que usa el emparejador; no se traduce` | Nombres crudos, se avisa | Ídem |
| 100 | `paginas/PanelMatching.tsx:134` | `<code>{m.metrica}</code>` | Nombres de métricas sin traducir | Ídem |
| 101 | `paginas/PanelMatching.tsx:176-180` | `Comparado con la pasada anterior (…). La comparación con la anterior es la medida de estabilidad: un emparejador que cambia de opinión cada día no sirve para decidir una compra.` | Explicación del método | Ídem |
| 102 | `paginas/PanelMatching.tsx:188-205` | `Muestra de pares aceptados` · `los primeros ${n} de esta pasada, con su método y sus rasgos` | Jerga | Ídem |
| 103 | `paginas/PanelMatching.tsx:237` | `Confianza del emparejador, de 0 a 1` | Jerga | Ídem |
| 104 | `paginas/PanelMatching.tsx:244-246` | `Por qué: {n} rasgos` + claves de `features` | Nombres de rasgos sin traducir | Ídem |
| 105 | `paginas/PanelMatching.tsx:273-281` | `Ver la respuesta en crudo` + `<pre>{JSON.stringify(d, null, 2)}</pre>` | Volcado de la respuesta entera | Ídem |
| 106 | `paginas/PanelMatching.tsx:360-368` | `Este servidor todavía no tiene esa ruta — Esta pantalla pide GET /api/panel/matching y la API ha contestado 404. La ruta está en plataforma/api/main.py desde el 22 de septiembre… docker compose up -d --build api` | Endpoint, fichero y comando de despliegue | Ídem |
| 107 | `paginas/PanelMatching.tsx:372-383` | `Qué devuelve cuando está` + `ultima`/`metricas`/`cambios`/`pares`/`ejecuciones` + `Está en catalogo.matching(). Si al implementarlo cambia el contrato, se cambia también src/tipos.ts aquí.` | Contrato de API y ruta de código | Ídem |
| 108 | `paginas/PanelMatching.tsx:386-391` | `Esta pantalla no valida nada — No hay botón de aprobar ni de rechazar equivalencias, y no lo va a haber. En este proyecto no hay validación humana…` | Ídem | Ídem |

**Total: 108 textos.** De ellos, **18 son de `/panel/matching`** (filas 92-108), **10 del panel interno**
(77-91) y **8 del prototipo de Cocina** (23-28).

### 3.3 Textos §8 que están en código muerto (no visibles; no hay que reescribirlos)

Estos ficheros **no se montan** en ninguna ruta: `componentes/Cabecera.tsx` (no importado),
`componentes/Nav.tsx` (solo lo importa Cabecera) y `paginas/Inicio.tsx` (no importado en `App.tsx`).
Contienen textos que incumplen §8 —«No sé de qué día son los precios: la API no contesta»
(`Cabecera.tsx:72`), «ofertas semanales, no el catálogo entero» (`Cabecera.tsx:132`), «Un precio de más
de N días se enseña con su fecha, pero no decide dónde comprar» (`Cabecera.tsx:146-147`), «Estado de
las cadenas» (`Cabecera.tsx:111`)—, pero **no se ven**. Se resuelven borrando los tres ficheros
(§5, arreglo 10), no reescribiéndolos.

---

## 4. Estado de las funciones del alcance ampliado (David, 2026-11-05)

Resumen por función: **completo** = se puede usar de punta a punta · **a medias** = hay piezas, falta
cerrarlo · **falta** = no existe.

| Función | Estado | Qué hay (archivo:línea) | Qué falta |
|---|---|---|---|
| **Favoritos de productos** | **Completo** | Página `paginas/Favoritos.tsx` (ventana 7/14/30 días, variación por unidad, quitar, pasar a la lista); botón en ficha `componentes/BotonFavorito.tsx`; API `GET/POST/DELETE /api/favoritos` (`main.py:1287,1358,1366`); paso a lista `POST /api/listas/{id}/desde-favoritos` (`main.py:965`) usado en `api/cesta.ts:317` | Nada esencial. No probado con sesión (401 en la auditoría) |
| **Lista de la compra** | **Completo** (muy por encima de lo pedido) | `paginas/Cesta.tsx` (1 862 líneas): crear/renombrar, varias listas, compartir por enlace e invitación, quién está dentro y con qué papel, notas por línea, cantidad 1-99, tachar, cerrar compra, «dónde comprar la lista entera», reparto entre tiendas, cola de cambios sin conexión. API `main.py:585-1200` | Pulido (§2.3) y los textos de §8 de Cesta |
| **Calculadora de calorías diarias** | **A medias — es lo más flojo del alcance** | Diario real con API: `paginas/Diario.tsx`, `/api/diario/*` (`main.py` + `diario.py`), totales por día con cobertura y «sin dato ≠ 0»; gráfica de tres series preparada para **registrado / previsto / objetivo** (`componentes/GraficaDeLasTres.tsx`, `logica/puntosDeLasTres.ts:73-79` lee la preferencia `objetivo:<fecha>`) | **No hay calculadora ni objetivos**: nada escribe `objetivo:<fecha>` (solo se escriben `cadenas_cerca` y `lista_del_diario`: `Ajustes.tsx:46`, `Diario.tsx:163`), así que la tercera serie **no existe nunca**. No hay pautas de salud ni referencias. Y «Mis alimentos» es el prototipo en memoria (`Cocina.tsx`, P0-3) |
| **Recetas: establecidas** | **Falta** | El almacén es por usuario (`core/recetas.py:28` `data/recetas.sqlite`; dueño solo de la sesión, `core/recetas.py,110-113`) | **No hay recetas de la casa**: no hay semilla ni catálogo inicial. El recetario de un usuario nuevo está vacío (`Recetario.tsx:250-253`) |
| **Recetas: creadas por el usuario** | **Completo** | Alta con nombre, raciones, ingredientes y preparación (`Recetario.tsx:100-196` → `useCrearReceta` → `POST /api/recetas` `recetas.py:118`); edición por versiones (`componentes/FormularioReceta.tsx` vía `useCambiarReceta`); archivar y ver archivadas (`Recetario.tsx:207,241-243`); plan semanal (`PlanSemanal.tsx`, `/api/recetas/plan`); del plan a la lista (`PlanSemanal.tsx:233` → `/listas/{id}/desde-el-plan`); pasar receta a la lista con coste (`RecetaDetalle.tsx:47-113`) | Enlazar «Importar una receta» (`/compra/importar` existe y no tiene puerta, P2-1) |
| **Ofertas con detalle (tipo / club)** | **A medias** | Llegan `promo` (texto de la cadena), `promo_club`, `promo_unidades`, `promo_solo_online` (`tipos.ts:129,160-164,446-448`); se pintan en ficha (`Producto.tsx:480-481`), grupo (`Grupo.tsx:657,674`) y tabla (`TablaResultados.tsx:406-407,475-476`); el lector de mecánicas entiende `nxm`, `enesima`, `porcentaje`, `lote`, `precio_fijo`, `umbral`, `descuento_fijo` y marca `acumulable` y `solo_online` (`core/promos.py:112-222`) | **El tipo normalizado no viaja a la API**: `Mecanica.tipo` se usa para calcular pero no hay campo `tipo` en `tipos.ts`; `promo_solo_online` **no se pinta en ninguna pantalla** (grep: solo en `tipos.ts`). El usuario ve el texto de folleto, no «2x1» / «descuento» / «precio club». Tampoco hay «miembro del club» como preferencia (`cadenas_cerca` es lo único que hay, `Ajustes.tsx:46`) |
| **Avisos** | **Completo** | `paginas/Avisos.tsx` (ha bajado / saltó y ya no / esperando, con la frase guardada y el punto de sin ver); campana en ficha (`componentes/Campana.tsx`); API `GET/POST/DELETE /api/alertas` y `/api/alertas/vistas` (`main.py:1199-1244`); vigilante que las hace saltar solo (`vigilante.py`) | Falta la señal en el menú (P2-9). No probado con sesión |
| **Despensa** | **Completo (básico) y a propósito**: no hay «he comprado» | `paginas/Despensa.tsx` (declarar / gastar / «no se sabe cuánto»); `/api/despensa`, `/consumir` (`despensa.py:73-105`); la decisión de no deducir stock de la compra está escrita (`Despensa.tsx:8-10`) | Puerta de sesión (P0-1) y el texto del «servidor» (fila 16) |
| **Aprender de las listas** | **A medias** | Historial propio con decaimiento de 30 días y tres escalones (`api/habituales.py`, `almacen.historial_de`): «tuyo» → «de todos» → «compra básica», y el mosaico lo usa en Buscar y Cesta (`Mosaico.tsx`, `consultas.ts:156-162`). El reparto entre tiendas sugiere dónde comprar cada cosa (`RepartoEnTiendas.tsx`, `core/oracle_reparto.py`) | **No hay «sugerir la siguiente lista» ni rellenar sola**: no existe endpoint de propuesta de lista desde el historial (los únicos «desde…» son plan y compra: `main.py:1574,1830,1953,1993`). «Sugerir comprar en otro sitio» solo existe como reparto de una lista concreta, no como aviso sobre lo que se repite |

**Funciones que el alcance pide y no están en ninguna parte del código** (comprobado por grep): pautas
de salud / TDEE / objetivos de calorías; semilla de recetas de la casa; tipo de oferta normalizado
visible; lista propuesta automáticamente; cuentas de las apps de los supers (§5.5 del alcance).

---

## 5. Top-10 de arreglos, en orden de valor para el usuario

Orden por lo que **rompe o desluce la app que ya existe**, que es lo que David ha mandado hacer primero.
No por facilidad de arreglo.

1. **Poner la puerta de sesión en las seis pantallas que hoy escupen «La API ha contestado 401»**
   (Despensa, Recetario, RecetaDetalle, PlanSemanal, Diario, Tendencias). Es la primera impresión de un
   usuario nuevo: hoy es un error rojo con texto de programador. La pieza ya existe y está probada en
   Favoritos/Avisos/Cesta/Ajustes.
2. **Separar «Gasto y ahorro» del panel interno**: la subsección del menú debe enseñar **lo que has
   pagado** (`LoQueHasPagado`) y nada más; el cuadro de mando del catálogo (`Panel`, `PanelMatching`)
   sale del menú de consumidor. Hoy la pantalla que promete «gasto» abre 10 pestañas de ingesta.
3. **Quitar los textos §8 de las tres pantallas que más se ven** (ficha de producto y grupo, lista y
   buscador): las 44 filas de inventario que van de `Producto`/`Grupo`/`Cesta`/`Buscar`. La más grave:
   la sección «Por qué está emparejado con esos», que enseña el JSON del emparejador en cada ficha.
4. **Arreglar «Mis alimentos» o quitarlo del menú**: si se queda como está, todo lo que se anote se
   pierde al recargar (P0-3). La calculadora de calorías que David pide necesita primero un sitio donde
   los datos duren; el Diario ya lo tiene.
5. **Bajar la ficha de producto y la de grupo de 1,5–6 s a menos de 1 s** (P1-1): son las pantallas
   donde se decide la compra y `DOCTRINA-CALIDAD.md` §3 no admite más de 3 s. Medir qué parte del
   tiempo es DuckDB y cachear por `fecha_datos` (gold cambia una vez al día).
6. **Añadir la calculadora de calorías que falta**: un objetivo diario que la persona se pone (y que
   hoy la gráfica ya sabe leer en `preferencias['objetivo:<fecha>']`) y referencias explicadas sin
   prescribir. Es la función del alcance con más hueco y la que menos backend nuevo necesita.
7. **Sembrar recetas «establecidas»**: el recetario de un usuario nuevo está vacío y la mitad del
   alcance («recetas establecidas y creadas por usuario») no existe. Con el modelo actual (versiones,
   ingredientes, coste) basta con cargar un recetario inicial.
8. **Normalizar el tipo de oferta y enseñarlo**: `nxm`, `2x1`, `descuento`, `precio club`,
   `solo online` ya están leídos en `core/promos.py`; falta que viajen a la API y se pinten, y usar
   `promo_solo_online`, que hoy no se enseña. Es lo que David pide en el punto 4 del alcance y cambia
   la recomendación de dónde comprar.
9. **Sustituir `/aprender` por el índice real o quitarlo del menú**, y decidir si `CocinaModo`
   (`/compra/cocina/…`) e `ImportarReceta` (`/compra/importar`) se enlazan o se borran: hoy son dos
   pantallas terminadas a las que no se llega y una puerta que lleva a un párrafo sobre el repositorio.
10. **Limpieza que engaña**: borrar `componentes/Cabecera.tsx`, `componentes/Nav.tsx` y
    `paginas/Inicio.tsx` (código muerto con textos §8 dentro y una cabecera que parece global y no se
    monta), corregir el glifo roto `? de` del plan semanal, las tildes de Diario/Recetario/Despensa/
    PlanSemanal/CocinaModo y los tamaños de letra inventados; proteger `/api/docs` y
    `/api/openapi.json`.

---

## Anexo: órdenes usadas (reproducibles)

```powershell
# 1. Rutas de la web (todas 200, SPA)
foreach ($p in @('/','/compra','/compra/listas','/compra/favoritos','/compra/despensa','/compra/analisis',
  '/compra/importar','/compra/productos/aldi/80500','/compra/comparar/64466','/recetas','/recetas/plan',
  '/recetas/1','/calorias','/calorias/alimentos','/calorias/tendencias','/avisos','/ajustes','/panel',
  '/panel/matching','/escaner','/aprender','/unirme/ABC')) {
  (Invoke-WebRequest "http://127.0.0.1:8080$p" -UseBasicParsing).StatusCode }
# 2. API, con latencia (mediana de 2)
#    python del .venv con urllib; rutas de la tabla §1.2
# 3. Código: npm run tipos (exit 0) y npm test (376 pass) en plataforma/web/app
# 4. Enlaces: todos los to="..." de src/**/*.tsx contra las path= de App.tsx
```

**Lo que este documento no puede decir:** si los flujos con sesión (listas, recetas, diario, despensa,
favoritos, avisos) funcionan de punta a punta. Eso exige una cuenta y una sesión, y la auditoría se
hizo sin credenciales por instrucción expresa. La primera prueba de flujo con sesión queda pendiente y
es la que cierra el «sin errores» que pide David.
