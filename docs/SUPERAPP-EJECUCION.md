# SUPERAPP · Tablero de ejecución

Objetivo y paquetes: [`SUPERAPP-GOAL-CONTINUACION-2026-10-11.md`](SUPERAPP-GOAL-CONTINUACION-2026-10-11.md).
Estado vivo y resumen vigente: [`SUPERAPP-ESTADO.md`](SUPERAPP-ESTADO.md).

Estados permitidos por paquete: `pendiente` · `en curso` · `implementado sin ensayo real` ·
`verificado` · `limitado por fuente` · `bloqueado`. **«Verificado» exige su criterio de aceptación
completo, no una compilación.**

## Tablero

| Paquete | Estado | Evidencia | Siguiente acción |
|---|---|---|---|
| G01 Diario efectivo | **`cerrado`** | recorrido medido en 390 y 1440 | **G02: texto libre útil en la lista** |
| G02 Texto libre | `pendiente` | — | línea sin producto, «Pendiente de identificar» |
| G03 Revocación exacta | `pendiente` | — | fixture de tres líneas, medir la pulsada |
| G04 Dos recorridos | `en curso` | — | depende de G01–G03 |
| G05 Gráficas | `pendiente` | — | depende de G01 para nutrición |
| G06 Acabado de las tres apps | `pendiente` | — | puede avanzar por pantallas |
| G07 Publicación diaria | `pendiente` | — | auditar `publicacion.publicar()` dentro del pipeline |
| G08 Fichas completas | `pendiente` | — | inventario por cadena |
| G09 Lidl integrado | `pendiente` | — | `run.py:ORDEN` sin Lidl |
| G10 Identidad exacta | `pendiente` | — | banco estratificado |
| G11 Oráculo de coste | `pendiente` | — | enumeración exhaustiva independiente |
| G12 Recetas | `pendiente` | — | versiones y escalado por ración |
| G13 Operación y privacidad | `pendiente` | — | copia/restauración probada en destino |
| G14 Aprendizaje y aceptación | `pendiente` | — | cierre tras los demás |

## G01 — Diario: registrar, persistir y explicar lo conocido

**Estado: `en curso`.** Ficheros: `plataforma/web/app/src/paginas/Diario.tsx`,
`src/api/diario.ts`, `plataforma/api/diario.py`, `core/diario.py`, puente en `api/cesta.py` y
`plataforma/prueba_navegador.py`.

### Hecho, con evidencia

| Qué | Evidencia | Fecha |
|---|---|---|
| Aceptación del **almacén**: números exactos, cobertura 1/2 y 2/2, dos comidas iguales, cero publicado, negativos/NaN/infinito, comida inválida, y aislamiento A/B incluido el borrado cruzado | `tests/test_g01_diario_aceptacion.py` — **11 pasan** | 11 oct 2026 |
| El cliente **devuelve el recibo** del servidor (`{id, dia}` / `{entrada}`) en vez de `undefined`, y los tres tipos están declarados | `src/api/diario.ts` | 11 oct 2026 |
| **Las tendencias se invalidan**: `useApuntar`, `useApuntarDesdeFicha` y `useBorrarEntrada` invalidan `['diario']` **y** `['diario-rango']` | `src/api/diario.ts` | 11 oct 2026 |
| `npm run tipos` limpio tras el cambio | `npx tsc --noEmit` | 11 oct 2026 |
| **La aceptación por HTTP montado**: recibo `{id, dia}`, cantidad y macros que se vuelven a leer, cobertura 1/2 y 2/2, el rango viendo el alta, negativos/compra/receta inventada rechazados, dos comidas iguales y el borrado con recibo | `tests/test_g01_diario_http.py` — **10 pasan** (1,9 s) | 11 oct 2026 |
| **El formulario**: `Alta` ofrece **cantidad (g)** y los **tres macronutrientes**, con la aclaración de que lo apuntado es lo comido y no los valores de 100 g; vacío es `null` (no `0`) y la coma decimal se acepta | `src/paginas/Diario.tsx` — `aNumero()` | 11 oct 2026 |
| **Al guardar se limpia solo lo guardado**: si el alta falla, el error se ve y no se borra lo escrito | `src/paginas/Diario.tsx` | 11 oct 2026 |
| **El puente compra→diario consume el recibo** (`{anotadas, ya_estaban, ajenas, sin_nutricion}`, tipado) y lo cuenta en pantalla; **invalida `['diario-rango']`**; y **solo usa la lista de casa**, sin elegir otra en silencio | `src/paginas/Diario.tsx`, `src/api/cesta.ts` — `npm run tipos` limpio | 11 oct 2026 |
| `tsc` cazó un comentario sin abrir en el primer intento y se corrigió antes de nada | `npx tsc --noEmit` | 11 oct 2026 |
| **`sin_nutricion` se rellena**: el puente anota sin nutrición y **ahora lo dice**, que era la mitad que faltaba de su propia promesa. *Medido: `sin_nutricion: []` mientras la entrada no llevaba un solo nutriente, y el fichero lo enseñaba* | `plataforma/api/main.py` — arreglo | 11 oct 2026 |
| **Las tres pruebas del recibo contra el almacén real**: las cuatro claves, `anotadas + ya_estaban == 1`, **la segunda vez no anota y lo dice**, una línea ajena **se devuelve en `ajenas`**, y **el recibo y el día dicen lo mismo sobre la nutrición** | `tests/test_g01_recibo_del_puente.py` — **3 pasan** (5,8 s, con `CESTA_POSTGRES` al 5434) | 11 oct 2026 |
| **El diario real, comprobado intacto** (mtime 10-10 13:44) tras sospechar que un ensayo lo había tocado | `data/diario.sqlite` | 11 oct 2026 |
| **Idempotencia por operación, en el almacén y el contrato**: `clave_operacion` opcional, índice único **parcial** por dueño+clave, y repetirla devuelve **la entrada que ya hay** | `core/diario.py`, `plataforma/api/diario.py` — 4 pruebas | 11 oct 2026 |
| Que **dos operaciones distintas con lo mismo son dos**, que **sin clave se comporta como antes**, y que **la clave no cruza entre personas** | `tests/test_g01_diario_aceptacion.py` — **15 pasan** | 11 oct 2026 |
| **La columna `unidad` ya existía** en el esquema del diario: desbloquea el caso `ml`/`g` sin migración nueva | `core/diario.py:47` | 11 oct 2026 |
| **El formulario manda la clave**: `crypto.randomUUID()` **al enviar**, dentro de `datos` — *así un reintento de la misma operación la repite, y el alta siguiente genera otra* | `src/paginas/Diario.tsx`, `src/api/diario.ts` — `tsc` limpio | 11 oct 2026 |
| **La idempotencia, por HTTP montado**: la misma clave dos veces devuelve **el mismo `id`** y una sola entrada; dos claves distintas, dos entradas | `tests/test_g01_diario_http.py` — **12 pasan** | 11 oct 2026 |

**Lo que ya existía y se conserva**: `tests/test_de_la_ficha_al_diario.py` (la cuenta de la ficha y
lo ausente-frente-a-cero) y `POST /api/diario/desde-ficha` con `gramos` + valores por 100 g, que
hace la cuenta **en el servidor**.

### Pendiente, y por qué

### G01, cerrado: el recorrido, medido en los dos anchos

| aceptación | resultado |
|---|---|
| alta desde el formulario, con cantidad y los tres macronutrientes | ✓ **250 kcal, sin recargar** (`POST /diario` 201) |
| lectura y aritmética del día | ✓ 300 + 300 = **600 kcal** |
| persistencia tras recarga | ✓ en 390 y en 1440 |
| **repintado en vivo del alta y del borrado** | ✓ **los dos, tras el arreglo de abajo** |
| borrado | ✓ **el día baja y la otra entrada sigue** (`DELETE` 200) |
| cobertura y aviso de parcial | ✓ «de 1 de 2 entradas… falta el dato de 1 entrada» |
| idempotencia por operación | ✓ almacén, contrato, HTTP y cliente |
| aislamiento entre cuentas | ✓ 401 anónimo; B no ve, no borra y no enumera |

**El defecto que cerró el paquete, y era mío**: `api/diario.ts:conCuerpo` leía el cuerpo **dos veces**
(`respuesta.json()` y luego `respuesta.text()`), y la segunda lanza `body used already` **después de
que el servidor ya hizo su trabajo**. Rompía **las tres mutaciones del diario** —alta, borrado y desde
ficha— y explicaba los tres síntomas que perseguí cinco rondas: la entrada que solo aparecía al
recargar, el `refetchQueries` que no repintaba (*`onSuccess` no corría nunca*) y el borrado que «no
enviaba petición». Lo introduje yo al hacer que `conCuerpo` devolviera el recibo. **Una sola lectura,
y los tres desaparecen.**

