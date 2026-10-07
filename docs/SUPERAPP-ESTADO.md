# SUPERAPP · Estado del trabajo

Encargo vigente: `docs/SUPERAPP-00-EMPEZAR-AQUI.md` (7 de octubre de 2026), con
`SUPERAPP-01` (diseño y producto), `SUPERAPP-02` (datos, Lidl e identidad) y `SUPERAPP-03`
(investigación y límites). Este fichero es el estado vivo: se actualiza **antes de cada pausa**
y es lo primero que hay que leer al retomar.

Reglas de lectura de este fichero: **terminado** = cumple su criterio de aceptación con evidencia ·
**verificado** = se ejecutó y pasó, pero no cubre todo el paquete · **pendiente** = no empezado.
No se mezclan las tres.

---

## Bitácora de la sesión SUPERAPP (commits, con lo que hizo cada uno)

| commit | qué dejó |
|---|---|
| `e50f04c` | **S00**: baseline congelado. Los cambios heredados se verifican y se preservan; 1.195 pruebas |
| `5b66bf2` | Fichero de estado vivo: plan S00–S12, decisiones cerradas, correcciones a las referencias de Stitch |
| `dcde817` | **S01**: publicación por versiones (carpeta por versión, puntero atómico, `rutas()` fija la versión por petición, rollback) + catálogo actual adoptado como primera versión |
| `247a9cc` | **S02 núcleo**: cola de fichas en SQLite (estados, *lease* con vencimiento, hash, evidencia, reenganche sin duplicar) |
| `9f06396` | **S02 medido**: inventario de 74.861 fichas desde bronze en 75,7 s (antes: sin terminar) |
| `6bfdfd1` y `fb4dc6a` | **S02 instrumento**: informe de cobertura por fuente con deuda de cola y edades |
| `240bad4` | **S03 primera mitad**: descubridor de Lidl (sitemap guardado, clasificación por *slug*, sin red) |
| `42683e7` | La «cuna» suelta fuera de la política: tercera vez que la trampa de las tildes mordía; queda cubierta por pruebas |
| `edb4d2d` | **S03 medido**: el sitemap real, 6.622 direcciones → 691 incluidas, 1.568 de bazar evitadas, 4.363 a revisión |
| `e09f5d3` | **Puente S03→S02**: lo descubierto entra en la cola con su evidencia; el bazar no genera trabajo |

**Lo que la puerta ha parado**: seis commits que habrían metido una regresión o una prueba mal
escrita. La práctica es: las pruebas corren **antes** del commit y si no pasan, no se commitea.

## Paquete actual

**S03 · Lidl — PRIMERA MITAD HECHA.** Siguiente: **las fichas de los 5.054 candidatos** (S03, segunda mitad).

## Baseline (S00)

| dato | valor |
|---|---|
| commit | `e50f04c` (S00 baseline: los cambios heredados, verificados y preservados) |
| padre | `f74c432` (muro al día) |
| `uv run pytest -q` | **1.195 pruebas en verde**, 2 avisos de dependencias |
| `uv run ruff check .` | limpio |
| `uv run python -m projects.cesta.verificar_docs` | verde (166 comandos comprobados) |
| árbol | limpio |

**Cambios heredados que se preservaron tal cual** (no son míos y no se reescriben):

- `core/schemas.py`: `ProductoRaw.disponible` pasa a `bool | None` — distinguir «no sé» de «sí».
- `projects/cesta/collectors/dia.py`: conserva tablas nutricionales **parciales** sin inventar los
  nutrientes ausentes, y exige finito y no negativo.
- `core/datos/alcance.yml`, `core/datos/secciones.yml`, `docs/CIFRAS.md`: al día.
- `projects/cesta/collectors/lidl.py`: ampliado (sitemap y fichas) — **leer antes de tocarlo**.
- `plataforma/web/app/*`: `App.tsx`, `Cabecera.tsx`, `Producto.tsx`, `BotonAnadirACesta.tsx`,
  `package.json` con preparación de pantallas.

