# Cesta: especificación maestra de producto y ejecución

Fecha: 18/10/2026. Base inspeccionada: `5204e2b`.
Encargo de David: desarrollar una superapp web y móvil propia, completa y profesional;
no prolongar una cadena de microarreglos que necesite a David como mensajero.

## 1. Autoridad, alcance y resultado

### Verificación adicional de `758cec8`: cerrar el contrato, no solo añadir un hash

M06 permanece en curso. M07 continúa sin depender de un nuevo permiso de David.
Esta revisión concreta la aclaración siguiente; no reinicia la cola M00–M22.

1. **Misma selección en ambos extremos.** El GET actual llama a `cotiza(lineas)`
   con toda la lista y `/cerrar` a `cotiza(en_el_carro)`. Con una línea en carrito
   y otra pendiente los sellos difieren sin cambiar precio alguno. Servir una
   cotización específica del carrito que se va a cerrar, distinguiéndola del
   coste de toda la lista. Hash, totales, cobertura y revisión del MISMO conjunto.
2. **Integración del cliente y obligatoriedad.** `cerrarCompra()` todavía no envía
   sello y el endpoint permite omitirlo y escribir igualmente. Conectar tipo,
   cliente, formulario y respuesta de conflicto. La ruta ordinaria protegida
   exige revisión; compatibilidad sin revisión, si se mantiene, se identifica
   como tal y no se certifica como cierre confirmado. Alinear campos nullable
   (`estimado_cent`, `diferencia_cent`) en API/TS y no formatear null como cero.
3. **Snapshot y concurrencia.** `cotiza` calcula estimación y coste por separado;
   `/cerrar` vuelve a calcular coste y `almacen.cierra_compra` relee líneas.
   Un hash válido antes no impide publicar catálogo o editar cantidades después.
   Obtener un resultado coherente sobre snapshot/version de catálogo y revisión
   de lista, y guardar ese mismo resultado. Validar/serializar cambios concurrentes
   en la transacción correspondiente; reintento de una compra no crea otra.
   Test con cambio entre comprobación y persistencia, no solo entre dos llamadas
   aisladas a funciones. No basta «añadir usuario al string del hash».
4. **Métrica sobre etiquetas evaluables.** El medidor ya cuenta desconocidos, pero
   sigue dividiendo `exactos_bien / exactos`, donde exactos incluye los pares sin
   etiqueta. Reproducción: un acierto conocido + un exacto sin etiqueta da 0,5,
   cuando la precisión sobre los evaluables es 1,0. Denominador = exactos con
   etiqueta conocida; si no hay ninguno, precisión null. Informar por separado
   predicciones totales, evaluables y sin etiqueta. Probar todo desconocido,
   conocido+desconocido y falso conocido+desconocido; revisar también `sirve`.

Reproducciones añadidas al script `scripts/auditar_cierre_y_banco_20261018.py`.
Las pruebas dirigidas actuales de banco/cierre (15) pasan, lo que NO acredita
estos casos ausentes. Las reproducciones son con dobles y no tocan bases.

No usar «M08–M22 sin empezar» para borrar funcionalidades existentes: significa
aceptación de esta entrega pendiente de auditar/completar, no ausencia de código.
Al cerrar este contrato, construir el banco M07 y seguir las entregas amplias.

### Aclaración operativa tras revisión de `dae4cf4`

Esta aclaración forma parte del contrato y prevalece sobre interpretaciones de
M06/M07 de las rondas 85–94. No sustituye la cola M00–M22 por otra tarea pequeña.
Primero corregir las desviaciones siguientes en una entrega vertical; después
continuar M07→M08 y el resto de la cola sin pedir una nueva autorización rutinaria.

Diagnóstico ejecutable: `uv run python -m scripts.auditar_cierre_y_banco_20261018`.
En `dae4cf4` reproduce mediante dobles, sin red ni escrituras en bases:

- Estimación mostrada 100, precio nuevo 120: el endpoint devuelve estimado 120 y
  diferencia 0 porque recalcula DESPUÉS de guardar. No ha retenido lo mostrado.
- Línea con DIA elegido y único candidato Aldi: el cierre devuelve Aldi a 90.
  La ausencia en una captura tampoco demuestra que DIA no lo venda.
- `cierto=None` en el banco se convierte con `bool(None)` en una etiqueta negativa
  y se cuenta como falso exacto. Desconocido no es falso.
- `VIAJE_CENT=150` impone una valoración que no ha introducido la persona.

Son reproducciones de contratos con dependencias sustituidas, no certificaciones
de HTTP/PostgreSQL ni del conjunto de precios reales. Crear las regresiones
correspondientes del servicio, endpoint montado, persistencia y componente.

**M06: reglas que no requieren decisión de David.**

1. Viaje opcional: sin valor introducido o escenario explícitamente activado,
   `viaje_cent=null`, `neto_cent=null`; mostrar ahorro bruto y número de tiendas.
   Cero introducido es cero conocido. No deducir 1,50 EUR ni monetizar el tiempo
   por defecto. No dictaminar «no merece la pena» como hecho universal.
2. Conservar la estimación que se confirmó: identificador/revisión de cotización
   ligada a usuario/lista/líneas/cantidades/elecciones/condiciones y publicación.
   Obtener sus cifras de una referencia servida y verificable, no aceptar como
   verdad un total arbitrario enviado por el cliente. Recalcular ambas cifras
   al cerrar no permite detectar lo que cambió desde que la persona lo vio.
3. Si la revisión o elegibilidad cambia, devolver una nueva previa y exigir
   confirmación antes del cierre, o un conflicto explícito recuperable. Bajo la
   misma revisión debe cumplirse estimación aceptada = cierre = histórico.
   Probar A=100 → B=120: aviso +20 y nueva confirmación, sin escritura previa
   silenciosa; probar también bajada, cambio de cantidad y rechazo/reintento.
4. Precio de web/catálogo NO es evidencia de dinero pagado en caja. Guardar
   procedencia del importe: calculado según catálogo, declarado por usuario o
   acreditado por recibo cuando exista esa función. No llamar «gasto pagado» a
   una suma inferida de gold. Una compra puede guardarse como registro estimado
   explícito; la corrección a importe real requiere confirmación y trazabilidad.
   Históricos sin procedencia conocida se conservan como desconocidos, sin
   reescritura masiva ni falsa certificación de pago.
5. Tienda elegida ausente/ineligible: línea sin oferta elegible en esa tienda,
   motivo y alternativas separadas. Nunca escoger otra y guardarla como si la
   persona hubiera comprado allí. Cambiar tienda/producto requiere aceptación.
   Las líneas manuales o sin precio pueden conservarse como parciales explícitas;
   no se borran ni se les inventa coste para cerrar.
6. La prueba del endpoint debe invocar el endpoint o cliente HTTP real sobre
   sandbox. Construir un diccionario esperado dentro del test no demuestra qué
   devuelve `/cerrar`. La prueba de viaje debe ejercer el servicio y la UI,
   no limitarse a `400 - 150 == 250` ni exigir que exista una constante arbitraria.