### G02, primera mitad: la línea puede no tener destino (esquema y servidor)

**La idea**: `linea_con_destino` **protegía la comparación y prohibía la lista**. Quien no encontraba
el producto no podía apuntarlo y acababa apuntándolo en otro sitio. La migración **014** la sustituye
por `linea_con_nombre`: *la línea existe, se lee, y se identifica después*. Mientras no tenga destino
se presenta como **«Pendiente de identificar»**, **no entra en ninguna comparación** y **no se le
inventa precio ni importe** -- sus importes quedan NULL, que es la verdad. **`favorito` no se toca**:
un favorito es, por definición, un producto del catálogo.

| | |
|---|---|
| migración `014`, **repetible** | ✓ `DROP CONSTRAINT IF EXISTS` + `ADD`, y dos arranques seguidos dan lo mismo |
| la línea con solo nombre | ✓ **201**, `grupo_id`/`producto_id` NULL, **`precio_cent` e `importe_cent` NULL** |
| sigue en la lista y se lee | ✓ |
| el nombre en blanco | ✓ **422**, no un 500 |
| la línea del catálogo | ✓ sin cambios |

**Tres cosas que costaron rondas, y las tres eran mías**:

1. **La columna se llama `nombre_visto`, no `nombre`.** El contrato de entrada la llama `nombre`; el
   almacén la guarda `nombre_visto` («lo que se vio escrito»). Usé el nombre de la API en la migración
   → `UndefinedColumn`; y **volví a usarlo en tres aserciones** → `assert None == 'Papel de cocina'`
   *con la línea creada y correcta delante*. **La migración no se aplicó a medias** porque van en
   transacción: `linea_con_destino` seguía puesta y la base quedó intacta.
2. **La migración no era repetible.** Solo tenía el `ADD`, y el **segundo** arranque del almacén
   moría con `DuplicateObject`. *O sea: reiniciar la API dos veces la mataba.* Lo cazó arrancar el
   almacén **una vez por módulo** — con un arranque por prueba era invisible.
3. **El nombre en blanco salía como 500.** La restricción nueva lo corta, pero llegar al INSERT es
   «el servidor ha fallado», que es mentira: es una petición mal formada. Ahora es **422**.

**La mitad visible**: en `Cesta.tsx`, junto al nombre, **«Pendiente de identificar»** cuando la
linea no tiene grupo ni producto. *No es un adorno*: esa linea **no tiene precio, no entra en ninguna
comparacion**, y lo unico que se puede hacer con ella es identificarla -- que es el enlace a la
busqueda que ya tiene al lado (`Cesta.tsx:474`). La pantalla no puede hacer que parezca un producto.

**Pendiente de verificar en el navegador**: que la etiqueta se vea y que la linea quede **fuera de los
totales con precio**. *Implementado y compilado, no recorrido.*

### G02, cerrado: la línea sin destino, medida en pantalla

| aceptación | resultado |
|---|---|
| migración `014`, repetible, en la base real | ✓ |
| la línea con solo nombre | ✓ 201, **sin destino y sin precio ni importe** |
| **apuntada en la lista de casa** | ✓ 201 |
| **«Pendiente de identificar» en pantalla** | ✓ **390 y 1440** |
| **la línea no lleva precio** | ✓ **verificado en su propia fila, en los dos anchos** |
| nombre en blanco → 422 · segunda lista de casa → 409 | ✓ **1.580 pruebas** |
| `favorito` | ✓ no se toca, con el motivo escrito |

**Y dos conclusiones mías que eran falsas, dichas para que no se repitan**:

1. *«En `/compra/listas` la línea no aparece»* -- **falso**. Aparece, debajo del resumen: comprobé
   **220 caracteres** de la pantalla y saqué una conclusión. El texto entero tiene 3.131.
2. *«Las listas son un `DIV` sin enlace: no se pueden abrir»* -- **tampoco**. No hay enlace porque
   **la lista se pinta en esa misma página**: no hay a dónde navegar. El `DIV` no era el defecto;
   *era mi lectura.*

### G03: la revocación, medida por línea

**Lo que el documento pedía, literal**: *«Fixture con al menos tres líneas: dos alternativas
autorizadas y una exacta. Identificar la línea por ID estable. Verificar respuesta, almacenamiento y
pantalla: solo ella pierde. Recargar y comparar los tres estados.»* Y la corrección de la revisión:
***«un contador global de alternativas no acredita esto»***.

**La revocación ya existía** —`almacen.autoriza_linea(..., autorizado=False)`, que *confirma o
desconfirma* **una** línea y devuelve su `id`—, y el diagnóstico del documento ya lo decía: *función
existente, falta una medición*.

| | |
|---|---|
| **tres líneas**: dos alternativas autorizadas y una exacta | ✓ la fixture se monta y las dos quedan con su producto y su cadena |
| la revocada pierde la autorización | ✓ |
| **las otras dos quedan exactamente igual** | ✓ **es lo que un contador no dice** |
| la respuesta **nombra el `id`** revocado | ✓ |
| un identificador que no es de esa lista no cambia nada | ✓ |
| el estado se relee de la base y dice lo mismo | ✓ |

**Tres cosas que costaron rondas, y las tres eran mías:**

1. **Los parámetros del endpoint van en la dirección, no en el cuerpo** (`autorizado`, `producto`,
   `cadena` son `Query`, `main.py:1217`). Mandé un JSON y recibí un 400 que **parecía** del dato:
   *«para autorizar hay que decir QUE producto se acepta»*.
2. **`autorizacion_de` devuelve un mapa de diccionarios, no de booleanos** —`{id: {"autorizado",
   "producto", "cadena"}}`— **y su anotación dice `dict[str, bool]`, o sea que miente.** Anotado, sin
   tocar la firma para no mezclarlo con este arreglo.
3. **Mi script de edición volvió a perder el trabajo entero**: abortó en la comprobación **séptima**
   después de aplicar seis, y *escribe el fichero al final*. **Es el mismo defecto que diagnostiqué en
   la ronda 8.** Ahora **verifica todas las anclas antes de escribir**, y así entró a la primera.

### G03, cerrado: la revocación por línea, y la pantalla medida por precio y por id

**La aceptación, en los dos anchos y con dos líneas distintas**:

    MOVIL 390  · tortilla (fila de DIA 2,60)     → cambiadas: 1 · ¿solo esa?: True
               · la suya: aut=False, cad=None · las otras 3 aceptadas · tras recargar: aguanta
    1440       · rustique (fila de Alcampo 8,72) → cambiadas: 1 · ¿solo esa?: True
               · la suya: aut=False, cad=None · las otras 2 aceptadas · tras recargar: aguanta

**`cambiadas == [esa]`** falla si cambian dos y falla si no cambia ninguna. *Es la afirmación que el
documento pedía —**«un contador global no acredita esto»**— y la única que no puede pasar por
accidente.*

**El control, por su nombre y su línea**: `RepartoEnTiendas.tsx:138` **«Aceptar el de {cadena}»** y
`:148` **«Volver al mío»**. *No se llama «Revocar» ni «Autorizar», y por eso no lo encontré buscando
esas palabras durante once rondas.*

**Y cómo se atribuye un botón a su línea cuando la pantalla no lo dice**: **por el precio**. *La fila
de la tortilla lleva DIA 2,60 · Aldi 2,99 · Alcampo 5,18 · Carrefour 5,95, y el rustique Alcampo 8,72:
**los mismos números que medí del catálogo en otra ronda y por otra vía**.* Cuando el nombre no
atribuye —el contenedor del botón envuelve sólo los botones de tienda— **el precio sí**.

**Las tres puertas, medidas**: estimación (`_total_autorizado`, filtrando por `Eleccion.autorizada`),
reparto (`_es_la_confirmada`), y cierre (`coste_por_linea`, que **no archiva sustitutos**: *no hay nada
que revocar en esa puerta*).

**Y una nota que va a G10**: **una línea movida puede tener la autorización puesta y no tiene botón
para quitarla** —*no tiene fila de reparto, así que no hay control*—. *No es un defecto grave: el
cierre la archiva sin precio y la pantalla la señala. Pero es un estado alcanzable sin salida visible.*

### G04, punto 1: el catalogo fijo de ensayo, publicado por el mecanismo de verdad

**Se usa el mecanismo real, no un doble.** `core/publicacion.py` publica por versiones: todos los
ficheros en `data/gold/v<sello>/`, y el puntero (`actual.json`) se mueve con `os.replace` **solo cuando
estan todos**. Una version incompleta no se publica; las anteriores no se borran. *Sustituirlo mediria
mi doble, no el sistema.*

