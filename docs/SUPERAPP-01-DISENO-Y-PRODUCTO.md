# Diseño de producto: tres aplicaciones, una casa

Especificación del 7 de octubre. Dirección v0 revisada por el agente; desarrollo
visual en Stitch. No copiar marcas, activos ni pantallas pixel a pixel de terceros.

## 1. Identidad: archivo doméstico, no panel genérico

Una mezcla de libro de cocina y cuaderno de cuentas: títulos editoriales breves,
tablas nítidas, superficies de papel, separadores y números protagonistas. Evitar
gradientes, cristal, hero gigante, iconos de IA y cuadrículas de tarjetas sin razón.
La personalidad surge de jerarquía, lenguaje y comportamiento; no de decorar cada dato.

| Token | Valor | Uso |
|---|---|---|
| fondo | `#F4F0E8` | lienzo cálido |
| papel | `#FBF9F4` | formularios y superficies |
| bosque | `#183A32` | navegación y acción principal |
| tinta | `#202724` | texto principal |
| secundaria | `#536158` | texto auxiliar, más oscuro que propuesta v0 |
| terracota | `#A94D36` | acento de marca y sección activa |
| borde | `#D8D2C7` | reglas no esenciales; bordes de controles deben reforzarse si no contrastan |
| aviso | `#805500` | dato incompleto, siempre con texto |
| error | `#A12626` | operación fallida, no juicio sobre comida |

Fraunces 600 para títulos cortos; IBM Plex Sans 400/500/600 para interfaz y datos.
Servir WOFF2 local con licencia incluida; fallback Georgia/system-ui si falta.
Nada de Google Fonts/CDN en ejecución. Cuerpo 16/24 px, tablas 14/22,
metadatos mínimo 13/18; H1 32/38 escritorio y 28/34 móvil. Cifras tabulares.
v0 sugirió 11 px en etiquetas: **rechazado por legibilidad**. Espaciado 4/8/12/16/24/32/48.
Radio 6–10 px; sombra solo en capas flotantes. Iconos coherentes con etiqueta,
no emojis como sistema de navegación. Verificar contraste en ambos temas antes
de publicar; estos valores son propuesta, no auditoría WCAG completada.

Medición sRGB del 7 de octubre: tinta/fondo **13,42:1**, secundaria/fondo
**5,74:1**, papel/bosque **11,81:1**, terracota/fondo **4,86:1**. El borde suave
contra papel solo da **1,43:1**: usarlo para separación decorativa, NO como única
delimitación de un input; usar secundaria/bosque o borde reforzado para controles.
Esto valida esas parejas, no todos los estados de una aplicación aún no construida.

## 2. Armazón y rutas

```text
Cesta (suite)
├─ Compra /compra
│  ├─ Buscar /compra/buscar
│  ├─ Listas /compra/listas/:id
│  ├─ Favoritos /compra/favoritos
│  ├─ Producto /compra/productos/:id
│  ├─ Comparar /compra/comparar/:identidad
│  └─ Gasto y ahorro /compra/analisis
├─ Recetas /recetas
│  ├─ Mi recetario /recetas/biblioteca
│  ├─ Receta y editor /recetas/:id
│  ├─ Cocinar /recetas/:id/cocinar
│  └─ Plan semanal /recetas/plan
├─ Calorías /calorias
│  ├─ Mi diario /calorias/diario?fecha=YYYY-MM-DD
│  ├─ Mis alimentos /calorias/alimentos
│  └─ Tendencias /calorias/tendencias
└─ Cuenta · Hogar · Preferencias · Aprender
```

Sidebar 248 px desde 1024 px; contenido ancho máximo 1280, márgenes24–40.
Las tres aplicaciones siempre visibles; subsecciones solo de la activa. En móvil,
botón «Menú» de 44×44 abre drawer 288 px, foco atrapado, Escape cierra y devuelve
foco; fondo inerte. Mostrar nombre de aplicación y título actual incluso cerrado.
Cada app puede tener hasta cuatro acciones móviles propias; nunca la barra de
Compra debajo de Calorías. No tres miniapps incrustadas en un dashboard común.

`/` es lanzador sobrio con tres accesos y «continuar donde estaba», sin mezclar
gráficas ni consultas privadas. Migrar rutas antiguas con alias/redirecciones y
parámetros conservados; no romper enlaces de escáner o invitaciones.
Carga diferida por aplicación. CompraLayout conoce fecha de precios; RecetasLayout
y CaloriasLayout no piden estado de supermercados para poder renderizar.
Eliminar el `Cocina` compartido con un `modo` como arquitectura definitiva.
Compartir funciones puras de nutrición, no el único borrador global de receta.
Separar claves de caché por usuario/hogar/módulo y vaciarlas al cerrar sesión.

