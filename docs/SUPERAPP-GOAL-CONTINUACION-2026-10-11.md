# Cesta: objetivo de continuación prolongada para DeepSeek

> **Continuación posterior:** este documento conserva el contrato y la base `17f140f`, no describe todo el código actual. Tras el cierre declarado en `480ac21`, seguir [la fase 2](SUPERAPP-FASE2-EMPEZAR-AQUI.md), con revisión de evidencia e investigación de competencia mediante el kit REA. No reiniciar tareas ya implementadas a partir de los hallazgos históricos de abajo.

Fecha de revisión: 11 de octubre de 2026. Base inspeccionada: `17f140f`, después de `9008d99`.

Este documento convierte el encargo en trabajo ejecutable. **No acredita que las tareas pendientes estén implementadas.** La revisión que lo origina fue por lectura de código, estado y contratos; no se volvió a ejecutar la suite ni el navegador. Las cifras y ensayos anteriores son evidencia registrada por el agente anterior, no una nueva ejecución de esta revisión.

## 1. Goal: resultado que debes perseguir

Dejar Cesta como una suite doméstica local, profesional y usable, con tres aplicaciones diferenciadas —Compra, Recetas y Calorías—, datos trazables de los seis supermercados, comparaciones exactas o alternativas claramente separadas, costes coherentes con promociones y cantidades, nutrición con procedencia y cobertura, y recorridos persistentes y privados entre cuentas. Completar los paquetes de este documento con evidencia reproducible, sin detenerte al acabar una pieza preparatoria, y mantener un punto de continuación breve para retomar sin reconstruir toda la conversación.

El resultado no es «muchas pruebas verdes», «muchas filas» ni «muchas rondas»: es que los recorridos de una persona funcionen con datos correctos y con límites visibles. No se autoriza un despliegue público ni gasto nuevo. El cierre debe separar preparación para uso doméstico de preparación para publicación pública.

### Primera acción, sin otra ronda de reconocimiento

**Empezar G01: registrar una comida real desde la pantalla del diario con datos controlados.** El contador del menú servido ya consta como cerrado; no volver a dedicarle una ronda salvo regresión reproducida. Leer los ficheros de G01, escribir las pruebas de comportamiento, implementar el formulario y sus contratos, y comprobar persistencia y tendencias.

## 2. Documentos y precedencia

Leer el resumen vigente de [SUPERAPP-ESTADO](SUPERAPP-ESTADO.md), no tratar toda su bitácora como estado actual. Después:

1. [Contrato general y S00–S12](SUPERAPP-00-EMPEZAR-AQUI.md).
2. [Diseño y funcionalidades](SUPERAPP-01-DISENO-Y-PRODUCTO.md).
3. [Fichas, Lidl e identidad](SUPERAPP-02-DATOS-LIDL-IDENTIDAD.md).
4. [Investigación y referencias](SUPERAPP-03-INVESTIGACION.md).
5. [Revisión del diario y privacidad](SUPERAPP-REVISION-2026-10-08.md) y [revisión de costes](SUPERAPP-REVISION-COSTES-2026-10-08.md), como antecedentes a contrastar, no como fallos necesariamente actuales.
6. Este documento para orden, entregables y aceptación de la continuación.

Los contratos anteriores siguen vigentes. Esta continuación concreta sus pendientes; no reinicia el proyecto ni obliga a rehacer piezas verificadas. Si un hallazgo histórico ya se resolvió, conservar su prueba y anotarlo como conservado.

## 3. Base observada y diferencias que importan

| Pieza | Estado de partida y acción |
|---|---|
| Contador de Listas | En `Suite.tsx`, menú servido. Medición anterior móvil/escritorio y cuatro estados registrada. Conservar; no arreglar `Nav.tsx` como si se sirviera. |
| Diario manual | `Diario.tsx:Alta` manda `cantidad_g`, proteínas, grasas e hidratos como `null`. Falta ofrecer y probar esos datos en la interfaz. |
| Cliente del diario | `api/diario.ts:conCuerpo` descarta el JSON de éxito. Las mutaciones invalidan `diario`, pero las tendencias usan `diario-rango`. Revisar contratos e invalidación de ambos. |
| Puente compra→diario | La pantalla calcula el mensaje de éxito con el número de la previa, no con el resultado efectivo. Selecciona casa o, en su ausencia, la primera lista. No confundir esa elección con una decisión explícita del usuario. |
| Revocación | Función existente; falta una medición que identifique la línea revocada y conserve las demás. |
| Historial de compra | La migración 013 y el almacenamiento de `importe_cent` existen. Evidencia anterior de PostgreSQL registrada. Conservar importes históricos; no recalcularlos con el catálogo actual. |
| Gráficas | `Chispa.tsx` configura `spanGaps: true`; revisar unión de huecos y mensajes que infieren días a partir del número de puntos. |
| Publicación | `pipeline.main()` captura el fallo de `publicacion.publicar()` y devuelve 0. `run.py` ejecuta el emparejador después del pipeline. Auditar el conjunto publicado y cómo el estado diario refleja publicación y derivados, no solo captura. |
| Lidl diario | `run.py:ORDEN` contiene cinco cadenas, no Lidl. Hay collector e inventario/fichas; no asumir que tener esos módulos significa refresco diario integrado. |
| Cambios ajenos | `core/datos/secciones.yml` y `docs/CIFRAS.md` están modificados. Preservar y no incluirlos en commits de este encargo. |

