# F08 -- Comparar, presupuesto y ahorro de verdad (P1)

**Criterio, de `docs/SUPERAPP-FASE2-EMPEZAR-AQUI.md:129`:**

> Investigar C06-C10 con Soysuper/Bring!/Listonic. Pantalla del mismo articulo con **formato/fecha/ambito**...
> Presupuesto de compra y **gasto pagado** por periodos/categorias. **Precio manual de recibo se conserva como
> pagado**...
> **Aceptacion:** lista parcial, **cupon/club no elegible**, **oferta caducada**, **cantidad/pack**, **historico
> desconocido**

**Y los cinco criterios que cubre, de `docs/SUPERAPP-COMPETENCIA-Y-REA.md:94-98`:**

| ID | lo que pide |
|---|---|
| **C06** | *comparar articulo/cesta* -- identidad/formato, ambito y fecha visibles; cantidad/promocion elegibles y **coste parcial explicito** |
| **C07** | *una tienda frente a varias* -- maximo de tiendas y coste de desplazamiento optativo; **ahorro neto definido**, oraculo multi-tienda |
| **C08** | *club/ofertas* -- condiciones y **vigencia**; **credito futuro separado del dinero pagado hoy** |
| **C09** | *presupuesto/gasto* -- **previsto contra guardado/pagado sin mezclar**; cobertura de lineas desconocidas |
| **C10** | *historial/reutilizar compra* -- **copiar necesidades, nunca precios antiguos como si fueran actuales** |

---

## 1. Punto de partida: lo que ya esta medido de estos cinco, y donde

**Nada de C06-C10 se ha medido en esta fase todavia** -- *y conviene decirlo antes de empezar, porque en esta
fase he dado por hecho lo contrario ocho veces.* **Lo que si existe, medido en OTROS paquetes y por otros
motivos:**

| pieza | donde se midio | **y que es de F08** |
|---|---|---|
| **el oraculo multi-tienda** | **F06**, con su oraculo | *`C07`: «ahorro neto definido, oraculo multi-tienda»* -- *el oraculo **es de F06**, y el ahorro neto de F08* |
| **la identidad** (`AvisoIdentidad`, `core/identidad.py`) | F01 y F07 | *`C06`: «identidad/formato, ambito y fecha visibles»* |
| **las promociones** (`cesta.coste_por_linea`, `promo`, `promo_hasta`) | F01 | *`C06`: «cantidad/promocion elegibles»; `C08`: «condiciones y vigencia»* |
| **el cierre de compra** (`cierra_compra`, `compra` con `total_cent` y `sin_precio`) | F07 (§10) | *`C09`: «previsto contra guardado/pagado sin mezclar»* |
| **la frescura** (`fecha_de_gold`, `procedencia`) | F03 y F05 | *`C06`: «ambito y fecha visibles»* |

**Asi que F08 no empieza de cero**: *empieza con **cinco piezas ya medidas en otros paquetes**, y lo que hay que
medir es **si cumplen el criterio de F08** -- que es distinto de que existan.*

### Y los cinco casos de la aceptacion, que son lo que hay que probar

**La aceptacion no pide funciones: pide **cinco casos dificiles**, y son los que hay que ejercer:

1. **lista parcial** -- *una lista donde solo algunas lineas tienen precio*
2. **cupon/club no elegible** -- *una oferta que **no se puede** aplicar, y que no se aplique*
3. **oferta caducada** -- *una promocion **ya vencida**, que no cuente*
4. **cantidad/pack** -- *un 3x2 o un pack de 2, donde la cantidad cambia el precio unitario*
5. **historico desconocido** -- *un producto que **no estaba** en el historico*

**Y los cinco son «casos raros»**: *el camino facil es que el precio salga bien cuando todo esta; **lo que el
criterio prueba es que salga bien cuando falta algo.*** **Es la misma forma que las cuatro etapas de F03: lo que
se prueba es el fallo, no el exito.**

### Y la primera medida, que es un `SELECT`

**Antes de montar nada**: *`compra` guarda `total_cent` **y** `sin_precio`* -- *medido en F07 (§10).* **Lo que
hay que ver es si el **presupuesto** y lo **pagado** son dos numeros separados o uno solo** -- *porque el
criterio dice **«sin mezclar»**, y esa palabra es el criterio entero de `C09`.*

**Es un `SELECT` sobre `compra` y sobre las columnas de presupuesto, y va antes que cualquier pantalla.**


