# Ampliación: catálogo relevante, fichas completas, Lidl y comparación automática

Medido y escrito el **6 de octubre de 2026**. Complementa el plan T01–T10; no lo sustituye.
Para el agente que está implementando: se han añadido dos instrumentos independientes y sus
pruebas. No se han cambiado colectores existentes, grupos, datos, listas, Docker ni la pasada diaria.

## 1. ¿Es suficiente el recorte?

No se decide por tener menos filas que Mercadona. Una cadena puede tener más marcas, sabores,
formatos y especialidades dentro de alimentación. No hay que recortar productos válidos hasta
alcanzar un número arbitrario. Sí hay que eliminar bazar y evitar repetir descargas innecesarias.

La ejecución de `projects.cesta.revisar_alcance` sobre gold da:

| Cadena | Filas | Incluidas | Excluidas por política | En revisión |
|---|---:|---:|---:|---:|
| Alcampo | 23.019 | 21.805 | 0 | 1.214 |
| Carrefour | 15.942 | 15.887 | 54 | 1 |
| DIA | 5.842 | 5.402 | 54 | 386 |
| Mercadona | 4.320 | 3.856 | 65 | 399 |
| Aldi | 2.536 | 1.873 | 51 | 612 |
| Total | 51.659 | 48.823 | 224 | 2.612 |

Son clasificaciones de registros que **siguen en gold**, no una prueba de que la API los oculte.
Tampoco son etiquetas de verdad revisadas independientemente. Cero excluidos en Alcampo significa
cero detectados por esta política, no ausencia demostrada de bazar.

### Contraejemplos al «control de seguridad a cero»

La misma ejecución declara cero, pero muestra:

- Aldi: «Barrita proteica sabor brownie», excluida por categoría `parafarmacia`.
- Carrefour: «Absorbeolores frigorífico XL Croc Odor 140 g.», excluido como electrónica por
  la palabra `frigorifico`.
- DIA: una bolsa de basura para cubo alto, excluida por `cubo de basura`.
- Aldi: «Botas de trekking» sin categoría quedan en revisión, no fuera.

**Conclusión: T01 no está cerrado.** La comprobación actual no detecta todos los falsos descartes.
En `core/alcance.py`, `_casa` exige palabras presentes, no una frase contigua: las palabras
«bolsa de basura ... cubo» pueden activar «cubo de basura». Además, la categoría excluyente se
resuelve antes que las inclusiones de producto. No generalizar «anteponer todas las inclusiones»:
un juguete que mencione comida podría entrar por error.

Trabajo inmediato para quien integra T01:

1. Añadir esos cuatro casos reales como regresiones, junto con sus negativos: frigorífico real,
   cubo real, suplemento no alimentario y calzado. Comprobar producto principal frente a uso
   («limpiador para horno» no es un horno), con reglas específicas explicables.
2. Crear un banco de verdad independiente del vocabulario del clasificador y del control.
   Muestrear incluidos, excluidos y revisión por cadena/familia; guardar IDs, etiquetas y motivos.
   Medir falsos descartes y bazar aceptado por separado, con tamaño de muestra.
3. Aplicar política al recorrido y a la publicación/consulta con estados explícitos; conservar
   histórico. En revisión no se recomienda automáticamente ni desaparece sin explicación.
4. Completar DIA/Mercadona/Aldi y filtro final Carrefour. Medir peticiones realmente evitadas,
   no inferirlas restando filas de dos días con distinta disponibilidad.
5. Para Aldi, combinar menú de categorías con caché de clasificación por ID/variante y hash.
   Sitemap sirve para descubrir IDs nuevos; no obliga a pedir de nuevo cada detalle cada día.
   Identidad desconocida se sondea con presupuesto; lo clasificado se revisa con caducidad.

## 2. Qué datos de composición llegan hoy a la aplicación

Medido por el nuevo `projects.cesta.laboratorio_comparacion`, leyendo gold sin modificarlo:

| Cadena | Ingredientes presentes | Tabla nutricional presente | Tabla numérica con base 100 g/ml |
|---|---:|---:|---:|
| Alcampo | 0 | 0 | 0 |
| Carrefour | 0 | 0 | 0 |
| Aldi | 0 | 0 | 0 |
| DIA | 4.402 | 3.940 | 3.269 |
| Mercadona | 2.756 | 0 | 0 |

Presencia no certifica exactitud; la última columna exige al menos un valor numérico no negativo
y base reconocida, pero no certifica calorías completas. Tampoco esta tabla demuestra que las
webs no publiquen esos campos: puede faltar pedir la ficha, parsearla o propagarla a gold.
Nutri-Score o NOVA no equivalen a una tabla nutricional.

### T11 — Ficha de producto completa e incremental (nuevo paquete)

Dependencia: contrato de procedencia T02; integración con identidad T03. Antes de programar nuevos
endpoints, revisar `auditar_crudo.py`, `rehacer_maestro.py`, colectores y `core/schemas.py`.

**Alcance:** todos los datos de producto publicados y accesibles: denominación, descripción,
marca/fabricante, GTIN, variantes, ingredientes, alérgenos y trazas por separado, nutrientes,
base nutricional, ración y su masa/volumen, pesos neto/escurrido, piezas, envase, origen,
conservación, preparación, certificaciones y advertencias. Para limpieza: composición y uso,
no una falsa tabla alimentaria. Conservar campos adicionales en un objeto de extensión.
No recoger credenciales, cookies personales ni rastreadores publicitarios como datos de producto.

**Secuencia concreta:**

1. Matriz por fuente/campo: publicado y extraído / publicado no extraído / no localizado en la
   muestra / no aplicable / fallo de extracción. No convertir todos estos estados en `null` sin motivo.
2. Muestra estratificada de fichas incluidas: familias, marca propia/nacional, con/sin EAN y
   distintas presentaciones. Comparar respuesta cruda, ficha visible y registros finales.
   Contar que una palabra aparece en HTML no prueba que haya una tabla del producto.
3. Reutilizar respuestas ya guardadas. Si hace falta red, presupuesto configurable por fuente,
   pausa ante 429/bloqueo, reanudación y límites de tiempo. No recorrer otra vez bazar.
4. Separar frecuencia de precio y ficha: precios diarios donde sea viable; ficha al descubrir,
   ante cambio de hash/variante, por caducidad y muestreo de control. Ingredientes y EAN pueden
   cambiar: no tratar el maestro como «una descarga para siempre».
5. Prioridad: favoritos/listas, nuevos incluidos, fichas incompletas, revisiones vencidas;
   reservar cuota para el resto del catálogo para evitar abandono permanente.
6. Guardar evidencia versionada: URL, fecha, región/canal, hash de respuesta, versión de parser,
   ruta JSON/selector, texto original, valor/unidad normalizados y motivo de ausencia.
   Diferenciar precio capturado hoy de ingredientes observados hace semanas.
7. Conservar snapshots útiles de ficha más allá de la caché raw de 30 días según política de
   retención y espacio; deduplicar por hash. No depender de una caché borrable para auditar un dato.
8. Pruebas con fixtures: coma decimal, kJ/kcal, porción sin peso, 100 ml frente a 100 g, cero real,
   nutrientes ausentes, receta nueva, campo adicional desconocido, ficha retirada y error de red.
   Comparar cobertura raw → bronze → silver → gold para detectar pérdidas de columnas.

**Aceptación:** informe de cobertura por campo y familia aplicable, errores explícitos, pruebas
de propagación y de no sustitución de un valor bueno por un fallo temporal. No prometer «todo
mañana»: ejecutar un primer lote y medir ritmo, cobertura y restricciones antes de dar plazo.

## 3. Lidl: se ha encontrado una vía pública que contradice el descarte anterior

