# Paquetes de implementación y pruebas de aceptación

Estado al 5 de octubre de 2026: todos los paquetes siguientes están **pendientes**.
El entregable actual es su especificación; no se han cambiado colectores, aplicación ni datos.
Leer primero [el plan](CESTA-PLAN-DE-IMPLEMENTACION.md), luego sus contratos de datos e interfaz.

## Reglas de ejecución para quien implemente

1. Comprobar Git y procesos activos. Preservar cambios del propietario; no incluirlos en un
   commit de esta tarea. Los archivos modificados detectados en la auditoría eran
   `core/datos/secciones.yml` y `docs/CIFRAS.md`; volver a comprobar antes de editar.
2. Ejecutar la línea base de tests. Trabajar con fixtures/copia de datos y base de pruebas.
   No lanzar la pasada de horas para desarrollar una regla de identidad.
3. Una entrega contiene código, migración cuando corresponda, pruebas y documento de resultado
   medido. No marcar un paquete hecho por escribir su propuesta.
4. No publicar gold con otro esquema sin probar todos sus consumidores y el adaptador antiguo.
5. Probar rollback y compatibilidad de listas/compras antes del corte de versión.

## T01 — Política familiar y presupuesto de extracción

**Dependencias:** ninguna. **Archivos:** nuevos `core/alcance.py`,
`core/datos/alcance.yml`; los cinco colectores, `reprocesar.py`, `cobertura.py` y `run.py`.

Implementar clasificación incluida/excluida/revisión con motivo y versión. Aplicar antes del
recorrido a categorías conocidas y después a los productos, incluidos buscador Alcampo,
promociones y sitemap Aldi. Crear ejecución seca que liste qué pediría y qué excluiría sin red.
Derivar prioridades de categorías de favoritos/lista y presupuesto, manteniendo descubrimiento.

**Pruebas:** comida de mascotas incluida/cama excluida; pañales incluidos/carrito excluido;
papel higiénico incluido/cuaderno excluido; alimento en categoría promocional admitido;
televisor dentro de promociones excluido; categoría mixta no excluida entera a ciegas;
ningún enriquecimiento del bazar ya clasificado. Captura con decoraciones desaparecidas no
rechaza alimentos válidos; desaparición de frescos sí activa advertencia/rechazo pertinente.

**Entrega:** informe por fuente de incluidos, excluidos, pendientes, peticiones estimadas y
posteriormente realizadas; no inventar porcentaje de ahorro de red. Política cubre todas las
familias del contrato y decisiones ambiguas quedan visibles.

## T02 — Oferta trazable y publicación consistente

**Depende de:** T01. **Archivos:** `schemas.py`, `storage.py`, `pipeline.py`, `emparejar.py`,
`catalogo.py`, `cifras.py`, `cobertura_diaria.py` y pruebas.

Transportar captura real, zona/tienda/canal, disponibilidad, retirada, origen de precio y
versión desde colector a oferta publicada. Distinguir último intento y última captura aceptada.
Publicar un conjunto completo en directorio versionado y activar por manifiesto atómico.

**Pruebas:** Alcampo rechazado hoy no aparece como precio actualizado hoy; combinar captura
parcial con observaciones anteriores conserva fechas individuales; crash antes del manifiesto
mantiene versión anterior; solicitud API nunca mezcla versiones; stock nulo no se vuelve `true`.

**Entrega:** consulta trazable desde cada precio de pantalla hasta observación de fuente.

## T03 — Identidad y banco de referencia por familias

**Depende de:** T01–T02. **Archivos:** nuevo `core/identidad.py`, `atributos.py`, `matching.py`,
`equivalencias.py`, `emparejar.py`; banco de casos y herramienta de revisión.

Separar artículo exacto, familia y alternativa. Validar GTIN y presentación, guardar evidencia,
conflictos y confirmaciones. Mantener candidatos textuales/vectoriales fuera de identidad
confirmada. Revisar extracciones por familia, sin trasladar la ausencia de atributo a un valor.

**Banco mínimo como objetivo de entrega:** 30 pares por cada una de las 13 familias del
contrato: 10 idénticos, 10 parecidos pero distintos y 10 incompletos/conflictivos. Son 390 pares
propuestos, no una muestra ya obtenida. Si alguna familia carece de positivos suficientes,
declarar hueco y no afirmar validación completa. Conservar fuente, fecha y justificación humana.
Separar conjunto de desarrollo y evaluación por producto/identidad, para que el mismo artículo
no aparezca a ambos lados. No derivar la etiqueta de verdad del algoritmo que se está midiendo.

**Casos obligatorios:** galleta rellena/simple; pan integral/blanco/sin gluten; pollo/cerdo;
pechuga/muslo; merluza/bacalao; filete/pescado entero; fresco/congelado; manzana/pera;
tomate fresco/triturado; atún en aceite/natural; detergente líquido/cápsulas; pañal talla 3/4;
comida de perro/gato; café grano/soluble; brik/botella; pack/unidad; mismo GTIN con pack contradictorio.