**M07: el banco no está bloqueado esperando autorización humana.**

El agente está autorizado a preparar y anotar pares utilizando raw y fichas
públicas permitidas existentes, con evidencia por par, autor agente y fecha.
No necesita preguntar si puede hacerlo: esto es investigación de datos dentro
del encargo. Revisión humana y adjudicación de ambigüedades son posteriores.
No atribuir anotaciones automáticas a una persona ni llamarlas gold humano.

- Cada par lleva IDs, snapshots/hash/fecha, cadena/categoría, relación anotada,
  estado conocido/desconocido, evidencia concreta y autor/proceso de anotación.
- No usar `decide()` para generar la verdad con la que luego se evalúa a sí mismo.
  Reglas débiles/pseudoetiquetas van en un conjunto distinto de evaluación.
  Si la evidencia no permite decidir, conservar desconocido y causa.
- Los al menos 200 pares son un objetivo de muestreo estratificado, no permiso
  para completar con copias, cambiar etiquetas o inventar fuentes. Si faltan
  pares adjudicables, entregar el subconjunto y el déficit por estrato y continuar.
- Separar ajuste/evaluación por entidades o familias relacionadas para limitar
  filtraciones; no permitir el mismo par invertido o duplicado en ambos lados.
- El esquema admite bool real para igualdad acreditada y desconocido explícito;
  rechazar cadenas `"False"`, números u otras entradas ambiguas en vez de aplicar
  `bool(...)`. Desconocidos no se cuentan como negativos en precisión/recall.
  Informar cuántos hay y cobertura de anotación además de abstención del motor.
- Validar etiqueta/procedencia, duplicados y partición antes de medir. Una
  precisión sin predicciones es `null`, no «perfecta». El campo `sirve` no
  acredita la calidad de las etiquetas ni habilita publicación automática.

Estos cambios REABREN M06. M07 continúa con la construcción del banco, no se
detiene tras escribir el medidor. No declarar cierre por «7 de 7» ni por pruebas
que solo comparan dos funciones con el mismo supuesto equivocado.

Este documento sustituye operativamente los encargos parciales de validación de
octubre. Reutiliza B00–B16 del plan del 13, sin asumir que sus cierres acreditan
los recorridos actuales. No borra historia ni cambios ajenos. El orden vigente es:

1. `SUPERAPP-GOAL-ACTUAL.md`, bloque vigente del 18.
2. Esta especificación: producto, contratos y criterios de aceptación.
3. `SUPERAPP-EJECUCION-2026-10-18.md`: estado corto, evidencias y siguiente acción.

Construir y verificar, no limitarse a proponer. Si una capacidad existe, medirla y
completarla; no reimplementarla por cambiarle el nombre. Una pantalla nueva debe
resolver una tarea nueva o una limitación demostrada. El éxito comercial o la
popularidad no se pueden prometer mediante código: sí una experiencia diferencial
que pueda ponerse a prueba con personas.

Tres espacios con navegación separada: Compra, Recetas y Calorías. La propuesta
propia es «tu semana doméstica con cuentas claras»: de cinco platos a necesidades,
envases, tiendas, sobrantes y porciones, con explicación de cada cifra. No una
colección de dashboards ni un clon de una aplicación comercial.

Móvil significa en esta entrega web responsive y PWA instalable cuando el entorno
lo permita. No se presupone una app nativa ni publicación en tiendas. Dejar una
evaluación nativa posterior; no detenerse para preguntar por React Native/Flutter.

## 2. Base observada, no certificado de toda la aplicación

Preparación de este encargo por GPT:

- Leídos rutas de `App.tsx`, navegación de `Suite.tsx`, dependencias del frontend,
  cálculo de comparación, plan previo, seguimiento y módulos de datos/recetas/diario.
- HEAD `5204e2b`. Sus resultados 104 frontend, 23 Python y demás puertas son del
  informe de DeepSeek; no se han repetido en esta preparación.
- En `Producto.tsx` la tabla conserva el cálculo `delMismo` sobre el grupo entero,
  aunque la frase ya consume `construyeComparacion`. El propio traspaso lo reconoce.
- La función de comparación filtra números finitos, pero no representa todavía por
  sí sola toda la elegibilidad temporal, regional y comercial. No llamarla selector
  completo por el nombre de un comentario.
- `package.json` no declara ESLint de hooks, Testing Library ni Vitest. Instalarlos
  localmente, si hacen falta, es un paso autorizado, no un bloqueo de producto.
- `/aprender` sigue mostrando que el índice llegará: existen capítulos en
  `docs/aprende`, no una experiencia de aprendizaje navegable terminada.
- Foto de `/api/estado`: publicación `20261018-131107`, fecha general 18/10;
  Alcampo 22.789, Aldi 2.494, DIA 5.743, Lidl 76 y Mercadona 4.169 del 18;
  Carrefour 16.561 del 17 y `al_dia=false`. Esto es frescura, no cobertura total.
- `runs.csv` del 18 registra Carrefour 0 filas, 1 error, `False`; Alcampo 22.802,
  0, `True`. Investigar Carrefour sin lanzar otra pasada si ya hay una activa.
- Lidl está en el runner diario con `--web --escribir`; la vía actual recoge ofertas
  parciales. Ni 79 filas ni similitud con Aldi prueban catálogo completo.
- README conserva «tres colectores» y «ningún campo se queda vacío»: ambas reglas
  requieren actualización. No rellenar huecos nutricionales por cumplir una frase.

La base tiene mucho trabajo útil: contratos, parsers, cuarentenas, emparejamiento,
motor de coste, datos privados, plan/cocina, diario y pruebas. La cola siguiente no
declara que todo falte: exige auditoría por capacidad, reutilización y evidencia.

## 3. Decisiones de producto ya tomadas: no volver a preguntarlas

- Núcleo: alimentación, bebidas, frescos, higiene, limpieza, bebé, mascotas y
  consumibles de casa. Reutilizables domésticos habituales en sección optativa,
  sin contaminar nutrición. Fuera televisores, muebles y bazar ajeno a este uso.
- Artículo exacto, familia y alternativa son relaciones distintas. El producto
  elegido no se sustituye sin autorización explícita y revocable por línea.
- Identidad desconocida no es identidad distinta. Coincidir en nombre, unidad o
  embeddings no acredita exactitud. EAN válido es evidencia, no permiso para ignorar
  contradicciones de presentación, variante, pack o dato desactualizado.
- Un ingrediente genérico puede tener alternativas; un artículo elegido conserva
  marca/variante/formato. Las elecciones afectan a esa operación, no al histórico.
- Comprar, planificar, preparar y consumir son eventos distintos. Ninguno de los
  tres primeros crea entradas del diario personal automáticamente.
- Destino de lista explícito; se puede recordar por usuario y pedir confirmación
  al cambiar. Nunca sustituir casa por la primera lista accesible silenciosamente.
