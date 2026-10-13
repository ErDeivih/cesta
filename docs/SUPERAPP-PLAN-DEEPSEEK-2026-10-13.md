# Cesta · Encargo vigente para DeepSeek

Fecha: 13 de octubre de 2026. Revisión de partida: `dddc74e`.
Destino: `F:\aprendizaje\scrap`. Este plan sustituye el encargo operativo anterior,
no borra sus informes ni convierte sus cierres en evidencia nueva.

## 1. Objetivo y límites

Construir una superapp doméstica profesional con tres aplicaciones separadas:
Compra, Recetas y Calorías. Comparten catálogo, identidad, hogar y operaciones,
pero no confunden comprar, planificar, cocinar y consumir. La prueba principal
es planificar cinco recetas para una semana, comprar los ingredientes correctos
y registrar únicamente las porciones realmente comidas.

Prioridad: datos correctos y funcionamiento completo antes que más pantallas.
Lidl debe entrar en el ciclo diario como sexta fuente; su cobertura parcial se
declara y sus precios válidos pueden utilizarse para artículos observados. No se
afirma surtido completo, disponibilidad negativa ni cesta completa sin evidencia.

No hay despliegue público, apertura de puertos, pago, creación de cuentas de
terceros ni copia de código o diseño propietario. No se promete eliminar todos
los fallos de red: se exige detectar, recuperar, acotar y explicar cada fallo sin
corromper datos ni vender un resultado parcial como completo.

## 2. Qué está comprobado y qué solo cuenta el traspaso

Comprobado en esta preparación:

- Árbol en `dddc74e`; solo tres modificaciones ajenas previas: secciones, CIFRAS
  y el goal del 11. Se conservan sin editar ni commitear.
- `Cesta diaria` está **Running**; última ejecución 13/10/2026 a las 10:59:53.
  El log muestra progreso de Carrefour y Alcampo y renovaciones WAF. No se inició
  una segunda captura, no se mató el trabajo ni se movió el puntero.
- Bronze del 13: Aldi 10:57:37, Mercadona 10:57:53 y DIA 11:08:01.
  Alcampo/Carrefour todavía conservan bronze del 11 en el momento observado.
- API servida: versión **20261012-162023**, precios del **2026-10-11**;
  `/api/estado/publicacion`: seis ficheros `bien`, `coherente=true`.
  Coherencia de publicación NO significa frescura del precio.
- `ruff check .`: limpio. Los **1.999 Python / 74 frontend** proceden de DeepSeek;
  no se ha reejecutado aquí la suite completa ni un ensayo destructivo de copia.
- Hay pantallas de plan, cocina, despensa y diario; no hay que recrearlas a ciegas.

El traspaso informa de pérdida de 716 usuarios, 2.529 listas y 2.533 líneas del
entorno de pruebas por un ensayo de copia. Conservar ese incidente y verificar
las barreras actuales antes de volver a ejecutar restauraciones. No llamar
«irreparable» a un volumen sin inventariar backups/volúmenes de forma no destructiva.

### Hallazgos nuevos de código que impiden cerrar el encargo

1. `run._una_cadena` llama `mod.main()`; el colector Lidl exige origen de entrada
   y región explícita. No hay adaptador que convierta incluirlo en `ORDEN` en una
   ingesta diaria funcional. El `SystemExit` está aislado, pero no resuelve Lidl.
2. `api/cesta.py` excluye Lidl globalmente porque su catálogo es parcial. Parcial
   no significa que todos sus precios observados sean inválidos. La elegibilidad
   debe decidirse por artículo, región, fecha y condiciones; la cobertura de la
   cesta se decide por separado. La lista constante de cinco no cierra esta tarea.
3. `_del_plan` lee la versión guardada, pero no escala por los comensales de cada
   ocurrencia. `traer_del_plan` deduplica por nombre y añade una unidad: dos recetas
   con el mismo ingrediente no se suman; la segunda necesidad se salta.
4. El POST de receta individual `/{receta_id}/a-la-lista` sigue otro camino:
   `round(ln.cantidad) or 1`, unidad omitida e identificador convertido solo si
   `isdigit()`. Una identidad `fuente:id` no sobrevive a ese criterio.
5. `PlanSemanal.tsx` elige la lista de casa o, si no existe, la primera lista.
   Debe elegir destino explícito, no escribir en otra lista silenciosamente.