**Y el aislamiento no depende de la disciplina**: `GOLD` y `PUNTERO` son constantes de modulo, asi que
apuntarlas a un temporal deja **todo** el mecanismo --carpetas, puntero atomico, completitud,
rollback-- funcionando contra el ensayo, sin tocar el catalogo que sirve el producto. *Hoy importa mas
que nunca: esta manana se publico la version **`20261011-124542`** mientras se trabajaba en esto, y el
tablero decia `20261010-142831`.*

**El contenido es del ensayo y se declara como tal**: un producto, **dos cadenas** (DIA 150 con
promocion, Alcampo 220 sin ella), los siete nutrientes por 100 g, la promocion con su texto, y las
cinco cadenas en `promos_por_cadena`. **Nada viene del catalogo real**: *si viniera, el ensayo mediria
el dia en que se ejecuta.*

| comprobado | |
|---|---|
| sin publicar: `version_actual()` es `None` y se lee el catalogo suelto | ✓ *el fallback, medido* |
| publicar V1 mueve el puntero y deja los **seis** ficheros | ✓ |
| `rutas()` devuelve los seis caminos **bajo la carpeta de la version** | ✓ |
| y lo que se lee **es el ensayo**, no los 51.609 productos reales | ✓ **2 filas, DIA y Alcampo** |

**Y `enlaces` quedo entendido leyendolo**: `i` y `j` son **indices de fila de `grupos`** (`i` llega a
50.855 con 51.609 filas; la fila `i=0` coincide), los pares van ordenados, y los niveles son
`identico`, `equivalente` y `ean`. *Era lo unico que estaba afirmando por deduccion.*

### G04, puntos 2 y 3: V1→V2 durante el uso, y la version fijada por peticion

| comprobado | |
|---|---|
| publicar **V2** mueve el puntero y `versiones()` tiene las dos | ✓ |
| **publicar no borra**: las dos carpetas conservan sus seis ficheros | ✓ |
| **se sirve la V2** -- el precio de DIA pasa de 150 a 120 -- y **lo que no cambio no cambia** (Alcampo 220) | ✓ |
| **la V1 se sigue leyendo por su sello** (150), no la sobrescribe la V2 | ✓ |
| `rutas(V1)` da los **seis caminos de UNA version**, no una mezcla | ✓ *la politica de version explicita del punto 3* |
| **rollback**: escribir el puntero atras sirve la V1 con sus datos, **y la V2 queda intacta** | ✓ |

**Y una nota de metodo**: `ruff --fix` me quito `import json` cuando no se usaba, y dejo de estar cuando
empece a usarlo. *El lint no se equivoca; el que cambia de idea soy yo.*

### G04, punto 4 (mecanismo): error de publicacion y desaparicion de candidato

| comprobado | |
|---|---|
| publicar con **un fichero de menos** lanza `PublicacionIncompleta` | ✓ |
| **el puntero NO se mueve** y se sigue sirviendo la V1 **entera** | ✓ |
| **la carpeta a medias se retira**: no queda una version fantasma con cinco ficheros | ✓ |
| **`fijar()` rechaza una version incompleta**, y el puntero no se mueve | ✓ *el rollback no sirve mezclas* |
| **desaparicion de candidato**: una V2 sin Alcampo deja **una** fila (DIA) | ✓ |
| **y la V1 sigue con las dos** -- no se reescribe lo publicado | ✓ |

**Y una correccion**: mi prueba de rollback de la ronda anterior **escribia el puntero a mano**
(`PUNTERO.write_text`) cuando `fijar()` existe, hace lo mismo **y ademas rechaza una version
incompleta**. *Pasaba igual, pero medía mi escritura en vez de la funcion.* Ahora usa `fijar()`.

**Lo que falta de G04 es el recorrido de usuario** -- *«buscar, abrir ficha, preparar compra/consumo,
publicar V2»* -- y su parte de aplicacion: **el fixture publica contra un `GOLD` temporal, y la API
sigue leyendo el suyo**, asi que el recorrido con el catalogo cambiando debajo **no esta recorrido**.

### G04, el recorrido: **la aplicacion lee el catalogo de ensayo**

**La palanca es `AJUSTES.gold`, no `publicacion.GOLD`** -- *son dos constantes en dos modulos, y la
aplicacion usa la segunda*. La API lee **DuckDB sobre los parquet de `AJUSTES.gold`** (`catalogo.py:1`)
y **deriva `buscable` de ellos en cada conexion**, asi que el ensayo es **una sola cosa que apuntar**.
Y `Ajustes` esta **congelado** (`FrozenInstanceError`), asi que se entra por `object.__setattr__`.

**Y un hecho del proyecto que sale de aqui**: **el mecanismo de publicacion por versiones existe, esta
probado, y la aplicacion todavia no lee versiones.** *Lo dice el propio modulo: «sin version publicada
se lee el catalogo suelto de siempre (fallback conservador): asi esto entra sin romper nada y se puede
adoptar cuando convenga»*. **Es una pieza preparada y aun no adoptada** -- anotado, no es un defecto.

| comprobado | |
|---|---|
| con `AJUSTES.gold` en el ensayo, la busqueda devuelve **mi** producto | ✓ **y no los 51.609 reales** |
| **`buscar` devuelve PRODUCTOS, no filas de cadena** | ✓ *una fila; los precios por cadena salen de la ficha* |
| **la ficha** (`catalogo.grupo`) da los precios **por cadena** | ✓ `{dia: 150, alcampo: 220}` |
| publicar **V2** cambia **uno** y no el otro | ✓ **`{dia: 120, alcampo: 220}`** |
| `catalogo.reiniciar()` es lo que hace releer | ✓ *la conexion se cachea por el `mtime` de `grupos.parquet`* |
| y las dos versiones siguen publicadas | ✓ |

**Y dos aserciones mias que estaban mal, dichas para que no se repitan**: di por hecho que la busqueda
devuelve una fila **por cadena** -- devuelve **un producto** -- y me construi un diccionario por
`nombre`, que como los dos nombres son iguales **se quedo con uno y ocultaba el resultado**. *El
codigo hacia lo sensato; el que no lo entendia era yo.*

### G04, la ultima clausula: **lo ya hecho se mantiene**

**El catalogo de ensayo Y el almacen de verdad**, cada uno en su sitio: el catalogo en un temporal, las
listas en el PostgreSQL desechable. *El diario real y las compras reales no se tocan.*

| comprobado | |
|---|---|
| se cierra una compra con el producto del ensayo | ✓ |
| **se publica V2 con el precio cambiado** | ✓ *DIA 150 -> 120, y `catalogo.reiniciar()`* |
| **la compra cerrada CONSERVA su precio** | ✓ **la linea archivada sigue en el mismo valor** |
| y **la lista sigue viva**, para poder seguir comprando | ✓ |

**Por que esto es lo que hace que una compra sirva de algo**: `almacen.lineas_de_compra` guarda la
compra **con sus precios** --*gold se reescribe cada dia*--, asi que **recalcularla con los precios de
hoy seria explicar una compra de ayer con los datos de hoy**. *Es la misma razon por la que existe la
columna `importe_cent` de la migracion 013.*

**Y con esto, los cuatro puntos de G04 estan medidos a nivel de servidor.** Lo que queda es **el
recorrido de interfaz** --*punto 2: «buscar, abrir ficha, preparar compra/consumo, publicar V2»*--, que
es donde el catalogo cambia **debajo de una pantalla**.

### G04, el recorrido de interfaz: **lo que se midio y el defecto que queda**

**Medido, con el ensayo servido por la aplicacion viva** (verificado por los dos lados: encuentra
«Barrita de ensayo» y «leche» devuelve CERO, o sea que no lee el catalogo real):

| paso del punto 2 | estado |
|---|---|
| **buscar** | ✓ **funciona**: encuentra el producto del ensayo, dice «2 cadenas», «ahorras 46,7 %», «datos del 1 ene 2026» |
| **abrir ficha** | ✗ **no carga**: se queda en «Cargando el grupo…» |
| preparar compra, publicar V2, medir lo conservado | **no recorrido** -- bloqueado por lo anterior |

**El defecto, diagnosticado hasta el limite**: `/compra/comparar/:grupoId` no termina de cargar. Lo
medido, uno por uno:

- **el parametro llega bien**: `grupoId=900001`, `Number.isFinite(id)=true`, y `enabled` se cumple;
- **la consulta se lanza** y su reintento tambien: `pide('/grupo/900001')` **se llama dos veces**;
- **la peticion sale, el servidor contesta 200** y `pide` **devuelve un objeto**: hay `fetch-hecho 200` y
  `cuerpo object`, dos veces;
- **la senal de React Query llega viva** (`senal viva tipo=object`), no abortada;
- **y la entrada de la consulta no registra nada**: `dataUpdatedAt: 0`, `isFetched: false`,
  `data: undefined`, con `status: 'pending'` y `fetchStatus: 'fetching'` para siempre.

