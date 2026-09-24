---
seccion: Fundamentos
resumen: Los terminos que usa el material, en una linea cada uno, agrupados por tema y con el capitulo donde se explican.
---

# 98 · Glosario

Todo el vocabulario que aparece en el material, en una línea cada uno y agrupado por tema. Al
lado de cada término, el capítulo donde se explica de verdad. Se puede leer de corrido: es, en
sí mismo, un resumen del curso.

## El dato y sus capas

| término | qué es | dónde |
|---|---|---|
| **raw** | lo que devolvió la web, tal cual. Se puede tirar cuando caduca | 15 |
| **bronze** | el mismo dato en Parquet tipado. **No se tira**: sin él no se puede reprocesar | 15 |
| **silver** | limpio y normalizado: unidades canónicas, céntimos enteros | 02 |
| **gold** | lo que consume la aplicación: grupos, precios por unidad, calidades | 02 |
| **Parquet** | formato columnar comprimido por columna. Permite leer solo lo que hace falta | 02 |
| **DuckDB** | motor SQL que lee Parquet directamente. La mitad de «leer» del proyecto | 02 |
| **Polars** | librería de dataframes multihilo. La mitad de «transformar» | 02 |
| **idempotencia** | correr dos veces con la misma entrada deja el mismo estado | 02 |
| **partición** | carpeta por fecha (`fecha=2026-09-24`) que se reescribe entera, nunca se añade | 02 |
| **tabla** frente a **vista** | PostgreSQL guarda lo que se escribe; DuckDB consulta lo que se lee | 11 |
| **migración** | fichero `00N_*.sql` que se aplica en cada arranque, y tiene que ser idempotente | 11 |

## El producto y su comparabilidad

| término | qué es | dónde |
|---|---|---|
| **ficha** | un producto de una cadena, con su `fuente` (la cadena) y su `id_fuente` | 01 |
| **EAN** | el código de barras. Dos fichas con el mismo EAN **son** el mismo producto | 01 |
| **grupo** | el mismo producto de verdad en varias cadenas, emparejado (`grupo_id`) | 04 |
| **unidad canónica** | `kg`, `l`, `m`, `ud`: la unidad con la que se compara | 03 |
| **precio por unidad** | €/kg, €/l, €/ud. Lo único comparable entre envases distintos | 03 |
| **pack** | varias unidades en un envase. Se dice, no se usa como cuchillo | 03 |
| **`cantidad_fiable`** | si el tamaño lo publica la cadena o es un «1 ud» de relleno | 03 |
| **`en_disputa`** | ficha donde nuestro €/unidad y el de la cadena se contradicen: se aparta | 03 |
| **recorte** | descartar relativos fuera de `1/3`–`3` en un índice, y decir cuántos | 07 |

## Algoritmos de emparejamiento

| término | qué es | dónde |
|---|---|---|
| **entity resolution** | decidir cuándo dos registros son la misma cosa. El problema central aquí | 04 |
| **bloqueo** | no comparar todos los pares: solo los que comparten formato y alguna palabra | 04 |
| **pair completeness** | cuántos pares verdaderos quedan juntos tras el bloqueo. **Es el techo del recall** | 05 |
| **reduction ratio** | cuántos pares te ahorras con el bloqueo | 04 |
| **Dice** | similitud por tokens: 2·comunes / total. Aquí ponderada por IDF | 04 |
| **IDF** | peso inverso a la frecuencia: «leche» distingue poco, «MILSANI» mucho | 04 |
| **trigrama** | grupos de tres letras. Salvan erratas y palabras pegadas, con descuento | 04 |
| **húngaro** | algoritmo de asignación óptima 1-a-1 entre dos conjuntos, con coste | 04 |
| **componentes conexas** | unir los enlaces en grupos. Imponen transitividad: A≈B y B≈C ⇒ A≈C | 04 |
| **medoide** | el miembro de un grupo con mayor parecido medio a los demás | 10 |
| **cohesión** | parecido de cada miembro con el medoide. Se midió y **no separa** aquí | 10 |
| **invariante** | propiedad que debe cumplirse siempre (0 ejes contradictorios, 0 grupos de 11+) | 05 |
| **must-link / cannot-link** | restricciones del dato: mismo EAN sí, EAN distinto no | 04 |

## Estadística y medidas

