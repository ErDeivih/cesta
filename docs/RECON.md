# Reconocimiento de fuentes — supermercados ES

Verificado en vivo el 6 sep 2026 abriendo cada web y leyendo su trafico de red.
Los endpoints internos cambian sin aviso: si un colector devuelve 0 filas, lo
primero es repetir este reconocimiento.

| Cadena | Metodo | EAN | Precio/unidad | Proteccion | Cadencia viable |
|---|---|---|---|---|---|
| Mercadona | API JSON publica | **SI** | si (bulk_price) | ninguna | diaria |
| Alcampo | SSR + API enriquecimiento | no | **si, ya calculado** | **AWS WAF** | diaria |
| Aldi | API JSON `/api/product/pds/` | no | **si (basePrice)** | ninguna | diaria |
| DIA | JSON embebido + API de ficha | **SI** | si | Akamai | diaria |
| Carrefour | SSR `__INITIAL_STATE__` | no* | si (texto) | Cloudflare | diaria, selectiva |
| Lidl | solo folleto semanal | no | no | consent + visor 3o | semanal, con navegador |

*Carrefour: el EAN no viene en el listado; queda por comprobar si esta en la ficha.

**Cuatro de las seis con HTTP plano. Alcampo necesita un navegador UNA VEZ al dia
(para la cookie del WAF) y Lidl uno por folleto semanal.**

---

## 1. Mercadona — VERIFICADO EN VIVO

    GET https://tienda.mercadona.es/api/categories/         -> 26 categorias raiz
    GET https://tienda.mercadona.es/api/categories/<id>/    -> subcategorias CON productos
    GET https://tienda.mercadona.es/api/products/<id>/      -> ficha completa
    PUT /api/postal-codes/actions/change-pc/  body {"new_postal_code":"28001"}

`/api/categories/112/` devolvio 4 subcategorias y 35 productos en una sola llamada.
Cabeceras: `cache-control: no-cache`, `allow: GET, HEAD, OPTIONS`.

Campo `price_instructions` de cada producto:

    {"unit_price":"17.25",          precio total del articulo
     "bulk_price":"3.45",           precio por unidad de referencia
     "reference_format":"L",        unidad de referencia
     "unit_size":5, "size_format":"l",
     "tax_percentage":"4.000",
     "previous_unit_price":"17.75", <- PRECIO ANTERIOR, regalado
     "price_decreased":false}       <- bandera de bajada

Mercadona te da el precio anterior y una bandera de bajada. Es la unica cadena que
lo hace: sirve para validar tu propio detector de anomalias.

`/api/products/<id>/` anade **`ean`** (verificado: 8402001027482), `brand`, `origin`,
`details.suppliers` (los fabricantes reales detras de Hacendado), `legal_name`,
`nutrition_information`, `packaging`, `is_variable_weight`.

El almacen se fija por cookie de sesion via el PUT del codigo postal. Probado que el
parametro `?wh=mad1` NO cambia precios: hay que hacer el PUT y reutilizar la cookie.
Para un uso personal en una sola zona, basta con fijarlo una vez.

## 2. Alcampo — VERIFICADO EN VIVO

    GET https://www.compraonline.alcampo.es/categories/<slug>/<CODIGO>
    PUT https://www.compraonline.alcampo.es/api/webproductpagews/v6/products

HTML con `window.__INITIAL_STATE__` (~1,2 MB) + `window.__URQL_DATA__` (cache GraphQL).
La respuesta del PUT es la mejor estructurada de todas:

    {"retailerProductId":"882535","name":"LA ESPAÑOLA Aceite ... 5 l.",
     "brand":"LA ESPAÑOLA","packSizeDescription":"5000ml",
     "price":{"amount":"19.95"},
     "unitPrice":{"price":{"amount":"3.99"},"unitName":"PER_LITRE"},
     "promotions":[{"description":"Producto en Folleto (27/08/26_09/09/26)"}],
     "categoryPath":["Alimentación","Aceite y Vinagre","Aceites",...]}

`regionId` (uuid) fija la tienda. robots.txt declara "maxima apertura para mapeo de
entidades y recoleccion de datos de rastreo". Sin Crawl-delay.
Sitemap: https://compraonline.alcampo.es/sitemaps/sitemap_index.xml

## 3. Aldi — VERIFICADO EN VIVO (nuevo)

Next.js. Las paginas de categoria son `/productos/<cat>/<subcat>.html` y llevan
`__NEXT_DATA__` con `apiData` (string JSON con las llamadas SSR ya resueltas).
El indice oficial `/sitemaps/.aldi-nord-sitemap-products.xml` contiene los IDs de
producto (2.096 el 6 sep 2026) y sustituye al rastreo incompleto del menu.
La pagina pide despues, en lote, la API de producto:

    GET https://www.aldi.es/api/product/pds/<id1>,<id2>,...?scope=es_pen

Respuesta `{"products":[...]}`, por producto:

    {"objectID":"940600","name":"Uva de mesa roja sin semillas",
     "productSlug":"...","salesUnit":"500 g unidad","isAvailable":true,
     "categoryIDs":["frutas"],"mainCategoryID":"frutas",
     "currentPrice":{"priceValue":1.49,
        "strikePrice":{"strikePriceValue":2.29},
        "basePrice":[{"basePriceValue":2.98,"basePriceScale":"kg"}],
        "priceTagLabels":{"promoText1":"-34%"},
        "validFrom":1788127200,"validUntil":1788731999},
     "promotionPrices":[...],"productReferences":[...]}

