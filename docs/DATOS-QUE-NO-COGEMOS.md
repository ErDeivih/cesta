# Lo que las webs publican y no estamos cogiendo — 26 de septiembre de 2026

**Por qué existe este documento.** El dueño lo dijo así: *"las webs he visto que muchas ofrecen
más datos de los que tú recoges en realidad, se puede hacer más si coges todos los datos de cada
web y mejores comparaciones"*. Tenía razón, y esto es la lista **medida** de lo que hay ahí fuera
sin usar.

**Cómo se mide.** Con la herramienta que ya existía para esto,
`projects/cesta/auditar_crudo.py`: lee el crudo del día, recorre los campos que aparecen con
valor, y dice cuáles **no pide** ningún colector. Los porcentajes son la proporción de productos
de esa cadena que traen ese campo con valor.

    uv run python -m projects.cesta.auditar_crudo

> **Aviso de método:** es una heurística y avisa de más. Un campo leído a través de una variable no
> se ve, así que la lista incluye cosas que en realidad sí se leen. Donde el propio auditor lo
> detecta, lo dice («de ese mismo sitio si se lee: …»). Lo que sigue son los campos donde **no**
> hay esa nota, o donde el dato es distinto del que sí se lee.

---

## 1. Lo que cambiaría las comparaciones (esto es lo que importa)

| Cadena | Campo | Con valor en | Qué mejoraría |
|---|---|---|---|
| mercadona | `price_instructions.reference_price` | **100 %** | El precio por unidad **publicado por la cadena**. Es una segunda opinión sobre nuestro `precio_unidad_cent`, que hoy calculamos nosotros: hoy solo se cruza en la ficha (`en_disputa`), no en el emparejador |
| mercadona | `price_instructions.unit_name` | 28,9 % | La unidad que usa la cadena (`ud.`, `kg`). Sirve para saber si su `reference_price` está por kilo o por unidad antes de compararlo |
| mercadona | `price_instructions.iva` | 27,6 % | El tipo de IVA. No cambia lo que pagas, pero sí explica saltos raros al comparar formatos y permite comprobar precios sin IVA si algún día hace falta |
| aldi | `promotionPrices[].validFromLocalDate` / `validUntilLocalDate` | 15 % | Las fechas de la oferta, **en claro**. Hoy `validUntil` se lee, pero el comienzo no: una oferta que empieza mañana no es una oferta de hoy |
| aldi | `isComingSoon` | 100 % | Producto **anunciado y aún no a la venta**. Es la señal directa de las «199 ofertas que todavía no han empezado» que lleva semanas en el BACKLOG |
| aldi | `currentPrice.validFrom` | 93,5 % | Desde cuándo vale ese precio: el **tiempo de validez** que el modelo de datos no tiene (capítulo 13: solo guardamos cuándo lo copiamos) |
| alcampo | `promotions[].requiredProductQuantity` | 8 % | Cuántas unidades pide la mecánica, **en número**. Hoy se adivina del texto («2ª unidad -50%»), y esto lo dice la propia web |
| alcampo | `type: CATCHWEIGHT` | 100 % | Producto **al peso**. Hoy se deduce comparando días (`peso_variacion_pct`); esto lo declara la cadena en cada ficha |
| dia | `prices.is_club_price` | 93,7 % | Si ese precio es **solo para socios**. Un precio de club no se puede comparar con el de la estantería de otra cadena |
| dia | `prices.discount_percentage` | 93,7 % | El porcentaje de descuento que publica la cadena, para contrastar el que calculamos |
| dia | `expiration_days` | 93,7 % | Días de caducidad (hoy 0 para la mayoría: se leería sin problema) |
| carrefour | `app_price` / `app_price_per_unit` | **100 %** | El precio que enseña la aplicación frente al de la web. Si difieren, hay una promoción que solo existe en un canal |
| carrefour | `restrictions[]` (`shipping-restriction`, `display_name: Lunes`, `quantity`) | 3 % | Restricciones de envío por producto. Para comparar precios no aporta; para «¿me lo pueden traer?», sí |

## 2. Lo que mejoraría el emparejamiento (juntar bien lo que es lo mismo)