- Recetas privadas por defecto; compartir es explícito. Listas del hogar no hacen
  públicos el diario ni objetivos personales. Datos legados sin dueño se conservan
  cerrados, sin adjudicación automática.
- Fuentes parciales pueden ofrecer precios observados elegibles. No observación
  significa desconocido, no agotado, retirado ni coste cero.
- Sin nutrición, tamaño, densidad, precio o coste de desplazamiento: desconocido.
  Un cero conocido se conserva como cero. No prescribir objetivos de salud.
- Alcance inicial local sin gastos. No publicar internet ni abrir acceso LAN externo
  automáticamente. Preparar el despliegue y sus verificaciones, no ejecutarlo.

## 4. Autonomía autorizada y límites

DeepSeek puede leer, modificar y probar este repositorio; crear fixtures, scripts y
migraciones aditivas; añadir dependencias gratuitas de desarrollo con lockfile;
ejecutar servidores de ensayo en loopback y puertos libres; generar assets propios
sin coste; refactorizar módulos para cerrar contratos; y hacer commits propios
con pruebas y cambios relacionados. No necesita permiso por cada botón ni fichero.

Mantener React/Vite/TypeScript y el stack Python existente. No migrar Tailwind ni
framework/base de datos para esquivar un fallo. No añadir dbt/Dagster, vectores o
LLM remoto solo para ampliar el stack. Medir necesidad antes de incorporar runtime.

Prohibido sin decisión adicional: pagar, subir datos personales o crudos a terceros,
usar las claves pegadas en conversaciones, crear cuentas comerciales, publicar,
modificar otros proyectos, resetear Docker, podar volúmenes o restaurar bases existentes.
No eludir CAPTCHA/WAF, restricciones de acceso, login o licencias.

Bases 5432 (casa), 5433 (facylf) y 5434 (ensayos compartidos) no son destinos de
restauración. Crear entorno desechable único con marcadores de pertenencia, DSN
verificado en cada subproceso y puerto libre. Nunca matar «el proceso del puerto»:
cerrar solo procesos/contenedores iniciados y registrados por este trabajo.

Preservar modificaciones previas de secciones, CIFRAS, controles y goals. Este
encargo autoriza añadir el bloque vigente al goal, no adjudicarse ni commitear lo
ajeno. Una ejecución de ingesta no se duplica ni interrumpe para hacer pruebas.

Preguntar solo por gasto/publicación, credenciales, interacción humana, acceso fuera
del alcance o una migración irreversible. Preferencias menores se resuelven con
defaults de este documento. Un bloqueo de fuente o dispositivo no bloquea el resto.

## 5. Diseño distintivo y arquitectura de pantallas

Mantener papel/marfil, bosque y terracota, Fraunces e IBM Plex Sans locales y los
tokens existentes. Evolucionar composición e interacción con código propio, no
repintar cada ronda. «Profesional» no equivale a tarjetas estiradas ni a eliminar
clases Tailwind; equivale a entender y completar la tarea con datos representativos.

| Espacio | Pantallas/áreas | Resultado que la persona consigue |
| --- | --- | --- |
| Inicio | Continuar, pendientes, próxima comida, estado de datos discreto | Elegir tarea en segundos |
| Compra | Búsqueda/pasillos, ficha, comparador, listas, favoritos, tienda, gasto | Saber qué, cuánto y dónde comprar |
| Recetas | Biblioteca, ficha/editor, plan, previa de compra, cocina, despensa | Organizar la semana y aprovechar lo disponible |
| Calorías | Diario, añadir, alimentos/recetas personales, previsto, tendencias | Registrar porciones reales y entender sus datos |
| Común | Hogar, preferencias, datos/fuentes, exportación, aprender | Controlar privacidad y confianza |

Reutilizar rutas presentes: `/compra`, `/compra/listas`, `/compra/productos/...`,
`/compra/comparar/...`, `/compra/analisis`, `/recetas`, `/recetas/plan`, `/calorias`,
`/calorias/alimentos`, `/calorias/tendencias`, `/ajustes`, `/avisos`, `/aprender`.
Despensa y cocina deben ser descubribles desde Recetas aunque conserven redirecciones
de compatibilidad de `/compra`. Inventariar enlaces reales, no arreglar código muerto.

Cada pantalla tiene una acción dominante, estados de carga/error/vacío/parcial,
vuelta coherente y unidades pegadas a las cifras. Divulgación progresiva: respuesta
corta arriba; cálculos, procedencia y alternativas detrás de «cómo se calcula».

Móvil: uso con una mano, teclado virtual sin tapar confirmaciones, safe areas,
objetivos táctiles de 44 px, modo tienda sin ruido, selección de cantidades fácil.
Escritorio: lateral real, lectura en columnas cuando ayude, filtros sin laberinto.
No convertir toda tabla en un bloque ilegible ni exigir scroll horizontal al cuerpo.

Evaluar 360/390/768/1280/1440 px, oscuro/claro, zoom 200 %, teclado/foco/lector de
pantalla. Drag-and-drop siempre con alternativa de botones/teclado. Iconos con nombre.
No imponer altura completa si empeora el formulario. Usar fotos autorizadas y
fallbacks dignos; no añadir productos o precios ficticios en modo normal.

### 5.1. Composición de las pantallas principales

No hace falta pedir otro diseño a David. Estas son las decisiones de partida;
pueden mejorarse con evidencia de uso, conservando tareas y contratos:

- **Inicio:** «Tu casa, esta semana», continuar donde estaba, una fila de tareas
  (lista pendiente, próxima preparación y último registro) y acceso a los tres
  espacios. Nada de presentar un total energético como salud del hogar.
- **Buscar:** consulta persistente arriba; filtros activos retirables; resultados
  con foto, nombre/variante/envase, marca, precio envase, precio normalizado y fecha.
  Acción «Añadir este» y acceso a comparar. Filtro de familia no implica equivalencia.
- **Ficha:** identidad y presentación arriba; respuesta exacta «dónde y cuánto»,
  condiciones y cobertura; precio histórico del mismo artículo; detalles/nutrición;
  alternativas claramente separadas. En móvil precio y acción no quedan enterrados
  bajo párrafos de metodología. Ayuda técnica plegada, accesible por teclado.
- **Comparar:** selector de referencia persistente; columnas de ofertas exactas
  con envase/base/condiciones/fecha, y sección aparte de alternativas. Una selección
  permanece al cambiar filtros. No usar color para esconder una exclusión.
- **Lista:** selector y ámbito de lista, entrada rápida, progreso, presupuesto si
  existe, secciones por pasillo y control de cantidad. Resumen inferior de coste
  conocido/faltantes; modo tienda reduce controles secundarios sin quitar deshacer.
- **Dónde comprar:** tres opciones entendibles: una tienda, hasta dos y elección
  manual. Cada tarjeta indica importe, líneas cubiertas, faltantes, club y viajes.
  «Más barato» solo dentro de un universo equivalente y elegible; detalle por línea.
