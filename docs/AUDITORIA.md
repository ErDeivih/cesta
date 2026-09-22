# Auditoria tecnica y hoja de ruta

Estado comprobado el 6 de septiembre de 2026. Este documento distingue lo que
funciona hoy de lo que los documentos de vision proponen para el futuro.

## Resumen real

- Pipeline local operativo: raw -> bronze -> silver -> gold -> DuckDB.
- Tres fuentes ejecutables: Mercadona, Aldi y Alcampo.
- Catalogo actual: 16.490 productos; 16.355 con precio comparable.
- Mercadona: 4.320 productos y primeras 100 fichas maestras con EAN y marca.
- Aldi: 2.096 productos descubiertos por su sitemap oficial; 135 sin precio.
- Alcampo: 10.074 productos reconstruidos desde raw. La API completa mejora el
  antiguo limite SSR de 50, pero AWS WAF todavia puede interrumpir recorridos largos.
- Busqueda local por texto, fuente y marca disponible en `projects.cesta.search`.
- 42 pruebas y analisis estatico limpio.

## Matriz de capacidad

| Pieza | Estado | Observacion |
|---|---|---|
| raw inmutable | operativo | contenido versionado; falta manifiesto con URL/status/fecha |
| bronze/silver/gold | operativo | un dia de historico; aun no prueba tendencias reales |
| DuckDB | operativo | vistas de catalogo actual, historico y precios |
| Mercadona | operativo | maestro incremental: 100 de 4.320 fichas |
| Aldi | operativo | sitemap + API por lotes |
| Alcampo | parcial | 10.074 recuperados; WAF impide garantizar una pasada completa |
| DIA | prototipo | parser sin orquestacion, paginacion ni escritura bronze |
| Carrefour | prototipo | parser sin categorias configuradas, `main` ni validacion viva |
| Lidl | investigacion | sin colector |
| matching/equivalencias | no existe | el EAN apenas empieza a poblarse |
| listas/favoritos/alertas | no existe | `config.yml` no se consume actualmente |
| API/interfaz web/voz | no existe | solo CLI de busqueda |
| dbt/Dagster | no instalado | aparecen en la vision, no en la ejecucion |
| tarea diaria Windows | no creada | `ejecutar.bat` existe, `schtasks` no |
| Git/GitHub | no configurado | la carpeta no contiene `.git`; Actions quedan manuales |

## Fallos graves corregidos durante la auditoria

1. Alcampo interpretaba `5G` de un telefono como 5 gramos y descartaba 1.080
   articulos sin formato. Ahora un articulo es una unidad y solo se usa peso
   variable cuando la fuente lo declara.
2. Las unidades Aldi `pastilla`, `toallita`, `panuelo`, `100-ml`, `g` y
   `m-(metro)` no eran canonicas. Ahora se convierten con semantica de fuente.
3. `producto` no existia en DuckDB por un error al comprobar el glob. Ahora hay
   `producto` (ultima observacion) y `producto_historico`.
4. El WAF hacia perder la categoria que disparaba la renovacion. Ahora se reintenta
   la misma categoria y las respuestas 405 de verificacion humana se reconocen.
5. Una ejecucion parcial podia sobrescribir un bronze completo. Ahora conserva el
   ultimo completo; raw permite reconstruir y reanudar.
6. El cliente aceptaba ciertos HTTP 4xx como datos y duplicaba el argumento timeout.
7. El pipeline eliminaba productos publicados sin precio. Ahora siguen en el
   catalogo con `precio_comparable=false` y no contaminan las series numericas.
8. DIA y Carrefour se saltaban y aun asi el orquestador imprimia `todo correcto`.
9. Aldi usaba 68 paginas de menu y encontraba 559 productos pese a existir un
   sitemap oficial con 2.096.

## Decisiones de arquitectura pendientes

### 1. Identidad y localizacion

Un precio pertenece a producto + tienda/zona + fecha. Hay que incorporar
`ubicacion_id` o `tienda_id`; hoy el codigo postal solo esta implicito en la sesion.
Sin esta dimension, comparar ejecuciones hechas con otra tienda mezcla precios.

Separar definitivamente:

- `producto`: identidad y ficha maestra estable;
- `oferta_diaria`: precio, promocion, stock, zona y momento de captura;
- `observacion_fuente`: exito/fallo/cobertura del colector para distinguir “no
  aparece” de “la fuente fallo”.

### 2. Matching

Orden recomendado: EAN exacto -> bloqueo por categoria/unidad/cantidad -> similitud
lexica -> revision humana. No introducir embeddings hasta tener varios cientos de
pares EAN Mercadona-DIA como conjunto de validacion. Un falso positivo en alergenos
es peor que mostrar “dato desconocido”.

### 3. Fuentes

1. Terminar maestro Mercadona y hacer que DIA produzca EAN.
2. Estabilizar Alcampo: cache/reanudacion, ritmo de 4 s y prueba de varias noches.
3. Implementar DIA de extremo a extremo.
4. Volver a reconocer Carrefour con sus sitemaps actuales y Cloudflare.
5. Dejar Lidl para despues de tener comparacion util con cuatro cadenas.

### 4. Producto local

La siguiente entrega util debe ser una web local pequena, no Dagster:

- buscador y filtros;
- ficha con precio total y unitario por cadena;
- lista de compra y favoritos persistidos en DuckDB/SQLite;
- fecha y zona visibles en cada precio;
- productos sin precio o fuente fallida mostrados honestamente.

### 5. Orquestacion y transformaciones

Dagster es un orquestador: representa cada paso como un activo, registra su estado,
reintenta y muestra dependencias. Aun no hace falta; `run.py` sigue siendo entendible.
Introducirlo cuando haya cuatro o cinco colectores completos, matching y tareas
independientes que necesiten reintentos parciales.

dbt organiza transformaciones SQL, pruebas y documentacion. Tampoco aporta aun mas
que el pipeline Polars. Conviene evaluarlo cuando el modelo DuckDB tenga varias
tablas estables y las transformaciones sean mayoritariamente SQL.

## Riesgos antes de automatizar

- Escritura atomica y bloqueo contra dos ejecuciones simultaneas: implementados;
  falta probarlos durante varias ejecuciones programadas reales.
- Registrar URL, HTTP status, timestamp, hash y parser version en un manifiesto raw.
- Crear copia semanal de `data/raw`; es la unica capa irrecuperable.
- Inicializar Git y hacer el primer commit antes de cambios de producto grandes.
- No activar GitHub Actions: el flujo actual no transporta el historico local y
  Alcampo necesita IP/sesion residencial.
- Revisar terminos de cada sitio ademas de robots.txt. robots.txt orienta a crawlers,
  pero no concede por si solo derechos de reutilizacion o publicacion.
- Mantener el uso personal/local y no publicar volcados completos de catalogos.

## Proximas entregas, en orden

1. Integridad operativa: escrituras atomicas, lock, manifiesto raw y backup.
2. Completar fichas Mercadona y colector DIA.
3. Modelo de zona, observaciones y catalogo actual.
4. Matching EAN + cola de revision.
5. Web local con busqueda, favoritos y lista.
6. Optimizador de cesta; despues alertas, calidad y voz.

---

# Pasada del 17 de septiembre de 2026 (tarde)

Siete fallos encontrados releyendo el crudo. Cuatro de ellos escribian datos
falsos en la plataforma; dos hacian imposible recuperarse de un error; uno era
peligroso de verdad.

## 1. GRAVE — `reprocesar.py` destruia las fichas maestras

`reprocesar` existe para una sola cosa: cuando el parser mejora, rehacer bronze
desde el crudo sin volver a scrapear. Llamaba a `a_registro(producto)` con **un
solo argumento**, y Mercadona y DIA tienen un segundo del que salen el EAN, el
origen, los ingredientes y los alergenos.

Efecto medido al reprocesar Mercadona del 17 de septiembre:

    EAN            4.317 -> 0
    origen         1.443 -> 0
    ingredientes   2.747 -> 0
    alergenos      2.788 -> 0

Y se escribia encima del bronze bueno **sin decir nada**. Una herramienta cuyo
unico proposito es recuperar no puede destruir en silencio.

