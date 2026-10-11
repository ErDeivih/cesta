# F05 · La cobertura de fichas, medida

Estado: **medido; sin empezar el trabajo**. Fecha: 13 de octubre de 2026.
Origen del hallazgo: revisión previa de fase 2, tabla §3, fila *«Fichas sin ejecución suficiente»*.

> *«Informe anterior registra 79.887 sin ficha y cinco cadenas sin cobertura. → **Medir situación actual
> por campo/cadena, integrar ejecución real, parser y presupuesto**; **no llamar toda ausencia
> "limitación de fuente"**.»*

---

## 1. Lo primero que pide el hallazgo: medir

**El instrumento ya existe y no había que escribir nada**: `core/inventario.py` -- *«cola de fichas: qué
sabemos de cada producto, cuándo lo miramos y cuándo toca volver»* --, con su `resumen()`.

```
data/inventario.sqlite

    alcampo         pendiente 43.603
    carrefour       pendiente 17.283
    dia             pendiente  6.292
    lidl            correcto     28   ·   pendiente 5.026
    mercadona       pendiente  4.477
    aldi            pendiente  3.206
    ───────────────────────────────────────
    TOTAL           pendiente 79.887  ·  correcto 28
```

**79.887 pendientes y 28 correctas.** *El número coincide exactamente con el que citaba la revisión, así
que no se ha movido: la cola está montada y **no se ha procesado**.*

## 2. Y lo que eso significa, dicho sin adorno

**La ausencia de fichas no es una limitación de fuente.** *Es trabajo sin ejecutar: hay 79.887 productos
en cola, esperando, y **28 hechas**.*

**Por eso el hallazgo insiste en esa frase** -- *«no llamar toda ausencia "limitación de fuente"»* --:
*una ficha que nunca se pidió y una ficha que la tienda no publica se ven igual en un porcentaje de
cobertura, y son dos cosas distintas: una se arregla ejecutando, la otra no.* **El 99,96 % de esta cola
está en el primer caso.**

**Y hay una consecuencia práctica**: *mientras la cola no se procese, cualquier cifra de cobertura de
fichas que se publique mide **cuánto se ha ejecutado**, no **cuánto se puede saber**. *Llamarla
«cobertura» sin decirlo es el mismo error que el encargo prohíbe en otras formas.*

## 3. Lo que hay montado, y lo que falta

**Montado** --medido, no supuesto--:

- **La cola** (`core/inventario.py`, SQLite): estados, *lease* con vencimiento, hash, alta idempotente, y
  `resumen()`. *Con sus pruebas.*
- **El alta desde bronze**: `enganche()` -- *«S02: inventario de 74.861 fichas desde bronze en 75,7 s»*,
  medido y documentado.
- **El informe de cobertura por fuente** (`docs/`), *con deuda de cola*.
- **Y `lidl` tiene 28 `correcto`**, así que **el camino completo -- pedir, parsear, guardar y marcar --
  funciona al menos una vez**.

**Lo que falta**, y es lo que el hallazgo pide:

1. **Ejecutar la cola de verdad** -- *79.887 fichas, con presupuesto y ritmo, y sin que el WAF lo pare*.
   *Es la parte grande, y no se ha hecho.*
2. **Medir por campo y por cadena**, no sólo por estado: *cuántos productos tienen kcal, cuántos
   ingredientes, cuántos Nutri-Score -- **y separar «la tienda no lo publica» de «no lo hemos pedido
   todavía»**.* **Sin esa separación, la cifra de cobertura miente por omisión.**
3. **El parser**, con su banco de pruebas.
4. **Y el presupuesto**: cuántas peticiones, a qué ritmo, y qué se hace cuando una cadena bloquea.

## 4. Lo que NO se ha hecho en esta ronda, y por qué

**Sólo se ha medido.** *F05 es un paquete grande -- la ejecución de 79.887 fichas es un trabajo de
operación, con red, WAF y presupuesto --, y empezarlo sin poder verificarlo habría dejado trabajo a
medias y una cifra sin comprobar.*

**Y medir era, literalmente, lo primero que el hallazgo pide.** *Ahora se sabe qué hay y qué no: **una
cola de 79.887 esperando y 28 hechas**.*


---

## 5. Y al ir a ejecutarla, el hallazgo de verdad: **hay ejecutor para una cadena de seis**

*(Ronda 26.)* Iba a ejecutar la cola de `aldi` con presupuesto acotado. **No se puede: para `aldi` no hay
nada que ejecutar.** Medido:

```
projects/cesta/fichas_lidl.py:72     inventario.tomar(con, limite, fuentes=["lidl"], ahora=ahora)
projects/cesta/fichas_lidl.py:28     from projects.cesta import ficha_lidl
projects/cesta/fichas_lidl.py:30     PARSER_VERSION = "lidl-jsonld-2"

modulos que piden una ficha, por cadena:
   banco_de_pares.py    alcampo, aldi, dia     <- no es un ejecutor de fichas
   mide_nutricion.py    lidl
```

**Hay un solo descargador y un solo parser, y son de Lidl.** *No hay `ficha_alcampo`, ni `ficha_aldi`, ni
`ficha_dia`, ni `ficha_carrefour`, ni `ficha_mercadona`.*

**Y eso explica, sin dejar nada al azar, el numero de la seccion 1**: de 79.887 pendientes, **las 28
`correcto` son todas de Lidl** -- *la unica cadena con ejecutor es la unica con fichas.*

### Lo que corrijo de lo que yo mismo escribi

Dije: *«la ausencia no es una limitacion de fuente: **es trabajo sin ejecutar**»*. **Es verdad a medias, y
la mitad que falta importa:**

- Para **Lidl**: hay ejecutor, y **28 de 5.054**. *Ahi si es trabajo sin ejecutar.*
- Para **las otras cinco**: **no hay con que ejecutarlo.** *No es trabajo pendiente de una pasada: es
  codigo que no existe.* **Llamarlo «sin ejecutar» hacia parecer que bastaba con lanzarlo.**

**Y la distincion que F05 pide -- «no llamar toda ausencia limitacion de fuente» -- ya esta hecha, campo a
campo, para Lidl**, en el propio comentario del ejecutor:

> *«**Y lo que este hash NO puede vigilar, medido.** El bloque `@type=Product` de Lidl trae nueve [campos]
> [...] Asi que no hay campos de contenido que hashear: **no es un parser incompleto, es una fuente que no
> los da**. Para tenerlos hay que **parsear el HTML** de la ficha o ir a **fuente** [externa].»*

*Es exactamente la frase del hallazgo, aplicada y con evidencia.* **Lo que falta es hacerla para las otras
cinco.**

### El estado de F05, entonces, es este

| pieza | estado |
|---|---|
| La cola (estados, *lease*, hash, revision, resumen) | **hecha y probada** |
| El alta desde bronze | **hecha** (74.861 fichas en 75,7 s, medido) |
| El presupuesto y el ritmo | **hechos** (`--limite`, `RITMO`, y dice cuantos dias faltan) |
| **Un descargador y un parser** | **solo de Lidl** |
| **Las otras cinco cadenas** | **no tienen nada** |
| La distincion «no lo publica» / «no lo hemos pedido» | **hecha para Lidl**; para las demas, **todo es «no lo hemos pedido»** |

**Y por eso la accion siguiente no es «lanzar una pasada»**: es **escribir el descargador y el parser de
una segunda cadena** -- *`aldi`, que tiene 3.206 pendientes y es la mas pequena --, con su `PARSER_VERSION`
y su prueba sin red (`fetch` es inyectable, asi que se puede probar sin pedir nada).*


---

## 6. Y para Aldi la respuesta esta en el crudo que **ya esta en disco**

*(Ronda 27.)* Iba a escribir `ficha_aldi.py`. **Antes de escribirlo mire que hay**, y el crudo lo
respondio **sin una sola peticion**.

`projects/cesta/collectors/aldi.py:74` -- *«sitemap oficial de productos + **API de producto por
lotes**»* -- llama a `{BASE}/api/product/pds/{ids}?scope=...`, **guarda la respuesta entera en crudo**
(`save_raw(FUENTE, f"pds-{lote[0]}", body)`) **y la reutiliza**. *Asi que la respuesta de Aldi esta en
`data/raw/fuente=aldi/`, y se puede leer sin pedir nada.*

**Los 18 campos que trae, medidos:**

```
assets  brandName  categoryIDs  currentPrice  isAvailable  isComingSoon  isFreezing  isRecall
longDescription  longDescriptionFormatted  mainCategoryID  metaDescription  metaTitle
name  objectID  productReferences  productSlug  salesUnit
```

**Ninguno es nutricion. Ni kcal, ni ingredientes, ni alergenos, ni Nutri-Score.**

### Lo que eso significa, y es exactamente la distincion que F05 pide

**Para Aldi NO es «no lo hemos pedido».** *El colector pide, a diario, por lotes, y la respuesta esta en
disco.* **Es «la fuente no lo publica» -- en la API que se usa.**

**Y la salida es la misma que el ejecutor de Lidl ya documenta para Lidl**: *«no es un parser incompleto,
es una fuente que no los da. Para tenerlos hay que **parsear el HTML** de la ficha o ir a **fuente**
[externa]».*

### Y otra vez corrige la accion siguiente