**No hay credenciales en el repositorio.** Las claves que circulan por el chat de origen deben
revocarse fuera del repositorio; aquí no se guardan ni se piden.

## Plan de paquetes (orden de dependencias)

| ID | estado | nota |
|---|---|---|
| S00 baseline | **terminado** | commit `e50f04c`, puertas ejecutadas |
| S01 publicación versionada | **terminado** | `core/publicacion.py`: versión con puntero atómico, `rutas()` fija la versión de una petición y fallback al catálogo suelto; 8 pruebas de aceptación |
| S02 cola de fichas | **núcleo hecho y medido** | `core/inventario.py` en SQLite: alta idempotente, lease con vencimiento, estados del contrato, próxima revisión, hash y evidencia; enganche desde bronze histórico. Falta: medir el inventario real y que los colectores consulten la cola |
| S03 Lidl por sitemap y fichas | **en curso**: sitemap medido (6.622 direcciones, 691 incluidas, 1.568 excluidas, 4.363 a revisión) | `projects/cesta/descubrir_lidl.py`: lee un sitemap guardado, separa fichas de categorías, clasifica por *slug* con la política (bazar inequívoco fuera, comida nunca fuera por su URL) e informa en direcciones y no en alimentos. Falta: recorrer el inventario real y las fichas |
| S04 identidad y banco independiente | pendiente | depende de S02 |
| S05 selector único y optimizador | pendiente | depende de S04 |
| S06 armazón y sistema visual | pendiente | **no depende de S01**; puede ir en paralelo |
| S07 Compra | pendiente | depende de S05 y S06 |
| S08 Recetas | pendiente | depende de S02 y S06 |
| S09 Calorías | pendiente | depende de S02, S06 y S08 |
| S10 puentes entre aplicaciones | pendiente | depende de S07–S09 |
| S11 gráficas y rendimiento | pendiente | depende de S07 y S09 |
| S12 ensayo integral y cierre | pendiente | depende de todo |

## Decisiones cerradas (no volver a preguntarlas)

- Menú lateral de aplicaciones en escritorio; cajón accesible en móvil.
- React/Vite/TypeScript y backend actual; sin migrar de framework.
- Datos e infraestructura locales; sin despliegue público ni servicios de pago.
- **Calorías es privada por persona**, aunque Compra sea del hogar.
- Un ingrediente genérico no es un producto comercial exacto. **Comprar no es consumir.**
- Prioridad a la precisión: **la abstención es un resultado válido**.
- Aprovechar el crudo histórico antes de pedir; renovar fichas conocidas por cola.
- No buscar paridad artificial de filas con Aldi.
- v0 ya dio la dirección visual; **no consumir más cuota**. Stitch es referencia, no código.

## Correcciones obligatorias al portar las referencias de `.stitch/`

1. Colores y tamaños de `SUPERAPP-01` §1; **rechazar los 11 px** de Stitch (mínimo 13 px en
   metadatos, 14 px en tablas, 16 px en cuerpo). Borde suave `#D8D2C7` **solo** decorativo: no
   delimita un control (contraste 1,43:1).
2. Compra: el panel derecho sale cortado en la referencia; lenguaje cotidiano («Mi lista»,
   «Tiendas», «Total estimado»), sin «gasto provisionado» ni «referencia mercantil».
3. Compra: **eliminar afirmaciones ficticias** de auditoría de tickets, comprobación física y
   producto exacto verificado. Precio ausente ≠ sin stock. Promociones con condiciones y cálculo.
4. Recetas: «Preparar lista» **abre una propuesta que se confirma**, no añade sola. Cambiar
   raciones escala unidades y recalcula cobertura nutricional.
5. Calorías: conservar «subtotal conocido» y el día sin datos como **hueco**. Los datos de la
   captura son de ejemplo.
6. El HTML descargado usa recursos externos: **no pegarlo**; portar componentes y servir local.
7. Las tres referencias son de escritorio: verificar 390 y 768 px, zoom 200 % y teclado.

## Problemas pendientes conocidos

- **T03 (identidad) sigue sin empezar** y es lo que gobierna que las comparaciones sean correctas.
  1.014 candidatos por GTIN y 10.999 pares con contradicciones medidos en el laboratorio.
