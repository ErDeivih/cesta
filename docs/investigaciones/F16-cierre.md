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
| **privacidad** | `_acceso` (403/404), el aislamiento de recetas (9 pruebas), y `core/diario.py` -- *«quien tiene permiso de solo mirar no puede sacar de aqui lo que hay dentro»* |
| **identidad/costes** | `core/identidad.py` (GTIN validado, cuarentena), y **el pack resuelto** (`parse_formato`) |
| **registro** | la clave de operacion, la version obligatoria, y `fuente_dato` con `raise` |
| **publicacion** | `prueba_f03_publicacion.py` **PASA**: 19,81 -> 20,81 EUR con el alta en el diario |
| **recuperacion** | **la mitad sin medir**: *los reintentos estan (clave de operacion); **lo de offline no**, y es F15* |

**Asi que F16 se puede escribir, y su veredicto va a ser honesto en el sentido que el encargo pide**: *no «todo
bien», sino **que se puede hacer hoy, que no, y por que** -- con la diferencia entre **no esta porque nadie lo ha
escrito** y **no esta porque la fuente no lo da**.*


---

## Las cuatro funciones que no existian: **cerradas, con lo que se midio en cada una**

*(Rondas 158-212. **Es el tramo que `F16` dejo apuntado como «lo que falta», y ya no falta.**)*

### 1. La paginacion del buscador -- **hecha**

*Tres lineas*: un `desplazamiento`, un `OFFSET ?` y su argumento. **Y destapo un defecto de verdad**: *`buscar`
ordena por `comparable DESC, cadenas DESC, min_unidad` **sin desempate**, asi que **la misma llamada devolvio
`[20378, ...]` una vez y `[10645, ...]` otra*** -- *y **sin orden total, paginar baraja***. **Fijado con `xfail`; es
la **cuarta decision** del dueno.*

### 2. `R05`, el modo cocina -- **cerrado de arriba abajo**

| la capa | **el resultado** |
|---|---|
| **la logica** | *`core/cocina.py`, **10 pruebas** -- y la decision escrita: **un temporizador no es una cuenta atras, es una hora de fin*** |
| **la tabla** | *migracion `018`: **`paso` nullable** y **los instantes en `jsonb`*** |
| **la ruta** | *5 endpoints; **`200` veinte de veinte*** |
| **la pantalla, con conexion** | ***tres de tres pintan, y el reloj encadena `29:59 -> 29:48 -> 29:37` en tres paginas independientes*** |
| **la pantalla, sin conexion** | ***`1785 -> 1774` con la red cortada*** |

**Las cinco, medidas.** *Y las dos ultimas son las que importan: **el numero no vive en la pantalla** -- *si viviera,
tres cargas habrian dado `30:00` las tres* --, **y tampoco necesita al servidor para seguir bajando.**

### 3. `R08`, la despensa -- **las cinco capas medidas**

*Logica (9 pruebas, los cuatro casos), tabla (`017`), ruta (`404 -> 401 -> 201`), **pantalla** (**«no se sabe
cuanto» esta en pantalla**), y **la lista se conserva al perder la conexion**.* **Y la regla del criterio sostenida en
las cinco**: *«compra no acredita consumo ni stock restante»* -- **no hay ninguna funcion que sume una compra, ninguna
ruta, ninguna clave ajena y ningun boton.**

### 4. `R02`, importar recetas -- **cinco piezas, y le falta una decision**

*La fuente permitida (7 pruebas), el borrador (la previa que **no escribe**), el lector (`ld+json`, 6 pruebas), la
ruta (verificada) y **la pantalla, vista con y sin conexion**.* **Lo unico que falta es la lista de fuentes** -- *la
quinta decision*.

### Y lo que costo, dicho sin adornos

**Catorce rondas (§6 a §21 de `F10`) para el modo cocina, y **dos causas de dos mundos distintos**: *una **del
ensayo** (`CESTA_API` sin poner: Vite proxya al `8000`, donde no habia nadie) y otra **del producto**
(`refetchInterval`), **mas una tercera que solo aparecio al arreglar las dos** (el tic de un segundo).*

**Y lo que las separo, al final, fue repetir el mismo ensayo tres veces** -- *no razonar sobre el.*

---

## Las cinco puertas, y el ensayo integral del 12 de octubre de 2026 a las 13:11

```
1) uv run ruff check . --output-format=concise       ->  All checks passed!            (0)
2) CESTA_POSTGRES=...5434... uv run pytest -q        ->  1842 passed, 5 xfailed        (0 fallan)
3) cd plataforma/web/app; npm test                   ->  46 tests, 46 pass, 0 fail    (0)
4) npx --no-install tsc --noEmit                     ->  0
5) npm run build                                     ->  built in 6.67s                (0)
```

**La tercera es nueva, y lleva ahi todo el tiempo**: *`npm test` corre **`node --test` sobre funciones puras de
`.ts`**, y **es la unica puerta que cubre el TypeScript de la interfaz**.* **Es la que permitio medir el tope de
espera cuando el navegador no podia** -- *cuatro ensayos intentaron bloquear `/api` desde el navegador, **y los
cuatro se quedaron en que abortar una peticion deja la aplicacion sin montar**: `#raiz` con **cero hijos**, y **sin
error de JavaScript**.*

---

## El veredicto honesto sobre uso domestico local

**Lo que se puede decir, porque esta medido:**

- **Compra, recetas y calorias funcionan**, con las cinco puertas en verde y **las tres funciones nuevas verificadas
  de punta a punta** -- *incluido el comportamiento **sin conexion**, que es lo que un movil en una cocina
  necesita.*
- **La nutricion tiene la cobertura que tiene**: **22,8 %** (11 064 de 48 606 grupos con `kcal_100g`), *y **los
  fichas** -- 72 319 pendientes -- **no se arreglan con codigo**.*
- **Dos cadenas no estan**: *Alcampo y Aldi, **0 productos**.* *Y de los 39 794 grupos que no se pueden arreglar,
  **25 896 no tienen EAN** y **13 898 tienen un EAN que OFF no conoce**.*

**Lo que no se puede decir, y por eso se calla:** *que esto sustituya a hacer la compra en una tienda.* *Lo que hay
es **una herramienta domestica que estima, compara y recuerda** -- *y **cada una de esas tres cosas tiene su limite
medido**, escrito y con su cifra.*

**Y las cinco cosas que **no** dependen de mas codigo, sino de una persona:**

1. **Que es «presupuesto»** -- *la estimacion, lo pagado, o un numero que se ponga quien lo usa.*
2. **El coste de desplazarse** -- *no se puede deducir de los datos.*
3. **La unidad de la linea de compra** -- *la que vino o la canonica.*
4. **El desempate del buscador** -- un cambio de una linea, *y cambia lo que ve quien ya lo usa.*
5. **De que sitios se puede importar una receta** -- *y cada sitio que se declare **hay que mirarlo**.*

**Las cinco estan en el tablero, con su coste escrito.** *Ninguna es un descuido: **son decisiones sobre que quiere
quien usa esto**, y **no se contestan mirando el codigo**.*
