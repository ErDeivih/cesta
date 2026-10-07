# Datos completos, cobertura Lidl y comparación exacta

Fecha de investigación: 7 de octubre de 2026. Este es un contrato de implementación;
no afirma que se hayan recorrido ya todos los productos ni todas las fuentes.

## 1. Dos inventarios, no una tabla que confunda todo

**Inventario de artículos:** unión de productos pertinentes conocidos de todas las
capturas, categorías, sitemaps y fichas, con primera/última observación y versiones.
No se pierde un producto por no aparecer hoy. **Observaciones comerciales:** precio,
promoción y disponibilidad por artículo/cadena/tienda/canal/instante. Un artículo
sin observación comercial vigente puede existir en biblioteca y no ser elegible
para recomendar dónde comprar. Contar artículos, variantes y ofertas por separado.

Interpretación operativa de «todos»: cubrir todo el inventario descubierto dentro
del alcance con una primera visita, y revisitar las fichas con una política
observable. No descargar indefinidamente todas las fichas todos los días. Tampoco
inferir cobertura de tiendas físicas a partir del número de URLs de una web.

## 2. Estado actual comprobado en código

| Fuente | Evidencia local | Siguiente trabajo |
|---|---|---|
| Mercadona | `ficha`, `_maestro_de_ficha`, maestro gzip; bucle salta IDs existentes | renovar conocidas, conservar versión/fecha y auditar todos los campos de respuesta |
| DIA | maestro y ficha individual; bucle `if sku in maestro: continue` | misma renovación; separar país/fabricante y etiquetas/alérgenos |
| Alcampo | descubrimiento categorías/búsqueda y parser de listado | inventario de fichas públicas y extracción de detalle por producto; no suponer que listado es ficha completa |
| Carrefour | listado con objetos de producto; auditoría textual sobre HTML exageraba campos | extraer detalle real con fixtures por producto y medir campo/base, no palabra en documento |
| Aldi | HTML/sitemap y `shortDescription` estructurada parcialmente | descubrir detalle y base nutricional si publicados; no depender de textos de categoría inexistentes en sitemap |
| Lidl | `collectors/lidl.py` usa solo URL semanal | añadir inventario multifuente y fichas; ofertas como segunda corriente |

Antes de cambiar parser, guardar muestra de respuesta y verificar asociación a ID.
No asignar una tabla de nutrición de un producto relacionado al producto principal.
Preservar campos originales, incluso si todavía no se normalizan.

## 3. Cola de enriquecimiento y renovación

Crear registro por `(fuente,id_fuente,variante,ambito)` con URL canónica,
`discovered_at`, `last_seen_at`, `detail_fetched_at`, `detail_checked_at`,
`next_check_at`, hash del contenido útil, versión de parser, intentos, resultado,
ETag/Last-Modified si existen y referencia al crudo. No guardar cookies o secretos
en evidencia de producto. Canonicalización no elimina la variante o ámbito.

Estados: pendiente, en_curso(con lease), correcto, parcial, no_publicado,
bloqueado, error_temporal, no_encontrado, excluido. Un 404 aislado no retira
automáticamente un artículo ni borra histórico. Separar fallo de red y fallo de parser.

Orden inicial: reprocesado local > artículo sin ficha > conflicto de identidad >
ficha caducada > revisión ordinaria. Reservar capacidad a todas las cadenas y a
las fichas antiguas para que no haya inanición. Política inicial configurable:
revisar detalles a los 30 días y a los 7 días cuando haya conflicto/cambio observado;
precios según ejecución diaria actual. Estos intervalos son defaults de trabajo,
no garantías de fuente. Priorizar favoritos no debe impedir recorrer el resto.

Presupuesto por host y por día; conservar ritmos existentes hasta medir. Una sola
petición simultánea por host inicialmente; respetar Retry-After y robots vigentes.
Reintentos acotados con backoff; 403/retos repetidos detienen esa fuente y conservan
progreso. No CAPTCHA automático, rotación para evadir límites ni APIs autenticadas
sin permiso. Lock de ejecución y checkpoints; lease caducado se recupera.
Reprocesar con versión nueva del parser sin red. Descargas condicionales si soportadas.

Estimación de primera pasada: `pendientes / fichas_correctas_diarias_observadas`;
publicar intervalo y errores, no prometer acabar mañana sin medir rendimiento.
Las fichas históricas se interpretan con su fecha; no sobrescribir ingredientes
de septiembre con la formulación de octubre como si siempre hubiera sido igual.

## 4. Contrato de ficha