*Es decir: `queryFn` resuelve y la consulta no lo guarda.* **El codigo de `useGrupo`, la version
instalada (`@tanstack/react-query` 5.103.2) y el patron --identico en `useBuscar`, `useSecciones` y
`useProducto`, que si cargan-- estan leidos y son correctos.** Queda como **defecto abierto y acotado**,
no como duda: *la firma esta arriba y se reproduce recargando.*

**Y el defecto de producto que hay debajo, que si es accionable**: **una consulta que no resuelve y una
que esta cargando se pintan igual.** `Grupo.tsx` ahora distingue el caso `isPending && fetchStatus ===
'idle'` (una consulta cancelada no esta cargando nada) y lo dice; **el caso de esta ficha
(`fetchStatus: 'fetching'` sin dato ni error) sigue esperando en silencio**, y eso no se puede
distinguir desde fuera de la biblioteca sin un tiempo de espera.

### G05, primeros hallazgos: **la chispa dibujaba precios que nadie midio**

`Chispa.tsx` -- el componente que el documento nombra **por su nombre** -- incumplia **tres requisitos
de G05, dos de ellos citados literalmente**:

| antes | y G05 dice |
|---|---|
| **`spanGaps: true`** | *«no conectar datos ausentes como si hubiera observaciones»* -- **la linea recta entre dos puntos afirmaba un precio no observado** |
| **«Sin historico: solo tenemos un dia de este precio»**, dicho **de una serie vacia** | *«no inferir "solo un dia" de una serie vacia»* -- *y `Producto.tsx:87` devuelve `puntos: []` como caso legitimo, asi que se decia en pantalla sin saberlo* |
| **`aMs` devolvia `0`** para una fecha ilegible | *«no convertir ausencias en cero»* -- **1970 es el origen del eje, y arrastraba la escala** |

**Arreglado, y con la decision fuera del componente**: `logica/chispa.ts` es puro -- sin uPlot y sin DOM
-- y devuelve `{xs, ys, total, dibujados, sinFecha, dibujable}`. **Lleva la cobertura en la forma que el
proyecto ya usa en `estado/cocina.ts` (`{valor, faltantes}`)**: *cuantos puntos se dibujan y cuantos se
quedaron fuera, porque sin eso un hueco y una ausencia se ven igual.*

**Cuatro pruebas nuevas, y las seis de antes siguen pasando** (10/10 en el cliente):

- **un hueco NO se conecta**: `ys = [100, null, 120]`, y el hueco **cuenta como punto**;
- **una serie vacia NO dice «un dia»**: `dibujable: false`;
- **una fecha ilegible se descarta y SE CUENTA** (`sinFecha`), no se coloca en 1970;
- **un valor no finito es un hueco, no un cero**.

**Y una nota de metodo**: `node --test` **importa `.ts` directamente** (Node 24 quita los tipos), asi que
la logica del cliente se puede probar sin navegador -- *y el proyecto ya tenia ahi una prueba con este
mismo principio: «subtotal no convierte ausencias en ceros conocidos».*

**Falta de G05**: la **tabla accesible de los mismos datos** que pide la aceptacion, y el resto de los
ocho puntos (evolucion por tienda, alternativas, gasto pagado, reparto, inflacion; y en Calorias y
Recetas, cobertura por nutriente y coste distinguiendo cantidad usada de envase).

### G05: la tabla accesible, con los huecos dentro -- y una prueba que me paró

**La aceptacion pide «tabla accesible de los mismos datos», y aqui «los mismos» incluye lo que no
hay**: una tabla que omitiera las fechas sin precio haria **invisible justo el hueco que la chispa ha
dejado de tapar** al no conectar los puntos. `filasDeChispa` vive en `logica/chispa.ts` -- puro y
probado -- y devuelve `{fecha, valor, texto}`: **el hueco es una fila con `valor: null` y texto «sin
dato»**, nunca 0 ni vacio. El `<details>` lleva su `<table>`, `caption` para lectores de pantalla y
cifras tabuladas, y **el resumen y el `aria-label` dicen cuantos dias no tienen dato**.

**Once pruebas en el cliente** (10 + la de la tabla).

**Y una prueba me paro, con razon.** `test_ui_movil.py:435` -- *«Nada de `<summary>` sueltos»* -- cayo
en cuanto escribi uno a mano:

    E  AssertionError: hay desplegables escritos a mano, y esos no llevan flecha:
       ['Chispa.tsx: <summary className="cursor-pointer text-xs text-tinta…']

**Su motivo esta documentado y es una linea de CSS que no se ve**: el triangulo que el navegador pinta
en un `<summary>` **desaparece en cuanto se le pone `display: flex`**, que es justo lo que hace falta
para que mida los 44 px de pulsar. Por eso los diez desplegables de la aplicacion se pintan con
`Resumen` (`componentes/ui.tsx`), que pone la flecha. *Y el comentario de la prueba dice como se
encontro: **mirando una captura, no leyendo el codigo**.* **Se cambia a `Resumen` y las cuatro puertas
pasan.** *Es la suite haciendo su trabajo sobre codigo mio equivocado, que es lo que debe pasar.*

### G05, segundo punto de Compra: **la chispa era la unica pieza que ignoraba la unidad**

G05: *«Separar precio del envase y precio unitario normalizado; **no una sola linea mezclando €/kg y
€/l**»*. Y el sistema **ya sabia** que `kg` y `ud` no se comparan:

- **`api/alertas.py`**: *«si la unidad cambio, no es una bajada»*;
- **`logica/curva.ts`**: *«tres dias en `kg` y uno en `ud` son dos series pegadas, y el minimo de las
  dos juntas no es el minimo de nada»* -- y **se niega a afirmar un minimo**, con un mensaje redactado;
- **`tipos.ts:173`**: `PuntoSerie` lleva **la unidad de ESE dia**, asi que dentro de una serie puede
  cambiar.

**Y la chispa recibia `{fecha, valor}` y dibujaba una sola linea con todo** -- *las dos llamadas
(`Grupo.tsx:475`, `Producto.tsx:93`) dejaban la unidad fuera*. **No era un desconocimiento repartido:
era un sitio al que no le habia llegado la regla.**

**Arreglado con el mismo criterio y las MISMAS PALABRAS que `curva.ts`** -- *dos mensajes distintos
para el mismo hecho acaban discrepando, que es lo que el propio proyecto dice en `cliente.ts`*:
`PuntoChispa` gana `unidad`; `serieDeChispa` devuelve `unidades` y `motivoUnidad`, y **con dos unidades
`dibujable: false`**; los dos consumidores pasan `s.unidad_canon`.

**Cuatro pruebas nuevas** (15 en el cliente): `[kg, kg, ud]` **no** se dibuja y lo dice; `[kg, kg]` si;
**sin unidad se dibuja** --*la API puede no mandarla y eso no puede romper nada*--; y **un punto
descartado por fecha no decide que la serie mezcla**.

### G05, el gasto pagado: **la regla primero, porque es donde el numero miente**

**La pagina se llama «Gasto y ahorro» y no tenia gasto.** Sus diez secciones son del catalogo (que
entro por cadena, precios movidos, dispersion, letras de calidad, indice), y **el gasto no se sumaba en
ningun sitio**: `importe_cent` -- la columna de la migracion 013, que G03 midio -- **no aparecia en
ninguna suma, ni en el servidor ni en el cliente**. *El dato estaba y nadie lo usaba.*

**Y el dato es alcanzable**: `GET /api/listas/{lista_id}/compras` devuelve las compras cerradas con sus
lineas y sus importes, **incluidos los `NULL` de las lineas movidas**.

**`core/gasto.py`**, con la regla que da sentido al modulo: **un importe que falta no es un cero.**

- `total_cent` suma **solo las lineas con importe**, y se acompana de **cuantas entraron y cuantas no**;
- **un periodo sin ninguna linea con importe tiene `total_cent = None`, no `0`** -- *no es que se
  gastara cero; es que no se sabe*;
- **`completo` es `False` en cuanto falta una**, aunque el total sea grande y creible;
- **un `0` explicito SI es un importe conocido** (algo que salio gratis), y no cobertura que falta;
- agrupa por **la fecha de la compra**, no la del precio -- *recalcular una compra de ayer con los
  precios de hoy seria explicar lo que paso con datos que no existian*;
- y **una linea sin fecha no se coloca en el periodo de hoy**: se cuenta aparte y se declara.

**Ocho pruebas, en 0,29 s.** La que da sentido a todo: *sin ningun importe, `total_cent is None`.*

*Es la misma distincion que `{valor, faltantes}` en `estado/cocina.ts` y la columna «Recortados» del
indice: el dato que falta se declara. Y en dinero importa mas, porque un `NULL` sumado como cero da un
numero redondo, mas bajo de lo real, y nada en la pantalla lo delata.*

