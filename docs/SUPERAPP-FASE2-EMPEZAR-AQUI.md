# Cesta fase 2: verificar lo entregado y mejorar las tres aplicaciones

Fecha: 11 de octubre de 2026. Base revisada: `480ac21`.

## 1. Goal prolongado

Convertir Cesta en una suite local propia y profesional que resuelva compra doméstica, recetas y registro nutricional con el nivel funcional de referencias pertinentes, sin clonar sus diseños ni sacrificar identidad, costes, privacidad o procedencia. **Primero reconciliar cierres con pruebas reales; después estudiar una capacidad, implementarla y verificarla, y continuar con la siguiente.** Alcanzar los criterios de esta fase y publicar límites concretos, no cerrar por una cifra de tests ni por haber leído una regla.

Destino: `F:\aprendizaje\scrap`. Laboratorio auxiliar: `F:\EspacioCodigo\ProyectoServidor\rea-sandbox`. Mantener los tres ámbitos separados: Cesta es producción local; el laboratorio produce evidencia; las referencias no se modifican.

No despliegue público, gastos, suscripciones ni migración de stack. La autorización permite priorizar y ejecutar mejoras reversibles de estas tres apps; no tocar otros proyectos ni el registro DSH. El objetivo es trabajo continuo con memoria y entregas, no una promesa de ejecución infinita sin límites del entorno.

## 2. Lectura y arranque autónomo

1. Inspeccionar git y convenios aplicables. Preservar cambios ajenos. `core/datos/secciones.yml` y `docs/CIFRAS.md` siguen fuera de los commits del encargo.
2. Leer este documento, [tablero de fase 2](SUPERAPP-FASE2-EJECUCION.md) y [competencia/REA](SUPERAPP-COMPETENCIA-Y-REA.md).
3. Leer [goal anterior G01–G14](SUPERAPP-GOAL-CONTINUACION-2026-10-11.md), [informe de cierre](INFORME-DE-CIERRE.md), resumen vigente y pruebas del paquete actual. El goal anterior es contrato e historial, no fotografía actual del código.
4. Contrastar la función servida, no solo un helper. Ejecutar una reproducción aislada antes de declarar un fallo corregido o un cierre válido.
5. Empezar **F00**. No repetir G01 entero: los campos de macros, respuesta real, invalidación de tendencias y Lidl en `ORDEN` ya están en el código revisado.

Para investigar referencias, seguir el kit como se concreta en `SUPERAPP-COMPETENCIA-Y-REA.md`. No continuar automáticamente las tareas de RadioPV del laboratorio: esta tarea ya tiene destino y prioridades.

## 3. Hallazgos de esta revisión: qué cambia respecto al cierre

Esta revisión leyó código y documentos y ejecutó las seis pruebas básicas de REA. **No reejecutó la suite de Cesta ni sus recorridos visuales**. Los siguientes son límites de evidencia o riesgos localizados que deben convertirse en pruebas; no una lista de fallos todos reproducidos.

