---
seccion: Práctica del análisis
resumen: Alcance, fichas completas, comparación automática y preparación para recetas.
en_una_frase: Menos ruido, más información por producto y pruebas de identidad son tres trabajos diferentes.
---

# 16 · De un catálogo grande a datos útiles

## Tres preguntas distintas

¿Este artículo pertenece a la cesta? Es **clasificación de alcance**.
¿Qué sabemos de él? Es **extracción y completitud**.
¿Es el mismo que vende otra cadena? Es **resolución de entidades**.
Reducir filas no resuelve las otras dos. Una tabla con muchos alimentos puede ser pertinente y
carecer de ingredientes; dos alimentos bien descritos pueden seguir siendo productos diferentes.

## El viaje del dato

1. **Descubrimiento:** encontrar categorías, artículos y variantes sin recorrer bazar.
2. **Raw:** guardar la respuesta y procedencia; aún no es un producto normalizado.
3. **Bronze:** extraer por fuente y validar tipos. Conservar campos adicionales para no perderlos.
4. **Silver:** unificar unidades, nombres de campos y estados sin inventar valores ausentes.
5. **Gold:** preparar ofertas, identidades y métricas para decisiones concretas.
6. **Aplicación:** conservar elección, zona, condiciones y fecha; explicar incertidumbres.

Para cada paso pregunta: ¿puedo volver al dato que justificó este número? Si no, falta trazabilidad.
No es necesario añadir dbt o Dagster para entenderlo: este repositorio ya ejecuta transformaciones
Python y consultas sobre Parquet. Una herramienta nueva no reemplaza contratos ni controles.

## Experimento 1: comprobar el alcance

    uv run python -m projects.cesta.revisar_alcance --ejemplos 2

Lee incluidos, excluidos y revisión, no solo porcentaje fuera. El 6 de octubre de 2026 había
224 excluidos por la política dentro de gold y 2.612 en revisión. El control anunciaba cero
alimentos descartados, pero entre los ejemplos aparecía una barrita proteica excluida.

**La lección:** el control también es un programa y puede equivocarse. Si comparte el mismo
vocabulario y supuestos del clasificador, puede confirmar sus errores. Necesitas un pequeño banco
independiente de ejemplos conocidos, incluyendo casos adversarios.

«Bolsa para cubo de basura» y «cubo de basura» comparten palabras, pero el objeto vendido no es
el mismo. Esto explica por qué coincidencia de palabras no basta para clasificar ni emparejar.

## Experimento 2: medir la riqueza del catálogo

    uv run python -m projects.cesta.laboratorio_comparacion

La salida JSON contiene `fuentes`, sus `campos` y `nutricion_numerica_con_base`.
Un campo ausente del esquema no es lo mismo que presente pero vacío. Una tabla nutricional
`{}` no cuenta; un valor numérico cero sí puede ser un dato real.

Antes de usar un porcentaje, define el denominador: toda la cadena, solo alimentación o solo
productos donde el campo aplica. No penalices un detergente por carecer de proteínas.
El instrumento muestra presencia sobre catálogo total; para afirmar cobertura alimentaria
todavía hay que cruzarlo con una clasificación validada.

Las fichas son relativamente estables, pero no eternas. El precio se consulta con más frecuencia;
ingredientes, formatos y advertencias se versionan y revisan cuando cambian o vencen. La caché
evita descargas duplicadas; el histórico permite explicar qué se sabía en una fecha.

## Experimento 3: identidad automática con capacidad de abstenerse

El laboratorio genera candidatos de grupos ya existentes y de un índice de GTIN. Después:

1. Valida longitud, caracteres y dígito de control del código; no elimina letras para arreglarlo.
2. Comprueba contradicciones de marca, formato y atributos extraídos del nombre.
3. Separa candidato fuerte por GTIN, código distinto, conflicto y evidencia insuficiente.
4. Calcula Jaccard de palabras: intersección / unión. Lo usa como información, **no como
   probabilidad de identidad** ni como permiso para fusionar.

El 6 de octubre evaluó 17.549 pares. Esto no cubre todos los pares posibles ni mide precisión:
falta contrastar con etiquetas de referencia independientes. Un candidato por GTIN no certifica
que ese código esté bien asignado en la fuente. Un conflicto de marca puede ser una alternativa
interesante, pero no es el mismo artículo.

**Automatizar no exige que el dueño revise todo.** Se revisa una muestra para medir calidad y
casos inciertos para mejorar reglas/modelos. Lo claro se procesa por lotes; lo no demostrado se
mantiene separado. No hace falta una IA generativa para comprobar que 6 botellas no son una.

En una segunda etapa, un modelo aprende a ponderar atributos sobre ejemplos etiquetados. Se
evalúa en otros productos, se calibra y se permite abstenerse. Embeddings sirven para encontrar
candidatos semánticos; no distinguen por sí solos todas las tallas, recetas o formatos.

## Experimento 4: un dato oculto al lector de texto no está ausente del HTML

El piloto Lidl lee `data-grid-data`, un atributo HTML que contiene JSON. La página pública de
ofertas semanales devolvió 76 variantes de 70 productos padre el 6 de octubre de 2026.
Dos sabores de kéfir compartían padre: deduplicar solo por `productId` habría borrado una variante.

Consulta la implementación en `projects/cesta/sondear_lidl.py`. No ejecuta red al importarla.
Su modo `--html` trabaja con una respuesta previamente guardada. `--web` consulta robots y una
página: requiere intención explícita y no lanza la captura diaria.