Esta tabla no permite inferir la cobertura actual de Lidl, que todas las comparaciones sean erróneas ni que Docker siga caído. Medir lo necesario cuando toque; no repetir cifras antiguas como actuales.

## 4. Cómo trabajar sin perder el objetivo

- Inspeccionar cambios y leer los ficheros antes de editarlos. Usar ediciones verificables, revisar el diff y comprobar sintaxis; no cadenas de sustituciones que puedan aplicar medio parche silenciosamente. No reescribir ficheros completos por defecto, especialmente si tienen cambios ajenos. El consejo histórico de reescritura en `SUPERAPP-METODO.md` no obliga a hacerlo: conservar lo ajeno y comprobar el resultado manda.
- Trabajar por comportamiento completo: contrato, servidor, pantalla, persistencia, pruebas y evidencia. Mover un import es un paso, no un entregable que justifique cerrar una etapa.
- Añadir pruebas que ejecuten comportamiento. Conservar los controles existentes de código/estilo, pero no usarlos como única evidencia de una función visible.
- No retirar un caso rojo válido para mantener la cifra verde. Implementar el contrato, o dejar documentado un impedimento real sin afirmar que se cumple. No introducir falsos positivos, saltos silenciosos o rangos que sustituyan una igualdad exigida.
- Durante el desarrollo, usar pruebas enfocadas; antes de cada commit, respetar las verificaciones del proyecto: suite Python y lint; si cambia frontend, tipos, build y pruebas del cliente pertinentes. Separar ensayos que necesitan servicios reales de los que no.
- Preparar datos y cuentas de ensayo aislados. Inspeccionar los guiones antes de ejecutarlos: pueden crear cuentas, compras o modificar bases. No usar la casa real como fixture ni limpiar datos reales para repetir pruebas.
- No comprobar Docker en cada minirronda: comprobar al retomar o antes de un ensayo que lo necesite. Si no hay motor, avanzar pruebas controladas, frontend, parsers y documentación; no declarar ejecutado el ensayo pendiente.
- Ante el mismo fallo repetido, cambiar de diagnóstico: reproducir mínimo, leer el componente que se monta, verificar respuesta/estado/selector. No añadir esperas de navegador para disimular componentes ausentes o datos incorrectos.
- Continuar con el siguiente paquete compatible al cerrar uno. Si falta contexto, guardar el siguiente paso exacto antes de terminar. No sustituir ejecución por otro plan largo.
- Pedir decisión solo por coste nuevo, credencial indispensable, intervención humana ante CAPTCHA, cambios destructivos, publicación pública o conflicto real con otro escritor. No eludir retos, ampliar límites de peticiones sin medir ni pedir nuevamente preferencias ya cerradas.

### Registro operativo, no otra bitácora interminable

Crear `docs/SUPERAPP-EJECUCION.md` como tablero operativo breve (objetivo: menos de 200 líneas), enlazado desde el resumen vigente del estado. Mantener la bitácora histórica sin duplicar páginas de explicación cada ronda.

Registrar por paquete: `pendiente / en curso / implementado sin ensayo real / verificado / limitado por fuente / bloqueado`, commit o diff, comando y fecha, evidencia y siguiente acción. «Verificado» exige su criterio completo, no una compilación. Actualizar el resumen vigente y este tablero antes de pausar y al cerrar un entregable; no modificar fechas históricas por intuición.

La continuación debe indicar **fichero + función/recorrido + prueba que falta + acción inmediata**, no «seguir mejorando». Una limitación de una cadena no bloquea todo el objetivo.