- **T11**: la ficha ya llega en Carrefour, DIA y Aldi y se tira al parsear; en Alcampo no llega.
  Falta la extracción con procedencia y fecha por campo.
- **Lidl**: el colector existe y está probado sin red; la primera captura real está pendiente y
  `--escribir` está detrás de una bandera porque la pasada diaria **descubre** las cadenas.
- **La plataforma web no está levantada** (Docker parado); los recorridos de interfaz se verificarán
  cuando se levante o con el servidor de desarrollo.
- Sin medir todavía: `plataforma/web/app` `npm run build` y `npm run test:cocina` en este baseline.

## S01 · Publicación versionada — HECHO (7 de octubre de 2026)

`core/publicacion.py`. Cómo cumple su criterio:

| exigencia de S01 | cómo se cumple |
|---|---|
| caída entre escrituras no mezcla versiones | cada publicación escribe en `data/gold/v<fecha-hora>/` y el **puntero** (`actual.json`) se cambia con `os.replace` **solo** cuando están todos los ficheros; si falla, la carpeta a medias se retira y el puntero no se mueve |
| rollback probado | las versiones no se borran; `fijar(version)` vuelve a una anterior y rechaza una incompleta |
| concurrencia probada | `rutas()` resuelve la versión **una vez** y devuelve todos los caminos de esa misma publicación: una petición no puede mezclar `grupos` de una con `enlaces` de otra |
| no romper lo que hay | sin puntero se lee el catálogo suelto de siempre (fallback conservador) |

Publicar **no borra** y una versión existente **no se sobrescribe**. 8 pruebas de aceptación en
`tests/test_publicacion.py`.

**Pendiente dentro de S01**: el pipeline todavía escribe los ficheros sueltos; hay que hacerlo
publicar por versiones y que la API lea con `rutas()`. Se hace al entrar en S02/S05, para no tocar
la tarea de las 06:00 a la vez que se cambia la lectura.

## S02 · Cola de fichas — núcleo hecho y medido (7 de octubre de 2026)

`core/inventario.py` + `tests/test_inventario.py` (9 pruebas). Lo que aporta y lo que se midió:

| cosa | valor |
|---|---|
| **inventario levantado del bronze histórico** | **74.861 fichas**, sin una sola petición de red |
| alcampo | 43.603 |
| carrefour | 17.283 |
| dia | 6.292 |
| mercadona | 4.477 |
| aldi | 3.206 |
| tiempo del enganche | **75,7 s** (antes: más de 710 s de CPU y sin terminar) |

**Ese 74.861 no es el surtido de ningún supermercado**: es lo **descubierto** en el histórico, la unión
de todas las capturas. Hoy el catálogo tiene 51.659 productos, así que el inventario es un 45 % más
grande: son productos que aparecieron en alguna captura y no están en la de hoy. Es justo para lo que
existe el inventario —no perder de vista lo que un día se vio— y es el denominador honesto para hablar
de cobertura, en lugar de contar filas de un día.

**Dos fallos propios que se corrigieron aquí, y cómo se encontraron:**

1. La evidencia reventaba si el bronze estaba fuera del repositorio (lo cazó la prueba del enganche
   con un bronze temporal: justo donde se prueba).
2. El enganche hacía un *upsert* por **(día, producto)**: millones de escrituras para guardar dos
   fechas, porque bronze guarda la misma ficha treinta días seguidos. Se agregó en memoria
   (primera y última fecha por producto) y se escribe una vez por fuente: de no terminar a 75,7 s.
   **Cambio de contrato declarado**: `enganche()` devolvía altas procesadas y ahora devuelve
   **productos distintos**, que es el dato que interesa; su prueba lo explica.

**Instrumento añadido**: `projects/cesta/informe_inventario.py`, el panel de cobertura por fuente
(descubiertos, sin ficha, con ficha, con contenido útil registrado y vencidas, más las edades por
tramos). Es lo que pide SUPERAPP-02 §8, es de solo lectura y no toca la pasada diaria.

