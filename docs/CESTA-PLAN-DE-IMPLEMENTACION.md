# Cesta familiar: encargo ejecutable

Fecha: 5 de octubre de 2026. Estado: **especificación lista para implementar; cambios de
producción pendientes**. Este documento traduce el encargo del propietario a decisiones de
producto, tareas de código y condiciones de aceptación. No es otro diagnóstico.

## Resultado contratado

Una persona puede preparar la compra habitual de su hogar, conservar sus favoritos, señalar
lo que necesita, comparar artículos exactos entre supermercados, aceptar alternativas cuando
quiera, comprar, registrar lo pagado y entender su gasto y ahorro con gráficas claras.

Aplica a TODAS las categorías de consumibles: alimentación, frescos, bebidas, limpieza,
higiene, bebé, mascotas y consumibles domésticos. La leche es solamente un caso de prueba.
El objetivo no es maximizar el número de productos, de enlaces ni de supermercados comparables.
Es ofrecer decisiones de compra correctas sobre un catálogo relevante.

## Documentos que forman el contrato

1. [Datos, alcance y comparación](CESTA-DATOS-Y-COMPARACION.md): qué recoger, qué conservar,
   cómo identificar artículos, cómo elegir ofertas y cómo migrar los datos.
2. [Aplicación y gráficas](CESTA-APLICACION-Y-GRAFICAS.md): pantallas, interacciones,
   contratos públicos, accesibilidad, gasto, ahorro y ofertas.
3. [Tareas y aceptación](CESTA-TAREAS-Y-ACEPTACION.md): unidades de trabajo con archivos,
   dependencias, pruebas y criterios de entrega.

Evidencia de partida: [auditoría del 5 de octubre](AUDITORIA-CESTA-2026-10-05.md).
La auditoría registra fallos; los tres documentos anteriores deciden cómo resolverlos.

Ampliación solicitada el 6 de octubre: [fichas completas, Lidl, comparación automática y
aprendizaje](CESTA-AMPLIACION-2026-10-06.md). Incluye resultados medidos, dos instrumentos
probados y paquetes T11/T12 pendientes de integración; no declara T01 ni T03 terminados.

## Decisiones cerradas para evitar otra ronda de ambigüedad

- Todo el proyecto se centra en cesta familiar. El bazar duradero queda fuera del catálogo
  de consumo, las recomendaciones y el recorrido diario. El histórico original se conserva.
- Se reutilizan Python, Polars, Parquet, DuckDB, FastAPI, PostgreSQL y React existentes.
  No se introduce otro framework, un servicio de IA pagado ni un despliegue público.
- Una ficha concreta se añade por identidad exacta. Cambiar de marca o de presentación
  requiere que la persona habilite alternativas en esa línea.
- Una búsqueda genérica explora familias; no convierte automáticamente todos sus resultados
  en un único producto. «Pan» permite explorar; no equipara pan sin gluten y pan de trigo.
- Cuando faltan pruebas de identidad se conserva el artículo y se explica que la coincidencia
  está por confirmar. No se inventa una coincidencia para mejorar la cobertura.
- La ausencia de un atributo no equivale a «no contiene». Esto aplica a alérgenos y también
  a sin lactosa, sin azúcar, integral, fresco/congelado y otras restricciones.
- Se distingue desembolso inmediato, saldo futuro de club y ahorro por sustitución.
- Gasto confirmado y gasto estimado son series diferentes. Los importes de compras antiguas
  no se reescriben cuando cambian precios, grupos o reglas.
- Los miembros de un club y sus cupones se configuran por hogar; una oferta condicionada
  no se aplica por defecto a todo el mundo.
- Los precios desconocidos, productos retirados, capturas viejas y cestas incompletas
  tienen estados visibles. No cuentan como gratis ni producen una recomendación ganadora.
- La nota propia de «calidad» deja de decidir el ahorro y de presentarse como calidad
  objetiva. Se muestran composición y datos publicados con procedencia, cuando existan.

