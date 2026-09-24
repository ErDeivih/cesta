---
seccion: Investigación y anexos
resumen: Todas las fórmulas que usa el proyecto, con sus símbolos, su origen y el número que dan hoy.
en_una_frase: Cada fórmula del proyecto, con lo que significa cada símbolo, de dónde sale y el número que produce hoy.
---

# 93 · Las fórmulas, una a una

Los capítulos cuentan **qué** se hace y **por qué**. Este anexo cuenta **con qué cuenta**: las
fórmulas, tal y como están escritas en el código, con el significado de cada símbolo, de dónde
sale cada una, y el número que produce hoy sobre este catálogo. Es el capítulo para volver cuando
alguien pregunte «¿y ese 0,55 de dónde sale?».

Todas las constantes que aparecen aquí se pueden ver en el código:

    core/matching.py            comparar nombres, repartir parejas, agrupar
    core/normalize.py           unidades y precio por unidad
    core/comparacion.py         ahorros, ventanas y el factor 30
    core/calidad.py             la nota de 0 a 100 y las letras A/B/C
    plataforma/api/analisis.py  indices de precios, pulso, desvio por seccion

> **Nota:** ninguna fórmula de este capítulo es decorativa: cada una existe porque hubo un caso
> concreto que la pidió, y casi todas llevan al lado la medición que las puso en ese valor. Donde
> no la hay, se dice.

## 1. Comparar dos nombres

### 1.1 De un nombre a un conjunto de palabras

    limpiar(nombre)      minusculas, sin tildes, sin puntuacion
    raiz(palabra)        "alubias" -> "alubia", "lentejas" -> "lenteja"
    tokens(nombre)       {raiz(p) : p en limpiar(nombre), |p| > 2, p no en RUIDO,
                          p no es un numero suelto}

`RUIDO` es una lista escrita a mano («de», «con», «sin», «calidad», «extra», «nuevo»…): palabras
que no distinguen un producto de otro y solo generan parecido falso. La raíz quita el plural
porque cada cadena escribe el producto a su manera, y «Alubia morada Luengo» de Carrefour contra
«Alubias moradas Luengo» de DIA **no compartirían ni una palabra** siendo el mismo bote.

### 1.2 Los trigramas

    trigramas(texto) = { texto[i:i+3] : i = 0 .. |texto|-3 }     (sin espacios)

Es el conjunto de trozos de tres letras. Existe por un caso medido: «Galleta chocowafer Milka»
contra «Galletas choco wafer Milka» no comparten casi palabras, pero como trozos son casi el mismo
texto. Partir por espacios da por hecho que las dos cadenas ponen el espacio en el mismo sitio, y
no lo hacen.

### 1.3 El coeficiente de Dice, y por qué no Jaccard

    Dice(A, B) = 2 · |A ∩ B| / (|A| + |B|)

Con `A = {fairy, 654, ml}` y `B = {lavavajillas, mano, ultra, poder, fairy, 654, ml}`:

    Dice     = 2 · 3 / (3 + 7)   = 0,600
    Jaccard  = 3 / 7             = 0,429

**La elección está razonada**: los nombres tienen longitudes muy distintas según la cadena, y
Jaccard castiga esa asimetría hasta hacerla indistinguible del ruido. Dice reconoce que **todo lo
que dice el corto lo dice también el largo**, que es exactamente el caso de un nombre comercial
escrito con más y menos detalle.

### 1.4 El peso de cada palabra: IDF

    idf(p) = ln( n / (1 + c_p) ) + 1

donde `n` es el número de productos (documentos) y `c_p` cuántos contienen la palabra `p`. Es la
fórmula clásica de la frecuencia inversa de documento, con el suavizado `+1` que evita el cero.
Sobre los 57.603 productos de hoy:

    palabra en     20 productos   ->  idf  8,917     ("chocowafer")
    palabra en    100 productos   ->  idf  7,346
    palabra en  2.866 productos   ->  idf  4,000     (el corte de "palabra ancla")
    palabra en 30.000 productos   ->  idf  1,652     ("leche")
    palabra en los 57.603         ->  idf  1,000     (aparece en todos)