## S03 · Lidl, primera medida real (7 de octubre de 2026)

`projects/cesta/descubrir_lidl.py` bajó el sitemap público **una vez** (robots.txt primero, una sola
petición, y el XML guardado para repetir el análisis sin red) y lo clasificó por el *slug* de cada
dirección. Resultado:

| medida | valor |
|---|---|
| direcciones en el sitemap | **6.622** |
| fichas de producto (no son categorías) | 6.622 |
| **incluidas por la política** | **691** |
| **excluidas (bazar inequívoco)** | **1.568** |
| **a revisión (la URL no decide)** | **4.363** |

**Lo que esto demuestra, que es justo lo que el encargo avisaba de no suponer:** 6.622 direcciones
**no** son 6.622 alimentos. Solo 691 entran sin más; 1.568 son bazar claro —carros de jardín,
colchones hinchables, tijeras de podar— y **se evitan sin pedir ni una ficha**, que es el objetivo de
esta mitad del paquete. Y **4.363 no se pueden decidir desde la dirección**: el sitemap de Lidl usa
slugs largos y a menudo en alemán, y forzar una decisión ahí sería inventar.

**Lo que no dice:** nada sobre el surtido. Es **catálogo público descubierto**, con cobertura
desconocida, y una dirección tampoco prueba que la página viva (el encargo documenta un 404 en el
mismo sitemap). La cobertura real la dirá la otra mitad de S03: las fichas.

**Puente hecho (7 de octubre de 2026)**: lo descubierto se da de alta en la cola de fichas (`--registrar`), con su evidencia; los incluidos y los que quedan a revisión entran como candidatos, y el bazar inequívoco se cuenta pero **no genera trabajo**. Así el recorrido completo queda: sitemap → inventario → informe de cobertura.\n\n**Pendiente de S03**: (1) las fichas de ese inventario, con cola y presupuesto, para resolver los
4.363 y traer ingredientes y nutrición; (2) el informe por fuente y familia; (3) las ofertas
semanales como segunda corriente, sin confundir «producto conocido» con «precio de hoy».

**Pendiente dentro de S02** (es lo que lo hará útil de verdad): que los colectores **consulten la
cola** —pedir ficha a quien le falta, renovarla a quien le vence y no volver a pedir la que está
correcta y en plazo— y el informe diario de cobertura por fuente y familia. Hasta entonces esto es
memoria escrita, no renovación.

### Lo que trae la ficha de Lidl, medido (7 de octubre de 2026)

Leído el fixture guardado (`data/lidl-ficha-ejemplo.html`), sin red. Trae **tres** bloques de datos
estructurados, y solo uno es del producto:

    [0] @type=Product        name, brand, description, gtin13, sku, image, offers, url
    [1] @type=Organization   LIDL
    [2] @type=Organization   Lidl (con el programa de socio)

**Tres consecuencias, y las tres cambian el plan:**

1. **Hay `gtin13`.** La ficha de producto **sí trae código de barras**, que la página de ofertas no
   traía. Eso alimenta directamente la identidad de S04: un GTIN válido y con procedencia es la vía
   fuerte para decir «este es el mismo producto en otra cadena».
2. **`sku` (11000174) no es un EAN.** Es el identificador interno. El contrato lo prohíbe
   expresamente y ahora está visto en el dato, no supuesto: confundirlos envenenaría las
   comparaciones.
3. **No trae ingredientes ni nutrición.** El JSON-LD da identidad, descripción y ofertas; la ficha
   nutricional tendrá que salir del **cuerpo HTML** o de otra fuente. Para T11 esto significa que las
   fichas de Lidl darán identidad y precio, y habrá que medir aparte cuánta nutrición publica.

Y dos cuidados que ya están escritos para el lector: la `description` viene con **HTML** (hay que
sanitizarla, no pintarla) y `offers` es una **lista** (varias condiciones: normal y club, con fechas).