| Hallazgo localizado | Evidencia de partida | Qué exigir |
|---|---|---|
| Tablero desactualizado | `SUPERAPP-EJECUCION.md` empieza con G02 pendiente y varias etapas pendientes, mientras `INFORME-DE-CIERRE.md` las declara cerradas. | Un estado único breve, enlazado a evidencias y sin esconder pendientes al final de la bitácora. |
| Aceptación rebajada | Informe llama G02 «texto libre del diario», pero G02 pedía lista; G04 resume conservación del histórico, no las tres apps durante publicación. | Relacionar cada criterio original con prueba exacta, no renombrar el criterio para adaptarlo a la prueba. |
| Multi-tienda sin demostrar | Informe G11 admite que el oráculo cubre aritmética, no asignaciones multi-tienda. | Oráculo exhaustivo independiente de asignaciones y promociones condicionadas al conjunto. |
| Sustitución estimada frente a compra | `coste_por_linea` filtra candidatos cuya llave termina en `alternativa`; `test_g03_cierre.py` prueba archivar el producto del grupo, no el sustituto. | Probar compra realmente realizada del sustituto aceptado, su identidad/precio/promoción/tienda y recibo. No dar por correcto ese contrato por estar verde. |
| Reintento manual del diario | `Diario.tsx:Alta` genera UUID en cada submit. Backend deduplica por clave. | Respuesta perdida seguida de pulsar otra vez: reutilizar operación pendiente; doble submit y carga idéntica con clave reutilizada. La prueba de mismo UUID por HTTP no cubre la UX. |
| Clave de diario escrita después del INSERT | `core/diario.py:apunta` busca la clave, inserta entrada, actualiza clave y hace commit. | Concurrencia/conflicto y atomicidad; misma clave con payload distinto no debe devolver éxito ambiguo. Definir recibo y política, probar. |
| Publicación y derivados | `pipeline.py` todavía captura fallo de publicar; el ciclo reconstruye grupos después del pipeline. | Auditar cierre de versión y estado diario. El arreglo de las fechas del puntero no demuestra coherencia de todos los artefactos. |
| Fichas sin ejecución suficiente | Informe anterior registra 79.887 sin ficha y cinco cadenas sin cobertura. | Medir situación actual por campo/cadena, integrar ejecución real, parser y presupuesto; no llamar toda ausencia «limitación de fuente». |
| Riesgo de identidad estable | Tablero describe grupos ordinales renumerados y migración a producto estable; informe da G10 cerrado por lectura. | Prueba lista/favorito/receta sobreviviendo a reordenación y separación de grupos. Resolver cualquier consumidor aún ligado a ordinal. |
| CSRF no ensayado | Informe lo posterga y dice que mismo origen lo hace irrelevante. | No aceptar esa inferencia: comprobar solicitudes cross-origin, cookies y mutaciones de la app local; mismo origen normal no prueba defensa. |

Se conservan avances reales: formulario y recibos del diario, huecos en gráficas (`spanGaps: false`), seis cadenas en el orden, texto libre del servidor, importes históricos, búsqueda del recetario y puente receta→lista. Medir regresiones, no reescribirlos por partir de un informe antiguo.

## 4. Modo de trabajo y continuidad

- Una capacidad por investigación y entregable. Dentro de Cesta completar modelo/API/UI/persistencia/pruebas pertinentes. Después avanzar; no gastar una ronda por import ni cerrar tras un documento.
- Decidir defaults reversibles dentro del contrato. No preguntar qué competidor estudiar: están priorizados en la matriz. No pedir otra confirmación para Compra, Recetas y Calorías separadas.
- P0: pérdida de datos, permisos, identidad/costes y publicación. P1: recorridos fundamentales y datos de seis cadenas. P2: rapidez, visual y capacidades adicionales. Si hay defecto P0, resolver antes de ampliar funciones dependientes.
- Mientras se investiga una referencia, detenerse cuando haya especificación comprobable. Primero ayuda pública/observación; REA solo ante pregunta interna concreta y objetivo permitido. No descifrar un backend remoto por intuición ni intentar eludir licencias/CAPTCHA.
- Pruebas enfocadas durante desarrollo; suite/lint antes de commit, tipos/build y todos los tests de cliente pertinentes si cambia frontend. Integrar los tests nuevos en comandos habituales: que exista un fichero no significa que el comando lo ejecute.
- Entorno aislado para cuentas/compra/diario/catalogo; no experimentar con datos de casa. Docker solo se comprueba al retomar o antes de un ensayo dependiente, no en cada ronda.
- Si algo falla dos veces igual, revisar diagnóstico y cambiar método, no añadir esperas. Si falta un servicio, registrar implementación y ensayo pendiente separadamente y avanzar una pieza independiente.
- A cada entrega, actualizar **solo un resumen breve** en el tablero: estado, evidencia y siguiente paso. Anexar informes por función para detalles, no crecer el tablero con 200 rondas. La tabla anterior de G01–G14 debe reconciliarse, no borrarse ni maquillarse.
- Antes de pausar por contexto, dejar fichero/función, caso que falla, diff, dependencia y acción inmediata. No declarar goal completo por alcanzar límite de contexto.

Pedir intervención únicamente ante credencial imprescindible, interacción humana/condiciones, coste nuevo, acción destructiva, publicación pública o conflicto irresoluble con otro escritor. Una app de referencia inaccesible se sustituye por otra o se limita a documentación; no detiene todo Cesta.

## 5. Paquetes y criterios de aceptación

### F00 · Reconciliar contrato, código y evidencia (P0)

