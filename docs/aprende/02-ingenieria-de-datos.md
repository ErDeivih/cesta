---
seccion: Ingeniería de datos
resumen: Capas, Parquet, DuckDB y Polars, idempotencia, calidad, coste y privacidad.
---

# 02 · Ingeniería de datos: capas, formatos, motores y la cadena diaria

Este capítulo es la parte de ingeniería del proyecto: cómo entra el dato, por dónde pasa y
cómo se guarda. Es la mitad del oficio que no se ve en un notebook y que decide si un
proyecto aguanta seis meses.

## 1. Las capas: bronce, plata y oro

La idea de las capas (la llamó *medallion* Databricks) es sencilla y no tiene nada que ver con
las herramientas: **cada capa tiene una responsabilidad y se puede reconstruir desde la
anterior**:

    raw      lo que devolvio la web, tal cual. Inmutable. Es lo unico que no se puede
             recuperar si se pierde.
    bronze   parquet sin tocar: mismo dato, legible y comprimido.
    silver   limpio, tipado y normalizado: unidades canonicas, precios en centimos enteros,
             campos derivados de la fuente.
    gold     lo que consume la aplicacion: grupos de productos equivalentes, precio por
             unidad, calidades, indices.

En este proyecto son cuatro carpetas y una regla: **es ELT, no ETL.** Se guarda el crudo
primero y se transforma después, con la potencia del motor. Guardar el HTML crudo es lo que
permite reprocesar un día entero **sin volver a golpear la web** — que en un sitio con WAF no
es un detalle de elegancia, es la diferencia entre poder arreglar un parser y no poder.

