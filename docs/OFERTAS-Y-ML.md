# Cesta — ofertas, recomendaciones y aprendizaje automatico

Escrito el 16 de septiembre de 2026. Contesta a dos preguntas: **que se puede
hacer con las ofertas** y **donde tiene sentido meter aprendizaje automatico** —
y, sobre todo, donde no.

La respuesta corta: casi todo el valor esta en cosas que no son aprendizaje
automatico, y el aprendizaje automatico util llega en unos meses, cuando haya
historico. Empezar por ahi seria construir el tejado antes que las paredes.

---

## 1. Las ofertas: lo que ya tenemos y no usabamos

Medido el 16 de septiembre sobre lo que publican las cadenas:

    cadena      productos con texto de oferta        que da
    ALCAMPO            3.045   (12,9 %)   mecanica completa y fechas
    CARREFOUR            ~11,8 % de las fichas       mecanica, en el HTML
    ALDI                    95   (4,6 %)   precio tachado y fecha de fin
    DIA                    107   (2,0 %)   solo la marca de promocion
    MERCADONA                0                nada

**Carrefour publicaba sus ofertas y las estabamos tirando.** El JSON que leemos
no las trae; estan en el HTML de la tarjeta, en un `title` de la insignia. Igual
que paso con el EAN, que ya se sacaba de ahi. Arreglado hoy.

### Lo que dicen esos textos

    681  Todo a 1 EUR (14/09/2026 - 08/10/2026)
    589  Producto en Folleto (10/09/26_23/09/26)
    285  Club Alcampo 2a unidad -50% acum en tu tarjeta
    239  2a unidad -50% (10/09/26_23/09/26)
    197  5 EUR dto. comprando 20 EUR en Nestle
    163  Stock Fuera (Unidades Limitadas)
    134  3x2  (10/09/2026 al 23/09/2026)
     40  2a unidad -50%          (Carrefour)
     37  -20% / -30% Dias Locos  (Carrefour)

### Una oferta no es un precio: es una regla

Esto es lo que cambia el calculo de la cesta. **"2a unidad -50%" no abarata el
producto: abarata el par.** Si la lista pide dos botes y hay 3x2, el tercero sale
gratis. Mientras la promocion sea una cadena de texto, el calculo de "donde sale
mas barata la lista" no puede tenerla en cuenta y da un resultado peor que el
real.

`core/promos.py` convierte el texto en algo con lo que se puede multiplicar:

    lee("2a unidad -50%").coste(2, 100)  ->  150 centimos   (no 100)
    lee("3x2").coste(3, 100)             ->  200
    lee("Todo a 1 EUR").coste(2, 250)    ->  200

Cinco mecanicas cubren **el 50,8 % de los productos con texto de oferta**:

    precio_fijo    "Todo a 1 EUR"                       681
    porcentaje     "-30% Dias Locos"                    467
    umbral         "5 EUR dto. comprando 20 EUR"        299
    enesima        "2a unidad -50%"                     279
    nxm            "3x2", "2x1"                         147

El resto no encaja y **se trata como si no hubiera oferta**, que es el error
seguro: "Producto en Folleto" no dice cuanto rebaja, y "Novedad Alcampo" no es
una oferta.

### La decision incomoda: los descuentos de tarjeta no cuentan

291 productos llevan "Club Alcampo ... acum en tu tarjeta". Ese dinero **no se
descuenta en caja**: se acumula en un monedero para otra compra.

Se reconocen, se marcan como `acumulable`, y **no bajan el precio del calculo**.
Un comparador que los reste esta mintiendo sobre lo que vas a pagar hoy. Se
pueden ensenar aparte ("y ademas acumulas 1,20 EUR"), pero no en el total.

### Lo que esto habilita en la app

1. **El reparto entre tiendas deja de estar mal.** Hoy suma precio x cantidad. Con
   las mecanicas, sabe que llevar dos es mas barato que dos veces uno.
