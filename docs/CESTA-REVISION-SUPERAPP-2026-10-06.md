# Revisión de la superapp y relevo para DeepSeek — 6 de octubre de 2026

Revisión iniciada el 6; cierre de verificaciones el 7 de octubre. Las cifras de
Lidl corresponden a la captura del 6, no a una segunda captura del día 7.

## Dictamen

**No está lista para un despliegue público.** Hay una base local útil, pero ni los
grupos actuales garantizan identidad exacta ni las nuevas pantallas de cocina
son un servicio persistente. Docker/API estaban inaccesibles durante esta
revisión: no se certifican autenticación, cesta y base de datos de extremo a
extremo. No se ha desplegado nada ni activado una nueva ingesta diaria.

Este documento complementa el muro, T02/T03/T11 y el traspaso; no declara esos
trabajos terminados. Se han respetado los cambios previos de secciones.yml y
CIFRAS.md. No regenerar cifras históricas para hacerlas coincidir con el código.

## Cambios implementados

- Lidl: lectura de precio numérico real y del envoltorio del precio club;
  fechas de vigencia, rechazo de negativos/no finitos, precio anterior,
  identificación de condición club cuando es el precio elegido, categoría y
  URL completas. Disponibilidad desconocida, no `true` inventado. Publicar
  exige región explícita y algún precio vigente. No se cuentan como peticiones
  ahorradas productos excluidos después de haber descargado su página.
- Prueba pública limitada de Lidl, respetando robots y sin publicar bronze:
  76 variantes, 70 productos padre, 74 precios regionales vigentes para región
  28. Las dos restantes no se convierten en productos gratis. Es una observación
  del día, no garantía de funcionamiento perpetuo ni catálogo completo.
- Añadir desde la ficha conserva `producto_id=fuente:id`, aunque exista grupo;
  ya no transforma esa elección en una autorización para sustituirla. Esto NO
  arregla todavía el emparejador, la pantalla de grupos ni todos los consumidores.
  Al cambiar de producto se reinicia el estado del botón: no hereda «En la cesta»
  del artículo anterior.
- Alcance v3 admite reutilizables domésticos seleccionados: fiambreras, vasos,
  botellas/bolsas reutilizables y recipientes. No reabre televisores ni todo el
  bazar. Un filtro de categoría anterior a la descarga puede seguir ocultándolos:
  hay que revisar rutas de descubrimiento, no prometer que ya se capturan.
- DIA conserva tablas nutricionales parciales en lugar de tirarlas si no tienen
  proteína/energía. Rechaza nutrientes negativos y no finitos; cero sigue siendo
  cero, ausencia sigue siendo ausencia. No se convierten bases desconocidas.
- Matriz de fichas: se retira la afirmación de «publicado y no extraído» basada
  únicamente en palabras dentro de HTML/JSON. Es una pista textual, con falsos
  positivos y negativos, no una prueba por producto ni una cota inferior.
- Rutas `/recetas` y `/calorias`: ingredientes manuales, cantidades, bases
  100 g/100 ml, raciones, calorías y macronutrientes con avisos de incompletitud;
  importar/exportar receta, descargar ingredientes, anotar comidas por fecha,
  deshacer y exportar diario. Una comida guarda el resultado de ese momento.
  **Estado solo en memoria de la pestaña**, con aviso visible: recargar lo pierde.
  No hay aún guardado por usuario, catálogo nutricional conectado, biblioteca de
  múltiples recetas ni incorporación automática a la cesta. No venderlo como
  funcionalidades completas; es una base comprobable para integrarlas.

## Evidencias que corrigen el último informe

1. Las pruebas sintéticas de Lidl no reproducían la forma del precio general
   real. La captura sí: intentar `.get()` sobre un número fallaba. Hay regresiones
   nuevas para esa forma y para vigencia/club/ausencias.
2. En una inspección de las primeras 40 respuestas ordenadas de Carrefour de
   2026-10-06, el parser devolvió 771 observaciones de producto. Sus objetos de
   listado no contenían campos de peso, origen o nutrición. Buscar «weight» en
   el documento entero no demuestra que se tenga ese dato de cada producto.
   Esta muestra tampoco demuestra que las fichas individuales no lo publiquen.
3. El manifiesto actual identifica y resume ficheros; escribir atómicamente ese
   JSON no publica atómicamente el conjunto de Parquet. T02 debe cerrarse con
   versiones inmutables y un puntero de publicación, no solo hashes.
4. Revisar `_candidatos` y todos sus consumidores: recibir una fecha de corte
   sin aplicarla no evita elegir precios antiguos. Es un pendiente del selector
   único, no resuelto por cambiar el botón de añadir.