**Aceptación:** cero falsos «idéntico» en esos casos obligatorios. Reportar precisión, recall,
abstenciones y cobertura por familia; no reducirlos a «acierto». Esa meta de cero en el banco
no se publicita como garantía universal. Un grupo con dos marcas no autoriza identidad exacta.

## T04 — Migración de listas, favoritos y alertas

**Depende de:** T03. **Archivos:** migración nueva después de la última disponible en
`plataforma/sql` (actualmente 010), `almacen.py`, `main.py`, `alertas.py`, `vigilante.py`,
`catalogo.py`, tipos y adaptadores del navegador.

Añadir identidad, artículo de referencia, modo exacto/alternativas, restricciones, necesidad,
cantidad/unidad y estado, manteniendo referencias heredadas. Resolver solo correspondencias
unívocas; las demás se conservan con solicitud de elección. Alertas de grupo ambiguo quedan
pendientes de resolución, sin disparar una bajada de otra marca.

**Pruebas:** número de listas/favoritos/compras preservado; textos y cantidades iguales;
grupo mixto no elige barato automáticamente; permiso de lector sigue sin escribir; dos
ejecuciones de migración no duplican; cliente antiguo falla con explicación o adaptador seguro;
rollback no elimina compras nuevas; favorito comprado sigue siendo favorito.

## T05 — Selector único de ofertas elegibles

**Depende de:** T02–T04. **Archivos:** `cesta.py`, `catalogo.py`, `movimientos.py`, alertas.

Aplicar identidad o restricciones explícitas, precio válido, fecha por observación, zona,
canal, retirada y stock. Devolver descartes explicados. Eliminar la semántica de que
`comparacion_fiable` por unidad significa identidad. Usar un reloj inyectable en pruebas.

**Pruebas:** oferta del día 1 no decide una cesta del día 5 con límite 3; día límite exacto
documentado; ausencia de zona/stock no garantiza compra; retirada siempre fuera; precio nulo
no suma cero; cantidad desconocida no habilita conversión de packs; filtros alimentarios
se respetan tanto en candidatos como en sustituciones.

## T06 — Cantidades, promociones y optimización

**Depende de:** T05. **Archivos:** `core/promos.py`, `api/cesta.py`, preferencias y contratos.

Implementar tipos/condiciones comerciales del contrato. Enumerar ofertas por coste final y
subconjuntos de tiendas; compartir el motor entre presupuesto, reparto y archivo estimado.
Cupones con efecto de cesta necesitan asignación conjunta; si no está soportada, exponer
estimación sin esa regla, no «óptimo» global. Perfil de club opcional.

| Fixture sintético | Resultado esperado |
|---|---|
| Dos unidades de 100 céntimos, segunda al 50 % | 150 céntimos |
| Tres unidades de 100, segunda al 50 % | 250 céntimos |
| Cuatro unidades de 100, 3×2 | 300 céntimos |
| Precio publicado final 80 tras 20 % | Una unidad cuesta 80, nunca 64 |
| Tarjeta acumula 20 % sobre 100 | Paga 100 hoy; saldo futuro 20, si elegible |
| Cupón único de 100 en dos líneas | Descontar 100 total como máximo |
| Demanda 1 l; pack 6 l/600 y unidad 1 l/120 | Mostrar desembolsos 600 y 120; no valorar el pack en 100 |
| Dos unidades: A 200/u; B 220/u segunda -50 % | B gana con 330 frente a 400 |
| Tienda A cubre 8/10 y B cubre 10/10 | A no gana como compra completa por tener menor subtotal |
| Cupón vencido o socio no elegible | No descontar |
| Se permite máximo tres tiendas | Evaluar también una y dos |

**Entrega:** descomposición conciliable de céntimos, cantidades, sobrantes, descuentos, saldo,
faltantes y referencia. Repetir cálculo con mismo contexto/versiones da el mismo resultado.

## T07 — Compra confirmada e histórico familiar

**Depende de:** T04 y T06. **Archivos:** nueva migración, `almacen.cierra_compra`,
`main.cerrar_compra`, `cesta.coste_por_linea`, interfaz de cierre e historial.

Aceptar importes confirmados o estimados explícitamente. Guardar precios y procedencia
inmutables, tienda real y momento. Total confirmado sin desglose no fabrica precios por línea.
Corregir compras con auditoría. Solo las líneas en carro pasan a compra; conservar pendientes.

**Pruebas:** tienda declarada sin precio no cambia a otra; doble envío devuelve misma compra;
error transaccional no archiva media lista; catálogo del día siguiente no cambia ticket;
total confirmado diferente de estimación no se oculta; cambio de cantidad requiere nuevo cálculo;
historial anterior queda etiquetado estimado, no elevado a confirmado retroactivamente.