2. **"Llevate una mas".** `unidades_optimas` dice cuando anadir una unidad baja el
   precio unitario: con 3x2 y dos en la lista, la tercera sale gratis. Se sugiere,
   no se impone — y solo hasta un tope, que proponer una carretilla por ahorrar
   treinta centimos es ruido.
3. **Una pantalla de ofertas de verdad**, con la mecanica traducida y la fecha de
   fin, no una lista de productos con una etiqueta roja.

---

## 2. Las ofertas que las cadenas NO declaran

Hay un segundo tipo de oferta, mas interesante: la bajada de precio que nadie
anuncia. Esa se ve en el historico, y ahi es donde el proyecto se vuelve valioso
con el tiempo.

    hoy (10 dias)     entre 1.000 y 2.000 precios se mueven al dia
    a los 30 dias     tendencia: que sube y que baja de verdad
    a los 45 dias     `oferta_sospechosa`: la subida previa a la "oferta"
    a los 90 dias     posicion en el rango: "esto no ha estado tan barato
                      desde julio"
    a los 365 dias    estacionalidad

`oferta_sospechosa` ya esta programado y hoy da **cero casos**, porque compara
con el precio de hace 45 dias y solo llevamos diez. Empieza a funcionar el **20
de octubre**. No hay nada que arreglar: hay que esperar.

---

## 3. Aprendizaje automatico: donde si y donde no

Antes de nada, la regla: **si una regla escrita a mano lo resuelve, una regla
escrita a mano es mejor.** Se explica, se prueba, se arregla, y no se degrada
sola. El aprendizaje automatico se gana el sitio cuando el problema tiene
demasiados casos para escribirlos.

### 3.1 Emparejar productos — el unico candidato claro HOY

Es el problema central del proyecto y el mas medido: **57 % de aciertos** sobre
1.748 pares conocidos, escondiendo el EAN a proposito. Sube desde el 57 % de
ayer gracias a los arreglos de Alcampo y Aldi.

Lo que hace ahora `core/matching.py` es bueno pero es artesania: Dice ponderado
por IDF, trigramas, comparacion sin marca, bloqueo por formato. Cada mejora se
gana peleando.

**Lo que aportaria un modelo, y es concreto:** tenemos **1.748 pares verdaderos y
gratis** — los que comparten EAN entre cadenas. Eso es un conjunto de
entrenamiento etiquetado que no ha costado nada.

    entrada    las senales que ya calculamos: parecido de tokens, de trigramas,
               sin marca, diferencia de cantidad, misma unidad, diferencia de
               precio por kilo, misma categoria
    salida     probabilidad de que sean el mismo producto
    modelo     una regresion logistica o un arbol (LightGBM). No una red
               neuronal: con 1.748 ejemplos y ocho senales seria absurdo.
    ganancia   hoy el umbral es 0,82 a ojo para todos los casos. Un modelo
               aprende que en refrescos hace falta mas parecido que en
               legumbres.

**Coste**: un dia de trabajo. **Riesgo**: que el modelo aprenda de los productos
que tienen EAN (marcas conocidas) y falle justo en los que no lo tienen (marca
blanca), que son los que nos importan. Eso hay que medirlo antes de creerselo.

**Pero antes que el modelo, hay algo mas barato**: los grupos demasiado anchos
(`CADENAS.md` punto 5.1). El grupo de agua con gas mete Perrier con la marca
blanca. Eso no lo arregla un modelo de emparejamiento: lo arregla decidir que
significa "equivalente".

### 3.2 Predecir cuando va a bajar un precio — todavia no

La idea es evidente: "no compres hoy el cafe, que baja el jueves". Con diez dias
de historico es adivinar.

    lo que hace falta     un ano por producto, para ver el ciclo
    lo que se puede       a los 3 meses: "este producto suele bajar cada 3
    hacer antes           semanas", que es estadistica descriptiva y no
                          necesita ningun modelo
    lo honesto            una media movil y la posicion en el rango de 90 dias
                          aciertan casi tanto como un modelo, y se explican

