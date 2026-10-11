# Cesta: competencia, producto y laboratorio REA

Revisión: 11 de octubre de 2026. Destino único: `F:\aprendizaje\scrap`.

## Qué se estudió y qué no

Se leyó el kit de `F:\EspacioCodigo\ProyectoServidor\rea-sandbox\estudiar-apps`, sus convenios, método, plantilla, ejemplo y referencias. Se ejecutó `run-smoke-tests.ps1`: **6 comprobaciones, 0 fallos**, REA 6.4.0; sin prueba nativa. Esto verifica el kit básico, **no una investigación de competidores ni Ghidra en ejecución**.

Se consultaron fuentes oficiales de los productos siguientes. Son evidencia documental de funciones anunciadas y de flujos descritos, no recorridos autenticados ni observación de algoritmos internos. No se descargaron apps, no se abrieron cuentas ni se analizaron binarios de esos competidores. Los agentes deben completar las investigaciones concretas según este documento, sin llamar «demostrado por REA» a una descripción comercial.

## 1. Referencias pertinentes a las tres aplicaciones

No se puede garantizar estudiar «todas las apps del mercado». El objetivo verificable es cubrir todas las capacidades de la matriz y contrastar las decisiones importantes con más de una referencia pertinente. Estas once referencias constituyen un punto de partida, no una obligación de clonar once productos.