Construir matriz de todos los criterios G01–G14 y S00–S12 con: conservado/verificado/pendiente/limitado, prueba exacta, ejecución/fecha, limitación. Corregir encabezado operativo del tablero anterior sin alterar los informes históricos ni reutilizar sus cifras. Un contrato completo no se acredita «por lectura» cuando exige navegador, concurrencia o HTTP.

Preparar catálogo controlado, dos usuarios y bases desechables. Ejecutar baseline actual y documentar skips/dependencias. Inspeccionar ensayos antes de lanzarlos. Separar problemas de fixture y producto con reproducción mínima. No seguir usando «apto local» como premisa: confirmar o rectificar tras las pruebas.

**Aceptación:** cada cierre tiene evidencia que cubre lo pedido o un pendiente explícito; siguiente tarea concreta F01. No dedicar toda la fase a escribir esta matriz: es preparación para actuar.

### F01 · Identidad estable y compra del producto efectivo (P0)

Seguir lista/favorito→solicitud→candidato→consentimiento→carrito→cierre→histórico. La solicitud original permanece; el producto efectivo comprado debe ser el exacto elegido o la alternativa específicamente aceptada. Un nombre/grupo renumerado no es identificador estable.

- V1 con producto A, V2 reordena grupos y añade B de otra categoría, V3 divide un grupo. La lista/favorito continúa apuntando A o queda pendiente motivado: jamás B por ordinal.
- Escenario de sustitución: A pedido, B aceptado en tienda T, tres unidades y oferta B 3×2. Estimación/cierre/histórico conservan B/T/3 y el mismo coste final. Al revocar, B deja de ser elegible; conservar otras líneas y consentimientos.
- Si la persona elige comprar de nuevo A, requiere acción explícita y actualización del efectivo; no archivar A «porque era el grupo» mientras se compró B.
- Migrar consumidores por pasos compatibles, conservando históricos y datos sin referencia como desconocidos, sin asignar arbitrariamente. Separar modelo de pertenencia al grupo y artículo permanente.

**Aceptación:** recorrido HTTP y navegador más almacenamiento real aislado, sumas en céntimos e identidades; tests actuales que consagren un contrato incorrecto se sustituyen con justificación, no simplemente se borran.

### F02 · Reintentos, cantidades y aislamiento del diario (P0/P1)

Mantener la operación pendiente y su payload hasta recibir resultado inequívoco o cancelación explícita. Simular servidor que guarda pero pierde la respuesta; pulsar otra vez no duplica. Nueva comida igual sí se registra. Misma clave con otro payload produce conflicto o política explícita, no éxito que parece guardar otro dato. Probar dos solicitudes simultáneas con misma clave y rollback limpio.

Cantidad/unidad/base: g, ml y raciones con conversiones trazables. Que SQLite tenga columna `unidad` no acredita API/cálculo/UI. Consumir parte del envase, no compra entera por defecto. Vista previa congelada a compra/líneas y receta/versiones; cambio antes de confirmar exige revalidación.

**Aceptación:** caso controlado 150 g, cobertura independiente, respuesta perdida, concurrencia, receta editada después, cambio A→B y cachés/borradores, 390/1440. Comprar no registra consumo.

### F03 · Publicación coherente y uso durante cambio (P0)

Construir/publicar todos los derivados de una versión antes del puntero. Inyectar fallos entre pipeline, matching, manifiesto y publicación. Resumen diario distingue capturado/procesado/publicado; reanuda desde crudo sin rescrapear todo. Última versión válida sigue servida y fechada correctamente por cadena.

Ensayar las tres apps con V1 fija y luego publicar V2 durante búsqueda, previa de lista, sustitución y alta de receta/comida. Respuesta individual no mezcla versiones; flujos de varias peticiones tienen token/versión o revalidación. Historial y consumo antiguos no cambian.

**Aceptación:** pruebas reales de API/almacenamiento y dos recorridos de navegador; el test de que un histórico no cambia es necesario pero insuficiente.

### F04 · Privacidad local y recuperación (P0)

HTTP A/B en listas, recetas/versiones/plan y diario/exportaciones; cuentas/hogares y cachés. Verificar mutaciones desde origen ajeno, atributos de cookies, política de Origin/CSRF pertinente al entorno; no exigir TLS público para probar privacidad local ni considerar localhost exento de ataques de navegador.

Restaurar PostgreSQL, ambas SQLite y referencias de catálogo en destino desechable; probar cantidades/importes/identidades/versiones y permisos. Copia en el mismo disco no acredita resiliencia ante fallo del disco; documentar qué puede hacerse localmente sin gastar ni copiar datos a un proveedor.