### G05, el gasto: **el endpoint sirve, y el caso que da sentido al modulo sale del servidor**

**Medido de punta a punta**, con dos compras cerradas de verdad en la base desechable y el ensayo
servido:

    A) 3 lineas, 2 de ellas sin precio  ->  cierre: total_cent 150        (las que si lo tenian)
    B) 1 linea, sin ningun precio       ->  cierre: total_cent 0          <-- el cierre GUARDA 0

    /api/listas/{id}/gasto?periodo=mes
      A: total_cent 150   compras 1  completo false
      B: total_cent null  compras 1  completo false      <--✓✓✓ ¡null, y no el 0 que se guardo!
      semana: 2026-W41    total_cent 150

**Lo importante de esa medida**: el cierre archiva `total_cent: 0` para una compra en la que **ninguna**
linea tenia precio, **y `gasto_de_compras` se niega a leerlo como un cero** -- lo detecta por
`sin_precio >= lineas`. *La regla ha hecho su trabajo sobre un dato que el propio sistema habia guardado
mal: es el caso que da sentido al modulo, y sale del servidor.*

**Y `completo: false` con `total_cent: 150`** en A: *el numero esta y se dice que no esta completo*, que
es la mitad de lo que G05 pide.

| endpoint | |
|---|---|
| `GET /api/listas/{id}/gasto?periodo=mes\|semana` | ✓ **sirve**; `periodo=dia` da **422** |
| `total_cent` cuando no hay ningun importe conocido | ✓ **`null`, nunca `0`** |
| `completo` con una compra incompleta | ✓ **`false`** |
| cobertura | ✓ **`compras`, `con_importe`, `sin_importe` y `lineas_sin_precio`** -- *el numero de LINEAS, no solo el de compras* |

**Lo que falta**: la **seccion en pantalla** (`/compra/analisis`), con el total y su cobertura al lado y
`null` dicho como que no se sabe. *El endpoint ya devuelve todo lo que necesita.*

### G05: la regla del gasto en la pantalla, **y un import que no debia estar**

`logica/gasto.ts` decide que se puede decir de un periodo: `totalConocido`, `importeEnCentimos`,
`textoDeLoQueFalta` y `textoDePeriodo`. **Y `null` no es `0`**: *un «0,00 €» se lee «ese mes no gaste
nada», y lo que pasa es que no se sabe* -- el numero sale mas bajo de lo real, redondo y creible.

**La primera version importaba `numero` de `api/formato`, y con eso el fichero de pruebas del cliente
NO LLEGABA NI A CARGAR** (`pass 0, fail 1`). *El formato de un numero no es logica de negocio: ahora el
modulo devuelve **el numero y su condicion**, y el «150,00 €» lo compone quien pinta.* Es la misma
disciplina que `logica/chispa.ts`, que **no importa nada** y por eso se prueba en un segundo.

**Y queda anotado un hallazgo de la misma clase**: `logica/curva.ts` **si** importa `api/formato`, asi
que **su regla de negocio -- la de la unidad, que es la que se nego a afirmar un minimo -- hoy no se
puede probar sin montar el navegador**. *Deberia poder, y es el mismo arreglo.*

**Cinco pruebas nuevas (20 en el cliente)**: sin total conocido no es un cero; un cero sabido si lo es y
no avisa de nada; un total parcial se dice **con** lo que le falta; el singular de una linea; y el
periodo legible, incluida la fila sin periodo.

### G05, el gasto: **la seccion, en pantalla** -- el punto, cerrado

`componentes/LoQueHasPagado.tsx`, montado **el primero** en `/compra/analisis`. *La pagina se llama
«Gasto y ahorro» y hasta hoy no tenia gasto: sus diez secciones eran del catalogo.*

- **el gasto es de la lista de casa**, que es la que tiene compras -- *la misma regla que el puente del
  diario* --, y sale de `useGasto(listaId, periodo)`;
- **conmutador mes / semana**, porque G05 pide «semanal/mensual» y los dos estan medidos;
- **la tabla la pinta `TablaScroll`**, con `caption` y `etiqueta` en cada celda: *es donde se lee, y es
  la tabla accesible de los mismos datos que G05 pide para cada grafica*;
- **y las dos mitades juntas, nunca una sin la otra**: el total **y** «faltan N lineas sin precio» en la
  misma fila. *Un total parcial sin su aviso es una mentira por omision; un aviso sin el total no
  informa.*
- **`null` se dice «No se sabe»** y nunca «0,00 €»: *un cero se lee «ese mes no gaste nada», y el numero
  sale mas bajo de lo real, redondo y creible.*

*El total lo suma el servidor (`core/gasto.py`, puro y probado); la decision de que se puede decir vive
en `logica/gasto.ts` (puro y probado, 5 pruebas); **el componente solo compone**.*

**Y con esto, el punto del gasto pagado de G05 queda cerrado**: regla, endpoint, cobertura de lineas,
medida de punta a punta, regla de presentacion y seccion en pantalla.

### G05, el coste de una receta: **lo que usas y lo que compras no son lo mismo**

**El coste no existia.** `estado/cocina.ts` son 38 lineas: tipos, validacion, nutricion y lista de la
compra -- y **`Ingrediente` no tiene ningun campo de precio**. El modelo de coste que si existe
(`cesta.py:_coste_para`) es para **unidades**, con promociones, no para gramos de una receta.

**Y la distincion que G05 pide es esta**: la receta dice «200 g de arroz» y el catalogo vende «1 kg por
1,20 EUR». **Lo que usas cuesta 0,24 EUR; lo que compras cuesta 1,20 EUR.** Los dos son ciertos y
significan cosas distintas -- *lo que cuesta hacer el plato, y lo que sale de tu bolsillo hoy* --, y dar
uno solo como «el coste de la receta» es elegir por quien lee sin decírselo.

`logica/costeReceta.ts`, **puro y sin imports** (como `chispa.ts` y `gasto.ts`: `node --test` lo carga
y las reglas se prueban en un segundo), devuelve por ingrediente **`costeUsadoCent` y `costeEnvaseCent`**,
y por receta los dos totales **con su cobertura**: `conDatos`, `sinDatos` (con nombres) y `completo`.

| caso | lo que hace |
|---|---|
| **200 g de un paquete de 1 kg a 1,20 EUR** | ✓ **usado 24, envase 120** |
| **«2 huevos»** | ✓ **usado = envase**: *un huevo no tiene fraccion, y decir 35 centimos seria inventarsela* |
| **se sabe el envase pero no cuanto trae** | ✓ **usado `null` con su motivo**, envase 350 -- y el total de lo usado **no es 0: no se sabe** |
| **sin precio** | ✓ **se cuenta y se nombra** en `sinDatos`, y `completo: false` |
| **nada conocido** | ✓ **los dos totales `null`**, no cero |
| **€/unidad del catalogo** | ✓ manda, y el envase se sigue diciendo |

**Seis pruebas nuevas (26 en el cliente).** *Falta la pantalla de la receta.*

### G05, el coste en la pantalla: **y la respuesta honesta hoy es «no se puede calcular»**

`RecetaDetalle.tsx` gana una tarjeta **«Lo que cuesta»** con los dos numeros que G05 pide -- *usando lo
que dice la receta, y comprando los envases enteros* -- **y con lo que falta dicho por su nombre**.

**Y hoy el resultado es «no se puede calcular todavía», y es correcto.** *El ingrediente de una receta
tiene nombre, cantidad y nutrientes, y **ningun `producto_id`**: no hay precio que aplicar.* Enlazarlo
**es el problema de identidad de G10**, y `cocina.ts:36` prohibe la salida facil -- *«no fusionar por
parecido de nombre: no demuestra que sean el mismo ingrediente»* --. Asi que el coste **no se inventa**:

- **no se pinta un «0,00 EUR»**, que se leeria como «esta receta es gratis»;
- se dice **«no se puede calcular todavía»** en los dos numeros;
- y se **nombran los ingredientes sin precio**, con el motivo: *los precios salen del catalogo y cada
  ingrediente tiene que estar enlazado; emparejarlos por el nombre no vale.*

**Lo que si esta verificado**: `/api/buscar` **ya devuelve `precio_cent`, `precio_unidad_cent` y
`unidad`** -- *los tres que el modulo necesita* --, y el escalado de raciones lo hace el servidor. *Asi
que cuando G10 traiga el enlace, esta tarjeta calcula los dos numeros sin tocar `logica/costeReceta.ts`.*

### G05, el reparto: **cuatro de cinco exigencias ya estaban, y la quinta era una frase**

El reparto de la lista por tiendas cumple **cuatro de las cinco** cosas que G05 pide, y lo dice en su
propia cabecera -- *«tres decisiones de esta pantalla, y las tres son de dinero»*:

| G05 pide | y estaba |
|---|---|
| **contra que se compara** | ✓ *«al lado va lo que costaria sin decidir nada (todo en la mas barata, o repartido en dos). Ensenar solo el total propio no deja comparar»* |
| **restricciones de ofertas** | ✓ *«las ofertas se ensenan desglosadas: el total con ofertas, el total sin ellas y la lista de las que se aplican»* |
| **cuantas lineas entran** | ✓ **`sin_precio` en `RepartoTiendas`**, junto a `lineas` y `decididas` -- y `cesta.py:387` manda `lineas_contadas` |
| **ahorro medido contra algo comprable** | ✓ *`cesta.py:514`: «el ahorro se mediria contra un total que no se puede comprar»* -- **se niega a calcularlo** |
| **y si falta transporte** | ✗ **`transporte` no aparecia en NINGUNA parte del proyecto** |

**La quinta, arreglada.** `logica/transporte.ts`, **puro y sin imports** (29 pruebas en el cliente), con
la frase que dice lo que el total no incluye: *«el total no incluye el transporte ni el tiempo: es lo que
cuesta la compra, no el viaje»*, **y con mas de una tienda lo nombra** -- *«con 2 tiendas hay 2 viajes, y
el ahorro puede ser menor que el segundo viaje»* --. Montado **dentro de la tarjeta del reparto**, antes
de los numeros.

*El problema no era de calculo -- la cuenta estaba bien -- sino de contexto: **el reparto comparaba dos
tiendas como si llegar a las dos costara lo mismo que llegar a una.** Y la frase se decide en una funcion
pura, no en el texto de la pantalla, porque «comparar dos tiendas sin decir que son dos viajes» tiene que
estar cubierto por una prueba.*

**Y «óptimo» no aparece en ninguna parte del proyecto**: G05 pide no llamar optimo a una heuristica, y
**el proyecto no llama optimo a nada** -- *«exacto» se reserva para lo que tiene GTIN, como dice
`identidad.py:219`*.

### G06, los dos recorridos: **cero errores, y un rotulo ambiguo**

**Los dos recorridos que G06 pide** -- *primera cuenta sin datos y cuenta con historial* -- **hechos, en
390 y 1440, con cero errores de pagina en los dos anchos**, y **79 capturas** en `data/debug/capturas/`.

**La cuenta nueva**: las cuatro pantallas dicen que no hay nada, **dicen que hacer a continuacion**, y
**no muestran ceros** -- *`/calorias` dice **«sin dato»** en los cuatro nutrientes y «de 0 de 0
entradas»; un «0 kcal» habria dicho «hoy no comiste nada»* --. Y las tendencias llevan la frase escrita
para quien lee: *«Medido sobre lo anotado y lo que se sabe. No es todo lo que comiste.»*

**Las tres apps estan diferenciadas** (punto 156): Compra tiene «Buscar / Listas (10) / 10 por coger en
la lista de casa / Favoritos / Gasto y ahorro»; Recetas, «Mi recetario / Plan semanal»; Calorias, «Mi
diario / Mis alimentos / Tendencias».

**La frontera Compra/Calorias** (punto 154): `BotonAnadirACesta.tsx` **no menciona nutricion ni una
vez**; la ficha de producto si lleva la tabla de nutricion, **y G06 la pide** («ingredientes/nutricion
cuando existe»); y el `SelloNutriscore` del buscador es **una etiqueta impresa en el envase**, no un
recuento dentro de una accion.

**Y un hallazgo, del punto 157** -- *«mensajes ambiguos»* --: **`Panel.tsx` titulaba «La ingesta de hoy»
una seccion que habla del CATALOGO** -- *«hoy N productos, y lo normal M», con alarmas de caida* --.
**«Ingesta» significa dos cosas** y ahi solo vale una: *dentro de «Gasto y ahorro» se leia como «lo que
has comido hoy», que es justo la confusion entre Compra y Calorias que hay que evitar.* **Corregido:
«Lo que entro hoy en el catalogo»**, con la nota al lado, y el `etiqueta` de la tabla tambien.

**Y mi propio desorden, cuantificado y limpiado**: la base desechable tenia **399 listas, 396 de
pruebas mias** -- *«Prueba texto libre» 130 veces, «Prueba G03 cierre» 90* --. Borradas **preguntando el
esquema primero** (`lista_linea`, y el orden que dictan las claves foraneas), **conservando «Casa» con
sus 12 lineas y su compra cerrada** y la «Sonda de ruta». *Quedan 3 listas.*

### G06, entregable: **la lista priorizada de mejoras visuales, VACIA y con su evidencia**

G06 pide *«una lista priorizada de mejoras visuales con capturas antes/después de la aplicacion real»*.
**La lista sale vacia**, y no por no haber buscado: **porque las tres mejoras que propuse resultaron
estar ya hechas**, y las tres cayeron por el mismo metodo.

| propuse | y la verdad |
|---|---|
| **plegar las listas de `/compra/listas`** | ya es un `<select>` (`Cesta.tsx:1370`) |
| **agrupar las doce secciones de `/compra/analisis`** | ya es un conmutador: `{activa === 'hoy' && <Hoy />}` (`Panel.tsx:139`) |
| **subir el puente en `/calorias`** | *«De la compra al diario»* ya va antes del detalle |

**Las tres veces medi el TEXTO que pinta la pagina y de ahi deduje como estaba construida.** *Los
12.000 caracteres, los doce rotulos y el orden eran medidas correctas; las conclusiones, inventadas.*
**El texto de una pagina no dice como esta ordenada.**

**Lo que sostiene la lista vacia, y no es una impresion:**

- **dos recorridos completos** -- primera cuenta sin datos y cuenta con historial -- **en 390 y 1440**,
  con **cero errores de pagina** en los dos anchos, y **79 capturas** en `data/debug/capturas/`;
- **los cuatro estados vacios dicen que no hay nada Y que hacer a continuacion**, y **ninguno muestra
  un cero**: *`/calorias` dice **«sin dato»** en los cuatro nutrientes y «de 0 de 0 entradas»*; un
  «0 kcal» habria dicho «hoy no comiste nada»;
- **las tres apps estan diferenciadas** (punto 156): Compra *«Buscar / Listas / Favoritos / Gasto y
  ahorro»*, Recetas *«Mi recetario / Plan semanal»*, Calorias *«Mi diario / Mis alimentos / Tendencias»*;
- **la frontera Compra/Calorias se sostiene** (punto 154): `BotonAnadirACesta.tsx` **no menciona
  nutricion ni una vez**, y la ficha de producto si lleva la tabla **porque G06 la pide**.

**Y un hallazgo real, corregido** (punto 157, mensajes ambiguos): `Panel.tsx` titulaba **«La ingesta de
hoy»** una seccion que habla del **catalogo** -- *«hoy N productos, y lo normal M», con alarmas de
caida* --. **«Ingesta» significa dos cosas** y ahi solo vale una: *dentro de «Gasto y ahorro» se leia
como «lo que has comido hoy»*, que es justo la confusion que hay que evitar. **Corregido a «Lo que
entro hoy en el catalogo»**, con la nota al lado y el `etiqueta` de la tabla tambien.

**Antes/despues**: existe par real **donde hubo captura** -- *la tarjeta de gasto vacia (ronda 158)
frente a con datos (161), y el rotulo viejo en `analisis-movil.png`* --. **Para la chispa, el transporte
y el gasto no hay «antes», porque se arreglaron antes de empezar a capturar**; la lista lo declara en
vez de fabricar un antes con el codigo de ayer.

**Nota de metodo, para G07-G14**: *abrir el componente antes de proponer un cambio. Me ha costado tres
rondas y tres propuestas inventadas.*

### G07: el puntero sellaba una fecha y la carpeta otra

`publicar(momento=X)` **nombraba la carpeta con `X`** (`_sello(momento)`) **y sellaba el puntero con
`datetime.now()`** (`_mueve_puntero`). *Con `momento=None`, el uso normal, las dos son «ahora» y
cuadra.* **Pero `/api/estado` comprueba la coherencia comparando justo esas dos fechas** --
`_vigencia(catalogo.fecha_de_gold(), puntero["publicado_en"])` --, **asi que una publicacion
retrofechada se declara incoherente sin serlo.** *Y el parametro `momento` existe precisamente para
poder fechar: la mitad del sello lo ignoraba.*

**Corregido**: `_mueve_puntero` acepta `momento` y sella con el. *Al volver atras (`fijar`) no se pasa,
y esta dicho por que: ahi lo que importa es **cuando se movio el puntero**, no cuando se publico la
version a la que se vuelve.*

**Y con su prueba**, que antes no existia: *publicar con una fecha elegida y **muy anterior a hoy**
--1 de enero de 2026-- y exigir que `publicado_en` empiece por esa fecha.* Sin el arreglo, el puntero
diria octubre y el `assert` cae.