Regalos: precio por kg ya calculado, precio tachado, % de descuento y **ventana de
validez de la promocion en timestamps**. Nadie mas da la fecha de fin de oferta.
`scope=es_pen` = peninsula (hay variantes para Baleares/Canarias).
NO trae EAN. IDs por lotes (12 en la llamada observada).
No existe endpoint de categoria->productos: los IDs se sacan de la pagina.

## 4. DIA — VERIFICADO EN VIVO

    GET https://www.dia.es/<l1>/<l2>/c/<CODIGO>?page=N        listado, 20/pagina
    GET https://www.dia.es/api/v1/product/<sku_id>?lang=es    ficha maestra

Listado: `<script id="vike_pageContext">` -> `INITIAL_STATE.l2.plp_items`:

    {"brand","display_name","sku_id","url","units_in_stock",
     "prices":{"price":1.85,"price_per_unit":1.85,"measure_unit":"LITRO",
               "strikethrough_price":1.85,"discount_percentage":0,
               "is_promo_price":false,"is_club_price":false}}

Ficha: 88 campos con **`ean_code`** y `secondary_eans`, ingredientes, alergenos,
peso neto, familia. Sin precio (depende de tienda).
Tambien hay JSON-LD `ItemList` con name+price: plan B mas estable.
Categorias: https://www.dia.es/sitemap.xml -> 6.804 URLs, patron `/c/L####`.
Proteccion: Akamai Bot Manager (POST a rutas ofuscadas). curl_cffi + ritmo lento.
robots.txt: `Disallow: /` solo para bots concretos, no para `*`. Sin Crawl-delay.

## 5. Carrefour — VERIFICADO EN VIVO

    GET https://www.carrefour.es/supermercado/<slug>/<catId>/c?offset=N

`window.__INITIAL_STATE__` -> `criteo.plpData.results.items`:

    {"product_id":"VC4AECOMM-651364","sku_id":"6513640000","name":"...",
     "brand":"CARREFOUR","price":"0,95 €","price_per_unit":"0,47 €",
     "measure_unit":"kg","units_in_stock":254}

Paginacion `?offset=` de 24 en 24 (el parametro `limit` se ignora).
El slug de la URL es cosmetico: manda el `catId`.
Precios como texto con coma decimal -> parsear a centimos.
Su API interna `/cloud-api/plp-food-papi/v1` da 503 desde el cliente: es server-side.
Cloudflare activo -> curl_cffi con impersonate es obligatorio.
robots.txt solo declara `Crawl-delay: 60` para `TwengaBot`, no para `User-agent: *`.
No obstante, Cloudflare bloquea facilmente y el colector debe ser selectivo y lento;
el limite operativo se decidira con pruebas, no atribuyendolo a una regla inexistente.

## 6. Lidl — el caso dificil (nuevo)

**Lidl Espana no vende alimentacion online.** lidl.es es tienda de bazar; el surtido
de alimentacion y sus precios solo existen en el folleto semanal, que se renderiza en
un visor de terceros del grupo Schwarz:

    https://www.lidl.es/l/folletos/folleto-alimentacion-<fechas>-<hash>/ar/0
    -> iframe a https://lidl.leaflets.schwarz/  (app React)

El iframe no carga hasta aceptar el banner de consentimiento, asi que no se puede
resolver con HTTP plano. Opciones, de mejor a peor:

1. **Patchright** (ver docs/PATCHRIGHT.md): abrir el folleto una vez, resolver el
   consentimiento, dejar cargar el visor e interceptar la respuesta JSON del visor,
   que contiene las "zonas activas" de cada pagina con producto y precio.
   Cadencia semanal (el folleto cambia los lunes), no diaria.
2. Descargar el folleto en PDF y extraer con OCR. Fragil, pero sin navegador.
3. Aceptar que Lidl entra a mano: 15 min a la semana metiendo 20 precios.
4. API comercial de pago (Apify, ShoppingScraper). Ultimo recurso.

Recomendacion: **deja Lidl para la fase 2**. Con cinco cadenas ya tienes comparacion
sobrada, y Lidl cambia precios semanalmente, no a diario.

---

## Conclusiones operativas

1. **Orden de implementacion:** Mercadona -> Aldi -> Alcampo -> DIA -> Carrefour -> Lidl.
   De menos a mas friccion.
2. **El EAN solo lo dan Mercadona y DIA.** Ancla por EAN entre esas dos y usa esos
   pares como conjunto de entrenamiento/validacion del matching por nombre para el
   resto. Es la forma barata de saber si tu matcher funciona.
3. **Alcampo y Aldi dan el precio por kg/litro ya calculado.** Uselos como referencia
   para validar tu propio parser de formatos.
4. **Aldi da la fecha de fin de promocion.** Es el unico. Alimenta directamente el
   aviso "esta oferta acaba el domingo".
5. **Mercadona da el precio anterior.** Test gratis de tu detector de bajadas.
6. **Carrefour sigue siendo selectivo por Cloudflare:** aunque el `Crawl-delay: 60`
   solo se aplica a TwengaBot, conviene empezar por categorias de la cesta.