**Ayer escribi que habia que «escribir el descargador y el parser de una segunda cadena (`aldi`)».**
*Medido, eso habria sido escribir un descargador para una API que **no trae nutricion**: trabajo que no
resuelve el problema.*

**Lo que hay que decidir primero es donde vive la nutricion de Aldi** -- la pagina HTML del producto, o
una fuente externa --, y **eso es una decision con evidencia, no un modulo que se escribe por inercia.**
*Y la misma pregunta hay que contestarla para alcampo, carrefour, dia y mercadona antes de escribir
ninguno.*

**Es la cuarta vez en esta fase que medir antes de escribir cambia el trabajo que iba a hacer.**


---

## 7. El metodo sirve, pero **no basta con 40 ficheros** -- y el escaneo por palabras engania

*(Ronda 28.)* Aplique el mismo metodo a las otras cuatro cadenas. **Y hay que separar lo que quedo
probado de lo que solo es una pista.**

### Lo que se hizo, y lo que da

**Primero, un escaneo por palabras** (`nutri`, `kcal`, `grasa`, `protein`, `ingred`, `alerg`...) sobre los
crudos de hoy:

```
alcampo     25/60 ficheros con algo de nutricion
aldi        25/60
carrefour   44/60
dia         60/60
mercadona   13/60
```

**Y ese escaneo NO vale como prueba.** *Lo demuestra Aldi: sale **25/60 con «grasa»**, cuando en la ronda
27 quedo medido, **por claves**, que sus 18 campos no traen nutricion.* **La palabra estaba en el texto
-- el nombre o la descripcion --, no en un campo.** *Un escaneo de palabras dice donde mirar, no que
hay.*

**Segundo, la comprobacion por claves** -- la que si vale --, sobre los 40 primeros crudos de `dia`:
**ninguna clave de nutricion.** *Asi que el 60/60 de dia tambien eran menciones en texto.*

### Lo que NO se puede concluir, y no lo concluyo

**Que las cadenas no publiquen nutricion en ningun sitio.** *40 ficheros de una cadena que no he
caracterizado no son una muestra: el crudo de una cadena trae **varias clases de captura** -- sitemaps,
listados de categoria, paginas de producto --, y los 40 primeros pueden ser todos listados.*

**Para contestarlo hace falta saber cual de esos ficheros es una ficha**, y eso no lo he medido. *Decir
«ninguna cadena publica nutricion» con esto seria exactamente el error que el encargo prohibe: **afirmar
una ausencia sin haber mirado donde toca**.*

### Lo que si queda establecido

| cadena | que se midio | como |
|---|---|---|
| **aldi** | su API de producto, **18 claves, ninguna de nutricion** | por claves, sobre un producto entero -- **riguroso** |
| **dia** | **ninguna clave** de nutricion en los 40 primeros crudos | por claves -- *muestra sin caracterizar* |
| alcampo, carrefour, mercadona | *solo el escaneo por palabras* | **no vale** |
| **el escaneo por palabras sobreestima** | *probado con Aldi* | comparacion de los dos metodos |

### Y la accion siguiente, corregida otra vez

**No es «escribir un descargador» ni «decidir de donde sale la nutricion»**: es **saber cual de los
crudos de cada cadena es una ficha.** *Eso es medible y barato -- mirar la forma de los ficheros y
agruparlos por clase --, y sin eso cualquier conclusion sobre nutricion es una suposicion.*

**Quinta vez en esta fase que medir cambia el trabajo.** *Y esta vez la leccion es mas fina: **el primer
instrumento que escribi medía mal** -- palabras en vez de claves --, y lo descubri porque **otra medicion
mas fina lo contradijo**.*


---

## 8. El mapa, por fin: **que publica cada cadena, por claves, sobre el crudo que ya hay**

*(Ronda 29.)* Faltaba saber **cual** de los crudos de cada cadena es una ficha. Clasificados **por la forma
del JSON**, aparece solo:

```
alcampo     399 ficheros · 396  dict[additionalPageInfo, metadata, missedPromotions, productGroups]
aldi        140 ficheros · 139  dict[products]
carrefour  2004 ficheros · TODOS (no es json)          <- HTML
dia         547 ficheros · 543 (no es json) · 4  dict[... allergen_type_code ...]
mercadona   155 ficheros · 148  dict[categories, id, is_extended, layout, name, next_category]
                             6  dict[badges, brand, categories, color_variants, details, display_name]
lidl        sin crudo de hoy
```

**Y con las fichas localizadas, las claves -- que es lo que vale:**

| cadena | sus fichas traen | veredicto |
|---|---|---|
| **mercadona** | `nutrition_information`, `ingredients`, `allergens`, `details` | **nutricion estructurada, y YA ESTA EN DISCO** |
| **dia** | `ingredients`, `allergen_type_code` | ingredientes y alergenos; **nutricion no** |
| **aldi** | 18 claves, ninguna de nutricion | **la fuente no la publica** en su API |
| **carrefour** | HTML | *hay que parsear la pagina* |
| **alcampo** | `productGroups` (forma de busqueda) | **sin comprobar** |