**Pendiente inmediato**: escribir el lector sobre el fixture (producto → campos de bronze) con
`gtin13` validado, `sku` **nunca** como EAN, `description` saneada y las condiciones de `offers`
separadas. Y después medir cuánta nutrición hay en el HTML de la ficha, sin darla por hecha.

## S03 · El lector de fichas, funcionando sobre una ficha real (7 de octubre de 2026)

`projects/cesta/ficha_lidl.py` lee el JSON-LD de la ficha y lo convierte en campos del proyecto. Sobre
la ficha real guardada (`data/lidl-ficha-ejemplo.html`):

    nombre: Galletas rellenas · marca: SONDEY · descripción: Rellenas de crema de chocolate.
    id_fuente: 11000174 (sku, identificador interno)
    ean: 4056489574392   <- GTIN válido, dígito de control comprobado
    precio_cent: None    <- y no se ha inventado
    condiciones: 1 oferta con availability=InStoreOnly y SIN importe

**Dos hallazgos que cambian el plan:**

1. **La ficha de producto de Lidl da códigos de barras de verdad.** El `gtin13` pasa la validación del
   dígito de control, así que **S04 tiene por fin una vía fuerte de identidad** con una cadena: GTIN
   válido y con procedencia. Y queda visto en el dato que `sku` no es un EAN.
2. **Esa ficha no publica precio.** Su oferta dice `availability: InStoreOnly` y no trae importe. El
   lector devolvió vacío en vez de inventar un precio, que es exactamente la distinción del encargo:
   **reunir fichas y disponer de precios actuales son trabajos diferentes**. La aplicación podrá
   conocer un producto de Lidl sin fingir que sabe cuánto cuesta hoy.

**Decisiones del lector, cada una con su prueba:** `gtin13` validado (el que no cuadra no se usa pero
tampoco se tira en silencio: se guarda aparte), `sku` jamás como EAN, `description` convertida a texto
en vez de pintada, y **dos condiciones de oferta no se funden en un precio**. Nueve pruebas en el
fichero, seis nuevas. Suite completa: **1.233 en verde**.

**Pendiente inmediato de S03**: la cola mandando (pedir fichas a los 691 incluidos con presupuesto por
host y día, guardar hash del contenido útil y versión de parser, próxima revisión a 30 días) · medir
cuánta nutrición publica Lidl en el **cuerpo HTML**, sin darla por hecha · resolver los 4.363 a
revisión **con la ficha, no con el slug** · informe por fuente y familia.

## S03 · ¿Publica Lidl nutrición? Medido, y con reservas (7 de octubre de 2026)

Sobre el fixture guardado, buscando **estructuras** y no palabras sueltas (que es la advertencia del
propio encargo):

| búsqueda | resultado |
|---|---|
| campos de una tabla nutricional española (energía, grasas, saturadas, hidratos, azúcares, proteínas, fibra, sal, kcal, kJ…) | **1 de 12**, y el que aparece es `kj` ×2 |
| bases que hacen interpretable una tabla (`por 100 g`, `100 ml`, porción con peso) | ninguna base real; `porción`/`ración` son texto de interfaz |
| señales de ingredientes (la palabra, harina, azúcar, aceite, cacao) | **0 de 6** — en un producto que **es una galleta** |

**Conclusión provisional: la ficha de producto de Lidl no publica la ficha nutricional.** Da
identidad (GTIN válido), nombre, marca, descripción, imagen y ofertas; la nutrición no está.

**Y el límite de esta medición, que importa tanto como el resultado:** es **un** producto. Un producto
no es la fuente. Para poder decir «Lidl publica poca nutrición» hacen falta **varias fichas
estratificadas** (frescos, envasados, droguería) y contarlo como cobertura, no como conclusión de
catálogo. Mientras tanto se dice **una ficha medida**, no una tendencia.

**Consecuencia para T11**: si se confirma, Lidl aportará **identidad y precio** a la plataforma y su
nutrición será una **limitación de fuente** que se declara —no se rellena desde otra fuente sin
decirlo, y no se presenta como dato propio—.

## S03 · Cobertura de nutrición sobre seis fichas (7 de octubre de 2026)

