# Registro de investigación y referencias

Consultado el 7 de octubre de 2026. Separar siempre observación, propuesta e implementación.
No se ha hecho login ni un ensayo completo de productos competidores; se han
consultado sus páginas oficiales y capturas públicas. No se han copiado sus activos.

## Referencias funcionales y visuales

| Fuente oficial | Observado | Adaptación propuesta, no copia literal |
|---|---|---|
| [Paprika](https://www.paprikaapp.com/) y [captura de receta Mac](https://www.paprikaapp.com/static/images/screenshots/mac/recipe.jpg) | biblioteca, ingredientes escalables, pasos, temporizadores, planificación y listas; captura inspeccionada visualmente con ingredientes a izquierda y pasos a derecha | recetario persistente y modo cocina con columnas claras; no reproducir contenido de la receta ni su marca |
| [Samsung Food Planner](https://samsungfood.com/meal-planner/) | plan semanal, recetas y paso explícito a lista | calendario y revisión de compra; no fusionar diario y compra ni asumir que el plan se consumió |
| [Cronometer Diary](https://support.cronometer.com/hc/en-us/articles/360018171731-Diary-Overview) | registro por día con cantidades/unidades y resumen nutricional; control visual de calendario inspeccionado | fecha protagonista, alimentos por comida y cobertura por nutriente; sin importar biometría clínica ni metas universales |
| [Cronometer Display Settings](https://support.cronometer.com/hc/en-us/articles/360060181932-Display-Settings) | secciones configurables y subtotales | ocultar widgets no usados y separar dato desconocido; no saturar con todos los indicadores |
| [Soysuper FAQ](https://soysuper.com/about/preguntas-frecuentes) | compara el coste de una lista entre supermercados | coste de la misma cesta, faltantes y condiciones visibles; referencia funcional, no auditoría de su matching |

La mayor diferencia respecto al prototipo local es estructural: biblioteca/diario
persistentes, navegación específica, búsqueda de alimentos y acciones de dominio.
No se resuelve poniendo nuevas tarjetas alrededor del formulario único de Cocina.

## Identidad, nutrición y accesibilidad

- [GS1: reglas de GTIN](https://www.gs1.org/1/gtinrules/en/) y
  [contenido neto](https://www.gs1.org/1/gtinrules/en/rule/266/declared-net-content):
  el contenido declarado y los niveles de envase importan para identificación.
  Aplicación al proyecto: cambios de cantidad/pack no son ruido a borrar; validar
  GTIN y atributos juntos. No implica que todos los datos de una tienda cumplan
  perfectamente el estándar.
- [Open Food Facts, documentación API](https://openfoodfacts.github.io/openfoodfacts-server/api/):
  posible fuente complementaria de ingredientes/nutrición por código, con límites,
  atribución y licencias diferenciadas. No garantiza exactitud/completitud.
  Para volumen aconseja exportaciones locales. **No integrado en esta entrega**.
  Antes de importar: revisar condiciones aplicables y mantener procedencia; no
  convertirlo en prueba de stock, precio actual o surtido completo de Lidl.
- [W3C contraste mínimo](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html):
  verificar 4,5:1 para texto ordinario y 3:1 para texto grande conforme a su definición.
  El diseño exige además objetivos táctiles 44px como criterio propio; no atribuir
  ese número al mismo criterio de contraste. Medir estados focus/disabled/hover.

## Lidl: evidencia reproducible

[Robots](https://www.lidl.es/robots.txt) →
[índice sitemap](https://www.lidl.es/static/sitemap.xml) →
[productos](https://www.lidl.es/p/export/ES/es/product_sitemap.xml.gz) y
[páginas](https://www.lidl.es/explore/assets/s/pages_es-ES_es.xml.gz).
Lectura HTTP y XML directa: 6.622 URLs de producto y 1.071 páginas. No equivalen
a 6.622 productos alimentarios. El filtro léxico mostró aparatos al buscar leche.

[Sondey, ficha observada](https://www.lidl.es/p/sondey-galletas-rellenas/p11000174):
nombre/marca/descripción e imágenes; no precio visible en lectura realizada.
[Categoría lácteos del sitemap](https://www.lidl.es/h/lacteos-quesos-y-huevos/h10095761):
404 comprobado. [Alimentación](https://www.lidl.es/c/alimentacion/s10068374):
mensaje sin ofertas en la lectura. [Folletos](https://www.lidl.es/c/descubre-nuevas-ofertas-cada-semana-folletos-lidl/s10087402)
describe surtido fijo y promociones temporales; el folleto no enumera necesariamente
todo el surtido. Conclusión: ampliar descubrimiento sí; afirmar cobertura total no.

No hay una prueba de que el surtido completo con precios de tienda esté accesible
públicamente. No hay tampoco justificación para dar el trabajo por cerrado en 76
ofertas. El siguiente agente debe implementar y medir el recorrido adicional
descrito en SUPERAPP-02, con las restricciones de acceso observadas.

## v0 y Stitch: uso real y ahorro de cuota

Se usó una petición v0-mini, solo dirección escrita, sin archivos, imágenes ni
herramientas externas. [Sesión privada v0](https://v0.app/chat/iKZwK5exGHM).
Resultado: archivo doméstico editorial, fondo marfil, bosque, terracota, serif
corta + sans para datos, menú lateral de 248 px, tres composiciones independientes.
El agente aumentó tamaños pequeños y oscureció texto auxiliar para legibilidad.
No hay precio/coste de API verificado en la respuesta; no afirmar consumo cero.

Proyecto privado creado en Stitch: `10604576992569971315`, título
«Cesta - Tres aplicaciones - 2026-10-07».
La solicitud inicial conjunta agotó 180 s y dos consultas posteriores devolvieron
vacío. Después se generó una pantalla por petición, con resultado HTTP 200 para
las tres. Los prompts y respuestas están en `.stitch/`, sin credenciales. Las
capturas y HTML se descargaron y las tres capturas se revisaron visualmente.

| Aplicación | Pantalla Stitch | Referencia visual local |
|---|---|---|
| Compra | `e7344b6c6ab8484aab900a583811ecf3` | [Compra](../.stitch/compra-2026-10-07.png) |
| Recetas | `1e78ec12b1c0458bb68f8a9f7b2aeed9` | [Recetas](../.stitch/recetas-2026-10-07.png) |
| Calorías | `50cfc7cfbc874d85bd7cb57ad4cca188` | [Calorías](../.stitch/calorias-2026-10-07.png) |

Cada identificador pertenece a `projects/10604576992569971315/screens/`.
Los prompts individuales son `compra-2026-10-07.json`,
`recetas-2026-10-07.json` y `calorias-2026-10-07.json` en `.stitch/prompts/`.
Las respuestas completas son los archivos `*-generation-2026-10-07.json`.
El diseño anterior de septiembre permanece como registro histórico.

### Correcciones obligatorias al portar las referencias

El documento SUPERAPP-01 fija los componentes y reglas definitivos. La imagen
generada no sustituye ese contrato ni demuestra funcionalidad o accesibilidad.

- Conservar la composición editorial, la identidad bosque/marfil y los tres
  destinos laterales. Aplicar los colores y tamaños contrastados de SUPERAPP-01;
  Stitch introdujo variantes y etiquetas pequeñas que no se aceptan automáticamente.
- Compra: corregir el panel derecho que queda cortado en la referencia reducida.
  Usar lenguaje cotidiano: «Mi lista», «Tiendas» y «Total estimado», evitando
  «gasto provisionado», «referencia mercantil» y «distribuidores».
- Compra: eliminar afirmaciones ficticias de auditoría de tickets, comprobación
  física y producto exacto verificado. Mostrar identidad y fecha solo cuando haya
  evidencia propia; precio ausente no significa sin stock. Escribir DIA correctamente.
  Las promociones requieren las cantidades, condiciones y cálculo de SUPERAPP-02.
- Recetas: la separación entre biblioteca, ingredientes y pasos funciona como
  referencia. Medir ancho, tamaños y foco en la aplicación real. «Preparar lista»
  abre una propuesta que se confirma expresamente; no añade productos por sí sola.
  Cambiar raciones exige escalar unidades y recalcular la cobertura nutricional.
- Calorías: conservar el subtotal conocido y el día sin datos como hueco. Mostrar
  «Calorías conocidas» cuando falte nutrición, con su cobertura; no presentar el
  subtotal como la ingesta completa. La captura contiene fechas y cifras de ejemplo.
  Objetivos, botones y acceso privado necesitan implementación y pruebas propias.
- Las tres referencias son de escritorio. No hay nueva maqueta móvil generada;
  verificar el diseño implementado a 390 y 768 px, zoom 200 % y con teclado.
- El HTML descargado usa recursos externos y código en línea. Portar componentes
  al proyecto y servir recursos locales conforme a la CSP; no pegarlo en producción.

No se hicieron más llamadas a v0. No se repitió ninguna generación después de
obtener las tres pantallas. Si otra petición agota el tiempo, consultar el proyecto
antes de repetir: un timeout no demuestra que el servidor haya dejado de generar.

Documentación consultada: [v0 creación de chat](https://v0.app/docs/api/v1/reference/chats/create)
y [SDK oficial Stitch](https://github.com/google-labs-code/stitch-sdk).
Se descubrieron herramientas y schemas desde el MCP real; no se instaló otro
framework ni un plugin. `scripts/design_probe.py` es solo ayuda de investigación:
credencial por stdin, sin reintentos de generación y sin integración en runtime.

Las claves facilitadas por el usuario no se guardan en ficheros. Revocarlas y
renovarlas fuera del repositorio; no pegarlas en prompts a modelos ni documentos.
Solo se transmitió al proveedor un brief sintético de diseño, no catálogo,
diarios, cuentas ni datos personales del usuario.

## Límites de esta entrega

Estos documentos y los artefactos de diseño son el resultado solicitado para el
siguiente agente. No se reescribió hoy la suite, no se recorrieron todas las fichas,
no se activó Lidl completo y no se desplegó nada. La batería de 1.195 pruebas
corresponde al cierre previo; esta investigación no añade esa prueba a funcionalidades
futuras. El siguiente agente debe ejecutar la aceptación de cada paquete.
