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


## Banco de verdad del alcance (6 de octubre de 2026)

### El problema

El control decía «cero alimentos excluidos» y a la vez enseñaba tres falsos descartes. Un control
que comparte vocabulario y supuestos con lo que vigila puede **confirmar sus propios errores**.

### El método (y por qué así)

    uv run python -m projects.cesta.banco_verdad muestrear --por-estrato 4   # 186 fichas
    uv run python -m projects.cesta.banco_verdad informe

1. **Muestra estratificada** por cadena y estado, y dentro de los incluidos por familia, con
   **semilla fija**: la misma muestra hoy y dentro de un mes, para que la diferencia entre dos
   mediciones sea de la política y no del muestreo.
2. **Fichero ciego** (`para-etiquetar.csv`) sin la columna del veredicto: quien etiqueta lee nombre
   y categoría, no lo que dice el clasificador. Hay una prueba que lo comprueba.
3. **Etiquetas humanas** con motivo, autor y fecha (`etiquetas.csv`). Y `duda` es una respuesta
   legítima: forzar un sí o un no en un caso límite es como se fabrican los números bonitos.
4. **Dos errores, dos cuentas**: falso descarte (cesta que la política tira) y bazar aceptado (no
   cesta que entra como cesta) van separados, cada uno con su denominador. Y `revisar` se cuenta
   aparte, porque no es un error: es una pregunta pendiente.

### Primeros resultados (37 etiquetas de 186, 6 de octubre de 2026)

    falsos descartes     4 de 20 cesta      (albahaca en maceta, apósitos, preservativos,
                                             cambiador desechable)
    bazar aceptado       0 de 14 no cesta
    dudas                3
    pendientes          17 (16 cesta, 1 no cesta)

Los cuatro falsos descartes y su causa: **maceta** excluye una hierba fresca de alimentación;
**parafarmacia** excluye apósitos y preservativos, que son consumibles domésticos; y **cambiador**
—término añadido el mismo día para cerrar la fuga de bebé— excluye un cambiador **desechable**.
Los tres primeros llevaban meses ahí sin que nadie los viera.

Y los 16 pendientes son un hueco de vocabulario, no casos raros: **plurales** («pescados-y-mariscos»
no casa con `pescado`; «golosinas» no está), **pasillos sin declarar** («Bodega» de Mercadona,
«cuidado-del-cabello», «barbacoa») y **singular contra plural** en mascotas («comida-de-gato» no
casa con `gatos`).

### Limitaciones, dichas

- La primera tanda se etiquetó **sabiendo el estrato** (se hizo para cazar falsos descartes). Las
  siguientes serán ciegas de verdad, y entonces la comparación entre tandas dirá si hay sesgo.
- 37 de 186: los porcentajes son de esas 37, no del catálogo. El informe lo dice en su primera
  línea y no deja mezclarlos.
- Las etiquetas son **mías, leyendo nombre y categoría**: no son una revisión humana independiente
  del dueño, que es la que tendría que cerrar los empates.
- El banco mide el alcance. No mide identidad (T03) ni fichas (T11): cada problema necesita su
  propio banco, y fingir que uno sirve para todo es la forma de no medir ninguno.


### Lo que el banco ha encontrado, y lo que ha cambiado (6 de octubre de 2026)

Con las 37 primeras etiquetas, el banco midió **4 falsos descartes de 20** y **0 bazar aceptado de
14**, con 17 fichas esperando decisión. Después de corregir lo que esas etiquetas señalaban:

    falsos descartes   4 -> 0
    bazar aceptado     0 -> 0
    pendientes        17 -> 5

Los cuatro falsos descartes y su arreglo: **maceta** (el envase) excluía una albahaca fresca de
alimentación; **parafarmacia** excluía apósitos y preservativos, que son reposición de casa; y
**cambiador** —término que yo mismo añadí para cerrar la fuga de bebé— excluía un cambiador
desechable. Los tres primeros llevaban semanas ahí.

Los pendientes eran un hueco de vocabulario, no casos raros: **la política no entendía plurales**.
«pescados-y-mariscos» no casaba con `pescado`, ni «golosinas» con `golosina`, ni «gatos» con `gato`.
Dieciséis fichas de comida esperaban en `revisar` por una «s», y el síntoma que se veía era «sin
clasificación suficiente», que no dice nada.

### Tres cosas que este trabajo enseña, y ninguna es de vocabulario

