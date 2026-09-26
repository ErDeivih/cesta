# El auditor del crudo

Escrito el 17 de septiembre de 2026, despues de que **siete veces seguidas**
apareciera un dato guardado en `data/raw` que ningun colector leia.

---

## 1. El patron que hay que romper

| dia | lo que estaba guardado y no se leia | efecto al leerlo |
|---|---|---:|
| 10 sep | el precio por kilo de Alcampo | 17,2 % → 100 % |
| 11 sep | la marca de Aldi (el comentario decia que no la publicaba) | 0 % → 91 %, 229 marcas |
| 13 sep | los packs de DIA anunciados solo en el nombre | 211 productos |
| 15 sep | las ofertas de Carrefour, con su fecha de fin | 3.387 productos |
| 16 sep | la tabla nutricional de DIA | 3.723 productos |
| 17 sep | los 32 certificados de Aldi | 1.106 productos |
| 17 sep | el envase y la conservacion de Mercadona | 3.452 / 1.785 |

Siete de siete. Eso ya no es mala suerte: **es que nadie mira**. Y mirar a mano
depende de que a alguien se le ocurra, que es justo lo que no se puede
planificar ni delegar.

    uv run python -m projects.cesta.auditar_crudo
    uv run python -m projects.cesta.auditar_crudo --fuente dia --minimo 5

---

## 2. Que hace, exactamente

1. Abre el crudo del ultimo dia de cada cadena y saca los productos **con el
   parser de verdad** (`productos_crudo`, el mismo que usa el reprocesador).
2. Aplana cada producto a rutas con puntos -- `currentPrice.validUntil`,
   `allergens[].name` -- y cuenta en que porcentaje de productos tiene valor.
3. Lee el **codigo fuente** del colector y saca todas las claves que pide, esten
   como `.get("x")` o como `p["x"]`.
4. Enseña lo que pasa del umbral y no aparece en el codigo.

Es una heuristica, no un demostrador: una clave leida a traves de una variable no
se ve, asi que puede avisar de algo que si se lee. **Falla hacia el lado bueno**
-- avisa de mas, nunca de menos -- que es lo que interesa en una auditoria.

---

## 3. Lo que encontro en su primera pasada

Cinco cadenas, media hora. Estos son los que valian la pena, ya cableados:

### DIA — el texto de sus ofertas, que no teniamos

`promotions[].description`: **221 productos** con "2ª UD AL 70% DTO.", "25% DTO",
"SOLO 2,59 EUR". DIA era la unica cadena con ofertas y sin texto de oferta, o sea
la unica a la que no se le podia aplicar `core/promos.py`.

Y lo importante: **200 de las 221 son `only_club_dia`**, solo con tarjeta. En el
proyecto ya estaba decidido que un descuento de tarjeta no baja lo que pagas en
caja (se acumula en un monedero). Sin la columna `promo_club`, anadir el texto de
DIA habria hecho que la app anunciara **200 rebajas que no estan en el ticket**.

### DIA — 1.078 sellos mas, en un campo con el nombre equivocado

`allergens[].name` **no son alergenos**: son 1.177 productos etiquetados "Sin
gluten" (1.081), "Sin lactosa" (296) o "BIO" (46). Y `product_info` trae 336 mas.
DIA tenia 147 sellos, todos leidos de los nombres; ahora tiene 1.225.

### DIA — "Mejor valorado", la unica senal de popularidad del proyecto

`stamp_description`: 282 productos "Mejor valorado", 168 "Novedad", 82 "Air
Fryer", 18 "Precio destacado". Ninguna cadena publica ventas ni resenas que
sirvan, asi que esto es lo unico que hay para ordenar entre dos productos
equivalentes.

### Alcampo — el rango real de lo que se vende al peso

`catchweight`: **742 productos** con minimo, tipico y maximo. Un tomate "al peso"
de 500 g que puede venir entre 375 y 625. Son exactamente los productos donde el
precio total es una estimacion, y ahora la ficha dice de cuanto: "ronda los 500 g
y puede variar un 25 %; el precio por kilo es exacto, el total una estimacion".

### Alcampo — la fecha de fin de sus ofertas, dentro del texto

Alcampo tenia 3.125 textos de oferta y **cero** fechas de fin. La fecha va dentro
del texto: `"Producto en Folleto (10/09/26_23/09/26)"`. El 61 % la lleva, o sea
**1.904 productos**.

