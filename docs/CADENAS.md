# Cesta — que publica de verdad cada supermercado

Medido el 15 de septiembre de 2026 sobre `data/silver/`, 407.099 filas de nueve
dias. No es lo que prometen sus webs: es lo que aparece en el parquet.

La tabla es el documento. Todo lo demas son consecuencias de ella.

---

## 1. La tabla

Porcentaje de productos de cada cadena que traen el campo relleno.

    campo                        ALCAMPO   ALDI  CARREF    DIA   MERCA
    productos/dia                 23.591  2.100  16.464  5.389   4.319
    ---------------------------------------------------------------
    nombre                           100    100     100    100     100
    marca                            100      0      99     97      85
    precio_cent                      100     93     100    100     100
    url                              100    100     100    100     100
    categoria (arbol propio)         100     95     100    100     100
    disponible                       100    100     100    100     100
    ---------------------------------------------------------------
    formato_txt                       73     94       0    100     100
    cantidad_declarada                 0      0       0    100      99
    unidad_declarada                   0      0       0    100     100
    ---------------------------------------------------------------
    precio_ref_nativo_cent           100     83     100    100     100
    unidad_ref_nativa                100*    82     100    100     100
    ---------------------------------------------------------------
    ean                                0      0      93    100      89
    ingredientes                       0      0       0     76      57
    alergenos                          0      0       0     20      58
    nombre_legal                       0      0       0     77      68
    proveedores_txt                    0      0       0     76      65
    origen                             0      0       0      0      30
    ---------------------------------------------------------------
    imagen                           100*   100     100    100     100
    iva                                0      0       0    100     100
    es_pack                            0      0       0      0     100
    promo (si/no)                    100    100     100    100       0
    promo_txt                         12      8       0      0       0
    promo_hasta                        0     93       0      0       0
    precio_anterior_nativo_cent        0      8       0    100       4

    * corregido el 15 de septiembre; antes 17 % y 0 %. Ver punto 4.

---

## 2. Las tres consecuencias que mandan sobre el diseno de la app

### 2.1 Media plantilla no tiene codigo de barras

Alcampo y Aldi no publican EAN. Son 25.638 de 51.781 productos: **el 50 % del
catalogo**.

El EAN es la unica forma de decir "este producto es exactamente este otro" sin
dudar, y es la llave para cruzar con Open Food Facts. Sin el:

- Alcampo y Aldi solo se emparejan por nombre, formato y cantidad, que es lo que
  hace `core/matching.py`. Mide un 57 % de aciertos contra pares conocidos.
- Alcampo y Aldi **nunca** tendran Nutri-Score, NOVA ni lista de ingredientes,
  porque OFF se cruza por EAN y no hay otra llave fiable.

No es un fallo que se arregle programando mejor. Es lo que hay en la fuente.

### 2.2 La informacion nutricional solo existe en tres cadenas, y a medias

    ingredientes en la ficha de la cadena    DIA 76 %, Mercadona 57 %, resto 0 %
    Nutri-Score tras cruzar con OFF          Carrefour 4.824, DIA 2.047,
                                             Mercadona 1.487, Alcampo 0, Aldi 0

De 51.781 productos, **8.359 tienen Nutri-Score** (16 %) y **9.754 tienen letra
de calidad** (19 %).

Esto obliga a una decision de interfaz: el filtro "solo Nutri-Score A o B" no
puede comportarse como un filtro normal, porque escondería el 84 % del catalogo
sin decir por que. Tiene que ensenar, junto al resultado, cuantos productos se
quedaron fuera **por no tener el dato** y no por tener mala nota.

### 2.3 El origen nacional practicamente no existe

Solo Mercadona lo declara, y en el 30 % de sus productos. Las otras cuatro, cero.

Son 1.444 productos de 51.781: **el 2,5 %**. El filtro "producto nacional" que
pediste, hoy, con datos propios, no se sostiene.

**Medido el 15 de septiembre contra el volcado entero de Open Food Facts**, que
era la esperanza: de nuestros 12.835 productos que cruzan con OFF, solo **1.248
traen `origins_tags`**, y de esos apenas **635 dicen `en:spain`**.

    origen declarado por la cadena       1.444 productos
    + lo que anadiria Open Food Facts      635
    -------------------------------------------
    techo realista                      ~1.900 de 51.781   (3,7 %)

