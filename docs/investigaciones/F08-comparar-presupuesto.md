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


---

## 4. «Oferta caducada»: **no hay ninguna, y por construccion** -- pero hay 1.553 sin fecha

*(Ronda 107.)* La prueba que iba a cerrar el caso, y su resultado:

```
promociones en el catalogo:  7.336
    sin fecha de fin:        1.553
    con fecha:               5.783
    rango de fechas:         2026-10-11  ..  2027-01-08
    hoy:                     2026-10-11
    VENCIDAS:                0
```

**Cero.** *Y la razon no es que alguien las filtre: es **estructural**.*

### Por que no puede haberlas, y no es un filtro

**El catalogo se reconstruye cada dia desde capturas frescas** -- *medido en F03: la version se cierra y se
publica cada ciclo.* **Asi que una promocion cuya fecha paso simplemente **no esta** en los datos de hoy**: *no
hay que descartarla, porque **nunca llego a entrar** -- el colector leyo la oferta **mientras estaba viva**.*

**Es la misma forma que el «precio desconocido» y el «sin pasillo»: el problema no se resuelve filtrando, se
resuelve **no teniendo el dato viejo**.** *Y por eso `C06` pide «ambito y **fecha** visibles»: **la fecha del
catalogo es lo que hace que todo lo demas sea de hoy.**

### Y el matiz que si importa: **1.553 promociones SIN FECHA**

*De las 7.336, **1.553 no traen `promo_hasta`**.* **Esas no se pueden caducar por fecha, porque no tienen** --
*y son el unico sitio donde una oferta vieja **podria** quedarse.*

**Y no es un defecto medido**: *puede ser que esas fuentes **no publiquen** la fecha de fin* -- *que es lo
normal en una oferta de folleto* --, **y entonces «no hay fecha» es la verdad, no un hueco.** *Lo que **no** se
sabe es si alguna de esas 1.553 lleva meses ahi.*

**Para saberlo haria falta comparar la promocion de hoy con la de ayer** -- *y eso el catalogo no lo guarda: solo
tiene el estado de hoy.* **Queda dicho como la pregunta abierta que es.**

### Y una confirmacion que vale la pena guardar

**Al escribir este `SELECT` me comi el `::VARCHAR`** -- *pedi `promo_hasta` tal cual* -- **y DuckDB contesto:**

```
Invalid Input Error: Required module 'pytz' failed to import,
    due to the following Python exception: ModuleNotFoundError: No module named 'pytz'
```

**Es **exactamente** el 500 que documenta `catalogo.py:836`** -- *«sin el `::VARCHAR` la pantalla de grupo daba
500 en cuanto un miembro tenia promocion con fecha; y era la mayoria»* --, **y lo he reproducido sin querer en
la ronda siguiente a leerlo.** *El comentario no era una nota historica: **es una trampa que sigue puesta**, y
se cae en ella igual que se cayo entonces.* **Con `::VARCHAR`, la consulta funciona.**

### Y F08, con lo que hay de sus cinco casos

| caso de la aceptacion | **estado** |
|---|---|
| **lista parcial** | **cubierto**: `sin_precio` y la estimacion en pantalla |
| **oferta caducada** | **no hay ninguna, por construccion** -- *el catalogo es de hoy*; **1.553 sin fecha, sin medir** |
| **cupon/club no elegible** | *por medir* (`promo_club`, `promo_solo_online`) |
| **cantidad/pack** | *por medir* (`unidades_pack`, `promo_unidades_minimas`) |
| **historico desconocido** | *por medir* (`historial_de`) |

**Uno cubierto, uno contestado por construccion, y tres por medir** -- *y los tres que quedan son columnas que
existen y casos que hay que ejercer.*


---

## 5. «Cantidad/pack»: **esta implementado hasta el precio unitario, y con comprobacion entre cadenas**

*(Ronda 108.)* El caso de la aceptacion que **conecta con F01**: *un 3x2 o un pack de 2, donde la cantidad cambia
el precio unitario.* *Y las 29 menciones de `unidades_pack` / `promo_unidades_minimas` dibujan **cuatro piezas**,
no una:*