| Cadena | Campo | Con valor en | Qué mejoraría |
|---|---|---|---|
| aldi | `longDescription` | 82 % | Texto largo de la ficha («El precio puede variar para las tiendas…») |
| aldi | `shortDescriptionFormatted[].text` | 42,8 % | Descripción corta con **la variedad** («Variedad: verdejo») y los ingredientes («Con zumo de manzana, piña y naranja»). Es texto que hoy no se mira y distingue variantes |
| mercadona | `main_feature` | 27,4 % | La línea de gancho de la ficha («con dulce de leche, galleta y plátano»): otra vez, texto que distingue variantes |
| dia | `promotions[].short_description` | 3,7 % | El nombre corto de la promoción |
| mercadona | `badges.is_water` | 100 % | Marca de agua (categoría aduanera; poco valor para nosotros) |

## 3. Lo que no vale la pena (dicho para no volver a mirarlo)

- `images.mobile`, `imageIds`, `imagePaths`, `imageConfig.availableFormats`, `info_tags[].icon`,
  `stamp_color`, `stamp_text_color`: son de presentación. La imagen ya se guarda (una).
- `ratingSummary.overallRating` / `count` (Alcampo): valoraciones de clientes. Interesantes para
  una ficha, no para comparar precios, y son de la **web**, no del producto.
- `quantityInBasket`, `isInShoppingList`, `isVerifiedPurchase`, `limit`,
  `maxQuantityReached`, `units_in_cart`: son del carrito **de quien navega** (nosotros no tenemos
  carrito), no del catálogo.
- `retailerFinancingPlanIds`, `document_type`, `catalog`, `prices.currency` (siempre EUR),
  `unitPrice.price.currency`, `price.currency`: constantes o de otro sistema.
- `type: PaginationDivider`, `headband_promotion` (solo dice que es una oferta exclusiva, sin
  fechas ni unidades).

## 4. Lo que se va a hacer, por orden de valor medido

1. **`reference_price` + `unit_name` de Mercadona** (100 % / 28,9 %): contraste independiente del
   precio por unidad, que es el número sobre el que se decide toda la comparación.
2. **`isComingSoon` y las fechas de validez de Aldi**: dejar de anunciar como oferta lo que aún no
   ha empezado, y saber **desde cuándo** vale un precio.
3. **`requiredProductQuantity` de Alcampo** (8 %) y `is_club_price` de DIA: las dos formas de que
   una oferta no se pueda comparar con un precio normal, dichas por la propia cadena.
4. **El texto de las fichas** (Aldi `shortDescriptionFormatted`, Mercadona `main_feature`): es la
   materia prima para separar variantes en el emparejamiento, que es el otro problema abierto
   (ver `docs/CALIDAD-DEL-EMPAREJAMIENTO.md`).

Cada uno de estos cuatro va con su medición antes y después sobre el mismo bronze, como todo lo
demás de este proyecto.

---

## 5. El primer cruce, hecho: el precio de referencia de cada cadena contra el nuestro

El punto 1 no se ha dejado para mañana: se ha medido sobre el crudo del 26 de septiembre de 2026.
Mercadona publica en cada ficha `reference_price` con su `reference_format` (kg, l, 100 g, 100 ml,
ud) y también `bulk_price`, que ya viene por kilo o por litro; las otras cuatro publican su precio
por unidad en la propia ficha del producto.

**Todos los números de este punto salen de un comando**, que es lo que hace que sigan siendo
ciertos la semana que viene:

    uv run python -m projects.cesta.auditar_escurrido --acuerdo 2026-09-26

Y la primera lectura es buena: **nuestro precio por unidad, que se calcula leyendo el nombre,
coincide con el que publica cada cadena**. Alcampo 99,2 %, Carrefour 98,3 %, DIA 97,1 %,
Mercadona 95,4 %, Aldi 94,6 %. Eso valida la normalización entera del proyecto (la regla de tres,
el catálogo de unidades, los formatos por dosis) contra una fuente que no es nuestra.