Asi que la respuesta es **no**: el filtro de producto nacional no se puede
construir con las fuentes disponibles. Se deja escondido y se dice por que.

Lo que **si** aporta Open Food Facts y no estamos trayendo:

    tabla de nutrientes completa (kcal, grasas, azucares, sal)   11.723
    categorias                                                  10.209
    sellos                                                       8.055
      sin gluten 2.667 | ecologico 1.205 | vegano 763
      sin lactosa 717 | sin aceite de palma 267

Los sellos son el hallazgo util: dan filtros que la gente busca de verdad, y con
mas cobertura que el origen. Son tres lineas en `CAMPOS` de `core/off.py`.

---

## 3. Ficha por cadena

### Alcampo — 23.591 productos, el catalogo mas grande
API interna de listado (`productGroups[].decoratedProducts[]`), tras AWS WAF.

    da bien       nombre, marca, categoria completa (`categoryPath`),
                  precio, precio por kilo/litro, imagen, promociones con texto
    no da         EAN, ingredientes, alergenos, origen, IVA
    rareza        publica el precio de referencia en cuatro escalas distintas
                  (kg, litro, 100 g, 100 ml, unidad, docena, metro) y con dos
                  nombres para la misma unidad: `unit` y `unitName`
    formato       `packSizeDescription` en el 73 %; el resto hay que sacarlo del
                  nombre

### Aldi — 2.100 productos, el mas pequeno
Web publica, sin defensas.

    da bien       nombre, formato (94 %), imagen, fecha de fin de promocion (93 %)
    no da         marca (0 %: todo es marca propia y no la nombra), EAN,
                  ingredientes, origen
    rareza        su precio de referencia mezcla `100-g` y `100-ml` con precios
                  que a veces ya vienen por kilo. 154 de 173 casos necesitan x10
                  y 16 no. Se decide fila a fila contra el precio del producto.
    consecuencia  sin marca y sin EAN, Aldi es la cadena mas dificil de emparejar

### Carrefour — 16.464 productos
Sitemap + paginas, tras Cloudflare.

    da bien       EAN (93 %), marca, imagen, precio por unidad siempre
    no da         formato como campo (0 %), ingredientes, origen, IVA
    rareza        el formato hay que leerlo del nombre. Se recuperan 11.004 de
                  14.833 casos, validando contra su propio precio por kilo con
                  un 5 % de tolerancia
    fragilidad    el sitemap dio 403 los dias 11 y 12 de septiembre. Ahora hay
                  respaldo: si hoy no se deja, se usa la captura mas reciente

### DIA — 5.389 productos, el mas completo
API interna, tras Akamai.

    da bien       EAN (100 %), formato estructurado (cantidad + unidad, 100 %),
                  ingredientes (76 %), nombre legal, proveedor, IVA, imagen,
                  precio anterior (100 %)
    no da         origen
    valor         es la cadena de referencia para validar el resto: cuando hay
                  que comprobar si un formato esta bien leido, se compara aqui

### Mercadona — 4.319 productos
API interna, sin defensas.

    da bien       EAN (89 %), formato estructurado, ingredientes (57 %),
                  alergenos (58 %), IVA, `es_pack`, imagen, **origen (30 %,
                  unico que lo da)**
    no da         campo de promocion (0 %)
    trampa        vende un pack de 6 rollos como "1 ud" y publica el precio
                  **por rollo**. Por eso la unidad `ud` no se compara entre
                  cadenas: medido, 24 % de diferencia mediana y 128 casos
                  imposibles de 550. Solo kg, l y m entran en `comparacion_fiable`

---

## 4. Cuatro fallos encontrados al medir, y corregidos hoy

### Alcampo: el precio por kilo y la imagen

En `projects/cesta/collectors/alcampo.py`.

**El precio por kilo de Alcampo se estaba tirando a la basura.** Su API manda la
unidad en dos campos: `unit` (`"fop.price.per.100ml"`) y `unitName`
(`"PER_100ML"`). El codigo leia `unitName`, que no estaba en el mapa de unidades.
Resultado: solo el 17 % de Alcampo tenia precio de referencia, y era el que
llegaba por la ruta HTML antigua.

Medido sobre 14.887 productos del 14 de septiembre:

    unidad de referencia    17,2 %  ->  100,0 %
    comparable en kg o l    ~17 %   ->   79,3 %