**Arreglado con dos cosas**: `reprocesar` carga la ficha maestra y se la pasa al
colector; y antes de escribir compara columna a columna con el bronze anterior y
**se niega a escribir** si el nuevo pierde datos (margen del 10 % para absorber
un dia con menos productos). Hay que pedirlo a proposito con `--forzar`.
Pruebas: `tests/test_reprocesar.py`.

## 2. GRAVE — el 42 % del catalogo no se podia reprocesar

Carrefour y DIA guardan **HTML** con extension `.json.gz`. El extractor generico
de `reprocesar` hacia `json.loads`, fallaba y devolvia lista vacia sin quejarse.
O sea: 21.827 productos (Carrefour 16.416 + DIA 5.411) donde arreglar el parser
obligaba a volver a scrapear una web con Cloudflare y otra con Akamai.

Arreglado con `productos_crudo(body)` en los dos colectores. La categoria, que
no se puede recuperar del nombre del fichero (`save_raw` guarda la clave ya
pasada por sha1), se saca de la URL canonica del propio HTML, que ademas es mas
fiable.

## 3. GRAVE — el filtro de dieta ensenaba productos que no lo cumplian

Al probar el filtro recien hecho, "galletas" + **sin gluten** devolvia unas
galletas Cuetara normales, y "pizza" + **congelado** devolvia una salsa barbacoa.

La busqueda trabaja por grupos: un grupo entra si alguno de sus miembros casa, y
luego se reconstruia el grupo **entero** para ensenar el mas barato. Si en el
grupo habia unas galletas sin gluten (3 EUR) y unas normales (1 EUR), se
ensenaban las normales bajo el filtro "sin gluten".

Para alguien celiaco eso no es un resultado flojo: es un resultado peligroso.

**La regla que se ha escrito**: el TEXTO se puede cumplir a nivel de grupo; un
ATRIBUTO tiene que cumplirlo cada producto que se ensena. Pruebas:
`tests/test_catalogo_filtros.py`.

## 4. `de_etiquetas` buscaba subcadenas y el comentario decia que no

El comentario prometia "que la etiqueta SEA el sello o lo contenga como palabra,
no que se parezca". La implementacion usaba `in`. Con `eco` y `bio` en el
diccionario, devolvia el sello **ecologico** para `Seco`, `Recambios`,
`Marruecos`, `economico` y `Ecopack`.

Con etiquetas cortas y controladas nunca llego a fallar. Salto al leer texto
libre: `Origen: Marruecos` marcaba el producto como ecologico. Ahora cada sello
es una expresion regular con limites de palabra.

## 5. Aldi: 1.645 ofertas que acababan en 2030

`currentPrice.validUntil` vale **2030-12-31** en 1.645 de los 2.065 productos.
Es un centinela de "este precio no caduca" y se escribia tal cual en
`promo_hasta`, asi que la plataforma creia que el 79,7 % del catalogo de Aldi
tenia una oferta con fecha de fin. Cualquier pantalla de "ofertas que se acaban"
habria empezado por esa basura.

De paso: exigir precio tachado dejaba fuera **75 de las 170 ofertas**, las que
bajan el precio sin tachar nada y solo se ven en `promotionPrices`.

## 6. DIA: `drained_weight` no es el peso escurrido

El campo se llama "peso escurrido" y no lo es. Coincide **exactamente** con la
cantidad neta en 4.323 de 4.995 productos, y para un litro de aceite de oliva
dice 916, que no es peso escurrido sino **la densidad del aceite**. Tambien dice
8.000 para un refresco de 2 litros y 6.000 para un brik de leche de uno: pesos de
caja.

Si se hubiera usado para "comparar por peso escurrido" en conservas, habria dado
el resultado equivocado en la direccion que mas importa.

Ahora va a `peso_neto_g`, con un filtro de plausibilidad (entre la mitad y el
doble de la cantidad declarada), y `peso_escurrido_g` se queda a None para DIA,
que es la respuesta honesta. De rebote es util: es **el puente entre una cadena
que vende el aceite por litros y otra que lo vende por kilos**.

## 7. DIA: 1.272 productos que caducaban dentro de dos anos y ocho meses

`days_to_expiration` vale **999** en 1.272 fichas: otro centinela de "no caduca".
La despensa deducida habria avisado de que se acaba el arroz en 2029.

## 8. Nueve columnas del contrato no llegaban a gold