**Aceptación:** pruebas montadas y restauración verificable, sin borrado real, secretos redaccionados. Seguridad pública sigue siendo otra fase.

### F05 · Seis cadenas y fichas: cerrar brecha de datos (P1)

Inventario actual, no números del cierre: descubiertos/incluidos/revisión/excluidos, precios frescos, fichas intentadas/útiles, cobertura por campo y fecha. Alimentación, limpieza, higiene, bebé, mascotas y reutilizables domésticos seleccionados; no bazar duradero general.

Conectar ejecución incremental de fichas de **las seis cadenas** al ciclo real y garantizar seguimiento de conocidos. Presupuesto configurable por cadena, TTL, leases, reintentos acotados y plazo calculado con throughput observado. «No ejecutado», «parser no extrae» y «fuente no publica» son estados distintos. Aumentar límite no prueba capacidad de procesar mil fichas correctamente.

Extraer ingredientes, alérgenos/trazas, nutrición/base, presentación, neto/escurrido, marca/GTIN, conservación/preparación/origen/especificaciones cuando existen. HTML/crudo primero, JSON-LD solo una vía. Fuente complementaria con coincidencia y procedencia separadas; no completar por parecido ni trasladar precios de campañas a surtido habitual.

**Lidl:** código ahora integrado en `ORDEN`, pero demostrar qué descubre y qué obtiene cada día. Explorar HTML accesible y datos ya capturados si JSON-LD no publica el detalle. No exigir paridad con Aldi, sí coverage por familia y limitación demostrada. Revisar fuentes/campos con muestra estratificada, sin seguir golpeando WAF.

**Aceptación:** una ejecución limitada real por cadena, reanudación, actualización de ficha conocida, cobertura antes/después y cola visible. No cerrar todo como limitación de fuente cuando cinco workers no han corrido.

### F06 · Matching y optimizador contrastados (P0/P1)

Preservar motor en sombra y banco independiente. Medir positivos/negativos duros por familia/cadena y candidatos, precisión/recall/abstención con denominadores. Mismo GTIN no ignora contradicciones; distinto GTIN no demuestra engaño. Formato/familia/alternativa no son artículo exacto. Evitar transitividad de parecido creando falsos exactos.

Construir oráculo exhaustivo de **asignaciones multi-tienda** para cestas pequeñas, independiente del optimizador. Aplicar promociones a cada conjunto realmente asignado, umbral, club, envases, fechas y máximo de tiendas. No elegir partes de un descuento calculado sobre una cesta que al final no se compra en esa tienda.

**Aceptación:** casos combinatorios con contraejemplos, discrepancias cero para escenarios cubiertos, suma de partes igual al total; garantías y límites del algoritmo publicados. Heurística se llama heurística.

### F07 · Compra rápida, familiar y clara (P1)

Investigar C01–C05 con Bring!/AnyList/Listonic. Mejorar solo lo que falte: lista por pasillos y orden persistente, añadir texto/cantidad/nota/foto autorizada, habituales/favoritos, deshacer, estado necesito/no necesito y carrito/comprado. Búsqueda tolerante a acentos/errores, filtros de cadena/categoría/marca y consulta entendible, sin bajar precisión de identidad.

Dos usuarios concurrentes del mismo hogar no pisan cantidades ni tachados; conflictos claros, sin empujar sincronización cloud. Flujos sin catálogo y con datos parciales útiles. Llevar favorito a lista no significa que se necesite cada semana.

**Aceptación:** tarea móvil con una mano, recorrido de cuenta vacía, recarga y dos sesiones; medir pasos/latencia antes/después y conservar controles del contador.

### F08 · Comparar, presupuesto y ahorro de verdad (P1)

Investigar C06–C10 con Soysuper/Bring!/Listonic. Pantalla del mismo artículo con formato/fecha/ámbito y alternativas separadas. Una tienda vs varias con condiciones elegibles, cobertura y máximo de tiendas. Desplazamiento opcional declarado por usuario; no geolocalización ni transporte estimado sin consentimiento.

Presupuesto de compra y gasto pagado por periodos/categorías. Precio manual de recibo se conserva como pagado, distinto del estimado del catálogo. Club/crédito futuro fuera del pago inmediato. Reutilizar compras sin copiar precios viejos como vigentes. Si se añade alertas de bajada, ámbito/fecha y deduplicación, no notificaciones externas nuevas.