## Siguiente secuencia de implementación

### Sobre el tamaño del catálogo

23.019 filas de Alcampo frente a 4.320 de Mercadona no demuestran por sí solas
sobrecaptura: marcas, formatos, variantes y cobertura son diferentes. Tampoco el
0,4 % de excluidos demuestra que el recorte sea suficiente si clasificador y
evaluador comparten las mismas reglas. Auditar muestras independientes por
familia/cadena, con falsos incluidos y alimentos excluidos; separar variantes,
duplicados y ofertas del recuento de artículos. Con reutilizables v3 cambia el
contrato: conservar métricas v2 y recalcular v3 sin comparar porcentajes como
si tuvieran el mismo alcance. No imponer un máximo arbitrario de productos.

### 1. Cerrar T02: trazabilidad y publicación

Crear `run_id` y directorio inmutable por ejecución. Cada observación lleva
fuente, tienda/región, URL, captura, vigencia comercial y versión de parser.
Construir y validar todos los artefactos en staging; publicar solo después,
cambiando un puntero pequeño de manera atómica. Lectores fijan una versión por
consulta. Mantener última versión válida y estado parcial por cadena.

Aceptación: fallo provocado entre dos escrituras no mezcla versiones; rollback
recupera el conjunto anterior; dos ejecuciones simultáneas no pisan publicación;
la UI enseña fecha real de cada oferta, no la del último pipeline global.

### 2. T03 y T05: identidad y oferta elegible

Separar tres relaciones: artículo exacto, familia de búsqueda y alternativa.
Generar candidatos por EAN validado y por marca/familia; normalizar unidades,
número de unidades y contenido total, sin borrar variante. Bloqueos explícitos
para sabor, sin lactosa, entero/desnatado, fresco/congelado, corte, especie,
pack/unidad y otras propiedades pertinentes según familia.

EAN distinto es conflicto a investigar, no prueba universal de diferencia ni
permiso para unir. EAN igual con formato incompatible también requiere revisión.
Similitud textual o embeddings proponen candidatos, no certifican identidad.
Usar reglas conservadoras y un clasificador calibrado sobre pares etiquetados;
registrar motivos y abstenerse cuando falte información. Evitar cierre transitivo
ingenuo: A parecido a B y B parecido a C no prueban A=C.

El selector común filtra tienda, fecha, disponibilidad conocida, precio y
condiciones club/cantidad antes de optimizar. Nunca sustituye un artículo
concreto por una alternativa sin consentimiento. Explicar cantidades y coste
total de packs; no recomendar una unidad imposible de comprar por separado.

Aceptación: banco versionado de pares positivos y negativos difíciles, con
separación entrenamiento/evaluación por familias o marcas; medir precisión,
recobrado, falsos positivos y abstenciones por familia. El pequeño banco de
alcance NO valida identidad. Añadir pruebas API/UI de producto sin grupo,
grupo impuro, oferta caducada, club no activado y comparación de packs.

### 3. T11: ficha completa incremental, sin descargar todo a diario

Inventariar campos por objeto de producto real: EAN, marca, variante, contenido,
pack, ingredientes, alérgenos, trazas, nutrición con base y unidades, conservación,
preparación, país de origen, fabricante y especificaciones. Guardar procedencia
por campo y estado: extraído, ausente en respuesta, no aplicable, ambiguo o fallo.
No llamar origen al domicilio o al nombre del fabricante. No llamar alérgenos
a etiquetas comerciales como BIO.

Precio/disponibilidad se refrescan con mayor frecuencia; ficha estable se
enriquece por cola, caducidad de caché y cambios observados. Conservar crudo
reprocesable antes de nuevas peticiones. Presupuesto por cadena, reintentos
acotados y parada ante bloqueo; nunca eludir autenticación o retos humanos.
No garantizar disponibilidad mañana de datos que la fuente no publica.

Aceptación: fixtures reales anonimizados/minimizados, pruebas de parser por
campo y denominador producto, porcentaje con valor + base válida + procedencia;
reprocesar crudo demuestra mejora antes de ampliar carga. Una tabla parcial
no se muestra como completa y un null jamás equivale a cero kcal.

### 4. Integrar recetas y diario de verdad

Guardar recetas, versiones de ingredientes, raciones y apuntes por usuario/hogar
en API autenticada. Migraciones, aislamiento entre cuentas, exportación y borrado.
Seleccionar producto exacto desde catálogo y fijar instantánea de sus nutrientes,
fuente y fecha; ediciones posteriores no reescriben comidas pasadas. Permitir
valores manuales identificados como tales cuando falten datos.