**De paso quedaron verificados dos puntos de G07 leyendo, no suponiendo**: *el pipeline publica al
final con `publicar()`, y **si no puede, el puntero se queda donde estaba y el desajuste queda
visible** (`pipeline.py:792-799`, con el incidente del **13 de octubre de 2026** -- gold en el 8 y el
puntero en el 7 -- documentado en el propio comentario)*; y **`/api/estado` lo declara** comparando las
dos fechas.

### G07: el manifiesto medía un reloj y hay dos

**La clausula que faltaba de 168**, y la que G07 escribe con dos frases: *«descubrimiento con sitemap
antiguo no implica automaticamente precio antiguo; **medir ambos por separado**»*.

**El manifiesto declaraba UNA fecha de captura por cadena** -- la de ficha, que sale de `bronze` -- y
los precios viven en **otro sitio y con su propio reloj**: `gold/precio_diario.parquet`, columna
`fecha`, **una por cadena** (medido: Alcampo de 2026-09-06 a 2026-10-11, Carrefour desde el 09-07).

*Un catalogo con las fichas de hoy y los precios de anteayer producia **cero avisos** y se leia como
fresco.* **Es exactamente el caso contra el que G07 escribe esa linea.**

**Corregido**: `_precios()` lee `max(fecha)` por `fuente` y lo mete en `fuentes[fuente]["precio"]`,
junto a `captura`; **y el aviso se parte en dos**:

    "{fuente}: sin captura de hoy (la ultima es X)"
    "{fuente}: la ficha es de hoy pero el precio es de X"      <-- nuevo

*Y una cadena con precio y sin ficha tambien entra: un precio sin ficha es un dato y hasta hoy no
aparecia.* **No lanza si falta el fichero**: el dia se mide por el dato, no por el manifiesto.

**Contra los datos reales**: las cinco cadenas con `ficha=2026-10-11` y `precio=2026-10-11`, **cero
avisos** -- que es la verdad. *El caso que importa -- ficha fresca y precio viejo -- lo fija la prueba.*

**Y seis pruebas nuevas** (`tests/test_g07_manifiesto.py`): las dos fechas por separado, **el aviso
cuando la ficha es de hoy y el precio de enero**, que con las dos iguales no avisa, que sin fichero de
precios el manifiesto sale igual, que un precio sin ficha entra, y que se escribe sin dejar temporal.

### G07, punto 169: **las cinco pruebas, y la leccion de las cuatro que fallaron**

**La quinta -- la de reintento -- costo cinco intentos, y los cuatro primeros ensenaron cuatro cosas
reales** sobre como falla la publicacion:

1. **`adoptar()` no escribe parquet: enlaza.** *Un monkeypatch sobre `write_parquet` no se dispara.*
   Son **dos modos de fallo distintos**, y el vecino -- «caida entre escrituras» -- cubre el primero.
2. **`publicar` captura el `OSError` de `os.link` y cae a `shutil.copy2`.** *Un enlace que falla no es
   una publicacion que falla: esta tratado.* Inyectar la caida solo en `link` no prueba nada.
3. **Un contador compartido entre las dos funciones miente**: el `copy2` de respaldo del mismo fichero
   era la llamada 3 y no fallaba. *Hay que contar por destino.*
4. **El tipo de excepcion depende de DONDE caiga el fallo**: antes de la comprobacion de completitud
   sale el `OSError` de `copy2`; despues, `PublicacionIncompleta`. *Fijarlo a uno ata la prueba a un
   detalle de implementacion.*

**Y el quinto intento no fue un hallazgo: fue otra suposicion.** *Ahi se revirtio el fichero y se dejo
la suite en verde, en vez de dejar una prueba que no entendia.* **El encargo prohibe retirar pruebas
validas; el simetrico es no anadir pruebas que no se sostienen.**

**La que si pasa, a la primera**: `test_una_publicacion_que_falla_se_reanuda_sin_regenerar_nada`, **sin
parchear nada** -- *el fallo se provoca **quitando un fichero declarado**, que es como falla de verdad*.
Mide el ciclo entero: **la publicacion falla** (`PublicacionIncompleta`), **el suelto queda intacto y con
sus bytes**, **no hay version ni carpeta a medias**; y despues **`adoptar()` publica los MISMOS bytes**
-- *enlaza, no regenera --*. **Reanudar no es volver a empezar: es publicar lo que ya estaba escrito.**

**Y con eso el punto 169 queda completo: cinco de cinco.**

### G07, punto 170: el cerrojo, la poda, y **una constante que no leia nadie**

**Cuatro exigencias, y las cuatro estan.**

| 170 exige | y hay |
|---|---|
| **bloqueo de ejecucion** | ✓✓ **`core/runlock.py`**: cerrojo **del sistema operativo** (`msvcrt.locking` en Windows, `fcntl.flock` en Linux), no bloqueante, mensaje claro -- *«ya hay otra ejecucion de cesta en marcha»* --, liberado en `finally`, **con dos pruebas** (`test_runlock.py`) y **tomado de verdad** (`run.py:30`) |
| **escrituras atomicas** | ✓✓ *`publicacion` y `manifiesto`: temporal y `os.replace`* |
| **no añadir tareas diarias duplicadas** | ✓ *la marca diaria de `ejecutar.bat`, con el motivo escrito* |
| **respetar la retencion sin borrar crudo necesario** | ✓✓ *`limpiar.py`: por dias, `--ensayo` para ver que borraria, **y `storage.comprueba_borrable` como cinturon** -- «es la unica del proyecto que llama a `rmtree` y el dia que alguien le cambie la raiz por descuido conviene que reviente aqui y no en bronze»* |

**Y el defecto que traia**: `config.py` tenia **dos** constantes para la retencion. **La documentada**
-- `RETENCION_RAW_DIAS = 0`, con el comentario ***«0 = para siempre»*** -- **no la leia nadie**: `git
grep` solo devolvia su definicion. La que manda es **`DIAS_RAW = int(os.environ.get("SCRAP_DIAS_RAW",
"30"))`**, documentada en dos sitios y usada por la poda.

*Quien abriera `config.py` para saber cuanto crudo se guarda leia «para siempre» y se lo creia, con
`limpiar.py` tirando a los 30 dias.* **Una constante muerta que se lee como politica es peor que no
tenerla.** Retirada; y los documentos y la poda **tenian razon los dos**: el arreglo era **borrar una
constante**, no tocar el comportamiento.

**Verificado sobre datos reales**: `carpetas_caducadas(0) == []` -- *«0 = para siempre» si esta
implementado* --, `carpetas_caducadas(30) == 0` -- *nada caducado hoy* -- y `--ensayo` no propone nada.

**Y con esto G07 queda entero: 165, 166, 167, 168, 169 y 170.**

### G08: el hash de Lidl, **y la limitacion de la fuente medida**

**El defecto que el documento nombraba**, confirmado y arreglado con lo que hay:

    antes:  ("nombre", "marca", "ean", "precio_cent", "descripcion")
    ahora:  ("nombre", "marca", "ean", "gtin_invalido", "descripcion", "url", "imagen")

- **fuera `precio_cent`**: *el precio **no es parte de la ficha**, asi que una oferta nueva marcaba «la
  ficha cambio» -- la columna que existe para vigilar la ficha vigilaba el escaparate.*
- **dentro `gtin_invalido`, `url` e `imagen`**, que si lo son. *Y `ean` a secas no bastaba: cuando el
  codigo no valida, `ean` es `None` y el codigo vive en `gtin_invalido`, asi que **dos fichas con GTIN
  invalido distinto daban el mismo hash**.*
- **`PARSER_VERSION` a `lidl-jsonld-2`**, para que los hashes viejos no se comparen con los nuevos.

**Y LA PREGUNTA DE FONDO, CERRADA Y MEDIDA.** Se persiguio cuatro rondas: *¿`lee` no extrae
ingredientes porque el parser esta incompleto?* **No.** El bloque `@type=Product` de Lidl trae **nueve
claves** -- `@type, brand, description, gtin13, image, name, offers, sku, url` -- y **no publica
ingredientes, nutricion ni alergenos, NI SIQUIERA EN UN ALIMENTO**: medido sobre una ficha de galletas
(«Galletas rellenas», Sondey). *Las mismas nueve claves que una licuadora.*

    Asi que el hash no se arregla anadiendo campos: **no hay campos que anadir.**
    No es un parser incompleto, **es una fuente que no los da.**

**Para tenerlos hay que parsear el HTML de la ficha -- donde `estructura_de` ve la palabra
«ingrediente» como senal, y su docstring avisa de que es «cota inferior» -- o ir a fuente
complementaria** (G08 puntos 176 y 181: *GTIN y presentacion compatibles antes de vincular*).