- **Recetario/ficha:** biblioteca con búsqueda, colecciones y filtros; foto/fallback,
  tiempos, raciones, coste por ración parcial y cobertura nutricional. Ficha con
  ingredientes y pasos en columnas en escritorio, pestañas/secciones en móvil.
  Acciones claras: planificar, llevar a lista, cocinar; no registrar consumo al pulsar.
- **Plan:** semana con día/comida y raciones; móvil usa días navegables sin siete
  columnas microscópicas. Resumen previsto y «Preparar compra» con contribuciones,
  despensa, envases y destino. Copiar semana permite revisar antes de confirmar.
- **Cocina:** paso actual dominante, ingredientes escalados accesibles, temporizadores
  visibles, volver/reanudar. «Preparado» distinto de «He comido una porción».
- **Diario:** fecha/comida y CTA «Añadir», entradas con porción y procedencia;
  subtotal conocido y cobertura cerca, no en letra pequeña. Previsto y objetivo en
  bloques identificados; corrección accesible sin borrar/recrear por obligación.
- **Tendencias:** elegir pregunta/periodo, una gráfica principal y tabla alternativa;
  cubrir coste, precios o nutrición según el espacio, no mezclar todos los universos.
- **Ajustes y fuentes:** hogar/permisos, listas predeterminadas, región/club, temas,
  objetivos opcionales, exportación y estado de fuentes. Herramientas técnicas del
  operador fuera del recorrido ordinario y nunca expuestas sin autorización.

### 5.2. Prueba de usabilidad y métricas del producto

Crear un guion corto para una persona no autora: encontrar un artículo exacto,
explicar la alternativa, añadir/tachar/deshacer, planificar un plato y registrar
media ración. El agente puede comprobar mecánica y legibilidad, no afirmar que
una persona real lo entendió sin esa sesión. No bloquear código independiente
esperando a David: entregar el guion, hallazgos automáticos y validación humana pendiente.

Medir sin analítica remota por defecto: tiempo/pasos/errores por tarea en sandbox,
cobertura de precios y detalles, porcentaje de comparación exacta y abstenciones,
reintentos/recuperación, y coste completo frente a parcial. No usar cantidad de
pantallas, tests o filas como única métrica de valor. No registrar hábitos personales
de producción como telemetría sin consentimiento.

## 6. Contratos compartidos obligatorios

1. Artículo estable: fuente + id de fuente; presentación, variantes, pack, EAN/GTIN
   y evidencias con fechas. No usar ordinal de grupo como identidad histórica.
2. Oferta observada: artículo, tienda/región/canal, precio/envase y base normalizada,
   fecha observada, vigencia, condiciones club/cupón, disponibilidad declarada o desconocida.
3. Comparación: referencia solicitada, identidad, base, elegibilidad, motivos de
   exclusión, universo de ofertas, costes y versión. La ficha, tabla, lista y
   gráficas no reinventan cuatro mínimos. Si backend y TS calculan, compartir un
   contrato de fixtures y comprobar paridad; preferir backend autoritativo para coste.
4. Necesidad: ingrediente, identidad/genérico, cantidad decimal, dimensión, receta/
   ocurrencia origen, despensa aplicada, envases, sobrante y contribuciones.
5. Operación: id/clave, propietario, destino, huella, revisión de entrada, estado y
   recibo. Mismo id y contenido distinto produce conflicto; reintento no duplica.
6. Consumo: persona, fecha local/comida, alimento o receta/version, porción real,
   snapshot, origen por nutriente y cobertura. Histórico no se recalcula con hoy.
7. Publicación: manifiesto y huellas; una petición usa una versión consistente.
   Publicar en medio de una visita no autoriza un fallo ni una suma híbrida.

Dinero en céntimos con reparto determinista; cantidades con precisión suficiente.
No comparar €/kg con €/ud; sí convertir dimensiones compatibles con datos acreditados.
El mismo envase exacto puede compararse por precio de venta aunque falte una base
normalizada común, si la presentación queda verificada. Peso variable no es envase fijo.

## 7. Programa de trabajo: entregas completas, no rondas de dos líneas

Orden: R0 = M00–M04; R1 = M05–M08; R2 = M09–M13; R3 = M14–M18;
R4 = M19–M22. Completar lo independiente si una dependencia externa falla.
No considerar un paquete «hecho» hasta código + contrato + prueba real + UX + docs.

### M00. Arranque seguro, estado y banco de ensayo

Leer estado actual, git, tarea diaria, lock y publicación antes de ejecutar.
Crear un comando de preparación/limpieza del sandbox con manifiesto de recursos
propios, PostgreSQL y SQLite separados de casa; probar las guardas antes de DDL.
Sembrar usuarios A/B, listas con/sin casa, 5 recetas, despensa, ofertas y avisos.
El catálogo de ensayo es pequeño y versionado; no depende del producto del día.
Aceptación: rechaza DSN protegido sin escribir; limpieza no toca recursos ajenos;
dos ejecuciones reproducen el mismo escenario y se conoce cada proceso creado.

### M01. Cerrar todas las superficies de comparación

Arreglar ahora la columna «diferencia +41 %» de `Producto.tsx`. Auditar ficha, grupo,
buscador, favoritos, avisos, reparto, estimación y gráficas; no solo el titular.
Construir un resultado común con relación exacto/familia/alternativa/desconocido,
base acreditada y elegibilidad. Contar fuentes distintas incluyendo el elegido aunque
no venga en candidatos. Separar horquilla, diferencia del elegido y ahorro por envase.
Desconocido en base neto/escurrido no se convierte en false por `Boolean(null)` salvo
que el contrato documente y acredite ese significado. Evitar mínimos inválidos/NaN.
Aceptación: Pote DIA/Carrefour mismo artículo, Hacendado alternativa; ninguna columna
resta el Hacendado como ahorro del Pote. Caso positivo de mismo artículo más barato,
caso elegido más barato y caso sin EAN. Unidad y alcance presentes en cada cifra.

### M02. Pruebas reales de frontend y recuperación de errores

Instalar/configurar ESLint y `eslint-plugin-react-hooks` con soporte TS. Adoptar
Testing Library + jsdom/Vitest o runner equivalente compatible; no es obligatorio
reemplazar los tests Node actuales. Lockfile y scripts reproducibles. Versiones
compatibles comprobadas; añadir dependencias es parte del trabajo autorizado.
Prueba del componente montado: carga → dato válido → ficha y armazón; respuesta
retenida/error/ausencia, cambio de artículo y caché. Capturar error React y contexto.
Añadir ErrorBoundary útil: mensaje recuperable, identificador y reintento; no ocultar
errores ni declarar éxito porque ya no está en blanco. Mantener privacidad en logs.
Aceptación: reintroducir el hook tras return hace fallar la regla; retorno partido
y componente flecha también. Reintroducir el fallo funcional hace fallar el ensayo.

### M03. Calorías: resolver el puente de compra sin atajos