La palabra que aparece en todos los productos pesa 1; una que aparece en veinte pesa casi nueve.
Sin esto, «leche» haría parecer iguales a dos productos que no tienen nada que ver.

### 1.5 El parecido de dos productos

    parecido(A, B) = 2 · Σ_{p ∈ A∩B} w(p) / ( Σ_{p ∈ A} w(p) + Σ_{p ∈ B} w(p) )

Es Dice ponderado por IDF: la misma fórmula de 1.3, pero cada palabra compartida cuenta por lo
que vale. Y el parecido final de un par es el **mayor de dos canales**:

    parejo(i, j) = max( parecido(palabras_i, palabras_j),
                        0,85 · Dice(trigramas_i, trigramas_j) )

El 0,85 es `PESO_TRIGRAMAS`, y su valor está medido: se bajó a 0,80 persiguiendo los grupos por
familia y **se volvió a 0,85 midiendo** — con 0,85 el acierto era 65 % y con 0,80 el 64 %, con 23
enlaces menos para nada. El motivo es aritmético y conviene tenerlo escrito: para que el canal de
trigramas abra un enlace con el listón en 0,55, su Dice tiene que llegar a

    0,55 / 0,85 = 0,647        (bajando el peso a 0,80 el corte sube a 0,6875)

así que bajar el peso **no apaga el canal, solo lo desplaza un poco**, y de paso se lleva por
delante aciertos que sí dependían de él.

### 1.6 Los dos listones, y el bloqueo

    UMBRAL            = 0,55    parecido minimo con el formato comprobado
    UMBRAL_SIN_FORMATO= 0,82    parecido minimo cuando el formato NO se puede comprobar

La lógica del segundo: si no se puede comprobar el tamaño, más vale exigir que el nombre sea casi
el mismo. El 0,82 no es un número redondo elegido por gusto; sale de la medición del 8 de
septiembre, cuando se vio que 579 de 1.767 pares ciertos caían en bloques distintos (334 porque a
alguno no se le pudo leer el formato, 274 porque una cadena lo vende por unidades y la otra al
peso, 239 porque los números no coinciden).

Y antes de comparar nada, **la clave de bloqueo**:

    bloque(cantidad, unidad) = (unidad, round(cantidad, 3))     o ("?") si falta cualquiera

Solo se comparan productos con el mismo formato. Sin esto habría que comparar 57.603 productos
entre sí: **1.400 millones de pares** en vez de los 16,7 millones que se recorren.

## 2. Repartir parejas sin repetir

### 2.1 El problema

Dentro de un bloque y de un par de cadenas hay candidatos con su puntuación. Hay que elegir un
conjunto de parejas que **maximice la suma** sin que ningún producto salga dos veces. Eso es un
problema de asignación lineal, y se resuelve con el algoritmo húngaro (Kuhn-Munkres).

    maximizar   Σ g_ij · x_ij
    sujeto a    Σ_j x_ij <= 1   para cada producto de la izquierda
                Σ_i x_ij <= 1   para cada producto de la derecha
                x_ij ∈ {0, 1}

### 2.2 La ganancia no es el parecido

    g_ij = max(0, s_ij − umbral)

Y esto es lo que más cambia el resultado: se maximiza la **ganancia por encima del listón**, no el
parecido a secas. Con el parecido a secas, dos parejas mediocres (0,56 + 0,56 = 1,12) ganan a una
buena y un hueco (0,90). Con la ganancia, la buena vale 0,35 y las dos mediocres 0,02: gana la
buena. Medido el 22 de septiembre al probarlo: la versión sin ganancia daba un 23 % más de enlaces
y **694 grupos comparables menos**, porque los pares flojos desplazaban a los buenos y además
fundían grupos entre sí.

### 2.3 Qué arregla, con el número

