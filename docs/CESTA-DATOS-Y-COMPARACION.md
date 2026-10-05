# Contrato de datos: consumibles, identidad exacta y ofertas

Estado: especificación de implementación, 5 de octubre de 2026.
Punto de entrada: [plan de implementación](CESTA-PLAN-DE-IMPLEMENTACION.md).

## 1. Alcance único del catálogo

Crear `core/alcance.py` y `core/datos/alcance.yml`, este último versionado e independiente
del mapa de secciones generado. Todos los colectores, reprocesadores y publicadores usan la
misma función `clasificar_alcance(producto, contexto) -> DecisionAlcance`.

Campos de salida: `estado` (incluido/excluido/revisar), `familia_id`, `motivo`,
`regla_id`, `version_politica` y evidencias de categoría/producto. Las reglas son explícitas
y deterministas. Una regla específica de producto prevalece sobre una categoría amplia.
No basta buscar «hogar», «natural» o «leche» como subcadenas del título.

| Incluir | Detalle y frontera |
|---|---|
| Frescos | Fruta, verdura, setas, huevos, carne, pescado, marisco; distinguir preparación y conservación |
| Despensa | Pan, galletas, cereales, pasta, arroz, legumbres, harinas, conservas, salsas, aceites, especias |
| Refrigerados y congelados | Lácteos, alternativas vegetales, embutidos, platos preparados, helados |
| Bebidas | Agua, café, té, zumos y refrescos; alcohol como categoría ocultable, sin mezclarlo con bebidas sin alcohol |
| Higiene | Gel, champú, higiene bucal, desodorante, compresas, tampones, papel higiénico, cosmética de reposición |
| Limpieza y lavado | Detergentes, lavavajillas, limpiadores, bolsas de basura, esponjas y recambios |
| Bebé | Alimentación, pañales, toallitas y consumibles de cuidado; excluir carritos, cunas y juguetes |
| Mascotas | Comida, arena y consumibles de higiene; excluir jaulas, camas y accesorios duraderos |
| Hogar consumible | Papel de cocina, servilletas, aluminio, film, bolsas alimentarias, pilas domésticas |

Excluir electrónica, televisores, electrodomésticos, herramientas, bricolaje, muebles,
decoración, textil, libros, papelería general, juguetes, deporte, automóvil y jardinería.
Para la primera versión excluir medicamentos y productos de finalidad médica cuya comparación
requiera reglas distintas; se conserva la higiene común. Un caso sin clasificación suficiente
va a revisión, no a una recomendación automática. Se puede recuperar desde una lista antigua.

### Aplicación a las cinco cadenas

- Mercadona: recorrer su surtido habitual; clasificar productos y no asumir que todo lo
  que publique cualquier día pertenece necesariamente al alcance.
- Carrefour: sitemap de supermercado, ramas permitidas y validación final de cada ficha.
  `supermercado` en la URL no garantiza que sea un consumible.
- DIA: categorías permitidas y filtro de producto; mantener alimentación animal y hogar.
- Alcampo: filtrar árbol, categorías hijas, términos de búsqueda y sus resultados. Aplicar
  otra vez la clasificación antes de bronze/publicación para evitar cruces de categorías.
- Aldi: separar surtido de consumo y bazar temporal; no consultar todos los detalles de bazar
  solo porque estén en el sitemap de productos.

Reducir solicitudes antes de descargar donde exista categoría fiable. Si la categoría solo
se conoce en el listado o ficha, guardar la respuesta y clasificar después. No ocultar el coste
de ese descubrimiento. Un producto excluido no dispara enriquecimiento ni matching.

### Frescura y cobertura

Priorizar categorías y productos presentes en listas/favoritos; recorrer después el resto del
alcance admitido. Si no existe endpoint de precios individuales, priorizar sus categorías.
Conservar descubrimiento periódico de nuevos productos dentro del alcance, sin quedar limitado
para siempre a los favoritos iniciales. El calendario tiene presupuesto por dominio, reanudación
y suspensión ante bloqueos persistentes; no multiplicar sesiones para forzar un recorrido.

