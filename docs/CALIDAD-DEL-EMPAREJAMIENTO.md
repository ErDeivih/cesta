# ¿Cuánta confusión hay en el emparejamiento, y de qué tipo? — 26 de septiembre de 2026

**Por qué existe.** El dueño lo dijo así: *"creo que sigue habiendo mucha confusión en productos
que catálogo como iguales y no lo son"*. Tenía razón, y esto es la medición: **cuánto**, **de qué
tipo**, y **qué reglas se probaron y no sirven**, que es la mitad útil de la respuesta.

    uv run python -m projects.cesta.verificar_ingesta     # (la ingesta, para contexto)
    uv run python -m projects.cesta.auditar_pares         # pares ciertos perdidos, contra el banco

---

## 1. De qué está hecho el catálogo de enlaces

22.772 enlaces en el gold del 25 de septiembre de 2026, clasificados por **la fuerza de la prueba
que los sostiene**:

| clase | enlaces | % | qué es |
|---|---:|---:|---|
| `equivalente` | 16.691 | 73,3 % | marca distinta y **mismo formato declarado**. Es el canal que justifica el proyecto: compara el Hacendado con el Carrefour |
| `marca` | 2.857 | 12,5 % | misma marca, mismo formato |
| `ean` | 1.757 | 7,7 % | mismo código de barras: prueba dura, no se discute |
| `suelto` | 1.467 | 6,4 % | **sin formato comprobado** (segunda pasada, listón 0,82): aquí el nombre es la única prueba |

## 2. Cuántos juntan cosas que no son lo mismo: **alrededor de 1 de cada 6**

Muestra de 40 enlaces **al azar** (semilla fija, para poder repetirla), juzgados uno a uno. De los
34 que se pueden juzgar sin dudar, **6 juntan productos distintos (17 %)**. Los seis, que valen más
que el porcentaje:

    TORRAS Chocolate negro con avellanas 150 g
      vs  Chocolate negro 70% con macadamia Valor 150 g          ← marca y fruto distintos

    CLAVILEÑO Chocolate negro sin azúcar añadido 100 g
      vs  Chocolate negro 85% cacao sin azúcar añadido Valor 100 g

    PRINCESA Galletas 120 g
      vs  Galletas de mantequilla Campbells 120 g                ← dos galletas, ni la misma marca

    1906 Cervezas reserva especial pack de 6 x 33 cl
      vs  Cerveza reserva 1925 Alhambra                          ← «1906» contra «1925»

    Ron Malibu con coco 70 cl
      vs  Ron blanco Velero 70 cl                                ← con coco contra blanco

    Chupetes AVENT Ultra air 0-6 meses 2 ud
      vs  Chupete Philips Avent Ultra air **nighttime** 2 ud      ← día contra noche

**El patrón es siempre el mismo**: mismo tipo de producto, **mismo formato**, un par de palabras
genéricas compartidas («chocolate negro», «ron», «cerveza», «galletas») y **la palabra que de
verdad distingue el uno del otro presente solo en un lado** (avellanas / macadamia, blanco / coco,
1906 / 1925). El matcher ve «chocolate negro 150 g» a los dos lados y el nombre se parece lo
bastante; la diferencia está en una palabra, y el IDF no la protege porque las dos son raras.

Dos cosas más de la misma muestra, que son problemas de dato y no de emparejamiento:
recambios de Oral-B «4 ud» en DIA contra «1 ud» en Mercadona con **el mismo EAN**, y lentejas
«425 g» contra «430 g» también con el mismo EAN: la cantidad declarada por una cadena está mal, y
eso envenena el precio por unidad (los dos casos están fuera de la comparación por unidad, que
solo admite kg, l y m, pero se ven en la ficha).

## 3. Tres reglas que parecían buenas, medidas y descartadas

Antes de tocar el matcher se midió cada idea sobre el gold del día. **Ninguna de las tres sirve**,
y esto se escribe para que nadie las vuelva a intentar:

**A. «Palabras distintivas sin ninguna en común»** (si los dos nombres tienen palabras raras
—idf ≥ 4— y no comparten ninguna, no son el mismo producto). Cazaría 4 de los 6 errores de arriba…
pero solo se dispara en **81 enlaces de 22.772 (0,4 %)**, y mirándolos **casi todos son correctos**:
«Dentífrico original Colgate Total» contra «Pasta de dientes original Colgate Total», «Brandy Terry
Centenario» contra «Bebida espirituosa Centenario Terry», «Coca-Cola pack» contra «Refresco
Coca-Cola». Cortaría más aciertos que errores.

**B. «El que calla bloquea», solo en los ejes de identidad** (descafeinado, sin lactosa, sin
azúcar, gas, integral…). Un lado declara el eje y el otro no: 4.376 enlaces (19,2 %), de los cuales
2.901 (12,7 %) son de ejes de identidad. Mirando la muestra, **son casi todos correctos**: pares con
**el mismo EAN** donde una cadena escribe «sin gluten», «sin lactosa» o «sin azúcar añadido» y la
otra no, porque el producto ya lo era. Aplicarlo cortaría miles de aciertos. La regla que hay
—«el que calla no bloquea»— está bien puesta.

**C. «Exigir la cantidad en el canal suelto»** (sin formato comprobado). Es tentador: 616 de los
1.467 enlaces de ese canal (42 %) tienen las dos cantidades declaradas y distintas. Pero mirándolos
uno a uno **casi todos tienen el mismo EAN** (300 ml contra 330 ml del mismo champú, 4 contra «4+2»
rollos del mismo papel): la diferencia es un error de la cadena al declarar el tamaño, no un
producto distinto. El canal existe justo para el caso «pack contra pieza suelta», así que exigir la
cantidad lo rompería.

## 4. Lo que sí puede arreglarlo

No es una regla más barata: es **mejor prueba**. Y aquí es donde entra lo que el dueño dijo de las
webs (`docs/DATOS-QUE-NO-COGEMOS.md`): hay texto y atributos publicados que no se están cogiendo y
que separan variantes justo por donde se escapan estos seis errores:

    aldi        shortDescriptionFormatted[].text   «Variedad: verdejo», «Con zumo de manzana…»   42,8 %
    mercadona   main_feature                       «con dulce de leche, galleta y plátano»        27,4 %
    alcampo     promotions[].requiredProductQuantity  la mecánica en número, no en texto          8,0 %
    mercadona   price_instructions.reference_price  el precio por unidad que publica la cadena  100,0 %

El orden de trabajo, por valor medido:

1. **Meter el texto de las fichas** (Aldi `shortDescriptionFormatted`, Mercadona `main_feature`) y
   usarlo como **prueba de variante**: si un lado dice «con coco» y el otro no dice nada de coco
   pero dice «blanco», hay una diferencia declarada que hoy no se mira.
2. **Cruzar el precio de referencia de Mercadona** (100 % de sus fichas) con el nuestro: es la
   única forma de detectar el caso «425 g contra 430 g» sin esperar a que una persona lo vea.
3. **Un banco de pares negativos**: hoy se mide el recall contra 1.799 pares ciertos (por EAN) y no
   se mide **cuántos pares que NO son el mismo producto se están enlazando**. Los 40 de la muestra
   de arriba, etiquetados, son el principio: con 200 pares negativos se puede medir si un cambio
   mejora la precisión o solo mueve el recall.

---

## 5. Lo que este documento no dice

- **No dice que el 17 % sea el número final.** Son 34 enlaces juzgados por quien escribe, con el
  criterio escrito arriba (mismo producto = misma variedad, mismo formato, misma marca o marca
  blanca equivalente). Una muestra más grande movería el número unos puntos, no el orden de
  magnitud.
- **No dice que el comparador esté roto.** El 83 % de los enlaces junta lo que tiene que juntar, y
  los grupos con mismo EAN (7,7 %) son prueba dura. Lo que no se puede decir hoy es «esta
  comparación es correcta» sin mirarla: eso es lo que hay que arreglar.