Con «el mejor de cada uno» (lo que había antes), cada producto elige por su cuenta y **dos
productos pueden elegir al mismo de enfrente**: uno se queda sin pareja teniendo una igual de
buena al lado. Medido: **137 de los 701 pares ciertos que se escapaban se perdían así, el 20 %**.

El algoritmo es O(n³), y aquí n es el tamaño de un bloque por par de cadenas, casi siempre menos
de cien: por eso está escrito a mano en vez de traer NumPy o SciPy.

### 2.4 Los cuatro frenos, con su fórmula

Un grupo es lo que queda conectado por los enlaces, y eso **se propaga**: no hacen falta muchos
enlaces flojos, basta uno. De ahí tres frenos numéricos y uno estructural:

| Freno | Fórmula | Qué impide |
|---|---|---|
| Unión | `s < 0,80` y los dos lados ya tienen grupo → **no se unen** | que un puente flojo pegue dos racimos correctos |
| Anchura | `max(hi) / min(lo) > 3,0` **por unidad** → no se unen | que un grupo acabe con el más caro a más del triple |
| Precio imposible | `max(p_i, p_j) / min(p_i, p_j) > 30` → ni se compara | un bote de 1 L a 2 € contra uno de 400 ml a 3 € |
| Reparto | un grupo no puede tener dos productos de la misma cadena (salvo mismo EAN) | diecisiete grupos fundidos en uno |

El de anchura se mide **por unidad**, porque mezclar euros por kilo con euros por litro no dice
nada. El del reparto es el que más limpia: los enlaces son 1-a-1 por par de cadenas, así que un
grupo correcto no puede tener dos productos de la misma cadena. Medido el 23 de septiembre: de los
grupos de 11 o más, **74 de 74 tenían una cadena repetida**. El grupo 92 lo decía sin leer un solo
nombre: 25 productos de Alcampo, 25 de DIA, 17 de Carrefour, 14 de Mercadona y 3 de Aldi.

Y el veto del precio imposible es **condicional a propósito**: solo actúa cuando los dos precios
son comparables, la unidad es de fiar (kg, l, m — «ud» no lo es, porque cada cadena cuenta una
cosa distinta) y ninguno baja de 5 céntimos. Ahorros de 28 veces comprobados existen, así que
vetar antes borraría aciertos.

## 3. Saber si el emparejador sirve

### 3.1 Las dos tasas de siempre

    recall     = VP / (VP + FN)      de los pares que son verdad, cuantos encuentra
    precision  = VP / (VP + FP)      de los que encuentra, cuantos son verdad
    F1         = 2 · P · R / (P + R) la media armonica de las dos

Aquí el recall se mide **escondiendo el EAN**: los pares que ya sabemos ciertos por código de
barras se usan como respuestas correctas y el algoritmo no los ve. Hoy: **1.161 de 1.799 pares
ciertos, el 64,5 %**.

### 3.2 El techo, que es la cuenta que casi nadie hace

    completitud_de_pares = pares ciertos que el bloqueo deja VER / pares ciertos totales
                         = 1.359 / 1.795 = 75,7 %

Y entonces la lectura cambia: **el 64,5 % es el 86 % de lo que el bloqueo deja ver**. El margen no
está en el matcher, está en las 436 parejas que se pierden antes de comparar.

### 3.3 Cuánto puede bailar ese 64,5 %: el intervalo de Wilson

Una proporción medida sobre una muestra tiene su horquilla. Para `p̂ = 0,645` con `n = 1.799`:

    centro = ( p̂ + z²/2n ) / ( 1 + z²/n )
    mitad  = ( z / (1 + z²/n) ) · √( p̂(1−p̂)/n + z²/4n² )        con z = 1,96

    -> [0,623 ; 0,667], es decir 64,5 % ± 2,2 puntos

Sin esa horquilla, una mejora de un punto se lee como una mejora, y es ruido.

### 3.4 La auditoría de los pares perdidos