**Aceptación:** lista parcial, cupón/club no elegible, oferta caducada, cantidad/pack, histórico desconocido y ahorro neto con referencia explícita; igualdad de cifras entre pantalla y API.

### F09 · Recetario completo y recuperación de borradores (P1)

Investigar R01–R04 con Paprika/Samsung Food. Búsqueda y filtros útiles, favoritos/colecciones, editor, versión y borrador recuperable sin mostrar el de otra cuenta. Importar receta por URL/archivo permitido con previa editable, fuente y advertencias; evitar SSRF en importador (URL, red local, redirecciones, tamaño/tiempo) y scripts activos en contenido importado. No abrir un importador arbitrario sin límites.

Raciones y cantidades reproducibles; unidades incompatibles sin conversiones inventadas. Recetas genéricas no obligan a marca. Receta antigua del diario sigue resoluble.

**Aceptación:** normal/error/URL inválida/duplicado/borrador/versiones/aislamiento; recetas de fixture propias o licenciadas, no copiar biblioteca ajena.

### F10 · Plan semanal, modo cocina y puentes (P1)

Investigar R05–R07 con Paprika/AnyList/Cookidoo/Mealime. Cola sin fecha y calendario editable, copiar semana, notas, drag-and-drop con alternativa de teclado. Modo cocina: pasos/ingredientes, temporizadores, foco/contraste, mantener pantalla cuando API lo permita y fallback, reanudación explícita.

Plan→lista: seleccionar lo necesario, consolidar compatibles y mantener trazabilidad ingrediente→receta. Porciones necesarias vs envases y coste de ingredientes usados. Idempotencia por operación, misma operación distinta carga conflictiva; nueva semana legítima sí. Probar endpoint HTTP además del helper.

**Aceptación:** dos recetas con ingrediente compartido, mezcla kg/g compatible y ud incompatible, cantidades ausentes, otra lista/hogar no autorizado, recarga y errores conservando la previa.

### F11 · Despensa y aprovechamiento (P2)

Investigar R08–R10; construir versión local pequeña, no inventario logístico. Stock declarado con unidad, ubicación opcional (nevera/congelador/despensa), caducidad opcional y ajuste manual con historial. Proponer registrar compras en despensa explícitamente; diario/compra no descuentan automáticamente stock sin regla confirmada.

Sugerir recetas por ingredientes disponibles, faltantes, fecha conocida y coste parcial. Descontar existencias en previa de plan→lista solo si se elige. No garantizar alérgenos seguros con fichas incompletas ni sustituir producto exacto por esa sugerencia.

**Aceptación:** consumo parcial/stock desconocido/unidades incompatibles/fecha ausente, filtros y privacidad; pendiente visible en vez de «tienes todo» inventado.

### F12 · Calorías con registro ágil, no solo formulario (P1)

Investigar N01–N06 con Cronometer/YAZIO/MacroFactor. Selección reciente/favorita, búsqueda por alimento/marca/GTIN, código de barras con permiso de cámara y fallback manual; no subir imágenes a servicios de pago. Mostrar candidato exacto/formato/origen antes de confirmar. Varios alimentos por comida, copiar comida a otro día y cantidades editables.

Alimentos personales, receta versionada y porción; edición/borrado/deshacer coherentes. Copiar comida es nueva operación y no comparte una clave que impida guardarla. Unidad real y fuente por dato; no convertir etiquetas incompletas en nutrición completa.

**Aceptación:** GTIN desconocido/varios candidatos/cámara denegada, reintentos, dos comidas iguales y cambio de usuario. No prescripción de dieta, ayuno ni calorías de una foto.

### F13 · Analítica legible de las tres apps (P1)

Gráficas: medida/unidad/universo/fecha/ámbito/cobertura/fuente; tabla equivalente y huecos reales. Compra: gasto pagado, cesta comparable fija y ahorro bajo restricciones. Recetas: coste usado/envases y nutrientes por ración. Diario: subtotal registrado y cobertura por nutriente, energía ausente `null`, ningún día vacío como cero consumo.

Campos nutricionales adicionales solo si disponibles (fibra, azúcares, saturadas, sal, etc.), manteniendo base y fuente; agregar independientemente de energía. No jerarquizar alimentos como saludables por algoritmos opacos.