## T08 — Interfaz cotidiana

**Depende de:** contratos T04–T07; desarrollo visual paralelo contra fixtures.
**Archivos:** `App.tsx`, `Inicio`, `Buscar`, `Producto`, `Grupo`, `Favoritos`, `Cesta`,
`BotonAnadirACesta`, `Etiquetas`, `RepartoEnTiendas`, estado local y tipos.

Implementar las cuatro rutas y los recorridos del documento de aplicación, conservando
capacidades existentes. Cambiar etiquetas que prometen identidad sin evidencia. No reescribir
todos los estilos ni sustituir componentes funcionales sin motivo.

**Pruebas de navegador:** elegir galleta exacta mantiene marca/receta; elegir pollo no
introduce cerdo; favorito → necesito → carro → compra conserva favorito; elegir alternativas
explica diferencia y permite desactivar; error deja acción recuperable; desconexión y
reconexión no duplican; lector compartido no edita; teclado llega a todas las acciones.

**Entrega:** capturas de móvil/escritorio de todos los estados y prueba con persona ajena
al desarrollo. No darlo por final por un test que solo comprueba que existen botones.

## T09 — Gráficas correctas

**Depende de:** T02, T03, T07. **Archivos:** `derive.py`, `api/analisis.py`, movimientos,
consultas de gasto, componentes gráficos y tablas accesibles.

Aplicar ventanas de calendario, series por identidad/presentación y episodios. Construir
gráficas con las fórmulas y coberturas del contrato. Separar gastos confirmados, estimados
y contrafactuales. No recalcular el pasado con precios actuales.

**Pruebas:** dos observaciones separadas 100 días no entran juntas en mínimo 90 días;
cambio de pack rompe continuidad pertinente; cambio de €/kg a €/ud no se une; dos campañas
separadas no forman una sola duración; hueco permanece hueco; suma de líneas = total de barras;
ticket sin desglose figura en gasto total pero en sección «Sin desglose»; mes incompleto
se compara con igual tramo o se avisa; cero compras no equivale a ausencia de sincronización.

## T10 — Verificación diaria y entrega operativa

**Depende de:** todas. **Archivos:** `run.py`, `ejecutar.bat`, verificadores, documentación
operativa, herramientas de despliegue local.

Probar primero con raw existente, luego una muestra en vivo de cada fuente dentro del alcance
y finalmente un recorrido diario controlado. Registrar categorías solicitadas, artículos únicos,
respuesta a bloqueos, cobertura de cesta, precios nuevos y motivo de no publicación. No llamar
«correcta» a una fuente cuyo dato no se aceptó aunque el proceso global termine.

Métricas operativas: peticiones/tiempo por fuente, incluidos/excluidos/revisión, cobertura de
favoritos, frescura por oferta, stock desconocido, conflictos de identidad, pares exactos
confirmados, cambios de GTIN/formato y cuántas líneas pueden presupuestarse de verdad.

Inyectar fallos: categoría vacía anómala, bloqueo, respuesta sin estado, fichero corrupto,
desaparición de rama fuera de alcance, corte durante publicación, precio antiguo y migración
interrumpida. Verificar que cada control detecta el problema pertinente sin falsear fechas.

## Comandos existentes de comprobación

Desde la raíz del proyecto:

    uv run pytest -q
    uv run python -m projects.cesta.auditar_identidad
    uv run python -m projects.cesta.verificar_docs

Desde `plataforma/web/app`:

    npm run tipos
    npm run build

Con las dependencias y servicios de prueba preparados según el manual actual:

    uv run python -m plataforma.prueba_funciones
    uv run python -m plataforma.prueba_navegador

Después de desplegar localmente y comprobar el destino de la prueba:

    uv run python -m plataforma.prueba_produccion

Estas puertas pueden crear usuarios de prueba y efectuar escrituras; leer su configuración
antes de ejecutarlas. El pase de la suite actual no reemplaza los casos nuevos T01–T10.

## Plantilla obligatoria de cierre de cada paquete

- Estado: pendiente / en curso / verificado en pruebas / desplegado y verificado.
- Archivos y migraciones modificados; versión de datos/contrato.
- Qué comportamiento cambia para la persona y cómo se reproduce.
- Pruebas añadidas, ejecutadas, resultado y limitaciones.
- Métricas antes/después sobre el mismo conjunto, con fecha.
- Compatibilidad, recuperación y evidencia de que listas/compras se conservan.
- Pendientes con condición concreta; no cerrar «todo correcto» si falta una verificación.

## Condición final de aceptación

La persona puede recorrer de favorito a compra confirmada; los consumibles relevantes se
actualizan; ningún caso obligatorio mezcla identidad y sustitución; toda recomendación tiene
fecha/zona/condiciones; y cada céntimo de una gráfica puede rastrearse a observaciones o pagos.
La aplicación explica ausencias y límites sin inventar cobertura ni ahorro.