Selector explícito de lista autorizada, recordado por persona; indicar sin lista
de casa aunque existan otras. Carga/error/no selección son estados distintos.
No crear otra casa por consultar caché vieja: invariantes en servidor, conflicto
comprensible, concurrencia A/pestaña2. No adjudicar listas antiguas automáticamente.
Previa de compra sin escrituras, con cantidades/origen/cobertura, y porciones que la
persona confirma; nunca asumir que consumir todo el envase equivale a una ración.
Una compra sin cerrar explica por qué no propone contenido, no bloquea toda la app.
Aceptación: cuentas sin listas, sin casa y con casa; selección y recarga; confirmar,
reintentar, corregir y volver a consumir legítimamente. Usuario B no obtiene datos de A.

### M04. Contratos de API y publicación durante uso

Auditar respuesta real frente a tipos TS: EAN, ingredientes, nutrición y detalles.
Eliminar tipos que prometen campos que no viajan. Fixture de contrato capturado y
anonimizado + endpoint montado con datos controlados + componente consumidor.
No llamar integración a comprobar una constante escrita a mano. No hacer fallar un
test porque el servidor añada un campo compatible; validar semántica y campos usados.
Probar búsqueda paginada, ficha abierta y lista durante cambio de versión; fijar o
avisar actualización sin mezclar series ni perder formulario. No invalidar datos
privados con claves globales: aislar cuenta y limpiar al salir/cambiar de usuario.
Aceptación: publicación A→B a mitad de visita, API error y abort; coherencia o conflicto
explícito. Armazón permanece utilizable; ningún cierre histórico cambia.

### M05. Compra cotidiana completa

Buscar título, marca, EAN, variantes y sinónimos; filtros categoría, formato, tienda,
oferta y preferencias. Texto libre y pegar varias líneas con previa; no interpretar
«2 kg» como dos envases sin base. Favorito/necesito/carrito/comprado diferenciados.
Listas personales/compartidas/casa con elección explícita, cantidades y notas.
Modo tienda por pasillos, deshacer, contador correcto, artículo manual sin precio,
reordenar y restaurar tras recarga. Fotos ayudan a reconocer la variante exacta.
Aceptación: lista de 30 líneas, duplicados deliberados, dos marcas parecidas,
reposición de favoritos y otra lista compartida; búsqueda no destruye la selección.
Offline/concurrencia se completan en M15, pero no se crean callejones sin salida aquí.

### M06. Coste real, promociones y optimización de cesta

Un selector elegible antes de minimizar coste: identidad, ámbito, fechas, cantidad,
club/cupón/limites y disponibilidad observada. Evaluar ofertas por cantidad final,
no descartar envases antes de aplicar promoción. Precisar si una oferta es club,
solo online, futura o incompatible; perfil club voluntario, sin guardar credenciales.
Ofrecer una tienda o hasta dos por defecto; mostrar las demás como elección avanzada.
Comparar solo cestas con cobertura equivalente; faltantes visibles, nunca ganadoras
por omitir líneas. Mostrar ahorro bruto y coste de viaje opcional por separado.
Oráculo exhaustivo independiente para casos pequeños. Estimación=cierre=histórico,
incluidos importes por línea persistidos, artículo efectivo, cantidad y tienda.
Aceptación: 3x2 en una línea/varias líneas, club sí/no, oferta vencida, dos tiendas,
centimos impares, cambio de precio durante cierre y sustitución revocada de UNA línea.

### M07. Identidad automática evaluada, no solo un EAN en frontend

Resolver entidades en pipeline: GTIN normalizado/validado, marca, variante (entera,
sin lactosa, sabor…), pack, contenido neto y peso variable. Mantener GTIN de envase
y multipack separados. Bloqueo de candidatos + reglas explicables + ranking opcional.
Embeddings/fuzzy solo para candidatos/familias, nunca sustitución exacta automática.
Banco etiquetado de al menos 200 pares estratificados por cadenas/categorías,
incluyendo difíciles y desconocidos, con procedencia de etiqueta. Separar ajuste y
evaluación; publicar precisión, recall, abstención y matriz de confusión por estrato.
Prioridad a evitar falsos exactos; no pasar clasificándolo todo como desconocido.
Publicar cambios primero en sombra, diff de altas/particiones/impacto y rollback.
Identidad estable y evidencia versionada; listas y compras previas no se reescriben.
Aceptación: invariantes duros sin falsos exactos en el banco crítico; cobertura y
errores medidos. Umbral automático documentado, no una cifra de calidad inventada.

### M08. Favoritos, alertas y ahorro explicable

Favoritos de artículo exacto y preferencias de familia explícitamente distintos.
Alerta de precio con objetivo opcional, regla, ámbito y periodo; «sin ver» accesible
desde el menú servido y pantalla, no solo lector de pantalla. Elegir contador discreto
junto a Avisos como default, sin pedir a David otra decisión de ubicación.
Sembrar el evento determinista, ejecutar vigilante real, ver, marcar y recargar.
No vender bajada como oferta si cambió cantidad/variante o falta observación anterior.
Histórico de ahorro distingue referencia disponible, estimación y compra pagada;
no sumar diferencias hipotéticas como dinero ahorrado. Aislamiento entre A/B.

### M09. Recetario de calidad de producto

Biblioteca con foto/fallback, búsqueda por título/ingredientes, colecciones, favoritos,
tiempo, raciones y coste conocido/parcial. Editor estructurado con unidades, pasos,
tiempos y vínculos de producto o genérico; duplicar y versionar sin romper planes.
Importar archivo/texto y URL de fuentes permitidas con preview/atribución; proteger
SSRF, redirecciones, tamaño, esquema, timeout y contenido activo. No importar masivamente
recetas con derechos ajenos. Recetas de demostración propias, solo en sandbox o modo
demo claramente rotulado. Compartir con hogar voluntario, no público por defecto.
Aceptación: crear/editar/duplicar/archivar y restaurar una receta con cantidades,
autoría y nutrición parcial; versión previa del plan/diario conserva su contenido.

### M10. Plan semanal útil y propuesta asistida

Calendario día/comida con varias ocurrencias, raciones/comensales, notas, duplicar
semana, cambiar fecha y reemplazar una ocurrencia sin borrar las demás. Operaciones
por id estable; si la clave actual no permite el caso, migración preservadora.
Resumen de coste de ingredientes usados vs envases a comprar; nutrición prevista
por persona, no «dieta completa». Ver despensa antes de enviar y elegir destino.
Propuesta local opcional de cinco recetas según tiempo, favoritos, presupuesto,
ingredientes que caducan y variedad: algoritmo explicable, no dieta médica.
Mostrar restricciones sin dato y razones de cada sugerencia; no inventar seguridad
de alergias. Comparar propuesta con baseline simple y permitir editar TODO.
Aceptación: cinco recetas, dos personas, raciones distintas, otra semana y duplicar;
plan manual funciona aunque el recomendador no tenga cobertura suficiente.

### M11. Plan/receta → necesidades → lista y despensa

