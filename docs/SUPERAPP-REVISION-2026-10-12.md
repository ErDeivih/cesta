# Revisión independiente de Cesta — 12 de octubre de 2026

## Dictamen

Hay una base funcional considerable y pruebas que detectan muchos errores reales.
La aplicación sirve para pruebas locales supervisadas, pero NO está acreditada como
comparador fiable de artículos idénticos ni como servicio público listo para desplegar.
No quedan solamente cinco decisiones del propietario. Hay fallos técnicos, cobertura
insuficiente y recorridos que todavía necesitan medición.

Esta revisión contrasta el traspaso de DeepSeek con código, pruebas ejecutadas,
API servida, ficheros locales, tarea de Windows y navegador. No acredita todos los
recorridos autenticados de Compra, Recetas y Calorías: no se han creado cuentas en
producción ni se ha alterado el historial real para simularlos.

## Evidencia reproducida, no heredada

- HEAD inicial: `3cf7bb9`. El traspaso adjunto se leyó junto con el documento del 12.
- Antes de cambios: Python **1.842 passed, 5 xfailed**, 198,71 s; cliente **46 passed**;
  ruff limpio y build correcto. Un xfail es un defecto pendiente, no una funcionalidad terminada.
- Después de las primeras correcciones: Python **1.853 passed, 1 xfailed**, 194 s.
  Se añadió después otra regresión del ejecutor; sus ocho pruebas de revisión pasan.
  Última ejecución integral, con las correcciones finales: **1.854 passed, 1 xfailed**,
  232,05 s; cliente **46 passed**, tsc/build correctos y ruff limpio.
- Las pruebas PostgreSQL se ejecutan contra el entorno de ensayo en `127.0.0.1:5434`.
  No se migró producción ni se tocó la base ajena del puerto 5433.
- Docker estaba funcionando: web en 8080, API y base de Cesta activas. El bloqueo
  por Docker apagado de rondas anteriores NO describe esta revisión.
- Navegador: búsqueda pública y navegación a `/compra/comparar/11627`.
  La búsqueda muestra resultados; la ficha permaneció en carga durante observaciones iniciales. La API de esa ficha
  respondió por separado, así que no se ha demostrado que su causa sea un backend caído.
  Tras el último build la ficha terminó cargando: se verificaron visualmente cabecera
  legible, advertencia de catálogo incoherente, «no lo sé» como ganadora y **0 de 5**
  candidatos que deciden. No se acreditó el instante exacto de disparo del timeout.

## 1. Ingesta: sí se ejecutó hoy, pero se interrumpió

El traspaso afirma «hoy no hubo ingesta» mirando `data/master`. Eso no es correcto:
master es el almacén de detalles; no sustituye la evidencia de bronze ni el registro.

Bronze contiene particiones del **12/10/2026**:

| Cadena | Hora de escritura de `part.parquet` |
| --- | --- |
| Aldi | 12:26:34 |
| Mercadona | 12:26:55 |
| DIA | 12:37:18 |

Alcampo y Carrefour mantienen bronze del 11. El registro de hoy termina con `^C`,
después de retos WAF de Alcampo y rescate de categorías de Carrefour. Eso prueba
interrupción, no que el WAF haya quedado resuelto definitivamente ni que la pasada acabara.

`Cesta diaria`: última ejecución 12/10 a las 12:24:20; resultado **3221225786**;
próxima 13/10 a las 06:00. El marcador `data/ultima_ejecucion.txt` continúa en **2026-10-11**.
No se lanzó otra captura larga ni se cambiaron sus horarios durante la revisión.

### Catálogo servido: incoherencia confirmada

`GET /api/estado` devuelve `version_catalogo=20261007-103000`,
`fecha_datos=2026-10-11` y `vigencia_precio.coherente=false`.
El puntero `data/gold/actual.json` dice publicación del 7; sus seis Parquet tienen
escrituras del 11. No es correcto describirlo como snapshot del 7 intacto sin matiz.

`fsutil hardlink list` confirma que `precio_diario.parquet` del gold suelto,
`v20261007-103000` y `v20261011-124542` comparten fichero físico. Esto NO demuestra,
por sí solo, cuándo se alteró: una adopción retrofechada o una escritura in situ son
hipótesis a investigar. Sí demuestra que no son tres copias independientes.

No se movió el puntero para esconder el problema. Antes de recuperarlo hay que
verificar las seis piezas, su fecha, esquema, enlaces y derivados, y publicar una
versión nueva coherente. No se refecha ni se reconstruye el pasado con precios actuales.

## 2. Comparación exacta: el problema central sigue siendo visible

La API del grupo **11627** devuelve estos miembros:

| Cadena | Producto / marca | EAN publicado |
| --- | --- | --- |
| Aldi | Leche entera / Milsani | desconocido |
| Carrefour | Leche entera Président brik 1 l | 8410285127613 |
| Alcampo | Central Lechera Asturiana botella 1 l | desconocido |
| DIA | Leche entera Asturiana 1 l | 8410297112041 |
| Mercadona | Leche entera Asturiana | 8410297112010 |

Esto puede ser una familia o un conjunto de alternativas. NO es el mismo artículo
de marca y presentación acreditado en cinco tiendas. El tooltip del buscador sí
afirmaba «el mismo producto». Se ha corregido esa afirmación y la de los ejemplos.
No se han partido todos los grupos automáticamente ni se ha cambiado la identidad
de listas existentes: eso exige migración y evaluación del motor.

El ahorro por unidad dentro de una familia no acredita ahorro al recomprar un
artículo concreto. Elegir Milsani no autoriza sustituirla por Président. EAN distinto
tampoco prueba necesariamente distinta receta: puede representar otro envase o pack;
por defecto impide afirmar identidad exacta sin evidencia adicional.

Otros riesgos localizados en `paginas/Grupo.tsx`: fecha ausente admite decidir;
la antigüedad se calcula respecto del día del catálogo y no siempre del día de uso.
Si el catálogo deja de actualizarse, ese cálculo puede seguir considerándolo fresco.
La revisión añade bloqueo de recomendación en la ficha cuando la API declara
incoherencia de publicación; NO equivale a corregir la política completa del motor.

## 3. Cobertura real de detalles y nutrición

Consulta DuckDB sobre `v20261007-103000/grupos.parquet`, la versión del puntero:

| Cadena | Filas de catálogo | Con kcal_100g | Con ingredientes no vacíos | Con descripción |
| --- | ---: | ---: | ---: | ---: |
| Alcampo | 23.128 | 0 | 0 | 0 |
| Aldi | 2.768 | 0 | 0 | 1.612 |
| Carrefour | 16.195 | 6.512 | 0 | 0 |
| DIA | 5.783 | 2.826 | 4.394 | 0 |
| Mercadona | 4.213 | 1.900 | 2.752 | 4.213 |

Son recuentos de presencia, NO garantías de exactitud, actualidad ni origen.
Parte de las kcal llega enriquecida: `nutricion` nativa es NULL en cadenas que sí
tienen `kcal_100g`. Hay que medir ambos caminos por separado. El denominador de
esta tabla incluye productos no alimentarios; no debe presentarse como porcentaje
de alimentos sin nutrición sin calcular antes ese universo.

Calorías no puede tratar esos huecos como cero; una receta no debe inferir alérgenos
ausentes. Se necesitan procedencia, fecha de ficha, base 100 g/100 ml/ración,
preparado frente a vendido, y distinción «no publicado / no capturado / error».

Hay material educativo en `docs/aprende`, incluido extracción, ingeniería de datos,
unidades e identidad. Debe completarse con ejemplos reales de estas carencias, no
con una descripción ideal que afirme cobertura conseguida.

## 4. Lidl no está completo ni publicado

No hay partición `data/bronze/fuente=lidl` ni fila de Lidl en el catálogo servido.
Sí existen sitemap, HTML de fichas, descubrimiento y cola. Tener esos componentes
NO demuestra un catálogo diario disponible para comparar.

`collectors/lidl.py` publica **ofertas_semanales_parcial**, no surtido completo;
su `main(argv)` exige `--html` o `--web`, y exige región explícita para escribir.
El ejecutor general incluye Lidl en `ORDEN`, pero `_una_cadena` llama `main()` sin
adaptar esa CLI. Un `SystemExit` de argparse escapaba del manejo de excepciones:
podía impedir terminar el ciclo de las otras cadenas. Se ha aislado ese fallo.
Esto NO conecta ni completa Lidl: falta un adaptador regional, fuente/cobertura
explícita, catálogo versus campañas y publicación con datos reales verificados.

Además `plataforma/api/cesta.py::CADENAS` todavía enumera cinco cadenas. Incluir
Lidl en extracción sin pasar por cálculo y cobertura tampoco completa la integración.
No se promete igualdad de número de productos con Aldi: debe medirse cobertura
respecto del universo realmente ofrecido por la fuente, no alcanzar una cifra artificial.

## 5. Correcciones hechas en esta revisión

1. Buscador: desempate final `grupo_id`; conserva los criterios principales de orden.
   Las dos pruebas xfail de orden son ahora pruebas normales sobre 30 grupos
   empatados controlados, sin depender de la ingesta del día.
2. API: `desplazamiento` llega desde `/api/buscar` hasta la consulta. Antes existía
   únicamente en `catalogo.buscar`; la ruta no lo recibía ni lo transmitía.
   Aún faltan controles y estado de página en el cliente.
