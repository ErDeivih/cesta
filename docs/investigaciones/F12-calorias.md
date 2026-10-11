# F12 -- Calorias con registro agil, no solo formulario (P1)

**Criterio, de `docs/SUPERAPP-FASE2-EMPEZAR-AQUI.md:161`:**

> Investigar N01-N06 con Cronometer/YAZIO/MacroFactor. **Seleccion reciente/favorita**, busqueda por
> alimento/... Alimentos personales, **receta versionada y porcion**; **edicion/borrado/deshacer coherentes**.
> **Copiar comida** es...
> **Aceptacion:** **GTIN desconocido** / **varios candidatos** / **camara denegada**, **reintentos**, **dos
> comidas iguales** y ca[ntidad]...

**Y los seis criterios que cubre, de `docs/SUPERAPP-COMPETENCIA-Y-REA.md:111-116`:**

| ID | lo que pide |
|---|---|
| **N01** | *registro rapido* -- **recientes/favoritos** y **copiar comida** con **cantidad editable** y **nueva operacion legitima** |
| **N02** | *codigo de barras* -- **GTIN validado** y producto verificable; **fallo de camara o sin resultados permite texto/numero** |
| **N03** | *porciones* -- **base nutricional clara**, gramos/ml/racion con **conversiones trazables** |
| **N04** | *diario por comidas* -- registrar/editar/borrar/**recargar y reintentos**; **cuenta y fecha local correctas** |
| **N05** | *alimentos propios* -- **fuente declarada**, datos desconocidos y **sin falsa verificacion de etiqueta** |
| **N06** | *receta consumida* -- **version y racion registradas**; **editar receta no reescribe ayer** |

---

## 1. Punto de partida: **nada medido**, y dos de los seis ya tienen precedente en esta fase

**De `N01`-`N06` no se ha medido nada.** *Y antes de empezar, dos conexiones que conviene anotar **como
sospechas, no como hechos**:*

1. **`N06` -- «editar receta no reescribe ayer» -- es la misma pregunta que `R03`.** *Alli se midio y **pasa**:
   `core/recetas.py` guarda **cada version autocontenida**, y `test_fase2_f09_recetario.py` comprueba que v1
   sigue diciendo «harina» despues de editar a «patata».* **Si el diario guarda la version -- y `diario.py:75-94`
   dice que la comprueba antes de anotar --, `N06` puede estar cubierto por la misma pieza.** *Por **medir**, no
   por suponer.*
2. **`N04` -- «recargar y reintentos» -- es lo que el encargo puso en su lista de prioridades**: *«reintentos
   del diario»*. **Es el unico de los seis que el encargo nombra explicitamente**, y por eso se empieza por el.

### Y los cuatro casos de la aceptacion

| caso | **de que criterio es** |
|---|---|
| **GTIN desconocido** | `N02` -- *un codigo que se lee y no esta en el catalogo* |
| **varios candidatos** | `N02` -- *un codigo que apunta a mas de uno* |
| **camara denegada** | `N02` -- *y el criterio dice que **tiene que permitir texto/numero*** |
| **dos comidas iguales** | `N01` -- *«copiar comida… **nueva operacion legitima**»: dos registros iguales **no son un duplicado*** |
| **reintentos** | `N04` |

**Y los dos ultimos son los interesantes**, porque son los dos en que un sistema bien hecho **se comporta al
reves de lo que parece**: *una camara denegada **no** puede dejar sin registrar, y **dos comidas iguales no son
un error**.*

### Y la primera medida, que es de `N04`

**«Recargar y reintentos» quiere decir dos cosas, y hay que ver las dos:**

1. **Que recargar la pantalla no pierda lo escrito ni duplique lo guardado** -- *que es **idempotencia**, y es
   la misma pregunta que `previa_compra` contesta con «repetir la misma transferencia no duplica».*
2. **Y que un fallo de red no deje el diario a medias** -- *que es **reintentos de verdad**: volver a mandar lo
   mismo tiene que acabar bien **o no hacer nada**, nunca contar dos veces.*

**Y en esta fase ya aparecio el mismo problema dos veces** (`C01b` en las listas, y la «nueva operacion
legitima» de `N01`), **asi que hay una pregunta que hacerle al codigo y que vale para los tres**: *¿que pasa si
se manda **dos veces la misma cosa**?*


---

## 2. `N04` y `N01`: **la clave de operacion ya los contesta** -- y contesta los dos casos a la vez

*(Ronda 129.)* La primera medida de F12, y **es la pregunta que el encargo puso en su lista de prioridades**
(*«reintentos del diario»*). **`plataforma/api/diario.py:51-54`:**

```python
51  # **La clave de la operacion.** El cliente la genera al enviar y la repite si reintenta: un
52  # doble clic o una respuesta perdida devuelven **la entrada que ya hay** en vez de crear otra.
53  # Dos comidas legitimas llevan claves distintas y se registran las dos.
54  clave_operacion: str | None = None
```

**Cuatro lineas, y contestan `N04` y `N01` enteros** -- *y **los dos casos de la aceptacion que parecian
contrarios***:

| el caso | **lo que dice el codigo** |
|---|---|
| **«reintentos»** (`N04`) | *«el cliente la genera al enviar y **la repite si reintenta**: un **doble clic** o una **respuesta perdida** devuelven **la entrada que ya hay** en vez de crear otra»* |
| **«dos comidas iguales»** (`N01`) | *«**Dos comidas legitimas llevan claves distintas y se registran las dos**»* |

### Y esto es lo que el criterio pedia, exactamente

**`N04`**: *«registrar/editar/borrar/**recargar y reintentos**»* -- **y los reintentos estan**.
**`N01`**: *«copiar comida con cantidad editable y **nueva operacion legitima**»* -- **y la operacion legitima
esta**: *dos comidas iguales **no son un duplicado**, y el sistema **no las confunde**, porque la clave la genera
quien come y no el servidor.*

**Y esa es la decision que lo hace funcionar**: *si la clave la generara el servidor **a partir del contenido**
-- «la misma comida a la misma hora» --, **dos comidas iguales se perderian**.* **Generandola el cliente, el
sistema distingue «lo mismo dicho dos veces» de «dos veces lo mismo»**, que es exactamente la distincion que la
aceptacion pone a prueba con dos casos que parecen el mismo.

### Y como se comporta el resto del diario, de paso

```
57   @rutas.get("/rango")               <- y :60 dice por que va ANTES: «si no, FastAPI leeria "rango" como una fecha»
68   @rutas.post("", status_code=201)
124  @rutas.post("/desde-ficha", status_code=201)
140  @rutas.get("/{fecha}")
149  @rutas.delete("/entrada/{entrada_id}")
```

**Las cinco rutas, y `:60` es otra decision escrita**: *el orden de las rutas importa y esta dicho.* **Y `:72-74`
es la tercera**: *«la receta se comprueba **antes** de guardarla... es lo que cierra las referencias
inventadas»* -- *que es `N06`, y es la pieza que ya se midio en `R03`.*

### Y `N06` empieza a confirmarse

**La sospecha del §1 se sostiene**: *`diario.py:72-74` comprueba la receta **antes** de anotar, y `R03` ya esta
medido (versiones autocontenidas, v1 no cambia).* **Falta la mitad de `N06`** -- *que el diario **guarde la
version** y que «editar receta **no reescriba ayer**» --, y eso es una columna y un `SELECT`.*

### Y F12, con lo medido

| criterio | **estado** |
|---|---|
| **`N01`** -- registro rapido | **la «nueva operacion legitima» esta** (`clave_operacion`, `:51-54`); *recientes/favoritos y copiar con cantidad editable, por medir* |
| **`N02`** -- codigo de barras | *por medir* |
| **`N03`** -- porciones | *por medir* |
| **`N04`** -- diario por comidas | **los reintentos estan, y por la via correcta** (`:51-52`); *recargar, cuenta y fecha local, por medir* |
| **`N05`** -- alimentos propios | *por medir* -- *`fuente_dato` existe (`:49`), con `diario.DESCONOCIDO` por defecto* |
| **`N06`** -- receta consumida | *la comprobacion previa esta (`:72-74`); **falta que se guarde la version*** |

**Y `N05` asoma en la misma firma**: *`fuente_dato: str = diario.DESCONOCIDO`* -- *«fuente declarada», y **por
defecto desconocida**, que es no afirmar lo que no se sabe.* **Es `nombre_visto` y `sin_precio` otra vez, en un
tercer sitio, y con el criterio pidiendolo con esas palabras: «sin falsa verificacion de etiqueta».***


---

## 3. `N06`: **hecho, y con una garantia dura** -- «sin ella no se puede releer»

*(Ronda 130.)* La mitad que faltaba del §1, y **la sospecha se confirma entera**: *`N06` no solo esta
cubierto, esta **blindado**.*

### La columna, la clave, y el `raise`

```python
45   version   TEXT,                                       # en la tabla `entrada`
92   _CAMPOS_DE_LA_OPERACION = ("fecha", "comida", "tipo", "referencia", "version", "cantidad_g", "kcal", ...)
154  if tipo == RECETA and version is None:
155      raise ValueError("una receta se anota con su version: sin ella no se puede releer")
```

**Las tres cosas, y cada una cierra una mitad del criterio** (`SUPERAPP-COMPETENCIA-Y-REA.md:116`):
*«**Version y racion registradas**; **editar receta no reescribe ayer**.»*

| lo que pide `N06` | **donde esta** |
|---|---|
| **«version... registrada»** | **la columna `version TEXT`** (`:45`), *y se escribe en el `INSERT`* (`:170`, `:194-196`) |
| **«...y racion registradas»** | **`cantidad_g`** *y los nutrientes de la entrada* -- *que es la racion **consumida**, no la de la receta* |
| **«editar receta **no reescribe ayer**»** | **`R03`** (*versiones autocontenidas, ya medido*) **+ que la entrada guarde la version**: *ayer apunta a la version 1, **y la version 1 no cambia*** |

### Y la frase que lo cierra es un `raise`, no un comentario

**`diario.py:154-155`**:

> *`if tipo == RECETA and version is None: raise ValueError("una receta se anota con su version: **sin ella no
> se puede releer**")`*

**No es que la version se pueda guardar: es que una entrada de receta **sin version no entra**.** *Y el motivo
esta dicho y es el correcto*: **sin la version, la entrada **no se puede releer** -- apuntaria a «la receta», y
«la receta» cambia.**

**Es la misma forma que `R04`** (*lo que no tiene cantidad no la gana*), **que `R08`** (*comprar no es comer*) y
que `previa_compra` (*lo que no se puede consolidar se nombra*): **la regla no se deja al cuidado de quien
escribe, se pone en el camino.** *Aqui, en un `raise` que impide guardar mal.*

### Y de propina: la version entra en la clave de operacion

**`_CAMPOS_DE_LA_OPERACION` (`:92`) incluye `version`.** *Asi que **la misma receta en dos versiones distintas
son dos operaciones distintas**, y una no se confunde con la otra* -- *que es `N01` y `N06` a la vez, con la
misma pieza.*

### Y F12, con lo medido

| criterio | **estado** |
|---|---|
| **`N01`** -- registro rapido | **la «nueva operacion legitima» esta**; *recientes/favoritos y copiar, por medir* |
| **`N02`** -- codigo de barras | *por medir* |
| **`N03`** -- porciones | *por medir* |
| **`N04`** -- diario por comidas | **los reintentos estan**; *recargar, cuenta y fecha local, por medir* |
| **`N05`** -- alimentos propios | *por medir* -- *`fuente_dato` con `DESCONOCIDO` por defecto* |
| **`N06`** -- receta consumida | **HECHO, con `raise`**: version obligatoria, y la version entra en la clave |

**Cuatro de los seis, con su mitad principal ya vista** -- *y las dos que quedan enteras (`N02`, `N03`) son las
del codigo de barras y las porciones, que son de pantalla y de conversion.*

### Y la cuenta de la fase, ya sin exagerar

**Diez piezas encontradas ya resueltas y con el motivo escrito**, mientras buscaba otra cosa: *`kcal_100g` por
EAN, `AvisoIdentidad`, `porPasillo`, el `::VARCHAR` de `promo_hasta`, `unidades_pack` que no llegaba a la
pantalla, el `409` de la lista duplicada, la clave de operacion, la version obligatoria, el historial con sus
tres decisiones, y `costeReceta`.*

**Y las diez son la misma cosa**: *el proyecto **ya sabia** lo que este encargo viene a comprobar, **y lo dejo
escrito donde se pudiera leer**.* *Lo que ha hecho esta fase, casi siempre, ha sido **leerlo.***


---

## 5. `N05`: **hecho, y con la fuente en un conjunto cerrado** -- la quinta vez la misma disciplina

*(Ronda 134.)* El criterio (`SUPERAPP-COMPETENCIA-Y-REA.md:115`): *«Alimentos propios -- **fuente declarada**,
datos desconocidos y **sin falsa verificacion de etiqueta**.»* **Y las tres cosas estan, en `core/diario.py`:**

```python
30   ETIQUETA = "etiqueta"
31   FICHA = ...            # (la ficha del catalogo)
32   ESTIMADO = ...
33   DESCONOCIDO = "desconocido"
34   FUENTES = (ETIQUETA, FICHA, ESTIMADO, DESCONOCIDO)
52   fuente_dato TEXT NOT NULL,
151  if fuente_dato not in FUENTES:
152      raise ValueError(f"fuente de dato desconocida: {fuente_dato}")
```

| lo que pide `N05` | **donde esta** |
|---|---|
| **«fuente declarada»** | **`fuente_dato`, `NOT NULL`** -- *no puede quedar sin decir* |
| **«datos desconocidos»** | **`DESCONOCIDO` esta en la lista** -- *es **una de las cuatro respuestas validas**, no la ausencia de respuesta* |
| **«sin falsa verificacion de etiqueta»** | **`ETIQUETA` y `FICHA` y `ESTIMADO` son tres cosas distintas**, *y una entrada **no puede** decir una de las cuatro que no sea* |

### Y la cuarta es la que hace el trabajo

**«Sin falsa verificacion de etiqueta» quiere decir que un numero **no puede** parecer leido de la etiqueta
cuando no lo fue.** *Y la forma de conseguirlo no es una advertencia en la pantalla: es **que la fuente sea un
campo obligatorio con cuatro valores posibles**, y que **inventarse uno sea un `raise`**.*

**Es la quinta vez la misma forma**, y ya se puede decir el patron entero:

| donde | la regla | y como se impone |
|---|---|---|
| **`escala`** (`R04`) | lo que no tiene cantidad no la gana | *no se le pone* |
| **`previa_compra`** | lo que no se puede consolidar se nombra | *se devuelve en `sin_consolidar`* |
| **`diario.py`** (`N06`) | una receta se anota con su version | **`raise`** |
| **`Escaner.tsx`** (`N02`) | «no puedo comparar» no es «no hay nada» | *`comparacion: null`, no `[]`* |
| **`diario.py`** (`N05`) | la fuente del dato se declara | **`raise` sobre un conjunto cerrado** |
| **`costeReceta.ts`** (`R09`) | lo usado y lo comprado no se juntan | *dos numeros, y la linea 9 dice por que* |

**Seis sitios, una sola regla**: *lo que no se sabe **se dice**, y **no se deja que se confunda** con un cero,
con una lista vacia, con un envase, o con una etiqueta.* **Y en dos de los seis, con un `raise` que impide
guardar mal.**

### Y `N03` queda para la ronda siguiente, y digo por que

**La busqueda de «porcion/racion/base nutricional» devuelve 212 menciones, y **casi todas son ruido** --
`alcance`, `atributos`, y `racion` en docstrings que hablan de otra cosa.** *No he encontrado la pieza en una
lectura, y **no voy a concluir «no existe» desde un grep ruidoso** -- que es el error que esta fase ha cometido
ocho veces.*

**Lo que si se ve, y hay que anotarlo sin confundirlo con una medicion**: *`fuente_dato` incluye **`FICHA`** --
que es la tabla nutricional del catalogo, y **la base de la ficha es un dato que existe** (`nutricion_por`,
`kcal_100g`).* **Si `N03` es «base nutricional clara», la base esta declarada por `nutricion_por`; lo que hay
que medir es si la conversion a racion es trazable.** *Es un `SELECT` y una lectura, y va en la ronda siguiente.*

### Y F12, con lo medido

| criterio | **estado** |
|---|---|
| **`N01`** | *la «nueva operacion legitima» esta* |
| **`N02`** | **hecho** (la camara como boton) |
| **`N03`** | **por medir** -- *y el grep ruidoso no cuenta como respuesta* |
| **`N04`** | **hecho** (los reintentos) |
| **`N05`** | **hecho**, con `raise` sobre conjunto cerrado |
| **`N06`** | **hecho** (version obligatoria) |

**Cuatro hechos, uno con su mitad vista, y uno por medir.**


---

## 6. `N03`: **la base nutricional es un campo con tres valores, y se ensena** -- con `SELECT`, no con grep

*(Ronda 135.)* El criterio (`SUPERAPP-COMPETENCIA-Y-REA.md:113`): *«Porciones -- **base nutricional clara**,
gramos/ml/racion con **conversiones trazables**.»* **Y la mitad de la base esta, y esta bien.**

### La base, declarada en el esquema y ensenada en la pantalla

```python
core/schemas.py:63      "nutricion_por": pl.Utf8,      # "100g" | "100ml" | "porcion"
plataforma/web/app.js:1299   `Por ${p.nutricion_por || '100 g'}`, tabla...       # el `app.js` de hoy
paginas/Producto.tsx:623     Nutricion {miembro.nutricion_por ? `(po[r] ...`}     # la app nueva
```

**Tres cosas, y las tres son del criterio:**

1. **La base es un campo con tres valores posibles** -- *`100g`, `100ml`, `porcion`* --, **no un numero
   implicito.** *Un `kcal` sin decir «por que» **no es un dato**: es un numero que parece un dato.*
2. **Y se ensena**: *«Por 100 g»*, *«Por 100 ml»*, *«Por porcion»* -- **en las dos pantallas**, la vieja
   (`app.js`) y la nueva (`Producto.tsx`).
3. **Y cuando falta, se dice `100 g`** -- `p.nutricion_por || '100 g'` --, *que es la convencion de la
   etiqueta europea y **el valor por defecto que el colector usa**.*

### Y el comentario del esquema dice de que va esto

```python
core/schemas.py:63    "nutricion_por": pl.Utf8,      # "100g" | "100ml" | "porcion"
core/schemas.py:64    # Ninguna otra app de la competencia tiene esto. Alimenta la despensa
core/schemas.py:65    # deducida: se compro hace 12 dias, dura 15, se acaba el viernes.
```

**«Ninguna otra app de la competencia tiene esto»** -- *y es verdad que es raro: **la mayoria de las apps
guardan `kcal` y no dicen por que**.* **Y la linea 64-65 dice **para que**: alimenta la despensa deducida.** *O
sea, `N03` **no es solo para ensenar la tabla: es lo que hace que `dias_caducidad` y la despensa se puedan
calcular.***

### Y la segunda mitad -- «conversiones trazables» -- es donde hay que seguir

**«Conversion trazable» quiere decir**: *poder ir **de la base a la racion**, y **poder decir como**.*

- **Con `100g` o `100ml`, la conversion es una regla de tres sobre el peso**, *y es trazable si se sabe el peso
  de la racion.*
- **Con `porcion`, la base **es** la racion** -- *pero **`porcion` no dice de que tamano***. *Y ahi esta el
  hueco: `kcal` «por porcion» **sin decir cuantos gramos es una porcion** no se puede comparar con nada.*
- **Y `costeReceta.ts` ya trata el caso analogo** (`R09`): *«en `ud` no se prorratea… seria inventar una fraccion
  de huevo».*

**Asi que la pregunta de la segunda mitad es una y es concreta**: ***¿hay un campo con el tamano de la porcion, o
«por porcion» se queda sin decir de cuanto?*** *Es un `SELECT` sobre el esquema y un `grep` de `porcion_g` o
equivalente, **y va en la ronda siguiente** -- y esta vez **con el `SELECT` primero**, que es lo que ha funcionado
cuando el grep se atasca.*

### Y F12, con lo medido

| criterio | **estado** |
|---|---|
| **`N01`** | *la «nueva operacion legitima» esta* |
| **`N02`** | **hecho** |
| **`N03`** | **la base, hecha y ensenada**; *la «conversion trazable» depende de si hay tamano de porcion* |
| **`N04`** | **hecho** |
| **`N05`** | **hecho** |
| **`N06`** | **hecho** |

**Cinco de los seis, con su mitad principal hecha; y `N03` tiene la mitad de la base y la pregunta de la racion
ya escrita.**