Componentes: SuiteSidebar, ModuleHeader, SearchField, FilterBar, ProductRow,
PriceCell, IdentityBadge, CoverageNotice, RecipeCard, ServingControl, DiaryRow,
ChartWithTable, EmptyState, ErrorState, SaveStatus y ConfirmationSheet.
Botones «Comparar», «Preparar lista», «Registrar comida»: verbos distintos.

## 3. Compra: contratos de pantalla

- **Buscar:** búsqueda por título/marca/código/categoría, filtros pertinentes,
  sin obligar a seleccionar cadena. Resultado agrupa solo identidad verificada;
  otros artículos siguen visibles como resultados separados. Marca, variante,
  contenido, precio/envase y €/unidad visibles; fecha y ámbito al desplegar.
- **Ficha:** identidad estable, variantes sin ocultarlas, ingredientes/nutrición,
  especificaciones y procedencia. Acción exacta «Añadir este producto»; alternativa
  separada y nombrada. Comparación en filas: cadena, formato, coste pagado hoy,
  unidad, condiciones, fecha y disponibilidad. Producto sin precio no gana ranking.
- **Lista:** necesidades, cantidades, elegido, comprado y deshacer. Favorito no
  implica necesidad; comprado no se elimina del histórico ni se consume solo.
  Modo tienda permite tachar sin red y sincroniza después con idempotencia.
- **Reparto:** misma cesta y cantidades; una tienda o máximo dos por defecto.
  Mostrar faltantes antes del ahorro. Coste de desplazamiento opcional explícito,
  no inventar kilómetros ni gastos. Club desactivado hasta que el usuario lo elija.
- **Analítica:** gasto confirmado frente a estimado, histórico de artículo exacto,
  ahorro simulado frente a tienda base sobre las mismas líneas. Nunca comparar una
  cesta completa con otra incompleta y llamar ahorro a la diferencia.

## 4. Recetas: aplicación completa, no calculadora con nombre

Biblioteca persistente, categorías propias, favoritos, búsqueda por ingrediente,
tiempo y raciones; listas vacías útiles. Crear/editar/duplicar/archivar/exportar.
Editor con nombre, autor/fuente, notas, ingredientes estructurados, medidas,
preparación/cocción, pasos y temporizadores. Fotografías propias o con permiso;
sin foto, composición tipográfica cuidada, no imagen falsa de la receta.

Detalle: título y tiempos arriba; en desktop ingredientes izquierda, pasos derecha;
en móvil pestañas accesibles o secciones consecutivas. Escalador visible, tachado
de ingredientes solo en sesión de cocina, paso activo y temporizadores recuperables.
Mantener pantalla despierta solo por acción de cocinar y si navegador lo permite.
No redondear 0,5 huevos a cero; presentar fracciones prácticas y avisar de ajustes.

Planificador por semana y comida, mover con botones además de arrastrar, repetir
menú y generar lista propuesta. «Preparar lista» abre revisión de raciones,
despensa opcional, ingredientes, productos elegidos, envases y sobrantes.
Agrupar solo ingrediente+estado+unidad compatibles, nunca por parecido de nombre.
Confirmar destino antes de escribir en Compra; una repetición con misma clave no duplica.

Importación de URL es fase posterior a editor funcional: Recipe JSON-LD cuando
permitido, conservar atribución, revisión antes de guardar, sanitizar HTML y
proteger contra SSRF, red privada, redirecciones abusivas y respuestas gigantes.
No construir un catálogo republicado de recetas ajenas sin permiso.

Nutrición y coste opcionales con cobertura; no bloquear receta de verduras por
faltar vitaminas. Un plan de comidas no crea entradas de consumo. «He comido»
propone fecha/comida/ración y pide confirmación en Calorías.

## 5. Calorías: diario independiente y privado

Hoy con anterior/siguiente/calendario; desayuno/comida/cena/otros, añadir alimento
desde catálogo, personal o receta guardada, cantidad y unidad verificable. Recientes,
favoritos personales, copiar comida a otra fecha, editar, deshacer, exportar y borrar.
La fecha de consumo es local; captura de producto es otra fecha. Congelar valores
y versión de receta en cada apunte. Cambiar etiqueta o receta no reescribe el pasado.

Resumen energético y macros del consumo **registrado**, no de la compra. Mostrar
«subtotal conocido» y entradas incompletas; cero real no es ausencia. Hidratación
manual opcional; sin ejercicios, biometría clínica, dietas automáticas ni objetivos
de pérdida de peso en esta entrega. Objetivos personales opcionales posteriores,
sin valor calórico universal precargado ni anillos rojos de culpabilidad.

Datos compartidos de producto no hacen compartido el diario. Invitación al hogar
no concede acceso a calorías, notas o hábitos; comprobar API, no solo ocultar menú.

## 6. Gráficas útiles y verificables