De paso se convierten a kilo y litro los precios que publica por 100 g (61
casos) y por 100 ml (1.206 casos), que antes habrian entrado con un valor diez
veces menor.

**Y no se guardaba la imagen.** `image.src` viene en el 100 % de los productos y
la linea que lo copiaba no existia.

Siete pruebas nuevas en `tests/test_alcampo.py` cierran las dos puertas.

Alcampo es el 45 % del catalogo. Esto no es un retoque: es la mitad del
comparador que estaba funcionando a ciegas.

### Aldi: la marca, que si la publica

En `projects/cesta/collectors/aldi.py` la linea decia:

    "marca": None,   # Aldi no separa la marca del nombre

Si la separa. `brandName` viene en el **91,2 % de sus productos** y hay **229
marcas distintas**: MILSANI (138), LACURA (133), LA TABLA (103), CHOCEUR,
TRADER JOE'S... Casi todas son marca propia de Aldi, que es justo lo que hace
falta saber para compararla con Hacendado o con Carrefour.

    marca en Aldi    0,0 %  ->  91,2 %

Se le quita el simbolo de marca registrada, que estorba al emparejador. Tres
pruebas en `tests/test_colectores.py`.

### Todas: los packs que solo se anuncian en el nombre

DIA publica "Cerveza sin filtrar 0,0 El aguila pack 24 x 33 cl" con
`formato_txt` **"33 cl"**. El pack solo esta en el nombre, asi que nos salian
**64,73 EUR/l** cuando la propia web de DIA dice **2,70**. Un error de 24 veces.

    productos con "pack N x" en el nombre y sin multiplicar     211
      DIA                                                       183
      Alcampo                                                    25
      Carrefour                                                   3

Arreglado en `projects/cesta/pipeline.py`, con la misma disciplina que la regla
de Carrefour: el nombre no decide solo. Solo se multiplica si al hacerlo el
precio por unidad **cuadra al 5 % con el que publica la propia cadena**.

    se corrigen (cuadran)     110
    se dejan como estaban     101

Los 101 restantes no validan, asi que se quedan igual: mejor un dato viejo que
uno inventado. Cuatro pruebas en `tests/test_pipeline.py`.

### DIA: la categoria es una URL

`categoria` en DIA vale `https://www.dia.es/congelados-y-helados/tartas-y-churros/c/L2136`
en vez de un arbol. Se puede leer el arbol de esa URL, pero no esta hecho.
Alcampo es el que tiene el arbol mas rico ("Alimentacion > Aperitivos... > ...")
y es el que conviene usar como base de la categoria canonica.

---

## 5. Lo que hay que arreglar en el dato, por orden

1. **Los grupos demasiado anchos.** Es lo que mas bloquea, mas de lo que parecia.
   El grupo de agua con gas mas disperso mete Perrier (2,40 EUR/l) con la marca
   blanca de Carrefour (0,28), con todos los formatos bien leidos. No es un fallo
   de formato: es que "equivalente" se esta estirando demasiado. Mientras siga
   asi, cualquier cifra de "diferencia de precio por seccion" mide la anchura del
   grupo y no el ahorro.
2. **Traer de Open Food Facts los nutrientes, las categorias y los sellos**
   (punto 2.3). Tres lineas en `CAMPOS` de `core/off.py` y desbloquea tanto los
   filtros utiles como la categoria canonica.
3. **Categoria canonica**, heredando de OFF donde cruce (10.209 productos) y del
   arbol de Alcampo donde no, que es el mas rico. Sin esto no hay "Explorar" ni
   analisis por linea de producto.
4. **Volver a medir el emparejador** (57 % de aciertos) ahora que Alcampo tiene
   precio por kilo y Aldi tiene marca. Las dos cosas alimentan directamente al
   emparejador, asi que deberia subir.
5. **Sondear las fichas de Alcampo y Aldi** con
   `projects/cesta/sondear_fichas.py`, para saber de una vez si publican EAN o
   nutricion en algun sitio que no estemos pidiendo. Si lo hacen, un maestro
   incremental calcado al de DIA cubre el catalogo en unas semanas sin que se
   note. Si no, se deja escrito y se deja de buscar.
6. **La categoria de DIA, que es una URL** y deberia ser un arbol.
7. **La letra de calidad que en realidad es el precio.** No es un fallo de dato,
   es un fallo de como se ensena: ver `DASHBOARD.md` estudio 3.2.