Los 1.799 pares ciertos se reparten en cuatro montones, y cada uno dice a quién hay que tocar:

    encontrado                                                 1.161   (64,5 %)
    A  el bloqueo por formato no los junta                       368   (20,5 %)
    B  mismo formato, ninguna palabra en comun                     3   (0,2 %)
    C  se comparan y no se parecen (por debajo del liston)        177   (9,8 %)
    D  se parecen y aun asi no se enlazan (el reparto 1-a-1)       90   (5,0 %)

El montón grande (A) no lo arregla ningún modelo. Donde un matcher mejor tiene margen son 177
pares: **+9,8 puntos de recall como techo**. Y hay 90 pares que el nombre ya aprueba y que se
pierden después, en el reparto.

## 4. Estadística de un catálogo sucio

    media      x̄ = (1/n) · Σ x_i
    mediana    el valor central: deja la mitad por debajo
    percentil  el valor por debajo del cual esta el k % de los datos
    recortada  media de lo que queda tras tirar el α % de cada cola
    CV         σ / x̄                     (dispersion relativa)
    IQR        q75 − q25
    MAD        mediana( |x_i − mediana(x)| )
    error tipico  σ / √n

Por qué aquí manda la mediana: la media del precio por unidad **es 2,31 veces la mediana**, el p99
son 24.911,3 céntimos y el máximo 1.419.000 (un azafrán que se vende por gramos, leído en €/kg).
Una media que multiplica por 2,3 el valor central no describe el catálogo: lo describe a medias.

Los recortes se **cuentan**: 1.679 de 797.390 valores (0,21 %) quedan fuera de la horquilla de los
índices. Un recorte silencioso es una decisión escondida; uno contado es una cifra más.

En la dispersión de los grupos, la medida es otra y también está escrita: para cada grupo se toma
`(max − min) / min` del precio por unidad, y se resume con su mediana (15,9 %) y su p90 (111,8 %).
La mediana dice que el grupo típico tiene una diferencia normal; el p90 dice que uno de cada diez
grupos tiene el doble de caro al lado del barato, y ahí hay que mirar, no promediar.

## 5. Índices de precios

### 5.1 El relativo de un producto

    r_it = p_it / p_i,t−1        (el precio de hoy entre el de la captura anterior del MISMO producto)

### 5.2 Las cuatro fórmulas de siempre

    Carli       (1/n) · Σ r_i                     media ARITMETICA de relativos
    Jevons      ( Π r_i )^(1/n) = exp( (1/n) Σ ln r_i )    media GEOMETRICA
    Dutot       ( Σ p_it ) / ( Σ p_i0 )           cociente de medias de precios
    Laspeyres   Σ (p_it · q_i0) / Σ (p_i0 · q_i0)          cesta del periodo BASE
    Paasche     Σ (p_it · q_it) / Σ (p_i0 · q_it)          cesta del periodo ACTUAL
    Fisher      √(Laspeyres · Paasche)            la media geometrica de las dos

### 5.3 La que se usa aquí, y por qué

    factor_t = exp( media( ln r_it ) )  para los r dentro de [1/3, 3]
    nivel_t  = 100 · Π_{s ≤ t} factor_s

Es **Jevons encadenado**: la media geométrica de los relativos, eslabón a eslabón. La razón de la
media geométrica está en una desigualdad clásica: la media geométrica **nunca supera** a la
aritmética, y la diferencia crece con la dispersión. Con precios que suben y bajan, Carli (la
aritmética) tiende a dar índices más altos que la realidad, porque una subida del 50 % y una
bajada del 50 % no se compensan (1,5 × 0,5 = 0,75). Jevons mide el factor multiplicativo, que es
lo que hace un precio.

El **recorte** [1/3, 3] sale del mismo sitio: un relativo de 3 o más de un día para otro no es una
oferta, es casi siempre un error de lectura, y se cuenta aparte.

### 5.4 El sesgo de encadenar, medido

Encadenar tiene un riesgo conocido (*chain drift*): si los precios rebotan y la cesta cambia, el
índice encadenado se desvía del nivel. Aquí se midió: **≤ 0,38 puntos porcentuales** como máximo, y
en cuatro de las cinco cadenas ≤ 0,02 pp, comparando el encadenado con el cálculo directo sobre el
mismo recorte y el mismo SQL de la aplicación.