| término | qué es | dónde |
|---|---|---|
| **mediana** | el valor del medio. Con colas largas es el resumen; la media es un artefacto | 06 |
| **media recortada** | la media sin el 10 % de cada extremo: compromiso entre mediana y media | 06 |
| **percentil** | el valor por debajo del cual está ese porcentaje. Cuenta la forma de la distribución | 06 |
| **IQR** | rango entre el percentil 25 y el 75. Base de las vallas de Tukey contra outliers | 06 |
| **ventana móvil** | las últimas *n* observaciones, para calcular una referencia que se adapta | 06 |
| **precio de siempre** | mediana móvil de 30 observaciones. La referencia para juzgar una oferta | 08 |
| **recall** | de los pares que sabemos ciertos, cuántos encuentra. Hoy 65 % | 05 |
| **precisión** | de los que encuentra, cuántos son ciertos | 05 |
| **B-cubed** | métrica de evaluación por registro, no por par: mira los grupos, no los enlaces | 05 |
| **fuga de información** | usar en el modelo algo derivado de la respuesta. Invalida la medida | 05 |
| **sesgo de selección** | analizar solo la parte comparable y extrapolar a todo | 06 |
| **calibración / ECE** | si dice «0,9», ¿acierta el 90 %? Se mide con el ECE | 10 |
| **intervalo de confianza** | el rango donde caería el número si se repitiera la muestra | 06 |

## Precios y promociones

| término | qué es | dónde |
|---|---|---|
| **Jevons** | media geométrica de relativos. La fórmula recomendada con datos de escáner | 07 |
| **Carli / Dutot** | media aritmética de relativos / cociente de medias. Carli tiene sesgo al alza | 07 |
| **encadenado** | multiplicar los eslabones día a día en vez de comparar extremos | 07 |
| **chain drift** | sesgo del encadenado cuando los precios rebotan. Aquí medido: ≤0,38 pp | 07 |
| **Törnqvist** | índice superlativo que necesita cuotas de gasto. Aquí no hay ventas | 07 |
| **descuento real** | 1 − precio de hoy / precio de siempre, calculado por nosotros | 08 |
| **anuncio de oferta** | el texto de promoción que publica la cadena (`promo_txt`) | 08 |
| **precio anterior** | para la norma, el **más bajo de los 30 días previos** | 08 |
| **oferta dudosa** | anuncia oferta y hoy no cuesta menos que su precio de siempre | 08 |
| **2x1, 3x2, lote** | mecánicas que bajan el precio **por unidad comprada**, no el de una unidad | 08 |

## Scraping e ingeniería

| término | qué es | dónde |
|---|---|---|
| **scraping** | traer datos de una web: cliente, caché, ritmo, sesión, validación y registro | 15 |
| **sitemap** | índice de URLs que publica la web. Muchas veces es la puerta más limpia | 15 |
| **SSR / `__INITIAL_STATE__`** | HTML que ya trae los datos dentro, en un JSON embebido | 15 |
| **WAF** | cortafuegos de aplicación (AWS WAF, Akamai). Devuelve un reto en vez de datos | 15 |
| **huella de navegador** | imitar a Chrome de verdad (`curl_cffi impersonate`), no cambiar solo el UA | 15 |
| **crawl-delay** | espera que pide `robots.txt`. Ojo: puede ser de otro bot y no aplicarte | 15 |
| **cobertura** | comparar la captura de hoy con la última buena **rama por rama** | 15 |
| **deriva (drift)** | que una cadena entregue de pronto la mitad de filas que su media | 15 |
| **runlog** | una fila por ejecución y cadena. «Vale más que el propio scraper» | 15 |
| **contrato de datos** | qué columnas, con qué tipos, y qué se considera válido | 02 |
| **cuarentena** | apartar la fila que no cumple, en vez de borrarla o inventarla | 02 |
| **CSP** | política de seguridad del navegador. Aquí prohíbe scripts y estilos en línea | 11 |

## Las reglas de la casa

Estas no son términos: son decisiones. Van al final porque son las que más se repiten.

| regla | qué dice | dónde |
|---|---|---|
| **«no lo sé»** | un dato que no tenemos es «no lo sé», nunca un cero de relleno | 00 |
| **el que calla no bloquea** | si un dato no declara nada, no está afirmando que sea igual | 04 |
| **medir antes y después** | sobre el mismo dato, o no sabes qué causó la diferencia | 12 |
| **misma unidad** | comparar €/kg con €/ud no da una diferencia: da un disparate | 03 |
| **contar los recortes** | todo filtro se cuenta y se enseña; un filtro silencioso es una mentira técnica | 06 |
| **nada de CAPTCHAs** | ni a mano ni automatizado; y nada de proxies residenciales | 15 |
