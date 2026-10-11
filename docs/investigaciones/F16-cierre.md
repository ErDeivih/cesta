# F16 -- Ensayo integral y cierre honesto

**Criterio, de `docs/SUPERAPP-FASE2-EMPEZAR-AQUI.md:195`:**

> **Matriz de capacidades C/R/N/X** y paquetes **F00-F16 con estado y evidencia**. Suite Python/lint, build/tipos...
> **Informe final distingue: implementado, probado, limite demostrado de fuente, pendiente y descartado por
> [decision].**
> **Veredicto domestico depende de privacidad, identidad/costes, registro, publicacion y recuperacion.**

---

## 1. Lo que este paquete es, y por que **no** es «un documento mas»

**F16 es el entregable que el encargo nombra al final**: *«Termina con **pruebas reproducibles, matriz de
capacidades y un veredicto honesto sobre uso domestico local**».*

**Y sus tres lineas son tres cosas ya hechas en parte, y una que no:**

| lo que pide F16 | **estado** |
|---|---|
| **matriz C/R/N/X**, F00-F16, **con estado y evidencia** | **`docs/SUPERAPP-FASE2-MATRIZ.md` existe** y tiene el inventario (§1), la tabla por paquete (§2, rehecha en la ronda 132), los ensayos (§3), el aviso de §0, y **falta §4 y §5** |
| **suite Python/lint, build/tipos** | **existen y pasan**: `ruff` limpio, **1800 pruebas + 3 xfailed**, `tsc` 0, build 0 |
| **el informe final, con cinco estados distinguidos** | **`SUPERAPP-FASE2-MATRIZ.md` §4** -- *no escrito* |
| **el veredicto domestico** | **§4**, y depende de cinco cosas que el criterio nombra |

### Y las «C/R/N/X» del criterio son las letras de los criterios

**`C` = Compra** (*C01-C10*), **`R` = Recetas** (*R01-R10*), **`N` = Nutricion/calorias** (*N01-N06*), y **`X`** =
*lo descartado o fuera de alcance.* *Es decir: **la matriz del proyecto ya esta organizada por esas letras**, y lo
que F16 pide es **el estado de cada una con su evidencia** -- que es exactamente lo que las rondas 127-145 han ido
midiendo.*

**Y los cinco estados que hay que distinguir son los del tablero**, y ya se ha trabajado con ellos:

| el estado | **que significa** | **ejemplos medidos** |
|---|---|---|
| **implementado** | *esta, y se puede usar* | `previa_compra`, `costeReceta`, la clave de operacion |
| **probado** | *esta **y hay una prueba que lo demuestra*** | `R03`/`R04` (9 pruebas), `kg+kg`, la publicacion |
| **limite demostrado de fuente** | ***no esta porque la fuente no lo da*** | *Alcampo y Aldi con **0** nutricion; Mercadona sin tablas* |
| **pendiente** | *no esta, y se puede hacer* | `R02` (importar), `R05` (cocina), `R08` (despensa), `C09` («previsto») |
| **descartado por decision** | *no se hara, y esta dicho por que* | *por escribir -- y las **tres decisiones** del tablero entran aqui si el dueno dice que no* |

**Y la distincion que mas importa, y que esta fase ha tenido que aprender**: *«limite de fuente» **no** es
«pendiente»*. *`N03` lo enseño con numeros: **`porcion` tiene 0 productos** -- y eso **no es un hueco**: es que
**la base que no tendria tamano no la usa nadie**.* **Un cero medido y un cero supuesto se parecen en un informe
y no se parecen en nada.**

### Y el veredicto depende de cinco cosas, y las cinco ya tienen su parte medida

**El criterio dice que el veredicto domestico depende de: privacidad, identidad/costes, registro, publicacion y
recuperacion.** *Y de las cinco hay algo medido:*

| de que depende | **lo medido** |
|---|---|
| **privacidad** | `_acceso` (403/404), el aislamiento de recetas (9 pruebas), y `diario.py:821` -- *«quien tiene permiso de solo mirar no puede sacar de aqui lo que hay dentro»* |
| **identidad/costes** | `core/identidad.py` (GTIN validado, cuarentena), y **el pack resuelto** (`parse_formato`) |
| **registro** | la clave de operacion, la version obligatoria, y `fuente_dato` con `raise` |
| **publicacion** | `prueba_f03_publicacion.py` **PASA**: 19,81 -> 20,81 EUR con el alta en el diario |
| **recuperacion** | **la mitad sin medir**: *los reintentos estan (clave de operacion); **lo de offline no**, y es F15* |

**Asi que F16 se puede escribir, y su veredicto va a ser honesto en el sentido que el encargo pide**: *no «todo
bien», sino **que se puede hacer hoy, que no, y por que** -- con la diferencia entre **no esta porque nadie lo ha
escrito** y **no esta porque la fuente no lo da**.*