## 6. Unidades, formatos y precio de referencia

### 6.1 El precio por unidad

    precio_unidad_cent = round( precio_cent / cantidad )      en centimos por unidad canonica

con la unidad canónica en `kg`, `l`, `m` o `ud`. La regla de tres es todo lo que hay, pero el
«redondear» no es un detalle: se redondea **una vez**, al final, y nunca se comparan dos `float`
de dinero con `==`.

### 6.2 Los formatos que se pueden y los que no

    g, gr  -> kg (÷ 1000)      ml, cl, l -> l        m -> m        ud, u, unidades -> ud

Y una conversión que **no** se hace: entre peso y volumen. El aceite pesa 0,916 kg/l y la miel
1,42, así que «1 l» y «1 kg» no son intercambiables sin saber qué hay dentro.

Cuando una cadena publica el precio por 100 g y el proyecto lo lee por kg, la comprobación admite
las dos lecturas (`valor` y `valor × 10`) en vez de decidir por su cuenta: es mejor dejar dos
candidatos y comprobar que elegir uno mal.

### 6.3 Qué unidad manda dentro de un grupo

    peso = (numero de cadenas que usan la unidad) · 1000 + (numero de productos con esa unidad)

Se queda la unidad con el peso mayor: primero la que comparten más cadenas, y a igualdad de
cadenas la que más productos tiene. Sin esta regla, la aplicación llegó a anunciar ahorros del
**229.833 %** restando euros por kilo de euros por unidad.

### 6.4 Cuándo dos precios no se pueden ni comparar

    factor = max(p_i, p_j) / min(p_i, p_j)
    factor > 30   -> no se da cifra de ahorro (FACTOR_INCREIBLE)
    factor > 3    -> se enseña, marcado (FACTOR_LLAMATIVO)

El 30 es el mismo número en los tres sitios donde aparece (comparación, calidad de la ficha y veto
del emparejador), a propósito: **un número compartido vive en un módulo que la API pueda
importar**, y tenerlo copiado en dos sitios acaba siendo tenerlo distinto.

## 7. Promociones: del texto al descuento

    descuento = 1 − ( precio_oferta / precio_base )

y para las mecánicas que se anuncian con palabras, el equivalente por unidad comprada:

    2x1                 compras 2, pagas 1        ->  −50,0 % por unidad
    2ª unidad al 70 %   compras 2, pagas 1,70     ->  −35,0 % por unidad
    3x2                 compras 3, pagas 2        ->  −33,3 % por unidad

Aquí está la razón de que el 80 % de las ofertas anunciadas no se puedan juzgar: su descuento
**depende de cuántas compres**, así que no existe «el descuento» de ese producto sin saber cuántas
unidades se compran. De 6.938 anuncios con texto, 3.658 son de ese tipo y 288 no anuncian precio.

La referencia legal (Directiva Omnibus) pide comparar contra el **precio más bajo de los 30 días
anteriores**, y eso aquí no se puede: el histórico más largo son 19 días y **no hay un solo
producto con 30 observaciones**. La regla propia que sí se puede calcular es una mediana móvil:

    precio_base   = mediana de los ultimos VENTANA_BASE = 30 dias
    min/max 90d   = ventana de VENTANA_PERC = 90 dias

Con 19 días, esa mediana se calcula sobre lo que hay, y por eso ninguna pantalla la presenta como
«precio de siempre» sin decir sobre cuántos días se ha calculado.

## 8. El dinero, que no es un número como los demás

    precio_cent ∈ ℤ          los precios se guardan en centimos enteros
    precio_unidad_cent ∈ ℝ   el precio por unidad si puede ser decimal (2,99 € / 750 g = 3,99 €/kg)

