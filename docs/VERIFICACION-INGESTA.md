# Verificación de la ingesta — 24 de septiembre de 2026

Una pregunta distinta de todas las que el proyecto se hacía hasta ahora: **¿lo que la cadena nos
dio hoy llegó entero al catálogo?** Los controles que había miraban el total (`runlog`), las ramas
que desaparecen (`cobertura`), los campos que no se leen (`auditar_crudo`) y los precios que no
cuadran con la web (`verificar_precios`). Ninguno contestaba esa.

Se ha escrito para ello `projects/cesta/verificar_ingesta.py`, que compara **el crudo del día**
(lo que la cadena dijo) contra **bronze** (lo que guardamos), y las cuatro cosas que puede
comprobar sin salir a la calle: productos, categorías, paginación y enlaces. Va aparte de los
documentos de aprendizaje: esto es el registro de trabajo, no el material de estudio.

    uv run python -m projects.cesta.verificar_ingesta
    uv run python -m projects.cesta.verificar_ingesta --fecha 2026-09-23
    uv run python -m projects.cesta.verificar_ingesta --fuente dia

Sale 0 si todo cuadra, y si no, cuántos problemas hay. **Hoy sale 0.**

---

## 1. El veredicto del día, cadena por cadena

| Cadena | Respuestas | Categorías declaradas | Productos declarados | En bronze | Faltan | Sobran | Páginas declaradas/pedidas | Enlaces |
|---|---:|---:|---:|---:|---:|---:|---|---|
| alcampo | 544 | 2.953 | 28.977 | 28.977 | 0 | 0 | — | 0 sin url, 0 sin su id |
| aldi | 105 | 2.069 (sitemap) | 2.069 | 2.066 | 3 | 0 | — | 0 sin url, 0 sin su id |
| carrefour | 2.100 | 685 | 16.462 | 16.452 | 10 | 0 | 2.065 / 2.065 | 0 sin url, 1.212 con otro id |
| dia | 527 | 289 | 5.789 | 5.789 | 0 | 0 | 520 / 520 | 0 sin url, 0 sin su id |
| mercadona | 156 | 620 | 4.319 | 4.319 | 0 | 0 | — | 0 sin url, 0 sin su id |
| **total** | **3.432** | | **57.616** | **57.603** | **13** | **0** | | |

Los 13 que faltan son **13 con explicación**, y ninguna es «se perdió»:

- **3 de Aldi**: el id está en el sitemap de productos de la cadena y no en ninguna respuesta de
  precios de su API. La cadena publica la ficha, pero no le da precio (agotado o sin precio
  publicado). Un producto sin precio no es un dato de precio: no hay nada que guardar.
- **7 de Carrefour**: aparecen en el **texto** de una página con rejilla pero no dentro de la
  rejilla. Son los bloques de recomendaciones, que traen productos de otras categorías. Se
  guardan los de la rejilla, y eso es lo correcto.
- **3 de Carrefour**: solo aparecen en páginas que la cadena sirve **sin rejilla** (`"plpData":{}`:
  páginas de marca o de campaña). El colector las cuenta en `sin_catalogo` y lo imprime; hoy:
  «10 categorías sin rejilla de productos (marca o vacías)».

El detalle que hace útil la herramienta no es el 0: es que **explica los 13**. Un producto
declarado y no guardado es un fallo solo si nadie puede decir por qué; por eso el informe separa
«con explicación» de «sin explicación», y la primera versión de la herramienta lo hizo mal —decía
«3 con explicación» y a la vez «3 sin explicación», porque restaba un diccionario de recuentos de
un conjunto de ids—. Está fijado en `tests/test_verificar_ingesta.py`.

**Nada sobra** en ninguna cadena: no hay filas en bronze que no salgan del crudo de hoy, o sea
que ningún bronze se escribió desde una caché de otro día.

## 2. Los enlaces: 57.603 de 57.603

     filas sin enlace                                     0
     enlaces repetidos                                    0
     enlaces fuera del dominio de su cadena                0
     enlaces que no llevan su propio id                    0   (donde lo construimos nosotros)