### Y esto cambia F05 entero

**Para Mercadona, la ficha no hay que pedirla: hay que extraerla.** *El colector ya captura
`nutrition_information` todos los dias y lo guarda en crudo; lo que falta es leerlo y meterlo en la cola.*

**Es la respuesta que el hallazgo pedia** -- *«medir situacion actual **por campo/cadena**»* -- **y no es
la que yo estaba buscando**: no hay un problema de descarga, hay **un campo que se tira a la basura
despues de haberlo pedido y pagado**.

**Y las otras quedan dichas sin adorno**: *Dia da ingredientes y alergenos y no nutricion; Aldi no da
nada de eso; Carrefour exige parsear HTML; y Alcampo esta sin comprobar.* **Ninguna de esas frases es una
suposicion: cada una sale de leer las claves de un fichero real.**

### Lo que queda de F05, con esto

1. **Extraer `nutrition_information` de Mercadona** desde el crudo a la cola de fichas. *4.477 pendientes,
   y el dato ya esta capturado: no hace falta red.* **Es el primer trozo que se puede cerrar entero.**
2. **Comprobar `alcampo`** (43.603, el mayor) -- *misma medicion, sobre `productGroups`*.
3. **Dia**: ingredientes y alergenos, sin nutricion. *Decidir si eso basta para lo que se quiere enseñar.*
4. **Carrefour**: parsear HTML, *que es lo que el comentario de Lidl ya anticipaba*.
5. **Lidl**: 28 de 5.054 con ejecutor, y su limite de campos ya documentado.


---

## 9. **Correccion**: lo de la ronda 29 era falso, y el error fue leer el **nombre** del campo

*(Ronda 30.)* Escribi que *«Mercadona publica nutricion estructurada y **ya esta en disco**»*. **Es falso.**
Y el campo se llama `nutrition_information`, que es justo lo que me enganio: **lei el nombre, no el
contenido.**

**Lo medido, entero:**

```
las 6 fichas JSON de Mercadona de hoy:
    nutrition_information -> exactamente 2 claves: allergens (str), ingredients (str)
    ninguna clave con valores numericos
```

**Texto, y con HTML dentro** (`"Contiene <strong>soja...</strong>..."`, `"<strong>INGREDIENTES</strong>:
Preparado de nata..."`). **Ni kcal, ni grasas, ni hidratos, ni proteinas.** *Y `details` es marca, origen y
proveedores -- metadatos de producto, no nutricion.*

**Asi que lo que Mercadona da hoy, en sus fichas, es: ingredientes y alergenos.** *Ni una cifra.*

### Y queda una puerta abierta, sin abrir

**Dos ficheros de Mercadona de hoy contienen la palabra `energy`** -- *lo encontro el escaneo por
palabras de la ronda 28, que para esto si sirvio: dijo donde mirar.* **Y esos dos no son JSON**: el
`json.loads` falla y los salta. *Asi que son de otra clase -- probablemente HTML -- y **no se ha medido
que hay dentro**.*

**Puede ser una tabla de nutricion en la pagina. O puede ser la palabra en un script.** *No lo se, y **no
lo afirmo**: seria repetir el error de esta misma ronda.*

### El error, dicho con precision, porque es nuevo

**No fue «suponer sin medir»** -- medi, y clasifique 155 ficheros por su forma --. **Fue leer el nombre de
un campo y creerme lo que prometia.** *`nutrition_information` no contiene informacion nutricional: contiene
ingredientes y alergenos.*

*Es mas sutil que los errores anteriores de esta fase, y por eso conviene dejarlo escrito:* **medir el
nombre no es medir el contenido.**

### Lo que queda establecido, corregido

| cadena | sus fichas traen | como se sabe |
|---|---|---|
| **mercadona** | `ingredients` y `allergens`, **en texto**; **sin cifras** | por claves, 6 fichas |
| **dia** | `ingredients`, `allergen_type_code` | por claves, 1 ficha |
| **aldi** | 18 claves, ninguna de nutricion | por claves, 1 producto |
| **carrefour** | HTML | 2.004 ficheros, ninguno JSON |
| **alcampo** | `productGroups`, **sin comprobar** | -- |
| **¿y las cifras?** | **sin encontrar en ninguna** | *y dos ficheros de Mercadona sin identificar* |

**Y la conclusion honesta, que no es la de ayer**: *en el crudo de hoy **no se ha encontrado nutricion
numerica en ninguna cadena**, y **la busqueda no esta completa** -- queda identificar los dos ficheros de
Mercadona con `energy` y comprobar `alcampo`.*


