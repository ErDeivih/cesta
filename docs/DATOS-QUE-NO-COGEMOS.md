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