## 5. Orden y mapa de paquetes

| Paquete | Resultado | Relación anterior | Dependencia |
|---|---|---|---|
| G01 | Diario efectivo y puentes seguros | S09, S10 | Empieza aquí |
| G02 | Lista con texto libre y vínculo explícito | S07 | Independiente |
| G03 | Revocación de la línea exacta | S05, S07 | Independiente |
| G04 | Recorridos estables y publicación durante el uso | S01, S12 | G01–G03 |
| G05 | Gráficas con significado y cobertura | S11 | G01 para nutrición |
| G06 | Acabado funcional y visual de las tres apps | S06–S10 | G01–G03; puede avanzar por pantallas |
| G07 | Publicación y ejecución diaria coherentes | S01 | Puede anticiparse si bloquea G04 |
| G08 | Fichas completas, cola y procedencia | S02 | Publicación compatible |
| G09 | Lidl integrado y cobertura demostrada | S03 | G08; descubrimiento puede anticiparse |
| G10 | Identidad exacta y alternativas automáticas | S04 | G08; banco y evaluación pueden avanzar antes |
| G11 | Coste y optimización validados independientemente | S05 | G10 para identidad; oráculo controlado independiente |
| G12 | Recetas y conversiones de ingredientes/raciones | S08, S10 | G08; interfaz puede avanzar con fixtures |
| G13 | Operación local, privacidad y recuperación | S12 | Transversal |
| G14 | Material de aprendizaje y auditoría final | S11, S12 | Documentación en paralelo; cierre tras los demás |

Primero cerrar la etapa de usuario G01–G05. No detener G06 porque falte nutrición en una cadena. No aplazar un defecto de integridad de publicación conocido si está invalidando los recorridos: arreglar G07 y volver al punto exacto.

## G01. Diario: registrar, persistir y explicar lo conocido

Ficheros iniciales: `plataforma/web/app/src/paginas/Diario.tsx`, `src/api/diario.ts`, `plataforma/api/diario.py`, `core/diario.py`, puente en API de cesta y `plataforma/prueba_navegador.py`.

### Implementación

1. Formulario comprensible: qué alimento, comida/fecha, cantidad y unidad cuando procede, energía, proteínas, grasas e hidratos, fuente del dato. Distinguir valores de la porción frente a valores por 100 g/100 ml. No multiplicar dos veces ni equiparar ml y g sin densidad o regla explícita trazable.
2. Ofrecer selección de ficha y versión de receta verificadas. Un nombre escrito libremente no demuestra vínculo con una receta ni permite atribuirle su nutrición. En receta, seleccionar una versión propia o autorizada y escalar por ración/cantidad con reglas claras.
3. Devolver y consumir un recibo real del servidor. Mensajes basados en entradas creadas/ya registradas, no en el tamaño de una vista previa anterior. Invalidar día, rangos/tendencias y consumidores afectados; limpiar estado al cambiar de cuenta.
4. Idempotencia por operación: doble clic, respuesta perdida o reintento con la misma clave no duplica. **Dos comidas legítimas con el mismo alimento deben poder registrarse** con operaciones distintas. No deduplicar solo por nombre, fecha y nutrientes.
5. Compra→diario: seleccionar compra y líneas, mostrar cantidades efectivamente consumidas y permitir cambiarlas. Comprar un envase no implica comérselo entero. Congelar referencias de la previa; si cambia la compra o receta, revalidar o pedir nueva confirmación. Nada se registra al cerrar la compra sin una acción de consumo.
6. Fuentes nutricionales y valores se conservan como instantánea o versión resoluble: editar catálogo/receta mañana no cambia lo que se registró ayer. No declarar «etiqueta/ficha» como dato verificado si es texto manual sin evidencia; conservar el origen declarado y la confianza por separado cuando haga falta.

### Aceptación obligatoria

- Caso controlado: ficha por 100 g con 200 kcal, 10 g proteína, 5 g grasa y 20 g hidratos. Consumir 150 g registra **300 kcal, 15 g, 7,5 g y 30 g**; recargar conserva cantidades, fuente y referencia. Repetir la misma operación no añade otra entrada; otra operación legítima sí.
- Añadir una segunda entrada con energía desconocida y 12 g de proteína: energía conocida sigue 300, proteína conocida pasa a 27, cobertura energética 1/2 y proteica 2/2. No llamar a ese subtotal «total de todo el día».
- Casos adicionales: cero publicado válido, campo ausente, decimal con coma, negativos inválidos, NaN/infinito, receta escalada y unidad incompatible sin conversión inventada.
- Crear/borrar actualiza el gráfico ya abierto, no solo tras recargar. Red perdida y reintento no duplican. Comprar por sí solo deja el diario intacto.
- HTTP sobre la app montada: anónimo 401; B no enumera, lee, modifica ni elimina entradas de A por ID o fecha; cambio A→B en el mismo navegador no muestra cachés ni borradores de A. No basta probar funciones internas con un propietario simulado.
- Navegador en 390 y 1440: alta efectiva, lectura, recarga, borrado y tendencias. Guardar IDs y resultados, no solo una captura de pantalla vacía.