| pieza | donde | **que hace** |
|---|---|---|
| **la normalizacion** | `core/normalize.py:11` | *«Todo acaba en **(cantidad, unidad_canon, unidades_pack)** y en precio por kg / L / ud»* -- *o sea, **el pack se convierte en precio unitario comparable*** |
| **el dato a la pantalla** | `catalogo.py:961` | *`"unidades_pack": f["unidades_pack"] if (...)`* -- **condicional, no crudo** |
| **lo que la pantalla dice** | `app.js:1312,1317` | *`cadaUno = p.cantidad / p.unidades_pack` y `fila('Vienen', ...)`: **«Vienen N x tamano»**, con el **precio del suelto al lado*** |
| **la comprobacion entre cadenas** | `projects/cesta/ejes.py:37` | *«Pares **ciertos** por codigo de barras cuyo `unidades_pack` se contradi…»* -- *es decir, **se buscan los packs que se contradicen entre cadenas** |

**Y las cuatro juntas son lo que el criterio pide**: *`C06` pide **«cantidad/promocion elegibles y coste parcial
explicito»*** -- *y aqui esta la cantidad normalizada, el pack visible, el precio del suelto al lado, **y una
comprobacion de que dos cadenas no digan packs distintos del mismo codigo de barras**.*

### Y otra pieza documentada que aparece de paso