La cobertura compara IDs únicos y familias canónicas dentro de la misma versión de alcance.
Medir cobertura de favoritos, cesta y catálogo familiar por separado. Una rama excluida nunca
veta una captura incluida. Una reorganización de nombres se investiga por IDs, no por conteos
de etiquetas únicamente. Desaparición no equivale a agotado; ausencia de captura no equivale
a desaparición. Conservar ambos estados.

Primer corte de alcance: clasificar anterior y nuevo con la misma política, obtener línea
base y motivos de cambios. Registrar diferencias; no compararlo directamente con el máximo
histórico de un surtido mayor. Capturas parciales pueden conservar observaciones válidas por
producto, pero nunca actualizar la fecha de productos arrastrados del día anterior.

## 2. Entidades y contratos

Identificadores estables opacos, no números derivados del orden del catálogo. Dinero en
céntimos enteros y moneda; cantidades y tasas con aritmética decimal. Fechas de captura UTC
y día comercial de la zona declarada. Los valores desconocidos son nulos.

| Entidad nueva | Campos mínimos y significado |
|---|---|
| `familia` | ID, nombre, sección, esquema de atributos y versión |
| `articulo_fuente` | ID interno, fuente, ID de origen, URL, nombre original, primera/última observación, alcance |
| `presentacion` | ID, marca canónica, gama, variante, atributos, contenido por envase, número de envases, cantidad total, unidad, peso neto/escurrido, tipo de envase |
| `identidad` | ID de artículo comercial exacto, presentación, estado confirmado/candidato/conflicto, evidencia, versión |
| `identidad_miembro` | Artículo de fuente, identidad, validez temporal, método y evidencia; sin adhesión automática por transitividad |
| `oferta_observada` | ID, artículo, identidad resuelta, tienda/zona/canal, capturado_en, precio público, precio anterior, disponibilidad, retirada, calidad de dato y ejecución |
| `promocion` | ID, texto original, tipo, vigencia, elegibilidad, base de cálculo, mínimos/máximos, acumulación, confianza |
| `observacion_ejecucion` | Fuente/alcance, peticiones, recibidos únicos, admitidos, rechazados, cobertura, publicación y motivo |

Cada atributo extraído lleva procedencia y evidencia (campo de la fuente o tramo de texto).
No convertir ingredientes, alérgenos o marcas ausentes en atributos heredados de otra marca.
Una equivalencia solo para búsqueda no autoriza copiar una ficha nutricional.

Se pueden materializar estas entidades en Parquet/DuckDB; PostgreSQL conserva estado personal
y referencias estables. No duplicar todo el histórico analítico en la base transaccional.

## 3. Identidad por familias, no una regla especial para leche

| Familia | Atributos que impiden una identidad exacta cuando difieren |
|---|---|
| Leche/lácteos | Marca/gama, especie o vegetal, grasa, lactosa, enriquecimiento, sabor, presentación |
| Galletas | Marca/gama, receta, sabor, relleno/cobertura, sin azúcar, gluten, gramos y multipack |
| Pan | Marca cuando existe, tipo, cereal, integral declarado, gluten, fresco/precocido/congelado, rebanado y peso |
| Carne | Especie, corte, con/sin hueso y piel, picada/preparada, fresca/congelada, certificación y unidad de venta |
| Pescado/marisco | Especie, entero/filete/lomo, limpio/sin limpiar, fresco/congelado, tamaño comercial cuando consta, peso neto/escurrido |
| Fruta/verdura | Especie/variedad, fresco/congelado/conserva, entero/cortado, ecológico, calibre/categoría declarados, granel/envasado |
| Conservas | Especie/ingrediente, medio de cobertura, receta, neto y escurrido, número de latas |
| Café/té | Marca/gama, variedad, molido/grano/soluble/cápsula, descafeinado, compatibilidad de cápsula y cantidad |
| Bebidas | Marca/gama, sabor, azúcar/edulcorante, alcohol, contenido y número de botellas/latas |
| Limpieza | Marca/gama, uso, formulación/concentración, dosis declaradas, recarga/envase y cantidad |
| Higiene | Marca/gama, uso/variante, talla o absorción cuando proceda, volumen/unidades y recambios |
| Bebé | Marca/gama, etapa/edad, talla de pañal, formulación y número de unidades |
| Mascotas | Marca/gama, especie/edad, seco/húmedo, receta, indicación dietética declarada y presentación |