Un servicio común para ambos puentes con contribuciones por ocurrencia. Consolidar
solo identidad y dimensiones compatibles; gramos/litros/unidades no se redondean a
envases. Aplicar stock explícito/reservas, calcular déficit/envases/sobrante, y dejar
pendiente lo desconocido. Modificar plan actualiza sus aportes, no borra líneas manuales.
Envases según tamaño verificado; ingrediente sin catálogo sigue visible con cantidad.
Recibo enlaza receta, necesidad y línea. Operación idempotente por destino/revisión.
Aceptación: escenario §8, suma de 150+200 g, dos marcas no fusionadas, trasvase de receta
individual y plan producen el mismo cálculo. Caída entre SQLite/PostgreSQL recuperable.

### M12. Cocina y aprovechamiento

Modo cocina legible con ingredientes escalados, pasos marcables, varios temporizadores
por hora final y recuperación tras cerrar/recargar. Wake lock solo si disponible y
solicitado, sin prometer alarmas en segundo plano que el navegador no garantiza.
Preparar genera porciones/lote disponible si se confirma; consumir se confirma aparte.
Despensa con movimientos (compra, uso, ajuste, merma), unidad, cantidad conocida o
desconocida, lote/fecha opcionales y reservas. No certificar frescura ni seguridad.
Sugerir «aprovecha esto» por existencias conocidas y recetas vinculadas; explicar
qué falta. Aceptación: dos platos reservan el mismo arroz sin doble gasto, cocina
recarga, uso parcial, merma y ajuste no inventan stock ni consumo personal.

### M13. Diario y nutrición personales completos

Añadir desde producto, receta/version, alimento manual o porción preparada. Buscador,
recientes/favoritos personales, base 100g/100ml/unidad/ración, cantidades decimales y
fuente de cada dato. Editar y deshacer propios; copiar comida con nueva operación.
No pedir gramos si la ficha solo acredita volumen; no asumir densidad 1. Nutrientes
independientes: proteína conocida sobrevive a energía ausente. Snapshot al confirmar.
Previsto/registrado/objetivo separados; objetivo opcional y por fecha, sin 2000 kcal
preasumidas. Sin recomendación clínica ni puntuación moral de alimentos/personas.
Aceptación: 270/135 kcal del escenario, registro sin kcal con proteína, cero conocido,
corrección/recarga/exportación, día cruzando medianoche local e idempotencia A/B.

### M14. Gráficas que ayudan a decidir

Compra: gasto pagado semanal/mensual por tienda/categoría, precio del mismo artículo,
coste de cesta y cobertura. Recetas: coste por ración y gasto en envases separados;
plan y aprovechamiento solo con movimientos conocidos. Calorías: series previstas,
registradas y objetivo opcional, con cobertura por nutriente y por periodo.
Cada gráfica: pregunta concreta, medida, unidad, universo, fechas, fuente, versión,
tabla accesible y exportación. Huecos no se conectan como mediciones ni se vuelven cero.
Mostrar datos crudos y método en «cómo se calcula». No comparar medias de tiendas
con surtido distinto como si fueran el mismo índice de cesta.
Aceptación: 0/1/muchos puntos, huecos, unidades distintas, cobertura parcial, móvil,
oscuro, filtros sincronizados y cifra de gráfico igual a tabla/API.

### M15. Web móvil instalable, offline y sincronización

Auditar capacidades actuales; añadir manifest, iconos propios, standalone y política
de actualización si faltan. PWA no equivale a nativa. Instalación/cámara/service worker
dependen de navegador y contexto seguro: documentar localhost y requisitos de HTTPS
para móvil real. No exponer la máquina ni cambiar certificados globales sin permiso.
App shell disponible sin red y cola de cambios de lista con id de operación, conflictos
y estado visible. No precachear todo el catálogo ni respuestas privadas indiscriminadas.
Particionar/borrar datos locales por cuenta; salir y entrar como B no muestra A offline.
App abierta durante nueva versión: no borrar trabajo pendiente ni servir API incompatible.
Aceptación: desconectar/reabrir/tachar/cantidad/reconectar sin pérdida/duplicación;
dos dispositivos simulados, revocación de acceso, nueva versión y caché privada aislada.
Si no hay móvil físico, dejar validado navegador y declarar prueba física pendiente.

### M16. Ingestas resistentes y ampliación acreditada de Lidl

Auditar seis fuentes por separado: catálogo descubierto/capturado/aceptado, precios,
detalle, fecha, región/canal y causas. Carrefour del 18 es un caso real de partida.
Reproducir desde raw antes de pedir más red. Desafío HTTP 200 no es página vacía;
429/Retry-After, backoff, presupuesto, checkpoint y circuit breaker. Reanudación
idempotente conserva último válido y estado degradado por cadena.
Lidl: revisar campaña, sitemap, categorías y fichas públicas permitidas; reconciliar
IAN/EAN, variante y región. Aumentar cobertura demostrada sin fijar «tantos como Aldi»
como objetivo artificial. Si la fuente no expone surtido completo, mostrar limitación
y entregar descubrimiento incremental real, no eternizar un bloqueo ni inventar filas.
Definir objetivo de cobertura contra un universo observado, no solo número obtenido.
Aceptación: fixtures por fuente, parada/reanudar, publicación atómica, catálogo vacío
legítimo, cambio de esquema y muestra real acotada respetuosa cuando sea posible.

### M17. Fichas ricas y nutrición con historial

Extraer los campos públicos disponibles de TODOS los productos dentro de alcance,
incluidos artículos históricos aún no enriquecidos: texto/ingredientes, alérgenos,
nutrientes/base/preparado-vendido si consta, peso neto/escurrido, pack, origen,
conservación, especificaciones, descripción, imagen autorizada y sellos acreditados.
Mantener precio diario separado de detalles estables. Cola nuevos/cambiados/vencidos
con TTL por campo, hash/ETag si procede, presupuesto por cadena y checkpoint.
Precio vigente no rejuvenece una ficha vieja. Registrar fuente URL/fecha/parser/hash
y campo nativo/enriquecido/manual/derivado, conflictos y estados ausente/no publicado/
bloqueado/error/no aplicable. NO_PUBLICADO requiere evidencia, no fallo del parser.
Open Food Facts u otra fuente permitida no sobreescribe en silencio la etiqueta local.
No inferir alérgenos ausentes. Aceptación: matriz por cadena/campo con numerador y
denominador, pruebas raw→campo→API→pantalla y reproceso offline de un histórico.

### M18. Operación observable y administración local

Pantalla de estado útil: versión servida/API/catálogo, frescura por cadena, cobertura,
última pasada, errores y checkpoints; separar datos comerciales de diagnóstico técnico.
Métricas de peticiones efectivas, reintentos, duración, nuevos/retirados aparentes y
presupuesto de detalles. No almacenar cookies/tokens ni HTML con secretos en informes.
Runlock, tareas y procesos verificados; códigos de salida distinguen éxito/degradado/
fallo. No mover puntero a mano como reparación. Política de retención con simulación,
sin eliminar raw o históricos del usuario por defecto. Alertas locales accionables,
sin notificar continuamente el mismo estado ni crear automatizaciones no solicitadas.
Aceptación: fallo de una fuente no oculta precios viejos ni tumba el resto; progreso
legible, log rotado, reanudación y runbook con comandos seguros.