**La lectura mala, y aquí va la enmienda de este documento.** La primera versión de este punto
decía que «el 9 % que no cuadra tiene un patrón claro: las conservas de pescado, ahí la nuestra sale
entre un 10 % y un 40 % más baja», y ponía tres ejemplos que en realidad estaban **de acuerdo**
(722,2 contra 722,0; 1.020,8 contra 1.021,0; 2.973,0 contra 2.973,0). Las tres «cifras suyas» de
aquella lista eran nuestras: el resultado de dividir el precio entre el peso escurrido, escritas
como si las publicara la cadena. Un número propio atribuido a la fuente externa es la forma más
rápida de que una medición deje de significar nada; de aquel error salió, eso sí, el arreglo que hoy
está en el pipeline, y el error entero está contado en el punto 5 bis.

Lo que queda cuando se mide bien, sobre el mismo día y con una definición escrita —comparables son
las filas donde nosotros derivamos el precio por unidad y la cadena publica el suyo, apartando las
que se llevan ×2 o más— son dos cosas que no tienen nada que ver entre sí, y por eso el porcentaje
de acuerdo engaña:

| cadena | comparables | coinciden al 2 % | de las que no: mediana de la diferencia | de 1 céntimo o menos |
|---|---|---|---|---|
| Alcampo | 19.413 | 99,2 % | 0,37 céntimos | 133 de 164 |
| Aldi | 1.765 | 94,6 % | 0,38 céntimos | 64 de 96 |
| Carrefour | 12.522 | 98,3 % | 0,43 céntimos | 140 de 212 |
| DIA | 5.753 | 97,1 % | 0,35 céntimos | 161 de 166 |
| Mercadona | 3.899 | 95,4 % | 227,18 céntimos | 45 de 181 |

**La primera cosa es el redondeo.** La referencia que publica la cadena va al céntimo entero, y la
nuestra no: un papel higiénico a 1,6 céntimos por hoja con la etiqueta en 2,0 son 0,4 céntimos de
diferencia y un 25 % en el papel. En las cuatro cadenas que no publican escurrido la mediana de la
diferencia es de **0,35-0,43 céntimos** y dos tercios o más son de un céntimo o menos. Un umbral
del 2 % es demasiado fino para un dato que viene redondeado, y llamar «desacuerdo» a eso hace que
el desacuerdo de verdad no se vea.

**La segunda cosa es la de Mercadona, y es la que este documento trata.** Su mediana no es de
céntimos: son **227 céntimos por kilo**, y son las 179 conservas y tarros donde Mercadona publica
el peso escurrido. Ahí ya no hay redondeo ninguno, hay una decisión: la comparación entre cadenas
manda sobre la coincidencia con su ficha. Está contada entera en el punto 5 bis.

## 5 bis. Lo que decidió el arreglo: la comparación entre cadenas, no la ficha de una

Las tres cifras «suyas» del §5 eran nuestras, y verlo así aclara todo lo demás. Mercadona **sí
publica** el peso escurrido (`drained_weight`): 179 productos, todos conserva o tarro. Y su precio
de referencia va sobre **lo declarado**, no sobre el escurrido: en 142 de esos 179 se comprueba que
su referencia es exactamente `precio ÷ peso declarado`, y en los 34 que no declaran peso en el
nombre va sobre el escurrido, porque no hay otra base que dar. O sea que en su propia ficha no hay
ningún error, y nuestra cuenta coincidía con ella. Lo que estaba mal era **la comparación entre
cadenas**.

La pregunta buena no es *¿nuestra cuenta coincide con su ficha?* sino ***¿el mismo producto
declara lo mismo en las cinco cadenas?***. Y ahí sí hay un problema grande. La ventresca de atún
claro:

| cadena | lo que declara | precio | por kilo declarado |
|---|---|---|---|
| Mercadona (Hacendado) | 111 g (neto) + **78 g escurridos** | 3,30 € | 2.973,0 c/kg |
| Alcampo (Sálvora) | 73 g | 3,12 € | 4.274,0 c/kg |
| Carrefour | 73 g | 3,09 € | 4.233,0 c/kg |
| DIA (Ribeira) | 73 g | 3,49 € | 4.781,0 c/kg |

