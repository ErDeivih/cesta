# F11 -- Despensa y aprovechamiento (P2)

**Criterio, de `docs/SUPERAPP-FASE2-EMPEZAR-AQUI.md:153`:**

> Investigar R08-R10; **construir version local pequeña, no inventario logistico**. Stock declarado con unidad...
> Sugerir recetas por ingredientes **disponibles, faltantes, fecha conocida y coste parcial**. Descontar exist[encias]...
> **Aceptacion:** **consumo parcial** / **stock desconocido** / **unidades incompatibles** / **fecha ausente**,
> filtros y privac[idad]

**Y los tres criterios que cubre, de `docs/SUPERAPP-COMPETENCIA-Y-REA.md:108-110`:**

| ID | lo que pide |
|---|---|
| **R08** | *despensa/sobrantes* -- **existencias declaradas**, ubicacion/caducidad **opcional**; **compra no acredita consumo ni stock restante** |
| **R09** | *coste por racion* -- **coste usado distinto de envases por comprar**; cobertura/ambito/version |
| **R10** | *buscar por lo disponible* -- explicar **disponibles/faltantes**, coste y restricciones; **sugerencia, no sustitucion automatica** |

---

## 1. Punto de partida: **nada medido, y una pista que vale mucho**

**De R08-R10 no se ha medido nada** -- *y lo digo antes de empezar.* **Lo que si hay, y es una pista mejor que un
modulo:**

**`core/diario.py:140` ya tiene escrita la regla central de `R08`:**

> *«**Rechaza `compra` a proposito.** **Comprar no es comer**: si una compra entrara aqui...»*

**Y `R08` dice, con otras palabras, exactamente lo mismo**: *«**compra no acredita consumo ni stock
restante**»* -- *comprar algo **no quiere decir** que se haya consumido, ni que quede, ni que no.*

**Es la misma disciplina que atraviesa toda la fase**: *`sin_precio` (un cero afirmaria que salio gratis),
`nombre_visto` (lo que no se sabe se dice), y ahora **una compra no es un consumo**.* **Y ya esta escrita, en
el diario, desde antes.**

### Y lo que NO hay, por lo que se ve

**Una busqueda de «despensa» y «stock» en `core`, `plataforma/api` y la pantalla devuelve ficheros que no son de
esto** -- *`alcance`, `cobertura`, `secciones`, `previa_compra`, `sellos`, `traspaso`* --, **y ninguno se llama
`despensa`.** *Pero **no lo cuento como «no existe» todavia**: eso exige mirarlo en las tres capas, y aqui solo
he mirado una.*

### Y los cuatro casos de la aceptacion, que son los que hay que ejercer

1. **consumo parcial** -- *se gasto parte de lo que habia*
2. **stock desconocido** -- *no se sabe cuanto queda, y hay que poder decirlo*
3. **unidades incompatibles** -- **el mismo problema que el `kg/g` de F10**, *y aqui vuelve*
4. **fecha ausente** -- *un producto sin caducidad conocida*

**Y el tercero es el que mas importa de los cuatro**, porque **ya se midio en F10 y esta fijado con
`xfail`**: *`previa_compra._unidad_canon` no usa `normalize._UNIDADES`, asi que `1 kg` y `500 g` no se suman.*
**Si la despensa descuenta existencias, va a necesitar exactamente la misma conversion** -- *y **la decision que
esta esperando el dueno** (guardar en la unidad que vino o en la canonica) **la necesita tambien este paquete**.*

**Asi que F11 no empieza de cero: empieza con una regla ya escrita (`diario.py:140`), un defecto ya medido
(`kg/g`), y una decision ya planteada -- que resulta que ** no era solo de F10.***

### Y la primera medida, que es un `SELECT`

**¿Existe una tabla de despensa?** *Es lo primero, y contesta `R08` entero: «existencias declaradas» **o no
existen**.* *Y despues, si existe: **¿la compra escribe en ella?*** -- *que es la pregunta de `R08`: «compra no
acredita consumo», **y hay que ver si la compra la toca.**


---

## 2. **La despensa no existe** -- y lo dicen cuatro capas

*(Ronda 126.)* La primera medida de F11, y **esta vez mire cuatro capas antes de decirlo** -- *que es la leccion
de las ocho veces en que concluí desde una.*

| capa | **lo que hay** |
|---|---|
| **la base de datos** | **13 tablas**: `alerta`, `compra`, `compra_linea`, `favorito`, `invitacion`, `invitaciones_vivas`, `lista`, `lista_acceso`, `lista_linea`, `preferencia`, `sesion`, `usuario`, `visita` -- **ninguna de despensa** |
| **la API** | **`plataforma/api/despensa.py` NO EXISTE** |
| **la pantalla** | *dos menciones de «stock», y las dos son **«Stock Fuera»*** -- *una **mecanica de cadena**: el producto no esta en la tienda.* **No es una despensa.** |
| **las preferencias** | **la tabla esta VACIA**, y el unico sitio que escribe es `main.py:1184` -- **una ruta generica donde el cliente manda la clave**. *Ningun codigo guarda una clave de despensa.* |

### Y la cuarta capa era la que habia que mirar

**`preferencia` es una tabla generica clave-valor** -- *asi que **una despensa podria vivir ahi** sin tabla
propia.* **Es exactamente el caso que me salvo en `C09`**: *alli el «presupuesto» no estaba en ninguna tabla, y
**tampoco** en el codigo; aqui, **tampoco.***

**Y no basta con que la tabla exista**: *hay que ver **si alguien escribe en ella**.* *El unico escritor es una
ruta generica, y **no hay ninguna clave de despensa en el codigo**.* **Con la tabla vacia, las dos cosas
concuerdan.**

### Y `R08` queda contestado entero, y en su primera mitad

**El criterio** (`SUPERAPP-COMPETENCIA-Y-REA.md:108`): *«**Existencias declaradas**, ubicacion/caducidad
**opcional**; **compra no acredita consumo ni stock restante**.»*

| la mitad de `R08` | **estado** |
|---|---|
| **«existencias declaradas»** | **NO EXISTEN** -- *no hay donde declararlas* |
| **«ubicacion/caducidad opcional»** | *no aplica: no hay existencias* |
| **«compra no acredita consumo ni stock restante»** | **se cumple por vacio** -- *no hay stock que acreditar* -- **y ademas esta escrito en el diario** (`diario.py:140`: *«Comprar no es comer»*) |

**Asi que `R08` es un hueco entero, y del tipo que ya conozco**: *no un defecto, sino **una funcion que nadie ha
escrito** -- como `R02` (importar) y `R05` (modo cocina).* **Van tres.**

### Y las otras dos, con lo que se ve

| criterio | **lo que se puede decir ya** |
|---|---|
| **`R09`** -- coste por racion | **hay piezas**: `cesta.coste_por_linea` (el coste de lo que se compra) y `previa_compra` (los envases **enteros**). **Y el criterio pide precisamente distinguirlas**: «**coste usado distinto de envases por comprar**». *Es la misma separacion que `compra.total_cent` contra la estimacion -- **por medir*** |
| **`R10`** -- buscar por lo disponible | **depende de `R08`**: *sin existencias no hay «disponibles» que explicar.* *Y su otra mitad -- «**sugerencia, no sustitucion automatica**» -- es la misma que `AvisoIdentidad` y que `F01`* |

**Asi que F11 son tres criterios y un solo hueco de fondo**: *sin despensa, `R10` no tiene de donde sacar los
«disponibles», y `R09` se queda en la mitad que ya existe.*
