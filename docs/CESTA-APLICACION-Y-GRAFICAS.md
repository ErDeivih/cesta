# Aplicación familiar: interfaz, funcionalidad y análisis

Especificación de implementación, 5 de octubre de 2026.
Depende del [contrato de datos](CESTA-DATOS-Y-COMPARACION.md).
No es una descripción de funcionalidades ya verificadas en producción.

## 1. Navegación y jerarquía

Conservar React y los componentes existentes. Navegación principal de cuatro destinos:
**Mi compra · Buscar · Favoritos · Mis gastos**. Ajustes desde el perfil. El panel técnico
queda en una ruta secundaria, fuera del recorrido habitual de compra.

Pantalla inicial: lista activa, cantidad de pendientes, presupuesto con cobertura y un botón
principal «Ver mi compra». Debajo, favoritos que necesita reponer y bajadas de sus artículos
exactos. Sin cuenta/lista, mostrar buscador y acción «Crear mi primera lista»; no una parrilla
de estadísticas sin contexto. No pedir tarjetas, presupuesto, gustos y registro en un único formulario.

Mantener como propuestas de diseño: texto base legible de 16 px, controles de al menos 44 × 44 px,
ancho móvil de prueba de 390 px, zoom 200 %, navegación por teclado, foco visible y contraste
comprobable. Son condiciones de aceptación del producto, no una certificación de accesibilidad.
Usar español familiar; reservar EAN, matching, bronze y otras palabras internas para ayuda técnica.

Cada pantalla debe definir y probar: cargando, vacía, resultados, error, datos antiguos y
sin conexión. No depender solo de rojo/verde. Moneda, unidades, fecha y condiciones visibles.

## 2. Buscar y comparar

### Búsqueda genérica

«Galletas», «pan», «pollo» o «verdura» abren una familia con artículos individuales.
Filtros adaptados a esa familia: marca, variante, formato, conservación, dieta y cadena.
Mostrar filtros activos y «Limpiar filtros». No rellenar una búsqueda estricta con resultados
que vulneren filtros para evitar una pantalla vacía.

Cada tarjeta representa un artículo exacto o una oferta de fuente todavía sin identidad
confirmada: nombre completo, imagen de ese artículo, formato, precio del envase y por unidad,
tiendas donde está confirmado, fecha y botón de añadir. La foto de una marca no puede representar
el precio más barato de otra. Si solo hay una tienda, sigue siendo un resultado útil.

La ordenación por «más barato» usa una magnitud visible: envase o unidad de referencia.
Comparar por kg no mezcla frescos, congelados, preparados o neto/escurrido sin que el usuario
seleccione ese alcance de exploración. No se denomina «ahorro» a ordenar productos diferentes.

### Ficha exacta

Encabezado con marca, variante, contenido y pack. Tabla de ofertas del mismo artículo,
cada una con tienda/zona, precio total, precio por unidad, fecha, disponibilidad y condición.
Botón principal «Añadir este producto». Favorito vinculado a esa identidad.

Sección independiente «Alternativas que puedes elegir», con diferencias explícitas:
otra marca, otro tamaño, otra presentación. Si la alternativa vulnera una restricción
obligatoria, no aparece como compatible. Las coincidencias pendientes no llevan «mismo producto».

El historial pertenece a artículo + presentación + tienda/zona/canal. Si falta historia,
explicar «Tenemos precios desde [fecha]». No usar la serie de todo el grupo de alternativas.

### Misma cadena

Permitir seleccionar entre dos y cuatro artículos para comparar lado a lado: precio del
envase, precio por unidad, cantidad, marca, atributos de familia, promociones y composición
publicada. No exigir que sean idénticos para esta vista exploratoria; titularla «Comparar
opciones». En cambio, una afirmación de ahorro sobre el mismo producto exige identidad exacta.

## 3. Favoritos, necesidad y lista

Un favorito es algo que el hogar quiere conservar. No se elimina al comprarlo.
En cada favorito: «Lo necesito» añade o incrementa una línea de la lista elegida; «Ya tengo»
quita su necesidad pendiente con opción de deshacer, pero mantiene el favorito. Mostrar
última compra confirmada si existe; no inferir existencias reales de una estimación.

Estados de línea: `pendiente`, `en_carro`, `comprado` (archivado en compra), `descartado`.
La necesidad recurrente pertenece al favorito; la compra pertenece a un episodio de lista.
No reutilizar un solo booleano para favorito, comprado y disponible.

Al añadir desde una ficha, modo **Este producto** y cantidad de envases por defecto uno.
Al añadir una necesidad genérica, modo **Acepto alternativas**, previa selección de atributos
mínimos de la familia. Ejemplo: «pescado» permite navegar, pero el optimizador pide concretar
especie y preparación antes de presupuestarlo. No imponer diálogos en cada tachado.