---

## 2. `C09`: **«pagado» esta, con su cobertura; «previsto» no existe** -- y es un hueco de verdad

*(Ronda 105.)* El `SELECT`, que iba antes que cualquier pantalla.

### Lo que hay

```
tablas con «compra» o «presupuesto»:  compra, compra_linea
    (y NINGUNA tabla de presupuesto)

compra:
    id, lista_id, usuario_id, cerrada_en, lineas, sin_precio, total_cent
```

**Y el criterio de `C09`** (*`SUPERAPP-COMPETENCIA-Y-REA.md:97`*): *«**Previsto contra guardado/pagado sin
mezclar**; cobertura de lineas desconocidas.»*

| mitad del criterio | **estado** |
|---|---|
| **«pagado»** | **esta**: `compra.total_cent` -- *lo que costo, al cerrar* |
| **«cobertura de lineas desconocidas»** | **esta**: `compra.sin_precio` -- *cuantas lineas no tenian precio* |
| **«previsto»** | **NO EXISTE** |
| **«sin mezclar»** | *no hay nada que mezclar, porque solo hay un numero* |

### Y comprobado que no esta en otro sitio, que es la leccion de esta fase

**Antes de decir «no existe» mire los tres sitios donde podria estar escondido** -- *porque **tres veces esta
sesion concluí de una capa y estaba en otra**:*

1. **¿una tabla?** *No: la consulta a `information_schema` no devuelve ninguna.*
2. **¿una preferencia?** *Hay `preferencias_de` / `guarda_preferencia`, y **no** aparece ninguna clave de
   presupuesto en el codigo.*
3. **¿el codigo?** ***Y aqui esta lo que decide*** -- *`git grep -i presupuesto` devuelve **dieciseis lineas, y
   todas son de COLECTOR**:*

```
alcampo.py:396    PRESUPUESTO_BARRIDO_S = 1200   # 20 minutos
dia.py:485        presupuesto = min(max(config.DIA_DETALLES_POR_DIA, faltan), ...)
mercadona.py:291  presupuesto = config.MERCADONA_DETALLES_POR_DIA ...
fichas_carrefour.py:28  «Procesa hasta limite fichas -- con presupuesto...»
```

**Son presupuestos de tiempo y de peticiones -- de cuanto trabajo se hace en una pasada --, no de dinero.**
*La palabra esta en el proyecto, **y significa otra cosa** -- que es justo el error que he cometido cuatro veces
esta fase: `nutriben`, `energy`, `nutrition_information` y `valores nutricionales` eran palabras de nutricion
que no eran nutricion.* **Aqui la palabra es «presupuesto», y es de colector.**

### Y lo que esto es, para F08

**No un hallazgo de «ya estaba hecho»** -- *que es lo que me ha pasado cinco veces hoy* --, **sino lo contrario:
una mitad del criterio que **falta**, y que se puede decir con precision por que falta:**

> **«Previsto contra guardado/pagado sin mezclar»** pide **dos numeros que se puedan mirar juntos y no se
> confundan**. *El proyecto guarda **uno** -- lo pagado, con su cobertura --, y **no guarda el previsto**.* **Asi
> que el «sin mezclar» hoy se cumple por vacio: no hay dos numeros que mezclar.**

**Y hay que decir tambien lo que SI se puede hacer ya sin construir nada**: *la **estimacion** de lo que costara
la lista existe -- `cesta.coste_por_linea` la calcula, y **la pantalla la ensena** (`estimacion.sin_precio`, en
`Cesta.tsx:1511`).* **Eso es «previsto» en el sentido de «lo que va a costar ahora mismo»** -- *y es **distinto**
de un presupuesto que la persona se ponga.*

**Asi que `C09` tiene tres piezas y hay que separarlas:**

| pieza | **estado** |
|---|---|
| **lo que va a costar la lista ahora** (estimacion) | **hecho**, y en pantalla |
| **lo que se pago** | **hecho**: `compra.total_cent` |
| **lo que la persona se propone gastar** | **NO EXISTE** -- *y es el «previsto» del criterio* |

*Y cual de las tres es «presupuesto» **es una decision del dueno**, no una medicion* -- *que es exactamente el
tipo de cosa que hay que preguntar en vez de construir.*

### Y los cinco casos de la aceptacion, con lo que ya se sabe