En coma flotante binaria el 0,1 no existe exactamente: `0,1 + 0,2 = 0,30000000000000004`. Sobre
este catálogo, medido: sumar los 57.456 precios por unidad en coma flotante da
`117.089.350,04890001`, y redondear cada valor a dos decimales antes de sumar mueve el total
**1,41 céntimos**. Un céntimo y medio sobre 117 millones no rompe nada, y ese es el problema: el
error no avisa.

    Regla: el dinero se guarda en la unidad minima entera, se redondea UNA vez al final,
           y no se compara con == entre float.

## 9. La nota de calidad y las letras

    nota = 100
           − 6,0 · min(aditivos, 10)                        (hasta −60 por codigos E)
           − 15,0 · [lleva aceite de palma]
           − 1,5 · min(max(n_ingredientes − 5, 0), 15)      (hasta −22,5 por lista larga)
           + 0,3 · max(0, pct_principal − 50)               (100 % del principal suma 15)
    nota = min(100, max(0, nota))

Los pesos están a la vista a propósito: **un número que no se puede explicar no sirve para decidir
una compra**. Y las letras A/B/C se reparten por **terciles dentro del grupo**, no en abstracto: un
aceite de oliva virgen extra y un refresco no compiten. Con menos de tres productos con datos no se
reparte nada, porque inventar un tercil sobre dos productos es ruido con aspecto de dato.

## 10. Ausencia, y lo que cuesta taparla

    tasa de ausencia(columna) = 1 − ( filas con dato / filas totales )

Hoy: certificados 98,8 %, nutrición 93,3 %, Nutri-Score 85,4 %, envase 84,2 %, sellos 77,6 %, EAN
55,9 %, cantidad 17,2 %. Y el efecto medido de rellenar con ceros en lugar de dejarlo vacío:

    media del precio por unidad ignorando los 147 nulos     2.037,90 c
    media contandolos como cero                             2.032,70 c   (−5,2 c)

El sesgo siempre va en la misma dirección. La taxonomía de Rubin (1976) distingue si falta al azar
(MCAR), condicionado a lo observado (MAR) o por el propio valor (MNAR); el reparto de este catálogo
es MNAR de libro: **el que calla, calla por algo**.

## 11. La captura: ritmo, reintentos, huella y retos

Aquí no hay fórmulas de datos, y por eso va aparte: lo que hay son **dos números con teoría**
(el ritmo y la espera de un reintento) y tres mecanismos que se explican con palabras. Todo está en
`core/fetch.py` (el cliente) y `core/waf.py` (los retos), y el capítulo 15 cuenta el caso de cada
cadena.

### 11.1 El ritmo: intervalo, y ruido encima

    intervalo_minimo = 1 / ritmo                 (ritmo en peticiones por segundo)
    espera           = intervalo_minimo − transcurrido + U(0, 0,4 · intervalo_minimo)

El ruido aleatorio (`U` es una uniforme) no es decoración: una máquina que pide exactamente cada
1,000 s se delata por la regularidad. Con el ruido, el hueco medio pasa a ser 1,2 veces el
intervalo, o sea que el ritmo real es un 17 % más lento que el nominal. Los que usa cada cadena:

| Cadena | Ritmo | Por qué |
|---|---|---|
| mercadona, aldi | 2,0 /s | API pública, sin muro: el límite es la educación, no la defensa |
| carrefour | 1,0 /s | el `Crawl-delay: 60` de su `robots.txt` es de **TwengaBot**, no de `User-agent: *` |
| dia | 1,0 /s | Akamai: sin prisa, y el recorrido entero cabe en la noche |
| alcampo | 0,15 /s (una cada 6,7 s) | AWS WAF: a 1/s cortaba, y a una cada 4 s el reto escaló a pedir un clic humano |

Ese último número tiene su historia medida: bajar de 1/s a una cada 4 s **no bastó** — el 8 de
septiembre el reto pasó a pedir interacción humana tras siete cortes. Menos presión es la única
palanca que queda del lado del código, y a una cada 6,7 s el recorrido entero pasa de 27 a unos
45 minutos de trabajo real, que en una tarea nocturna no le importa a nadie.