Identificación: fuente/ID/URL, GTIN observado y validación, marca, fabricante,
nombre comercial/legal, categoría y atributos de variante.
Presentación: unidades de pack, contenido individual/total, peso neto/escurrido,
unidad, venta al peso, estado físico y envase. Separar 6×1L de1L.
Alimentación: texto íntegro de ingredientes, lista analizada adicional, alérgenos
declarados y trazas por separado; nutrición por100g/100ml/porción, tamaño de porción,
energía kcal/kJ, grasas/saturadas, hidratos/azúcares, fibra, proteína, sal y otros
nutrientes si están publicados, con sus unidades. No deducir «sin» de ausencia.
Otros: origen del producto, conservación, preparación, advertencias, alcohol,
material/dimensiones/capacidad/cuidados para reutilizables. Nutrición en bayeta
es no_aplicable, no dato faltante.

Cada campo normalizado lleva valor, unidad/base, fuente, fecha, ruta de extracción,
parser y estado. Mantener `specifications_raw` para lo todavía desconocido con
límites de tamaño y sanitización; no perderlo por encajarlo en un esquema corto.
Separar país de fabricación, país de ingredientes, domicilio y fabricante.
Un valor «<0,5g» es censurado, no0,5 exacto ni cero; almacenar operador y límite.
OCR de etiqueta solo como candidato con imagen/revisión, no verdad automática.
Descripción similar, fotografía o tabla nutricional iguales apoyan matching pero
no prueban identidad comercial. No copiar nutrientes entre marcas equivalentes.

## 5. Lidl: hallazgos nuevos y estrategia concreta

Fuentes observadas por GET público el 7/10 (comprobar de nuevo al ejecutar):

- `https://www.lidl.es/robots.txt` anuncia `https://www.lidl.es/static/sitemap.xml`.
- El índice responde 200 y remite a productos, páginas y tiendas.
- `https://www.lidl.es/p/export/ES/es/product_sitemap.xml.gz`: **6.622 URLs**.
  Prefijos de ID observados:100=5.946,110=307,111=298; resto71. **Los prefijos
  NO son un clasificador de alimentación**. No convertirlos en regla permanente.
- `https://www.lidl.es/explore/assets/s/pages_es-ES_es.xml.gz`: **1.071 URLs**;
  mezcla categorías, contenidos editoriales y rutas antiguas.
- Buscar leche/queso/etc. en URLs da falsos positivos: espumadores de leche,
  tablas de quesos y prensas de galletas. No afirmar 82 alimentos por 82 coincidencias.
- Ficha `https://www.lidl.es/p/sondey-galletas-rellenas/p11000174`: marca,
  título, descripción e imágenes; sin precio visible en la lectura realizada.
- `https://www.lidl.es/h/lacteos-quesos-y-huevos/h10095761` figuraba en sitemap
  pero respondió 404. Un sitemap no garantiza página viva ni producto disponible.
- `https://www.lidl.es/c/alimentacion/s10068374` mostraba mensaje sin ofertas,
  por lo que tampoco es prueba de catálogo vacío.
- El colector semanal anterior obtuvo 76 variantes el6/10; no se ha repetido
  aquí una captura completa ni sumado esos 76 a los 6.622 como si fueran disjuntos.

Implementar dos caminos que confluyen por ID/variante:

1. **Descubrimiento y detalle**: sitemap de productos + categorías públicas vivas
   + enlaces de fichas encontrados. Normalizar URLs; clasificar con breadcrumb y
   ficha, rechazar bazar inequívoco antes de gastar detalle cuando sea posible;
   ambiguos a revisión, no excluir alimentos por slug. Registrar cobertura por fuente.
2. **Ofertas**: semanales y otras páginas públicas pertinentes, con normal/club,
   fechas, formato y región. Conservar ambas ofertas simultáneas, no escoger club
   como precio universal. Vincular a inventario, no fabricar GTIN a partir de IAN.

En robots observado se excluyen entre otras rutas `search?q=`, `?offset=`,
`productsOnly=` e `idsOnly=`. No resolver paginación saltándose esas exclusiones.
Si una ruta no permite acceso automatizado, buscar fuente autorizada; guardar
limitación y continuar. Robots no equivale a licencia de republicación.

Piloto siguiente: inspección estratificada de 50 fichas (alimentos frescos,
envasados, droguería, mascotas, reutilizables y bazar negativo), crudo+fixture;
después recorrer todo el inventario pertinente por cola. Medir 90/95/100 % de
URLs descubiertas procesadas **no** como porcentaje del surtido físico.
Informe diario: descubiertos, incluidos, excluidos, ambiguos, visitados, vivos,
con GTIN válido, con nutrición/base, con precio vigente y errores por región.

Cierre de S03: fuentes públicas pertinentes inventariadas, cola recorrida o
limitaciones documentadas, varias ejecuciones incluida transición semanal,
integración de artículos sin precio y ofertas con condiciones, pruebas de deriva,
sin pérdidas de histórico. No exigir 2.536 filas porque Aldi tuviera esa cantidad.
Para declarar «surtido completo» hace falta denominador fiable de la fuente;
si no existe, decir «catálogo público descubierto», con cobertura desconocida.