Marca de distribuidor distinta implica sustitución, aunque el fabricante parezca el mismo.
No inferir identidad por compartir proveedor. Origen o calibre de frescos pueden variar por
lote: registrar atributo observado, con su validez temporal, y aplicar las restricciones del
comprador. Productos de granel sin marca no se anuncian como el mismo SKU: se comparan como
alternativas especificadas por especie, corte, preparación y calidad comercial declarada.

### Procedimiento de decisión

1. Normalizar GTIN sin fabricar dígitos: admitir las longitudes soportadas, validar dígito de
   control y conservar original. No usar `quitar todo salvo números` como validación suficiente.
2. Mismo GTIN válido es evidencia fuerte. Si contradice variante o presentación, marcar
   conflicto de fuente y bloquear la unión hasta revisión. Un pack y una unidad no se igualan
   por llevar publicado el código del envase individual.
3. GTIN distintos no se unen automáticamente. Un cambio de código requiere alias documentado
   con fechas/evidencia de fabricante o revisión humana; guardar quién y por qué lo confirmó.
4. Sin código suficiente, atributos y texto generan candidatos. Exigir marca, variante y
   presentación verificadas; un atributo esencial desconocido deja el caso pendiente.
5. Similitud textual o vectorial ordena la revisión; nunca convierte sola un candidato en
   identidad confirmada. El modo exacto usa solo miembros confirmados.
6. Las alternativas se calculan separadamente, con restricciones de familia y usuario. No
   unirlas mediante componentes conexas con identidades: A≈B y B≈C no demuestra A=C.

El filtro de precio no demuestra identidad. Puede detectar anomalías, pero una diferencia
grande no se elimina únicamente por ser grande, ni una pequeña prueba que dos productos sean iguales.

## 4. Oferta elegible y cálculo

Crear un selector único usado por búsqueda exacta, ficha, cesta, favoritos, alertas y gráficos
de comparación actual. Devuelve candidatos y descartes con motivo.

Condiciones: en alcance, identidad/restricciones correctas, cantidad fiable para la operación,
precio positivo y coherente, no retirado, disponibilidad confirmada según datos de la fuente,
zona/canal compatibles y edad dentro de la política. Si stock o zona son desconocidos, mostrar
precio orientativo aparte; no prometer compra disponible. El límite actual de tres días es
un máximo de antigüedad configurable, no una garantía de precio en caja.

La fecha se toma de la observación de CADA oferta, no del último fichero global. Guardar contexto
de CP/tienda de la sesión. Un precio sin ese contexto se etiqueta como zona no confirmada.

No elegir primero el envase de menor precio y aplicar después la promoción: calcular coste
de la cantidad solicitada para cada oferta elegible y luego elegir. Ejemplo de aceptación:
dos unidades; A cuesta 200 céntimos/unidad sin promoción, B cuesta 220 con segunda al 50 %.
B cuesta 330 frente a 400 de A y debe ganar.

