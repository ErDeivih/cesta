# Lo que ya tenemos descargado y todavia no leemos (18 sep 2026)

Pasada de `auditar_crudo` sobre el crudo del dia, cadena por cadena, y despues
**medicion de cada candidato** contra el crudo real y contra gold. Sin medir, la
lista del auditor es una lista de sospechas; con los numeros al lado es una lista
de trabajo.

Regla de la casa que se aplica aqui: medir y descartar tambien es un resultado, y
se escribe con su numero.

---

## 0. Primero, el falso positivo que costo media hora

El auditor senalo `iconAttributes[].file` en el **52,2 %** del catalogo de Alcampo
y parecia el hallazgo del ano: gluten, vegano, eco, sin lactosa, congelado,
refrigerado, alcohol y marca propia, declarados por la cadena en 10.197 productos.

**Ya se leen.** El colector coge esa misma lista por `iconAttributes[].label`, que
dice lo mismo en cristiano, y los numeros de gold lo confirman: 3.400 sin gluten,
2.414 veganos, 1.135 sin lactosa, 1.052 ecologicos. Lo mismo con
`icons[].path`/`[].type`, que el colector lee por `label` como pictogramas de
peligro CLP.

El auditor avisa por hoja (`file`), no por rama (`iconAttributes[]`), asi que no
podia saberlo. Ahora lo dice:

```
   52.2%  iconAttributes[].file    icon_vegan
          (de ese mismo sitio si se lee: label -- probablemente ya cubierto)
```

No se descarta solo a proposito: hay hermanos que si aportan --
`promotions[].type` frente a `promotions[].description` es el caso justo de
abajo--. Pero decirlo ahorra la media hora.

---

## 1. ALDI: 199 ofertas que **todavia no han empezado**

Lo mas interesante de toda la pasada, y estaba delante desde el principio.

De los 2.175 productos de Aldi del 18, **317 traen `promotionPrices` (14,6 %)**, y
cada entrada es una oferta completa:

```json
{"validFromLocalDate": "2026-09-19", "validUntilLocalDate": "2026-09-22",
 "priceValue": 3.99, "strikePrice": {"strikePriceValue": 6.99},
 "priceTagLabels": {"promoText1": "-42%"}}
```

Fecha de inicio, fecha de fin, precio de antes, precio de despues y el porcentaje
ya calculado. Y el reparto, medido el dia 18:

| | productos |
|---|---:|
| promociones que **empiezan mas adelante** | **199** |
| promociones ya activas | 122 |
| promociones caducadas | 0 |

Ejemplos reales de ese dia:

    Vino tinto crianza DOCa Rioja      6,99 -> 3,99   -42 %   del 19 al 22
    Pack de 2 vinos blancos           14,99 -> 11,99  -20 %   del 19 al 22
    Leche omega 3                      1,89 ->  1,69  -10 %   del 21 al 27

El colector **las ve y las tira**. Hay hasta un comentario en `aldi.py` que lo
dice ("62 de las 174 promociones de hoy aun no han empezado"), pero solo las usa
para averiguar el `validUntil` del precio de hoy.

### Por que importa

Ninguna de las aplicaciones que hemos mirado hace esto. Todas contestan "cuanto
cuesta hoy" o "cuanto costaba antes". Esto contesta otra pregunta, que es la que
de verdad ahorra dinero:

> **"No lo compres hoy: el sabado baja un 42 %."**

Y no es una prediccion ni un modelo: es la propia cadena publicando su calendario.

### Spec para quien lo implemente

**Contrato de datos.** Tres columnas nuevas en bronze, que llegan a gold:

    promo_futura_desde      date    | inicio de la ventana (validFromLocalDate)
    promo_futura_hasta      date    | fin de la ventana (validUntilLocalDate)
    promo_futura_cent       int     | priceValue * 100, el precio que se pagara
    promo_futura_antes_cent int     | strikePrice.strikePriceValue * 100
    promo_futura_origen     str     | "aldi_promotionPrices"

Regla de seleccion: de todas las entradas de `promotionPrices` con
`validFromLocalDate > hoy`, quedarse con **la mas proxima**. Si hay varias que
empiezan el mismo dia, la mas barata.

**Lo que NO se debe hacer**, y es el error facil: meter ese precio en
`precio_cent` o en la serie historica. Es un precio que todavia no existe. Va en
su columna, se compara con el precio de hoy **de esa misma cadena** y solo se
ensena como aviso.