6. El recorrido de Recetas/Calorías del adjunto observa estados vacíos. Prueba
   que las páginas abren, no cinco recetas, cantidades, consumo y persistencia.
7. «SameSite=Lax + POST sin cookie → 401» no reproduce un ataque CSRF. Falta
   auditar origen, métodos y ataques con sesión en un entorno desechable.

El puente semanal también se reprodujo ejecutando
`uv run python -m scripts.auditar_puente_plan_20261013`, con mocks de conexión,
recetario y almacén, sin red ni bases reales: 100 g para dos raciones con cuatro
comensales más otra receta de 100 g para dos = 300 g requeridos; la previa devuelve
100/100, la mutación inserta una unidad y nota «100 g», y descarta la segunda
contribución como repetida. Es un diagnóstico, NO una aceptación verde del error.
Los demás hallazgos de lógica son por lectura. Antes de cambiar cada camino,
convertir el caso en regresión ejecutable controlada.

## 3. Reglas de producto ya decididas

- Artículo elegido = identidad exacta; alternativa = consentimiento explícito.
  Una familia permite explorar todas las leches, panes o pescados, no sustituir
  automáticamente un producto de marca/variante/envase ya seleccionado.
- Ingrediente genérico puede quedar pendiente de vincular, visible, con cantidad
  y unidad conservadas. No perderlo por no tener precio o catálogo.
- Una cantidad de receta NO es cantidad de envases. Usar dimensión compatible,
  tamaño publicado, envases enteros y sobrante. Sin tamaño: desconocido.
- Un mismo nombre NO es identidad suficiente para consolidar artículos concretos.
- Energía prevista NO es consumida. Compra y cierre no crean comidas. Cocinar
  tampoco declara quién comió ni cuánto: hay confirmación de ración por persona.
- Objetivo energético opcional, introducido por la persona; no asumir 2.000 kcal
  ni generar prescripciones de salud. Dietas/alergias usan datos acreditados;
  ausencia de alérgeno no significa «seguro».
- Presupuesto máximo, coste estimado y gasto pagado son tres conceptos distintos.
- Viajes: número de tiendas visible; coste monetario opcional y desconocido si
  no se ha introducido. No inventar que el desplazamiento es gratuito.
- Comida, bebidas, frescos, limpieza, higiene, bebé, mascotas y consumibles
  domésticos son el núcleo. Reutilizables de compra cotidiana pueden incluirse
  como sección optativa sin mezclarse con nutrición; no convertir esto en bazar
  de televisores, mobiliario o electrodomésticos.

## 4. Mapa de pantallas y responsabilidades

Una sola navegación global con Compra / Recetas / Calorías. Cada selección abre
su espacio y sus subsecciones; puentes explícitos con previa y recibo de operación.

| Espacio | Páginas necesarias | Acción principal |
| --- | --- | --- |
| Inicio | Resumen de casa, pendientes y estado de fuentes | Continuar tarea, no mezclar tres dashboards completos |
| Compra | Buscar/pasillos, ficha, comparar, listas, favoritos, modo tienda, histórico, gasto/ahorro | Comprar una lista con identidad y coste verificables |
| Recetas | Recetario, ficha/editor, plan semanal, previa de compra, cocina, despensa | Planificar y cocinar raciones, versionadas |
| Calorías | Diario, añadir alimento/receta/ración, previstos, mis alimentos, tendencias, objetivos opcionales | Registrar lo comido y ver cobertura |
| Común | Hogar/cuenta, preferencias, exportaciones, estado de datos y aprendizaje | Controlar datos, privacidad y procedencia |

No exige inventar rutas nuevas si existe la página. Revisar `App.tsx` y `Suite.tsx`,
anotar página real/ruta/estado y completar el recorrido. Una ruta oculta no es
descubrible; una pantalla vacía no equivale a capacidad terminada.

Mantener la dirección visual propia: papel/marfil, bosque y terracota, tipografía
legible, jerarquía editorial doméstica, no un mosaico genérico de métricas.
Cada pantalla debe tener una tarea dominante, unidades junto a cifras, cobertura,
acción de vuelta y estados de carga/error/reintento. Claro y oscuro, 390/768/1440,
zoom 200 %, teclado, foco, lectores de pantalla y controles de al menos 44 px.
No rediseñar toda la marca en cada ronda; usar los componentes existentes.

## 5. Modelo de integración: un solo cálculo, varios lectores