El contrato tenia 40 columnas y `emparejar.COLUMNAS` 17. `sellos`, `nutricion`,
`conservacion`, `es_marca_propia`, `tipo_producto`, `envase`, `peso_escurrido_g`,
`dias_caducidad` y `descripcion` se quedaban en silver.

**Un dato que no cruza la frontera de gold es un dato que no existe**: la app
monta gold en solo lectura y no ve nada mas. Se habian conquistado a las cadenas
tres dias antes y no habian llegado a ninguna pantalla.

Ademas, `dia.a_registro` no copiaba a la fila los seis campos que
`_maestro_de_ficha` si sabia producir: existian en `data/master` y en ningun otro
sitio.

## 9. La app se caia entera si gold era mas viejo que el codigo

El scraper escribe `data/gold` y la plataforma lo monta en solo lectura; las dos
mitades se actualizan por separado. Pedir una columna que el ultimo gold aun no
tiene tiraba **la app entera** con un Binder Error, no una busqueda, porque la
conexion se crea al arrancar.

Ahora las columnas nuevas se piden comprobando antes si existen. Un dato que
todavia no existe debe ser None, no una caida.

---

## Lo que se anadio en la misma pasada

| pieza | que hace |
|---|---|
| `core/certificados.py` | los 32 logotipos de certificacion de Aldi -> sellos, origen, marca propia |
| `core/envases.py` | el "frasco" de DIA y el "Tarro" de Mercadona son la misma opcion del filtro |
| `sellos.de_prosa()` | leer sellos de una descripcion, con vocabulario restringido |
| `sellos.conservacion_de_prosa()` | "Conservar a -18 ºC" -> congelado, sin confundirse con "una vez abierto" |
| `projects/cesta/rehacer_maestro.py` | rehace `data/master` desde el crudo, sin red y reanudable |
| filtros de dieta en la busqueda | sello, conservacion, marca blanca, en oferta |
| ficha con sellos, tabla nutricional y certificados | con la procedencia del dato al lado |

285 pruebas en verde, ruff limpio, contrato en 43 columnas, 34 llegan a gold.

---

## Segunda mitad de la pasada: los precios que no se pueden restar

Con los datos nuevos ya en gold, se comprobo lo que la app estaba **anunciando**,
mirando solo los enlaces entre productos con el mismo codigo de barras -- o sea,
el mismo producto sin discusion:

    enlaces con el mismo EAN                    2.680
      con el precio por unidad >2x distinto       180  (6,7 %)
      con el precio por unidad >10x distinto       92  (3,4 %)

Cuatro fallos mas, los cuatro visibles en pantalla:

### 10. La app anunciaba ahorros del 102.896 %

231 grupos comparables (3,7 %) mezclaban unidades distintas dentro del mismo
grupo: la manzanilla Hornimans de 25 bolsitas, a 2,15 EUR en las tres cadenas,
salia como 0,04 EUR/ud en Alcampo, 0,09 EUR/ud en DIA y 61,43 EUR/kg en
Carrefour, que mide el peso de la hierba. Los tres precios son correctos y no se
pueden restar. **Esos 231 grupos eran el 67 % de todos los que decian "mas de
10x"**. Ahora se elige una unidad por grupo y solo se compara dentro de ella.

### 11. Aun asi quedaban 15 grupos imposibles

Azafran que Alcampo etiqueta "400g" cuando son 400 mg, un champan comparado por
botella contra el mismo por unidad, un filete de dorada a 7.120 EUR/kg. La
frontera resulto limpia: **por debajo de 30x son ahorros reales** (marca blanca
contra Durex, 28x), por encima son todos errores. Ahora el grupo se marca
`dudoso` y no pone numero: en pantalla, "precios que no cuadran entre cadenas".

### 12. 72 filas donde nuestro precio y el de la cadena se contradicen

Y no hay forma fiable de saber quien tiene razon, porque hay errores en las dos
direcciones (DIA publica "0,095 g" para unas conchitas de 95 g; Aldi publica
"0,03 EUR/kg" para una barrita proteica). Se apartan de las comparaciones en vez
de elegir ganador. Ver `docs/PRECIO-POR-UNIDAD.md`, punto 3.

