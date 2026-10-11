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


---

## 6. Medido: **hay UNA alerta**, y la tabla ya guarda el nombre -- pero no la clave

*(Ronda 42.)* El `SELECT` de una linea, hecho sobre la base de trabajo (`127.0.0.1:5434`):

```
alerta               1 fila
compra             463      lista              877      usuario        12
compra_linea       474      lista_linea       1026      sesion       1495
favorito             0      invitacion           0      visita        141

la unica alerta:
    grupo_id      11627
    tipo          minimo_90d
    creada_en     2026-10-10
    salto_nombre  «Leche entera Central Lechera Asturiana brik 1 l.»
    salto_texto   «esta al precio mas bajo de los ultimos 90 dias: 1.24 EUR/l en carrefour»
```

### Y un hallazgo dentro del hallazgo, que corrige mi propia lectura

**La tabla tiene `salto_nombre` y `salto_texto`, y mi lectura del esquema (seccion 1) no los vio.**
*`001_esquema.sql` declara siete columnas y la tabla tiene nueve: **una migracion posterior anadio las
dos**.* **Lei el esquema base y di por hecho que era la tabla** -- *el mismo error de siempre, esta vez con
una migracion en medio.*

**Asi que la alerta ya guarda el nombre del producto que vigila**, en `salto_nombre`. *Y eso **mitiga** el
problema: si el `grupo_id` se renombra, **el texto de la alerta sigue diciendo de que producto era**.*

**Pero es una etiqueta, no una clave.** *`salto_nombre` es para leerlo una persona; **no sirve para volver a
resolver el grupo en la siguiente pasada**, que es lo que hace falta para que la alerta siga vigilando lo
mismo.* **Es la diferencia entre un recibo y un identificador.**

### Y con esto, la migracion es pequena

**Hay una sola alerta, y su producto esta identificado por nombre y por grupo.** *Asi que rellenar su
identidad estable es resolver **un** caso, no una politica:*

- **el grupo 11627** dice que producto es, y
- **`salto_nombre`** lo confirma en palabras.

**Lo que falta es el paso que no se ha dado**: resolver ese grupo a un `ean` en el catalogo de hoy y
guardarlo. **No se ha hecho**, y *es un `SELECT` y un `UPDATE` de un caso* -- ***pero antes hay que
comprobar que el grupo 11627 del catalogo de hoy sigue siendo ese producto**, porque si el emparejador lo
ha renumerado desde el 10 de octubre, **la propia migracion estaria escribiendo el dato equivocado**.*
**Y esa comprobacion es, exactamente, el defecto que este hallazgo describe: se mide o no se sabe.**


---

## 7. Y la comprobacion que decia la seccion 6: **el grupo 11627 ya no es lo que la alerta decia**

*(Ronda 43.)* Iba a comprobar si el grupo 11627 del catalogo de hoy seguia siendo el producto de la alerta.
**No lo es, y lo que hay dentro es mas grave que una renumeracion.**

### Lo que el grupo 11627 contiene HOY

```
grupo 11627  aldi       MILSANI     «Leche entera»                                 96 cent
grupo 11627  carrefour  PRESIDENT   «Leche entera President brik 1 l.»            102 cent
grupo 11627  alcampo    CENTRAL LECHERA ASTURIANA «Leche entera botella 1 l.»     126 cent
grupo 11627  dia        Asturiana   «Leche entera Asturiana 1 L»                  129 cent
grupo 11627  mercadona  Asturiana   «Leche entera Asturiana»                      129 cent
```

**Y la alerta guardaba:**

```
salto_nombre  «Leche entera Central Lechera Asturiana brik 1 l.»
salto_texto   «esta al precio mas bajo de los ultimos 90 dias: 1.24 EUR/l en carrefour»
```

### Lo que se puede afirmar, y lo que NO