Para leerla hubo que arreglar dos veces el mismo tipo de error: `\b` no delimita
numeros pegados a puntuacion. `"Todo a 1€ (...)"` no casaba porque el simbolo del
euro no es caracter de palabra, y `"(10/09/26_23/09/26)"` no casaba porque el
guion bajo **si** lo es. Los dos arreglados con miradas `(?<!\d)` / `(?!\d)`.

### Alcampo — los pictogramas de peligro

`icons[].label`: **450 productos** de limpieza con "Corrosivo para la piel, ojos
y/o metales", "Peligro para el medio ambiente", "Inflamable". El tipo dice
`CERTIFICATION` y no certifican nada: avisan. Importa en una casa con ninos, y no
lo ensena ninguna app.

### Mercadona — el peso escurrido de verdad

`price_instructions.drained_weight`: **179 productos**. Es la columna que DIA parecía dar al 100 %
y resultó ser otra cosa (ver `docs/AUDITORIA.md`, punto 6), y **desde el 26 de septiembre de 2026 se
usa para calcular**: el precio por kilo de esos 179 va sobre el escurrido, porque comparar un bote
de aceitunas por su peso total con otro que declara el escurrido da un «más barato» que no existe.
La medición completa (antes 1 de 18 grupos dentro del ±20 % de la mediana de las otras cadenas;
después 13 de 18) está en `docs/DATOS-QUE-NO-COGEMOS.md`, punto 5 bis, y se repite con
`uv run python -m projects.cesta.auditar_escurrido`.

### Aldi — el aviso de retirada de producto

`isRecall`, en sus 2.065 productos. Hoy vale `false` en todos, y aun asi es la
funcionalidad **que ninguna app de la competencia tiene**: sabemos exactamente
que hay en cada lista de la compra. Cuando deje de ser cero, la ficha lo dice en
rojo y arriba.

---

## 4. Lo que encontro y se descarto, con el numero al lado

Igual de util. Para que nadie lo vuelva a intentar:

| campo | cadena | por que no |
|---|---|---|
| `ratingSummary` | alcampo | 1.060 productos con **1.260 votos en total** y mediana de UN voto. "4 estrellas" con un voto no es una valoracion, es ruido |
| `badge.description` | carrefour | nunca aparece sin `badge_map.promotions`, y de las 102 insignias que `promos.lee()` no entiende no rescata **ninguna**: son "Envio Gratis", "XXL Ahorro", "Super Precio" |
| `envase` como bloqueo del emparejador | todas | de los 980 enlaces con envase en las dos puntas, **372 (38 %) no coinciden**, y son el mismo producto con distinta palabra: las mismas barritas son "bolsa" y "paquete" |
| `longDescription` | aldi | existe en el 79,2 % y es "El precio puede variar para las tiendas de Baleares" el 99,3 % de las veces |
| `productReferences` | aldi | solo `KVArticleNumber`, su codigo interno. **Aldi no tiene EAN**, comprobado en los 2.065 |

---

## 5. Lo que queda por cablear, con su medicion

Todo esto ya esta medido y guardado; falta decidir y hacer.

| campo | cadena | productos | para que |
|---|---|---:|---|
| `price_instructions.total_units` | mercadona | 1.320 | el numero REAL de unidades de un pack, que hoy se adivina con `unidades_inferidas` |
| `price_instructions.pack_size` | mercadona | 522 | el tamano de cada unidad dentro del pack |
| `weight_in_grams` | dia | 108 | peso real de lo que se vende al peso (ya cableado a `peso_neto_g`) |
| `item_treatment_type` | dia | por medir | la conservacion de DIA, que hoy es 0 % |
| `family_code` / `subfamily_code` | dia | 5.410 | un arbol de categorias de verdad, en vez de deducirlo de la URL |
| `main_feature` | mercadona | 1.200 | "ultracongelado", "lonchas": `tipo_producto` gratis |
| `promotions[].requiredProductQuantity` | alcampo | 509 | el "2ª unidad" estructurado, sin leer el texto |

> **La regla del proyecto**: antes de pedirle un campo nuevo a una web, buscarlo
> en `data/raw`. Ha aparecido ahi las siete veces que se ha mirado, y la octava
> lo encontro esta herramienta sola.

---

## 6. Como se anade una cadena al auditor

Una sola cosa: que su colector tenga `productos_crudo(body) -> list[dict]`, la
misma funcion que necesita `reprocesar.py`. Si no la tiene, el auditor lo dice:

    mercadona: no se pudo leer el crudo (¿le falta `productos_crudo`?)

Mercadona es el unico caso hoy, y funciona porque su crudo es JSON y el extractor
generico lo entiende.