1. **Un arreglo puede introducir el error de al lado.** Al cerrar la fuga de 233 accesorios
   duraderos de bebé añadí el término «cambiador», y con él salió del catálogo un cambiador
   desechable. Lo cazó el banco **en la primera pasada**, el mismo día. Sin banco, ese error habría
   viajado como «mejora».
2. **Una excepción tiene que valer donde se decide.** La política permite declarar que una inclusión
   le gana a una exclusión concreta (`gana_a_exclusion`). La puse solo en el paso de la categoría, y
   la mitad de las exclusiones se resuelven antes, en el paso del producto: la excepción no llegaba
   a mirarse. Se unificó en un ayudante, `_inclusion_que_gana`, para que la política no sepa cosas
   distintas según por dónde pase la ficha.
3. **Un banco que no puede enseñar el efecto de un arreglo no sirve.** El informe comparaba contra
   el estado guardado en la muestra —una foto del día en que se sacó—, así que seguía diciendo
   «cuatro falsos descartes» después de arreglarlos. Ahora recalcula el estado al vuelo.

Y la lección de método que ya apareció tres veces esta semana: **cortar por la mitad una palabra o
una línea miente**. Quitar «-es» convertía «carnes» en «carn» y el plural dejaba de casar; y un
`count` sobre una línea sin su salto de línea contaba dos veces `cat-higiene`, porque
`cat-higiene-dermocosmetica` empieza igual.


## Contar las peticiones de verdad (6 de octubre de 2026)

### El problema

La ampliación pide *«medir peticiones realmente evitadas, no inferirlas restando filas de dos días
con distinta disponibilidad»*. Restar filas de dos días es lo que **parece** una medida: si un día
la cadena publica menos, la resta lo llama ahorro.

### El método

Se cuenta **el acto**, donde ocurre, y son tres cosas distintas:

| número | dónde se cuenta | qué significa |
|---|---|---|
| `peticiones` | `core/fetch.py`, al enviar | peticiones HTTP enviadas, por host |
| `cache` | `core/storage.py`, al leer | respuestas que ya estaban guardadas y **no** generaron petición |
| `evitadas` | el colector, al decidir | decisiones de **no pedir** por política (una rama de bazar) |

Separar `cache` de `peticiones` es lo que permite distinguir **ahorro** de **avería**: sin esa
columna, «menos peticiones» puede ser que la cadena se cayó.

Y lo que no hace: **no estima lo que habría pasado**. «Evitadas» es un recuento de decisiones, no
una predicción de lo que la cadena habría servido. Se dice en el propio informe.

### Dos decisiones de ingeniería

1. **El recuento se escribe al salir del proceso** (`atexit`), no al final del colector. Son cinco
   cadenas en cinco procesos y la tarea diaria las lanza por separado: un contador que hay que
   acordarse de cerrar es un contador que un día no se cierra.
2. **Si no hay recuento, se dice «sin recuento»; no se escribe un cero.** Un fichero con ceros
   parecería una captura que fue bien y no pidió nada, y no es lo mismo que no haber corrido. El
   informe lo imprime así (`no hay ningún recuento de ese día`).

### Una medición que salió mal, y por qué se cuenta

Al ejecutar el informe apareció un recuento de Carrefour con **0 peticiones y 2 lecturas de caché**
del día en curso. No era una captura: lo había escrito **una prueba** al recorrer el camino de la
caché, y el informe del día lo habría leído como una cadena que corrió y no pidió nada.

Arreglarlo en el informe (filtrando) habría escondido el problema; se arregló donde nace:
`registra_al_salir` no registra nada si corre pytest. **Un instrumento que ensucia el dato que mide
es peor que no tenerlo.**

### Primer resultado honesto

    uv run python -m projects.cesta.peticiones
    Peticiones del 2026-10-06
      no hay ningún recuento de ese día. Ninguna cadena lo dejó escrito

Las cinco cadenas de hoy corrieron **antes** de que el contador existiera, así que hoy no hay nada
que medir y se dice así. La primera medida real es la pasada siguiente, y esa será la que permita
afirmar cuántas peticiones ahorra la política, en lugar de suponerlo.

### Limitación

El contador mide peticiones **enviadas**, incluyendo reintentos y las que acabaron en error: es lo
que se le pide al servidor de la cadena, que es lo que importa para no abusar de él. No mide
bytes ni tiempo, que son otra conversación.