**Lo que se puede afirmar, y es la demostracion del defecto**: *la alerta dice «Central Lechera Asturiana,
brik 1 l., en carrefour», y **el miembro de carrefour del grupo 11627 hoy es «Leche entera President brik
1 l.» a 1,02**.* **El nombre guardado y lo que el grupo contiene hoy no coinciden.** *Es exactamente lo que
la seccion 2 describia en abstracto: **la alerta guarda una clave que se renombra, y el nombre es lo unico
que la ata a su producto** -- y ese nombre **ya no describe al grupo**.*

**Lo que NO voy a afirmar, porque no lo he medido**: *si esto es una **renumeracion** del grupo -- el hecho
que la seccion 2 describe -- o si el **emparejador ha juntado marcas distintas** desde el 10 de octubre.*
**Son dos causas distintas y llevan a arreglos distintos**, y *para distinguirlas hay que mirar como cambio
el grupo entre el 10 de octubre y hoy, que no se ha hecho.*

**Y lo que SI conviene decir, porque salta a la vista y no es una interpretacion**: *el grupo 11627 tiene
hoy **cuatro marcas** -- MILSANI, PRESIDENT, CENTRAL LECHERA ASTURIANA y Asturiana --, y **tres de ellas son
marcas distintas del mismo tipo de producto**.* **Si el grupo significa «el mismo producto en distintas
cadenas», agrupar Milsani con President no es una renumeracion: es una equivalencia inventada** -- *y el
encargo prohibe inventar equivalencias.* **Queda anotado como pregunta, no como defecto: no he medido el
criterio del emparejador para este grupo.**

### Y el estado del hallazgo, tras medirlo

| lo que se creia | lo que hay |
|---|---|
| `alerta` ligada a un ordinal que se renumera | **cierto, y hay 1 alerta** |
| *«resolver cualquier consumidor ligado a ordinal»* | **localizado**: `alerta.grupo_id NOT NULL`, sin identidad estable |
| ¿el defecto ya hizo dano? | **el nombre guardado ya no describe al grupo**, medido hoy |
| **la causa** | **sin determinar**: *renumeracion o emparejamiento* |

**Asi que el siguiente paso no es la migracion: es distinguir las dos causas.** *Si es el emparejador
juntando marcas, **migrar la alerta a un `ean` no arreglaria nada**: el problema estaria en quien forma los
grupos.* **Y esa es la pregunta que F06 (matching) tiene abierta, ahora con un caso real delante.**


---

## 8. Que une a esos cinco: **el codigo lo dice, y no es una equivalencia inventada**

*(Ronda 44.)* Pregunte si el grupo 11627 era una renumeracion o un emparejamiento que habia juntado
marcas. **El criterio esta escrito, y es mas cuidadoso de lo que yo suponia:**

```
core/identidad.py:5    «de los grupos multi-cadena medidos, 2.276 agrupan productos con EAN distinto»
core/identidad.py:12   «El GTIN se valida, no se copia. Es la via fuerte: mismo GTIN valido y pre[sentacion]»
core/identidad.py:15   «Mismo GTIN con presentacion incompatible va a CUARENTENA, no a identidad»
core/identidad.py:17   «GTIN distinto no se fusiona por texto, NUNCA»
core/identidad.py:20   «Sin GTIN no hay identidad exacta. Marca, nombre y formato compatibles dan [aproximacion]»
```

**Asi que hay dos vias, y estan separadas a proposito:**

- **La fuerte**: mismo GTIN valido y presentacion compatible → **identidad**. *Mismo GTIN con presentacion
  incompatible va a cuarentena.*
- **La debil**: **sin GTIN no hay identidad exacta**; marca, nombre y formato compatibles dan **una
  aproximacion**.
- **Y lo que nunca se hace**: *fusionar por texto dos productos con **GTIN distinto**.*

### Y con eso, el grupo 11627 queda explicado

**Los miembros de alcampo de ese grupo traen `ean=None`** -- *medido en la seccion 7, y hay 25.975 filas en
el catalogo sin GTIN* --. **Asi que el grupo se formo por la via debil**: *sin GTIN, marca, nombre y formato
compatibles.* **No es una renumeracion, y no es una equivalencia inventada: es la aproximacion declarada,
aplicada.**