La última línea es la comprobación que faltaba el 21 de septiembre, cuando los **23.776 enlaces de
Alcampo** daban 404 porque la URL pública lleva el `retailerProductId` y guardábamos el
`productId` — un UUID interno. El precio estaba bien y el catálogo parecía bien: un enlace roto
solo se nota cuando una persona lo pulsa.

Y tiene una excepción que hoy está medida: **Carrefour publica su enlace como `R-<referencia>`**,
así que su `product_id` (el que guardamos como `id_fuente`) **no aparece** en la URL. Le pasa a
1.212 filas de 16.452 (el 7,4 %). Ahí el enlace no lo construimos nosotros: lo da la cadena en su
propia respuesta, y comprobarlo es cosa de `verificar_precios.py`, que sale a la calle. Exigirle
el id daría 1.212 falsas alarmas al día y acabaría con la comprobación desactivada.

## 3. Lo que dicen las cadenas cuando se les pregunta por sus categorías

### Alcampo: 34 categorías que no se piden, y **0 productos perdidos**

`auditar_recorrido.py` dice que su árbol declara 2.953 categorías, que se pidieron 544 respuestas
y que **34 categorías no se pidieron ni llegaron por otro camino**. Eso suena a pérdida, así que se
preguntó a Alcampo, una a una, con su sesión del WAF (que hoy seguía viva):

    de 34 categorias: 34 con productos, 485 productos devueltos

Las 34 tienen productos (la mayor, `OCSINGSINL` «Sin Gluten / Sin Lactosa, Nutrición deportiva y
Funcional», 300 — el tope de su API). Y al cruzar esos productos con bronze, **por id** (477 ids
distintos: el recuento en vivo cuenta filas de sus bloques, el cruce cuenta identificadores):

    productos que Alcampo devuelve en esas 34 categorias   477
    de ellos, en bronze                                    477
    QUE FALTAN DEL CATALOGO DE HOY                            0

**Lo que se pierde no son productos: es la etiqueta.** Los 477 productos están en el catálogo,
pero etiquetados con la ruta de su categoría padre (llegaron por el barrido de términos de
búsqueda, 600 de 5.153 al día, o dentro de la respuesta de un padre cuyo subárbol cabe entero).
Consecuencia real: quien filtre por «Helados veganos» no los encuentra bajo ese nombre. Es un
problema de navegación, no de dato.

Y esto no es nuevo: el 17 de septiembre de 2026 la misma herramienta contaba **32** de estas
categorías, y están escritas en `docs/AUDITAR-RECORRIDO.md` — «Sin Gluten / Sin Lactosa», «Arroz
Ecológico», «Pollo Ecológico», «Sobrasada», «Bebidas de avena veganas». Hoy son 34, con los mismos
nombres dentro. Lo que cambia con esta comprobación es la lectura: la mitad de esas categorías son
**de dieta**, justo donde los sellos importan, y **sus productos sí están** en el catálogo desde
que se arregló el nodo de navegación vacío; lo que sigue faltando es la palabra que los agrupa.

Nota de método: esa comprobación en vivo guardó 34 respuestas dentro de `raw/2026-09-24`, y eso
**ensuciaba la evidencia del día** (el recorrido de hoy no pidió esas categorías, y el crudo tiene
que seguir diciendo eso). Se movieron a `data/debug/verificaciones/2026-09-24/`.

### Mercadona: la categoría 491 «Pizzas refrigeradas», que sí llega

`auditar_recorrido.py` marca 1 categoría que «no llega de ninguna forma». Comprobado a mano: la
491 es una categoría de **tercer nivel dentro de la 138**, y sus **24 productos están en bronze**
(los 24 de 24). Lo que no llega es el **nombre** de la subcategoría como etiqueta, porque el
colector etiqueta todo lo de la 138 con el nombre del nivel 2. Es la misma clase de hallazgo que
Alcampo, y aquí en pequeño: en bronze hay 26 categorías distintas de Mercadona, que son sus 26
niveles 2.