3. Previa: g/kg y ml/l se suman; una unidad homogénea conserva su presentación;
   una mezcla compatible se muestra en la canónica. Masa, volumen y piezas NO se
   convierten entre sí. Se rechazan bool, NaN e infinito. Las dos xfail kg/g se eliminan.
4. Estado: productos distintos del último día de CADA cadena, no todas las filas
   del histórico. Las cifras anteriores de cientos de miles no eran surtido actual.
5. UI: no se afirma identidad exacta basándose solo en pertenecer a un grupo.
6. UI: cabecera `bg-papel` en lugar de fondo blanco fijo; el texto semántico oscuro
   sobre fondo blanco era prácticamente invisible con preferencias de tema oscuro.
7. Ficha: aviso de espera excesiva en vez de carga indefinida; ante publicación
   incoherente se muestra advertencia y sus candidatos no recomiendan tienda.
8. Ejecutor: `SystemExit` de un colector se registra como fallo de esa cadena,
   no termina el ciclo completo. No se captura KeyboardInterrupt como si fuera éxito.

Cambios de backend probados en el árbol local; no se reconstruyó la imagen de API.
El frontend sí se compiló en el directorio que Caddy monta. No confundir build
correcto con todos los recorridos de usuario verificados en navegador.

## 6. No son cinco decisiones que justifiquen parar todo

| Pregunta de DeepSeek | Criterio de continuación |
| --- | --- |
| Presupuesto | Separar «estimación», «pagado» y «límite que fijaste». Implementar límite opcional; no rebautizar los otros dos. |
| Viajes | Mostrar número de tiendas; coste opcional introducido por la persona, desconocido si falta. No deducir euros sin distancia, medio y tarifa. |
| g/kg | Resuelto aquí: base común interna y presentación original homogénea. No necesita migrar el histórico. |
| Orden del buscador | Resuelto aquí: desempate estable; el orden entre empates era indefinido, no una preferencia del usuario. |
| Importar recetas | `FUENTES={}` deshabilita la importación URL real. Mantenerlo así hasta revisar fuentes permitidas; avanzar con entrada manual/JSON autorizado y preview sin inventar licencia. |

## 7. Continuación para DeepSeek, ordenada y con puertas

**Objetivo:** terminar una suite local usable de Compra, Recetas y Calorías,
con datos trazables y comparaciones exactas cuando la persona elige un artículo;
alternativas solo por consentimiento. No desplegar públicamente ni convertir
las pruebas verdes en sustituto de los recorridos reales.

### A01 — Recuperar publicación y evitar repetición (P1)

Investigar la versión del 7 con datos del 11, enlaces duros y escrituras/adopciones.
Contrastar `core/publicacion.py`, escritores, `version_vigente` y ensayos que fijan
fechas o presuponen un nombre de versión real. Trabajar en sandbox antes de recuperar.
Guardar evidencia y hashes; crear un snapshot coherente nuevo, no alterar anteriores.
Aceptar solo si datos, promociones, grupos, enlaces y estado responden desde la misma
versión durante una publicación concurrente. Un fallo debe conservar el último válido.

### A02 — Identidad y recomendaciones (P1)

Separar artículo exacto, familia y alternativa en respuestas y UI. Auditar los
seleccionadores de coste existentes, no sustituirlos por similitud de nombres.
Banco determinista con marca distinta, EAN distinto, mismo EAN con formato contradictorio,
pack, variedad, sin lactosa, peso variable, falta de EAN y desconocidos.
Aceptar: elegir artículo no produce sustituciones; confirmar/revocar solo modifica
la línea elegida; familia permite comparar por unidad pero se nombra como familia.
Contrastar las versiones del motor en sombra antes de migrar listas.

### A03 — Frescura por producto y ofertas de la misma captura (P1)

No inferir fecha de una ficha por el máximo de toda la cadena. Revisar Grupo,
`cesta._candidatos`, `_promos_vigentes` y lectores de silver sin pin de publicación.
Precios sin fecha, futuros, expirados o de versión incoherente no recomiendan tienda;
se conservan visibles como datos históricos. Reloj controlado en pruebas.
Aceptar: dejar de ingerir cuatro días elimina recomendaciones vigentes sin borrar datos.

### A04 — Concurrencia de cantidades (P1)

La xfail restante de `test_fase2_f07_dos_sesiones.py` prueba pérdida de actualización:
una edición antigua que llega tarde pisa una nueva. Diseñar revisión por línea o
conflicto explícito; no confiar ciegamente en reloj cliente para ordenar todas las mutaciones.
Migración aditiva con datos históricos conservados y pruebas HTTP de ambos órdenes,
reintento y dos usuarios. Aceptar antes de quitar la xfail.

### A05 — Lidl de punta a punta (P1/P2)

