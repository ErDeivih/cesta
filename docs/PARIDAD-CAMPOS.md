# Que dato tiene cada cadena, campo a campo

Medido el 17 de septiembre de 2026 sobre `data/gold/grupos.parquet`, despues de
la pasada de mineria de ese dia. **Este es el documento que hay que mirar antes
de prometer una funcionalidad**: si una columna esta al 0 % en las dos cadenas
grandes, la pantalla que la necesita no se puede hacer todavia.

A David no le gusta ver "dato no encontrado". Esta tabla dice exactamente donde
va a salir y por que.

---

## 1. La matriz

```
campo                alcampo      aldi carrefour       dia mercadona     TOTAL
(productos)            23793      2065     16416      5411      4317     52002
------------------------------------------------------------------------------
nombre                  100%      100%      100%      100%      100%      100%
marca                   100%       91%       99%       97%       95%       99%
ean                       0%        0%       93%      100%      100%       48%
precio_cent              97%       93%      100%      100%      100%       98%
imagen                  100%      100%      100%      100%      100%      100%
categoria               100%       97%      100%      100%      100%      100%
url                     100%      100%      100%      100%      100%      100%
origen                    0%       15%        0%        0%       33%        3%
ingredientes              0%        0%        0%       76%       64%       13%
alergenos                 0%        0%        0%       20%       65%        7%
sellos                   26%       19%       24%        3%        4%       21%
certificados              0%       35%        0%        0%        0%        1%
conservacion             22%        6%        5%        0%       41%       15%
es_marca_propia          11%       25%        0%        0%        0%        6%
nutricion                 0%        0%        0%       68%        0%        7%
tipo_producto             0%        0%        0%      100%        0%       10%
envase                    0%        0%        0%       98%       80%       17%
peso_neto_g               0%        0%        0%       86%        0%        9%
dias_caducidad            0%        0%        0%       78%        0%        8%
descripcion               0%       63%        0%      100%*     100%       11%
grado_alcohol             0%        0%        0%        0%        4%        0%
promo_txt                13%        4%       21%        0%        0%       13%
promo_hasta               0%        8%       21%        0%        0%        7%
```

\* DIA tiene texto de ficha pero aun no se pasa a `descripcion`; ver punto 4.

**Cuidado con dos numeros que se parecen y no son lo mismo**: la ficha maestra de
DIA tiene tabla nutricional en **3.737** productos, y a gold llegan **3.723**. La
diferencia son fichas de productos que hoy no estan a la venta. El que vale para
hablar de la app es el de gold; el del maestro solo sirve para medir el lector de
fichas.

---

## 2. Como leer esto

**Una columna sirve para una pantalla cuando llega a las dos cadenas grandes.**
Alcampo (23.793) y Carrefour (16.416) son el 77 % del catalogo. Una funcionalidad
que solo funcione con DIA cubre el 10 % de lo que la gente busca, y va a producir
la sensacion de app rota aunque el dato sea correcto.

Con esa regla:

| se puede hacer ya | esta a medias | no se puede todavia |
|---|---|---|
| filtrar por sello (21 %, las tres grandes) | filtrar por conservacion (15 %, falta DIA y Carrefour) | ficha nutricional (7 %, solo DIA) |
| ver la foto (100 %) | escanear codigo de barras (48 %, falta Alcampo y Aldi enteros) | filtrar por origen (3 %) |
| comparar precio por kg/l (78 %) | marca blanca (6 %) | despensa por caducidad (8 %, solo DIA) |
| envase (17 %, DIA y Mercadona) | | grado de alcohol (0,3 %) |

---

## 3. Los agujeros, por orden de lo que costaria taparlos

### 3.1 Ingredientes y alergenos en Alcampo y Carrefour — 0 %

Es el agujero mas caro y el mas valioso. Son el 77 % del catalogo y no tenemos
**nada** de composicion. Hoy la letra de calidad se calcula ordenando por precio
en el 77 % de los casos (ver `docs/VEREDICTO.md`), y esta es la razon.

Las dos publican ficha de producto con su propia URL. **No se ha sondeado
ninguna**: `projects/cesta/sondear_fichas.py` existe y no se ha ejecutado nunca,
porque la sesion que escribe este codigo no tiene red hacia esos dominios.

> **Tarea para el agente que implemente**: ejecutar `sondear_fichas.py` contra 30
> fichas de Alcampo y 30 de Carrefour, listar los campos con su porcentaje, y si
> aparecen ingredientes, anadir el barrido de fichas por tandas igual que hacen
> `dia.py` y `mercadona.py` (un `data/master/<cadena>.json.gz`, no una peticion
> por producto y dia). Alcampo esta detras de AWS WAF: ver `docs/PATCHRIGHT.md`.

### 3.2 EAN en Alcampo y Aldi — 0 %