Añadir biblioteca, edición de ingredientes, instrucciones propias, planificación
semanal y compra de ingredientes mediante operación idempotente. Primero elegir
producto/alternativa, luego calcular envases necesarios y sobrantes. Una receta
genérica no identifica automáticamente la marca ni autoriza sustituciones por
alérgenos. No convertir g/ml/unidad sin equivalencia verificable, ni crudo/cocido
sin rendimiento declarado. Energía: cantidad/base × valor × raciones consumidas
/raciones receta. Comprar no equivale a comer.

Referencias de interacción, sin copiar activos ni recetas protegidas:
[Samsung Food](https://samsungfood.com/meal-planner/) conecta planificación y
compra; [MyFitnessPal](https://www.myfitnesspal.com/) usa diario de alimentación
y seguimiento nutricional. Adaptar esos recorridos a nuestros datos incompletos,
no importar afirmaciones nutricionales ni objetivos médicos.

Aceptación: receta con varias raciones, ingrediente sin kcal, cero real, misma
comida dos fechas, cambio posterior de receta, cuenta distinta, refresco y
restauración. Gráficas semanales con huecos explícitos y subtotales, no ceros
inventados; distinguir gasto observado, compra estimada y consumo registrado.

### 5. Lidl antes de activarlo cada día

Mantener cobertura `ofertas_semanales_parcial`. Probar región elegida por el
usuario, cambios de semana, precios futuros/caducados, club y precio normal
simultáneos, variantes sin EAN y fallos de red. Actualmente se selecciona una
oferta: falta almacenar varias ofertas normales/club con condiciones separadas.
No usar ausencias del folleto como retiradas de catálogo ni inferir stock.
Mostrar cobertura en búsqueda/comparación y ejecutar varios días con revisión
de anomalías antes de integrar la publicación diaria. Una captura de 76 ofertas
no permite afirmar «Lidl perfecto» ni cobertura equivalente a Mercadona.

### 6. Puerta de despliegue y usabilidad

Con Docker disponible, probar búsqueda → producto exacto → favorito → cesta →
comparación → comprado, con cuentas separadas y datos reales. Revisar móvil,
teclado, contraste, carga, errores y vacíos; no ocultar falta de backend.
Revisar TLS, cookie Secure en producción, registro habilitado explícitamente,
límites de intentos, autorización por objeto, secretos, dependencias y registros
sin datos sensibles. Ensayar backup/restauración y migraciones. Revisar permisos
de uso/publicación de cada fuente antes de abrirlo a terceros. No se certifica
cumplimiento legal en esta revisión.

El build avisa de un paquete JS mayor de 500 kB: separar rutas por carga diferida
es una mejora concreta, sin silenciar el aviso como sustituto de optimizar.

## Material didáctico que debe acompañar cada entrega

Ejemplo pequeño trazable: respuesta original → parser → bronze tipado → limpieza
silver → histórico gold → consulta → pantalla. Explicar Parquet como formato
columnar, no base transaccional; distinguir histórico de precios de una captura
completa de catálogo. Documentar fórmula, supuestos, unidades, pérdida de datos,
test de regresión y caso que falla. No atribuir a dbt/Dagster trabajo que no
ejecutan realmente en este repositorio.

Para matching: enseñar un positivo, un negativo parecido y una abstención;
para nutrición: 200 g a 350 kcal/100 g son 700 kcal en receta completa, 350 por
ración si salen dos. Sin proteína declarada no se deducen cero proteínas.
Para ahorro: explicar tienda/región, vigencia, club, cantidad comprable y coste
de desplazamiento si se incorpora, separando estimaciones de hechos.

## Verificación reproducible

Resultado final del 7 de octubre: **1.195 pruebas Python pasan**, con dos avisos
de deprecación de Starlette/httpx/anyio; **6 pruebas de la lógica web pasan**;
`uv run ruff check .` limpio y build web correcto. El aviso de tamaño de JS sigue
abierto. `git diff --check` de los cambios propios limpio; los avisos de espacios
en secciones.yml y CIFRAS.md eran de cambios previos y no se han reescrito.

Se actualizaron dos expectativas de alcance por la nueva autorización de
reutilizables. La prueba estática de nombres de cadena confundía interpolación
de identificadores con texto visible; se corrigió ese falso positivo. No se
desactivó la batería ni se sustituyeron las comprobaciones funcionales.

Desde la raíz: `uv run pytest -q`. En `plataforma/web/app`: `npm run build` y
`npm run test:cocina` (requiere Node con soporte de TypeScript nativo, probado en
Node 24). Ruff sobre ficheros modificados. Pruebas visuales locales de recetas y
diario, incluida anchura móvil de 390 px; el backend no estaba disponible.
No confundir una compilación web correcta con un ensayo completo del servicio.