---

## 10. El mapa, cerrado: **ninguna cadena publica nutricion numerica** -- y no es una suposicion

*(Ronda 31.)* Los dos huecos que quedaban, resueltos.

### Los dos ficheros de Mercadona con `energy`

**Eran listados de categoria, y `energy` estaba en el NOMBRE DE UN PRODUCTO:**

```
103c086d6c29   {"id":72,  "name":"Leche y bebidas vegetales", ...}
   ..."slug":"batido-chocolate-colacao-energy-pack-4"...
f9dd7a579b27   {"id":163, "name":"Isot?nico y energ?tico", ...}
   ..."slug":"bebida-energetica-vice-guava-monster-energy-ultra-zero-azucar-lata"...
```

*Un batido que se llama «energy» y una bebida «Monster Energy».* **El escaneo por palabras habia
encontrado una palabra en una marca, no un campo de nutricion** -- *por tercera vez en esta fase.*

### Alcampo

`productGroups` tiene **59 claves, y ninguna es de nutricion**. *Lo que trae es lo que se espera de un
listado de tienda*: `brand`, `description`, `amount`, `image`, `availableFormats`, `categoryPath`,
`alcohol`, `catchweight`... **y ni una cifra nutricional.**

### Y el mapa queda asi, cerrado

| cadena | nutricion **numerica** | lo que si da |
|---|---|---|
| **mercadona** | **no** | `ingredients` y `allergens`, en texto (6 fichas, por claves) |
| **alcampo** | **no** | 59 claves, ninguna de nutricion |
| **aldi** | **no** | 18 claves, ninguna de nutricion |
| **dia** | **no** | `ingredients`, `allergen_type_code` |
| **carrefour** | *HTML, sin medir* | -- |
| **lidl** | **no**, y documentado | *«no es un parser incompleto, es una fuente que no los da»* |

**En el crudo que el sistema captura a diario, ninguna cadena publica nutricion numerica.** *Y eso ya no
es una impresion: es el resultado de leer las claves de ficheros reales de cinco cadenas.*

### Y lo que F05 pedia, contestado

El hallazgo decia: *«**no llamar toda ausencia "limitacion de fuente"**»*. **Ahora se puede decir cual es
cual, y sale partido:**

- **Las cifras (kcal, grasas, hidratos, proteinas): es limitacion de fuente.** *Cinco cadenas medidas, y
  ninguna las publica en lo que se captura.* **No se arregla ejecutando la cola: no hay nada que pedir.**
- **Los ingredientes y los alergenos: NO es limitacion de fuente.** *Mercadona y Dia los publican, **y ya
  estan en disco**.* **Eso si se arregla extrayendo, y es el unico trozo de ficha que se puede cerrar hoy
  sin red.**
- **Y `lidl`, que si tiene ejecutor, da 28 de 5.054.** *Ahi la ausencia es trabajo sin ejecutar.*

### Y esto cambia el veredicto del producto, no solo el mapa

**Enseñar calorias no se puede con estas fuentes** -- *ni ejecutando la cola entera ni esperando* --.
**Enseñar ingredientes y alergenos, si**, *y para dos cadenas el dato ya se pidio y esta guardado.*

*Es la frase que faltaba en el veredicto, y ahora tiene cinco cadenas detras.*


---

## 11. El extractor, hecho -- **y lo que hay en el crudo son TRES fichas, no un tesoro**

*(Ronda 32.)* `projects/cesta/ficha_mercadona.py`, con siete pruebas y **una de ellas contra un fichero
real** (`test_contra_el_crudo_real`, que se salta si no hay crudo -- el crudo es del entorno, no del
codigo -- y **que hoy se ejecuto, no se salto**).

**Lo que hace**: lee `ingredients` y `allergens` del bloque `nutrition_information`, **quita el marcado sin
perder el texto** -- *el `<strong>` marca los alergenos, no decora* --, y **no rellena lo que la fuente no
trae**: un campo ausente no aparece, para no contar como cobertura una ficha vacia.

### Y ahora la cobertura de verdad, que es pequena

```
mercadona  155 crudos de hoy   ->  con ingredientes 3/155   con alergenos 3/155
dia        547 crudos de hoy   ->  543 NO son JSON, y con ingredientes 0/547
```

**Tres fichas.** *Asi que el crudo de hoy de Mercadona trae **3 fichas de producto** y el resto son
listados de categoria.* **Y no es que el extractor falle: es que el colector solo pidio tres paginas de
producto.**

**Y un numero mio que era enganoso, dicho para que no se cite**: en el primer pase mi script imprimia
*«con algo: 154/155»*, porque contaba tambien `id` y `nombre` -- **que no son una ficha**. *La cuenta buena
es la de ingredientes y alergenos: **3**.*

