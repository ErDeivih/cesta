# F01 · Identidad estable: el consumidor que quedaba ligado al ordinal

Estado: **encontrado y localizado; sin arreglar**. Fecha: 13 de octubre de 2026.
Origen: hallazgo #9 de la revisión (*«Riesgo de identidad estable»*) y la mitad pendiente de F01.

> *«Tablero describe grupos ordinales renumerados y migración a producto estable; informe da G10 cerrado
> por lectura. → **Prueba lista/favorito/receta sobreviviendo a reordenación** y separación de grupos.
> **Resolver cualquier consumidor aún ligado a ordinal.**»*

---

## 1. La mitad «resolver consumidores»: **encontrada, y hay uno**

**Primero se comprobó que no hubiera consumidores _de código_**, con `git grep`: las tres menciones del
ordinal del grupo son **comentarios** (`catalogo.py:777`, `cesta.py:908`, `main.py:671`), y dos de ellos
dicen justo lo que el hallazgo avisa. *Ningún código trata el ordinal como identidad.*

**Pero el esquema sí distingue, y ahí está el hallazgo:**

```
plataforma/sql/001_esquema.sql:98    linea:    grupo_id bigint,  producto_id text
plataforma/sql/001_esquema.sql:109   CONSTRAINT linea_con_destino  CHECK (grupo_id IS NOT NULL OR producto_id IS NOT NULL)
plataforma/sql/001_esquema.sql:126   favorito: grupo_id bigint,  producto_id text
plataforma/sql/001_esquema.sql:129   CONSTRAINT favorito_con_destino
plataforma/sql/001_esquema.sql:136   alerta:
plataforma/sql/001_esquema.sql:139       grupo_id  bigint NOT NULL      <- SOLO el ordinal
```

**`linea` y `favorito` guardan las dos referencias** -- *y por eso pueden apuntar a un producto estable
(la migración 015 y el trabajo de F01 van por ahí)* --. **`alerta` guarda `grupo_id` y nada más, y encima
`NOT NULL`.**

## 2. Y por qué eso importa, medido

**`grupo_id` es un ordinal que el emparejador renumera en cada pasada.** *No es una interpretación: lo dice
el propio código, en tres sitios, y uno de ellos lo explica como advertencia:*

```
plataforma/api/main.py:671    # `grupo_id` es un ordinal que el emparejador renumera en cada pasada, asi...
plataforma/api/cesta.py:908   # ordinal que se renumera en cada pasada, asi que esta linea puede e...
plataforma/api/catalogo.py:777 **Esto es el sintoma de que `grupo_id` es un ordinal, no una identidad...
```

**Así que una alerta creada para «el grupo 5000» puede, tras una reordenación, estar vigilando otro
producto.** *Y como las alertas son de bajada de precio, el fallo es silencioso y del peor tipo:* **la
persona recibe un aviso de un producto que no pidió, o deja de recibirlo del que sí, y nada se lo dice.**

**`favorito` y `linea` no tienen ese problema porque tienen `producto_id`.** *`alerta` no.*

## 3. Lo que NO se ha hecho

1. **El arreglo.** *La dirección es la misma que ya se siguió con `linea` y `favorito`: dar a `alerta` una
   referencia al producto estable, con su `CHECK` de «una u otra».* **No se ha escrito la migración.**
2. **La prueba** de lista/favorito/receta sobreviviendo a una reordenación, que es la otra mitad del
   hallazgo. *Y ojo: **la lista y el favorito sí pueden pasar esa prueba hoy** -- tienen `producto_id` --,
   pero **no se ha demostrado**, y **la alerta no podría**.*
3. **Y una pregunta que hay que contestar antes de tocar `alerta`**: *una alerta «de este grupo» ¿es
   legítimamente del grupo -- «vigila este producto, se llame como se llame» -- o siempre debería ser de un
   producto?* **De la respuesta depende si `alerta` necesita las dos columnas o sólo cambiar de una a
   otra.** *No la contesto yo.*

## 4. Lo que se puede afirmar hoy

**El hallazgo #9 tenía razón, y su mitad «resolver consumidores» da un caso concreto**: *`alerta` está
ligada al ordinal, `linea` y `favorito` no, y el ordinal se renumera.* **No es una hipótesis del tablero:
está en el esquema y lo avisa el propio código.**

*Y es el único caso de los nueve hallazgos de F00 que ha resultado ser **un defecto localizado y no
arreglado**, en vez de un cierre insuficiente ya cubierto.*


---

## 5. Y la pregunta, contestada -- leyendo el codigo que evalua las alertas

*(Ronda 41.)* Deje abierto: *«una alerta "de este grupo" ¿es legitimamente del grupo -- "vigila este
producto, se llame como se llame" -- o siempre deberia ser de un producto?»*. **El codigo lo contesta.**

```
alertas.py:57    def _mejor_de_cada_grupo(grupos)   -> «el mejor de cada grupo»
alertas.py:84    row_number() OVER (PARTITION BY grupo_id ...)   -> el mas barato del grupo
alertas.py:209   grupos = sorted({int(a["grupo_id"]) for a in alertas})
alertas.py:212   claves = {(mejores[...]["cadena"], mejores[...]["id_fuente"]) ...}
```

**La alerta es, legitimamente, del grupo**: *lo que se vigila es **la mejor oferta de ese producto**, mire
en la cadena que mire, y el grupo es exactamente eso.* **Asi que la semantica esta bien y no hay que
cambiarla.**

**Y ahi esta el problema, con precision**: *la **intencion** de la alerta es estable -- «este producto» --,
pero su **clave** (`grupo_id`) es un ordinal que se renombra en cada pasada.* **La alerta quiere decir una
cosa estable y la guarda con un nombre inestable.**

### Y la clave que falta no es `producto_id`

**`linea` y `favorito` resuelven su caso con `producto_id`** -- que segun el propio esquema es *«solo si se
fijo una cadena»*. *Pero una alerta de grupo **no es de una cadena**: es de un producto en cualquiera.*
**Asi que copiar `producto_id` seria cambiarle la semantica a la alerta para arreglar el almacenamiento.**

**La identidad estable que ya existe en el proyecto es el `ean`** -- *hay endpoint propio (`/api/ean/{codigo}`)
y el matching trabaja con el*. **Y es la que corresponde**: *el `ean` identifica el producto con
independencia de en que grupo haya caido y de en que cadena se venda.*

### Lo que habria que hacer, entonces, y por que no lo hago ahora

**La direccion**: *guardar en `alerta` la identidad estable del producto vigilado -- el `ean` --, y resolver
el grupo desde ahi en cada evaluacion*, con una migracion que **rellene** lo existente desde el grupo actual
y **no borre nada**.

**Y no se ha escrito**, por dos razones que conviene decir:

1. **Rellenar hacia atras exige decidir que `ean` es «el» del grupo cuando el grupo tiene varios** -- *y eso
   no es un detalle de migracion: es la misma pregunta de identidad que F01 tiene abierta, y contestarla
   mal escribiria un dato estable **equivocado**, que es peor que uno inestable.*
2. **Y no se ha comprobado cuantas alertas existen hoy.** *Si no hay ninguna, la migracion es trivial; si
   hay, hay datos de personas que decidir.* **No lo he medido, y es un `SELECT` de una linea.**

**Asi que el defecto queda localizado, entendido y con direccion** -- *y con el paso siguiente que es medir
cuantas alertas hay antes de tocar nada.*