## Flujo que debe quedar completo

1. Configurar zona de compra, tiendas y tarjetas opcionales.
2. Buscar o recuperar un favorito; elegir artículo exacto o necesidad con alternativas.
3. Marcar «Lo necesito» y cantidad. La lista es persistente y compartible.
4. Consultar presupuesto: una tienda o hasta el número de tiendas permitido, con líneas
   cubiertas, faltantes, ofertas y sustituciones identificadas.
5. Marcar productos en el carro, incluso sin conexión; sincronizar sin duplicarlos.
6. Cerrar compra, confirmar tienda e importe o dejarlo expresamente como estimación.
7. Ver gasto semanal/mensual y evolución de la cesta; reponer a partir de favoritos.

## Qué conservar de la aplicación

Cuentas y permisos, listas compartidas, invitaciones, cola sin conexión, escáner, avisos,
componentes de interfaz y sistema de pruebas son activos existentes. Se adaptan sus contratos,
no se reconstruyen a ciegas. Se mantienen las compras, listas y favoritos de los usuarios.

`grupo_id` queda como referencia heredada o de alternativas. No se reutiliza como prueba de
identidad. El cambio exige migración; renombrar la etiqueta del grupo no basta.

## Secuencia de entregas

| Entrega | Resultado visible | Dependencia |
|---|---|---|
| E1. Catálogo familiar | Bazar fuera del catálogo y de los recorridos innecesarios; cobertura coherente | Ninguna |
| E2. Identidad y ofertas | Fichas exactas, formatos, zona y fecha conservados | E1 |
| E3. Lista fiel a la elección | Añadir y favoritos conservan el artículo; alternativas explícitas | E2 |
| E4. Presupuesto correcto | Promociones, packs, faltantes y comparación de cestas equivalentes | E2–E3 |
| E5. Compra y gastos | Ticket/importe confirmado separado de estimación; cierre idempotente | E3–E4 |
| E6. Experiencia final | Navegación simple, gráficas verificadas, móvil y pruebas de usuario | E1–E5 |

Cada entrega se activa solo después de superar sus casos de aceptación. La interfaz puede
desarrollarse contra fixtures del nuevo contrato mientras se prepara el dato, sin publicar
resultados simulados como reales.

## Seguridad de la transición

Trabajar primero en una copia de los Parquet y una base de pruebas. No regenerar grupos sobre
producción mientras existan listas referidas a los identificadores antiguos sin migración.
Guardar una copia recuperable de la base y un manifiesto de versión antes del corte.

Publicar datos por versión: escribir catálogo, identidades, ofertas y métricas en un directorio
nuevo, validarlo y cambiar un único manifiesto activo de forma atómica. La API fija esa versión
durante cada solicitud. Evita mezclar identidades nuevas y precios anteriores.

Activar la nueva API/interfaz mediante una opción reversible. Conservar lectura de referencias
antiguas hasta resolverlas, y mantener el lector nuevo de compras aunque se desactive el nuevo
optimizador: una reversión no puede hacer desaparecer compras creadas después del corte.

## Qué se entrega al cerrar este encargo

- Cambios de código y migraciones versionadas, junto con los documentos actualizados.
- Informe de alcance antes/después por cadena y motivo de exclusión.
- Banco de identidad revisado por categorías, falsos positivos y cobertura medidos por separado.
- Pruebas de todos los recorridos y ejemplos numéricos de cesta y ofertas.
- Informe de identidad/frescura de cada recomendación y de los datos que alimentan cada gráfica.
- Capturas de la interfaz final en móvil y escritorio, con estados vacíos y errores.
- Copia recuperable y procedimiento probado de activación/reversión.

No se considera terminado por pasar los tests antiguos, por aumentar el catálogo ni por
mostrar una gráfica atractiva. Debe superar las pruebas del nuevo contrato.