| App | Pregunta | Visual | Regla de datos |
|---|---|---|---|
| Compra | ¿Cuánto cambió este artículo? | líneas/steps por cadena | mismo artículo y unidad; huecos por falta de captura |
| Compra | ¿Dónde compro esta lista? | barras de coste y faltantes | universo y cantidades idénticos; club explícito |
| Compra | ¿En qué gasté? | barras apiladas por semana/categoría | compras confirmadas, reembolsos identificados |
| Recetas | ¿Qué tengo planificado? | calendario semanal | planificación, no consumo |
| Recetas | ¿Cuánto costaría esta receta? | desglose ingredientes | coste usado y desembolso de envases separados |
| Calorías | ¿Qué anoté esta semana? | barras diarias kcal | sin apunte = hueco; parcial = patrón/etiqueta |
| Calorías | ¿Qué nutrientes conozco? | barras horizontales en gramos | cada nutriente con cobertura, no 100 % ficticio |

Sin 3D, doble eje confuso o pastel con 20 segmentos. Unidades, periodo, fuente,
tabla accesible y exportación. Tooltip usable con teclado/táctil. Colores no únicos
para distinguir series; etiquetas o patrones. No unir períodos incompatibles tras
cambiar peso/pack. No inferir salud de una gráfica ni «ahorro» sin contrafactual definido.

## 7. Revisión de maquetas antes de integrar

Stitch es referencia, no código listo para producción. Corregir cifras, contraste,
etiquetas, formato español y estados de error; reemplazar datos ficticios por API.
Nada de CDNs, scripts inline o estilos que debiliten CSP. No introducir librerías
masivas por copiar una pantalla. Conservar tablas reales y fuentes locales.
Probar 360/390/768/1440 px y zoom 200: no scroll horizontal global, controles 44px,
foco visible y nombre accesible. Tablas extensas pueden desplazarse en su propio
contenedor. Fallo de Compra no debe vaciar Recetas o Calorías.

## 8. Contratos de comportamiento para implementar sin ambigüedad

Entidades propuestas (modelo lógico, adaptar a las migraciones actuales):

- `Recipe`: ID estable, propietario, visibilidad, título, estado archivado.
- `RecipeVersion`: revisión inmutable, raciones, pasos, tiempos, fuente y fecha.
- `RecipeIngredient`: orden, texto original, ingrediente genérico, cantidad,
  unidad, estado crudo/cocido y vínculo opcional a producto exacto/versionado.
- `MealPlanEntry`: día/comida/raciones y versión de receta; no es consumo.
- `DiaryEntry`: propietario personal, fecha local, comida, cantidad/unidad,
  snapshot de nutrientes y origen, revisión y clave idempotente.
- `ShoppingProposal`: destino, ingredientes, disponibilidad en despensa declarada,
  elección comercial, envases, sobrantes, coste y consentimiento a alternativas.

Servicios orientativos: listar/crear/editar/versionar recetas; planificar; calcular
propuesta de compra sin escribir; confirmar propuesta; anotar/editar/deshacer
consumo; consultar resumen por periodo. Especificar DTO y permisos antes de UI.
Mutaciones con versión esperada para detectar edición simultánea; conflicto 409
con opción de recargar/revisar, no sobrescritura silenciosa. Sincronización offline
solo de operaciones conocidas y pendientes visibles; nunca inventar éxito del servidor.

Todos los importes de dinero en céntimos enteros; cantidades con precisión
declarada. Fechas de diario `YYYY-MM-DD` en zona personal; captura UTC con zona
de presentación. Campo ausente y cero tienen representaciones distintas.
Datos de demostración aislados del almacenamiento real y claramente etiquetados.

Casos de aceptación con resultados esperados:

1. Receta de dos raciones con 200 g a 350 kcal/100g: 700 kcal total, 350 por ración;
   duplicar raciones de preparación duplica ingredientes, no kcal por ración.
2. Añadir un ingrediente sin kcal: conservar subtotal y marcar incompleto; no
   dibujar total cerrado ni ocultar la fila. Grasa 0 declarada permanece 0.
3. Dos personas del mismo hogar: comparten lista autorizada, no diario. Intentar
   acceder directamente al ID ajeno devuelve rechazo sin revelar datos.
4. Confirmar compra propuesta dos veces con la misma clave: una operación, no dos
   listas. Cambiar raciones genera revisión explícita, no una segunda copia muda.
5. Consumir receta V1 y luego editar a V2: la entrada histórica sigue usando V1.
6. Harina 500 g requerida y envase 1 kg: coste de ingrediente usado y desembolso del
   envase distintos; 500 g sobrantes. No considerar sobrante consumido automáticamente.
7. URL antigua de producto: llega a Compra conservando ID. Navegar a Calorías no
   muestra estado de supermercados ni conserva selección de carrito como comida.
8. Diario vacío: mensaje y botón Añadir; gráfica muestra sin registros. Día
   parcialmente anotado no se interpreta como ayuno ni se incluye como cero
   en una media semanal. Mostrar denominador de días/entradas disponibles.