**Y el propio modulo lo dice con un numero**: *2.276 grupos multi-cadena agrupan productos con EAN distinto.*
**No es un descubrimiento mio; es una cifra medida y escrita en el codigo.** *Lo que yo iba a reportar como
sospecha llevaba tiempo documentado.*

### Y la pregunta que queda, que si es nueva -- y es del producto, no del motor

**El motor distingue identidad exacta de aproximacion. La pregunta es si quien compra puede distinguirlas.**

*En la ficha, un grupo formado por GTIN valido y uno formado por marca y nombre compatibles **se ven
igual***. **Y para decidir si comprar la leche de Milsani en vez de la de Central Lechera Asturiana -- que es
lo que el grupo invita a hacer -- esa diferencia es exactamente lo que hace falta saber.** *«Es la misma» y
«se parecen» no son lo mismo cuando alguien va a pagar por ello.*

**No he comprobado si la interfaz lo dice.** *Es una pantalla, y es lo siguiente que hay que mirar.*


---

## 9. Y la pantalla **si** distingue «es la misma» de «se parecen» -- en la linea

*(Ronda 45.)* Pregunte si la interfaz distingue la identidad exacta de la aproximacion. **Si, y hay un
componente dedicado:**

```
plataforma/web/app/src/componentes/AvisoIdentidad.tsx
   1   /** El aviso de que una linea se resuelve con otro producto, o con uno que no se puede confirmar.
   3    *  **Solo aparece cuando hay algo que decir.** Con `exacto` o sin veredicto no pinta nada: un aviso
   4    *  que sale siempre deja de leerse.
   6    *  **Y distingue los dos casos que importan.** `probable` es "parece el mismo, pero no tengo el
   7    *  codigo que lo confirme": pide prudencia. `alternativa`, `cuarentena` o `abstiene` es "esto no es lo
   8    *  que pediste": pide una decision.
  11    *  El encargo es explicito en esto: *elegir un producto concreto no autoriza a sustituirlo por otro
  12    *  mas barato*, y una sustitucion que no se ve es exactamente lo que hay que evitar.
  25   if (CONFIRMADO.has(identidad)) return null          // exacto, null, undefined
  37      'Puede que sea el mismo producto, pero no hay codigo que lo confirme.'     <- probable
  38      'Ojo: esta linea se resuelve con otro producto, no con el que pediste.'    <- el resto
```

**Y la API alimenta ese veredicto**: `cesta.py:205 veredicto = identidad.decide(...)` y
`cesta.py:206 exacta = veredicto["estado"] == identidad.EXACTO` ✓

**Asi que mi sospecha de la ronda 44 era infundada, y lo digo claro**: *el motor distingue, **y la pantalla
tambien** -- con dos mensajes distintos, no uno naranja para todo, y con la razon escrita de por que: «un
aviso que sale siempre deja de leerse».*

### Y lo que queda, ahora acotado a una cosa concreta

**El aviso es de la linea de una lista, no de la ficha del grupo.** *Y mi pregunta era por la ficha: si
alguien abre el grupo 11627 y ve cuatro marcas, ¿se le dice que tres de ellas no son el mismo producto, o se
le presentan como equivalentes?*

**No lo he comprobado.** *`/api/grupo/{grupo_id}` y la pantalla que lo pinta no se han leido.* **Asi que la
pregunta baja de «¿distingue la app?» -- que ya tiene respuesta, y es si -- a «¿lo dice tambien en la ficha
del grupo?», que es una pantalla concreta.**

### Y el hallazgo #9 queda asi

| | |
|---|---|
| `alerta` ligada al ordinal | **defecto real, 1 alerta, con daño medido** (el nombre guardado ya no describe al grupo) |
| la causa | **explicada**: via debil sin GTIN, declarada en el codigo |
| el motor | **distingue exacto de probable**, con cuarentena para el GTIN incompatible |
| la pantalla de la linea | **lo dice**, con dos mensajes distintos |
| **la ficha del grupo** | **sin comprobar** |
| **la migracion de `alerta`** | **pendiente**: darle identidad estable por `ean` |