Ya no es un producto. El colector guarda ahora **una copia por producto** (`data/fichas-lidl/<id>.html`),
así que las fichas se acumulan y el análisis es **offline y repetible**. Sobre las seis primeras,
sacadas de la cola con presupuesto:

| medida | resultado |
|---|---|
| fichas guardadas | **6** |
| **con datos estructurados de producto** | **6/6** — el lector las lee todas |
| con tabla nutricional (3+ campos) | **0/6** |
| con base interpretable (`por 100 g`) | **0/6** |
| con ingredientes (2+ señales) | **0/6** |

**Qué permite decir esto:** la ficha de producto de Lidl es **fiable para identidad** (GTIN, nombre,
marca, descripción, imagen, ofertas) y **no trae la ficha nutricional** en las seis medidas.

**Qué no permite decir:** que sea así en todo el surtido. Son **seis fichas de 5.046 candidatos**, y
la muestra no está estratificada por familia (frescos, envasados, droguería). Se dice cobertura de
esta muestra, no una propiedad de la cadena.

**Progreso de la cola con estas rondas**: `correcto` pasó de 0 a **8**, y quedan **5.046**
pendientes. Cada ficha cerrada deja su hash del contenido útil, su versión de parser y su próxima
revisión a 30 días.

## Siguiente paso concreto

**S03 · segunda mitad: las fichas de Lidl.** Los 5.054 candidatos están ya en la cola (691 incluidos
y 4.363 a revisión) con su evidencia, y 1.568 direcciones de bazar quedaron fuera sin generar trabajo.
Lo que falta, en este orden:

1. **Un lector de ficha de Lidl** a partir de una ficha guardada (fixtures primero, sin red), con lo
   que publique: marca, título, descripción, ingredientes, alérgenos, nutrición con su base, peso,
   envase y procedencia. Lo que no publique queda `no_publicado`, no `null` sin motivo.
2. **La cola manda**: pedir ficha solo a los `pendiente`, con presupuesto por host y por día, guardar
   el hash del contenido útil y la versión del parser, y dejar `proxima_revision` a 30 días (7 si hay
   conflicto). Reanudable y sin duplicar, como ya está probado en S02.
3. **Resolver los 4.363 a revisión** con lo que diga la ficha, no con el *slug*: es la única forma
   honesta de saber si esos productos son de la cesta.
4. **Informe por fuente y familia** (descubiertos, incluidos, excluidos, ambiguos, visitados, vivos,
   con GTIN, con nutrición, con precio vigente y errores), sin declarar cobertura completa.

**Antes de eso, una comprobación de una línea**: pasar `uv run pytest -q` y `uv run ruff check .`, y
confirmar que siguen verdes. La última suite completa verificada es **1.223**.

### Lo que queda del encargo, sin adornos

- **Terminado y verificado**: S00, S01, S02 (núcleo, inventario y cobertura) y la primera mitad de S03.
- **Sin empezar**: S04 (identidad exacta, con el laboratorio como diagnóstico y no como sustituto),
  S05 (selector único: **`_candidatos` recibe `fecha_tope` y no la aplica**, y sus llamantes pasan
  cadena vacía — es el primer arreglo concreto del paquete), S06 (armazón con menú lateral, sin los
  11 px de Stitch ni datos ficticios), S07 a S12.
- **Decisión pendiente del dueño**: ninguna que bloquee. Cuando toque verificar recorridos completos
  de interfaz hará falta **Docker arrancado** (hoy está parado y la plataforma no responde).

## Detalle histórico: S02 · Cola de fichas. Crear el registro por `(fuente, id_fuente, variante, ámbito)` con
`discovered_at`, `last_seen_at`, `detail_fetched_at`, `next_check_at`, hash del contenido útil,
versión de parser, intentos y resultado; estados (`pendiente`, `en_curso` con lease, `correcto`,
`parcial`, `no_publicado`, `bloqueado`, `error_temporal`, `no_encontrado`, `excluido`); reanudación
sin duplicar; y el inventario de cobertura que hoy no existe. Empezar por el **crudo histórico**,
que ya está descargado, antes de pedir nada.