En la línea se puede cambiar de modo. Habilitar alternativas muestra restricciones conservadas
y diferencias permitidas; no borra la identidad de referencia. Cambiar de producto recalcula
presupuesto y explica el efecto. Compras y preferencias anteriores permanecen intactas.

Cantidad editable con botones y entrada directa, unidad visible, validación y deshacer.
Para frescos permitir demanda decimal en kg; para envases enteros impedir fracciones imposibles.
Orden de lista por pasillos, con opciones de agrupar por tienda elegida o ver pendientes.
Marcar en el carro debe ser una acción grande de un toque, independiente de abrir la ficha.

### Sin conexión y listas compartidas

Conservar cola local existente. Cada mutación tiene ID idempotente, versión de línea y estado
pendiente/sincronizado/conflicto. Mostrar «Guardado en este móvil; pendiente de sincronizar».
Reintentar sin duplicar líneas ni cantidades. Conflictos de cantidades se explican; no sumar
ciegamente dos asignaciones absolutas. Tachado y borrado simultáneos se resuelven con política
documentada y opción de recuperación. Respetar permisos de lectura/escritura existentes.

## 4. Dónde comprar

Resumen con dos vistas: **Una tienda** y **Repartir la compra**. El usuario limita tiendas
y configura su habitual. La respuesta dice cuántas líneas cubre, cuánto pagará ahora,
qué falta, qué alternativas usa y qué condiciones exige. Precio antiguo orientativo aparte.

Mostrar «Estimación para 18 de 20 productos», no «Tu compra cuesta X» si faltan dos.
Las cantidades y artículos de referencia son constantes entre escenarios. Ahorro por mismo
producto y ahorro aceptando sustituciones se presentan en renglones distintos.

Cada tienda del reparto tiene una sublista operable, con subtotales. Explicar qué líneas
justifican otra parada. Coste de viaje opcional configurable por visita y envío cuando proceda;
si no se incluye, mostrarlo. No convertir tiempo del cliente en dinero sin que lo configure.

Perfil de club: tarjetas que posee el hogar, canal y cupones activados. Separar «Pagas hoy»
y «Acumulas para otra compra». Ofertas requieren aceptación solo cuando impliquen comprar
más o cambiar de artículo; la selección no puede añadir seis unidades silenciosamente.

## 5. Cerrar compra y registrar gasto

«Terminar compra» revisa solo lo que está en el carro. Lo pendiente sigue en la lista.
Confirmar tienda por línea o por compra y ofrecer:

1. «Confirmar importes»: introducir el total del ticket y, opcionalmente, precios por línea.
2. «Guardar estimación»: conservar previsión, marcada como estimada.

La primera versión no depende de OCR. Un total confirmado sin detalle permite gasto total,
pero no un reparto exacto por categorías. No distribuir descuentos desconocidos inventando
precios por artículo. Si se reparte proporcionalmente para análisis orientativo, guardar
procedencia de asignación y no tratarla como importe observado.

Compra inmutable con correcciones auditables: ID, tienda, fecha real, líneas, cantidades,
precios confirmados/estimados, descuentos inmediatos, saldo obtenido, envío, total y origen.
No guardar el menor precio de otra tienda cuando falta el de la tienda declarada.
Repetir el cierre con el mismo ID no produce dos compras ni dos gastos.

Para contrafactuales guardar versión de ofertas y restricciones usadas al comprar, o una
instantánea suficiente para reconstruir la comparación. Un precio encontrado mañana no
demuestra lo que se habría ahorrado ayer.

## 6. Gráficas y conclusiones

Todas tienen título que responde una pregunta, unidad, periodo, procedencia, fecha de
actualización y cobertura. Tabla accesible con los mismos valores. Tooltip con teclado/táctil.
No pintar cero para días sin datos; no unir huecos como si fueran observaciones reales.
Conservar identificadores de producto, presentación, tienda y zona en cada punto.

| Gráfica | Cálculo | Lo que no debe afirmar |
|---|---|---|
| Precio de este artículo | Serie observada por identidad/presentación/tienda; elegir envase o €/unidad | Evolución de un grupo con marcas cambiantes |
| Mi gasto semanal/mensual | Suma de pagos confirmados por fecha de compra; estimaciones en serie separada | Gasto real a partir del catálogo |
| En qué gasto | Importes confirmados de líneas clasificadas; resto como «Sin desglose» | Atribuir un ticket completo a categorías inventadas |
| La misma cesta en cada tienda | Suma de cantidades fijas y ofertas elegibles, misma referencia | Que una tienda incompleta sea más barata |
| Qué cambio me ahorra más | Diferencia por línea entre referencia y opción; suma concilia con el total | Mezclar ahorro de identidad y sustitución |
| Qué ha cambiado de precio | Relativos del mismo artículo/presentación; cobertura y huecos declarados | Inflación de mi hogar a partir de la media del surtido |