Reutilizar lo que ya funciona, pero unificar las dos transferencias que divergen.
Diseñar primero la representación normalizada de una necesidad:

- Ocurrencia planificada: id estable, dueño/ámbito, fecha, comida, receta y versión,
  comensales/raciones solicitadas, porciones asignadas cuando se conocen.
- Ingrediente: texto, cantidad decimal y unidad, dimensión, artículo elegido o
  genérico, evidencia de vínculo, origen y contribuciones de cada ocurrencia.
- Necesidad consolidada: cantidad requerida, disponible/reservada en despensa,
  cantidad pendiente, envase elegido, envases necesarios y sobrante.
- Compra: pedido original, producto efectivo autorizado, unidades de envase,
  tienda/ámbito, promoción aplicada, importe final y versión de catálogo.
- Consumo: persona, fecha/comida, porción real, receta versionada o alimento,
  snapshot nutricional, cobertura por nutriente y clave de operación.

La vista previa y la mutación comparten el mismo servicio. La previa no escribe.
La confirmación recibe su versión/revisión y falla explícitamente si cambió el
plan, la despensa o el catálogo. Cambiar uno no modifica retroactivamente compras
cerradas ni comidas registradas.

Idempotencia por operación y destino, no solo por nombre ni por semana actual:
enviar el plan de la semana siguiente el domingo debe usar esa semana elegida.
Reintentar la misma operación no duplica; otra sesión de compra o consumo
legítimo con contenido idéntico sí puede ser otra operación.

Si SQLite de recetas y PostgreSQL de listas intervienen, no fingir una transacción
distribuida: registro de operación, recibo y recuperación/reconciliación. Probar
caída entre ambos commits y reintento. Sincronizar despensa mediante reservas o
movimientos explícitos; no descontar de dos recetas el mismo stock dos veces.

## 6. Caso de aceptación principal: cinco recetas de una semana

Datos sintéticos; no depende del supermercado, promoción ni usuario reales.
Todas las recetas tienen dos raciones; cada ocurrencia se prepara para dos.

| Ocurrencia | Necesidad de toda la receta | Nutrición de prueba |
| --- | --- | --- |
| Lunes R1 | 150 g arroz seco | 360 kcal/100 g |
| Martes R2 | 200 g arroz seco | 360 kcal/100 g |
| Miércoles R3 | 500 ml leche | 60 kcal/100 ml |
| Jueves R4 | 0,5 l de la misma leche | 60 kcal/100 ml |
| Viernes R5 | 3 huevos | 80 kcal por unidad |

Resultados exactos exigidos:

- Arroz: 350 g necesarios; despensa confirmada 100 g; faltan 250 g. Envase 1 kg:
  un envase comprado y 750 g sobrantes de ese envase después de cubrir el déficit.
- Leche: 1 l requerido, una botella de 1 l; no 500 envases ni dos ingredientes
  ignorándose por compartir nombre. Huevos: pack de 6, uno comprado, 3 sobrantes.
- Raciones escaladas: si R1 pasa de dos a cuatro, cambia necesidad a 300 g;
  las otras ocurrencias no cambian. Distintas marcas no se consolidan sin autorización.
- Plan energético del hogar: 2.100 kcal sobre estas cinco preparaciones. Una
  persona que tiene una ración de cada una tiene 1.050 kcal previstas en esos platos.
  Es un subconjunto del menú semanal, NO toda su dieta ni el total que debe comer.
- Diario inicialmente vacío. Planificar/comprar/cocinar no registra consumo.
  Confirmar una ración de R1 = 270 kcal; media ración = 135. Reintento de la misma
  operación no duplica; otra ingesta legítima sí se registra.
- Cambiar después la receta o el catálogo conserva plan versionado y consumo
  histórico. Recarga confirma persistencia. Usuario B no ve diario ni receta privada de A.
- Caso adicional con proteína conocida y kcal ausente: conserva proteína;
  calorías desconocidas, nunca cero. Despensa con cantidad desconocida no descuenta.

Agregar una segunda variante con receta sin catálogo: entra en la lista como
pendiente, se conserva cantidad/unidad y el coste queda parcial. No se pierde sal
por ser manual ni se duplica una necesidad nueva porque ya existe su nombre.

## 7. Cola operativa B00–B16

Cada paquete: inspección → regresión → implementación → ensayo → evidencia.
Estados: pendiente, en curso, implementado sin ensayo, verificado, limitado por
fuente, bloqueado. Un bloqueo aislado no termina el objetivo entero.

