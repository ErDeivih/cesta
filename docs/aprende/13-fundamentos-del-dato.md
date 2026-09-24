---
seccion: Fundamentos
resumen: Qué es un dato, qué grano tiene, qué significa no saberlo y por qué el dinero va en céntimos.
en_una_frase: Un dato no es un número: es un número con su unidad, con su momento, con su grano y con su procedencia.
---

# 13 · Fundamentos del dato: valor, grano, clave y ausencia

Los capítulos anteriores cuentan qué se hace con los datos. Este cuenta **qué es un dato**, que
es la pregunta que decide casi todos los errores que vienen después. No es filosofía: cada
apartado de aquí abajo se puede comprobar con una consulta sobre el catálogo de hoy, y las
consultas están escritas.

> **Nota:** los apartados 1 a 5 son los que hacen falta para leer cualquier tabla de este
> material; los apartados 6 a 9 son los que explican por qué las cuentas salen mal cuando el
> grano, el tiempo o el dinero se tratan como detalles.

## 1. Las cuatro cosas que van pegadas a un valor

    valor        6,73
    unidad       € por kilo            (no «6,73» a secas)
    momento      2026-09-24            (el precio de cuándo)
    procedencia  mercadona, id_fuente  (quién lo dijo y de dónde salió)

Quitar cualquiera de las cuatro rompe el dato de una forma que no se nota hasta que se toma una
decisión con él:

- Sin **unidad**, 6,73 €/kg y 6,73 €/ud parecen lo mismo y no lo son (capítulo 03).
- Sin **momento**, no se puede saber si un cambio de precio es una subida o una comparación
  entre dos días distintos.
- Sin **procedencia**, no se puede reclamar nada: un número sin origen no se puede auditar.

En este proyecto la unidad y el momento **no son convenciones de quien escribe la consulta**: son
columnas. `unidad_canon` vale `kg`, `l`, `ud` o `m`; `fecha` está en todas las filas del
histórico. Y la procedencia son dos columnas que van juntas, `fuente` e `id_fuente`, que además
son la clave del catálogo (§3).

## 2. La escala manda en lo que se puede hacer con el número

La clasificación clásica de las escalas de medida (Stevens, 1946) tiene mala fama de teórica y es
la herramienta práctica más útil de este capítulo, porque dice **qué operaciones son legítimas**:

| Escala | Qué permite | Ejemplo aquí |
|---|---|---|
| Nominal | igualdad, contar | `marca`, `categoria`, `fuente` |
| Ordinal | orden, mediana | `nutriscore` (a–e), `nova` (1–4), `calidad` (A/B/C) |
| De intervalo | suma y resta, medias | fechas, temperaturas |
| De razón | todo, incluido cocientes | `precio_cent`, `cantidad` |

> **Trampa:** sobre una escala ordinal se puede calcular una media, y la media no significa
> nada. Aquí hay 8.401 productos con Nutri-Score: si se mapea a 1–5 y se promedia sale **3,19**;
> con NOVA (1.102 de tipo 1, 241 de tipo 2, 1.640 de tipo 3 y 4.775 de tipo 4) sale **3,30**.
> Los dos números son inútiles: un 3,19 no es «un poco peor que la media entre C y D», porque
> entre C y D no hay una distancia. Lo que sí se hace con un ordinal es **contar**: 1.424
> productos con A y 1.769 con E. Ahí sí hay información.

Es el mismo error que «la provincia media de España» y se comete todos los días con las
encuestas de satisfacción y con las notas de crédito.

## 3. El grano: qué es una fila

El grano (el *grain* de Kimball) es la respuesta a «¿una fila de qué?». Antes de mirar una
columna, hay que saber esto, porque todas las cuentas se equivocan igual si el grano está mal
entendido.

    grupos.parquet          una fila por OFERTA: (fuente, id_fuente)         57.603 filas
    precio_diario.parquet   una fila por (fecha, fuente, producto_id)       872.650 filas

Y no se cree: se comprueba. Una tabla tiene el grano que dice tener si agrupar por la clave no
junta nada:

```sql
-- esto tiene que devolver 0: si devuelve algo, la «clave» no es clave
SELECT count(*) FROM (
  SELECT fecha, fuente, producto_id FROM 'data/gold/precio_diario.parquet'
  GROUP BY 1, 2, 3 HAVING count(*) > 1);
-- 0
```

Los dos granos de arriba dan 0, y eso convierte una afirmación en una comprobación. La misma
consulta sobre `grupos.parquet` agrupando por `(fuente, id_fuente)` da 57.603 grupos distintos
para 57.603 filas: una oferta, una fila.