**Cuatro pruebas nuevas.** *Tres del hash*: el precio no lo cambia, el GTIN invalido si, y la
descripcion y la imagen tambien. *Y una **fija la limitacion***: la ficha de un alimento **no** trae
ingredientes, nutricion ni alergenos -- *y **si algun dia los trae, la prueba cae y avisa***, que es
para lo que sirve.

**Y un hallazgo de paso, medido**: de las **27 fichas guardadas en `data/fichas-lidl/`, NINGUNA es
alimentaria** -- *woks, juguetes, textil, jardin, bano, menaje* --. **Es el «exceso de bazar» que G08
nombra en su punto 183 y el alcance que G09 prohibe en su 188.** *Y `core/alcance.py` existe, con
`clasificar_alcance` memorizado y politica en `alcance.yml`: la pregunta abierta es **quien llena la
cola de Lidl y si le aplica el filtro**.*

**Las tres puertas del cálculo, medidas sin base de datos.** `donde_comprar` seria lo natural de
medir, pero **lee el catálogo** (`_candidatos` sobre `data/gold/`) y una prueba suya *mide el
calendario*. Las dos piezas donde la revocación decide **si** son puras:

| | |
|---|---|
| `_es_la_confirmada(peticion, alternativa)` | ✓ **`autorizado=False` deja de contar, por el primer camino** |
| las tres condiciones, **cada una sola** | ✓ sin alternativa · sin producto aceptado · otro producto · otra cadena |
| **la cadena por sus dos nombres** (`fuente` y `cadena`) | ✓ *el defecto que ya hubo, fijado para que no vuelva* |
| la alternativa como **diccionario o como objeto** | ✓ |
| `_total_autorizado` | ✓ suma lo autorizado, cuenta, y **devuelve las pendientes con su motivo** |

**12 pruebas, puras, en 0,40 s.** Y tres correcciones mias por el camino, todas por leer un trozo:
`donde_comprar` **no** es pura (dije que si); el endpoint autoriza por **`Query`**, no por cuerpo;
y **`Eleccion` tiene `autorizada`, `identidad` y `motivo`** -- campos que no vi porque mi lectura del
dataclass se cortó en `linea_id`, y sin `autorizada` mis dos pruebas del total *median mi suposición,
no el código*. **Un total que esconde lo que no pudo contar es peor que un total más bajo**: por eso
`pendientes` viaja con su motivo, y por eso la línea revocada **no es un hueco**.

### G03, las tres puertas del cierre: medida, y con la conclusión contraria a mi hipótesis

Iba a demostrar que **revocar cambia el precio que se archiva** al cerrar. **No lo cambia, y está bien
que no lo cambie:**

```
cesta.py:867   if not linea.get("producto_movido"):                    ← una movida no recibe precio
cesta.py:872       suyos = [... if k[-1] != "alternativa"]              ← el cierre descarta sustitutos
```

**El cierre no archiva sustitutos.** Archiva **el producto que el grupo es hoy**, con la tienda
decidida mandando sobre el más barato. *Es de precios y guarda lo que se compró, no lo que se aceptó*:
**no hay nada que revocar en esa puerta.** La frase del documento —«estimación, reparto y cierre no
pueden seguir usando el producto revocado»— **se cumple de tres formas distintas**:

| puerta | cómo | estado |
|---|---|---|
| estimación | la revocada **deja de contar** y pasa a `pendientes` con su motivo | ✓ medido |
| reparto | `_es_la_confirmada` devuelve `False` **por el primer camino** | ✓ medido |
| **cierre** | **nunca usó el sustituto**; archiva el producto del grupo, o **nada** si la línea se movió | ✓ medido |

**Y ahí el cierre sí tiene algo que demostrar, y lo demuestra**: **una línea movida se archiva con
`precio_cent` en NULL** —*con y sin autorización*—, que va a `sin_precio`: *un cero ahí sería afirmar
que salió gratis*.

**Qué es una línea movida** (`catalogo.py:798`): la que dice un nombre que **ya no es** el de ningún
producto de su grupo. **El síntoma de que `grupo_id` es un ordinal que el emparejador renumera en cada
pasada** —*medido el 28 de septiembre de 2026 con datos de casa: la leche entera salía en el pasillo
de higiene y belleza, con el precio del pintalabios*—. **La migración al `producto_id` estable está
apuntada desde el 22 de septiembre** (`docs/MODELO.md`, `docs/DIAGNOSTICO-MATCHING.md` §21) y **es el
paquete G10**. Anotado aquí porque G03 lo ha tocado de lado.

**Observación para G10, no afirmación**: `coste_por_linea` construye `Peticion`es con `autorizado` y
`autorizado_producto` **y después descarta las alternativas por la llave**. *Ese dato entra en
`_candidatos` y no se usa para el precio.* Puede ser correcto; **no lo afirmo**.

**La segunda lista de casa responde 409, no 500.** La base impone `lista_de_casa_por_dueno` --una
lista de casa por persona, que es la regla correcta: es el eje que alimenta el contador del menú, el
puente de la compra y las alertas-- y la API no la atrapaba: crear la segunda salía como «Internal
Server Error». Ahora dice *«Ya tienes una lista de casa, y solo puede haber una…»*. *Misma clase que
el 422 de las líneas: la restricción hace su trabajo y el mensaje culpaba al servidor.*

**Y la causa de tres rondas de fallos en el andamiaje, encontrada**: **salir del `with TestClient(...)`
ejecuta el `lifespan` de la aplicación, que CIERRA el almacén.** Por eso la primera prueba de un
módulo pasaba y las siguientes morían con `RuntimeError: el almacen no esta arrancado` (y antes con
`psycopg`, según por dónde reventara). *La firma era inconfundible y no la vi: **la prueba pasa sola y
falla en el fichero**.* El arranque va ahora en el limpiador, que corre entre pruebas.

**Cómo se ejecuta la prueba del recibo** (la cadena se lee al importar, no vale `monkeypatch`):

    $env:CESTA_POSTGRES='postgresql://cesta:prueba@127.0.0.1:5434/cesta'
    uv run pytest -q tests/test_g01_recibo_del_puente.py

Sin esa variable **se salta diciendo qué hacer**, no conecta al 5432 por defecto.

1. **El recorrido en navegador 390 y 1440**: alta efectiva, lectura, recarga, borrado y tendencias,
   guardando IDs y resultados. *Es lo único que falta para cerrar G01: el contrato está probado en
   almacén y por HTTP, pero **no recorrido en un navegador**.*
2. **El puente compra→diario usaba el número de la previa**, no el recibo: `Diario.tsx:62` hace
   `setAnotadas(previa?.anotarian.length ?? 0)`. *Acción: consumir `ReciboDeAlta`/lo que devuelva
   `anotarDeLaCompra`, y decir cuántas se anotaron de verdad.*
3. **Idempotencia por operación**: hoy no hay clave. *Acción: una clave por operación (doble clic,
   respuesta perdida, reintento) que no duplique, **sin** deduplicar por nombre+fecha+nutrientes —
   eso ya está probado que debe permitir dos comidas iguales.*
4. **`ml` frente a `g`**: el formulario solo ofrece gramos. Ofrecer mililitros exige una unidad
   declarada en el almacén (`cantidad_g` no puede guardar ml: es justo la equivalencia que el
   documento prohíbe sin densidad trazable). *Acción: decidir con el modelo, no en la pantalla.*
5. **Aislamiento por HTTP montado**: anónimo 401; B no enumera, lee, modifica ni borra entradas de A
   por ID o fecha; cambio A→B sin cachés ni borradores. *Acción: extender las pruebas de la API con
   `TestClient`, que es donde se prueba la ruta y no la función interna.*
6. **Navegador 390 y 1440**: alta efectiva, lectura, recarga, borrado y tendencias, guardando IDs y
   resultados. *Acción: sección nueva en `plataforma/prueba_navegador.py`, con la disciplina del
   fichero: esperar a que el dato esté, y anclarse en los textos de hoy.*

### Limitaciones registradas

- **La ingesta del 11 de octubre estaba en curso** durante esta ejecución (tarea `Cesta diaria`,
  arrancada 11:05, Carrefour 425/596 categorías, WAF y un HTTP 520). La versión publicada seguía
  siendo `20261010-142831`. **No se ha detenido ni alterado**, y ningún ensayo de este paquete
  depende de la versión del catálogo.
- Los ensayos de este paquete usan **base SQLite temporal** (`tmp_path`) y **la base desechable del
  5434**; **no se ha tocado el diario real ni compras reales**.

### Comprobaciones del paquete

```
uv run pytest -q tests/test_g01_diario_aceptacion.py tests/test_de_la_ficha_al_diario.py
uv run ruff check .
cd plataforma/web/app && npx --no-install tsc --noEmit
```