### Y Dia no se lee con esto

**0 de 547**, y **543 no son JSON**. *Dia tiene otra forma* -- la que encontre en la ronda 29 con
`allergen_type_code` -- **y este modulo es de Mercadona, no la lee.** *Decirlo es parte del resultado:
no he escrito un extractor generico, he escrito uno de Mercadona y **probado que no sirve para Dia**.*

### Lo que esto deja dicho sobre F05, sin adornos

1. **El extractor funciona y esta probado**, contra la forma real y contra un fichero real.
2. **Lo que hay capturado son 3 fichas.** *Para tener las 4.477 de la cola hay que **pedir las paginas**,
   y eso es red -- no un extractor.*
3. **Dia necesita su propio lector**, de otra forma.
4. **Y las cifras nutricionales siguen sin existir en ninguna fuente**, que es lo que el mapa de la
   seccion 10 dejo cerrado.

**Asi que «extraer lo que ya esta» da tres fichas, no cuatro mil.** *El trabajo grande sigue siendo pedir,
y ahora se sabe exactamente que pedir y para que.*


---

## 12. **Correccion grave**: la seccion 10 era falsa. **Dia SI publica nutricion numerica**

*(Ronda 33.)* En la seccion 10 escribi, y quedo commiteado, que *«en el crudo que el sistema captura a
diario, **ninguna cadena publica nutricion numerica**»*. **Es falso**, y el error es de metodo.

**Lo medido, sobre el crudo de hoy de Dia:**

```
kilo_calories  {"name": "Kcal",                  "uom": "kcal", "value": 54}
energy         {"name": "Valor Energetico (KJ)", "uom": "kJ",   "value": 257}
fat            {"name": "Grasas",                "uom": "g",    "value": 3.5}
carbohydrate   {"name": "Hidratos de carbono",   "uom": "g",    "value": 4.0}
sugars         {"name": "Azucares",              "uom": "g",    "value": 4.0}
protein        {"name": "Proteinas",             "uom": "g",    "value": 3.3}
salt           {"name": "Sal",                   "uom": "g",    "value": 0.1}
ingredients    {"name": "Ingredientes",          "value": "<p>...</p>"}
```

**La tabla entera, con unidades, y ya capturada.**

### Como lo perdi, porque es el error mas caro de la fase

**Generalice desde tres cadenas a cinco.** *Mercadona, Alcampo y Aldi **si** son «no publican» -- medido por
claves. Y de ahi salte a «ninguna cadena», **sin mirar las claves de Dia**, que tenia **cuatro ficheros
JSON clasificados en la ronda 29 y sin inspeccionar**.*

**Y habia una senal que ignore**: en la ronda 28 el escaneo por palabras encontro `energy` en dos ficheros
de Mercadona -- *que resultaron ser nombres de producto* -- **y no se me ocurrio comprobar los de Dia.**

**Es exactamente el error que el encargo prohibe**: *afirmar una ausencia sin haber mirado donde toca.* **Y
es peor que los anteriores de esta fase**: no fue leer mal un dato, fue **extender una conclusion a casos
que no habia medido**.

### Y queda un lector, hecho y probado

`projects/cesta/ficha_dia.py`, con **nueve pruebas y una contra un fichero real** (*que hoy se ejecuta*).
*Lee los siete nutrientes con su `uom`, los ingredientes sin marcado, y la identidad.*

**Y un fallo de forma que salio al escribir la prueba, no al leer**: *Dia mezcla dos formas* -- los
nutrientes como `{name, uom, value}` y **la identidad plana** (`"sku_id": "310847"`). *Aceptar solo la
primera dejaba fuera justo los campos para casar la ficha con el producto.*

**Y la trampa de esta fuente, escrita en la prueba**: `width` tiene **la misma forma** que `fat`
(`{name, uom, value}`), y no es nutricion. *Por eso se lee **por nombre de campo**, no por forma.*

### El mapa, corregido otra vez

| cadena | nutricion **numerica** | como se sabe |
|---|---|---|
| **dia** | **SI** -- kcal, kJ, grasas, hidratos, azucares, proteinas, sal | por claves, 4 fichas, **lector hecho** |
| **mercadona** | **no** | 6 fichas: solo `ingredients` y `allergens` en texto |
| **alcampo** | **no** | 59 claves |
| **aldi** | **no** | 18 claves |
| **carrefour** | *HTML, sin medir* | -- |
| **lidl** | **no**, documentado | *«es una fuente que no los da»* |

### Y lo que esto cambia en el veredicto