De aquí salen las dos cifras que este material repite todo el rato, y que **no son la misma
cosa**:

    57.603 ofertas   lo que hay en el catálogo de hoy
    44.434 grupos    conjuntos de ofertas que creemos el mismo producto

Los dos números están a un `GROUP BY` de distancia, y confundirlos multiplica o divide por nada
cualquier conclusión. Cuando este material dice «productos», dice ofertas; cuando dice «grupos»,
dice grupos; y cuando hace falta el tercero —cuántas ofertas son comparables de verdad— lo dice
con su nombre.

## 4. Que algo sea clave no lo hace único

El código de barras (EAN) parece la clave natural del catálogo. Medido hoy:

    filas con EAN                 25.413 de 57.603   (44,1 %; en 32.190 no viene)
    códigos distintos             23.662
    códigos en más de una fila     1.627
    ... de ellos, en 2+ cadenas    1.590   (luego 37 se repiten dentro de la misma cadena)
    ... y con 2+ precios distintos   654

Tres lecturas, y las tres importan:

1. **Más de la mitad del catálogo no tiene código** (55,9 %): Alcampo y Aldi no lo publican. Un
   catálogo cuya clave natural falta en la mitad de las filas **no tiene clave natural**.
2. **Un código repetido no es un dato sucio**: es el mismo producto en dos cadenas —que es justo
   lo que se quiere comparar— o dos formatos con el mismo código.
3. **654 códigos tienen más de un precio** a la vez. Es la prueba de que el precio no es una
   propiedad del producto: es una propiedad de la **oferta** (producto, cadena, momento).

> **Regla:** la clave de una tabla la decide el grano, no la intuición. Y cuando la clave natural
> falta o se repite, la tabla necesita una clave **subrogada** —aquí, la pareja
> (`fuente`, `id_fuente`) que da el propio sitio web— y la natural se queda como atributo, con
> sus repeticiones a la vista.

## 5. «No lo sé» no es cero

Esta es la regla de la casa número uno, y este es el capítulo donde se ve por qué. Lo que falta
en el catálogo de hoy, contado:

| Columna | Sin dato | % del catálogo |
|---|---:|---:|
| `certificados` | 56.890 | 98,8 % |
| `nutricion` | 53.750 | 93,3 % |
| `nutriscore` | 49.202 | 85,4 % |
| `envase` | 48.477 | 84,2 % |
| `sellos` | 44.692 | 77,6 % |
| `ean` | 32.190 | 55,9 % |
| `cantidad` | 9.928 | 17,2 % |
| `marca` | 737 | 1,3 % |
| `categoria` | 74 | 0,1 % |
| `unidad_canon`, `url`, `imagen`, `grupo_id` | 0 | 0 % |

La tentación es rellenar: un cero es cómodo, no rompe los `JOIN` y no obliga a decidir en cada
consulta. Y es mentira. Un `0` en `nutricion` significa «este producto no tiene hidratos», que es
una afirmación que **no se ha medido**; un `0` en `certificados` significa «ninguno de sus
ingredientes está certificado». Ausencia de dato y dato de ausencia son cosas distintas, y el
segundo es una acusación.

Y no es solo cuestión de honestidad: **desvía los números**. Medido sobre el precio por unidad:

    media ignorando los 147 nulos        2.037,90 céntimos
    media contando los nulos como cero   2.032,70 céntimos   (-5,2 c)

Aquí el error es pequeño porque solo faltan 147 filas de 57.603. Con las columnas de la tabla de
arriba, rellenar con ceros no da un error pequeño: da un catálogo entero de productos con 0 g de
azúcar y 0 certificados. Y el sesgo **siempre va en la misma dirección**: rellenar con cero
empuja las medias hacia abajo y las cuentas hacia cero, nunca al revés.

> **Nota:** la teoría de los datos perdidos de Rubin (1976) distingue tres casos: si falta
> **al azar** (MCAR), ignorarlo está bien; si falta **condicionado a lo observado** (MAR), hay
> métodos de imputación honestos; y si falta **por el propio valor** (MNAR) —justo lo que pasa
> con `certificados`, porque solo se publica cuando lo hay— no hay forma de reconstruirlo. Aquí
> el reparto de columnas de arriba es MNAR de libro: el que calla, calla por algo.

## 6. La tabla larga y la tabla ancha

Con 19 días y 5 cadenas, un catálogo de precios cabe en una tabla de 95 celdas de ancho: una
columna por día. Ese formato (*ancho*) es cómodo para mirar y horrible para mantener, porque
**añadir un día cambia el esquema**: la consulta de ayer no vale hoy.

Aquí el histórico es **largo** (*tidy*, Wickham): una fila por observación, 872.650 filas, y el
paso del tiempo no toca el esquema.

    fecha       fuente      producto_id   precio_cent
    2026-09-23  mercadona   24708         222.750
    2026-09-24  mercadona   24708         222.750