Ojo al orden: 148 de las 220 filas que saltaban eran en realidad **envases con
mas piezas de las declaradas**, que ya tenian su propio mecanismo
(`unidades_inferidas`) y es una explicacion mejor.

### 13. El emparejador se hizo un 45 % mas lento sin tocar el algoritmo

Recorre 16,7 millones de pares candidatos consultando el diccionario de cada
fila. Al pasar el contrato de 17 a 34 columnas, los mismos pares costaron de 79 s
a mas de 115 s: diccionarios mas grandes, peor localidad de cache.
`matching.adelgaza()` se queda con las seis columnas que mira de verdad y
devuelve el tiempo. Lo que importa no es el 30 % de hoy, es que **deja de
empeorar cada vez que se le gana un dato a una cadena**.

### Y algo que no es un fallo pero conviene decidir

`data/externo/food.parquet` ocupa **7,85 GB**: es el volcado mundial de Open Food
Facts. Al lado, `off_es.parquet` -- el extracto espanol, que es el que usa el
pipeline -- ocupa 25 MB. El grande solo hace falta para regenerar el extracto.
Borrarlo libera 7,8 GB en el disco de casa y solo cuesta volver a descargarlo el
dia que se quiera refrescar Open Food Facts.

---

## Estado al cerrar la pasada

    290 pruebas en verde          ruff limpio
    contrato        43 columnas   a gold llegan 34
    catalogo        52.575 productos de 5 cadenas
    comparables      6.448 grupos entre cadenas
    con sello       11.910 (20,7 %), con su procedencia
    con certificado    729
    con nutricion    3.723
    con envase       8.829
    documentos          33

---

# Tercera pasada del 17 de septiembre: la herramienta que mira sola

La conclusion de las dos pasadas anteriores fue que **siete veces seguidas**
habia aparecido un dato guardado en `data/raw` que ningun colector leia, y las
siete porque a alguien se le ocurrio mirar a mano. Eso no se puede planificar,
asi que se automatizo: `projects/cesta/auditar_crudo.py`. Ver
`docs/AUDITAR-CRUDO.md` para lo que encontro (y para lo que descarto, con su
medicion, que es igual de util).

Cuatro fallos nuevos, todos encontrados por el camino:

## 14. `\b` no delimita numeros pegados a puntuacion. Dos veces el mismo dia

Alcampo tenia 3.125 textos de oferta y **cero** fechas de fin, y la fecha estaba
dentro del texto todo el tiempo:

    "Todo a 1€ (14/09/2026 - 08/10/2026)"       no casaba: € no es caracter de palabra
    "Producto en Folleto (10/09/26_23/09/26)"   no casaba: _ SI es caracter de palabra

Los dos con `\b` de por medio, y los dos fallando por la razon contraria. Ahora
se usan miradas `(?<!\d)` y `(?!\d)`, que es lo que habia que usar desde el
principio para delimitar numeros. Resultado: 1.904 productos de Alcampo con
fecha de fin donde antes habia cero.

## 15. "champu" empieza como "champan"

El detector de alcohol daba un 77 % de precision, y toda la culpa era de un
patron que decia `champ`. Marcaba como bebida alcoholica **todos los champus
anticaspa del catalogo**.

Es literalmente el mismo error que "eco" dentro de "seco" en `core/sellos.py`,
cometido el mismo dia y por la misma razon: buscar un prefijo creyendo que se
busca una palabra. Con limites de palabra, y quitando la comida que se llama como
una bebida ("vinagre de Jerez", "carrilladas al vino", "coctel de frutos secos"),
la precision es del **100 %** contra lo que declaran Alcampo y Mercadona.

## 16. Una oferta de tarjeta presentada como oferta

No llego a pasar, pero estuvo a un paso. Al encontrar el texto de las ofertas de
DIA -- 221 productos que antes no teniamos -- resulto que **200 son solo con la
tarjeta Club**. En el proyecto ya estaba decidido que un descuento de tarjeta no
baja lo que pagas en caja: se acumula en un monedero. Cablearlo sin mas habria
hecho que la app anunciara 200 rebajas que no estan en el ticket.

Ahora hay una columna `promo_club`, el filtro "en oferta" las excluye, la tarjeta
del resultado dice "oferta solo con tarjeta" y la ficha, con esas palabras: "solo
con la tarjeta de la cadena -- no baja lo que pagas en caja".

