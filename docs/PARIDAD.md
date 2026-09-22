# Paridad de datos — que ninguna cadena tenga huecos

Principio: **la interfaz nunca dice "sin datos" porque una cadena de menos.**
Si un campo no viene de origen, se rellena por otra via, y se marca COMO se ha
rellenado. Cuatro procedencias:

    nativo    la cadena lo publica
    derivado  lo calculamos de NUESTRO historico (core/derive.py)
    externo   Open Food Facts (core/off.py)
    inferido  heredado del grupo por matching, con score

Cada campo del esquema canonico lleva su columna `proc_<campo>`. La interfaz puede
mostrar un punto gris junto a un dato inferido, pero el dato ESTA.

## Verificado: quien da que (6 sep 2026)

| Campo | Merca | Aldi | Alcampo | DIA | Carrefour | Lidl | Como se rellena el hueco |
|---|---|---|---|---|---|---|---|
| precio | si | si | si | si | si | folleto | — |
| precio/unidad | si | si | si | si | texto | no | **normalizador propio** (core/normalize.py) desde el formato |
| formato/cantidad | si | si | si | si | si | si | normalizador |
| precio anterior | **si** | strike | promo | strike | no | no | **derivado**: shift(1) de nuestro historico |
| ha bajado | **si** | — | — | — | no | no | derivado |
| promo activa | — | si | si | si | no | si | derivado: precio < 95% de la mediana de 30d |
| fin de promo | no | **si** | texto | no | no | fechas | derivado: duracion tipica aprendida por cadena |
| descuento real | no | %  | no | % | no | % | derivado: frente a NUESTRA base, no al tachado |
| EAN | **si** | no | no | **si** | **si (ficha)** | no | inferido por matching + OFF por marca+nombre |
| ingredientes | si | parcial | **si (ficha)** | si | **si (ficha)** | no | externo OFF por EAN |
| nutricion | si | no | **si (ficha)** | si | **si (ficha)** | no | externo OFF |
| Nutri-Score | no | no | no | no | no | no | **calculado por nosotros** desde la nutricion, o OFF |
| NOVA / ultraprocesado | no | no | no | no | no | no | externo OFF |
| denominacion legal | si | no | **si (ficha)** | si | **si (ficha)** | no | externo / inferido |
| origen | si | texto | si (ficha) | si | si (ficha) | no | externo / inferido |
| alergenos | si | no | si (ficha) | si | si (ficha) | no | externo OFF |
| imagen | si | si | si | si | si | no | OFF como respaldo |
| disponibilidad | si | si | si | si | si | no | derivado: presencia en el listado |
| historico | **ninguna** | ninguna | ninguna | ninguna | ninguna | ninguna | **nuestro** |

Hallazgo clave del 6 sep: **la ficha de producto de Carrefour SI trae EAN**
(`__INITIAL_STATE__.product.ean` y `gtin13` en el JSON-LD), ingredientes y
denominacion legal. Y la ficha de Alcampo trae ingredientes, nutricion completa,
denominacion legal, alergenos, origen y sellos vegano/vegetariano, aunque no EAN.
Con eso, cuatro de seis llegan a paridad casi total sin ayuda externa.

## Las dos ideas que resuelven el 90% de los huecos

### 1. La ficha maestra se scrapea UNA VEZ; el precio, a diario

Los ingredientes de un producto no cambian. El EAN no cambia. La denominacion legal
no cambia. Solo el precio y el stock cambian a diario.

    tabla producto        <- se rellena una vez por producto, y ya
    tabla precio_diario   <- 1 fila por producto y dia

Esto desactiva el problema de Carrefour. Su `Crawl-delay: 60` hace inviable pedir
2.000 fichas cada dia, pero pedirlas UNA vez son ~33 horas repartidas en varias
madrugadas, en segundo plano, sin prisa. Despues, el coste diario de Carrefour es
solo el de los listados, que ya traen precio.

Cola de fichas pendientes, con prioridad: primero los productos de tu lista y tus
favoritos, luego el resto. El dia 1 ya tienes ficha completa de lo que te importa.

### 2. A partir del dia 30, nosotros damos MAS que ellos

Precio anterior, si ha bajado, si esta en promocion, cuanto es el descuento de
verdad, en que percentil esta hoy, cuanto suelen durar las ofertas de esa cadena,
si la oferta esta inflada. **Ninguna cadena publica eso completo, y nosotros lo
tenemos para las seis por igual**, calculado con el mismo codigo.

La paridad no se consigue scrapeando mas. Se consigue esperando, y por eso lo unico
urgente es que el cron empiece hoy aunque el modelo aun sea feo.

## Open Food Facts

Volcado en Parquet, regenerado cada noche:
`huggingface.co/datasets/openfoodfacts/product-database` -> `food.parquet`.
DuckDB lo lee directamente. **No usar la API para masivo**: limita a 15 req/min en
producto y 10 en busqueda, y lo dicen expresamente. El volcado no tiene limite.

Licencia ODbL (datos) + DBCL (contenidos) + CC-BY-SA (imagenes): uso libre, incluso
comercial, **citando la fuente**. Si la web sale a internet, atribucion visible.

Aporta lo que NADIE da: Nutri-Score, grupo NOVA (ultraprocesados), Eco-Score.
Y cubre a Aldi y Lidl, que no dan ingredientes, cruzando por marca + nombre +
cantidad con el mismo umbral y la misma cola de revision que el matching interno.

## El Nutri-Score cuando OFF no llega

Es una formula publica: puntos negativos (energia, azucares, grasas saturadas, sal)
menos puntos positivos (fibra, proteina, fruta/verdura/frutos secos), con umbrales
por tipo de alimento. Con la tabla nutricional que dan Mercadona, DIA, Alcampo y
Carrefour se calcula entero. Asi el campo esta siempre, sea nativo, externo o
calculado, y la columna de procedencia dice cual.

## Regla de oro

Un campo puede ser inferido, pero no puede faltar. Y la interfaz no ensena "n/d":
ensena el valor y, si acaso, de donde sale.
