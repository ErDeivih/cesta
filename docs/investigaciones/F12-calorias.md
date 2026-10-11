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