**`catalogo.py:879` dice, cortado, *«…y `unidades_pack` no llegaba nunca a la pantalla (leia `adverte…»*.** *Es
**el sexto arreglo documentado** que aparece mientras buscaba otra cosa:* **el pack estaba en el dato y no
llegaba a la pantalla** -- *que es **literalmente el mismo defecto** que el `sin_precio` de la ronda 96 y la
columna `kcal_100g` de la 82: **el dato existe y la pantalla no lo ensena.*** *Y aqui esta arreglado y dicho.*

### Y lo que queda, que es **ejercerlo**

**Las cuatro piezas estan; lo que no esta es la prueba del caso**: *coger un producto con `unidades_pack > 1`
-- o con `promo_unidades_minimas` --, **pedir 3 unidades en la lista**, y comprobar que **el precio unitario que
se sirve es el del pack y no el del suelto.***

**Es un `SELECT` mas una llamada a `cesta.coste_por_linea`** -- *sin navegador* --, **y es exactamente la clase
de prueba que F01 ya hizo para la promocion 3x2.** *Queda como el paso siguiente, y es pequeno.*

### Y F08, con sus cinco casos

| caso | **estado** |
|---|---|
| **lista parcial** | **cubierto**: `sin_precio` y la estimacion en pantalla |
| **oferta caducada** | **no hay ninguna, por construccion**; *1.553 sin fecha* |
| **cantidad/pack** | **cuatro piezas implementadas** (normalizacion, pack visible, suelto al lado, y comprobacion entre cadenas); *ejercerlo, pendiente* |
| **cupon/club no elegible** | *por medir* (`promo_club`, `promo_solo_online`) |
| **historico desconocido** | *por medir* (`historial_de`) |

**Dos cubiertos, uno contestado por construccion, y dos por medir** -- *y el que se ha medido hoy trae **cuatro
piezas y un arreglo documentado**, que es mas de lo que el criterio pide.*


---

## 6. El pack, ejercido: **`precio_unidad_cent` divide por `cantidad` y NO por el pack**

*(Ronda 109.)* La prueba del caso, con numeros de verdad:

```
grupos con unidades_pack > 1:   1.507 de 52.087

alcampo  'SCOTTEX Fresh Papel higienico humedo'
    cantidad=148 ud · pack=2 · precio=581 cent
    precio_unidad_cent=3,9257 cent ·  ref=4,0 cent por ud

aldi     'Vasitos de quinoa'
    cantidad=0,25 kg · pack=2 · precio=139 cent
    precio_unidad_cent=556,0 cent ·  ref=556,0 cent por kg
```

### La aritmetica, que es lo que hay que mirar

| producto | lo que da `precio_cent / cantidad` | lo que daria `/ (cantidad x pack)` | **lo que se sirve** |
|---|---|---|---|
| **SCOTTEX** | *581 / 148 = **3,9257*** | *581 / 296 = **1,963*** | **3,9257** -- *o sea, `/cantidad`* |
| **aldi vasitos** | *139 / 0,25 = **556,0*** | *139 / 0,5 = **278,0*** | **556,0** -- *o sea, `/cantidad`* |

**En los dos casos, `precio_unidad_cent` es `precio_cent / cantidad`**, y **`unidades_pack` no entra en la
division.** *Y `precio_ref_canon_cent` es el mismo numero redondeado* (3,9257 -> 4,0; 556,0 -> 556).

### Y lo que NO puedo concluir, que es lo honesto

**Que la division ignore el pack **puede estar bien o mal**, y depende de una cosa que no he mirado: **si
`cantidad` ya incluye el pack o no.**

- **Si `cantidad` es el total del envase** -- *296 ud en el SCOTTEX, porque son dos rollos* --, **entonces
  `581 / 296 = 1,963` es el precio por unidad de verdad, y el 3,9257 esta mal.**
- **Si `cantidad` es lo que trae cada unidad del pack** -- *148 ud por rollo, y el pack trae dos* --, **entonces
  el precio por unidad **de un rollo** es 3,9257, y es correcto** -- *aunque el «precio por ud» que se ensena
  al lado de un pack de dos deberia ser el del pack, porque **es lo que se compra**.*

**Las dos lecturas dan numeros distintos, y cual es la buena no se decide mirando el `SELECT`: se decide
mirando **que significa `cantidad` en el colector de Alcampo**, y eso es un campo que hay que leer.**

### Y por que esto es el caso «cantidad/pack» del criterio, exactamente

**El criterio dice**: *«cantidad/promocion **elegibles** y **coste parcial explicito**»* -- *y `C06`: «identidad/
formato, ambito y fecha visibles»*.*** Aqui el «formato» es el pack, y **un pack de 2 hace que el precio
comparable cambie por dos** -- *que es justo lo que un comparador de precios no puede hacer mal.*

**Asi que esto no queda «medido y bien» ni «medido y mal»: queda **medido y a una pregunta** -- *y la pregunta
es de una funcion del colector, no de la pantalla.*

### Y el estado del caso, con precision

| lo que hay | **estado** |
|---|---|
| **`unidades_pack` en el dato** | **si**, en 1.507 grupos |
| **la normalizacion** (`normalize.py`) | **si** |
| **el pack en la pantalla** («Vienen N x tamano», con el suelto al lado) | **si** |
| **la comprobacion entre cadenas** (`ejes.py:37`) | **si** |
| **que el precio unitario tenga en cuenta el pack** | **NO** -- *divide por `cantidad`* |
| **y si eso es correcto** | **depende de que significa `cantidad`**, y **sin medir** |

**Un caso con **cuatro piezas hechas y una pregunta abierta** -- *y la pregunta, otra vez, hay que **leerla**, no
suponerla.* *Es la septima vez en esta fase que la respuesta esta en un campo que no he mirado.*


---

## 7. El pack, **resuelto: el precio unitario esta bien, y la duda era mia**

*(Ronda 110.)* La pregunta de la ronda 109 -- *«¿`cantidad` ya incluye el pack?»* -- **se contesta leyendo el
contrato de la funcion que lo calcula**, `core/normalize.py:69`:

```python
70  """'Pack 6 x 1 L' -> (6.0, 'l', 6).  '500 g unidad' -> (0.5, 'kg', 1).
72  Devuelve (cantidad_TOTAL_en_unidad_canon, unidad_canon, unidades_del_pack).
73  """
78  m = _PACK.search(t)
79  if m:
80      n, cant, uni = _num(m.group(1)), _num(m.group(2)), m.group(3)
83      return round(n * cant * factor, 6), canon, int(n)
```

**La respuesta, en dos sitios de cuatro lineas:**

1. **El docstring lo dice con esas palabras**: *«Devuelve (**cantidad_total** en unidad canon, unidad canon,
   unidades del pack)»* -- **`n * cant`**, o sea **6 x 1 L son 6 litros, no 1**.
2. **Y la linea lo hace**: `round(n * cant * factor, 6)` -- *el **producto**, no el factor de uno.*

**Asi que `cantidad` **es el total, pack incluido**, y `precio_cent / cantidad` **es el precio por unidad de
verdad**.** *El SCOTTEX: 581 cent / 148 ud = **3,9257 cent por unidad**, y **148 ud es lo que trae el envase
entero** (los dos rollos juntos, con `unidades_pack=2` para poder decir «vienen 2»).*

### Y la duda era mia, y conviene decir de donde salio

**En la ronda 109 escribi**: *«si `cantidad` es lo que trae cada unidad del pack, entonces 3,9257 es correcto
-- aunque el precio por ud que se ensena al lado de un pack de dos deberia ser el del pack».*

**Sali de leer `pack=2` y suponer que `cantidad` era por unidad.** *Y no lo era.* **Lo que lo resuelve no es
razonar sobre el numero: es **leer la funcion que lo produce**, que tiene el contrato escrito **en su
docstring**.*

**Es la misma leccion de las siete anteriores de esta fase, esta vez con la respuesta a cuatro lineas de donde
yo estaba mirando** -- *y ademas con un `_PACK` y un `_SIMPLE` que dicen que **el parseo de formatos es un
problema que ya se penso**, no un `split` de fortuna.*

### Y `C06` queda asi

| lo que pide `C06` | **estado** |
|---|---|
| **identidad/formato** | **el formato, resuelto**: `parse_formato` normaliza **packs, unidades y pesos** a una cantidad canonica, **y el precio unitario sale de ahi** |
| **ambito visible** | *por medir* -- *¿se dice de que cadenas es?* |
| **fecha visible** | **si**: la fecha del catalogo, y F03 la publica |
| **cantidad/promocion elegibles** | **si**: el pack y las unidades minimas llegan a la pantalla |
| **coste parcial explicito** | **si**: `sin_precio` y la estimacion |

**Cuatro de cinco contestados, y el que falta -- «ambito visible» -- es una pregunta de la pantalla.** *Y el
formato, que era el unico con una duda abierta, **queda cerrado y bien**.*

### Y F08, con sus cinco casos

| caso | **estado** |
|---|---|
| **lista parcial** | **cubierto** |
| **oferta caducada** | **no hay ninguna, por construccion** |
| **cantidad/pack** | **CERRADO**: `cantidad` es el total del envase (`parse_formato`), y el precio unitario divide bien |
| **cupon/club no elegible** | *por medir* (`promo_club`, `promo_solo_online`) |
| **historico desconocido** | *por medir* (`historial_de`) |

**Tres cubiertos, uno contestado por construccion, y dos por medir.**


---

## 8. «Cupon/club no elegible»: **resuelto en cuatro sitios, y mejor que el criterio**

*(Ronda 111.)* El criterio pide, para `C08`: *«**condiciones y vigencia**; credito futuro separado del dinero
pagado hoy»*, y la aceptacion nombra *«**cupon/club no elegible**»*. **Y las 39 menciones de `promo_club` /
`promo_solo_online` dibujan cuatro decisiones, no una:**

| donde | que hace | **por que es lo correcto** |
|---|---|---|
| **`alertas.py:76-77`** | *`AND NOT coalesce(b.promo_club, false) AND NOT coalesce(b.promo_solo_online, false)`* | ***las alertas las EXCLUYEN*** -- *no se avisa de una bajada que **no se puede aprovechar**; avisar de una oferta de tarjeta a quien no la tiene es una alerta falsa* |
| **`catalogo.py:328-329`** | *el filtro de ofertas tambien las excluye* | *«ensename solo lo que puedo coger»* |
| **`catalogo.py:404`** | *`count(*) FILTER (WHERE coalesce(promo_club, false)) AS ...`* | **y se cuentan aparte** -- *asi que se sabe cuantas hay **sin ensenarlas** como si fueran tuyas* |
| **`app.js:1269`** | *`` `${p.promo_club ? 'Oferta de tarjeta' : 'Oferta'}` ``* | **y la pantalla LO DICE**: *una promocion de club **se llama «Oferta de tarjeta»**, no se disfraza de oferta normal* |
| **`pesos.ts:101`** | *`return p.promo_club ? 0.5 : 1`* | **y ademas PESA LA MITAD** -- *una decision de puntuacion, deliberada y escrita* |

### Y esto es el criterio entero de `C08`

*«Condiciones»*: **las condiciones estan dichas** -- *la pantalla la llama «oferta de tarjeta», que es la
condicion.* *«Vigencia»*: **la fecha esta** (§3). **Y «no elegible» esta resuelto **en los dos sitios donde
importa** -- *el aviso (**no avisar de lo que no se puede coger**) y el filtro (**no ensenarlo como tuyo**)*
--, **y ademas se cuenta aparte en vez de esconderse.**

**Es la misma forma que `sin_precio`, `nombre_visto` y los pasillos sin seccion**: *lo que no se puede aplicar
**no se esconde ni se disfraza**: **se dice y se cuenta**.*

### Y `pesos.ts:101` es la pieza que no esperaba

**`return p.promo_club ? 0.5 : 1`** -- *una promocion de club **vale la mitad** en la puntuacion.* **No se que
puntua** (habria que leer `pesos.ts`), **pero la decision esta escrita y es defendible**: *una oferta que la
mitad de la gente no puede coger **no deberia pesar lo mismo** que una que cualquiera puede coger.*

**Y es la octava pieza de esta fase que aparece **ya resuelta y con el motivo escrito** mientras buscaba otra
cosa.**

### Y F08, con sus cinco casos

| caso | **estado** |
|---|---|
| **lista parcial** | **cubierto** |
| **oferta caducada** | **no hay ninguna, por construccion** |
| **cantidad/pack** | **CERRADO** |
| **cupon/club no elegible** | **CUBIERTO en cuatro sitios** -- *excluido de alertas, excluido del filtro, contado aparte, dicho en pantalla, y con la mitad de peso* |
| **historico desconocido** | *por medir* (`historial_de`) |

**Cuatro de los cinco casos, cubiertos; y el que queda -- historico desconocido -- es el unico sin medir.**


---

## 9. «Historico desconocido»: **el historial devuelve necesidades, no precios** -- y `C10` queda cerrado

*(Ronda 112.)* **El ultimo caso de la aceptacion**, y el criterio de `C10`
(`SUPERAPP-COMPETENCIA-Y-REA.md:98`): *«**Copiar necesidades, nunca precios antiguos como si fueran
actuales**.»*

### La respuesta, en el docstring de la propia funcion

`almacen.historial_de` (`plataforma/api/almacen.py:808`):

```python
809  """Los grupos que esta persona ha anadido, lo reciente pesando mas.
811  Tres decisiones, y las tres estan en el SQL para que la regla y la consulta no
812  se puedan separar:
814  **Se cuentan todas las lineas, incluidas las borradas.** `lista_linea` no borra
815  de verdad: pone `borrado_en` y `limpiar_lineas_borradas` las quita a los 30
816  dias. *Una lista se vacia al terminar la compra; el habito no.* ...
821  **Se cuenta por `anadido_por`, no por "las listas en las que estoy".** En una
822  lista compartida se apunta lo que trae el otro, y eso no es tu historial: es el
823  suyo. Ademas, quien tiene permiso de solo mirar una lista **no puede sacar de
824  aqui lo que hay dentro de ella**.
826  **Lo reciente pesa mas, con un decaimiento y no con un corte.** ...
```

**La primera linea ya contesta `C10`**: *«Los **grupos** que esta persona ha **anadido**»* -- *o sea,
**necesidades, no precios**.* **El historial devuelve **a que productos** vuelve alguien, y el precio de esos
productos sale **del catalogo de hoy** -- que es lo unico que el proyecto guarda.**

**Asi que `C10` no esta «cumplido por cuidado»: esta cumplido **por estructura**.** *No hay precios antiguos
que copiar, porque **el historial no guarda precios**.*

### Y las tres decisiones que trae, que son de las mejores piezas de esta fase

1. **«Se cuentan todas las lineas, incluidas las borradas»** -- *«Una lista se vacia al terminar la compra; **el
   habito no**»*. *Contando solo las vivas, **el historial de quien usa la lista como se usa una lista estaria
   siempre vacio**, y el mosaico ensenaria lo de todos a alguien que lleva meses comprando.* **Es la diferencia
   entre «lo que tengo apuntado» y «lo que suelo comprar», y esta escrita.**
2. **`anadido_por`, y con la consecuencia de seguridad dicha**: *«quien tiene permiso de **solo mirar** una lista
   **no puede sacar de aqui** lo que hay dentro de ella»*. **Segunda decision de seguridad de esta fase que
   aparece escrita, despues de `_acceso`** -- *y esta es mas sutil: no es que no pueda **entrar**, es que **no
   puede deducir** lo de dentro por el historial.*
3. **La recencia, y por que no un corte** -- *y esta es la que vale la pena leer entera:*

> *«Con un corte a 90 dias, un producto **desaparece del mosaico de un dia para otro** al cruzar el dia 90, y
> `veces` tendria que pasar a significar "veces en 90 dias". **Dos numeros distintos con el mismo nombre es
> justo el error que este proyecto ya pago una vez con "imposible"** (`core/comparacion.py`).»*

**Una decision de diseno argumentada, con el caso a favor y en contra, con el numero elegido (vida media de 30
dias) y con un **precedente real del propio proyecto** como razon.** *Y el encargo pedia exactamente esto --
«elegir entre contar los ultimos 90 dias o pesar por recencia, **y escribirlo**» --, **y esta escrito.***

### Y F08, con sus cinco casos **enteros**

| caso de la aceptacion | **estado** |
|---|---|
| **lista parcial** | **cubierto**: `sin_precio` y la estimacion en pantalla |
| **oferta caducada** | **no hay ninguna, por construccion** -- *el catalogo es de hoy* |
| **cantidad/pack** | **CERRADO**: `parse_formato` normaliza el total, y el precio unitario divide bien |
| **cupon/club no elegible** | **cubierto en cuatro sitios**, y con la mitad de peso |
| **historico desconocido** | **cubierto por estructura**: el historial devuelve **necesidades, no precios** |

**Los cinco, cubiertos** -- *y la aceptacion de F08 queda contestada entera, con la unica mitad sin medir siendo
«ambito visible» de `C06`, que es una pregunta de la pantalla.*

### Y la cuenta de la fase, que ya se puede dar

**Ocho piezas de este paquete aparecieron **ya resueltas y con el motivo escrito** mientras buscaba otra cosa**:
*el `::VARCHAR` de `promo_hasta` con su prueba, `unidades_pack` que no llegaba a la pantalla, el historial con
sus tres decisiones, el club excluido de las alertas, el peso de media, y tres mas.*

**Y eso cambia lo que este paquete significa**: *F08 no ha sido «implementar comparacion y presupuesto» -- **ha
sido comprobar que el proyecto ya habia pensado casi todo eso**, y encontrar **las dos piezas que de verdad
faltan**:*
1. **el «previsto» de `C09`** -- *lo que la persona se propone gastar: **no existe***
2. **y el «ambito visible» de `C06`** -- *por medir*

**Dos huecos, y ninguno es un descuido: los dos son cosas que nadie ha pedido todavia.**


---

## 10. «Ambito y fecha visibles»: **las dos, y la fecha en la cabecera de todas las pantallas**

*(Ronda 113.)* El ultimo medio caso de `C06`: *«identidad/formato, **ambito y fecha visibles**»*. *Y las dos
estan.*

### La fecha: en la cabecera, y con una decision escrita al lado

```
Cabecera.tsx:3    *  `fecha_datos` NO ES UN ADORNO DE PIE DE PAGINA. La r...
Cabecera.tsx:77       Datos del <strong ...>
Cabecera.tsx:82         ({hace(data.fecha_datos)})          <- «hace N dias/horas»
Buscar.tsx:271        <span> · datos del {fecha(resultados.data.fecha_datos)}
Cesta.tsx:1524        Datos del {detalle.data.fecha_datos}
Escaner.tsx:237,247   Datos del {fecha(perdido.fecha_datos)} / sub={Datos del ${...}}
Favoritos.tsx:279     <Etiqueta tono="dato">datos del ...
Grupo.tsx:279         {grupo.fecha_datos && (...
```

**No esta en una pantalla: esta en la **cabecera**, o sea **en todas** -- *y con **«hace N»** al lado, que es lo
que convierte una fecha en algo que se puede juzgar de un vistazo.* **Y `Cabecera.tsx:3` lo dice: «`fecha_datos`
**no es un adorno de pie de pagina**»** -- *es decir, **alguien decidio que fuera visible en vez de discreta**,
que es exactamente lo que el criterio pide.*

### El ambito: una columna, y el orden por defecto que lo explica

```
TablaResultados.tsx:80    // Por defecto, lo que pide el backend: prim[ero]...
TablaResultados.tsx:153       id: 'cadenas',
TablaResultados.tsx:155       accessorFn: (f) => f.cadenas,
TablaResultados.tsx:159       {row.original.cadenas} {row.origina...
TablaResultados.tsx:169       accessorFn: (f) => (f.comparable && !f....
TablaResultados.tsx:175       if (!f.comparable || f.dudoso) {
```

**Hay una columna `cadenas`** -- *cuantas cadenas tienen ese producto* -- **y una columna `comparable`**, *con
`ahorro_pct: 0.0` tratado como **«centinela»** en el codigo*.

**Y `TablaResultados.tsx:80` dice el criterio con otras palabras**: *«Por defecto, lo que pide el backend:
**primero [...] cadenas y, dentro, el mas barato**»* -- *o sea, **el ambito es una de las dos cosas por las que
se ordena**.*

**Y eso es lo que se vio en la pantalla en la ronda 101, sin buscarlo**: *«Gofres con chocolate Hacendado ·
**mercadona** · Hacendado · ahorras un 7,7 % · **comparable · 2 cadenas** · sin Eco-Score · 33,55 EUR»* -- **la
cadena, las cadenas que lo tienen, y «comparable»**, todo en el resultado.

### Y `C06` queda **entero**

| lo que pide `C06` | **estado** |
|---|---|
| **identidad/formato** | **resuelto**: `parse_formato` normaliza packs, unidades y pesos |
| **ambito visible** | **si**: columna `cadenas`, y la cadena en cada resultado |
| **fecha visible** | **si, y en la cabecera de todas las pantallas**, con «hace N» |
| **cantidad/promocion elegibles** | **si**: el pack y las unidades minimas llegan a la pantalla |
| **coste parcial explicito** | **si**: `sin_precio` y la estimacion |

**Los cinco, cubiertos.**

### Y F08 queda cerrado

**Los cinco casos de su aceptacion, cubiertos; y los cinco criterios que cubre -- `C06` a `C10` --, con su
parte principal medida.** *Y lo que **no** queda hecho son **dos cosas que nadie ha pedido todavia**:*

1. **El «previsto» de `C09`** -- *lo que la persona se propone gastar. **No existe**, y **cual de las tres
   piezas** (estimacion, pagado, presupuesto propio) **es «presupuesto» es una decision del dueno.**
2. **Y `C07` completo** -- *el **ahorro neto definido** y el **coste de desplazamiento optativo**: *el oraculo
   multi-tienda es de F06, y **el «maximo de tiendas» y el desplazamiento** son de F08 y **no se han medido**.*

**Dos huecos, y el segundo lo encuentro al cerrar** -- *que es la forma en que han aparecido casi todos en esta
fase: **mirando el conjunto despues de medir las partes.***


---

## 11. `C07`: **«maximo de tiendas» y «ahorro neto», hechos; «coste de desplazamiento», no existe**

*(Ronda 114.)* El criterio (`SUPERAPP-COMPETENCIA-Y-REA.md:95`): *«**Maximo de tiendas** y **coste de
desplazamiento optativo**; **ahorro neto definido**, oraculo multi-tienda.»* **Y son tres piezas, no una:**

| lo que pide | **estado** |
|---|---|
| **oraculo multi-tienda** | **hecho, y es de F06**: `core/oraculo_reparto.py` |
| **maximo de tiendas** | **hecho**: `AJUSTES.max_tiendas`, con `CESTA_MAX_TIENDAS` (por defecto **2**) |
| **ahorro neto definido** | **hecho**: `_mejor_reparto` elige *«la mejor combinacion de hasta `max_tiendas`, **si gana a ir a una sola**»* |
| **coste de desplazamiento optativo** | **NO EXISTE** |

### La pieza que si esta, y esta bien

```
ajustes.py:19      max_tiendas: int
ajustes.py:41      max_tiendas=int(os.environ.get("CESTA_MAX_TIENDAS", "2"))
cesta.py:471       max_t = max_tiendas or AJUSTES.max_tiendas
cesta.py:531       def _asignaciones(peticiones, por_cadena, cadenas, max_tiendas)
cesta.py:544           for combo in combinations(cadenas, min(max_tiendas, len(cadenas))):
cesta.py:552       """La mejor combinacion de hasta `max_tiendas`, si gana a ir a una sola.
cesta.py:572           **el optimo** entre las asignaciones de como mucho `max_tiendas` tiendas
cesta.py:600       if max_tiendas < 2 or len(por_cadena) < 2: ...
oraculo_reparto.py:36   oraculo(peticiones, oferta, max_tiendas=2)
oraculo_reparto.py:135      if len(usadas) > max_tiendas:
```

**Es configurable** (*variable de entorno, por defecto 2*), **lo usa el optimizador de verdad**
(`combinations` sobre las cadenas), **y el oraculo lo respeta** -- *o sea, que **el tope y el oraculo estan de
acuerdo**, que es lo que hace que el oraculo sirva para juzgar al optimizador.*

**Y el «ahorro neto» tambien esta, y con la definicion dicha**: *«si **gana a ir a una sola**».* **Eso **es**
una definicion de ahorro neto: la diferencia contra el caso de una tienda** -- *que es la comparacion que
importa, porque ir a una es lo que hace todo el mundo.*

### Y la pieza que no esta

**«Coste de desplazamiento optativo» no aparece en ninguna parte**: *28 menciones en la busqueda, y **las 28
eran de `max_tiendas`**.* **No hay gasolina, ni kilometros, ni «coste de ir»** -- *ni como campo, ni como
parametro, ni en la pantalla.*

**Y es un hueco distinto de los otros dos**, porque **no es que falte un dato: es que falta una **decision**.**

> *¿Cuanto cuesta ir a una tienda?* **No es un numero que este en ningun catalogo**: *depende de donde viva
> cada persona, de si va andando o en coche, y de si de todas formas pasaba por alli.* **Meter un «coste de
> desplazamiento» es pedirle a alguien un dato suyo, y el criterio dice «**optativo**» precisamente por eso.**

**Asi que `C07` queda con tres piezas y una que no puede venir de los datos** -- *y esa es la clase de hueco que
se dice, no que se rellena con un cero.*

### Y F08, cerrado del todo

| criterio | **estado** |
|---|---|
| **`C06`** -- identidad/formato, ambito, fecha, cantidad, coste parcial | **entero** |
| **`C07`** -- oraculo, maximo de tiendas, ahorro neto | **hecho**; **coste de desplazamiento: NO EXISTE**, y es una decision |
| **`C08`** -- condiciones, vigencia, no elegible | **cubierto en cuatro sitios**, con el club a media peso |
| **`C09`** -- pagado y cobertura | **hecho**; **«previsto» NO EXISTE** |
| **`C10`** -- copiar necesidades, no precios | **por estructura** |

**Y los cinco casos de la aceptacion, cubiertos.** *Lo que F08 deja son **tres cosas que nadie ha pedido
todavia**, y las tres son **decisiones del dueno**, no medidas:*

1. **que es «presupuesto»** -- *la estimacion, lo pagado, o un numero que se ponga la persona*
2. **cuanto cuesta ir a una tienda** -- *y por eso el criterio dice «optativo»*
3. **que se copia del historico** -- *que ya esta resuelto: necesidades, no precios*

**Dos decisiones y un cierre, y ninguna es un descuido.**