**Enseñar calorias SI se puede** -- *para Dia, que publica la tabla entera, y cuyo lector ya esta escrito y
probado*. **Lo que no se puede es enseñarlas para todas las cadenas**, y ahora se sabe **cual si y cual
no**, campo a campo.

*Lo que hay capturado hoy son **4 fichas de Dia** -- y en 3 esta la tabla --, asi que el trabajo sigue
siendo **pedir**: el lector no llena la cola solo.* **Pero la pregunta «¿se puede?» tiene respuesta, y es
que si.**


---

## 13. Carrefour: el unico hueco, y **no se puede cerrar por claves**

*(Ronda 34.)* El mapa quedaba con Carrefour *«HTML, sin medir»*. Medido:

```
2.004 crudos de hoy, y los 2.004 son HTML -- ni un JSON

ficheros con alguna palabra de nutricion: 40/2004
   nutriben 35   proteina 2   energia 2   nutricosmetica 1
```

**Y esas palabras no dicen nada.** *`nutriben` es **una marca de potitos** -- 35 de los 40 --, y
`nutricosmetica` es otra palabra de catalogo.* **Es el mismo falso positivo que ya me ha enganado tres veces
en esta fase.**

**Y hay una razon de fondo**: *en HTML **no hay claves que leer***. *Todo el metodo que ha funcionado con
Mercadona, Dia, Alcampo y Aldi -- leer las claves de un JSON -- **no se puede aplicar aqui**.*

**Asi que lo honesto no es decir que Carrefour no publica nutricion: es decir que no se sabe.** *Para
saberlo hay que **parsear el HTML** -- buscar la tabla en el marcado, o el JSON que la pagina lleve
incrustado --, y eso **no se ha hecho**.*

*Es exactamente la leccion de la ronda 33 aplicada a tiempo: **no extender una conclusion a un caso que no
he medido**. Ayer escribi «ninguna cadena» sin mirar Dia; hoy no escribo «Carrefour tampoco» sin mirar su
HTML.*

### Y el mapa queda cerrado, con un solo hueco declarado

| cadena | nutricion **numerica** | como se sabe |
|---|---|---|
| **dia** | **SI** -- kcal, kJ, grasas, hidratos, azucares, proteinas, sal | por claves, 4 fichas, **lector hecho y probado** |
| **mercadona** | **no** | 6 fichas: solo `ingredients` y `allergens`, en texto |
| **alcampo** | **no** | 59 claves, ninguna |
| **aldi** | **no** | 18 claves, ninguna |
| **lidl** | **no**, y documentado | *«no es un parser incompleto, es una fuente que no los da»* |
| **carrefour** | **NO SE SABE** | HTML; **el metodo de claves no sirve**, y no se ha parseado |

**Uno de seis sin contestar, y esta dicho como lo que es** -- *no como un «tampoco», que es lo que habria
escrito ayer.*


---

## 14. Carrefour, cerrado -- y **el hallazgo que unifica las seis cadenas**

*(Ronda 35.)* El hueco de Carrefour se puede cerrar, y no por claves sino **leyendo su `ld+json`** -- *que es
lo mismo que hace `ficha_lidl.py`, asi que la tecnica ya estaba en el proyecto.*

```
2.004 crudos: 1.998 con ld+json
los @type que aparecen:   BreadcrumbList 1995 · Product 1995 · Organization 3
y los 1.995 bloques Product tienen TODOS las mismas CUATRO claves:
    ['@context', '@type', 'name', 'offers']
```

**Ninguno trae ficha.** *Ni ingredientes, ni alergenos, ni nutricion: nombre y oferta.* **Y las paginas son
de categoria** -- los titulos dicen *«Comprar Platos Preparados | Supermercado Online Carrefour»* --, asi
que esos bloques `Product` son **entradas de listado, no fichas de producto.**

**Asi que la respuesta para Carrefour no es «no se sabe» ni «no publica»: es que **lo capturado no trae
ficha**, porque **lo que se captura son paginas de categoria**.**

### Y aqui esta lo que unifica las seis cadenas

*Mirando las seis juntas, el problema deja de ser seis problemas distintos:*

| cadena | fichas en el crudo de hoy | **que captura el colector** |
|---|---|---|
| **lidl** | 5.054 en cola, **28 hechas** | *tiene **ejecutor propio** (`fichas_lidl.py`)* |
| **mercadona** | **3** de 155 | **listados de categoria** (`{"categories": [...]}`) |
| **dia** | **4** de 547 | **listados y paginas sueltas** (543 no son JSON) |
| **carrefour** | **0** de 2.004 | **paginas de categoria** (1.995 `Product` de listado) |
| **alcampo** | -- | `productGroups`, **forma de busqueda** |
| **aldi** | -- | su **API de producto por lotes**, que **no trae nutricion** |