### M19. Seguridad, privacidad y recuperación

Auditar todos los endpoints montados: anónimo, A/B, hogar compartido y permisos
revocados; recetas/versiones/plan, diario, despensa, exportaciones y cachés. Tests HTTP
con sesión real, no solo mocks de dependencia. CSRF con cookie/origen, SSRF, XSS de
texto/recetas importadas, uploads, sesión/cookies y límites razonables.
Copias consistentes de PostgreSQL y SQLite privados + catálogo/manifiestos. Restaurar
en instancia nueva y comparar usuarios, dueños, cantidades, totales por línea, snapshots
y hashes. Probar interrupción entre almacenes y reconciliación; no fingir atomicidad
distribuida. Secretos por entorno y muestras sin credenciales; dependencia vulnerable
se evalúa por alcance, no con upgrades mayores ciegos.
Aceptación: exportar datos propios, revocar, logout offline, backup-restauración y
matriz de amenazas reproducibles. Un fichero local no acredita privacidad por usuario.

### M20. Rendimiento y calidad percibida

Medir en build, datos representativos y red limitada: búsqueda, ficha fría/caliente,
lista de 100 líneas y plan semanal. Reducir N+1, cargas repetidas y bundles; índices
solo con evidencia. Usar virtualización/paginación cuando se justifique, no por moda.
Presupuestos iniciales de laboratorio: búsqueda p95 ≤1 s caliente, ficha utilizable
≤2,5 s en perfil acordado y respuesta visual local ≤100 ms; son objetivos a medir,
no promesas sobre todas las redes. Guardar perfil/hardware/dataset y baseline.
Una prueba lenta debe explicar espera/red/CPU y producir traza; no subir timeout
para ocultar un bucle, una excepción o una operación deshabilitada.
Aceptación: informe antes/después, ninguna mejora rompe exactitud/aislamiento y
experiencia de teclado/scroll/carga no tiene regresiones evidentes.

### M21. Aprendizaje dentro del producto y documentación coherente

Convertir `/aprender` en índice navegable de capítulos existentes, con ejemplos
seguros y glosario: raw/bronze/silver/gold, Parquet, DuckDB, SQLite, PostgreSQL,
matching, nutrición, promociones, algoritmos y evaluación. Mostrar qué usa realmente
el proyecto; dbt/Dagster se explican como conceptos si no se usan.
Actualizar README, arquitectura, modelo, operación, contratos y decisiones; no añadir
otro documento de 70 KB para una hipótesis. Separar snapshot histórico de estado vivo.
Cada algoritmo tiene entradas/salidas, límites, ejemplo calculado y comando/test.
Aceptación: seguir un producto crudo→precio comparable→lista→receta→diario sin
inventar campos; ejemplos corren en sandbox y enlaces internos funcionan.

### M22. Release candidate verificable, no despliegue automático

Preparar instalación local de un solo recorrido, configuración ejemplo, healthchecks,
versiones y migraciones seguras. Build servido comprobado, no solo `tsc` o bundle nuevo.
Playbook para despliegue privado/público futuro con HTTPS, secretos, backups, límites,
monitorización y reversión. No ejecutar exposición, DNS ni servicios pagos.
Entregar matriz: usable local / probado en móvil / preparado para piloto privado /
no apto público, con bloqueos por capacidad y criterios que faltan. No declarar
«app completa» porque el instrumento haya terminado con N comprobaciones.
Demo reproducible con escenario completo y datos identificados como sintéticos.
Aceptación final §11; si faltan permisos externos, cerrar el resto y entregar el
paquete pendiente exacto. Popularidad y reconocimiento no son criterios técnicos.

## 8. Escenario común obligatorio: una semana doméstica

Fixture independiente de promociones reales. Usuario A y B; hogar compartido con
lista Casa y lista personal Viaje; diario privado. Cinco recetas de dos raciones:

| Receta | Necesidad de receta completa | Nutrición sintética acreditada |
| --- | --- | --- |
| R1 | 150 g arroz seco | 360 kcal/100 g |
| R2 | 200 g del mismo arroz | 360 kcal/100 g |
| R3 | 500 ml de leche elegida | 60 kcal/100 ml |
| R4 | 0,5 l de esa misma leche | 60 kcal/100 ml |
| R5 | 3 huevos | 80 kcal/ud |

Resultados: 350 g de arroz, 100 g de despensa confirmados, déficit 250 g, un envase
de 1 kg, 750 g restantes de ese envase; leche 1 l en una botella; pack de seis huevos
con tres sobrantes. Si R1 pasa a cuatro raciones, necesita 300 g ella sola.
No agregar otra marca elegida sin autorización. Ingrediente manual queda pendiente.

Energía de las cinco preparaciones: 2100 kcal; una ración de cada una: 1050 kcal,
un subconjunto de la semana, NO ingesta total. R1 una ración =270 kcal; media=135.
Planificar/comprar/cocinar dejan diario vacío. Registro explícito, recarga y reintento
mantienen una entrada; otra comida legítima puede añadir otra. Caso con proteína
conocida y kcal ausente conserva proteína y cobertura energética incompleta.

Extender con precio envase arroz 120 céntimos, leche 100 y huevos 180: gasto en esos
tres envases 400 céntimos antes de promociones. Si todo el arroz requerido se valora
a ese precio, coste de ingrediente usado 42 céntimos; compra necesaria de arroz 120:
no son la misma magnitud, y aplicar despensa no convierte en gratis lo ya comprado.
Los costes históricos de despensa se dejan desconocidos si no constan.

## 9. Banco de aceptación transversal

Cada caso debe nombrar prueba, comando, revisión y evidencia. No todos requieren
navegador; sí los recorridos y fallos de render. Usar servicios reales de sandbox.

| Caso | Oráculo mínimo |
| --- | --- |
| Exacto vs alternativa | Alternativa muy barata/cara no cambia comparación exacta |
| Mismo artículo, otra base | Se reconoce identidad; no resta kg/ud; compara envase si acreditado |
| Elegido fuera de candidatos | Cuenta su fuente/precio una vez; no pierde una cadena |
| Precio inválido | null, NaN, infinito, negativo o vencido no producen mínimo ganador |
| Oferta condicionada | Perfil sin club no recibe ahorro de club; fecha y región importan |
| 3x2 | 3 envases de 100 cent cuestan 200, también repartidos 1+2 líneas |
| Envase pequeño | 0,0004 kg se presenta como 0,4 g, nunca cero |
| Semana completa | Escenario §8 en receta y plan, previa=confirmación=persistencia |
| Catálogo cambiado | Previa antigua exige revisión o conserva snapshot explícito |
| Consumo | Compra no escribe; 270/135 solo tras confirmación personal |
| Idempotencia | Reintento igual no duplica; distinta carga con misma clave da conflicto |
| Permisos | B no enumera/lee/edita/exporta lo privado de A, ni por id adivinado |
| Offline | Cantidad y tachado sobreviven, conflicto explicado, logout purga A |
| Fuente caída | Último válido fechado y limitado, sin publicación vacía disfrazada |
| Recuperación | Restauración aislada conserva importes, identidad, dueños y snapshots |
| Accesibilidad | Lateral REAL, teclado, foco, diálogo, tabla alternativa y zoom |