Es la misma lata, y Mercadona sale «un 30 % más barata» por el artefacto del aceite que se paga y
no se come. Con el escurrido: 4.230,8 c/kg, que es donde están las otras tres.

Medido en los 18 grupos de conserva donde Mercadona publica escurrido y hay al menos dos cadenas
más vendiendo lo mismo por kilo, comparando el precio por kilo de Mercadona contra la mediana de
las otras:

    dividiendo por lo declarado    mediana 0,590 veces la mediana   1 de 18 dentro del ±20 %
    dividiendo por el escurrido    mediana 0,982 veces la mediana  13 de 18 dentro del ±20 %

La mediana de las otras es una referencia frágil —hay grupos con dos rivales que se llevan ×3 entre
sí, una marca cara y una marca blanca—, así que va también la medida que no se puede torcer: ¿el
precio por kilo de Mercadona cae cerca (±20 %) de **algún** rival del mismo grupo?

    por lo declarado   coincide con algún rival del grupo:  2 de 18  (11 %)
    por el escurrido   coincide con algún rival del grupo: 16 de 18  (89 %)

Y el efecto sobre la pregunta que contesta la app (*¿dónde está más barato?*): en esos 18 grupos
el más barato cambia en **17**, y Mercadona deja de serlo en **12** sin pasar a serlo en ninguno.

**Lo que cuesta, dicho antes de que sorprenda.** El acuerdo con la ficha de cada cadena, con la
misma definición antes y después (tolerancia del 2 %, apartando las filas que se llevan ×2 o más,
que el propio pipeline no compara). Los dos días a la vez:

    uv run python -m projects.cesta.auditar_escurrido --acuerdo 2026-09-25 2026-09-26

    alcampo   99,2 % -> 99,2 %
    aldi      94,5 % -> 94,6 %
    carrefour 98,4 % -> 98,3 %
    dia       97,1 % -> 97,1 %
    mercadona 98,4 % -> 95,4 %   <- 3,1 puntos, y son las conservas con escurrido publicado:
                                    el 25 de septiembre no había ni una diferencia grande con su
                                    ficha (61, todas de menos de un céntimo) y el 26 hay 181,
                                    con mediana de 227 céntimos por kilo

Las cuatro cadenas que no publican escurrido no se mueven. Mercadona baja porque **su** referencia
va sobre lo declarado: coincidir con ella es coincidir con la base que hace que la comparación
entre cadenas esté mal. Se acepta el cambio por eso, y el número queda escrito aquí para que la
próxima vez no haya que descubrirlo.

**Y el límite, que también es un resultado.** La base no es la misma en todas las cadenas: en las
sardinas, Mercadona declara 85 g con 65 g escurridos y la competencia declara 85-90 g, y en la piña
en su jugo la competencia declara el neto. De los 18 grupos, 5 se quedan fuera del ±20 %, y mirando
uno por uno no son un problema del escurrido sino de **con quién se compara**:

    melva en aceite     Mercadona queda en 2.312,5 c/kg, exactamente donde Carrefour (2.312,5);
                        la mediana la mueve Alcampo, que es la marca cara USISA a 6.062,5
    berenjenas          Mercadona queda en 1.025,7 c/kg, exactamente donde DIA (1.025,7), que es
                        la misma marca (Antonio); Alcampo vende el tarro de 170 g a 1.588,2
    sardina ahumada     el par es dudoso de entrada: «filetes de sardina ahumada» contra
                        «sardinas en aceite de girasol»
    piña en su jugo     los rivales se llevan ×3 entre sí (Aldi 397 c/kg y Del Monte 1.188)
    aceitunas verdes    cuatro tamaños distintos de Mercadona contra dos rivales

Arreglar eso pide saber la base y la marca de cada cadena rival en cada producto, y saber que el par
es el mismo producto, que es justo el otro problema abierto del proyecto
(`docs/CALIDAD-DEL-EMPAREJAMIENTO.md`). Lo que sí se puede —y se hace— es no esconderlo: la cifra
lleva su etiqueta («€/kg escurrido») y el producto enseña los dos pesos.