### B00 · Seguridad de ensayos y estado único — primero

Inventariar tarea, procesos, runlock, Docker, DSN y rutas antes de ejecutar.
Proteger casa 5432, facylf 5433 y pruebas compartidas 5434. Restauración en
contenedores únicos, etiquetas de pertenencia, puertos verificados y DSN impuesto
en todos los subprocesos. No basta cambiar nombres: rechazar destinos protegidos
aunque lleguen por entorno. Verificar el servidor/base reales antes de DDL.
No retirar un contenedor ajeno por coincidir su nombre. Migraciones aditivas y
copias; no reinicializar tablas. Ensayo de guardas con DSN peligroso sin ejecutar DDL.
Aceptación: el guion se niega antes de escribir y deja bases protegidas intactas.

### B01 · Ingesta activa, progreso y recuperación

Al retomar mirar, no lanzar. Un pid antiguo de otra herramienta no es una sesión
recuperable aquí. Usar tarea, log y procesos actuales. Si sigue viva, trabajar B04–B16.
Progress JSON por cadena: fase, última petición, categorías/fichas, presupuesto,
reintentos, causa del bloqueo y heartbeat; no inferir progreso por mtime final.
Conservar checkpoints y resultados parciales aislados, reanudación idempotente,
estado degradado explícito y marcador del día sin confundir completo con parcial.
No ejecutar `P.publicar()` como sustituto de reconstruir pipeline y derivados.
Aceptar publicación solo cuando terminó su conjunto de artefactos y validaciones;
no adoptar mientras se escriben grupos/precios/promociones.

### B02 · Carrefour y Alcampo resistentes

Medir requests efectivos, cobertura de ramas, productos únicos, tiempo y motivo
de cada reintento. Parser de cero resultados válido versus HTML de desafío/error;
429/503 y Retry-After, backoff con límite, circuit breaker y checkpoints.
HTTP 200 no garantiza datos; desafíos no son catálogo vacío. No eludir CAPTCHA,
no aumentar presión ni introducir proxies furtivos. Si exige interacción humana,
marcar `requiere_interaccion`, conservar último válido y continuar otras cadenas.
No declarar «Alcampo nunca publica nutrición» por muestras insuficientes: registrar
URL/tipo de ficha/fecha/número de muestras y dónde el campo sí/no fue encontrado.
Aceptar fixtures de desafíos, esquema cambiado, página vacía, corte a mitad,
reanudar y publicación final, más captura acotada real cuando sea posible.

### B03 · Lidl como sexta fuente diaria y candidatos por artículo

Leer `collectors/lidl.py`, `descubrir_lidl.py`, `fichas_lidl.py`, `ficha_lidl.py`,
`sondear_lidl.py`, `run.py` y `docs/LIDL.md`. Adaptador explícito de CLI/config;
validar tienda/región y no convertir CP en id de región sin correspondencia.
Usar preferencia existente si acredita ámbito; si no, capturar descubrimiento sin
inventar precios regionales y pedir SOLO ese dato al propietario cuando sea necesario.
Reconciliar productos de campaña con productos descubiertos, no confundir IAN con
EAN ni promoción semanal con catálogo total. Entrada diaria con cobertura por campo.
Eliminar veto global a precios válidos de Lidl: permitir candidatos observados,
vigentes y de identidad acreditada, y marcar los no observados como desconocidos.
Lidl no gana una cesta completa si faltan líneas; sí puede ofrecer una línea exacta
con precio válido o una alternativa que la persona acepte.
Aceptación: ejecución desde el mismo runner diario, bronze→silver→gold→API→UI;
region/club/fechas/nutrición/ausencias probadas, captura acotada y contador visible.

### B04 · Contrato único plan/receta→lista — prioridad funcional

Regresiones para los dos caminos actuales. Escalar por ocurrencia/comensales,
consolidar cantidades compatibles por identidad, aplicar despensa explícita y
envases; preservar texto libre. Nada de `round(gramos)` como envases ni uno fijo.
Elegir lista destino de forma explícita; no fallback a la primera.
Normalizar `producto_id`, `grupo_id`, fuente y formato sin destruir `fuente:id`.
Aceptación: escenario de cinco recetas, dos listas, dos marcas y plan de otra semana;
preview=confirmación=persistencia, cambios/versiones y reintentos incluidos.

### B05 · Idempotencia y consistencia entre almacenes