No retirar una prueba roja válida para sostener «todo verde». Si descubre un defecto,
corregirlo; si depende de algo externo, marcarlo explícitamente y no declararlo pasado.
No desactivar afirmaciones porque el catálogo real de hoy carezca de la oferta:
el obligatorio usa fixture, el real es una comprobación adicional.

## 10. Referencias funcionales y diferenciación

Revisadas sus páginas oficiales el 18/10/2026. Son documentación, no una auditoría
de sus algoritmos ni una sesión de uso autenticada. Implementación y diseño propios.

- [Paprika](https://www.paprikaapp.com/help/android/): referencia de recetario,
  escalado, lista, despensa y cocina con pasos/temporizadores. Aplicar a M09–M12;
  nuestra diferencia es enlazar coste y cobertura verificables de varias cadenas.
- [Mealime](https://support.mealime.com/article/151-getting-started-guide): referencia
  de elegir platos, consolidar necesidades y ver para qué receta es cada ingrediente.
  Aplicar a M10–M11; no copiar sus recetas ni afirmar conocer su motor de propuestas.
- [Cronometer](https://cronometer.com/features/): referencia de entrada de alimentos,
  recetas y análisis nutricional. Aplicar a M13–M14 con las fuentes realmente disponibles,
  sin prometer su número de nutrientes ni añadir ejercicio/diagnósticos fuera de alcance.
- [AnyList](https://www.anylist.com/features): referencia de listas compartidas,
  favoritos, cantidades, categorías, recetas y plan. Aplicar a M05/M08/M10/M15.
  No copiar servicios comerciales de sincronización ni integrar cuentas de terceros.
- [Instalación PWA](https://web.dev/learn/pwa/installation/): instalación y soporte
  dependen del navegador/plataforma. Una emulación responsive no acredita app nativa.

Para cada función: necesidad → evidencia de referencia → adaptación propia → test.
Si hace falta investigar un runtime o artefacto autorizado con REA, leer primero
los skills `rea-windows-local` y `reverse-engineer-anything` y las instrucciones de
`F:\EspacioCodigo\ProyectoServidor\rea-sandbox`. No usar REA para leer nuestro fuente
ni detener el desarrollo por falta de acceso a una aplicación de pago.

## 11. Definición de terminado y ejecución prolongada

Una entrega tiene: comportamiento observable, cálculo correcto, permisos, errores,
persistencia, accesibilidad, prueba reproducible y documentación suficiente. No
aceptar «instalado», «compila», «pantalla abre», «sin errores consola» o N tests como
sustitutos de su criterio. No exigir toda la suite tras cada coma: tests dirigidos
durante desarrollo; puertas completas al cerrar una entrega funcional.

Puertas: Python/ruff; frontend tests/ESLint/tsc/build; HTTP con sandbox; oráculos de
coste/unidades; recorridos móvil y escritorio; offline/publicación/copia; revisión
visual de TODAS las pantallas modificadas con estados de datos representativos.
Capturas con viewport, URL, commit, catálogo y objetivo de prueba; revisarlas, no
solo producir ficheros. Un timeout conserva traza, selector, estado y respuestas.

Trabajar por paquetes verticales: no terminar una ronda por dejar un TODO de dos
líneas cuyo arreglo es parte del mismo contrato. El conocido defecto de tabla de
M01 se corrige en esa entrega, no se devuelve a David para que lo retransmita.
Si dos intentos no acotan el fallo, reproducir mínimo y revisar el instrumento;
no producir veinte rondas de hipótesis descartadas. Error de build invalida el
experimento servido; verificar versión antes de interpretar pantalla.

Mantener como máximo dos paquetes en curso. Evitar commits de bitácora sin progreso.
Una reproducción que acota una causa sí cuenta como avance; reescribir el mismo
resumen, repetir «Docker caído» o medir el mismo cero sin nueva variable no cuenta.
Tiempo prolongado significa completar la cola finita, no consumir tokens ni esperar
indefinidamente. No inventar que un goal externo está activo por editar Markdown.

Al terminar un paquete, actualizar el control en menos de una página por entrega:
qué funciona, pruebas exactas, qué falta y próximo comando. Si hay bloqueo externo,
registrar dependencia y continuar el paquete independiente siguiente. Si TODA la
cola restante depende de autorización externa, dar un único informe con opciones,
no seguir generando rondas. Reanudar tras respuesta desde ese punto.

Release final: escenario §8 completo; matriz §9; seis fuentes con cobertura honesta;
PWA probada donde sea posible; documentación/instalación/copia; revisión de seguridad;
dictamen por uso local, piloto y público. Pendiente físico/externo se declara, no se
rellena. Ningún despliegue público se hace como parte de esta autorización.

### 11.1. Evidencia y automatización de las puertas

Crear un comando local de verificación por entrega que orqueste las puertas
existentes y las nuevas, propague códigos de salida y guarde un manifiesto JSON
de evidencia: commit, árbol sucio, versiones de runtime, catálogo, suite/comando,
inicio/fin, exit code y fichero de resultado. Un campo no ejecutado es `no_ejecutado`,
no `verde`. Un skip lleva capacidad y razón. No codificar 104/280 como cifra de éxito.

El runner no crea/restaura bases sin la guarda M00 ni mata servidores ajenos. Separar
modo offline/unidad, HTTP sandbox y navegador. Ejecutar el componente contra respuesta
controlada y el navegador contra build real; son evidencias complementarias.
Exigir que `npm run lint`, `npm test`, `npm run tipos` y `npm run build` (o equivalentes
documentados) existan y se usen. Reutilizar `uv run ruff check .`, pytest y los ensayos
de `plataforma/` tras verificar su alcance y aislamiento. No ejecutar comandos de
ejemplos antiguos que señalan 5434 sin adaptar el sandbox protegido.

## 12. Primer bloque de ejecución, sin otra consulta

1. Inspeccionar git/tarea/lock/publicación y crear estado de M00; no duplicar ingesta.
2. Cerrar M01 entero, tabla incluida, con caso positivo y negativo en componente.
3. Instalar dependencias de M02 y añadir reglas/tests: no posponer por ser instalación.
4. Cerrar M03 con usuarios/SQLite/PostgreSQL de sandbox y lista destino explícita.
5. M04 y recorrido §8; cerrar R0. Continuar R1→R4 sin pedir otra aprobación de rutina.
6. Diagnosticar Carrefour del 18 desde logs/raw mientras avanzan paquetes independientes.

Los documentos anteriores siguen siendo material de consulta; no deben transformar
en «hecho» un requisito de esta especificación sin evidencia correspondiente.