### Carrefour: 2.065 de 2.065 páginas, y 22 categorías que su padre sirve

- **Paginación completa**: la suma de páginas que declaran sus 685 categorías es 2.065, y se
  pidieron 2.065. Ni una cortada.
- **22 categorías «redirigen a la de su padre»**: la dirección ya no existe y Carrefour contesta
  con la de su rama. El colector lo detecta por el `navigation_id` y deja de paginar; la rama sí
  se recorre por su cuenta. Sin mirarlo, se leían 42 páginas del padre por cada hija difunta
  (medido el 19 de septiembre: 531 de 2.634 páginas, el 20 % de lo pedido).
- **4 categorías rotas en origen** (`HTTP 500`/`520`, papelería y congelados): están declaradas en
  `ROTAS_EN_ORIGEN` con su nombre, y no cuentan como fallo nuestro. El registro del día las lista.

### DIA: 520 de 520 páginas, y 3 direcciones de su propio sitemap que dan 404

El sitemap de DIA lista 289 categorías; 3 de ellas responden **404** —su propio índice publica
direcciones que ya no sirve, y dos son alias del mismo código (`L2176`)—. El registro del día lo
dice con esas palabras: «3 categorías del sitemap ya no existen». Desde fuera no se puede
distinguir «no se pidió» de «la cadena la sirve rota», así que la herramienta las cuenta aparte y
no como problema.

### Aldi: su sitemap es el catálogo

2.069 direcciones de producto, 2.066 con precio en su API (los 3 de arriba). No hay paginación
que auditar: el sitemap es la lista entera.

## 4. Comprobar los precios en las cadenas: los dos puntos ciegos, cerrados

    uv run python -m projects.cesta.verificar_precios --por-cadena 10

**Antes** (24 de septiembre de 2026, con el comprobador tal y como estaba):

    dia        10/10 coinciden
    carrefour   9/10  (1 no se pudo: la red)
    mercadona   9/10  (1 no aparece: producto al peso, 0,64 nuestro contra 0,62 en su API)
    alcampo     3/10  (7 sin precio)
    aldi        0/10  (10 sin precio)

Los dos últimos números **no decían que el dato estuviera mal**: decían que la comprobación
no podía leer esas páginas.

    aldi      la pagina del producto (70 KB de HTML) no trae ni una cifra con simbolo de euro:
              su precio lo pinta el navegador pidiendoselo a su API
    alcampo   la respuesta son 2.491 bytes: es el reto del WAF, porque la comprobacion no lleva
              la sesion que el colector si tiene

**Ahora** (26 de septiembre de 2026, los dos cerrados):

    alcampo    0/10 coinciden   10 sin poder comprobar por el reto del WAF
    aldi      10/10 coinciden
    carrefour 10/10 coinciden
    dia       10/10 coinciden
    mercadona 10/10 coinciden

    salida del programa: 0   (ningun precio mal)

Lo que se cambió, y son dos cosas distintas:

- **Aldi se pregunta a su API** (`/api/product/pds/<id>?scope=es_pen`), que es la misma que usa
  su web. De 0/10 a 10/10 sin tocar ningún precio.
- **Alcampo se pide con la sesión del WAF** que ya tiene el colector. No es reutilizar su
  lector —eso seguiría prohibido, y por eso el precio se sigue leyendo a ojo de persona—, es
  usar el mismo transporte: sin la cookie, la página del producto no llega.
- Y cuando aun así llega el reto, el estado es **`reto`**, no `sin precio`. Un punto ciego del
  instrumento contado como un problema del dato fue lo que dejó a Alcampo en 3/10 y a Aldi en
  0/10 pareciendo un suspenso de sus precios. Ahora sale en su propia línea («10 sin poder
  comprobar por el reto del WAF: eso no dice nada de su precio») y **no cuenta como fallo**: la
  salida del programa es el número de precios que no cuadran, y eso no cambió.