Operaciones con recibo y huella del contenido; misma clave con contenido distinto
produce conflicto, no éxito ficticio. Concurrencia y caída tras insertar media lista.
Reservas de despensa y actualización del plan con cálculo incremental: editar un
menú no borra líneas manuales de compra ni duplica todas las necesidades.
Aceptar dos pestañas, versiones concurrentes, recuperación y destino distinto.

### B06 · Nutrición por campo, cadena y universo

Inventario de ingredientes, alérgenos, kcal, macros, fibra/sal, pesos, cantidades,
origen, conservación, descripción y fechas. Campo nativo/enriquecido/manual;
ausente/no aplicable/no publicado/error/pendiente diferenciados.
Cola por nuevos/cambiados/caducados, hash y presupuesto por fuente; no 88 horas
de fichas sin prioridad ni pedir cada detalle estable cada día. Históricos de ficha
para poder explicar identidad y cambios, no mezclar precio actual con detalle obsoleto.
Nutrición por 100 g/100 ml/ración y preparado/vendido. Conversión ml→g solo con
dato específico acreditado, nunca asumir densidad 1. Sin kcal no perder macros.
Aceptar cobertura con numerador/denominador, origen, fecha y causa de huecos.

### B07 · Recetario y cocina completos

Editor con cantidades/unidades, raciones, pasos, tiempos, etiquetas, foto propia,
fuente y vínculos de artículo. Importación manual/archivo con preview; URL solo
fuentes revisadas, guardas SSRF/redirecciones/tamaño/timeout y atribución.
Plan con varias comidas por día, repetir/duplicar semana y raciones por ocurrencia.
Cocina recuperable, pasos/temporizadores y preparado/pendiente, sin declarar consumo.
Aceptar cinco recetas con datos, edición, versión, importación permitida, cocina,
recarga y cambios de semana; no cerrar por entrar a cinco rutas vacías.

### B08 · Calorías integradas pero personales

Vista de previstos separada del diario real. Elegir receta versionada, porciones
efectivas y comida; consultar snapshot nutricional y cobertura antes de confirmar.
Acceso rápido desde plan/cocina con recibo de consumo y corrección/borrado propios.
Objetivo opcional por persona y fecha; grafías de registrado versus previsto versus
objetivo, sin totalizar un día no completo ni colorear diagnósticos médicos.
Aceptar R1=270, media=135, ausencia de energía con proteína conocida, idempotencia,
recarga y aislamiento A/B; compra nunca genera consumo por sí sola.

### B09 · Identidad y coste con oráculo completo

Reutilizar motor y pruebas existentes; banco de pares real/sintético con EAN,
marca/variante/neto/pack y contradicciones. Exacto/familia/alternativa/desconocido
visibles. EAN coincidente no neutraliza formato incompatible; distinto no acredita
mismo artículo. No modificar grupos de listas históricas por ordinal.
Evaluar candidatos elegibles después de cantidades/promociones/club/ámbito.
Contrastar asignaciones de una y dos tiendas con enumeración exhaustiva pequeña,
no solo sumas de céntimos. Mismo artículo efectivo y coste final en estimación,
cierre, líneas persistidas e histórico; 3x2 dividido y redondeos exactos.

### B10 · Compra profesional para familias

Favoritos/necesito/en carrito/comprado distinguidos, listas de casa y personales,
texto libre, orden por pasillos, búsqueda con marca/formato/EAN y filtros útiles.
Paginación fijada a versión/cursor y feedback sobre cambios del catálogo.
Histórico de gasto pagado, ahorro demostrable frente a referencia elegible y
estimaciones parciales con líneas que faltan. Presupuesto opcional y coste de viajes
separados. Reintento/offline/concurrencia no pierden cantidades ni revocaciones.

### B11 · Gráficas útiles, no decorativas

Gasto pagado semanal/mensual por tienda y categoría; precios del mismo artículo;
distribución y comparación de coste de cesta cubierta; plan y consumo por comida;
nutrientes con cobertura; sobrantes y despensa solo con movimientos conocidos.
Cada gráfica declara medida, unidad, universo, período, fuente y versión. Huecos
no son cero ni se unen silenciosamente. No comparar packs por precio absoluto.
Tabla accesible alternativa, exportación y explicación de una frase. Sin ocho
donuts de colores que no ayudan a decidir qué comprar o cocinar.

### B12 · Estudio de referencias con REA y documentación