## 6. Identidad: algoritmo automático con abstención

Modelo lógico: producto_fuente_version → artículo_comercial → familia; relación
alternativa aparte. Una oferta referencia producto/versión y ámbito. La entidad
artículo no debe confundirse con receta, ingrediente genérico o marca blanca.

Pipeline:

1. Normalizar GTIN como texto con ceros, longitudes y dígito de control; no IAN,
   ni códigos internos de peso variable entre cadenas. Conservar observado.
2. Normalizar marca con alias versionados, cantidades y pack; extraer atributos
   por familia. «Sin lactosa», corte, especie, sabor, etapa infantil, concentración
   o dosis no son stopwords. No descartar negaciones.
3. Generar candidatos por GTIN y bloques marca+familia+formato; búsqueda léxica
   para recall. Evitar O(N²). Embeddings locales opcionales solo si mejoran banco.
4. Reglas duras: contradicción de variante/contenido/pack/formulación impide
   identidad. GTIN igual incompatible se pone en cuarentena. GTIN distintos
   no se fusionan por texto: excepción solo con evidencia de equivalencia comercial.
5. GTIN válido coherente → candidato fuerte con evidencia. Sin GTIN, marca,
   nombre y atributos compatibles → probable, no «exacto» por umbral arbitrario.
   Entrenar modelo interpretable (p. ej. logística) cuando exista banco fiable;
   calibrar en validación independiente y versionar umbrales.
6. Unión de grupos exige compatibilidad con todos los miembros/atributos canónicos;
   no cierre transitivo de similitud. Split/merge conserva eventos y referencias de
   listas; IDs estables no ligados a orden de filas.

Ingredientes/nutrición son señales complementarias. Coincidencia no implica mismo
fabricante ni producto; diferencias pueden indicar reformulación, fuente vieja o
error. Separar versión temporal en vez de sobrescribir o unir silenciosamente.
En granel, fruta/carne/pescado sin identificador común: comparar **especificación
equivalente**, no prometer artículo idéntico. Etiqueta y modo separados en UI.

Banco inicial propuesto: al menos 1.000 pares, estratificado en seis cadenas,
familias y dificultades; aumentar donde haya errores. Positivos con evidencia,
negativos difíciles (pack, sabor, crudo/cocido, 500/450g, corte), desconocidos.
No entrenar y evaluar con duplicados del mismo artículo/GTIN ni con etiquetas
generadas por la propia regla que se evalúa. LLM puede proponer, no ser juez único.
Reportar precisión/recall/abstención, intervalos y tamaño por familia. Objetivo de
precisión exacta≥99,5 % en muestra independiente como puerta de ingeniería;
no afirmar 99,5 % poblacional sin incertidumbre y muestreo adecuados.
Muestrear también pares que el blocking excluyó para medir recall real.
Revisión automática prioriza conflictos; el usuario solo decide política o casos
no resolubles, no tiene que emparejar uno a uno todo el catálogo.

## 7. Ofertas y publicación

Servicio único: identidad aceptada → tienda/canal → ventana de captura y vigencia
→ disponibilidad → condiciones de usuario → coste por cantidad comprable.
`_candidatos` actualmente recibe `fecha_tope` sin aplicarla: arreglar el contrato y
todos sus llamantes, que hoy pasan cadena vacía. Probar fecha antigua, futura y límite.
Precio sin stock conocido se muestra con incertidumbre; no se promete existencia.
Promoción exige condiciones trazables: descuento directo, multicompras, segunda
unidad, cupón activado, saldo diferido y club no son equivalentes.
Elegir por coste de la cantidad solicitada, no primero por precio unitario más bajo.

Snapshots inmutables y publicación conjunta de catálogo, identidades y ofertas.
Readers fijan una versión por petición; migrar sin romper listas antiguas, con
fallback conservador al producto elegido. Una fuente incompleta no reemplaza
la última captura completa como si estuvieran retirados los ausentes.

## 8. Material de aprendizaje y operación

Crear capítulo por etapa con un ejemplo ejecutable mínimo: crudo, campos y sus
rutas, unidades, bronze, transformaciones silver, histórico gold, identidad,
consulta y visual. Explicar hashing, caché, TTL, idempotencia, backoff, GTIN,
blocking, precisión/recall, calibración y datos ausentes. Mostrar errores reales
del proyecto y su prueba, no una explicación genérica de herramientas no usadas.
Panel de calidad separado de consumo: cobertura por campo/cadena, edad de fichas,
deuda de cola, fallos de parser, identidad desconocida y versiones publicadas.
Preservar crudo para reproducir sin red; política de retención y tamaño medidos.
