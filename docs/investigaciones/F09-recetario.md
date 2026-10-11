# F09 -- Recetario completo y recuperacion de borradores (P1)

**Criterio, de `docs/SUPERAPP-FASE2-EMPEZAR-AQUI.md:137`:**

> Investigar R01-R04 con Paprika/Samsung Food. Busqueda y filtros utiles, favoritos/colecciones, editor, v[ersiones]...
> Raciones y cantidades reproducibles; **unidades incompatibles sin conversiones inventadas**. Recetas gener[icas]...
> **Aceptacion:** normal/error/**URL invalida**/**duplicado**/**borrador**/**versiones**/**aislamiento**; recetas de fixture p[ara pruebas]

**Y los cuatro criterios que cubre, de `docs/SUPERAPP-COMPETENCIA-Y-REA.md:101-104`:**

| ID | lo que pide |
|---|---|
| **R01** | *biblioteca/filtros* -- recetas propias, etiquetas, favoritos, busqueda y **vacio con filtros explicados** |
| **R02** | *importar receta* -- **URL/archivo de fuente permitida**; previa, **fuente, unidades y edicion antes de guardar** |
| **R03** | *editor/versiones* -- **borrador recuperable y version persistente**; diario antiguo permanece estable |
| **R04** | *raciones/unidades* -- **escalado reproducible**; **g/ml/ud no sumados por apariencia** |

---

## 1. Punto de partida: lo que hay, y lo que **no** se ha medido

**De R01-R04 no se ha medido nada en esta fase** -- *y lo digo antes de empezar, porque en esta fase he dado por
hecho lo contrario ocho veces.* **Lo que si se ha visto de pasada, y conviene anotar sin confundirlo con una
medicion:**

- **`core/recetas.py` existe**, y `plataforma/api/recetas.py` tiene una ruta base -- *`recetas.ruta_base()`, que
  aparece en `diario.py:78` al comprobar que una receta anotada existe de verdad.*
- **El diario comprueba la receta antes de guardarla** -- *`diario.py:75-94`: «la receta se comprueba ANTES de
  guardarla. Una version que no existe, o de otra persona, no se anota»* --, **y eso es `R03` visto desde el
  diario: la version importa**.
- **`cocina.ts:36` prohibe algo** -- *lo nombra `RecetaDetalle.tsx:228`: «identidad de G10*, y `cocina.ts:36`
  prohibe...»* -- *sin leer.*

**Asi que hay modulo, hay ruta base, y hay una comprobacion de version ya usada por el diario.** *Nada de eso es
una medicion de R01-R04: es **saber donde mirar**.*

### Y los siete casos de la aceptacion, que son lo que hay que probar

**La aceptacion no pide funciones: pide **siete casos**, y son los que hay que ejercer:**

1. **normal** -- *el camino que funciona*
2. **error** -- *algo que sale mal y se dice*
3. **URL invalida** -- *importar de una direccion que no vale*
4. **duplicado** -- *la misma receta dos veces*
5. **borrador** -- *lo que se empieza y no se termina*
6. **versiones** -- *editar una receta y que lo viejo siga*
7. **aislamiento** -- *que una receta de otra persona no se vea ni se pueda anotar*

**Y hay una octava linea que dice algo mas de lo que parece**: *«recetas de **fixture** para pruebas»*. *Es
decir: **la aceptacion pide que las pruebas no dependan de recetas de verdad de nadie** -- *que es la misma
regla que el encargo pone al principio, «preserva datos reales», y que en esta fase ha costado un incidente
(F03, ronda 50).*

### Y `R04` es el criterio que mas me interesa de los cuatro

**«Escalado reproducible; **g/ml/ud no sumados por apariencia**.»**

*«No sumados por apariencia» es una frase muy concreta: **100 g de harina y 100 ml de leche no son 200 de
nada**.* **Y es el mismo problema que F01 y F08 ya trataron con los formatos** -- *`parse_formato` normaliza
packs, unidades y pesos a una cantidad canonica* --, **pero al reves**: *alli habia que convertir para comparar
precios; **aqui hay que negarse a convertir cuando no se puede**.*

**Asi que `R04` se mide con la misma pregunta que F08**: *¿hay una funcion que decida si dos unidades se pueden
sumar, **y que se niegue cuando no**?* *Y en F08 la respuesta fue que **si**, con `_UNIDADES` y un factor
explicito. **Aqui hay que ver si la receta usa la misma** -- *o si suma por apariencia.*

**Es un `SELECT` sobre `core/recetas.py` y `core/normalize.py`, y va antes que cualquier pantalla.**


---

## 2. `R04`: **el escalado esta hecho y no suma nada** -- y la suma esta en F10

*(Ronda 116.)* El `SELECT` sobre `core/recetas.py`, que era lo primero que habia que mirar.

### El escalado, entero, en veinte lineas

```python
134  def escala(ingredientes: list[dict], de_raciones: int, a_raciones: int) -> list[dict]:
135      """Los ingredientes para `a_raciones` en vez de para `de_raciones`.
137      **Lo que no tiene cantidad, no la gana.** Un ingrediente anotado como "sal" sigue sin cantidad: la
138      regla de tres no se puede aplicar a lo que no se sabe, e inventarle un cero seria convertir un dato
139      que falta en un dato falso.
141      Se redondea a dos decimales, y sin miedo: media unidad de huevo es raro de leer pero es la verdad.
142      Redondear a 2 seria comodo y mentira; quien cocina decide, con el numero delante.
143      """
144      if de_raciones < 1 or a_raciones < 1:
145          raise ValueError("las raciones son al menos una")
146      factor = a_raciones / de_raciones
148      for uno in ingredientes:
150          cantidad = copia.get("cantidad")
151          if isinstance(cantidad, (int, float)):
152              copia["cantidad"] = round(cantidad * factor, 2)
```

**Las dos mitades del criterio, una por una:**

| lo que pide `R04` | **estado** |
|---|---|
| **«escalado reproducible»** | **si**: *una multiplicacion por el factor, redondeada a dos decimales -- **determinista**, y sin depender de nada mas* |
| **«lo que no tiene cantidad, no la gana»** | **si, y dicho**: *la sal sigue sin cantidad, porque **inventarle un cero seria convertir un dato que falta en un dato falso*** |
| **«g/ml/ud no sumados por apariencia»** | **aqui se cumple por no haber suma** -- *ver abajo* |

### Y el hallazgo que importa: **`escala` no suma, multiplica**

**«No sumados por apariencia» presupone que hay una suma.** *Y en `escala` **no la hay**: recorre los
ingredientes **de uno en uno** y multiplica cada cantidad por el factor.* **Asi que no puede sumar g con ml
porque no suma nada con nada.**

**La suma aparece **en otro sitio**: cuando el plan semanal se convierte en lista de la compra** -- *«Plan→lista:
seleccionar lo necesario, **consolidar compatibles** y mantener trazabilidad ingrediente-receta»*, que es
**F10** (`SUPERAPP-FASE2-EMPEZAR-AQUI.md:149`).*

> **Ahi es donde 100 g de harina de una receta y 200 g de harina de otra tienen que ser 300 g** -- *y donde
> 100 ml de leche y 100 g de mantequilla **no pueden ser 200 de nada**.*

**Asi que `R04` queda medido -- el escalado esta y esta bien --, y **la mitad que da miedo no es de este
paquete**: es de F10, y conviene decirlo para no darla por buena desde aqui.** *Es la misma trampa que F08 me
enseno a evitar: **la pieza existe en un sitio y el criterio se cumple en otro.***

### Y `R03` empieza a aparecer solo, y es fuerte

**El docstring del modulo, en sus tres primeras lineas:**

```
:3    **Privacidad, implementada.** Cada receta tiene propietario, y **todas** las operaciones lo exig[en]...
:11   **Lo historico, sin dueno, queda conservado e inaccesible.** La migracion anade la columna y dej[a]...
:15   **Cada version es autocontenida**: guarda sus raciones, su preparacion y sus ingredientes **copi[ados]**...
```

**Y las tres son `R03` y el aislamiento de la aceptacion:**

| lo que dice el modulo | **que criterio toca** |
|---|---|
| **«Privacidad, implementada. Cada receta tiene propietario, y todas las operaciones lo exigen»** | **`R03`/aislamiento** -- *el septimo caso de la aceptacion* |
| **«Lo historico, sin dueno, queda conservado e inaccesible»** | *una decision de migracion: **no se borra y no se ve*** |
| **«Cada version es autocontenida: guarda sus raciones, su preparacion y sus ingredientes copiados»** | **`R03`: «version persistente»** -- *una version no cambia porque cambie la receta* |

**Y hay funciones que lo dicen en su nombre**: `versiones()`, `actualizar()`, `archivar()`, y **`_de_quien(con,
propietario, receta_id)`** -- *que es el guardian de `R03`, y es una funcion de tres argumentos que **devuelve
`None` si no es tuya**.*

**Asi que `R03` tiene modulo, docstring y guardian.** *Falta **medirlo** -- el aislamiento de verdad, con dos
propietarios --, que es exactamente la prueba que F07 ya hizo para las listas (`test_fase2_f07_otro_hogar.py`) y
que aqui se puede copiar entera.*


---

## 3. `R03` y el aislamiento, **medidos y pasan** -- y un instrumento mio que medía la forma

*(Ronda 117.)* `tests/test_fase2_f09_recetario.py`, **nueve pruebas** contra un SQLite temporal -- *«recetas de
fixture», que es lo que la aceptacion pide, y sin tocar datos de nadie.*

### La afirmacion del modulo, probada entera

| lo que dice `core/recetas.py` | **la prueba** |
|---|---|
| *«Cada receta tiene propietario, y **todas** las operaciones lo exigen»* | **el dueno lee la suya y el de fuera no**; **no puede cambiarla**; **no puede archivarla** |
| *«`listar`»* | **y las listas no mezclan duenos** |
| *«Cada version es autocontenida»* | **una version no cambia porque cambie la receta** -- *v1 sigue diciendo «harina» despues de editar a «patata»* |
| *«version persistente»* | **las versiones crecen** (`[1]` -> `[1, 2]`) |
| *«todas las operaciones»* | **y las versiones de otro tampoco se ven** (`[]`) |

**Las nueve pasan.** *Y `R04` esta en las dos ultimas: el escalado no le inventa cantidad a la sal, y multiplica
sin sumar.*

### Y un instrumento mio que medía la forma y no el fondo

**La prueba del archivado estaba escrita asi:**

```python
with pytest.raises(Exception):
    recetas.archivar(con, "luis", mia)
```

**Y fallo: `DID NOT RAISE Exception`.** *A punto estuve de apuntar un defecto de aislamiento.*

**Y NO LO ERA.** *`archivar` no levanta **y tampoco borra**: su `WHERE` no casa ninguna fila, devuelve 0, y
**la receta de ana sigue ahi** -- que es **exactamente lo que se quiere**.*

**Lo que fallaba era mi asercion**: *pedia **una excepcion**, y lo que hay que pedir es **el efecto**.* **Es el
mismo error de la lista vacia que contaba como distinta, y del `ok` que pasaba con ocho encabezados que no eran
pasillos** -- *y van **cuatro** en esta fase.*

**Corregido, la prueba dice lo que quiere decir:**

```python
with contextlib.suppress(Exception):
    recetas.archivar(con, "luis", mia)
assert recetas.leer(con, "ana", mia) is not None, "**la de ana sigue ahi**"
```

**«No se exige que falle: se exige que no borre.»**

### Y dos formas mas que el modulo dijo, y mis pruebas no sabian

*Las dos las corrigio el propio error, no mi memoria:*

1. **El campo de un ingrediente es `texto`, no `nombre`** -- *«un ingrediente necesita al menos su texto»*. **Y
   trae `producto_id`, `grupo_id` y `fuente`** -- *que es **la trazabilidad ingrediente->catalogo** de `R02` y
   `R07`.*
2. **`crear` devuelve el id**, no un diccionario -- *lo dijo un `TypeError`.*

**Las dos son la misma cosa que me ha pasado toda la fase**: *escribir de memoria un nombre o una forma, y que
lo corrija **el error del programa** en vez de mi recuerdo. **Y por eso se corren las pruebas antes de
commitear** -- *que es lo que hace que ninguna de estas haya llegado al commit.*

### Y F09, con lo medido

| criterio | **estado** |
|---|---|
| **`R01`** -- biblioteca/filtros | *por medir* |
| **`R02`** -- importar receta | *por medir* |
| **`R03`** -- borrador y versiones | **medido y PASA**: aislamiento (3 pruebas), versiones persistentes (2), y `listar` sin mezclar |
| **`R04`** -- raciones/unidades | **medido y PASA**: escalado reproducible, sin inventar cantidades, **y sin sumar** |

**Dos de los cuatro, medidos y pasando; y los dos que faltan -- `R01` y `R02` -- son los que tienen que ver con
las pantallas y con traer recetas de fuera.**


---

## 4. `R02`: **importar recetas no existe** -- y esta vez lo dicen las tres capas

*(Ronda 118.)* El criterio (`SUPERAPP-COMPETENCIA-Y-REA.md:102`): *«**URL/archivo de fuente permitida**;
**previa, fuente, unidades y edicion antes de guardar**.»*

**Y despues de ocho veces en esta fase en que la respuesta estaba en otra capa, esta vez no**: *lo he mirado en
**tres** y las tres dicen lo mismo.*

| capa | lo que hay |
|---|---|
| **las rutas de la API** (`plataforma/api/recetas.py`) | `/plan` · `/{receta_id}` · `/{receta_id}/a-la-lista` · `/{receta_id}/versiones` · `PUT /{receta_id}` · `/{receta_id}/archivar` -- **ninguna ruta de importar** |
| **la pantalla** (`plataforma/web/app/src`) | **una** mencion de «importar»... **y es de CSS**: *«el pasillo se pegaria en `top: 0`»*. **No hay pantalla de importar.** |
| **el campo `fuente`** | existe -- `core/recetas.py:97`, `"fuente": uno.get("fuente")` --, **pero es del INGREDIENTE**, no de la receta: *dice de donde salio un ingrediente, no de donde se trajo la receta* |

**Asi que `R02` no esta implementado, y no es que falte una pieza: falta el camino entero** -- *traer una receta
de fuera, ensenarla **antes** de guardarla, y dejar editar unidades y texto.*

### Y por que esto es una buena noticia para el metodo

**En esta fase he concluido ocho veces que algo faltaba, y ocho veces estaba en otra capa.** *Esta es la
**primera** en que mirar tres capas **confirma** que falta.*

**La diferencia no es la suerte: es que las otras ocho veces **no mire las tres**.** *Mire una -- el `SELECT`,
el grep del resumen, el `lineas_de` -- y concluí.* **Aqui mire tres antes de decirlo, y por eso lo puedo decir.**

### Y lo que si hay, que conviene no perder

- **`GET /{receta_id}/a-la-lista` y `POST /{receta_id}/a-la-lista`** -- *que es **`R07`**: «Plan→lista»,*
  *«seleccionar lo necesario, consolidar compatibles y mantener trazabilidad ingrediente-receta»*.
  **Ya existe una ruta para eso**, y es de F10.
- **`PUT /{receta_id}`** -- *que es el editor.*
- **`GET /{receta_id}/versiones`** -- *que es `R03`, ya medido.*
- **Y los ingredientes llevan `producto_id`, `grupo_id` y `fuente`** -- *que **es** la trazabilidad
  ingrediente→receta→catálogo que `R02` y `R07` piden.* **El dato esta; lo que falta es el camino para
  meterlo desde fuera.**

### Y `R02` queda como lo que es: **un hueco con nombre, y con sus tres casos**

**La aceptacion nombra tres casos que son de este criterio**, y sin importar no existen:

| caso de la aceptacion | **que necesitaria** |
|---|---|
| **URL invalida** | *una comprobacion de **fuente permitida** -- que es literalmente lo que el criterio pide, y no hay* |
| **duplicado** | *traer dos veces la misma receta, y decidir que se hace* |
| **error** | *que la fuente no conteste, o conteste algo que no es una receta* |

**Los tres son casos **de importar**, y los tres estan sin poder probarse** -- *no porque fallen, sino porque
**no hay donde**.* **Es el unico criterio de F09 en ese estado, y conviene que se lea asi: no es un defecto, es
una funcion que nadie ha escrito.**


---

## 5. `R01`: **hecho, y con el mejor comentario de la fase**

*(Ronda 119.)* El criterio (`SUPERAPP-COMPETENCIA-Y-REA.md:101`): *«Recetas propias, **etiquetas, favoritos,
busqueda** y **vacio con filtros explicados**.»*

**Y despues de mirar la pagina equivocada** -- *`Cocina.tsx`, que es la de cocinar, no la del recetario* --, **el
recetario es `Recetario.tsx`, 303 lineas, y `logica/recetario.ts`, 125.** *Y ahi esta todo.*

### `Recetario.tsx`: los estados, dichos de si mismo

```
:1-9   «El recetario: la pantalla propia de Recetas.
       **El selector de version es lo importante de esta pantalla.** El recetario guarda versiones para que
       el diario pueda citar una y que no se mueva; pero eso, SIN PODER MIRARLO, ES UNA PROMESA. Con el
       selector, quien cocina puede comprobar que la version 1 sigue diciendo lo que decia...
       Estados de verdad: cargando, sin nada, y error con el motivo que da la API.
       UNA PANTALLA QUE SOLO SABE PINTAR EL CASO BUENO NO ESTA TERMINADA.»
```

**Y las dos cosas del criterio, en el codigo:**

| lo que pide `R01` | **donde esta** |
|---|---|
| **busqueda** | `Recetario.tsx:221`, `placeholder="Buscar por nombre..."` -- *y `:201` dice **«G12, punto 218: el buscador que faltaba»*** |
| **filtro por etiqueta** | `:229`, `aria-label="Filtrar por etiqueta"`, con `etiquetasDe(todas)` |
| **etiquetas** | *en el dato: `listar` devuelve `etiquetas`, y `logica/recetario.ts` las acepta **en dos formas** porque el servidor manda texto* |
| **favoritos** | *por medir* -- *no aparece en esta pantalla* |
| **vacio con filtros explicados** | **`textoDelVacio`**, importado en `:22` -- *y el tipo `Filtro` dice **que significa cada filtro*** (`«Vacio significa todo»`, `«Vacia o ausente significa todas»`) |
| **y el selector de version** | *que es `R03` **hecho visible**: «sin poder mirarlo, es una promesa»* |

### Y el comentario que dice lo que yo llevo 119 rondas aprendiendo

`logica/recetario.ts`, lineas 4 a 6:

> *«G12 pide en su 218 "biblioteca, **busqueda/filtros**, crear/editar/versionar/archivar", y el recetario tenia
> la biblioteca y no tenia buscador. **Es la primera funcion de interfaz que este encargo encuentra ausente --
> en once paquetes, todo lo demas estaba escrito.**»*

**Alguien, en una sesion anterior, encontro exactamente lo que yo llevo encontrando ocho veces** -- *y lo dijo
**mejor**: **«en once paquetes, todo lo demas estaba escrito»**.* **Es la misma conclusion, y ya estaba escrita
en el codigo, esperando a que alguien la leyera.**

### Y la decision del filtrado, que es de seguridad

`logica/recetario.ts:8-13`:

> *«**Se filtra en el cliente y no en el servidor, y eso es una decision, no una comodidad.** La lista que llega
> ya viene **filtrada por dueno** desde `recetas.listar(con, propietario)` -- que es la puerta del 223:
> "privadas por defecto" --, asi que **filtrar aqui no puede ensenar nada que no fuera tuyo**: lo que se esconde
> es un subconjunto de lo que ya te tocaba. **Hacerlo en el servidor anadiria un parametro mas que habria que
> recordar comprobar contra el dueno, y ese es justo el sitio donde un olvido se convierte en una fuga.**»*

**Es un argumento de **seguridad** para una decision de **interfaz*** -- *y es correcto: **cuantos menos sitios
donde haya que acordarse de comprobar el dueno, menos sitios donde olvidarlo**.* *Es la misma logica que
`_de_quien` y que `_acceso`: **la comprobacion, en un solo sitio**.*

### Y F09, con sus cuatro criterios

| criterio | **estado** |
|---|---|
| **`R01`** -- biblioteca/filtros | **hecho**: busqueda, filtro por etiqueta, estados (cargando/sin nada/error), **vacio explicado**, y el selector de version; *«favoritos» por medir* |
| **`R02`** -- importar receta | **NO EXISTE**, y lo dicen tres capas -- *es una funcion que nadie ha escrito* |
| **`R03`** -- borrador y versiones | **medido y PASA** (9 pruebas) |
| **`R04`** -- raciones/unidades | **medido y PASA** -- *y la mitad de la suma es de F10* |

**Tres de los cuatro, hechos o medidos; y el cuarto es un hueco con nombre.** *Y `R01` trae ademas **la respuesta
a la pregunta de esta fase**: **en once paquetes, todo lo demas estaba escrito.***


---

## 6. La suma que `R04` no cubre: **esta en `previa_compra`, y esta bien** -- `R07`, y es de F10

*(Ronda 120.)* **En la ronda 116 escribi** que la mitad de `R04` -- *«g/ml/ud no sumados por apariencia»* --
**no era de este paquete porque `escala` no suma.** *Y que estaba en «Plan→lista», que es F10.* **Lo he
seguido, y esta, y esta mejor de lo que esperaba.**

**El modulo es `core/previa_compra.py`, 145 lineas**, y **su docstring dice las tres reglas y por que:**

```
12  **Las tres reglas que aplica, y por que:**
14  1. **La consolidacion es por producto Y unidad.** *Dos lineas del mismo producto en kilos se suman;
15     una en kilos y otra en unidades **no**, y se dice por que.* **Sumar 1 kg con 2 unidades daria un
16     numero que no significa nada.**
17  2. **Lo que no tiene cantidad no se compra.** *Un ingrediente anotado como "sal" no se puede...*
21  3. **Los envases son enteros.** *Si hacen falta 1,4 kg y el envase es de 1 kg, hay que comprar 2.*
22     **Y el sobrante se dice**, porque es informacion util: *?te sobran 600 g?* no es un error...
```

**Y la regla 1, en el codigo, es literalmente el criterio:**

```python
53   sin_consolidar: list[str]     # el mismo producto en unidades incompatibles
89   # **La clave de la consolidacion: producto si lo hay, y si no el texto.** *La unidad va
90   # dentro: sumar kilos con unidades seria inventar.*
92   clave = f"{quien}|{unidad}"
105  # **Regla 1: lo que quedo en unidades incompatibles se nombra.** *No se suma ni se elige una.*
108  if len(unidades) > 1:
111      sin_consolidar.append(f"{nombre}: {' y '.join(sorted(unidades))}")
```

**«La unidad va dentro [de la clave]: sumar kilos con unidades seria inventar»** -- *que es **exactamente**
«g/ml/ud no sumados por apariencia», dicho de otra forma.* **Y lo que no se puede consolidar **se nombra con sus
dos unidades**, no se suma ni se elige una.**

### Y `R07` sale entero de aqui tambien

| lo que pide `R07` | **donde esta** |
|---|---|
| **«consolidar compatibles»** | **la clave `producto|unidad`**, y las tres reglas |
| **«elegir que transferir»** | *`Previa` con **lo comprable y lo que no**, y la ruta **`GET` que no escribe*** |
| **«rastrear receta de origen»** | *`de_donde=[texto]` en cada linea consolidada* |
| **«idempotencia»** | *«Repetir la misma transferencia no duplica»* (`:4`), y **la previa precede al `POST`** |

**Y hay una decision de diseno que vale la pena guardar** -- *`recetas.py:190-196`:*

> *«Y hace falta que exista [la previa]: el `POST` escribe, asi que **ensenar la previa antes de decidir exige
> un sitio que la calcule y no toque nada.** La consolidacion y los envases son logica de servido (Python), no
> de pantalla, asi que **no se duplica en el cliente**. **Y devuelve tambien lo que NO se puede comprar** -- lo
> que no tiene cantidad y lo que no se puede consolidar -- **con su motivo**. Es la mitad del valor de una
> previa: **saber que la sal no se compra porque no se sabe cuanto, en vez de ver una lista sin sal y no
> entender por que.**»*

**Es `R02`'s «previa… antes de guardar» y `R04`'s «no sumados», juntos, y con el motivo por el que la previa
tiene que ser una ruta aparte.** *Y la frase final -- **«en vez de ver una lista sin sal y no entender por
que»** -- es la regla de la casa entera, dicha en una linea.*

### Y el hilo de F09 a F10, ya cerrado

| criterio | **donde vive de verdad** | **estado** |
|---|---|---|
| **`R04`** | *el escalado, en `core/recetas.escala`* | **medido y PASA** |
| **`R04`**, la mitad de la suma | **`core/previa_compra`** -- *que es F10* | **hecho, con sus tres reglas y sus dos salidas** |
| **`R07`** | **el mismo modulo** | **hecho**: consolidar, elegir, rastrear, idempotencia |
| **`R02`**, la previa | *la ruta `GET /{id}/a-la-lista`, **que no escribe*** | **hecho** -- *lo que falta de `R02` es **traer de fuera**, no la previa* |

**Asi que la advertencia de la ronda 116 se cumple**: *la pieza estaba **en otro paquete**, y **estaba
hecha**.* *Y la encontre **siguiendola**, no suponiendola -- que es lo unico que ha funcionado en esta fase.*


---

## 7. **Medido**: `previa_compra` no distingue `kg/g` de `kg/ud` -- y la aceptacion si

*(Ronda 121.)* `tests/test_fase2_f10_previa_compra.py`, **siete pruebas**, y una sonda sobre los cuatro casos.
**El resultado, sin adornos:**

```
kg + kg   -> [('harina', 1.5, 'kg')]                        <- SUMA
kg + g    -> [('harina', 500, 'g'), ('harina', 1, 'kg')]    <- NO suma
             SIN CONSOLIDAR: ['harina: g y kg']             <- y lo DICE
kg + ud   -> SIN CONSOLIDAR: ['harina: kg y ud']            <- NO suma
ml + g    -> SIN CONSOLIDAR: ['leche: g y ml']              <- NO suma
```

### Y la aceptacion pide **distinguir** esos dos casos

**La aceptacion de F10 lo dice con dos palabras contrapuestas:**

> *«Aceptacion: dos recetas con ingrediente compartido, **mezcla kg/g compatible y ud incompatible**…»*

***«kg/g compatible» y «ud incompatible» estan puestos juntos a proposito*** -- *son **el caso que se puede
combinar** y **el que no**, y la prueba tiene que comprobar que el sistema los trata **distinto**.*

**Y `previa_compra` los trata igual**: *`1 kg` de harina y `500 g` de harina **son 1,5 kg de verdad**, y el
modulo los deja en dos lineas y los nombra como incompatibles, **igual que hace con `kg` y `ud`**.*

### Y lo que esto **no** es, que tambien hay que decirlo

**No es un dato mal sumado.** *El modulo **no inventa nada**: no suma, y **nombra** lo que no pudo consolidar
con sus dos unidades.* **Es la decision segura** -- *y es exactamente lo que su regla 1 dice que hace.*

**Asi que es un hueco, y es pequeno y esta bien definido:** *falta convertir `g` a `kg` **cuando la conversion
es de la misma magnitud*** -- *que es lo que `core/normalize._UNIDADES` ya sabe hacer, con su factor, y que aqui
**no se usa**.*

**Y el arreglo no seria inventar**: *`_unidad_canon` hoy solo pasa a minusculas y quita espacios -- y **podria
devolver tambien la cantidad convertida**, con la misma tabla que usa el catalogo para el precio por kg.*
**La pieza existe y esta a un import de distancia.**

### Y las otras tres reglas, que **si** pasan

| la regla | **la prueba** | |
|---|---|---|
| **misma unidad suma** | `kg` + `kg` = `1,5 kg` | **pasa** |
| **2: lo que no tiene cantidad no se compra** | *la `sal` no sale en `lineas` y **sale en `sin_cantidad`*** | **pasa** |
| **sin unidad tampoco** | *«3 de que» -- **se dice, no se supone*** | **pasa** |
| **3: los envases son enteros, y el sobrante se dice** | *`envases`, `tamano_envase`, `sobrante`* | *por medir -- necesita el catalogo* |
| **y la previa **no escribe nada** | *misma entrada, misma salida, y la entrada **no se modifica*** | **pasa** |

**Cuatro de cinco, y la que falla es la que el criterio nombra con dos palabras.**

### Y F10, con lo medido

| criterio | **estado** |
|---|---|
| **`R05`** -- modo cocina | *por medir* |
| **`R06`** -- calendario y cola | *por medir* -- *hay `planificar`/`plan`/`quitar_del_plan`* |
| **`R07`** -- plan→lista | **el modulo esta, y cuatro de sus cinco reglas pasan**; **falta la conversion kg/g** |
| **y `R04`** -- la mitad de la suma | *la misma pieza: lo que falta es convertir, no sumar mal* |

**Y el hueco tiene nombre**: *`previa_compra._unidad_canon` no usa `core/normalize._UNIDADES`, asi que `g` y `kg`
son dos unidades distintas en vez de dos formas de decir la misma.*