Ver sección 8: una función por investigación. Priorizar consolidar el menú,
porciones/diario y flujos de lista. No estudiar un binario enorme por usar REA.
Aplicar ideas con código propio y diseñar la prueba equivalente en Cesta.
Una funcionalidad anunciada en una web no acredita su mecanismo interno.

### B13 · UX con datos reales y pruebas de recorridos

Inventariar rutas y componentes montados, evitar arreglar `Nav` si se sirve `Suite`.
Recorrer cinco recetas, compra y diario con usuarios de prueba, no cuentas reales.
Móvil/desktop, temas y zoom, HTTP retenida/error/cancelación/llegada tardía.
Capturas con versión de frontend/API, commit, catálogo, fecha y hash, más manifiesto
sin datos privados. Guardar evidencia referenciable sin commitear nutrición personal.
Medir pasos para plan→lista y receta→consumo; corregir mensajes, no tolerar fallos
porque haya publicación concurrente. No «cerrar A09 entero» con vacíos únicamente.

### B14 · Seguridad, copias y operación

Revisar CSRF con sesión real de ensayo, origen permitido/rechazado y misma-site
distinto origen; CORS no sustituye autorización de mutación. Auditar GET sin cambios,
Origin/Referer/Fetch Metadata o token según contrato y pruebas negativas.
Copias de PostgreSQL, SQLite privados y metadatos; restauración de los tres, hashes,
retención y verificación. Programación local solo con guardas; destino externo
requiere decisión concreta, no subir datos a una nube elegida por el agente.
Logs crecientes con rotación, métricas y secretos ausentes; TLS/registro/ratelimits
en matriz distinta de uso local. No declarar defensa completa por 401 sin cookie.

### B15 · Aprendizaje reproducible

Actualizar `docs/aprende`: fuente→raw→bronze→silver→gold→API, fichas versus precios,
Parquet/DuckDB/SQLite/PostgreSQL, entidades, unidades, matching, costes y promociones,
evaluación del algoritmo, linaje, nutrición y casos de errores reales.
DBT/Dagster: documentar qué está realmente instalado/usado; no introducirlos para
decorar el stack. Cada capítulo con ejemplo, comando seguro, salida esperada y test.

### B16 · Aceptación final, no cierre por cansancio

Puertas Python/client/lint/tsc/build, ensayos HTTP, sandbox PostgreSQL/SQLite,
cinco recetas completas en navegador, publicación durante el uso, recuperación
de ingesta y restauración aislada. Cero xfail/skips sin explicación específica.
Dictamen por capacidad: implementado/verificado/limitado, con versión y evidencia.
Separar usable en casa de desplegable para público. Si una fuente es inaccesible,
explicar alcance y no fingir que ya son seis catálogos completos.

## 8. Referencias y uso concreto de REA

Investigación documental inicial consultada el 13/10/2026; no se han descargado ni
decompilado las apps comerciales ni reproducido sus flujos privados en esta tarea.