Con la tabla larga, «cuántos días tengo» es un `count(distinct fecha)` y no un problema de
esquema. El precio de ese formato es que las comparaciones piden `JOIN` o funciones de ventana en
vez de restar dos columnas. En este proyecto se paga con gusto: el análisis se escribe una vez y
el esquema no se toca nunca más.

## 7. El tiempo: dos fechas distintas que se confunden siempre

En un almacén de datos hay dos tiempos, no uno (Kimball los llama *tiempo de validez* y *tiempo
de transacción*):

    ¿cuándo era verdad el precio?          tiempo de validez
    ¿cuándo lo copiamos nosotros?          tiempo de transacción

Aquí **solo hay el segundo**, y está en la ruta del fichero (`raw/fuente=…/fecha=2026-09-24/`).
El primero no se puede tener: la web no publica desde cuándo vale un precio, solo el precio de
hoy. Es una limitación del origen, no del código, y por eso este proyecto no puede hacer la
ventana de 30 días que exige la Directiva Omnibus: **el catálogo más largo que se puede
comprobar hoy son 19 días**, y no hay ni un producto con 30 observaciones.

El otro detalle del tiempo es que la rejilla tiene agujeros, y no es cuadrada:

    día 2026-09-06 .. 2026-09-24        19 días de calendario
    mercadona, aldi                     19 días cada una
    dia                                 18
    alcampo                             17
    carrefour                           14
    días con las 5 cadenas              14 de 19  (3 días con 3 cadenas, 2 con 4)

    alcampo      422.840 filas  17 días   ~24.873 productos/día
    carrefour    230.664 filas  14 días   ~16.476 productos/día
    dia           99.906 filas  18 días    ~5.550 productos/día
    mercadona     81.966 filas  19 días    ~4.314 productos/día
    aldi          37.274 filas  19 días    ~1.962 productos/día

> **Trampa:** «872.650 filas = 19 días × 5 cadenas» es falso, y ese 19 × 5 = 95 no existe en
> ninguna parte de los datos. Si una media se calcula por día sin mirar qué cadenas había ese
> día, se está comparando un día de 5 cadenas con uno de 3. La regla que se sigue aquí: **toda
> cifra de tendencia dice sobre qué rejilla está calculada**, y las series se comparan por
> cadenas, no por totales sueltos.

Un detalle más de formato, que es una crítica a este proyecto y se puede medir: en
`precio_diario.parquet` la `fecha` es **texto** (`VARCHAR`, 10 bytes por fila, 8.726.500 bytes en
total), no `DATE` (4 bytes, 3.490.600). Se ahorrarían 5,2 MB y no se podría escribir `2026-9-6`
en vez de `2026-09-06`. Se sostiene porque es ISO-8601 de ancho fijo —se ordena, se corta y se
compara como si fuera una fecha, y hoy hay 0 fechas mal formadas y 0 nulos—, pero es una decisión
de comodidad, no de ingeniería, y en un almacén con más de un escritor sería un error.

## 8. El dinero va en céntimos enteros

Los precios se guardan en **céntimos, en entero** (`precio_cent`, `BIGINT`). No es un detalle de
estilo: en coma flotante binaria no existe el 0,1 exacto (`0.1 + 0.2` da `0.30000000000000004`),
y el error se acumula en silencio. La regla de la industria es vieja y sigue siendo la buena:
el dinero, en la unidad mínima y entera; el redondeo, en el último paso y con una regla escrita.

Lo que se puede medir aquí es dónde **sí** hay decimales: el precio por unidad
(`precio_unidad_cent`, `DOUBLE`), porque 2,99 € por 750 g son 3,99 €/kg. Y ahí el error está a la
vista:

    57.456 precios por unidad, de los que 25.294 (44,0 %) no son enteros
    suma en coma flotante                     117.089.350,04890001
    suma redondeando cada valor a 2 decimales 117.089.351,45999894
    diferencia                                1,41 céntimos

Un céntimo y medio sobre 117 millones no rompe nada, y ese es exactamente el problema: **el
error no avisa**. Suma 100 millones de precios y sigue pareciendo bien. Por eso la comparación de
dinero en este proyecto nunca se hace con `==` sobre un `float`, y todo lo que la aplicación
enseña como precio total viene de un entero.

> **Regla:** el dinero se almacena en la unidad mínima entera (céntimos), se redondea una sola
> vez al final, y no se compara con igualdad entre `float`. Cuando el valor es una *tasa* —el
> precio por kilo— sí puede ser decimal, y entonces se compara con tolerancia y se documenta
> cuál.

## 9. El valor no es el número: es el par (cantidad, unidad)