**Aceptación:** datos controlados exactos, filtro que cambia universo explicado, fechas duplicadas, series vacías/parciales, cambio catálogo/cuenta, borrado de comida que repinta tendencia; teclado y zoom.

### F14 · Sistema visual propio aplicado (P1/P2)

Hacer inventario de pantallas servidas y componentes, no rediseñar solo una portada. Adoptar la dirección de [competencia/UI](SUPERAPP-COMPETENCIA-Y-REA.md), refinando tokens actuales. Compra más operativa, Recetas más culinaria, Calorías más registrable; armazón común sin mezclar acciones ni borradores.

Crear antes/después con mismos fixtures. Simplificar jerarquía, números/unidades, textos y estados; densidad adecuada para móvil y catálogo grande. No marcas, logos ni iconos extraídos de competidores. Reutilizar referencias Stitch existentes; no más v0 ni claves en repo.

**Aceptación:** 360/390/768/1440, zoom 200 %, teclado/cajón/foco, reducción de movimiento, contraste y carga/error/vacío; validación de recorridos con datos, no solo maqueta bonita.

### F15 · Offline, rendimiento y aprendizaje (P1/P2)

Definir qué funciona sin red local/servicio: datos cacheados fechados, borradores y acciones pendientes. No anunciar sincronización completa si solo hay caché. Si se implementa cola offline: operaciones con IDs, payload, propietario, caducidad/revalidación y conflicto; logout no deja datos privados accesibles a otra cuenta.

Medir búsqueda/listas/fichas/gráficas con volumen real: paginación, índices, cargas, tamaños JS y latencias p50/p95 bajo escenario declarado. Optimizar cuello medido antes de incorporar más infraestructura.

Actualizar material educativo con ejemplos reproducibles crudo→normalización→identidad→coste/nutrición→pantalla; explicar algoritmo y errores, nuevas decisiones y pruebas. No afirmar uso de dbt/Dagster si no existe.

**Aceptación:** mala conexión/error/recuperación sin duplicados y cuenta cruzada; antes/después de rendimiento; ejemplos locales ejecutables y docs enlazados.

### F16 · Ensayo integral y cierre honesto

Matriz de capacidades C/R/N/X y paquetes F00–F16 con estado y evidencia. Suite Python/lint, build/tipos, todos los tests de cliente; HTTP montado; PostgreSQL y SQLite reales aislados; recorridos navegador, publicación durante uso y restauración.

Informe final distingue: implementado, probado, límite demostrado de fuente, pendiente y descartado por alcance. No «cerrado por lectura» en lugar de pruebas exigidas. No presumir alta calidad por cantidad de filas/tests ni ampliar alcance para parecer un clon completo.

Veredicto doméstico depende de privacidad, identidad/costes, registro, publicación y recuperación. Limitaciones nutricionales/fuentes pueden mostrarse sin bloquear todo, pero una sustitución mal guardada no se convierte en limitación menor. Despliegue público excluido y evaluado por separado.

## 6. Primeras acciones concretas y comprobaciones

1. F00: comparar informe con criterios G y pruebas, fijar baseline y tablero corto.
2. F01: fixture A pedido/B aceptado, ejecutar coste/cierre y comprobar producto efectivo. Revisar `plataforma/api/cesta.py:coste_por_linea`, `tests/test_g03_cierre.py` y persistencia del cierre.
3. F02: servidor registra y respuesta se pierde; re-submit manual con UUID nuevo. Corregir operación pendiente si la reproducción confirma duplicado.
4. F03/F04: integridad de versión/privacidad antes de nuevas funciones dependientes.
5. F05/F06 en incrementos, alternando con F07–F14 para que los datos no paralicen las pantallas ni la UI esconda problemas del motor.

Comandos habituales desde raíz: `uv run pytest -q`, `uv run ruff check .`. En frontend: `npm run tipos`, `npm run build`, `npm run test:cocina`; añadir/documentar un comando que ejecute **todos** los tests del cliente, no asumir que cocina ya los recoge. Ensayos de `plataforma/prueba_*.py` después de leer efectos y configurar entorno aislado.

Cada entrega de investigación enlaza fuente/evidencia→decisión→implementación→aceptación. Cada pausa deja siguiente acción exacta. No parar tras F00 ni transformar esta fase en otra serie de informes sin producto.