| | |
|---|---|
| Referencia | *Medallion lakehouse architecture* (Databricks) · [ELT frente a ETL (AWS)](https://docs.aws.amazon.com/whitepapers/latest/data-warehousing-on-aws/data-processing.md) |
| Aquí | `data/raw` → `data/bronze` → `data/silver` → `data/gold` |
| Lo que NO se hace | ni catálogo, ni metastore, ni Delta/Iceberg, ni Kafka: con un escritor y un lector al día, el coste (JVM, mantenimiento) es real y el beneficio marginal |

## 2. El formato: por qué Parquet y cuándo no

Parquet es columnar: guarda y comprime **por columna** y agrupa filas en bloques con
estadísticas min/max, lo que permite dos cosas que se notan mucho: leer solo las columnas que
hacen falta (*projection pushdown*) y saltarse bloques enteros que no pueden contener lo que
se busca (*predicate pushdown*).
[Parquet, explicado](https://airbyte.com/data-engineering-resources/parquet-data-format) ·
[Escritura particionada (DuckDB)](https://www.duckdb.org/docs/current/data/partitioning/partitioned_writes)

Lo que este proyecto aprovecha, con números:

    grupos.parquet        4,5 MB   57.603 filas de 53 columnas
    precio_diario.parquet 9,9 MB  872.650 filas (19 dias x 5 cadenas)
    precio_derivado.parquet 4,7 MB  872.650 filas con 14 columnas calculadas

872.650 filas con 14 columnas en 4,7 MB son unos 5 bytes por valor. Eso es lo que hace que
todo el análisis de este curso se pueda hacer **en un portátil, sin servidor**.

**Cuándo NO usar Parquet**, que es la mitad útil de la pregunta: ficheros diminutos (miles de
ficheros de pocos KB hacen más daño que bien), datos que se reescriben fila a fila, y todo lo
que alguien tenga que leer con `grep` o comparar en un `diff`. CSV y JSON siguen siendo el
formato de intercambio; Arrow es un formato de memoria, no de disco.

## 3. Los motores: DuckDB para consultar, Polars para transformar

Dos herramientas, cada una en su papel:

- **DuckDB** es un motor SQL columnar que lee Parquet directamente y cabe en un proceso. Aquí
  hace todo el SQL de `gold` y de la API. Su límite real es que no es un servidor para mucha
  concurrencia — y eso a este proyecto le da igual: hay un lector. ([Guía de rendimiento](https://duckdb.org/docs/stable/guides/performance/environment))
- **Polars** es una librería de dataframes multihilo, con evaluación perezosa y optimizador.
  Aquí hace las transformaciones de `silver` y del histórico, porque son expresiones que en
  SQL quedarían peor de leer (ventanas por producto, uniones de esquemas, reversiones).
- **Spark no está, y es una decisión.** Añade JVM, arranque y memoria para resolver un
  problema de volumen que este proyecto no tiene. Hay comparativas públicas de motores
  ([TPC-H, DuckDB/Polars/Daft/Spark](https://docs.coiled.io/blog/tpch.html),
  [Polars frente a Spark](https://pola.rs/posts/polars-pyspark-benchmarks/)), y de ellas se
  saca la lección útil: **el motor se elige por el working set, no por el tamaño total**.

El criterio que sí se puede medir aquí, y está medido en `docs/BACKLOG.md`: la pasada del
emparejador tarda **~450 s** con el catálogo entero, y el catálogo cabe en memoria decenas de
veces. Cuando la consulta no quepa, DuckDB empieza a escribir a disco y Polars a hacer
*streaming*: **ese** es el día de mirar el motor, no antes.

## 4. Idempotencia: la propiedad que separa un script de un sistema

Un proceso es **idempotente** cuando ejecutarlo dos veces con la misma entrada deja el mismo
estado. Suena académico y es lo que decide si puedes dormir: una cadena que se puede relanzar
sin miedo se arregla a las 07:00; una que duplica filas, no.

Las tres recetas que se usan aquí, y que son las de la industria:

1. **Particionar por fecha y sobrescribir la partición entera** (`fecha=2026-09-24`), nunca
   hacer `append` sobre el destino. Es exactamente la lógica de las materializaciones
   incrementales de dbt: [About incremental strategy](https://docs.getdbt.com/docs/build/incremental-strategy).
2. **Idempotencia por clave, no por fichero**: al reprocesar un día, se quitan primero las
   filas de ese (cadena, fecha) y se escriben las nuevas. Sin eso, relanzar duplica.
   (`projects/cesta/pipeline.py`, `a_gold()`: *«reejecutar solo reemplaza lo que trae esta
   pasada»*).
3. **Escribir en `_staging/` y renombrar al final**, para que el destino nunca se lea a
   medias.

Y un caso real de este proyecto que ilustra por qué importa: hasta el 18 de septiembre de
2026, `--rehacer-historico` no existía, y al probar la cadena entera sobre una copia limpia el
histórico reconstruido salió con **dos días y 52.000 filas** en vez de los 19 días reales. La
razón: el pipeline se queda a propósito con la instantánea más reciente de cada cadena y **la
añade** al histórico, así que el histórico solo vivía en un parquet que se podía perder. Ahora
se reconstruye día a día desde `bronze` (`docs/OPERACION.md`), y eso convierte una pérdida en
una tarde de CPU.

> **Regla:** todo paso de la cadena tiene que poder correrse dos veces con el mismo resultado.
> Un paso que no cumpla eso no es un paso: es un riesgo que se descubre el día que hay que
> relanzar a las siete de la mañana con la web cambiada.

## 5. La cadena diaria, paso a paso

Todo el sistema corre con **un comando**, disparado por el Programador de tareas a las 06:00
(`ejecutar.bat` → `projects/cesta/run.py`):

    1. las cinco cadenas                     raw: 72.426 ficheros, 2.874 MB acumulados
    2. las fichas maestras nuevas del dia
    3. el pipeline        raw -> bronze -> silver -> gold
    4. el emparejador entre cadenas y las calidades A/B/C
    5. los avisos de precio que hayan saltado
    6. el resumen, las cifras de los documentos y la verificacion de esos documentos

Tres decisiones de ingeniería que están en ese `run.py` y merecen copiarse:

- **Se puede relanzar sin miedo**: cada paso es idempotente, y la marca de «hoy ya está hecho»
  solo se escribe si el día salió bien. Un día fallido se reintenta al siguiente arranque, y
  como el crudo está en caché, cuesta minutos y no horas.
- **Un paso que falla no tumba los siguientes** si su ausencia no es crítica (`avisos`,
  `resumen`, `cifras` van en `try/except` con su aviso), pero **el paso de datos sí**:
  si `pipeline` o `emparejar` fallan, el resumen no se imprime y el código de salida no es 0,
  que es lo que hace que la tarea se marque como fallida.
- **Verifica los documentos**: el último paso comprueba que las cifras escritas en `docs/`
  siguen siendo las de hoy, porque una cifra caducada es peor que ninguna (nadie la vuelve a
  mirar).

## 6. Calidad del dato sin nadie mirando

La regla que este proyecto sigue es: **el dato es válido o va aparte, y nunca se inventa**. No
hay un humano aprobando nada, así que la validez son reglas deterministas con su umbral
escrito:

    precio_unidad_cent > 0            y con unidad canonica (kg, l, m, ud)
    unidad_canonica IS NOT NULL       si no, no hay comparacion posible
    cobertura por cadena              si una cadena trae menos de lo normal, se avisa
    «en disputa» aparte               cuando la cadena se contradice por un factor de 2 o mas

Lo último es un ejemplo que merece la pena contar entero: hay fichas donde **el precio por
unidad que calcula el proyecto y el que publica la propia cadena se contradicen por un factor
de dos o más**. No se elige ganador: la fila se aparta de las comparaciones (`en_disputa`, 72
filas de 52.002, un 0,14 %), se sigue enseñando su precio total y se puede añadir a la lista,
pero **no decide dónde sale más barato algo**. Eso es un contrato de datos en la práctica:
reglas explícitas, cuarentena y nada de silencios.
([Contratos: acuerdo frente a ejecución](https://dlthub.com/blog/data-contracts-agreement-vs-enforcement))

## 7. Observabilidad: cuatro alertas, no cuarenta

La cadena diaria imprime, por paso, cuántas filas han entrado y cuánto ha tardado; y el
resumen del día se guarda. La lección de la industria que aquí se aplica es **alertar sobre
síntomas, no sobre causas**: fallo total, cobertura incompleta, un número de filas fuera del
rango histórico y un dato demasiado viejo. Una ejecución que tardó un poco más y terminó bien
no es una alerta: es ruido, y el ruido entrena a la gente a no mirar.
([SLOs y alertas](https://cloud.google.com/architecture/framework/reliability/slo-and-alerts) ·
[Observabilidad de datos](https://www.ataccama.com/blog/what-is-data-observability))

Ejemplo real de este proyecto que vale por un capítulo: la comprobación diaria avisaba de
«precios malos» cuando la red fallaba, y el aviso era el mismo que el de un día con datos
malos. Se corrigió el criterio: **solo «no aparece» y «404» cuentan** como fallo; un día de
red mala ya no se confunde con un día de precios malos.

## 8. El coste, medido en lo que cuesta de verdad

En una máquina de casa, el coste no son euros de nube: son **segundos de CPU, megabytes y
vatios**. Este proyecto lo mide así:

    emparejar el catalogo entero      ~450 s de CPU
    --medir (recall sobre el banco)   498 s
    una consulta de gold (por pais)    0,1-0,5 s
    la API en caliente                 9-16 ms por peticion

Con esos números, la decisión de ingeniería se vuelve evidente: **no hay nada que optimizar
antes de medir**. Y cuando algo hay que optimizar, se sabe dónde: por ejemplo, el canal de
vectores (190 MB de `embedding.parquet`) costaba 239,9 s y 270 MB de memoria por pasada, y hoy
está **apagado** por una razón que no es el coste (capítulo 10).

## 9. Reproducibilidad: mismo código, misma entrada, mismo resultado

Sin esto, «hemos mejorado un 3 %» no significa nada. Las tres piezas:

1. **El crudo, inmutable** y con su huella (cada captura se guarda tal cual y no se toca).
2. **Medir antes y después sobre el mismo dato**: es la práctica que más veces se repite en
   este material, y la que convierte un cambio en un experimento controlado. Si la entrada
   cambia entre las dos medidas, no sabes qué causó la diferencia.
3. **Dependencias fijadas** (`uv.lock`) y versiones en el propio repositorio.

**Lo que aquí NO se hace, y por qué**: ni DVC ni OpenLineage ni git-lfs. Versionar datos a
esta escala cuesta más que copiar la carpeta, y el linaje ya está escrito en el nombre de las
capas y en los documentos. La herramienta que se adopta es la que resuelve un problema que
tienes, no la que sale en las conferencias.
([OpenLineage](https://openlineage.io/getting-started/) ·
[Guía de DVC](https://datos.gob.es/sites/default/files/documentacion/files/Guia_DVC_en.pdf))

## 10. Privacidad: el dato que no sale de casa

Este proyecto tiene datos personales de verdad (usuarios, listas de la compra, que revelan
hábitos), y por eso la arquitectura es lo que es: **todo corre en el PC**, la base publica su
puerto solo en `127.0.0.1`, y lo único que sale de aquí es lo que piden los móviles de la casa
por una red privada. Los secretos viven en variables de entorno — nunca en el código ni en el
repositorio — y el registro de altas está limitado.
([Principios de protección de datos, ICO](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/data-protection-principles/a-guide-to-the-data-protection-principles/) ·
[Twelve-Factor: config](https://12factor.net/config))

La parte incómoda, que también hay que decir: **los catálogos son públicos** (precios de
supermercado), así que el riesgo real es bajo; lo que no es público es **tu lista de la
compra**, y eso es exactamente lo que nunca sale de la máquina.

## 11. Lo que se aprende en este capítulo

- Capas con responsabilidad clara, y **el crudo inmutable**: es lo único irrecuperable.
- Parquet no es una moda: es lo que permite hacer todo este análisis en un portátil (872.650
  filas con 14 columnas en 4,7 MB).
- La idempotencia no es un lujo: es lo que permite relanzar la cadena sin miedo.
- La calidad del dato son reglas escritas y cuarentena, no buena voluntad.
- Cuatro alertas y un runbook valen más que cuarenta métricas.
- El coste en casa se mide en CPU, MB y vatios, y se mide **antes** de optimizar.

## Antipatrones, con su síntoma

Van con su síntoma porque así se reconocen en un proyecto ajeno en cinco minutos:

| Antipatrón | Síntoma que se ve |
|---|---|
| `append` ciego sin partición | al reprocesar un día, los recuentos se duplican |
| Escribir directo en el destino | tras un corte hay ficheros a medias |
| Un fichero por producto | miles de ficheros diminutos y consultas lentas |
| Dependencias sin fijar | el resultado cambia sin tocar el código |
| Alertar en cada paso | nadie lee los avisos y el fallo real pasa |
| Copias nunca restauradas | se descubre que estaban rotas el día que hacen falta |
| Validar solo en la capa final | el error ya entró y se propagó a todos los agregados |
| Un orquestador para un solo pipeline diario | más tiempo operándolo que mirando los datos |
| Comparar antes/después en días distintos | se atribuye al cambio lo que era variación del dato |