Anotado para revisarlo en diciembre, cuando haya tres meses.

### 3.3 Recomendar productos — no, y conviene decir por que

"Te puede interesar" necesita saber que compras. Nosotros tenemos **dos
usuarios** y una lista de la compra. Con dos personas no hay filtrado
colaborativo: no hay nadie parecido a ti con quien compararte.

Lo que si tiene sentido, y no es aprendizaje automatico:

- **"Lo compras siempre y hoy esta barato."** Es un `join` entre tus favoritos y
  `resumen.parquet`.
- **"Esto es lo mismo un 30 % mas barato."** Ya lo hace el emparejador.
- **"Esto lleva menos aditivos y cuesta igual."** Ya lo hace `calidad.py`, con la
  advertencia del origen de la letra.

Las tres responden mejor que cualquier recomendador, porque no adivinan.

### 3.4 Clasificar productos en categorias — el mejor candidato practico

Este es el que mas desbloquea y casi nadie lo pensaria como aprendizaje
automatico.

No hay categoria comun entre cadenas, y eso bloquea "Explorar", los filtros por
seccion y media docena de analisis del panel. Open Food Facts nos da la categoria
de **10.209 productos**. Son 10.209 ejemplos etiquetados.

    entrada    nombre del producto + marca + su categoria propia
    salida     una de ~25 secciones canonicas
    modelo     TF-IDF sobre los nombres + regresion logistica. Es el "hola
               mundo" de la clasificacion de texto, y para nombres de
               supermercado va muy bien.
    resto      los productos que no cruzan con OFF, que son la mayoria

**Coste**: medio dia. **Riesgo**: bajo, porque se puede medir con validacion
cruzada sobre los 10.209 y porque un error se ve a simple vista. **Ganancia**:
desbloquea la pantalla de secciones del panel y el "Explorar" de la app.

Si hubiera que elegir un solo sitio donde meter aprendizaje automatico hoy, es
este. No el emparejador, que ya funciona; no la prediccion, que no tiene datos.

### 3.5 Optimizar la cesta — no es aprendizaje, es un problema de mochila

"Reparte catorce productos entre dos tiendas minimizando el total, con las
ofertas puestas" no necesita aprender nada. Es combinatoria, y pequena:

    cinco cadenas, maximo dos tiendas  ->  10 combinaciones
    con las mecanicas de oferta        ->  una decision por producto

Se calculan todas y se coge la mejor. Un algoritmo de media pagina. Meter aqui
aprendizaje automatico seria confundir "algoritmo avanzado" con "algoritmo caro".

Lo unico que si tiene miga: **modelar cuanto vale tu tiempo**. Ir a dos tiendas
cuesta media hora. Si el reparto ahorra 6,30 EUR, ¿compensa? Eso no lo decide un
modelo: lo decides tu, y la app deberia tener un ajuste ("no me propongas dos
tiendas por menos de X EUR") en vez de fingir que lo sabe.

---

## 4. Por donde empezar, en orden

1. **Terminar las mecanicas de oferta** (`core/promos.py`, hecho) y meterlas en
   el calculo de la cesta. Es lo unico de esta lista que baja lo que pagas, hoy.
2. **Arreglar los grupos demasiado anchos.** Bloquea mas cosas de las que parece.
3. **Clasificador de categorias** con los 10.209 ejemplos de OFF (3.4). Es el
   aprendizaje automatico con mejor relacion entre esfuerzo y desbloqueo.
4. **Esperar a octubre** para `oferta_sospechosa` y `tendencia_30d`. Cero trabajo,
   se llenan solas.
5. **Revisar en diciembre** si el emparejador con modelo (3.1) merece la pena, ya
   con tres meses de datos y los grupos arreglados.

Lo que **no** hay que hacer todavia: predecir precios, recomendar productos, ni
montar nada que se entrene solo cada noche. Con diez dias de historico y dos
usuarios, eso es complejidad sin dato detras.
