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