| Referencia | Fuente oficial consultada | Capacidad documentada útil | Qué no asumir |
|---|---|---|---|
| Bring! | [Funciones](https://www.getbring.com/en/features), [personalización](https://www.getbring.com/en/features/personalized) | Listas compartidas, cantidades/notas/fotos, orden personalizable, ofertas y paso de ingredientes a lista; vistas de lista o mosaico. | No prueba comparación exacta entre supermercados españoles ni funcionamiento offline. |
| AnyList | [Inicio](https://help.anylist.com/articles/getting-started/), [añadir artículos](https://help.anylist.com/articles/feature-overview-adding-items/), [cola del plan](https://help.anylist.com/articles/meal-plan-queue/) | Artículos y recetas; plan y traslado selectivo de ingredientes; cola de recetas aún sin fecha. | Parte de la funcionalidad es de pago; no hace falta contratarla para adaptar una idea descrita. |
| Listonic | [Funciones](https://listonic.com/features), [guías](https://listonic.com/features-guides) | Categorías/pasillos, edición de detalles, sugerencias de habituales y total con cantidades. | Sus precios recordados no equivalen a precios capturados y vigentes de seis cadenas. |
| Soysuper | [Preguntas frecuentes](https://soysuper.com/about/preguntas-frecuentes) | Comparación del coste de una lista entre supermercados y consideración de gastos/condiciones de compra. | No demuestra su algoritmo de matching ni acceso vigente a todas las cadenas citadas históricamente. No contratar ni integrar su servicio. |
| Paprika | [Producto](https://www.paprikaapp.com/), [guía Android](https://www.paprikaapp.com/help/android/) | Recetario, ingredientes escalados, lista consolidada, plan, seguimiento de pasos e ingredientes y temporizadores. | Una conversión culinaria no autoriza convertir cualquier volumen a masa. No copiar su biblioteca de recetas. |
| Samsung Food | [Producto](https://samsungfood.com/), [planificador](https://samsungfood.com/meal-planner/), [lista](https://samsungfood.com/grocery-list-app/) | Guardar recetas, plan semanal, traslado selectivo a lista, cantidades y organización por receta o pasillo. | Su cálculo nutricional y recomendaciones no están verificados por observación de la web comercial. |
| Mealime | [Guía de inicio](https://support.mealime.com/article/151-getting-started-guide), [ayuda de lista](https://support.mealime.com/category/69-grocery-list) | Relación ingrediente→recetas, consolidación de cantidades y planificación orientada a comprar/cocinar con menos sobrantes. | No adaptar sus integraciones de entrega estadounidenses ni afirmar ahorro real de Cesta sin medir. |
| Cookidoo | [Organizar y planificar](https://cookidoo.es/foundation/es-ES/pages/tutorials-organise) | Colecciones, recetas por día, moverlas entre fechas y lista editable desde el plan. | Cesta no debe depender de Thermomix ni importar contenido protegido de su catálogo. |
| Cronometer | [Funciones](https://cronometer.com/features/) | Diario, búsqueda/registro de alimentos y análisis nutricional como referencia de separación entre datos y visualización. | Ni su base nutricional ni puntuaciones son datos disponibles gratuitamente para Cesta. Verificar cada flujo en su ayuda antes de especificarlo. |
| YAZIO | [Contador](https://www.yazio.com/en/calorie-counter) | Registro de alimentos/macros, código de barras y selección de recientes/frecuentes para reducir tecleo. | No copiar prescripción de objetivos de peso, puntuaciones sanitarias ni publicidad de resultados. |
| MacroFactor | [Registro](https://help.macrofactorapp.com/en/articles/215-how-to-log-food-in-macrofactor), [colección de ayuda](https://help.macrofactorapp.com/en/collections/18-macrofactor-nutrition) | Entradas rápidas y biblioteca, cantidades y organización del diario; documentación de registro parcial y acciones de alimentos. | No reconstruir su coaching metabólico ni presentar estimación de fotos como calorías medidas. |

La [beta de Paprika 4](https://www.paprikaapp.com/news/2026/09/28/paprika-4-is-now-in-open-beta/) anuncia funciones adicionales. Tratarla como **beta y propuesta**, no como comportamiento estable comprobado; la dirección de Cesta no depende de contratar esa versión.

## 2. Qué aporta realmente el kit y dónde falla su selección por defecto

El kit distingue laboratorio, referencia y proyecto destino; obliga a una función por investigación, tres cestas de evidencia y código propio. Es útil y debe conservarse.

Su cola actual prioriza RadioPV y CueDigital. Las apps instaladas descritas son principalmente reproductores, editores e interfaces de agentes. **No son competidores de Cesta por estar disponibles en el PC.** Para este encargo, destino y prioridad ya los ha fijado David: Cesta y sus tres aplicaciones. No empezar P-01 de RadioPV ni solicitar otra elección de proyecto.

La autorización de mejorar Cesta permite al agente decidir mejoras reversibles dentro de este contrato. No autoriza modificar el servidor, el registro DSH, los repositorios de RadioPV/CueDigital o sus cuentas. Tampoco permite decompilar cualquier producto comercial por ser competencia: observación pública primero; artefactos solamente propios, abiertos o con análisis permitido.

### Ruta de lectura del laboratorio

1. `rea-sandbox\AGENTS.md` y `estudiar-apps\AGENTS.md`.
2. `OPERAR.md`, `ESTADO.md`, `PLAYBOOK.md` completos.
3. `ESTUDIAR-LA-INTERFAZ.md`, `REFERENCIAS.md`, plantilla e índice de investigaciones.
4. Skills `reverse-engineer-anything` y `rea-windows-local` cuando se use REA.

No cambiar la cola global de otros proyectos. La cola de Cesta vive en [el tablero de fase 2](SUPERAPP-FASE2-EJECUCION.md). Si se generan investigaciones en el laboratorio, actualizar su índice/estado sin sobrescribir investigaciones de terceros; la implementación y su aceptación viven en Cesta.

## 3. Enrutamiento: qué herramienta responde a cada pregunta

| Pregunta | Evidencia apropiada | Qué no demuestra |
|---|---|---|
| ¿Qué capacidades ofrece una app? | Ayuda oficial, documentación de producto, versión/fecha. | No demuestra haberla usado ni su lógica interna. |
| ¿Cuántos pasos y qué estados tiene un flujo? | Recorrido autorizado, capturas, accesibilidad/DOM y acciones registradas. | Una captura normal no demuestra vacío, error, recarga o privacidad. |
| ¿Cómo calcula internamente una función? | Fuente abierta verificable; paquete permitido con REA; pruebas controladas del comportamiento. | Nombre de un módulo o cadena encontrada no prueba algoritmo. |
| ¿Qué guarda o manda al servidor? | Captura pasiva autorizada, exportación de datos propios, almacenamiento de cuenta de ensayo. | Tráfico cliente no revela toda la lógica del servidor. |
| ¿Funciona ya en Cesta? | Sus fuentes y pruebas HTTP/almacenamiento/navegador del componente servido. | REA no sustituye estudiar el código propio. |

Para web pública y documentación no hace falta Ghidra. Para UI usar las herramientas de navegador disponibles; si el agente tiene control visual, respetar su skill y APIs. No lanzar Chrome sobre el perfil personal con depuración ni publicar un puerto CDP para buscar material. Si se necesita CDP, usar perfil desechable, loopback y objetivo concreto; no exponer sesiones ni cookies reales.

Para JS/ASAR autorizado: `analyze_javascript_application` con resumen y luego vistas/trace focalizadas. Para APK permitido: inventario y herramientas Android anunciadas. Para nativo: `open_binary`, pista, referencias, pseudocódigo, prueba y `close_binary`, usando `rea-local.mjs`. Nunca parchear `node_modules`.

Usar las herramientas **realmente disponibles**. Los nombres en el playbook no garantizan que el MCP esté conectado al agente. Si no está, comprobar el CLI local; si tampoco se puede, documentar el límite y seguir documentación/UI. Un REA roto bloquea sus conclusiones, no toda investigación documental ni toda implementación.

No repetir diagnósticos por función. Hacer la comprobación de entorno al iniciar una sesión REA o ante cambios/fallos; después reutilizar evidencia por artefacto/hash. No volcar JSON enormes en el contexto. No inventar IDs `ev_…`: si la prueba es una captura/documento, citar ese archivo o URL y su alcance.

## 4. Investigación mínima que produce una mejora

Cada informe trata **una capacidad**, no una app entera. Puede comparar dos referencias para esa misma capacidad. Usar la plantilla del kit y añadir:

- Usuario y tarea de Cesta; caso de éxito medible.
- Fuente, fecha, versión o hash cuando exista artefacto. En una web sin versión, URL/fecha y evidencia de la página; no fabricar una versión.
- Observaciones de entrada→interacción→salida→fallo→persistencia, con estados normal, vacío y error cuando sean accesibles.
- Demostrado documental / demostrado por ejecución / hipótesis / desconocido. El pseudocódigo es pseudocódigo, no fuente original.
- Idea que se adapta, expresión que se descarta, diseño propio y por qué beneficia a una familia española.
- Ficheros y contratos de Cesta afectados; riesgo de privacidad, identidad, unidades y costes.
- La misma matriz de casos para referencia y Cesta. Si no se pudo ejecutar la referencia, escribir «no observado»; no rellenar con intuición.
- Prueba de Cesta, capturas antes/después, commit y limitaciones. La investigación entregada no significa mejora implementada.

No extraer catálogos de recetas, marcas, ilustraciones, textos largos ni código privado de competidores. Inspirarse en decisiones y flujos, conservar origen de referencias y escribir código/textos propios. No crear cuentas, aceptar condiciones ni iniciar pruebas de pago sin autorización necesaria.

**Regla de parada:** cuando se puede especificar una mejora comprobable con las fuentes suficientes, implementar. Para cada capacidad, empezar con una referencia primaria y una secundaria; ampliar solo si hay una contradicción concreta. No pasar semanas catalogando pantallas sin mejorar Cesta.

## 5. Matriz de capacidades que debe cubrir el producto

Las referencias son semillas de investigación. La columna «aceptación» define Cesta, no afirma que el competidor se comporte exactamente así. Estados reales se rellenan después de inspeccionar/ejecutar Cesta: no marcar ausencia por no verla en el README.

| ID | Capacidad y referencia inicial | Aceptación para Cesta |
|---|---|---|
| C01 | Lista familiar — Bring!/AnyList | Añadir/tachar/deshacer desde dos sesiones, sin perder cambios ni exponer listas de otro hogar. |
| C02 | Texto libre/notas/cantidades — Listonic | Guardado sin catálogo, vínculo posterior explícito y precio desconocido visible. |
| C03 | Vista de compra por pasillos — Bring!/Listonic | Orden editable por lista/tienda; uso con una mano y conservación al recargar. |
| C04 | Habituales/favoritos — AnyList/Listonic | Añadir frecuentes sin confundir preferencia con necesidad; estados necesito/no necesito y carrito/comprado. |
| C05 | Búsqueda — referencias de listas | Acentos/typos/filtros útiles; sugerir no significa declarar identidad exacta. |
| C06 | Comparar artículo/cesta — Soysuper | Identidad/formato, ámbito y fecha visibles; cantidad/promoción elegibles y coste parcial explícito. |
| C07 | Una tienda frente a varias — Soysuper | Máximo de tiendas y coste de desplazamiento optativo; ahorro neto definido, oráculo multi-tienda. |
| C08 | Club/ofertas — Bring! | Condiciones y vigencia; crédito futuro separado del dinero pagado hoy. |
| C09 | Presupuesto/gasto — Listonic | Previsto contra guardado/pagado sin mezclar; cobertura de líneas desconocidas. |
| C10 | Historial/reutilizar compra — AnyList | Copiar necesidades, nunca precios antiguos como si fueran actuales. |
| C11 | Ficha y evidencia — catálogo propio | Ingredientes/alérgenos/nutrientes/detalles publicados, origen y fecha por campo. |
| C12 | Frescura/cobertura — catálogo propio | Seis cadenas, familias incluidas y precios/fichas frescos medidos por separado. |
| R01 | Biblioteca/filtros — Paprika/Cookidoo | Recetas propias, etiquetas, favoritos, búsqueda y vacío con filtros explicados. |
| R02 | Importar receta — Paprika/Samsung Food | URL/archivo de fuente permitida; previa, fuente, unidades y edición antes de guardar. |
| R03 | Editor/versiones — Paprika | Borrador recuperable y versión persistente; diario antiguo permanece estable. |
| R04 | Raciones/unidades — Paprika | Escalado reproducible; g/ml/ud no sumados por apariencia. |
| R05 | Cocina — Paprika | Paso actual, ingredientes usados, temporizadores y reanudación sin conexión cuando sea viable. |
| R06 | Calendario y cola — AnyList/Cookidoo | Mover/copiar recetas y notas; recetas aún sin fecha no obligan a inventar día. |
| R07 | Plan→lista — Samsung Food/Mealime | Consolidar compatibles, rastrear receta de origen, elegir qué transferir e idempotencia. |
| R08 | Despensa/sobrantes — Paprika/Mealime | Existencias declaradas, ubicación/caducidad opcional; compra no acredita consumo ni stock restante. |
| R09 | Coste por ración — datos de Cesta | Coste usado distinto de envases por comprar; cobertura/ámbito/versión. |
| R10 | Buscar por lo disponible — Mealime | Explicar ingredientes disponibles/faltantes, coste y restricciones; sugerencia, no sustitución automática. |
| N01 | Registro rápido — YAZIO/MacroFactor | Recientes/favoritos y copiar comida con cantidad editable y nueva operación legítima. |
| N02 | Código de barras — YAZIO | GTIN validado y producto verificable; fallo de cámara o sin resultados permite texto/número. |
| N03 | Porciones — Cronometer/MacroFactor | Base nutricional clara, gramos/ml/ración con conversiones trazables. |
| N04 | Diario por comidas — Cronometer | Registrar/editar/borrar/recargar y reintentos; cuenta y fecha local correctas. |
| N05 | Alimentos propios — MacroFactor | Fuente declarada, datos desconocidos y sin falsa verificación de etiqueta. |
| N06 | Receta consumida — catálogo propio | Versión y ración registradas; editar receta no reescribe ayer. |
| N07 | Nutrientes/cobertura — Cronometer | Macros y campos adicionales publicados con subtotal y cobertura independiente. |
| N08 | Tendencias — Cronometer | Huecos, parcialidad, tablas accesibles y actualización inmediata tras cambios. |
| N09 | Exportación privada — biblioteca propia | Solo datos propios, formatos documentados; descarga no filtra otra cuenta. |
| X01 | Errores/offline/deshacer — kit REA | Borradores conservados, conflicto explícito y reintento con misma operación. |
| X02 | Sistema visual y accesibilidad — investigación UI | Tres apps orientadas y consistentes, no tres clones de la misma pantalla. |
| X03 | Privacidad/recuperación — código propio | HTTP A/B, cambio de sesión y backup restaurado de todos los almacenes. |

C07/R08/R10 aportan capacidades nuevas, pero se construyen después de integridad y datos. No implementar social feeds, ventas, pagos, wearables, ayuno, objetivos médicos ni calorías deducidas de fotos para parecerse a la competencia. Se pueden registrar como descartadas por alcance. Objetivos nutricionales, si ya existen, son voluntarios y declarados por el usuario, no prescripción automática.

## 6. Dirección visual propia: propuesta, no resultado observado

Cesta debe parecer una herramienta doméstica de calidad, no un panel corporativo lleno de KPIs ni una colección de tarjetas genéricas. Conservar el lenguaje actual de papel/tinta y revisarlo con pantallas reales.

- Fondo cálido, superficies discretas, texto de alto contraste, un acento principal y acentos de sección moderados. No un gradiente diferente en cada tarjeta.
- Escala tipográfica y de espaciado única; texto de formulario de al menos 16 px en móvil, metadatos legibles y cifras alineadas. Fuentes existentes/locales con licencia; no dependencia de un CDN para poder leer.
- **Compra:** lista densa y operable, búsqueda dominante, cantidad/formato y coste junto a la acción; comparativa en tabla en escritorio y bloques comparables en móvil.
- **Recetas:** foco en receta y preparación; imágenes propias/autorizadas cuando existan, ingredientes y pasos como contenido principal, calendario sin sobrecarga.
- **Calorías:** cronología/diario claro y resumen de lo conocido con cobertura. Evitar anillos que aparenten completar toda la ingesta con un registro parcial.
- Un control para una acción; confirmación contextual de sustituciones; deshacer en acciones reversibles. Evitar modales repetidos y números sin unidad.
- Vacío, carga, error y datos parciales diseñados como pantallas útiles. Verificar teclado, foco del cajón, zoom 200 %, reducción de movimiento y móvil estrecho.

Crear tokens y ejemplos de componentes **desde el sistema actual**, no otra migración de framework. Las referencias de Stitch existentes sirven de material, no de autorización para gasto ni de prueba de que la UI servida coincide.