Cantidades admitidas: unidades/envases o demanda en kg/l/unidades de consumo. Para packs
indivisibles, número de envases = techo(demanda/contenido); mostrar cantidad comprada y sobrante.
Ejemplo: demanda 1 l, pack de 6 l a 600 céntimos y brik 1 l a 120. El pack es más barato por
litro, pero exige pagar 600; no puede presupuestarse como 100 céntimos para esa demanda.
Para peso variable, estimar con peso solicitado y registrar intervalo/tolerancia disponible;
importe real solo después de pesaje o confirmación.

### Promociones

Tipos explícitos: precio público ya rebajado, precio exclusivo de socio, NxM, descuento en
unidad n, lote fijo, descuento por umbral, cupón inmediato y saldo futuro. Conservar base y
orden de aplicación, ámbito del umbral (artículo/categoría/cesta), límite de usos y exclusiones.
Aplicar redondeo en el nivel declarado por el comercio; si se desconoce, identificar cálculo
como estimación. No aplicar otra vez un porcentaje incluido en el precio publicado.

La elegibilidad depende de tarjetas activas, cupones confirmados, canal y fecha. Saldo futuro
no reduce el importe a pagar hoy. Cupones únicos se asignan una sola vez a toda la cesta.
Promociones incompatibles se enumeran como opciones, no se suman. Texto ambiguo queda sin
aplicación automática y muestra qué falta por confirmar. Cachear por versión de oferta y
promoción, no únicamente por día.

### Optimización

Enumerar subconjuntos de 1 a N tiendas elegidas (cinco cadenas no exigen un solver externo).
Para promociones independientes, minimizar por línea tras calcular cantidad y coste. Para
umbrales o cupones de cesta, evaluar asignaciones y restricciones de forma conjunta, o declarar
la regla no optimizada hasta implementar un algoritmo exacto con límites documentados.
No afirmar «óptimo» si una heurística no certifica el resultado.

Comparar listas de composición y cantidades constantes. Una tienda con faltantes no gana
por sumar menos artículos. Mostrar total parcial, faltantes y porcentaje cubierto. El ahorro
usa una referencia elegida (tienda habitual o escenario íntegramente especificado), no siempre
el supermercado más caro. Desplazamiento/envío se añaden solo si se conocen o los configura el
usuario; indicar cuando no están incluidos. Restricciones alimentarias nunca se relajan para ahorrar.

## 5. Migración y publicación

Conservar raw/bronze históricos. Generar el catálogo en alcance y las identidades en una
versión paralela. Mantener tabla de correspondencias viejo artículo/grupo → nuevas identidades,
con estado único/ambiguo/sin correspondencia.

Una referencia vieja a un producto de cadena puede resolverse por ese artículo. Una referencia
a un grupo mixto sin artículo no permite adivinar la intención: conservar texto, cantidad,
estado y favorito, marcar «Elige el producto para comparar» y excluirla del ahorro confirmado.
Permitir convertirla explícitamente en necesidad con alternativas. No seleccionar el miembro más
barato durante la migración. Preservar compras históricas y su procedencia estimada.

Publicación por manifiesto atómico como define el plan. Mantener trazabilidad de política,
extractor, normalizador y modelo de identidad; las cachés de API incluyen esa versión.

## 6. Archivos afectados

- Nuevos: `core/alcance.py`, `core/datos/alcance.yml`, `core/identidad.py`, contratos de oferta
  y materializador versionado (nombres finales decididos al implementar, con una sola fuente).
- Existentes: los cinco `projects/cesta/collectors/*.py`, `core/cobertura.py`, `core/schemas.py`,
  `projects/cesta/pipeline.py`, `emparejar.py`, `reprocesar.py`, `core/equivalencias.py`.
- Consumidores: `plataforma/api/catalogo.py`, `cesta.py`, `movimientos.py`, `analisis.py`,
  `alertas.py`, `vigilante.py`, contratos de interfaz y pruebas asociadas.
- Informes: `projects/cesta/cifras.py`, `cobertura_diaria.py` y `run.py`: distinguir recibido,
  admitido, publicado y vigente; los fallos parciales siguen siendo visibles.