Ventanas de 7/30/90 días se calculan por fechas de calendario. En mínimos históricos indicar
«mínimo observado» y días/capturas disponibles. Descuento frente a referencia previa excluye
el precio actual cuando se afirma «frente a lo habitual anterior». Promociones se agrupan
en episodios contiguos observados, con inicio/fin desconocido cuando hay huecos.

Gasto mensual compara meses completos o el mismo tramo del mes. Sin cesta constante,
distinguir efecto cantidad, mezcla y precio en lugar de atribuirlo todo a subidas.
Escenarios anuales basados en compras semanales se etiquetan como proyección, con frecuencia
explícita; no como ahorro anual demostrado. No afirmar estacionalidad anual con un mes de datos.

La clasificación A/B/C por precio no se usa como calidad nutricional. Los sellos publicados
y la composición tienen procedencia y fecha; no se promete seguridad dietética por similitud.

## 7. Contratos de API propuestos

Ampliar de manera versionada; mantener adaptadores para clientes anteriores durante migración.
Las rutas siguientes son **propuestas nuevas**, no comandos ni endpoints ya disponibles.

- Búsqueda: `GET /api/v2/articulos` con texto, familia y filtros; devuelve artículos, no grupos
  mixtos. Incluye `identidad_id`, `articulo_fuente_id`, presentación y estado de comparación.
- Ficha: `GET /api/v2/articulos/{id}` con ofertas exactas, alternativas separadas y evidencias.
- Lista: ampliar línea con `modo`, `identidad_id`, referencia de fuente, `familia_id`,
  restricciones, cantidad, unidad, estado y versión. Crear/editar valida consistencia.
- Presupuesto: `POST /api/v2/presupuestos` con líneas, zona, tiendas, clubes, cupones y fecha;
  devuelve ID/versión, elegidos, descartes, faltantes, sustituciones, pagos y saldo futuro.
- Cierre: `POST /api/v2/compras` con clave idempotente, revisión de lista, líneas del carro
  e importes/origen; devuelve compra persistida, pendientes restantes y conciliación.
- Análisis: endpoints específicos con `metodo`, `version_datos`, `periodo`, `cobertura`,
  `puntos` y `advertencias`. No devolver solo arrays sin contexto.

Una línea exacta sin identidad confirmada puede apuntar al artículo de fuente y comprarse
en esa cadena; no se amplía a otras hasta confirmar miembros. Respuestas incluyen causas
estables como `precio_antiguo`, `zona_desconocida`, `sin_stock`, `identidad_pendiente`,
`restriccion_incompatible`, `oferta_sin_confirmar`. La interfaz traduce códigos a frases.

## 8. Cambios concretos de interfaz

- `BotonAnadirACesta.tsx`: recibir artículo/identidad y modo; dejar de insertar automáticamente
  `producto_id: null`. Destino de lista visible cuando el hogar tiene varias.
- `Producto.tsx` y `Grupo.tsx`: ficha exacta y alternativas separadas; series por artículo.
- `Buscar.tsx` y `Etiquetas.tsx`: tarjetas de identidad; retirar promesa de «mismo producto»
  basada solo en número de cadenas. Sin porcentajes de ahorro mezclados.
- `Cesta.tsx` y `RepartoEnTiendas`: modos, cantidades, elegibilidad, cobertura, sustituciones,
  cierre y cola sin conexión adaptados al nuevo contrato.
- `Favoritos.tsx`, `Inicio.tsx`, `Mosaico`: necesidad persistente separada del favorito;
  no sugerir automáticamente productos fuera del alcance familiar.
- `Panel.tsx`/gráficas: mantener diagnóstico técnico aparte; añadir Mis gastos con datos
  confirmados y un selector explícito para estimaciones.
- `tipos.ts`, `api/*`, cachés y estado local: actualizar contratos, versiones y migración
  del almacenamiento del navegador. Un móvil antiguo no debe enviar una mutación ambigua.

## 9. Prueba de uso con personas

Usar una cuenta de prueba sin datos personales. Persona que no participó en el desarrollo,
en móvil: crear lista, encontrar su artículo, añadir favorito, marcar necesidad, ajustar
cantidad, entender una oferta, comparar una o varias tiendas, tachar sin conexión y cerrar compra.
Preguntar qué artículo comprará, cuánto pagará hoy y qué parte del ahorro exige cambiar de marca.

No dar la prueba por aprobada si confunde saldo de club con descuento inmediato, presupuesto
con gasto real o alternativa con artículo idéntico. Registrar errores, tiempo y ayudas dadas;
el desarrollador corrige las pantallas y repite. Las pruebas automáticas no sustituyen esta parte.