| caso | **pieza que lo cubre, si existe** |
|---|---|
| **lista parcial** | *`sin_precio` -- y la estimacion lo dice en pantalla* |
| **cupon/club no elegible** | *por medir: `promo_club`, `promo_solo_online` estan en el catalogo* |
| **oferta caducada** | *por medir: `promo_hasta` esta* |
| **cantidad/pack** | *por medir: `unidades_pack`, `promo_unidades_minimas` estan* |
| **historico desconocido** | *por medir: `historial_de` existe* |

**Los cinco tienen columna.** *Y que la columna este **no es** que el caso funcione* -- *es que hay donde
mirarlo, que es distinto.*


---

## 3. La oferta caducada: **la fecha se guarda y se ensena; que se cumpla, sin medir**

*(Ronda 106.)* De los cinco casos de la aceptacion, **el que puede mentir en el precio** es *«oferta caducada»*
-- *una promocion terminada que siga descontando.* **Y lo medido es la mitad.**

### Lo que hay, y son las tres piezas menos una

```
core/schemas.py:41            "promo_hasta": pl.Datetime("us", "UTC")        <- se GUARDA
catalogo.py:848               f"{c}::VARCHAR AS {c}" if c == "promo_hasta"   <- se CONVIERTE
catalogo.py:953               "promo_hasta": f["promo_hasta"][:10] ...       <- se SIRVE
Grupo.tsx:637                 {p.promo_hasta && `... hasta el ${fechaTexto(...)}`}   <- se ENSENA
alcampo/aldi/carrefour/lidl.py   "promo_hasta": ...                          <- los colectores la leen
```

**Y las 18 menciones de `promo_hasta` no incluyen **ninguna** comparacion con la fecha de hoy.** *No hay un
`WHERE promo_hasta > now()`, ni un `if` que descarte una promocion vencida.*

### Y lo que eso significa, con cuidado

**La fecha se guarda, se sirve y **se ensena en la pantalla**** -- *con su «hasta el ...», que es lo que hace
que la persona pueda juzgar por si misma.* **Y que la promocion **se aplique o no** despues de esa fecha no lo
he medido**: *no he encontrado donde se compare, **y no he encontrado donde no** -- que es distinto.*

**Asi que `C08` queda asi:**

| lo que pide el criterio | **estado** |
|---|---|
| **«condiciones y vigencia»** -- *las condiciones* | *por medir* (`promo_club`, `promo_solo_online`) |
| **«condiciones y vigencia»** -- *la vigencia, **visible*** | **hecho**: la fecha se guarda y se ensena |
| **«condiciones y vigencia»** -- *la vigencia, **aplicada*** | **SIN MEDIR** -- *18 menciones, ninguna comparacion con hoy* |
| **«credito futuro separado del dinero pagado hoy»** | **por medir** |

### Y una pieza que aparece y conviene guardar

**El comentario de `catalogo.py:836` explica **otra cosa** -- y es un arreglo con su prueba:**

> *«Ojo con `promo_hasta`: es un `TIMESTAMP WITH TIME ZONE` y se pide **ya convertido a texto**. DuckDB, para
> devolverlo como objeto de fecha, importa `pytz` por debajo, y la imagen de la API no lo trae -- ni debe,
> porque la API no maneja zonas horarias. Sin el `::VARCHAR` la pantalla de grupo, que es la pantalla clave del
> encargo, **daba 500** en cuanto un miembro tenia promocion con fecha; **y era la mayoria**. Lo vigila
> `test_la_ficha_del_grupo_no_necesita_pytz`.***

**Un 500 que afectaba a «la mayoria» de los miembros con promocion, arreglado, con su prueba, y con el motivo
escrito** -- *que es la quinta pieza de esta fase que aparece **ya resuelta y documentada** mientras buscaba otra
cosa.*

### Y lo que hay que hacer para cerrar «oferta caducada», que es una prueba

**Coger una promocion con `promo_hasta` **ya vencida** y comprobar **si el precio que sirve la API la
descuenta**.** *Es un `SELECT` sobre `grupos` mas una llamada a `catalogo.buscar` -- sin navegador y sin red.*

**Y hay que hacerlo **antes** de tocar nada**: *si el descuento **no** se aplica, la promocion vencida solo
queda como texto informativo, y **esta bien**; si **si** se aplica, **es un defecto que miente en el precio** --
que es el peor sitio donde puede mentir un dato en esta aplicacion.*