Adaptador del ejecutor con argumentos explícitos, región configurada y errores aislados.
Conectar descubrimiento/fichas/precios/publicación y consultas; mantener cobertura
parcial visible donde proceda. No resolver restricciones de fuente con evasión.
Pruebas offline de catálogo controlado, robots, región, club, fechas y fuente vacía;
después captura acotada y medida. No activar una captura masiva para aparentar avance.

### A06 — Fichas y nutrición (P2)

Inventario por campo y cadena, universo de alimentos, fuente y fecha de captura.
Cola de nuevos/cambiados/caducados con presupuesto, hashes, reintentos y límites.
Priorizar Alcampo/Aldi y datos nativos de Carrefour por sus huecos medidos.
Aceptar: cada ausencia tiene estado; ingrediente/alérgeno desconocido no es negativo;
datos enriquecidos no se atribuyen al supermercado; macros y kcal conservan cobertura propia.

Ejemplo de procedencia que también debe llegar a pantalla: el Président de Carrefour
del grupo revisado tiene `calidad_origen=ingredientes_off`, nota 100 y letra A, aunque
su columna nativa `ingredientes` esté vacía. No prueba un parser erróneo: la valoración
es enriquecida desde Open Food Facts. La API del grupo no expone ese origen y el
sello solo dice «leída de ingredientes»; debe distinguir dato nativo y enriquecido.

### A07 — Paginación usable y espera recuperable (P2)

Agregar página/offset en URL, hook y botones, reiniciar al cambiar filtros; no
ordenar solo la página como si fuera el catálogo entero. Fijar versión o cursor
para no duplicar filas cuando cambia el catálogo entre páginas.
Ensayos DOM de respuesta retenida, error, cancelación y llegada tardía; las pruebas
de la función pura `estaAtascada` no prueban por sí solas el hook React.

### A08 — Recetas, compra y envases (P2)

Resolver `_tamano_del_envase`: hoy espera dict/objeto con cantidad, pero `envases.lee`
devuelve tupla de tipo de envase y tamaño de pack; no está calculando peso del envase.
Usar tamaño neto publicado del artículo elegido y convertir dimensiones compatibles.
Aceptar: 1,4 kg / envase 1 kg = dos envases y 0,6 kg sobrante; ausencia de tamaño
produce desconocido, no una compra fraccionaria inventada. Preview, idempotencia y
despensa conservan permisos y no registran consumo por comprar.

### A09 — Recorridos reales y puerta de publicación (P1/P2)

Entorno desechable con catálogo versionado controlado, usuarios A/B/hogar y nutrición
controlada. Compra: texto libre, exacto, alternativa, revocar, 3x2 dividido, cierre e
histórico persistido. Recetas: alta, edición, versión, cocina, despensa y transferencia.
Calorías: alta, recarga, nutrientes independientes, repetición legítima frente a retry,
aislamiento y subtotal parcial. Catálogo fijo primero; publicación durante uso después.
390/768/1440 px, tema claro/oscuro y zoom 200%; controles, textos y errores reales,
no solo conteo de píxeles. Guardar capturas y resultados con commit/imagen/versión.

### A10 — Preparación de despliegue y aprendizaje (P2)

Medir bundles y separar rutas: el JS actual ronda **692 kB / 208 kB gzip**, con warning.
Revalidar backups/restauración, migraciones, permisos, sesiones, límites de registro,
protección de mutaciones, logs sin secretos y exposición de puertos. El web actual
escucha `0.0.0.0:8080`; eso no prueba exposición a Internet, pero no es solo loopback.
No abrir servicios públicamente sin el encargo correspondiente.
Actualizar `docs/aprende` con trazabilidad, consulta de cobertura, transformaciones,
algoritmos y fallos reales, enlazados a código y ejemplos reproducibles.

## Disciplina para no perder otras ochenta rondas

- Un tablero corto: objetivo, paquete, evidencia nueva, pendiente y siguiente comando.
- Si falta una decisión aislada, seguir con el siguiente paquete independiente.
- Cerrar con criterio ejecutado, no por terminar Markdown o porque la suite permite xfail.
- No copiar cifras heredadas: publicar universo, fecha, versión y consulta.
- No tocar 5433, datos de casa, secretos ni cambios ajenos. No commitear
  `core/datos/secciones.yml`, `docs/CIFRAS.md` ni el goal de continuación existente.
- Escalar solo identidad/región/fuentes realmente desconocidas o acciones fuera del alcance;
  estabilidad de orden, conversiones compatibles y honestidad de etiquetas son trabajo técnico.

## Comandos de verificación de esta revisión

```powershell
$env:CESTA_POSTGRES='postgresql://cesta:prueba@127.0.0.1:5434/cesta'
uv run pytest -q
uv run ruff check .
# Desde plataforma/web/app:
npm test
npm run build
```

No ejecutar el ejemplo de PostgreSQL contra un servicio distinto sin comprobar antes
que corresponde al entorno de ensayo. No lanzar ingesta para sustituir auditoría de publicación.