**Como se ve en la aplicacion.** Un aviso en la linea de la lista y una pantalla
"Espera unos dias" con lo que baja esta semana, ordenado por cuanto se ahorra en
esa lista concreta. La frase tiene que decir el dia, no "proximamente".

**Ojo con la honestidad del dato.** Solo Aldi lo publica. En la ficha hay que
decir de donde sale ("Aldi publica esta oferta para el 19-22 de septiembre") para
que nadie crea que se lo hemos adivinado, y hay que dejar de ensenarlo en cuanto
la ventana pasa aunque no haya habido captura nueva.

**Prueba que tiene que existir:** una promocion con `validFrom` en el pasado no
puede acabar en `promo_futura_*`; y una con `validFrom` manana si.

---

## 2. CARREFOUR: la regla de la oferta escrita en espanol, en 2.024 productos

`badge.description` no se lee. Lo traen **2.024 de los 11.613 productos unicos
del dia (17,4 %)**, y dice exactamente en que consiste la oferta:

| veces | texto |
|---:|---|
| 2.711 | Compra 2 unidades de este producto y te descontamos el 50 % en la 2ª ud |
| 800 | Compra 2 unidades, Ahorra la segunda |
| 307 | Compra 12 unidades de leche entera, semi o desnatada PASCUAL brik 1 l |
| 105 | Compra 3 unidades de este producto y paga solo 2 |
| 52 | Compra 4 unidades de este producto y paga solo 3 |
| 46 | Te descontamos 5 € por la compra de 18 € en estos productos. Exclusivo online |
| 30 | 15 % dto en estos productos NEUTROGENA. Exclusivo online |

(las veces son apariciones en el crudo, donde un producto sale en varias
categorias; los productos unicos con badge son 2.024)

Esto es materia prima directa para el modelo que ya tenemos escrito: **una oferta
es una regla, no un precio**. "2ª unidad al 50 %" significa que dos unidades
cuestan 1,50 veces una, no 1,00. Hoy eso se deduce del texto de promocion que ya
leiamos; `badge.description` es mas explicito y cubre mas productos.

Tambien aparece ahi, y hay que tratarlo distinto: **"Exclusivo online"**. Un
descuento que no existe si vas a la tienda no puede entrar en el total de una
cesta que se va a comprar a pie.

### Spec

Extender `core/promos.py` con estos patrones, cada uno con su regla:

    "compra N ... y paga solo M"        -> N unidades al precio de M
    "2ª unidad al X %"                  -> 2 unidades = 1 + (1 - X/100)
    "compra N unidades de <marca> ..."  -> regla por marca, NO por producto
    "te descontamos X € por la compra de Y €"  -> umbral por importe
    "exclusivo online"                  -> marcar `solo_online`, fuera del total

El tercero y el cuarto son los peligrosos: **no son reglas de producto**, son
reglas de cesta. Si se aplican producto a producto, el total sale mal. Mientras no
haya modelo de cesta, se guardan y se ensenan como texto, pero **no se restan**.

---

## 3. ALCAMPO: la cantidad que hace falta, y la oferta que es solo con tarjeta

Dos campos de `promotions[]` sin leer, medidos sobre los 20.571 productos unicos:

    promotions[].type                  OFFER 2.344 | LOYALTY 534 | COUPON 6
    promotions[].requiredProductQuantity   2 -> 338 | 3 -> 156 | 4 -> 3   (497)

`requiredProductQuantity` es **la regla de la oferta como dato estructurado**, sin
tener que leer ningun texto: 338 productos que piden dos unidades, 156 que piden
tres.

`type = LOYALTY` en **534 productos** es todavia mas importante, porque toca una
regla que ya esta escrita en el proyecto: el descuento de tarjeta **no baja lo que
pagas en caja**. Hoy eso se deduce del texto; aqui la cadena lo dice.

### Spec

    promo_requiere_unidades  int   | requiredProductQuantity
    promo_tipo               str   | "oferta" | "tarjeta" | "cupon"

y la regla, que es la de siempre: si `promo_tipo != "oferta"`, el ahorro se
ensena aparte y **no entra en el total de la cesta**. La comparacion entre cadenas
tiene que poder hacerse con y sin tarjetas, porque no todo el mundo las tiene.

`maxAvailableQuantity` (8,1 %, 1.670 productos) es lo mas parecido a una senal de
stock que publica nadie. No sirve para saber si hay existencias -- solo aparece
cuando hay tope --, asi que se anota y no se promete nada con ello.

---

## 4. MERCADONA: `main_feature`, que ataca un problema abierto