## G02. Texto libre útil en la lista

- Añadir «pan para mañana» sin elegir producto, manteniendo la línea y su cantidad/nota al recargar. Estado visible **Pendiente de identificar**; precio/coste desconocido, no cero. Debe contar como pendiente y mantener estimación parcial.
- Buscar después y vincular explícitamente un producto exacto, mostrando formato, cantidad y tienda. Conservar el texto original o nota. Desvincular no borra la necesidad.
- No usar el emparejador para convertir silenciosamente texto libre en una compra autorizada. Las sugerencias son candidatos, no elecciones del usuario.
- Probar convivencia de líneas identificadas/no identificadas, tachar/destachar, contador, duplicados intencionales, recarga, permisos del hogar y coste parcial. Mantener operaciones idempotentes sin impedir dos líneas legítimas iguales.

## G03. Revocación: medir la línea que se pulsó

- Fixture con al menos tres líneas: dos alternativas autorizadas y una exacta. Pulsar revocar en una de las dos autorizadas.
- Identificar la línea por ID estable. Verificar respuesta, almacenamiento y pantalla: solo ella pierde el consentimiento y el producto efectivo correspondiente; la otra conserva alternativa, tienda y cantidad; la exacta no cambia.
- Recargar y comparar los tres estados. Estimación/reparto/cierre no pueden seguir usando el producto revocado. Confirmación inválida por desaparición, cambio de identidad o ámbito de tienda requiere nueva decisión explícita.
- Un contador global de alternativas no acredita esto. Mantener pruebas de confirmación, revocación y desaparición ya existentes.

## G04. Dos recorridos completos, no excusas por catálogo en movimiento

1. **Catálogo fijo de ensayo**: versiones, productos, precios, nutrición y promociones controlados. Compra→lista→oferta→cierre→historial; receta→plan→lista; alimento/receta→diario→tendencias. Dos usuarios, móviles/escritorio, IDs y valores exactos.
2. **Cambio deliberado V1→V2 durante el uso**: buscar, abrir ficha, preparar compra/consumo, publicar V2, terminar o revalidar. No mezclar artefactos de versiones distintas dentro de una respuesta; no mantener infinitamente datos viejos sin indicarlo.
3. En un flujo de varias peticiones, hacer explícita la política de versión. Si una previa ya no es válida, devolver un conflicto comprensible y revalidar; no confirmar otro producto/precio/cantidad por debajo de la interfaz.
4. Probar desaparición de candidato, error de publicación y recuperación. Mantener compras/consumos ya guardados estables. Un cambio de catálogo no justifica descartar un fallo del recorrido.

## G05. Gráficas que expliquen algo real

Definir un contrato por gráfica: medida, unidad, universo, filtros, fechas/ámbito, cobertura, fuente, versión y qué significa un hueco. No conectar datos ausentes como si hubiera observaciones; no convertir ausencias en cero. Normalizar fechas, ordenar y tratar duplicados con una regla documentada.

### Compra

- Evolución del **mismo artículo exacto**, por tienda y ámbito, con fecha de captura. Separar precio del envase y precio unitario normalizado; no una sola línea mezclando €/kg y €/l.
- Comparación de alternativas como alternativas, mostrando formato y atributos que cambian; no presentarla como historial del mismo producto.
- Gasto pagado semanal/mensual a partir de compras guardadas e importes conocidos. Separar fechas de compra y de precios. Cobertura de importes históricos `NULL` visible.
- Reparto por categorías y ahorro estimado: declarar cuántas líneas tienen precio, restricciones de tiendas/club/ofertas, referencia contra la que se compara y si falta transporte. «Óptimo» solo con garantía del algoritmo para ese modelo; si es heurística, decirlo.
- Inflación de una cesta fija, si se ofrece: misma composición, cantidades, artículos/alternativas permitidas y reglas de sustitución, sin cambiar el universo para fabricar mejora.