## 17. El emparejador se comia un minuto y medio de cada iteracion

Recorre 16,7 millones de pares candidatos. Cada columna que se anade al contrato
lo hace mas lento, aunque el algoritmo no cambie, porque construye un diccionario
por producto. Dos arreglos:

  * `catalogo_actual()` ya no materializa las 40 columnas de gold: solo las nueve
    que se usan de verdad.
  * `--reusar-enlaces` reutiliza `enlaces.parquet` cuando el cambio no toca
    ninguna de las seis columnas que mira el emparejador. Con la comprobacion de
    que el catalogo siga teniendo el mismo tamano, porque los enlaces son pares
    de **posiciones**: usarlos contra un catalogo distinto emparejaria productos
    al azar. Iterar en la calidad o en una columna nueva pasa de 97 s a 9 s.

---

## Estado al cerrar el dia

    302 pruebas en verde          ruff limpio
    contrato        49 columnas   a gold llegan 40
    catalogo        52.575 productos de 5 cadenas
    comparables      6.448 grupos entre cadenas
    con sello       11.910 (22,8 %), con su procedencia
    con texto de oferta  6.825    con fecha de fin  5.461
    con alcohol      3.316 (declarado en 2 cadenas, deducido en 5)
    documentos          34

---

# 18 de septiembre: la revision de la ingesta

Detalle completo en `docs/INGESTA-18SEP.md`. Resumen de los fallos, numerados
desde el 17:

### 18. Alcampo entrego un catalogo sin la seccion de frescos, con cero errores

2.646 productos de Frescos el dia 17, **91** el 18. Se dio por completa, se
escribio el bronze y salio a la app. Los tres controles que habia miran el total,
y un total puede bajar un 13 % por mil razones normales. Arreglado con
`core/cobertura.py`, que compara rama a rama y dice que no sin mirar el tamano.

### 19. Carrefour perdio el 57 % del catalogo por no reintentar un 403

373 de 653 categorias bloqueadas por Cloudflare durante unos veinte minutos. El
`Fetcher` reintentaba 429, 500, 502, 503 y 504, pero **no el 403**, y el bucle no
volvia nunca a por la categoria fallida. El bloqueo se levanto solo a mitad de
ejecucion, con las 373 ya descartadas. Arreglado con reintentos y con tres
vueltas de rescate a ritmo decreciente.

### 20. El silver sobrevivio a su bronze y volvio a colar el catalogo roto

Apartar el bronze malo no bastaba: el silver derivado de el seguia en disco, con
fecha mas nueva, y el emparejador coge el mas reciente. El arreglo parecia no
funcionar. Ahora el pipeline tira el silver huerfano al escribir.

### 21. "Diferencia imposible" significaba dos cosas distintas

El resumen usaba 3 veces y la interfaz 30. El resumen avisaba de 340 diferencias
"imposibles" que en su mayoria eran reales -- marca blanca contra marca llega a
28 veces. La regla vive ahora en `core/comparacion.py` y el resumen separa las dos
bandas: 352 grandes pero creibles, **5** imposibles.

### 22. `precio_comparable` no llegaba a gold

Las 72 filas en disputa del 17 de septiembre seguian decidiendo donde estaba mas
barato algo, porque la bandera se quedaba en silver. Eran los peores casos del
resumen del dia.

### 23. El cupo de fichas de DIA dejaba una deuda que crecia sola

459 productos nuevos, cupo de 100 fijo, 374 sin ficha -- o sea sin EAN, sin
ingredientes y sin nutricion. Al dia siguiente vuelve a haber nuevos y la cola no
baja. Ahora el cupo es lo que falte, con suelo de 100 y techo de 400.

---

## Estado al cerrar el 18 de septiembre

    308 pruebas en verde          ruff limpio        35 documentos
    contrato        50 columnas   a gold llegan 43
    catalogo        52.575 productos de 5 cadenas
      alcampo y carrefour con la captura del 17: la del 18 no paso el control
    comparables      6.448 grupos entre cadenas
    con sello       11.910   con nutricion 3.723   con envase 8.829
    diferencias imposibles: 5 (eran 340 con el criterio viejo)