### 11.2 Los reintentos: espera creciente con ruido, y una excepción

    se reintenta:  429, 500, 502, 503, 504   (y los fallos de red)
    espera:        min(Retry-After, 120 s)  si el servidor lo manda
                   si no: 2^intento + U(0,1)  ->  1-2 s, 2-3 s, 4-5 s
    NO se reintenta: 403

La espera creciente (backoff exponencial) con ruido es el patrón estándar: si el servidor está
saturado, insistir al mismo ritmo lo empeora, y el ruido evita que varios clientes reintenten a la
vez.

**El 403 no se reintenta aquí, y eso costó una medición.** Parecía obvio: Cloudflare y AWS WAF
contestan 403 cuando te tienen fichado un rato, y el 18 de septiembre el bloqueo de Carrefour se
levantó solo a los veinte minutos. Se puso una espera de 15 s y otra de 30 s por petición… y
medido contra un servidor de mentira que bloquea de verdad salían **45 segundos por categoría
bloqueada**: con las 373 de aquel día, cuatro horas y media durmiendo en una tarea que entera dura
38 minutos. El error de fondo era tener dos mecanismos esperando por lo mismo: **quien espera es el
colector**, que apunta las categorías fallidas y vuelve a por ellas en tandas, esperando una vez
para todo el grupo.

### 11.3 La huella: por qué `curl_cffi` y no un cliente HTTP normal

Antes de que el servidor lea una sola cabecera, el cliente y el servidor han hecho un saludo TLS, y
en ese saludo el cliente **elige** qué cifrados propone y en qué orden, qué extensiones manda y con
qué curvas. Esa lista la fija la librería y su versión, así que identifica al cliente igual que una
matrícula: es lo que se conoce como huella TLS (`JA3`, y su versión más fina `JA4`). Un cliente
HTTP de Python tiene una huella que **ningún navegador del mundo** tiene, y por eso Akamai (DIA)
puede decidir antes de mirar el `User-Agent`: la cabecera se escribe a mano, la huella no.

`curl_cffi` reproduce el saludo de un Chrome real (`impersonate="chrome131"`). No es magia ni
disfraz: es mandar el mismo saludo que mandaría el navegador de la casa.

Y una consecuencia que se paga en cookies: **la sesión es parte de la identidad**. El 20 de
septiembre el rescate de Carrefour creaba un `Fetcher` nuevo para ir más despacio, y las cuatro
categorías dieron 403 a la primera («rescatadas 0 de 4»): una `Session` nueva no lleva las cookies
(`__cf_bm` y compañía) que el recorrido se había ganado en media hora de navegación limpia. Ir más
despacio es una propiedad del ritmo, no de la identidad: se cambia el ritmo y **se conserva quién
eres**.

### 11.4 El reto: qué es un WAF y cómo se pasa

Cuando no hay testigo válido, AWS WAF no devuelve un 403 a secas: devuelve una **página de reto**
—un JavaScript que calcula algo y se lo devuelve al servidor— en vez del catálogo. El código la
reconoce por lo que trae dentro (`window.gokuProps`, `awsWafCookieDomainList`) y no por su tamaño.

    es_reto(html)  =  "gokuProps" in html  or  "awsWafCookieDomainList" in html

Después de resolverlo, la página deja cookies que valen horas (aquí se cachean 6 h) y **sí**
funcionan desde `curl_cffi`. De ahí la arquitectura: **un navegador al día, no uno por página.**

Cuatro detalles que se aprendieron fallando, y que son la parte aprovechable:

1. **Se valida por resultado, no por el nombre de la cookie.** Comprobar si existe
   `aws-waf-token` daba por mala una sesión que ya era buena; lo que se comprueba es que una página
   de categoría de verdad llegue **con datos**.
2. **Se copia el `User-Agent` del navegador.** El testigo va ligado al agente que lo obtuvo:
   mandarlo con otro agente lo invalida.
3. **La página de prueba tiene que ser una protegida** (una categoría, no la portada). Validar
   contra una página libre guarda una sesión inútil.