### Calorías y Recetas

- Energía y macros de entradas registradas, con cobertura por nutriente. Días sin registro no son días de cero consumo. Días parciales deben distinguirse del subtotal plenamente conocido de las entradas registradas.
- Recetas: nutrición por ración y coste estimado, distinguiendo cantidad usada de coste de comprar envases; indicar ingredientes sin datos.

Aceptación: tabla accesible de los mismos datos, navegación por teclado, etiquetas/unidades/leyendas legibles, huecos y estados vacíos correctos, 390/1440 y zoom 200 %. Revisar `Chispa.tsx`, páginas consumidoras y contratos API; no arreglar solo el dibujo. No inferir «solo un día» de una serie vacía ni contar registros duplicados como días distintos.

## G06. Interfaz propia y profesional, conservando lo útil

- Mantener React/Vite y el sistema visual existente; aprovechar los documentos y referencias de Stitch, no reiniciar una maqueta genérica. No consumir más generaciones v0 ni copiar marcas/assets ajenos. Las claves no van en código, capturas ni documentos.
- Suite: menú lateral de aplicaciones y navegación de sección, con móvil accesible. Compra, Recetas y Calorías tienen pantallas, acciones y borradores propios. Evitar indicadores nutricionales dentro de acciones de compra salvo enlace/puente explícito.
- Compra: búsqueda por nombre/marca/categoría, ficha de producto con formato, identidad, precio/fecha, ingredientes/nutrición cuando existe; favoritos, listas, estados pendiente/carrito/comprado, comparación y compras anteriores. Acciones principales evidentes y recuperables.
- Recetas: biblioteca, editor, detalle/versiones/raciones, modo cocina y plan semanal. Calorías: diario por fecha, alta/borrado, selección de ficha/receta y tendencias. No tres páginas con la misma tarjeta genérica.
- Revisar textos, acentos, mensajes ambiguos, carga/error/sin resultados/sin datos, contraste, jerarquía, tamaños de toque y formularios. Error recuperable no debe borrar lo escrito.
- Ensayar un recorrido de primera cuenta sin datos y otro de cuenta con historial. Reducir clics sin esconder alcance, consentimiento ni datos ausentes. Buscar problemas en el componente servido, no en uno abandonado.
- Crear lista priorizada de mejoras visuales con capturas antes/después de la aplicación real. Las pantallas generadas son referencias, no evidencia de implementación.

## G07. Publicación y ejecución diaria: coherencia y recuperación

Auditar `projects/cesta/run.py`, `pipeline.py`, `emparejar.py`, `core/publicacion.py`, `core/manifiesto.py`, lectores API y `ejecutar.bat`.

- Construir una versión candidata coherente con catálogo, fichas/identidad/derivados que consumen los lectores y manifiesto. Publicar el puntero solo cuando su conjunto obligatorio esté listo. Revisar especialmente publicación dentro del pipeline antes de reconstruir grupos.
- Diferenciar captura, transformación, emparejado y publicación. Una captura válida puede conservarse aunque falle publicar, pero el resumen/marcador no debe insinuar que la aplicación sirve esa versión.
- Un fallo de publicación deja la última versión válida y un estado operativo accionable. Permitir reanudar publicación/derivados desde datos locales sin volver a scrapear todo. No invalidar días buenos por una cadena fallida ni ocultar qué cadenas están atrasadas.
- Manifiesto: fechas por cadena/precio/ficha, reglas/parser/modelo, cobertura, fuentes y versión. Descubrimiento con sitemap antiguo no implica automáticamente precio antiguo; medir ambos por separado.
- Pruebas de caída entre escrituras, publicación concurrente, lector durante cambio, artefacto faltante y reintento. Ningún lector adopta ficheros sueltos mutables como parte de una versión fijada.
- Mantener bloqueo de ejecución y escrituras atómicas. No añadir tareas diarias duplicadas. Respetar retención, pero no borrar crudo aún necesario para reparar una captura o un ensayo.

## G08. Fichas completas en todas las cadenas, con presupuesto

Inventariar Mercadona, DIA, Carrefour, Alcampo, Aldi y Lidl: lo que devuelve listado, ficha, crudo histórico y fuente complementaria. Reutilizar primero HTML/JSON ya guardado; luego cola incremental con prioridades y revisión de productos conocidos, no solamente nuevos.