El 6 de octubre se descargó con HTTP 200 la página oficial de
[ofertas semanales](https://www.lidl.es/c/ofertas-semanales/a10089449).
Su HTML contiene objetos JSON en atributos `data-grid-data`: **76 fichas/variantes, 70 IDs padre**,
todas esas fichas con `regionsPrices`. Es una muestra de una página, no el catálogo completo.
La extracción textual del buscador no mostraba esos objetos; no hay que confundir esa limitación
con ausencia de datos en la respuesta HTML.

Se ha implementado y probado `projects/cesta/sondear_lidl.py`:

- Lector offline de HTML y modo de sondeo web explícito. El modo web consulta primero
  [robots.txt](https://www.lidl.es/robots.txt) y una sola página; no usa API móvil ni login.
- Conserva el JSON completo al parsear, separa `productId` de `variantId` y no inventa EAN a partir
  de `ians` o IDs internos. Se encontraron kéfires de sabores distintos bajo un mismo padre.
- Resuelve `regionsV2[region].regionPriceId` antes de consultar `regionsPrices`.
  No elige el menor precio entre regiones ni confunde ID de región con código postal.
- Conserva `currentPrice` y `currentLidlPlusPrice` con fechas y condiciones. En la muestra,
  la región 28 corresponde a Madrid; es prueba técnica, no configuración del hogar del usuario.
- Cero fichas, JSON roto o duplicados contradictorios fallan explícitamente.

**Todavía no publica Lidl en la app ni en bronze.** El CLI muestra un resumen; `extraer` devuelve
los objetos completos para que el futuro colector los persista con el almacenamiento del proyecto.

### T12 — Integrar Lidl con cobertura parcial explícita

1. Incorporar lector al colector, almacenar raw por los mecanismos existentes y aplicar alcance.
2. Configurar zona real; oferta debe tener fecha/condiciones interpretables. Precio antiguo
   tachado no es automáticamente un precio normal vigente. Región publicada no certifica stock.
3. Mantener variante estable y URL; comprobar qué campos adicionales publica su ficha pública.
4. Descubrir las campañas vigentes desde navegación permitida con presupuesto y deduplicación.
   No rastrear bricolaje para conseguir un número grande. No usar páginas antiguas de buscador
   como ofertas actuales ni endpoints móviles no verificados como dependencia principal.
5. Mostrar «ofertas conocidas de Lidl», no «catálogo completo de Lidl». No declarar Lidl ganador
   de una cesta si faltan productos ni interpretar ausencia en campaña como retirada definitiva.
6. Añadir fixtures fechados y tests de expiración, región, club, variantes y catálogo vacío;
   pasar una captura acotada antes de añadirlo a la tarea diaria.

## 4. Comparaciones automáticas: algoritmo e integración

Se ha implementado un **laboratorio de diagnóstico**, no el sustituto de producción de T03:
`projects/cesta/laboratorio_comparacion.py`. Evalúa automáticamente los pares entre cadenas de
los grupos existentes y los recuperados por GTIN incluso si están en grupos separados.

En este catálogo evaluó **17.549 pares**: 10.999 con alguna contradicción, 4.901 sin evidencia
suficiente, 1.014 candidatos por GTIN con formato comprobable, 237 con GTIN coincidente sin
formato verificable y 398 de códigos distintos sin otra contradicción detectada.

**No son 10.999 errores demostrados**: marcas diferentes son válidas como alternativas, y las
variaciones de escritura pueden generar alertas conservadoras. No confundir pares con grupos.
Los 1.014 candidatos tampoco son 1.014 identidades certificadas. La estructura GTIN no prueba
asignación válida ni ausencia de códigos internos. Este instrumento no altera listas ni grupos.

### Algoritmo de producción requerido para T03

1. **Normalizar sin borrar diferencias:** marca y alias documentados, magnitud y unidad,
   presentación/piezas, variante, estado fresco/congelado, receta y atributos específicos de
   familia. Mantener texto original; no eliminar «sin» de las restricciones.
2. **Generar candidatos por varias vías:** índice GTIN, marca+familia+formato, tokens raros y
   similitud de caracteres; opcionalmente embeddings locales para recuperar nombres distintos.
   Los índices evitan comparar todo contra todo. Medir recall de esta etapa separadamente.
3. **Vetar contradicciones:** distinta marca, especie, corte, receta, talla, cantidad o pack
   impiden identidad exacta salvo evidencia explícita de error de origen corregido. No son veto
   universal a una alternativa elegida por el usuario. Atributo ausente no confirma igualdad.
4. **Decidir con evidencia:** GTIN validado y procedencia adecuada + presentación compatible
   habilita vía fuerte; códigos distintos necesitan alias documentado. Sin GTIN, modelo
   probabilístico supervisado con atributos y texto, calibrado por familia y con abstención.
   No publicar automáticamente basándose solo en una similitud arbitraria de nombre.
5. **Evitar fusiones transitivas:** A≈B y B≈C no implica A=C. Validar cada nuevo miembro contra
   restricciones de todo el grupo exacto; mantener propuestas y alternativas aparte.
6. **Aprender de revisiones pequeñas:** muestreo estratificado y casos de incertidumbre/conflicto,
   no obligar al dueño a emparejar cada producto. Las decisiones revisadas se reutilizan mientras
   no cambie presentación. La muestra de evaluación queda separada por identidad de entrenamiento.
7. **Medir:** precisión de identidad, recall de candidatos, cobertura automática, abstención y
   errores por familia/cadena, incluidos negativos difíciles. Etiquetas generadas por el mismo
   algoritmo no sirven como verdad. El 57 % anterior no equivale a precisión de identidad.
8. **Publicar en sombra primero:** comparar resultado nuevo y antiguo, revisar cambios de listas,
   luego migración T04 y selector T05. No reutilizar `grupo_id` como identidad certificada.

GTIN: referencias primarias de [longitudes y representación](https://support.gs1.org/support/solutions/articles/43000734386-are-all-gtins-unique-numbers-)
y [dígito de control](https://www.gs1.org/services/check-digit-calculator).

## 5. Recetas y nutrición: preparar el dato sin confundir compra con consumo

Una receta debe expresar ingrediente genérico + cantidad/unidad + preparación y restricciones.
La persona vincula una opción compatible, no necesariamente una marca idéntica. Escalar raciones,
restar despensa confirmada y redondear a envases comprables; explicar sobrantes y conversiones.

Para calcular nutrientes: cantidad comestible en g o ml × valor por 100 / 100. No convertir
litros a kilos sin densidad documentada; no mezclar crudo/cocinado, peso escurrido/neto ni porción
sin tamaño. Sumar solo campos conocidos y mostrar cobertura; lo desconocido no aporta cero.
Calorías compradas, preparadas y consumidas son magnitudes distintas. Un detergente no entra en
el denominador de cobertura nutricional. «No declara alérgenos» no significa seguro para alergias.

Primera entrega futura: importación de receta estructurada, escalado y generación de lista con
confirmación, antes de OCR o generación automática. Tests de cantidades, conversiones y faltantes.
No crear recomendaciones médicas ni una nota universal de salud con pesos inventados.

## 6. Aprendizaje y verificación

Nuevo capítulo: [16 · De un catálogo grande a datos útiles](aprende/16-catalogo-fichas-identidad.md).
Cada entrega de T01–T12 debe aportar: problema, evidencia cruda anonimizada, transformación,
algoritmo explicado, prueba reproducible, métricas fechadas y limitaciones. Mantener separados
«implementado», «medido» y «propuesto». La documentación forma parte de la entrega, no es opcional.

Comprobaciones añadidas (sin red):

    uv run pytest tests/test_laboratorio_comparacion.py tests/test_sondear_lidl.py -q
    uv run python -m projects.cesta.laboratorio_comparacion

Sondeo de red explícito, no tarea diaria:

    uv run python -m projects.cesta.sondear_lidl --web --region 28

En esta entrega: **21 pruebas nuevas pasan**, revisión estática de los dos instrumentos y tests
sin errores. Suite completa: **1.118 pruebas pasan**, con dos avisos de deprecación de dependencias.
La primera pasada detectó una sección desconocida en la cabecera del capítulo nuevo; se corrigió,
se repitieron las 20 pruebas del curso y después la suite completa con el resultado anterior.
Verificador documental correcto y sitio didáctico generado en una carpeta temporal, sin reemplazar
la web activa. Esto no certifica los recorridos de la aplicación con Docker apagado. No se ha
corrido la ingesta masiva ni se han publicado datos de Lidl. T11/T12 y T03 siguen pendientes de integración.