- [Paprika 3, guía oficial Android](https://www.paprikaapp.com/help/android/):
  referencia de recetario, escalado, plan, listas y despensa, separadas por navegación.
- [Mealime, guía oficial](https://support.mealime.com/article/151-getting-started-guide):
  referencia de elegir varias recetas y consolidar ingredientes para comprar.
- [Cronometer, funciones oficiales](https://cronometer.com/features/):
  referencia de diario, recetas/alimentos y lectura de nutrientes.
- [OWASP, CSRF](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html):
  base para revisar la conclusión excesiva de SameSite. Releer sus condiciones,
  no convertir la recomendación en un requisito de token impuesto sin analizar contexto.

Estas referencias prueban funcionalidades documentadas, no el algoritmo ni la
calidad de uso observada. Cesta no tiene que imitar su marca ni añadir fitness,
red social o servicios de pago para ser completa en su nicho.

Laboratorio local: `F:\EspacioCodigo\ProyectoServidor\rea-sandbox`.
Leer skills `rea-windows-local` y `reverse-engineer-anything`; después el convenio
`estudiar-apps/AGENTS.md`, `OPERAR.md`, estado, `PLAYBOOK.md` y guía de interfaz.
El estado global incluye otros proyectos: este encargo es Cesta; no desviarse a
cazador, facylf o CueDigital ni cambiar sus objetivos. Crear un perfil de Cesta
si hace falta, conservando el trabajo ajeno del laboratorio.

Investigaciones separadas propuestas:

| ID | Una función | Referencia | Evidencia a conseguir |
| --- | --- | --- | --- |
| E01 | Consolidar compra de varias recetas | Paprika/Mealime | Cantidades, unidades y contribuciones de dos recetas |
| E02 | Confirmar una porción realmente consumida | Cronometer | Ración, snapshot y edición del diario |
| E03 | Descontar despensa sin doble reserva | Referencia autorizada | Cantidad disponible, desconocida y reintento |
| E04 | Recuperar cocina tras recarga | Referencia autorizada | Pasos/temporizador y persistencia |
| E05 | Recorrer lista en móvil sin red | Referencia autorizada | Pendientes, cambios y reconciliación |

Primero manual/capturas públicas; REA solo cuando la pregunta necesita artefacto
o runtime y hay objetivo concreto autorizado. Un repositorio propio con fuente
completa se estudia con herramientas normales. No descargar APKs de mirrors
desconocidos, eludir licencias/login/pagos, CAPTCHA ni protecciones.

Para REA usar el MCP anunciado o `node ...\rea-local.mjs`; no parchear node_modules.
Comprobar el entorno conforme al kit al iniciar análisis real. Leer la guía
específica browser/JS/Android antes de su herramienta. No inventar herramientas
ausentes ni conectar a puertos de depuración de cuentas ajenas.
Registrar versión/hash o URL/fecha, evidencia `ev_...` o fichero, demostrado /
hipótesis / desconocido, y diseño propio con prueba equivalente. Cerrar sesiones.
Los APKs/instalaciones que no sean de análisis permitido son un bloqueo de esa
investigación, no permiso para detener B04–B11.

## 9. Cómo trabajar sin perderse ni parar por cada detalle

Fuente operativa única: `SUPERAPP-GOAL-ACTUAL.md` → este plan →
`SUPERAPP-CONTROL-DEEPSEEK-2026-10-13.md`. Los documentos anteriores son históricos.
Antes de cada continuación leer objetivo, paquete y próximo comando, no toda la
bitácora. Si el estado escrito difiere de la máquina, manda la evidencia actual.

Una ronda debe entregar código verificado, una reproducción útil o evidencia
que cambie una decisión. No consumir una ronda por repetir «sigue Running» ni
resumir de nuevo el mismo commit. Mientras hay ingesta, completar trabajos
independientes. Si dos intentos de instrumento fallan, inspeccionar su contrato
y reducir el caso antes de otro parche por sustitución de texto.

Después de cada paquete actualizar SOLO estado, evidencia, qué falta y próximo
comando. No reescribir cientos de líneas de historia. No cerrar una tarea porque
la interfaz muestre un aviso; demostrar además cálculo, permisos y persistencia.

No usar un número de rondas como objetivo. El criterio es completar B00–B16 con
evidencia. Si necesita interacción WAF, ámbito Lidl o destino externo de backup,
presentar una pregunta acotada y continuar lo independiente. No inventar esa decisión.

Preservar los tres ficheros ajenos y cualquier cambio nuevo concurrente. No tocar
5433 ni ejecutar restauraciones sobre 5432/5434. Leer antes de parchear; cambios
propios pequeños, pruebas asociadas y commits solo de su ámbito según instrucciones
del repositorio. Ningún secreto del historial pasa a documentación, logs o Word.

## 10. Primera continuación exacta

1. Comprobar tarea, log, runlock, API de estado/publicación y git; no arrancar otra
   ingesta si la actual vive. No reutilizar `pwsh-9853` como si existiera en esta sesión.
2. Auditar guardas de B00 sin ejecutar restauración. Registrar estado en control.
3. Reproducir B04 con fixtures del escenario: comensales, arroz compartido,
   ingrediente genérico y dos destinos. Arreglar ambos caminos con un servicio común.
4. Completar B03 en paralelo temporal con la espera de red: adaptador/config,
   elegibilidad por artículo y prueba diaria offline. No pedir una campaña masiva.
5. Cuando acabe la ingesta, comprobar su resultado y publicación normal. Si falla,
   registrar qué cadena/fase falló; recuperar desde checkpoint cuando proceda,
   sin republicar datos a medio construir. Después continuar B05–B16.

No hay un «ya está porque pasan 1.999 pruebas»: esos tests son una base que se
preserva; las funciones nuevas requieren sus propios contratos y recorridos.
