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


---

## 3. `R09`: **hecho, y con la mejor explicacion de la fase** -- coste usado contra envases

*(Ronda 127.)* El criterio (`SUPERAPP-COMPETENCIA-Y-REA.md:109`): *«**Coste usado distinto de envases por
comprar**; cobertura/ambito/version.»* **Y esta hecho, en `plataforma/web/app/src/logica/costeReceta.ts`, 138
lineas.**

### El modulo se explica solo, y explica el criterio

```typescript
1   /** Lo que cuesta una receta: **lo que usas y lo que hay que comprar, y no son lo mismo**.
3   *  G05 lo pide en Recetas: *«nutricion por racion y coste estimado, **distinguiendo cantidad usada de
4   *  coste de comprar envases**; **indicar ingredientes sin datos**»*.
6   *  **El caso que da sentido al modulo**: la receta dice «200 g de arroz» y el catalogo vende «1 kg por
7   *  1,20 EUR». **Lo que usas cuesta 0,24 EUR; lo que compras cuesta 1,20 EUR.** Los dos numeros son ciertos
8   *  y significan cosas distintas -- *lo que cuesta hacer el plato, y lo que sale de tu bolsillo hoy* --,
9   *  y dar uno solo como «el coste de la receta» es **elegir por quien lee sin decírselo**.
11  *  **Y el caso que no se puede prorratear**: «2 huevos». *Un huevo no tiene fraccion: o compras el envase
12  *  o no lo compras.* Ahi `costeUsadoCent` **es** el del envase, y decir otra cosa seria **inventar una
13  *  fraccion de huevo**.
16  *  ...**los ingredientes sin datos se cuentan y se nombran**, porque **un total sobre la mitad de los
17  *  ingredientes no es el total**.
18  */
```

**Las tres cosas que el criterio pide, una por una:**

| lo que pide `R09` | **donde esta** |
|---|---|
| **«coste usado distinto de envases por comprar»** | **`CosteDeReceta` con sus dos numeros** -- *`costeUsadoCent` y el del envase --, y la linea 9 dice por que no se juntan* |
| **«cobertura»** | **`{valor, faltantes}`** -- *«los ingredientes sin datos **se cuentan y se nombran**»* |
| **«ambito/version»** | *los precios vienen del catalogo, y `RecetaDetalle.tsx:256` lo pinta sobre la receta **versionada*** |

### Y el modulo contesta, de paso, la pregunta del pack de F08

**`costeReceta.ts:11-13` trata exactamente el caso que en F08 me dejo dudando** -- *«2 huevos»:*

> *«Un huevo **no tiene fraccion**: o compras el envase o no lo compras. Ahi `costeUsadoCent` **es** el del
> envase, **y decir otra cosa seria inventar una fraccion de huevo**.»*

**Es la misma regla que `parse_formato`** (*la cantidad es el total*) **y la misma que `previa_compra`** (*la
unidad va en la clave*) -- **y aqui esta dicha en una linea**: *lo que no se puede partir **no se parte**.*

**Y el caso `ud` esta en el tipo, no en un comentario**: *`unidadEnvase?: string | null` con **«En `ud` no se
prorratea»*** (`:27`). **La regla esta en la firma.**

### Y hay pruebas, y estan en el sitio correcto

```
plataforma/web/app/tests/cocina.test.mjs:189   // --- G05: el coste de una receta -- lo que usas y lo que...
plataforma/web/app/tests/cocina.test.mjs:192   const r = costeDeReceta([
```

**`node --test`, y el modulo esta escrito **sin dependencias** precisamente para eso**: *«nada de `api/`, para
que `node --test` lo cargue y **las reglas se prueben en un segundo**»* (`:15-16`).

### Y F11, con lo medido

| criterio | **estado** |
|---|---|
| **`R08`** -- despensa | **NO EXISTE** -- *cuatro capas; `R08` no tiene su primera mitad* |
| **`R09`** -- coste por racion | **HECHO**, con los dos numeros, la cobertura por `faltantes`, y la regla de `ud` **en la firma** |
| **`R10`** -- buscar por lo disponible | **depende de `R08`**: *sin existencias no hay disponibles*; *su mitad de «sugerencia, no sustitucion» es la de `AvisoIdentidad`* |

**Uno hecho, uno que no existe, y el tercero colgando del que no existe.** *Y el que esta hecho es el que
**no** necesitaba la despensa, que era exactamente por donde habia que empezar.*