Campos cuando la fuente los publica: GTIN/EAN, marca, denominación/variante, presentación y unidades del pack, contenido neto/escurrido, unidad de venta, ingredientes, alérgenos y trazas separados, nutrición y base, conservación/preparación, origen y especificaciones pertinentes. Conservar evidencia y campos fuente; no inventar lo ausente.

- Estados separados: pendiente, válido/fresco, desactualizado, no publicado, error temporal, parser fallido, excluido/revisión y retirada confirmada. Una ficha inaccesible o ausente del sitemap no acredita retirada.
- Cola reanudable, leases, deduplicación, límite por cadena, pausa ante bloqueo, TTL y fecha siguiente. Calcular cuánto tardaría en cubrir y refrescar todo el universo pertinente con el presupuesto real; tres fichas por ejecución no acreditan cobertura completa.
- Hash semántico de todos los campos relevantes, serialización estable y versión del parser. Revisar `_hash_util` de Lidl: hoy solo incorpora nombre, marca, EAN, precio y descripción; si se amplían campos, deben detectar cambios de ingredientes/nutrición/especificaciones.
- Fuentes complementarias, si están permitidas, con procedencia independiente. No rellenar campos de un producto parecido como si fueran de esa ficha; GTIN y presentación compatibles antes de vincular. No usar nutrición complementaria como prueba de precio/disponibilidad local.
- Unidades y bases: 100 g/100 ml/porción/preparado; kJ/kcal; sal/sodio; porcentajes y nutrientes por separado. Validaciones plausibles generan alertas/cuarentena motivada, no la afirmación de que «la web miente».
- Informe por cadena y familia: universo descubierto/incluido, fichas intentadas/leídas/frescas, cobertura por campo, antigüedad y errores. Un alto recuento total no acredita calidad ni exceso de bazar.

## G09. Lidl: no solo unas ofertas, ni una cifra artificial

- Medir fuentes públicas pertinentes: sitemap, familias/categorías, fichas y ofertas vigentes; distinguir catálogo habitual, campañas y no alimentación. Registrar qué parte se puede conocer y qué parte no publica la web.
- Clasificar consumibles y reutilizables domésticos seleccionados según contrato: incluir/excluir/revisión con motivo, seguridad para no excluir alimentos por coincidencias de palabras. No reabrir electrodomésticos/televisores como alcance.
- Integrar descubrimiento, cola de fichas y refresco de ofertas/precios en el ciclo diario, con presupuesto razonable y resumen específico. `ORDEN` actual sin Lidl debe resolverse o reemplazarse por una planificación explícita que realmente lo ejecute.
- No extender precio/disponibilidad de una campaña a todo el catálogo ni asumir venta online, tienda física o ubicación indistintamente. Conservar fechas de validez y ámbito.
- Fixtures de layouts reales y tests de parser; después comprobación de muestra estratificada vigente. Medir familias cubiertas, URLs procesadas, deduplicación y pendientes. No exigir mismo número que Aldi: demostrar cobertura accesible y publicar limitaciones.
- Si hay bloqueo o catálogo no expuesto, detener esa vía y documentar. No fabricar precios, eludir controles ni dedicar el objetivo entero a repetir fallos de red.

## G10. Identidad automática fiable, con abstención

- Separar artículo comercial exacto, familia/ingrediente genérico y alternativa. Un EAN distinto no demuestra por sí solo un error, y un EAN igual no autoriza ignorar conflictos de presentación o datos mal extraídos.
- Validar GTIN, normalizar marca y contenido neto, pack, variedad, composición clave, forma/estado y unidad. Atributos críticos por familia: entera/desnatada, con/sin lactosa, sabor, tipo de cereal, especie/corte, fresco/congelado, etc. Nutrición e ingredientes ayudan a corroborar/conflictar; no son una huella infalible.
- Generar candidatos eficientes y puntuar con reglas/algoritmos documentados; evitar que relaciones «parecidas» se propaguen transitivamente y creen grupos exactos falsos. Mantener candidato probable fuera del selector de exactos hasta cumplir criterios.
- Banco independiente estratificado por familias/cadenas, positivos y negativos difíciles; partición de evaluación que evite fuga entre variantes relacionadas. Medir precisión, falsas equivalencias, recuperación y abstención; indicar denominadores y errores analizados.
- Publicar en sombra primero y comparar con el motor anterior. Aprobar componentes demostrados sin exigir revisar manualmente todo el catálogo; conservar casos ambiguos en revisión. No convertir propuestas de división en errores históricos demostrados.
- Elegir un producto exacto no autoriza sustituirlo por una alternativa barata. Aplicar esta regla en todos los endpoints y costes, no solo en un aviso visual. Conservar solicitud original, producto efectivo, motivo, consentimiento y ámbito de tienda.
- Identificadores/versiones estables para favoritos, listas e historial. Cambiar el modelo no debe reasignar compras antiguas ni romper enlaces sin migración compatible.