Bloquea el escaner en el 50 % del catalogo. Aldi **no tiene EAN**: su
`productReferences` solo trae `KVArticleNumber`, su codigo interno. Comprobado
sobre los 2.065 productos, no hay ni uno.

Esto no es un fallo que arreglar: es un limite de la cadena. Lo que si se puede
es lo que ya se midio el 16 de septiembre: **el codigo de barras es del
fabricante**, asi que escanear una Coca-Cola dentro de un Alcampo casa con la
fila de Carrefour y el grupo llega a Alcampo igualmente en el 34 % de los casos.
La marca propia de Alcampo y Aldi, no.

### 3.3 Texto de oferta en DIA y Mercadona — 0 %

Las dos saben que hay oferta (`is_promo_price`, `price_decreased`) pero no
publican **que oferta es** en el listado. Sin el texto no se puede aplicar
`core/promos.py`, que es lo que convierte "2ª unidad -50 %" en un precio real.

> **Tarea**: mirar en la ficha de producto de DIA (`/api/v1/product/<sku>`) y en
> la de Mercadona si viene el texto de la promocion. Las dos fichas ya se
> guardan en `data/raw`, asi que **esto se puede medir sin red**, con
> `projects/cesta/rehacer_maestro.py` como punto de partida.

### 3.4 Conservacion en DIA — 0 %

DIA tiene `item_treatment_type` en su ficha y no se lee. Medirlo es gratis: las
5.410 fichas estan en disco.

---

## 4. Lo que ya se puede cablear sin pedirle nada a nadie

Todo esto esta **descargado y guardado** en `data/raw`, y solo falta leerlo:

| dato | cadena | donde esta | productos |
|---|---|---|---|
| texto de ficha | DIA | `product.value` y campos de la ficha | 5.410 |
| tratamiento (frio/ambiente) | DIA | `item_treatment_type` | por medir |
| variedad | DIA | `item_variety`, `variety_description` | por medir |
| categoria estructurada | DIA | `family_code`, `subfamily_code`, `section_code` | 5.410 |
| aviso de alcohol | Mercadona | `badges.requires_age_check` | ~200 |
| caracteristica principal | Mercadona | `main_feature` ("ultracongelado") | 58 % |
| retirada de producto | Aldi | `isRecall` | 0 hoy, ver punto 5 |

**La regla del proyecto**: antes de pedirle un campo nuevo a una web, buscarlo en
`data/raw`. Ha aparecido ahi las siete veces que se ha mirado.

---

## 5. `isRecall`: una funcionalidad que nadie tiene

Aldi publica un booleano `isRecall` en los 2.065 productos. Hoy vale `false` en
todos, pero el campo **existe**, lo que significa que Aldi lo pone a `true`
cuando retira un lote.

Ninguna app de la competencia avisa de retiradas de producto. Nosotros guardamos
la lista de la compra y sabemos que compro cada persona: si un dia `isRecall`
pasa a `true` para algo que esta en una lista, se puede avisar.

> **Tarea, pequena y barata**: pasar `isRecall` a bronze como una columna
> booleana, y que el resumen diario cuente cuantos hay. Cuando deje de ser cero,
> ya habra donde engancharlo. Fuente externa complementaria: las alertas
> alimentarias de AESAN, que son publicas.

---

## 5-bis. Lo que cambio la tarde del 17 de septiembre

`projects/cesta/auditar_crudo.py` encontro, solo, otra tanda de campos guardados
y sin leer. Ver `docs/AUDITAR-CRUDO.md`. Resumen de lo que movio la matriz:

| campo | antes | ahora | de donde |
|---|---:|---:|---|
| sellos | 10.761 | **11.910** | `allergens[].name` y `product_info` de DIA |
| promo_txt | 6.604 | **6.825** | `promotions[].description` de DIA |
| promo_hasta | 3.557 | **5.461** | la fecha dentro del texto de Alcampo |
| peso_neto_g | 4.665 | **5.436** | `catchweight` de Alcampo |
| peso_escurrido_g | 0 | **179** | `drained_weight` de Mercadona (el de verdad) |
| es_alcohol | — | **3.316** | declarado por 2 cadenas + deducido para las 5 |
| promo_club | — | **200** | `only_club_dia` de DIA |
| distintivo | — | **550** | `stamp_description` de DIA |
| advertencias | — | **450** | `icons[].label` de Alcampo (pictogramas CLP) |
| peso_variacion_pct | — | **742** | `catchweight` de Alcampo |
| es_recall | — | **0** | `isRecall` de Aldi: existe, hoy vale false |

---

## 6. Como se regenera esta tabla

```
uv run python -m projects.cesta.verificar_docs     # comprueba las cifras
```

La matriz se saca con una consulta de cinco lineas sobre `data/gold/grupos.parquet`:
contar no nulos por `fuente` para cada columna. Si se anade una columna al
contrato, **se anade tambien aqui**, o el siguiente que lea este documento
prometera una pantalla que no se puede hacer.