Los diez de Alcampo de hoy están sin comprobar porque el WAF está respondiendo el reto en este
momento (se le ha pedido bastante durante la investigación del barrido): es exactamente el caso
que el estado nuevo existe para decir en voz alta.

### Lo que sí se pudo comprobar, y se comprobó el 24 de septiembre

- **Aldi, el enlace**: el nombre del producto aparece en su página en **8 de 8** que se miraron.
  Los enlaces llevan donde tienen que llevar.
- **Alcampo, la API**: con la sesión del WAF (la del colector), la API responde — así se
  comprobaron las 34 categorías y sus 477 productos.
- **Mercadona, el que no cuadra**: es un producto al peso (pimiento verde), y su precio cambia con
  el peso de la pieza del día. Es la clase de diferencia que hay que esperar, no un fallo de
  lectura.

## 5. Los 1.276 precios que no están, y por qué no se rellenan

    filas sin precio en gold    1.276 de 57.603   (2,2 %)
      alcampo  1.129   las 1.129 son producto AL PESO (peso_variacion_pct no nulo): su web no
                       publica precio hasta que se pesa (calamar, salmón en rodajas, fruta)
      aldi       147   fichas que su API devuelve sin precio (tomate pera, manzana, ajo...)

La regla de la casa se cumple: un precio que no está es `null`, **nunca un cero**. Un `0,00 €` se
leería como «gratis» y arrastraría las medias hacia abajo (medido: rellenar con cero baja la media
del precio por unidad 5,2 céntimos).

## 6. Lo que queda abierto de este día

1. **44 respuestas de Alcampo llegaron al tope de 300 productos** de su API. Una categoría que
   devuelve exactamente el tope puede estar cortada; el colector las cubre con el barrido de
   términos de búsqueda, pero **no se puede saber desde el crudo si falta algo**. La forma de
   cerrarlo es pedir esas 44 categorías con paginación propia y contar.
2. **Las etiquetas de las subcategorías** (Alcampo 34, Mercadona 1): los productos están, el
   nombre de su categoría fina no. Afecta a la navegación por pasillo, no a los precios.
3. **DIA publica 3 direcciones muertas en su sitemap**: no es nuestro, pero conviene no contarlas
   como categorías del día.
4. **Los enlaces de Carrefour con otro id: comprobados, y no están rotos.** Eran 1.212 el 24 de
   septiembre y son **1.238 hoy**, y se han pedido de verdad (que es lo único que puede
   juzgarlos, porque el enlace lo da la cadena). Resultado de hoy:

       uv run python -m projects.cesta.verificar_ingesta --fuente carrefour --enlaces 30

       enlaces: sin url 0  sin su id 1.238  fuera de su dominio 0  repetidos 0
       enlaces pedidos de verdad: 30 de 30 responden y llevan su producto
       sin problemas

   Y en la pasada completa, 8 por cadena: los 8 de Carrefour bien. La comprobación quedó como
   opción (`--enlaces N`) para que se pueda repetir sin depender de que alguien se acuerde: en
   `--enlaces 0` (por defecto) el informe sigue siendo de solo lectura y no pide nada.

## 7. Cómo se reproduce

    uv run python -m projects.cesta.verificar_ingesta          # crudo vs bronze, 0 si todo cuadra
    uv run python -m projects.cesta.verificar_ingesta --enlaces 30   # y 30 enlaces de verdad
    uv run python -m projects.cesta.auditar_recorrido          # que categorias no se pidieron
    uv run python -m projects.cesta.verificar_precios --por-cadena 10
    uv run pytest tests/test_verificar_ingesta.py -q

Los cuatro son de solo lectura: no piden nada a las cadenas salvo `verificar_precios`, que pide 10
páginas por cadena y las pide despacio (0,5 por segundo), y `verificar_ingesta --enlaces N`, que
pide exactamente N enlaces y a ese mismo ritmo.