Una región apunta a un grupo de precios; un precio de club conserva su condición. Ni el código
interno es un EAN, ni una oferta semanal es el surtido completo, ni estado ONLINE demuestra stock
en tu tienda. Esas distinciones son ingeniería de datos, no detalles de interfaz.

## Lo necesario antes de recetas y calorías

Mantener base 100 g / 100 ml / porción y cantidad consumida. La fórmula por nutriente es:

    aporte = cantidad_en_la_unidad_de_la_base * valor_por_100 / 100

No usarla si falta la base o la conversión. Una compra no es una comida: puede repartirse entre
personas, sobrar o desperdiciarse. Distingue lista comprada, receta preparada y consumo anotado.
Un total parcial debe decir qué ingredientes no pudo calcular, no presentar esos huecos como cero.

## Cómo seguir aprendiendo

Lee después el [encargo técnico con resultados y pendientes](../CESTA-AMPLIACION-2026-10-06.md).
Para cada cambio haz una predicción, ejecuta el instrumento, busca un contraejemplo y escribe
qué cambió y qué sigue sin demostrarse. Esa práctica enseña más que añadir un gráfico sin revisar
el significado de sus datos.


## Entrega del 6 de octubre de 2026 · cerrar el alcance de verdad

### El problema

El control de alcance decía «cero alimentos excluidos» y a la vez mostraba tres falsos descartes
reales. Un control que comparte vocabulario y supuestos con lo que vigila puede confirmar sus
propios errores: eso no es medir, es repetir.

### Evidencia cruda (producto, cadena y pasillo, tal cual)

    Aldi        Barrita proteica sabor brownie                     parafarmacia
    Carrefour   Absorbeolores frigorífico XL Croc Odor 140 g.      drogueria-y-limpieza/ambientadores
    DIA         Bolsa de basura 30 L cubo alto con autocierre      https://www.dia.es/limpieza-...
    Aldi        Botas de trekking                                  (sin categoría)

Los cuatro estaban mal clasificados, y por tres causas distintas.

### La transformación

1. **`_casa` comparaba palabras sueltas en cualquier orden.** «cubo de basura» casaba con las
   palabras {bolsa, de, basura, cubo, alto}. Una frase de la política tiene que ser **contigua y
   en orden**; si no, no es una frase, es una lista de palabras.
2. **Palabras del título que nombran un uso, no un producto.** «frigorífico» excluía un
   absorbeolores *para* el frigorífico. Los aparatos que se nombran así (frigorífico, nevera,
   aspirador, ventilador, batidora, cafetera, tostadora) salen del léxico: su pasillo
   («Electrodomésticos») ya los excluye, y la palabra solo hacía daño.
3. **Un pasillo de comida sin declarar.** «Sin Gluten / Sin Lactosa, Nutrición deportiva» caía en
   revisión, y en Aldi la barrita salía excluida por estar en «parafarmacia», que es lo único que
   publica. Se declara la dietética como comida de reposición, y se permite que una regla de
   producto le gane **a una exclusión concreta y declarada** (`gana_a_exclusion`), no a todas: un
   juguete que mencione comida no puede entrar por esa puerta.
4. **Calzado sin rama.** Aldi publica «Botas de trekking» sin categoría: se declara por producto.

Y una fuga en la dirección contraria, encontrada al medir el bazar aceptado: **233 accesorios
duraderos de bebé entraban** (cunas de viaje, cochecitos, tronas) porque la familia «Bebé» tiene
prioridad 35 y ganaba a todo. La frontera del dueño es la reposición: una cuna no se gasta. Se
excluye el pasillo durable con prioridad 40 y se añaden los términos de producto.

### El algoritmo, en una frase

**Para excluir, el título; para decidir, el pasillo; y el producto solo gana a una exclusión si la
política lo declara regla a regla.** El detalle está en `core/alcance.py` (`_casa`, `_clasifica`) y
la política en `core/datos/alcance.yml` (versionada con el código).

### Prueba reproducible

    uv run pytest tests/test_alcance.py -q                      # 41 pruebas
    uv run python -m projects.cesta.revisar_alcance --ramas     # informe y control de seguridad

Cada caso medido entra como regresión **con su negativo**: el cubo de verdad sigue fuera, el
frigorífico de verdad sigue fuera, el ibuprofeno sigue fuera, y la cuña de queso entra (porque sin
tildes «cuña» es «cuna», que es la trampa que este proyecto ya se comió una vez).

### Métricas fechadas (6 de octubre de 2026, sobre 51.659 productos de 5 cadenas)

    antes   entran 48.823   salen 224   a revisar 2.612
    ahora   entran 49.268   salen 293   a revisar 2.098

Salen más porque se cerró la fuga de bebé (+90) y entran más porque la dietética dejó de caer en
revisión (514 salen de revisión). **La comida sigue a cero descartes**, que es la condición que
puso el dueño. Ramas sin un solo producto de cesta: de 12 a 1.

### Limitaciones

- El control de seguridad sigue siendo un programa: se le ha quitado el ruido medido, pero una
  lista de palabras no sustituye a un banco de verdad con etiquetas humanas, que es el paso
  siguiente.
- «No estar en el catálogo» no es «no existir»: el caso de DIA se buscó por el nombre real y
  aparece; otros pueden faltar por cómo los captura su web.
- Las prioridades (20, 30, 35, 40) son decisiones explicadas, no una verdad universal: se cambian
  en un sitio y el informe dice el efecto en segundos.
- Quedan **3 productos sin nombre** en gold, que ningún control estaba contando.