## G11. Coste y reparto: un oráculo independiente

Conservar los controles ya añadidos de 3×2, reparto de céntimos, igualdad lista/cierre/histórico y migración 013. Extenderlos sin volver a presentar esa migración como pendiente.

- Evaluar todos los candidatos elegibles para la cantidad solicitada y sus promociones; no preseleccionar el menor €/unidad del envase antes de calcular coste final.
- Condiciones: fecha, canal/tienda, club autorizado, cupón, productos participantes, límite, umbral, cantidades, pack y redondeo. No aplicar club como descuento universal ni confundir ahorro estimado con cobro acreditado.
- Construir un oráculo por enumeración exhaustiva en cestas pequeñas, independiente del código de producción. Comparar asignaciones tienda/producto y coste final.
- Revisar optimización por línea cuando el precio depende del grupo comprado en una tienda. Repartir primero el descuento de una cesta completa y elegir luego las partes más baratas puede romper las condiciones del descuento: comprobarlo y recalcular promociones por asignación efectiva.
- Casos: 3×2 repartido entre líneas iguales; cantidades 1/2/3/4/6; productos distintos participantes; umbral de cesta; dos tiendas; oferta que caduca; club no autorizado; candidato sin precio; alternativa aceptada/revocada/desaparecida; coste parcial y cantidades incompatibles.
- Igualdad exacta en céntimos entre estimación del carrito, respuesta del cierre, total guardado y suma de `importe_cent` conocidos. Mantener desconocidos históricos como `NULL`. Identidad, tienda, cantidad y alcance de promoción persisten juntos, en transacción.
- Si no se obtiene óptimo global en producción, documentar la heurística y sus restricciones. No llamar óptimo a «el más barato observado» sin delimitar el universo.

## G12. Recetas: funcionalidad culinaria con datos honestos

- Verificar biblioteca, búsqueda/filtros, crear/editar/versionar/archivar, ingredientes con cantidades/unidades, pasos, raciones, modo cocina y plan semanal. Implementar lo que falte; no asumir completo porque `/recetas` tiene pantalla propia.
- Ingrediente genérico y producto seleccionado son entidades distintas. Permitir seleccionar producto sin obligar a que toda receta dependa de una marca. Alternativas propuestas por atributos y restricciones explícitas, no equivalencias comerciales inventadas.
- Escalar raciones sin modificar la versión base. Guardar en plan/diario referencia a versión y cantidades. Cambio posterior de receta no reescribe consumos anteriores.
- Receta→lista: previa de cantidades, consolidación compatible, distinción g/ml/unidades y envases enteros necesarios. Repetir la misma transferencia no duplica; otra semana/operación legítima sí. Descontar despensa solo si está modelada y la persona lo elige, no por haber comprado antes.
- Nutrición/coste por ración con cobertura y procedencia. Separar coste de ingredientes usados del desembolso por envases. No afirmar «sin alérgenos» cuando faltan ingredientes o trazas; no dar garantías médicas.
- Privacidad en listado, receta, versiones, plan, exportación y mutaciones: privadas por defecto, compartir explícito y revocable con hogar. Registros legado conservados sin propietario no se asignan por conveniencia. Pruebas A/B de rutas montadas y cachés.

## G13. Uso local seguro, rápido y recuperable

- Verificar cookies/sesiones, autorización del servidor, cambio de cuenta y borradores; revisar protección de mutaciones y manejo de errores. No confiar en IDs enviados por el cliente como propietario.
- Copia/restauración de PostgreSQL, SQLite de recetas/diario y referencias/versiones de catálogo necesarias. Ensayo en destino desechable que prueba recuperación, no solo que existe un ZIP. Conservar importes, producto efectivo, cantidades, tienda, recetas/versiones y privacidad.
- Migraciones idempotentes y no destructivas; rollback operativo sin recalcular históricos. No borrar bases ni asignar datos antiguos a un usuario para que pasen las pruebas.
- Rendimiento con catálogo real: búsqueda/paginación/filtros, consultas, gráficos y tamaño de frontend. Registrar escenario, hardware, tamaño y tiempos antes/después. Optimizar cuellos medidos, no migrar de tecnología por intuición.
- Arranque local y tarea diaria documentados; salud de servicios/catálogo y errores visibles. Secretos fuera del repositorio/logs; si hay exposición, rotación requiere coordinación, no reutilización en documentación.
- Diferenciar limitaciones de uso doméstico de requisitos pendientes de despliegue público: TLS, cookies/CSRF según entorno, secretos, backups automatizados, acceso, límites, observabilidad y obligaciones de fuentes. No publicar nada en este encargo.