**1.209 productos (26,4 %)** traen `main_feature`, que es el descriptor de la
variante:

    Yogur griego dulce Hacendado   ->  "con dulce de leche, galleta y platano"

Esto no es un campo mas: es munición para **el problema abierto F2, los grupos
demasiado anchos**. El sintoma conocido es que buscar "galletas sin gluten" saca
chocolate, porque el grupo mete en el mismo saco cosas que solo comparten la
cabecera del nombre. Dos yogures que se diferencian solo en el sabor caen hoy en
el mismo grupo, y con esto se distinguen.

### Spec

Columna nueva `variante` (texto) en bronze, y en el emparejador: **si dos
candidatos de la misma cadena tienen `variante` y son distintas, no son el mismo
producto**. Entre cadenas no se puede usar como negativa -- las demas no publican
el campo --, solo para partir grupos dentro de Mercadona y como texto a ensenar en
la ficha.

Tambien sin leer, y de menos interes: `pack_size` (520 productos) y
`selling_method` (0 en 4.578, 1 en 9).

---

## 5. DIA: promociones de folleto y descuentos con porcentaje

    headband_promotion       exclusive_offer 214 | exclusive_online 106
    stamp_code               4 -> 502 | 2 -> 323 | 1 -> 251 | 3 -> 20   (1.096)
    prices.discount_percentage != 0                                        161
    prices.is_club_price = True                                            130
    weight_in_grams / average_weight                            139 (1,6 %)

`exclusive_online` en 106 productos es el mismo caso que el de Carrefour: un
descuento que no existe en la tienda fisica. **Hay que marcarlo**, porque hoy
entra en el total como si fuera real.

`discount_percentage` da el descuento ya calculado en 161 productos (20 % en 53,
30 % en 15, 15 % en 15...). Sirve de **contraste**: si nuestro calculo y el suyo
no coinciden, uno de los dos esta mal leyendo el formato. Ese desacuerdo es una
alarma de calidad, no un dato que copiar.

`is_club_price` ya se cubre por otra via (`only_club_dia` dentro de la promocion),
pero conviene cruzarlo: si un producto dice `is_club_price` y nuestro
`promo_club` esta vacio, se nos ha escapado.

Los `stamp_code` (1, 2, 3, 4) no sabemos que significan. Antes de darles sentido
hay que cruzarlos con el texto de la promocion de esos mismos 1.096 productos y
ver si cada codigo cae siempre en el mismo tipo de oferta. **Hasta entonces no se
tocan**: un codigo mal interpretado es peor que un codigo sin leer.

---

## 6. Medido y descartado (con su numero, para no volver a mirarlo)

| que | resultado |
|---|---|
| Carrefour `app_price` / `app_price_per_unit` | **iguales al precio web en 20.741 de 20.741**. No hay precio distinto en la app. |
| Aldi `productReferences[].value` | es `KVArticleNumber`, numero interno de articulo. **No es un EAN**, no cruza con Open Food Facts. |
| Alcampo `iconAttributes` / `icons` | **ya se leen**, por `label`. Falso positivo del auditor. |
| Mercadona `price_instructions.iva` | **ya se lee**. |
| Mercadona `price_instructions.reference_price` | se ignora **a proposito**: el precio por unidad lo calculamos nosotros. |
| Alcampo `ratingSummary.overallRating` | 0.0 en el 100 % del catalogo. No hay valoraciones. |
| DIA `expiration_days` | 0 en el 93,7 %. No dice nada. |
| Alcampo `quantityInBasket`, `isInShoppingList`, `maxQuantityReached` | estado de **su** sesion, no del producto. |

---

## 7. Orden de trabajo sugerido

1. **Aldi, ofertas futuras** -- es lo unico de esta lista que ninguna aplicacion
   de la competencia tiene, y el dato esta completo y fechado.
2. **`solo_online` en Carrefour y DIA** -- no anade una funcionalidad, **corrige
   un total que hoy esta mal**: descuentos que no existen si vas a la tienda.
3. **Alcampo `type` + `requiredProductQuantity`** -- la regla de la oferta sin
   adivinar nada.
4. **Carrefour `badge.description`** -- mas cobertura para el mismo modelo, con
   cuidado con las reglas de cesta, que no se restan.
5. **Mercadona `main_feature`** -- entra por el problema F2, no por la ficha.
6. **Cruces de calidad** (DIA `discount_percentage` e `is_club_price`) -- no dan
   datos nuevos, dan **desacuerdos**, que es lo que encuentra errores.