4. **Con ventana pasa más retos que sin ella** (medido: en modo sin ventana el WAF corta más a
   menudo). Por eso la tarea programada corre con sesión iniciada, y el modo sin ventana existe
   como opción consciente.

Y la medida que hoy deja claro qué es un reto: sin la sesión, la página de producto de Alcampo
devuelve **2.491 bytes**, que es el reto; con la sesión, sus endpoints de API responden. Eso es lo
que se encontró al verificar la ingesta del 24 de septiembre, y por eso la conclusión fue «esta
comprobación no puede leer esta cadena», no «el precio no está».

### 11.5 Lo que aquí no hay

No hay una fórmula para «parecer humano». Hay ritmo, ruido, sesión, persistencia y una regla que
está por encima de todas: **un reto no es un dato**, y quien no pueda distinguirlos debe decir «no
puedo comprobar esto» en vez de publicar un cero.

## 12. Las constantes, en una tabla

| Constante | Valor | Qué gobierna |
|---|---|---|
| `UMBRAL` | 0,55 | parecido mínimo para enlazar, con formato comprobado |
| `UMBRAL_SIN_FORMATO` | 0,82 | parecido mínimo cuando el formato no se puede comprobar |
| `PESO_TRIGRAMAS` | 0,85 | cuánto valen las letras frente a las palabras |
| `UMBRAL_UNION` | 0,80 | un enlace flojo no pega dos grupos ya formados |
| `ANCHO_MAXIMO` | 3,0 | un grupo no puede tener el más caro a más del triple |
| `FACTOR_PRECIO_IMPOSIBLE` | 30,0 | dos precios por unidad que no pueden ser el mismo producto |
| `FACTOR_INCREIBLE` | 30,0 | a partir de aquí no se da cifra de ahorro |
| `FACTOR_LLAMATIVO` | 3,0 | a partir de aquí la diferencia se enseña marcada |
| `MIN_IDF_ANCLA` | 4,0 | palabra lo bastante rara para buscar por ella (≤ 2.866 productos) |
| `RECORTE_MIN` / `RECORTE_MAX` | 1/3 / 3,0 | relativos que se recortan en los índices |
| `MINIMO_MOVIMIENTO_PCT` | 0,5 % | por debajo de esto es redondeo, no un movimiento |
| `VENTANA_BASE` | 30 días | mediana móvil del «precio de siempre» |
| `VENTANA_PERC` | 90 días | ventana del mínimo y el máximo |
| `TOPE_API` (Alcampo) | 300 | productos por respuesta: al llegar al tope, hay que bajar al subárbol |
| `TERMINOS_POR_DIA` (Alcampo) | 600 de 5.153 | términos de búsqueda que se recorren cada día, en turnos de ~9 días |
| `RITMO` | 2,0 / 1,0 / 0,15 | peticiones por segundo, por cadena (el 0,15 es Alcampo, con WAF) |
| ruido del ritmo | hasta 40 % del intervalo | evita pedir exactamente cada 1,000 s |
| reintentos | 3, con `2^intento + U(0,1)` | 1-2 s, 2-3 s, 4-5 s; nunca para un 403 |
| `VIDA_SEGUNDOS` (WAF) | 6 h | cuánto vale en caché la sesión del navegador |
| `DIAS_RAW` | 30 | días de crudo que se conservan (lo que se puede reprocesar) |

## 13. Lo que este anexo no tiene

No hay una fórmula para decidir **cuándo** alguien es el mismo producto: hay una puntuación, unos
frenos y unas invariantes. Tampoco hay una fórmula para la exactitud de un dato, porque no se puede
medir desde dentro (capítulo 13). Y no hay ninguna fórmula que sustituya a mirar los casos: casi
todos los números de esta página se pusieron mirando **qué pares concretos** cambiaban al moverlos,
y las mediciones están citadas donde están las constantes.

> **La lección:** una fórmula sin su unidad, su umbral y su medición al lado es una opinión escrita
> en símbolos. Las de esta página se pueden discutir porque cada una dice de dónde viene y cuánto
> vale aquí.