## G14. Aprendizaje y aceptación final

Extender `docs/aprende/` sin duplicar capítulos existentes. Cada tema debe explicar problema, datos de entrada, transformación/algoritmo, salida, errores posibles, prueba y referencia a los módulos actuales. Ejemplos reproducibles con fixtures locales, sin lanzar miles de peticiones para aprender.

Temas mínimos:

1. Extracción responsable: listado/ficha/sitemap, HTTP, caché, paginación, límites, WAF, crudo y fuentes.
2. Bronze→silver→gold, Parquet/Polars/DuckDB y papel real de PostgreSQL/SQLite. No afirmar que dbt o Dagster orquestan el proyecto si no se usan; explicar qué aportarían como opción futura.
3. Normalización de unidades/packs/precios y nutrición; ausencia frente a cero; cobertura y procedencia.
4. Identidad/candidatos/reglas/modelos/banco independiente; precisión, recuperación, abstención y fuga de datos.
5. Promociones, redondeo, enumeración/optimización y coherencia transaccional del histórico.
6. Publicación versionada, concurrencia, privacidad, migraciones, recuperación y pruebas.
7. Diseño de gráficas: medidas, universos, sesgos, fechas, huecos y afirmaciones que el dato no permite.

### Puerta de cierre

Crear un informe final corto con matriz G01–G14 y S00–S12: criterio, evidencia, resultado y limitación. Ejecutar suite/lint/build/pruebas de cliente pertinentes y ensayos HTTP/PostgreSQL/navegador en entorno aislado. Medir las tres aplicaciones, dos cuentas, 390/1440, ancho estrecho y zoom/teclado; confirmar recuperación y catálogo cambiado durante uso.

No declarar «desplegable» por un número de tests ni por una imagen compilada. Estados finales permitidos:

- **Apto para uso doméstico local**, si los recorridos esenciales, privacidad, datos/costes y recuperación se verificaron; fuentes incompletas se muestran y no falsean decisiones.
- **Apto local con limitaciones explícitas**, si existen limitaciones de fuentes acotadas y el producto no promete más; enumerar funciones restringidas.
- **No apto todavía**, si persisten fallos esenciales de autorización, identidad/coste, registro, publicación o recuperación.

La publicación pública queda fuera. Informar por separado qué exigiría una fase posterior.

## 6. Qué hacer cuando no puedas terminar un paquete

No reemplazarlo por «me falta contexto» sin dejar continuación. Registrar prueba que falla, causa comprobada, diff conservado, dependencia y acción inmediata. Si falta un servicio, marcar implementación y ensayo pendiente por separado y trabajar un paquete independiente. Si una fuente no expone datos, medir la limitación y terminar lo demás; no reintentar indefinidamente ni inventar cobertura.

No finalizar todo el goal porque se cerró G01, una migración o un import. El objetivo continúa hasta verificar los paquetes aplicables y explicar con precisión los límites restantes. Al retomar, empezar en la acción inmediata del tablero, contrastando el estado git; no volver al principio de la bitácora.

## 7. Comprobaciones habituales y evidencia

Desde la raíz, `uv run pytest -q` y `uv run ruff check .`. Desde `plataforma/web/app`, `npm run tipos`, `npm run build` y `npm run test:cocina`, más las nuevas pruebas de cliente integradas en un comando documentado. No afirmar que `test:cocina` cubre diario/listas si no lo hace.

Inspeccionar y usar los guiones de `plataforma/prueba_navegador.py`, `prueba_suite.py`, `prueba_e2e.py`, `prueba_copia.py` y `prueba_transaccion.py` en entorno aislado, extendiendo sus aserciones. Anotar servicios, fixtures/versiones, IDs, comando, fecha y resultado. Una evidencia antigua se conserva como antigua; una cifra nueva se obtiene ejecutando.

**Próxima acción resumida:** G01, `Diario.tsx:Alta` y `api/diario.ts`: datos de cantidad/macros, respuesta real e invalidación de tendencias; fixture 150 g y cobertura independiente; recarga e idempotencia por operación; después G02, sin otra consulta rutinaria.