Sin unidad, un 6,73 no es un precio. En este catálogo la unidad canónica se reparte así:

    kg   30.782       l   15.038       ud   11.712       m   71

y hay **9.928 filas (17,2 %) sin cantidad**, que no es lo mismo que «1 unidad»: es «no lo sé».
Esas filas se ven, se pueden añadir a la lista de la compra y se enseña su precio total, pero no
entran en ninguna comparación por unidad, porque no hay con qué.

Un caso que enseña más que cualquier definición: el precio más alto del catálogo son **222.750
céntimos** (2.227,50 €) de «Alistado pequeño congelado», de Mercadona, que se vende *granel*.
La cantidad viene vacía, y su precio por unidad dice 22,50 €/kg. Las dos cosas juntas no cuadran
(2.227,50 € sería un lote de 99 kg), y **no se sabe** si es una caja, un lote o un error de la
web. La respuesta correcta a «¿cuánto cuesta eso?» es que no se sabe; la incorrecta es enseñar
«2.227,50 €» como si fuera el precio de un paquete. La normalización de unidades —y el techo de
lo que se puede normalizar— está en el capítulo 03.

## 10. Declarado, derivado y juzgado

Las 53 columnas de `grupos.parquet` no son la misma clase de cosa, y mezclarlas es cómo se
estropean los datos sin querer:

| Clase | Qué es | Ejemplos |
|---|---|---|
| **Declarado** | lo que dice la web, tal cual | `nombre`, `marca`, `url`, `imagen`, `precio_cent` |
| **Derivado** | lo calcula el código, con una regla | `unidad_canon`, `precio_unidad_cent`, `comparacion_fiable`, `grupo_id` |
| **Juzgado** | una valoración del proyecto, con su porqué | `calidad` (A/B/C), `calidad_nota`, `sellos` |

La regla que se sigue aquí: **una columna declarada no se sobrescribe nunca con una derivada**.
Se corrige el código y se recalcula, para que el arreglo valga para todos los días; si se
parcheara la columna, el parche se perdería en la siguiente pasada y nadie sabría de dónde salió
el valor bueno.

Y un juicio lleva su explicación pegada: de las 57.603 filas, **47.999 (83,3 %) no tienen
calidad asignada**, y no es un fallo del clasificador: es que no hay dato para juzgarlas. Las que
la tienen son 4.593 con A, 2.462 con B y 2.549 con C, y cada una guarda con qué se decidió
(`calidad_origen`, `calidad_nota` en 11.728 filas). Un juicio sin registro de cómo se hizo es una
opinión con formato de columna.

## 11. Las seis dimensiones de la calidad, con el número de cada una

El marco habitual (DAMA-DMBOK) parte la calidad del dato en dimensiones. Está bien porque obliga
a decir **qué** se está midiendo cuando se dice «el dato es bueno»:

| Dimensión | Pregunta | Aquí, hoy |
|---|---|---|
| Completitud | ¿está? | EAN en el 44,1 % de las filas; nutrición en el 6,7 % |
| Unicidad | ¿está una vez? | 0 duplicados sobre el grano; 1.627 códigos de barras repetidos |
| Oportunidad | ¿es de hoy? | gold del 2026-09-24, y la API publica la fecha del dato en cada respuesta |
| Validez | ¿cumple las reglas? | 0 precios ≤ 0, 0 fechas mal formadas, 0 ejes contradictorios |
| Exactitud | ¿es verdad? | **no se puede medir desde dentro** (abajo) |
| Consistencia | ¿concuerda consigo mismo? | 0 contradicciones entre el precio por unidad propio y el de la cadena |

> **Aviso:** la exactitud es la única dimensión que **no se puede comprobar con el dato dentro de
> casa**: para saber si 6,73 € es el precio de verdad hay que ir a la tienda o comparar con una
> fuente externa. Todo lo que este material llama «validado» es validez y consistencia, que son
> cosas más débiles. Decirlo no es modestia: es lo que evita que alguien use estas cifras como si
> fueran un recibo.

El resto de la calidad del dato —contratos, umbrales, cuarentena de las filas en disputa— está en
el capítulo 02, apartado 6.

## 12. Lo que este capítulo deja abierto

- **Comparabilidad**: dos ofertas con el mismo producto pueden no ser comparables si una es un
  pack. Es el capítulo 03 (unidades) y el 04 (emparejar).
- **Identidad**: decidir que dos ofertas son «el mismo producto» es un juicio probabilístico, no
  una lectura de la clave. Capítulos 04 y 05.
- **Ausencia**: las 44.692 filas sin sellos y las 32.190 sin EAN están *dentro* de los datos y
  *fuera* de las cuentas, y esa frontera hay que declararla en cada cifra que se publique
  (capítulo 12).