**Cinco de las seis cadenas capturan listados, no fichas. La unica que pide fichas es Lidl.**

**Y eso convierte F05 en un solo problema, no en seis**: *no hay que escribir cinco parsers distintos ni
decidir cinco veces de donde sale la nutricion.* **Hay que hacer lo que Lidl ya tiene: pedir las fichas.**
*Los lectores ya estan escritos para las dos cadenas cuyas fichas traen algo* -- `ficha_mercadona.py` y
`ficha_dia.py`, **probados contra crudo real** --, *y lo que falta es **el equivalente de `fichas_lidl.py`
para ellas.***

### Lo que queda de F05, en una linea

**Pedir fichas, como Lidl.** *La cola, el lease, el presupuesto, el ritmo y dos lectores ya estan hechos y
probados; lo que no existe es quien **pida** para las otras cinco.* **Y `carrefour` no necesita parser
nuevo: necesita que se pidan sus paginas de producto.**


---

## 15. **La respuesta, y estaba ya hecha**: Dia tiene 6.331 productos con tabla nutricional

*(Ronda 36.)* Yendo a escribir el ejecutor de Dia, mire `collectors/dia.py` antes -- *por fin, antes* -- y
**estaba todo hecho, y mejor de lo que yo iba a hacerlo.**

### Lo que ya existe en el colector

```
collectors/dia.py:5     Ficha: /api/v1/product/<sku_id>?lang=es -> ean_code
collectors/dia.py:77    def ficha(f, sku_id)  ->  f.get(f"{BASE}/api/v1/product/{sku_id}?lang=es")
collectors/dia.py:165   def _nutricion(p)  ->  la tabla, y por cuanto esta expresada
```

**El colector de Dia pide la ficha y extrae la tabla en cada pasada diaria.** *No hace falta ni cola ni
ejecutor nuevo para eso: ya ocurre.*

**Y esta hecho con el cuidado que F05 pide**, en su propio comentario:

> *«Se conserva una tabla parcial **sin inventar los nutrientes ausentes**. Quien la consulte debe
> distinguir **desconocido de cero** y comprobar la base.»*

> *«Ocho fichas dicen que su tabla esta por "1447g", "2.7g" o "97ml". No se sabe comparar eso con un "por
> 100 g", y **una tabla que no se puede comparar enseñada como si se pudiera es peor que no tenerla**.»*

### Y la cobertura de verdad, en los maestros

```
dia        6.331 entradas  ->  con nutricion: 6.331   (claves: nutricion, nutricion_por)   <- TODAS
mercadona  4.494 entradas  ->  con nutricion: 0
alcampo, aldi, carrefour, lidl:  no hay maestro
```

**Dia: 6.331 productos con tabla nutricional, el 100 % de su maestro, ya extraida.** *Y con la base
declarada al lado (`nutricion_por`), que es lo que permite enseñarla sin mentir.*

**Mercadona: 4.494 productos y cero tablas**, *coherente con que su fuente no las publique.*

### Y la correccion que me toca

**`ficha_dia.py` y `ficha_mercadona.py`, escritos en las rondas 32 y 33, no hacian falta para esto.** *El
proyecto ya tenia el de Dia, dentro del colector, **y con dos cosas que el mio no tiene**: la base
(`nutricion_por`) y el rechazo de las bases incomparables.* **Los mios leen el crudo; el del colector lee
la ficha de la API y ademas decide si la tabla es comparable.**

**Y el error es el mismo de siempre, mas grande**: *pase cinco rondas tratando F05 como «la cola no se ha
ejecutado» cuando **la respuesta -- 6.331 productos con nutricion -- llevaba todo el tiempo en el maestro**.
Grep a `collectors/dia.py` lo habria dicho en el primer minuto.* **Mire el crudo antes que el codigo que lo
escribe.**

### Lo que F05 deja, contestado

| pregunta | respuesta | evidencia |
|---|---|---|
| ¿Se puede enseñar nutricion? | **Si, para Dia** | **6.331 productos**, 100 % de su maestro, con base declarada |
| ¿Y para Mercadona? | **No** | 4.494 productos, 0 tablas; su fuente no las publica |
| ¿Y para las otras cuatro? | **No se sabe: no hay maestro** | alcampo, aldi, carrefour y lidl no tienen maestro construido |
| ¿La cola de 79.887 es el camino? | **No para esto** | *la nutricion de Dia no pasa por la cola: la extrae el colector en cada pasada* |

**Asi que la cobertura de fichas no es cero: es 6.331 de Dia y 0 de Mercadona, y el resto sin maestro.**
*Lo que la cola de 79.887 mide es **otra cosa** -- refresco y fichas de cadenas que no las traen en el
listado --, y decirlo como «cobertura de fichas» mezclaba dos cosas distintas.*
